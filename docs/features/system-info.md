---
title: System Info & Diagnostics
description: Settings → System page — version, DB stats, storage breakdown, log viewer, debug-logging toggle, support bundle, optimize-DB, search-index rebuild, update checker
---

# System Info & Diagnostics

The Settings → System page is BamDude's admin diagnostics surface — version metadata, database row counts, storage breakdown, the log viewer, debug-logging toggle, support bundle generator, and the maintenance buttons (optimize DB, rebuild search index, check for updates).

## :material-information: What it is

A read-only dashboard that pulls from `GET /api/v1/system/info` (most of the page), `GET /api/v1/system/storage-usage` (the storage breakdown), and `GET /api/v1/support/logs` (the log viewer). Maintenance actions are POST endpoints behind the appropriate permissions. Everything lives in the running BamDude process — no external metrics database is required (for that, see [Prometheus](prometheus.md)).

## :material-tag-outline: Version info

| Field | Source |
|---|---|
| `version` | `APP_VERSION` from `backend/app/core/config.py`, set at build time by `node scripts/set_version.js`. |
| `python_version` | Python interpreter version of the running process. |
| Database engine + version | `SHOW server_version` on PostgreSQL, `SELECT sqlite_version()` on SQLite. |
| `platform` / `architecture` / `hostname` | From Python's `platform` module. |
| `boot_time` / `uptime` | System boot time from `psutil`, formatted to `Nd Nh Nm`. |

Build date and git SHA are not exposed via this endpoint — release builds bake the version string at `set_version.js` time, that's the canonical identifier. The Node version isn't reported either; the React bundle is shipped pre-built under `static/`.

## :material-database: Database stats

`GET /api/v1/system/info` aggregates row counts and a few sums:

| Stat | What it counts |
|---|---|
| `archives` | Total `print_archives` rows. |
| `archives_completed` / `archives_failed` / `archives_printing` | Same, partitioned by status. |
| `printers` | Total registered printers. |
| `spools` | Total spool records (live inventory rows). |
| `projects` | Total projects. |
| `smart_plugs` | Total registered smart plugs. |
| `total_print_time_seconds` / `_formatted` | Sum of `print_time_seconds` across all archives. |
| `total_filament_grams` / `_kg` | Sum of `filament_used_grams`. |
| `database.size` (under `storage`) | File size of `bambuddy.db`, or PostgreSQL DB size if PG is in use. |

## :material-harddisk: Storage usage breakdown

`GET /api/v1/system/storage-usage` walks the data directories and classifies every file into one of these buckets, returning size + percentage of total:

| Bucket | Roots covered |
|---|---|
| `database` | `bambuddy.db` (and a legacy `bambutrack.db` if present). |
| `library_thumbnails` / `library_files` / `library_other` | `<archive_dir>/library/...`. |
| `archive_files` / `archive_thumbnails` / `archive_timelapses` | The archive directory itself. |
| `virtual_printer_uploads` / `virtual_printer_upload_cache` / `virtual_printer_certs` / `virtual_printer_other` | `<base_dir>/virtual_printer/...`. |
| `downloads` | `<base_dir>/firmware/`. |
| `plate_calibration` | The plate-detection reference image directory. |
| `logs` | The configured log directory. |
| `other_data` | Anything under the data dirs that didn't match a rule, with a per-bucket sub-breakdown distinguishing `system` (deletable=false) from `data` (deletable=true). |

The scan is cached for 5 minutes (`STORAGE_USAGE_CACHE_SECONDS = 300`). Pass `?refresh=true` to force a re-scan; pass `max_age_seconds=N` (clamped to 0–3600) to override the cache TTL.

!!! tip "Use this before backups"
    Eyeballing the breakdown ahead of a backup tells you whether your archive folder is the dominant share (it usually is) and whether you have headroom to keep timelapses, or should prune them first.

## :material-memory: Resource usage

| Stat | Source |
|---|---|
| CPU count + percent | `psutil.cpu_count()` / `psutil.cpu_percent(interval=0.1)`. |
| Memory total / available / used / percent | `psutil.virtual_memory()`. |
| Disk total / used / free / percent | `psutil.disk_usage(base_dir)`. |
| `connected_printers` | Live MQTT-connected printers from `printer_manager`. |

The values are point-in-time — refreshing the page re-samples them. There's no historical rollup here. For time-series, scrape [Prometheus](prometheus.md).

## :material-text-box-search: Log viewer

`GET /api/v1/support/logs` tails `<log_dir>/bamdude.log`, parses each line into a structured entry, and returns the most recent entries first.

| Param | Notes |
|---|---|
| `limit` | 1–1000, default 200. |
| `level` | `DEBUG`, `INFO`, `WARNING`, or `ERROR`. Case-insensitive. |
| `search` | Substring match against the message body and the logger name. Case-insensitive. |

Multi-line entries (stack traces, especially) are reassembled — a continuation line gets attached to the next-parsed entry above it.

| Action | Endpoint | Permission |
|---|---|---|
| List recent logs | `GET /api/v1/support/logs` | `settings:read` |
| Truncate the log file | `DELETE /api/v1/support/logs` | `settings:update` |
| Toggle DEBUG-level logging | `POST /api/v1/support/debug-logging` | `settings:update` |

!!! note "DEBUG-level logging is gated"
    The `_apply_log_level` helper pins `httpcore` and `httpx` to WARNING even in DEBUG mode — full request URL logging would leak bearer tokens in Discord / generic-webhook URLs. `paho.mqtt` switches to DEBUG when the toggle is on, which is where most useful printer-protocol detail lives.

## :material-lifebuoy: Support bundle

`GET /api/v1/support/bundle` produces a ZIP file containing:

| File | Contents |
|---|---|
| `support-info.json` | Version, OS info, DB row counts, sanitised printer/integration info, anonymised settings, dependency versions, log-file size, network interfaces with masked subnets, WebSocket connection count, Docker memory limit (if containerised). |
| `bamdude.log` | The tail of `bamdude.log`, sanitised. |

The bundle requires **debug logging to be currently enabled** — the endpoint refuses to generate one otherwise (`400 Debug logging must be enabled before generating a support bundle`). Workflow:

1. Settings → System → flip DEBUG logging on.
2. Reproduce the issue.
3. Generate the bundle.
4. Flip DEBUG logging back off (it stays on otherwise — the state is persisted in the `Settings` table and re-applied on restart).

### Sanitisation

`_sanitize_log_content` and `_collect_support_info` work together to keep secrets out:

- Printer names → `[PRINTER]`, serial numbers → `[SERIAL]`, IP addresses → `[IP]`, access codes → `[ACCESS_CODE]`, usernames → `[USER]`, emails → `[EMAIL]`.
- URL credentials (`http://user:pass@host`, `rtsps://bblp:code@host`) → `[CREDENTIALS]@`.
- Path components like `/home/<user>/`, `/Users/<user>/`, `/opt/<user>/` collapsed to `/home/[user]/` etc.
- MQTT relay broker → masked: bare IP becomes `[IP]`, hostname becomes `*.tld`.
- Subnets in network info → first two octets become `x.x` (so `192.168.1.0/24` → `x.x.1.0/24`).
- Settings values — keys containing any of `access_code`, `password`, `token`, `secret`, `api_key`, `cloud_token`, `mqtt_password`, `email`, `username`, `vapid`, `private_key`, `public_key`, `webhook`, `url`, `path`, `config`, `_ip`, `host`, `credential` are redacted to `[REDACTED]` (or `""` if empty). Any other settings pass through as-is, so feature flags and themes are visible in the bundle.

The bundle is the right thing to attach to a [GitHub issue](https://github.com/kainpl/bamdude/issues) when reporting a bug.

## :material-tools: Maintenance actions

| Action | Endpoint | Permission |
|---|---|---|
| **Optimize / vacuum SQLite** — runs `ANALYZE`, `PRAGMA wal_checkpoint(TRUNCATE)`, then `VACUUM` | `POST /api/v1/settings/optimize-db` | `settings:backup` |
| **Rebuild archive search index** — see [Search](search.md) | `POST /api/v1/archives/search/rebuild-index` | `archives:update_all` |
| **Check for updates** — see [Updates](#update-checker) below | `GET /api/v1/updates/check` | `system:read` |

There is **no separate "Clear Cache" button** on the BamDude System page — the page-level caches (storage breakdown, system info) auto-expire on their own; the only manual flush is the `?refresh=true` query param on `/system/storage-usage`.

There is also **no "Restart application" button** — the upstream Bambuddy concept of an in-app restart only makes sense for bare-metal/systemd installs, and the BamDude target deployment is Docker. Restart the container with `docker compose restart bamdude` (or whatever your orchestrator uses).

## :material-update: Update checker

`GET /api/v1/updates/check` polls GitHub Releases and compares the latest tag to `APP_VERSION`. Behaviour:

| Setting key | Effect |
|---|---|
| `check_updates` (default `true`) | When `false`, the endpoint returns `{update_available: false, message: "Update checks are disabled"}` without hitting GitHub. |
| `include_beta_updates` (default `false`) | When `true`, prereleases (`X.Y.ZbN`) are eligible matches. When `false`, only stable releases are surfaced. |

The endpoint surfaces a badge in the sidebar when an update is available; **it does not auto-install**. For Docker installs (the target deployment), update by pulling the new image:

```bash
docker compose pull bamdude && docker compose up -d bamdude
```

There is also a `POST /api/v1/updates/apply` endpoint for in-app updates, but that path is intended for bare-metal / systemd installs and is not part of the supported Docker workflow.

This is the BamDude self-update path. For **printer firmware** updates, see [Firmware Updates](firmware-updates.md) — completely separate flow.

## :material-shield-key: Permissions

| Action | Permission |
|---|---|
| View system info, storage usage, update check | `system:read` |
| View logs, get debug-logging state, generate support bundle | `settings:read` |
| Toggle debug logging, clear logs | `settings:update` |
| Optimize/vacuum DB, restore backup | `settings:backup` |
| Rebuild archive search index | `archives:update_all` |

There is no `system:maintenance` or `support_bundle:create` permission — the support bundle and log endpoints sit under the `settings` namespace.

## :material-api: API reference

```
GET    /api/v1/system/info             # full system snapshot
GET    /api/v1/system/storage-usage    # bucketed storage breakdown
GET    /health                         # unauthenticated liveness probe ({"status":"healthy"})
GET    /api/v1/support/logs            # tail of bamdude.log
DELETE /api/v1/support/logs            # truncate the log file
GET    /api/v1/support/debug-logging   # current debug-logging state
POST   /api/v1/support/debug-logging   # toggle debug logging
GET    /api/v1/support/bundle          # download a support ZIP
POST   /api/v1/settings/optimize-db    # ANALYZE + WAL checkpoint + VACUUM
POST   /api/v1/archives/search/rebuild-index  # rebuild FTS index
GET    /api/v1/updates/version         # current version (unauthenticated)
GET    /api/v1/updates/check           # check GitHub for newer release
```

The unauthenticated `/health` is whitelisted by the setup-gate middleware, so you can scrape it before initial setup completes.
