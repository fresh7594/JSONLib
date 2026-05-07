# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

JSONLib는 RFC 8259 준수 JSON 파싱 및 파일 저장 Python 라이브러리다. 런타임 외부 의존성 없이 표준 라이브러리만으로 구현한다. 전체 요구사항은 `doc/SPEC.md`, 구현 계획은 `doc/PLAN.md` 참고.

## 개발 환경 명령어

```bash
# 가상환경 활성화 (Windows)
.venv\Scripts\activate

# 개발 의존성 설치
pip install pytest pytest-cov

# 전체 테스트 실행
pytest

# 단일 테스트 파일 실행
pytest tests/test_parser.py

# 단일 테스트 함수 실행
pytest tests/test_parser.py::test_parse_nested_object

# 커버리지 측정 (목표: 90% 이상)
pytest --cov=jsonlib --cov-report=term-missing
```

## 아키텍처

구현은 아직 시작되지 않았으며 `doc/PLAN.md`의 Phase 순서대로 진행한다.

### 모듈 의존성 흐름

```
exceptions.py ──┐
options.py ─────┤
                ▼
            lexer.py
                ▼
            parser.py ──────────────────────────┐
                                                 │
            serializer.py ───────────────────────┤
                                                 │
            validator.py (lexer + parser 재사용) │
                                                 │
            formatter.py (lexer 재사용) ──────────┤
                                                 │
            file_io.py (parser + serializer) ────┤
                                                 ▼
                                           __init__.py (공개 API)
```

### 핵심 설계 원칙

- **Lexer/Parser 분리**: `lexer.py`는 문자열 → 토큰 스트림, `parser.py`는 토큰 스트림 → Python 객체. 두 레이어를 독립적으로 테스트할 수 있게 분리한다.
- **옵션 중앙화**: `ParseOptions` / `SerializeOptions` dataclass(`options.py`)가 모든 설정을 보유. 함수마다 `**kwargs`로 받아 dataclass로 변환한다.
- **예외 계층**: 모든 오류는 `JSONLibError` 하위 4종(`JSONSyntaxError`, `JSONSchemaError`, `JSONFileError`, `JSONSerializeError`) 중 하나로 발생시킨다. `JSONSyntaxError`는 반드시 `line`, `column`, `suggestion`을 포함해야 한다.
- **원자적 파일 쓰기**: `file_io.py`는 `tempfile.NamedTemporaryFile` + `os.replace()`로 파일 저장 원자성을 보장한다.
- **순환 참조 감지**: `serializer.py`는 방문 중인 객체의 `id()`를 `set`으로 추적한다.

### 공개 API (`jsonlib/__init__.py`에서 노출)

```python
parse(text, **options) -> Any
parse_file(path, encoding="utf-8", **options) -> Any
stringify(obj, indent=None, **options) -> str
save_file(obj, path, indent=None, encoding="utf-8", **options) -> None
validate(text) -> bool
validate_schema(obj, schema) -> bool
minify(text) -> str
prettify(text, indent=2) -> str
```

### JSON → Python 타입 매핑

| JSON | Python |
|------|--------|
| object | `dict` |
| array | `list` |
| string | `str` |
| number (정수) | `int` |
| number (소수) | `float` |
| boolean | `bool` |
| null | `None` |

## 구현 시 주의사항

- `lexer.py`의 토큰은 `(type, value, line, column)` 4-튜플로 생성해 위치 정보를 보존한다.
- `parser.py`의 재귀 함수는 `depth` 카운터를 인자로 전달해 `ParseOptions.max_depth` 초과를 감지한다.
- `validator.py`의 스키마 검사는 JSON Schema draft 7 서브셋(`type`, `required`, `properties`, `minimum`, `maximum`, `minLength`, `maxLength`, `pattern`, `enum`, `items`, `additionalProperties`)만 구현한다.
- Python 3.9 이상만 지원하므로 `str | Path` 같은 union 타입 힌트를 사용할 수 있다 (`from __future__ import annotations` 불필요).
- 런타임 외부 라이브러리를 추가하지 않는다.
