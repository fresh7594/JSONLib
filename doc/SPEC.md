# JSONLib 라이브러리 요구사항 명세서

## 1. 개요

JSONLib는 JSON 데이터의 파싱 및 파일 저장을 위한 Python 라이브러리입니다.
RFC 8259 표준을 준수하며, 안정성·성능·사용 편의성을 핵심 목표로 합니다.

---

## 2. 기능 요구사항

### 2.1 JSON 파싱 (Parsing)

| ID | 요구사항 | 우선순위 |
|----|----------|----------|
| P-01 | RFC 8259 표준을 완전히 준수하는 JSON 파서 구현 | Must |
| P-02 | 6가지 JSON 기본 타입 지원: string, number, boolean, null, object, array | Must |
| P-03 | 중첩 구조(object 안의 object/array) 재귀 파싱 지원 | Must |
| P-04 | 유니코드(U+0000 ~ U+10FFFF) 완전 지원 | Must |
| P-05 | 이스케이프 시퀀스 처리: `\"`, `\\`, `\/`, `\b`, `\f`, `\n`, `\r`, `\t`, `\uXXXX` | Must |
| P-06 | 공백(스페이스, 탭, 개행)을 무시하고 파싱 | Must |
| P-07 | 최대 중첩 깊이(MaxDepth) 설정 옵션 제공 | Should |
| P-08 | 후행 쉼표(trailing comma) 허용 여부 설정 옵션 제공 | Should |
| P-09 | 키 이름 대소문자 구분 여부 설정 옵션 제공 | Should |
| P-10 | JSONPath 표현식을 이용한 데이터 쿼리 지원 | Nice |

### 2.2 직렬화 / 역직렬화 (Serialization / Deserialization)

| ID | 요구사항 | 우선순위 |
|----|----------|----------|
| S-01 | Python 객체(dict, list, str, int, float, bool, None) → JSON 문자열 변환 | Must |
| S-02 | JSON 문자열 → Python 객체 변환 | Must |
| S-03 | 직렬화 후 역직렬화 시 원본 데이터 동일성 보장 (Round-trip) | Must |
| S-04 | 날짜/시간 타입을 ISO 8601 문자열로 직렬화 지원 | Should |
| S-05 | 사용자 정의 타입을 위한 커스텀 직렬화/역직렬화 핸들러 등록 | Should |
| S-06 | 순환 참조(circular reference) 감지 및 오류 발생 | Must |
| S-07 | 중복 키 처리 정책 설정 (마지막 값 사용 / 오류 발생) | Should |
| S-08 | 출력 포맷 선택: 미니파이(compact) / 예쁜 출력(pretty-print, 들여쓰기) | Must |

### 2.3 파일 I/O

| ID | 요구사항 | 우선순위 |
|----|----------|----------|
| F-01 | JSON 파일 읽기: 파일 경로를 입력받아 파싱 결과 반환 | Must |
| F-02 | JSON 파일 쓰기: Python 객체를 직렬화하여 파일로 저장 | Must |
| F-03 | UTF-8 인코딩 기본 적용, 인코딩 옵션 설정 가능 | Must |
| F-04 | 파일 쓰기 시 원자적(atomic) 저장 지원 (임시 파일 후 교체) | Should |
| F-05 | 대용량 파일을 위한 스트리밍(streaming) 읽기/쓰기 지원 | Should |
| F-06 | 파일 존재 여부, 권한 등 기본 파일 검증 수행 | Must |
| F-07 | BOM(Byte Order Mark) 포함 파일 감지 및 무시 처리 | Should |

### 2.4 유효성 검사 (Validation)

| ID | 요구사항 | 우선순위 |
|----|----------|----------|
| V-01 | JSON 구문(syntax) 유효성 검사: 괄호 매칭, 따옴표, 쉼표 위치 검증 | Must |
| V-02 | 오류 발생 시 라인 번호와 컬럼 번호를 포함한 위치 정보 제공 | Must |
| V-03 | JSON Schema(draft 7 이상) 기반 스키마 유효성 검사 | Should |
| V-04 | 필수 필드, 타입 제약, 숫자 범위, 문자열 패턴 등 스키마 규칙 지원 | Should |
| V-05 | 파싱 없이 유효성만 검사하는 `validate()` 메서드 제공 | Should |

### 2.5 에러 처리 (Error Handling)

| ID | 요구사항 | 우선순위 |
|----|----------|----------|
| E-01 | 잘못된 입력에 대해 예외(Exception)를 발생시키고 절대 크래시 없음 | Must |
| E-02 | 에러 종류 분류: 구문 오류 / 스키마 오류 / 파일 I/O 오류 | Must |
| E-03 | 에러 메시지에 오류 유형, 위치(라인·컬럼), 설명, 수정 제안 포함 | Must |
| E-04 | 라이브러리 전용 예외 클래스 계층 구조 제공 (`JSONLibError` 기반) | Must |
| E-05 | 오류 로깅(logging 모듈 연동) 지원 | Should |

---

## 3. 비기능 요구사항

### 3.1 성능

| ID | 요구사항 |
|----|----------|
| PF-01 | 100MB 이하 JSON 파일을 4GB 미만 메모리에서 처리 가능 |
| PF-02 | 스트리밍 모드에서 1GB 이상의 파일도 메모리 효율적으로 처리 |
| PF-03 | 최대 중첩 깊이 1,000단계 이상 스택 오버플로 없이 처리 |
| PF-04 | 불필요한 메모리 복사 최소화 |

### 3.2 호환성

| ID | 요구사항 |
|----|----------|
| C-01 | Python 3.9 이상 지원 |
| C-02 | 외부 의존성 최소화 (표준 라이브러리 우선 사용) |
| C-03 | Windows / macOS / Linux 크로스 플랫폼 동작 |

### 3.3 코드 품질

| ID | 요구사항 |
|----|----------|
| Q-01 | 타입 힌트(type hints) 완전 적용 |
| Q-02 | 단위 테스트 커버리지 90% 이상 |
| Q-03 | 공개 API에 대한 docstring 작성 |

---

## 4. 데이터 타입 명세

### 4.1 JSON → Python 타입 매핑

| JSON 타입 | Python 타입 |
|-----------|-------------|
| string    | `str` |
| number (정수) | `int` |
| number (소수) | `float` |
| boolean   | `bool` |
| null      | `None` |
| object    | `dict` |
| array     | `list` |

### 4.2 숫자 처리 주의사항

- 2^53을 초과하는 정수는 정밀도 손실이 발생할 수 있으며, 문자열로 저장하도록 권장
- 부동소수점 반올림 오류는 문서화하여 사용자에게 안내

---

## 5. 공개 API 설계

```python
# 파싱
def parse(text: str, **options) -> Any: ...
def parse_file(path: str | Path, encoding: str = "utf-8", **options) -> Any: ...

# 직렬화
def stringify(obj: Any, indent: int | None = None, **options) -> str: ...
def save_file(obj: Any, path: str | Path, indent: int | None = None,
              encoding: str = "utf-8", **options) -> None: ...

# 유효성 검사
def validate(text: str) -> bool: ...
def validate_schema(obj: Any, schema: dict) -> bool: ...

# 포맷
def minify(text: str) -> str: ...
def prettify(text: str, indent: int = 2) -> str: ...
```

---

## 6. 에러 클래스 계층

```
JSONLibError
├── JSONSyntaxError      # 구문 오류 (라인, 컬럼 포함)
├── JSONSchemaError      # 스키마 유효성 오류
├── JSONFileError        # 파일 읽기/쓰기 오류
└── JSONSerializeError   # 직렬화 오류 (순환 참조 등)
```

---

## 7. 인코딩 요구사항

- **기본 인코딩**: UTF-8 (RFC 8259 필수 요건)
- **지원 인코딩**: UTF-8, UTF-16 (LE/BE), UTF-32 (LE/BE)
- 네트워크 전송 시 BOM 없는 UTF-8 사용 권장
- 파일 읽기 시 BOM이 존재하면 감지하여 자동으로 무시

---

## 8. 엣지 케이스 처리 요건

| 케이스 | 처리 방법 |
|--------|-----------|
| 빈 객체 `{}` / 빈 배열 `[]` | 정상 처리 |
| 중복 키 | 설정에 따라 마지막 값 사용 또는 오류 발생 |
| 이모지·다국어 문자 | 정상 파싱 (UTF-8 완전 지원) |
| 깊은 중첩 구조 | MaxDepth 초과 시 `JSONSyntaxError` 발생 |
| 순환 참조 | `JSONSerializeError` 발생 |
| `null` vs 키 없음 | 명확히 구분하여 처리 |
| 매우 긴 문자열 값 | 스트리밍 모드에서 청크 단위 처리 |
| 잘못된 이스케이프 시퀀스 | `JSONSyntaxError` 발생 |
| 비 UTF-8 바이트 | 인코딩 오류로 `JSONFileError` 발생 |

---

## 9. 참고 표준 및 문서

- [RFC 8259](https://datatracker.ietf.org/doc/html/rfc8259) - JSON 데이터 교환 포맷 표준
- [JSON Schema](https://json-schema.org/) - JSON 스키마 검증 표준
- [ECMA-404](https://www.ecma-international.org/publications-and-standards/standards/ecma-404/) - JSON 데이터 교환 구문
