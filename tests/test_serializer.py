import math
from datetime import date, datetime

import pytest

from jsonlib.exceptions import JSONSerializeError
from jsonlib.serializer import stringify


# ── Scalars ───────────────────────────────────────────────────────────────────

def test_none():
    assert stringify(None) == "null"


def test_true():
    assert stringify(True) == "true"


def test_false():
    assert stringify(False) == "false"


def test_integer():
    assert stringify(42) == "42"


def test_negative_integer():
    assert stringify(-7) == "-7"


def test_zero():
    assert stringify(0) == "0"


def test_float():
    assert stringify(3.14) == repr(3.14)


def test_float_integer_value():
    # 1.0 must stay a float representation, not become "1"
    result = stringify(1.0)
    assert "." in result or "e" in result


def test_string_simple():
    assert stringify("hello") == '"hello"'


def test_string_empty():
    assert stringify("") == '""'


def test_string_escape_double_quote():
    assert stringify('say "hi"') == r'"say \"hi\""'


def test_string_escape_backslash():
    assert stringify("a\\b") == r'"a\\b"'


def test_string_escape_newline():
    assert stringify("line1\nline2") == r'"line1\nline2"'


def test_string_escape_tab():
    assert stringify("a\tb") == r'"a\tb"'


def test_string_escape_backspace():
    assert stringify("\b") == r'"\b"'


def test_string_escape_formfeed():
    assert stringify("\f") == r'"\f"'


def test_string_escape_carriage_return():
    assert stringify("\r") == r'"\r"'


def test_string_control_char_generic():
    # U+0001 has no named escape → 
    assert stringify("\x01") == '"\\u0001"'


def test_string_unicode_preserved_by_default():
    assert stringify("こんにちは") == '"こんにちは"'


def test_string_emoji_preserved_by_default():
    assert stringify("😀") == '"😀"'


# ── ensure_ascii ──────────────────────────────────────────────────────────────

def test_ensure_ascii_escapes_non_ascii():
    result = stringify("中", ensure_ascii=True)
    assert result == '"\\u4e2d"'


def test_ensure_ascii_emoji_becomes_surrogate_pair():
    # 😀 = U+1F600 → 😀
    result = stringify("😀", ensure_ascii=True)
    assert result == '"\\ud83d\\ude00"'


def test_ensure_ascii_ascii_unchanged():
    assert stringify("hello", ensure_ascii=True) == '"hello"'


# ── Containers ────────────────────────────────────────────────────────────────

def test_empty_object():
    assert stringify({}) == "{}"


def test_empty_array():
    assert stringify([]) == "[]"


def test_simple_object():
    result = stringify({"a": 1})
    assert result == '{"a":1}'


def test_simple_array():
    assert stringify([1, 2, 3]) == "[1,2,3]"


def test_nested_object():
    result = stringify({"a": {"b": 1}})
    assert result == '{"a":{"b":1}}'


def test_nested_array():
    assert stringify([[1, 2], [3, 4]]) == "[[1,2],[3,4]]"


def test_tuple_serializes_as_array():
    assert stringify((1, 2, 3)) == "[1,2,3]"


def test_mixed_object():
    result = stringify({"n": None, "b": True, "i": 1})
    assert '"n":null' in result
    assert '"b":true' in result
    assert '"i":1' in result


# ── Pretty-print ──────────────────────────────────────────────────────────────

def test_pretty_object():
    result = stringify({"a": 1}, indent=2)
    assert result == '{\n  "a": 1\n}'


def test_pretty_array():
    result = stringify([1, 2], indent=2)
    assert result == '[\n  1,\n  2\n]'


def test_pretty_nested():
    result = stringify({"a": {"b": 1}}, indent=2)
    assert "  " in result
    assert "\n" in result


def test_compact_no_whitespace():
    result = stringify({"a": 1, "b": [1, 2]})
    assert " " not in result
    assert "\n" not in result


# ── Circular reference ────────────────────────────────────────────────────────

def test_circular_reference_dict():
    d: dict = {}
    d["self"] = d
    with pytest.raises(JSONSerializeError, match="[Cc]ircular"):
        stringify(d)


def test_circular_reference_list():
    lst: list = []
    lst.append(lst)
    with pytest.raises(JSONSerializeError, match="[Cc]ircular"):
        stringify(lst)


def test_shared_reference_allowed():
    shared = [1, 2, 3]
    obj = {"a": shared, "b": shared}
    result = stringify(obj)
    assert result.count("[1,2,3]") == 2


# ── datetime / date ───────────────────────────────────────────────────────────

def test_datetime_iso8601():
    dt = datetime(2024, 1, 15, 12, 30, 0)
    assert stringify(dt) == '"2024-01-15T12:30:00"'


def test_date_iso8601():
    d = date(2024, 1, 15)
    assert stringify(d) == '"2024-01-15"'


# ── Custom handlers ───────────────────────────────────────────────────────────

def test_custom_handler_basic():
    class Point:
        def __init__(self, x: int, y: int):
            self.x, self.y = x, y

    result = stringify(
        Point(1, 2),
        custom_handlers={Point: lambda p: {"x": p.x, "y": p.y}},
    )
    assert result == '{"x":1,"y":2}'


def test_custom_handler_overrides_default():
    # Override bool serialization
    result = stringify(True, custom_handlers={bool: lambda b: 1 if b else 0})
    assert result == "1"


def test_custom_handler_recursive():
    class Wrapper:
        def __init__(self, value):
            self.value = value

    result = stringify(
        Wrapper([1, 2, 3]),
        custom_handlers={Wrapper: lambda w: w.value},
    )
    assert result == "[1,2,3]"


# ── Error cases ───────────────────────────────────────────────────────────────

def test_unsupported_type_raises():
    with pytest.raises(JSONSerializeError, match="not JSON serializable"):
        stringify(object())


def test_set_raises():
    with pytest.raises(JSONSerializeError):
        stringify({1, 2, 3})


def test_infinity_raises():
    with pytest.raises(JSONSerializeError, match="inf"):
        stringify(float("inf"))


def test_nan_raises():
    with pytest.raises(JSONSerializeError, match="inf|nan"):
        stringify(float("nan"))


def test_negative_infinity_raises():
    with pytest.raises(JSONSerializeError):
        stringify(float("-inf"))
