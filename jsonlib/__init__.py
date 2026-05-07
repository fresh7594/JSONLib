from __future__ import annotations

from pathlib import Path
from typing import Any

from .exceptions import (
    JSONFileError,
    JSONLibError,
    JSONSchemaError,
    JSONSerializeError,
    JSONSyntaxError,
)
from .file_io import read_file, stream_file, write_file
from .formatter import minify as _minify
from .formatter import prettify as _prettify
from .options import ParseOptions, SerializeOptions
from .parser import parse as _parse
from .serializer import stringify as _stringify
from .validator import validate as _validate
from .validator import validate_schema as _validate_schema


def parse(text: str, **options: Any) -> Any:
    """Parse a JSON string and return the corresponding Python object."""
    return _parse(text, **options)


def parse_file(path: str | Path, encoding: str = "utf-8", **options: Any) -> Any:
    """Read and parse a JSON file."""
    return read_file(path, encoding=encoding, **options)


def stringify(obj: Any, indent: int | None = None, **options: Any) -> str:
    """Serialize a Python object to a JSON string."""
    return _stringify(obj, indent=indent, **options)


def save_file(
    obj: Any,
    path: str | Path,
    indent: int | None = None,
    encoding: str = "utf-8",
    **options: Any,
) -> None:
    """Serialize a Python object and write it atomically to a JSON file."""
    write_file(obj, path, indent=indent, encoding=encoding, **options)


def validate(text: str) -> bool:
    """Return True if text is valid JSON, False otherwise."""
    return _validate(text)


def validate_schema(obj: Any, schema: dict) -> bool:
    """Validate obj against a JSON Schema (draft 7 subset).

    Returns True on success, raises JSONSchemaError on failure.
    """
    _validate_schema(obj, schema)
    return True


def minify(text: str) -> str:
    """Remove all unnecessary whitespace from a JSON string."""
    return _minify(text)


def prettify(text: str, indent: int = 2) -> str:
    """Format a JSON string with consistent indentation."""
    return _prettify(text, indent=indent)


__all__ = [
    # Core API
    "parse", "parse_file",
    "stringify", "save_file",
    "validate", "validate_schema",
    "minify", "prettify",
    # Options
    "ParseOptions", "SerializeOptions",
    # Exceptions
    "JSONLibError", "JSONSyntaxError",
    "JSONSchemaError", "JSONFileError", "JSONSerializeError",
    # Streaming (advanced)
    "stream_file",
]
