"""Build a centre with enough real, graded work behind it that every report says something.

Read `.ai/e2e/centre/PLAN.md` first — it explains why each number is the number it is, and what this data must
never be used to conclude. The short version of the warning, because it is the expensive part:

    Every attempt here is fabricated. That is harmless for the report screens, which only need structure. It
    destroys exactly one thing: section 4 of `difficulty_report.py`, where a level is checked against the rate at
    which students actually answer correctly. After this runs, that column on this organisation is a column of
    numbers this script chose, and it will look exactly like evidence.

Everything goes through the HTTP API a person would use, so grading, `answer_facts` and topic mastery are written
by the product (synchronously, on submit) rather than by this file. A seed that inserts rows directly leaves
mastery empty and the per-class screens blank.

    python3 scripts/seed_centre.py --yes                      # the shape in the plan
    python3 scripts/seed_centre.py --yes --classes 1 --students 3 --papers 1 --topic-papers 1   # smoke run
    python3 scripts/seed_centre.py --check                    # only re-print the self-check table

The self-check table at the end is the point of the exercise: every row is a threshold that exists in the
analytics code, so a thin seed reports itself as thin instead of looking fine until someone opens a screen.
"""
import argparse
import json
import os
import pathlib
import random
import sys
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = os.environ.get("EXAMIND_URL", "http://localhost:8088")
SEED_PASSWORD = "Examind@2026"          # every seeded account, so a person can sign in and look around
STUDENT_PREFIX, TEACHER_PREFIX = "hs", "gv"
#: thresholds that live in the product; the self-check quotes them so a thin seed is visible as thin
MIN_ANSWERS_PER_TOPIC = 5               # analytics/domain/services/mastery.py:16
WEAK_BELOW = 0.6                        # analytics/domain/services/mastery.py:15
MIN_OBSERVATIONS = 10                   # bank/domain/services/item_stats.py:6
SUBMITS_FOR_A_SPREAD = 20               # assignment_report.py:50-52 buckets ten columns

TRIAL_MATRIX = [("mcq", 12), ("true_false", 4), ("short_answer", 6)]   # the THPT 2025 shape
TOPIC_PAPER_COUNT = 15


def env_file(path: pathlib.Path) -> dict:
    out = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
    return out


class Api:
    """One signed-in identity. `ip` is sent as X-Forwarded-For so that signing in 150 students does not trip the
    login limiter, which counts 30 a minute against one address (identity/interface/deps.py:154)."""

    def __init__(self, ip: str = "127.0.0.1"):
        self.cookies: dict[str, str] = {}
        self.ip = ip
        self.calls = 0

    def request(self, method: str, path: str, body=None, quiet: bool = False, retry: bool = True):
        headers = {"x-forwarded-for": self.ip}
        payload = None
        if body is not None:
            payload = json.dumps(body).encode()
            headers["content-type"] = "application/json"
        if self.cookies:
            headers["cookie"] = "; ".join(f"{k}={v}" for k, v in self.cookies.items())
        req = urllib.request.Request(f"{BASE}/api{path}", data=payload, headers=headers, method=method)
        self.calls += 1
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                for header in r.headers.get_all("set-cookie") or []:
                    k, _, v = header.split(";")[0].partition("=")
                    self.cookies[k] = v
                raw = r.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300]
            # the access cookie lives 15 minutes; the admin session here runs far longer than that
            if e.code == 401 and retry and path != "/auth/refresh":
                self.request("POST", "/auth/refresh", retry=False, quiet=True)
                return self.request(method, path, body, quiet=quiet, retry=False)
            if quiet:
                return {"__error__": e.code, "detail": detail}
            raise SystemExit(f"{method} {path} → {e.code}\n  {detail}") from None

    def get(self, path, quiet=False):
        return self.request("GET", path, quiet=quiet)

    def post(self, path, body=None, quiet=False):
        return self.request("POST", path, body, quiet=quiet)

    def put(self, path, body=None, quiet=False):
        return self.request("PUT", path, body, quiet=quiet)

    def login(self, org: str, user: str, password: str):
        return self.post("/auth/login", {"org_code": org, "username": user, "password": password})


def page(api: Api, path: str, body: dict) -> list:
    """Every row of a search, following pages; the contract caps `limit` at 1000."""
    out, p = [], 1
    while True:
        got = api.post(path, {**body, "page": p, "limit": 500})
        out.extend(got["data"])
        if len(out) >= got["total"] or not got["data"]:
            return out
        p += 1


# ----------------------------------------------------------------- the people


def make_teachers(admin: Api, n: int) -> list[dict]:
    made = []
    for i in range(1, n + 1):
        username = f"{TEACHER_PREFIX}{i:02d}"
        r = admin.post("/users", {"full_name": f"Giáo viên {i}", "username": username, "role": "teacher",
                                  "password": SEED_PASSWORD}, quiet=True)
        if "__error__" in r:  # already there from an earlier run
            made.append({"username": username})
            continue
        made.append(r["user"])
    return made


def make_classes(admin: Api, names: list[tuple[str, int]], grades: dict) -> list[dict]:
    out = []
    for name, grade in names:
        r = admin.post("/classes", {"name": name, "grade_id": grades[grade]}, quiet=True)
        if "__error__" in r:
            found = [c for c in page(admin, "/classes/search", {}) if c["name"] == name]
            if not found:
                sys.exit(f"không tạo được lớp {name}: {r['detail']}")
            out.append(found[0])
        else:
            out.append(r)
    return out


def make_students(admin: Api, klass: dict, count: int, first: int, known: dict) -> list[dict]:
    """Explicit passwords, because that is the only way `must_change_password` comes out False
    (identity/application/commands/create_user.py:38-46) — and an account with the flag set cannot do anything.

    An account that already exists is looked up rather than skipped: the first version returned no id for it, and
    a second run then quietly had those students sit nothing at all while reporting the class as full.
    """
    made = []
    for i in range(first, first + count):
        username = f"{STUDENT_PREFIX}{i:03d}"
        r = admin.post("/users", {"full_name": f"Học sinh {i:03d}", "username": username, "role": "student",
                                  "password": SEED_PASSWORD}, quiet=True)
        if "__error__" in r:
            if username not in known:
                sys.exit(f"{username} đã tồn tại nhưng không tìm lại được: {r['detail']}")
            made.append(known[username])
        else:
            made.append(r["user"])
    admin.post(f"/classes/{klass['id']}/members", {"user_ids": [s["id"] for s in made]})
    return made


# ----------------------------------------------------------------- the papers


def strand_pool(admin: Api, topics: list[dict]) -> list[tuple[dict, int]]:
    """Each strand with how many usable questions sit under it, biggest first. A blueprint row whose topic holds
    nothing aborts the whole call with 422 `empty_topic` (exam_rules.py:84), so this is read, never assumed."""
    out = []
    for t in (x for x in topics if x["depth"] == 1):
        n = admin.post("/questions/search", {"page": 1, "limit": 1, "topic_id": t["id"]})["total"]
        out.append((t, n))
    return sorted(out, key=lambda p: -p[1])


def trial_paper(teacher: Api, title: str, subject_id: str, strands: list[tuple[dict, int]], seed: int) -> dict:
    """A mock exam in the THPT 2025 shape, spread over the strands so the heatmap has a column everywhere."""
    exam = teacher.post("/exams", {"title": title, "subject_id": subject_id,
                                   "settings": {"points_by_type": {"mcq": 0.25, "true_false": 1.0,
                                                                   "short_answer": 0.5, "essay": 1.0},
                                                "scale_to": 10}})
    wide = [t for t, n in strands if n >= 20]
    rows = []
    for qtype, total in TRIAL_MATRIX:
        per = max(1, total // len(wide))
        for i, t in enumerate(wide):
            count = total - per * (len(wide) - 1) if i == 0 else per
            if count > 0:
                rows.append({"topic_id": t["id"], "type": qtype, "count": count})
    r = teacher.post(f"/exams/{exam['id']}/blueprint", {"rows": rows, "seed": seed, "replace": True})
    return r["exam"]


def topic_paper(teacher: Api, title: str, subject_id: str, strand: dict, seed: int) -> dict:
    """One strand, many questions: this is what gives a student ≥5 answers on a leaf topic, which is the gate
    (`MIN_ANSWERS = 5`) below which no topic is ever called weak and "chuyên đề yếu nhất" stays empty."""
    exam = teacher.post("/exams", {"title": title, "subject_id": subject_id,
                                   "settings": {"points_by_type": {"mcq": 0.25, "true_false": 1.0,
                                                                   "short_answer": 0.5, "essay": 1.0},
                                                "scale_to": 10}})
    rows = [{"topic_id": strand["id"], "count": TOPIC_PAPER_COUNT}]
    r = teacher.post(f"/exams/{exam['id']}/blueprint", {"rows": rows, "seed": seed, "replace": True})
    return r["exam"]


def assign(teacher: Api, exam: dict, klass: dict, days_ago: int, minutes: int = 90) -> dict:
    """Opened in the past so the paper is sittable now, and closing well ahead so nothing auto-submits mid-run.

    `shuffle_questions` and `shuffle_options` default to **true**, and with options shuffled the labels a student
    sees are relabelled A–D over a new order — every answer computed from the bank's key would be wrong. Both off.
    """
    opened = time.time() - days_ago * 86400
    return teacher.post("/assignments", {
        "exam_id": exam["id"], "title": exam["title"], "class_ids": [klass["id"]],
        "open_at": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(opened)),
        "close_at": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(time.time() + 30 * 86400)),
        "duration_minutes": minutes, "max_attempts": 1,
        "shuffle_questions": False, "shuffle_options": False, "results_policy": "after_submit"})


# ----------------------------------------------------------------- the sitting


def wrong_response(q: dict, key: dict, rng: random.Random) -> dict:
    """A wrong answer that is a real choice, not a blank.

    A question left unanswered writes no answer fact and moves no mastery (assessment/application/common.py:170),
    so blanks would quietly shrink every report. A wrong MCQ also has to name a specific option, because "Hay chọn
    sai" counts responses whose key differs from the snapshot — with no response there is nothing to count.
    """
    if q["type"] == "mcq":
        labels = [o["label"] for o in q["options"]]
        others = [x for x in labels if x != (key or {}).get("key")] or labels
        return {"key": rng.choice(others)}
    if q["type"] == "true_false":
        truth = {o["label"]: bool((key or {}).get(o["label"])) for o in q["options"]}
        flip = rng.sample(list(truth), k=min(2, len(truth)))  # two statements wrong: partial credit, not zero
        return {k: (not v if k in flip else v) for k, v in truth.items()}
    if q["type"] == "short_answer":
        return {"value": "0"}
    return {"text": "Em chưa làm xong phần này."}


def right_response(q: dict, key: dict) -> dict:
    if q["type"] == "mcq":
        return {"key": (key or {}).get("key") or q["options"][0]["label"]}
    if q["type"] == "true_false":
        return {o["label"]: bool((key or {}).get(o["label"])) for o in q["options"]}
    if q["type"] == "short_answer":
        return {"value": str((key or {}).get("value", ""))}
    return {"text": "Bài làm của em."}


def sit(student: Api, assignment_id: str, keys: dict, topic_of: dict, ability: float,
        strand_offset: dict, rng: random.Random) -> dict | None:
    """One student sitting one paper, through the product: start, answer every question, submit.

    Correct or not comes from the student's own ability and how they get on with that strand — **never from the
    question's difficulty**. Feeding difficulty in here would make section 4 of the difficulty report confirm the
    very labels it is supposed to test (see the plan).
    """
    started = student.post(f"/assignments/{assignment_id}/start", quiet=True)
    if "__error__" in started:
        return None
    attempt = student.get(f"/attempts/{started['attempt_id']}")
    for q in attempt["questions"]:
        key = keys.get(q["id"])
        strand = topic_of.get(q["id"], "")
        p = min(0.97, max(0.03, ability + strand_offset.get(strand, 0.0) + rng.gauss(0, 0.08)))
        body = right_response(q, key) if rng.random() < p else wrong_response(q, key, rng)
        student.put(f"/attempts/{attempt['id']}/answers/{q['id']}",
                    {"response": body, "seconds_spent": max(5, int(rng.gauss(70, 30)))})
    student.post(f"/attempts/{attempt['id']}/submit")
    return student.get(f"/attempts/{attempt['id']}/result", quiet=True)


# ----------------------------------------------------------------- self-check


def self_check(admin: Api, org_code: str) -> None:
    """Every row here is a threshold that exists in the product, so thin data reports itself instead of looking
    fine until someone opens a screen and finds "chưa đủ dữ liệu"."""
    print("\n── Tự kiểm: mỗi dòng là một ngưỡng có thật trong code")
    classes = page(admin, "/classes/search", {})
    exams = page(admin, "/exams/search", {})
    assignments = page(admin, "/assignments/search", {})
    print(f"  lớp {len(classes)} · đề {len(exams)} · bài giao {len(assignments)}")

    enough, thin = 0, 0
    for a in assignments:
        report = admin.get(f"/assignments/{a['id']}/report", quiet=True)
        if "__error__" in report:
            continue
        if report.get("submitted", 0) >= SUBMITS_FOR_A_SPREAD:
            enough += 1
        else:
            thin += 1
    print(f"  bài giao có ≥{SUBMITS_FOR_A_SPREAD} bài nộp (phổ điểm ra hình): {enough}/{enough + thin}")

    weak_seen, checked = 0, 0
    for k in classes:
        ov = admin.get(f"/classes/{k['id']}/overview", quiet=True)
        if "__error__" in ov:
            continue
        rows = ov if isinstance(ov, list) else ov.get("students", [])
        checked += len(rows)
        weak_seen += sum(1 for s in rows if s.get("weakest"))
    print(f"  học sinh có ≥1 chuyên đề dưới {WEAK_BELOW} (cần ≥{MIN_ANSWERS_PER_TOPIC} câu/chuyên đề): {weak_seen}/{checked}")

    topics = admin.get("/stats/topics", quiet=True) or []
    answered = [t for t in (topics if isinstance(topics, list) else []) if (t.get("answered") or 0) > 0]
    print(f"  hàng 'theo chuyên đề' có dữ liệu: {len(answered)}")
    for by in ("type", "difficulty", "tag"):
        rows = admin.get(f"/stats/groups?by={by}", quiet=True) or []
        rows = [r for r in (rows if isinstance(rows, list) else []) if (r.get("answered") or 0) > 0]
        print(f"  tab 'theo {by}' có {len(rows)} hàng có dữ liệu" + ("   ← rỗng thì tab trắng" if not rows else ""))
    print("\n  Kiểm phần còn lại bằng SQL (lượt trả lời, term_code, class_ids, topic_path):")
    sql = ("select count(*) filter (where term_code is not null) as co_hoc_ky,"
           " count(*) filter (where class_ids <> '{}') as co_lop,"
           " count(*) filter (where topic_path is not null) as co_chuyen_de,"
           " count(*) as tong from answer_facts;")
    print(f'  docker compose exec -T postgres psql -U examind -d examind -c "{sql}"')


def warn(org_code: str) -> None:
    print(f"""
  ⚠  Kịch bản này ghi bài làm BỊA vào tổ chức {org_code}.
     Vô hại với mọi màn hình báo cáo. Nhưng từ lúc nó chạy, mục 4 của difficulty_report.py trên tổ chức này
     KHÔNG còn là bằng chứng về bất cứ điều gì: tỉ lệ làm đúng ở đó là tỉ lệ script bốc ra, và nó sẽ trông
     hệt như dữ liệu thật. Muốn đo lại độ chính xác của mức độ thì phải xoá DB và dựng lại.
     Đây là quyết định đã cân nhắc (.ai/e2e/centre/PLAN.md) — cờ --yes là để không bấm nhầm lần thứ hai.
""")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--yes", action="store_true", help="đồng ý ghi bài làm bịa vào tổ chức này")
    ap.add_argument("--check", action="store_true", help="chỉ in lại bảng tự kiểm")
    ap.add_argument("--classes", type=int, default=6)
    ap.add_argument("--students", type=int, default=25, help="mỗi lớp")
    ap.add_argument("--papers", type=int, default=3, help="đề thi thử mỗi lớp")
    ap.add_argument("--topic-papers", dest="topic_papers", type=int, default=3, help="đề chuyên đề mỗi lớp")
    ap.add_argument("--teachers", type=int, default=4)
    ap.add_argument("--seed", type=int, default=20260925)
    args = ap.parse_args()

    creds = env_file(ROOT / ".ai" / "credentials.env")
    org, user, password = creds.get("LOCAL_ORG"), creds.get("LOCAL_USER"), creds.get("LOCAL_PASSWORD")
    if not all((org, user, password)):
        sys.exit("thiếu LOCAL_ORG / LOCAL_USER / LOCAL_PASSWORD trong .ai/credentials.env")

    admin = Api()
    admin.login(org, user, password)
    if args.check:
        return self_check(admin, org)
    warn(org)
    if not args.yes:
        sys.exit("dừng: chạy lại với --yes nếu đúng ý.")

    rng = random.Random(args.seed)
    began = time.monotonic()

    taxonomy = admin.get("/taxonomy")
    subject = next((s for s in taxonomy["subjects"] if s["code"] == "toan"), taxonomy["subjects"][0])
    grades = {g["level"]: g["id"] for g in page(admin, "/grades/search", {})}
    topics = admin.get(f"/topics?subject_id={subject['id']}")
    strands = strand_pool(admin, topics)
    print("1. đọc sẵn có: " + " · ".join(f"{t['name']} {n}" for t, n in strands))
    if not [n for _, n in strands if n >= TOPIC_PAPER_COUNT]:
        sys.exit("không mạch nào đủ câu cho một đề chuyên đề")

    print(f"2. {args.teachers} giáo viên")
    teachers = make_teachers(admin, args.teachers)
    sessions = []
    for t in teachers:
        s = Api(ip=f"10.1.0.{len(sessions) + 1}")
        s.login(org, t["username"], SEED_PASSWORD)
        sessions.append(s)

    # two khối so that the "Khối" grouping and the structure screen have something to group; the content is THPT
    # maths, so 11 and 12 are the honest choice and 10 would not be
    twelves = max(1, args.classes - 2)
    names = ([(f"12A{i}", 12) for i in range(1, twelves + 1)] +
             [(f"11A{i}", 11) for i in range(1, args.classes - twelves + 1)])[: args.classes]
    print(f"3. {len(names)} lớp: {', '.join(n for n, _ in names)}")
    classes = make_classes(admin, names, grades)

    print(f"4. {args.students} học sinh mỗi lớp")
    known = {u["username"]: u for u in page(admin, "/users/search", {})}
    roster: dict[str, list[dict]] = {}
    for i, k in enumerate(classes):
        roster[k["id"]] = make_students(admin, k, args.students, 1 + i * args.students, known)
        print(f"   {k['name']}: {len(roster[k['id']])}")

    print("5. đề và bài giao")
    plan: list[tuple[dict, dict]] = []   # (assignment, class)
    wide = [t for t, n in strands if n >= TOPIC_PAPER_COUNT]
    for ci, k in enumerate(classes):
        teacher = sessions[ci % len(sessions)]
        for j in range(args.papers):
            exam = trial_paper(teacher, f"Thi thử {k['name']} lần {j + 1}", subject["id"], strands,
                               args.seed + ci * 100 + j)
            plan.append((assign(teacher, exam, k, days_ago=14 - j * 4), k))
        for j in range(args.topic_papers):
            strand = wide[(ci + j) % len(wide)]
            exam = topic_paper(teacher, f"Chuyên đề {strand['name']} · {k['name']}", subject["id"], strand,
                               args.seed + 500 + ci * 100 + j)
            plan.append((assign(teacher, exam, k, days_ago=10 - j * 3, minutes=45), k))
        print(f"   {k['name']}: {args.papers} thi thử + {args.topic_papers} chuyên đề")

    print("6. đọc đáp án của ngân hàng (để biết trước đúng/sai)")
    bank = page(admin, "/questions/search", {"status": "usable"})
    keys = {q["id"]: q["answer"] for q in bank}
    topic_of = {q["id"]: (next((t["name"] for t in q.get("topics") or [] if t.get("is_primary")), "")) for q in bank}
    strand_names = [t["name"] for t, _ in strands]

    print(f"7. {sum(len(roster[k['id']]) for k in classes)} học sinh làm bài")
    done, failed = 0, 0
    for k in classes:
        todo = [a for a, kk in plan if kk["id"] == k["id"]]
        for s in roster[k["id"]]:
            ability = min(0.95, max(0.15, rng.gauss(0.58, 0.16)))
            offset = {n: rng.gauss(0, 0.13) for n in strand_names}
            sess = Api(ip=f"10.2.{(done // 250) % 250}.{done % 250 + 1}")
            sess.login(org, s["username"], SEED_PASSWORD)
            for a in todo:
                if sit(sess, a["id"], keys, topic_of, ability, offset, rng) is None:
                    failed += 1
                else:
                    done += 1
            print(f"   {done} lượt nộp · {round(time.monotonic() - began)}s", end="\r", flush=True)
    print(f"\n   {done} lượt nộp" + (f" · {failed} lượt không mở được" if failed else ""))

    print(f"\nxong trong {round(time.monotonic() - began)}s")
    self_check(admin, org)


if __name__ == "__main__":
    main()
