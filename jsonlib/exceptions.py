from __future__ import annotations


class JSONLibError(Exception):
    """Base exception for all JSONLib errors."""


class JSONSyntaxError(JSONLibError):
    """Raised when JSON input has invalid syntax.

    Attributes:
        line: 1-based line number where the error occurred.
        column: 1-based column number where the error occurred.
        suggestion: Human-readable hint for fixing the error.
    """

    def __init__(self, message: str, line: int, column: int, suggestion: str = "") -> None:
        self.line = line
        self.column = column
        self.suggestion = suggestion
        super().__init__(message)

    def __str__(self) -> str:
        base = f"[Line {self.line}, Col {self.column}] {self.args[0]}"
        if self.suggestion:
            base += f" — {self.suggestion}"
        return base


class JSONSchemaError(JSONLibError):
    """Raised when JSON data does not conform to the given schema.

    Attributes:
        path: JSONPath expression pointing to the offending value (e.g. '$.users[0].age').
        rule: The schema keyword whose constraint was violated (e.g. 'required', 'type').
    """

    def __init__(self, message: str, path: str = "$", rule: str = "") -> None:
        self.path = path
        self.rule = rule
        super().__init__(message)

    def __str__(self) -> str:
        base = f"[{self.path}] {self.args[0]}"
        if self.rule:
            base += f" (rule: {self.rule})"
        return base


class JSONFileError(JSONLibError):
    """Raised on file I/O failures (missing file, bad encoding, permission denied).

    Attributes:
        file_path: The filesystem path that caused the error.
    """

    def __init__(self, message: str, file_path: str = "") -> None:
        self.file_path = file_path
        super().__init__(message)

    def __str__(self) -> str:
        if self.file_path:
            return f"[{self.file_path}] {self.args[0]}"
        return self.args[0]


class JSONSerializeError(JSONLibError):
    """Raised when a Python object cannot be serialized to JSON
    (e.g. circular reference, unsupported type).
    """
