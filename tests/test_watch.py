from pastecleaner.watch import has_gutter, render_plist


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


def test_render_plist_has_valid_structure():
    out = render_plist()
    assert "<key>Label</key>" in out
    assert "<string>com.pastecleaner.watch</string>" in out
    assert "<key>KeepAlive</key>" in out
    assert "pastecleaner-watch" in out  # resolved binary path
    assert "{binary_path}" not in out   # template placeholder was substituted


def test_render_plist_uses_absolute_binary_path():
    # launchd requires an absolute path for ProgramArguments
    out = render_plist()
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("<string>/") or not line.startswith("<string>"):
            continue
        if "pastecleaner-watch" in line:
            assert line.startswith("<string>/"), f"non-absolute path: {line}"
