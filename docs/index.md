---
title: Home
description: BamDude - Self-hosted 3D print farm management for Bambu Lab printers
hide:
  - navigation
  - toc
---

<style>
.md-typeset h1 { display: none; }
</style>

<div class="hero" markdown>

<div markdown>

# Your Farm.<br>Your Data.<br>Your Control.

**BamDude** is a self-hosted 3D print farm management system for Bambu Lab printers. Monitor your fleet in real-time, queue and schedule prints, automate workflows with macros, and control everything from a Telegram bot.

Hard fork of [Bambuddy](https://github.com/maziggy/bambuddy) with per-printer queues, swap mode, staggered start, Telegram bot, macros, maintenance history, and more.

<div class="stats-row" markdown>
  <span class="stat-badge" markdown>:material-printer-3d: Multi-Printer</span>
  <span class="stat-badge" markdown>:material-cloud-off-outline: Works Offline</span>
  <span class="stat-badge" markdown>:material-open-source-initiative: Open Source</span>
</div>

[Get Started :material-arrow-right:](getting-started/index.md){ .btn .btn-primary }
[View on GitHub :material-github:](https://github.com/kainpl/bamdude){ .btn .btn-secondary }

</div>

</div>

---

## :material-help-circle-outline: Why BamDude

BamDude is a **fleet manager**, not a passive backend that just listens to your slicer. The classic "slice → print → BamDude logs whatever it can" flow is fine for one or two printers, but it falls apart the moment accurate history and real spool control start mattering.

The fleet-first flow flips it: **slicer → BamDude → printers.** Hit Print in your slicer, route it to a BamDude virtual printer in File Manager mode, then in BamDude pick how many printers and how many copies. BamDude dispatches the file, runs swap macros, watches progress, writes history, and tracks every gram of filament — across the whole fleet, from one place.

[Read the full pitch :material-arrow-right:](why.md){ .md-button }

---

## :rocket: Quick Start

<div class="quick-start" markdown>

[:material-download: **Installation**<br><small>Get up and running in minutes</small>](getting-started/installation.md)

[:material-docker: **Docker**<br><small>One-command deployment</small>](getting-started/docker.md)

[:material-printer-3d: **Add Printer**<br><small>Connect your first printer</small>](getting-started/first-printer.md)

[:material-arrow-up-circle: **Upgrading**<br><small>Upgrade and roll back safely</small>](getting-started/upgrading.md)

</div>

---

## :sparkles: Features

<div class="feature-grid" markdown>

<div class="feature-card" markdown>
### :material-monitor-dashboard: [Real-time Monitoring](features/monitoring.md)
Live printer status via WebSocket, MJPEG camera streaming, HMS error tracking, and AMS humidity/temperature monitoring.
</div>

<div class="feature-card" markdown>
### :material-clock-outline: [Per-Printer Queues](features/print-queue.md)
Independent print queues per printer with drag-and-drop ordering, scheduled prints, staggered start, and swap mode for A1 Mini plate swappers.
</div>

<div class="feature-card" markdown>
### :material-archive: [Print Archive](features/archiving.md)
Automatic 3MF archiving with metadata extraction, 3D model preview, duplicate detection, and full-text search.
</div>

<div class="feature-card" markdown>
### :material-robot: [Telegram Bot](features/telegram-bot.md)
Full printer control from Telegram with inline menus, multi-chat authorization, role-based permissions, and actionable notifications.
</div>

<div class="feature-card" markdown>
### :material-code-braces: [Macros](features/macros.md)
G-code macros triggered by print events (start, end, pause). Built-in editor with per-printer and per-model configuration.
</div>

<div class="feature-card" markdown>
### :material-bell-ring: [Notifications](features/notifications.md)
Multi-provider alerts via Telegram, Discord, Email, Pushover, ntfy, CallMeBot (WhatsApp), Home Assistant, and custom webhooks. Per-provider quiet hours and daily digest.
</div>

<div class="feature-card" markdown>
### :material-cog-transfer: [Server-Side Slicing](features/slicer-api.md)
OrcaSlicer + BambuStudio sidecar containers, per-job slicer picker with reachability badges, bed-type override, inline multi-plate selection, owner-filter on preset dropdowns.
</div>

<div class="feature-card" markdown>
### :material-folder-multiple: [File Manager + Library](features/file-manager.md)
3MF / G-code / STL / STEP library with composite tag chips (format / readiness / modifiers / provenance), chip-row filter, per-plate gallery, 3D + G-code viewer with build-volume wireframe. Page-level drag-and-drop on File Manager + per-printer queue cards + the Auto-Queue panel.
</div>

<div class="feature-card" markdown>
### :material-source-branch: [Farm Auto-Queue](features/auto-queue.md)
One pool of work spread across the whole farm: jobs route to any printer whose loaded filament matches, with staggered starts, plate-clear gates and per-printer fallbacks.
</div>

<div class="feature-card" markdown>
### :material-power-plug: [Zigbee, With No Hub](features/smart-plugs.md)
BamDude drives the radio itself over USB or Ethernet — smart plugs and temperature / humidity sensors pair into a network it owns. No Home Assistant, no Zigbee2MQTT, no broker to keep alive.
</div>

<div class="feature-card" markdown>
### :material-lightning-bolt: [Energy and Cost per Print](features/energy.md)
Watt-hours captured against the archive of each print, with hourly snapshots behind the range figures and a dynamic tariff if your supplier publishes one.
</div>

<div class="feature-card" markdown>
### :material-palette-swatch: [Filament and Spools](features/inventory.md)
Spool inventory with usage tracking, colour resolution against a shared catalogue, printable labels, and two-way [Spoolman](features/spoolman.md) sync.
</div>

<div class="feature-card" markdown>
### :material-tune: [Calibration](features/filament-calibration.md)
Flow-rate and pressure-advance runs with the K-profiles they produce, plus device calibration — bed levelling, vibration, motor noise, nozzle offset — gated to what each model actually supports.
</div>

<div class="feature-card" markdown>
### :material-wrench-clock: [Maintenance](features/maintenance.md)
Per-printer service intervals counted in print hours, with what is due surfaced on the printer card and markable from the web or the bot.
</div>

<div class="feature-card" markdown>
### :material-printer-eye: [Virtual Printer](features/virtual-printer.md)
Send from the slicer to a printer that is not there: the file lands in the library as something you can browse, tag and print later, rather than in the archive.
</div>

<div class="feature-card" markdown>
### :material-shield-account: [Authentication](features/authentication.md)
Always on. Permission groups per user, TOTP and email 2FA, OIDC single sign-on, and scoped API keys for everything that is not a browser.
</div>

</div>

[Explore All Features :material-arrow-right:](features/index.md){ .md-button }

---

## :printer: Supported Printers

| Series | Models |
|--------|--------|
| **X1 Series** | X1, X1 Carbon, X1E |
| **H2 Series** | H2D, H2D Pro, H2C, H2S |
| **P1 Series** | P1P, P1S |
| **P2 Series** | P2S |
| **X2 Series** | X2D |
| **A2 Series** | A2L |
| **A1 Series** | A1, A1 Mini |

---

## :wrench: Tech Stack

<div class="feature-grid" markdown>

<div class="feature-card" markdown>
### Backend
:material-language-python: Python
:material-api: FastAPI
:material-database: SQLAlchemy + SQLite
</div>

<div class="feature-card" markdown>
### Frontend
:material-react: React
:material-language-typescript: TypeScript
:material-tailwind: Tailwind CSS
</div>

<div class="feature-card" markdown>
### Communication
:material-transit-connection-variant: MQTT over TLS
:material-folder-network: FTPS
:material-web: WebSocket
</div>

</div>

---

## :material-heart: Where this came from

BamDude grew out of a volunteer workshop. Its author volunteers with
[**DrukArmy**](https://drukarmy.org.ua/ua/about-us) — Ukraine's largest volunteer 3D-printing effort
for the front line — printing, and running the FPV direction as senior curator.

Batches, deadlines and a farm that has to keep moving around the clock do not fit any off-the-shelf
tool, so every feature here earned its place on a real order first. That is also why Ukrainian is a
first-class locale rather than an afterthought.

[:material-account-plus: Join DrukArmy](https://app.drukarmy.org.ua/inv/ujnv7w8i){ .md-button }

## :material-handshake: Partners

<div class="grid cards" markdown>

-   ![DrukArmy](assets/partners/drukarmy.png){ width="64" style="background:#fff;border-radius:12px;padding:6px;float:right;margin-left:12px" }

    **[DrukArmy](https://drukarmy.org.ua/ua)**

    ---

    Ukraine's largest volunteer 3D-printing community, printing for the front line. BamDude was born in this workshop — and if you have a printer, there is useful work waiting for it.

    [:material-account-plus: Join DrukArmy](https://app.drukarmy.org.ua/inv/ujnv7w8i)

-   ![Dragons of Defense](assets/partners/dragons.png){ width="64" style="border-radius:12px;float:right;margin-left:12px" }

    **[Dragons of Defense](https://dragons.in.ua/)**

    ---

    A volunteer 3D-printing initiative: a 24/7 print farm making plastic gear for Ukraine's defense forces, with fully transparent finances — everything public, counted automatically.

    [:material-open-in-new: dragons.in.ua](https://dragons.in.ua/)

-   ![AdditHub](assets/partners/addithub.png){ width="64" style="background:#fff;border-radius:12px;padding:6px;float:right;margin-left:12px" }

    **[AdditHub](https://addithub.com/)**

    ---

    Ukraine's #1 3D-printing marketplace: post a job and verified makers place blind bids — FDM, SLA and SLS printing, 3D modelling and post-processing.

    [:material-open-in-new: addithub.com](https://addithub.com/)

</div>

## :material-hand-heart: Support the project

BamDude is free and stays free — AGPL-3.0, no paid tiers, no pro edition. The most valuable support
is a bug report, a translation PR or a star on GitHub. If you would rather chip in:

| | |
|---|---|
| **Monobank jar** | [send.monobank.ua/jar/2vREyf3SrF](https://send.monobank.ua/jar/2vREyf3SrF) |
| **PayPal** | `pushkar.valeriy@gmail.com` |
| **USDT (TRC20)** | `TWe1MaXz7mpDZZqDkY7Az7NdZ6s9H5fvMF` |

---

<div style="text-align: center; margin-top: 3rem;" markdown>
<span style="opacity: 0.6;">Made with :heart: for the 3D printing community</span>
</div>
