---
title: System Info і діагностика
description: Сторінка Settings → System — версія, DB stats, storage breakdown, log viewer, debug-logging toggle, support bundle, optimize-DB, rebuild search index, update checker
---

# System Info і діагностика

Сторінка Settings → System — це адмін-діагностична поверхня BamDude — version metadata, DB row counts, storage breakdown, log viewer, debug-logging toggle, support bundle generator і кнопки maintenance (optimize DB, rebuild search index, check for updates).

## :material-information: Що це

Read-only дашборд, що тягне з `GET /api/v1/system/info` (більшість сторінки), `GET /api/v1/system/storage-usage` (storage breakdown) і `GET /api/v1/support/logs` (log viewer). Maintenance-actions — POST endpoint-и за відповідними permission-ами. Усе живе в running BamDude-процесі — зовнішня metrics-БД не потрібна (для цього див. [Prometheus](prometheus.uk.md)).

## :material-tag-outline: Version info

| Поле | Source |
|---|---|
| `version` | `APP_VERSION` з `backend/app/core/config.py`, ставиться при build-time через `node scripts/set_version.js`. |
| `python_version` | Версія Python interpreter running-процесу. |
| Database engine + version | `SHOW server_version` на PostgreSQL, `SELECT sqlite_version()` на SQLite. |
| `platform` / `architecture` / `hostname` | З Python-модуля `platform`. |
| `boot_time` / `uptime` | System boot time з `psutil`, форматоване в `Nd Nh Nm`. |

Build date і git SHA через цей endpoint не експонуються — release-білди печуть version string при `set_version.js` time, це канонічний ідентифікатор. Node version теж не репортиться; React-bundle шипиться pre-built під `static/`.

## :material-database: Database stats

`GET /api/v1/system/info` агрегує row counts і кілька sum-ів:

| Stat | Що рахує |
|---|---|
| `archives` | Загальна кількість рядків `print_archives`. |
| `archives_completed` / `archives_failed` / `archives_printing` | Те саме, partition за status. |
| `printers` | Усі зареєстровані принтери. |
| `spools` | Усі spool-records (live inventory rows). |
| `projects` | Усі projects. |
| `smart_plugs` | Усі зареєстровані smart-plug-и. |
| `total_print_time_seconds` / `_formatted` | Сума `print_time_seconds` крізь усі архіви. |
| `total_filament_grams` / `_kg` | Сума `filament_used_grams`. |
| `database.size` (під `storage`) | Розмір файлу `bambuddy.db` або PostgreSQL DB size, якщо PG. |

## :material-harddisk: Storage usage breakdown

`GET /api/v1/system/storage-usage` ходить по data-директоріях і класифікує кожен файл в один з buckets, повертаючи size + percentage of total:

| Bucket | Roots |
|---|---|
| `database` | `bambuddy.db` (і legacy `bambutrack.db`, якщо є). |
| `library_thumbnails` / `library_files` / `library_other` | `<archive_dir>/library/...`. |
| `archive_files` / `archive_thumbnails` / `archive_timelapses` | Сама archive-директорія. |
| `virtual_printer_uploads` / `virtual_printer_upload_cache` / `virtual_printer_certs` / `virtual_printer_other` | `<base_dir>/virtual_printer/...`. |
| `downloads` | `<base_dir>/firmware/`. |
| `plate_calibration` | Директорія plate-detection reference image. |
| `logs` | Сконфігурована log-директорія. |
| `other_data` | Все під data-теками, що не зматчилось правилом, з per-bucket sub-breakdown, що відрізняє `system` (deletable=false) від `data` (deletable=true). |

Scan кешується на 5 хвилин (`STORAGE_USAGE_CACHE_SECONDS = 300`). Передай `?refresh=true`, щоб форсити re-scan; передай `max_age_seconds=N` (clamped 0–3600), щоб override-нути cache TTL.

!!! tip "Дивись перед backup-ом"
    Окидаючи поглядом breakdown перед backup, бачиш — чи archive-тека є домінантною часткою (зазвичай так), і чи є headroom тримати timelapse-и, чи прунити їх спочатку.

## :material-memory: Resource usage

| Stat | Source |
|---|---|
| CPU count + percent | `psutil.cpu_count()` / `psutil.cpu_percent(interval=0.1)`. |
| Memory total / available / used / percent | `psutil.virtual_memory()`. |
| Disk total / used / free / percent | `psutil.disk_usage(base_dir)`. |
| `connected_printers` | Live MQTT-connected принтери з `printer_manager`. |

Значення — point-in-time — refresh сторінки re-семплить їх. Historical rollup тут немає. Для time-series скрейпай [Prometheus](prometheus.uk.md).

## :material-text-box-search: Log viewer

`GET /api/v1/support/logs` тейлить `<log_dir>/bamdude.log`, парсить кожен рядок у структурований entry, і повертає найсвіжіші entry-ї першими.

| Param | Замітки |
|---|---|
| `limit` | 1–1000, default 200. |
| `level` | `DEBUG`, `INFO`, `WARNING` або `ERROR`. Case-insensitive. |
| `search` | Substring-match по message body і logger name. Case-insensitive. |

Multi-line entry-ї (особливо stack traces) пересобираються — continuation-рядок прикріплюється до next-parsed entry над ним.

| Дія | Endpoint | Permission |
|---|---|---|
| List recent logs | `GET /api/v1/support/logs` | `settings:read` |
| Truncate log-файл | `DELETE /api/v1/support/logs` | `settings:update` |
| Toggle DEBUG-level logging | `POST /api/v1/support/debug-logging` | `settings:update` |

!!! note "DEBUG-level logging gated"
    Helper `_apply_log_level` пінить `httpcore` і `httpx` на WARNING навіть у DEBUG mode — full request URL logging would leak bearer-токени в Discord / generic-webhook URL-ах. `paho.mqtt` перемикається на DEBUG, коли toggle on — там і живе більшість корисного printer-protocol detail.

## :material-lifebuoy: Support bundle

`GET /api/v1/support/bundle` створює ZIP-файл з:

| Файл | Вміст |
|---|---|
| `support-info.json` | Version, OS info, DB row counts, sanitised printer/integration info, anonymized settings, dependency versions, log-file size, network interfaces з masked subnets, WebSocket connection count, Docker memory limit (якщо containerised). |
| `bamdude.log` | Tail `bamdude.log`, sanitised. |

Bundle вимагає, щоб **debug logging був наразі ввімкнений** — endpoint відмовляється генерувати інакше (`400 Debug logging must be enabled before generating a support bundle`). Workflow:

1. Settings → System → перемкни DEBUG logging on.
2. Відтвори issue.
3. Згенеруй bundle.
4. Перемкни DEBUG logging back off (інакше залишається on — стан персистить у `Settings`-таблиці і re-apply при рестарті).

### Sanitisation

`_sanitize_log_content` і `_collect_support_info` працюють разом, щоб тримати secret-и зовні:

- Printer names → `[PRINTER]`, serial numbers → `[SERIAL]`, IP addresses → `[IP]`, access codes → `[ACCESS_CODE]`, usernames → `[USER]`, email-и → `[EMAIL]`.
- URL credentials (`http://user:pass@host`, `rtsps://bblp:code@host`) → `[CREDENTIALS]@`.
- Path-компоненти типу `/home/<user>/`, `/Users/<user>/`, `/opt/<user>/` колапсуються в `/home/[user]/` тощо.
- MQTT relay broker → masked: bare IP стає `[IP]`, hostname стає `*.tld`.
- Subnets в network info → перші два октети стають `x.x` (тож `192.168.1.0/24` → `x.x.1.0/24`).
- Settings values — ключі, що містять будь-яке з `access_code`, `password`, `token`, `secret`, `api_key`, `cloud_token`, `mqtt_password`, `email`, `username`, `vapid`, `private_key`, `public_key`, `webhook`, `url`, `path`, `config`, `_ip`, `host`, `credential` редактяться у `[REDACTED]` (або `""` якщо порожнє). Будь-які інші settings passthrough as-is, тож feature flags і themes видно в bundle.

Bundle — правильна штука, щоб приклеїти до [GitHub-issue](https://github.com/kainpl/bamdude/issues) при репорті бага.

## :material-tools: Maintenance actions

| Дія | Endpoint | Permission |
|---|---|---|
| **Optimize / vacuum SQLite** — виконує `ANALYZE`, `PRAGMA wal_checkpoint(TRUNCATE)`, потім `VACUUM` | `POST /api/v1/settings/optimize-db` | `settings:backup` |
| **Rebuild archive search index** — див. [Search](search.uk.md) | `POST /api/v1/archives/search/rebuild-index` | `archives:update_all` |
| **Check for updates** — див. [Updates](#material-update-update-checker) нижче | `GET /api/v1/updates/check` | `system:read` |

**Окремої "Clear Cache" кнопки** на BamDude System-сторінці немає — page-level кеші (storage breakdown, system info) автоекспайряться самі; єдиний manual flush — `?refresh=true` query-param на `/system/storage-usage`.

**"Restart application" кнопки** теж немає — upstream Bambuddy-концепт in-app restart має сенс тільки для bare-metal/systemd-інсталів, а target-deployment BamDude — Docker. Рестартуй контейнер через `docker compose restart bamdude` (або що там в твоєму orchestrator-і).

## :material-update: Update checker

`GET /api/v1/updates/check` poll-ить GitHub Releases і порівнює latest-tag до `APP_VERSION`. Поведінка:

| Setting key | Ефект |
|---|---|
| `check_updates` (default `true`) | Коли `false`, endpoint повертає `{update_available: false, message: "Update checks are disabled"}` без походу на GitHub. |
| `include_beta_updates` (default `false`) | Коли `true`, prerelease-и (`X.Y.ZbN`) — eligible matches. Коли `false`, тільки stable-релізи. |

Endpoint surface-ить badge у сайдбарі, коли update available; **auto-install не робить**. Для Docker-інсталів (target deployment) апдейтись через pull нового image:

```bash
docker compose pull bamdude && docker compose up -d bamdude
```

Є також `POST /api/v1/updates/apply` endpoint для in-app оновлень, але цей path призначений для bare-metal / systemd-інсталів і не входить у supported Docker workflow.

Це BamDude self-update path. Для **printer firmware** оновлень див. [Firmware Updates](firmware-updates.md) — повністю окремий flow.

## :material-shield-key: Permission-и

| Дія | Permission |
|---|---|
| Дивитись system info, storage usage, update check | `system:read` |
| Дивитись logs, отримати debug-logging state, генерувати support bundle | `settings:read` |
| Toggle debug logging, clear logs | `settings:update` |
| Optimize/vacuum DB, restore backup | `settings:backup` |
| Rebuild archive search index | `archives:update_all` |

`system:maintenance` чи `support_bundle:create` permission-у немає — support bundle і log endpoint-и сидять під namespace `settings`.

## :material-api: API reference

```
GET    /api/v1/system/info             # full system snapshot
GET    /api/v1/system/storage-usage    # bucketed storage breakdown
GET    /health                         # unauthenticated liveness probe ({"status":"healthy"})
GET    /api/v1/support/logs            # tail bamdude.log
DELETE /api/v1/support/logs            # truncate log-файл
GET    /api/v1/support/debug-logging   # поточний debug-logging state
POST   /api/v1/support/debug-logging   # toggle debug logging
GET    /api/v1/support/bundle          # download support ZIP
POST   /api/v1/settings/optimize-db    # ANALYZE + WAL checkpoint + VACUUM
POST   /api/v1/archives/search/rebuild-index  # rebuild FTS index
GET    /api/v1/updates/version         # current version (unauthenticated)
GET    /api/v1/updates/check           # check GitHub for newer release
```

Unauthenticated `/health` whitelist-нутий setup-gate middleware-ом, тож скрейпай його ще до того, як initial setup completes.
