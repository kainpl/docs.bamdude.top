---
title: Supported Printers
description: Compatibility information for Bambu Lab printer models
---

# Supported Printers

BamDude supports the Bambu Lab 3D printers listed below when Developer Mode is available.

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
| **X2D** | X2 | :material-check: | :material-check: |
| **A1** | A1 | :material-check: | AMS Lite |
| **A1 Mini** | A1 | :material-check: | AMS Lite |
| **A2L** | A2 | :material-check:[^a2l] | :material-check:[^a2l] |

BambuStudio `v02.08.04.57` also includes an **N8** model description. BamDude
recognizes its model name and code in the mirrored catalog, but N8 connection,
printing, and laser features have not been verified. It is therefore not in
the supported-model table or feature matrix yet.

---

## :material-printer-3d: Feature Highlights by Series

### X1 Series

- Active chamber heating on X1E; X1 and X1 Carbon have a chamber sensor but no active heater
- Up to 4 AMS units
- RTSP live camera support; frame rate depends on the printer and connection

### H2 Series

- H2D / H2D Pro: Dual nozzle with L/R nozzle status
- H2C: 6-slot tool changer nozzle rack
- Chamber heating

### P1 Series

- P1P requires add-on camera
- Up to 4 AMS units
- Low-frame-rate image camera

### A1 Series

- A1 and A1 mini: AMS Lite support, including slot configuration, filament routing and filament backup when enabled on the printer
- Both also support an external spool. A1 mini is a primary target for [swap mode](../features/swap-mode.md); swap mode does not mean the model lacks AMS support
- Low-frame-rate image camera

### X2 Series

- X2D: dual-nozzle with L/R nozzle status
- Ethernet port + RTSP camera (port 322)
- Steel-rod maintenance class

### A2 Series

- A2L: single FDM extruder — the second head is an integrated cutter/plotter, not a nozzle
- Wi-Fi only (no Ethernet), low-rate chamber-image camera on port 6000
- Linear-rail maintenance class

---

## :material-table-check: BamDude Capability Matrix

This table shows which BamDude features light up per printer series. Boxes
unchecked mean the hardware doesn't expose the data, the protocol bit is
unverified, or the model class doesn't apply — BamDude won't show fake
state in those cases.

| Capability | X1 | P1P | P1S | P2S / X2D | A1 | A1 Mini | A2L | H2D / H2D Pro | H2C | H2S |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| Camera (built-in) | :material-check: | add-on | :material-check: | :material-check: | :material-check: | :material-check: | :material-check:[^a2l] | :material-check: | :material-check: | :material-check: |
| RTSP live stream | :material-check: | — | — | :material-check: | — | — | — | :material-check: | :material-check: | :material-check: |
| Ethernet port [^network] | X1E only | — | — | X2D only | — | — | — | :material-check: | :material-check: | :material-check: |
| Active chamber heating | X1E only | — | — | X2D only | — | — | — | :material-check: | :material-check: | :material-check: |
| Door-open sensor (MQTT) [^door] | :material-check: | n/a [^opentop] | — | :material-check:[^door] | n/a [^opentop] | n/a [^opentop] | — | — [^bit23] | — [^bit23] | — [^bit23] |
| Dual nozzle (L/R) | — | — | — | X2D only | — | — | — | :material-check: | :material-check: | — |
| 6-slot tool changer | — | — | — | — | — | — | — | — | :material-check: | — |
| Four-slot AMS [^ams] | up to 4 | up to 4 | up to 4 | up to 4 | see note | see note | :material-check:[^a2l] | up to 4 | up to 4 | up to 4 |
| AMS Lite | — | — | — | — | :material-check: | :material-check: | — | — | — | — |
| External spool | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: |
| AMS-HT (single-slot 128–135) | — | — | — | — | — | — | — | :material-check: | :material-check: | :material-check: |
| AMS humidity / temperature notifications [^ams] | :material-check: | :material-check: | :material-check: | :material-check: | — with Lite | — with Lite | :material-check: | :material-check: | :material-check: | :material-check: |
| Maintenance — Carbon Rods | :material-check: | :material-check: | :material-check: | — | — | — | — | — | — | — |
| Maintenance — Steel Rods | — | — | — | :material-check: | — | — | — | — | — | — |
| Maintenance — Linear Rails | — | — | — | — | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: |
| Swap mode (push-off) [^swap] | — | — | — | — | :material-check: | :material-check: | — | — | — | — |
| Vibration-cali skip patcher | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: |
| Print-by-object skip | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: |

[^door]: BamDude reads `home_flag` bit 23 for X1 models and `stat` bit 23 for X2D/P2S. X2D was verified on hardware; P2S support uses the same interpretation and remains inferred. P1S has no door sensor. See `backend/app/utils/printer_models.py::door_sensor_field`.

[^opentop]: Open-frame printers physically have no door — there is nothing
to sense.

[^bit23]: The hardware sensor and a usable MQTT report are separate capabilities. BamDude does not show a door badge for these models until the correct telemetry field is verified.

[^ams]: AMS support does not imply every AMS feature. AMS Lite on **both A1 and A1 mini** supports filament feeding and slot management, including RFID identification of Bambu spools, but does not provide humidity readings or active drying. Other AMS variants and their available controls depend on the connected hardware, adapter and firmware; see [AMS settings](../features/ams.md). Humidity, temperature and drying controls require the corresponding reported capability.

[^network]: Ethernet is not implied by LAN mode. The manufacturer's [X1/X1C guide](https://cdn1.bambulab.com/documentation/quick-start-2024-01-17/Quick-Start-X1%26X1C_en.pdf), [P1S guide](https://cdn1.bambulab.com/documentation/quick-start-2024-01-17/Quick-Start-P1S_en.pdf) and [P2S guide](https://csm.bblcdn.com/hub/2ddc44d3a72443ba914efe0f963fbbc5.pdf) list wireless connectivity; [X1E](https://cdn1.bambulab.com/x1e/spec/Bambu%20Lab%20X1E%20Technical%20Specification.pdf) includes Ethernet.

[^swap]: Swap mode is officially supported on A1 series. Other models can
opt in by writing custom swap-mode G-code macros, but no factory profiles
ship for them.

[^a2l]: A2L is an emerging **single-extruder** model — its second head is an
integrated cutter/plotter, **not** a second nozzle. It is **Wi-Fi-only** (no
Ethernet port), exposes a **low-rate chamber-image camera** on port 6000 (no
RTSP / 30 FPS), and sits in the **linear-rail** maintenance class. Its AMS
support is inferred from the firmware's "print-while-drying" capability (which
requires a heated AMS); finer AMS details are still being confirmed against
real hardware.

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
