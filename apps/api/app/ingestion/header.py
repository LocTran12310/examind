"""What an exam header says about the file (official-exam-ingestion AC-09, ADR-05).

    SỞ GD&ĐT TP. HCM / TRƯỜNG THCS -THPT NGUYỄN KHUYẾN / ĐỀ THI THI THỬ TỐT NGHIỆP LẦN 1 /
    NĂM HỌC: 2024 - 2025 / MÔN: TOÁN / (Thời gian làm bài: 90 phút …)

`detect(texts)` reads the lines before the first PHẦN / Câu and returns only what it found.
`apply(db, doc, lines)` stores it in `doc.meta["detected"]` and fills the meta fields the uploader
left empty, so the questions created from the file inherit subject, grade, đợt, năm học and nguồn.
"""
from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session
from unidecode import unidecode

from app.ingestion.lines import Line, strip_markup

HEAD_LINES = 14
STOP_RE = re.compile(r"^(?:PHẦN|Phần)\s+[IV1-5]|^(?:Câu|CÂU)\s*\d|^\d{1,2}\s*[.)]\s", re.U)
KEEP_UPPER = {"THPT", "THCS", "TH", "GD", "ĐT", "GD&ĐT", "KHTN", "ĐH", "HCM", "TP", "KSCL", "PTDTNT", "GDTX", "I", "II", "III"}


def _title(s: str) -> str:
    """"TRƯỜNG THCS -THPT NGUYỄN KHUYẾN" → "Trường THCS-THPT Nguyễn Khuyến" (acronyms stay upper)."""
    def word(w: str) -> str:
        bare = w.strip(".,()")
        return w if bare.upper() in KEEP_UPPER or not bare.isupper() else w[:1] + w[1:].lower()

    s = re.sub(r"\s+-(?=\S)", "-", s)
    return " ".join("-".join(word(p) for p in w.split("-")) for w in s.split())


def _clean(line: str) -> str:
    t = strip_markup(line).replace("­", "")
    return re.sub(r"\s+", " ", t).strip(" *\t")


def detect(texts: list[str]) -> dict:
    head: list[str] = []
    for raw in texts[:40]:
        t = _clean(raw)
        if not t:
            continue
        if STOP_RE.match(t):
            break
        head.append(t)
        if len(head) >= HEAD_LINES:
            break
    joined = " \n ".join(head)
    up = joined.upper()
    out: dict = {}

    so = next((i for i, t in enumerate(head) if re.match(r"^SỞ\s", t.upper())), None)
    school = next((i for i, t in enumerate(head) if re.match(r"^(?:TRƯỜNG|THPT|THCS|KHỐI\s+THPT)\b", t.upper())), None)
    if so is not None:
        prov = re.sub(r"^SỞ\s+(?:GIÁO\s+DỤC\s*(?:VÀ|&)\s*ĐÀO\s+TẠO|GD\s*(?:&|-|VÀ)?\s*ĐT)\s*", "", head[so], flags=re.I)
        prov = re.sub(r"^(?:TỈNH|THÀNH\s+PHỐ)\s+", "", prov.strip(), flags=re.I).strip(" .")
        if not prov and so + 1 < len(head) and head[so + 1].isupper() and len(head[so + 1]) <= 30 and not re.search(r"ĐỀ|TRƯỜNG|KÌ|KỲ", head[so + 1]):
            prov = head[so + 1]  # "SỞ GIÁO DỤC VÀ ĐÀO TẠO" / "YÊN BÁI"
        prov = re.sub(r"^TP\.?\s*", "TP ", prov) if prov.upper().startswith("TP") else prov
        if prov:
            out["province"] = _title(prov)
    if school is not None:
        name = head[school]
        nxt = head[school + 1] if school + 1 < len(head) else ""
        if nxt and len(nxt) <= 20 and nxt.isupper() and not re.search(r"ĐỀ|KÌ|KỲ|NĂM|MÔN|MÃ", nxt):
            name += " " + nxt  # "TRƯỜNG THPT CHUYÊN" / "ĐH KHTN", "… THUẬN THÀNH" / "SỐ 1, SỐ 2"
        out["issuer"] = _title(name)
    elif out.get("province"):
        out["issuer"] = f"Sở GD&ĐT {out['province']}"

    if m := re.search(r"NĂM\s+HỌC\s*:?\s*(\d{4})\s*[-–]\s*(\d{4})", up):
        out["school_year"] = f"{m.group(1)}-{m.group(2)}"
    elif m := re.search(r"NĂM\s+(20\d{2})\b", up):
        y = int(m.group(1))
        out["school_year"] = f"{y - 1}-{y}"  # "THI THỬ TỐT NGHIỆP THPT … NĂM 2025"

    if m := re.search(r"(?:MÔN(?:\s+THI)?|BÀI\s+THI)\s*:?\s*([A-ZÀ-Ỹ][A-ZÀ-Ỹ ]*?)(?=\s*(?:[-,–(]|LỚP|\d|\n|$))", up):
        out["subject_name"] = m.group(1).strip().capitalize()

    if m := re.search(r"(?:LỚP|KHỐI)\s*:?\s*(\d{1,2})\b", up) or re.search(r"MÔN(?:\s+THI)?\s*:?\s*[A-ZÀ-Ỹ ]+?\s(\d{1,2})\b", up):
        out["grade"] = int(m.group(1))
    elif "TỐT NGHIỆP" in up:
        out["grade"] = 12

    if "THI THỬ" in up:
        out["exam_kind"] = "Thi thử"
    elif re.search(r"GIỮA\s+(?:HỌC\s+)?K[ỲÌ]", up):
        out["exam_kind"] = "Giữa kỳ"
    elif re.search(r"CUỐI\s+(?:HỌC\s+)?K[ỲÌ]", up):
        out["exam_kind"] = "Cuối kỳ"
    elif re.search(r"KHẢO\s+SÁT|KSCL|KIỂM\s+TRA\s+CHẤT\s+L", up):
        out["exam_kind"] = "Khảo sát"
    elif "TỐT NGHIỆP" in up:
        out["exam_kind"] = "Thi thử"
    if m := re.search(r"LẦN\s*(\d{1,2})\b", up):
        out["attempt"] = int(m.group(1))
    if m := re.search(r"(\d{2,3})\s*PHÚT", up):
        out["duration"] = int(m.group(1))
    return out


def _subject_id(db: Session, org_id, name: str) -> str | None:
    from app.models import Subject

    want = unidecode(name).lower().strip()
    for s in db.scalars(select(Subject).where(Subject.organization_id == org_id)):
        if unidecode(s.name).lower().strip() == want or unidecode(s.code).lower() == want:
            return str(s.id)
    return None


def apply(db: Session, doc, lines: list[Line]) -> dict:
    """Store detected header values and fill empty meta fields; returns the detected dict."""
    found = detect([l.text for l in lines])
    if not found:
        return found
    meta = dict(doc.meta or {})
    meta["detected"] = found
    if not meta.get("subject_id") and found.get("subject_name"):
        sid = _subject_id(db, doc.organization_id, found["subject_name"])
        if sid:
            meta["subject_id"] = sid
    if meta.get("grade") in (None, "") and found.get("grade") and 1 <= found["grade"] <= 12:
        meta["grade"] = found["grade"]
    if not meta.get("exam_kind") and found.get("exam_kind"):
        meta["exam_kind"] = found["exam_kind"]
    if not meta.get("school_year") and found.get("school_year"):
        meta["school_year"] = found["school_year"]
    if not meta.get("source_name") and found.get("issuer"):
        meta["source_name"] = found["issuer"][:100]
    doc.meta = meta
    return found

