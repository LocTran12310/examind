"""Build the sandbox the end-to-end teaching-loop walk runs in, inside the real organisation.

The walk needs several students actually sitting an exam, and that cannot be faked: the browser signs each one
in. The organisation's own students are not usable for it — all but one have never logged in
(`must_change_password`), so driving them would mean changing real children's passwords, and their mastery would
carry answers a machine invented. So the walk gets its own class, its own students and its own questions, all
named `E2E`, inside `trungtama` where the screens and the reports are the real ones.

    python3 scripts/e2e_fixture.py            # build (idempotent), print the answer key and the credentials
    python3 scripts/e2e_fixture.py --show     # print what already exists, build nothing

Everything it creates is removed again by scripts/e2e_teardown.py. It reads .ai/credentials.env for the admin
account and the URL, and writes nothing to disk.
"""
import argparse
import datetime
import json
import os
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREFIX = "E2E"
CLASS_NAME = f"{PREFIX} · lớp thử"
TOPIC_NAME = f"{PREFIX} · chuyên đề thử"
EXAM_TITLE = f"{PREFIX} · vòng dạy học"      # the walk builds this one through the screens
PAPER_TITLE = f"{PREFIX} · bài mẫu"          # --with-exam: a paper already sitting in the class, for specs that need one
STUDENT_PASSWORD = "E2eHocSinh!2026"
STUDENTS = [("e2e.hs01", "E2E Học sinh 01"), ("e2e.hs02", "E2E Học sinh 02"),
            ("e2e.hs03", "E2E Học sinh 03"), ("e2e.hs04", "E2E Học sinh 04")]

# The paper's shape is the THPT 2025 one: four multiple-choice, three true/false of four statements each (the
# 0.1 / 0.25 / 0.5 / 1.0 partial credit only applies at four), three short answers.
#
# Every question of a type carries the SAME key on purpose, and it is what makes the walk possible at all: the
# exam is built from a matrix, and the matrix picks questions out of the topic in an order nothing promises, so
# "the question at position 3" is not the same question twice. With one key per type, a student's answers are
# right or wrong regardless of which question landed where, and the walk can still say exactly who scores what.
# The cost is a paper whose key reads A-A-A-A; these ten questions exist for nothing else.
QUESTIONS = [
    {"type": "mcq", "stem": "Đạo hàm của hàm số $f(x)=x^2$ là:",
     "options": [{"label": "A", "content": "$2x$"}, {"label": "B", "content": "$x$"},
                 {"label": "C", "content": "$x^2$"}, {"label": "D", "content": "$2$"}]},
    {"type": "mcq", "stem": "Nghiệm của phương trình $2x-6=0$ là:",
     "options": [{"label": "A", "content": "$x=3$"}, {"label": "B", "content": "$x=2$"},
                 {"label": "C", "content": "$x=-3$"}, {"label": "D", "content": "$x=6$"}]},
    {"type": "mcq", "stem": "Tập xác định của hàm số $y=\\sqrt{x-1}$ là:",
     "options": [{"label": "A", "content": "$[1;+\\infty)$"}, {"label": "B", "content": "$\\mathbb{R}$"},
                 {"label": "C", "content": "$(-\\infty;1]$"}, {"label": "D", "content": "$(1;+\\infty)$"}]},
    {"type": "mcq", "stem": "Giá trị của $\\log_2 8$ bằng:",
     "options": [{"label": "A", "content": "$3$"}, {"label": "B", "content": "$4$"},
                 {"label": "C", "content": "$6$"}, {"label": "D", "content": "$2$"}]},
    {"type": "true_false", "stem": "Cho hàm số $f(x)=x^3-3x$. Xét tính đúng sai của các mệnh đề:",
     "options": [{"label": "a", "content": "$f\'(x)=3x^2-3$"}, {"label": "b", "content": "$f$ có hai điểm cực trị"},
                 {"label": "c", "content": "$f$ đồng biến trên $\\mathbb{R}$"}, {"label": "d", "content": "$f(0)=0$"}]},
    {"type": "true_false", "stem": "Cho tam giác $ABC$ vuông tại $A$. Xét tính đúng sai:",
     "options": [{"label": "a", "content": "$AB^2+AC^2=BC^2$"}, {"label": "b", "content": "$\\widehat{B}+\\widehat{C}=90^\\circ$"},
                 {"label": "c", "content": "$BC$ là cạnh nhỏ nhất"}, {"label": "d", "content": "$\\sin B=\\dfrac{AC}{BC}$"}]},
    {"type": "true_false", "stem": "Cho dãy số $u_n=2n+1$. Xét tính đúng sai:",
     "options": [{"label": "a", "content": "$u_1=3$"}, {"label": "b", "content": "Dãy là cấp số cộng công sai $2$"},
                 {"label": "c", "content": "$u_5=10$"}, {"label": "d", "content": "Dãy tăng"}]},
    {"type": "short_answer", "stem": "Tính $\\int_0^1 10x\\,dx$."},
    {"type": "short_answer", "stem": "Cho $f(x)=2x+1$. Tính $f(2)$."},
    {"type": "short_answer", "stem": "Số đường chéo của một ngũ giác lồi là bao nhiêu?"},
]
#: one key per type — see the note above
KEY = {"mcq": {"key": "A"}, "true_false": {"a": True, "b": True, "c": False, "d": True},
       "short_answer": {"value": "5"}}


def credentials() -> dict:
    out = {}
    path = os.path.join(ROOT, ".ai", "credentials.env")
    for line in open(path, encoding="utf-8") if os.path.exists(path) else []:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            out[key.strip()] = value.strip()
    return out


class Api:
    """The organisation's own API, as a staff member uses it. Cookies are kept the way the browser keeps them."""

    def __init__(self, base: str):
        self.base = base.rstrip("/")
        self.jar = {}

    def __call__(self, method: str, path: str, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(f"{self.base}{path}", data=data, method=method)
        req.add_header("content-type", "application/json")
        if self.jar:
            req.add_header("cookie", "; ".join(f"{k}={v}" for k, v in self.jar.items()))
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                for header in r.headers.get_all("set-cookie") or []:
                    name, _, rest = header.partition("=")
                    self.jar[name] = rest.split(";")[0]
                raw = r.read().decode()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            raise SystemExit(f"{method} {path} → {e.code}: {e.read().decode()[:300]}") from None


def one(rows: list, name: str, key: str = "name"):
    return next((r for r in rows if r.get(key) == name), None)


def build(api: Api, show: bool, reset: bool, with_exam: bool = False) -> dict:
    subject = one(api("GET", "/taxonomy")["subjects"], "Toán")
    topics = api("GET", f"/topics?subject_id={subject['id']}")
    topic = one(topics, TOPIC_NAME)
    if topic is None and not show:
        topic = api("POST", "/topics", {"name": TOPIC_NAME, "subject_id": subject["id"]})

    classes = api("POST", "/classes/search", {"page": 1, "limit": 200})["data"]
    klass = one(classes, CLASS_NAME)
    if klass is None and not show:
        grades = api("POST", "/grades/search", {"page": 1, "limit": 50})["data"]
        grade = one(grades, "Lớp 12") or grades[0]
        klass = api("POST", "/classes", {"name": CLASS_NAME, "grade_id": grade["id"]})

    users = api("POST", "/users/search", {"page": 1, "limit": 500})["data"]
    students, made = [], []
    for username, full_name in STUDENTS:
        found = one(users, username, "username")
        if found is None and not show:
            # an explicit password is the point: without one the account is created with must_change_password,
            # and the browser would be bounced to /change-password before it ever reached the exam
            found = api("POST", "/users", {"full_name": full_name, "username": username,
                                           "role": "student", "password": STUDENT_PASSWORD})["user"]
            made.append(username)
        if found and not found.get("is_active", True) and not show:
            api("PATCH", f"/users/{found['id']}", {"is_active": True})   # the teardown deactivates rather than deletes
            found = {**found, "is_active": True}
        if found:
            students.append(found)
    if students and klass and not show:
        api("POST", f"/classes/{klass['id']}/members", {"user_ids": [s["id"] for s in students]})

    made_questions = []
    if topic and not show:
        have = api("POST", "/questions/search", {"page": 1, "limit": 100, "topic_id": topic["id"], "status": "all"})
        if reset:
            for q in have["data"]:
                api("DELETE", f"/questions/{q['id']}")
            have = {"data": []}
        by_stem = {q["stem"]: q for q in have["data"]}
        for spec in QUESTIONS:
            found = by_stem.get(spec["stem"])
            if found is None:
                found = api("POST", "/questions", {**spec, "answer": KEY[spec["type"]], "subject_id": subject["id"],
                                                   "grade": 12, "difficulty": "th", "primary_topic_id": topic["id"]})
            made_questions.append(found)

    exam = assignment = None
    if with_exam and made_questions and klass and not show:
        exam, assignment = _paper(api, klass, made_questions, subject)
    return {"subject": subject, "topic": topic, "class": klass, "students": students,
            "questions": made_questions, "created_students": made, "exam": exam, "assignment": assignment}


def _paper(api: Api, klass: dict, questions: list, subject: dict) -> tuple[dict, dict]:
    """An exam of the ten questions, already given to the test class. The end-to-end walk builds its own paper
    through the screens on purpose, so this one carries a **different title**: two exams of the same name in one
    organisation make every `click td:has-text(...)` and every `[data-testid="open-<title>"]` ambiguous, and the
    step picks whichever came first rather than the one it means."""
    exam = one(api("POST", "/exams/search", {"page": 1, "limit": 200})["data"], PAPER_TITLE, "title")
    if exam is None:
        # the subject is part of the fixture, not decoration: what a student sees grouped by subject comes from
        # exams.subject_id, so a paper without one would exercise the null branch and nothing else
        exam = api("POST", "/exams", {"title": PAPER_TITLE, "subject_id": subject["id"]})
        api("POST", f"/exams/{exam['id']}/questions", {"question_ids": [q["id"] for q in questions]})
        exam = api("GET", f"/exams/{exam['id']}")
    elif not exam.get("subject_id"):
        exam = api("PATCH", f"/exams/{exam['id']}", {"subject_id": subject["id"]}) or exam
    assignment = one(api("POST", "/assignments/search", {"page": 1, "limit": 200})["data"], PAPER_TITLE, "title")
    if assignment is None:
        opens = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
        assignment = api("POST", "/assignments", {
            "exam_id": exam["id"], "title": PAPER_TITLE, "class_ids": [klass["id"]],
            "open_at": opens.isoformat(), "close_at": (opens + datetime.timedelta(days=7)).isoformat(),
            "duration_minutes": 120, "max_attempts": 1,
            # deterministic labels: a verification step that clicks "phương án A" must mean the same A every run
            "shuffle_questions": False, "shuffle_options": False, "results_policy": "after_submit"})
    return exam, assignment


def report(state: dict) -> None:
    klass, topic = state["class"], state["topic"]
    print(f"lớp     : {CLASS_NAME} · {klass['id'] if klass else '(chưa có)'}")
    print(f"chuyên đề: {TOPIC_NAME} · {topic['id'] if topic else '(chưa có)'}")
    print(f"học sinh : {len(state['students'])}/{len(STUDENTS)}"
          + (f" (mới tạo: {', '.join(state['created_students'])})" if state["created_students"] else ""))
    print(f"câu hỏi  : {len(state['questions'])}/{len(QUESTIONS)}")
    if state["questions"]:
        print("\nđáp án — một khoá cho mỗi loại câu, nên đúng/sai không phụ thuộc câu nào rơi vào vị trí nào:")
        for qtype, key in KEY.items():
            count = sum(1 for s in QUESTIONS if s["type"] == qtype)
            print(f"  {qtype:<13} ×{count}  {json.dumps(key, ensure_ascii=False)}")
    if state.get("assignment"):
        print(f"bài giao  : {PAPER_TITLE} · {state['assignment']['id']}")
    print("\ndán vào .ai/credentials.env:")
    for username, _ in STUDENTS:
        print(f"  {username.replace('e2e.hs', 'E2E_HS').upper()}_USER={username}")
        print(f"  {username.replace('e2e.hs', 'E2E_HS').upper()}_PASSWORD={STUDENT_PASSWORD}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--show", action="store_true", help="print what exists, create nothing")
    parser.add_argument("--reset", action="store_true", help="delete the E2E questions and write them again")
    parser.add_argument("--with-exam", action="store_true", help="also create the exam and give it to the test class")
    args = parser.parse_args()
    env = credentials()
    api = Api((env.get("LOCAL_URL") or "http://localhost:8088") + "/api")
    api("POST", "/auth/login", {"org_code": env.get("LOCAL_ORG", "trungtama"),
                                "username": env.get("LOCAL_USER"), "password": env.get("LOCAL_PASSWORD")})
    report(build(api, args.show, args.reset, args.with_exam))
    if args.show:
        print("\n(--show: không tạo gì)", file=sys.stderr)


if __name__ == "__main__":
    main()
