---
title: Docker Installation
description: Deploy BamDude with Docker in one command
---

# Docker Installation

Docker is the easiest way to run BamDude. One command and you're done.

---

## :rocket: Quick Start

=== ":material-download: Pre-built Image"

    ```bash
    mkdir bamdude && cd bamdude
    curl -O https://raw.githubusercontent.com/kainpl/bamdude/main/docker-compose.yml
    docker compose up -d
    ```

=== ":material-source-branch: Build from Source"

    ```bash
    git clone https://github.com/kainpl/bamdude.git
    cd bamdude
    docker compose up -d --build
    ```

Open [http://localhost:8000](http://localhost:8000) in your browser.

---

## :material-cog: Configuration

### docker-compose.yml (host mode — Linux, recommended)

```yaml
services:
  bamdude:
    image: ghcr.io/kainpl/bamdude:latest
    build: .
    container_name: bamdude
    # Drop volume permission warnings: match the host user that owns
    # /var/lib/docker/volumes — usually 1000:1000 on Debian / Ubuntu.
    # Discover with: id -u && id -g
    user: "${PUID:-1000}:${PGID:-1000}"
    # Allow binding to privileged ports (322 RTSP, 990 FTPS) as non-root.
    cap_add:
      - NET_BIND_SERVICE
    # Linux only — Docker Desktop on macOS / Windows doesn't support host mode.
    # On those, comment this out and use the bridge-mode block below instead.
    network_mode: host
    volumes:
      - bamdude_data:/app/data
      - bamdude_logs:/app/logs
      # Share virtual-printer certs with a parallel native install if you have one.
      - ./virtual_printer:/app/data/virtual_printer
    environment:
      - TZ=${TZ:-Europe/Kyiv}
      - PORT=${PORT:-8000}
    restart: unless-stopped

volumes:
  bamdude_data:
  bamdude_logs:
```

### docker-compose.yml (bridge mode — macOS / Windows / strict networking) {#bridge-mode}

Docker Desktop on macOS / Windows doesn't support `network_mode: host`, and some hardened Linux setups prefer not to use it either. With bridge mode you have to map every port the printer talks to and every port the virtual printer listens on. Auto-discovery of physical printers stops working — add them manually by IP from the UI.

```yaml
services:
  bamdude:
    image: ghcr.io/kainpl/bamdude:latest
    container_name: bamdude
    user: "${PUID:-1000}:${PGID:-1000}"
    cap_add:
      - NET_BIND_SERVICE
    ports:
      - "${PORT:-8000}:8000"            # Web UI + REST + WebSocket
      - "322:322"                        # Virtual-printer RTSP camera proxy
      - "990:990"                        # Virtual-printer FTPS control
      - "3000:3000"                      # Virtual-printer bind/detect
      - "3002:3002"                      # Virtual-printer bind/detect alt
      - "6000:6000"                      # Virtual-printer file tunnel
      - "8883:8883"                      # Virtual-printer MQTT
      - "2024-2026:2024-2026"            # Virtual-printer A1 / P1S range
      - "50000-50100:50000-50100"        # Virtual-printer FTP PASV data
    volumes:
      - bamdude_data:/app/data
      - bamdude_logs:/app/logs
    environment:
      - TZ=${TZ:-Europe/Kyiv}
      - PORT=${PORT:-8000}
      # Required for FTP PASV to work behind NAT — set to the Docker host's
      # LAN IP. The slicer needs this to open the data connection.
      - VIRTUAL_PRINTER_PASV_ADDRESS=${VIRTUAL_PRINTER_PASV_ADDRESS:-}
    restart: unless-stopped

volumes:
  bamdude_data:
  bamdude_logs:
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TZ` | `UTC` | Your timezone (e.g., `America/New_York`) |
| `PORT` | `8000` | Port BamDude runs on |
| `DEBUG` | `false` | Enable debug logging |
| `LOG_LEVEL` | `INFO` | Log level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_TO_FILE` | `true` | Write logs to `/app/logs/bamdude.log` |
| `DATABASE_URL` | unset (SQLite) | PostgreSQL URL, e.g. `postgresql+asyncpg://user:pass@host:5432/bamdude` |
| `TRUSTED_PROXY_IPS` | empty | Comma-separated reverse-proxy IPs trusted for `X-Forwarded-For` (set this when fronting BamDude with nginx / Caddy / Traefik) |
| `AUTH_REFRESH_COOKIE_SECURE` | unset (auto) | Force the refresh-cookie `Secure` flag. Auto-detect from request scheme by default. |
| `MFA_ENCRYPTION_KEY` | unset | URL-safe base64 Fernet key for at-rest encryption of TOTP / OIDC secrets. |
| `APP_URL` | `http://localhost:5173` | Public-facing base URL — used in password-reset / MFA emails, OIDC callbacks, and the Obico cached-frame URL. The `external_url` setting in Settings → System overrides this. |
| `PUID` / `PGID` | `1000` / `1000` | UID / GID the container runs as. Match the owner of your mounted volumes to avoid permission errors. |
| `VIRTUAL_PRINTER_PASV_ADDRESS` | unset | Override the FTP-PASV IP advertised by the virtual printer. Required in **bridge mode** (set to the Docker host's LAN IP); leave unset in host-mode. |
| `JWT_SECRET_KEY` | auto-generated, persisted | Don't change on a running install -- it invalidates all issued tokens. |

See [Installation > Environment Variables](installation.md#environment-variables) for the full list including optional integrations.

---

## :material-database: Data Persistence

| Volume | Purpose |
|--------|---------|
| `bamdude.db` | SQLite database with all your print data |
| `archive/` | Archived 3MF files and thumbnails |
| `logs/` | Application logs |

!!! tip "Backup"
    To backup your data, simply copy these files/directories. See [Backup & Restore](../features/backup.md) for the built-in backup feature.

---

## :material-update: Updating

=== ":material-download: Pre-built Image"

    ```bash
    docker compose pull && docker compose up -d
    ```

=== ":material-source-branch: Built from Source"

    ```bash
    cd bamdude && git pull && docker compose build --pull && docker compose up -d
    ```

---

## :material-server: Advanced Setups

### Reverse Proxy (Nginx)

```nginx
server {
    listen 443 ssl http2;
    server_name bamdude.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

!!! warning "WebSocket Support"
    Make sure your reverse proxy supports WebSocket connections -- required for real-time printer updates.

### Network Mode Host

Host network mode is **required** for printer discovery and camera streaming on Linux:

```yaml
services:
  bamdude:
    network_mode: host
```

!!! note "macOS / Windows"
    Docker Desktop on macOS and Windows requires port mapping instead of host mode. Copy the [bridge-mode compose block above](#bridge-mode) — mapping just `ports: ["8000:8000"]` is enough for the web UI but breaks printer discovery, the virtual printer, and FTP archive downloads. Add physical printers manually by IP from the UI.

!!! warning "DEBUG=true on first boot of a big install"
    Setting `DEBUG=true` causes BamDude to re-run the latest migration on every boot. With several thousand archives that means walking every 3MF on disk before the API comes up — startup goes from seconds to minutes. Switch DEBUG off after the migration cycle settles.

---

## :material-help-circle: Troubleshooting

### Container Won't Start

```bash
docker compose logs bamdude
```

### Can't Connect to Printer

```bash
docker compose exec bamdude ping YOUR_PRINTER_IP
```

If using bridge network mode, try `network_mode: host`.

---

## :checkered_flag: Next Steps

<div class="quick-start" markdown>

[:material-printer-3d: **Add Your Printer**<br><small>Connect your first printer</small>](first-printer.md)

[:material-arrow-up-circle: **Upgrading**<br><small>Migrate from Bambuddy</small>](upgrading.md)

[:material-help-circle: **Troubleshooting**<br><small>Having issues?</small>](../reference/troubleshooting.md)

</div>

> Originally based on [Bambuddy](https://github.com/maziggy/bambuddy) documentation.
