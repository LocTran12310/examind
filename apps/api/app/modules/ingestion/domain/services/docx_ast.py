"""Word (.docx) content → line stream, from Pandoc's JSON AST (exam-ingestion ADR-02, A-05). Pure: the Pandoc run and the
media files it extracts are handed in by the adapter (infrastructure/adapters/pandoc.py).

Math becomes `$…$`, pictures become `![](asset:<id>)`, underline/bold/highlight are kept as
`[…]{.underline}` / `**…**` / `[…]{.mark}` so the splitter can read answers marked by formatting.
Auto-numbered lists are rendered with their labels (`A.`, `a)`, `12.`) because Word hides them in styles.
MathType OLE equations are swapped for text tokens before Pandoc runs (`inline_mathtype`).
"""
from collections.abc import Callable
import io
import os
import re
import zipfile

from app.modules.ingestion.domain.ports import ImageStore
from app.modules.ingestion.domain.services import mtef
from app.modules.ingestion.domain.services.lines import Line

ReadMedia = Callable[[str], bytes]  # path of an extracted media file -> bytes (raises OSError)


def lines_from_ast(ast: dict, base: str, store: ImageStore, warnings: list[str], math: dict[str, str], read: ReadMedia) -> list[Line]:
    walker = _Walker(base, store, warnings, math, read)
    for block in ast["blocks"]:
        walker.block(block)
    return walker.lines


class _Walker:
    def __init__(self, base: str, store: ImageStore, warnings: list[str], math: dict[str, str] | None = None,
                 read: ReadMedia | None = None):
        self.base, self.store, self.warnings, self.read = base, store, warnings, read
        self.math = math or {}
        self.lines: list[Line] = []
        self._cache: dict[str, str | None] = {}

    # ---------------------------------------------------------------- blocks
    def emit(self, text: str) -> None:
        # a picture in a paragraph with words (formula pictures, small icons) stays in the line;
        # pictures on their own (figures) get a line each
        has_words = bool(_IMG.sub("", text).strip())
        text = _IMG.sub((lambda m: m.group(1)) if has_words else (lambda m: "\n" + m.group(1) + "\n"), text)
        text = _IMG_THEN_LABEL.sub(r"\1\n", text)  # "![](…) D. $0$": the next option starts a line
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
            return _TOKEN.sub(lambda m: f"${self.math[m.group(0)]}$" if m.group(0) in self.math else "", c) if "⟦" in c else c
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
        if t in ("Superscript", "Subscript"):
            inner = self.inlines(c)
            if "$" in inner or "![" in inner:
                return inner  # a formula or picture only raised/lowered for alignment: keep it as is
            return f"${'^' if t == 'Superscript' else '_'}{{{inner}}}$"
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
                data = self.read(path)
            except OSError:
                self.warnings.append(f"Không đọc được hình {os.path.basename(src)}")
                self._cache[src] = None
            else:
                self._cache[src] = self.store(data, None)
        asset_id = self._cache[src]
        return f"\x1e![](asset:{asset_id})\x1e" if asset_id else ""


_IMG = re.compile(r"\x1e(!\[\]\(asset:[^)]+\))\x1e")
_IMG_THEN_LABEL = re.compile(r"(!\[\]\(asset:[^)]+\))\s+(?=(?:\*\*)?\[?(?:[A-D][.)]|[a-d]\))\s)")

# ---------------------------------------------------------------- MathType
_TOKEN = re.compile(r"⟦EQ\d+⟧")
_OBJECT = re.compile(rb"<w:object\b.*?</w:object>", re.S)
_OLE_RID = re.compile(rb'<o:OLEObject\b[^>]*?ProgID="Equation\.(?:DSMT\d*|3)"[^>]*?\br:id="([^"]+)"|<o:OLEObject\b[^>]*?\br:id="([^"]+)"[^>]*?ProgID="Equation\.(?:DSMT\d*|3)"')
_REL = re.compile(rb'<Relationship\b[^>]*?\bId="([^"]+)"[^>]*?\bTarget="([^"]+)"|<Relationship\b[^>]*?\bTarget="([^"]+)"[^>]*?\bId="([^"]+)"')


def _latex(ole: bytes) -> str | None:
    data = mtef.mtef_from_ole(ole)
    if data is None:
        return None
    try:
        return mtef.mtef_to_latex(data)
    except mtef.MtefError:
        return None


def inline_mathtype(data: bytes) -> tuple[bytes, dict[str, str], int]:
    """Replace MathType OLE objects in the body by text tokens; returns (docx, token→LaTeX, failures).

    Pandoc only keeps the WMF preview of an OLE equation, so each object whose MTEF converts is
    swapped for a `⟦EQn⟧` run text before Pandoc runs; the walker turns tokens back into `$…$`.
    Objects that do not convert are left alone and still come out as pictures.
    """
    try:
        zin = zipfile.ZipFile(io.BytesIO(data))
        doc = zin.read("word/document.xml")
        rels_xml = zin.read("word/_rels/document.xml.rels")
    except (zipfile.BadZipFile, KeyError):
        return data, {}, 0
    if b"Equation." not in doc:
        return data, {}, 0
    rels = {}
    for m in _REL.finditer(rels_xml):
        rid, target = (m.group(1), m.group(2)) if m.group(1) else (m.group(4), m.group(3))
        rels[rid.decode()] = target.decode()
    math: dict[str, str] = {}
    failed = 0

    def swap(m: re.Match) -> bytes:
        nonlocal failed
        obj = m.group(0)
        ref = _OLE_RID.search(obj)
        if not ref:
            return obj
        target = rels.get((ref.group(1) or ref.group(2)).decode())
        try:
            ole = zin.read("word/" + target.lstrip("/").removeprefix("word/")) if target else None
        except KeyError:
            ole = None
        latex = _latex(ole) if ole else None
        if latex is None:
            failed += 1
            return obj
        if latex == "":
            return b""  # an empty formula object: nothing to show
        token = f"⟦EQ{len(math)}⟧"
        math[token] = latex
        return f'<w:t xml:space="preserve">{token}</w:t>'.encode()

    doc = _OBJECT.sub(swap, doc)
    if not math:
        return data, {}, failed
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            zout.writestr(item, doc if item.filename == "word/document.xml" else zin.read(item.filename))
    return out.getvalue(), math, failed
