"""The pure rules of the ingestion pipeline: what a question's position in the paper says about its level
(difficulty-at-upload T-01-02) and how a difficulty model's reply is read (T-02-01)."""
import json

import pytest

from app.modules.ingestion.application.difficulty import DifficultyModelPass
from app.modules.ingestion.domain.entities import AiModel
from app.modules.ingestion.domain.errors import LlmError
from app.modules.ingestion.domain.ports import ChatResult
from app.modules.ingestion.domain.services.difficulty_rules import (
    BY_PART,
    BY_TYPE,
    DIFFICULTY_BATCH,
    DIFFICULTY_SYSTEM,
    DIFFICULTY_TEXT_CHARS,
    difficulty_for,
    difficulty_request,
    read_difficulty_reply,
)

LEVELS = ("nb", "th", "vd", "vdc")  # the bank's scale, restated here: the rule may never invent a fifth level


@pytest.mark.parametrize("number,level", [(1, "nb"), (6, "nb"), (7, "th"), (10, "th"), (11, "vd"), (12, "vd")])
def test_part_one_rises_from_recall_to_application(number, level):
    assert difficulty_for("1", number, "mcq") == level


@pytest.mark.parametrize("number,level", [(1, "th"), (2, "th"), (3, "vd"), (4, "vd")])
def test_part_two_never_starts_at_recall(number, level):
    """Four statements about one setting: even the first true/false question is past nhận biết."""
    assert difficulty_for("2", number, "true_false") == level


@pytest.mark.parametrize("number,level", [(1, "vd"), (3, "vd"), (4, "vdc"), (6, "vdc")])
def test_part_three_is_the_hard_end_of_the_paper(number, level):
    assert difficulty_for("3", number, "short_answer") == level


def test_parts_are_ordered_easiest_first():
    """The convention the whole rule rests on: the same position number is harder in a later part."""
    assert [difficulty_for(p, 1, "mcq") for p in ("1", "2", "3")] == ["nb", "th", "vd"]


@pytest.mark.parametrize("number,level", [(1, "nb"), (15, "nb"), (16, "th"), (30, "th"), (31, "vd"), (37, "vd"), (38, "vdc"), (40, "vdc")])
def test_a_paper_without_parts_stretches_the_same_shape(number, level):
    """A 40-question paper has no PHẦN header; the type stands in for it and the bands stretch to its length."""
    assert difficulty_for(None, number, "mcq") == level


@pytest.mark.parametrize("qtype,number,level", [("true_false", 1, "th"), ("true_false", 4, "vd"),
                                                ("short_answer", 2, "vd"), ("short_answer", 5, "vdc"),
                                                ("essay", 1, "vd"), ("essay", 3, "vdc")])
def test_without_a_part_the_type_carries_the_convention(qtype, number, level):
    assert difficulty_for(None, number, qtype) == level


def test_a_number_past_the_last_band_keeps_the_hardest_level():
    """A paper longer than the convention expects keeps rising; it does not wrap back to nhận biết."""
    assert difficulty_for("1", 99, "mcq") == "vd"
    assert difficulty_for("3", 99, "short_answer") == "vdc"
    assert difficulty_for(None, 500, "mcq") == "vdc"


def test_an_unknown_part_or_type_still_gets_a_level():
    """Never None (ADR-02): a PHẦN IV, a missing number or a type the rule has no band table for still answers."""
    assert difficulty_for("4", 2, "true_false") == "th"       # unknown part: the type decides
    assert difficulty_for(None, None, "mcq") == "nb"          # no number: read as the first of its part
    assert difficulty_for(None, 1, "something_else") == "nb"  # unknown type: the commonest shape
    assert difficulty_for("1", None, "mcq") == "nb"


def test_every_band_names_a_level_of_the_scale():
    for bands in list(BY_PART.values()) + list(BY_TYPE.values()):
        assert [level for _, level in bands] == sorted({level for _, level in bands}, key=LEVELS.index)
        assert all(level in LEVELS for _, level in bands)
        assert [last for last, _ in bands] == sorted(last for last, _ in bands)


def test_the_rule_needs_nothing_but_its_arguments():
    """T-01-02: pure. No clock, no database, no config, no framework — the module's imports say so."""
    import ast
    import inspect

    import app.modules.ingestion.domain.services.difficulty_rules as mod

    tree = ast.parse(inspect.getsource(mod))
    imported = {n.names[0].name if isinstance(n, ast.Import) else n.module
                for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))}
    assert imported == {"unicodedata", "app.modules.ingestion.domain.services.ai_parse"}


def test_a_reply_becomes_levels_by_the_number_the_prompt_gave():
    keys = {7: "a", 8: "b"}
    reply = json.dumps({"results": [{"number": 7, "level": "vd"}, {"number": 8, "level": "nb"}]})
    assert read_difficulty_reply(reply, keys) == {"a": "vd", "b": "nb"}
    assert read_difficulty_reply("Đây là kết quả: ```json\n" + reply + "\n```", keys) == {"a": "vd", "b": "nb"}


def test_the_label_is_read_in_words_as_well_as_in_codes():
    """A 7B model answers in the words of the prompt as readily as in its codes — and "vận dụng cao" ends with
    the whole of "vận dụng", so the two must not be told apart by a prefix."""
    rows = [{"number": 1, "level": "Nhận biết"}, {"number": 2, "level": "vận dụng cao"}, {"number": 3, "level": " VD "},
            {"number": 4, "level": "thong hieu"}]
    got = read_difficulty_reply(json.dumps({"results": rows}), {1: "a", 2: "b", 3: "c", 4: "d"})
    assert got == {"a": "nb", "b": "vdc", "c": "vd", "d": "th"}


def test_anything_that_is_not_one_of_the_four_levels_is_dropped():
    """The position rule keeps those questions, so a bad answer costs coverage of the model, never a level."""
    rows = [{"number": 1, "level": "trung bình"}, {"number": 2, "level": 3}, {"number": 3}, {"number": 99, "level": "nb"},
            {"level": "nb"}, {"number": "x", "level": "nb"}, {"number": 4, "level": "vdc"}]
    assert read_difficulty_reply(json.dumps({"results": rows}), {1: "a", 2: "b", 3: "c", 4: "d"}) == {"d": "vdc"}
    assert read_difficulty_reply(json.dumps({"results": "nb"}), {1: "a"}) == {}
    assert read_difficulty_reply(json.dumps({"answer": "nb"}), {1: "a"}) == {}


def test_a_reply_that_is_not_json_is_a_model_error():
    with pytest.raises(LlmError):
        read_difficulty_reply("Mức độ của câu 1 là nhận biết.", {1: "a"})
    with pytest.raises(LlmError):
        read_difficulty_reply('{"results": [', {1: "a"})


def test_the_request_restates_the_count_and_the_numbers():
    """The lesson of the tagging pass: a small model mirrors the example and answers once for a whole batch unless
    the request says again how many answers it wants and for which questions."""
    asked = difficulty_request([(3, "Tính đạo hàm"), (4, "x" * 900)])
    assert "Trả về đúng 2 phần tử, cho các câu: 3, 4." in asked
    assert "Câu 3: Tính đạo hàm" in asked and "Câu 4: " in asked
    assert len(asked.split("Câu 4: ")[1].strip()) == DIFFICULTY_TEXT_CHARS  # a long question is cut, not sent whole
    assert all(code in DIFFICULTY_SYSTEM for code in LEVELS)


def test_the_pass_asks_in_batches_and_maps_each_answer_back_to_its_question():
    rows = [(f"q{i}", i, f"Câu {i}") for i in range(1, 26)]

    class Chat:
        def __init__(self):
            self.asked = []

        def chat(self, model, system, user, images=None, json_mode=True, timeout=None, schema=None):
            self.asked.append(user)
            numbers = [int(x.split(":")[0].replace("Câu ", "")) for x in user.split("CÂU HỎI:")[1].strip().split("\n\n")]
            return ChatResult(json.dumps({"results": [{"number": n, "level": "th"} for n in numbers]}), 1, "m")

    chat = Chat()
    model = AiModel(organization_id=None, name="m", provider="ollama", model="m:1", base_url="http://m")
    pass_ = DifficultyModelPass(chat, model)
    batches = list(pass_.batches(rows))
    assert [len(b) for b in batches] == [DIFFICULTY_BATCH, DIFFICULTY_BATCH, 5]
    got = {}
    for batch in batches:
        got.update(pass_.ask(batch))
    assert got == {f"q{i}": "th" for i in range(1, 26)} and len(chat.asked) == 3
