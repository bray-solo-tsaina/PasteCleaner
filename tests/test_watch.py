from pastecleaner.watch import has_gutter, render_plist


def test_has_gutter_detects_each_supported_char_at_line_start():
    for ch in "▎│┃▏▌▍▐":
        # Single-line panels still qualify: 1 of 1 non-blank lines matches
        assert has_gutter(f"{ch} some line"), f"missed {ch!r}"


def test_has_gutter_false_for_plain_text():
    assert not has_gutter("just regular prose with no vertical bars")
    assert not has_gutter("")
    assert not has_gutter("pipes | and / slashes are fine")


def test_has_gutter_detects_claude_sample():
    src = "▎ heads up:\n  ▎ wrapped line\n"
    assert has_gutter(src)


def test_has_gutter_ignores_middle_of_line_chars():
    # Gutter char in the middle of a line doesn't indicate a TUI panel
    assert not has_gutter("prefix │ middle │ suffix")


def test_has_gutter_ignores_tree_output():
    # `tree` uses │ internally; only 1 of 4 lines starts with a gutter glyph
    tree_output = (
        "src/\n"
        "├── a.py\n"
        "│   └── module.py\n"
        "└── b.py\n"
    )
    assert not has_gutter(tree_output)


def test_has_gutter_requires_majority():
    # 1 of 3 non-blank lines matches -> does not trigger
    assert not has_gutter("regular line\n▎ one gutter line\nanother regular\n")
    # 2 of 3 non-blank lines match -> triggers
    assert has_gutter("▎ line one\n▎ line two\nregular tail\n")


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
