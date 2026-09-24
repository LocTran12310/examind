"""Remove what an end-to-end teaching-loop walk left on the real organisation.

The walk writes to `trungtama`, and most of what it writes the product can take back: the exam, the assignment,
the class, the questions, the four sandbox accounts. One thing it cannot — a submitted attempt. The product
refuses to delete an assignment that has been sat (`DeleteAssignmentHandler`), and offers no way to delete an
attempt at all, by design: a real answer is not something a teacher should be able to erase.

So this script does everything the API can do, and for the attempts it prints the one statement that removes
them — `answer_facts.attempt_id` is ON DELETE CASCADE, so the facts go with them — and runs it only when you
pass --yes. Deleting rows from a live database is the owner's decision, not a script's default.

    python3 scripts/e2e_teardown.py            # say what would go, delete nothing that needs SQL
    python3 scripts/e2e_teardown.py --yes      # also delete the attempts, then rebuild mastery

Run it between two walks: a second walk on an uncleaned organisation makes a second exam of the same name.
"""
import argparse
import subprocess
import sys

sys.path.insert(0, __import__("os").path.dirname(__file__))
from e2e_fixture import CLASS_NAME, PREFIX, STUDENTS, TOPIC_NAME, Api, credentials, one  # noqa: E402

EXAM_TITLE = f"{PREFIX} · vòng dạy học"
ATTEMPT_SQL = """delete from attempts a
 using assignments s, exams e
 where a.assignment_id = s.id and s.exam_id = e.id
   and e.organization_id = '{org}' and e.title = '{title}'"""


def psql(sql: str) -> str:
    out = subprocess.run(["docker", "compose", "exec", "-T", "postgres", "psql", "-U", "examind", "-d", "examind",
                          "-tAc", sql], capture_output=True, text=True)
    if out.returncode:
        raise SystemExit(f"psql: {out.stderr.strip()[:300]}")
    return out.stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--yes", action="store_true", help="also delete the submitted attempts (SQL, irreversible)")
    args = parser.parse_args()
    env = credentials()
    api = Api((env.get("LOCAL_URL") or "http://localhost:8088") + "/api")
    api("POST", "/auth/login", {"org_code": env.get("LOCAL_ORG", "trungtama"),
                                "username": env.get("LOCAL_USER"), "password": env.get("LOCAL_PASSWORD")})
    org = api("GET", "/auth/me")["org"]["id"]

    exams = [e for e in api("POST", "/exams/search", {"page": 1, "limit": 200})["data"] if e["title"] == EXAM_TITLE]
    if any(not e["title"].startswith(PREFIX) for e in exams):      # belt and braces: nothing without the prefix
        raise SystemExit("từ chối: có đề không mang tiền tố E2E trong danh sách sẽ xoá")
    attempts = int(psql(f"select count(*) from attempts a join assignments s on s.id = a.assignment_id "
                        f"join exams e on e.id = s.exam_id where e.organization_id = '{org}' "
                        f"and e.title = '{EXAM_TITLE}'") or 0)
    print(f"đề    : {len(exams)} · bài làm đã nộp: {attempts}")

    if attempts:
        sql = ATTEMPT_SQL.format(org=org, title=EXAM_TITLE)
        if not args.yes:
            print("\nCòn bài làm. Xoá chúng là thao tác không hoàn lại được và phải do anh quyết — chạy lại với --yes,")
            print("hoặc tự chạy câu này:\n")
            print(f"  {sql}\n")
            print("(answer_facts đi theo attempt vì khoá ngoại là ON DELETE CASCADE)")
            return
        print(f"\nxoá bài làm:\n  {sql}")
        psql(sql)
        left = psql(f"select count(*) from attempts a join assignments s on s.id = a.assignment_id "
                    f"join exams e on e.id = s.exam_id where e.organization_id = '{org}' and e.title = '{EXAM_TITLE}'")
        print(f"  → còn {left} bài")

    # Filtering happens here, on ids this script itself resolved from the title — never by a key handed to a
    # search endpoint. `/assignments/search` has no `exam_id` filter and silently ignores one, so asking it for
    # "the assignments of my exam" answers with every assignment of the organisation. This script very nearly
    # deleted the owner's own assignments that way; a refusal from the API was the only thing that stopped it.
    mine = {e["id"] for e in exams}
    assignments = [a for a in api("POST", "/assignments/search", {"page": 1, "limit": 200})["data"]
                   if a["exam_id"] in mine]
    for a in assignments:
        api("DELETE", f"/assignments/{a['id']}")
    for exam in exams:
        api("DELETE", f"/exams/{exam['id']}")
    print(f"đã xoá {len(exams)} đề và {len(assignments)} bài giao của chúng")

    topic = one(api("GET", "/topics"), TOPIC_NAME)
    if topic:
        for q in api("POST", "/questions/search", {"page": 1, "limit": 100, "topic_id": topic["id"], "status": "all"})["data"]:
            api("DELETE", f"/questions/{q['id']}")
        api("DELETE", f"/topics/{topic['id']}")
        print("đã xoá chuyên đề thử và các câu hỏi của nó")

    klass = one(api("POST", "/classes/search", {"page": 1, "limit": 200})["data"], CLASS_NAME)
    if klass:
        api("DELETE", f"/classes/{klass['id']}")
        print("đã xoá lớp thử")

    # The four accounts stay. `DELETE /users/{id}/membership` refuses a user's home organisation — an account
    # cannot be orphaned — and the product has no other way to remove one, deliberately: a person who has
    # answered questions is not something a script should be able to erase. Deactivating is the honest end:
    # they keep their history, disappear from the pickers, and cannot sign in again.
    users = api("POST", "/users/search", {"page": 1, "limit": 500})["data"]
    off = 0
    for username, _ in STUDENTS:
        found = one(users, username, "username")
        if found and found.get("is_active", True):
            api("PATCH", f"/users/{found['id']}", {"is_active": False})
            off += 1
    print(f"đã vô hiệu hoá {off} tài khoản thử (không xoá được: đây là tổ chức gốc của chúng)")

    if attempts and args.yes:
        r = api("POST", "/analytics/mastery/rebuild", {})
        print(f"dựng lại mastery: {r}")


if __name__ == "__main__":
    main()
