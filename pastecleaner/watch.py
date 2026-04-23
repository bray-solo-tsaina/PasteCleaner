"""Clipboard watcher: monitors the macOS pasteboard and auto-cleans any
content that contains a gutter character, so terminal output you copy is
paste-ready without a manual `pastecleaner -c`.

Designed to run under `launchctl` as a LaunchAgent; see contrib/ for a plist
template.
"""
from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import time

from pastecleaner.cli import GUTTER_CHARS, _is_bordered, clean

POLL_INTERVAL_SEC = 0.5

PLIST_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.pastecleaner.watch</string>
    <key>ProgramArguments</key>
    <array>
        <string>{binary_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/pastecleaner-watch.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/pastecleaner-watch.err</string>
</dict>
</plist>
"""


def render_plist() -> str:
    binary_path = shutil.which("pastecleaner-watch") or sys.argv[0]
    binary_path = os.path.abspath(binary_path)
    return PLIST_TEMPLATE.format(binary_path=binary_path)


def has_gutter(text: str) -> bool:
    """Return True if the text looks like bordered TUI output worth cleaning.

    Uses the same majority rule as the CLI (`_is_bordered`) so that a lone
    box-drawing character in tree or graph output does not trigger the
    daemon. Only flips to True when the gutter glyph appears at line-start
    on more than half of the non-blank lines.
    """
    return _is_bordered(text.splitlines())


def _pbpaste() -> str:
    return subprocess.run(["pbpaste"], capture_output=True, text=True).stdout


def _pbcopy(text: str) -> None:
    subprocess.run(["pbcopy"], input=text, text=True)


def _install_signal_handlers() -> None:
    def _exit(*_: object) -> None:
        sys.exit(0)

    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(sig, _exit)


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] in ("--print-plist", "plist"):
        sys.stdout.write(render_plist())
        return 0

    _install_signal_handlers()

    last_seen = ""
    while True:
        try:
            current = _pbpaste()
        except Exception:
            time.sleep(POLL_INTERVAL_SEC)
            continue

        if current != last_seen:
            if has_gutter(current):
                cleaned = clean(current)
                if cleaned != current:
                    _pbcopy(cleaned)
                last_seen = cleaned
            else:
                last_seen = current

        time.sleep(POLL_INTERVAL_SEC)


if __name__ == "__main__":
    sys.exit(main() or 0)
