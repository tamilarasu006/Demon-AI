#!/usr/bin/env bash
# DEMON-uninstall.sh — clean removal of DEMON from $HOME.
#
# Removes:
#   ~/.DEMON/
#   ~/.local/bin/DEMON
#   ~/.local/bin/DEMON-uninstall
#
# Does NOT remove: ollama, uv, or the Rust toolchain.

set -euo pipefail

DEMON_HOME="${DEMON_HOME:-$HOME/.DEMON}"

if [[ -f "$DEMON_HOME/.state/bg.pid" ]]; then
    pid=$(cat "$DEMON_HOME/.state/bg.pid" 2>/dev/null || echo "")
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
        echo "Stopping background work (pid=$pid)..."
        kill "$pid" 2>/dev/null || true
    fi
fi

if command -v ollama >/dev/null 2>&1; then
    ollama stop >/dev/null 2>&1 || true
fi

if [[ -d "$DEMON_HOME" ]]; then
    rm -rf "$DEMON_HOME"
    echo "Removed $DEMON_HOME"
fi

for f in "$HOME/.local/bin/DEMON" "$HOME/.local/bin/DEMON-uninstall"; do
    if [[ -L "$f" ]] || [[ -f "$f" ]]; then
        rm -f "$f"
        echo "Removed $f"
    fi
done

cat <<EOF

DEMON removed.

Left intact (may be used by other tools):
  - Ollama       (uninstall: brew uninstall ollama  /  rm -f /usr/local/bin/ollama)
  - uv           (uninstall: rm -rf ~/.local/share/uv ~/.cargo/bin/uv)
  - Rust toolchain (uninstall: rustup self uninstall)
EOF
