import json
import os
import zipfile

import pytest

EXAMS = os.path.join(os.path.dirname(__file__), "..", "..", "..", "samples", "exams")


@pytest.mark.parametrize("name,n", [("de-mau-toan10", 40), ("de-thpt2025-toan", 22), ("de-kho", 8)])
def test_sample_docx_is_valid_with_omml_and_truth(name, n):
    with zipfile.ZipFile(os.path.join(EXAMS, f"{name}.docx")) as z:
        xml = z.read("word/document.xml").decode()
        assert "<m:oMath" in xml  # equations are real Word equations (OMML)
        if name == "de-mau-toan10":
            assert len([f for f in z.namelist() if f.startswith("word/media/")]) == 3
    truth = json.load(open(os.path.join(EXAMS, f"{name}.expected.json"), encoding="utf-8"))
    assert len(truth["questions"]) == n
