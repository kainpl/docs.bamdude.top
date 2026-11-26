---
title: Notifications
description: Multi-provider push notifications for print events
---

# Notifications

Nine delivery channels, one editor, one routing config. Subscribe each provider to whichever events you actually want, set per-provider quiet hours and a daily digest, customise templates per language. And a tenth destination that never leaves the farm: the [notification centre](#the-notification-centre) behind the sidebar Bell, which fills for each person who logs in whether or not a single provider is configured.

---

## :material-bell-ring: Supported Providers

| Provider | Setup | Features |
|----------|:-----:|----------|
| **Telegram** | Medium | Via the BamDude bot, with actionable inline buttons (clear plate, mark maintenance done, pause/stop). Each Telegram provider routes only to its own authorised chats that subscribed to the event. |
| **Discord** | Easy | Channel webhook URL, embed formatting, image attachments. |
| **Email (SMTP)** | Medium | STARTTLS / SSL / plain. Per-provider `to_email` so different users see different bodies. |
| **Pushover** | Easy | Priority levels, image attachment up to 2.5 MB. |
| **ntfy** | Easy | Topic-based, optional bearer token, image attachments. |
| **Bark** | Easy | iOS-only, no account. Interruption levels — **Critical** delivers through Silent mode and Focus. Public relay or your own `bark-server`. |
| **CallMeBot** | Easy | WhatsApp / Signal bridge — phone + API key, URL-encoded message. |
| **Signal CLI API** | Medium | Self-hosted [signal-cli-rest-api](https://github.com/bbernhard/signal-cli-rest-api) — recipient numbers or one group, image attachments. |
| **Home Assistant** | Easy | `persistent_notification.create` or any `notify.*` service. Single global HA URL/token from Settings (or `HA_URL` / `HA_TOKEN` env). |
| **Webhook** | Flexible | Generic JSON or Slack-format POST, custom field names, base64 image, optional bearer token. |

---

## :material-plus-circle: Adding a Provider

1. Go to **Settings** > **Notifications**
2. Click **Add Provider**
3. Select provider type and enter configuration
4. Click **Send Test** to verify (all provider types except Telegram)
5. Configure event triggers
6. Click **Add**

For Telegram, save the bot first, add and activate a chat on that bot, then use **Send Test** on the saved provider card.

---

Every provider subscribes to events on its own, and the form offers all of them, grouped exactly as the notification centre groups them — print, printers, filament, AMS, queue, inventory, sensors. What you see ticked when you add a provider is what it will be saved with.

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

Pushover has one **Priority** per provider (`-2…+2`, `0` = normal), applied to everything that provider sends. Per-event priority is ntfy's alone (see below).

!!! info "Priority 2 (Emergency) needs two extra fields"
    Pushover *mandates* a retry interval and an expiry for Emergency alerts — they re-alert until you acknowledge them, so it refuses any priority-2 message that doesn't say how often and for how long. Set **Priority** to `2` and two fields appear:

    | Field | Meaning | Default |
    |---|---|---|
    | **Emergency Retry (s)** | How often Pushover re-alerts | 60 s (min 30 s) |
    | **Emergency Expire (s)** | When it gives up | 3600 s (max 10800 s) |

    They're only sent at priority 2 — Pushover ignores them at every other level.

### Bark (iOS)

[Bark](https://bark.day.app/) is a free iOS push app with no account at all — install it, copy the device key it shows you, paste it here. Nothing else is required.

| Field | Value |
|---|---|
| **Device Key** | The key the Bark app shows on its first screen — **required** |
| **Server** | `https://api.day.app` (default) or your own `bark-server` |
| **Group** | Optional — puts BamDude's notifications in their own group in the app |
| **Sound** | Optional — one of the sound names the Bark app lists |
| **Interruption Level** | `Default` / `Active` / `Time Sensitive` / `Critical` |

!!! tip "Critical is the reason to have Bark next to ntfy and Pushover"
    | Level | What iOS does with it |
    |---|---|
    | **Critical** | Delivered **through Silent mode and through Focus** — the print that stopped at 03:00 gets through |
    | **Time Sensitive** | Breaks through scheduled summaries, without going that far |
    | **Active** | A normal notification |
    | **Passive** | Arrives with no sound — recorded, not announced |

    Wire *print failed* and *filament runout* to a Critical Bark provider and leave everything else on a Default one, rather than making every event wake you.

A self-hosted `bark-server` is subject to the same address rules as a self-hosted ntfy: on your own network is fine, anything that is not a real HTTP service is refused. If it sits behind a Cloudflare challenge, BamDude says so instead of dumping the challenge page at you.

!!! info "An 'OK' that isn't one"
    `bark-server` reports some failures *inside* an HTTP 200 body. BamDude reads the body rather than trusting the status, so a wrong device key is reported as a failure in **Send Test** instead of showing as sent and never arriving.

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

Zero-config when HA is already wired up under **Settings** → **Network** → **Home Assistant** (or the `HA_URL` / `HA_TOKEN` env vars). Left empty, events become `persistent_notification.create` calls in your HA dashboard.

| Field | Value |
|---|---|
| **Service** | Optional — any HA service, e.g. `notify.mobile_app_myphone`. Accepted as `notify.x`, `notify/x` or `api/services/notify/x`. Empty = `persistent_notification.create` |
| **Data (JSON)** | Optional — a JSON **object** forwarded as HA's nested `data`, the same place an automation puts it |

The **Data** field is what makes an Android push behave. HA's mobile-app integration takes its options there, not in the title and message:

```json
{ "priority": "high", "ttl": 0, "channel": "BamDude" }
```

`priority: high` + `ttl: 0` are what make a notification arrive *immediately* rather than whenever the phone next wakes; `channel` gives printer alerts their own sound instead of burying them among everything else HA sends.

!!! info "Why JSON and not `key=value` lines"
    So `ttl: 0` stays the number HA expects, and so nested options are possible at all. It is validated when you save it **and** again when it is sent — a malformed field is refused in front of you rather than becoming a notification that quietly never arrives.

    Leave it empty and nothing changes: it is only sent when filled in, because `persistent_notification.create` rejects extra keys.

!!! tip "Forward HA notifications to other channels"
    Use HA automations to mirror these persistent notifications to the HA Companion app, Telegram, ntfy, etc. — gives you a single audit log in HA plus your usual mobile push.

### Signal CLI API

Signal messages through a [signal-cli-rest-api](https://github.com/bbernhard/signal-cli-rest-api) instance you host yourself. The provider is named for what it talks to: there is no official Signal API, and BamDude does not pretend to be one. Register a number with signal-cli first (that project's README walks through it); BamDude then sends from that number.

| Field | Value |
|---|---|
| **Signal API URL** | The base URL of your signal-cli-rest-api, e.g. `http://192.168.1.50:8080`. Pasting the full `/v2/send` endpoint from its docs is tolerated — BamDude strips it back to the base. |
| **Sender Number** | The number registered with signal-cli, in E.164 form (`+15551234567`) |
| **Recipient Type** | **Phone Numbers** — one or more recipients, added row by row — or **Group ID** — a single Signal group. signal-cli-rest-api cannot mix the two in one request, so a provider is one or the other; add a second provider if you want both. |
| **Group ID** | The group's id as signal-cli lists it; a bare id gets the `group.` prefix for you |
| **Authorization** | Optional — the `Authorization` header value when the API sits behind an authenticating reverse proxy (`Bearer …`, or just the token) |

Print-finish photos attach to the message. The URL is subject to the same address rules as a self-hosted ntfy or `bark-server`: your own network is fine, anything that is not a real HTTP service is refused.

Running BamDude in Docker with no signal-cli-rest-api yet? The shipped `docker-compose.signal.yml` runs one next to BamDude and `docker-install.sh` offers it — see [Docker → Signal notifications sidecar](../getting-started/docker.md#signal-notifications-sidecar).

---

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
    With **format = slack**, only `{"text": "..."}` is sent — structured event fields are dropped. An event that carries a picture adds it as a link (see [Photos in notifications](#photos-in-notifications)). Use the generic format for any automation that needs to read structured data; use slack only for human-readable channel posts.

---

## :material-tune: Event Triggers

Each provider subscribes independently. Toggling an event off on one provider doesn't stop it on others.

**Print:**

| Event | Fires when |
|-------|------------|
| `print_start` | Print starts on a printer |
| `first_layer_complete` | Layer 1 finishes (catch first-layer fails fast) |
| `pause_coming_up` | **Pause coming up** — a heads-up shortly before a pause added in the slicer. Off by default; see [below](#pause-coming-up). |
| `print_progress` | At 25% / 50% / 75% progress, counted from the first layer — nothing is sent while the printer is still heating or preparing, whatever percentage it reports — and every print starts over. A **minimum duration** floor can mute these for prints estimated shorter than N minutes — and the value belongs to each recipient: every Telegram chat carries its own (beside the Progress Milestones checkbox in the chat's settings) and every other provider carries its own (on its card, beside the same toggle). Empty or `0` = always send; there is no shared global value. The duration is estimated from the printer's own remaining-time report at each milestone, and an unknown estimate sends rather than guesses away. |
| `print_paused` | Printer transitioned RUNNING→PAUSE — body carries a normalised `{reason}` (door open / filament runout / presence-check / file-pause-command / AI defect / plate-objects / paused by user / HMS-other) plus the underlying `{hms_code}` for forensics. Default ON for new providers + included in the default Telegram-chat event set. |
| `print_resumed` | Printer transitioned PAUSE→RUNNING — body carries `{paused_for}` (mm:ss) computed from the matching pause edge. Default ON for new providers; opt-in for Telegram chats. |

The pause-state is also visualised on the Printers page in real time — a paused card surfaces a small `<PauseChip>` next to the status badge with the classified reason and a live mm:ss counter, plus a yellow warning pip in the corner. The chip disappears the moment the printer resumes; the resume event keeps the same `{paused_for}` value the notification body carries.

| `print_complete` | Print finishes successfully |
| `print_failed` | HMS error / hardware fault stopped the print |
| `print_stopped` | A person stopped the print — from the printer card, the queue, the Telegram bot, a webhook or the HMS dialog's **Stop Printing** |
| `print_outcome_unchecked` | **Result Not Checked** — a reminder that nobody has checked the result of a completed print. Off by default; see [below](#result-not-checked). |
| `bed_cooled` | Bed cooled to threshold (post-print cleanup signal) |

**AMS / filament:**

| Event | Fires when |
|-------|------------|
| `print_missing_spool_assignment` | Print started without complete spool→AMS mapping |
| `filament_low` | Spool remaining below `low_stock_threshold` (or the spool's own override). A spool bound to your inventory is checked when a print's consumption lands, right when it is put into a slot already below the threshold (assigned by hand, matched by its RFID tag, or loaded from stock automatically), and when its weight, label weight or own threshold is edited by hand while it sits in a slot — once per run-down, and only for a spool in a slot; a Spoolman-bound slot is checked on every AMS change, once per spool in a slot. A slot with no inventory binding is never judged by the printer's own counter — a spool without an RFID tag reports 0 %, which is no answer — so an unbound slot stays silent. |
| `ams_humidity_high` / `ams_temperature_high` | AMS exceeds its threshold |
| `sensor_above_max` / `sensor_below_min` | A [sensor](sensors.md) reading left the limits set for it |
| `sensor_back_in_range` | …and came back |
| `sensor_silent` / `sensor_speaking_again` | A sensor stopped reporting, and started again |

**Printer:**

| Event | Fires when |
|-------|------------|
| `printer_offline` | MQTT disconnect |
| `printer_error` | An HMS fault of severity Fatal or Serious appeared (BamDude includes the human-readable translation). Each fault is announced once per appearance — see [HMS notifications](monitoring.md#hms-notifications). A smart plug's [power alert](smart-plugs.md#power-alerts) arrives through this event too. |
| `ai_failure_detection` | AI failure detection (Obico or OctoEverywhere) flags a likely print failure — **opt-in, off by default**. Split out of `printer_error` so you can be paged on AI alerts without every HMS hardware code. It has its own template, its own per-provider toggle, and its own per-chat Telegram item; the body carries the printer, job name, the detector, its own measure — Obico's confidence score or OctoEverywhere's print quality, the other reads a dash — and the action BamDude took (notify / pause / pause + power off), and the notification carries the frame the detector flagged. |
| `plate_not_empty` | Bed-occupancy gate caught the next-print start (auto-pause). Carries the frame the check judged. |
| `maintenance_due` | Scheduled maintenance interval reached |

**Queue:**

| Event | Fires when |
|-------|------------|
| `queue_job_added` / `queue_job_started` / `queue_job_skipped` / `queue_job_failed` | Queue lifecycle events. Job added is announced after a successful operator action, once for a group of copies from the same add. Automatic assignment or return of existing AutoQueue work does not send another Job added notification. |
| `queue_job_waiting` | New actionable AutoQueue obstacles, aggregated once per routing pass. Ordinary busy printers stay silent; see [AutoQueue notifications](auto-queue.md#notifications-about-obstacles). Not sent to a provider or Telegram chat [limited to some printers](#per-printer-filtering). |
| `queue_completed` | The **entire install's** queues drain — fires only once every printer is idle with nothing pending. |
| `printer_queue_completed` | An **individual printer's own** queue drains — fires the moment that printer finishes its last pending job, regardless of what other printers are doing. |

!!! note "Global vs. per-printer queue completion"
    On a single-printer setup the two are equivalent. On a **multi-printer farm** they differ: `queue_completed` waits for *every* printer to go idle, so a long job on one printer suppresses it for all the others. `printer_queue_completed` fires per printer the moment that printer's own queue empties — pick this one if you want a "this machine is free, load the next plate" ping per printer. `printer_queue_completed` is **ON** by default for new providers; `queue_completed` is off by default.

**Inventory:**

| Event | Fires when |
|-------|------------|
| `stock_reorder_alert` | A filament has reached its reorder point in the stock forecast. |
| `stock_break_alert` | A filament will run out before a replenishment could arrive. |

Both are off by default on providers and Telegram chats. The message names the filament in full — material, subtype and **colour** — in its title and body, so Black and White of one product are two different messages. A filament is in one state or the other, and a break is the more urgent news: a recipient subscribed to both events gets the break message only, while a recipient subscribed to **reorder alerts only** gets the reorder message for a filament that is already in break. Nobody receives both for the same filament.

A filament whose every spool is archived is not running out — it ran out. Its row stays in the forecast for 90 days, but the alerts treat it differently:

- while the same material, subtype and colour is on the shelf under **another brand**, nothing is sent about it at all — the farm has simply moved to another brand;
- otherwise it is announced **once** as **Out of stock**, with its own text (template `stock_depleted_alert`), to exactly the recipients a stock break reaches. A stock break repeats once a day; a filament that ran out is not repeated. It is announced again only if it runs out again after a spool of it — of any brand — was back on the shelf.

If a colour is gone for good and you do not want even that one message, turn off alerts for its row in the Forecast view.

**User / system:**

| Event | Fires when |
|-------|------------|
| `user_created`, `password_reset` | Account-management emails (HTML + plain). |
| `user_print_start` / `user_print_complete` / `user_print_failed` / `user_print_stopped` | Per-user email notifications when the user owns the print. |
| `test` | Validation send from the provider editor. |
| `external_app_message` | Another program sent a message through the API — see [Messages from external apps](#external-app-messages). |

### Pause coming up { #pause-coming-up }

**Pause coming up** (`pause_coming_up`) warns that the running print is about to reach a pause added in the slicer — time to walk to the printer with the magnets, nuts or the next filament. It is about the same pauses the printer card shows as the [next slicer pause](monitoring.md#next-pause), and it only informs: nothing is sent to the printer.

- **Off by default everywhere** — on every provider, in every Telegram chat, and in the inbox subscriptions (it is an *info* event). Switch it on where you want it.
- **Once per pause per print.** A file with three pauses gives three messages, one before each. Printing the same file again is another print and is warned about again.
- **When it is sent** is the **Pause heads-up lead time** under **Settings → Printing**: 0–120 minutes, 5 by default. With a time estimate — Standard speed and a file with time markers — the event is sent once the estimate is at or below the lead time. Without one it is sent when the print reaches the layer before the pause. **0 switches the event off.**
- **After a restart of BamDude** a print that is found again already inside the lead time skips that one warning — it may have gone out before the restart, and no warning is ever sent twice.

The default message:

```
Pause Coming Up
Bambu X1C: Benchy
Pause at layer 42/250, in about 5 min
```

Without a time estimate the last part reads *on the next layer*.

### Result not checked { #result-not-checked }

**Result Not Checked** (`print_outcome_unchecked`) reminds that a completed print still carries its [**Not checked** mark](archiving.md#checking-a-prints-result) — nobody has recorded its defects or pressed **No defects**. It only informs: the print, its defect count and the queue are not touched.

- **Off by default everywhere** — on every provider, in every Telegram chat, and in the inbox subscriptions (it is an *info* event). Switch it on where you want it.
- **Once per print.** A reminder that could not be delivered is not sent again, and a print gets none once its result has been checked.
- **When it is sent** is the **Unchecked result reminder** under **Settings → Printing**: how many minutes a completed print may stay unchecked, 60 by default, from 5 minutes to a week (10080). The time counts from the moment the print finished.
- **Only completed prints.** A failed, cancelled or calibration print is never unchecked, so it is never reminded about.
- **Switching the event on later releases no backlog.** A print whose time has passed is settled whether or not anybody was subscribed at that moment.
- **In Telegram** the reminder carries **Defects…** and **No defects** buttons for that print, and a 👍 or 👎 reaction on it answers too — see [Telegram Bot → Actionable Notifications](telegram-bot.md#actionable-notifications).

The default message:

```
Print Result Not Checked
Bambu X1C: Benchy
Finished 2024-01-15 13:30. Nobody has checked the result yet.
https://bamdude.example/archives?outcome=unchecked
```

The link opens the Archives page with the **Unchecked** filter on; it is left out when no **External URL** is set under **Settings → Network**.

### Messages from external apps { #external-app-messages }

Another program of the farm — Home Assistant, a script, a bot — can tell the farm's people something through BamDude's channels: *the power is out*, *the dryer has finished*. It sends one request, and the message arrives as the **External App** event (`external_app_message`).

- **Who may send.** Only an API key created with **Send notifications as an external app** ticked (**Settings → API Keys**; off by default), whose owner is active and may manage notifications (`notifications:update` — Administrators and Operators have it). A signed-in browser cannot send these messages.
- **Who receives it.** Everybody's inbox shows it by default. Providers and Telegram chats receive it once **External App** is switched on for them — it is off for both by default. It is farm-wide news, so a provider limited to some printers receives it too.
- **Its level.** The sender chooses `info` (the default), `warning` or `error`. The level colours the message in the inbox and puts ℹ️, ⚠️ or 🚨 at the start of its title in the other channels.
- **Its sender is always shown** — the key's name and its owner: in the inbox on a line of its own (**From: Home Assistant · admin**), in the other channels as the last line of the message. Editing the template cannot remove it, so a program's message cannot pass for one of BamDude's own.
- **What may be sent.** Plain text: a title of up to 120 characters, a message of up to 2000, and optionally a link (`http` or `https` only), which the inbox shows as **Open link**. Control characters are dropped, and `*` is replaced so it cannot switch Telegram's bold text on.
- **How often.** 20 messages a minute per key. The next one is refused with `429` and a `Retry-After` header.

The request:

```http
POST /api/v1/notifications/external-message
X-API-Key: bd_…
Content-Type: application/json

{"title": "Power lost", "message": "The farm is on battery.", "level": "error", "link": "https://ha.local/lovelace/power"}
```

The answer says whom it reached — people whose inbox took it, and providers that were asked to send it: `{"inbox_recipients": 3, "channels": 2}`.

From Home Assistant, a `rest_command` and an action that calls it:

```yaml
rest_command:
  bamdude_message:
    url: "http://YOUR_BAMDUDE_IP:8000/api/v1/notifications/external-message"
    method: POST
    headers:
      X-API-Key: !secret bamdude_api_key
    content_type: "application/json"
    payload: '{{ {"title": title, "message": message, "level": level | default("info")} | to_json }}'
```

```yaml
action: rest_command.bamdude_message
data:
  title: "Power lost"
  message: "The farm is on battery."
  level: "error"
```

The default message in the other channels:

```
🚨 Power lost
The farm is on battery.
https://ha.local/lovelace/power

— Home Assistant · admin
```

---

## :material-send: Actionable Telegram Notifications

When using Telegram as a notification provider, BamDude sends actionable notifications with inline buttons:

| Event | Actions |
|-------|---------|
| **Print Complete** | Clear plate / Repeat print / Defects… / No defects buttons |
| **Result Not Checked** | Defects… / No defects buttons |
| **Maintenance Due** | Mark done button |
| **Print Progress** | Pause / Stop buttons |

See [Telegram Bot Setup](telegram-bot.md) for full configuration.

!!! tip "Per-chat event routing"
    Telegram notifications are not routed to a single hard-coded chat -- they are fanned out to every authorized chat whose `telegram_chats.notification_events` setting includes the firing event. So one chat can subscribe to "Print Complete" + "HMS Error" only, while another chat takes everything. Configure each chat's subscriptions under **Settings > Notifications > Telegram Chats**.

!!! tip "Localized templates per user"
    Notification bodies are rendered from `notification_templates_{en,uk}.json`. The template language is picked per-recipient -- Telegram uses the chat's owning user's `settings.language`, email uses the recipient user's language, etc. Adding a new template key means updating *both* `en` and `uk` JSON files (BamDude ships en + uk only).

---

## :material-priority-high: Per-event priority (ntfy)

ntfy supports priority levels from `1` (min) to `5` (urgent). BamDude lets you pick the priority **per event type** on each ntfy provider, so a finished print doesn't push to the lock-screen but a print failure does:

| Event type | Suggested ntfy priority | Why |
|---|---|---|
| `print_complete`, `bed_cooled` | `default` | Informational — read when convenient. |
| `print_failed`, `printer_error`, `plate_not_empty` | `high` or `urgent` | Action-required. |
| `filament_low`, `maintenance_due` | `default` | Plan-ahead, not interrupt-now. |
| `ams_humidity_high` | `high` | Affects filament you're about to use. |

Configure in the ntfy provider's edit form: the **Event priority (ntfy)** section lists the events the provider is subscribed to, each with its own dropdown. Every event starts at `default` (3) — escalate only where it matters. Pushover takes one priority for the whole provider instead (see [Pushover](#pushover)).

This is independent of the daily digest / quiet hours pipeline below — a quiet-hour-suppressed event isn't sent at any priority; an active event still respects the per-event priority you picked.

---

## :material-clock: Quiet hours & daily digest

Configuration shape varies by provider type — the Telegram bot is special.

**Non-telegram providers (email / ntfy / pushover / discord / webhook / homeassistant / callmebot / signal)** carry both settings on the provider row itself:

| Setting | Where | Effect |
|---|---|---|
| `quiet_hours_enabled` + `quiet_hours_start` / `quiet_hours_end` | Provider config | Events that fire inside the window are dropped (not queued — quiet hours is "shut up", not "delay"). |
| `daily_digest_enabled` + `daily_digest_time` | Provider config | Events that fire any time in the day are queued in `notification_digest_queue`; the next time the wall clock crosses `daily_digest_time` BamDude flushes the queue as a single digest message. The digest goes out at its time even inside the provider's quiet hours. |

**Telegram (m045)** is structured differently: the bot/provider row keeps only the **schedule** (`daily_digest_enabled` + `daily_digest_time`), while the per-event opt-in, quiet hours, and digest opt-in all live on each `TelegramChat` row. So one chat can be in quiet hours while another stays loud, both fed by the same bot. See [Telegram Bot Setup](telegram-bot.md) for the per-chat fields.

---

## :material-file-document-edit: Template editor

Every event has a default template in `data/notification_templates_{en,uk}.json`. The Templates tab under Settings → Notifications lets you override any of them — title + body — with a MarkdownV2 toolbar and live preview. Every template lists its variables and has a preview.

The Templates tab groups the default templates by purpose so a glance tells you which dispatch path each one feeds:

| Group | Count | What it's for |
|---|---|---|
| **Print events** | 13 | `print_start/complete/failed/stopped/paused/resumed/progress`, `plate_not_empty`, `bed_cooled`, `first_layer_complete`, `pause_coming_up`, `print_outcome_unchecked`, `print_missing_spool_assignment` |
| **Printer status** | 4 | `printer_offline`, `printer_error`, `filament_low`, `maintenance_due` |
| **AMS environmental** | 2 | `ams_humidity_high`, `ams_temperature_high` (also reused at runtime for the AMS-HT events) |
| **Sensor alerts** | 5 | `sensor_above_max`, `sensor_below_min`, `sensor_back_in_range`, `sensor_silent`, `sensor_speaking_again` — see [Environment Sensors](sensors.md) |
| **Print queue** | 7 | `queue_job_added/started/waiting/skipped/failed`, `queue_completed`, `printer_queue_completed` |
| **Job owner emails** | 4 | `user_print_start/complete/failed/stopped` — SMTP-only, sent to the print job owner |
| **System emails** | 2 | `user_created` (welcome), `password_reset` |
| **Test** | 1 | `test` — used by the "Send test" buttons |

Each card carries a small UPPERCASE channel badge:

- **Green `ALL`** — fan-out to every provider type that wants the event (TG / email / ntfy / pushover / discord / webhook / homeassistant / callmebot / signal). The entries in the first 4 groups.
- **Blue `EMAIL`** — SMTP-only flow. The 4 `user_print_*` job-owner emails plus `user_created` / `password_reset`.
- **Amber `TEST`** — internal test-button helper.

The mapping is metadata about which dispatch path consumes each template; it's not stored on the row, just rendered from a static lookup in the frontend.

Variable substitution uses simple curly-brace placeholders (`{printer_name}`, `{filament_grams}`, `{eta}`, etc.); the schema is locked per-event so the editor warns when a placeholder doesn't resolve.

Templates are picked **per recipient language**: a Telegram chat owned by an operator with `settings.language=uk` gets the Ukrainian body; an email to a different user with `settings.language=en` gets the English one. Add new keys to **both** JSON files — BamDude ships en + uk only.

---

## :material-email-newsletter: Daily Digest example

When a provider has `daily_digest_enabled` + `daily_digest_time` set, every event that fires during the day is queued and bundled into one summary message at the digest time:

```
Daily Digest - 5 Events

== Print Complete (3) ==
  09:12 [P1S-01] Print complete: Benchy
  11:40 [X1C-02] Print complete: Phone Stand
  14:05 [P1S-01] Print complete: Cable Clip

== Print Failed (1) ==
  16:31 [X1C-02] Print failed: Prototype v3

== Filament Low (1) ==
  13.04 22:48 [P1S-01] Low filament
```

Events are grouped by type, in the order they happened. Each line is the time, the printer in brackets when the event has one, and the title the event was sent with — so the lines are in the language of your templates, while the heading and the group names are fixed.

A digest that could not be sent keeps its events for the next attempt; events older than 48 hours are dropped unsent. An event carried over from an earlier day is listed with its date, not only its time.

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
| `{error_code}` (alias `{error_type}`) | HMS error code — the full four-group code (`0500-0600-0002-0070`) for a fault from the printer's HMS list, the short `XXXX_XXXX` form for a `print_error` |
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

**Pause heads-up** (`pause_coming_up`):

| Variable | Meaning |
|---|---|
| `{printer}` | Printer display name |
| `{filename}` | The file currently printing |
| `{layer}` | The layer the pause is on |
| `{total_layers}` | Total layers of the print |
| `{time_to_pause}` | A ready phrase: `in about 5 min`, or `on the next layer` when there is no time estimate |
| `{minutes}` | The estimate as a bare number; empty when there is no time estimate |

**Result not checked** (`print_outcome_unchecked`):

| Variable | Meaning |
|---|---|
| `{printer}` | Printer display name |
| `{filename}` | The print's name |
| `{finished_at}` | When the print finished, in the server's time zone (`2024-01-15 13:30`) |
| `{archive_url}` | Link to the Archives page with the **Unchecked** filter on; empty without an External URL |

**Inventory events** (`stock_reorder_alert`, `stock_break_alert`, and `stock_depleted_alert` — the text a filament that ran out is announced with):

| Variable | Meaning |
|---|---|
| `{filament}` | The filament the alert is about — material, subtype and colour in one name |
| `{material}`, `{subtype}`, `{color}` | The same three parts on their own |
| `{brand}` | Brand |
| `{stock_g}` | Stock left, grams |
| `{rate_g_day}` | Consumption rate, grams per day |
| `{days_left}` | Days of stock left |
| `{lead_time_days}` | Lead time in days (`stock_break_alert` and `stock_depleted_alert`) |

**External apps** (`external_app_message`):

| Variable | Meaning |
|---|---|
| `{title}` | The title the program sent |
| `{message}` | Its text |
| `{level}` | `info`, `warning` or `error` |
| `{level_icon}` | ℹ️, ⚠️ or 🚨 |
| `{link}` | Its link; empty without one |
| `{sender}` | The key and its owner — the code adds this line to every message anyway |

**Job owner emails** (`user_print_start`, `user_print_complete`, `user_print_failed`, `user_print_stopped`):

| Variable | Meaning |
|---|---|
| `{username}` | The print's owner |
| `{printer}` | Printer display name |
| `{filename}` | The printed file |
| `{finish_photo_url}` | Link to the finish photo (completed / failed / stopped; see below) |

**Common to every event:** `{timestamp}`, `{app_name}` (always `"BamDude"`).

Click **Reset to default** in the editor to restore the original template from `notification_templates_{en,uk}.json`.

### Photos in notifications

Events that have a camera frame carry it: the finish photo on print completion and failure, the first-layer snapshot, the frame the detector flagged on **AI Failure Detection**, the frame the check judged on **Plate Not Empty**, and a snapshot with a printer error.

- **Most channels receive the picture itself** — Telegram, Discord, Pushover, ntfy, Signal and generic-format webhooks. Email embeds the finish photo when its template uses `{finish_photo_url}` (see below).
- **Home Assistant, Bark and Slack / Mattermost-format webhooks receive a link** to a copy of that one picture, because these services fetch it themselves. Home Assistant gets it only with a custom `notify.*` service, as `data.image` — unless your **Data (JSON)** field sets its own `image`. Bark shows it as the notification's icon. This needs the **External URL** setting; without it these channels get text only.
- **Attach photos** — every channel has this switch, on by default. Off, that channel gets text only.

The copy a link points to has an unguessable address, needs nothing but the link to open, and stops working after 3 days. It opens that one picture only — not the archive and not a camera.

### Finish Photo URL

The `{finish_photo_url}` placeholder puts a camera snapshot of the finished plate into completion / failure notifications. It needs a reachable external URL to work:

1. **Settings** → **Network** → **External URL** — set it to the address recipients can reach (e.g. `https://bamdude.example.com` or `http://192.168.1.100:8000`)
2. The setting auto-detects from your browser the first time you open System settings
3. Edit your template and add `{finish_photo_url}` wherever you want the photo

!!! tip "Email inlines the photo, not just a link"
    For **email** providers, when the rendered body contains the substituted `{finish_photo_url}` **and** a finish photo was actually captured, BamDude sends the message as a `multipart/related` email with the JPEG embedded inline (via a `Content-ID` referenced from the HTML part) — the photo shows in the mail body itself, not as a bare link. The plain-text alternative still carries the clickable URL for text-only clients. When the template doesn't reference `{finish_photo_url}` (or no photo exists), the original single-part text email is used — no surprise attachment. Non-email channels (WhatsApp / webhook / …) still receive the link, which is why the External URL below has to be reachable.

!!! note "External URL prerequisite"
    Without a configured External URL the link has no address an outside service could reach. The link does not lead to the archive's own photo — that one needs sign-in like every other archive picture — but to a separate copy of that one photo, with an unguessable address, that stops working after 3 days. Whoever has the link can open the picture until then, so keep notification links private if the finished plate contains sensitive work.

!!! info "Start and completion delivery"
    A queued dispatch sends its start notification once per run, and finish-photo capture and completion delivery finish after the live print state is cleared. A camera failure can still leave a message without a photo. Starting a new print cancels the previous run's permission to capture the printer or perform delayed post-print actions.

---

## :material-bell-off: Quick Disable

A global mute toggle lives in the sidebar — click the bell icon to drop **every** outgoing notification across **every** provider until you click again. Useful during maintenance windows, demo runs, or noisy migrations where you don't want to flood the team chat.

The toggle does not delete digests-in-progress — events that fired into the digest queue before mute still flush at the next `daily_digest_time`. To hold a digest, disable the daily-digest toggle on the provider instead.

---

## :material-printer: Per-Printer Filtering

Each non-telegram provider has a printer scope — **All** (default), one, or any subset, ticked on the provider form. Events from printers outside the picked set never reach that provider, regardless of event toggles. **For Telegram the scope lives on each chat instead** (see [Telegram Bot → Printer scope](telegram-bot.md)), where it also scopes the bot itself — lists, cameras, queue and controls. Useful patterns:

- One Discord webhook per workshop — each scoped to that workshop's printers
- A "VIP printer" Telegram chat scoped to your one revenue-generating production unit
- A maintenance-only ntfy provider scoped to printers due for filter changes / belt swaps

News that names no printer is split in two. Farm-wide news — the whole farm's queue completing, stock alerts, test messages — still reaches every provider and chat, restricted or not. Two kinds do **not** reach a recipient limited to some printers:

- the **AutoQueue needs attention** summary (`queue_job_waiting`) — it describes the whole farm's obstacles and names no printer, so it goes to unrestricted providers, unrestricted Telegram chats and the inbox only;
- alerts of a **room or storage sensor** — one that stands on a location, not on a printer. An alert of a sensor placed on a printer follows that printer's scope.

A provider or chat that should receive these has to be left on **All** printers.

---

## :material-inbox: The notification centre

A notification does not have to leave the farm. The **Bell** in the sidebar opens a per-user notification centre with three tabs, and **the inbox fills whether or not a single provider is set up** — so an install with no provider at all still has somewhere to put an alarm about its own hardware. That is the point of it — providers are how a notification reaches your phone, the inbox is how it reaches whoever logs in.

Read and unread are **per person**. One operator opening an alarm does not clear it for anybody else. That is the difference between an inbox and a shared log: everyone subscribed to an event has to deal with it themselves.

### Inbox

The events you are subscribed to, newest first. Unread rows are marked; clicking a row marks it read and expands its full text. Every row carries:

| Shown on the row | What it tells you |
|---|---|
| Severity | **info**, **warning** or **error** |
| Printer | which printer the event came from |
| Age | how long ago it happened |

Four filters narrow the list — **severity**, **printer**, **unread only**, and the **period**: last 24 hours, last 7 days, last 30 days, or all time. A long history loads a page at a time behind a **Show more** button instead of all at once.

!!! warning "Mark all read and Clear act on the filter, not on the whole inbox"
    Both buttons apply to exactly what the filters currently select. With *error* + *one printer* + *last 7 days* picked, **Clear** deletes those rows and leaves everything else alone — and with no filters set at all, it deletes everything. **Clear** deletes; it asks for confirmation first. Single rows can also be deleted one at a time from the row itself.

### Subscriptions

A checkbox per event, grouped by area — print jobs, printers, filament, AMS, queue, inventory, sensors — each shown with the severity it carries, so you can see what a subscription will cost you before you tick it.

**By default a person receives warnings and errors only.** The inbox stays quiet unless something actually wants attention, and **Reset to defaults** puts it back to exactly that after any amount of experimenting. Every change saves immediately — there is no Save button to forget.

Subscriptions belong to the person, not to the farm: two operators on the same install can watch completely different things, and neither one's choices touch the other's inbox.

### Email

The four per-user e-mail switches — see [Per-User Email Notifications](#per-user-email-notifications) below for what they send and when.

The tab appears only when Advanced Authentication is on, the **User Notifications** master switch is on, and you hold the `notifications:user_email` permission.

### The unread badge

The sidebar Bell carries a live unread count. It updates over the WebSocket connection the rest of the interface already uses, so a new event lands on the bell without a page refresh and without polling for it. On narrow screens the compact header carries the same bell and the same badge.

### Permission

The notification centre requires the `notifications:inbox` permission.

!!! warning "Upgrade note — a custom group does not get it on its own"
    **Administrators**, **Operators** and **Viewers** all receive `notifications:inbox` on upgrade. A group you built yourself does **not** — an upgrade will not add permissions to a group somebody hand-made. Until an administrator grants it, that group's members lose the page entirely, **including the per-user e-mail switches they had before**. Walk your custom groups right after upgrading.

### Retention

**Settings** → **Data Management** carries **Inbox notifications (days)**.

| Setting | Default | Range |
|---|---|---|
| Inbox notifications | **30 days** | 1–365 days |

The daily cleanup removes anything older than the window, whether or not it was read — an inbox nobody opens does not grow forever. Deleting a user removes that user's inbox along with them.

---

## :material-email-outline: Per-User Email Notifications { #per-user-email-notifications }

Separate from the provider system above, BamDude can email the **owner** of a print directly when it completes / fails / stops — useful in shared / multi-tenant deployments where each user wants their own prints' mail in their personal inbox.

### Requirements

- Authentication enabled (it always is)
- SMTP configured under **Settings** → **Authentication** → **Email Authentication** (the **SMTP Configuration** card)
- **Settings** → **Notifications** → **User Notifications** toggled on
- The user has an email address on their account
- The user holds the `notifications:user_email` permission (granted to **Administrators** + **Operators** by default — see [Authentication](authentication.md))
- The user holds the `notifications:inbox` permission — the switches are a tab of the [notification centre](#the-notification-centre), and without it the page cannot be opened at all

### Supported Events

| Event | Fires on |
|---|---|
| `user_print_start` | The user's print begins |
| `user_print_complete` | Their print finishes successfully |
| `user_print_failed` | Their print errored |
| `user_print_stopped` | They cancelled their own print |

The print-finished e-mail shows the finish photo when one was taken, and the completed / failed / stopped templates can place it with `{finish_photo_url}`.

A print end that BamDude cannot match to a print of its own mails nobody: only the notification providers subscribed to the event are told.

Each user opts in and out of the four events individually on the **Email** tab of their own [notification centre](#the-notification-centre) — the Bell in the sidebar. Operators / admins control the global **User Notifications** master switch under **Settings** → **Notifications**.

---

## :material-bed: Getting an action-required event through the night

Some events stall the farm until somebody acts on them:

- **`plate_not_empty`** — a non-empty plate was caught before a queue job started, and dispatch is now paused. Sleeping through this means the queue stalls until you wake.
- **`bed_cooled`** — the bed dropped below your configured threshold (default 35 °C) after a print, so the part is safe to remove.
- The **sensor threshold alarms** — a room too cold or too damp for the filament that is printing in it.

!!! warning "Quiet hours are per provider, not per event"
    There is no per-event bypass. A provider inside its quiet window drops **everything**, including the three above — so a provider that is quiet from 22:00 will not tell you the queue stalled at 01:00.

    Route it instead: give the action-required events **their own provider** with quiet hours off, and leave the chatty ones (progress, print started) on the provider that does sleep. On iOS a [Bark](#bark-ios) provider at **Critical** is the strongest version of this — it comes through Silent mode and Focus as well.

The **daily digest** is a separate opt-in channel and never delays anything: every notification is sent when it happens, and the digest is an extra summary on top. It is sent at its configured time even inside the provider's quiet hours.

---

## :material-check-circle: Testing

Saved providers have a **Send Test** button. For ordinary providers, it fires a synthetic event through the full pipeline (template render, quiet-hour gate, priority mapping, transport-specific wrap) so the resulting message is a faithful preview of what real events will look like — not a stripped-down "hello world". Telegram uses its own active chats: its test is sent immediately to every active chat attached to that bot, regardless of that chat's event subscriptions, printer scope, or quiet hours. That verifies delivery to each recipient rather than simulating a farm event.

Re-test after editing templates, switching priorities, or changing transport-level fields like SMTP credentials. The test bypasses the digest queue (always sent immediately) so you don't have to wait until your digest time to see the result.

---

## :material-lightbulb: Tips

!!! tip "Start with ntfy"
    ntfy is the easiest provider to set up -- no account needed, just pick a topic name and subscribe on your phone.

!!! tip "Multiple Providers"
    You can configure multiple providers to receive notifications through different channels simultaneously.

> Originally based on [Bambuddy](https://github.com/maziggy/bambuddy) documentation.
