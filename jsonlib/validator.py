from __future__ import annotations

import re
from typing import Any

from .exceptions import JSONSchemaError, JSONSyntaxError
from .parser import parse as _parse


def validate(text: str) -> bool:
    """Return True if text is valid JSON, False otherwise."""
    try:
        _parse(text)
        return True
    except JSONSyntaxError:
        return False


def validate_schema(obj: Any, schema: dict) -> None:
    """Validate obj against a JSON Schema (draft 7 subset).

    Raises JSONSchemaError with path and rule information on the first failure.
    Supported keywords: type, required, properties, additionalProperties,
    items, enum, minimum, maximum, minLength, maxLength, pattern.
    """
    _validate_node(obj, schema, path="$")


# ── Internal validation ──────────────────────────────────────────────────────

_TYPE_MAP: dict[str, type | tuple[type, ...]] = {
    "string":  str,
    "number":  (int, float),
    "integer": int,
    "boolean": bool,
    "null":    type(None),
    "object":  dict,
    "array":   list,
}


def _validate_node(obj: Any, schema: dict, path: str) -> None:
    if "type" in schema:
        _check_type(obj, schema["type"], path)

    if "enum" in schema:
        if obj not in schema["enum"]:
            raise JSONSchemaError(
                f"Value {obj!r} is not one of {schema['enum']!r}",
                path=path,
                rule="enum",
            )

    if isinstance(obj, dict):
        _validate_object(obj, schema, path)

    if isinstance(obj, list):
        _validate_array(obj, schema, path)

    if isinstance(obj, str):
        _validate_string(obj, schema, path)

    if isinstance(obj, (int, float)) and not isinstance(obj, bool):
        _validate_number(obj, schema, path)


def _check_type(obj: Any, expected: str | list, path: str) -> None:
    if isinstance(expected, list):
        for t in expected:
            try:
                _check_type(obj, t, path)
                return
            except JSONSchemaError:
                pass
        raise JSONSchemaError(
            f"Value {obj!r} does not match any of types {expected!r}",
            path=path,
            rule="type",
        )

    if expected not in _TYPE_MAP:
        return  # Unknown type keyword — ignore per draft-7 spec

    python_type = _TYPE_MAP[expected]

    # bool is a subclass of int: exclude it from numeric type checks
    if expected in ("number", "integer") and isinstance(obj, bool):
        raise JSONSchemaError(
            f"Expected type {expected!r}, got 'boolean'",
            path=path,
            rule="type",
        )

    if not isinstance(obj, python_type):
        raise JSONSchemaError(
            f"Expected type {expected!r}, got {type(obj).__name__!r}",
            path=path,
            rule="type",
        )


def _validate_object(obj: dict, schema: dict, path: str) -> None:
    if "required" in schema:
        for key in schema["required"]:
            if key not in obj:
                raise JSONSchemaError(
                    f"Required key {key!r} is missing",
                    path=path,
                    rule="required",
                )

    if "properties" in schema:
        for key, sub_schema in schema["properties"].items():
            if key in obj:
                child_path = f"{path}.{key}"
                _validate_node(obj[key], sub_schema, path=child_path)

    if schema.get("additionalProperties") is False:
        allowed = set(schema.get("properties", {}).keys())
        for key in obj:
            if key not in allowed:
                raise JSONSchemaError(
                    f"Additional property {key!r} is not allowed",
                    path=f"{path}.{key}",
                    rule="additionalProperties",
                )


def _validate_array(obj: list, schema: dict, path: str) -> None:
    if "items" in schema:
        for i, item in enumerate(obj):
            _validate_node(item, schema["items"], path=f"{path}[{i}]")


def _validate_string(obj: str, schema: dict, path: str) -> None:
    if "minLength" in schema and len(obj) < schema["minLength"]:
        raise JSONSchemaError(
            f"String length {len(obj)} is less than minLength {schema['minLength']}",
            path=path,
            rule="minLength",
        )
    if "maxLength" in schema and len(obj) > schema["maxLength"]:
        raise JSONSchemaError(
            f"String length {len(obj)} exceeds maxLength {schema['maxLength']}",
            path=path,
            rule="maxLength",
        )
    if "pattern" in schema and not re.search(schema["pattern"], obj):
        raise JSONSchemaError(
            f"String {obj!r} does not match pattern {schema['pattern']!r}",
            path=path,
            rule="pattern",
        )


def _validate_number(obj: int | float, schema: dict, path: str) -> None:
    if "minimum" in schema and obj < schema["minimum"]:
        raise JSONSchemaError(
            f"Value {obj} is less than minimum {schema['minimum']}",
            path=path,
            rule="minimum",
        )
    if "maximum" in schema and obj > schema["maximum"]:
        raise JSONSchemaError(
            f"Value {obj} exceeds maximum {schema['maximum']}",
            path=path,
            rule="maximum",
        )
