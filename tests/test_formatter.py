import pytest

from jsonlib.exceptions import JSONSyntaxError
from jsonlib.formatter import minify, prettify
from jsonlib.parser import parse


# ── minify ────────────────────────────────────────────────────────────────────

def test_minify_removes_spaces():
    assert minify('{ "a" : 1 }') == '{"a":1}'


def test_minify_removes_newlines():
    ugly = '{\n  "a": 1,\n  "b": 2\n}'
    assert minify(ugly) == '{"a":1,"b":2}'


def test_minify_idempotent():
    compact = '{"a":1,"b":[1,2,3]}'
    assert minify(compact) == compact


def test_minify_array():
    assert minify("[ 1 , 2 , 3 ]") == "[1,2,3]"


def test_minify_nested():
    result = minify('{"a": {"b": [1, 2]}}')
    assert result == '{"a":{"b":[1,2]}}'


def test_minify_preserves_string_spaces():
    result = minify('"hello world"')
    assert result == '"hello world"'


def test_minify_preserves_empty_containers():
    assert minify("{}") == "{}"
    assert minify("[]") == "[]"


def test_minify_invalid_json_raises():
    with pytest.raises(JSONSyntaxError):
        minify("{bad}")


# ── prettify ──────────────────────────────────────────────────────────────────

def test_prettify_adds_indent():
    result = prettify('{"a":1}', indent=2)
    assert result == '{\n  "a": 1\n}'


def test_prettify_default_indent_2():
    result = prettify('{"a":1}')
    assert "  " in result
    assert "\n" in result


def test_prettify_custom_indent_4():
    result = prettify('{"a":1}', indent=4)
    assert "    " in result


def test_prettify_array():
    result = prettify("[1,2,3]", indent=2)
    assert result == "[\n  1,\n  2,\n  3\n]"


def test_prettify_nested():
    result = prettify('{"a":{"b":1}}', indent=2)
    assert "    " in result  # 4 spaces for nested level


def test_prettify_idempotent_values():
    original = '{"x": 1, "y": [true, null]}'
    assert parse(prettify(original)) == parse(original)


def test_prettify_invalid_json_raises():
    with pytest.raises(JSONSyntaxError):
        prettify("[1,2,")


# ── Round-trip equivalence ────────────────────────────────────────────────────

def test_minify_then_prettify_equals_original():
    original = '{"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}'
    assert parse(minify(original)) == parse(original)
    assert parse(prettify(original)) == parse(original)


def test_minify_prettify_roundtrip():
    obj = {"a": [1, True, None], "b": {"c": "hello"}}
    from jsonlib.serializer import stringify
    compact = stringify(obj)
    assert parse(minify(compact)) == obj
    assert parse(prettify(compact)) == obj
