# Installation

## Platform-specific guides

| Platform | One-liner | Detailed guide |
|---|---|---|
| **macOS** | `curl -fsSL https://DEMON.github.io/DEMON/install.sh \| bash` | [macOS install](macos.md) |
| **Linux** | `curl -fsSL https://DEMON.github.io/DEMON/install.sh \| bash` | [Linux install](linux.md) |
| **WSL2 on Windows** | `curl -fsSL https://DEMON.github.io/DEMON/install.sh \| bash` (run inside Ubuntu) | [WSL2 install](wsl2.md) |
| **Native Windows** | `irm https://DEMON.github.io/DEMON/install.ps1 \| iex` | [Native Windows install](windows-native.md) |
| **Desktop GUI** | Download from the [latest release](https://github.com/DEMON/DEMON/releases) | — |

The bash and PowerShell installers do the same thing on their respective hosts. The rest of this page documents the bash installer in detail; the [native Windows guide](windows-native.md) is the equivalent reference for PowerShell.

## Bash installer

```bash
curl -fsSL https://DEMON.github.io/DEMON/install.sh | bash
```

The installer downloads everything for you — including [uv](https://docs.astral.sh/uv/)
(the Python package manager), the Python venv, Ollama, and a small starter
model. **You don't need to install uv or any other prerequisite first.**

!!! info "Install URL"
    This script is served straight from the project's own GitHub Pages site,
    so HTTPS always works. You may also see `https://DEMON.ai/install.sh`
    referenced in older docs — that domain is community-operated and has had
    intermittent TLS issues ([#337](https://github.com/DEMON/DEMON/issues/337)).
    The `DEMON.github.io` URL above is the canonical one.

About 3 minutes on a typical broadband connection. Type `DEMON` to start chatting.

## What the installer does

| Phase | Step | Where |
|---|---|---|
| Foreground | Install `uv` (Python package manager) | `~/.cargo/bin/` or `~/.local/bin/` |
| Foreground | Clone DEMON repo | `~/.DEMON/src/` |
| Foreground | Create Python 3.11 venv | `~/.DEMON/.venv/` |
| Foreground | `uv pip install -e .` (editable install) | venv |
| Foreground | Install Ollama | system default |
| Foreground | Start `ollama serve` | systemd-user / launchd / nohup |
| Foreground | Pull `qwen3.5:2b` (~1.5 GB) | Ollama's model store |
| Foreground | Write `config.toml` (auto-detected hardware + engine + model) | `~/.DEMON/config.toml` |
| Foreground | Symlink `DEMON` and `DEMON-uninstall` | `~/.local/bin/` |
| Foreground | Add `~/.local/bin` to PATH if missing (with on-screen notice) | `~/.bashrc` or `~/.zshrc` |
| Background | Install Rust toolchain via rustup | `~/.cargo/` |
| Background | Build the maturin extension (memory + security features) | venv |
| Background | Pull hardware-tier and tier+1 models | Ollama's model store |

## What the installer does NOT touch

- Your existing Python installations
- Your `~/.bashrc` / `~/.zshrc` other than appending one PATH line (with on-screen notice)
- Your existing Ollama models
- Any other tool or dotfile

## Idempotent re-runs

Re-running the curl line is safe. The installer reads `~/.DEMON/.state/install-state.json` and skips completed steps. If your venv got nuked, re-running heals it.

## Cloud quick-path

If any of these env vars are set when you install or run `DEMON init`, the installer/init proposes cloud as the default and writes the matching provider into `config.toml`:

- `OPENROUTER_API_KEY`
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `GOOGLE_API_KEY` (or `GEMINI_API_KEY`)

Local-first remains the default when no key is in env. Precedence is OpenRouter > Anthropic > OpenAI > Google.

## Flags

| Flag | Effect |
|---|---|
| `--minimal` | Skip the foreground model pull. First chat will need to wait for the bg pull to finish. |
| `--no-bg-orchestrator` | Don't detach the background work pipeline. (Mostly for testing.) |
| `--force` | Re-run all steps even if `install-state.json` says they're done. |

## Environment overrides

| Variable | Default | Purpose |
|---|---|---|
| `DEMON_HOME` | `$HOME/.DEMON` | Install location. |
| `DEMON_REPO_URL` | `https://github.com/DEMON/DEMON.git` | Source repo for the clone step. |

## Uninstall

```bash
DEMON-uninstall
```

Removes `~/.DEMON/`, `~/.local/bin/DEMON`, and `~/.local/bin/DEMON-uninstall`. Leaves Ollama, uv, and the Rust toolchain in place (they may be used by other tools); the script prints removal hints.

## Updating

```bash
DEMON update
```

Pulls the latest source, refreshes the editable install, and rebuilds the Rust extension in the background. Models are not touched.

## Troubleshooting

### "command not found: DEMON"

`~/.local/bin` isn't on your PATH. Run `source ~/.bashrc` (or `~/.zshrc`) or open a new terminal.

### "memory features unavailable"

Rust extension hasn't finished building yet (or failed). Check status:

```bash
DEMON doctor
```

Manually retry:

```bash
~/.DEMON/.scripts/install-rust.sh && ~/.DEMON/.scripts/build-extension.sh
```

### A bigger model failed to download

Check status and retry:

```bash
DEMON doctor
~/.DEMON/.scripts/pull-model.sh qwen3.5:9b
```

### Behind a corporate proxy

Set `HTTPS_PROXY` and `CURL_CA_BUNDLE` in your environment before running the installer.
