"""Word (.docx) → line stream: MathType tokens swapped in, Pandoc run, AST walked (exam-ingestion ADR-02, A-05)."""
import json
import os
import subprocess
import tempfile

from app.modules.ingestion.domain.errors import DocxError
from app.modules.ingestion.domain.ports import ImageStore
from app.modules.ingestion.domain.services.docx_ast import inline_mathtype, lines_from_ast
from app.modules.ingestion.domain.services.lines import Line

PANDOC_TIMEOUT = 120


def _read(path: str) -> bytes:
    with open(path, "rb") as fh:
        return fh.read()


def extract_docx(data: bytes, store: ImageStore, stats: dict | None = None) -> tuple[list[Line], list[str]]:
    warnings: list[str] = []
    data, math, failed = inline_mathtype(data)
    if stats is not None:
        stats.update(equations=len(math), equations_failed=failed)
    if failed:
        warnings.append(f"{failed} công thức MathType không chuyển được sang LaTeX, giữ dạng hình")
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "in.docx")
        with open(src, "wb") as fh:
            fh.write(data)
        try:
            proc = subprocess.run(
                ["pandoc", "-f", "docx", "-t", "json", f"--extract-media={tmp}/media", src],
                capture_output=True, timeout=PANDOC_TIMEOUT, check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise DocxError("Pandoc quá thời gian khi đọc file Word") from exc
        if proc.returncode != 0:
            raise DocxError("Không đọc được file Word: " + proc.stderr.decode(errors="replace")[:300])
        ast = json.loads(proc.stdout)
        return lines_from_ast(ast, tmp, store, warnings, math, _read), warnings


class PandocDocxReader:
    """DocxReader port."""

    def read(self, data: bytes, store: ImageStore, stats: dict | None = None) -> tuple[list[Line], list[str]]:
        return extract_docx(data, store, stats)
