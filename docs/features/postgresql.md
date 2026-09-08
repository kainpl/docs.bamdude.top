---
title: PostgreSQL Support
description: SQLite, a bundled PostgreSQL, or your own server — one setting picks the database backend
---

# PostgreSQL Support

BamDude stores everything in **SQLite** by default — nothing to configure, one file, great for most farms. When a large, busy farm wants PostgreSQL, you have two ways to get it, both chosen with a single setting:

- **Bundled PostgreSQL** — a full PostgreSQL 18 that ships with BamDude and that BamDude runs for you. No server to install, no connection string to write.
- **Your own PostgreSQL** — an external server you already run, given as a URL.

One variable, `DATABASE_URL`, selects between the three:

| `DATABASE_URL` | Backend |
|----------------|---------|
| *empty / unset* | SQLite (the default) |
| `embedded` | the bundled PostgreSQL 18 |
| `postgresql+asyncpg://…` | an external PostgreSQL server |

Anything else is refused at startup with a readable message, so a typo is caught immediately rather than as a connection error later.

---

## :material-database: When to Use Which

| Scenario | Recommended |
|----------|:-----------:|
| Single user, 1–5 printers | SQLite |
| Small farm, < 10 printers | SQLite |
| Busy farm, 10+ printers | PostgreSQL |
| **40+ printers** | **PostgreSQL — treat this as required** |
| High concurrency (many API clients) | PostgreSQL |
| Want PostgreSQL without running a server | **`embedded`** |
| Already run PostgreSQL, want BamDude to use it | external URL |
| Simplest possible setup | SQLite |

The bundled and external servers are the same PostgreSQL to BamDude — the difference is only who starts and stops it.

!!! warning "Past about 40 printers, move to PostgreSQL"
    SQLite allows exactly one writer at a time, and its page cache is per connection, so every connection in a busy pool starts cold. Neither is a setting anyone can tune around: at that size the writer becomes the queue everything waits in. Switching is one variable and a restart — the import runs itself — so do it before the farm grows into the problem rather than after. `embedded` is the least work: no server to install or administer.

---

## :material-package-variant-closed: The bundled PostgreSQL (`embedded`)

Set one variable:

```env
DATABASE_URL=embedded
```

That is all. On the next start BamDude:

1. initialises a PostgreSQL 18 cluster under `DATA_DIR/postgres/18` (once),
2. starts it on `127.0.0.1` with a password it generates for itself,
3. imports your existing `bamdude.db` if there is one (see [Migrating from SQLite](#migrating-from-sqlite), below),
4. and stops it cleanly when BamDude shuts down.

The binaries come from our open-source [`embedded-postgres`](https://github.com/kainpl/embedded-postgres) package (PostgreSQL 18 + `pgvector` + `pg_stat_statements`), shipped as a wheel for Linux (x86_64, aarch64, armv7l), macOS and Windows, and pulled in automatically with BamDude's Python dependencies. Nothing to download by hand.

### Where its files live

| File | Purpose |
|------|---------|
| `DATA_DIR/postgres/18/` | the database cluster (versioned by the PostgreSQL major) |
| `DATA_DIR/postgres/password` | the generated password (mode 0600) |
| `DATA_DIR/postgres/port` | the port it settled on (only when not pinned) |

### Reaching it with other tools

By default the server picks a free port and remembers it in `DATA_DIR/postgres/port`. Pin a known port instead so you can connect with `psql`, DBeaver, pgAdmin, Grafana and the like:

```env
DATABASE_URL=embedded
EMBEDDED_PG_PORT=6432
```

Then, for example:

```bash
psql -h 127.0.0.1 -p 6432 -U bamdude -d bamdude
# password: the contents of DATA_DIR/postgres/password
```

The server listens on `127.0.0.1` only — it is not exposed to your network.

!!! info "One PostgreSQL major, pinned"
    The bundled server is PostgreSQL 18 and BamDude refuses to open a cluster created by a different major. A future major upgrade ships as its own release with an explicit migration step, so an upgrade never silently rewrites your data directory.

---

## :material-download: Choosing the backend in the installers

Every installer now asks which backend you want, and an upgrade keeps whatever you already use.

=== "Linux / macOS (`install.sh`)"

    Interactively it asks SQLite / bundled / external. Unattended:

    ```bash
    ./install.sh --db embedded --yes
    ./install.sh --db external --database-url "postgresql+asyncpg://user:pass@host:5432/bamdude" --yes
    ```

    With the bundled server the service unit is given a longer, cleaner shutdown window (systemd `TimeoutStopSec=90` + `KillMode=mixed`) so its checkpoint always completes.

=== "Windows (installer `.exe`)"

    The wizard has a **Database** page with four choices:

    - **SQLite** (default),
    - **bundled PostgreSQL as its own Windows service** — registers a `BamDudePostgres` service that starts before BamDude (most robust),
    - **bundled PostgreSQL run by BamDude** — one service, simplest,
    - **external PostgreSQL** — enter the URL.

    Uninstalling asks (defaulting to *No*) whether to also delete all data, and cleanly removes the PostgreSQL service.

=== "Docker (`docker-install.sh`)"

    Asks SQLite / bundled-in-container / a separate PostgreSQL container / external URL, and writes `.env` for you. See the Docker section below.

---

## :material-cog: Using an external server

Point `DATABASE_URL` at your server. The **driver must be `postgresql+asyncpg`**, and the **database must already exist** — BamDude creates the tables, not the database.

```env
DATABASE_URL=postgresql+asyncpg://bamdude:password@192.168.1.100:5432/bamdude
```

| Component | Value |
|-----------|-------|
| Driver | `postgresql+asyncpg` (required) |
| User / Password | your database credentials |
| Host | the server's address |
| Port | default `5432` |
| Database | must already exist |

---

## :material-docker: PostgreSQL with Docker

There are two easy paths.

### Bundled, inside the BamDude container

The simplest: no second container, no networking.

```env
# .env next to docker-compose.yml
DATABASE_URL=embedded
```

The database lives in the existing `bamdude_data` volume under `postgres/`. The shipped compose file already waits 60 seconds on `docker compose down` so the server checkpoints cleanly.

### A separate PostgreSQL container

Use the shipped override `docker-compose.postgres.yml`:

```env
# .env
COMPOSE_FILE=docker-compose.yml:docker-compose.postgres.yml
POSTGRES_PASSWORD=change-me
DATABASE_URL=postgresql+asyncpg://bamdude:change-me@127.0.0.1:5433/bamdude
```

!!! warning "Host networking and the database host"
    The default compose runs BamDude with `network_mode: host` for printer discovery, and a host-network container **cannot** reach another container by its Compose name. So on Linux the override publishes PostgreSQL on `127.0.0.1:5433` and you point `DATABASE_URL` there; on Docker Desktop (macOS/Windows), where host mode is dropped, use the service name `@postgres:5432` instead. `docker-install.sh` writes the correct one for your platform automatically.

---

## :material-swap-horizontal: Migrating from SQLite

Switching to either PostgreSQL (bundled or external) does the migration for you, once.

1. Set `DATABASE_URL` (`embedded` or a URL) and restart BamDude.
2. BamDude sees an **empty** PostgreSQL next to an existing `bamdude.db`.
3. It **transfers all data** from SQLite to PostgreSQL.
4. It renames `bamdude.db` → `bamdude.db.migrated`.

!!! info "No manual steps required"
    All tables, settings, archives, spools, queues and user accounts move across. Type conversion (SQLite `0/1` → boolean, datetime strings → timestamps), auto-increment sequences and the full-text index are all handled.

### What does NOT migrate

- FTS5 virtual tables (replaced by PostgreSQL `tsvector`)
- WAL/SHM files (SQLite-specific)
- The internal migrations bookkeeping (recreated fresh)

!!! tip "Reverting to SQLite"
    Remove `DATABASE_URL` (or set it empty) and restart. Your original data is still in `bamdude.db.migrated` — rename it back to `bamdude.db`.

---

## :material-backup-restore: Backup & Restore

Backups are **always in a portable SQLite format**, whatever backend you run:

- a backup from PostgreSQL restores onto SQLite and vice versa,
- it is a single, inspectable file,
- no dependency on `pg_dump`.

Create and restore from **Settings → Backup**. On backup, BamDude exports every table to a temporary SQLite file and packages it with your archives and other data into a ZIP; on restore it imports that SQLite back into the active backend with type conversion.

For a native PostgreSQL dump of an external server, use `pg_dump` directly — the web UI always produces the portable format.

---

## :material-magnify: Full-Text Search

The search API behaves the same either way; only the engine underneath differs:

| Feature | SQLite | PostgreSQL |
|---------|--------|------------|
| Engine | FTS5 virtual table | `tsvector` + GIN index |
| Query syntax | `MATCH` with wildcards | `to_tsquery` with prefix matching |
| Weights | not weighted | A (name) > B (filename, tags) > C (designer, filament) > D (notes) |

---

## :material-connection: Connection Pool

| Setting | SQLite | PostgreSQL |
|---------|--------|------------|
| Pool size | 20 | 20 |
| Max overflow | 200 | 80 |
| Pre-ping / recycle | — | on / 1800 s |

Large farms can raise these with `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_TIMEOUT`, `DB_POOL_RECYCLE` and `DB_POOL_USE_LIFO`. If you use an external PostgreSQL, make sure its own `max_connections` comfortably exceeds `(pool_size + max_overflow) × workers` — the bundled server is configured with a generous `max_connections` for exactly this.

---

## :material-clock-alert: Slow first-boot migrations

Some migrations are slow whatever the backend, because the bottleneck is opening 3MFs on disk, not database writes. **m022** (0.4.1), for example, reads one config file from inside every existing 3MF; a library of thousands can spend a few minutes there before the API comes up — the same wall-clock cost on PostgreSQL and SQLite. Watch for `m022 … progress` lines if a boot looks stuck.

---

---

## :material-heart-pulse: Checking that it is healthy

**System → Database health** answers «is this database well, and if not, which part» on either backend. Note the page: it is the top-level **System** entry in the sidebar, not a Settings tab.

| What it shows | What to look at |
|---|---|
| Engine, version and **mode** | `SQLite`, the bundled PostgreSQL run by BamDude, the bundled one run as a Windows service, or an external server. Worth checking first — an install that was *meant* to move to PostgreSQL and did not says so here. |
| Size on disk | The real figure on both backends. (The older «Database» card above it stats `bamdude.db`, so it reads 0 on PostgreSQL.) |
| Connection pool | Checked-out against pool size, plus overflow. Persistent overflow means the pool is too small for the farm — raise `DB_POOL_SIZE`. |
| Cache hit ratio (PostgreSQL) | Below ~90% on a warm server means it is reading from disk more than it should; usually `shared_buffers`, or a query reading far more rows than it needs. |
| Deadlocks (PostgreSQL) | Should be 0. Anything else is worth reporting. |
| Journal mode and WAL size (SQLite) | Journal mode must be `wal`. A WAL that keeps growing means checkpoints are not completing. |
| Slowest statements | The statement text, how often it ran, and how long it took in total. |

### Where the slow-statement list comes from

- **PostgreSQL** — from the server's own `pg_stat_statements`. The bundled server enables it for you. ⚠️ If you run the bundled PostgreSQL **as a Windows service**, BamDude does not write that server's configuration, so the extension may be installed while the library was never preloaded; the card then says so rather than showing an empty table.
- **SQLite** — there is no such view, so the list comes from BamDude's own measurements and needs **Slow query log** turned on in Settings → General (see [Finding what is slow](../reference/troubleshooting.md#finding-what-is-slow)). Until it is, the card says so.

A figure BamDude could not read is left out and named at the bottom of the card, so a single unavailable statistic never blanks the rest.

!!! tip "Prometheus"
    The same numbers are exported as `bamdude_db_*` gauges on the metrics endpoint — engine info, size, pool, and per backend either cache hit ratio, connections and deadlocks, or WAL bytes and free pages.

## :material-alert: Good to know

!!! warning "An external database must exist first"
    For an external server, create the database beforehand — BamDude creates only the tables. The bundled server needs none of this; it creates its own.

!!! tip "Keep the connection string out of sight"
    In production, prefer a `.env` file with restricted permissions (or Docker secrets) over a plain environment variable. The bundled server never puts a password in your `.env` at all — it keeps it in `DATA_DIR/postgres/password`.
