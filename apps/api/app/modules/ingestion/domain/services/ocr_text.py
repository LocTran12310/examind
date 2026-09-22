"""Tesseract TSV output → lines with a confidence per line (exam-ingestion ADR-05)."""
import csv
import io

from app.modules.ingestion.domain.services.lines import Line


def parse_tsv(tsv: str, page: int) -> list[Line]:
    lines: dict[tuple, list[tuple[str, float]]] = {}
    order: list[tuple] = []
    for row in csv.DictReader(io.StringIO(tsv), delimiter="\t", quoting=csv.QUOTE_NONE):
        if row.get("level") != "5" or not (row.get("text") or "").strip():
            continue
        key = (row["block_num"], row["par_num"], row["line_num"])
        if key not in lines:
            lines[key] = []
            order.append(key)
        lines[key].append((row["text"], max(0.0, float(row["conf"] or 0))))
    out = []
    for key in order:
        words = lines[key]
        text = " ".join(w for w, _ in words).strip()
        conf = sum(c for _, c in words) / len(words) / 100
        out.append(Line(text, page, ocr=True, confidence=round(conf, 2)))
    return out
