"""What the tagging queue's suggestions are worth on the real backlog (topic-coverage T-03-02, ADR-04).

Read-only against the live stack: page by page, exactly as the queue does, it asks `/questions/suggest-topics`
twice — once with `use_model: false` (the rules alone) and once with the model — and reports how many questions
got a candidate either way, where the candidates came from, and how long a page costs. Agreement is measured on
the questions a teacher has already placed by hand: how often the top candidate, and the top `ai` candidate, is
the topic the teacher chose.

    python scripts/suggestion_report.py [--page 20] [--limit 0] [--json report.json]

EXAMIND_URL / EXAMIND_ORG / EXAMIND_USER / EXAMIND_PASSWORD override the stack it talks to.
"""
import argparse
import collections
import json
import os
import sys
import time

import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # run it from anywhere
from app.modules.ingestion.domain.services.topic_rules import WEAK_KEYWORD  # noqa: E402

BASE = os.environ.get("EXAMIND_URL", "http://localhost:8088/api")
ORG = os.environ.get("EXAMIND_ORG", "trungtama")
USER = os.environ.get("EXAMIND_USER", "admin")
PASSWORD = os.environ.get("EXAMIND_PASSWORD", "admin123456")


def login() -> httpx.Client:
    c = httpx.Client(base_url=BASE, timeout=600)
    c.post("/auth/login", json={"org_code": ORG, "username": USER, "password": PASSWORD}).raise_for_status()
    return c


def questions(c: httpx.Client, limit: int, **filters) -> list[dict]:
    """Every question matching the filters, oldest page first; `limit` 0 means all of them."""
    out, page = [], 1
    while True:
        body = {"status": "all", "page": page, "limit": 100, "sort": [{"field": "created_at", "desc": True}], **filters}
        got = c.post("/questions/search", json=body).json()
        out += got["data"]
        if len(out) >= got["total"] or not got["data"] or (limit and len(out) >= limit):
            return out[:limit] if limit else out
        page += 1


def suggest(c: httpx.Client, ids: list[str], use_model: bool) -> tuple[dict, bool, float]:
    """(suggestions, model_used, seconds) for one page of the queue."""
    t0 = time.monotonic()
    got = c.post("/questions/suggest-topics", json={"question_ids": ids, "use_model": use_model}).json()
    return got["suggestions"], got["model_used"], round(time.monotonic() - t0, 1)


def primary(q: dict) -> dict | None:
    return next((t for t in q["topics"] if t["is_primary"]), None)


def pct(n: int, total: int) -> str:
    return f"{n}/{total} ({round(100 * n / total) if total else 0}%)"


def weak(candidates: list[dict]) -> bool:
    """What the model is asked about: no candidate at all, or nothing the cues are confident in."""
    return not candidates or candidates[0]["score"] < WEAK_KEYWORD


def coverage(c: httpx.Client, rows: list[dict], page_size: int) -> dict:
    """Ask for every page twice — the rules alone, then the way the queue asks — and count what came back."""
    stats = {"questions": len(rows), "rule_placed": 0, "model_placed": 0, "asked": 0, "answered": 0, "pages": [],
             "sources": collections.Counter(), "model_pages": 0, "degraded_pages": 0}
    for start in range(0, len(rows), page_size):
        page = rows[start:start + page_size]
        ids = [q["id"] for q in page]
        rules, _, rule_secs = suggest(c, ids, use_model=False)
        with_model, model_used, model_secs = suggest(c, ids, use_model=True)
        asked = [i for i in ids if weak(rules[i])]
        stats["rule_placed"] += sum(1 for i in ids if rules[i])
        stats["model_placed"] += sum(1 for i in ids if with_model[i])
        stats["asked"] += len(asked)
        stats["answered"] += sum(1 for i in asked if any(x["source"] == "ai" for x in with_model[i]))
        stats["model_pages"] += bool(asked) and model_used
        stats["degraded_pages"] += bool(asked) and not model_used
        for i in ids:
            for candidate in with_model[i]:
                stats["sources"][candidate["source"]] += 1
        stats["pages"].append({"n": len(ids), "asked": len(asked), "rules_secs": rule_secs, "model_secs": model_secs,
                               "model_used": model_used})
        state = "model_used" if model_used else ("degraded" if asked else "không cần model")
        print(f"  page {len(stats['pages'])}: {len(ids)} câu, hỏi model {len(asked)} — rules {rule_secs}s, "
              f"+model {model_secs}s ({state})", flush=True)
    return stats


def agreement(c: httpx.Client, rows: list[dict], page_size: int) -> dict:
    """The questions a teacher placed by hand: does the classifier propose what the teacher chose?"""
    stats = {"questions": len(rows), "top_match": 0, "any_match": 0, "ai_offered": 0, "ai_top_match": 0, "ai_any_match": 0}
    for start in range(0, len(rows), page_size):
        page = rows[start:start + page_size]
        found, _, _ = suggest(c, [q["id"] for q in page], use_model=True)
        for q in page:
            chosen, candidates = primary(q)["id"], found[q["id"]]
            ai = [x for x in candidates if x["source"] == "ai"]
            stats["top_match"] += bool(candidates) and candidates[0]["topic_id"] == chosen
            stats["any_match"] += any(x["topic_id"] == chosen for x in candidates)
            stats["ai_offered"] += bool(ai)
            stats["ai_top_match"] += bool(ai) and ai[0]["topic_id"] == chosen
            stats["ai_any_match"] += any(x["topic_id"] == chosen for x in ai)
    return stats


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--page", type=int, default=20, help="questions per request, as the queue shows them")
    ap.add_argument("--limit", type=int, default=0, help="stop after this many questions (0 = the whole backlog)")
    ap.add_argument("--json", help="also write the numbers to this file")
    args = ap.parse_args()
    c = login()

    untagged = questions(c, args.limit, has_topic=False)
    print(f"Chưa gắn chuyên đề: {len(untagged)} câu, {args.page} câu mỗi trang", flush=True)
    cov = coverage(c, untagged, args.page)

    tagged = [q for q in questions(c, 0, has_topic=True) if (t := primary(q)) and t["source"] == "manual"]
    print(f"\nĐã được giáo viên gắn: {len(tagged)} câu", flush=True)
    agr = agreement(c, tagged[:args.limit] if args.limit else tagged, args.page) if tagged else {"questions": 0}

    total = cov["questions"]
    secs = [p["model_secs"] for p in cov["pages"]]
    print(f"\n── Phủ (trên {total} câu chưa gắn)")
    print(f"   chỉ luật        : {pct(cov['rule_placed'], total)}")
    print(f"   luật + model    : {pct(cov['model_placed'], total)}")
    print(f"   nguồn ứng viên  : {dict(cov['sources'])}")
    print(f"   model trả lời   : {pct(cov['answered'], cov['asked'])} câu đã hỏi")
    print(f"   trang có model  : {cov['model_pages']}, trang phải hạ cấp: {cov['degraded_pages']}")
    if secs:
        print(f"   thời gian/trang : {min(secs)}–{max(secs)}s (trung vị {sorted(secs)[len(secs) // 2]}s)")
    if agr["questions"]:
        n = agr["questions"]
        print(f"\n── Trùng với lựa chọn của giáo viên (trên {n} câu)")
        print(f"   ứng viên đầu đúng   : {pct(agr['top_match'], n)}")
        print(f"   nằm trong 3 ứng viên: {pct(agr['any_match'], n)}")
        print(f"   có ứng viên AI      : {pct(agr['ai_offered'], n)}")
        print(f"   ứng viên AI đầu đúng: {pct(agr['ai_top_match'], agr['ai_offered'])}")
    if args.json:
        cov["sources"] = dict(cov["sources"])
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({"coverage": cov, "agreement": agr}, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
