#!/usr/bin/env python3
"""CLI Viewer — reads config.json, runs the command, shows output.

A minimal GTK4 window that runs a command from config.json and
displays its output in a monospace text view. ANSI escape codes
are stripped so they don't show up as garbage.
"""

import json
import re
import subprocess
import sys

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib


# --- ANSI escape code stripper ---

# Matches: CSI sequences (colors, cursor moves, etc.)
#          OSC sequences (title SetWindowTitle, etc.)
#          Other escape sequences (\\x1b[...m, \\x1b]...\\x07)
_ANSI_CSI_RE = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]")
_ANSI_OSC_RE = re.compile(r"\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)")
_ANSI_OTHER_RE = re.compile(r"\x1b[@-Z\\-_]")  # single-char escapes
_ANSI_FULL_RE = re.compile(
    r"\x1b\[[0-9;?]*[a-zA-Z]"       # CSI: \x1b[...X
    r"|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)"  # OSC: \x1b]...\x07
    r"|\x1b[@-Z\\-_]"               # single-char: \x1bM etc.
    r"|\x1b[()][AB0]"               # charset designation
)


def stripAnsi(text: str) -> str:
    """Remove all ANSI escape sequences from *text*."""
    return _ANSI_FULL_RE.sub("", text)


def cleanOutput(text: str) -> str:
    """Strip ANSI codes and normalize line endings."""
    text = stripAnsi(text)
    # Remove carriage returns (curl progress bar uses \r)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse runs of blank lines (from progress bar remnants)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# --- Main ---

def main() -> int:
    # Read config
    configPath = sys.argv[1] if len(sys.argv) > 1 else "config.json"
    with open(configPath) as f:
        config = json.load(f)

    # Run the command — stdout only, stderr discarded (avoids curl progress junk)
    result = subprocess.run(
        config["command"],
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    raw = result.stdout
    if result.stderr.strip() and not raw.strip():
        # If stdout is empty but stderr has content, show stderr (cleaned)
        raw = result.stderr

    output = cleanOutput(raw)

    # Build the window
    GLib.set_prgname("Luci4GTKviewer")
    app = Gtk.Application(application_id="luci.Luci4GTKviewer")

    def on_activate(_app):
        win = Gtk.ApplicationWindow(application=app, title="CLI Viewer")
        win.set_default_size(
            config.get("width", 600),
            config.get("height", 400),
        )

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)
        win.set_child(scrolled)

        textBuffer = Gtk.TextBuffer()
        textBuffer.set_text(output)
        textView = Gtk.TextView(buffer=textBuffer)
        textView.set_editable(False)
        textView.set_monospace(True)
        textView.set_margin_start(8)
        textView.set_margin_end(8)
        textView.set_margin_top(8)
        textView.set_margin_bottom(8)
        scrolled.set_child(textView)

        win.present()

    app.connect("activate", on_activate)
    return app.run()


if __name__ == "__main__":
    sys.exit(main())

