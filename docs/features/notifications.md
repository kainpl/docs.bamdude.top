---
title: Notifications
description: Multi-provider push notifications for print events
---

# Notifications

Eight delivery channels, one editor, one routing config. Subscribe each provider to whichever events you actually want, set per-provider quiet hours and a daily digest, customise templates per language.

---

## :material-bell-ring: Supported Providers

| Provider | Setup | Features |
|----------|:-----:|----------|
| **Telegram** | Medium | Via the BamDude bot, with actionable inline buttons (clear plate, mark maintenance done, pause/stop). Routes to every authorised chat that subscribed to the event. |
| **Discord** | Easy | Channel webhook URL, embed formatting, image attachments. |
| **Email (SMTP)** | Medium | STARTTLS / SSL / plain. Per-provider `to_email` so different users see different bodies. |
| **Pushover** | Easy | Priority levels, image attachment up to 2.5 MB. |
| **ntfy** | Easy | Topic-based, optional bearer token, image attachments. |
| **CallMeBot** | Easy | WhatsApp / Signal bridge — phone + API key, URL-encoded message. |
| **Home Assistant** | Easy | `persistent_notification.create` or any `notify.*` service. Single global HA URL/token from Settings (or `HA_URL` / `HA_TOKEN` env). |
| **Webhook** | Flexible | Generic JSON or Slack-format POST, custom field names, base64 image, optional bearer token. |

---

## :material-plus-circle: Adding a Provider

1. Go to **Settings** > **Notifications**
2. Click **Add Provider**
3. Select provider type and enter configuration
4. Click **Send Test** to verify
5. Configure event triggers
6. Click **Add**

---

## :material-cog: Per-Provider Setup

### ntfy

Topic-based, free, no account needed. The simplest channel to bring online.

| Field | Value |
|---|---|
| **Server** | `https://ntfy.sh` (default) or your self-hosted instance URL |
| **Topic** | A unique string — anyone who knows it can publish, so use something unguessable |
| **Bearer token** | Optional; required for self-hosted ACL-protected topics |

Subscribe on your phone with the [ntfy Android](https://play.google.com/store/apps/details?id=io.heckel.ntfy) or [iOS](https://apps.apple.com/app/ntfy/id1625396347) app. ntfy supports **5 priority levels** that BamDude maps per event:

| Priority | ntfy value | Typical use |
|---|---|---|
| **Min** | 1 | Diagnostics-style pings — no sound, no badge |
| **Low** | 2 | Informational, non-urgent (e.g. "first layer complete") |
| **Default** | 3 | Standard notification |
| **High** | 4 | Audible / urgent (e.g. "filament low") |
| **Urgent** | 5 | Wakes the device, ignores Do-Not-Disturb (e.g. "print failed") |

### WhatsApp / Signal (CallMeBot)

Free WhatsApp / Signal bridge — no own bot infrastructure needed.

1. Add CallMeBot to your contacts: **+34 644 51 95 23**
2. Send `I allow callmebot to send me messages` via WhatsApp
3. CallMeBot replies with your **API key**

| Field | Value |
|---|---|
| **Phone number** | Your number in E.164 format (e.g. `+1234567890`) |
| **API key** | The key CallMeBot returned |

### Discord

Channel webhook URL — easiest way to get rich embed messages with thumbnails into a Discord server.

1. In Discord open the target channel's settings → **Integrations** → **Webhooks**
2. Click **New Webhook**, customise name/avatar, **Copy Webhook URL**
3. Paste the URL into BamDude's provider form

BamDude posts as embeds with the snapshot image inline when one is available.

### Pushover

Per-user push service with native iOS/Android apps and on-device priority escalation.

1. Create an account at [pushover.net](https://pushover.net/) and install the app
2. Create an **Application** in your dashboard

| Field | Value |
|---|---|
| **User key** | From your Pushover account page |
| **API token** | From the Application you just created |

Pushover priority maps to numeric levels `-2…+2` per event in BamDude — same idea as ntfy but with the Pushover scale.

### SMTP / Gmail

Plain SMTP — works with any provider that exposes username + password auth.

| Field | Example |
|---|---|
| **SMTP host** | `smtp.gmail.com` |
| **Port** | `587` (STARTTLS) or `465` (SSL) |
| **Security** | `STARTTLS` / `SSL` / `plain` |
| **Username** | Your full email address |
| **Password** | App password (not the account password — Gmail rejects the latter) |
| **From address** | The sender address recipients see |
| **To address** | Per-provider; lets different team members get different bodies |

For Gmail: enable 2FA, then generate an [App Password](https://myaccount.google.com/apppasswords) and use that here.

### Home Assistant

Zero-config when HA is already wired up under **Settings** → **Network** → **Home Assistant** (or the `HA_URL` / `HA_TOKEN` env vars). The provider has no extra fields — events become `persistent_notification.create` calls in your HA dashboard.

!!! tip "Forward HA notifications to other channels"
    Use HA automations to mirror these persistent notifications to the HA Companion app, Telegram, ntfy, etc. — gives you a single audit log in HA plus your usual mobile push.

### Generic Webhook

For everything else — n8n, Node-RED, custom HTTP endpoints, Slack-format integrations.

| Field | Value |
|---|---|
| **URL** | Your endpoint (HTTPS recommended) |
| **Headers** | Optional — use for `Authorization: Bearer …` and similar |
| **Format** | `generic` (structured BamDude JSON) or `slack` (`{"text": "..."}` only) |

See **Webhook Payload Schema** below for the structured-JSON shape.

---

## :material-code-json: Webhook Payload Schema

Generic-format webhooks send a standardised JSON envelope: `title`, `message`, `timestamp`, `source`, `event` (the event-type string), plus all event-specific fields hoisted to top-level keys so automation tools can branch on `event` without parsing the message text.

**`print_complete`:**

```json
{
  "title": "Print Complete",
  "message": "Workshop X1C: benchy.3mf completed in 2h 15m",
  "timestamp": "2026-04-02T14:30:00.123456",
  "source": "BamDude",
  "event": "print_complete",
  "printer": "Workshop X1C",
  "filename": "benchy.3mf",
  "duration": "2h 15m",
  "filament_grams": "15.2",
  "filament_details": "AMS-A T1 PLA: 15.2g"
}
```

**`print_failed`** (and `print_stopped`) carry extra `progress` + `reason` fields:

```json
{
  "title": "Print Failed",
  "message": "Workshop X1C: benchy.3mf failed at 50%",
  "timestamp": "2026-04-02T15:15:00.123456",
  "source": "BamDude",
  "event": "print_failed",
  "printer": "Workshop X1C",
  "filename": "benchy.3mf",
  "duration": "0h 45m",
  "filament_grams": "7.6",
  "filament_details": "PLA: 7.6g",
  "progress": "50",
  "reason": "Filament runout"
}
```

**`printer_offline`** — minimal payload, only what's relevant:

```json
{
  "title": "Printer Offline",
  "message": "Workshop X1C is offline",
  "timestamp": "2026-04-02T14:30:00.123456",
  "source": "BamDude",
  "event": "printer_offline",
  "printer": "Workshop X1C"
}
```

**`first_layer_complete`** — includes a base64-encoded JPEG snapshot in the `image` field:

```json
{
  "title": "First Layer Complete",
  "message": "Workshop X1C: benchy.3mf — Layer 1/200 done",
  "timestamp": "2026-04-02T14:30:00.123456",
  "source": "BamDude",
  "event": "first_layer_complete",
  "printer": "Workshop X1C",
  "filename": "benchy.3mf",
  "total_layers": "200",
  "image": "/9j/4AAQSkZJRg..."
}
```

!!! tip "Decoding the image"
    The `image` field is a standard base64-encoded JPEG. Home Assistant: pass it to `notify.mobile_app_*` as `image` data via a template. Node-RED: `Buffer.from(msg.payload.image, 'base64')`. The field is only present when a snapshot was actually captured — not all events include it.

!!! info "Slack / Mattermost format compatibility"
    With **format = slack**, only `{"text": "..."}` is sent — structured event fields are dropped. Use the generic format for any automation that needs to read structured data; use slack only for human-readable channel posts.

---

## :material-tune: Event Triggers

Each provider subscribes independently. Toggling an event off on one provider doesn't stop it on others.

**Print:**

| Event | Fires when |
|-------|------------|
| `print_start` | Print starts on a printer |
| `first_layer_complete` | Layer 1 finishes (catch first-layer fails fast) |
| `print_progress` | At configurable progress milestones |
| `print_complete` | Print finishes successfully |
| `print_failed` | HMS error / hardware fault stopped the print |
| `print_stopped` | User-initiated stop |
| `bed_cooled` | Bed cooled to threshold (post-print cleanup signal) |

**AMS / filament:**

| Event | Fires when |
|-------|------------|
| `print_missing_spool_assignment` | Print started without complete spool→AMS mapping |
| `filament_low` | Spool remaining below `low_stock_threshold` |
| `ams_humidity_high` / `ams_temperature_high` | AMS exceeds its threshold |

**Printer:**

| Event | Fires when |
|-------|------------|
| `printer_offline` | MQTT disconnect |
| `printer_error` | HMS error code triggered (BamDude includes the human-readable translation) |
| `plate_not_empty` | Bed-occupancy gate caught the next-print start (auto-pause) |
| `maintenance_due` | Scheduled maintenance interval reached |

**Queue:**

| Event | Fires when |
|-------|------------|
| `queue_job_added` / `queue_job_started` / `queue_job_waiting` / `queue_job_skipped` / `queue_job_failed` / `queue_completed` | Self-explanatory queue lifecycle events. Only the events you opt into. |

**User / system:**

| Event | Fires when |
|-------|------------|
| `user_created`, `password_reset` | Account-management emails (HTML + plain). |
| `user_print_start` / `user_print_complete` / `user_print_failed` / `user_print_stopped` | Per-user email notifications when the user owns the print. |
| `test` | Validation send from the provider editor. |

---

## :material-send: Actionable Telegram Notifications

When using Telegram as a notification provider, BamDude sends actionable notifications with inline buttons:

| Event | Actions |
|-------|---------|
| **Print Complete** | Clear plate button |
| **Maintenance Due** | Mark done button |
| **Print Progress** | Pause / Stop buttons |

See [Telegram Bot Setup](telegram-bot.md) for full configuration.

!!! tip "Per-chat event routing"
    Telegram notifications are not routed to a single hard-coded chat -- they are fanned out to every authorized chat whose `telegram_chats.notification_events` setting includes the firing event. So one chat can subscribe to "Print Complete" + "HMS Error" only, while another chat takes everything. Configure each chat's subscriptions under **Settings > Notifications > Telegram Chats**.

!!! tip "Localized templates per user"
    Notification bodies are rendered from `notification_templates_{en,uk}.json`. The template language is picked per-recipient -- Telegram uses the chat's owning user's `settings.language`, email uses the recipient user's language, etc. Adding a new template key means updating *both* `en` and `uk` JSON files (BamDude ships en + uk only).

---

## :material-priority-high: Per-event priority (ntfy & Pushover)

Both ntfy and Pushover support priority levels — `default` / `high` / `urgent` for ntfy, `-2…+2` for Pushover. BamDude lets you pick the priority **per event type** on each provider, so a finished print doesn't push to the lock-screen but a print failure does:

| Event type | Suggested ntfy priority | Why |
|---|---|---|
| `print_complete`, `bed_cooled` | `default` | Informational — read when convenient. |
| `print_failed`, `printer_error`, `plate_not_empty` | `high` or `urgent` | Action-required. |
| `filament_low`, `maintenance_due` | `default` | Plan-ahead, not interrupt-now. |
| `ams_humidity_high` | `high` | Affects filament you're about to use. |

Configure under each provider's edit form: there's a per-event priority dropdown next to the event-subscribe toggle. Defaults map every event to `default` priority — opt-in to escalation only where it matters. Pushover's same control accepts the numeric levels.

This is independent of the daily digest / quiet hours pipeline below — a quiet-hour-suppressed event isn't sent at any priority; an active event still respects the per-event priority you picked.

---

## :material-clock: Quiet hours & daily digest

Configuration shape varies by provider type — the Telegram bot is special.

**Non-telegram providers (email / ntfy / pushover / discord / webhook / homeassistant / callmebot)** carry both settings on the provider row itself:

| Setting | Where | Effect |
|---|---|---|
| `quiet_hours_enabled` + `quiet_hours_start` / `quiet_hours_end` | Provider config | Events that fire inside the window are dropped (not queued — quiet hours is "shut up", not "delay"). |
| `daily_digest_enabled` + `daily_digest_time` | Provider config | Events that fire any time in the day are queued in `notification_digest_queue`; the next time the wall clock crosses `daily_digest_time` BamDude flushes the queue as a single digest message. |

**Telegram (m045)** is structured differently: the bot/provider row keeps only the **schedule** (`daily_digest_enabled` + `daily_digest_time`), while the per-event opt-in, quiet hours, and digest opt-in all live on each `TelegramChat` row. So one chat can be in quiet hours while another stays loud, both fed by the same bot. See [Telegram Bot Setup](telegram-bot.md) for the per-chat fields.

---

## :material-file-document-edit: Template editor

Every event has a default template in `data/notification_templates_{en,uk}.json`. The Templates tab under Settings → Notifications lets you override any of them — title + body — with a MarkdownV2 toolbar and live preview.

The Templates tab groups the 28 default templates by purpose so a glance tells you which dispatch path each one feeds:

| Group | Count | What it's for |
|---|---|---|
| **Print events** | 9 | `print_start/complete/failed/stopped/progress`, `plate_not_empty`, `bed_cooled`, `first_layer_complete`, `print_missing_spool_assignment` |
| **Printer status** | 4 | `printer_offline`, `printer_error`, `filament_low`, `maintenance_due` |
| **AMS environmental** | 2 | `ams_humidity_high`, `ams_temperature_high` (also reused at runtime for the AMS-HT events) |
| **Print queue** | 6 | `queue_job_added/started/waiting/skipped/failed`, `queue_completed` |
| **Job owner emails** | 4 | `user_print_start/complete/failed/stopped` — SMTP-only, sent to the print job owner |
| **System emails** | 2 | `user_created` (welcome), `password_reset` |
| **Test** | 1 | `test` — used by the "Send test" buttons |

Each card carries a small UPPERCASE channel badge:

- **Green `ALL`** — fan-out to every provider type that wants the event (TG / email / ntfy / pushover / discord / webhook / homeassistant / callmebot). The 21 entries in the first 4 groups.
- **Blue `EMAIL`** — SMTP-only flow. The 4 `user_print_*` job-owner emails plus `user_created` / `password_reset`.
- **Amber `TEST`** — internal test-button helper.

The mapping is metadata about which dispatch path consumes each template; it's not stored on the row, just rendered from a static lookup in the frontend.

Variable substitution uses simple curly-brace placeholders (`{printer_name}`, `{filament_grams}`, `{eta}`, etc.); the schema is locked per-event so the editor warns when a placeholder doesn't resolve.

Templates are picked **per recipient language**: a Telegram chat owned by an operator with `settings.language=uk` gets the Ukrainian body; an email to a different user with `settings.language=en` gets the English one. Add new keys to **both** JSON files — BamDude ships en + uk only.

---

## :material-email-newsletter: Daily Digest example

When a provider has `daily_digest_enabled` + `daily_digest_time` set, every event that fires during the day is queued and bundled into one summary message at the digest time:

```
Daily Print Summary (Apr 14)

3 prints completed
1 print failed
Total time: 8h 45m
Filament used: 245g

Details:
- Benchy (2h 15m) - completed
- Phone Stand (45m) - completed
- Cable Clip (15m) - completed
- Prototype v3 (3h 30m) - failed
```

The digest message respects the same template language pick as immediate notifications — Telegram chats owned by uk-language operators get the Ukrainian summary, an English-language email recipient gets the English one.

---

## :material-file-document-edit: Message Template variables

Templates substitute `{variable}` placeholders. The schema is locked per event, so the template editor warns when an unknown placeholder is used. Variables are grouped by event category:

**Print events** (`print_start`, `print_complete`, `print_failed`, `print_stopped`, `print_progress`):

| Variable | Meaning |
|---|---|
| `{printer_name}` (alias `{printer}`) | Printer display name |
| `{print_name}` (alias `{filename}`) | The file currently printing |
| `{progress}` | Completion percentage (failed/stopped only) |
| `{eta_minutes}` / `{eta}` | Wall-clock completion time |
| `{estimated_time}` | Estimated print duration (e.g. `1h 23m`) |
| `{duration}` | Actual elapsed print time |
| `{filament_used_g}` (alias `{filament_grams}`) | Total grams (scaled by progress for failures) |
| `{filament_details}` | Per-spool breakdown (e.g. `AMS-A T1 PLA: 15.2g`) |
| `{material}` | Aggregate material name |
| `{reason}` | Failure reason (failed/stopped only) |
| `{finish_photo_url}` | Camera snapshot URL (see below) |

**Printer events** (`printer_offline`, `printer_error`):

| Variable | Meaning |
|---|---|
| `{printer_name}` | Printer display name |
| `{error_code}` (alias `{error_type}`) | HMS error code |
| `{error_message}` (alias `{error_detail}`) | Human-readable description (BamDude translates the 853-code catalogue) |

**AMS events** (`ams_humidity_high`, `ams_temperature_high`, `filament_low`, `print_missing_spool_assignment`):

| Variable | Meaning |
|---|---|
| `{ams_id}` | The AMS unit (`AMS-A`, `AMS-B`, …) |
| `{slot}` | Tray index (`T1`–`T4`) |
| `{material}` | Material assigned to the slot |
| `{remaining_percent}` | Filament left (`filament_low`) |
| `{humidity}` | Humidity percentage (humidity events) |
| `{missing_slots}` | Comma-separated slot labels (`A1, A3`) for `print_missing_spool_assignment` |
| `{missing_slot_details}` | Per-slot breakdown with expected profile (`- A1: PLA Basic`) |

**Common to every event:** `{timestamp}`, `{app_name}` (always `"BamDude"`).

Click **Reset to default** in the editor to restore the original template from `notification_templates_{en,uk}.json`.

### Finish Photo URL

The `{finish_photo_url}` placeholder embeds a camera snapshot link — useful in WhatsApp / email / webhook bodies that won't pull image attachments inline. It needs a reachable external URL to work:

1. **Settings** → **System** → **External URL** — set it to the address recipients can reach (e.g. `https://bamdude.example.com` or `http://192.168.1.100:8000`)
2. The setting auto-detects from your browser the first time you open System settings
3. Edit your template and add `{finish_photo_url}` wherever you want the link

!!! note "External URL prerequisite"
    Without a configured External URL the placeholder renders empty. Camera snapshots also gate on the [stream-token camera flow](authentication.md) — the URL embeds a short-lived token so recipients can fetch the JPEG without an Authorization header.

---

## :material-bell-off: Quick Disable

A global mute toggle lives in the sidebar — click the bell icon to drop **every** outgoing notification across **every** provider until you click again. Useful during maintenance windows, demo runs, or noisy migrations where you don't want to flood the team chat.

The toggle does not delete digests-in-progress — events that fired into the digest queue before mute still flush at the next `daily_digest_time`. To hold a digest, disable the daily-digest toggle on the provider instead.

---

## :material-printer: Per-Printer Filtering

Each provider has a **Printers** scope picker — select **All** to subscribe to every printer (default) or pin the provider to a subset. Events from printers outside the picked set never reach this provider, regardless of event toggles. Useful patterns:

- One Discord webhook per workshop — each scoped to that workshop's printers
- A "VIP printer" Telegram chat scoped to your one revenue-generating production unit
- A maintenance-only ntfy provider scoped to printers due for filter changes / belt swaps

---

## :material-account-bell: Per-User Email Notifications

Separate from the provider system above, BamDude can email the **owner** of a print directly when it completes / fails / stops — useful in shared / multi-tenant deployments where each user wants their own prints' mail in their personal inbox.

### Requirements

- Authentication enabled (it always is on 0.4.0+)
- SMTP configured under **Settings** → **System** → **Email**
- **Settings** → **Notifications** → **User Notifications** toggled on
- The user has an email address on their account
- The user holds the `notifications:user_email` permission (granted to **Administrators** + **Operators** by default — see [Authentication](authentication.md))

### Supported Events

| Event | Fires on |
|---|---|
| `user_print_start` | The user's print begins |
| `user_print_complete` | Their print finishes successfully |
| `user_print_failed` | Their print errored |
| `user_print_stopped` | They cancelled their own print |

The user can opt in/out of each event individually under their personal **Notifications** sidebar entry. Operators / admins control the global "User Notifications" master switch under **Settings** → **Notifications**.

---

## :material-bed: Bed-Cooled / Plate-Not-Empty quiet-hours bypass

Two events bypass quiet hours by default because they're action-required:

- **`plate_not_empty`** — caught a non-empty plate before a queue job started (auto-pauses dispatch). Sleeping through this means the queue stalls until you wake.
- **`bed_cooled`** — the bed dropped below your configured threshold (default 35 °C) after a print, signalling the part is safe to remove. Useful at any hour for high-volume operators.

The bypass is configurable per provider — open the provider's edit form and toggle **Bypass quiet hours** on the relevant event row if you'd rather have everything respect the window.

---

## :material-check-circle: Testing

Every provider has a **Send Test** button next to the save action. Clicking it fires a synthetic event through the full pipeline (template render, quiet-hour gate, priority mapping, transport-specific wrap) so the resulting message is a faithful preview of what real events will look like — not a stripped-down "hello world".

Re-test after editing templates, switching priorities, or changing transport-level fields like SMTP credentials. The test bypasses the digest queue (always sent immediately) so you don't have to wait until your digest time to see the result.

---

## :material-lightbulb: Tips

!!! tip "Start with ntfy"
    ntfy is the easiest provider to set up -- no account needed, just pick a topic name and subscribe on your phone.

!!! tip "Multiple Providers"
    You can configure multiple providers to receive notifications through different channels simultaneously.

> Originally based on [Bambuddy](https://github.com/maziggy/bambuddy) documentation.
