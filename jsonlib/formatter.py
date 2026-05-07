from __future__ import annotations

from .parser import parse as _parse
from .serializer import stringify as _stringify


def minify(text: str) -> str:
    """Remove all unnecessary whitespace from a JSON string."""
    return _stringify(_parse(text))


def prettify(text: str, indent: int = 2) -> str:
    """Format a JSON string with consistent indentation."""
    return _stringify(_parse(text), indent=indent)
