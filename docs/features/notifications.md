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

Both are configured **per provider**, not globally — a Discord channel can stay loud while your phone gets only a 9 a.m. summary.

| Setting | Where | Effect |
|---|---|---|
| `quiet_hours_enabled` + `quiet_hours_start` / `quiet_hours_end` | Provider config | Events that fire inside the window are dropped (not queued — quiet hours is "shut up", not "delay"). |
| `daily_digest_enabled` + `daily_digest_time` | Provider config | Events that fire any time in the day are queued in `notification_digest_queue`; the next time the wall clock crosses `daily_digest_time` BamDude flushes the queue as a single digest message. |

The Telegram chat list (Settings → Notifications → Telegram Chats) has the same pair of toggles per chat, plus a `notification_events` filter so each chat subscribes only to events it cares about.

---

## :material-file-document-edit: Template editor

Every event has a default template in `data/notification_templates_{en,uk}.json`. The Templates tab under Settings → Notifications lets you override any of them — title + body — with a MarkdownV2 toolbar and live preview.

Variable substitution uses simple curly-brace placeholders (`{printer_name}`, `{filament_grams}`, `{eta}`, etc.); the schema is locked per-event so the editor warns when a placeholder doesn't resolve.

Templates are picked **per recipient language**: a Telegram chat owned by an operator with `settings.language=uk` gets the Ukrainian body; an email to a different user with `settings.language=en` gets the English one. Add new keys to **both** JSON files — BamDude ships en + uk only.

---

## :material-lightbulb: Tips

!!! tip "Start with ntfy"
    ntfy is the easiest provider to set up -- no account needed, just pick a topic name and subscribe on your phone.

!!! tip "Multiple Providers"
    You can configure multiple providers to receive notifications through different channels simultaneously.

> Originally based on [Bambuddy](https://github.com/maziggy/bambuddy) documentation.
