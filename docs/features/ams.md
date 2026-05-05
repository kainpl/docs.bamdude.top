---
title: AMS & Humidity
description: Monitor AMS filament systems, humidity, and remote drying
---

# AMS & Humidity Monitoring

BamDude provides comprehensive monitoring for your AMS (Automatic Material System) units.

---

## :material-tray-full: AMS Slot Status

Each AMS slot displays:

- **Filament color** -- Visual color swatch
- **Material type** -- PLA, PETG, ABS, etc.
- **Remaining** -- Estimated filament left
- **Active** -- Currently feeding indicator
- **Slot number** -- 1-based number with auto-contrast text

### RFID Re-read

Refresh filament information for individual slots by hovering and clicking the menu button. Useful when you've swapped a spool but the AMS hasn't detected the change.

### Configure AMS Slot

Manually configure slots for third-party filaments:

1. Hover over a slot, click the menu
2. Select **Configure Slot**
3. Choose a filament preset (filtered by printer model)
4. Select a matching K profile
5. Optionally set a custom color

!!! tip "AMS-HT preset stickiness fixed (#1053)"
    Earlier builds keyed AMS-HT slot presets at `ams_id * 4 + tray_id = 512`, but the frontend looks them up by `ams_id` directly for HT (single-slot units share their global tray id with the unit id). The slot fell through to the generic preset (`Generic PLA`) on every poll even after a custom preset was saved — so operators had to re-select it after every spool change. Backend now keys via the same helper the frontend uses, and the saved preset stays put.

### Pre-population for configured slots

When you open the Configure AMS Slot modal for a slot that already has a configuration, BamDude pre-populates the form so you can review or tweak without starting from scratch:

- **Filament preset** — the previously-configured preset is pre-selected (resolved from the saved mapping or by matching the slot's `tray_info_idx` to the corresponding preset).
- **Colour** — the colour picker is pre-populated with the slot's current filament colour, resolved against the [`color_catalog`](inventory.md#colour-catalog).
- **K-profile** — the active pressure-advance profile is pre-selected by matching the slot's `cali_idx` to the available [K-profile](kprofiles.md) entries.
- **Auto-scroll** — the preset list automatically scrolls to the selected entry so it's visible without manual scrolling. For empty slots the list scrolls to the last preset you used so common refills are one click away.

### Multi-AMS Support

Up to 4 AMS units per printer (16 total slots). External spool holders supported for printers without AMS.

### Assign Spool from Inventory

The AMS slot menu's **Assign Spool** option pairs a physical inventory row (from [Filaments](spoolman.md)) with the slot. The picker now includes:

- **RFID-detected spools** — Bambu Lab tags read on the slot.
- **Manually-added inventory rows without RFID** — refills, third-party brands, untagged spools (#1047). Earlier builds required exact `slicer_filament_name` equality and hid every spool that didn't carry a slicer profile name; the picker now also accepts partial-material match (a `PLA` spool shows up for a `PLA Basic` slot, and vice versa).
- **External slots (`amsId 254/255`)** — those have no RFID reader so the picker shows the full inventory.

!!! tip "Filter by slicer filament name"
    When a 3MF is loaded on the printer, the picker can be filtered by the slicer's expected filament profile (extracted from the active 3MF). Narrows the list to spools that match the print's required material — drops the chance of accidentally assigning a wrong spool. Toggle off the filter to see the full list, with a one-line warning when material doesn't match.

### Load / Unload from a slot

Drive **Load** and **Unload** directly from any AMS slot or external spool — no walk to the touchscreen:

1. Hover over the slot on the printer card.
2. Click :material-dots-vertical: in the slot's hover menu.
3. **Load** to feed the tray, **Unload** to retract whatever is currently loaded.

!!! note "Availability"
    The Load / Unload menu is hidden while the printer is `RUNNING` — wait for idle.

!!! info "H2D dual-extruder behaviour (Ext-L / Ext-R)"
    The H2D has two external spool positions — **Ext-L** (feeds left nozzle) and **Ext-R** (feeds right nozzle). Each is loaded against its own nozzle's actual current temperature (matches BambuStudio behaviour); a 215 °C fallback is used if the target nozzle reports cold or unknown.

!!! warning "Permission"
    Load / Unload requires the `printers:control` permission — same scope as start / stop / pause / resume.

### Custom AMS labels

Give your AMS units friendly names so you can tell them apart in multi-AMS setups.

1. Hover the AMS label (e.g. `AMS-A`) on the printer card → AMS info popover appears.
2. The popover surfaces:
   - **Serial Number** — the hardware serial reported over MQTT.
   - **Firmware Version** — parsed from the printer's `get_version` response.
   - **Friendly Name** — editable text field.
3. Type a name (e.g. *Silk Colours*, *Workshop AMS*) → press **Enter** or click **Save**. Clear the field + save to remove the label.

**Labels persist by AMS serial number, not slot position** — move an AMS between printers and the label follows it. If the AMS serial isn't reported (older firmware), BamDude falls back to a `(printer_id, ams_position)` key. Custom labels appear in the [Inventory](inventory.md) location column too, so finding spools across a print farm is one glance.

Editing labels requires the `printers:update` permission.

---

## :material-lan: AMS Discovery & Wiring

BamDude auto-discovers AMS units when a printer connects — no manual configuration. Updates flow in whenever the AMS configuration changes (a unit added / removed / re-cabled).

### Dual-nozzle wiring (H2D / H2D Pro)

On dual-nozzle printers each AMS unit is physically wired to either the left or right nozzle. BamDude shows the wiring diagram on the printer card so you can plan multi-material prints.

### Nozzle-aware filament mapping

When a 3MF assigns filaments to specific nozzles, BamDude constrains matching to AMS trays connected to the correct nozzle:

1. The 3MF carries `filament_nozzle_map` + `physical_extruder_map` in `project_settings.config`, mapping each filament slot to a target nozzle (`0` = right, `1` = left).
2. The printer reports `ams_extruder_map` over MQTT, indicating which AMS feeds which nozzle.
3. The matcher only considers trays on the correct nozzle — if no trays match, falls back to the full tray list.

The filament-mapping UI shows **L** / **R** badges next to each filament requirement so you can see at a glance which nozzle is involved. This applies to:

- The print scheduler's auto-mapping
- The reprint modal
- The Add-to-Queue modal
- Multi-printer selection (per-printer mapping for farms)

Single-nozzle printers (X1C, P1S, A1, A1-mini, P2S, etc.) skip the nozzle filter — every AMS tray is available.

### Filament Track Switch (FTS)

The Filament Track Switch is an external dual-nozzle accessory that sits between an AMS and the printer's extruders, dynamically routing any AMS slot to either nozzle. With FTS, the AMS is no longer wired to a single extruder.

BamDude detects the FTS via MQTT key `print.device.fila_switch` and **auto-suppresses the per-nozzle filter** in the print modal:

- **Without FTS** — each AMS feeds a fixed nozzle, dropdown only shows trays on the matching nozzle (prevents the *position of left hotend is abnormal* failure from cross-nozzle assignment).
- **With FTS** — every loaded slot is selectable for any nozzle, since FTS handles routing on the fly.

**Routing badges:** slots currently fed into a track display `[L]` or `[R]` next to the colour swatch and in the dropdown, indicating which extruder FTS is currently routing them to. Idle slots (not in any track) show no badge. Detection is automatic and re-evaluated on every MQTT push, so plugging in or removing the accessory updates the dropdown behaviour without a refresh.

---

## :material-water-percent: Humidity Monitoring

| Level | Status | Action |
|:-----:|--------|--------|
| < 20% | :material-check-circle:{ style="color: #4caf50" } Excellent | None needed |
| 20-40% | :material-check-circle:{ style="color: #8bc34a" } Good | None needed |
| 40-60% | :material-alert:{ style="color: #ff9800" } Fair | Consider drying |
| > 60% | :material-alert-circle:{ style="color: #f44336" } High | Replace desiccant |

Configure custom warning thresholds in **Settings** > **General**.

---

## :material-fire: Remote AMS Drying

Control AMS drying directly from BamDude for AMS 2 Pro and AMS-HT units — start, monitor, stop without touching the printer's screen.

### Supported hardware

Remote drying needs an AMS with an internal heater. The original AMS (no heater) can be monitored but not dried.

| AMS type | Module key | Max temperature | Drying support |
|---|:---:|:---:|:---:|
| AMS 2 Pro | `n3f` | 65 °C | :material-check: |
| AMS-HT | `n3s` | 85 °C | :material-check: (recommended for PA / PC / PVA) |
| AMS (original) | `ams` | — | :material-close: monitoring only |

### Printer firmware requirements

| Printer | Min firmware | Notes |
|---|:---:|---|
| X1 / X1C | 01.09.00.00 | |
| P1P / P1S | 01.08.00.00 | |
| H2D | 01.02.30.00 | |
| H2D Pro | any | No version gate |
| X1E | any | No version gate |
| P2S, A1, A1 mini | — | :material-close: not supported |
| H2S, H2C | — | :material-close: not supported |

For models not listed above (future hardware), BamDude lets the drying command through. If the printer's firmware doesn't support it, the call fails gracefully without side effects.

### Power supply requirements

AMS 2 Pro and AMS-HT need an external power supply (PSU) to run the heater. Without one, the AMS can monitor humidity but can't actively dry.

| Hardware | Idle draw | Drying draw | PSU recommendation |
|---|:---:|:---:|---|
| AMS 2 Pro × 1 | ~5 W | ~80 W | Bundled adapter is sufficient |
| AMS 2 Pro × 4 | — | ~320 W | Dedicated bench PSU; do **not** chain through the printer |
| AMS-HT × 1 | ~5 W | ~120 W (heating) | Bundled adapter |

The printer firmware reports power constraints via `dry_sf_reason` per AMS unit. BamDude reads these and disables the drying button with a "Power required" tooltip when any of the codes below are active. This applies to manual drying, queue auto-drying, and ambient drying — the scheduler skips AMS units with active reasons.

#### `dry_sf_reason` codes

| Code | Reason | Description |
|:---:|---|---|
| `0` | Task occupied | Printer is busy with another operation |
| `1` | Insufficient power | Too many AMS units drying simultaneously — disconnect others or add PSU |
| `2` | AMS busy | AMS is performing another operation |
| `3` | Consumable at outlet | Filament detected at AMS outlet |
| `4` | Initiating | Drying is already starting up |
| `5` | Not supported in 2D mode | Cannot dry in current mode |
| `6` | Already drying | Drying session already active |
| `7` | Upgrading | Firmware update in progress |
| `8` | Need plugin power | No external PSU connected — plug in the AMS power adapter |

!!! warning "PSU not connected (most common cause)"
    If the drying button is greyed out with a "Power required" tooltip, the most likely cause is `dry_sf_reason=8` — connect the external power adapter to your AMS unit.

### HMS error codes (AMS power)

Power-related issues also surface as HMS (Health Management System) errors in the printer's HMS panel. `XX` represents the AMS unit index (`00`–`07` for units A–H).

#### AMS 2 Pro range (`07XX_*`)

| HMS code | Description |
|---|---|
| `07XX_9200_0002_0003` | Heater fan 1 can't start — PSU not connected |
| `07XX_9300_0002_0003` | Heater fan 2 can't start — PSU not connected |
| `07XX_9800_0002_0001` | PSU voltage too low |
| `07XX_9800_0002_0002` | PSU voltage too high |

#### AMS-HT range (`18XX_*`)

| HMS code | Description |
|---|---|
| `18XX_2500_0002_0001` | Using printer power instead of dedicated adapter — connect the AMS-HT PSU |
| `18XX_9200_0002_0003` | Heater fan 1 can't start — PSU not connected |
| `18XX_9300_0002_0003` | Heater fan 2 can't start — PSU not connected |
| `18XX_9800_0002_0001` | PSU voltage too low |
| `18XX_9800_0002_0002` | PSU voltage too high |

### Starting a Drying Session

1. Click the :material-fire: flame icon in the AMS card header
2. Select filament type, temperature, and duration
3. Optionally enable spool rotation
4. Click **Start**

### Queue Auto-Drying

Automatically dry filament between scheduled prints when humidity exceeds the threshold.

- Enable in **Settings** > **AMS Display Thresholds** > **Queue Auto-Drying** (`queue_drying_enabled`).
- **Non-blocking** (default, `queue_drying_block=false`) — drying runs in the background; prints in the queue take priority.
- **Blocking** (`queue_drying_block=true`) — the queue stalls until drying completes. Use this when you really want a dry spool before the next print starts and don't mind the wait.
- Per-filament temperature + duration come from the configurable presets (Settings → AMS Display Thresholds → Drying Presets), not hard-coded defaults — AMS 2 Pro and AMS-HT have separate columns since they reach different temperatures.

#### Detailed flow

1. The scheduler watches every idle printer that has at least one **scheduled** queue item — items in pure "Queue Only" mode don't trigger auto-drying.
2. For each AMS unit, BamDude reads the live humidity over MQTT.
3. If humidity exceeds the **Fair (orange)** threshold from Settings, drying starts using the per-filament preset (see below).
4. Drying runs for a **minimum of 30 minutes** — even if humidity drops below the threshold sooner. This stops rapid start/stop cycling when humidity is right at the threshold.
5. After 30 min BamDude rechecks humidity each scheduler cycle; once at or below threshold, drying stops early.
6. When the next scheduled print is ready to run, any in-progress drying is stopped (non-blocking mode) and the print starts. In blocking mode the queue waits.

#### When auto-drying stops

- Humidity drops at or below the Fair threshold (only after 30 min minimum)
- A scheduled print is ready to start (non-blocking mode)
- The queue item's schedule is removed or flipped to "Queue Only"
- All scheduled items leave the queue
- Auto-drying is disabled in Settings
- The printer is powered off or disconnects

#### Conservative temperature for mixed AMS units

When a single AMS holds **multiple filament types** (e.g. PLA in slot 1 + PETG in slot 2), BamDude picks parameters that won't melt anything:

| Parameter | Rule | Why |
|---|---|---|
| **Temperature** | **Lowest** max-safe across all loaded filaments | PLA at 65 °C is mush — the run is bounded by the most heat-sensitive filament in the unit |
| **Duration** | **Longest** across all loaded filaments | Run long enough to dry the slowest-drying filament |

Worked example: AMS holds PLA + PETG → temperature = 50 °C (PLA cap), duration = 8 h (PETG default). Pure PETG would have used 65 °C / 8 h.

#### Requirements

- At least one **scheduled** queue item ("Queue Only" doesn't count)
- AMS 2 Pro or AMS-HT (original AMS has no heater)
- Supported printer firmware (see [Printer firmware requirements](#printer-firmware-requirements))
- Humidity above the Fair threshold
- No active `dry_sf_reason` codes (see [`dry_sf_reason` codes](#dry_sf_reason-codes))
- The printer is online and connected to BamDude

If you want drying to run without a scheduled print, see [Ambient Drying](#ambient-drying).

#### Configurable drying presets

Defaults are based on BambuStudio's official filament drying profiles. Edit them under **Settings → AMS Display Thresholds → Drying Presets**; changes auto-save and apply to manual drying, queue auto-drying, and ambient drying simultaneously.

| Filament | AMS 2 Pro temp | AMS-HT temp | AMS 2 Pro duration | AMS-HT duration |
|---|:---:|:---:|:---:|:---:|
| PLA | 50 °C | 50 °C | 8 h | 8 h |
| PETG | 65 °C | 65 °C | 8 h | 8 h |
| TPU | 65 °C | 70 °C | 12 h | 12 h |
| ABS | 65 °C | 80 °C | 12 h | 8 h |
| ASA | 65 °C | 80 °C | 12 h | 8 h |
| PA | 65 °C | 90 °C | 12 h | 16 h |
| PC | 65 °C | 80 °C | 12 h | 8 h |
| PVA | 65 °C | 85 °C | 12 h | 18 h |

!!! note "AMS 2 Pro temperature limit"
    AMS 2 Pro (`n3f`) caps at 65 °C in firmware. AMS-HT (`n3s`) caps at 85 °C. Setting a higher temperature in the preset is harmless — it's clamped to the hardware ceiling at command time.

### Ambient Drying

A separate path that doesn't depend on the queue. Enable under **Settings** > **Print Queue** > **Ambient Drying** (`ambient_drying_enabled`). On any idle printer where humidity is above the threshold, BamDude starts drying without setting a target temperature — useful as a 24/7 humidity-keeper for an idle farm.

---

## :material-chart-line: Historical Charts

Click humidity or temperature indicators to view historical data.

### Time ranges

| Range | Use case |
|---|---|
| **6 hours** | Recent trends — what just happened |
| **24 hours** | Daily pattern, day-night humidity swing |
| **48 hours** | Extended view — drying-cycle effectiveness |
| **7 days** | Weekly overview — shop-environment baseline |

### Chart features

- **Line chart of slot fill-level over time** — for inventory-tracked spools, the AMS history overlays remaining grams against humidity, so you can see how a sticky filament dried out (or didn't).
- **Min / max / avg statistics** for the selected range.
- **Threshold reference lines** at the Fair / High / Excellent boundaries — easy to see when humidity actually crossed the trigger.
- **Interactive tooltips** show exact value + timestamp on hover.
- **Zoom + pan** to drill into a specific incident.

---

## :material-database: AMS Data Retention

AMS humidity / temperature samples are persisted to the local DB for the historical charts.

| Setting | Default | Range |
|---|---|---|
| AMS data retention | **90 days** | 1–365 days |

Configure under **Settings → General → AMS Data Retention**. Older samples are pruned by the daily cleanup tick.

!!! warning "Storage impact"
    Longer retention means more rows in `ams_history` and a bigger DB. On a busy farm with 4× printers × 4× AMS × 4 slots updating every 30 s, 90 days is roughly 90 × 86400 / 30 × 64 = ~16 M rows — fine on SQLite WAL with the default page size, but worth keeping in mind if you bump the window way up.

---

## :material-lightbulb: Tips

!!! tip "Auto-Drying Between Prints"
    Enable queue auto-drying to keep filament dry during long print queues, or enable ambient drying for all idle printers.

!!! tip "Desiccant Maintenance"
    When humidity consistently stays high, replace or regenerate your desiccant packets.

> Originally based on [Bambuddy](https://github.com/maziggy/bambuddy) documentation.
