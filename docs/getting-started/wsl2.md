# WSL2 Install

DEMON on Windows installs two ways: **WSL2** (this page — the
recommended path; identical to native Linux) or **[native Windows
(advanced)](windows-native.md)** (Phase-1; PowerShell installer, no
WSL2 / no Docker). Pick WSL2 for the smoothest experience.

## One-time WSL setup

In an admin PowerShell:

```powershell
wsl --install
```

Then open the Ubuntu (or Debian) shell that gets installed.

## Install DEMON

```bash
curl -fsSL https://DEMON.github.io/DEMON/install.sh | bash
```

About 3 minutes. Type `DEMON` to start.

## WSL-specific notes

- The installer detects WSL via `/proc/sys/kernel/osrelease` and uses `nohup ollama serve &` instead of systemd to start the Ollama daemon (WSL2 doesn't ship systemd by default).
- The first time you run `DEMON`, the WSL kernel may show a "process running in background" notification — that's the bg-orchestrator detaching. It's expected.
- Models are stored in WSL's filesystem (`~/.DEMON/`), not your Windows drive. To free up space later: `DEMON-uninstall` removes everything.

## See also

- [Full installer reference](install.md)
