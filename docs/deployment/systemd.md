# systemd Service (Linux)

DEMON includes a systemd unit file for running the API server as a managed background service on Linux. This provides automatic startup on boot, crash recovery, and integration with standard Linux service management tools.

## Prerequisites

Before installing the service, ensure that:

1. DEMON is installed in a virtual environment at `/opt/DEMON/.venv` (or adjust paths accordingly).
2. A dedicated `DEMON` system user exists (recommended for security).
3. An inference engine (such as Ollama) is running and accessible.

Create the user and installation directory:

```bash
sudo useradd --system --create-home --home-dir /opt/DEMON DEMON
sudo -u DEMON python3 -m venv /opt/DEMON/.venv
sudo -u DEMON git clone https://github.com/DEMON/DEMON.git /opt/DEMON/DEMON
cd /opt/DEMON/DEMON && sudo -u DEMON uv sync --extra server
```

## Installing the Service

The unit binds `0.0.0.0`, so an **API key is required** — and the unit
declares `EnvironmentFile=/etc/DEMON/env` (no `-` prefix), so it will
**fail to start** until that file exists with a key. Create it first:

```bash
sudo mkdir -p /etc/DEMON
echo "DEMON_API_KEY=$(DEMON auth generate-key)" | sudo tee /etc/DEMON/env
sudo chmod 600 /etc/DEMON/env
```

Then copy the unit file, reload the daemon, and enable the service:

```bash
sudo cp deploy/systemd/DEMON.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable DEMON
sudo systemctl start DEMON
```

Clients must send `Authorization: Bearer <key>` on `/v1/*` and `/api/*`
requests. (If you instead bind to `127.0.0.1`, the key is optional and you
can drop the `EnvironmentFile` line.)

Verify it is running:

```bash
sudo systemctl status DEMON
```

## Service File Reference

The provided unit file at `deploy/systemd/DEMON.service`:

```ini
[Unit]
Description=DEMON API Server
After=network.target

[Service]
Type=simple
User=DEMON
WorkingDirectory=/opt/DEMON
ExecStart=/opt/DEMON/.venv/bin/DEMON serve --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=5
Environment=HOME=/opt/DEMON

[Install]
WantedBy=multi-user.target
```

### `[Unit]` Section

| Directive     | Value              | Description                                                                 |
|---------------|--------------------|-----------------------------------------------------------------------------|
| `Description` | `DEMON API Server` | Human-readable name shown in `systemctl status` and logs.              |
| `After`       | `network.target`   | Delays startup until the network stack is available, since the server binds to a network socket and may need to reach a remote engine. |

### `[Service]` Section

| Directive          | Value                                                              | Description                                                                                     |
|--------------------|--------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| `Type`             | `simple`                                                           | The process started by `ExecStart` is the main service process. systemd considers the service started immediately. |
| `User`             | `DEMON`                                                       | Runs the server as the `DEMON` user rather than root, limiting the blast radius of any security issue. |
| `WorkingDirectory` | `/opt/DEMON`                                                  | Sets the working directory for the process. This is where DEMON looks for local files and writes data. |
| `ExecStart`        | `/opt/DEMON/.venv/bin/DEMON serve --host 0.0.0.0 --port 8000` | The command to start the server. Uses the full path to the `DEMON` binary inside the virtual environment. |
| `Restart`          | `on-failure`                                                       | Automatically restarts the service if it exits with a non-zero exit code. Does not restart on clean shutdown (`systemctl stop`). |
| `RestartSec`       | `5`                                                                | Waits 5 seconds before attempting a restart, preventing rapid restart loops if the service crashes immediately on startup. |
| `Environment`      | `HOME=/opt/DEMON`                                             | Sets the `HOME` environment variable so DEMON finds its configuration at `~/.DEMON/config.toml` (resolving to `/opt/DEMON/.DEMON/config.toml`). |

### `[Install]` Section

| Directive    | Value               | Description                                                                                 |
|--------------|---------------------|---------------------------------------------------------------------------------------------|
| `WantedBy`   | `multi-user.target` | The service starts when the system reaches multi-user mode (standard boot target for servers). `systemctl enable` creates a symlink under this target. |

## Configuration Options

### Changing the Bind Address and Port

Edit the `ExecStart` line to change the host or port:

```ini
ExecStart=/opt/DEMON/.venv/bin/DEMON serve --host 127.0.0.1 --port 9000
```

!!! tip
    Binding to `127.0.0.1` restricts access to localhost only. Use this when running behind a reverse proxy like Nginx or Caddy.

### Setting the Engine and Model

Pass additional flags to `DEMON serve`:

```ini
ExecStart=/opt/DEMON/.venv/bin/DEMON serve --host 0.0.0.0 --port 8000 --engine ollama --model qwen3:8b
```

### Adding Environment Variables

Add multiple `Environment` directives or use `EnvironmentFile` for complex configurations:

```ini
[Service]
Environment=HOME=/opt/DEMON
Environment=DEMON_ENGINE_DEFAULT=vllm
Environment=DEMON_OLLAMA_HOST=http://localhost:11434
```

Or load from a file:

```ini
[Service]
EnvironmentFile=/opt/DEMON/.env
```

### Changing the User

If you prefer a different service user, update both the `User` directive and the paths:

```ini
[Service]
User=myuser
WorkingDirectory=/home/myuser/DEMON
ExecStart=/home/myuser/DEMON/.venv/bin/DEMON serve --host 0.0.0.0 --port 8000
Environment=HOME=/home/myuser/DEMON
```

### Using a Configuration File

Ensure the configuration file exists at the path where `HOME` points:

```bash
sudo -u DEMON mkdir -p /opt/DEMON/.DEMON
sudo -u DEMON cp config.toml /opt/DEMON/.DEMON/config.toml
```

The server reads `~/.DEMON/config.toml` on startup, where `~` resolves from the `HOME` environment variable.

## Viewing Logs

DEMON logs are captured by journald. View them with `journalctl`:

```bash
# View all logs for the service
sudo journalctl -u DEMON

# Follow logs in real time
sudo journalctl -u DEMON -f

# View logs since the last boot
sudo journalctl -u DEMON -b

# View logs from the last hour
sudo journalctl -u DEMON --since "1 hour ago"

# View only error-level messages
sudo journalctl -u DEMON -p err
```

## Managing the Service

### Start, Stop, and Restart

```bash
# Start the service
sudo systemctl start DEMON

# Stop the service
sudo systemctl stop DEMON

# Restart the service (stop + start)
sudo systemctl restart DEMON

# Reload configuration without full restart (sends SIGHUP)
sudo systemctl reload-or-restart DEMON
```

### Check Status

```bash
sudo systemctl status DEMON
```

Example output:

```
● DEMON.service - DEMON API Server
     Loaded: loaded (/etc/systemd/system/DEMON.service; enabled; preset: enabled)
     Active: active (running) since Fri 2026-02-21 10:00:00 UTC; 2h ago
   Main PID: 12345 (DEMON)
      Tasks: 4 (limit: 4915)
     Memory: 256.0M
        CPU: 1min 23s
     CGroup: /system.slice/DEMON.service
             └─12345 /opt/DEMON/.venv/bin/python /opt/DEMON/.venv/bin/DEMON serve --host 0.0.0.0 --port 8000
```

### Enable and Disable on Boot

```bash
# Enable automatic start on boot
sudo systemctl enable DEMON

# Disable automatic start on boot
sudo systemctl disable DEMON
```

### Apply Changes After Editing the Unit File

After modifying `/etc/systemd/system/DEMON.service`, reload the systemd daemon and restart the service:

```bash
sudo systemctl daemon-reload
sudo systemctl restart DEMON
```

## Running Alongside Ollama

If Ollama is also managed via systemd, you can add an ordering dependency so the DEMON service waits for Ollama to start:

```ini
[Unit]
Description=DEMON API Server
After=network.target ollama.service
Requires=ollama.service
```

| Directive  | Description                                                              |
|------------|--------------------------------------------------------------------------|
| `After`    | Ensures DEMON starts after Ollama.                                  |
| `Requires` | If Ollama fails to start, DEMON will not start either.              |

!!! note
    Use `Wants` instead of `Requires` if you want DEMON to start even when Ollama is unavailable (for example, if you plan to start Ollama manually later).
