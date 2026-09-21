"""Success signal of question-review: flagged share and actions per flagged question on the golden docs."""
import json
import os

from tests.test_documents_api import EXAMS, run_jobs, sample, upload
from tests.test_review_api import setup_admin


def test_review_flow_on_golden_documents(client, db):
    setup_admin(client, db)
    total = flagged = actions = reviewed = 0
    for name in ("de-mau-toan10", "de-thpt2025-toan"):
        doc = upload(client, f"{name}.docx", sample(f"{name}.docx")).json()["document"]["id"]
        run_jobs()
        truth = {(t["part"], t["number"]): t for t in json.load(open(os.path.join(EXAMS, f"{name}.expected.json"), encoding="utf-8"))["questions"]}
        info = client.get(f"/api/review/documents/{doc}").json()
        total += info["total"]
        queue = client.get(f"/api/review/documents/{doc}/queue").json()
        flagged += info["counts"]["needs_review"]
        reviewed += len(queue)
        for q in queue:  # a teacher: fix the answer if wrong (1 key), then Enter
            want = truth[(q["part"], q["number"])]["answer"]
            if q["answer"] != want:
                client.patch(f"/api/questions/{q['id']}", json={"answer": want})
                actions += 1
            r = client.post(f"/api/review/questions/{q['id']}/action", json={"action": "approve"})
            assert r.status_code == 200, r.text
            actions += 1
        assert client.get(f"/api/review/documents/{doc}/queue").json() == []
    assert flagged / total <= 0.15, f"{flagged}/{total}"
    assert reviewed and actions / reviewed <= 2.0, (actions, reviewed)
