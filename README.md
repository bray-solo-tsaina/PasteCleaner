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

### Claude Code slash command (optional)

Drop this in `~/.claude/commands/clean.md` to invoke from Claude Code via `/clean`:

```markdown
---
description: Clean the clipboard of terminal gutter/padding
---

Run `pastecleaner -c` in the shell.
```

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
