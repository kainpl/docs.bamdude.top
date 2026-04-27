---
title: Telegram Bot Setup
description: Full printer control from Telegram with inline menus
---

# Telegram Bot

BamDude includes a built-in Telegram bot (aiogram 3.x) for full printer control, monitoring, and notifications directly from Telegram.

---

## :material-robot: Overview

The Telegram bot provides:

- **Printer status** -- View all printers with real-time status
- **Print control** -- Pause, stop, and resume prints
- **Camera snapshots** -- View live camera images
- **Speed control** -- Adjust print speed on the fly
- **Print from library** -- Browse and start prints from your file library
- **Queue management** -- View and manage the print queue
- **Calibration** -- Trigger printer calibration routines
- **Maintenance** -- View and mark maintenance tasks as complete
- **Statistics** -- View print statistics
- **Actionable notifications** -- Inline buttons on print complete, failed, progress

---

## :material-cog: Setup

### Step 1: Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the prompts
3. Choose a name and username for your bot
4. Copy the **bot token** provided by BotFather

### Step 2: Configure in BamDude

1. Go to **Settings** > **Notifications**
2. Add a **Telegram** notification provider
3. Paste the bot token
4. Enable the provider
5. The bot starts polling automatically

### Step 3: Authorize Your Chat

1. Open your bot in Telegram and send `/start`
2. The bot will register your chat
3. Go to **Settings** > **Notifications** > **Telegram Chats** in BamDude
4. Authorize the chat and assign a group (role)

!!! info "Bot Token Source"
    The bot token is read from the first enabled Telegram notification provider in the database.

!!! info "Per-message permission checks"
    Every command and inline-button press passes through `auth_middleware` before the handler runs. The middleware looks up the chat in `telegram_chats`, resolves its assigned group, and rejects the action unless the group holds the matching `resource:action` permission (e.g. `printers:control`, `archives:read`). Unauthorized chats see "У вас немає прав" / "You don't have permission" instead of executing the action.

---

## :material-message-text: Commands

The bot only registers a small set of slash commands; everything else is driven by the **reply keyboard** that `/start` sets up. Treat the keyboard buttons (📋 Printers / 🖨️ Queue / 📊 Stats / 📷 Camera / etc.) as the primary navigation — typing `/printers` or `/queue` won't match a handler and the bot will fall through to the unknown-command path.

| Command | Description |
|---------|-------------|
| `/start` | Register chat and show the main reply keyboard |
| `/help` | Show available commands |
| `/status` | Quick status of all printers |
| `/camera` | Camera snapshot picker |

---

## :material-view-grid: Inline Menus

The bot uses inline keyboard buttons for navigation instead of text commands:

- **Printer list** -- Tap a printer to see details, control, or camera
- **Print actions** -- Pause, stop, resume with confirmation
- **Speed presets** -- Quick speed adjustment buttons
- **Camera** -- Request a live snapshot
- **Calibration** -- Start bed leveling, vibration compensation, etc.
- **Queue** -- Paginated queue view with status indicators

---

## :material-image: Camera Snapshots

Request camera snapshots directly in Telegram:

1. Select a printer from the list
2. Tap **Camera**
3. A snapshot is sent as a photo message

---

## :material-book-open: Print from Library (Scene/FSM)

Start a print from your file library using an interactive flow:

1. Tap **Print from Library** in the main menu
2. Browse files with pagination
3. Select a file
4. Choose target printer
5. Confirm to print or add to queue

The flow uses aiogram's FSM (Finite State Machine) for multi-step interactions.

---

## :material-printer-3d-nozzle: Add Printer (Scene)

Add a new printer directly from Telegram:

1. Enter the printer's IP address
2. Enter the access code (8-digit code from the printer's network settings)
3. BamDude connects, auto-detects the printer model + serial, and adds it to the database
4. Confirm to add

!!! note "No mDNS auto-discovery"
    Telegram's add-printer scene asks for the IP + access code explicitly -- there is no automatic LAN discovery from inside the bot. Find the IP on the printer's screen (Settings > Network) before starting the flow.

---

## :material-bell-ring: Actionable Notifications

Notifications sent to Telegram include inline action buttons:

| Notification | Actions |
|-------------|---------|
| **Print Complete** | Clear plate |
| **Print Failed** | Clear plate |
| **Maintenance Due** | Mark done |
| **Print Progress** | Pause / Stop |

---

## :material-account-multiple: Multi-Chat Roles & Authorization

BamDude treats every Telegram chat (private *or* group) as an independent
identity with its own role. Add as many chats as you want — typical layouts:

- **Owner private chat** — `Administrators` group, gets every event.
- **Workshop group chat** — `Operators`, only print-lifecycle events.
- **Read-only viewer chat** — `Viewers` group, can browse status but cannot
  pause/stop prints.

The bot is **token-shared, role-isolated**: one bot user serves all chats, but
`auth_middleware` resolves the per-chat group on every keypress before letting
the handler proceed. A chat without a group (auto-registered, pending setup)
can read nothing and do nothing until an admin assigns one in
**Settings → Notifications → Telegram Chats**.

Optionally link a chat to a BamDude system user (`user_id`) for audit logging.
Linking does **not** override the group's permissions — the group is the
authority on what the chat can do.

---

## :material-bell-cog: Per-Chat Notification Preferences

Each Telegram chat has its own notification configuration, edited in
**Settings → Notifications → Telegram Chats → <chat>**. None of these
preferences leak between chats — set them once per chat.

### Event filter

Pick which of the 23 event types (`backend/app/models/telegram_chat.py::ALL_NOTIFY_EVENTS`) this chat should receive. The defaults mirror what most operators care about:

| Default events ON |
|---|
| `print_complete`, `print_failed`, `print_stopped`, `plate_not_empty`, `queue_job_waiting`, `queue_job_skipped`, `queue_job_failed` |

Everything else (`print_start`, `print_progress`, `printer_offline`,
`maintenance_due`, AMS humidity/temperature, queue lifecycle, etc.) is
opt-in. A workshop chat can subscribe only to `print_failed`; an admin
chat can subscribe to everything.

`should_notify(event_type)` runs on every notification: the chat must be
**active**, **outside quiet hours**, and the event must be in its enabled
list before a message is sent.

### Quiet hours

Suppress notifications during a daily window (e.g. 22:00 → 07:00). Both
same-day (`08:00 → 18:00`) and overnight (`22:00 → 07:00`) windows are
supported — the comparison wraps midnight automatically.

| Field | Purpose |
|-------|---------|
| `quiet_hours_enabled` | Master on/off toggle |
| `quiet_hours_start` | Start time, `HH:MM` (24-hour) |
| `quiet_hours_end` | End time, `HH:MM` (24-hour) |

Quiet hours apply to *all* events for this chat — there's no per-event
override. Pair with the event filter to keep critical events on while
silencing low-priority ones.

### Daily digest

Toggle `daily_digest` on a chat to additionally receive a once-per-day
summary message (yesterday's prints, failures, queue depth). The digest
respects quiet hours just like any other notification.

---

## :material-translate: Internationalization

All bot UI strings are translatable. Strings are stored in `backend/app/data/telegram_ui_{lang}.json` and accessed via `t(lang, "telegram_ui", "key")`.

Currently supported: English (en), Ukrainian (uk).

---

## :material-lightbulb: Tips

!!! tip "MarkdownV2 Formatting"
    All dynamic text sent by the bot uses Telegram's MarkdownV2 format. Special characters are automatically escaped via `escape_md()`.

!!! tip "Group Chat Support"
    The bot works in both private chats and group chats. Each chat is authorized independently with its own permissions.

!!! tip "Notification Routing"
    Different chats can receive different notification events. Configure per-chat notification events in the web UI.
