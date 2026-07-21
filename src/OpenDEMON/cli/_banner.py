"""Startup banner — OpenDemon wordmark + tagline."""

from __future__ import annotations

# "OpenDemon" rendered in figlet "standard" font.
_WORDMARK = (
    '  ___                   ____                              ',
    ' / _ \\ _ __   ___ _ __ |  _ \\  ___ _ __ ___   ___  _ __  ',
    '| | | | \'_ \\ / _ \\ \'_ \\| | | |/ _ \\ \'_ ` _ \\ / _ \\| \'_ \\ ',
    '| |_| | |_) |  __/ | | | |_| |  __/ | | | | | (_) | | | |',
    ' \\___/| .__/ \\___|_| |_|____/ \\___|_| |_| |_|\\___/|_| |_|',
    '      |_|                                                  ',
)

_TAGLINE = "Personal AI, On Personal Devices"


def print_banner(quiet: bool = False) -> None:
    """Print the DEMON startup banner. No-op when quiet."""
    if quiet:
        return
    try:
        from rich.console import Console

        console = Console()
        for line in _WORDMARK:
            console.print(line, style="bold bright_blue", highlight=False, markup=False)
        console.print(f"      {_TAGLINE}", style="cyan", highlight=False, markup=False)
        console.print()
    except ImportError:
        for line in _WORDMARK:
            print(line)
        print(f"      {_TAGLINE}")
        print()
