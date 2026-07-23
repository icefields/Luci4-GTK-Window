> AI Warning: This Readme is partially AI genereated, I asked the llm to analyze and describe the code, create a table of content, and formatting.
> 
# GtkCmdWindow

A minimal, suckless-like GTK4 window that runs a shell command and displays its output in a monospace text view. Configure the command in `config.json`, run the app, done.

ANSI escape codes (colors, cursor moves, progress bars) are automatically stripped so output from tools like `curl`, `htop`, `neofetch`, or any CLI program renders as clean text — no escape sequence garbage.

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
  - [Config Options](#config-options)
  - [Config Examples](#config-examples)
- [How It Works](#how-it-works)
- [Code Description](#code-description)
  - [File Structure](#file-structure)
  - [main.py Reference](#mainpy-reference)
- [ANSI Stripping](#ansi-stripping)
- [Dependencies](#dependencies)
- [License](#license)

---

## Installation

### Prerequisites

- **Python 3.10+**
- **GTK4** development libraries
- **PyGObject** (the `gi` Python bindings)

On Arch Linux:

```bash
sudo pacman -S gtk4 python-gobject
```

On Debian:

```bash
sudo apt install libgtk-4-dev python3-gi python3-gi-cairo gir1.2-gtk-4.0
```

### No installation needed — just run it

```bash
cd ~/Code/Python/GtkCmdWindow
python3 main.py
```

Or specify a custom config path:

```bash
python3 main.py /path/to/my-config.json
```

---

## Quick Start

1. Edit `config.json`:

```json
{
    "command": "curl wttr.in"
}
```

2. Run:

```bash
python3 main.py
```

3. A GTK window opens showing the weather forecast, clean, no ANSI garbage.

---

## Configuration

All configuration is done through a single JSON file. By default the app looks for `config.json` in the current directory, but you can pass a custom path as the first argument:

```bash
python3 main.py ~/my-configs/weather.json
```

### Config Options

| Key | Type | Required | Default | Description |
|-----|------|----------|---------|-------------|
| `command` | string | Yes | — | Shell command to execute. Output (stdout) is captured and displayed. |
| `width` | int | No | 600 | Initial window width in pixels. |
| `height` | int | No | 400 | Initial window height in pixels. |

### Config Examples

**Weather forecast (wttr.in):**

```json
{
    "command": "curl wttr.in"
}
```

**Weather, compact mode:**

```json
{
    "command": "curl wttr.in?format=3"
}
```

**System info (neofetch):**

```json
{
    "command": "neofetch"
}
```

**Disk usage:**

```json
{
    "command": "df -h"
}
```

**NPB baseball results (using the npb-fetch CLI):**

```json
{
    "command": "~/Code/Python/BaseballNpbFetch/.venv/bin/npb-fetch schedule recent && echo ' ' && ~/Code/Python/BaseballNpbFetch/.venv/bin/npb-fetch standings central 2026 && echo ' ' && ~/Code/Python/BaseballNpbFetch/.venv/bin/npb-fetch standings pacific 2026",
    "width": 800,
    "height": 600
}
```

**Multiple commands chained with `&&`:**

```json
{
    "command": "echo '=== UPTIME ===' && uptime && echo '' && echo '=== MEMORY ===' && free -h && echo '' && echo '=== DISK ===' && df -h /",
    "width": 700,
    "height": 500
}
```

**Calendar:**

```json
{
    "command": "cal -y",
    "width": 800,
    "height": 600
}
```

**Git log (last 20 commits):**

```json
{
    "command": "git -C ~/Code/Python/BaseballNpbFetch log --oneline -20",
    "width": 900,
    "height": 500
}
```

**Custom script:**

```json
{
    "command": "~/scripts/morning-report.sh",
    "width": 720,
    "height": 800
}
```

---

## How It Works

1. **Read config** — loads `config.json` (or the path passed as argv[1]).
2. **Run command** — executes the `command` string via `subprocess.run(shell=True)`, capturing stdout. If stdout is empty but stderr has content, stderr is used instead (useful for commands that write diagnostics to stderr).
3. **Clean output** — strips all ANSI escape sequences (color codes, cursor moves, OSC sequences) and normalizes line endings (removes `\r` from curl's progress bar, collapses excessive blank lines).
4. **Display** — creates a GTK4 `ApplicationWindow` with a `ScrolledWindow` containing a `TextView` with a monospace font. The cleaned output is set as the buffer text. The window is non-editable (read-only).

The app runs once — it executes the command at startup, displays the output, and stays open until you close the window. It does not refresh or poll. For live-updating output, you'd need to add a timer or a refresh button (not currently implemented — keeping it suckless).

---

## Code Description

### File Structure

```
GtkCmdWindow/
├── main.py          # The entire application — single file, ~100 lines
├── config.json      # Default configuration
└── README.md        # This file
```

No build system, no dependencies beyond GTK4 and PyGObject. Just `python3 main.py`.

### main.py Reference

The file is organized into three sections:

#### ANSI Escape Code Stripper

A regex-based ANSI escape sequence remover. The regex (`_ANSI_FULL_RE`) matches four categories of escape sequences:

| Pattern | Matches | Example |
|---------|---------|---------|
| `\x1b\[[0-9;?]*[a-zA-Z]` | CSI sequences (colors, cursor moves, styling) | `\x1b[38;5;226m` (256-color yellow), `\x1b[0m` (reset), `\x1b[1m` (bold) |
| `\x1b\][^\x07\x1b]*(?:\x07\|\x1b\\)` | OSC sequences (window title, hyperlinks) | `\x1b]0;My Title\x07` |
| `\x1b[@-Z\\-_]` | Single-character escapes | `\x1bM` (reverse line feed) |
| `\x1b[()][AB0]` | Charset designation sequences | `\x1b(B` (US ASCII) |

**`stripAnsi(text: str) -> str`** — removes all ANSI escape sequences from the input string. Pure regex substitution, no state machine. Handles the vast majority of real-world CLI output (curl, htop, neofetch, etc.).

**`cleanOutput(text: str) -> str`** — full output cleaning pipeline:
1. Strip ANSI escape codes via `stripAnsi()`
2. Normalize line endings: `\r\n` → `\n`, standalone `\r` → `\n` (curl's progress bar uses `\r` to overwrite the same line)
3. Collapse runs of 3+ consecutive newlines into 2 (removes progress bar remnants)
4. Strip leading/trailing whitespace

#### Main Function

**`main() -> int`** — the entry point. Accepts an optional config path as `sys.argv[1]` (defaults to `config.json`).

Flow:
1. Load and parse the JSON config file
2. Run the command via `subprocess.run(shell=True, capture_output=True)` with UTF-8 encoding and `errors="replace"` (handles invalid UTF-8 gracefully)
3. Use stdout; fall back to stderr if stdout is empty
4. Clean the output via `cleanOutput()`
5. Create a `Gtk.Application` with ID `"lucie.cliviewer"`
6. On activate: build the window (see below)
7. Run the GTK main loop

#### Window Construction (inside `on_activate`)

The widget hierarchy:

```
ApplicationWindow
└── ScrolledWindow (hexpand, vexpand)
    └── TextView (editable=False, monospace=True)
        └── TextBuffer (contains cleaned output)
```

- **`ApplicationWindow`** — top-level window. Title is "CLI Viewer". Default size from `config.width` and `config.height` (600×400 if not specified).
- **`ScrolledWindow`** — makes the content scrollable. Set to expand both horizontally and vertically.
- **`TextView`** — read-only (`set_editable(False)`), monospace font (`set_monospace(True)`), with 8px margins on all sides.
- **`TextBuffer`** — holds the cleaned output text.

---

## ANSI Stripping

Many CLI tools emit ANSI escape codes for colors, cursor movement, and terminal control. When you capture their output and display it in a GTK text view, these codes appear as garbage characters like `[38;5;226m` instead of rendering as colors.

This app strips them all. Here's what gets removed:

**Color codes (256-color and truecolor):**
```
\x1b[38;5;226m  →  (removed)
\x1b[0m         →  (removed)
\x1b[1m         →  (removed, bold)
```

**Cursor movement:**
```
\x1b[2J          →  (removed, clear screen)
\x1b[H           →  (removed, cursor home)
\x1b[K           →  (removed, clear line)
```

**OSC sequences (terminal title):**
```
\x1b]0;My Title\x07  →  (removed)
```

**Carriage returns (progress bars):**
```
\r              →  \n  (normalized)
\r\n           →  \n  (normalized)
```

After stripping, the output contains only readable text: Unicode box-drawing characters (┌─┐│└─┘), weather symbols, numbers, and plain text. No `[38;5;226m` garbage.

**What's NOT stripped:** Unicode characters (box drawing, arrows, symbols) are preserved. Only ANSI escape *codes* (the `\x1b` sequences) are removed. This means `curl wttr.in` output shows clean box-drawing borders and weather icons — just without the colors.

---

## Dependencies

| Package | Purpose | Arch package | Debian package |
|---------|---------|-------------|----------------|
| GTK4 | Window, widgets, text view | `gtk4` | `libgtk-4-dev` |
| PyGObject | Python bindings for GTK | `python-gobject` | `python3-gi` |
| Python 3.10+ | Runtime | `python` | `python3` |

No pip packages. No virtual environment. No build step. Just system packages and a single Python file.
