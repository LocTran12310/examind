"""Golden set: the rule-based pipeline on the bundled samples (exam-ingestion success signal)."""
import json
import os
import time

import pytest

from tests.test_documents_api import EXAMS, run_jobs, sample, teacher_with_taxonomy, upload


def exact(q, t):
    return q["type"] == t["type"] and q["answer"] == t["answer"] and len(q["options"]) == t["n_options"]


@pytest.mark.parametrize("name,min_ratio", [("de-mau-toan10", 0.95), ("de-thpt2025-toan", 0.95)])
def test_golden_docx(client, db, name, min_ratio):
    teacher_with_taxonomy(client, db)
    doc_id = upload(client, f"{name}.docx", sample(f"{name}.docx")).json()["document"]["id"]
    t0 = time.monotonic()
    run_jobs()
    elapsed = time.monotonic() - t0
    truth = json.load(open(os.path.join(EXAMS, f"{name}.expected.json"), encoding="utf-8"))["questions"]
    got = {(q["part"], q["number"]): q for q in client.get(f"/api/documents/{doc_id}/questions").json()}
    ok = sum(1 for t in truth if (t["part"], t["number"]) in got and exact(got[(t["part"], t["number"])], t))
    assert ok / len(truth) >= min_ratio, f"{ok}/{len(truth)}"
    assert elapsed < 60
    well_formed = [q for q in got.values() if q["confidence"] >= 0.85]
    assert len(well_formed) / len(got) >= 0.85
    if name == "de-mau-toan10":
        q5, q8, q12 = got[(None, 5)], got[(None, 8)], got[(None, 12)]
        assert "asset:" in q5["options"][2]["content"]
        assert "asset:" in q8["stem"]
        assert "asset:" in q12["solution"]
        assert all(q["solution"] for q in got.values())
