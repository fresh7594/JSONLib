from __future__ import annotations

from typing import Any

from .exceptions import JSONSyntaxError
from .lexer import Lexer, Token, TokenType
from .options import ParseOptions


class Parser:
    def __init__(self, tokens: list[Token], options: ParseOptions) -> None:
        self._tokens = tokens
        self._pos = 0
        self._options = options

    def parse(self) -> Any:
        value = self._parse_value(depth=0)
        tok = self._peek()
        if tok.type != TokenType.EOF:
            raise JSONSyntaxError(
                f"Unexpected token after JSON value: {tok.value!r}",
                line=tok.line,
                column=tok.column,
                suggestion="Remove extra content after the JSON value.",
            )
        return value

    # ── Internal helpers ────────────────────────────────────────────────────

    def _peek(self) -> Token:
        return self._tokens[self._pos]

    def _consume(self) -> Token:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def _expect(self, ttype: TokenType) -> Token:
        tok = self._peek()
        if tok.type != ttype:
            raise JSONSyntaxError(
                f"Expected {ttype.value!r}, got {tok.value!r}",
                line=tok.line,
                column=tok.column,
                suggestion=f"Add or correct '{ttype.value}'.",
            )
        return self._consume()

    # ── Value dispatch ──────────────────────────────────────────────────────

    def _parse_value(self, depth: int) -> Any:
        if depth > self._options.max_depth:
            tok = self._peek()
            raise JSONSyntaxError(
                f"Maximum nesting depth ({self._options.max_depth}) exceeded",
                line=tok.line,
                column=tok.column,
                suggestion=f"Reduce nesting or increase max_depth (currently {self._options.max_depth}).",
            )

        tok = self._peek()

        if tok.type == TokenType.EOF:
            raise JSONSyntaxError(
                "Unexpected end of input: expected a JSON value",
                line=tok.line,
                column=tok.column,
                suggestion="Provide a valid JSON value (object, array, string, number, true, false, or null).",
            )
        if tok.type == TokenType.LBRACE:
            return self._parse_object(depth + 1)
        if tok.type == TokenType.LBRACKET:
            return self._parse_array(depth + 1)
        if tok.type == TokenType.STRING:
            return self._consume().value
        if tok.type == TokenType.NUMBER:
            return self._convert_number(self._consume())
        if tok.type == TokenType.TRUE:
            self._consume()
            return True
        if tok.type == TokenType.FALSE:
            self._consume()
            return False
        if tok.type == TokenType.NULL:
            self._consume()
            return None

        raise JSONSyntaxError(
            f"Unexpected token: {tok.value!r}",
            line=tok.line,
            column=tok.column,
            suggestion="Expected a JSON value: object, array, string, number, true, false, or null.",
        )

    # ── Object ──────────────────────────────────────────────────────────────

    def _parse_object(self, depth: int) -> dict:
        self._expect(TokenType.LBRACE)
        result: dict = {}
        seen_keys: set[str] = set()

        if self._peek().type == TokenType.RBRACE:
            self._consume()
            return result

        while True:
            key_tok = self._peek()
            if key_tok.type == TokenType.EOF:
                raise JSONSyntaxError(
                    "Unterminated object: missing '}'",
                    line=key_tok.line,
                    column=key_tok.column,
                    suggestion="Add a closing '}'.",
                )
            if key_tok.type != TokenType.STRING:
                raise JSONSyntaxError(
                    f"Object key must be a string, got {key_tok.value!r}",
                    line=key_tok.line,
                    column=key_tok.column,
                    suggestion='Wrap the key in double quotes (e.g., "myKey").',
                )
            self._consume()
            key: str = key_tok.value  # type: ignore[assignment]
            if self._options.case_insensitive_keys:
                key = key.lower()

            if key in seen_keys and self._options.duplicate_key_policy == "error":
                raise JSONSyntaxError(
                    f"Duplicate object key: {key!r}",
                    line=key_tok.line,
                    column=key_tok.column,
                    suggestion="Remove the duplicate key or use duplicate_key_policy='last'.",
                )
            seen_keys.add(key)

            self._expect(TokenType.COLON)
            result[key] = self._parse_value(depth)

            tok = self._peek()
            if tok.type == TokenType.RBRACE:
                self._consume()
                return result
            if tok.type == TokenType.COMMA:
                self._consume()
                if self._peek().type == TokenType.RBRACE:
                    if self._options.allow_trailing_comma:
                        self._consume()
                        return result
                    next_tok = self._peek()
                    raise JSONSyntaxError(
                        "Trailing comma in object",
                        line=next_tok.line,
                        column=next_tok.column,
                        suggestion="Remove the trailing comma or set allow_trailing_comma=True.",
                    )
                continue
            if tok.type == TokenType.EOF:
                raise JSONSyntaxError(
                    "Unterminated object: missing '}'",
                    line=tok.line,
                    column=tok.column,
                    suggestion="Add a closing '}'.",
                )
            raise JSONSyntaxError(
                f"Expected ',' or '}}' in object, got {tok.value!r}",
                line=tok.line,
                column=tok.column,
                suggestion="Separate key-value pairs with commas.",
            )

    # ── Array ───────────────────────────────────────────────────────────────

    def _parse_array(self, depth: int) -> list:
        self._expect(TokenType.LBRACKET)
        result: list = []

        if self._peek().type == TokenType.RBRACKET:
            self._consume()
            return result

        while True:
            tok = self._peek()
            if tok.type == TokenType.EOF:
                raise JSONSyntaxError(
                    "Unterminated array: missing ']'",
                    line=tok.line,
                    column=tok.column,
                    suggestion="Add a closing ']'.",
                )
            result.append(self._parse_value(depth))

            tok = self._peek()
            if tok.type == TokenType.RBRACKET:
                self._consume()
                return result
            if tok.type == TokenType.COMMA:
                self._consume()
                if self._peek().type == TokenType.RBRACKET:
                    if self._options.allow_trailing_comma:
                        self._consume()
                        return result
                    next_tok = self._peek()
                    raise JSONSyntaxError(
                        "Trailing comma in array",
                        line=next_tok.line,
                        column=next_tok.column,
                        suggestion="Remove the trailing comma or set allow_trailing_comma=True.",
                    )
                continue
            if tok.type == TokenType.EOF:
                raise JSONSyntaxError(
                    "Unterminated array: missing ']'",
                    line=tok.line,
                    column=tok.column,
                    suggestion="Add a closing ']'.",
                )
            raise JSONSyntaxError(
                f"Expected ',' or ']' in array, got {tok.value!r}",
                line=tok.line,
                column=tok.column,
                suggestion="Separate array elements with commas.",
            )

    # ── Number conversion ────────────────────────────────────────────────────

    def _convert_number(self, tok: Token) -> int | float:
        s: str = tok.value  # type: ignore[assignment]
        if "." in s or "e" in s or "E" in s:
            return float(s)
        return int(s)


# ── Module-level convenience function ───────────────────────────────────────

def parse(text: str, **kwargs: Any) -> Any:
    """Parse a JSON string and return the corresponding Python object."""
    valid = ParseOptions.__dataclass_fields__
    options = ParseOptions(**{k: v for k, v in kwargs.items() if k in valid})
    tokens = Lexer(text).tokenize()
    return Parser(tokens, options).parse()
