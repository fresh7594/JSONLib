# JSONLib

RFC 8259 준수 JSON 파싱 및 파일 저장 Python 라이브러리.
런타임 외부 의존성 없이 표준 라이브러리만으로 구현되었습니다.

## 특징

- **RFC 8259 완전 준수** — 6가지 JSON 타입, 유니코드(서로게이트 페어 포함), 모든 이스케이프 시퀀스
- **상세한 에러 메시지** — 오류 발생 위치(라인·컬럼)와 수정 제안 포함
- **풍부한 파서 옵션** — 최대 중첩 깊이, 후행 쉼표, 대소문자 무시, 중복 키 정책
- **원자적 파일 저장** — 임시 파일 + `os.replace()`로 쓰기 중 크래시에 안전
- **BOM 자동 처리** — UTF-8/16/32 BOM 감지 및 제거
- **JSON Schema 검증** — draft-7 서브셋(type, required, properties, enum 등)
- **커스텀 직렬화** — 사용자 정의 타입 핸들러 등록, `datetime` 기본 지원
- **제로 의존성** — Python 3.9+ 표준 라이브러리만 사용

## 설치

```bash
git clone https://github.com/fresh7594/JSONLib.git
cd JSONLib
pip install -e .
```

## 빠른 시작

```python
import jsonlib

# 파싱
data = jsonlib.parse('{"name": "Alice", "age": 30}')
print(data["name"])  # Alice

# 직렬화
json_str = jsonlib.stringify({"active": True, "score": 9.5}, indent=2)
print(json_str)
# {
#   "active": true,
#   "score": 9.5
# }

# 파일 읽기 / 저장
jsonlib.save_file(data, "output.json", indent=2)
loaded = jsonlib.parse_file("output.json")
```

## API 레퍼런스

### 파싱

```python
jsonlib.parse(text, **options)           # JSON 문자열 → Python 객체
jsonlib.parse_file(path, encoding="utf-8", **options)  # 파일 읽기 + 파싱
```

**파서 옵션 (`**options`)**

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `max_depth` | `1000` | 최대 중첩 깊이 |
| `allow_trailing_comma` | `False` | `[1, 2,]` 형태 허용 |
| `case_insensitive_keys` | `False` | 키를 소문자로 정규화 |
| `duplicate_key_policy` | `"last"` | 중복 키 처리: `"last"` 또는 `"error"` |

### 직렬화

```python
jsonlib.stringify(obj, indent=None, **options)  # Python 객체 → JSON 문자열
jsonlib.save_file(obj, path, indent=None, encoding="utf-8", **options)  # 파일로 저장
```

**직렬화 옵션 (`**options`)**

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `ensure_ascii` | `False` | 비ASCII 문자를 `\uXXXX`로 이스케이프 |
| `custom_handlers` | `{}` | `{type: callable}` 커스텀 핸들러 |

### 유효성 검사

```python
jsonlib.validate(text)                   # bool 반환 (구문 검사)
jsonlib.validate_schema(obj, schema)     # JSON Schema 검증, 실패 시 JSONSchemaError
```

### 포맷

```python
jsonlib.minify(text)                     # 공백 제거
jsonlib.prettify(text, indent=2)         # 들여쓰기 추가
```

## 사용 예시

### 파서 옵션

```python
# 후행 쉼표 허용 (JavaScript 스타일)
jsonlib.parse('[1, 2, 3,]', allow_trailing_comma=True)

# 최대 중첩 깊이 제한
jsonlib.parse('{"a": {"b": 1}}', max_depth=1)  # JSONSyntaxError

# 중복 키를 에러로 처리
jsonlib.parse('{"a": 1, "a": 2}', duplicate_key_policy="error")  # JSONSyntaxError
```

### 커스텀 직렬화

```python
from decimal import Decimal
from datetime import datetime

result = jsonlib.stringify(
    {"price": Decimal("9.99"), "created": datetime(2024, 1, 15)},
    custom_handlers={Decimal: float},
)
# {"price":9.99,"created":"2024-01-15T00:00:00"}
```

### JSON Schema 검증

```python
schema = {
    "type": "object",
    "required": ["name", "age"],
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "age":  {"type": "integer", "minimum": 0, "maximum": 150},
    },
    "additionalProperties": False,
}

jsonlib.validate_schema({"name": "Alice", "age": 30}, schema)  # OK

try:
    jsonlib.validate_schema({"name": "", "age": -1}, schema)
except jsonlib.JSONSchemaError as e:
    print(e)  # [$.name] String length 0 is less than minLength 1 (rule: minLength)
```

### 스트리밍 (JSON Lines)

```python
from jsonlib import stream_file

for record in stream_file("large.jsonl"):
    process(record)  # 한 줄씩 파싱 — 메모리 효율적
```

## 타입 매핑

| JSON | Python |
|------|--------|
| `object` | `dict` |
| `array` | `list` |
| `string` | `str` |
| `number` (정수) | `int` |
| `number` (소수) | `float` |
| `true` / `false` | `bool` |
| `null` | `None` |

## 예외 계층

```
JSONLibError
├── JSONSyntaxError      # 구문 오류 (line, column, suggestion 포함)
├── JSONSchemaError      # 스키마 위반 (path, rule 포함)
├── JSONFileError        # 파일 I/O 오류 (file_path 포함)
└── JSONSerializeError   # 직렬화 오류 (순환 참조 등)
```

```python
try:
    jsonlib.parse_file("data.json")
except jsonlib.JSONSyntaxError as e:
    print(f"Line {e.line}, Col {e.column}: {e}")
except jsonlib.JSONFileError as e:
    print(f"File error [{e.file_path}]: {e}")
```

## 개발

```bash
# 의존성 설치
pip install pytest pytest-cov

# 전체 테스트
pytest

# 단일 파일 테스트
pytest tests/test_parser.py

# 커버리지 측정
pytest --cov=jsonlib --cov-report=term-missing
```

**테스트 현황:** 316개 통과 / 커버리지 95%

## 라이선스

MIT
