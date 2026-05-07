from __future__ import annotations

import unicodedata

from .exceptions import CRUDError, RecordNotFoundError
from .store import CONTACT_FIELDS, ContactStore

# ── 표시 레이블 ──────────────────────────────────────────────────────────────

_FIELD_LABELS: dict[str, str] = {
    "name":  "이름",
    "phone": "전화번호",
    "email": "이메일",
    "memo":  "메모",
}

_SEP = "─" * 62
_MENU_TEXT = """\

{sep}
  연락처 관리  |  {path}  |  총 {count}건
{sep}
  [1] 추가 (Create)        [2] 전체 목록 (Read All)
  [3] ID 조회 (Read)       [4] 검색 (Search)
  [5] 수정 (Update)        [6] 삭제 (Delete)
  [0] 종료
{sep}"""


# ── 한글 등 전각 문자 폭 계산 유틸리티 ──────────────────────────────────────

def _disp_width(s: str) -> int:
    """터미널에서의 표시 폭을 반환합니다 (전각=2, 반각=1)."""
    return sum(2 if unicodedata.east_asian_width(c) in ("W", "F") else 1 for c in s)


def _ljust_disp(s: str, width: int) -> str:
    """표시 폭 기준으로 왼쪽 정렬합니다."""
    return s + " " * max(0, width - _disp_width(s))


def _truncate_disp(s: str, max_width: int) -> str:
    """표시 폭 기준으로 문자열을 잘라냅니다 (초과 시 '…' 추가)."""
    result, width = "", 0
    for ch in s:
        cw = 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
        if width + cw > max_width - 1:
            return result + "…"
        result += ch
        width += cw
    return result


# ── CLI ──────────────────────────────────────────────────────────────────────

class ContactCLI:
    """연락처 관리 콘솔 인터페이스."""

    # 테이블 컬럼 표시 폭 (전각 기준)
    _COL_WIDTHS = {"id": 4, "name": 12, "phone": 14, "email": 22, "memo": 14}

    def __init__(self, store: ContactStore) -> None:
        self._store = store

    def run(self) -> None:
        print("\n  연락처 관리 시스템에 오신 것을 환영합니다!")
        while True:
            print(_MENU_TEXT.format(
                sep=_SEP,
                path=self._store.file_path,
                count=self._store.count,
            ))
            try:
                choice = input("  선택 > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n  종료합니다.")
                break

            if choice == "0":
                print("\n  종료합니다.")
                break

            handler = {
                "1": self._create,
                "2": self._read_all,
                "3": self._read_by_id,
                "4": self._search,
                "5": self._update,
                "6": self._delete,
            }.get(choice)

            if handler is None:
                print("  잘못된 선택입니다. 0~6 중에서 입력하세요.")
                continue

            try:
                handler()
            except CRUDError as e:
                print(f"\n  [오류] {e}")
            except (EOFError, KeyboardInterrupt):
                print("\n  작업이 취소되었습니다.")

    # ── 입력 헬퍼 ────────────────────────────────────────────────────────────

    @staticmethod
    def _prompt(label: str, required: bool = False, current: str = "") -> str:
        hint = " (필수)" if required else f" (현재: {current!r}, Enter 유지)" if current else " (선택)"
        while True:
            value = input(f"  {label}{hint}: ").strip()
            if required and not value:
                print("  필수 항목입니다. 다시 입력하세요.")
                continue
            return value

    @staticmethod
    def _prompt_id(label: str = "ID") -> int:
        while True:
            raw = input(f"  {label} > ").strip()
            if raw.isdigit() and int(raw) > 0:
                return int(raw)
            print("  양의 정수 ID를 입력하세요.")

    @staticmethod
    def _confirm(message: str) -> bool:
        return input(f"  {message} (y/N) > ").strip().lower() in ("y", "yes")

    # ── 표시 헬퍼 ────────────────────────────────────────────────────────────

    def _print_table(self, records: list[dict]) -> None:
        if not records:
            print("  결과가 없습니다.")
            return

        w = self._COL_WIDTHS
        header = (
            f"  {'ID':>{w['id']}} | "
            + _ljust_disp("이름", w["name"]) + " | "
            + _ljust_disp("전화번호", w["phone"]) + " | "
            + _ljust_disp("이메일", w["email"]) + " | "
            + _ljust_disp("메모", w["memo"])
        )
        sep_line = "  " + "─" * (_disp_width(header) - 2)

        print(sep_line)
        print(header)
        print(sep_line)
        for r in records:
            print(
                f"  {r['id']:>{w['id']}} | "
                + _ljust_disp(_truncate_disp(r.get("name",  ""), w["name"]),  w["name"])  + " | "
                + _ljust_disp(_truncate_disp(r.get("phone", ""), w["phone"]), w["phone"]) + " | "
                + _ljust_disp(_truncate_disp(r.get("email", ""), w["email"]), w["email"]) + " | "
                + _ljust_disp(_truncate_disp(r.get("memo",  ""), w["memo"]),  w["memo"])
            )
        print(sep_line)
        print(f"  총 {len(records)}건")

    @staticmethod
    def _print_record(r: dict) -> None:
        print()
        print(f"  {'ID':>8}: {r['id']}")
        for field, label in _FIELD_LABELS.items():
            print(f"  {label:>6}: {r.get(field, '')}")

    # ── CRUD 핸들러 ───────────────────────────────────────────────────────────

    def _create(self) -> None:
        print("\n  [ 연락처 추가 ]")
        name  = self._prompt("이름",   required=True)
        phone = self._prompt("전화번호")
        email = self._prompt("이메일")
        memo  = self._prompt("메모")
        record = self._store.create(name, phone, email, memo)
        print(f"\n  저장 완료 — ID: {record['id']},  이름: {record['name']}")

    def _read_all(self) -> None:
        print("\n  [ 전체 목록 ]")
        self._print_table(self._store.read_all())

    def _read_by_id(self) -> None:
        print("\n  [ ID 조회 ]")
        rid = self._prompt_id()
        self._print_record(self._store.read_by_id(rid))

    def _search(self) -> None:
        print("\n  [ 검색 ]")
        keyword = input("  검색어 > ").strip()
        if not keyword:
            print("  검색어를 입력하세요.")
            return
        results = self._store.search(keyword)
        print(f"\n  '{keyword}' 검색 결과 — {len(results)}건")
        self._print_table(results)

    def _update(self) -> None:
        print("\n  [ 수정 ]")
        rid = self._prompt_id()
        record = self._store.read_by_id(rid)
        self._print_record(record)

        print("\n  수정할 필드를 선택하세요:")
        field_list = list(_FIELD_LABELS.keys())
        for i, (field, label) in enumerate(_FIELD_LABELS.items(), 1):
            print(f"  [{i}] {label}")

        while True:
            sel = input("  선택 (1~4) > ").strip()
            if sel.isdigit() and 1 <= int(sel) <= len(field_list):
                chosen_field = field_list[int(sel) - 1]
                break
            print("  1~4 중에서 입력하세요.")

        label   = _FIELD_LABELS[chosen_field]
        current = record.get(chosen_field, "")
        new_val = self._prompt(label, required=(chosen_field == "name"), current=current)
        if not new_val:
            new_val = current  # Enter 입력 시 기존 값 유지

        updated = self._store.update(rid, **{chosen_field: new_val})
        print(f"\n  수정 완료 — ID: {updated['id']},  {label}: {updated[chosen_field]!r}")

    def _delete(self) -> None:
        print("\n  [ 삭제 ]")
        rid = self._prompt_id()
        record = self._store.read_by_id(rid)
        self._print_record(record)
        print()
        if self._confirm(f"ID {rid} '{record['name']}'을(를) 삭제하시겠습니까?"):
            removed = self._store.delete(rid)
            print(f"\n  삭제 완료 — ID: {removed['id']},  이름: {removed['name']}")
        else:
            print("  삭제가 취소되었습니다.")
