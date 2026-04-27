---
title: Settings reference
description: Every key under Settings → System / Print / Archive / Inventory / Network / Integrations
---

# Settings reference

This is the comprehensive index of every persistent setting BamDude exposes — what each one does, its default, and where it shows up in the UI. Settings live in the `settings` key-value table; most are surfaced under **Settings** in the side nav, but a few are read-only mirrors of env vars (the env value wins).

If a setting isn't on this page, it doesn't exist. If a UI field doesn't appear here, it's a per-row config (notification provider, smart plug, printer) rather than a global setting.

## :material-cog: System / general

| Key | Default | Effect |
|---|---|---|
| `language` | `en` | Server-side default language for all browsers + Telegram chat content + email templates. Frontend reads this on first load and syncs i18n; users can override per-tab in the UI. |
| `time_format` | `24h` | `12h` or `24h`. ETA / timestamp display in cards, notifications, and emails. |
| `date_format` | `system` | `system` (browser locale), `us` (`MM/DD/YYYY`), `eu` (`DD/MM/YYYY`), `iso` (`YYYY-MM-DD`). Controls every user-visible date. |
| `external_url` | empty | Public-facing URL of BamDude. Wins over the `APP_URL` env var. Used in password-reset / MFA email links, OIDC callback construction, and the Obico cached-frame URL. Set this when you front BamDude with a reverse proxy. |
| `default_printer_id` | unset | Default printer for new queue items / Print Now from the file manager. |
| `check_updates` | `true` | Periodically check the BamDude release feed for new versions. |
| `check_printer_firmware` | `true` | Periodically check Bambu's firmware feed for printer updates. |
| `include_beta_updates` | `false` | Surface beta releases in the update banner alongside stable releases. |

## :material-archive: Print archive

| Key | Default | Effect |
|---|---|---|
| `archive_3mf_retention_enabled` | `false` | Enable nightly auto-cleanup of `.3mf` files that haven't printed in N days. Metadata + thumbnails stay; only the `.3mf` is dropped. |
| `archive_3mf_retention_days` | `30` | The N. Minimum 1. |
| `save_thumbnails` | `true` | Capture a first-layer camera frame and store it as the archive's thumbnail when no 3MF thumbnail is available. |
| `capture_finish_photo` | `true` | Capture a completion photo and attach it to `print_complete` notifications. |
| `default_plate` | `0` | Plate style default for new queue items / library prints. |

## :material-clock-outline: Print queue

| Key | Default | Effect |
|---|---|---|
| `queue_drying_enabled` | `false` | Allow auto-drying between queue items when the next print's filament needs it. |
| `queue_drying_block` | `false` | Block the next print until drying completes (rather than running it in parallel with the current print). |
| `ambient_drying_enabled` | `false` | Allow ambient-temperature dry cycles (vs full drying schedules). |
| `stagger_enabled` | `false` | Enable [staggered start](../features/staggered-start.md) — limit concurrent bed heats across the farm to avoid power spikes. |
| `stagger_concurrent` | `2` | Maximum concurrent prints in stagger mode. |
| `stagger_interval_minutes` | `5` | Minimum minutes between stagger print starts. |
| `stagger_wait_for_bed` | `false` | Wait for the previous print's bed to cool before starting the next. |
| `stagger_strict_for_direct_dispatch` | `false` | Apply stagger to Print Now / direct-dispatch jobs too (otherwise stagger only governs queued items). |

## :material-package-variant: Inventory & filament

| Key | Default | Effect |
|---|---|---|
| `low_stock_threshold` | `10` | Spool remaining percentage at which `filament_low` notifications fire. |
| `disable_filament_warnings` | `false` | Master mute for low / out-of-filament alerts. |
| `prefer_lowest_filament` | `false` | Auto-assignment prefers the spool with the lowest remaining percentage. |
| `default_filament_cost` | `25` | Per-kg fallback cost when a spool's `cost` field is unset. |
| `ams_humidity_good` | `30` | Green-zone humidity threshold (%) on AMS cards. |
| `ams_humidity_fair` | `45` | Yellow-zone threshold. Above this is red. |
| `ams_temperature_good` | `30` | Green-zone temperature threshold (°C). |
| `ams_temperature_fair` | `40` | Yellow-zone threshold. |
| `ams_history_retention_days` | `90` | How many days of AMS history to keep before pruning. |
| `spoolman_enabled` | `false` | Enable [Spoolman two-way sync](../features/spoolman.md). |
| `spoolman_disable_weight_sync` | `false` | Don't push BamDude-tracked usage back to Spoolman. |
| `spoolman_report_partial_usage` | `false` | Push partial usage (mid-print snapshots) to Spoolman, not just on completion. |

## :material-bolt: Energy & cost

| Key | Default | Effect |
|---|---|---|
| `energy_cost_per_kwh` | `0.0` | Cost per kWh for archive / project cost calculations. Set to your local rate. |
| `library_disk_warning_gb` | `5` | Library disk-free threshold below which a banner warning shows in the UI. |

## :material-network: Network / connectivity

| Key | Default | Effect |
|---|---|---|
| `mqtt_enabled` | `false` | Enable [MQTT publishing](../features/mqtt.md) — republish printer state to an external MQTT broker. |
| `mqtt_broker` | empty | Broker hostname. |
| `mqtt_port` | `1883` | Broker port. |
| `mqtt_username` / `mqtt_password` | empty | Broker auth. Password is encrypted at rest. |
| `mqtt_use_tls` | `false` | Use TLS for the MQTT broker connection. |
| `mqtt_topic_prefix` | `home/bambu/` | Prefix for republished topics. |
| `prometheus_enabled` | `false` | Enable the [`/metrics` endpoint](../features/prometheus.md). |
| `ftp_retry_enabled` | `true` | Retry FTP 3MF downloads when the printer was unreachable at print start. See [Print Archive](../features/archiving.md). |
| `ftp_retry_count` | `3` | Maximum retries per attempt cycle. |
| `ftp_retry_delay` | `60` | Seconds between retries. |
| `ftp_timeout` | `120` | FTP download timeout in seconds. |

## :material-printer-3d: Virtual printer

| Key | Default | Effect |
|---|---|---|
| `virtual_printer_enabled` | `false` | Master toggle for the [virtual printer feature](../features/virtual-printer.md). Per-VP rows live in the `virtual_printers` table. |

## :material-puzzle: Integrations

| Key | Default | Effect |
|---|---|---|
| `ha_enabled` | `false` | Enable the Home Assistant integration. |
| `ha_url` / `ha_token` | empty | HA instance URL + long-lived token. Encrypted at rest. Env vars `HA_URL` / `HA_TOKEN` override these and lock them read-only in the UI when both are set. |
| `ldap_enabled` | `false` | Enable LDAP authentication. See [Authentication](../features/authentication.md). |
| `ldap_auto_provision` | `false` | Auto-create users on first successful LDAP bind. |
| `ldap_server_uri` | empty | LDAP server address (e.g. `ldap://ldap.example.com:389`). |
| `ldap_bind_dn` | empty | Bind DN template (with `{username}` placeholder). |
| `ldap_bind_password` | empty | Encrypted bind password. |
| `ldap_search_base` | empty | Search base DN. |
| `ldap_search_filter` | empty | User-search filter (e.g. `(uid={username})`). |

## :material-robot-confused: Obico AI

See [Obico AI Failure Detection](../features/obico.md) for context on each.

| Key | Default | Effect |
|---|---|---|
| `obico_enabled` | `false` | Master toggle. |
| `obico_ml_url` | empty | ML API endpoint URL. |
| `obico_sensitivity` | `medium` | `low` / `medium` / `high`. |
| `obico_action` | `notify` | `notify` / `pause` / `pause_and_off`. |
| `obico_poll_interval` | `30` | Seconds between snapshots (5–120). |
| `obico_enabled_printers` | `null` | Optional JSON array of printer IDs to restrict detection to. `null` = all printers. |

## :material-bell: Per-user notifications

| Key | Default | Effect |
|---|---|---|
| `user_notifications_enabled` | `false` | Enable per-user email notifications for prints the user owns. |

## :material-account-key: Auth (mostly env-driven)

These are not editable from the UI — they're read-only env mirrors. See [Installation](../getting-started/installation.md) for the env-var details.

| Setting | Source | Effect |
|---|---|---|
| Setup gate active | `users` table | Drops automatically when the first admin is created. The `reset_admin` CLI clears it for recovery. |
| JWT signing key | `JWT_SECRET_KEY` env or `data/.jwt_secret` file | Auto-generated on first boot if neither is present. |
| Refresh-cookie `Secure` flag | `AUTH_REFRESH_COOKIE_SECURE` env | Auto-detected from request scheme when unset. |
| Trusted reverse-proxy IPs | `TRUSTED_PROXY_IPS` env | Comma-separated. Required for accurate per-IP rate limiting behind nginx / Caddy. |
| MFA-secret encryption key | `MFA_ENCRYPTION_KEY` env | Plaintext fallback works without it but logs a warning. |
