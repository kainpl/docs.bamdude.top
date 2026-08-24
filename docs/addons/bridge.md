---
title: BamDude Bridge
description: Windows tray app that connects a workstation to BamDude — accepts sliced plates from Bambu Studio and drives USB label printers
---

# BamDude Bridge

A small desktop app that connects a **Windows workstation** to your BamDude server. BamDude usually runs in a container on another machine, so two things are structurally out of its reach: a file your slicer just wrote to the local disk, and a label printer plugged into a USB port. Bridge does those things on your machine and hands the result to the server over its normal HTTP API.

It is a **bridge, not a second product**: it holds no database and has no opinion about what your library contains. It lives in the system tray — closing the window hides it, left-click brings it back, and **Quit in the tray menu is the only real exit**.

[:material-download: Download from GitHub Releases](https://github.com/kainpl/bamdude-bridge/releases){ .md-button .md-button--primary }

---

## :material-download-box: Install

Two builds, same job:

| Build | What you get |
|---|---|
| **Installer** (`…-setup.exe`) | Start Menu entry, uninstaller, fetches the WebView2 runtime if missing |
| **Portable** (`…-portable.zip`) | Unpack anywhere and run. Settings and logs still live under `%APPDATA%` / `%LOCALAPPDATA%`; registering the slicer hand-off still touches the registry |

!!! warning "Unsigned binaries"
    Neither build is code-signed yet, so SmartScreen warns on first run: **More info → Run anyway**.

Bridge keeps itself current on both paths — the installed copy through the standard updater, the portable one through its own in-place update that never silently converts you to an installed copy.

## :material-lan-connect: Connect it to your server

In the settings window enter your **server URL** and an **API key**. The key needs two scopes:

- **Manage Library** — the slicer hand-off uploads plates into your library;
- **Print labels on a desk printer** — the label poller claims jobs and reports results.

The connection check does more than ping: it **proves the key can actually write**, so a wrong-scope key fails at setup time rather than at the first real hand-off.

!!! note "One identity per machine"
    Bridge mints an installation id on first run and your server ties the adopted label device to it. Wiping `%APPDATA%\BamDude Bridge` mints a new id — the server then sees a brand-new, un-adopted device and quietly stops handing it work until you adopt it again.

## :material-send: Role 1 — plates from Bambu Studio

Bambu Studio's **Send to Bambu Farm Manager Client** button hands a sliced plate to whatever app owns a specific URL scheme. Bridge registers itself as that receiver: the slicer exports a temporary 3MF, launches the URL, and Bridge uploads the file straight into your BamDude library.

- Registration is a **deliberate button in the settings window** — never something the installer does behind your back. If Bambu Lab's own farm client already owns the scheme, Bridge says so instead of silently taking over (a system has one handler per scheme — only one app can receive those files).
- Registering also adds a per-user autostart entry so a reboot doesn't break the hand-off; unregistering removes it.
- A successful hand-off pops a notification and **does not raise the window** — the slicer is in front of you. Only a failure brings the window up. The tray tooltip always carries the last outcome, and everything is logged, so a suppressed notification is never confused with a failed upload.

This integration is **Windows-only** — Bambu never implemented the hand-off for macOS.

## :material-label: Role 2 — label printers (Niimbot, USB)

The label role is **off unless you turn it on** — a Bridge installed only for the slicer hand-off never opens a serial port. Switch it on, pick the port, and Bridge reads the printer: model (and whether it is supported), firmware, serial, paper state, and what the cassette tag says — barcode, consumable type, usage.

From there it polls your server's label queue: BamDude renders the label to a 1-bit raster the moment you queue it (what you saw in the preview is what prints — even hours later), Bridge claims the job, prints, and reports back. See [Spool Labels](../features/labels.md) for the server side.

- **The device is adopted by a human, not by the key.** A freshly seen printer shows up on the server disabled; you enable it in **Settings → Filament → Marking**. An API key proves the bridge is yours — it does not decide that the printer behind it may receive your labels.
- **The template is the truth, the cassette is the gate.** A design prints at exactly its own size or is refused — never scaled: fractionally scaling a 1-bit raster silently breaks barcode ratios.
- **Out of paper pauses, it doesn't fail.** A job waits for you to drop a new roll in — that's a ten-second fix, not an error state.
- **Cassette sizes are asked once, server-side.** No Niimbot tag reports its size in millimetres; Bridge shows the barcode, and BamDude asks you once per cassette it hasn't seen. There is deliberately no size field in Bridge — a size that can be set in two places becomes two sizes.

!!! warning "The NIIMBOT desktop app holds the port exclusively"
    While it runs, nothing else can open the printer and the error is a bare "Access is denied". Close it first.

## :material-help-circle: Troubleshooting

??? question "The printer shows in Bridge but never prints anything"
    It is probably not **adopted** on the server yet — a new device arrives disabled by design. Enable it in **Settings → Filament → Marking** on the BamDude side.

??? question "Jobs queue up but nothing comes out"
    Check the paper state in Bridge — an empty roll parks the queue rather than failing it. Also make sure the NIIMBOT desktop app is closed.

??? question "\"Access is denied\" when opening the port"
    The NIIMBOT desktop app (or another program) holds the serial port exclusively. Close it and reconnect.

??? question "No notification appeared after sending from the slicer"
    Focus Assist can suppress notifications. The tray tooltip always shows the last hand-off outcome, and the log beside the settings records everything — including whether the notification was accepted.

??? question "After reinstalling Windows / clearing AppData the printer went silent"
    A fresh installation id means the server sees a new, un-adopted device. Adopt it again in **Settings → Filament → Marking**.
