import os
from pathlib import Path

import pytest

from jsonlib.exceptions import JSONFileError, JSONSyntaxError
from jsonlib.file_io import read_file, stream_file, write_file


# ── read_file ─────────────────────────────────────────────────────────────────

def test_read_simple(tmp_path: Path):
    f = tmp_path / "data.json"
    f.write_text('{"key": 42}', encoding="utf-8")
    assert read_file(f) == {"key": 42}


def test_read_array(tmp_path: Path):
    f = tmp_path / "data.json"
    f.write_text("[1, 2, 3]", encoding="utf-8")
    assert read_file(f) == [1, 2, 3]


def test_read_nested(tmp_path: Path):
    data = '{"users": [{"id": 1, "name": "Alice"}]}'
    f = tmp_path / "data.json"
    f.write_text(data, encoding="utf-8")
    result = read_file(f)
    assert result["users"][0]["name"] == "Alice"


def test_read_accepts_string_path(tmp_path: Path):
    f = tmp_path / "data.json"
    f.write_text('"hello"', encoding="utf-8")
    assert read_file(str(f)) == "hello"


# ── write_file ────────────────────────────────────────────────────────────────

def test_write_simple(tmp_path: Path):
    f = tmp_path / "out.json"
    write_file({"key": 42}, f)
    assert f.exists()


def test_write_read_roundtrip(tmp_path: Path):
    obj = {"users": [{"id": 1, "active": True}, {"id": 2, "active": False}]}
    f = tmp_path / "out.json"
    write_file(obj, f)
    assert read_file(f) == obj


def test_write_pretty(tmp_path: Path):
    f = tmp_path / "out.json"
    write_file({"a": 1}, f, indent=2)
    content = f.read_text(encoding="utf-8")
    assert "\n" in content
    assert "  " in content


def test_write_overwrites_existing(tmp_path: Path):
    f = tmp_path / "out.json"
    write_file({"v": 1}, f)
    write_file({"v": 2}, f)
    assert read_file(f) == {"v": 2}


def test_write_atomic_no_temp_file_remains(tmp_path: Path):
    f = tmp_path / "out.json"
    write_file({"a": 1}, f)
    tmp_files = list(tmp_path.glob("*.tmp"))
    assert tmp_files == []


def test_write_accepts_string_path(tmp_path: Path):
    f = tmp_path / "out.json"
    write_file([1, 2], str(f))
    assert read_file(f) == [1, 2]


# ── BOM handling ──────────────────────────────────────────────────────────────

def test_read_utf8_bom(tmp_path: Path):
    f = tmp_path / "bom.json"
    f.write_bytes(b"\xef\xbb\xbf" + b'"hello"')
    assert read_file(f) == "hello"


def test_read_utf16_le_bom(tmp_path: Path):
    f = tmp_path / "bom.json"
    f.write_bytes(b"\xff\xfe" + '"hello"'.encode("utf-16-le"))
    assert read_file(f) == "hello"


def test_read_utf16_be_bom(tmp_path: Path):
    f = tmp_path / "bom.json"
    f.write_bytes(b"\xfe\xff" + '"hello"'.encode("utf-16-be"))
    assert read_file(f) == "hello"


# ── Encoding ──────────────────────────────────────────────────────────────────

def test_read_explicit_encoding(tmp_path: Path):
    f = tmp_path / "data.json"
    f.write_text('"こんにちは"', encoding="utf-8")
    assert read_file(f, encoding="utf-8") == "こんにちは"


def test_write_read_utf8_unicode(tmp_path: Path):
    f = tmp_path / "out.json"
    write_file("こんにちは😀", f)
    assert read_file(f) == "こんにちは😀"


def test_invalid_encoding_raises(tmp_path: Path):
    f = tmp_path / "data.json"
    f.write_bytes(b"\x80\x81\x82")  # not valid UTF-8
    with pytest.raises(JSONFileError, match="[Dd]ecode|[Ee]ncoding"):
        read_file(f, encoding="utf-8")


# ── Error cases ───────────────────────────────────────────────────────────────

def test_file_not_found_raises():
    with pytest.raises(JSONFileError, match="[Ff]ile not found|[Nn]ot found"):
        read_file("/nonexistent/path/data.json")


def test_path_is_directory_raises(tmp_path: Path):
    with pytest.raises(JSONFileError):
        read_file(tmp_path)


def test_parent_dir_not_exist_raises(tmp_path: Path):
    f = tmp_path / "nonexistent" / "out.json"
    with pytest.raises(JSONFileError, match="[Dd]irectory"):
        write_file({}, f)


def test_invalid_json_in_file_raises(tmp_path: Path):
    f = tmp_path / "bad.json"
    f.write_text("{bad json}", encoding="utf-8")
    with pytest.raises(JSONSyntaxError):
        read_file(f)


# ── stream_file ───────────────────────────────────────────────────────────────

def test_stream_file_jsonl(tmp_path: Path):
    f = tmp_path / "data.jsonl"
    f.write_text('{"id": 1}\n{"id": 2}\n{"id": 3}\n', encoding="utf-8")
    results = list(stream_file(f))
    assert results == [{"id": 1}, {"id": 2}, {"id": 3}]


def test_stream_file_skips_empty_lines(tmp_path: Path):
    f = tmp_path / "data.jsonl"
    f.write_text('1\n\n2\n\n3\n', encoding="utf-8")
    assert list(stream_file(f)) == [1, 2, 3]


def test_stream_file_empty_file(tmp_path: Path):
    f = tmp_path / "empty.jsonl"
    f.write_text("", encoding="utf-8")
    assert list(stream_file(f)) == []


def test_stream_file_not_found_raises():
    with pytest.raises(JSONFileError):
        list(stream_file("/nonexistent/stream.jsonl"))
