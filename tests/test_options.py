from jsonlib.options import ParseOptions, SerializeOptions


# ── ParseOptions 기본값 ────────────────────────────────────────────────────────

def test_parse_options_defaults():
    opts = ParseOptions()
    assert opts.max_depth == 1000
    assert opts.allow_trailing_comma is False
    assert opts.case_insensitive_keys is False
    assert opts.duplicate_key_policy == "last"


def test_parse_options_custom_values():
    opts = ParseOptions(
        max_depth=50,
        allow_trailing_comma=True,
        case_insensitive_keys=True,
        duplicate_key_policy="error",
    )
    assert opts.max_depth == 50
    assert opts.allow_trailing_comma is True
    assert opts.case_insensitive_keys is True
    assert opts.duplicate_key_policy == "error"


# ── SerializeOptions 기본값 ───────────────────────────────────────────────────

def test_serialize_options_defaults():
    opts = SerializeOptions()
    assert opts.indent is None
    assert opts.ensure_ascii is False
    assert opts.custom_handlers == {}


def test_serialize_options_custom_handlers_isolated():
    opts1 = SerializeOptions()
    opts2 = SerializeOptions()
    opts1.custom_handlers[int] = str
    assert int not in opts2.custom_handlers


def test_serialize_options_custom_values():
    handler = lambda x: x.isoformat()
    opts = SerializeOptions(indent=4, ensure_ascii=True, custom_handlers={})
    opts.custom_handlers[object] = handler
    assert opts.indent == 4
    assert opts.ensure_ascii is True
    assert opts.custom_handlers[object] is handler
