---
title: Installation
description: Install BamDude on your system, including the first-boot auth setup gate
---

# Installation

This guide covers installing BamDude manually. For Docker (recommended), see the [Docker guide](docker.md).

---

## :material-check-all: Requirements

| Requirement | Details |
|------------|---------|
| **Python** | 3.12+ (native install only — Docker and the Windows installer bring their own) |
| **macOS** | 12 or newer for a native install |
| **Network** | Same LAN as your Bambu Lab printer |
| **Printer** | Developer Mode enabled ([see guide](index.md#enabling-developer-mode)) |
| **SD Card** | Inserted in the printer (required for file transfers) |

!!! tip "Docker Alternative"
    If you prefer containers, check out the [Docker installation guide](docker.md) -- it's even simpler!

---

## :material-download: Manual Install

!!! note "Optional STEP thumbnails"
    `git clone`, creating a Python venv and `pip install -r requirements.txt` do **not** install the CAD component. For STEP thumbnails, complete the separate [STEP component setup](#step-previews) below. Starting BamDude does not download this optional component either.

=== ":material-ubuntu: Ubuntu/Debian"

    ```bash
    # Install prerequisites
    sudo apt update
    sudo apt install python3 python3-venv python3-pip git

    # Clone and setup
    git clone https://github.com/kainpl/bamdude.git
    cd bamdude
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

    # The pinned Node.js part thumbnails render with (after 0.7.0; downloaded once)
    python -m backend.app.services.render_runtime provision --runtime runtime

    # Run
    uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --loop asyncio --timeout-graceful-shutdown 15
    ```

=== ":material-apple: macOS"

    ```bash
    # Install prerequisites (if needed)
    brew install python@3.12

    # Clone and setup
    git clone https://github.com/kainpl/bamdude.git
    cd bamdude
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

    # The pinned Node.js part thumbnails render with (after 0.7.0; downloaded once)
    python -m backend.app.services.render_runtime provision --runtime runtime

    # Run
    uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --loop asyncio --timeout-graceful-shutdown 15
    ```

!!! warning "macOS: the printer is unreachable while everything else works"
    macOS grants Local Network access to a code signature, and Homebrew's Python on Intel Macs has none — every connection to the printer is then dropped with no error and no prompt. `install/install.sh` signs the interpreter on a macOS install (only if it is unsigned), and re-running it after `brew upgrade python` signs the new one. By hand: `codesign --force --sign - "$(python3 -c 'import os,sys;print(os.path.realpath(sys._base_executable))')"`. The connection diagnostic's **macOS Local Network permission** check tells you which case you are in.

Part thumbnails (after 0.7.0) render with a pinned Node.js. `install/install.sh`, `update.sh` and the in-app update in Settings download it once into `runtime/` of the installation — 26–30 MiB depending on the platform, about 118 MiB unpacked on Linux — and a manual install runs the `provision` line above. A native install that starts without it — a `git clone` or `git pull` by hand, a development checkout, or the first update from 0.7.0, whose updater predates this step — installs it by itself in the background, once per start; meanwhile the System page shows `runtime_provisioning`. What an interrupted provisioning left behind is removed by the next one. Several machines installing Node.js into one installation directory at the same time — an installation directory on a network share that more than one machine runs from — is not supported; this concerns the installation directory only, not a shared data directory. If it still ends without Node.js, the System page shows **Part thumbnail worker** as `runtime_missing`; see [Part thumbnail worker](../reference/troubleshooting.md#part-thumbnail-worker). The Windows installer and the Docker image carry Node.js already.

Which Node.js a machine gets: Linux and macOS on x64 or arm64, and Windows x64, run Node.js 24. A Raspberry Pi with the 32-bit Raspberry Pi OS (armhf — Pi 2, 3, 4, 5, Zero 2 W) runs Node.js 22, the last line Node.js publishes for 32-bit ARM, until its support ends on 30 April 2027; after that, a BamDude update returns it to the fallback picture. 2 GB of RAM or more is recommended there — a Pi with 1 GB is not promised to render a heavy plate beside the service. armv6 (Pi 1, Zero, Zero W), an armel or musl 32-bit system and RISC-V have no official Node.js build: parts get only the fallback picture the file allows.

### :material-cube-scan: STEP previews {#step-previews}

[STEP thumbnails](../features/file-manager.md#step-thumbnails) (after 0.7.0) need an optional component of about 170 MB — an Open CASCADE build. The Docker image and the Windows installer ship it; on a native install it is the administrator's choice:

- `install/install.sh` asks *"Install the STEP preview component?"*. The answer defaults to **yes** when this install already has it enabled and to **no** otherwise, so `--yes` keeps an enabled component and leaves a fresh install without one. `--with-step-preview` installs it without asking.
- It is offered on Debian/Ubuntu and Fedora/RHEL — the script installs the system libraries it needs, as root: `libgl1 libx11-6 libexpat1 zlib1g` or `mesa-libGL libX11 expat zlib` — and on macOS (nothing extra), on x86_64 and arm64. On Arch Linux and openSUSE it is not offered: install libGL, libX11 and expat yourself, then run `install/step-preview.sh enable`.
- Without it STEP files are still kept in the library; they just get no thumbnail, and the job ends with *the STEP component is not available on this server* (`cad_unavailable`).

For a manual Git + venv installation, first install the ordinary Python requirements, then enable the CAD component separately. The helper downloads the pinned packages into the installation's `runtime/` directory, separately from the main venv. It also records your choice so updates from Settings can maintain the component.

**Linux / macOS:** to enable it later, or repair it, run from the install directory — BamDude may keep running, and the next STEP thumbnail uses the component:

```bash
sudo install/step-preview.sh enable    # records the choice, installs the libraries, then the component
sudo install/step-preview.sh status    # checks that it really renders, and says what to do if not
```

On macOS run both without `sudo`. `--path DIR` points them at another install. They exit `0` when done (or when the component works), `1` on a failure, with its reason, and `3` when the component is not available for this machine or its Python. `enable` waits at most 15 minutes for another install of the component, 15 minutes for the download and 120 seconds for each check of it; reading its files and proving its processes ended are not bounded.

**Windows Git checkout with a Python venv:** use PowerShell in the repository root, with the same venv that runs BamDude. Activating the venv is not required when using these explicit paths:

```powershell
# Record the choice for future updates
.\venv\Scripts\python.exe -m backend.app.step_runtime choose enabled --by cli

# Download and install the pinned CAD component
.\venv\Scripts\python.exe -m backend.app.step_runtime install

# Verify the files and a real STEP-to-PNG conversion
.\venv\Scripts\python.exe -m backend.app.step_runtime status --check
```

Check that each command succeeds before continuing. The final check reports `"bundle": "works"` on success. If BamDude is already running the code that supports STEP thumbnails, installing the component does not require a restart. Existing STEP files can then use **Generate Thumbnail** in the library.

After a manual `git pull` and requirements update, run `install` and `status --check` again with that installation's Python to install and check the current pin. `pip install` alone does not refresh the CAD component.

!!! note "Development branches with a candidate pin"
    If a development checkout still has a `candidate` CAD pin, local testing requires `install --allow-candidate` in place of `install`. This flag is for development only; use the ordinary command with a release pin. You do not need it for a released Docker image or Windows installer.

| Reason | What to do |
|--------|------------|
| `smoke_failed:system_library:<soname>` | A system library is missing: install the package `status` names, then run `enable` |
| `permission` | Something under `runtime/` is not writable by the install's owner (often left by an earlier `sudo` run): `sudo chown -R <owner> <install>/runtime`, then `enable` |
| `lock_timeout` | Another install of the component held its lock for 15 minutes: let it finish, then run `enable` again |
| `helper_unproven` | An update from Settings could not prove an earlier run of the helper ended: restart BamDude, then update again or run `enable` |
| `pip_timeout`, `pip_failed` | The download did not complete: check the network, then run `enable` |

An install or update that finds a half-finished folder of an earlier run of the component, and cannot prove that run has ended, keeps the folder for a later install. The log then has one warning per such folder, starting `bamdude-step-staging-kept`, with the reason as a closed code: the helper prints it to its error output, and an update from Settings writes it to BamDude's log. It names no path or user, and nothing about the folder changes because of it.

Updates keep an enabled component current — `update.sh` and an update from Settings refresh it, never install one you declined and never fail because of it; see [Upgrading → The STEP preview component on update](upgrading.md#step-component-on-update). Choosing *no* (or `disabled`) stops updates from touching the component; it does not remove one that is already installed. The System page shows the component's state — installed or not, never "works", which only `status` checks — and, on a native install, these two commands; see [System Info](../features/system-info.md#what-it-is).

!!! note "Where the component's source is"
    The parts of the component under a licence that asks for their source — Open CASCADE Technology, LibRaw, FreeImage and, on Linux, libgomp — have that source attached to every release that carries the component, as the asset `bamdude-step-preview-sources-<id>.tar` on its [Releases](https://github.com/kainpl/bamdude/releases) page, with its SHA-256 beside it: each component's upstream source together with what built it. The notices that ship with the component say where it is, and the same source is available on request, for no more than the cost of providing it, for at least three years after BamDude last distributed a version that carries the component — open an issue.

Open [http://localhost:8000](http://localhost:8000) in your browser.

---

## :material-microsoft-windows: Windows (native installer)

Windows 10/11 has a self-contained **`.exe` installer** — no Docker, no WSL, and **no separate Python or Node install**. The setup bundles an embedded Python runtime, a static `ffmpeg` and — after 0.7.0 — the pinned Node.js that renders part thumbnails (about 21 MiB of the installer; measured 2026-10-12, Node v24.17.0), lays everything down, and registers BamDude as a **Windows Service** that starts on boot.

After 0.7.0 the installer also carries the component that makes [STEP thumbnails](../features/file-manager.md#step-thumbnails) (about 167 MB installed) and checks it — a real STEP turned into a picture — before it starts the service: an install whose component fails that check leaves the service stopped and says so, instead of starting with a broken one. Its copyleft parts have their source published with every release; see [STEP previews](#step-previews) above.

1. Download the latest **`bamdude-<version>-windows-x64-setup.exe`** from the [Releases page](https://github.com/kainpl/bamdude/releases).
2. Run it (it needs Administrator rights — it registers a service and writes to `ProgramData`).
3. When it finishes, your browser opens [http://localhost:8000](http://localhost:8000).

That's it — the service is already running.

!!! note "SmartScreen: the installer is not code-signed"
    Windows SmartScreen shows *"Windows protected your PC"* on first run — click **More info → Run anyway**. The upstream binaries bundled inside the installer (embedded Python, NSSM, ffmpeg) carry their own vendors' signatures or none. What the app sends out, and how to switch telemetry off: [Privacy & Telemetry](../privacy.md).

### :material-folder-cog: What the installer lays down

| What | Where |
|------|-------|
| **Program files** (embedded Python 3.12, backend + pre-built frontend, NSSM, ffmpeg) | `C:\Program Files\BamDude` |
| **Your data** (database, archives, plate calibration) | `C:\ProgramData\BamDude\data` |
| **Logs** | `C:\ProgramData\BamDude\logs` |

The installer also adds Start-Menu shortcuts (**Open BamDude Dashboard**, **BamDude Logs**, **Uninstall**), an optional desktop shortcut, and — if you leave the box ticked — a **Windows Firewall** rule opening port `8000`.

!!! info "Your data survives uninstall + upgrade"
    Everything under `C:\ProgramData\BamDude` is left untouched on uninstall. Re-installing (or installing a newer build on top) picks the same database and archives back up automatically.

### :material-service-toggle: The BamDude service

The installer registers a Windows Service named **BamDude** (supervised by [NSSM](https://nssm.cc/)) that runs as `LocalSystem`, starts automatically on boot, and serves the dashboard on `http://localhost:8000`. Manage it with the standard cmdlets:

```powershell
Get-Service BamDude          # Check status
Start-Service BamDude        # Start
Stop-Service BamDude         # Stop
Restart-Service BamDude      # Restart
```

### :material-update: Updating

Download a newer `bamdude-<version>-windows-x64-setup.exe` and run it — it stops the service, overwrites the program files in place, and restarts. Your database, archives, and logs under `C:\ProgramData\BamDude` are preserved.

Then open [http://localhost:8000](http://localhost:8000).

---

## :material-tune: Configuration

Configure BamDude using environment variables or a `.env` file:

```bash
cp .env.example .env
nano .env
```

### Environment Variables

#### Core

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `false` | Enable debug mode (verbose logging; in dev also re-runs the latest migration on every boot) |
| `LOG_LEVEL` | `INFO` | Log level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_TO_FILE` | `true` | Write logs to `logs/bamdude.log` |
| `DATA_DIR` | `<repo>/data` | Override the persistent-data directory (DB + archives + plate calibration) |
| `LOG_DIR` | `<repo>/logs` | Override the log directory |
| `PORT` | `8000` | Port the bundled `python -m backend.app.main` entrypoint binds to |
| `TZ` | system | Timezone string passed to Python (e.g. `Europe/Kyiv`) |

#### Database

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | unset (SQLite) | `embedded` for the bundled PostgreSQL 18, or a URL such as `postgresql+asyncpg://user:pass@host:5432/bamdude` for your own server. Empty means SQLite. See [PostgreSQL Support](../features/postgresql.md). |
| `EMBEDDED_PG_PORT` | picked once, remembered | Pin the bundled server's port (e.g. `6432`) so `psql` or DBeaver can reach it. |

!!! tip "The installer asks for you"
    `install.sh` offers SQLite, the bundled PostgreSQL, or an external server — interactively, or unattended with `--db sqlite|embedded|external` (plus `--database-url` for the last). Re-running over an existing install keeps the backend you already use.

!!! important "External PostgreSQL: enable query statistics"
    Full database diagnostics require `pg_stat_statements` on the PostgreSQL server. Setting `DATABASE_URL` or updating the BamDude image does not enable it. Follow [the setup and verification steps for Docker or a self-hosted server](../features/postgresql.md#pg-stat-statements).

#### Auth & reverse-proxy

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET_KEY` | auto-generated and persisted under `data/` | Override the JWT signing key. Don't change this on a running install or every issued token will be invalidated. |
| `TRUSTED_PROXY_IPS` | empty | Comma-separated reverse-proxy IPs whose `X-Forwarded-For` is trusted (right-to-left resolution). Required behind nginx for accurate per-IP rate limiting. |
| `AUTH_REFRESH_COOKIE_SECURE` | unset (auto-detect) | Force `Secure` polarity on the refresh-token cookie. Auto-detect from the request scheme is the right default; set `true` to force, `false` to disable (LAN HTTP dev only). |
| `MFA_ENCRYPTION_KEY` | unset | URL-safe base64 Fernet key. When set, TOTP secrets and OIDC client secrets are encrypted at rest. Plaintext fallback works without it but logs a warning at boot. |
| `APP_URL` | `http://localhost:5173` | Public-facing base URL of BamDude. Used to build absolute links in password-reset / MFA-recovery emails, OIDC callback URL, and the Obico cached-frame URL the Obico ML API fetches back. The `external_url` setting under Settings → System overrides this when set. |

#### Integrations (optional)

| Variable | Description |
|----------|-------------|
| `HA_URL`, `HA_TOKEN` | Home Assistant base URL + long-lived token. When **both** are set, HA integration is auto-enabled and the matching DB settings become read-only (env wins). Recommended for the HA Add-on; native installs can also enable HA via Settings → Integrations without env vars. |
| `VIRTUAL_PRINTER_PASV_ADDRESS` | Override the FTP-PASV address advertised by the virtual printer (set this if BamDude runs behind NAT and slicers can't reach the bind IP). |
| `VIRTUAL_PRINTER_ADVERTISE_ADDRESS` | The upload destination a virtual printer bound to a real printer tells the slicer (set this if BamDude runs behind NAT, e.g. Docker bridge mode). |

#### Container detection

Either of these env vars (any non-empty value) marks the runtime as a container, which adjusts SSDP discovery behaviour. Normally set automatically by the container runtime — only override if you're running native but want container-style discovery.

| Variable | Description |
|----------|-------------|
| `CONTAINER` | Generic container marker. |
| `DOCKER_CONTAINER` | Docker-specific marker. |

#### Docker compose helpers (read by `docker-compose.yml`, not by BamDude itself)

| Variable | Description |
|----------|-------------|
| `PUID` / `PGID` | UID / GID the bamdude container runs as. Match these to the owner of your mounted volumes to avoid permission errors on archive writes. Get them with `id -u && id -g`. |

---

## :material-account-key: First-Boot Setup

BamDude has authentication **always on** — there is no "no-auth" mode. On the very first start the API rejects every request with `503 {"detail": "setup_required"}` until the initial admin user is created. The whitelist that bypasses the gate is exactly three routes (`/api/v1/auth/status`, `/api/v1/auth/setup`, `/api/v1/system/health`), so login and every other endpoint stay closed until setup completes.

### :material-web: Setup wizard (browser)

Open BamDude in a browser. The frontend reads `/api/v1/auth/status`, sees `requires_setup=true`, and renders the setup form:

| Field | Required | Notes |
|-------|----------|-------|
| Username | yes | Becomes the first admin. Max 150 chars. |
| Password | yes | Min 8 chars, must include at least one uppercase + one lowercase + one digit. No special-character rule — BamDude follows NIST SP 800-63B which explicitly advises against composition rules beyond length + a basic mix. Max 256 chars. Stored as a bcrypt hash. |
| Email | optional | Max 254 chars. Used for password-reset flows + email-OTP MFA later. |

Submit creates the admin, drops the setup gate, and signs you in. The form never shows again — once any admin exists, navigating to `/setup` redirects to `/login`.

### :material-api: Setup over API

Scripts and bootstrap automation can `POST /api/v1/auth/setup` directly:

```bash
curl -X POST http://localhost:8000/api/v1/auth/setup \
  -H "Content-Type: application/json" \
  -d '{"admin_username":"admin","admin_password":"ChangeMe123","admin_email":"ops@example.com"}'
```

The endpoint is one-shot — once any admin exists, subsequent calls return `403 Forbidden` with `"Setup has already been completed."`. Calls before setup don't need a token; calls after setup must use a JWT.

### :material-key-remove: Recovery — lost all admins

If every admin account is deleted or disabled and nobody can sign in any more, run the rescue CLI to clear the setup-completed flag. The next boot re-enters the wizard. **All other data is preserved** — only the gate flag is cleared.

=== ":material-server: Native install"

    ```bash
    cd /path/to/bamdude
    source venv/bin/activate
    python -m backend.app.cli reset_admin
    ```

=== ":material-docker: Docker"

    ```bash
    docker compose exec bamdude python -m backend.app.cli reset_admin
    ```

The CLI refuses to run while at least one admin still exists — delete the dead accounts directly in the DB first (or via the admin UI if you have any working admin left), then re-run.

!!! tip "Full auth docs"
    Sessions, refresh-token rotation, MFA (TOTP / email OTP / backup codes), OIDC, LDAP, API keys, and rate limiting all live in [Authentication](../features/authentication.md). The setup gate is just step zero.

---

## :material-cog: Running as a Service

=== ":material-linux: systemd (Linux)"

    Create the service file:

    ```bash
    sudo nano /etc/systemd/system/bamdude.service
    ```

    ```ini
    [Unit]
    Description=BamDude Print Farm Manager
    After=network.target

    [Service]
    Type=simple
    User=YOUR_USERNAME
    Group=YOUR_USERNAME
    WorkingDirectory=/home/YOUR_USERNAME/bamdude
    Environment="PATH=/home/YOUR_USERNAME/bamdude/venv/bin"
    ExecStartPre=-/usr/bin/pkill -9 ffmpeg
    ExecStopPost=-/usr/bin/pkill -9 ffmpeg
    ExecStart=/home/YOUR_USERNAME/bamdude/venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --loop asyncio --timeout-graceful-shutdown 15
    Restart=always
    RestartSec=10

    [Install]
    WantedBy=multi-user.target
    ```

    Enable and start:

    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable bamdude
    sudo systemctl start bamdude
    ```

---

## :material-network: Network Requirements

**Outbound to your printers** (BamDude → printer):

| Port | Protocol | Purpose |
|------|----------|---------|
| 8883 | MQTT/TLS | Live state, control commands |
| 990 | FTPS | 3MF upload, archive download |

**Inbound to BamDude** (browser / slicer / Telegram → BamDude):

| Port | Protocol | Purpose |
|------|----------|---------|
| 8000 | HTTP / WS | Web UI + REST API + WebSocket for live updates |

**Inbound to BamDude when the virtual-printer feature is enabled** (slicer "Send to Printer" → BamDude pretending to be a printer). Only required if you use Virtual Printer; native installs can run with just port 8000:

| Port | Protocol | Purpose |
|------|----------|---------|
| 322 | RTSP | Camera proxy (X1 / H2 / P2 series) |
| 990 | FTPS control | Slicer upload session |
| 3000, 3002 | TCP | Bambu proprietary bind/detect protocol |
| 6000 | TCP | File-transfer tunnel |
| 8883 | MQTTS | Slicer→printer MQTT emulation |
| 50000–50100 | TCP | FTP passive-mode data range |

Linux deployments using `network_mode: host` in compose pick all of these up automatically. Bridge-mode Docker on macOS / Windows needs every port mapped explicitly — see the [Docker guide](docker.md#bridge-mode).

---

## :material-folder-cog: Build Frontend from Source

The repository includes pre-built frontend files. To build from source:

```bash
cd frontend
npm install
npm run build
cd ..
```

---

## :checkered_flag: Next Steps

<div class="quick-start" markdown>

[:material-printer-3d: **Add Your Printer**<br><small>Connect your first printer</small>](first-printer.md)

[:material-docker: **Try Docker Instead**<br><small>Even simpler setup</small>](docker.md)

[:material-help-circle: **Troubleshooting**<br><small>Installation issues?</small>](../reference/troubleshooting.md)

</div>

> Originally based on [Bambuddy](https://github.com/maziggy/bambuddy) documentation.
