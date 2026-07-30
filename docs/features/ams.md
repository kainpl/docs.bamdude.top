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
3. Choose a filament preset (filtered by printer model **and by the nozzle
   actually installed**)
4. Select a matching K profile
5. Optionally set a custom color

The picker filters by the **nozzle diameter actually fitted**, not a fixed
0.4 mm. With a 0.6 mm nozzle you get the 0.6 mm profiles for your trays; on a
dual-nozzle H2D each AMS shows the profiles for the nozzle that feeds it.
Configuring a slot with a profile that doesn't match the installed nozzle is what
makes the printer reject a print with the cryptic *"Failed to get AMS mapping
table"* — the queue now catches that mismatch before uploading and fails the item
with an actionable message instead.

!!! success "Assignments are confirmed, not assumed"
    Assigning a spool from Inventory, or configuring a slot here, used to report
    success the moment the command was sent — whether or not the tray accepted
    it. A silently-dropped assignment never surfaced anywhere, and because a
    print only deducts from the spool on the exact tray it pulls from, it also
    recorded no filament usage.

    BamDude now reads the AMS telemetry back and tells you the outcome:
    **loaded** when the tray echoes the filament you assigned, a **warning** when
    the filament landed but its flow calibration (K-profile) didn't, and **not
    confirmed** if the tray hasn't reported it after about 30 seconds. If the
    printer goes quiet it stays silent rather than inventing a failure.

!!! tip "AMS-HT preset stickiness fixed (#1053)"
    Earlier builds keyed AMS-HT slot presets at `ams_id * 4 + tray_id = 512`, but the frontend looks them up by `ams_id` directly for HT (single-slot units share their global tray id with the unit id). The slot fell through to the generic preset (`Generic PLA`) on every poll even after a custom preset was saved — so operators had to re-select it after every spool change. Backend now keys via the same helper the frontend uses, and the saved preset stays put.

### Slots showing "?" instead of "Empty"

A spool with no readable RFID is reported by a standard AMS with no filament type
at all — structurally identical to a genuinely empty slot. BamDude uses the same
authoritative "a spool is physically here" signal Bambu Studio does, so:

- **"?"** — a spool is present but unidentified. Click **Configure Slot** to tell
  BamDude what's loaded.
- **Empty** — the slot really is empty.

### When a print pauses on a filament runout

The printer's own message says to reload *"the same AMS slot"*, which is wrong
whenever **AMS Filament Backup** is on: the firmware won't re-accept the depleted
slot and has already moved to the next compatible one.

BamDude reads the printer's target and previous slot during the pause and
highlights both on the AMS graphic — amber (with a small ↓ marker) on the slot
that needs filament, red on the slot that ran out — while the HMS error dialog
spells both out in words. Where the slot genuinely can't be pinned down (an
ambiguous multi-AMS layout) it says so and points you at the printer screen
rather than naming the wrong slot.

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

## :material-cog: AMS Settings Dialog

A per-printer dialog that mirrors **Bambu Studio → AMS Settings**. Click the :material-cog: gear icon in the **Filaments** section header on a printer card.

Toggle the same AMS-level behaviours Bambu Studio exposes — without leaving BamDude.

- **Insertion update** — read RFID automatically when you insert a new Bambu Lab spool (~20 s).
- **Power on update** — re-read RFID at printer startup (~1 minute, rolls spools).
- **Update remaining capacity** — let the AMS estimate how much filament is left on Bambu Lab spools.
- **AMS filament backup** — auto-switch to another spool with the same properties when the active one runs out.
- **Air printing detection** *(A1 / A1 Mini only)* — abort the print on clog / grind events to save time and material.
- **Calibrate AMS** — issues `M620 C<ams_id>` to one of the connected AMS units. Same routine as the printer-screen calibrate.
- **AMS Type** *(A1 only)* — switch the connected AMS between **FULL** and **LITE** firmware. Requires a printer-side firmware update (~30 s). Confirm dialog warns before sending.
- **Arrange AMS Order** *(H2D family)* — sends an `ams_reset` to clear the connected-AMS ID sequence; the printer expects you to then physically disconnect and reconnect units in the desired order.

### Visibility — what shows up depends on the printer

Each row is gated by what the printer actually supports — there's no point showing **AMS firmware type** on an X1C, or **air-print detection** on a P1S. BamDude resolves the per-printer capability table from the printer model code; rows whose capability is `false` are hidden entirely.

| Row | X1 family | P1 / P2 / X2D | A1 | A1 Mini | H2D family |
|---|---|---|---|---|---|
| Insertion update | yes | yes | yes | — | yes |
| Power on update | yes | yes | yes | — | yes |
| Update remaining capacity | yes | yes | yes | — | yes |
| AMS filament backup | yes | yes | yes | — | yes |
| Air printing detection | — | — | yes | yes | — |
| AMS firmware type | — | — | yes | — | — |
| Arrange AMS order | — | — | — | — | yes |
| Calibrate AMS | when ≥1 AMS connected, all models |

A1 Mini's AMS Lite has no RFID reader, so the four RFID-driven flags are not shown for it.

### State source of truth — the printer

BamDude does **not** persist a "desired state" on its side. The state shown in the dialog comes from the printer's MQTT push (`print.cfg` hex bitfield for the four main flags + `print.ams.*` for older firmware fallback). When you toggle a checkbox, BamDude publishes the matching MQTT command (`ams_user_setting` for the first three, `print_option` for backup / air-print, `M620 C<id>` for calibrate, `mc_for_ams_firmware_upgrade` for firmware switch, `ams_reset` for reorder) and starts a 3-second hold so the row doesn't flicker between optimistic and confirmed values.

If the printer drops a setting (factory reset, firmware update wipe), BamDude reflects that — there's no reconciliation. Open the dialog again and re-toggle.

### Permissions and audit

The gear icon only appears for users with the `printers:update` permission. The same permission gates the `POST /api/v1/printers/{id}/ams/settings` endpoint.

Every applied change writes one row to the `ams_setting_audit` table — `(printer_id, user_id, action, payload_json, sequence_id, result, error_message, created_at)`. No in-UI viewer yet; query the table directly if you need to answer "who turned RFID auto-read off last Thursday?"

!!! warning "Destructive actions"
    **AMS firmware type** and **Arrange AMS order** carry confirm dialogs because they're not pure toggles — firmware switch forces a ~30 s AMS reboot, and reorder invalidates the current AMS ID sequence (you must physically reconnect units afterwards). Read the confirm text before clicking through.

### AMS Filament Backup badge

The **Filaments** section header on each printer card carries a small **AMS Filament Backup** badge (:material-repeat:) so you can see the auto-switch state without opening the dialog:

| Badge | State |
|---|---|
| Green | Backup **on** — the AMS auto-switches to another matching spool on runout |
| Grey | Backup **off** |
| Faded grey | **Unknown** — the printer hasn't reported the flag yet |

Click the badge to jump straight to the AMS Settings dialog where the toggle lives (needs `printers:update`; otherwise it's read-only).

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

### Per-filament thresholds

The single Fair / High band above is a global default. You can also set **per-filament-type** auto-dry / alarm humidity thresholds under **Settings → Filaments** (`ams_humidity_thresholds`) — PLA, PETG, TPU, ABS, ASA, PA, PC, PVA, plus a `default` catch-all. When one AMS holds several materials, BamDude resolves to the **strictest (lowest)** threshold across all loaded spools, so the most moisture-sensitive filament in the unit sets the trigger. Empty slots contribute no constraint; unknown types fall back to `default`, then to the global Fair threshold.

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
| P1P / P1S | — | :material-close: **screen-only** — see below |
| H2D | 01.02.30.00 | |
| H2C | 01.02.00.00 | |
| H2D Pro | any | No version gate |
| X1E | any | No version gate |
| P2S, A1, A1 mini | — | :material-close: not supported |
| H2S | — | :material-close: not supported |

For models not listed above (future hardware), BamDude lets the drying command through. If the printer's firmware doesn't support it, the call fails gracefully without side effects.

!!! warning "P1P / P1S: drying can only be started at the printer"
    Bambu's own P1 manual is explicit — *"P1S connected AMS drying functions may only be controlled from the P1S screen."* The firmware accepts the drying command, answers **success**, and then discards it, which is why a P1S with an AMS 2 Pro would sit at zero dry status no matter how many times Start Drying was pressed.

    Since 0.4.7b4 BamDude no longer sends a command it can't fulfil. **The flame button stays on the card**, disabled, with a tooltip explaining that drying here is screen-only — the point is to learn *where* to dry, not to watch the control quietly disappear. A cycle you start at the printer still shows in BamDude with its live countdown, because reading the state was never the problem; only the Stop button is hidden, since a P1 ignores stop exactly as it ignores start. Queue auto-drying and ambient drying skip P1 printers for the same reason.

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

!!! note "You're told whether it actually started"
    A printer's acknowledgement only means the command was *taken*, not that the AMS began drying. You get a **"Drying command sent"** confirmation immediately, and if the unit hasn't actually started within 30 seconds — or reports an error — a warning says the printer accepted the command but the AMS never started drying.

    Each AMS is watched separately, so starting a cycle on a second unit doesn't lose the first one's result, and a unit still cooling down from a previous cycle isn't mistaken for one that just started.

!!! tip "Drying badge"
    While a cycle is active, the AMS card shows a **Drying** badge with the active filament and target temperature — e.g. *Drying · PETG @ 65°C* — alongside the time remaining, so you can see what's cooking at a glance. Bambu only echoes the drying time on later pushes, so BamDude caches the filament + target locally when it starts the cycle.

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

### Continue drying while printing

By default, drying only runs on **idle** printers — starting a print stops any active cycle. Turn on **Continue drying while printing** (`print_drying_enabled`, **Settings → Print Queue**, default **off**) to let auto-drying also fire *while a print is running*, so a humid spool keeps drying without stalling the queue.

This needs firmware that supports concurrent "Print While Drying". BamDude only offers it on:

| Model | Min firmware |
|---|:---:|
| H2D | 01.03.00.00 |
| H2C · H2S · P2S · H2D Pro | 01.02.00.00 |
| X2D · A2L | 01.01.00.00 |
| X1C | 01.11.02.00 |

A1, A1 Mini, P1P / P1S, X1 (non-C) and X1E are excluded — their firmware rejects the command mid-print anyway (`dry_sf_reason=0`, TaskOccupied).

!!! note "Temperature is capped mid-print"
    While a print is running, the drying temperature is capped **5 °C below the idle preset**, with a floor of **40 °C** — Bambu warns the drying temperature must stay below the filament's softening point during a print. Example: a PETG preset of 65 °C dries at 60 °C mid-print.

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
