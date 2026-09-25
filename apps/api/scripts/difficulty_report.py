"""Measure the two difficulty signals against each other, and against the only thing that actually measures
difficulty — before deciding which one leads (difficulty-at-upload ADR-02, A-05).

Reads only: it never writes a level. Same posture `suggestion_report.py` takes for topics — run it, read the
numbers, then choose. That script is why the topic prompt's coverage was measured instead of assumed.

    docker compose exec -T -e PYTHONPATH=/app api python scripts/difficulty_report.py [--limit 400] [--json out.json]

Unlike `suggestion_report.py` this one runs **inside the api container** rather than over HTTP: there is no
on-demand endpoint for levels the way `/questions/suggest-topics` exists for topics, so the only way to ask the
model the question the pipeline asks is to build the same pass in process. `PYTHONPATH=/app` is what puts the
`app` package on the path when the script, not the package, is the entry point.

It goes through `DifficultyModelPass.ask` and so through the same `DIFFICULTY_SYSTEM`, the same batch size and the
same reply reading as the pipeline stage. Anything else would measure a prompt that is not the one shipping.

Four numbers, each with the size of the sample under it:

1. **Coverage** — of the questions the model was asked, how many came back as a level it could read.
2. **Agreement** with the position rule, split into the same band, one band apart, two or more. The split matters:
   `th` against `vd` is where two teachers disagree too; `nb` against `vdc` is one of them being wrong.
3. **The spread each signal produces.** A model answering `th` nine times in ten is not classifying — it has found
   the most common label and is repeating it. Agreement alone cannot see that, and high agreement with a lopsided
   spread is the failure this section exists to catch.
4. **Against the real correct-rate**, for questions with enough answers. This is the only section that measures
   difficulty rather than guessing at it; on a bank that has barely been sat it will be thin, so its sample size
   is printed first and never left off.
5. **Where the two-band disagreements sit** — by part, with the direction, and the label pairs that produce them.
   A disagreement spread evenly over the paper is noise; one that piles into a single part, in a single
   direction, is one signal being wrong about that part in a way that can be named.

`--json` writes the per-question answers, not only the totals: the model pass costs five minutes over this bank,
and every later cut of the same run should come out of the file rather than out of the model again.

**Agreement is not accuracy.** Two signals wrong the same way agree perfectly. Only section 4 says either is
right, and only when it has a sample.
"""
import argparse
import collections
import json
import statistics
import sys
import time

from sqlalchemy import func, select

import app.metadata  # noqa: F401  (every table and mapping)
from app.modules.bank.domain.entities import USABLE
from app.modules.ingestion.application.difficulty import DifficultyModelPass
from app.modules.ingestion.application.models import usable_model
from app.modules.ingestion.domain.errors import LlmError
from app.modules.ingestion.domain.services.difficulty_rules import (
    DIFFICULTY_BATCH,
    difficulty_for,
    question_text,
)
from app.modules.ingestion.domain.services.processing import org_defaults
from app.modules.ingestion.infrastructure.adapters.llm import HttpChatModels
from app.modules.ingestion.infrastructure.repositories import SqlAiModelRepository
from app.shared.infrastructure import db as dbmod
from app.shared.infrastructure.schema.assessment import answer_facts
from app.shared.infrastructure.schema.bank import questions
from app.shared.infrastructure.schema.identity import organizations

LEVELS = ("nb", "th", "vd", "vdc")
RANK = {level: i for i, level in enumerate(LEVELS)}
LABEL = {"nb": "Nhận biết", "th": "Thông hiểu", "vd": "Vận dụng", "vdc": "Vận dụng cao"}
#: answers on one question before its correct-rate is worth reading at all
MIN_ANSWERS = 10


def pct(n: int, total: int) -> str:
    return f"{n}/{total} ({round(100 * n / total) if total else 0}%)"


def spread(counts: collections.Counter, total: int) -> str:
    return " · ".join(f"{LABEL[lv]} {pct(counts.get(lv, 0), total)}" for lv in LEVELS)


def pick_org(db, code: str | None):
    o = organizations.c
    stmt = select(o.id, o.code, o.name, o.settings)
    stmt = stmt.where(o.code == code) if code else stmt.where(o.is_system.is_(False)).order_by(o.created_at).limit(1)
    return db.execute(stmt).first()


def usable_questions(db, org_id, limit: int):
    """The questions a blueprint can actually draw, which is the population whose levels matter."""
    q = questions.c
    return list(db.execute(
        select(q.id, q.part, q.number, q.type, q.stem, q.options, q.difficulty, q.difficulty_source)
        .where(q.organization_id == org_id, q.status.in_(USABLE), q.stem != "")
        .order_by(q.part, q.number).limit(limit)))


def correct_rates(db, org_id):
    """{question_id: (mean correct_ratio, answers)} for questions answered enough times to mean anything.

    `correct_ratio` is points/max_points as graded, so a true/false question scored statement by statement counts
    as the fraction it earned rather than pass or fail — which is what makes it comparable across the three parts.
    """
    f = answer_facts.c
    rows = db.execute(
        select(f.question_id, func.avg(f.correct_ratio).label("ratio"), func.count().label("n"))
        .where(f.organization_id == org_id).group_by(f.question_id).having(func.count() >= MIN_ANSWERS))
    return {r.question_id: (float(r.ratio), int(r.n)) for r in rows}


def ask_model(passer, rows, size=DIFFICULTY_BATCH):
    """{question id: level} the model gave, plus how long each batch took and how many failed.

    The numbering is no longer this script's business: `DifficultyModelPass.ask` assigns it by position in the
    batch, so this measures exactly what the pipeline sends (T-02-04).
    """
    answers, seconds, failed, asked = {}, [], 0, 0
    for start in range(0, len(rows), size):
        chunk = rows[start:start + size]
        batch = list(chunk)
        asked += len(batch)
        began = time.monotonic()
        try:
            answers.update(passer.ask(batch))
        except LlmError as exc:
            failed += 1
            print(f"  lô {start // size + 1} lỗi: {exc}", file=sys.stderr)
        seconds.append(round(time.monotonic() - began, 1))
        print(f"  … {asked}/{len(rows)}", end="\r", file=sys.stderr, flush=True)
    return answers, seconds, failed, asked


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=400)
    ap.add_argument("--org", default=None, help="mã tổ chức; mặc định: tổ chức thật đầu tiên")
    ap.add_argument("--json", dest="out", default=None)
    # asking one question at a time is the only way its level stops depending on the nine questions beside it —
    # measured at 58% per-question agreement between two batchings of the same bank. This is how the cost of that
    # is measured rather than guessed at.
    ap.add_argument("--batch", type=int, default=DIFFICULTY_BATCH, help="số câu mỗi lần hỏi model")
    args = ap.parse_args()

    dbmod.configure()
    db = dbmod.session_factory()()
    try:
        org = pick_org(db, args.org)
        if org is None:
            sys.exit("không tìm thấy tổ chức")
        rows = usable_questions(db, org.id, args.limit)
        if not rows:
            sys.exit("tổ chức này chưa có câu hỏi dùng được")

        rule = {r.id: difficulty_for(r.part, r.number, r.type) for r in rows}
        stored = {r.id: (r.difficulty, r.difficulty_source) for r in rows}

        model_id = org_defaults((org.settings or {}).get("ingestion") or {}).get("tag_model")
        model = usable_model(SqlAiModelRepository(db), org.id, model_id) if model_id else None

        print(f"\nTổ chức {org.name} ({org.code}) · {len(rows)} câu dùng được"
              f" · model: {model.model if model else 'chưa đăng ký'}")

        answers, seconds, failed, asked = {}, [], 0, 0
        if model is not None:
            answers, seconds, failed, asked = ask_model(
                DifficultyModelPass(HttpChatModels(), model),
                [(r.id, question_text(r.stem, r.type, r.options)) for r in rows], args.batch)

        report = {"org": org.code, "questions": len(rows), "model": model.model if model else None}

        print("\n── 1. Model đọc được bao nhiêu câu")
        if model is None:
            print("  Tổ chức chưa đăng ký model phân loại nào, nên chỉ có quy tắc vị trí — và nó phủ 100%.")
        else:
            print(f"  hỏi {asked}, đọc được {pct(len(answers), asked)}" + (f" · {failed} lô lỗi" if failed else ""))
            if seconds:
                print(f"  mỗi lô {args.batch} câu: {min(seconds)}s – {max(seconds)}s,"
                      f" giữa {statistics.median(seconds)}s · cả lượt {round(sum(seconds))}s")
        report["coverage"] = {"asked": asked, "read": len(answers), "failed_batches": failed}

        print("\n── 2. Model so với quy tắc vị trí")
        pairs = [(rule[qid], lv) for qid, lv in answers.items()]
        if not pairs:
            print("  không có câu nào để so.")
            report["agreement"] = None
        else:
            gaps = collections.Counter(abs(RANK[a] - RANK[b]) for a, b in pairs)
            far = sum(v for k, v in gaps.items() if k >= 2)
            print(f"  trùng khớp      {pct(gaps[0], len(pairs))}")
            print(f"  lệch một bậc    {pct(gaps[1], len(pairs))}   ← hai giáo viên cũng lệch nhau chừng này")
            print(f"  lệch ≥ hai bậc  {pct(far, len(pairs))}   ← ít nhất một bên sai")
            report["agreement"] = {"same": gaps[0], "one_band": gaps[1], "two_or_more": far, "compared": len(pairs)}

        print("\n── 3. Mỗi tín hiệu phân bố ra sao")
        rule_spread = collections.Counter(rule.values())
        print(f"  quy tắc : {spread(rule_spread, len(rule))}")
        model_spread = collections.Counter(answers.values())
        if answers:
            print(f"  model   : {spread(model_spread, len(answers))}")
            top = model_spread.most_common(1)[0]
            if top[1] / len(answers) >= 0.7:
                print(f"  ⚠ model dồn {pct(top[1], len(answers))} vào một mức ({LABEL[top[0]]}): đây là dấu hiệu nó"
                      " đang lặp lại nhãn phổ biến nhất chứ không phân loại, và đồng thuận cao cũng không cứu được.")
        print(f"  đang lưu: {spread(collections.Counter(d for d, _ in stored.values() if d), len(rows))}"
              f" · chưa có mức: {sum(1 for d, _ in stored.values() if not d)}")
        report["spread"] = {"rule": dict(rule_spread), "model": dict(model_spread),
                           "stored_missing": sum(1 for d, _ in stored.values() if not d)}

        print(f"\n── 4. So với tỉ lệ làm đúng thật (câu có ≥ {MIN_ANSWERS} lượt trả lời)")
        rates = correct_rates(db, org.id)
        measured = [qid for qid in rule if qid in rates]
        report["measured"] = {"sample": len(measured)}
        if not measured:
            print(f"  **Mẫu: 0 câu.** Chưa câu nào đủ {MIN_ANSWERS} lượt trả lời, nên không con số nào ở trên được"
                  " kiểm chứng: cả hai tín hiệu đang đoán, và đây là phần duy nhất nói được ai đoán đúng."
                  "\n  Chạy lại khi học sinh đã làm bài thật.")
        else:
            print(f"  **Mẫu: {len(measured)} câu** trên {len(rows)}.")
            for name, guess in (("quy tắc", rule), ("model", answers)):
                got = [(guess[qid], rates[qid][0]) for qid in measured if qid in guess]
                if not got:
                    continue
                print(f"  {name}:")
                for lv in LEVELS:
                    mine = [ratio for level, ratio in got if level == lv]
                    if mine:
                        print(f"    {LABEL[lv]:<14} tỉ lệ đúng {round(100 * statistics.mean(mine))}%"
                              f" trên {len(mine)} câu")
            print("  (mức càng cao thì tỉ lệ đúng phải càng thấp; không giảm đều nghĩa là thứ tự đang sai)")

        print("\n── 5. Chỗ lệch ≥ hai bậc nằm ở đâu")
        far_rows = [r for r in rows if r.id in answers and abs(RANK[rule[r.id]] - RANK[answers[r.id]]) >= 2]
        if not far_rows:
            print("  không có câu nào lệch xa thế.")
        else:
            per_part = collections.Counter(r.part or "(không có)" for r in rows if r.id in answers)
            for part, total in sorted(per_part.items()):
                mine = [r for r in far_rows if (r.part or "(không có)") == part]
                if not mine:
                    continue
                higher = sum(1 for r in mine if RANK[answers[r.id]] > RANK[rule[r.id]])
                print(f"  Phần {part} ({total} câu): {pct(len(mine), total)}"
                      f" — model cao hơn {higher}, thấp hơn {len(mine) - higher}")
            print("  cặp nhãn hay gặp:")
            pairs_far = collections.Counter((rule[r.id], answers[r.id]) for r in far_rows)
            for (a, b), n in pairs_far.most_common(4):
                print(f"    quy tắc {LABEL[a]} → model {LABEL[b]}: {n} câu")
        report["far"] = {"total": len(far_rows),
                         "by_part": dict(collections.Counter(r.part or "?" for r in far_rows))}
        # the model pass is the expensive part of this run; keep every answer so a later cut needs no second one
        report["rows"] = [{"id": str(r.id), "part": r.part, "number": r.number, "type": r.type,
                           "rule": rule[r.id], "model": answers.get(r.id),
                           "rate": rates.get(r.id, (None, 0))[0], "answers": rates.get(r.id, (None, 0))[1]}
                          for r in rows]

        if args.out:
            with open(args.out, "w", encoding="utf-8") as fh:
                json.dump(report, fh, ensure_ascii=False, indent=2)
            print(f"\nđã ghi {args.out}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
