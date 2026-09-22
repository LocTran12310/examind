"""MathType (MTEF v5) → LaTeX (official-exam-ingestion AC-01, AC-02)."""
import json
import struct
from pathlib import Path

import pytest

from app.modules.ingestion.domain.services import mtef

FIX = Path(__file__).parent / "fixtures" / "mtef"
EXPECTED = json.loads((FIX / "expected.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_reference_objects_convert(name):
    """Objects taken from the 18 official exam files (one per construct)."""
    assert mtef.to_latex((FIX / f"{name}.bin").read_bytes()) == EXPECTED[name]


# ------------------------------------------------------------------ synthetic MTEF
HEADER = bytes([5, 1, 0, 6, 9]) + b"DSMT6\x00" + b"\x01"
VAR, NUM, SYM, TEXT, FUNC = 128 + 3, 128 + 8, 128 + 6, 128 + 1, 128 + 2


def ch(c: str, face: int = VAR) -> bytes:
    return bytes([2, 0, face]) + struct.pack("<H", ord(c))


def line(*items: bytes) -> bytes:
    return bytes([1, 0]) + b"".join(items) + b"\x00"


NULL = bytes([1, 1])


def tmpl(sel: int, var: int, *items: bytes) -> bytes:
    return bytes([3, 0, sel, var, 0]) + b"".join(items) + b"\x00"


def eq(*items: bytes) -> bytes:
    return HEADER + line(*items)


def tex(*items: bytes) -> str:
    return mtef.mtef_to_latex(eq(*items))


def test_fraction_root_and_scripts():
    assert tex(tmpl(11, 0, line(ch("a")), line(ch("2", NUM)))) == r"\frac{a}{2}"
    assert tex(tmpl(10, 0, line(ch("x")), NULL)) == r"\sqrt{x}"
    assert tex(tmpl(10, 1, line(ch("x")), line(ch("3", NUM)))) == r"\sqrt[3]{x}"
    assert tex(ch("x"), tmpl(28, 0, NULL, line(ch("2", NUM)))) == "x^{2}"
    assert tex(ch("u"), tmpl(27, 0, line(ch("n")), NULL)) == "u_{n}"


def test_fences_follow_variation_bits():
    body = line(ch("x"))
    assert tex(tmpl(1, 3, body, ch("(", 128 + 22), ch(")", 128 + 22))) == r"\left(x \right)"
    assert tex(tmpl(4, 3, body)) == r"\left| x \right|"
    assert tex(tmpl(3, 1, body)) == r"\left[ x \right."


def test_system_becomes_cases():
    pile = bytes([4, 0, 1, 1]) + line(ch("x"), ch("=", SYM), ch("1", NUM)) + line(ch("y"), ch("=", SYM), ch("2", NUM)) + b"\x00"
    assert tex(tmpl(2, 1, line(pile))) == r"\begin{cases}x=1 \\ y=2\end{cases}"


def test_integral_with_glyph_slot_and_limits():
    op = tmpl(21, 0x20, NULL, NULL, line(bytes([2, 0, 128 + 24]) + struct.pack("<H", 0xEF01)), line(ch("∫", SYM)))
    assert tex(op, tmpl(29, 0, line(ch("0", NUM)), line(ch("1", NUM))), ch("x"), ch("d"), ch("x")) == r"\int_{0}^{1}xdx"


def test_vector_degree_and_symbols():
    assert tex(tmpl(31, 2, line(ch("A"), ch("B")))) == r"\overrightarrow{AB}"
    assert tex(ch("6", NUM), ch("0", NUM), ch("°", SYM)) == r"60^\circ"
    assert tex(ch("x"), ch("≤", SYM), ch("π")) == r"x\le \pi"


def test_slashed_relations():
    neq = bytes([2, 1, SYM]) + struct.pack("<H", ord("=")) + bytes([6, 0, 10, 0])  # "=" with the "not" embellishment
    assert tex(ch("a"), neq, ch("0", NUM)) == r"a\ne 0"


def test_text_runs_and_functions():
    assert tex(ch("k", TEXT), ch("h", TEXT), ch("i", TEXT)) == r"\text{khi}"
    assert tex(ch("l", TEXT), ch("o", TEXT), ch("g", TEXT), ch("x")) == r"\log x"
    assert tex(ch("s", FUNC), ch("i", FUNC), ch("n", FUNC), ch("x")) == r"\sin x"
    assert tex(ch("7", TEXT), ch("%", TEXT)) == r"\text{7\%}"


def test_future_record_is_skipped():
    future = bytes([0x66, 3]) + b"abc"
    assert mtef.mtef_to_latex(HEADER + future + line(ch("x"))) == "x"


def test_unreadable_data_returns_none():
    assert mtef.to_latex(b"not an ole file") is None
    with pytest.raises(mtef.MtefError):
        mtef.mtef_to_latex(HEADER + bytes([1, 0, 2, 0]))  # char cut short
    with pytest.raises(mtef.MtefError):
        mtef.mtef_to_latex(HEADER + line(tmpl(99, 0, line(ch("x")))))  # unknown template
    with pytest.raises(mtef.MtefError):
        mtef.mtef_to_latex(bytes([3]) + HEADER[1:])  # MTEF v3
