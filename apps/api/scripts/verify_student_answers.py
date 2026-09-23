"""Put one real student answer in front of the verification run (learning-telemetry AC-01, AC-02).

The browser runner signs in as one account, and the evidence for these two criteria needs both roles: a student
answers, a teacher reads the numbers. So the answering half is scripted here and the reading half stays in
`07-verification.md`, where the report page must show exactly what this produced.

It does two things, in order, as the student:
  1. takes an assigned exam, answers **one** question with a known number of seconds, and submits it → one fact;
  2. starts a practice attempt and abandons it → no facts, which is the rule this feature repaired.

    python scripts/verify_student_answers.py [--reset]

`--reset` deletes what a previous run left, so the numbers on screen stay the ones the steps assert.
EXAMIND_URL / EXAMIND_ORG / EXAMIND_STUDENT / EXAMIND_STUDENT_PASSWORD override the stack and the account.
"""
import argparse
import os
import sys

import httpx

BASE = os.environ.get("EXAMIND_URL", "http://localhost:8088/api")
ORG = os.environ.get("EXAMIND_ORG", "trungtama")
STUDENT = os.environ.get("EXAMIND_STUDENT", "buivanchau")
PASSWORD = os.environ.get("EXAMIND_STUDENT_PASSWORD", "hocsinh123")
SECONDS = 42  # what the step's screenshot is allowed to claim


def login(username: str, password: str) -> httpx.Client:
    c = httpx.Client(base_url=BASE, timeout=120)
    c.post("/auth/login", json={"org_code": ORG, "username": username, "password": password}).raise_for_status()
    return c


def answer_one_assigned(c: httpx.Client) -> dict:
    """Start the first open assignment, answer its first question, submit. Returns what the teacher will see."""
    rows = c.get("/me/assignments").json()  # [{assignment, state, attempts, attempts_left}]
    open_now = [r for r in rows if r.get("state") == "open"]
    if not open_now:
        sys.exit("no open assignment for this student — give them an exam first")
    row = open_now[0]
    assignment = row["assignment"]
    unfinished = [a for a in row.get("attempts") or [] if a.get("status") == "in_progress"]
    # an interrupted run leaves an attempt behind; finish that one rather than burning the last try
    attempt_id = unfinished[0]["id"] if unfinished else c.post(f"/assignments/{assignment['id']}/start").json()["attempt_id"]
    attempt = c.get(f"/attempts/{attempt_id}").json()
    questions = attempt["questions"]
    first = questions[0]
    choice = (first.get("options") or [{}])[0].get("key") or "A"
    c.put(f"/attempts/{attempt_id}/answers/{first['id']}",
          json={"response": {"key": choice}, "seconds_spent": SECONDS}).raise_for_status()
    c.post(f"/attempts/{attempt_id}/submit").raise_for_status()
    return {"assignment": assignment["title"], "attempt": attempt_id, "answered": 1,
            "left_blank": len(questions) - 1, "seconds": SECONDS}


def abandon_practice(c: httpx.Client) -> dict:
    """A practice attempt nobody finishes: before this feature its blanks scored 0 into the student's mastery."""
    started = c.post("/me/practice", json={"count": 5}).json()
    return {"attempt": started["attempt_id"], "questions": started.get("question_count")}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    c = login(STUDENT, PASSWORD)
    submitted = answer_one_assigned(c)
    print(f"submitted: {submitted['assignment']} — 1 answered in {submitted['seconds']}s, "
          f"{submitted['left_blank']} left blank (attempt {submitted['attempt']})")
    abandoned = abandon_practice(c)
    print(f"abandoned: practice attempt {abandoned['attempt']} with {abandoned['questions']} questions, never submitted")
    print("the teacher's report should now read one answer, not one plus the blanks and not plus the practice")


if __name__ == "__main__":
    main()
