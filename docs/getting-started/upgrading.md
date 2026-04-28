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

## :material-database-cog: 4. Migration overview — what each version changes

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

See [CHANGELOG.md](https://github.com/kainpl/bamdude/blob/main/CHANGELOG.md) for the per-version detail.
