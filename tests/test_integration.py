"""End-to-end tests that exercise the public API from jsonlib.__init__."""
from pathlib import Path

import pytest

import jsonlib
from jsonlib import (
    JSONFileError,
    JSONLibError,
    JSONSchemaError,
    JSONSerializeError,
    JSONSyntaxError,
    ParseOptions,
    SerializeOptions,
    minify,
    parse,
    parse_file,
    prettify,
    save_file,
    stringify,
    validate,
    validate_schema,
)


# ── Public API surface ────────────────────────────────────────────────────────

def test_all_public_names_accessible():
    for name in jsonlib.__all__:
        assert hasattr(jsonlib, name)


# ── parse + stringify round-trip ──────────────────────────────────────────────

def test_roundtrip_primitives():
    for v in [None, True, False, 0, 42, -7, 3.14, "", "hello"]:
        assert parse(stringify(v)) == v


def test_roundtrip_nested():
    obj = {
        "users": [
            {"id": 1, "name": "Alice", "active": True, "score": 9.5},
            {"id": 2, "name": "Bob",   "active": False, "score": 7.0},
        ],
        "meta": {"total": 2, "tag": None},
    }
    assert parse(stringify(obj)) == obj


def test_roundtrip_unicode():
    obj = {"emoji": "😀", "japanese": "こんにちは", "arabic": "مرحبا"}
    assert parse(stringify(obj)) == obj


def test_roundtrip_empty_containers():
    assert parse(stringify({})) == {}
    assert parse(stringify([])) == []


def test_roundtrip_deeply_nested():
    # 20-level deep object
    deep = {"x": None}
    for _ in range(19):
        deep = {"child": deep}
    assert parse(stringify(deep)) == deep


# ── parse_file + save_file round-trip ────────────────────────────────────────

def test_file_roundtrip(tmp_path: Path):
    obj = {"key": [1, 2, 3], "flag": True}
    path = tmp_path / "data.json"
    save_file(obj, path)
    assert parse_file(path) == obj


def test_file_roundtrip_pretty(tmp_path: Path):
    obj = {"a": 1, "b": [True, None]}
    path = tmp_path / "pretty.json"
    save_file(obj, path, indent=2)
    assert parse_file(path) == obj


def test_file_roundtrip_unicode(tmp_path: Path):
    obj = {"greeting": "こんにちは😀"}
    path = tmp_path / "unicode.json"
    save_file(obj, path)
    assert parse_file(path) == obj


# ── validate ──────────────────────────────────────────────────────────────────

def test_validate_valid():
    assert validate('{"a": 1}') is True


def test_validate_invalid():
    assert validate("{bad}") is False


# ── validate_schema ───────────────────────────────────────────────────────────

def test_validate_schema_returns_true():
    assert validate_schema({"name": "Alice"}, {"type": "object", "required": ["name"]}) is True


def test_validate_schema_raises_on_failure():
    with pytest.raises(JSONSchemaError):
        validate_schema({}, {"required": ["name"]})


# ── minify + prettify ─────────────────────────────────────────────────────────

def test_minify_via_public_api():
    assert minify('{ "a" : 1 }') == '{"a":1}'


def test_prettify_via_public_api():
    result = prettify('{"a":1}', indent=2)
    assert result == '{\n  "a": 1\n}'


# ── Exception hierarchy ───────────────────────────────────────────────────────

def test_all_errors_inherit_jsonliberror():
    assert issubclass(JSONSyntaxError, JSONLibError)
    assert issubclass(JSONSchemaError, JSONLibError)
    assert issubclass(JSONFileError, JSONLibError)
    assert issubclass(JSONSerializeError, JSONLibError)


# ── SPEC §8 edge cases ────────────────────────────────────────────────────────

def test_edge_empty_object():
    assert parse("{}") == {}


def test_edge_empty_array():
    assert parse("[]") == []


def test_edge_null_value_vs_missing_key():
    obj = parse('{"key": null}')
    assert "key" in obj
    assert obj["key"] is None


def test_edge_duplicate_key_last_wins():
    assert parse('{"a": 1, "a": 2}')["a"] == 2


def test_edge_deep_nesting_default_limit():
    # 50 levels — must succeed with default max_depth=1000
    json_str = '{"x":' * 50 + "1" + "}" * 50
    assert parse(json_str) is not None


def test_edge_max_depth_exceeded():
    json_str = '{"x":' * 5 + "1" + "}" * 5
    with pytest.raises(JSONSyntaxError, match="[Dd]epth"):
        parse(json_str, max_depth=3)


def test_edge_circular_reference():
    d: dict = {}
    d["self"] = d
    with pytest.raises(JSONSerializeError):
        stringify(d)


def test_edge_invalid_escape():
    with pytest.raises(JSONSyntaxError):
        parse(r'"bad \q escape"')


def test_edge_trailing_comma_rejected():
    with pytest.raises(JSONSyntaxError):
        parse("[1, 2,]")


def test_edge_trailing_comma_allowed():
    assert parse("[1, 2,]", allow_trailing_comma=True) == [1, 2]


def test_edge_emoji_roundtrip():
    assert parse(stringify("😀")) == "😀"


def test_edge_surrogate_pair_in_json():
    assert parse(r'"😀"') == "😀"


def test_edge_file_not_found():
    with pytest.raises(JSONFileError):
        parse_file("/nonexistent/file.json")


def test_edge_invalid_json_file(tmp_path: Path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not valid}", encoding="utf-8")
    with pytest.raises(JSONSyntaxError):
        parse_file(bad)
