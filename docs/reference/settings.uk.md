---
title: Reference налаштувань
description: Кожен ключ під Settings → System / Print / Archive / Inventory / Network / Integrations
---

# Reference налаштувань

Це повний індекс кожного persistent-налаштування, яке експортує BamDude — що робить, дефолт, де в UI. Налаштування живуть у key-value таблиці `settings`; більшість виставлені під **Settings** у бічному меню, але кілька — read-only mirror'и env-змінних (env виграє).

Джерело істини — `backend/app/schemas/settings.py::AppSettings`. Якщо налаштування немає тут, перевіряйте там, перш ніж вважати, що його не існує — дефолти нижче звірені з кодом.

## :material-cog: System / general

| Key | Default | Ефект |
|---|---|---|
| `language` | `en` | Серверний default-язик для всіх браузерів + Telegram-чатів + email-шаблонів. Frontend читає це на першому завантаженні і синкить i18n; юзери можуть перевизначати per-tab у UI. |
| `time_format` | `system` | `system` (browser locale), `12h` або `24h`. ETA / timestamps у картках, нотифікаціях, листах. |
| `date_format` | `system` | `system` (browser locale), `us` (`MM/DD/YYYY`), `eu` (`DD/MM/YYYY`), `iso` (`YYYY-MM-DD`). Контролює кожну видиму дату. |
| `currency` | `USD` | Код валюти для відображення вартості. |
| `external_url` | пусто | Публічний URL BamDude. Виграє над env-змінною `APP_URL`. Використовується в password-reset / MFA email-посиланнях, OIDC callback construction і Obico cached-frame URL. Постав, коли BamDude за reverse proxy. |
| `default_printer_id` | не задано | Default-принтер для нових queue-items / Print Now з file-manager. |
| `default_sidebar_order` | пусто | Admin-задано дефолтне впорядкування sidebar — JSON `{"order": [...ids]}` або JSON-масив. Пусто = вбудоване впорядкування. |
| `check_updates` | `true` | Періодично перевіряти release-feed BamDude на нові версії. |
| `check_printer_firmware` | `true` | Періодично перевіряти firmware-feed Bambu на оновлення принтерів. |
| `include_beta_updates` | `false` | Показувати beta-релізи в update-banner поряд зі stable. |

## :material-palette: Тема

| Key | Default | Ефект |
|---|---|---|
| `dark_style` | `classic` | `classic`, `glow` або `vibrant`. |
| `dark_background` | `neutral` | `neutral`, `warm`, `cool`, `oled`, `slate` або `forest`. |
| `dark_accent` | `green` | `green`, `teal`, `blue`, `orange`, `purple` або `red`. |
| `light_style` | `classic` | `classic`, `glow` або `vibrant`. |
| `light_background` | `neutral` | `neutral`, `warm` або `cool`. |
| `light_accent` | `green` | Ті ж опції, що в `dark_accent`. |

## :material-archive: Print archive

| Key | Default | Ефект |
|---|---|---|
| `archive_3mf_retention_enabled` | `false` | Увімкнути нічне auto-cleanup `.3mf` файлів, що не друкувались N днів. Метадані + thumbnails лишаються; видаляється тільки `.3mf`. |
| `archive_3mf_retention_days` | `30` | Те N. Мінімум 1. |
| `save_thumbnails` | `true` | Витягати preview-картинки з 3MF для карток архіву. |
| `capture_finish_photo` | `true` | Робити фото на завершенні друку з камери і прикріплювати до `print_complete`-нотифікацій. |
| `library_disk_warning_gb` | `5.0` | Показувати banner-warning, коли вільне місце на data-партиції менше за цей поріг. |

## :material-clock-outline: Print queue & dispatch

| Key | Default | Ефект |
|---|---|---|
| `queue_drying_enabled` | `false` | Дозволити auto-drying між queue-items, коли пластик наступного друку це потребує. |
| `queue_drying_block` | `false` | Блокувати наступний друк до завершення drying (замість паралельно з поточним). |
| `ambient_drying_enabled` | `false` | Auto-сушити AMS-філамент на idle-принтерах, коли humidity вище порогу — незалежно від стану черги. |
| `drying_presets` | пусто | JSON-об'єкт пресетів сушіння per-філамент. Пусто = вбудовані дефолти. |
| `stagger_enabled` | `false` | Увімкнути [staggered start](../features/staggered-start.uk.md) — обмежити одночасне нагрівання столів на фермі, щоб уникнути просадок мережі. |
| `stagger_concurrent` | `2` | Максимум одночасних принтерів, що нагріваються. |
| `stagger_interval_minutes` | `5` | Хвилини очікування після того, як слот звільниться, до старту наступного. |
| `stagger_wait_for_bed` | `true` | Слот звільняється, коли стіл досяг target-temp ±1 °C. Якщо вимкнено, слот звільняється одразу після старту друку. |
| `per_printer_mapping_expanded` | `false` | Розгортати секцію custom filament mapping у print-modal за замовчуванням. |

## :material-printer-3d: Віртуальний принтер

| Key | Default | Ефект |
|---|---|---|
| `virtual_printer_enabled` | `false` | Master-toggle для [фічі віртуального принтера](../features/virtual-printer.uk.md). Per-VP рядки живуть у таблиці `virtual_printers`. |
| `virtual_printer_access_code` | пусто | 8-символьний код, яким мають автентифікуватися слайсери до будь-якого VP. Per-VP override живе на рядку `virtual_printers`. |
| `virtual_printer_mode` | `file_manager` | Default-режим для нових VP-рядків: `file_manager`, `print_queue` або `proxy`. Див. [Режими VP](../features/virtual-printer.uk.md#modes). |
| `preferred_slicer` | `bambu_studio` | `bambu_studio` або `orcaslicer`. Який слайсер пропонувати у workflows, що лінкають назовні. |

## :material-package-variant: Inventory & filament

| Key | Default | Ефект |
|---|---|---|
| `low_stock_threshold` | `20.0` | % залишку котушки, при якому стріляє `filament_low`. Діапазон 0.1 – 99.9. |
| `disable_filament_warnings` | `false` | Master mute для low / out-of-filament алертів. |
| `prefer_lowest_filament` | `false` | Auto-присвоєння віддає перевагу котушці з найменшим залишком. |
| `default_filament_cost` | `25.0` | Per-kg fallback-ціна, коли поле `cost` котушки не задано. |
| `ams_humidity_good` | `40` | Зелена-зона humidity-поріг (%) на AMS-картках (≤ це значення). |
| `ams_humidity_fair` | `60` | Жовта-зона humidity (≤ це значення). Вище — червоне. |
| `ams_temp_good` | `28.0` | Зелена-зона temp-поріг (°C) на AMS-картках. |
| `ams_temp_fair` | `35.0` | Жовта-зона temp. Вище — червоне. |
| `ams_history_retention_days` | `30` | Скільки днів історії AMS тримати до prune. |
| `bed_cooled_threshold` | `35.0` | Температура столу (°C), при якій стріляє нотифікація `bed_cooled`. |

## :material-bolt: Energy & cost

| Key | Default | Ефект |
|---|---|---|
| `energy_cost_per_kwh` | `0.15` | Ціна за kWh для розрахунків ціни архіву / проєкту. Постав свою локальну. |
| `energy_tracking_mode` | `total` | `total` показує lifetime-споживання розетки на стат-сторінці; `print` показує суму per-print-дельт. Див. [Smart plugs → Energy display mode](../features/smart-plugs.uk.md#energy-display-mode). |

## :material-spool-of-thread: Spoolman

| Key | Default | Ефект |
|---|---|---|
| `spoolman_enabled` | `false` | Увімкнути [Spoolman two-way sync](../features/spoolman.uk.md). |
| `spoolman_url` | пусто | URL Spoolman-сервера (наприклад `http://localhost:7912`). |
| `spoolman_sync_mode` | `auto` | `auto` синкає одразу на кожну зміну; `manual` чекає кнопки. |
| `spoolman_disable_weight_sync` | `false` | Не пушити BamDude-tracked usage назад у Spoolman — оновлювати лише локацію. |
| `spoolman_report_partial_usage` | `true` | Звітувати оцінену витрату на failed / cancelled друках за progress-у шарів. |
| `spool_display_template` | `{brand} {material} {color_name}` | Шаблон синтезованого display-name котушки. Placeholder-и: `{brand}`, `{material}`, `{subtype}`, `{color_name}`, `{color_hex}`, `{slicer_filament_name}`, `{note}`, `{label_weight_g}`, `{label_weight_kg}`, `{remaining_g}`, `{remaining_kg}`, `{remaining_pct}`, `{cost_per_kg}`. Невідомі placeholder-и лишаються як є — щоб одруки виплили. |

## :material-network: Мережа / зв'язок

| Key | Default | Ефект |
|---|---|---|
| `mqtt_enabled` | `false` | Увімкнути [MQTT publishing](../features/mqtt.uk.md) — републікувати стан принтерів у зовнішній MQTT-брокер. |
| `mqtt_broker` | пусто | Hostname або IP брокера. |
| `mqtt_port` | `1883` | Порт брокера. TLS-деплої зазвичай використовують `8883`. |
| `mqtt_username` / `mqtt_password` | пусто | Auth брокера. Пароль шифрується at-rest. |
| `mqtt_use_tls` | `false` | TLS для з'єднання з MQTT-брокером. |
| `mqtt_topic_prefix` | `bambuddy` | Prefix для всіх республікованих топіків. Успадковано з апстрім Bambuddy — змініть на `bamdude` на свіжих інсталяціях, якщо так зручніше. |
| `ftp_retry_enabled` | `true` | Перевикачувати FTP 3MF, коли принтер був недосяжний на старті. Див. [Print Archive](../features/archiving.uk.md). |
| `ftp_retry_count` | `3` | Максимум retry на цикл (1–10). |
| `ftp_retry_delay` | `2` | Секунди між retry (1–30). |
| `ftp_timeout` | `30` | FTP-таймаут підключення в секундах (10–300). |

## :material-camera: Камера

| Key | Default | Ефект |
|---|---|---|
| `camera_view_mode` | `window` | `window` відкриває камери в новому вікні браузера; `embedded` показує overlay на дашборді. |

## :material-bell: Telegram & нотифікації

| Key | Default | Ефект |
|---|---|---|
| `telegram_registration_open` | `false` | Коли `true`, невідомі Telegram-чати авто-реєструються з `is_active=False, group_id=NULL` (pending admin activation). Коли `false`, невідомі чати відхиляються одразу. Окремого "approval"-режиму немає — auto-register-then-activate flow робить саме `true`. |
| `user_notifications_enabled` | `true` | Увімкнути per-user email-нотифікації для друків, які користувач власник (потрібен Advanced Authentication). |

## :material-puzzle: Інтеграції

### Home Assistant

| Key | Default | Ефект |
|---|---|---|
| `ha_enabled` | `false` | Увімкнути інтеграцію Home Assistant. |
| `ha_url` / `ha_token` | пусто | URL HA-інстансу + long-lived token. Шифрується at-rest. Env-змінні `HA_URL` / `HA_TOKEN` перебивають їх і блокують read-only в UI, коли задані обидві. |

### LDAP

| Key | Default | Ефект |
|---|---|---|
| `ldap_enabled` | `false` | Увімкнути LDAP-автентифікацію. Див. [Автентифікація](../features/authentication.uk.md). |
| `ldap_server_url` | пусто | URL LDAP-сервера (наприклад `ldap://ldap.example.com:389`). |
| `ldap_security` | `starttls` | `starttls` або `ldaps`. |
| `ldap_bind_dn` | пусто | Bind DN для пошуку (наприклад `cn=admin,dc=example,dc=com`). |
| `ldap_bind_password` | пусто | Шифрований bind-пароль. |
| `ldap_search_base` | пусто | Search base DN (наприклад `ou=users,dc=example,dc=com`). |
| `ldap_user_filter` | `(sAMAccountName={username})` | LDAP user-search filter. `{username}` замінюється логіном. Дефолт — Active Directory; для OpenLDAP перемкніть на `(uid={username})`. |
| `ldap_group_mapping` | пусто | JSON-об'єкт мапінгу LDAP-груп на BamDude-групи. Пусто = без group sync. |
| `ldap_auto_provision` | `false` | Auto-створювати BamDude-користувача на першому успішному LDAP bind. |
| `ldap_default_group` | пусто | Fallback BamDude-група, коли LDAP-користувач не має жодної мапнутої групи. Пусто = без fallback (логін падає). |

### Prometheus

| Key | Default | Ефект |
|---|---|---|
| `prometheus_enabled` | `false` | Увімкнути [`/metrics` endpoint](../features/prometheus.uk.md). |
| `prometheus_token` | пусто | Bearer-token, потрібний на metrics-endpoint. Пусто = без auth (для local-only деплоїв). |

## :material-robot-confused: Obico AI

Контекст на кожне — на сторінці [AI-детекція фейлів Obico](../features/obico.uk.md).

| Key | Default | Ефект |
|---|---|---|
| `obico_enabled` | `false` | Master-toggle. |
| `obico_ml_url` | пусто | URL ML API (наприклад `http://192.168.1.10:3333`). |
| `obico_sensitivity` | `medium` | `low`, `medium` або `high`. |
| `obico_action` | `notify` | `notify`, `pause` або `pause_and_off`. |
| `obico_poll_interval` | `10` | Секунди між detection-перевірками під час друку. Діапазон 5 – 120. |
| `obico_enabled_printers` | пусто | JSON-масив printer-ID, на яких детекція активна. Пусто = всі підключені принтери. |

## :material-content-save: Локальні бекапи

| Key | Default | Ефект |
|---|---|---|
| `local_backup_enabled` | `false` | Увімкнути scheduled local backup-и. |
| `local_backup_schedule` | `daily` | `hourly`, `daily` або `weekly`. |
| `local_backup_time` | `03:00` | Час доби для daily / weekly бекапів (HH:MM, 24-годинний). |
| `local_backup_retention` | `5` | Скільки backup-файлів тримати (1–100). |
| `local_backup_path` | пусто | Каталог для виходу бекапів. Пусто = `DATA_DIR/backups`. |

## :material-account-key: Auth (переважно env-driven)

Ці не редагуються з UI — read-only mirror'и env-змінних. Деталі env — на [сторінці інсталяції](../getting-started/installation.uk.md).

| Setting | Source | Ефект |
|---|---|---|
| Setup gate active | таблиця `users` | Опускається автоматом, коли створений перший адмін. CLI `reset_admin` чистить його для recovery. |
| JWT signing key | env `JWT_SECRET_KEY` або файл `data/.jwt_secret` | Auto-generated на першому boot, якщо нічого з цього нема. |
| Refresh-cookie `Secure` flag | env `AUTH_REFRESH_COOKIE_SECURE` | Auto-detect зі схеми запиту, коли не задано. |
| Trusted reverse-proxy IPs | env `TRUSTED_PROXY_IPS` | Comma-separated. Потрібно для коректного per-IP rate-limit за nginx / Caddy. |
| MFA-secret encryption key | env `MFA_ENCRYPTION_KEY` | Plaintext fallback працює без нього, але логує warning. |
