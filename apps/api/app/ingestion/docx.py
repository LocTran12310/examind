"""Word (.docx) → line stream via Pandoc's JSON AST (exam-ingestion ADR-02, A-05).

Math becomes `$…$`, pictures become `![](asset:<id>)`, underline/bold/highlight are kept as
`[…]{.underline}` / `**…**` / `[…]{.mark}` so the splitter can read answers marked by formatting.
Auto-numbered lists are rendered with their labels (`A.`, `a)`, `12.`) because Word hides them in styles.
"""
import json
import os
import subprocess
import tempfile

from app.ingestion.assets import ImageStore
from app.ingestion.lines import Line

PANDOC_TIMEOUT = 120


class DocxError(Exception):
    pass


def extract_docx(data: bytes, store: ImageStore) -> tuple[list[Line], list[str]]:
    warnings: list[str] = []
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
        walker = _Walker(tmp, store, warnings)
        for block in ast["blocks"]:
            walker.block(block)
        return walker.lines, warnings


class _Walker:
    def __init__(self, base: str, store: ImageStore, warnings: list[str]):
        self.base, self.store, self.warnings = base, store, warnings
        self.lines: list[Line] = []
        self._cache: dict[str, str | None] = {}

    # ---------------------------------------------------------------- blocks
    def emit(self, text: str) -> None:
        for part in text.split("\n"):
            if part.strip():
                self.lines.append(Line(part.strip()))

    def block(self, b: dict, prefix: str = "") -> None:
        t, c = b["t"], b.get("c")
        if t in ("Para", "Plain"):
            self.emit(prefix + self.inlines(c))
        elif t == "Header":
            self.emit(prefix + self.inlines(c[2]))
        elif t == "LineBlock":
            for line in c:
                self.emit(self.inlines(line))
        elif t in ("BlockQuote",):
            for x in c:
                self.block(x)
        elif t == "Div":
            for x in c[1]:
                self.block(x)
        elif t == "Figure":
            for x in c[2]:
                self.block(x)
        elif t == "OrderedList":
            (start, style, delim), items = c[0], c[1]
            for i, item in enumerate(items):
                label = self._list_label(start + i, style["t"], delim["t"])
                for j, x in enumerate(item):
                    self.block(x, prefix=(label + " ") if j == 0 else "")
        elif t == "BulletList":
            for item in c:
                for x in item:
                    self.block(x)
        elif t == "Table":
            self.table(c)
        elif t in ("CodeBlock", "RawBlock"):
            self.emit(c[1] if isinstance(c, list) else "")
        # HorizontalRule, Null: nothing

    @staticmethod
    def _list_label(n: int, style: str, delim: str) -> str:
        if style == "UpperAlpha":
            body = chr(ord("A") + n - 1)
        elif style == "LowerAlpha":
            body = chr(ord("a") + n - 1)
        else:
            body = str(n)
        return body + (")" if delim in ("OneParen", "TwoParens") else ".")

    def table(self, c: list) -> None:
        head, bodies, foot = c[3], c[4], c[5]
        rows = list(head[1])
        for body in bodies:
            rows += body[2] + body[3]
        rows += foot[1]
        for row in rows:
            cells = row[1]
            texts = []
            simple = True
            for cell in cells:
                blocks = cell[4]
                if len(blocks) > 1 or any(b["t"] not in ("Para", "Plain") for b in blocks):
                    simple = False
                texts.append(" ".join(self.inlines(b["c"]) for b in blocks if b["t"] in ("Para", "Plain")))
            if simple:
                self.emit(" | ".join(t.strip() for t in texts))
            else:  # layout tables (options in a 2×2 grid, whole questions in cells): keep reading order
                for cell in cells:
                    for b in cell[4]:
                        self.block(b)

    # ---------------------------------------------------------------- inlines
    def inlines(self, xs: list) -> str:
        return "".join(self.inline(x) for x in xs)

    def inline(self, x: dict) -> str:
        t, c = x["t"], x.get("c")
        if t == "Str":
            return c
        if t in ("Space",):
            return " "
        if t == "SoftBreak":
            return " "
        if t == "LineBreak":
            return "\n"
        if t == "Math":
            kind, tex = c[0]["t"], c[1].strip()
            return f"$${tex}$$" if kind == "DisplayMath" else f"${tex}$"
        if t == "Strong":
            inner = self.inlines(c)
            return f"**{inner.strip()}**" if inner.strip() else inner
        if t == "Underline":
            inner = self.inlines(c)
            return f"[{inner.strip()}]{{.underline}}" if inner.strip() else inner
        if t == "Span":
            inner = self.inlines(c[1])
            return f"[{inner.strip()}]{{.mark}}" if "mark" in c[0][1] and inner.strip() else inner
        if t in ("Emph", "Strikeout", "SmallCaps"):
            return self.inlines(c)
        if t == "Superscript":
            return f"$^{{{self.inlines(c)}}}$"
        if t == "Subscript":
            return f"$_{{{self.inlines(c)}}}$"
        if t == "Quoted":
            q = '"' if c[0]["t"] == "DoubleQuote" else "'"
            return q + self.inlines(c[1]) + q
        if t == "Code":
            return c[1]
        if t == "Link":
            return self.inlines(c[1])
        if t == "Image":
            return self.image(c[2][0])
        if t == "Note":
            return ""
        if t == "RawInline":
            return ""
        if t == "Cite":
            return self.inlines(c[1])
        return ""

    def image(self, src: str) -> str:
        if src not in self._cache:
            path = src if os.path.isabs(src) else os.path.join(self.base, src)
            try:
                with open(path, "rb") as fh:
                    data = fh.read()
            except OSError:
                self.warnings.append(f"Không đọc được hình {os.path.basename(src)}")
                self._cache[src] = None
            else:
                self._cache[src] = self.store(data, None)
        asset_id = self._cache[src]
        return f"\n![](asset:{asset_id})\n" if asset_id else ""
