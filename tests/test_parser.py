import pytest
from jsonlib.parser import parse
from jsonlib.exceptions import JSONSyntaxError


# ── Primitives ────────────────────────────────────────────────────────────────

def test_parse_null():
    assert parse("null") is None


def test_parse_true():
    assert parse("true") is True


def test_parse_false():
    assert parse("false") is False


def test_parse_string():
    assert parse('"hello"') == "hello"


def test_parse_empty_string():
    assert parse('""') == ""


def test_parse_string_with_escape():
    assert parse(r'"line1\nline2"') == "line1\nline2"


def test_parse_integer():
    result = parse("42")
    assert result == 42
    assert isinstance(result, int)


def test_parse_negative_integer():
    assert parse("-7") == -7


def test_parse_zero():
    assert parse("0") == 0


def test_parse_float():
    result = parse("3.14")
    assert result == pytest.approx(3.14)
    assert isinstance(result, float)


def test_parse_negative_float():
    assert parse("-0.5") == pytest.approx(-0.5)


def test_parse_scientific_notation():
    assert parse("1e3") == pytest.approx(1000.0)
    assert isinstance(parse("1e3"), float)


def test_parse_scientific_with_sign():
    assert parse("2.5e+2") == pytest.approx(250.0)


# ── Objects ───────────────────────────────────────────────────────────────────

def test_parse_empty_object():
    assert parse("{}") == {}


def test_parse_single_pair():
    assert parse('{"a": 1}') == {"a": 1}


def test_parse_multiple_pairs():
    assert parse('{"x": 1, "y": 2, "z": 3}') == {"x": 1, "y": 2, "z": 3}


def test_parse_nested_object():
    assert parse('{"a": {"b": {"c": 42}}}') == {"a": {"b": {"c": 42}}}


def test_parse_object_with_all_types():
    result = parse('{"n": null, "b": true, "f": false, "s": "hi", "i": 1, "d": 1.5}')
    assert result == {"n": None, "b": True, "f": False, "s": "hi", "i": 1, "d": 1.5}


def test_parse_object_preserves_key_order():
    result = parse('{"z": 1, "a": 2, "m": 3}')
    assert list(result.keys()) == ["z", "a", "m"]


# ── Arrays ────────────────────────────────────────────────────────────────────

def test_parse_empty_array():
    assert parse("[]") == []


def test_parse_integer_array():
    assert parse("[1, 2, 3]") == [1, 2, 3]


def test_parse_mixed_array():
    assert parse('[1, "two", true, null]') == [1, "two", True, None]


def test_parse_nested_array():
    assert parse("[[1, 2], [3, 4]]") == [[1, 2], [3, 4]]


def test_parse_array_of_objects():
    assert parse('[{"a": 1}, {"b": 2}]') == [{"a": 1}, {"b": 2}]


def test_parse_single_element_array():
    assert parse("[42]") == [42]


# ── Round-trip ────────────────────────────────────────────────────────────────

def test_roundtrip_nested():
    import json
    original = {"users": [{"id": 1, "active": True}, {"id": 2, "active": False}]}
    assert parse(json.dumps(original)) == original


# ── ParseOptions: max_depth ──────────────────────────────────────────────────

def test_max_depth_object_exceeded():
    with pytest.raises(JSONSyntaxError, match="depth"):
        parse('{"a": {"b": 1}}', max_depth=1)


def test_max_depth_object_ok():
    assert parse('{"a": {"b": 1}}', max_depth=2) == {"a": {"b": 1}}


def test_max_depth_array_exceeded():
    with pytest.raises(JSONSyntaxError, match="depth"):
        parse("[[1]]", max_depth=1)


def test_max_depth_array_ok():
    assert parse("[[1]]", max_depth=2) == [[1]]


def test_max_depth_default_allows_deep_nesting():
    # 10-level deep object; default max_depth=1000 must not raise
    json_str = '{"a":' * 10 + "1" + "}" * 10
    result = parse(json_str)
    assert result is not None


# ── ParseOptions: allow_trailing_comma ───────────────────────────────────────

def test_trailing_comma_array_rejected_by_default():
    with pytest.raises(JSONSyntaxError, match="[Tt]railing"):
        parse("[1, 2,]")


def test_trailing_comma_array_allowed():
    assert parse("[1, 2,]", allow_trailing_comma=True) == [1, 2]


def test_trailing_comma_object_rejected_by_default():
    with pytest.raises(JSONSyntaxError, match="[Tt]railing"):
        parse('{"a": 1,}')


def test_trailing_comma_object_allowed():
    assert parse('{"a": 1,}', allow_trailing_comma=True) == {"a": 1}


# ── ParseOptions: case_insensitive_keys ──────────────────────────────────────

def test_case_insensitive_keys_lowercases():
    result = parse('{"Name": "Alice", "AGE": 30}', case_insensitive_keys=True)
    assert result == {"name": "Alice", "age": 30}


def test_case_sensitive_keys_default():
    result = parse('{"Name": "Alice", "name": "Bob"}')
    assert result["Name"] == "Alice"
    assert result["name"] == "Bob"


# ── ParseOptions: duplicate_key_policy ───────────────────────────────────────

def test_duplicate_key_last_wins_by_default():
    assert parse('{"a": 1, "a": 2}')["a"] == 2


def test_duplicate_key_error_policy():
    with pytest.raises(JSONSyntaxError, match="[Dd]uplicate"):
        parse('{"a": 1, "a": 2}', duplicate_key_policy="error")


def test_duplicate_key_case_insensitive_error():
    # With case_insensitive_keys, "A" and "a" become the same key
    with pytest.raises(JSONSyntaxError, match="[Dd]uplicate"):
        parse('{"A": 1, "a": 2}', case_insensitive_keys=True, duplicate_key_policy="error")


# ── Error cases ───────────────────────────────────────────────────────────────

def test_empty_input_raises():
    with pytest.raises(JSONSyntaxError):
        parse("")


def test_whitespace_only_raises():
    with pytest.raises(JSONSyntaxError):
        parse("   ")


def test_extra_content_after_value():
    with pytest.raises(JSONSyntaxError):
        parse("1 2")


def test_unterminated_object():
    with pytest.raises(JSONSyntaxError):
        parse('{"a": 1')


def test_unterminated_array():
    with pytest.raises(JSONSyntaxError):
        parse("[1, 2")


def test_unquoted_key():
    with pytest.raises(JSONSyntaxError):
        parse("{key: 1}")


def test_missing_colon():
    with pytest.raises(JSONSyntaxError):
        parse('{"a" 1}')


def test_missing_comma_in_array():
    with pytest.raises(JSONSyntaxError):
        parse("[1 2]")


def test_missing_comma_in_object():
    with pytest.raises(JSONSyntaxError):
        parse('{"a": 1 "b": 2}')


def test_error_carries_location():
    try:
        parse("\n\n{bad}")
    except JSONSyntaxError as e:
        assert e.line >= 1
        assert e.column >= 1
    else:
        pytest.fail("Expected JSONSyntaxError")


# ── Edge cases ────────────────────────────────────────────────────────────────

def test_empty_object_and_array_nested():
    assert parse('{"a": [], "b": {}}') == {"a": [], "b": {}}


def test_null_value_vs_missing_key():
    result = parse('{"key": null}')
    assert "key" in result
    assert result["key"] is None


def test_unicode_key():
    assert parse('{"こんにちは": 1}') == {"こんにちは": 1}


def test_large_number():
    assert parse("123456789012345") == 123456789012345
