import pytest
from jsonlib.lexer import Lexer, Token, TokenType
from jsonlib.exceptions import JSONSyntaxError


def lex(text: str) -> list[Token]:
    return Lexer(text).tokenize()


def token_types(text: str) -> list[TokenType]:
    return [t.type for t in lex(text)]


# ── Simple tokens ─────────────────────────────────────────────────────────────

def test_lbrace():
    tok = lex("{")[0]
    assert tok.type == TokenType.LBRACE
    assert tok.value == "{"


def test_rbrace():
    assert lex("}")[0].type == TokenType.RBRACE


def test_lbracket():
    assert lex("[")[0].type == TokenType.LBRACKET


def test_rbracket():
    assert lex("]")[0].type == TokenType.RBRACKET


def test_colon():
    assert lex(":")[0].type == TokenType.COLON


def test_comma():
    assert lex(",")[0].type == TokenType.COMMA


def test_eof_always_last():
    tokens = lex("{}")
    assert tokens[-1].type == TokenType.EOF


def test_empty_input_produces_eof():
    tokens = lex("")
    assert len(tokens) == 1
    assert tokens[0].type == TokenType.EOF


# ── Whitespace ────────────────────────────────────────────────────────────────

def test_spaces_ignored():
    assert token_types("  {  }  ") == [TokenType.LBRACE, TokenType.RBRACE, TokenType.EOF]


def test_newline_ignored():
    assert token_types("{\n}") == [TokenType.LBRACE, TokenType.RBRACE, TokenType.EOF]


def test_tab_ignored():
    assert token_types("{\t}") == [TokenType.LBRACE, TokenType.RBRACE, TokenType.EOF]


def test_carriage_return_ignored():
    assert token_types("{\r\n}") == [TokenType.LBRACE, TokenType.RBRACE, TokenType.EOF]


# ── Literals ──────────────────────────────────────────────────────────────────

def test_true_token():
    tok = lex("true")[0]
    assert tok.type == TokenType.TRUE
    assert tok.value is True


def test_false_token():
    tok = lex("false")[0]
    assert tok.type == TokenType.FALSE
    assert tok.value is False


def test_null_token():
    tok = lex("null")[0]
    assert tok.type == TokenType.NULL
    assert tok.value is None


# ── Strings ───────────────────────────────────────────────────────────────────

def test_empty_string():
    tok = lex('""')[0]
    assert tok.type == TokenType.STRING
    assert tok.value == ""


def test_simple_string():
    assert lex('"hello"')[0].value == "hello"


def test_string_escape_double_quote():
    assert lex(r'"say \"hi\""')[0].value == 'say "hi"'


def test_string_escape_backslash():
    assert lex(r'"\\"')[0].value == "\\"


def test_string_escape_forward_slash():
    assert lex(r'"\/"')[0].value == "/"


def test_string_escape_backspace():
    assert lex(r'"\b"')[0].value == "\b"


def test_string_escape_formfeed():
    assert lex(r'"\f"')[0].value == "\f"


def test_string_escape_newline():
    assert lex(r'"\n"')[0].value == "\n"


def test_string_escape_carriage_return():
    assert lex(r'"\r"')[0].value == "\r"


def test_string_escape_tab():
    assert lex(r'"\t"')[0].value == "\t"


def test_string_unicode_escape_ascii():
    assert lex(r'"A"')[0].value == "A"  # U+0041 = 'A'


def test_string_unicode_escape_cjk():
    assert lex(r'"中"')[0].value == "中"


def test_string_unicode_escape_case_insensitive():
    assert lex(r'"O"')[0].value == "O"  # uppercase hex digits


def test_string_emoji_surrogate_pair():
    # 😀 = U+1F600, encoded as 😀
    assert lex(r'"😀"')[0].value == "\U0001F600"


def test_string_surrogate_pair_musical_note():
    # 𝄞 = U+1D11E
    assert lex(r'"𝄞"')[0].value == "\U0001D11E"


def test_string_multibyte_literal():
    assert lex('"こんにちは"')[0].value == "こんにちは"


def test_string_emoji_literal():
    assert lex('"😀"')[0].value == "😀"


# ── Numbers ───────────────────────────────────────────────────────────────────

def test_number_zero():
    tok = lex("0")[0]
    assert tok.type == TokenType.NUMBER
    assert tok.value == "0"


def test_number_positive_integer():
    assert lex("42")[0].value == "42"


def test_number_negative_integer():
    assert lex("-7")[0].value == "-7"


def test_number_float():
    assert lex("3.14")[0].value == "3.14"


def test_number_negative_float():
    assert lex("-0.5")[0].value == "-0.5"


def test_number_exponent_lower():
    assert lex("1e10")[0].value == "1e10"


def test_number_exponent_upper():
    assert lex("1E10")[0].value == "1E10"


def test_number_exponent_positive():
    assert lex("1.5e+3")[0].value == "1.5e+3"


def test_number_exponent_negative():
    assert lex("2.0e-4")[0].value == "2.0e-4"


def test_number_large():
    assert lex("9999999999999")[0].value == "9999999999999"


# ── Position tracking ─────────────────────────────────────────────────────────

def test_first_token_at_line1_col1():
    tok = lex("{}")[0]
    assert tok.line == 1
    assert tok.column == 1


def test_second_char_at_col2():
    tok = lex("{}")[1]
    assert tok.line == 1
    assert tok.column == 2


def test_newline_increments_line():
    tokens = lex('{\n"key"')
    key_tok = next(t for t in tokens if t.type == TokenType.STRING)
    assert key_tok.line == 2
    assert key_tok.column == 1


def test_column_after_spaces():
    tokens = lex("   [")
    assert tokens[0].column == 4


def test_error_location_after_newlines():
    try:
        lex("\n\n   @")
    except JSONSyntaxError as e:
        assert e.line == 3
        assert e.column == 4
    else:
        pytest.fail("Expected JSONSyntaxError")


# ── Error cases ───────────────────────────────────────────────────────────────

def test_unexpected_character():
    with pytest.raises(JSONSyntaxError, match="Unexpected character"):
        lex("@")


def test_unterminated_string():
    with pytest.raises(JSONSyntaxError, match="Unterminated string"):
        lex('"hello')


def test_invalid_escape_sequence():
    with pytest.raises(JSONSyntaxError, match="Invalid escape sequence"):
        lex(r'"\q"')


def test_unescaped_control_character():
    with pytest.raises(JSONSyntaxError, match="control character"):
        lex('"\x00"')


def test_unescaped_newline_in_string():
    with pytest.raises(JSONSyntaxError, match="control character"):
        lex('"line1\nline2"')


def test_invalid_unicode_hex_digit():
    with pytest.raises(JSONSyntaxError):
        lex(r'"\uGGGG"')


def test_incomplete_unicode_escape():
    # 3 hex digits + closing quote → "Invalid hex digit" ('"' is not hex)
    with pytest.raises(JSONSyntaxError):
        lex(r'"\u004"')

def test_truncated_unicode_escape_at_eof():
    # escape cut off by end of input entirely
    with pytest.raises(JSONSyntaxError, match="Incomplete"):
        lex(r'"\u00')


def test_unpaired_high_surrogate():
    with pytest.raises(JSONSyntaxError, match="surrogate"):
        lex(r'"\uD800"')


def test_unpaired_low_surrogate():
    with pytest.raises(JSONSyntaxError, match="surrogate"):
        lex(r'"\uDC00"')


def test_invalid_surrogate_pair_wrong_low():
    # High surrogate followed by a non-low-surrogate \u sequence
    with pytest.raises(JSONSyntaxError, match="surrogate"):
        lex(r'"\uD800A"')


def test_leading_zero_in_number():
    with pytest.raises(JSONSyntaxError, match="leading zero"):
        lex("01")


def test_minus_without_digit():
    with pytest.raises(JSONSyntaxError):
        lex("-")


def test_decimal_without_fraction_digits():
    with pytest.raises(JSONSyntaxError):
        lex("1.")


def test_exponent_without_digits():
    with pytest.raises(JSONSyntaxError):
        lex("1e")


def test_invalid_literal_uppercase_true():
    with pytest.raises(JSONSyntaxError):
        lex("True")


def test_invalid_literal_uppercase_null():
    with pytest.raises(JSONSyntaxError):
        lex("Null")


def test_syntax_error_has_suggestion():
    try:
        lex(r'"\q"')
    except JSONSyntaxError as e:
        assert e.suggestion != ""
    else:
        pytest.fail("Expected JSONSyntaxError")
