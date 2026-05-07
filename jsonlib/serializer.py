from __future__ import annotations

from datetime import date, datetime
from math import isfinite
from typing import Any

from .exceptions import JSONSerializeError
from .options import SerializeOptions


_CTRL_ESCAPE: dict[int, str] = {
    0x08: "\\b", 0x09: "\\t", 0x0A: "\\n",
    0x0C: "\\f", 0x0D: "\\r",
}


class Serializer:
    def __init__(self, options: SerializeOptions) -> None:
        self._opts = options
        self._seen: set[int] = set()

    def serialize(self, obj: Any) -> str:
        return self._build(obj, level=0)

    # ── Value dispatch ───────────────────────────────────────────────────────

    def _build(self, obj: Any, level: int) -> str:
        # Custom handlers take priority over all built-in types
        for typ, handler in self._opts.custom_handlers.items():
            if isinstance(obj, typ):
                return self._build(handler(obj), level)

        if obj is None:
            return "null"
        # bool before int: bool is a subclass of int
        if isinstance(obj, bool):
            return "true" if obj else "false"
        if isinstance(obj, int):
            return str(obj)
        if isinstance(obj, float):
            return self._float_str(obj)
        if isinstance(obj, str):
            return self._str_literal(obj)
        if isinstance(obj, (list, tuple)):
            return self._array_str(obj, level)
        if isinstance(obj, dict):
            return self._dict_str(obj, level)
        # datetime before date: datetime is a subclass of date
        if isinstance(obj, datetime):
            return self._str_literal(obj.isoformat())
        if isinstance(obj, date):
            return self._str_literal(obj.isoformat())

        raise JSONSerializeError(
            f"Type {type(obj).__name__!r} is not JSON serializable. "
            "Register a handler via SerializeOptions.custom_handlers."
        )

    # ── Scalars ──────────────────────────────────────────────────────────────

    def _float_str(self, value: float) -> str:
        if not isfinite(value):
            raise JSONSerializeError(
                f"Float value {value!r} is not JSON serializable (inf/nan). "
                "Use a custom handler to convert it to a JSON-safe representation."
            )
        return repr(value)

    def _str_literal(self, s: str) -> str:
        out: list[str] = ['"']
        for ch in s:
            cp = ord(ch)
            if ch == '"':
                out.append('\\"')
            elif ch == '\\':
                out.append('\\\\')
            elif cp in _CTRL_ESCAPE:
                out.append(_CTRL_ESCAPE[cp])
            elif cp < 0x20:
                out.append(f"\\u{cp:04x}")
            elif self._opts.ensure_ascii and cp > 0x7E:
                if cp > 0xFFFF:
                    # Encode as UTF-16 surrogate pair
                    adjusted = cp - 0x10000
                    high = 0xD800 + (adjusted >> 10)
                    low = 0xDC00 + (adjusted & 0x3FF)
                    out.append(f"\\u{high:04x}\\u{low:04x}")
                else:
                    out.append(f"\\u{cp:04x}")
            else:
                out.append(ch)
        out.append('"')
        return "".join(out)

    # ── Containers ────────────────────────────────────────────────────────────

    def _guard(self, obj: Any) -> None:
        oid = id(obj)
        if oid in self._seen:
            raise JSONSerializeError(
                "Circular reference detected: object references itself."
            )
        self._seen.add(oid)

    def _release(self, obj: Any) -> None:
        self._seen.discard(id(obj))

    def _dict_str(self, obj: dict, level: int) -> str:
        self._guard(obj)
        try:
            if not obj:
                return "{}"
            indent = self._opts.indent
            pairs = [
                (self._str_literal(str(k)), self._build(v, level + 1))
                for k, v in obj.items()
            ]
            if indent is None:
                return "{" + ",".join(f"{k}:{v}" for k, v in pairs) + "}"
            inner = " " * (indent * (level + 1))
            outer = " " * (indent * level)
            body = ",\n".join(f"{inner}{k}: {v}" for k, v in pairs)
            return "{\n" + body + "\n" + outer + "}"
        finally:
            self._release(obj)

    def _array_str(self, obj: list | tuple, level: int) -> str:
        self._guard(obj)
        try:
            if not obj:
                return "[]"
            indent = self._opts.indent
            items = [self._build(v, level + 1) for v in obj]
            if indent is None:
                return "[" + ",".join(items) + "]"
            inner = " " * (indent * (level + 1))
            outer = " " * (indent * level)
            body = ",\n".join(f"{inner}{v}" for v in items)
            return "[\n" + body + "\n" + outer + "]"
        finally:
            self._release(obj)


# ── Module-level convenience function ────────────────────────────────────────

def stringify(obj: Any, indent: int | None = None, **kwargs: Any) -> str:
    """Serialize a Python object to a JSON string."""
    valid = SerializeOptions.__dataclass_fields__
    opts: dict[str, Any] = {k: v for k, v in kwargs.items() if k in valid}
    if indent is not None:
        opts["indent"] = indent
    return Serializer(SerializeOptions(**opts)).serialize(obj)
