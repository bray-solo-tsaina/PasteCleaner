"""Clipboard watcher: monitors the macOS pasteboard and auto-cleans any
content that contains a gutter character, so terminal output you copy is
paste-ready without a manual `pastecleaner -c`.

Designed to run under `launchctl` as a LaunchAgent; see contrib/ for a plist
template.
"""
from __future__ import annotations

import signal
import subprocess
import sys
import time

from pastecleaner.cli import GUTTER_CHARS, clean

POLL_INTERVAL_SEC = 0.5


def has_gutter(text: str) -> bool:
    """Return True if any of the recognized gutter glyphs appear in text."""
    return any(ch in text for ch in GUTTER_CHARS)


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
