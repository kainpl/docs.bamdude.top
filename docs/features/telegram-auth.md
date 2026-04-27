---
title: Multi-Chat Auth
description: Per-chat authorization with roles, permissions, and registration
---

# Multi-Chat Authorization

BamDude's Telegram bot supports multiple chats with independent authorization, role-based permissions, and registration control.

---

## :material-shield-lock: Overview

Each Telegram chat (private or group) is linked to a BamDude group (role). This provides:

- **Per-chat permissions** -- Different chats can have different access levels
- **Notification routing** -- Each chat receives only the events it's subscribed to
- **Quiet hours** -- Per-chat quiet hour configuration
- **Registration control** -- Control how new chats are authorized

---

## :material-account-group: Chat Management

Manage Telegram chats in the web UI at **Settings > Notifications > Telegram Chats**.

### Chat Properties

| Property | Description |
|----------|-------------|
| **Chat ID** | Telegram chat identifier (auto-detected) |
| **Chat Name** | Display name |
| **Group** | BamDude group (role) assignment |
| **Notification Events** | Which events this chat receives |
| **Quiet Hours** | Time window to suppress notifications |
| **Daily Digest** | Receive a summary instead of individual messages |
| **Active** | Enable/disable the chat |

---

## :material-key: Permission Gating

The bot middleware checks permissions before executing commands:

1. User sends a command or taps an inline button
2. Middleware looks up the chat's group
3. Checks if the group has the required permission
4. Allows or denies the action

### Permission Examples

| Action | Required Permission |
|--------|:------------------:|
| View printers | `printers:read` |
| Control printers | `printers:control` |
| Start prints | `queue:create` |
| View queue | `queue:read` |
| Manage maintenance | `settings:update` |

---

## :material-account-plus: Registration: open vs. closed

A single boolean — `telegram_registration_open` (Settings → Notifications → Telegram) — controls how new chats appear:

| Setting | Behaviour |
|---|---|
| `telegram_registration_open=true` | Unknown chats that message the bot are auto-registered with `is_active=False, group_id=NULL`. They cannot do anything yet — an admin still has to assign a group and flip them active in **Settings → Notifications → Telegram Chats**. Effectively a "let me see who wants in" mode. |
| `telegram_registration_open=false` (default) | Unknown chats are silently rejected. To let a new chat in, an admin adds it manually in the web UI. |

There is no third "open with auto-active default group" mode — neither option auto-grants permissions. Activation is always a manual step in the web UI.

---

## :material-chat-processing: Auth Middleware

The auth middleware (`telegram_handlers/auth_middleware.py`) runs on every message and callback:

1. Checks if the chat exists in the `telegram_chats` table.
2. If new and `telegram_registration_open=true`: inserts a row with `is_active=False, group_id=NULL` and silently drops the message — the chat will only become functional after an admin activates + assigns a group in the web UI.
3. If new and `telegram_registration_open=false`: rejects the message outright.
4. Loads the chat's group and permissions.
5. Injects permissions into the handler context.
6. Handler checks required permissions before acting.

---

## :material-bell-ring: Per-Chat Notifications

Each chat can subscribe to different notification events:

- **Print events** -- complete, failed, progress
- **Queue events** -- added, started, waiting, complete
- **System events** -- printer offline, HMS errors, maintenance due

Configure in the web UI per chat.

---

## :material-lightbulb: Tips

!!! tip "Admin Chat"
    Set up a private chat with the Administrators group for full control, and a group chat with Viewers group for monitoring.

!!! tip "Quiet Hours"
    Set quiet hours per chat to avoid notifications during off-hours. The daily digest will summarize missed events.

!!! tip "Revoking Access"
    To revoke a chat's access, either delete it from the web UI or set it to inactive. The bot will stop responding to that chat.
