---
title: Settings reference
description: Every settings key — general, printing, archive, inventory, network and integrations
---

# Settings reference

## Optional AI assistant connection (development preview)

The [AI assistant setup panel](../addons/ai-assistants/setup.md) is under Settings → API Keys. `mcp_enabled` defaults to `false`; `mcp_endpoint_url` is the operator's saved canonical address; `mcp_allowed_hosts` and `mcp_allowed_origins` are exact allowlists. These settings do not grant a key MCP access or increase owner permissions.

This is the comprehensive index of every persistent setting BamDude exposes — what each one does, its default, and where it shows up in the UI. Settings live in the `settings` key-value table; most are surfaced under **Settings** in the side nav, but a few are read-only mirrors of env vars (the env value wins).

The source of truth is `backend/app/schemas/settings.py::AppSettings`. If a setting isn't on this page, check there before assuming it doesn't exist — defaults below were verified against that schema.

## :material-cog: System / general

| Key | Default | Effect |
|---|---|---|
| `language` | `en` | Server-side default language for all browsers + Telegram chat content + email templates. Frontend reads this on first load and syncs i18n; users can override per-tab in the UI. |
| `time_format` | `system` | `system` (browser locale), `12h`, or `24h`. ETA / timestamp display in cards, notifications, and emails. |
| `date_format` | `system` | `system` (browser locale), `us` (`MM/DD/YYYY`), `eu` (`DD/MM/YYYY`), `iso` (`YYYY-MM-DD`). Controls every user-visible date. |
| `currency` | `USD` | Currency code for cost tracking display. |
| `external_url` | empty | Public-facing URL of BamDude. Wins over the `APP_URL` env var. Used in password-reset / MFA email links, OIDC callback construction, the Obico cached-frame URL (unless `obico_snapshot_base_url` is set), and the photo links in notifications. Set this when you front BamDude with a reverse proxy. |
| `default_printer_id` | unset | Accepted and stored for API compatibility; nothing reads it and the Settings page has no control for it. |
| `default_sidebar_order` | empty | Admin-set default sidebar item order — JSON `{"order": [...ids]}` or a JSON array. Empty = use built-in order. |
| `check_updates` | `true` | Periodically check the BamDude release feed for new versions. |
| `check_printer_firmware` | `true` | Printer cards check Bambu Lab for firmware updates. Off: the cards make no automatic checks and the server does not contact Bambu Lab for a card's check; the Firmware page and an upload you start yourself still work. |
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
| `save_thumbnails` | `true` | Accepted and stored for API compatibility; nothing reads it (previews are always extracted) and the Settings page has no control for it. |
| `capture_finish_photo` | `true` | Capture a completion photo from the printer camera and attach it to `print_complete` notifications. |
| `library_disk_warning_gb` | `5.0` | Show a banner warning when the data partition has less than this much free space. |

## :material-clock-outline: Print queue & dispatch

| Key | Default | Effect |
|---|---|---|
| `queue_drying_enabled` | `false` | Allow auto-drying between queue items when the next print's filament needs it. |
| `queue_drying_block` | `false` | Hold the printer's queue while a drying cycle is really running. It does not prevent a cycle ahead of a job that cannot start yet; the AutoQueue prefers an equally suitable printer that is not held. |
| `auto_drying_sustained_minutes` | `15` | Minutes an AMS must read above its humidity threshold before auto-drying starts a cycle no scheduled job is waiting for; `0` starts on the first reading. See [AMS & Humidity](../features/ams.md). |
| `ambient_drying_enabled` | `false` | Auto-dry AMS filament on idle printers when humidity exceeds threshold, regardless of queue state. |
| `print_drying_enabled` | `false` | Allow auto-drying to also fire on a printer that's currently **printing**, when its model + firmware supports concurrent drying (H2D 01.03.00.00+, H2C/H2S/P2S/H2D Pro 01.02.00.00+, X2D/A2L 01.01.00.00+, X1C 01.11.02.00+). Mid-print drying temp is capped 5 °C below the idle preset (floor 40 °C). See [AMS & Humidity](../features/ams.md). |
| `drying_presets` | empty | JSON object of per-filament drying presets. Empty = use built-in defaults. |
| `stagger_enabled` | `false` | Enable [staggered start](../features/staggered-start.md) — limit concurrent bed heats across the farm to avoid power spikes. |
| `stagger_concurrent` | `2` | Maximum concurrent printers heating. |
| `stagger_interval_minutes` | `5` | Wait time after a slot frees before the next start. |
| `stagger_wait_for_bed` | `true` | Slot frees when the bed reaches target temp (±1 °C). When off, the slot frees immediately after print start. |
| `stagger_strict_for_direct_dispatch` | `false` | Print Now and Re-print are refused while the printer's stagger group has no free slot, instead of waiting for one. Queued prints always wait. |
| `per_printer_mapping_expanded` | `false` | Expand the custom filament mapping section by default in the print modal. |
| `auto_queue_compatible_models` | `false` | Let Auto Queue use a Bambu Studio compatible printer when no exact-model printer is ready. Manual compatible targets remain available when off. |
| `model_dispatch_order` | `fewest_hours` | Which printer an AutoQueue job takes among equally fit ones: `fewest_hours`, `most_hours`, `least_recently_used` (idle the longest) or `priority` (each printer's *Priority for AutoQueue jobs*, lowest first, empty last). See [Which printer gets the job](../features/auto-queue.md#printer-order). |

## :material-printer-3d: Virtual printer

| Key | Default | Effect |
|---|---|---|
| `virtual_printer_enabled` | `false` | Master toggle for the [virtual printer feature](../features/virtual-printer.md). Per-VP rows live in the `virtual_printers` table. |
| `virtual_printer_access_code` | empty | 8-character access code that slicers must use to authenticate against any virtual printer. Per-VP overrides live on the `virtual_printers` row. |
| `virtual_printer_mode` | `file_manager` | Default mode for new VP rows: `file_manager`, `print_queue`, or `proxy`. See [Virtual printer modes](../features/virtual-printer.md#modes). |
| `preferred_slicer` | `bambu_studio` | `bambu_studio` or `orcaslicer`. Which slicer to suggest in workflows that link out. |

## :material-content-cut: Slicer API

| Key | Default | Effect |
|---|---|---|
| `use_slicer_api` | `false` | Master toggle for [server-side slicing](../features/slicer-api.md). Off = the Slice button is replaced by "open in your desktop slicer". |
| `orcaslicer_api_url` | empty | URL of the OrcaSlicer sidecar. Empty falls back to the `SLICER_API_URL` env var (`http://localhost:3003`). Validated on save — see the note below. |
| `bambu_studio_api_url` | empty | URL of the BambuStudio sidecar. Empty falls back to `BAMBU_STUDIO_API_URL` (`http://localhost:3001`). Validated on save. |
| `slicer_stall_timeout_minutes` | `15` | Minutes to keep waiting **with no progress** from the sidecar (range 1–240). The clock resets on every progress update, so a heavy model that keeps reporting runs to completion. On a sidecar too old to report progress it bounds total slicing time instead. |

!!! warning "Addresses you type in are validated"
    The two slicer URLs, the Home Assistant URL and the Obico detection endpoint
    are all checked before they are saved. A mistyped or hostile value could point
    BamDude at somewhere it should never fetch — most notably the **cloud metadata
    address**, which is the standard way credentials get read out of a server.

    Addresses on your own machine or home network stay allowed, because that is
    where these services normally live. What is refused: a non-web address, an
    address written as a plain number, a multicast address, and the cloud metadata
    endpoints. The single-sign-on issuer address, which must be reachable on the
    public internet, is checked by the stricter rule it always should have used.

## :material-package-variant: Inventory & filament

| Key | Default | Effect |
|---|---|---|
| `low_stock_threshold` | `20.0` | Spool remaining percentage at which `filament_low` notifications fire. Range 0.1 – 99.9. |
| `runout_zero_point_enabled` | `true` | Close a spool at exactly its label weight when the printer reports an unambiguous filament runout. |
| `runout_archive_spool_enabled` | `false` | Archive a spool after an unambiguous runout closes and a backup or replacement continues the print; built-in inventory and Spoolman. Requires runout close-out. |
| `ams_sync_bidirectional` | `true` | Let idle AMS readings correct a Bambu-tagged spool's weight downward too (a value must repeat across two reports a minute apart). |
| `runout_purge_grams` | `0` | Grams charged to the backup spool for the purge of an AMS auto-switch. 0 disables it. |
| `usage_events_retention_hours` | `72` | How long a finished print's usage-event journal (runout/tray timeline) is kept for troubleshooting. |
| `disable_filament_warnings` | `false` | Master mute for low / out-of-filament alerts. |
| `prefer_lowest_filament` | `true` | After compatibility and exact-colour preference, auto-assignment favours the lowest remaining source. Tracked AMS spools use grams and firmware-only sources use percentage in a separate tier. Among AutoQueue printers with an equal place in the [printer order](../features/auto-queue.md#printer-order), prefer the lower known average reported fill. |
| `default_filament_cost` | `25.0` | Per-kg fallback cost when a spool's `cost` field is unset. |
| `auto_add_unknown_rfid` | `true` | Auto-add a spool to inventory when an AMS reads an unknown RFID tag. Off → a confirmation card (material / colour pre-filled) is shown instead of silent creation. See [Spool Inventory](../features/inventory.md). |
| `ams_humidity_good` | `40` | Green-zone humidity threshold (%) on AMS cards (≤ this value). |
| `ams_humidity_fair` | `60` | Yellow-zone humidity threshold (≤ this value). Above is red. |
| `ams_humidity_thresholds` | empty | JSON map of per-filament-type humidity trigger thresholds for auto-drying + alarms — `{"default": int, "PLA": int, "ASA": int, …}`. Empty = fall back to `ams_humidity_fair` for every type. A multi-material AMS resolves to the strictest (lowest) across its loaded spools. |
| `ams_temp_good` | `28.0` | Green-zone temperature threshold (°C) on AMS cards. |
| `ams_temp_fair` | `35.0` | Yellow-zone temperature threshold. Above is red. |
| `ams_temp_alarm` | unset | Temperature (°C) above which the AMS temperature alarm is sent. Unset (or 0 and below) falls back to `ams_temp_fair`. No alarm while the AMS is drying or cooling down after it. |
| `ams_history_retention_days` | `30` | How many days of AMS history to keep before pruning. Minimum 1; 0 is refused. |
| `inbox_retention_days` | `30` | How many days of in-app notification-centre history each person keeps. Range 1-365. Swept once a day, read or not. |
| `log_retention_days` | `7` | Retention limit for daily `bamdude-YYYY-MM-DD.log` archives. Range 1–365. Excess archives are removed at the next successful rotation. See [System info → Log rotation](../features/system-info.md#log-rotation-retention). |
| `bed_cooled_threshold` | `35.0` | Bed temperature (°C) at which the `bed_cooled` notification fires. |
| `pause_warning_minutes` | `5` | **Pause heads-up lead time** (Settings → Printing): how many minutes before a pause added in the slicer the [Pause coming up](../features/notifications.md#pause-coming-up) event is sent. Range 0–120; `0` switches the event off. Without a time estimate the event is sent when the print reaches the layer before the pause. |
| `outcome_reminder_after_minutes` | `60` | **Unchecked result reminder** (Settings → Printing): how many minutes a completed print may stay [unchecked](../features/archiving.md#checking-a-prints-result) before the [Result Not Checked](../features/notifications.md#result-not-checked) event is sent, once per print. Range 5–10080 (a week). |

## :material-bolt: Energy & cost

| Key | Default | Effect |
|---|---|---|
| `energy_cost_per_kwh` | `0.15` | The electricity price now, per kWh: the fixed price you entered, or — with a Home Assistant sensor as the source — the last price read from it. Every change is kept in a price history with its time, and energy is costed at the price in effect when it was used; changing the price does not re-cost the past. A negative price counts as 0. While the source is `homeassistant` it cannot be set by hand in Settings; `POST /settings/electricity-price` is still accepted. See [Energy → Cost Calculation](../features/energy.md#cost-calculation). |
| `energy_price_source` | `fixed` | **Electricity price source** (Settings → Printing → Cost Tracking). `fixed` — the price is entered by hand. `homeassistant` — the price is read from the sensor named in `energy_price_ha_entity` once an hour; when the sensor cannot be read, the last price stays. Switching to `homeassistant` reads the sensor first and is refused if that read fails. |
| `energy_price_ha_entity` | *(empty)* | **Price sensor**: the Home Assistant entity whose value is the electricity price — a `sensor.*`, `input_number.*` or `number.*` entity id. A price per MWh or per Wh is converted to per kWh by the entity's unit; a negative price counts as 0. Used only while `energy_price_source` is `homeassistant`; needs the Home Assistant connection. |

## :lucide-spool: Spoolman

| Key | Default | Effect |
|---|---|---|
| `spoolman_enabled` | `false` | Enable [Spoolman two-way sync](../features/spoolman.md). |
| `spoolman_url` | empty | Spoolman server URL (e.g. `http://localhost:7912`). Saved with **Save address** after a confirmation, never auto-saved: a new non-empty address removes every Spoolman slot assignment and K-profile link ([Connecting](../features/spoolman.md#spoolman-connecting)). |
| `spoolman_sync_mode` | `auto` | `auto` syncs immediately on changes; `manual` requires explicit button press. |
| `spoolman_disable_weight_sync` | `false` | Don't push BamDude-tracked usage back to Spoolman — only update location. |
| `spoolman_report_partial_usage` | `true` | Report estimated usage on failed / cancelled prints based on layer progress. |
| `spool_sort_order` | empty | Sort levels (a field and a direction each) for the slot-assignment dialog and for the Filaments page while no column is chosen. Empty keeps the built-in order. See [Spool order](../features/inventory.md#spool-order). |
| `spool_display_template` | `{brand} {material} {subtype} {color_name}` | Template for the synthesised spool display name. Placeholders: `{brand}`, `{material}`, `{subtype}`, `{color_name}`, `{color_hex}`, `{slicer_filament_name}`, `{note}`, `{label_weight_g}`, `{label_weight_kg}`, `{remaining_g}`, `{remaining_kg}`, `{remaining_pct}`, `{cost_per_kg}`. Unknown placeholders are kept verbatim so typos surface. |

## :material-network: Network / connectivity

| Key | Default | Effect |
|---|---|---|
| `mqtt_enabled` | `false` | Enable [MQTT publishing](../features/mqtt.md) — republish printer state to an external MQTT broker. |
| `mqtt_broker` | empty | Broker hostname or IP. |
| `mqtt_port` | `1883` | Broker port. TLS deployments typically use `8883`. |
| `mqtt_username` / `mqtt_password` | empty | Broker auth. Password is encrypted at rest. |
| `mqtt_use_tls` | `false` | Use TLS for the MQTT broker connection. |
| `mqtt_tls_verify` | `false` | With TLS on, check the broker's certificate and host name against the system's trusted authorities and refuse to connect when the check fails. Off accepts any certificate (a self-signed broker works). |
| `mqtt_topic_prefix` | `bambuddy` | Prefix for all republished topics. Inherited from upstream Bambuddy — change to `bamdude` on fresh installs if you prefer. |
| `ftp_retry_enabled` | `true` | Retry FTP 3MF downloads when the printer was unreachable at print start. See [Print Archive](../features/archiving.md). |
| `ftp_retry_count` | `3` | Maximum retries per attempt cycle (1–10). |
| `ftp_retry_delay` | `2` | Seconds between retries (1–30). |
| `ftp_timeout` | `30` | Seconds a single FTP socket operation may sit with no data arriving (10–300). It bounds a **stalled** transfer, not a slow one — a 3MF download that keeps arriving is left to finish however long it takes. See [Print Archive](../features/archiving.md#3mf-download-recovery). |

## :material-camera: Camera

| Key | Default | Effect |
|---|---|---|
| `camera_view_mode` | `window` | `window` opens cameras in a new browser window; `embedded` shows them as an overlay on the dashboard. The default for a browser that has not picked a mode on a printer's camera button — each browser remembers its own pick. |

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
| `prometheus_token` | empty | Bearer token required on the metrics endpoint. Required when enabled; blank legacy configurations return 503. |

### Zigbee sensors

| Key | Default | Effect |
|---|---|---|
| `zigbee_sensor_poll_seconds` | `30` | Poll cadence for mains-powered Zigbee sensors (jittered like the plug poller). Battery sensors are never polled — they sleep. |
| `zigbee_sensor_reporting` | empty | JSON blob of per-measurement reporting defaults (`{"temperature": {"min_interval": …, "max_interval": …, "reportable_change": …}, …}`) applied to devices with no override of their own. Empty, or any missing field, falls back to the registry defaults. |
| `zigbee_sensor_stale_multiplier` | `2` | A reporting sensor's value older than this multiple of its `max_interval` counts as stale ("sensor went silent"). Per-device staleness override wins; polled devices keep a fixed 120 s window. |

### Manyfold

The connection to a self-hosted [Manyfold](../features/manyfold.md) library. It is edited on its own card under *Settings → Network*, by an administrator only, and saved with **Save connection** — not with the rest of the settings.

| Key | Default | Effect |
|---|---|---|
| `manyfold_enabled` | `false` | **Use Manyfold** — switches the Manyfold tab of *Model sources* on. Needs the three values below. |
| `manyfold_url` | empty | **Manyfold URL** — `http://` or `https://`, an address on your own network is fine. |
| `manyfold_client_id` | empty | **Client ID** of the OAuth application created in Manyfold with the scopes `public` and `read`. |
| `manyfold_client_secret` | empty | **Client secret** of that application. Never shown again after saving, left out of Git backups, and asked for again when the URL or the client ID changes. |

## :material-robot-confused: Obico AI

See [Obico AI Failure Detection](../features/obico.md) for context on each.

| Key | Default | Effect |
|---|---|---|
| `obico_enabled` | `false` | Master toggle. Turning it on turns `octoeverywhere_enabled` off. |
| `obico_ml_url` | empty | ML API endpoint URL (e.g. `http://192.168.1.10:3333`). |
| `obico_snapshot_base_url` | empty | **BamDude address for the ML API (optional)** — the address the ML API fetches camera frames from: BamDude's LAN address or its Docker service name (e.g. `http://bamdude:8000`). A full `http://` or `https://` address without credentials, query parameters or a fragment. Empty = `external_url` is used. Only frame fetching uses it. Administrators only; saved with **Save connection**. |
| `obico_sensitivity` | `medium` | `low`, `medium`, or `high`. Scales the Low / High thresholds, and the Pause level (1.75 × High) with them. |
| `obico_action` | `notify` | `notify`, `pause`, or `pause_and_off`. A notification is sent once per print at the alert level whatever the action; `pause` and `pause_and_off` act at the stronger Pause level, also once per print. |
| `obico_poll_interval` | `10` | Seconds between detection checks while a print is running. Range 5 – 120. |
| `obico_enabled_printers` | empty | JSON array of printer IDs to monitor. Empty = monitor every connected printer. A deleted printer is removed from the list. |

## :material-robot-confused: OctoEverywhere AI

See [OctoEverywhere AI Failure Detection](../features/octoeverywhere.md).

| Key | Default | Effect |
|---|---|---|
| `octoeverywhere_enabled` | `false` | Master toggle. Administrators only. Turning it on turns `obico_enabled` off; a save that turns both on is refused. A full restore turns it off; a Git restore never writes it. |
| `octoeverywhere_api_key` | empty | **Gadget API key**. Write-only; administrators only; saved with **Save key**. Sent only to OctoEverywhere. A Git restore never restores it. |
| `octoeverywhere_confidence` | `medium` | `lowest`, `low`, `medium`, `high` or `highest` — how certain the model has to be before it suggests a warning or a pause. |
| `octoeverywhere_action` | `notify` | `notify`, `pause` or `pause_and_off`. A suggested warning notifies; `pause` and `pause_and_off` follow OctoEverywhere's pause suggestion, once per print. |
| `octoeverywhere_poll_interval` | `20` | Seconds between checks of each printing printer. Range 5 – 30; OctoEverywhere may ask for a longer pause. |
| `octoeverywhere_enabled_printers` | empty | JSON array of printer IDs to monitor. Empty = monitor every connected printer. A deleted printer is removed from the list. |

## :material-content-save: Local backups

| Key | Default | Effect |
|---|---|---|
| `local_backup_enabled` | `false` | Enable scheduled local backups. |
| `local_backup_schedule` | `daily` | `hourly`, `daily`, or `weekly`. |
| `local_backup_time` | `03:00` | Time of day for daily / weekly backups (HH:MM, 24-hour). |
| `local_backup_retention` | `5` | Number of backup files to keep (1–100). |
| `local_backup_path` | empty | Backup output directory. Empty = `DATA_DIR/backups`. |

## :material-account-key: Auth (mostly env-driven)

A couple of auth settings *are* editable from the UI (**Settings → Users**):

| Key | Default | Effect |
|---|---|---|
| `session_max_hours` | `720` | Admin ceiling on session lifetime (the refresh-token TTL), in hours. Range 1–720; default 720 h (30 days) preserves remember-me. Applied to existing sessions at their next refresh. Set via the Session Policy card. See [Authentication](../features/authentication.md). |
| `local_login_enabled` | `true` | Allow username + password login on `/auth/login`. Turn off when only SSO should be usable (guarded: needs ≥ 1 enabled OIDC provider and your own account OIDC-linked). Env `BAMDUDE_LOCAL_LOGIN=true` bypasses this at the route level for recovery. |

The rest are read-only env mirrors — set them via environment variables. See [Installation](../getting-started/installation.md) for the env-var details.

| Setting | Source | Effect |
|---|---|---|
| Setup gate active | `users` table | Drops automatically when the first admin is created. The `reset_admin` CLI clears it for recovery. |
| JWT signing key | `JWT_SECRET_KEY` env or `data/.jwt_secret` file | Auto-generated on first boot if neither is present. |
| Refresh-cookie `Secure` flag | `AUTH_REFRESH_COOKIE_SECURE` env | Auto-detected from request scheme when unset. |
| Trusted reverse-proxy IPs | `TRUSTED_PROXY_IPS` env | Comma-separated. Required for accurate per-IP rate limiting behind nginx / Caddy. |
| MFA-secret encryption key | `MFA_ENCRYPTION_KEY` env | Plaintext fallback works without it but logs a warning. |


## :material-database: Database connection environment

These are process settings, not editable Settings rows. Restart after a change. See [PostgreSQL](../features/postgresql.md) for limits and dead-connection behavior.

| Variable | Default | Effect |
|---|---|---|
| `DB_POOL_SIZE` | SQLite `10`, PostgreSQL `20` | Persistent pooled connections per engine. |
| `DB_MAX_OVERFLOW` | SQLite `90`, PostgreSQL `60` | Extra connections above the pool size. Explicit values retain their existing meaning. |
| `DB_POOL_PRE_PING` | PostgreSQL `true` | Check a connection before use; SQLite ignores it. With `false` the first use of a dead connection can fail. No transaction replay. |
