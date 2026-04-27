---
title: Supported Printers
description: Compatibility information for Bambu Lab printer models
---

# Supported Printers

BamDude supports all Bambu Lab 3D printers with Developer Mode capability.

---

## :material-check-circle: Supported Models

| Model | Series | Camera | AMS |
|-------|--------|:------:|:---:|
| **X1** | X1 | :material-check: | :material-check: |
| **X1 Carbon** | X1 | :material-check: | :material-check: |
| **X1E** | X1 | :material-check: | :material-check: |
| **H2D** | H2 | :material-check: | :material-check: |
| **H2D Pro** | H2 | :material-check: | :material-check: |
| **H2C** | H2 | :material-check: | :material-check: |
| **H2S** | H2 | :material-check: | :material-check: |
| **P1P** | P1 | Add-on | :material-check: |
| **P1S** | P1 | :material-check: | :material-check: |
| **P2S** | P2 | :material-check: | :material-check: |
| **A1** | A1 | :material-check: | AMS Lite |
| **A1 Mini** | A1 | :material-check: | :material-close: |

---

## :material-printer-3d: Feature Highlights by Series

### X1 Series

- Chamber heating
- Up to 4 AMS units
- Full camera support (up to 30 FPS)

### H2 Series

- H2D / H2D Pro: Dual nozzle with L/R nozzle status
- H2C: 6-slot tool changer nozzle rack
- Chamber heating

### P1 Series

- P1P requires add-on camera
- Up to 4 AMS units
- Camera limited to ~5 FPS

### A1 Series

- A1: AMS Lite support
- A1 Mini: External spool only, primary target for [swap mode](../features/swap-mode.md)
- Camera limited to ~5 FPS

---

## :material-table-check: BamDude Capability Matrix

This table shows which BamDude features light up per printer series. Boxes
unchecked mean the hardware doesn't expose the data, the protocol bit is
unverified, or the model class doesn't apply — BamDude won't show fake
state in those cases.

| Capability | X1 | P1P | P1S | P2S / X2D | A1 | A1 Mini | H2D / H2D Pro | H2C | H2S |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| Camera (built-in) | :material-check: | add-on | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: |
| 30 FPS stream | :material-check: | — | — | — | — | — | :material-check: | :material-check: | :material-check: |
| Ethernet port | X1C/X1E only | — | :material-check: | :material-check: | — | — | :material-check: | :material-check: | :material-check: |
| Chamber heating | :material-check: | — | passive | :material-check: | — | — | :material-check: | :material-check: | :material-check: |
| Door-open sensor (MQTT) [^door] | :material-check: | n/a [^opentop] | — [^bit23] | — [^bit23] | n/a [^opentop] | n/a [^opentop] | — [^bit23] | — [^bit23] | — [^bit23] |
| Dual nozzle (L/R) | — | — | — | — | — | — | :material-check: | — | — |
| 6-slot tool changer | — | — | — | — | — | — | — | :material-check: | — |
| AMS Pro (4-slot) | up to 4 | up to 4 | up to 4 | up to 4 | — | — | up to 4 | up to 4 | up to 4 |
| AMS Lite | — | — | — | — | :material-check: | — | — | — | — |
| External spool | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | only | :material-check: | :material-check: | :material-check: |
| AMS-HT (single-slot 128–135) | — | — | — | — | — | — | :material-check: | :material-check: | :material-check: |
| AMS humidity / temperature notifications | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: [^lite] | — | :material-check: | :material-check: | :material-check: |
| Maintenance — Carbon Rods | :material-check: | :material-check: | :material-check: | — | — | — | — | — | — |
| Maintenance — Steel Rods | — | — | — | :material-check: | — | — | — | — | — |
| Maintenance — Linear Rails | — | — | — | — | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: |
| Swap mode (push-off) [^swap] | — | — | — | — | :material-check: | :material-check: | — | — | — |
| Vibration-cali skip patcher | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: |
| Print-by-object skip | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: |

[^door]: Door-state is parsed from `home_flag` bit 23 on MQTT. Only X1 family
firmware has been reverse-engineered to publish a trustworthy value;
non-listed enclosed models report a permanently-zero bit on observed
firmware, so BamDude refuses to show a misleading "Door closed" badge for
them. See `backend/app/utils/printer_models.py::DOOR_SENSOR_MODELS`.

[^opentop]: Open-frame printers physically have no door — there is nothing
to sense.

[^bit23]: Enclosed model whose `home_flag` bit 23 has not been confirmed to
flip. Will be enabled once verified against a real printer; do not request
on speculation.

[^lite]: AMS Lite reports humidity but not the AMS-HT sub-stream.

[^swap]: Swap mode is officially supported on A1 series. Other models can
opt in by writing custom swap-mode G-code macros, but no factory profiles
ship for them.

---

## :material-connection: Connection Requirements

All printers require:

- **Developer Mode** enabled (provides LAN access)
- **SD card** inserted (for file transfers)
- **Same network** as BamDude server

| Port | Protocol | Purpose |
|------|----------|---------|
| 8883 | MQTT/TLS | Printer communication |
| 990 | FTPS | File transfers |

> Originally based on [Bambuddy](https://github.com/maziggy/bambuddy) documentation.
