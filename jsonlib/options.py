from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class ParseOptions:
    """Configuration for the JSON parser.

    Attributes:
        max_depth: Maximum allowed nesting depth before raising JSONSyntaxError. (P-07)
        allow_trailing_comma: When True, a trailing comma before ] or } is accepted. (P-08)
        case_insensitive_keys: When True, all object keys are lowercased on parse. (P-09)
        duplicate_key_policy: How to handle duplicate keys in an object.
            'last'  — keep the last value (default, matches most JSON parsers).
            'error' — raise JSONSyntaxError on the first duplicate. (S-07)
    """

    max_depth: int = 1000
    allow_trailing_comma: bool = False
    case_insensitive_keys: bool = False
    duplicate_key_policy: str = "last"


@dataclass
class SerializeOptions:
    """Configuration for the JSON serializer.

    Attributes:
        indent: Number of spaces for pretty-print indentation.
            None produces compact (minified) output. (S-08)
        ensure_ascii: When True, non-ASCII characters are escaped as \\uXXXX.
        custom_handlers: Mapping from a type to a callable that converts an
            instance of that type into a JSON-serializable value. (S-05)
    """

    indent: int | None = None
    ensure_ascii: bool = False
    custom_handlers: dict[type, Callable[[Any], Any]] = field(default_factory=dict)
