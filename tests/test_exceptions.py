import pytest
from jsonlib.exceptions import (
    JSONLibError,
    JSONSyntaxError,
    JSONSchemaError,
    JSONFileError,
    JSONSerializeError,
)


# ── 계층 구조 ──────────────────────────────────────────────────────────────────

def test_all_errors_are_jsonliberror():
    assert issubclass(JSONSyntaxError, JSONLibError)
    assert issubclass(JSONSchemaError, JSONLibError)
    assert issubclass(JSONFileError, JSONLibError)
    assert issubclass(JSONSerializeError, JSONLibError)


def test_all_errors_are_exceptions():
    assert issubclass(JSONLibError, Exception)


# ── JSONSyntaxError ────────────────────────────────────────────────────────────

def test_syntax_error_stores_location():
    err = JSONSyntaxError("unexpected token", line=3, column=12)
    assert err.line == 3
    assert err.column == 12


def test_syntax_error_str_contains_location():
    err = JSONSyntaxError("unexpected token", line=3, column=12)
    assert "Line 3" in str(err)
    assert "Col 12" in str(err)
    assert "unexpected token" in str(err)


def test_syntax_error_str_with_suggestion():
    err = JSONSyntaxError("missing closing brace", line=1, column=5, suggestion="Add }")
    assert "Add }" in str(err)


def test_syntax_error_str_without_suggestion():
    err = JSONSyntaxError("bad escape", line=1, column=1)
    assert err.suggestion == ""
    result = str(err)
    assert "—" not in result


def test_syntax_error_is_catchable_as_jsonliberror():
    with pytest.raises(JSONLibError):
        raise JSONSyntaxError("oops", line=1, column=1)


# ── JSONSchemaError ────────────────────────────────────────────────────────────

def test_schema_error_stores_path_and_rule():
    err = JSONSchemaError("value out of range", path="$.age", rule="maximum")
    assert err.path == "$.age"
    assert err.rule == "maximum"


def test_schema_error_str_contains_path():
    err = JSONSchemaError("missing field", path="$.users[0]", rule="required")
    assert "$.users[0]" in str(err)
    assert "missing field" in str(err)
    assert "required" in str(err)


def test_schema_error_defaults():
    err = JSONSchemaError("invalid type")
    assert err.path == "$"
    assert err.rule == ""


def test_schema_error_str_without_rule():
    err = JSONSchemaError("invalid type", path="$.name")
    assert "rule:" not in str(err)


# ── JSONFileError ──────────────────────────────────────────────────────────────

def test_file_error_stores_path():
    err = JSONFileError("file not found", file_path="/data/config.json")
    assert err.file_path == "/data/config.json"


def test_file_error_str_contains_path():
    err = JSONFileError("permission denied", file_path="/etc/secret.json")
    assert "/etc/secret.json" in str(err)
    assert "permission denied" in str(err)


def test_file_error_str_without_path():
    err = JSONFileError("unknown I/O error")
    assert err.file_path == ""
    assert str(err) == "unknown I/O error"


# ── JSONSerializeError ─────────────────────────────────────────────────────────

def test_serialize_error_basic():
    err = JSONSerializeError("circular reference detected")
    assert "circular reference" in str(err)


def test_serialize_error_is_catchable_as_jsonliberror():
    with pytest.raises(JSONLibError):
        raise JSONSerializeError("cannot serialize")
