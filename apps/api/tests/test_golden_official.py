"""Reference set: the 18 official THPT 2025 files (official-exam-ingestion AC-08, A-01, A-08).

The files stay outside the repo. Set EXAMIN_DIR to the folder holding them (scripts/verify.sh
mounts it); files are matched by SHA-256, so names and sub-folders do not matter.
"""
import hashlib
import json
import os
from pathlib import Path

import pytest

from app.modules.ingestion.infrastructure.image_store import document_store
from app.modules.ingestion.infrastructure.adapters.pandoc import extract_docx
from app.modules.ingestion.domain.services.splitter import split
from app.shared.domain.answers import same_short_answer
from tests.factories import make_org

EXPECTED = json.loads((Path(__file__).parent / "golden" / "official_expected.json").read_text(encoding="utf-8"))["documents"]
ROOT = os.environ.get("EXAMIN_DIR")
pytestmark = pytest.mark.skipif(not ROOT or not Path(ROOT).is_dir(), reason="EXAMIN_DIR not set")


def _files() -> dict[str, Path]:
    found = {}
    for p in Path(ROOT).rglob("*.docx"):
        if not p.name.startswith("~$"):
            found[hashlib.sha256(p.read_bytes()).hexdigest()] = p
    return found


def _same(qtype: str, got, want) -> bool:
    if want is None or got is None:
        return got == want
    if qtype == "short_answer":
        return same_short_answer(str(want.get("value", "")), str(got.get("value", "")))
    return got == want


def test_reference_files(db):
    files = _files()
    org = make_org(db)
    totals = dict(expected=0, found=0, answers=0, with_answer=0, solutions=0, want_solutions=0, pictures_lost=0)
    for doc in EXPECTED:
        path = files.get(doc["sha256"])
        assert path, f"missing reference file: {doc['file']}"
        warnings, stats = [], {}
        lines, extract_warnings = extract_docx(path.read_bytes(), document_store(db, org.id, None, warnings, stats), stats)
        got = {(q.part, q.number): q for q in split(lines).questions}
        totals["pictures_lost"] += stats.get("vector_failed", 0) + len(warnings)
        assert stats.get("equations_failed", 0) <= 1, (doc["file"], stats)
        for want in doc["questions"]:
            totals["expected"] += 1
            q = got.get((want["part"], want["number"]))
            if q is None:
                continue
            totals["found"] += 1
            if want["answer"] is not None:
                totals["with_answer"] += 1
                totals["answers"] += _same(want["type"], q.answer, want["answer"]) and q.type == want["type"]
            if want["has_solution"]:
                totals["want_solutions"] += 1
                totals["solutions"] += bool(q.solution)
    print("official reference set:", totals)
    assert totals["expected"] == totals["found"] == 396
    assert totals["answers"] / totals["expected"] >= 0.98
    assert totals["answers"] == totals["with_answer"]
    assert totals["solutions"] == totals["want_solutions"]
    assert totals["pictures_lost"] == 0
