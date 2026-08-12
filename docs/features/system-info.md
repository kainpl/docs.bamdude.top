---
title: System Info & Diagnostics
description: Information page — version, DB stats, storage breakdown, log viewer, debug-logging toggle, support bundle, optimize-DB, search-index rebuild, update checker
---

# System Info & Diagnostics

The **Information** page (sidebar → Information, route `/system`) is BamDude's admin diagnostics surface — version metadata, database row counts, storage breakdown, the log viewer, debug-logging toggle, support bundle generator, and the maintenance buttons (optimize DB, rebuild search index, check for updates).

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

### Log rotation + retention

The active log file (`bamdude.log`) rolls over at midnight (local time) — yesterday's logs are gzipped to `bamdude.log.YYYY-MM-DD.gz` and kept under `log_retention_days` (default **30**). On startup BamDude scans `<log_dir>/bamdude.log.*.gz` and deletes anything older than the retention setting.

The system-info page surfaces a **Log Archives** panel listing every gzipped archive currently on disk — for each archive: date, size, **Download** (streams the `.gz`), and **Delete** (two-stage: first click arms the destructive button, second click actually deletes). Combined with the **Truncate** action on the live log file, the panel gives full per-day control without shelling into the container.

`log_retention_days` lives in **Settings → System** (range 1–365) — operators with `settings:update` can change it in-app. The setting also applies on tomorrow's rollover, so reducing 30→7 frees disk on the next midnight tick.

## :material-lifebuoy: Support bundle

`GET /api/v1/support/bundle` produces a ZIP file containing:

| File | Contents |
|---|---|
| `support-info.json` | Version, OS info, DB row counts, sanitised printer/integration info, anonymised settings, dependency versions, log-file size, network interfaces with masked subnets, WebSocket connection count, Docker memory limit (if containerised), **and the BamDude process itself** — see below. |
| `bamdude.log` | The tail of `bamdude.log`, sanitised. |

### The BamDude process itself

The bundle used to describe the machine, the database, the printers and the settings — everything except the process actually running. So a report of *"memory climbs for days until it gets killed"* arrived with nothing to act on: the numbers that identify the cause only exist **while it is happening**, and by the time anyone asks, the container has been restarted.

Bundles now carry:

| Field | Why it matters |
|---|---|
| **Memory in use vs memory reserved** | The difference between those two is what separates a real leak from harmless address space |
| **Thread and child-process counts** | A climbing thread count is a different bug from a climbing heap |
| **Open files and sockets** | Descriptor leaks look like memory leaks from the outside |
| **Uptime** | Puts every other number in scale |
| **A breakdown of what the memory is filled with** | Points at *which* allocation is growing |

!!! note "On a process already very large, the breakdown is skipped — and says so"
    Generating a bundle to diagnose runaway memory must not be the thing that
    finishes the machine off.

    **Child processes are recorded by name only, never by command line** — an
    `ffmpeg` command line contains the camera password.

This lands in both the bundle you download and the pack attached to a [bug report](bug-report.md).

The bundle requires **debug logging to be currently enabled** — the endpoint refuses to generate one otherwise (`400 Debug logging must be enabled before generating a support bundle`). Workflow:

1. Settings → System → flip DEBUG logging on.
2. Reproduce the issue.
3. Generate the bundle.
4. Flip DEBUG logging back off (it stays on otherwise — the state is persisted in the `Settings` table and re-applied on restart).

### Sanitisation

`_sanitize_log_content` and `_collect_support_info` work together to keep secrets out:

- Printer names → `[PRINTER]`, serial numbers → `[SERIAL]`, IP addresses → `[IP]`, access codes → `[ACCESS_CODE]`, usernames → `[USER]`, emails → `[EMAIL]`.
- URL credentials (`http://user:pass@host`, `rtsps://bblp:code@host`) → `[CREDENTIALS]@`.
- LDAP Distinguished Names → `[DN]`. A DN's leading `CN=` is the user's real name, so it is treated like an email address. Unlike everything else on this list it cannot be looked up in the database — a DN is per-user and comes from your directory — so it is matched by shape instead: two or more comma-joined `attr=value` components. `CN=Joe Schmoe,OU=Staff,DC=example,DC=com` is therefore removed wherever it appears, including inside an error message raised by the directory library. A lone `key=value` in an unrelated line is left alone.
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

`GET /api/v1/updates/check` polls GitHub Releases and compares the latest tag to `APP_VERSION`. Two settings keys steer it:

| Setting key | Effect |
|---|---|
| `check_updates` (default `true`) | When `false`, the endpoint returns `{update_available: false, message: "Update checks are disabled"}` without hitting GitHub. |
| `include_beta_updates` (default `false`) | When `true`, prereleases (`X.Y.ZbN`) are eligible matches. When `false`, only stable releases are surfaced. Detection is dual-signal: a release is treated as a prerelease if its tag matches `bN`/`betaN`/`alphaN`/`rcN` **OR** if it's marked prerelease in the GitHub UI. |

The check response carries `is_prerelease`, `is_docker`, and `latest_version` so the UI can render the right install guidance per channel + per install shape.

### In-app apply (native installs)

`POST /api/v1/updates/apply` does the actual git checkout + dependency install. Behaviour as of **0.4.4**:

- Accepts an optional `tag_name` body field — the frontend passes back what it just got from `/check` so apply hits the exact release the user saw.
- Resolves to a `vX.Y.Z[bN]` git ref via `_resolve_git_ref()` (handles both `v`-prefixed and bare forms).
- Runs `git fetch origin --tags --prune --force` followed by `git reset --hard refs/tags/<ref>`. This works for **any tag regardless of branch** — pre-fix it hardcoded `git reset --hard origin/main` which silently no-op'd beta installs (because beta tags live on `dev`, not `main`).
- Installs Python deps (`pip install -r requirements.txt`) and rebuilds the frontend bundle (`npm install && npm run build`) when npm is available.

The endpoint requires `settings:update`. Trigger from **Settings → System → Install Update** when an update is shown as available.

### Docker installs

Docker installs reject `/apply` with `is_docker: True` — running `git fetch` / `pip install` / `npm build` inside a live container would corrupt the image. Instead, the UI surfaces two side-by-side blocks with concrete commands using the resolved `latest_version` + `is_prerelease`:

**Image-based (typical)** — most operators run `image: kainpl/bamdude:<tag>` in their compose file:

```yaml
# docker-compose.yml
image: kainpl/bamdude:0.4.5b1     # for betas — explicit pin required
# OR
image: kainpl/bamdude:latest      # for stable (latest only tracks main)
```

```bash
docker compose pull && docker compose up -d
```

The hint text in the UI explicitly explains why `:latest` won't pick up a beta — the `:latest` Docker tag tracks `main`, betas are tagged on `dev` and ship as `:X.Y.ZbN` only.

**Source-build** — for operators who cloned the repo and use `build:` in compose:

```bash
git fetch origin --tags --prune --force
git checkout v0.4.5b1
docker compose build --pull
docker compose up -d
```

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
