from pathlib import Path

import pytest

from crudapp.exceptions import RecordNotFoundError, ValidationError
from crudapp.store import ContactStore


@pytest.fixture
def store(tmp_path: Path) -> ContactStore:
    return ContactStore(tmp_path / "contacts.json")


# ── Create ────────────────────────────────────────────────────────────────────

def test_create_returns_record_with_id(store):
    r = store.create("홍길동")
    assert r["id"] == 1
    assert r["name"] == "홍길동"


def test_create_id_auto_increments(store):
    r1 = store.create("Alice")
    r2 = store.create("Bob")
    assert r2["id"] == r1["id"] + 1


def test_create_all_fields(store):
    r = store.create("홍길동", phone="010-1234-5678", email="hong@example.com", memo="VIP")
    assert r["phone"] == "010-1234-5678"
    assert r["email"] == "hong@example.com"
    assert r["memo"]  == "VIP"


def test_create_strips_whitespace(store):
    r = store.create("  홍길동  ", phone="  010-0000-0000  ")
    assert r["name"]  == "홍길동"
    assert r["phone"] == "010-0000-0000"


def test_create_name_empty_raises(store):
    with pytest.raises(ValidationError, match="이름"):
        store.create("")


def test_create_name_whitespace_only_raises(store):
    with pytest.raises(ValidationError):
        store.create("   ")


def test_create_optional_fields_default_empty(store):
    r = store.create("Alice")
    assert r["phone"] == ""
    assert r["email"] == ""
    assert r["memo"]  == ""


def test_create_increments_count(store):
    assert store.count == 0
    store.create("Alice")
    assert store.count == 1
    store.create("Bob")
    assert store.count == 2


# ── Read All ──────────────────────────────────────────────────────────────────

def test_read_all_empty(store):
    assert store.read_all() == []


def test_read_all_returns_all_records(store):
    store.create("Alice")
    store.create("Bob")
    records = store.read_all()
    assert len(records) == 2


def test_read_all_returns_copies(store):
    store.create("Alice")
    result = store.read_all()
    result[0]["name"] = "MODIFIED"
    assert store.read_all()[0]["name"] == "Alice"


# ── Read by ID ────────────────────────────────────────────────────────────────

def test_read_by_id_found(store):
    r = store.create("Alice")
    found = store.read_by_id(r["id"])
    assert found["name"] == "Alice"


def test_read_by_id_not_found(store):
    with pytest.raises(RecordNotFoundError) as exc_info:
        store.read_by_id(999)
    assert exc_info.value.record_id == 999


def test_read_by_id_returns_copy(store):
    r = store.create("Alice")
    found = store.read_by_id(r["id"])
    found["name"] = "MODIFIED"
    assert store.read_by_id(r["id"])["name"] == "Alice"


# ── Search ────────────────────────────────────────────────────────────────────

def test_search_by_name(store):
    store.create("홍길동")
    store.create("김철수")
    results = store.search("홍")
    assert len(results) == 1
    assert results[0]["name"] == "홍길동"


def test_search_by_phone(store):
    store.create("Alice", phone="010-1111-2222")
    store.create("Bob",   phone="010-3333-4444")
    assert len(store.search("1111")) == 1


def test_search_by_email(store):
    store.create("Alice", email="alice@example.com")
    assert len(store.search("alice@")) == 1


def test_search_by_memo(store):
    store.create("Alice", memo="VIP 고객")
    assert len(store.search("VIP")) == 1


def test_search_case_insensitive(store):
    store.create("Alice", email="TEST@EXAMPLE.COM")
    assert len(store.search("test@example")) == 1


def test_search_no_match(store):
    store.create("Alice")
    assert store.search("xyz_not_found") == []


def test_search_multiple_matches(store):
    store.create("홍길동", phone="010-0001-0001")
    store.create("홍길순", phone="010-0002-0002")
    store.create("김철수", phone="010-0003-0003")
    assert len(store.search("홍")) == 2


# ── Update ────────────────────────────────────────────────────────────────────

def test_update_phone(store):
    r = store.create("Alice", phone="010-0000-0000")
    updated = store.update(r["id"], phone="010-9999-9999")
    assert updated["phone"] == "010-9999-9999"
    assert updated["name"]  == "Alice"  # 다른 필드 유지


def test_update_name(store):
    r = store.create("Alice")
    updated = store.update(r["id"], name="Alicia")
    assert updated["name"] == "Alicia"


def test_update_multiple_fields(store):
    r = store.create("Alice")
    updated = store.update(r["id"], phone="010-1111-2222", email="new@example.com")
    assert updated["phone"] == "010-1111-2222"
    assert updated["email"] == "new@example.com"


def test_update_strips_whitespace(store):
    r = store.create("Alice")
    updated = store.update(r["id"], phone="  010-1234-5678  ")
    assert updated["phone"] == "010-1234-5678"


def test_update_id_field_ignored(store):
    r = store.create("Alice")
    original_id = r["id"]
    store.update(r["id"], id="99")
    assert store.read_by_id(original_id)["id"] == original_id


def test_update_name_empty_raises(store):
    r = store.create("Alice")
    with pytest.raises(ValidationError, match="이름"):
        store.update(r["id"], name="")


def test_update_not_found(store):
    with pytest.raises(RecordNotFoundError):
        store.update(999, name="Ghost")


# ── Delete ────────────────────────────────────────────────────────────────────

def test_delete_removes_record(store):
    r = store.create("Alice")
    store.delete(r["id"])
    assert store.count == 0


def test_delete_returns_removed_record(store):
    r = store.create("Alice")
    removed = store.delete(r["id"])
    assert removed["name"] == "Alice"


def test_delete_not_found(store):
    with pytest.raises(RecordNotFoundError):
        store.delete(999)


def test_delete_only_target(store):
    r1 = store.create("Alice")
    r2 = store.create("Bob")
    store.delete(r1["id"])
    assert store.count == 1
    assert store.read_by_id(r2["id"])["name"] == "Bob"


# ── 영속성 (Persistence) ──────────────────────────────────────────────────────

def test_data_persists_across_instances(tmp_path: Path):
    path = tmp_path / "contacts.json"
    s1 = ContactStore(path)
    s1.create("Alice")
    s1.create("Bob")

    s2 = ContactStore(path)
    assert s2.count == 2
    assert s2.read_all()[0]["name"] == "Alice"


def test_next_id_does_not_reuse_deleted(tmp_path: Path):
    path = tmp_path / "contacts.json"
    s1 = ContactStore(path)
    r = s1.create("Alice")
    s1.delete(r["id"])

    s2 = ContactStore(path)
    new_r = s2.create("Bob")
    assert new_r["id"] == r["id"] + 1


def test_file_created_on_first_save(tmp_path: Path):
    path = tmp_path / "sub" / "contacts.json"
    store = ContactStore(path)
    store.create("Alice")
    assert path.exists()


def test_update_persists(tmp_path: Path):
    path = tmp_path / "contacts.json"
    s1 = ContactStore(path)
    r = s1.create("Alice")
    s1.update(r["id"], phone="010-1111-2222")

    s2 = ContactStore(path)
    assert s2.read_by_id(r["id"])["phone"] == "010-1111-2222"
