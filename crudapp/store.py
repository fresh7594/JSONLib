from __future__ import annotations

from pathlib import Path
from typing import Any

import jsonlib
from jsonlib.exceptions import JSONFileError, JSONSyntaxError

from .exceptions import CRUDError, RecordNotFoundError, ValidationError

# 연락처 필드 정의 (id 제외)
CONTACT_FIELDS: tuple[str, ...] = ("name", "phone", "email", "memo")


class ContactStore:
    """JSON 파일 기반 연락처 CRUD 저장소.

    JSON 파일 구조:
        {
            "next_id": 3,
            "records": [
                {"id": 1, "name": "홍길동", "phone": "...", "email": "...", "memo": ""},
                ...
            ]
        }
    """

    def __init__(self, file_path: str | Path) -> None:
        self._path = Path(file_path)
        self._records: list[dict[str, Any]] = []
        self._next_id: int = 1
        self._load()

    # ── Persistence ──────────────────────────────────────────────────────────

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            data = jsonlib.parse_file(self._path)
            self._records = data.get("records", [])
            self._next_id = data.get("next_id", 1)
        except (JSONFileError, JSONSyntaxError) as exc:
            raise CRUDError(f"데이터 파일을 읽는 중 오류 발생: {exc}") from exc

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        jsonlib.save_file(
            {"next_id": self._next_id, "records": self._records},
            self._path,
            indent=2,
        )

    # ── CRUD ─────────────────────────────────────────────────────────────────

    def create(
        self,
        name: str,
        phone: str = "",
        email: str = "",
        memo: str = "",
    ) -> dict[str, Any]:
        """새 연락처를 생성하고 저장된 레코드를 반환합니다."""
        name = name.strip()
        if not name:
            raise ValidationError("이름은 필수 입력입니다.")

        record: dict[str, Any] = {
            "id":    self._next_id,
            "name":  name,
            "phone": phone.strip(),
            "email": email.strip(),
            "memo":  memo.strip(),
        }
        self._records.append(record)
        self._next_id += 1
        self._save()
        return dict(record)

    def read_all(self) -> list[dict[str, Any]]:
        """전체 연락처 목록을 반환합니다."""
        return [dict(r) for r in self._records]

    def read_by_id(self, record_id: int) -> dict[str, Any]:
        """ID로 단일 연락처를 반환합니다. 없으면 RecordNotFoundError."""
        for r in self._records:
            if r["id"] == record_id:
                return dict(r)
        raise RecordNotFoundError(record_id)

    def search(self, keyword: str) -> list[dict[str, Any]]:
        """모든 필드에서 키워드를 검색하여 일치하는 연락처 목록을 반환합니다."""
        kw = keyword.lower()
        return [
            dict(r) for r in self._records
            if any(kw in str(r.get(f, "")).lower() for f in CONTACT_FIELDS)
        ]

    def update(self, record_id: int, **fields: str) -> dict[str, Any]:
        """특정 필드를 수정하고 수정된 레코드를 반환합니다.

        id 필드는 수정 불가. name을 빈 값으로 변경하려 하면 ValidationError.
        """
        for r in self._records:
            if r["id"] == record_id:
                for key, value in fields.items():
                    if key == "id":
                        continue
                    if key == "name" and not value.strip():
                        raise ValidationError("이름은 빈 값으로 수정할 수 없습니다.")
                    if key in CONTACT_FIELDS:
                        r[key] = value.strip()
                self._save()
                return dict(r)
        raise RecordNotFoundError(record_id)

    def delete(self, record_id: int) -> dict[str, Any]:
        """연락처를 삭제하고 삭제된 레코드를 반환합니다."""
        for i, r in enumerate(self._records):
            if r["id"] == record_id:
                removed = self._records.pop(i)
                self._save()
                return dict(removed)
        raise RecordNotFoundError(record_id)

    # ── Properties ───────────────────────────────────────────────────────────

    @property
    def count(self) -> int:
        return len(self._records)

    @property
    def file_path(self) -> Path:
        return self._path
