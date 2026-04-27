---
title: Settings reference
description: Every key under Settings → System / Print / Archive / Inventory / Network / Integrations
---

# Settings reference

This is the comprehensive index of every persistent setting BamDude exposes — what each one does, its default, and where it shows up in the UI. Settings live in the `settings` key-value table; most are surfaced under **Settings** in the side nav, but a few are read-only mirrors of env vars (the env value wins).

The source of truth is `backend/app/schemas/settings.py::AppSettings`. If a setting isn't on this page, check there before assuming it doesn't exist — defaults below were verified against that schema.

## :material-cog: System / general

| Key | Default | Effect |
|---|---|---|
| `language` | `en` | Server-side default language for all browsers + Telegram chat content + email templates. Frontend reads this on first load and syncs i18n; users can override per-tab in the UI. |
| `time_format` | `system` | `system` (browser locale), `12h`, or `24h`. ETA / timestamp display in cards, notifications, and emails. |
| `date_format` | `system` | `system` (browser locale), `us` (`MM/DD/YYYY`), `eu` (`DD/MM/YYYY`), `iso` (`YYYY-MM-DD`). Controls every user-visible date. |
| `currency` | `USD` | Currency code for cost tracking display. |
| `external_url` | empty | Public-facing URL of BamDude. Wins over the `APP_URL` env var. Used in password-reset / MFA email links, OIDC callback construction, and the Obico cached-frame URL. Set this when you front BamDude with a reverse proxy. |
| `default_printer_id` | unset | Default printer for new queue items / Print Now from the file manager. |
| `default_sidebar_order` | empty | Admin-set default sidebar item order — JSON `{"order": [...ids]}` or a JSON array. Empty = use built-in order. |
| `check_updates` | `true` | Periodically check the BamDude release feed for new versions. |
| `check_printer_firmware` | `true` | Periodically check Bambu's firmware feed for printer updates. |
| `include_beta_updates` | `false` | Surface beta releases in the update banner alongside stable releases. |

## :material-palette: Theme

| Key | Default | Effect |
|---|---|---|
| `dark_style` | `classic` | `classic`, `glow`, or `vibrant`. |
| `dark_background` | `neutral` | `neutral`, `warm`, `cool`, `oled`, `slate`, or `forest`. |
| `dark_accent` | `green` | `green`, `teal`, `blue`, `orange`, `purple`, or `red`. |
| `light_style` | `classic` | `classic`, `glow`, or `vibrant`. |
| `light_background` | `neutral` | `neutral`, `warm`, or `cool`. |
| `light_accent` | `green` | Same options as `dark_accent`. |

## :material-archive: Print archive

| Key | Default | Effect |
|---|---|---|
| `archive_3mf_retention_enabled` | `false` | Enable nightly auto-cleanup of `.3mf` files that haven't printed in N days. Metadata + thumbnails stay; only the `.3mf` is dropped. |
| `archive_3mf_retention_days` | `30` | The N. Minimum 1. |
| `save_thumbnails` | `true` | Extract preview images from 3MF files for archive cards. |
| `capture_finish_photo` | `true` | Capture a completion photo from the printer camera and attach it to `print_complete` notifications. |
| `library_disk_warning_gb` | `5.0` | Show a banner warning when the data partition has less than this much free space. |

## :material-clock-outline: Print queue & dispatch

| Key | Default | Effect |
|---|---|---|
| `queue_drying_enabled` | `false` | Allow auto-drying between queue items when the next print's filament needs it. |
| `queue_drying_block` | `false` | Block the next print until drying completes (rather than running it in parallel with the current print). |
| `ambient_drying_enabled` | `false` | Auto-dry AMS filament on idle printers when humidity exceeds threshold, regardless of queue state. |
| `drying_presets` | empty | JSON object of per-filament drying presets. Empty = use built-in defaults. |
| `stagger_enabled` | `false` | Enable [staggered start](../features/staggered-start.md) — limit concurrent bed heats across the farm to avoid power spikes. |
| `stagger_concurrent` | `2` | Maximum concurrent printers heating. |
| `stagger_interval_minutes` | `5` | Wait time after a slot frees before the next start. |
| `stagger_wait_for_bed` | `true` | Slot frees when the bed reaches target temp (±1 °C). When off, the slot frees immediately after print start. |
| `per_printer_mapping_expanded` | `false` | Expand the custom filament mapping section by default in the print modal. |

## :material-printer-3d: Virtual printer

| Key | Default | Effect |
|---|---|---|
| `virtual_printer_enabled` | `false` | Master toggle for the [virtual printer feature](../features/virtual-printer.md). Per-VP rows live in the `virtual_printers` table. |
| `virtual_printer_access_code` | empty | 8-character access code that slicers must use to authenticate against any virtual printer. Per-VP overrides live on the `virtual_printers` row. |
| `virtual_printer_mode` | `file_manager` | Default mode for new VP rows: `file_manager`, `print_queue`, or `proxy`. See [Virtual printer modes](../features/virtual-printer.md#modes). |
| `preferred_slicer` | `bambu_studio` | `bambu_studio` or `orcaslicer`. Which slicer to suggest in workflows that link out. |

## :material-package-variant: Inventory & filament

| Key | Default | Effect |
|---|---|---|
| `low_stock_threshold` | `20.0` | Spool remaining percentage at which `filament_low` notifications fire. Range 0.1 – 99.9. |
| `disable_filament_warnings` | `false` | Master mute for low / out-of-filament alerts. |
| `prefer_lowest_filament` | `false` | Auto-assignment prefers the spool with the lowest remaining percentage. |
| `default_filament_cost` | `25.0` | Per-kg fallback cost when a spool's `cost` field is unset. |
| `ams_humidity_good` | `40` | Green-zone humidity threshold (%) on AMS cards (≤ this value). |
| `ams_humidity_fair` | `60` | Yellow-zone humidity threshold (≤ this value). Above is red. |
| `ams_temp_good` | `28.0` | Green-zone temperature threshold (°C) on AMS cards. |
| `ams_temp_fair` | `35.0` | Yellow-zone temperature threshold. Above is red. |
| `ams_history_retention_days` | `30` | How many days of AMS history to keep before pruning. |
| `bed_cooled_threshold` | `35.0` | Bed temperature (°C) at which the `bed_cooled` notification fires. |

## :material-bolt: Energy & cost

| Key | Default | Effect |
|---|---|---|
| `energy_cost_per_kwh` | `0.15` | Cost per kWh for archive / project cost calculations. Set to your local rate. |
| `energy_tracking_mode` | `total` | `total` shows lifetime plug consumption on stats; `print` shows the sum of per-print energy deltas. See [Smart plugs → Energy display mode](../features/smart-plugs.md#energy-display-mode). |

## :lucide-spool: Spoolman

| Key | Default | Effect |
|---|---|---|
| `spoolman_enabled` | `false` | Enable [Spoolman two-way sync](../features/spoolman.md). |
| `spoolman_url` | empty | Spoolman server URL (e.g. `http://localhost:7912`). |
| `spoolman_sync_mode` | `auto` | `auto` syncs immediately on changes; `manual` requires explicit button press. |
| `spoolman_disable_weight_sync` | `false` | Don't push BamDude-tracked usage back to Spoolman — only update location. |
| `spoolman_report_partial_usage` | `true` | Report estimated usage on failed / cancelled prints based on layer progress. |
| `spool_display_template` | `{brand} {material} {color_name}` | Template for the synthesised spool display name. Placeholders: `{brand}`, `{material}`, `{subtype}`, `{color_name}`, `{color_hex}`, `{slicer_filament_name}`, `{note}`, `{label_weight_g}`, `{label_weight_kg}`, `{remaining_g}`, `{remaining_kg}`, `{remaining_pct}`, `{cost_per_kg}`. Unknown placeholders are kept verbatim so typos surface. |

## :material-network: Network / connectivity

| Key | Default | Effect |
|---|---|---|
| `mqtt_enabled` | `false` | Enable [MQTT publishing](../features/mqtt.md) — republish printer state to an external MQTT broker. |
| `mqtt_broker` | empty | Broker hostname or IP. |
| `mqtt_port` | `1883` | Broker port. TLS deployments typically use `8883`. |
| `mqtt_username` / `mqtt_password` | empty | Broker auth. Password is encrypted at rest. |
| `mqtt_use_tls` | `false` | Use TLS for the MQTT broker connection. |
| `mqtt_topic_prefix` | `bambuddy` | Prefix for all republished topics. Inherited from upstream Bambuddy — change to `bamdude` on fresh installs if you prefer. |
| `ftp_retry_enabled` | `true` | Retry FTP 3MF downloads when the printer was unreachable at print start. See [Print Archive](../features/archiving.md). |
| `ftp_retry_count` | `3` | Maximum retries per attempt cycle (1–10). |
| `ftp_retry_delay` | `2` | Seconds between retries (1–30). |
| `ftp_timeout` | `30` | FTP connection timeout in seconds (10–300). |

## :material-camera: Camera

| Key | Default | Effect |
|---|---|---|
| `camera_view_mode` | `window` | `window` opens cameras in a new browser window; `embedded` shows them as an overlay on the dashboard. |

## :material-bell: Telegram & notifications

| Key | Default | Effect |
|---|---|---|
| `telegram_registration_open` | `false` | When `true`, unknown Telegram chats are auto-registered as inactive (pending admin activation). When `false`, unknown chats are rejected outright. There is no separate "approval" mode — the auto-register-then-activate flow is what `true` does. |
| `user_notifications_enabled` | `true` | Enable per-user email notifications for prints the user owns (requires Advanced Authentication). |

## :material-puzzle: Integrations

### Home Assistant

| Key | Default | Effect |
|---|---|---|
| `ha_enabled` | `false` | Enable the Home Assistant integration. |
| `ha_url` / `ha_token` | empty | HA instance URL + long-lived token. Encrypted at rest. Env vars `HA_URL` / `HA_TOKEN` override these and lock them read-only in the UI when both are set. |

### LDAP

| Key | Default | Effect |
|---|---|---|
| `ldap_enabled` | `false` | Enable LDAP authentication. See [Authentication](../features/authentication.md). |
| `ldap_server_url` | empty | LDAP server URL (e.g. `ldap://ldap.example.com:389`). |
| `ldap_security` | `starttls` | `starttls` or `ldaps`. |
| `ldap_bind_dn` | empty | Bind DN for searches (e.g. `cn=admin,dc=example,dc=com`). |
| `ldap_bind_password` | empty | Encrypted bind password. |
| `ldap_search_base` | empty | Search base DN (e.g. `ou=users,dc=example,dc=com`). |
| `ldap_user_filter` | `(sAMAccountName={username})` | LDAP user search filter. `{username}` is replaced with the login username. The default targets Active Directory; for OpenLDAP, switch to `(uid={username})`. |
| `ldap_group_mapping` | empty | JSON object mapping LDAP group DNs to BamDude group names. Empty = no group sync. |
| `ldap_auto_provision` | `false` | Auto-create the BamDude user on first successful LDAP bind. |
| `ldap_default_group` | empty | Fallback BamDude group name when an LDAP user has no mapped groups. Empty = no fallback (login fails). |

### Prometheus

| Key | Default | Effect |
|---|---|---|
| `prometheus_enabled` | `false` | Enable the [`/metrics` endpoint](../features/prometheus.md). |
| `prometheus_token` | empty | Bearer token required on the metrics endpoint. Empty = no auth (local-only deployments). |

## :material-robot-confused: Obico AI

See [Obico AI Failure Detection](../features/obico.md) for context on each.

| Key | Default | Effect |
|---|---|---|
| `obico_enabled` | `false` | Master toggle. |
| `obico_ml_url` | empty | ML API endpoint URL (e.g. `http://192.168.1.10:3333`). |
| `obico_sensitivity` | `medium` | `low`, `medium`, or `high`. |
| `obico_action` | `notify` | `notify`, `pause`, or `pause_and_off`. |
| `obico_poll_interval` | `10` | Seconds between detection checks while a print is running. Range 5 – 120. |
| `obico_enabled_printers` | empty | JSON array of printer IDs to monitor. Empty = monitor every connected printer. |

## :material-content-save: Local backups

| Key | Default | Effect |
|---|---|---|
| `local_backup_enabled` | `false` | Enable scheduled local backups. |
| `local_backup_schedule` | `daily` | `hourly`, `daily`, or `weekly`. |
| `local_backup_time` | `03:00` | Time of day for daily / weekly backups (HH:MM, 24-hour). |
| `local_backup_retention` | `5` | Number of backup files to keep (1–100). |
| `local_backup_path` | empty | Backup output directory. Empty = `DATA_DIR/backups`. |

## :material-account-key: Auth (mostly env-driven)

These are not editable from the UI — they're read-only env mirrors. See [Installation](../getting-started/installation.md) for the env-var details.

| Setting | Source | Effect |
|---|---|---|
| Setup gate active | `users` table | Drops automatically when the first admin is created. The `reset_admin` CLI clears it for recovery. |
| JWT signing key | `JWT_SECRET_KEY` env or `data/.jwt_secret` file | Auto-generated on first boot if neither is present. |
| Refresh-cookie `Secure` flag | `AUTH_REFRESH_COOKIE_SECURE` env | Auto-detected from request scheme when unset. |
| Trusted reverse-proxy IPs | `TRUSTED_PROXY_IPS` env | Comma-separated. Required for accurate per-IP rate limiting behind nginx / Caddy. |
| MFA-secret encryption key | `MFA_ENCRYPTION_KEY` env | Plaintext fallback works without it but logs a warning. |
