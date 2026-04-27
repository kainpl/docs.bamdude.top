---
title: First Printer Setup
description: Connect your first Bambu Lab printer to BamDude
---

# First Printer Setup

This guide walks you through adding your first printer to BamDude.

---

## :material-list-status: Prerequisites

Before adding a printer, ensure:

- [x] BamDude is running ([Installation](installation.md) or [Docker](docker.md))
- [x] Your printer is powered on and connected to your network
- [x] **SD card is inserted** in the printer
- [x] Developer Mode is enabled ([see guide](index.md#enabling-developer-mode))
- [x] You have the IP address, serial number, and access code

---

## :material-printer-3d-nozzle: Adding Your Printer

You can add a printer two ways: let BamDude **auto-discover** it on the LAN
(fastest), or fill in the IP / access-code / serial **manually**.

### Option A — LAN auto-discovery

1. Open BamDude → **Printers** → **:material-plus: Add Printer** →
   **Discover on LAN**.
2. Pick the discovery method that matches your install:

    === "Native install"

        BamDude listens for **SSDP** broadcasts. Bambu Lab printers
        announce themselves on the LAN every few seconds and show up in
        the discovery list automatically. Click **Start**, wait ~10
        seconds, then pick your printer from the list.

    === "Docker (host network)"

        SSDP works as long as the container is on `network_mode: host`
        (see [Docker → Host-mode compose](docker.md)). Same flow as
        native install.

    === "Docker (bridge network)"

        SSDP multicast doesn't cross the bridge, so BamDude switches to
        **subnet scan** instead. Enter your LAN's CIDR (e.g.
        `192.168.1.0/24`) and click **Scan** — BamDude probes every host
        for the Bambu MQTT/FTPS ports and lists every printer it finds.
        On a `/24` this finishes in under a minute.

3. Click your printer in the result list. BamDude pre-fills **IP** and
   **Serial** for you — only the **Access Code** is left to type.
4. Skip to *Step 3 — Save and Connect* below.

!!! info "Discovery permission"
    The discovery routes require the `discovery:scan` permission. The
    default **Administrators** and **Operators** groups have it; **Viewers**
    do not.

### Option B — Manual entry

Use this when discovery is unavailable (different VLAN, mDNS blocked,
locked-down environment) or you already have the printer's connection
details.

1. Open BamDude in your browser
2. Go to the **Printers** page
3. Click the **:material-plus: Add Printer** button
4. Choose **Enter manually**

### Step 2: Enter Printer Details

| Field | Description | Example |
|-------|-------------|---------|
| **Name** | A friendly name for your printer | `Workshop X1C` |
| **Model** | Pick the model from the dropdown (X1C, P1S, A1 Mini, H2D, …). BamDude uses this to enable model-specific features (door sensor, dual nozzle, AMS-HT) before MQTT confirms it. | `X1 Carbon` |
| **IP Address** | Your printer's local IP address (auto-discovery fills this) | `192.168.1.100` |
| **Access Code** | 8-character code from Developer Mode | `12345678` |
| **Serial Number** | Your printer's serial number (auto-discovery fills this) | `01P00A000000001` |

!!! tip "Model selection matters"
    BamDude derives several capabilities from the model — door-state
    detection, dual-nozzle UI, AMS-HT slot rendering, maintenance task
    filtering (carbon/steel rod vs. linear rail). Picking the wrong
    model will hide or surface the wrong features. Check the
    [capability matrix](../reference/printers.md#bamdude-capability-matrix)
    if you're unsure which class your printer falls into.

### Step 3: Save and Connect

1. Click **Save**
2. BamDude will attempt to connect to your printer
3. Wait for the connection indicator to turn green

---

## :material-cloud-outline: Bambu Cloud (optional, per-user)

Linking your Bambu account unlocks cloud-only features: firmware-update
checks, cloud filament catalog, slicer-setting profiles. Each BamDude
**user** stores their own cloud credentials — admins don't share their
Bambu account with operators or viewers.

1. Open **Settings → Cloud** while logged in as the user you want to link.
2. Pick the **region** — `global` (default, EU/US/AS) or `china`. The
   region maps to a different Bambu Cloud endpoint; the wrong choice
   results in `Login failed`.
3. Enter email + password. If 2FA is enabled on your Bambu account, you'll
   be prompted for the verification code next.
4. The token is stored encrypted on the user row. Other users on the same
   BamDude install do **not** see or share it.

!!! info "Auth disabled?"
    On installs where auth is disabled (rare — auth has been on by default
    since 0.4.0) the cloud token falls back to the global `Settings` table
    instead of per-user storage.

---

## :material-check-circle: Verifying Connection

A successfully connected printer shows:

| Element | Description |
|---------|-------------|
| :material-circle:{ style="color: #4caf50" } Green indicator | Connection is active |
| Live temperatures | Nozzle, bed, and chamber readings |
| HMS status | Health Management System shows "OK" |

---

## :material-alert-circle: Connection Issues?

1. **Is Developer Mode enabled?** Re-check both LAN Only Mode and Developer Mode
2. **Correct IP address?** Verify in printer network settings
3. **Access code fresh?** Codes change when Developer Mode is toggled
4. **Same network?** BamDude server and printer must be on the same LAN
5. **Firewall rules?** Ensure ports 8883 (MQTT) and 990 (FTPS) are open

See the full [Troubleshooting Guide](../reference/troubleshooting.md) for more.

---

## :material-printer-3d: Adding More Printers

Repeat the process to add additional printers. BamDude supports unlimited printers -- manage your entire print farm from one interface.

---

## :checkered_flag: Next Steps

<div class="quick-start" markdown>

[:material-archive: **Print Archiving**<br><small>How archiving works</small>](../features/archiving.md)

[:material-clock-outline: **Print Queue**<br><small>Schedule prints</small>](../features/print-queue.md)

[:material-bell-ring: **Notifications**<br><small>Get alerts on your phone</small>](../features/notifications.md)

[:material-robot: **Telegram Bot**<br><small>Control from Telegram</small>](../features/telegram-bot.md)

</div>

> Originally based on [Bambuddy](https://github.com/maziggy/bambuddy) documentation.
