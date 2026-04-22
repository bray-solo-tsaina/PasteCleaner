# pastecleaner

Strip the gutter and padding from terminal output you've copied, so you can paste it cleanly elsewhere.

## The problem

Modern TUIs (Claude Code, Codex CLI, lazygit, k9s, some git views) render messages inside a bordered panel with a vertical gutter glyph on the left. When you select + copy that text, you get:

- the gutter character (`▎`, `│`, `┃`, etc.) on every line
- leading whitespace to indent past the gutter
- trailing padding spaces to the terminal width
- hard line breaks at the terminal width, not at paragraph boundaries

So a single flowing paragraph pastes as a jagged block that has to be hand-edited before it's usable in an email, doc, or issue.

**Before:**

```
▎ Heads up on the cache-invalidation pass: the current TTL sweep runs per-key      
  ▎ and holds the write lock for the whole batch, which stalls writers under load.  
  ▎                                                                                  
  ▎ Switching to a chunked sweep with a 256-key batch should fix it.                 
```

**After `pastecleaner`:**

```
Heads up on the cache-invalidation pass: the current TTL sweep runs per-key and holds the write lock for the whole batch, which stalls writers under load.

Switching to a chunked sweep with a 256-key batch should fix it.
```

## Install

```
pipx install pastecleaner
```

Or from source:

```
git clone https://github.com/bray-solo-tsaina/pastecleaner
pipx install ./pastecleaner
```

## Usage

```
pastecleaner file.txt              # clean to stdout
pastecleaner -i file.txt           # rewrite file in place
pastecleaner -c                    # read clipboard, write back to clipboard (macOS)
pbpaste | pastecleaner | pbcopy    # same idea, explicit
cat output.log | pastecleaner      # stdin
```

### Flags

- `-c, --clipboard` — read from clipboard, write back to clipboard (macOS; uses `pbpaste`/`pbcopy`)
- `-i, --in-place` — rewrite the input file
- `--unwrap` / `--no-unwrap` — force paragraph unwrapping on or off. Default is auto: on when a gutter is detected, off otherwise.

### Supported gutter glyphs

Any of these are recognized as a left gutter and stripped: `▎ │ ┃ ▏ ▌ ▍ ▐`. If none of them appear in the input, `pastecleaner` just trims trailing whitespace and leaves structure alone.

## Running automatically

Three ways to avoid remembering to run `pastecleaner -c` yourself. Pick whichever matches your workflow — they're all optional; the manual CLI works fine on its own.

### 1. Clipboard-watcher daemon (macOS, recommended)

A tiny background process that polls the pasteboard and auto-cleans any content containing a gutter glyph. Runs at login, works across every app and terminal, zero keypresses.

Install:

```
pipx install pastecleaner                 # provides both `pastecleaner` and `pastecleaner-watch`
mkdir -p ~/Library/LaunchAgents
sed "s|__PASTECLEANER_WATCH_PATH__|$(which pastecleaner-watch)|" \
  contrib/com.pastecleaner.watch.plist \
  > ~/Library/LaunchAgents/com.pastecleaner.watch.plist
launchctl load ~/Library/LaunchAgents/com.pastecleaner.watch.plist
```

Check it's running:

```
launchctl list | grep pastecleaner
tail -f /tmp/pastecleaner-watch.log /tmp/pastecleaner-watch.err
```

Uninstall:

```
launchctl unload ~/Library/LaunchAgents/com.pastecleaner.watch.plist
rm ~/Library/LaunchAgents/com.pastecleaner.watch.plist
```

The daemon only rewrites the clipboard when it sees one of the supported gutter glyphs — normal copy/paste is untouched.

### 2. Hotkey (one keypress)

Bind `pbpaste | pastecleaner | pbcopy` to a shortcut in:

- **Raycast**: *Create Script Command → Shell Script*, paste the pipeline, assign a hotkey.
- **Alfred**: *Workflow → Hotkey → Run Script*, same pipeline.
- **macOS Shortcuts app** (built-in): *New Shortcut → Run Shell Script*, pick a keyboard shortcut in the shortcut's settings.

Then: copy as usual, tap your hotkey, paste.

### 3. Claude Code slash command

Drop this in `~/.claude/commands/clean.md` to invoke from Claude Code via `/clean`:

```markdown
---
description: Clean the clipboard of terminal gutter/padding
---

Run `pastecleaner -c` in the shell.
```

### 4. Claude Code Stop hook (caveat)

You can wire a hook into `~/.claude/settings.json` to run `pastecleaner -c` after every response:

```json
{
  "hooks": {
    "Stop": [
      { "hooks": [{ "type": "command", "command": "pastecleaner -c" }] }
    ]
  }
}
```

Caveat: the hook fires when Claude *finishes* its response, before you've had a chance to select and copy text. It only helps if you habitually copy *during* Claude's output (e.g. from a long reply) and paste afterwards. For anything else, the watcher daemon (option 1) is a better fit.

## Development

```
git clone https://github.com/bray-solo-tsaina/pastecleaner
cd pastecleaner
python -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'
pytest
```

## License

MIT — see [LICENSE](./LICENSE).
