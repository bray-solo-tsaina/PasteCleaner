from pastecleaner.cli import clean


SAMPLE_CLAUDE = (
    "▎ Heads up on the cache-invalidation pass: the current TTL sweep runs per-key and holds the write lock for the whole batch.         \n"
    "  ▎ Switching to a chunked sweep with a 256-key batch should fix it.\n"
    "  ▎                                                         \n"
    "  ▎ Separately, the hit-ratio metric is double-counting negative lookups.\n"
    "  ▎ Worth a follow-up but not blocking.\n"
)


def test_strips_gutter_and_unwraps_paragraphs():
    out = clean(SAMPLE_CLAUDE)
    assert "▎" not in out
    # First paragraph flows on one line
    assert out.startswith("Heads up on the cache-invalidation pass:")
    assert "whole batch. Switching to a chunked sweep" in out
    # Paragraph break preserved
    assert "\n\n" in out
    # No trailing padding whitespace on any line
    for line in out.splitlines():
        assert line == line.rstrip()


def test_no_gutter_input_preserves_structure():
    src = "  hello world   \n\n  second line   \n"
    out = clean(src)
    # No gutter detected -> no unwrap, leading indent preserved
    assert out == "  hello world\n\n  second line\n"


def test_no_unwrap_keeps_line_breaks():
    out = clean(SAMPLE_CLAUDE, unwrap=False)
    assert "▎" not in out
    # Original hard line breaks retained
    assert "whole batch.\nSwitching to a chunked" in out


def test_force_unwrap_on_gutterless_input():
    src = "first line\nsecond line\n\nnext para\n"
    out = clean(src, unwrap=True)
    assert out == "first line second line\n\nnext para\n"


def test_each_supported_gutter_char():
    for ch in "▎│┃▏▌▍▐":
        src = f"{ch} hello\n  {ch} world\n"
        out = clean(src)
        assert out == "hello world\n", f"failed for gutter char {ch!r}: {out!r}"


def test_empty_input():
    assert clean("") == "\n"


def test_trailing_blank_gutter_lines_dropped():
    src = "▎ hello\n  ▎\n  ▎\n"
    out = clean(src)
    assert out == "hello\n"


def test_bullet_list_items_preserved():
    src = (
        "▎ intro:\n"
        "  ▎ - first bullet\n"
        "  ▎ - second bullet\n"
        "  ▎ - third bullet\n"
    )
    out = clean(src)
    assert out == (
        "intro:\n"
        "- first bullet\n"
        "- second bullet\n"
        "- third bullet\n"
    )


def test_list_item_wrapped_continuation_joins_back():
    src = (
        "▎ - a long bullet that wraps across\n"
        "  ▎ two terminal lines\n"
        "  ▎ - next bullet\n"
    )
    out = clean(src)
    assert out == "- a long bullet that wraps across two terminal lines\n- next bullet\n"


def test_numbered_list_preserved():
    src = "▎ 1. first\n  ▎ 2. second\n  ▎ 3) third\n"
    out = clean(src)
    assert out == "1. first\n2. second\n3) third\n"


def test_blank_line_before_list_keeps_blank():
    src = "▎ intro paragraph\n  ▎\n  ▎ - bullet one\n  ▎ - bullet two\n"
    out = clean(src)
    assert out == "intro paragraph\n\n- bullet one\n- bullet two\n"
