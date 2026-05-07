from __future__ import annotations

import enum
from typing import NamedTuple

from .exceptions import JSONSyntaxError


class TokenType(enum.Enum):
    LBRACE   = "{"
    RBRACE   = "}"
    LBRACKET = "["
    RBRACKET = "]"
    COLON    = ":"
    COMMA    = ","
    STRING   = "STRING"
    NUMBER   = "NUMBER"
    TRUE     = "true"
    FALSE    = "false"
    NULL     = "null"
    EOF      = "EOF"


class Token(NamedTuple):
    type: TokenType
    value: object   # str for STRING/NUMBER (raw), bool for TRUE/FALSE, None for NULL/EOF
    line: int
    column: int


_SIMPLE_TOKENS: dict[str, TokenType] = {
    "{": TokenType.LBRACE,
    "}": TokenType.RBRACE,
    "[": TokenType.LBRACKET,
    "]": TokenType.RBRACKET,
    ":": TokenType.COLON,
    ",": TokenType.COMMA,
}

_ESCAPE_MAP: dict[str, str] = {
    '"': '"', "\\": "\\", "/": "/",
    "b": "\b", "f": "\f", "n": "\n",
    "r": "\r", "t": "\t",
}


class Lexer:
    def __init__(self, text: str) -> None:
        self._text = text
        self._pos = 0
        self._line = 1
        self._col = 1

    def tokenize(self) -> list[Token]:
        tokens: list[Token] = []
        while True:
            tok = self._next_token()
            tokens.append(tok)
            if tok.type == TokenType.EOF:
                break
        return tokens

    # ── Internal helpers ────────────────────────────────────────────────────

    def _char(self) -> str:
        return self._text[self._pos] if self._pos < len(self._text) else ""

    def _advance(self) -> str:
        ch = self._text[self._pos]
        self._pos += 1
        if ch == "\n":
            self._line += 1
            self._col = 1
        else:
            self._col += 1
        return ch

    def _skip_whitespace(self) -> None:
        while self._pos < len(self._text) and self._text[self._pos] in " \t\n\r":
            self._advance()

    # ── Token dispatch ──────────────────────────────────────────────────────

    def _next_token(self) -> Token:
        self._skip_whitespace()
        if self._pos >= len(self._text):
            return Token(TokenType.EOF, None, self._line, self._col)

        line, col = self._line, self._col
        ch = self._char()

        if ch in _SIMPLE_TOKENS:
            self._advance()
            return Token(_SIMPLE_TOKENS[ch], ch, line, col)

        if ch == '"':
            return Token(TokenType.STRING, self._read_string(line, col), line, col)

        if ch == "t":
            self._read_keyword("true", line, col)
            return Token(TokenType.TRUE, True, line, col)

        if ch == "f":
            self._read_keyword("false", line, col)
            return Token(TokenType.FALSE, False, line, col)

        if ch == "n":
            self._read_keyword("null", line, col)
            return Token(TokenType.NULL, None, line, col)

        if ch == "-" or ch.isdigit():
            return Token(TokenType.NUMBER, self._read_number(line, col), line, col)

        raise JSONSyntaxError(
            f"Unexpected character: {ch!r}",
            line=line,
            column=col,
            suggestion="Check for invalid characters or unquoted strings.",
        )

    # ── String ──────────────────────────────────────────────────────────────

    def _read_string(self, str_line: int, str_col: int) -> str:
        self._advance()  # consume opening "
        parts: list[str] = []

        while self._pos < len(self._text):
            ch = self._char()

            if ch == '"':
                self._advance()
                return "".join(parts)

            if ch == "\\":
                esc_line, esc_col = self._line, self._col
                self._advance()  # consume backslash
                if self._pos >= len(self._text):
                    raise JSONSyntaxError(
                        "Unterminated escape sequence at end of input",
                        line=esc_line,
                        column=esc_col,
                        suggestion="Complete the escape sequence.",
                    )
                esc = self._advance()
                if esc in _ESCAPE_MAP:
                    parts.append(_ESCAPE_MAP[esc])
                elif esc == "u":
                    parts.append(self._read_unicode_escape(esc_line, esc_col))
                else:
                    raise JSONSyntaxError(
                        f"Invalid escape sequence: \\{esc}",
                        line=esc_line,
                        column=esc_col,
                        suggestion=r'Valid escapes: \", \\, \/, \b, \f, \n, \r, \t, \uXXXX.',
                    )
                continue

            if ord(ch) < 0x20:
                raise JSONSyntaxError(
                    f"Unescaped control character (U+{ord(ch):04X}) in string",
                    line=self._line,
                    column=self._col,
                    suggestion="Escape control characters (e.g., use \\n for newline).",
                )

            parts.append(ch)
            self._advance()

        raise JSONSyntaxError(
            'Unterminated string: missing closing \'"\'',
            line=str_line,
            column=str_col,
            suggestion='Add a closing double-quote ".',
        )

    def _read_unicode_escape(self, esc_line: int, esc_col: int) -> str:
        high_hex = self._read_hex4(esc_line, esc_col)
        high_val = int(high_hex, 16)

        if 0xD800 <= high_val <= 0xDBFF:
            # High surrogate — must be immediately followed by \uLOW
            if (
                self._pos + 1 < len(self._text)
                and self._text[self._pos] == "\\"
                and self._text[self._pos + 1] == "u"
            ):
                self._advance()  # consume \
                self._advance()  # consume u
                low_hex = self._read_hex4(esc_line, esc_col)
                low_val = int(low_hex, 16)
                if 0xDC00 <= low_val <= 0xDFFF:
                    code_point = 0x10000 + ((high_val - 0xD800) << 10) + (low_val - 0xDC00)
                    return chr(code_point)
                raise JSONSyntaxError(
                    f"Invalid surrogate pair: \\u{high_hex}\\u{low_hex}",
                    line=esc_line,
                    column=esc_col,
                    suggestion="High surrogate (\\uD800–\\uDBFF) must be followed by a low surrogate (\\uDC00–\\uDFFF).",
                )
            raise JSONSyntaxError(
                f"Unpaired high surrogate: \\u{high_hex}",
                line=esc_line,
                column=esc_col,
                suggestion="High surrogate must be immediately followed by a low surrogate.",
            )

        if 0xDC00 <= high_val <= 0xDFFF:
            raise JSONSyntaxError(
                f"Unpaired low surrogate: \\u{high_hex}",
                line=esc_line,
                column=esc_col,
                suggestion="Low surrogate cannot appear without a preceding high surrogate.",
            )

        return chr(high_val)

    def _read_hex4(self, esc_line: int, esc_col: int) -> str:
        digits = ""
        for _ in range(4):
            if self._pos >= len(self._text):
                raise JSONSyntaxError(
                    "Incomplete \\uXXXX escape: expected 4 hex digits",
                    line=esc_line,
                    column=esc_col,
                    suggestion="Provide exactly 4 hexadecimal digits after \\u.",
                )
            ch = self._char()
            if ch not in "0123456789abcdefABCDEF":
                raise JSONSyntaxError(
                    f"Invalid hex digit {ch!r} in \\uXXXX escape",
                    line=self._line,
                    column=self._col,
                    suggestion="Use only hexadecimal digits (0-9, a-f, A-F).",
                )
            digits += ch
            self._advance()
        return digits

    # ── Number ──────────────────────────────────────────────────────────────

    def _read_number(self, line: int, col: int) -> str:
        start = self._pos

        if self._char() == "-":
            self._advance()
            if self._pos >= len(self._text) or not self._char().isdigit():
                raise JSONSyntaxError(
                    "Expected digit after '-'",
                    line=line,
                    column=col,
                    suggestion="A number must have at least one digit after '-'.",
                )

        if self._char() == "0":
            self._advance()
            if self._pos < len(self._text) and self._char().isdigit():
                raise JSONSyntaxError(
                    "Invalid number: leading zeros are not allowed",
                    line=line,
                    column=col,
                    suggestion="Remove the leading zero (e.g., use 1 instead of 01).",
                )
        else:
            if not self._char().isdigit():
                raise JSONSyntaxError(
                    "Expected digit",
                    line=line,
                    column=col,
                    suggestion="Numbers must start with a digit.",
                )
            while self._pos < len(self._text) and self._char().isdigit():
                self._advance()

        # Fractional part
        if self._pos < len(self._text) and self._char() == ".":
            self._advance()
            if self._pos >= len(self._text) or not self._char().isdigit():
                raise JSONSyntaxError(
                    "Expected digit after decimal point",
                    line=line,
                    column=col,
                    suggestion="Add at least one digit after the decimal point.",
                )
            while self._pos < len(self._text) and self._char().isdigit():
                self._advance()

        # Exponent part
        if self._pos < len(self._text) and self._char() in "eE":
            self._advance()
            if self._pos < len(self._text) and self._char() in "+-":
                self._advance()
            if self._pos >= len(self._text) or not self._char().isdigit():
                raise JSONSyntaxError(
                    "Expected digit in exponent",
                    line=line,
                    column=col,
                    suggestion="Add at least one digit in the exponent.",
                )
            while self._pos < len(self._text) and self._char().isdigit():
                self._advance()

        return self._text[start : self._pos]

    # ── Keyword ─────────────────────────────────────────────────────────────

    def _read_keyword(self, word: str, line: int, col: int) -> None:
        for expected in word:
            if self._pos >= len(self._text):
                raise JSONSyntaxError(
                    f"Unexpected end of input while reading '{word}'",
                    line=line,
                    column=col,
                    suggestion=f"Did you mean '{word}'?",
                )
            actual = self._advance()
            if actual != expected:
                raise JSONSyntaxError(
                    f"Invalid literal: expected '{word}'",
                    line=line,
                    column=col,
                    suggestion=f"Use lowercase '{word}'.",
                )
