from __future__ import annotations


class CRUDError(Exception):
    """CRUDApp 기본 예외."""


class RecordNotFoundError(CRUDError):
    """요청한 ID의 레코드가 존재하지 않을 때 발생."""

    def __init__(self, record_id: int) -> None:
        self.record_id = record_id
        super().__init__(f"ID {record_id}인 레코드를 찾을 수 없습니다.")


class ValidationError(CRUDError):
    """입력값 유효성 검사 실패 시 발생."""
