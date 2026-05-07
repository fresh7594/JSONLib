# JSONLib 구현 계획서

## 1. 프로젝트 구조

```
JSONLib/
├── jsonlib/
│   ├── __init__.py          # 공개 API 진입점
│   ├── exceptions.py        # 예외 클래스 계층
│   ├── options.py           # 파서/직렬화 옵션 dataclass
│   ├── lexer.py             # 토크나이저 (문자열 → 토큰 스트림)
│   ├── parser.py            # 파서 (토큰 스트림 → Python 객체)
│   ├── serializer.py        # 직렬화기 (Python 객체 → JSON 문자열)
│   ├── file_io.py           # 파일 읽기/쓰기
│   ├── validator.py         # 구문 및 스키마 유효성 검사
│   └── formatter.py         # minify / prettify 포맷터
├── tests/
│   ├── test_lexer.py
│   ├── test_parser.py
│   ├── test_serializer.py
│   ├── test_file_io.py
│   ├── test_validator.py
│   ├── test_formatter.py
│   └── test_integration.py
├── doc/
│   ├── SPEC.md
│   └── PLAN.md
└── pyproject.toml
```

---

## 2. 모듈별 구현 상세

### Phase 1 — 기반 인프라 (Must 항목의 전제 조건)

#### 2.1 `exceptions.py`
SPEC §6 에러 클래스 계층을 그대로 구현한다.

```python
class JSONLibError(Exception): ...

class JSONSyntaxError(JSONLibError):
    line: int
    column: int
    suggestion: str

class JSONSchemaError(JSONLibError):
    path: str          # 오류 발생 JSON 경로 (e.g. "$.users[0].age")
    rule: str          # 위반한 스키마 규칙

class JSONFileError(JSONLibError):
    file_path: str

class JSONSerializeError(JSONLibError): ...
```

- `JSONSyntaxError`는 생성 시 `line`, `column`, `suggestion`을 필수로 받는다.
- 모든 예외는 `__str__`에서 위치 정보를 포함한 메시지를 반환한다.
- 커버 요구사항: E-01 ~ E-04

#### 2.2 `options.py`
파서와 직렬화기의 설정을 한 곳에서 관리하는 dataclass.

```python
@dataclass
class ParseOptions:
    max_depth: int = 1000           # P-07
    allow_trailing_comma: bool = False  # P-08
    case_insensitive_keys: bool = False # P-09
    duplicate_key_policy: str = "last"  # "last" | "error"  (S-07)

@dataclass
class SerializeOptions:
    indent: int | None = None       # S-08: None → compact, int → pretty
    ensure_ascii: bool = False      # 비ASCII 문자를 \uXXXX로 이스케이프
    custom_handlers: dict[type, Callable] = field(default_factory=dict)  # S-05
```

---

### Phase 2 — 핵심 파싱 엔진 (Must)

#### 2.3 `lexer.py` — 토크나이저
역할: 입력 문자열을 순회하며 토큰 스트림을 생성한다. 파서로부터 파싱 로직을 분리해 각각 독립적으로 테스트할 수 있게 한다.

**토큰 종류**

| 토큰 | 대응 문자 |
|------|-----------|
| `LBRACE` | `{` |
| `RBRACE` | `}` |
| `LBRACKET` | `[` |
| `RBRACKET` | `]` |
| `COLON` | `:` |
| `COMMA` | `,` |
| `STRING` | `"..."` |
| `NUMBER` | 정수/소수/지수 |
| `TRUE` | `true` |
| `FALSE` | `false` |
| `NULL` | `null` |
| `EOF` | 입력 끝 |

**구현 포인트**

- 토큰마다 `(type, value, line, column)` 4-튜플을 생성한다 → V-02 위치 정보
- 문자열 토큰 생성 시 이스케이프 시퀀스 전부 변환: `\"`, `\\`, `\/`, `\b`, `\f`, `\n`, `\r`, `\t`, `\uXXXX` (P-05)
- `\uXXXX` + `\uXXXX` 서로게이트 쌍(surrogate pair)을 합쳐 하나의 코드포인트로 변환 (P-04)
- 잘못된 이스케이프 시퀀스 → `JSONSyntaxError` (SPEC §8 엣지케이스)
- 공백 문자(`0x20`, `0x09`, `0x0A`, `0x0D`)는 토큰을 생성하지 않고 건너뜀 (P-06)
- 커버 요구사항: P-01 ~ P-06, V-02

#### 2.4 `parser.py` — 파서
역할: Lexer가 생성한 토큰 스트림을 소비하며 Python 객체 트리를 반환한다.

**구현 포인트**

- 재귀 하강 파서(Recursive Descent Parser) 방식 채택
  - `parse_value()` → `parse_object()` / `parse_array()` / 리터럴 처리
- 재귀 호출마다 `depth` 카운터를 증가시켜 `max_depth` 초과 시 `JSONSyntaxError` 발생 (P-07)
- `allow_trailing_comma=True`면 `]`, `}` 직전의 쉼표를 허용 (P-08)
- `duplicate_key_policy="error"`면 object 파싱 중 중복 키 발견 시 `JSONSyntaxError` 발생 (S-07)
- `case_insensitive_keys=True`면 반환 dict의 키를 소문자로 정규화 (P-09)
- 숫자 토큰을 `int` 또는 `float`으로 변환 (SPEC §4.1)
- 커버 요구사항: P-01 ~ P-09, S-02, S-03, S-06, S-07

---

### Phase 3 — 직렬화 엔진 (Must)

#### 2.5 `serializer.py` — 직렬화기
역할: Python 객체를 JSON 문자열로 변환한다.

**구현 포인트**

- 타입별 변환 디스패치 테이블 방식으로 구현
  - `dict` → object, `list`/`tuple` → array, `str` → string, `int`/`float` → number, `bool` → `true`/`false`, `None` → `null`
- 순환 참조 감지: 직렬화 중 방문한 객체 `id()`를 집합(set)으로 추적, 중복 발견 시 `JSONSerializeError` 발생 (S-06)
- `custom_handlers`에 등록된 타입이면 핸들러 함수를 호출하여 JSON-직렬화 가능한 값으로 변환 (S-05)
- `datetime` 타입은 기본 핸들러로 ISO 8601 포맷 자동 직렬화 (S-04)
- `ensure_ascii=True`면 비ASCII 문자를 `\uXXXX` 형태로 이스케이프
- `indent` 옵션에 따라 compact/pretty 출력 (S-08)
- 문자열 내 제어 문자(0x00-0x1F)를 반드시 이스케이프 처리
- 커버 요구사항: S-01, S-03 ~ S-08

---

### Phase 4 — 파일 I/O (Must + Should)

#### 2.6 `file_io.py` — 파일 입출력
역할: 파일 시스템과의 모든 상호작용을 담당한다.

**읽기 흐름**

```
경로 검증 → 파일 열기(인코딩 감지) → BOM 제거 → 텍스트 반환
```

**쓰기 흐름 (원자적 저장)**

```
직렬화 → 임시파일(.tmp) 쓰기 → os.replace(tmp, 목표경로)
```

**구현 포인트**

- 파일 존재 여부·읽기 권한 검증 후 없으면 `JSONFileError` 발생 (F-06)
- `encoding` 파라미터 기본값 `"utf-8"` (F-03)
- UTF-8 BOM(`EF BB BF`), UTF-16 BOM 감지 및 자동 제거 (F-07)
- 쓰기 시 `tempfile.NamedTemporaryFile` + `os.replace()`로 원자성 보장 (F-04)
- 스트리밍 읽기: `ijson` 없이 표준 라이브러리만으로 청크 단위 처리 가능하도록 제너레이터 API 제공 (F-05)
- 비 UTF-8 바이트 시퀀스 감지 시 `JSONFileError` 발생
- 커버 요구사항: F-01 ~ F-07

---

### Phase 5 — 유효성 검사 (Must + Should)

#### 2.7 `validator.py` — 유효성 검사기
역할: 파싱 결과물 또는 원본 JSON 텍스트를 검사한다.

**구문 검사 (`validate(text)`)**

- 내부적으로 `Lexer` + `Parser`를 실행하되 반환값을 버린다
- 예외 발생 여부만 `bool`로 반환 (V-01, V-05)

**스키마 검사 (`validate_schema(obj, schema)`)**

지원 키워드 (JSON Schema draft 7 서브셋):

| 키워드 | 설명 |
|--------|------|
| `type` | 타입 제약 (`string`, `number`, `integer`, `boolean`, `null`, `object`, `array`) |
| `required` | 필수 키 목록 |
| `properties` | 각 키의 서브스키마 |
| `minimum` / `maximum` | 숫자 범위 (V-04) |
| `minLength` / `maxLength` | 문자열 길이 |
| `pattern` | 정규식 패턴 (V-04) |
| `enum` | 허용 값 목록 |
| `items` | 배열 원소 서브스키마 |
| `additionalProperties` | 추가 키 허용 여부 |

- 오류 발생 시 `JSONSchemaError`를 던지고 `path`에 JSON 경로를 포함 (V-03, V-04)
- 커버 요구사항: V-01 ~ V-05

---

### Phase 6 — 포맷터 & 공개 API (Must)

#### 2.8 `formatter.py` — 포맷터
역할: JSON 텍스트를 재파싱하지 않고 토큰 스트림 수준에서 포맷을 변환한다.

```python
def minify(text: str) -> str: ...   # 공백·개행 제거
def prettify(text: str, indent: int = 2) -> str: ...  # 들여쓰기 추가
```

- Lexer를 재사용하여 토큰 스트림을 순회하며 공백만 재조정
- 커버 요구사항: S-08

#### 2.9 `__init__.py` — 공개 API 진입점
SPEC §5의 함수 시그니처를 그대로 노출한다.

```python
from .parser import Parser
from .serializer import Serializer
from .file_io import read_file, write_file
from .validator import Validator
from .formatter import minify, prettify
from .options import ParseOptions, SerializeOptions
from .exceptions import (
    JSONLibError, JSONSyntaxError,
    JSONSchemaError, JSONFileError, JSONSerializeError,
)

def parse(text: str, **options) -> Any: ...
def parse_file(path: str | Path, encoding: str = "utf-8", **options) -> Any: ...
def stringify(obj: Any, indent: int | None = None, **options) -> str: ...
def save_file(obj: Any, path: str | Path, indent: int | None = None,
              encoding: str = "utf-8", **options) -> None: ...
def validate(text: str) -> bool: ...
def validate_schema(obj: Any, schema: dict) -> bool: ...
```

---

## 3. 구현 순서 (의존성 기반)

```
exceptions.py          (의존성 없음)
    ↓
options.py             (의존성 없음)
    ↓
lexer.py               (exceptions)
    ↓
parser.py              (lexer, exceptions, options)
    ↓
serializer.py          (exceptions, options)
    ↓
validator.py           (lexer, parser, exceptions)
    ↓
formatter.py           (lexer)
    ↓
file_io.py             (parser, serializer, exceptions, options)
    ↓
__init__.py            (전체 모듈)
```

각 모듈은 완성 즉시 해당 테스트 파일을 함께 작성한다.

---

## 4. 테스트 전략

### 4.1 단위 테스트

| 파일 | 주요 테스트 케이스 |
|------|--------------------|
| `test_lexer.py` | 각 토큰 타입 생성, 이스케이프 시퀀스, 위치 정보(line/col), 잘못된 입력 |
| `test_parser.py` | 6가지 타입 파싱, 중첩 구조, max_depth 초과, trailing comma, 중복 키 |
| `test_serializer.py` | 타입별 직렬화, 순환 참조, 커스텀 핸들러, datetime, compact/pretty |
| `test_file_io.py` | 정상 읽기/쓰기, BOM 처리, 원자적 저장, 권한 오류, 인코딩 오류 |
| `test_validator.py` | 구문 검사 정/오, 스키마 검사 각 키워드, 오류 경로 |
| `test_formatter.py` | minify/prettify 결과, 파싱과 포맷 후 동등성 |

### 4.2 통합 테스트 (`test_integration.py`)

- Round-trip: `parse(stringify(obj)) == obj` (S-03)
- 대용량 파일(10MB+) 파싱·저장 후 내용 동일성
- `parse_file` + `save_file` 왕복 검증
- 엣지 케이스 전체 목록(SPEC §8) 순회

### 4.3 커버리지 목표

- 전체 라인 커버리지 90% 이상 (Q-02)
- `pytest-cov` 사용: `pytest --cov=jsonlib --cov-report=term-missing`

---

## 5. 외부 의존성

| 라이브러리 | 용도 | 필수 여부 |
|-----------|------|-----------|
| (없음) | 핵심 구현은 표준 라이브러리만 사용 | — |
| `pytest` | 테스트 실행 | 개발 의존성 |
| `pytest-cov` | 커버리지 측정 | 개발 의존성 |

> SPEC C-02에 따라 런타임 외부 의존성은 추가하지 않는다.

---

## 6. `pyproject.toml` 구성

```toml
[project]
name = "jsonlib"
version = "0.1.0"
requires-python = ">=3.9"
dependencies = []

[project.optional-dependencies]
dev = ["pytest", "pytest-cov"]

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.coverage.run]
source = ["jsonlib"]
```

---

## 7. 구현 체크리스트

### Phase 1 — 기반 인프라
- [ ] `exceptions.py` — 예외 클래스 4종 구현
- [ ] `options.py` — `ParseOptions`, `SerializeOptions` dataclass 구현

### Phase 2 — 파싱 엔진
- [ ] `lexer.py` — 토크나이저 구현
- [ ] `test_lexer.py` — 단위 테스트 작성
- [ ] `parser.py` — 재귀 하강 파서 구현
- [ ] `test_parser.py` — 단위 테스트 작성

### Phase 3 — 직렬화 엔진
- [ ] `serializer.py` — 직렬화기 구현
- [ ] `test_serializer.py` — 단위 테스트 작성

### Phase 4 — 파일 I/O
- [ ] `file_io.py` — 읽기/쓰기/원자적 저장 구현
- [ ] `test_file_io.py` — 단위 테스트 작성

### Phase 5 — 유효성 검사
- [ ] `validator.py` — 구문·스키마 검사 구현
- [ ] `test_validator.py` — 단위 테스트 작성

### Phase 6 — 포맷터 & 공개 API
- [ ] `formatter.py` — minify / prettify 구현
- [ ] `test_formatter.py` — 단위 테스트 작성
- [ ] `__init__.py` — 공개 API 노출
- [ ] `test_integration.py` — 통합 테스트 작성
- [ ] `pyproject.toml` — 패키지 메타데이터 작성
