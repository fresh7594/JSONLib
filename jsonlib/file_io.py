from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any, Iterator

from .exceptions import JSONFileError
from .options import ParseOptions, SerializeOptions
from .parser import parse as _parse
from .serializer import stringify as _stringify


# UTF BOM signatures ordered by specificity (longer BOMs first)
_BOMS: list[tuple[bytes, str]] = [
    (b"\x00\x00\xfe\xff", "utf-32-be"),
    (b"\xff\xfe\x00\x00", "utf-32-le"),
    (b"\xef\xbb\xbf",     "utf-8"),
    (b"\xfe\xff",         "utf-16-be"),
    (b"\xff\xfe",         "utf-16-le"),
]


def _strip_bom(raw: bytes, encoding: str) -> tuple[bytes, str]:
    """Remove a leading BOM and return (stripped_bytes, detected_encoding)."""
    for bom, enc in _BOMS:
        if raw.startswith(bom):
            return raw[len(bom):], enc
    return raw, encoding


def _check_readable(path: Path) -> None:
    if not path.exists():
        raise JSONFileError("File not found", file_path=str(path))
    if not path.is_file():
        raise JSONFileError("Path is not a regular file", file_path=str(path))
    if not os.access(path, os.R_OK):
        raise JSONFileError("Permission denied", file_path=str(path))


def read_file(path: str | Path, encoding: str = "utf-8", **kwargs: Any) -> Any:
    """Read a JSON file and return the parsed Python object."""
    path = Path(path)
    _check_readable(path)

    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise JSONFileError(str(exc), file_path=str(path)) from exc

    raw, encoding = _strip_bom(raw, encoding)

    try:
        text = raw.decode(encoding)
    except (UnicodeDecodeError, LookupError) as exc:
        raise JSONFileError(
            f"Cannot decode file with encoding {encoding!r}: {exc}",
            file_path=str(path),
        ) from exc

    return _parse(text, **kwargs)


def write_file(
    obj: Any,
    path: str | Path,
    indent: int | None = None,
    encoding: str = "utf-8",
    **kwargs: Any,
) -> None:
    """Serialize obj and write it atomically to a JSON file."""
    path = Path(path)
    parent = path.parent

    if not parent.exists():
        raise JSONFileError(
            f"Parent directory does not exist: {parent}", file_path=str(path)
        )
    if not os.access(parent, os.W_OK):
        raise JSONFileError(
            f"Permission denied for directory: {parent}", file_path=str(path)
        )

    text = _stringify(obj, indent=indent, **kwargs)

    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding=encoding,
            dir=parent,
            delete=False,
            suffix=".tmp",
        ) as tmp:
            tmp_path = tmp.name
            tmp.write(text)
        os.replace(tmp_path, path)
        tmp_path = None  # replaced successfully — no cleanup needed
    except OSError as exc:
        if tmp_path is not None:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        raise JSONFileError(str(exc), file_path=str(path)) from exc


def stream_file(
    path: str | Path,
    encoding: str = "utf-8",
    **kwargs: Any,
) -> Iterator[Any]:
    """Yield one parsed JSON value per non-empty line (JSON Lines format)."""
    path = Path(path)
    _check_readable(path)

    try:
        with open(path, "r", encoding=encoding) as f:
            for line in f:
                line = line.strip()
                if line:
                    yield _parse(line, **kwargs)
    except OSError as exc:
        raise JSONFileError(str(exc), file_path=str(path)) from exc
