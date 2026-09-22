"""MathType equations (MTEF v5 inside an OLE `Equation Native` stream) → LaTeX.

Official Vietnamese exam files (the Sở/THPT "thi thử" .docx) keep every formula as a MathType
OLE object with a WMF preview. Browsers cannot show WMF and Pandoc only keeps the preview, so the
equation is read from its binary form instead. Record layout follows the MathType SDK's
"MTEF v5" description; the template/embellishment numbering matches zhexiao/mtef-go (Apache-2.0).

`to_latex(ole_bytes)` returns the LaTeX (no `$`), or None when the object is not MTEF v5 or a
record is not understood — callers then keep the picture, so an unreadable formula is never lost.
"""
from __future__ import annotations

import io
import re
import struct
from dataclasses import dataclass, field

import olefile

# record tags
END, LINE, CHAR, TMPL, PILE, MATRIX, EMBELL, RULER, FONT_STYLE_DEF, SIZE = range(10)
FULL, SUB, SUB2, SYM, SUBSYM, COLOR, COLOR_DEF, FONT_DEF, EQN_PREFS, ENCODING_DEF = range(10, 20)
FUTURE = 100

OPT_NUDGE = 0x08
OPT_CHAR_EMBELL, OPT_CHAR_FUNC_START, OPT_CHAR_ENC_CHAR_8 = 0x01, 0x02, 0x04
OPT_CHAR_ENC_CHAR_16, OPT_CHAR_ENC_NO_MTCODE = 0x10, 0x20
OPT_LINE_NULL, OPT_LP_RULER, OPT_LINE_LSPACE = 0x01, 0x02, 0x04

# typeface styles (typeface byte − 128)
FN_TEXT, FN_FUNCTION, FN_VARIABLE, FN_LCGREEK, FN_UCGREEK, FN_SYMBOL, FN_VECTOR, FN_NUMBER = range(1, 9)
FN_MTEXTRA, FN_TEXT_FE, FN_EXPAND, FN_MARKER, FN_SPACE = 11, 12, 22, 23, 24


class MtefError(Exception):
    pass


@dataclass
class Char:
    code: int
    style: int
    func_start: bool = False
    embells: list[int] = field(default_factory=list)


@dataclass
class Line:
    items: list | None  # None = empty slot


@dataclass
class Tmpl:
    selector: int
    variation: int
    items: list


@dataclass
class Pile:
    halign: int
    lines: list


@dataclass
class Matrix:
    rows: int
    cols: int
    cells: list


# ------------------------------------------------------------------ reading
class _Reader:
    def __init__(self, data: bytes):
        self.b = io.BytesIO(data)

    def u8(self) -> int:
        c = self.b.read(1)
        if not c:
            raise MtefError("unexpected end of equation")
        return c[0]

    def u16(self) -> int:
        c = self.b.read(2)
        if len(c) < 2:
            raise MtefError("unexpected end of equation")
        return struct.unpack("<H", c)[0]

    def cstr(self) -> str:
        out = bytearray()
        while (c := self.u8()) != 0:
            out.append(c)
        return out.decode("latin-1")

    def skip(self, n: int) -> None:
        self.b.seek(n, io.SEEK_CUR)

    def nudge(self) -> None:
        dx, dy = self.u8(), self.u8()
        if dx == 128 and dy == 128:  # small nudges are one byte each
            self.skip(4)

    def dims(self, count: int) -> None:
        """Nibble-coded dimension arrays in EQN_PREFS: each value ends with a 0xF nibble."""
        seen = 0
        while seen < count:
            c = self.u8()
            for nib in (c >> 4, c & 0xF):
                if nib == 0xF:
                    seen += 1
                    if seen == count:
                        break


def _parse(data: bytes) -> list:
    r = _Reader(data)
    if r.u8() != 5:
        raise MtefError("not MTEF v5")
    r.skip(4)  # platform, product, version, sub-version
    r.cstr()  # application key, e.g. "DSMT6"
    r.u8()  # equation options
    items = _list(r, top=True)
    return items


def _list(r: _Reader, top: bool = False) -> list:
    """Objects until END (or end of data at the top level)."""
    out: list = []
    while True:
        try:
            tag = r.u8()
        except MtefError:
            if top:
                return out
            raise
        if tag == END:
            return out
        obj = _record(r, tag)
        if obj is not None:
            out.append(obj)


def _record(r: _Reader, tag: int):
    if tag == LINE:
        opt = r.u8()
        if opt & OPT_NUDGE:
            r.nudge()
        if opt & OPT_LINE_LSPACE:
            r.u16()
        if opt & OPT_LP_RULER:
            _ruler(r)
        return Line(None if opt & OPT_LINE_NULL else _list(r))
    if tag == CHAR:
        opt = r.u8()
        if opt & OPT_NUDGE:
            r.nudge()
        typeface = r.u8()
        code = 0
        if not opt & OPT_CHAR_ENC_NO_MTCODE:
            code = r.u16()
        if opt & OPT_CHAR_ENC_CHAR_8:
            pos = r.u8()
            code = code or pos
        if opt & OPT_CHAR_ENC_CHAR_16:
            pos = r.u16()
            code = code or pos
        ch = Char(code, typeface - 128, bool(opt & OPT_CHAR_FUNC_START))
        if opt & OPT_CHAR_EMBELL:
            ch.embells = [e for e in _list(r) if isinstance(e, int)]
        return ch
    if tag == TMPL:
        opt = r.u8()
        if opt & OPT_NUDGE:
            r.nudge()
        selector = r.u8()
        v = r.u8()
        if v & 0x80:
            v = (v & 0x7F) | (r.u8() << 8)
        r.u8()  # template-specific options
        return Tmpl(selector, v, _list(r))
    if tag == PILE:
        opt = r.u8()
        if opt & OPT_NUDGE:
            r.nudge()
        halign, _valign = r.u8(), r.u8()
        if opt & OPT_LP_RULER:
            _ruler(r)
        return Pile(halign, [x for x in _list(r) if isinstance(x, Line)])
    if tag == MATRIX:
        opt = r.u8()
        if opt & OPT_NUDGE:
            r.nudge()
        r.u8(), r.u8(), r.u8()  # valign, h_just, v_just
        rows, cols = r.u8(), r.u8()
        r.skip((2 * (rows + 1) + 7) // 8)  # row partition lines
        r.skip((2 * (cols + 1) + 7) // 8)  # column partition lines
        return Matrix(rows, cols, [x for x in _list(r) if isinstance(x, Line)])
    if tag == EMBELL:
        opt = r.u8()
        if opt & OPT_NUDGE:
            r.nudge()
        return r.u8()
    if tag == RULER:
        _ruler(r)
        return None
    if tag == FONT_STYLE_DEF:
        r.u8()
        r.u8()
        return None
    if tag == SIZE:
        lsize = r.u8()
        if lsize == 101:
            r.u16()
        elif lsize == 100:
            r.u8()
            r.u16()
        else:
            r.u8()
        return None
    if tag in (FULL, SUB, SUB2, SYM, SUBSYM):
        return None
    if tag == COLOR:
        r.u8()
        return None
    if tag == COLOR_DEF:
        opt = r.u8()
        r.skip(8 if opt & 0x01 else 6)
        if opt & 0x04:
            r.cstr()
        return None
    if tag == FONT_DEF:
        r.u8()
        r.cstr()
        return None
    if tag == EQN_PREFS:
        r.u8()
        r.dims(r.u8())  # sizes
        r.dims(r.u8())  # spaces
        for _ in range(r.u8()):  # styles
            if r.u8():
                r.u8()
        return None
    if tag == ENCODING_DEF:
        r.cstr()
        return None
    if tag >= FUTURE:  # MathType 7 adds e.g. "TeX Input Language"; a one-byte length follows
        r.skip(r.u8())
        return None
    raise MtefError(f"unknown record {tag}")


def _ruler(r: _Reader) -> None:
    for _ in range(r.u8()):
        r.u8()
        r.u16()


# ------------------------------------------------------------------ LaTeX
SYMBOLS = {
    0x2212: "-", 0x00B1: r"\pm ", 0x2213: r"\mp ", 0x00D7: r"\times ", 0x00F7: r"\div ", 0x22C5: r"\cdot ",
    0x00B7: r"\cdot ", 0x2219: r"\cdot ", 0x2264: r"\le ", 0x2265: r"\ge ", 0x2A7D: r"\leqslant ", 0x2A7E: r"\geqslant ",
    0x2260: r"\ne ", 0x2248: r"\approx ", 0x2261: r"\equiv ", 0x223C: r"\sim ", 0x2245: r"\cong ", 0x221D: r"\propto ",
    0x221E: r"\infty ", 0x2192: r"\to ", 0x2190: r"\leftarrow ", 0x2194: r"\leftrightarrow ", 0x21D2: r"\Rightarrow ",
    0x21D0: r"\Leftarrow ", 0x21D4: r"\Leftrightarrow ", 0x21A6: r"\mapsto ", 0x2208: r"\in ", 0x2209: r"\notin ",
    0x220B: r"\ni ", 0x2282: r"\subset ", 0x2283: r"\supset ", 0x2286: r"\subseteq ", 0x2287: r"\supseteq ",
    0x2284: r"\not\subset ", 0x222A: r"\cup ", 0x2229: r"\cap ", 0x2205: r"\varnothing ", 0x2200: r"\forall ",
    0x2203: r"\exists ", 0x2204: r"\nexists ", 0x2220: r"\angle ", 0x2221: r"\measuredangle ", 0x00B0: r"^\circ ",
    0x2218: r"\circ ", 0x2032: "'", 0x2033: "''", 0x2034: "'''", 0x2211: r"\sum ", 0x220F: r"\prod ", 0x222B: r"\int ",
    0x222C: r"\iint ", 0x222D: r"\iiint ", 0x222E: r"\oint ", 0x221A: r"\surd ", 0x2206: r"\Delta ", 0x22A5: r"\perp ",
    0x2225: r"\parallel ", 0x2226: r"\nparallel ", 0x2223: r"\mid ", 0x2026: r"\ldots ", 0x22EF: r"\cdots ",
    0x22EE: r"\vdots ", 0x22F1: r"\ddots ", 0x2216: r"\setminus ", 0x2227: r"\wedge ", 0x2228: r"\vee ",
    0x00AC: r"\neg ", 0x2202: r"\partial ", 0x2207: r"\nabla ", 0x210F: r"\hbar ", 0x2113: r"\ell ",
    0x211D: r"\mathbb{R}", 0x2115: r"\mathbb{N}", 0x2124: r"\mathbb{Z}", 0x211A: r"\mathbb{Q}", 0x2102: r"\mathbb{C}",
    0x2329: r"\langle ", 0x232A: r"\rangle ", 0x27E8: r"\langle ", 0x27E9: r"\rangle ", 0x2016: r"\| ",
    0x25B3: r"\triangle ", 0x2206: r"\Delta ", 0x25B5: r"\triangle ", 0x22BF: r"\triangle ", 0x2234: r"\therefore ",
    0x2235: r"\because ", 0x226A: r"\ll ", 0x226B: r"\gg ", 0x2243: r"\simeq ", 0x2241: r"\nsim ", 0x2262: r"\not\equiv ",
    0x21C4: r"\rightleftarrows ", 0x21CC: r"\rightleftharpoons ", 0x2191: r"\uparrow ", 0x2193: r"\downarrow ",
    0x2197: r"\nearrow ", 0x2198: r"\searrow ", 0x2135: r"\aleph ", 0x2118: r"\wp ", 0x2111: r"\Im ", 0x211C: r"\Re ",
    0x0025: r"\% ", 0x0023: r"\# ", 0x0026: r"\& ", 0x0024: r"\$ ", 0x005F: r"\_ ", 0x007B: r"\{ ", 0x007D: r"\} ",
    0x005C: r"\backslash ", 0x007E: r"\sim ", 0x005E: r"\hat{}", 0x00A0: "~", 0x2009: r"\, ", 0x200A: r"\, ",
    0x2002: r"\enspace ", 0x2003: r"\quad ", 0x2005: r"\; ", 0x2006: r"\, ", 0x200B: "", 0x2061: "",
    0x22C0: r"\bigwedge ", 0x22C1: r"\bigvee ", 0x22C2: r"\bigcap ", 0x22C3: r"\bigcup ", 0x2295: r"\oplus ",
    0x2297: r"\otimes ", 0x25CB: r"\bigcirc ", 0x2299: r"\odot ", 0x2020: r"\dagger ",
    # MathType's private-use glyphs (MT Extra)
    0xE900: r"\ldots ", 0xEB01: r"\,", 0xEB02: r"\:", 0xEB04: r"\;", 0xEB05: r"\quad ", 0xEB08: r"\,",
    0xEC00: r"\to ", 0xEC01: r"\leftarrow ", 0xEE04: r"\ddots ", 0xEE05: r"\ldots ", 0xEE06: r"\cdots ",
    0xEE07: r"\vdots ", 0xEE08: r"\ddots ", 0xEE09: r"\iddots ", 0xE98F: r"\to ", 0xE990: r"\leftarrow ",
    0xEF01: r"\,", 0xEF02: r"\:", 0xEF03: r"\;", 0xEF04: r"\quad ", 0xEF05: r"\qquad ", 0xEF06: r"\!", 0xEF07: "",
    0xEF08: r"\,", 0xE921: r"\,", 0xE922: r"\,", 0xE923: r"\,", 0xE924: r"\,", 0xE925: r"\,", 0xE926: r"\,",
}
GREEK = {
    0x03B1: "alpha", 0x03B2: "beta", 0x03B3: "gamma", 0x03B4: "delta", 0x03B5: "varepsilon", 0x03F5: "epsilon",
    0x03B6: "zeta", 0x03B7: "eta", 0x03B8: "theta", 0x03D1: "vartheta", 0x03B9: "iota", 0x03BA: "kappa",
    0x03BB: "lambda", 0x03BC: "mu", 0x03BD: "nu", 0x03BE: "xi", 0x03BF: "o", 0x03C0: "pi", 0x03D6: "varpi",
    0x03C1: "rho", 0x03F1: "varrho", 0x03C3: "sigma", 0x03C2: "varsigma", 0x03C4: "tau", 0x03C5: "upsilon",
    0x03C6: "varphi", 0x03D5: "phi", 0x03C7: "chi", 0x03C8: "psi", 0x03C9: "omega",
    0x0393: "Gamma", 0x0394: "Delta", 0x0398: "Theta", 0x039B: "Lambda", 0x039E: "Xi", 0x03A0: "Pi",
    0x03A3: "Sigma", 0x03A5: "Upsilon", 0x03A6: "Phi", 0x03A8: "Psi", 0x03A9: "Omega",
}
FUNCTIONS = {
    "sin", "cos", "tan", "cot", "sec", "csc", "arcsin", "arccos", "arctan", "sinh", "cosh", "tanh", "coth",
    "log", "ln", "lg", "exp", "lim", "max", "min", "sup", "inf", "det", "deg", "dim", "gcd", "arg", "ker", "hom",
}
FUNC_ALIASES = {"tg": r"\tan ", "cotg": r"\cot ", "arctg": r"\arctan ", "arccotg": r"\operatorname{arccot}", "cot": r"\cot "}

FENCES = {  # selector → (left, right)
    0: (r"\langle ", r"\rangle "), 1: ("(", ")"), 2: (r"\{", r"\}"), 3: ("[", "]"), 4: ("|", "|"),
    5: (r"\|", r"\|"), 6: (r"\lfloor ", r"\rfloor "), 7: (r"\lceil ", r"\rceil "), 8: (r"[\![", r"]\!]"),
}
INTERVAL = {0: "(", 1: ")", 2: "[", 3: "]"}
BIG_OPS = {16: r"\sum", 17: r"\prod", 18: r"\coprod", 19: r"\bigcup", 20: r"\bigcap", 21: r"\int", 22: r"\sum"}
EMBELLS = {
    2: r"\dot{%s}", 3: r"\ddot{%s}", 4: r"\dddot{%s}", 5: "%s'", 6: "%s''", 7: "{}'%s", 8: r"\tilde{%s}",
    9: r"\hat{%s}", 10: r"\not{%s}", 11: r"\overrightarrow{%s}", 12: r"\overleftarrow{%s}",
    13: r"\overleftrightarrow{%s}", 14: r"\vec{%s}", 15: r"\overleftarrow{%s}", 16: r"\overline{%s}",
    17: r"\overline{%s}", 18: "%s'''", 19: r"\overset{\frown}{%s}", 20: r"\overset{\smile}{%s}",
    21: r"\cancel{%s}", 22: r"\cancel{%s}", 23: r"\bcancel{%s}", 24: r"\ddddot{%s}", 25: r"\underset{.}{%s}",
    26: r"\underset{..}{%s}", 29: r"\underline{%s}", 30: r"\utilde{%s}", 33: r"\underrightarrow{%s}",
    34: r"\underleftarrow{%s}", 35: r"\underleftrightarrow{%s}",
}


NEGATED = {"=": r"\ne ", r"\in": r"\notin ", r"\subset": r"\not\subset ", r"\equiv": r"\not\equiv ", "<": r"\nless ",
           ">": r"\ngtr ", r"\le": r"\nleq ", r"\ge": r"\ngeq ", r"\parallel": r"\nparallel ", r"\sim": r"\nsim ", r"\exists": r"\nexists "}


class _Unknown(Exception):
    pass


def _char(c: Char) -> str:
    code = c.code
    if c.style == FN_MARKER or c.style == FN_EXPAND and code in (0x28, 0x29, 0x5B, 0x5D, 0x7B, 0x7D, 0x7C):
        return ""
    if code in GREEK:
        return "\\" + GREEK[code] + " "
    if code in SYMBOLS:
        return SYMBOLS[code]
    if 0x20 <= code < 0x7F:
        ch = chr(code)
        if c.style == FN_VECTOR and ch.isalnum():
            return r"\mathbf{%s}" % ch
        return ch
    if 0xE000 <= code <= 0xF8FF:
        if c.style == FN_SPACE:
            return r"\,"
        raise _Unknown(f"U+{code:04X}")
    if code == 0:
        return ""
    return chr(code)  # Vietnamese letters and other printable Unicode: KaTeX handles them in \text


def _is_text(it) -> bool:
    return isinstance(it, Char) and it.style in (FN_TEXT, FN_TEXT_FE) and not it.embells


def _is_func(it) -> bool:
    return isinstance(it, Char) and it.style == FN_FUNCTION and not it.embells and chr(it.code).isalpha()


def _text_run(chars: list[Char]) -> str:
    s = "".join(chr(c.code) if c.code >= 0x20 else "" for c in chars).replace("\xa0", " ")
    if not s.strip():
        return "~" if s else ""
    word = s.strip()
    if word.replace(".", "").replace(",", "").isdigit():
        return word
    if word in FUNCTIONS or word in FUNC_ALIASES:  # "log", "cos" typed in text style
        return _func_name(word) + (" " if s.endswith(" ") else "")
    if len(word) == 1 and ord(word) in GREEK:
        return "\\" + GREEK[ord(word)] + " "
    if len(word) == 1 and ord(word) in SYMBOLS:
        return SYMBOLS[ord(word)]
    out = s.replace("\\", "").replace("{", "").replace("}", "")
    for ch in "%#&$_":
        out = out.replace(ch, "\\" + ch)
    return r"\text{%s}" % out


def _func_run(chars: list[Char]) -> str:
    out: list[str] = []
    word = ""
    for c in chars:
        if c.func_start and word:
            out.append(_func_name(word))
            word = ""
        word += chr(c.code)
    if word:
        out.append(_func_name(word))
    return "".join(out)


def _func_name(w: str) -> str:
    if w in FUNC_ALIASES:
        return FUNC_ALIASES[w]
    if w in FUNCTIONS:
        return "\\" + w + " "
    if len(w) == 1:
        return r"\mathrm{%s}" % w
    return r"\mathrm{%s}" % w if not w.isalpha() or len(w) > 6 else r"\operatorname{%s}" % w


def _items(items: list | None) -> str:
    if not items:
        return ""
    out: list[str] = []
    i = 0
    while i < len(items):
        it = items[i]
        if _is_text(it):
            j = i
            while j < len(items) and _is_text(items[j]):
                j += 1
            out.append(_text_run(items[i:j]))
            i = j
            continue
        if _is_func(it):
            j = i
            while j < len(items) and _is_func(items[j]) and (j == i or not items[j].func_start or True):
                j += 1
            out.append(_func_run(items[i:j]))
            i = j
            continue
        out.append(_obj(it))
        i += 1
    return "".join(out)


def _obj(it) -> str:
    if isinstance(it, Char):
        s = _char(it)
        for e in it.embells:
            if e == 10:  # slash through: "=" + not is ≠
                s = NEGATED.get(s.strip(), r"\not " + s.strip() + " ")
                continue
            fmt = EMBELLS.get(e)
            if fmt is None:
                raise _Unknown(f"embell {e}")
            s = fmt % s.strip()
        return s
    if isinstance(it, Line):
        return _items(it.items)
    if isinstance(it, Tmpl):
        return _tmpl(it)
    if isinstance(it, Pile):
        return _pile(it)
    if isinstance(it, Matrix):
        return _matrix(it)
    return ""


def _slots(t: Tmpl) -> tuple[list[Line], list[Char]]:
    return [x for x in t.items if isinstance(x, Line)], [x for x in t.items if isinstance(x, Char)]


def _slot(lines: list[Line], i: int) -> str:
    return _items(lines[i].items).strip() if i < len(lines) else ""


def _pile(p: Pile, align: str | None = None) -> str:
    col = align or {1: "l", 2: "c", 3: "r"}.get(p.halign, "l")
    rows = [_items(ln.items).strip() for ln in p.lines]
    return r"\begin{array}{%s}%s\end{array}" % (col, r" \\ ".join(rows))


def _system_rows(obj) -> list[str] | None:
    """Rows of a one-column pile/matrix used for a system of equations, else None."""
    if isinstance(obj, Pile):
        return [_items(ln.items).strip() for ln in obj.lines]
    if isinstance(obj, Matrix) and obj.cols == 1:
        return [_items(c.items).strip() for c in obj.cells]
    return None


def _matrix(m: Matrix) -> str:
    cells = [_items(c.items).strip() for c in m.cells]
    rows = [" & ".join(cells[r * m.cols:(r + 1) * m.cols]) for r in range(m.rows)]
    return r"\begin{matrix}%s\end{matrix}" % r" \\ ".join(rows)


def _tmpl(t: Tmpl) -> str:
    sel, var = t.selector, t.variation
    lines, chars = _slots(t)
    main = _slot(lines, 0)
    if sel in FENCES:
        left, right = FENCES[sel]
        has_l, has_r = var & 1, var & 2
        body = lines[0].items if lines else None
        only = body[0] if body and len(body) == 1 else None
        rows = _system_rows(only)
        if rows is not None and has_l and not has_r and sel in (2, 3):
            if sel == 2:  # hệ: { … — rendered as cases
                return r"\begin{cases}%s\end{cases}" % r" \\ ".join(rows)
            return r"\left[ \begin{array}{l}%s\end{array} \right." % r" \\ ".join(rows)  # tuyển: [ …
        return r"\left%s %s \right%s" % (left.strip() if has_l else ".", main, right.strip() if has_r else ".")
    if sel == 9:
        return r"\left%s %s \right%s" % (INTERVAL.get(var & 0x3, "("), main, INTERVAL.get((var >> 4) & 0x3, ")"))
    if sel == 10:
        index = _slot(lines, 1)
        return r"\sqrt[%s]{%s}" % (index, main) if var == 1 and index else r"\sqrt{%s}" % main
    if sel == 11:
        num, den = main, _slot(lines, 1)
        if var & 0x2:
            return "{%s}/{%s}" % (num, den)
        return r"\frac{%s}{%s}" % (num, den)
    if sel == 12:
        return (r"\underline{\underline{%s}}" if var & 1 else r"\underline{%s}") % main
    if sel == 13:
        return (r"\overline{\overline{%s}}" if var & 1 else r"\overline{%s}") % main
    if sel == 14:
        top, bottom = main, _slot(lines, 1)
        arrow = r"\xleftarrow" if var & 0x10 and not var & 0x3 else r"\xrightarrow"
        if var & 0x1:
            arrow = r"\xleftrightarrow"
        if var & 0x2:
            arrow = r"\xrightleftharpoons"
        return arrow + ("[%s]" % bottom if bottom else "") + "{%s}" % top
    if sel == 15 or sel in BIG_OPS:
        if sel == 15:
            op = {1: r"\int", 2: r"\iint", 3: r"\iiint"}.get(var & 0x3, r"\int")
            if var & 0x4:
                op = r"\oint"
        else:
            op = BIG_OPS[sel]
        glyph = _op_glyph(lines[3] if len(lines) > 3 else None) or _op_glyph(Line(chars))
        if glyph and sel in (21, 22):
            op = glyph
        return op + _limits(_real(_slot(lines, 1)), _real(_slot(lines, 2))) + (" " + main if _real(main) else " ")
    if sel == 23:
        lower, upper = _slot(lines, 1), _slot(lines, 2)
        name = main.strip() or r"\lim"
        bare = re.sub(r"\\(text|mathrm|operatorname)\{(\w+)\}", r"\2", name).replace(" ", "")
        if bare in ("lim", r"\lim"):
            name = r"\lim"
        elif bare.lstrip("\\") in FUNCTIONS:
            name = "\\" + bare.lstrip("\\")
        elif "\\" in name:
            name = r"\mathop{%s}" % name
        else:
            name = r"\operatorname*{%s}" % bare
        return name + (r"\limits_{%s}" % lower if lower else "") + ("^{%s}" % upper if upper else "") + " "
    if sel in (24, 25):
        label = _slot(lines, 1)
        top = var & 1
        cmd = (r"\overbrace" if top else r"\underbrace") if sel == 24 else (r"\overbracket" if top else r"\underbracket")
        if sel == 25:
            cmd = r"\overbrace" if top else r"\underbrace"
        return cmd + "{%s}" % main + (("^{%s}" if top else "_{%s}") % label if label else "")
    if sel == 26:
        return r"%s\,\overline{\smash{\big)}\,%s}" % (_slot(lines, 1), main)
    if sel in (27, 28, 29):
        sub, sup = _slot(lines, 0), _slot(lines, 1)
        if sup.startswith(r"^\circ"):  # a degree sign typed inside a superscript
            sup = sup[1:]
        s = ""
        if sub:
            s += "_{%s}" % sub
        if sup:
            s += "^{%s}" % sup
        return ("{}" + s) if var & 1 else s
    if sel == 30:
        a, b = main, _slot(lines, 1)
        left = r"\langle %s" % a if var & 1 else ""
        right = r"%s\rangle " % b if var & 2 else ""
        return left + ("|" if left and right else "") + right
    if sel == 31:
        if var & 0x8:
            return (r"\overleftharpoon{%s}" if var & 1 else r"\overrightharpoon{%s}") % main
        under = var & 0x4
        both = var & 0x3 == 0x3
        if both:
            cmd = r"\underleftrightarrow" if under else r"\overleftrightarrow"
        elif var & 0x1:
            cmd = r"\underleftarrow" if under else r"\overleftarrow"
        else:
            cmd = r"\underrightarrow" if under else r"\overrightarrow"
        return cmd + "{%s}" % main
    if sel == 32:
        return r"\widetilde{%s}" % main
    if sel == 33:
        return r"\widehat{%s}" % main
    if sel == 34:
        return r"\overset{\frown}{%s}" % main
    if sel == 35:
        return r"\underset{%s}{\underline{%s|}}" % (_slot(lines, 1), main)
    if sel == 36:
        return r"\cancel{%s}" % main
    if sel == 37:
        return r"\boxed{%s}" % main
    raise _Unknown(f"template {sel}")


SPACING = {r"\,", r"\:", r"\;", r"\!", r"\quad", r"\qquad", "~", r"\ ", r"\enspace"}


def _real(s: str) -> str:
    """'' when a slot holds only spacing (MathType puts a thin space in 'empty' limits)."""
    rest = s
    for sp in sorted(SPACING, key=len, reverse=True):
        rest = rest.replace(sp, "")
    return s if rest.strip() else ""


def _op_glyph(line: Line | None) -> str:
    for it in (line.items or []) if line else []:
        if isinstance(it, Char) and it.code in SYMBOLS:
            return SYMBOLS[it.code].strip()
    return ""


def _limits(lower: str, upper: str) -> str:
    return ("_{%s}" % lower if lower else "") + ("^{%s}" % upper if upper else "")


# ------------------------------------------------------------------ public
def mtef_from_ole(ole: bytes) -> bytes | None:
    try:
        with olefile.OleFileIO(io.BytesIO(ole)) as f:
            if not f.exists("Equation Native"):
                return None
            data = f.openstream("Equation Native").read()
    except (OSError, ValueError):
        return None
    if len(data) < 28:
        return None
    header = struct.unpack("<H", data[:2])[0]  # cbHdr, normally 28
    return data[header:]


def mtef_to_latex(mtef: bytes) -> str:
    """Raises MtefError when the equation cannot be converted faithfully."""
    try:
        items = _parse(mtef)
        latex = _items(items)
    except _Unknown as exc:
        raise MtefError(str(exc)) from exc
    except RecursionError as exc:
        raise MtefError("equation too deep") from exc
    return _tidy(latex)


def to_latex(ole: bytes) -> str | None:
    mtef = mtef_from_ole(ole)
    if mtef is None:
        return None
    try:
        return mtef_to_latex(mtef) or None
    except MtefError:
        return None


def _tidy(s: str) -> str:
    s = " ".join(s.split())
    for a, b in ((" }", "}"), ("{ ", "{"), (" ^", "^"), (" _", "_"), (" )", ")"), ("( ", "(")):
        s = s.replace(a, b)
    return s.strip()
