---
title: Reference налаштувань
description: Кожен ключ під Settings → System / Print / Archive / Inventory / Network / Integrations
---

# Reference налаштувань

Це повний індекс кожного persistent-налаштування, яке експортує BamDude — що робить, дефолт, де в UI. Налаштування живуть у key-value таблиці `settings`; більшість виставлені під **Settings** у бічному меню, але кілька — read-only mirror'и env-змінних (env виграє).

Якщо налаштування немає тут — його не існує. Якщо UI-поле тут не описане — це per-row config (notification provider, smart plug, printer), а не глобальне налаштування.

## :material-cog: System / general

| Key | Default | Ефект |
|---|---|---|
| `language` | `en` | Серверний default-язик для всіх браузерів + Telegram-чатів + email-шаблонів. Frontend читає це на першому завантаженні і синкить i18n; юзери можуть перевизначати per-tab у UI. |
| `time_format` | `24h` | `12h` або `24h`. ETA / timestamps у картках, нотифікаціях, листах. |
| `date_format` | `system` | `system` (browser locale), `us` (`MM/DD/YYYY`), `eu` (`DD/MM/YYYY`), `iso` (`YYYY-MM-DD`). Контролює кожну видиму дату. |
| `external_url` | пусто | Публічний URL BamDude. Виграє над env-змінною `APP_URL`. Використовується в password-reset / MFA email-посиланнях, OIDC callback construction і Obico cached-frame URL. Постав, коли BamDude за reverse proxy. |
| `default_printer_id` | не задано | Default-принтер для нових queue-items / Print Now з file-manager. |
| `check_updates` | `true` | Періодично перевіряти release-feed BamDude на нові версії. |
| `check_printer_firmware` | `true` | Періодично перевіряти firmware-feed Bambu на оновлення принтерів. |
| `include_beta_updates` | `false` | Показувати beta-релізи в update-banner поряд зі stable. |

## :material-archive: Print archive

| Key | Default | Ефект |
|---|---|---|
| `archive_3mf_retention_enabled` | `false` | Увімкнути нічне auto-cleanup `.3mf` файлів, що не друкувались N днів. Метадані + thumbnails лишаються; видаляється тільки `.3mf`. |
| `archive_3mf_retention_days` | `30` | Те N. Мінімум 1. |
| `save_thumbnails` | `true` | Захоплювати кадр першого шару з камери як thumbnail архіву, коли в 3MF свого нема. |
| `capture_finish_photo` | `true` | Робити фото на завершенні і прикріплювати до `print_complete`-нотифікацій. |
| `default_plate` | `0` | Default plate-style для нових queue-items / library-friends. |

## :material-clock-outline: Print queue

| Key | Default | Ефект |
|---|---|---|
| `queue_drying_enabled` | `false` | Дозволити auto-drying між queue-items, коли пластик наступного друку це потребує. |
| `queue_drying_block` | `false` | Блокувати наступний друк до завершення drying (замість паралельно з поточним). |
| `ambient_drying_enabled` | `false` | Дозволити ambient-temperature dry-cycles (vs повноцінні drying schedules). |
| `stagger_enabled` | `false` | Увімкнути [staggered start](../features/staggered-start.uk.md) — обмежити одночасне нагрівання столів на фермі, щоб уникнути просадок мережі. |
| `stagger_concurrent` | `2` | Максимум одночасних друків у stagger-режимі. |
| `stagger_interval_minutes` | `5` | Мінімум хвилин між stagger-стартами. |
| `stagger_wait_for_bed` | `false` | Чекати охолодження столу попереднього друку перед стартом наступного. |
| `stagger_strict_for_direct_dispatch` | `false` | Застосовувати stagger також на Print Now / direct-dispatch (інакше stagger керує тільки queued items). |

## :material-package-variant: Inventory & filament

| Key | Default | Ефект |
|---|---|---|
| `low_stock_threshold` | `10` | % залишку котушки, при якому стріляє `filament_low`. |
| `disable_filament_warnings` | `false` | Master mute для low / out-of-filament алертів. |
| `prefer_lowest_filament` | `false` | Auto-присвоєння віддає перевагу котушці з найменшим залишком. |
| `default_filament_cost` | `25` | Per-kg fallback-ціна, коли поле `cost` котушки не задано. |
| `ams_humidity_good` | `30` | Зелена-зона humidity-поріг (%) на AMS-картках. |
| `ams_humidity_fair` | `45` | Жовта-зона. Вище — червоне. |
| `ams_temperature_good` | `30` | Зелена-зона temp-поріг (°C). |
| `ams_temperature_fair` | `40` | Жовта-зона. |
| `ams_history_retention_days` | `90` | Скільки днів історії AMS тримати до prune. |
| `spoolman_enabled` | `false` | Увімкнути [Spoolman two-way sync](../features/spoolman.uk.md). |
| `spoolman_disable_weight_sync` | `false` | Не пушити BamDude-tracked usage назад у Spoolman. |
| `spoolman_report_partial_usage` | `false` | Пушити часткову витрату (mid-print snapshots) у Spoolman, не тільки на завершенні. |

## :material-bolt: Energy & cost

| Key | Default | Ефект |
|---|---|---|
| `energy_cost_per_kwh` | `0.0` | Ціна за kWh для розрахунків ціни архіву / проєкту. Постав свою локальну. |
| `library_disk_warning_gb` | `5` | Поріг вільного місця на library-диску, нижче якого в UI з'являється banner-warning. |

## :material-network: Мережа / зв'язок

| Key | Default | Ефект |
|---|---|---|
| `mqtt_enabled` | `false` | Увімкнути [MQTT publishing](../features/mqtt.uk.md) — републікувати стан принтерів у зовнішній MQTT-брокер. |
| `mqtt_broker` | пусто | Hostname брокера. |
| `mqtt_port` | `1883` | Порт брокера. |
| `mqtt_username` / `mqtt_password` | пусто | Auth брокера. Пароль шифрується at-rest. |
| `mqtt_use_tls` | `false` | TLS для з'єднання з MQTT-брокером. |
| `mqtt_topic_prefix` | `home/bambu/` | Prefix для републікованих топіків. |
| `prometheus_enabled` | `false` | Увімкнути [`/metrics` endpoint](../features/prometheus.uk.md). |
| `ftp_retry_enabled` | `true` | Перевикачувати FTP 3MF, коли принтер був недосяжний на старті. Див. [Print Archive](../features/archiving.uk.md). |
| `ftp_retry_count` | `3` | Максимум retry на цикл. |
| `ftp_retry_delay` | `60` | Секунди між retry. |
| `ftp_timeout` | `120` | FTP download timeout у секундах. |

## :material-printer-3d: Віртуальний принтер

| Key | Default | Ефект |
|---|---|---|
| `virtual_printer_enabled` | `false` | Master-toggle для [фічі віртуального принтера](../features/virtual-printer.uk.md). Per-VP рядки живуть у таблиці `virtual_printers`. |

## :material-puzzle: Інтеграції

| Key | Default | Ефект |
|---|---|---|
| `ha_enabled` | `false` | Увімкнути інтеграцію Home Assistant. |
| `ha_url` / `ha_token` | пусто | URL HA-інстансу + long-lived token. Шифрується at-rest. Env-змінні `HA_URL` / `HA_TOKEN` перебивають їх і блокують read-only в UI, коли задані обидві. |
| `ldap_enabled` | `false` | Увімкнути LDAP-автентифікацію. Див. [Автентифікація](../features/authentication.uk.md). |
| `ldap_auto_provision` | `false` | Авто-створювати користувачів на першому успішному LDAP bind. |
| `ldap_server_uri` | пусто | Адреса LDAP-сервера (наприклад `ldap://ldap.example.com:389`). |
| `ldap_bind_dn` | пусто | Bind DN-шаблон (з `{username}` placeholder). |
| `ldap_bind_password` | пусто | Шифрований bind-пароль. |
| `ldap_search_base` | пусто | Search base DN. |
| `ldap_search_filter` | пусто | User-search filter (наприклад `(uid={username})`). |

## :material-robot-confused: Obico AI

Контекст на кожне — на сторінці [AI-детекція фейлів Obico](../features/obico.uk.md).

| Key | Default | Ефект |
|---|---|---|
| `obico_enabled` | `false` | Master-toggle. |
| `obico_ml_url` | пусто | URL ML API. |
| `obico_sensitivity` | `medium` | `low` / `medium` / `high`. |
| `obico_action` | `notify` | `notify` / `pause` / `pause_and_off`. |
| `obico_poll_interval` | `30` | Секунди між snapshot-ами (5–120). |
| `obico_enabled_printers` | `null` | Опційний JSON-масив printer-ID, на яких детекція активна. `null` = всі. |

## :material-bell: Per-user нотифікації

| Key | Default | Ефект |
|---|---|---|
| `user_notifications_enabled` | `false` | Увімкнути per-user email-нотифікації для друків, які користувач власник. |

## :material-account-key: Auth (переважно env-driven)

Ці не редагуються з UI — read-only mirror'и env-змінних. Деталі env — на [сторінці інсталяції](../getting-started/installation.uk.md).

| Setting | Source | Ефект |
|---|---|---|
| Setup gate active | таблиця `users` | Опускається автоматом, коли створений перший адмін. CLI `reset_admin` чистить його для recovery. |
| JWT signing key | env `JWT_SECRET_KEY` або файл `data/.jwt_secret` | Auto-generated на першому boot, якщо нічого з цього нема. |
| Refresh-cookie `Secure` flag | env `AUTH_REFRESH_COOKIE_SECURE` | Auto-detect зі схеми запиту, коли не задано. |
| Trusted reverse-proxy IPs | env `TRUSTED_PROXY_IPS` | Comma-separated. Потрібно для коректного per-IP rate-limit за nginx / Caddy. |
| MFA-secret encryption key | env `MFA_ENCRYPTION_KEY` | Plaintext fallback працює без нього, але логує warning. |
