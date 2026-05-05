---
title: Backup & Restore
description: Manual ZIP backups, scheduled local backups, and Git-pushed profile backups
---

# Backup & Restore

Three independent paths protect your install: an on-demand ZIP from the UI, a scheduled local-disk job that keeps the last N snapshots, and a Git push that archives printer profiles to GitHub or GitLab.

---

## :material-backup-restore: What's in a Backup ZIP

The on-demand and scheduled local backups produce the same ZIP layout. Top-level entries:

| Entry | Contents |
|-------|----------|
| `bamdude.db` | The full database, **always exported as portable SQLite** — even when your runtime is PostgreSQL the dump goes through `dump_to_sqlite()` so the same ZIP restores onto either backend. |
| `archive/` | Every per-print archive directory: `.3mf`, thumbnail PNG, plate-N.png, and the per-archive folder. |
| `virtual_printer/` | Pending uploads + virtual-printer working state. |
| `plate_calibration/` | Reference frames + ROI definitions used by plate detection. |
| `icons/` | Custom icons uploaded for printers / projects. |
| `projects/` | Project attachments. |

Excluded by design: `logs/`, caches, temp files, the bundled frontend (it ships with the image / repo). Some sensitive fields are also filtered before the database dump — LDAP bind password is never returned in API responses, and API keys are stored as one-way hashes.

!!! note "PostgreSQL → SQLite → PostgreSQL"
    Even on a PostgreSQL runtime, `dump_to_sqlite()` normalises the export. Restoring on a fresh PostgreSQL install runs the inverse `import_sqlite_to_postgres()` and re-creates rows in the live database. The same ZIP also restores onto a SQLite install with no extra steps.

---

## :material-download: Manual Backup

1. **Settings → System → Backup & Restore**
2. Click **Create Backup**
3. Browser downloads `bamdude-backup-YYYYMMDD-HHMMSS.zip`

The ZIP is streamed from a temp file rather than buffered in memory, so multi-gigabyte backups don't OOM the process. The temp file is deleted automatically once the response finishes.

API: `GET /api/v1/settings/backup` (requires `settings:backup`).

---

## :material-clock-outline: Scheduled Local Backups

Set under **Settings → System → Local Backup Schedule**. The scheduler ticks once per minute and fires due jobs into the same ZIP builder the manual button uses, then prunes older backups beyond the retention limit.

| Setting | Default | Notes |
|---------|---------|-------|
| `local_backup_enabled` | `false` | Master switch. |
| `local_backup_schedule` | `daily` | `hourly`, `daily`, or `weekly`. |
| `local_backup_time` | `03:00` | `HH:MM` for daily/weekly runs (server-local time). Hourly ignores this. |
| `local_backup_retention` | `5` | Keep the most recent N backups; older ones auto-prune. Range 1–100. |
| `local_backup_path` | empty | Output directory. Empty = `data/backups/`. |

The settings page shows last-run timestamp + outcome (`success` / `failed`), the next scheduled run, and a list of currently retained backups with file sizes. Manual "Create Backup" runs are stored in the same directory and counted toward retention.

Legacy `bambuddy-backup-*.zip` files (from upstream installs) are still listed and restorable so an upgrade doesn't strand pre-existing snapshots.

---

## :material-source-branch: Git Backup (Profiles to GitHub / GitLab)

Distinct from the ZIP flow. **Settings → System → Git Backup** pushes selected printer-profile data to a GitHub or GitLab repository — useful for off-site profile sync, multi-host farm coordination, and PR-based change history of your printer settings.

### :material-cog-outline: Configuration

| Setting | Notes |
|---------|-------|
| Provider | `github`, `gitlab`, `gitea`, or `forgejo`. |
| Repository URL | Full clone URL (HTTPS form). |
| Access Token | Personal Access Token. Stored encrypted at rest. |
| Branch | Target branch (default `main`). |
| API base URL | Self-hosted GitLab only. |
| Allow insecure HTTP | For self-hosted Gitea/Forgejo/GitLab without HTTPS. |
| Schedule | `hourly` / `daily` / `weekly`, or off. |

### :material-account-key: Provider setup walkthroughs

=== ":material-github: GitHub"

    1. **Create a GitHub repository** (private is fine).
    2. **Generate a Personal Access Token (PAT)**:
        - Go to [GitHub Personal Access Tokens](https://github.com/settings/tokens){ target="_blank" rel="noopener" }.
        - Click **Generate new token** → **Generate new token (classic)**.
        - Choose your expiration (`No expiration` is recommended for unattended scheduled backups).
        - Under **Select scopes**, check `repo` (required for repository access and commits).
    3. **Configure in BamDude**:
        - **Settings** → **Backup & Restore** → Git Backup.
        - Provider: `github`.
        - Repository URL: e.g. `https://github.com/username/bamdude-backup`.
        - Enter the PAT.
        - Click **Test Connection**.

    !!! note "Fine-grained tokens"
        Instead of classic tokens, you can use GitHub's fine-grained tokens. Grant `Read access to Metadata` — `Read and Write access to code` is automatically included on creation.

=== ":material-gitlab: GitLab"

    1. **Create a GitLab repository** (private is fine).
    2. **Generate a Personal Access Token**:
        - Go to [GitLab Personal Access Tokens](https://gitlab.com/-/user_settings/personal_access_tokens){ target="_blank" rel="noopener" }.
        - Click **Add new token** (Legacy / classic shape).
        - Under scopes, check `api` (required for repository access and commits).
    3. **Configure in BamDude**:
        - Provider: `gitlab`.
        - For self-hosted GitLab, also fill **API base URL**.
        - If hosted locally without HTTPS, tick **Allow insecure HTTP**.
        - Repository URL: e.g. `https://gitlab.com/username/bamdude-backup`.
        - Enter the PAT.
        - Click **Test Connection**.

    !!! note "Project Access Tokens"
        Project Access Tokens also work — grant the `api` and `write_repository` scopes, otherwise commits will fail with access errors.

=== ":material-git: Gitea"

    1. **Create a new repository** (private is fine).
    2. **Generate a Personal Access Token**:
        - **Settings** → **Applications** in your Gitea profile.
        - Under **Access Tokens**, name the token.
        - Set scope to `All (public, private, and limited)`.
        - Select `Read and write` under **repository** permissions.
        - Click **Generate token**.
    3. **Configure in BamDude**:
        - Provider: `gitea`.
        - Repository URL: e.g. `https://gitea.example.com/username/bamdude-backup`.
        - If hosted locally without HTTPS, tick **Allow insecure HTTP**.
        - Specify the correct **Branch** (`main`, `master`, etc.).
        - Enter the PAT.
        - Click **Test Connection**.

=== ":material-git: Forgejo"

    1. **Create a new repository** (private is fine).
    2. **Generate a Personal Access Token**:
        - **Settings** → **Applications** in your Forgejo profile.
        - Under **Manage Access Tokens**, name the token.
        - Click **Generate Token**.
    3. **Configure in BamDude**:
        - Provider: `forgejo`.
        - Repository URL: e.g. `https://forgejo.example.com/username/bamdude-backup`.
        - If hosted locally without HTTPS, tick **Allow insecure HTTP**.
        - Enter the PAT.
        - Click **Test Connection**.

!!! warning "Bambu Cloud login required for K-profiles + Cloud profiles"
    Backing up *Cloud profiles* and *K-profiles* requires an active Bambu Cloud login. Sign in via **Profiles → Cloud Profiles** before scheduling a Git backup that includes those categories — otherwise the relevant directories will be empty in the repo.

### :material-checkbox-marked: What gets pushed

Toggle each independently. Defaults are tuned for "back up the things most operators want, leave the noisy/large things off":

| Category | Description | Default |
|----------|-------------|:-------:|
| **K-profiles** | Per-printer pressure-advance profiles (organized by serial number). | :material-check: On |
| **Cloud profiles** | Filament, printer, and process profiles from Bambu Cloud. | :material-check: On |
| **Spools** | Full inventory dump (rows + usage history). | :material-check: On |
| **Archives (metadata)** | Print history metadata — filament, temperatures, times, costs, energy (no 3MF / no thumbnails). | :material-check: On |
| **App settings** | Application settings table (sensitive fields excluded). | :material-close: Off |
| **Archives (3MF + thumbnails)** | Bulk 3MF + thumbnail file content — bumps repo size by ~50–500 MB per 100 prints. | :material-close: Off |

Only changed files generate commits — a no-op run is recorded as `skipped`.

### :material-folder-tree: Repository structure

After a successful run, the repo looks like:

```
repo/
├── backup_metadata.json
├── kprofiles/
│   └── {serial_number}/
│       ├── 0.2.json
│       ├── 0.4.json
│       └── ...
├── cloud_profiles/
│   ├── filament.json
│   ├── printer.json
│   └── process.json
├── settings/
│   └── app_settings.json
├── spools/
│   ├── inventory.json
│   └── usage_history.json
└── archives/
    └── print_history.json
```

The flat structure makes partial restore unambiguous — you can pull just `kprofiles/{serial}/` for one printer, or just `spools/inventory.json` for inventory recovery, without touching the rest.

### :material-monitor-dashboard: Status panel

The settings page shows the live status:

- **Last backup** — timestamp, status (`success` / `failed` / `skipped`), commit SHA, and message.
- **Next scheduled run** — when the scheduler will fire next.
- **Log table** — historical runs with trigger (`manual` / `scheduled`), duration, and any error message.
- **Run Now** button — fires an immediate push regardless of schedule.

Push frequency, content checkboxes, and credentials can all be edited live without restarting BamDude.

---

## :material-upload: Restoring a Backup ZIP

1. **Stop BamDude** before restoring (or the upload below replaces files under a running process — risky).
2. Either drop the ZIP into the data directory and let BamDude detect it on next boot, or use **Settings → System → Restore** and upload through the form.
3. On boot / form submission, BamDude:
   - Extracts the ZIP into a temp dir
   - Closes the current DB connections
   - Replaces the database (`bamdude.db` import on SQLite, `import_sqlite_to_postgres` on PG)
   - Replaces `archive/`, `virtual_printer/`, `plate_calibration/`, `icons/`, `projects/`
   - Re-initialises the database (runs pending migrations on the restored data)
   - Deletes the source ZIP after success

!!! danger "Restore replaces current state"
    The restore overwrites the live DB and the data directories listed above. **Take a fresh backup of the current state first** if you might want to roll back the restore itself.

API: `POST /api/v1/settings/restore` (multipart `file=…`, requires `settings:restore`).

### :material-database-arrow-right: Cross-backend restore

The portable SQLite dump means you can:

- Take a backup from a **SQLite** install → restore onto **PostgreSQL** (the loader migrates rows).
- Take a backup from a **PostgreSQL** install → restore onto **SQLite** (DB was already exported as SQLite).
- Take a backup from PG → restore onto a fresh PG (loader re-imports SQLite into PG).

Conflicting primary keys are merged or skipped per row depending on the table — referential integrity is preserved across the migration.

---

## :material-folder-download: Bulk archive export

3MF files and thumbnails aren't included in the default Backup ZIP layout (they live in `archive/` only when explicitly opted-in). For dedicated archive export:

1. Go to **Archives**.
2. Click **Export**.
3. Tick **Include 3MF files** in the export modal.
4. Optionally narrow by date range, printer, or status.
5. Download the resulting ZIP.

Useful for hand-off to another print farm, archival into cold storage, or one-time migration without dragging the full database along.

---

## :material-database-export: Manual SQLite / PostgreSQL backup

If you want a CLI / scripted backup outside BamDude's UI flow — e.g. for inclusion in a wider system backup, or PostgreSQL-specific point-in-time recovery — go directly to the database engine:

=== ":material-database: SQLite (default)"

    Stop BamDude first to ensure a consistent snapshot, then:

    ```bash
    # Plain copy (fastest)
    cp /path/to/bamdude.db bamdude_$(date +%Y%m%d).db

    # SQL dump (portable across versions)
    sqlite3 /path/to/bamdude.db ".dump" > bamdude.sql

    # Restore from SQL dump
    sqlite3 new_bamdude.db < bamdude.sql
    ```

=== ":material-elephant: PostgreSQL"

    Connect using your `DATABASE_URL`:

    ```bash
    # Custom-format dump (recommended — supports parallel restore + selective restore)
    pg_dump -Fc bamdude > bamdude.backup
    # or with explicit DSN:
    pg_dump -Fc "postgresql://user:pass@host:5432/bamdude" > bamdude.backup

    # Restore (drops + recreates objects on import)
    pg_restore -d bamdude bamdude.backup
    # or with explicit DSN:
    pg_restore --clean --if-exists \
        -d "postgresql://user:pass@host:5432/bamdude" bamdude.backup
    ```

    !!! tip "BamDude's built-in backup is easier"
        The Settings → Backup page produces portable backups that work across both SQLite and PostgreSQL. Use manual `pg_dump` only when you need PostgreSQL-specific features like point-in-time recovery, logical-replication snapshotting, or integration with an existing PG backup pipeline.

!!! warning "Stop BamDude before raw file copy"
    Direct `cp` of `bamdude.db` while BamDude is running can capture an inconsistent WAL state. The portable Settings → Backup flow handles this safely — manual file copy needs the process stopped first.

---

## :material-restore: Recovery scenarios

Three common shapes the recovery flow takes:

### Lost database

DB is corrupted, deleted, or otherwise unrecoverable:

1. Stop BamDude.
2. Remove the corrupted `bamdude.db` (or drop the PostgreSQL database).
3. Start BamDude — it creates a fresh empty DB on first boot.
4. **Settings → System → Restore** → upload your latest backup ZIP.
5. BamDude replaces the empty DB with the restored one and runs pending migrations.

### New installation

Moving to a new server / new Docker host:

1. Install BamDude on the new host (Docker compose, bare metal, whichever).
2. Boot once so the data directory is created and the setup-gate is sitting on `setup_required`.
3. Copy your backup ZIP onto the new host.
4. **Settings → System → Restore** → upload the ZIP — note the same setup-gate whitelists `/restore`-style flow when no admin exists yet, but in practice the easiest path is to complete setup with a placeholder admin first, then restore (which replaces the placeholder with your real users).

### Data migration

Migrating between database backends, between OS hosts, or moving Docker volumes:

1. Take a backup on the old install (Settings → Backup → Create Backup).
2. Stand up BamDude on the new host.
3. Restore from the backup ZIP — BamDude's portable SQLite layer translates SQLite ↔ PostgreSQL automatically (see "Cross-backend restore" above).
4. Verify printers reconnect, profiles are present, archives load. Then decommission the old host.

---

## :material-file-chart: Backup file size guidance

Rough sizing so you can plan storage:

| Profile | Approximate size | Contents |
|---------|-----------------:|----------|
| **Small** | < 50 MB | DB only — no archives, no 3MFs, no library files. |
| **Medium** | 100–500 MB | DB + archive metadata + thumbnails (no 3MFs). |
| **Large** | 1–50 GB | DB + full 3MF + thumbnails + library files + timelapses. |

If you have many timelapse videos, large profile is the right model — periodic cleanup of old timelapses (or excluding `archive/` from a separate full-data backup) is the easiest way to keep the ZIP manageable.

---

## :material-shield-check: Best practices

- **Daily for production** — combine **Scheduled Local Backups** with `daily` frequency (e.g. 03:00) and `retention=7` to keep a rolling week.
- **Off-site at least one** — store one snapshot somewhere not on the BamDude host: NAS share, cloud storage (Dropbox / Google Drive / S3 via rclone), or an external USB drive that's rotated weekly. Hardware loss only hurts you when both copies are on the same hardware.
- **Periodic restore drill** — every few months, take a backup ZIP and try restoring it onto a throwaway BamDude install. A backup you've never restored is a backup that might not work.
- **Backup before upgrade** — the [`UPDATING.md`](https://github.com/kainpl/bamdude/blob/main/UPDATING.md) protocol recommends a fresh manual backup before every minor-version upgrade. Migrations are idempotent and one-shot but a downgrade has no automatic path.
- **Date-suffix manual backups** — when grabbing a manual backup before a risky change, name it for what triggered it (`bamdude-pre-0.5.0-upgrade.zip`) so you find it later.

---

## :material-docker: Docker volume bind-mount example

For Docker users, mount the backup output directory as a volume so backups persist outside the container — and ideally onto a NAS share for off-site coverage:

```yaml
services:
  bamdude:
    image: ghcr.io/kainpl/bamdude:latest
    container_name: bamdude
    network_mode: host
    volumes:
      - bamdude_data:/app/data
      - bamdude_logs:/app/logs
      - ./backups:/app/data/backups          # local relative path
      # or
      - /mnt/nas/bamdude-backups:/app/data/backups   # NAS / network share
    environment:
      - TZ=Europe/Kyiv
      - BACKUP_DIR=/app/data/backups
    restart: unless-stopped

volumes:
  bamdude_data:
  bamdude_logs:
```

Or with `docker run`:

```bash
docker run -d \
  --network host \
  -v bamdude_data:/app/data \
  -v bamdude_logs:/app/logs \
  -v /mnt/nas/bamdude-backups:/app/data/backups \
  -e TZ=Europe/Kyiv \
  -e BACKUP_DIR=/app/data/backups \
  --name bamdude \
  --restart unless-stopped \
  ghcr.io/kainpl/bamdude:latest
```

`BACKUP_DIR` overrides the default `data/backups/` path inside the container — use it when your bind mount lands somewhere other than `/app/data/backups`.

!!! tip "NAS / Samba / NFS"
    Point the bind mount at a NAS share, Samba mount, or NFS path for automatic off-site backups without any extra scripts. Combined with the retention-based rotation, you get a hands-off off-site backup pipeline.

---

## :material-lightbulb: Tips

!!! tip "Off-site coverage"
    Combine **Scheduled Local Backups** (full data, on-disk) with **Git Backup** (profiles, off-site) — the local one survives a software wipe, the git one survives a hardware loss.

!!! tip "Backup before upgrade"
    [`UPDATING.md`](https://github.com/kainpl/bamdude/blob/main/UPDATING.md) recommends a fresh manual backup before every minor-version upgrade. Migrations are idempotent and one-shot but a downgrade has no automatic path.

> Originally based on [Bambuddy](https://github.com/maziggy/bambuddy) documentation.
