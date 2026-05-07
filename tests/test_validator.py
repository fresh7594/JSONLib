import pytest

from jsonlib.exceptions import JSONSchemaError
from jsonlib.validator import validate, validate_schema


# ── validate(text) ────────────────────────────────────────────────────────────

def test_valid_object():
    assert validate('{"a": 1}') is True


def test_valid_array():
    assert validate("[1, 2, 3]") is True


def test_valid_string():
    assert validate('"hello"') is True


def test_valid_number():
    assert validate("42") is True


def test_valid_null():
    assert validate("null") is True


def test_valid_true():
    assert validate("true") is True


def test_valid_false():
    assert validate("false") is True


def test_invalid_unquoted_key():
    assert validate("{key: 1}") is False


def test_invalid_trailing_comma():
    assert validate("[1, 2,]") is False


def test_invalid_empty_string():
    assert validate("") is False


def test_invalid_incomplete():
    assert validate('{"a":') is False


# ── validate_schema: type ─────────────────────────────────────────────────────

def test_type_string_ok():
    validate_schema("hello", {"type": "string"})


def test_type_string_fail():
    with pytest.raises(JSONSchemaError, match="type"):
        validate_schema(42, {"type": "string"})


def test_type_integer_ok():
    validate_schema(42, {"type": "integer"})


def test_type_integer_rejects_float():
    with pytest.raises(JSONSchemaError, match="type"):
        validate_schema(3.14, {"type": "integer"})


def test_type_integer_rejects_bool():
    with pytest.raises(JSONSchemaError, match="type"):
        validate_schema(True, {"type": "integer"})


def test_type_number_accepts_int():
    validate_schema(42, {"type": "number"})


def test_type_number_accepts_float():
    validate_schema(3.14, {"type": "number"})


def test_type_number_rejects_bool():
    with pytest.raises(JSONSchemaError, match="type"):
        validate_schema(True, {"type": "number"})


def test_type_boolean_ok():
    validate_schema(True, {"type": "boolean"})
    validate_schema(False, {"type": "boolean"})


def test_type_boolean_rejects_int():
    with pytest.raises(JSONSchemaError, match="type"):
        validate_schema(1, {"type": "boolean"})


def test_type_null_ok():
    validate_schema(None, {"type": "null"})


def test_type_null_fail():
    with pytest.raises(JSONSchemaError, match="type"):
        validate_schema(0, {"type": "null"})


def test_type_object_ok():
    validate_schema({"a": 1}, {"type": "object"})


def test_type_array_ok():
    validate_schema([1, 2], {"type": "array"})


def test_type_union_ok():
    validate_schema(None, {"type": ["string", "null"]})
    validate_schema("hi", {"type": ["string", "null"]})


def test_type_union_fail():
    with pytest.raises(JSONSchemaError, match="type"):
        validate_schema(42, {"type": ["string", "null"]})


# ── validate_schema: required ─────────────────────────────────────────────────

def test_required_present():
    validate_schema({"name": "Alice"}, {"required": ["name"]})


def test_required_missing():
    with pytest.raises(JSONSchemaError, match="[Rr]equired"):
        validate_schema({}, {"required": ["name"]})


def test_required_multiple_missing_one():
    with pytest.raises(JSONSchemaError, match="[Rr]equired"):
        validate_schema({"name": "Alice"}, {"required": ["name", "age"]})


# ── validate_schema: properties ───────────────────────────────────────────────

def test_properties_valid():
    schema = {"properties": {"age": {"type": "integer"}}}
    validate_schema({"age": 25}, schema)


def test_properties_invalid():
    schema = {"properties": {"age": {"type": "integer"}}}
    with pytest.raises(JSONSchemaError) as exc_info:
        validate_schema({"age": "old"}, schema)
    assert "$.age" in str(exc_info.value)


def test_properties_missing_key_allowed_without_required():
    schema = {"properties": {"age": {"type": "integer"}}}
    validate_schema({}, schema)  # no error — key is optional


# ── validate_schema: additionalProperties ────────────────────────────────────

def test_additional_properties_false_ok():
    schema = {
        "properties": {"a": {}, "b": {}},
        "additionalProperties": False,
    }
    validate_schema({"a": 1, "b": 2}, schema)


def test_additional_properties_false_fail():
    schema = {
        "properties": {"a": {}},
        "additionalProperties": False,
    }
    with pytest.raises(JSONSchemaError, match="[Aa]dditional"):
        validate_schema({"a": 1, "c": 3}, schema)


def test_additional_properties_true_allows_extra():
    schema = {"properties": {"a": {}}, "additionalProperties": True}
    validate_schema({"a": 1, "z": 99}, schema)


# ── validate_schema: items ────────────────────────────────────────────────────

def test_items_valid():
    validate_schema([1, 2, 3], {"items": {"type": "integer"}})


def test_items_invalid():
    with pytest.raises(JSONSchemaError) as exc_info:
        validate_schema([1, "two", 3], {"items": {"type": "integer"}})
    assert "[1]" in str(exc_info.value)


def test_items_empty_array_ok():
    validate_schema([], {"items": {"type": "integer"}})


# ── validate_schema: enum ─────────────────────────────────────────────────────

def test_enum_ok():
    validate_schema("red", {"enum": ["red", "green", "blue"]})


def test_enum_fail():
    with pytest.raises(JSONSchemaError, match="[Ee]num|not one of"):
        validate_schema("yellow", {"enum": ["red", "green", "blue"]})


def test_enum_null_ok():
    validate_schema(None, {"enum": [None, "active"]})


# ── validate_schema: minimum / maximum ───────────────────────────────────────

def test_minimum_ok():
    validate_schema(5, {"minimum": 0})


def test_minimum_equal_ok():
    validate_schema(0, {"minimum": 0})


def test_minimum_fail():
    with pytest.raises(JSONSchemaError, match="[Mm]inimum|minimum"):
        validate_schema(-1, {"minimum": 0})


def test_maximum_ok():
    validate_schema(99, {"maximum": 100})


def test_maximum_equal_ok():
    validate_schema(100, {"maximum": 100})


def test_maximum_fail():
    with pytest.raises(JSONSchemaError, match="[Mm]aximum|maximum"):
        validate_schema(101, {"maximum": 100})


# ── validate_schema: minLength / maxLength ───────────────────────────────────

def test_min_length_ok():
    validate_schema("hi", {"minLength": 2})


def test_min_length_fail():
    with pytest.raises(JSONSchemaError, match="[Mm]in[Ll]ength|minLength"):
        validate_schema("a", {"minLength": 2})


def test_max_length_ok():
    validate_schema("hello", {"maxLength": 10})


def test_max_length_fail():
    with pytest.raises(JSONSchemaError, match="[Mm]ax[Ll]ength|maxLength"):
        validate_schema("toolongstring", {"maxLength": 5})


# ── validate_schema: pattern ─────────────────────────────────────────────────

def test_pattern_ok():
    validate_schema("abc123", {"pattern": r"^[a-z0-9]+$"})


def test_pattern_fail():
    with pytest.raises(JSONSchemaError, match="[Pp]attern"):
        validate_schema("ABC", {"pattern": r"^[a-z]+$"})


# ── validate_schema: error path ──────────────────────────────────────────────

def test_error_path_nested_object():
    schema = {
        "properties": {
            "user": {
                "properties": {
                    "age": {"type": "integer"}
                }
            }
        }
    }
    with pytest.raises(JSONSchemaError) as exc_info:
        validate_schema({"user": {"age": "not-a-number"}}, schema)
    assert "$.user.age" in str(exc_info.value)


def test_error_path_array_item():
    with pytest.raises(JSONSchemaError) as exc_info:
        validate_schema(["a", 1, "c"], {"items": {"type": "string"}})
    assert "[1]" in str(exc_info.value)


def test_error_carries_rule():
    try:
        validate_schema(-1, {"minimum": 0})
    except JSONSchemaError as e:
        assert e.rule == "minimum"
    else:
        pytest.fail("Expected JSONSchemaError")
