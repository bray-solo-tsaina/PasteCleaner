from pastecleaner.watch import has_gutter


def test_has_gutter_detects_each_supported_char():
    for ch in "▎│┃▏▌▍▐":
        assert has_gutter(f"some line {ch} more text"), f"missed {ch!r}"


def test_has_gutter_false_for_plain_text():
    assert not has_gutter("just regular prose with no vertical bars")
    assert not has_gutter("")
    assert not has_gutter("pipes | and / slashes are fine")


def test_has_gutter_detects_claude_sample():
    src = "▎ heads up:\n  ▎ wrapped line\n"
    assert has_gutter(src)
