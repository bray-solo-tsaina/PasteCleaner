"""Clean up text copied from bordered terminal output (Claude Code, lazygit, etc).

Strips a leading gutter marker (▎ │ ┃ …) plus its surrounding indentation,
trims trailing whitespace, and optionally unwraps soft-wrapped lines back
into flowing paragraphs.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

# Vertical-bar glyphs commonly used as a left gutter in TUIs.
# ▎ is what Claude Code uses; the others cover lazygit/k9s/git-log-graph/etc.
GUTTER_CHARS = "▎│┃▏▌▍▐"
GUTTER_RE = re.compile(rf"^\s*[{GUTTER_CHARS}] ?")

# Detects lines that start a list item so they aren't swallowed into the
# previous paragraph during unwrap. Supports -, *, +, •, and 1-3 digit numbers
# followed by . or ).
LIST_RE = re.compile(r"^(?:[-*+•]|\d{1,3}[.)])\s+")


def _strip_gutter(line: str) -> str:
    return GUTTER_RE.sub("", line)


def _is_bordered(raw_lines: list[str]) -> bool:
    """Return True when the input looks like bordered TUI output.

    Majority rule: more than half of the non-blank lines must begin with a
    gutter glyph (optionally after leading whitespace). This avoids firing
    on incidental box-drawing characters, e.g. the internal ``│`` in
    ``tree`` output where only a few lines start with that glyph.
    """
    non_blank = [l for l in raw_lines if l.strip()]
    if not non_blank:
        return False
    matches = sum(1 for l in non_blank if GUTTER_RE.match(l))
    return matches * 2 > len(non_blank)


def clean(text: str, unwrap: bool | None = None) -> str:
    raw_lines = text.splitlines()
    bordered = _is_bordered(raw_lines)

    if bordered:
        lines = [_strip_gutter(line).rstrip() for line in raw_lines]
    else:
        lines = [line.rstrip() for line in raw_lines]

    if unwrap is None:
        unwrap = bordered

    if not unwrap:
        return "\n".join(lines).strip("\n") + "\n"

    # Blocks: (kind, text, tight_with_prev) where kind in {"para", "item"}.
    # tight_with_prev=True means no blank line separated this block from the
    # previous one in the source (used to decide \n vs \n\n when joining).
    blocks: list[tuple[str, str, bool]] = []
    current_kind: str | None = None
    current_text = ""
    seen_blank = False

    def flush() -> None:
        nonlocal current_kind, current_text, seen_blank
        if current_text:
            blocks.append((current_kind or "para", current_text, not seen_blank))
            current_kind = None
            current_text = ""
            seen_blank = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush()
            seen_blank = True
            continue

        if LIST_RE.match(stripped):
            flush()
            current_kind = "item"
            current_text = stripped
        elif current_kind is None:
            current_kind = "para"
            current_text = stripped
        else:
            current_text += " " + stripped

    flush()

    out_parts: list[str] = []
    for i, (kind, text, tight) in enumerate(blocks):
        if i == 0:
            out_parts.append(text)
            continue
        prev_kind = blocks[i - 1][0]
        if prev_kind == "item" and kind == "item":
            sep = "\n"
        elif prev_kind == "para" and kind == "item" and tight:
            sep = "\n"
        else:
            sep = "\n\n"
        out_parts.append(sep + text)

    return "".join(out_parts) + "\n"


def _pbpaste() -> str:
    return subprocess.run(
        ["pbpaste"], capture_output=True, text=True, check=True
    ).stdout


def _pbcopy(text: str) -> None:
    subprocess.run(["pbcopy"], input=text, text=True, check=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pastecleaner",
        description="Clean up text copied from Claude Code terminal output.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        type=Path,
        help="Input file (default: read from stdin)",
    )
    parser.add_argument(
        "-i",
        "--in-place",
        action="store_true",
        help="Rewrite the input file in place",
    )
    parser.add_argument(
        "-c",
        "--clipboard",
        action="store_true",
        help="Read from and write back to the clipboard (macOS pbpaste/pbcopy)",
    )
    parser.add_argument(
        "--unwrap",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Force paragraph unwrapping on/off. Default: auto (on when a ▎ gutter is detected).",
    )
    args = parser.parse_args(argv)

    if args.in_place and not args.file:
        parser.error("--in-place requires a file argument")
    if args.clipboard and args.in_place:
        parser.error("--clipboard and --in-place are mutually exclusive")

    if args.clipboard:
        text = _pbpaste()
    elif args.file is not None:
        text = args.file.read_text()
    else:
        text = sys.stdin.read()

    cleaned = clean(text, unwrap=args.unwrap)

    if args.clipboard:
        _pbcopy(cleaned)
        sys.stderr.write(f"pastecleaner: wrote {len(cleaned)} chars to clipboard\n")
    elif args.in_place:
        args.file.write_text(cleaned)
    else:
        sys.stdout.write(cleaned)

    return 0


if __name__ == "__main__":
    sys.exit(main())
