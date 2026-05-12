---
title: System Info і діагностика
description: Сторінка Інформація — версія, DB stats, storage breakdown, log viewer, debug-logging toggle, support bundle, optimize-DB, rebuild search index, update checker
---

# System Info і діагностика

Сторінка **Інформація** (бокова панель → Інформація, route `/system`) — це адмін-діагностична поверхня BamDude — version metadata, DB row counts, storage breakdown, log viewer, debug-logging toggle, support bundle generator і кнопки maintenance (optimize DB, rebuild search index, check for updates).

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

### Ротація + retention логів

Активний файл логу (`bamdude.log`) ротується опівночі (за локальним часом) — учорашні логи пакуються в `bamdude.log.YYYY-MM-DD.gz` і зберігаються згідно з `log_retention_days` (за замовчуванням **30**). При старті BamDude сканує `<log_dir>/bamdude.log.*.gz` і видаляє все, старше за retention-налаштування.

Сторінка system-info показує панель **Архіви логів** зі списком усіх gzip-архівів на диску — для кожного: дата, розмір, **Завантажити** (стримить `.gz`), і **Видалити** (двостадійно: перший клік ставить деструктивну кнопку «озброєною», другий — таки видаляє). У парі з кнопкою **Обрізати** на активному файлі логу панель дає повний контроль за днями без заходу в контейнер.

`log_retention_days` живе в **Налаштування → Система** (діапазон 1–365) — оператори з `settings:update` можуть змінювати в інтерфейсі. Налаштування також застосовується на наступну ротацію опівночі, тож зменшення з 30 до 7 звільняє диск на наступному добовому тіку.

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
| **Check for updates** — див. [Updates](#update-checker) нижче | `GET /api/v1/updates/check` | `system:read` |

**Окремої "Clear Cache" кнопки** на BamDude System-сторінці немає — page-level кеші (storage breakdown, system info) автоекспайряться самі; єдиний manual flush — `?refresh=true` query-param на `/system/storage-usage`.

**"Restart application" кнопки** теж немає — upstream Bambuddy-концепт in-app restart має сенс тільки для bare-metal/systemd-інсталів, а target-deployment BamDude — Docker. Рестартуй контейнер через `docker compose restart bamdude` (або що там в твоєму orchestrator-і).

## :material-update: Update checker

`GET /api/v1/updates/check` poll-ить GitHub Releases і порівнює latest-tag до `APP_VERSION`. Два setting keys кермують поведінкою:

| Setting key | Ефект |
|---|---|
| `check_updates` (default `true`) | Коли `false`, endpoint повертає `{update_available: false, message: "Update checks are disabled"}` без походу на GitHub. |
| `include_beta_updates` (default `false`) | Коли `true`, prerelease-и (`X.Y.ZbN`) — eligible matches. Коли `false`, тільки stable-релізи. Detection — dual-signal: реліз вважається prerelease якщо тег матчить `bN`/`betaN`/`alphaN`/`rcN` **АБО** якщо marked-prerelease у GitHub UI. |

Check-response несе `is_prerelease`, `is_docker`, `latest_version` — UI рендерить правильні install-команди per-channel + per-install-shape.

### In-app apply (native-інстали)

`POST /api/v1/updates/apply` робить фактичний git checkout + dependency install. Поведінка з **0.4.4**:

- Приймає опційний `tag_name` body field — frontend передає те, що тільки що отримав з `/check`, щоб apply ударив exact-реліз який юзер бачив.
- Резолвить у `vX.Y.Z[bN]` git-ref через `_resolve_git_ref()` (працює і з `v`-prefixed і з bare формами).
- Виконує `git fetch origin --tags --prune --force` потім `git reset --hard refs/tags/<ref>`. Працює для **будь-якого tag незалежно від гілки** — pre-fix хардкодив `git reset --hard origin/main`, що тихо no-op'ило бета-інстали (бо бета-теги на `dev`, не `main`).
- Встановлює Python-deps (`pip install -r requirements.txt`) і ребілдить frontend-бандл (`npm install && npm run build`) коли npm доступний.

Endpoint потребує `settings:update`. Запуск з **Settings → System → Install Update** коли update показано як available.

### Docker-інстали

Docker-інсталам `/apply` відмовляє з `is_docker: True` — запуск `git fetch` / `pip install` / `npm build` всередині запущеного контейнера зіпсує image. Замість того UI surface-ить дві бокові секції з конкретними командами що використовують resolved `latest_version` + `is_prerelease`:

**Image-based (типове)** — більшість операторів запускає `image: kainpl/bamdude:<tag>` у compose-файлі:

```yaml
# docker-compose.yml
image: kainpl/bamdude:0.4.5b1     # для бет — явний пін обов'язковий
# АБО
image: kainpl/bamdude:latest      # для stable (latest трекає тільки main)
```

```bash
docker compose pull && docker compose up -d
```

Hint-текст у UI явно пояснює чому `:latest` не підтягне бету — `:latest` Docker tag трекає `main`, бети тегаються на `dev` і шипляться як `:X.Y.ZbN` без `:latest`-промоушна.

**Source-build** — для операторів які склонували репо і використовують `build:` у compose:

```bash
git fetch origin --tags --prune --force
git checkout v0.4.5b1
docker compose build --pull
docker compose up -d
```

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
