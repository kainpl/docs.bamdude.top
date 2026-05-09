---
title: Upgrading & Migration
description: Backup-first protocol for upgrading BamDude, full migration map for 0.4.0 / 0.4.1, and rollback procedure.
---

# Upgrading & Migration

This guide is the operator's safe-upgrade protocol. The DB schema advances **forward only** — there is no automatic down-migration. Restore from backup if you need to go back.

> **Always back up `data/` (or the `bamdude_data` Docker volume) before any upgrade.** Specifically: `bamdude.db` (or PostgreSQL dump if you run PG), the `archive/` directory (3MFs + thumbnails), and the `library/` directory.

---

## :material-clipboard-check: 1. Pre-upgrade checklist

Before touching anything:

1. **Stop the BamDude service** (`sudo systemctl stop bamdude` or `docker compose down`).
2. **Back up the data directory** — see the backup commands below.
3. **Note your current version** — open `/system/health` in a browser, or run `cat pyproject.toml | grep version` for native installs. Useful if you need to roll back.
4. **If running behind a reverse proxy** (nginx / Caddy / Traefik), copy the config aside so you can verify it after upgrade.
5. **Check log size** — if `data/logs/` is huge, this is a good moment to rotate.

### Backup commands

=== "Docker volumes"

    ```bash
    # Data volume — sqlite DB, archives, thumbnails, uploads
    docker run --rm \
      -v bamdude_data:/from \
      -v "$(pwd)/backup":/to \
      alpine tar czf /to/bamdude-data-$(date +%Y%m%d).tar.gz -C /from .

    # Logs (optional)
    docker run --rm \
      -v bamdude_logs:/from \
      -v "$(pwd)/backup":/to \
      alpine tar czf /to/bamdude-logs-$(date +%Y%m%d).tar.gz -C /from .
    ```

=== "Native — UI backup (recommended)"

    Open **Settings → Backup → Local Backup → Create Backup**, then **Download Backup** to save the zip to your computer. The zip packs the SQLite DB, archive directory, thumbnails, uploads, and config in the same layout `install.sh` lays out on disk — restore is just "unzip into the install path and restart". It also captures encryption-key metadata and scheduled-backup state that a raw `tar` of `data/` leaves behind.

=== "Native — shell"

    ```bash
    cd /opt/bamdude
    tar czf ~/bamdude-data-$(date +%Y%m%d).tar.gz data/
    ```

=== "PostgreSQL"

    ```bash
    pg_dump -Fc -f ~/bamdude-$(date +%Y%m%d).dump "$DATABASE_URL"
    # Plus tar up the archive/ + library/ directories from the data volume.
    ```

---

## :material-docker: 2. Upgrade procedure — Docker

```bash
cd bamdude
docker compose pull          # if pinned to :latest
docker compose up -d
docker compose logs -f       # watch migrations apply
```

Pinning a specific tag in `compose.yaml` is fine and recommended for stable installs — `:0.4.1` will never move; `:latest` follows `main`.

```yaml
# Pinned, recommended
image: ghcr.io/kainpl/bamdude:0.4.1

# Rolling, follows main
image: ghcr.io/kainpl/bamdude:latest
```

Watch the startup log for migration progress. Long-running migrations log batched progress (e.g. `m020 library_files: progress` on m020/m022). **Wait for "Migrations complete" before testing.**

```text
INFO  [backend.app.migrations] Applying m019_archive_queue_batch_error
INFO  [backend.app.migrations] Applied m019 (version 19)
INFO  [backend.app.migrations] Applying m022_label_object_metadata_backfill
INFO  [backend.app.migrations] m022 library_files: progress 100/847
INFO  [backend.app.migrations] m022 library_files: progress 200/847
...
INFO  [backend.app.migrations] Applied m022 (version 22)
INFO  [backend.app.main] Startup complete
```

Sanity-check `/system/health` returns 200.

---

## :material-server: 3. Upgrade procedure — Manual (Python venv)

```bash
cd /opt/bamdude
sudo systemctl stop bamdude

# Pull source
sudo -u bamdude git fetch
sudo -u bamdude git checkout v0.4.1     # or whatever tag

# Python deps
sudo -u bamdude ./venv/bin/pip install -r requirements.txt --upgrade

# Frontend bundle (regenerates the tracked static/ directory).
# Skip this step if you only ever pull pre-built tags — the bundle ships
# in-tree at the release commit. Only needed if you build from a custom branch.
sudo -u bamdude bash -c 'cd frontend && npm ci && npm run build'

# Restart and tail logs
sudo systemctl start bamdude
sudo journalctl -u bamdude -f
```

The shipped `install/update.sh` automates the whole sequence (stop → backup → git pull → pip install → npm build → start) and supports env overrides:

```bash
sudo /opt/bamdude/install/update.sh
```

| Variable | Default | Purpose |
|---|---|---|
| `INSTALL_DIR` | `/opt/bamdude` | Where BamDude lives |
| `SERVICE_NAME` | `bamdude` | systemd unit to restart |
| `BRANCH` | current checked-out branch | Switch to another branch during update |
| `BACKUP_MODE` | `auto` | `auto` skips when nothing to back up, `require` aborts if backup fails, `skip` disables |
| `FORCE` | `0` | Set to `1` to bypass dirty-worktree / backup checks |

---

## :material-cursor-default-click-outline: 4. Upgrade procedure — In-app updater (Settings → System)

For native installs the easiest path is the in-app updater. **Settings → System → Check for updates** shows the latest release; **Install Update** (the button below it) does the full sequence (`git fetch --tags`, `git reset --hard refs/tags/<release>`, `pip install`, `npm run build`) without leaving the UI.

Toggles in the same panel:

- **Check for updates automatically** — turn off to stop GitHub polling entirely.
- **Include beta updates** — surface `vX.Y.ZbN` releases too. Off by default. The updater respects either the version-name convention OR GitHub's prerelease flag, so a release explicitly marked prerelease in the GitHub UI is also gated behind this toggle.

Docker installs reject the in-app `Install Update` button — running `git fetch` / `pip install` / `npm build` inside a live container would corrupt the image. Instead, the panel surfaces two side-by-side blocks with the resolved tag pre-filled: **image-based** (`pull && up -d` with the right `image:` line, including a beta-specific hint that `:latest` doesn't track betas), and **source-build** (`git fetch --tags && git checkout v<tag> && compose build --pull && up -d`). Copy-paste either block depending on your install shape — full reference in [System Info → Update checker](../features/system-info.md#update-checker).

> The in-app updater is hardened against the pre-release tag mismatch that 0.4.3-and-earlier silently fell into: clicking Install Update on a beta release used to no-op because the apply path hard-reset to `origin/main`, which doesn't carry the beta tag. Fixed in 0.4.4.

---

## :material-database-cog: 5. Migration overview — what each version changes

BamDude tracks applied migrations in the `_migrations` table. Each release runs every pending version in order on first boot. New installs run `create_all()` first (creating tables from the current model definitions), then `m000` + `m001` are pre-stamped as applied via the bootstrap step, and only later migrations actually execute.

Migrations marked **seed** include a DML step (data backfill / normalisation) and may take noticeable time on large installs; pure-DDL migrations (column adds, FK swaps) finish in milliseconds.

| Version | Title | What changes | Seed | First needed in |
|---|---|---|---|---|
| **m000** | `bambuddy_to_bamdude_301` | Imports a legacy `bambuddy.db` / `bambutrack.db` if found next to where BamDude expects to find `bamdude.db`. No-op when no legacy DB is present. The original Bambuddy file is **renamed**, not deleted, so rollback is possible. | yes (import) | Forks/upgrades from Bambuddy 2.2.2 |
| **m001** | `bamdude_baseline` | Creates the FTS index for archive search (FTS5 on SQLite, tsvector + GIN on PostgreSQL) and seeds the initial reference data (printer model catalog, default groups, etc.). | yes | Fresh BamDude installs |
| **m002** | `bamdude_311` | BamDude 3.0.1 → 3.1.1 schema bump. Adds `printer_queues`, `macros`, swap-mode columns, stagger config, maintenance history tables, queue rework (`queue_id`), `printer_models` on maintenance types. Drops the dead `filaments` table. | yes | Upgrading from BamDude 3.0.x |
| **m003** | `enforce_admin_user` | Codifies the always-on auth model: stamps `auth_enabled=true` + `setup_completed=true` if at least one admin exists; otherwise clears both flags so the next boot routes the user through `/setup`. Schema unchanged. | yes | All installs |
| **m004** | `m002_reconcile` | Re-runs `m002.upgrade()` verbatim. Catches installs that got stuck on an early version of m002 (pre-frozen-migrations rule) where the version was marked applied but later m002 amendments never ran. | yes | Stuck post-3.1.1 installs |
| **m005** | `swap_profiles` | Second dimension on swap mode: `printers.swap_profile` + `macros.swap_profile`. Rebinds the existing A1 Mini built-in macros to `swap_profile='a1mini_kit'`; seeds empty built-ins for `a1mini_stl` + `jobox-a1`. | yes | All installs |
| **m006** | `mesh_mode_fast_check` | Adds `print_queue.mesh_mode_fast_check BOOLEAN DEFAULT 1` so the operator can opt out of the bed-mesh fast-check probe per queue item. | no | All installs |
| **m007** | `drop_vibration_cali` | Drops `print_queue.vibration_cali` (Bambu Studio hardcodes this `false` for every model now; lives only in the calibration wizard). MQTT payload still emits the key for firmware compatibility. | no | All installs |
| **m008** | `swap_macro_queue_fields` | Adds `print_queue.execute_swap_macros BOOLEAN DEFAULT 1` + `swap_macro_events TEXT (JSON array)` so each queue item can override which swap events fire for it. | no | All installs |
| **m009** | `archive_source_hash` | Adds `print_archives.source_content_hash` (SHA256 of unpatched source) + `applied_patches` (JSON). Dedup queries switch to `COALESCE(source_content_hash, content_hash)` so BamDude-patched archives dedup against their library originals. | no | All installs |
| **m010** | `queue_reliability` | Adds `print_archives.subtask_id VARCHAR(64)` (advisory archive matching across restarts) + `printers.awaiting_plate_clear BOOLEAN DEFAULT 0` (persisted plate-clear gate, survives Auto Off power-cycle). | no | All installs |
| **m011** | `cloud_region` | Adds `users.cloud_region VARCHAR(10)` so per-user Bambu Cloud credentials carry their region. Closes the cross-tenant region leak the singleton service had. | no | All installs |
| **m012** | `mfa` | The MFA / 2FA / OIDC cluster — six new tables: `user_totp`, `user_otp_codes`, `auth_ephemeral_tokens`, `auth_rate_limit_events`, `oidc_providers`, `user_oidc_links`, plus `users.password_changed_at`. Backs the always-on auth model from 0.4.0. | no | 0.4.0 |
| **m013** | `library_file_print_count` | Adds `library_files.print_count INTEGER DEFAULT 0`. Per-file completed-print counter, incremented in `on_print_complete`. | no | 0.4.0 |
| **m014** | `archive_library_link` | Adds `print_archives.library_file_id` FK (`ON DELETE SET NULL`) + backfills it on every existing archive by hash-matching against `library_files.file_hash`. **Recomputes `library_files.print_count` and `last_printed_at` from completed-archive history** (overwrites prior values — archive history is authoritative). | yes | 0.4.0 |
| **m015** | `refresh_token_support` | Adds `auth_ephemeral_tokens.used_at` + `family_id` to back the sliding-session refresh flow (§18.14). Reuse-detection revokes the whole family if a refresh token is replayed. | no | 0.4.0 |
| **m016** | `project_print_plan` | Creates `project_print_plan_items` (per-project ordered list of `.3mf` files with copies stepper). Backfills one row per existing `library_files.project_id` link at copies=1. | yes | 0.4.0 |
| **m017** | `macro_action_type` | Adds `macros.action_type` + `mqtt_action` + `delay_seconds`. Lets a macro invoke an MQTT command (`chamber_light_off`, `chamber_light_on`) instead of gcode, on `print_started` / `print_finished` events with optional delay. | no | 0.4.0 |
| **m018** | `queue_library_fk_set_null` | Changes `print_queue.library_file_id` FK from `ON DELETE CASCADE` to `ON DELETE SET NULL`. Combined with the in-app cascade in `delete_file`, this gives SQLite the same behaviour PostgreSQL gets natively. | no | 0.4.0 |
| **m019** | `archive_queue_batch_error` | The queue↔archive refactor. Adds `print_archives.queue_id` (FK, indexed) + `batch_id` (VARCHAR(36), indexed) + `error_message` (TEXT). Drops the four cached counters from `printer_queues` (`completed_count` / `failed_count` / `cancelled_count` / `total_count`). Backfills `queue_id`/`batch_id`/`error_message` from existing `print_queue.archive_id` links. **Deletes completed queue items that have an archive link** — backfill equivalent of the new `on_print_complete` auto-cleanup. | yes | 0.4.0 |
| **m020** | `spool_purchase_date` | Adds three columns to `spool`: `purchase_date DATETIME`, `filament_diameter VARCHAR(8) NOT NULL DEFAULT '1.75'`, `lot INTEGER`. Backfills `filament_diameter` to `'1.75'` (Bambu default). | yes | 0.4.0 (post-b2) |
| **m021** | `drop_auto_light_off` | Drops the legacy `printers.auto_light_off` column. Replaced by the macro framework (configure a `chamber_light_off` mqtt-action macro on the `print_started` event for the same effect, plus optional symmetric `chamber_light_on` on `print_finished`). | no | 0.4.0 |
| **m022** | `label_object_metadata_backfill` | Opens every existing 3MF still on disk, extracts `gcode_label_objects` + `exclude_object` from `Metadata/project_settings.config`, merges them into `library_files.file_metadata` and `print_archives.extra_data`. **Long startup on first boot if you have many archives** — see [§5 Notable upgrade paths](#5-notable-upgrade-paths). | yes | 0.4.1 |
| **m023** | `per_plate_metadata_backfill` | Opens every 3MF on disk again and serialises the full per-plate breakdown (`plates[]` payload + `is_multi_plate` flag) into the same `library_files.file_metadata` and `print_archives.extra_data` JSON columns. Backs the per-plate gallery in the file manager + the multi-plate UI in PrintModal without re-opening the 3MF on every list query. **Same long-startup cost profile as m022** — runs once. | yes | 0.4.1 |

---

## :material-arrow-decision: 5. Notable upgrade paths

### From Bambuddy HE 3.0.x → BamDude 0.4.x

`m000` imports your data, `m002` adapts the schema, `m005`+ are BamDude-native.

!!! warning "Always upgrade to **0.4.0.1** or later"
    Going from a legacy 3.0.1 install straight to **0.4.0** crashed at `m005_swap_profiles.seed()` with `no such column: printers.awaiting_plate_clear` — the seed used ORM `select(Printer)` which loaded every column from the *current* model, including columns that don't exist yet at m005's point in the chain. Fixed in 0.4.0.1 by rewriting the seed to use raw SQL with explicit column lists.

---

## :material-swap-horizontal: Scenario 1 — Migrating from Bambuddy 2.2.2

Place a Bambuddy DB file next to where BamDude expects to find it. On first boot the `m000_bambuddy_import` migration detects it, imports every table BamDude still uses, and renames the file to `bamdude.db`.

The original Bambuddy file is **left in place** (not deleted) so you can roll back.

### via Docker Compose (source checkout)

```bash
# 1. Stop Bambuddy
cd /path/to/bambuddy && docker compose down

# 2. Clone BamDude
git clone https://github.com/kainpl/bamdude.git
cd bamdude

# 3. Copy your Bambuddy DB + archives into the bamdude_data volume
docker volume create bamdude_data
docker run --rm \
  -v /path/to/bambuddy/data:/from \
  -v bamdude_data:/to \
  alpine cp -a /from/. /to/

# 4. Start — migrations run automatically on first boot
docker compose up -d

# 5. Follow startup logs, look for "Bambuddy → BamDude import complete"
docker compose logs -f bamdude
```

### via `docker run` (GHCR image)

```bash
# 1. Stop Bambuddy (however you run it)

# 2. Create the new volume and seed it with your Bambuddy data
docker volume create bamdude_data
docker run --rm \
  -v /path/to/bambuddy/data:/from \
  -v bamdude_data:/to \
  alpine cp -a /from/. /to/

# 3. Start BamDude from GHCR
docker run -d \
  --name bamdude \
  --network host \
  -e TZ=Europe/Kyiv \
  -v bamdude_data:/app/data \
  -v bamdude_logs:/app/logs \
  --restart unless-stopped \
  ghcr.io/kainpl/bamdude:latest
```

### via native / self-install

```bash
# 1. Stop the Bambuddy service

# 2. Install BamDude
curl -fsSL https://raw.githubusercontent.com/kainpl/bamdude/main/install/install.sh \
  -o install.sh && chmod +x install.sh
sudo ./install.sh --yes       # defaults to /opt/bamdude

# 3. Drop your Bambuddy DB into BamDude's data dir BEFORE first start
sudo cp /path/to/bambuddy/data/bambuddy.db /opt/bamdude/data/
sudo cp -r /path/to/bambuddy/data/archives /opt/bamdude/data/   # if you have one

# 4. Fix ownership (installer runs as the bamdude service user)
sudo chown -R bamdude:bamdude /opt/bamdude/data/

# 5. Start the service — import migration fires automatically
sudo systemctl start bamdude
sudo journalctl -u bamdude -f
```

!!! tip "The import is one-shot"
    `m000_bambuddy_import` checks for `bambuddy.db` / `bambutrack.db` and only runs if BamDude's own `bamdude.db` does not yet exist. After a successful import the file is renamed to `bamdude.db` and the migration is marked applied in the `_migrations` table, so a subsequent restart won't re-import.

---

## :material-compare-horizontal: Switching install method

You can change install method at any time without touching data — just point the new instance at the existing `data/` directory or copy the volume contents.

### Native → Docker

```bash
sudo systemctl stop bamdude

# Copy native data into a Docker volume
docker volume create bamdude_data
docker run --rm \
  -v /opt/bamdude/data:/from \
  -v bamdude_data:/to \
  alpine cp -a /from/. /to/

# Start the GHCR image against the new volume
docker run -d --name bamdude --network host \
  -v bamdude_data:/app/data -v bamdude_logs:/app/logs \
  --restart unless-stopped ghcr.io/kainpl/bamdude:latest

# Only after you've verified the Docker instance works, disable/remove the native service:
sudo systemctl disable bamdude
```

### Docker → Native

```bash
docker compose down

# Copy the volume out to disk
docker run --rm \
  -v bamdude_data:/from \
  -v "$(pwd)/extracted":/to \
  alpine cp -a /from/. /to/

# Install native pointing at the extracted data
sudo ./install/install.sh --data-dir "$(pwd)/extracted" --yes
```

### Docker Hub → GHCR (or vice versa)

Registry swap only, no data touch:

```bash
# docker-compose.yml
# image: kainpl/bamdude:latest      ← Docker Hub
# image: ghcr.io/kainpl/bamdude:latest  ← GitHub Container Registry
docker compose pull
docker compose up -d
```

Both registries publish the same tags. GHCR is the preferred source (built in CI on every release); Docker Hub is a mirror.

---

## :material-clipboard-check-multiple: 6. Post-upgrade verification

After the service is back up:

1. **`/system/health` returns 200.**
2. **Settings → System → version** reflects the new release.
3. **Connect to a printer that was working pre-upgrade** — should reconnect within 30 seconds; check the printer card on the Printers page.
4. **Open the latest few archives** — thumbnails should still render, the 3D preview should work, the printer-icon click should jump to the owning printer.
5. **Trigger a queue dispatch on two printers at once** — the bottom-right toast should show both jobs progressing in parallel. The DB-insert phase is briefly serialised (startup-lock), but FTP upload + start happen concurrently. See [Per-Printer Queues → Dispatch behaviour](../features/print-queue.md#dispatch-behaviour).
6. **Log in again** (if upgrading 0.3.x → 0.4.x) so a refresh-token cookie is issued and the sliding-session flow takes over.

Migration log fragments to grep for:

```text
INFO  [backend.app.migrations] Applied m019 (version 19)
INFO  [backend.app.migrations] Applied m022 (version 22)
INFO  [backend.app.main] Startup complete
```

Failure indicators:

```text
ERROR  [backend.app.migrations] Migration mXXX failed: ...
sqlite3.OperationalError: no such column: ...
```

`no such column` / `no such table` on startup almost always means a migration didn't run — usually a filesystem permissions issue on `data/`. Fix with `sudo chown -R bamdude:bamdude /opt/bamdude/data` and restart.

---

## :material-undo-variant: 7. Rollback (if things break)

Because the schema advances forward only, the rollback plan is always **restore the pre-upgrade backup**. There is no automatic down-migration — you can't, for example, "undo" m019's archive↔queue refactor in place. Restoring a backup is the only path.

=== "Docker volumes"

    ```bash
    docker compose down

    # Wipe the new volume contents
    docker volume rm bamdude_data
    docker volume create bamdude_data

    # Restore from backup tarball
    docker run --rm \
      -v "$(pwd)/backup":/from \
      -v bamdude_data:/to \
      alpine sh -c 'cd /to && tar xzf /from/bamdude-data-YYYYMMDD.tar.gz'

    # Pin compose to the previous Docker tag before starting:
    # image: ghcr.io/kainpl/bamdude:0.4.0
    docker compose up -d
    ```

=== "Native (UI backup)"

    On a fresh install of the older tag, after first-run setup, open **Settings → Backup → Local Backup**, **Upload** the downloaded zip, then restart the service. The zip restores DB + archives + uploads + config in one go.

=== "Native (shell tar)"

    ```bash
    sudo systemctl stop bamdude
    cd /opt/bamdude
    sudo rm -rf data
    sudo tar xzf ~/bamdude-data-YYYYMMDD.tar.gz
    sudo -u bamdude git checkout v0.4.0       # or your prior tag
    sudo -u bamdude ./venv/bin/pip install -r requirements.txt
    sudo systemctl start bamdude
    ```

=== "PostgreSQL"

    ```bash
    docker compose down       # or stop the native service
    pg_restore -c -d "$DATABASE_URL" ~/bamdude-YYYYMMDD.dump
    # Then restore archive/ + library/ from the data tarball.
    docker compose up -d      # with image pinned to the previous tag
    ```

The version you roll back to **must be the one that created the backup** — otherwise the schema in the DB will be newer than what that code expects, and startup fails with a column-not-found error on the first read.

!!! info "Forward-only is intentional"
    Down-migrations would need code paths that BamDude doesn't carry — restoring from a backup is structurally simpler and always correct. The `:0.4.0` Docker tag stays pinned indefinitely so you can always roll back to it.

---

## :material-database: 8. Database backend notes

### SQLite (default)

The DB file lives at `data/bamdude.db`. SQLite pragmas: WAL journal, 15 s busy timeout, NORMAL synchronous. WAL means there's also `bamdude.db-wal` and `bamdude.db-shm` next to the main file — back up all three together (or stop the service first so the WAL is checkpointed into the main file).

If a legacy `bambuddy.db` (or `bambutrack.db`) exists in the data directory but `bamdude.db` does not, BamDude renames it on first boot before any migration runs. This is how the `m000_bambuddy_import` path takes effect for native installs that swap the binary in-place.

### PostgreSQL

Set `DATABASE_URL=postgresql+asyncpg://user:pass@host/db` in your environment. On first startup with a **fresh, empty** PostgreSQL database, BamDude auto-migrates content from the SQLite file if both are present (one-shot SQLite → PG copy). After the copy, only PG is used; the SQLite file is left in place for safety but no longer touched.

Existing PG installs run the same migration chain on every boot — same `_migrations` table, same versions, same sequencing. The dialect helpers route DDL through PG-native paths where SQLite needs `recreate_table` (FK changes, column drops). PG-side migrations also enforce FK constraints that SQLite lets pass silently — `m018` is a good example, where SET NULL only affects the live behaviour on PG.

---

## :material-database-search: 9. Data persistence — "new container started empty" {#9-data-persistence-new-container-started-empty}

The most common upgrade-time disaster is starting a fresh BamDude container and finding **no printers, no archives, no settings — like a clean install**. The data is almost never actually gone; it's still in a Docker volume or container layer that the new instance isn't reading from. This section walks every cause we've seen and the fix for each.

### Quick diagnostic

Run this on the host and read back what it prints. It enumerates BamDude-related containers, every volume that could plausibly hold data, the size of each volume, and the mount layout of any "old" container you kept around as a backup.

```bash
echo "=== Containers ==="
docker ps -a --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.CreatedAt}}" \
  | grep -iE "bamdude|bambuddy"
echo

echo "=== Volumes ==="
for v in $(docker volume ls -q | grep -iE "bamdude|bambuddy"); do
  size=$(docker run --rm -v "$v":/d alpine du -sh /d 2>/dev/null | awk '{print $1}')
  printf "%-50s  %s\n" "$v" "$size"
done
echo

echo "=== Old container mounts (replace 'bamdude-old' with the actual name) ==="
docker inspect bamdude-old --format '{{range .Mounts}}{{.Type}}: {{.Source}} → {{.Destination}}{{"\n"}}{{end}}'
echo

echo "=== Old container DATA_DIR contents ==="
docker exec bamdude-old sh -c 'echo "DATA_DIR=$DATA_DIR"; ls -la "$DATA_DIR" 2>/dev/null | head'
```

A healthy data volume is **tens of MB minimum** (SQLite + thumbnails) and typically **GBs** with archive history. A fresh / empty volume is a few hundred KB at most. That contrast usually pinpoints where the data lives in two seconds.

---

### Scenario A — Compose project name changed (most common)

Docker Compose v2 namespaces every named volume by the **project name**, which by default is the **basename of the directory the compose file lives in**. The volume entry that reads `bamdude_data` in your `docker-compose.yml` becomes `<project>_bamdude_data` on disk:

| Setup | Real volume name |
|---|---|
| `~/bambuddy/docker-compose.yml` (upstream Bambuddy) | `bambuddy_bambuddy_data` |
| `~/bamdude/docker-compose.yml` | `bamdude_bamdude_data` |
| `~/bamdude-new/docker-compose.yml` | `bamdude-new_bamdude_data` |
| `~/3d/bamdude/docker-compose.yml` (with `COMPOSE_PROJECT_NAME=3d`) | `3d_bamdude_data` |

Renaming the compose folder (`mv ~/bamdude ~/bamdude-old`) and unpacking a fresh checkout at the original path therefore creates a **brand-new namespace**, and `docker compose up -d` provisions an empty `bamdude_bamdude_data` while your real data sits in `bamdude-old_bamdude_data`. Both volumes show up in `docker volume ls`; only one has the data.

**Fix — point the new project at the existing volume:**

The cleanest path is to declare the existing volume as `external` in the new compose file so Docker Compose doesn't try to manage it:

```yaml
services:
  bamdude:
    # ... unchanged ...
    volumes:
      - bamdude_data:/app/data
      - bamdude_logs:/app/logs

volumes:
  bamdude_data:
    external: true
    name: bamdude-old_bamdude_data    # the volume that has your data
  bamdude_logs:
    external: true
    name: bamdude-old_bamdude_logs    # likewise for logs
```

After `docker compose up -d`, the new container reads/writes the same physical volume the old one used. Once you've verified everything works, you can stop the old container and free its name.

**Or — copy the data into the new volume:**

If you'd rather keep the new project's namespacing clean and end up with a single `<new>_bamdude_data` volume:

```bash
# Stop the new container so it doesn't race the copy.
docker compose down

# Recreate the (empty) target volume just to be safe.
docker volume rm <new>_bamdude_data
docker volume create <new>_bamdude_data

# One-shot copy with a throw-away alpine container that mounts both volumes.
docker run --rm \
  -v bamdude-old_bamdude_data:/from:ro \
  -v <new>_bamdude_data:/to \
  alpine sh -c 'cp -a /from/. /to/'

# Start the new compose project.
docker compose up -d
```

---

### Scenario B — Container layer (no volume at all)

If the original install was a bare `docker run ghcr.io/kainpl/bamdude:latest` **without a `-v bamdude_data:/app/data`** flag, all writes landed in the container's writable layer. Renaming that container with `docker rename` preserves the layer (and therefore the data), but starting a fresh container from the same image creates a **new** layer. New layer = no `bamdude.db`, no archives.

You can detect this by running `docker inspect <old_container>` and checking `.Mounts`. If there's no entry mounting `/app/data`, the data is in the layer.

**Fix — extract the data, then move to a proper volume-backed setup:**

```bash
# Copy the data out of the old container's layer onto the host.
docker cp bamdude-old:/app/data ./bamdude-data-recovered

# Create a proper named volume and seed it.
docker volume create bamdude_bamdude_data    # match your new project's namespace
docker run --rm \
  -v "$(pwd)/bamdude-data-recovered":/from:ro \
  -v bamdude_bamdude_data:/to \
  alpine sh -c 'cp -a /from/. /to/'

# Use the official compose file — it always declares a volume.
cd ~/bamdude
docker compose up -d
```

Going forward, **always** declare a volume (named or bind-mount) for `/app/data` and `/app/logs`. The shipped `docker-compose.yml` does this; raw `docker run` commands need an explicit `-v`.

---

### Scenario C — Bind-mount path changed

If your compose used a bind-mount (`./data:/app/data` or `/srv/bamdude:/app/data`) instead of a named volume, moving the compose folder also moves the bind-mount target. The new install lands at a fresh empty path.

```yaml
volumes:
  - ./data:/app/data    # path is RELATIVE TO THE COMPOSE FILE
```

Detect with `docker inspect <container> --format '{{range .Mounts}}{{.Source}}{{"\n"}}{{end}}'`. If a `/srv/...` or `/home/...` host path appears, that's where the data really is.

**Fix — copy the host directory into the new location, or point the new compose at the old path:**

```bash
# Option 1: relocate the bind directory.
mv ~/bamdude-old/data ~/bamdude/data
docker compose up -d

# Option 2: keep the data where it is, point the new compose at it.
# Edit volumes: in docker-compose.yml to use the absolute old path:
#   - /home/user/bamdude-old/data:/app/data
docker compose up -d
```

---

### Scenario D — PUID / PGID mismatch (data is there but the app can't read it)

The shipped compose runs the container as `${PUID:-1000}:${PGID:-1000}`. If your old container ran as `1000:1000` and the new run uses different IDs (e.g. you set `PUID=$(id -u)` in a shell where `id -u != 1000`), the volume's files belong to a UID the new process cannot read or write. Symptoms vary:

- Startup logs show `PermissionError: [Errno 13] Permission denied: '/app/data/bamdude.db'`
- Or the app silently falls back to a fresh DB next to the unreadable old one
- Or `init_db` fails on the first migration write

Check ownership with:

```bash
docker run --rm -v bamdude_bamdude_data:/d alpine ls -ln /d
```

The numeric UID / GID in the third and fourth columns must match what `id -u` / `id -g` returns for the user the new container runs as.

**Fix — chown the volume contents to the new IDs:**

```bash
docker compose down
docker run --rm -v bamdude_bamdude_data:/d alpine chown -R 1000:1000 /d
# Or whatever PUID:PGID your compose uses now.
docker compose up -d
```

The Dockerfile already `chmod 777`s `/app/data` at build time, so Docker bind-mounted directories inherit that loose mode. Named volumes pick up the ownership of the **first** writer to them, which is why a one-time chown is enough.

---

### Scenario E — `docker compose down -v` (volumes deleted)

The `-v` flag on `docker compose down` permanently removes the project's named volumes. If you ran this before the upgrade ("just to be safe"), the data is **gone from Docker's perspective** — there is no Recycle Bin. The renamed-old container only helps if it was started with a **bind-mount** (host directory survives) or kept its data in the **container layer** (Scenario B).

Sanity check: `docker volume ls | grep bamdude` should show the old volumes too if they exist. If only the freshly created ones appear and none has the GB-scale size, the data was deleted.

**Recovery — restore from the application-level backup:**

The only reliable recovery in this case is the BamDude UI backup zip, which you should have pre-upgrade per [§1](#1-pre-upgrade-checklist). The flow:

1. Bring the new BamDude up (it lands in the setup-required state).
2. Complete first-run setup with throwaway credentials — the next step replaces the DB anyway.
3. Open **Settings → Backup → Local Backup → Upload Backup** and pick the pre-upgrade zip.
4. Restart the container so the migration system reconciles against the restored DB.

This restores `bamdude.db`, archives, library files, thumbnails, uploads, and every Settings row. Encrypted secrets (TOTP, OIDC `client_secret`) restore correctly because the backup carries the metadata `MFA_ENCRYPTION_KEY` was used to encrypt them — the **same key** must be set in the new container's environment, otherwise those rows will fail to decrypt.

If you have **no backup** and none of the prior scenarios apply, the data is unrecoverable.

---

### Scenario F — Container manager UI (Portainer / Dockge / Komodo) creates its own namespace

GUI Docker managers often create their own Compose project on import — Portainer's "stacks" become projects named after the stack, Dockge mounts each compose under `/opt/stacks/<name>` and uses that name as the project. Importing the same compose file under a different stack name produces a fresh volume namespace just like Scenario A.

The fix is identical to Scenario A: declare the existing volume as `external` and point at it by its real name. Run `docker volume ls` to see what name the GUI created and which one your old install used.

---

### Scenario G — Image moved `DATA_DIR` between versions (rarely the cause)

BamDude has shipped `ENV DATA_DIR=/app/data` since the first Docker release and we've never moved it — this scenario is documented for completeness in case you're upgrading from a private fork or a custom image. If you ever moved data into `/data` instead of `/app/data` in your own image, the volume mounted at the old path won't be picked up by the new image. Move the data:

```bash
docker run --rm \
  -v <volume>:/v \
  alpine sh -c 'mkdir -p /v/app/data && mv /v/data/* /v/app/data/ 2>/dev/null'
```

Or simply re-mount the volume at the new path the image expects:

```yaml
volumes:
  - bamdude_data:/app/data    # not /data
```

---

### Why our legacy-DB rename doesn't always fire

BamDude's startup (`migrations/__init__.py`) renames `bambuddy.db` / `bambutrack.db` to `bamdude.db` if found in the data directory. This **only fires when the legacy file is inside the new container's `/app/data`** — i.e. when the volume mount is correct. If the new container is reading from a fresh empty volume (Scenarios A, C, D, E), there is no legacy file to rename in the first place; the rename logic is irrelevant.

The fix is always the same shape: get the new container reading from the volume that holds your data, by either pointing at the existing volume (`external: true`) or copying the data into the new one.

---

## :material-bug: Troubleshooting

**Startup log shows `setup_required` 503s on every endpoint**
: First boot creates no admin. Open `/` in a browser to go through the setup flow. This is normal for fresh installs and after every `cli reset_admin`.

**`no such column` / `no such table` on startup**
: A migration didn't run. Check the log for the stack trace; usually it means the file permissions on `data/` don't allow the service user to write. Fix with `sudo chown -R bamdude:bamdude /opt/bamdude/data`.

**Bambuddy import didn't fire**
: Either `bamdude.db` already exists (so the file was never scanned) or the file is not named `bambuddy.db` / `bambutrack.db`. Rename and restart — the migration check re-runs on every boot until applied.

**Docker volume copy fails with `device or resource busy`**
: Stop both the source and the destination container first. The `--rm` alpine container mounting both volumes cannot share the filesystem with a running service holding open files.

**Native update leaves the service broken**
: `update.sh` writes a backup before it touches anything (`/opt/bamdude/backups/pre-update-YYYYMMDD-HHMMSS/`). Stop the service, restore the backup directory over `data/`, and check out the prior git tag.

**Long pause on 0.4.1 first boot**
: That's `m022` walking every 3MF on disk. Tail the log — you should see `m022 library_files: progress N/M` lines every batch of 100. Don't kill the process; restarting just resumes from where the batch commit left off.

**`database is locked` mid-migration**
: You started the service before the previous instance fully stopped. Stop, wait for the old process to exit (check with `pgrep -f bamdude` / `docker compose ps`), then start again. The migration system is idempotent — failed-mid-run migrations re-run cleanly on next boot.

---

## :material-new-box: What's new in 0.4.x

| Feature | Description |
|---------|-------------|
| **Per-Printer Queues** | Independent queue per printer with card-based UI; quantity > 1 routes every copy through the queue (no special "primary"). |
| **Queue↔archive refactor** | Live queue auto-cleans; queue history lives on `print_archives` (m019). |
| **Parallel dispatch** | Multiple printers can receive jobs simultaneously. The brief DB-write phase is wrapped in a startup-lock (still serialised) to keep SQLite from racing on `INSERT INTO print_archives`; everything else — FTP upload, the actual MQTT start command — runs in parallel. The earlier "one job at a time across the farm" gate that landed mid-0.4.1 was scrapped once the startup-lock was in. |
| **Sliding-session auth** | Access JWT TTL 1 h; rotating refresh cookie keeps users signed in transparently. Remember-me opts into 30-day persistence. |
| **MFA + OIDC** | TOTP, email OTP, 10 backup codes, OIDC SSO with PKCE + JWKS + SSRF guards. Encrypted at rest with `MFA_ENCRYPTION_KEY`. |
| **MQTT-action macros** | Macros can invoke an MQTT command (`chamber_light_off` / `chamber_light_on`) on `print_started` / `print_finished` with optional delay. Supersedes the legacy `auto_light_off` flag. |
| **Per-project print plan** | Each project carries an ordered list of its `.3mf` library files with copies stepper, per-row totals, and a grand-totals strip. |
| **3MF download recovery** | Fallback archives auto-fill via FTP when the printer was unreachable at print start. |
| **Label-object metadata** | Skip-objects support flags extracted from `Metadata/project_settings.config` and persisted on every library file + archive (m022). |
| **Server-side slicing** *(0.4.2b3)* | OrcaSlicer + BambuStudio sidecar containers in the same Compose project (`--profile orca` / `--profile bambu` / `--profile all`), per-job slicer picker in the Slice modal with live reachability badges, bed-type override (Cool / Engineering / High-Temp / Textured PEI / SuperTack), inline multi-plate selection, owner-filter on preset dropdowns. |
| **Composite file tags** *(0.4.2b3)* | `library_files.file_tags` JSON column drives badges + chip-row filter on the File Manager: format (`gcode` / `3mf` / `stl` / `obj` / `step`), readiness (`sliced` / `project` / `geometry`), modifiers (`swap` / `multiplate`), provenance (`makerworld`). m036 + m037 backfill historical rows. |
| **Per-plate archive awareness** *(0.4.2b3)* | Multi-plate archives now record which plate of the source 3MF was actually printed; thumbnail, print info, G-code preview, and 3D model all reflect that plate. m038 backfills `plate_index` on existing rows and re-parses 3MFs where `plate_index > 1` to update slicer-derived columns + thumbnail. |
| **Library viewer capabilities + correct bed** *(0.4.2b3)* | New `/library/files/{id}/capabilities` endpoint (mirrors archive route) drives 3D / G-code tab visibility from `file_tags` instead of file-extension probing; the 3D viewer now draws a translucent build-volume wireframe matching the printer's bed (was hardcoded 256³). |

See [CHANGELOG.md](https://github.com/kainpl/bamdude/blob/main/CHANGELOG.md) for the per-version detail.
