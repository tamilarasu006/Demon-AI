#!/usr/bin/env bash
# DEMON-wrapper.sh — symlinked to ~/.local/bin/DEMON.
# Activates the managed venv and execs the real DEMON CLI.

DEMON_HOME="${DEMON_HOME:-$HOME/.DEMON}"
VENV="$DEMON_HOME/.venv"

if [[ ! -d "$VENV" ]]; then
    echo "DEMON: venv not found at $VENV" >&2
    echo "Re-run the installer: curl -fsSL https://DEMON.github.io/DEMON/install.sh | bash" >&2
    exit 1
fi

exec "$VENV/bin/DEMON" "$@"
