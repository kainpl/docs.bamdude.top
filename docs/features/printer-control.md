---
title: Printer Control
description: All the runtime control actions on a BamDude printer card
---

# Printer Control

Every printer card on the dashboard exposes the in-app equivalent of the buttons on the physical printer's touchscreen. This page is the catalogue: what each button does, which BamDude permission gates it, and which MQTT command actually goes out the wire.

---

## :material-information: What It Is

A printer card is a thin client that sits in front of `PrinterManager` (`backend/app/services/printer_manager.py`) and talks to the printer over MQTT through `BambuMqttClient`. The card surfaces:

- **Status** (idle / printing / paused / error) and live telemetry (temps, fans, AMS)
- **Print actions** (start / pause / resume / stop / clear plate / skip object)
- **Hardware controls** (chamber light, bed jog, full home, print speed, airduct mode)
- **Smart-plug actions** (power on / off via the bound plug)
- **Debug helpers** (force MQTT refresh)

Most actions are gated by `printers:control`. Two subsets carve off lower-privilege actions: `printers:clear_plate` (just the post-print "next job ready" handshake) and `printers:read` (status + object lists, no commands).

---

## :material-printer: Print Actions

### Start a print from the card

Drag a sliced `.gcode` or `.gcode.3mf` file onto a printer card or click the green **Print** button. The file is uploaded to your library, the print modal opens with that printer pre-selected, and the job is dispatched through the standard print queue.

The card also shows a red **"Printer busy"** overlay when you drop on a non-idle printer, so you don't accidentally interrupt a running job. See [Print Queue](print-queue.md) for what happens after the dispatch.

!!! note "Permission"
    `printers:control`. The library upload itself also checks `library:write`.

### Pause / Resume

| Button | When visible | Endpoint | What it sends |
|--------|--------------|----------|---------------|
| :material-pause: **Pause** | State = printing | `POST /api/v1/printers/{id}/print/pause` | MQTT `pause` |
| :material-play: **Resume** | State = paused | `POST /api/v1/printers/{id}/print/resume` | MQTT `resume` |

Both actions show a confirmation dialog to prevent fat-finger interrupts.

### Stop print

`POST /api/v1/printers/{id}/print/stop` — sends MQTT `stop` and **also** marks the printer as user-stopped in the dispatch tracking dict. That second step is important: without it the HMS heuristic in `_dispatch_archive_update` would later misclassify the cancel-sequence HMS code (e.g. H2D's module-`0x0C`) as a real "Layer shift" failure. Stopping a print cannot be undone — the print restarts from the beginning if you re-queue it.

### Skip object

For multi-object plates: skip a single object that's failing while letting the rest finish.

```
GET  /api/v1/printers/{id}/print/objects     → list objects with skip status
POST /api/v1/printers/{id}/print/skip-objects → skip selected IDs
```

The list comes from the active 3MF (`subtask_name`). If the in-memory object list is empty (e.g. after a backend restart), pass `?reload=true` and BamDude pulls the 3MF off the printer's FTP and re-parses it — supports multiple filename variants (`{name}.3mf`, `{name}.gcode.3mf`, with-spaces and underscored).

!!! warning "Wait for layer 2"
    The printer firmware refuses skip commands until the first layer is laid down. The skip modal shows a yellow banner on layer 0/1.

!!! tip "Match printer object IDs"
    The IDs shown in the BamDude modal match the IDs on the printer's touchscreen plate visualisation — that's how you identify which physical part is which.

### Clear plate

After a print finishes (or fails) and there are queued jobs waiting, the **Clear Plate & Start Next** button appears. Clicking it calls:

```
POST /api/v1/printers/{id}/clear-plate
```

This **does not send an MQTT command** to the printer — it just flips a server-side `awaiting_plate_clear` flag, which unblocks the queue scheduler so the next start command goes out. The printer accepts the new print and overrides its `FINISH` / `FAILED` state automatically.

Accepted printer states: `FINISH`, `FAILED`, **`IDLE`**. The IDLE case covers Auto-Off cycles — when the printer was powered off via smart plug after a job, the persisted `awaiting_plate_clear` flag is still set when it boots back into IDLE, and the operator still needs to acknowledge the cleared plate.

!!! note "Distinct permission"
    Clear-plate uses `printers:clear_plate` — a more granular permission than `printers:control`. You can grant a tech the ability to OK the next job without giving them stop / pause / chamber-light access.

### Clear HMS errors

`POST /api/v1/printers/{id}/hms/clear` — sends `clean_print_error` via MQTT and clears the HMS list from the card immediately. Useful after a cancel that left stale `print_error` codes behind.

---

## :material-arrow-up-down: Bed Jog (Z-Axis)

Move the build plate up or down by a fixed step.

```
POST /api/v1/printers/{id}/bed-jog?distance=N[&force=true]
```

| Param | Validation |
|-------|------------|
| `distance` | Non-zero, `|distance| <= 200` mm |
| `force` | If `true`, wraps the move in `M211 S0` … `M211 S1` to bypass soft endstops |

Step selector in the popover: `1 / 10 / 50 mm`. Only enabled when the printer is **not** running a print.

### G-code emitted

| Mode | Sequence |
|------|----------|
| Normal | `G91` → `G1 ZN F600` → `G90` |
| Force | `M211 S0` → `G91` → `G1 ZN F600` → `G90` → `M211 S1` |

### Not-homed warning

After a print completes, the Z axis usually isn't referenced. The first jog click in a session shows a Bambu-Studio-style modal:

| Choice | Action |
|--------|--------|
| **Home Z** | Sends `G28 Z` and dismisses the dialog — re-click jog after homing |
| **Move anyway** | Calls `bed-jog` with `force=true` (single-move soft-endstop bypass) and remembers the choice for the rest of the browser session |
| **Cancel** | Closes the dialog, no command sent |

!!! warning "Soft-endstop bypass"
    `force=true` disables soft limits for one move only. Keep distances small (≤10 mm) until the plate is in a known-safe position — the firmware still enforces hard physical limits, but it's on you to make sure the commanded move is sane.

---

## :material-home: Home Axes

```
POST /api/v1/printers/{id}/home-axes?axes={z|xy|all}
```

The `axes` parameter is **kept only for backward compatibility** — every call sends a bare `G28`, regardless of what you passed. The reason is upstream issue #1052: on H2C the bed homes by moving **up** toward the top endstop, and a bare `G28 Z` skips the toolhead-park step that a full `G28` runs first. The result was bed crashing into the toolhead. So BamDude unconditionally sends `G28` and lets the firmware run its safe park-XY-then-home-Z sequence.

Invalid `axes` values still return 400 so typos surface.

---

## :material-lightbulb-on: Chamber Light

```
POST /api/v1/printers/{id}/chamber-light?on={true|false}
```

Toggles the chamber LED via MQTT. Optimistic UI update on click, toast confirmation on round-trip success.

!!! info "H2D dual lights"
    On H2D, both chamber lights are controlled together — there's no per-light toggle in the firmware.

---

## :material-snowflake: Airduct Mode (P2S / X2D / H2 series)

Available only on printers with an active airduct (P2S, X2D, H2D, H2C, H2S). The card shows an airduct badge in the controls row; printers without an airduct hide it entirely.

| Mode | Icon | Use With |
|------|------|----------|
| **Cooling** | :material-snowflake: | PLA / PETG / TPU — filters and cools the chamber |
| **Heating** | :material-fire: | ABS / ASA / PC / PA — circulates and heats the chamber, closes top exhaust flap |

Switching mode goes out as the MQTT `set_airduct` command (`BambuMqttClient.set_airduct_mode`). The current mode is reflected back via `airduct.modeCur` in the printer's status push — the badge updates as soon as the printer confirms.

---

## :material-speedometer: Print Speed Presets

Change print speed mid-job without leaving the printer card.

```
POST /api/v1/printers/{id}/print-speed?mode=N
```

| Mode | Preset | Speed | Use For |
|------|--------|-------|---------|
| `1` | Silent | 50% | Night prints, noise-sensitive rooms |
| `2` | Standard | 100% | Default slicer speed |
| `3` | Sport | 124% | Simple geometry, time-pressure |
| `4` | Ludicrous | 166% | Maximum speed |

The badge in the controls row shows the current speed percentage and is dimmed when no print is active.

---

## :material-fan: Fan Status (display only)

Three live fan badges in the controls row: **Part Cooling**, **Auxiliary**, **Chamber**. They show real-time speeds (0–100%) reported by the printer.

!!! info "Read-only"
    Fan speeds are determined by the slicer profile and the printer firmware — BamDude shows them but doesn't expose a control.

---

## :material-power: Power Controls (smart plug)

If a [smart plug](smart-plugs.md) is bound to the printer:

| Action | What happens |
|--------|--------------|
| **Power On** | Plug turns on. The printer boots and reconnects to MQTT a few seconds later. |
| **Power Off** | Plug turns off. BamDude does **not** send an MQTT shutdown command — it just cuts power. |

Auto-power-off is configured per printer: after a print completes and the bed/nozzle drop below a configurable cooldown threshold for a configurable wait time, the bound plug is turned off. See [Smart Plugs](smart-plugs.md) for the threshold + wait-time fields and for the integration types (Tasmota / HA / REST / MQTT).

!!! warning "BamDude does not have a "soft shutdown" MQTT command"
    There is no MQTT command that cleanly shuts a Bambu printer down. Power-off goes through the smart plug. If you don't have one, the only way to shut down is the printer's own front-panel button.

---

## :material-refresh: Force Refresh (MQTT pushall)

```
POST /api/v1/printers/{id}/refresh-status
```

Asks the printer to re-broadcast its full status (MQTT `pushall`). Useful when a value on the card looks stale and you don't want to fully reconnect — full reconnect tears down the existing MQTT/FTP session and is slower. The endpoint is in the printer card's three-dot menu.

For a heavier reset, the **stop / start** of `printer_manager.ensure_fresh_connection_for_printer` runs automatically before any control command — that re-establishes a stalled MQTT connection without operator intervention.

---

## :material-checkbox-multiple-marked: Bulk Actions

Select multiple printer cards (Select-mode toolbar at the top of the printer page) and apply the same action to all of them at once. Smart-enabled buttons — only active when at least one selected printer is in the right state for that action.

| Bulk action | Required state | Permission |
|-------------|----------------|------------|
| Stop | At least one printing or paused | `printers:control` |
| Pause | At least one printing | `printers:control` |
| Resume | At least one paused | `printers:control` |
| Clear Notifications | Always | `printers:control` |
| Clear Bed | At least one in `FINISH` / `FAILED` / `IDLE` with `awaiting_plate_clear` | `printers:clear_plate` |

Selection helpers in the floating toolbar:

- **Select All** — every visible card
- **Select by State** — pick a state (Printing / Paused / Finished / Idle / Error / Offline) and select all cards in it
- **Select by Location** — only visible when at least one printer has a location set

Exit selection mode with **Esc** or the floating toolbar's **X**.

---

## :material-information-outline: Status Badges

Three small icon-only badges sit in the top status row of every card:

| Badge | Green | Red / Yellow | Notes |
|-------|:-----:|:------------:|-------|
| :material-sd: SD Card | inserted | red when missing | All printers |
| :material-door-closed: Door | closed | yellow when open | X1 / P1S / P2S / X2D / H2 series only |

Door state is decoded from the right MQTT field per printer family (X1: `home_flag` bit 23; others: `stat` bit 23) and pushed live over WebSocket — no waiting for the next status poll.

---

## :material-shield-account: Permission Matrix

| Action | Permission |
|--------|------------|
| Read status, AMS, object list | `printers:read` |
| Start / pause / resume / stop print | `printers:control` |
| Bed jog, home, chamber light, print speed, airduct, skip-object, clear-HMS | `printers:control` |
| Clear plate (acknowledge next job) | `printers:clear_plate` |
| Bind / unbind a smart plug | `printers:control` + `smart_plugs:write` |
| Add / remove printers, factory-reset, firmware push | `printers:admin` |

---

## :material-link: Related

- [Monitoring](monitoring.md) — the live status display these controls sit on top of
- [Print Queue](print-queue.md) — clear-plate handshake, dispatch flow
- [Smart Plugs](smart-plugs.md) — power on/off, auto-power-off thresholds, plug bindings
- [Macros](macros.md) — multi-step custom actions you can fire from the card menu
- [AMS](ams.md) — load / unload / calibrate
- [Notifications](notifications.md) — pause / stop / fail event routing

---

## :material-lightbulb: Tips

!!! tip "Confirm before bulk stop"
    Bulk Stop is irreversible. The toolbar shows a single confirmation for the whole batch — re-read the count before clicking through.

!!! tip "Skip beats stop"
    If one of eight objects on a plate fell off but the rest are fine, **Skip Object** keeps the print going. Stop loses everything.

!!! tip "Force MQTT refresh first"
    When a card looks stuck on a stale value, **Force Refresh** (pushall) is the cheapest fix. Restart the connection only if pushall doesn't help.

!!! tip "Auto-power-off needs a thermal cool-down"
    Don't set the cooldown threshold too aggressive — pulling power while the chamber is hot stresses ABS prints and can leave the toolhead warm with no fan running.
