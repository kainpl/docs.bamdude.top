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
    `printers:control`. The library upload itself also checks `library:upload`.

### Nozzle Offset Calibration (dual-nozzle only)

On the **H2D, H2D Pro, H2C and X2D**, the print dialog shows a **"Nozzle Offset Calibration"** toggle — **on by default**, matching Bambu Studio. It controls whether the printer runs its nozzle-offset calibration routine before the print starts.

Previously this calibration was always skipped, with no way to enable it — and, just as importantly, no way to keep it *deliberately* off. That off case matters for diamond-nozzle setups, which must **not** run the routine.

The toggle **only appears on dual-nozzle printers**. Single-nozzle machines always skip the calibration regardless of any setting. Your choice is remembered per queue item and applied on every dispatch path (queue, drag-and-drop, re-print).

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

The list comes from the active 3MF (`subtask_name`), read from the G-code's own `; model label id:` header where present — that is the list the firmware works from, and it names every copy on the plate. `slice_info.config` is only the last fallback: newer OrcaSlicer records just the original there when a plate holds several copies of one model. If the in-memory object list is empty (e.g. after a backend restart), pass `?reload=true` and BamDude pulls the 3MF off the printer's FTP and re-parses it — supports multiple filename variants (`{name}.3mf`, `{name}.gcode.3mf`, with-spaces and underscored).

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

## :material-cog: Printer Settings Dialog

A per-printer dialog that mirrors **Bambu Studio → Print Options + Printer Parts**. Open it from the kebab :material-dots-vertical: menu on a printer card → **Printer Settings**.

Four tabs:

- **Print Options** — every toggle BS exposes for the running printer: AI detections, sensors, plate behaviours, sound, auto-recovery. Gated to exactly what the printer reports it supports (see [Visibility](#visibility-what-shows-up-depends-on-the-printer)).
- **Safety** *(X2D / P2S)* — Open Door Detection + Idle Heating Protection, mirroring BS's Safety Options dialog. Only appears on models that expose safety options.
- **Printer Parts** — read-only view of installed nozzle(s) (type, diameter, flow rate). Editing parts on-printer is reserved for a future phase; today the API returns `409 parts_not_editable` if a write is attempted.
- **Add-ons** — the printer body plus every connected accessory (AMS units, filament buffer, exhaust fan, …), mirroring BS's Update Device view. See the [Add-ons tab](#add-ons) section below.

### Print Options — what's there

| Group | Setting | Values | MQTT |
|---|---|---|---|
| AI detections | AI monitoring (legacy toggle) | On/Off + Low/Medium/High | `xcam_control_set` (`printing_monitor`) |
| | Spaghetti detector | On/Off + Low/Medium/High | `xcam_control_set` (`spaghetti_detector`) |
| | Pile-up at purge chute | On/Off + Low/Medium/High | `xcam_control_set` (`pileup_detector`) |
| | Nozzle-clumping | On/Off + Low/Medium/High | `xcam_control_set` (`clump_detector`) |
| | Air-printing | On/Off + Low/Medium/High | `xcam_control_set` (`airprint_detector`) |
| | First-layer inspector | On/Off | `xcam_control_set` (`first_layer_inspector`) |
| Sensors | FOD check (foreign-object) | On/Off | `xcam_control_set` (`fod_check`) |
| | Displacement detection | On/Off | `xcam_control_set` (`model_movement_check`) |
| | Filament tangle detect | On/Off | `print_option` (`filament_tangle_detect`) |
| | Nozzle-blob detect (legacy) | On/Off | `print_option` (`nozzle_blob_detect`) |
| | Nozzle-clumping (smart, 3-mode) | Auto / On / Off | `print_option` (`nozzle_blob_detect_v2`) |
| | Air-print detection (sensor) | On/Off | `print_option` (`air_print_detect`) |
| Plate | Build-plate position detection (legacy) | On/Off | `xcam_control_set` (`buildplate_marker_detector`) |
| | Build-plate marker/type detect | On/Off | `xcam_control_set` (`buildplate_marker_detector`) |
| | Plate alignment check | On/Off | `xcam_control_set` (`plate_offset_switch`) |
| Chamber | Purify air at print end | Off / Inside / Outside | `print_option` (`air_purification`) |
| Misc | Auto recovery on step loss | On/Off | `print_option` (`auto_recovery`) |
| | Prompt sound | On/Off | `print_option` (`sound_enable`) |
| | Camera snapshot enable | On/Off | `ipcam_cap_pic_set` |
| | Store sent files on external storage | On/Off | `system` (`print_cache_set`) |

A few options are mutually exclusive (BS parity), so you only ever see one of each pair: the legacy **build-plate position** toggle vs the newer **marker + alignment** group; the legacy **nozzle-blob** on/off vs the smart **3-mode nozzle-clumping** switch; and the legacy **AI monitoring** toggle vs the newer per-type AI detections (spaghetti / pile-up / clumping / air-print). The `xcam_control_set` module names above are the firmware's own wire names — several differ from BamDude's internal keys, and are mapped on the way out so the toggles actually apply. **Open Door Detection** used to live here; it now sits in the **Safety** tab on X2D / P2S (and stays in Print Options for the X1 family) — see below.

### Visibility — what shows up depends on the printer

Each row shows **only if the printer reports it supports that option** — resolved the same way Bambu Studio does, from the live capability flags in the MQTT push (`fun` / `fun2` / `cfg` / `home_flag` bitfields, the `xcam` message, and the `support_*` booleans), not from a hardcoded per-model table. So the list matches the printer — and BS — on every model, and stays correct as firmware evolves.

In practice this means, for example:

- The **AI detections** (spaghetti, pile-up, nozzle-clumping, air-printing) appear on camera-AI machines that advertise them via the `fun` bits — the X2D and H2 family — and are correctly absent on the P1 / A1 series (which report no `xcam.cfg`, so they have no AI at all).
- **Foreign-object** and **displacement** detection follow the same `fun2` support bits.
- **Filament tangle**, **nozzle blob** and **notification sounds** come from `home_flag` bits, so they show on whichever models actually expose them (e.g. the A1 mini reports tangle + blob; the P1S doesn't).
- **Store sent files on external storage** shows only where the firmware advertises the feature (X2D), and is hidden on printers that have storage but don't expose it (P1S).
- **Purify air** follows its `fun2` bit; **Open Door Detection** follows `fun` bit 12 and the model's `support_safety_options` config (Print Options for the X1 family, the Safety tab for X2D / P2S).

If a printer hasn't sent its full status yet (the first moment after connecting), BamDude falls back to a conservative per-family guess until the real flags arrive.

### State source of truth — the printer

BamDude does **not** persist a "desired state" on its side. The state shown in the dialog comes from the printer's MQTT status push. When you toggle a row, BamDude publishes the matching MQTT command and starts a 3-second hold (`printer_settings_hold` per-key) so the row doesn't flicker between optimistic and confirmed values — same pattern as the AMS Settings dialog.

Because that MQTT round-trip takes a moment, the control you touched **freezes and shows a small "waiting for confirmation" spinner** until the printer confirms, then the value refreshes **in the open dialog** — it never closes and reopens. You can't fire the same toggle repeatedly while it's still applying.

If the printer drops a setting (factory reset, firmware-update wipe), BamDude reflects that — there's no reconciliation. Open the dialog again and re-toggle.

### Safety tab (X2D / P2S)

Printers that advertise `support_safety_options` (currently the X2D and P2S) get a **Safety** tab next to Print Options, mirroring BS's Safety Options dialog:

- **Open Door Detection** — what the printer does when the enclosure door opens mid-print: **Off** / **Notification** / **Pause printing**. Read from `cfg` bits 20-21, written via the `system` `set_door_stat` command. On these models the control lives here instead of in Print Options.
- **Idle Heating Protection** — automatically stops heating after 5 minutes of idle. Read from `cfg` bits 32-33 (a third "unavailable" state greys the toggle while the printer's heating-maintenance function is active), written via `set_against_continued_heating_mode`.

### Permissions and audit

The kebab item only appears for users with the `printers:update` permission. The same permission gates the `POST /api/v1/printers/{id}/settings` endpoint.

Every applied change writes one row to the `printer_setting_audit` table (m061) — `(printer_id, user_id, tab, action, payload_json, sequence_id, result, error_message, created_at)`. No in-UI viewer yet; query the table directly if you need to answer "who turned spaghetti-detection off last Thursday?"

!!! info "On-device calibration is separate"
    Bed leveling, resonance, motor noise and the other machine self-calibration routines aren't print-option toggles — they're long-running on-device routines under their own kebab entry **Calibration**, documented next.

---

## :material-tune-variant: Device Calibration

The printer's own **on-device** self-calibration routines — bed leveling, resonance/vibration, motor noise, and, on newer hardware, nozzle offset, high-temp bed leveling, micro-lidar and nozzle-clumping detection. This is the same set Bambu Studio exposes under **Device → Calibration**: not filament tuning (that's the wizard below), but the machine's own calibration steps that run on the printer with no sliced g-code involved.

Open it from the kebab :material-dots-vertical: menu on a printer card → **Calibration**.

### What's available depends on the model

BamDude shows only the calibrations your specific printer model **and** firmware actually support — resolved exactly like Bambu Studio:

| Calibration | Typically available on |
|---|---|
| Auto Bed Leveling | almost every model |
| Vibration Compensation | every model |
| Motor Noise Cancellation | read live from the printer (P1S, A1 series, X2D, …) |
| Nozzle Offset | dual-nozzle / X2D / H2 series |
| High-Temp Bed Leveling | X2D / H2 series / P2S / A2L |
| Micro Lidar | X1 series |
| Nozzle Clumping Detection | P2S / H2S |

The availability isn't a hand-maintained table. BamDude merges two sources — **hybrid gating**, mirroring Bambu Studio:

1. **Base defaults** — byte-for-byte copies of Bambu Studio's own per-model config files (`resources/printers/<model>.json`), shipped under `backend/app/data/printers/`. Re-syncing them is a folder re-copy + `git diff` against a fresh Bambu Studio checkout.
2. **Live capability flags** — the printer's own MQTT status flags, which override the defaults. **Motor Noise Cancellation** in particular is a *live* signal, not a static per-model flag: some machines advertise it in the `home_flag` bitfield (P1 / X1 series), others in the `fun` bitfield (H2 / X2 series), so BamDude surfaces it wherever the printer reports it — exactly as Bambu Studio does.

### Live progress

Pick the steps you want and press **Start Calibration**. The dialog then stays open and shows the printer's own **stage-by-stage progress** live — the same stage list Bambu Studio renders — each step ticking from pending → running → done until the routine completes.

---

## :material-flask: Filament Calibration

A wizard that mirrors **Bambu Studio → Calibrate → Pressure Advance / Flow Rate / Towers** without leaving BamDude. Open it from the kebab :material-dots-vertical: menu on a printer card → **Filament Calibration**. History review lives on a sibling kebab entry → **Calibration History**.

### What's calibrated

| Mode | Path | Output |
|---|---|---|
| **PA Line** | Manual: flat one-layer block of stepped-K rows (slow / fast / slow extrusion in each) + numbered side tab — pick the cleanest row, K = label next to it. Visually like PA Pattern but with straight lines instead of V-shaped walls | `pa_k_value` per (filament, nozzle, extruder) |
| **PA Tower** | Manual: stepped vertical tower — measure the height (mm) where corners look cleanest, K = Start + (Step × height) | `pa_k_value` per (filament, nozzle, extruder) |
| **PA Pattern** | Manual: comb of V-shaped walls at stepped K values + numbered digits in a glyph tab — pick the cleanest pattern column, read the K from its label | `pa_k_value` per (filament, nozzle, extruder) |
| **Auto PA** | X1 / X1E / H2D Pro: lidar scans + reports K/N | same (pre-filled save dialog) |
| **Flow Rate** | Manual: 9-block coarse (−20…+20 %) → 7-block fine refinement | `flow_ratio` per combo |
| **Auto Flow Rate** | X1 lidar variant | same |
| **Temp / VolSpeed / VFA / Retraction Tower** | Manual print only; read result with your eyes, enter in slicer | no DB row written |

### Per-model capability gating

Per-model rules — auto paths need lidar + firmware support flag; manual paths universally available.

| Path | X1 family | P1 / P2 / X2D | A1 / A1 Mini | H2D / H2D Pro |
|---|---|---|---|---|
| Manual PA / Flow Rate / Towers | yes | yes | yes | yes |
| Auto PA (lidar) | yes | — | — | yes (Pro) |
| Auto Flow Rate (lidar) | yes | — | — | yes (Pro) |
| Dual-extruder (per-extruder cali) | — | — | — | yes |

### Slicer-sidecar gating *(0.4.5)*

Bambu Studio's calibration wizard always runs full slicing — even modes that look "pre-sliced" (PA Pattern, Flow Rate, Auto PA) load geometry from `resources/calib/` as scaffolds, then BS applies the active printer / process / filament preset plus per-mode g-code injection through `Plater::calib_*` / `CalibUtils::*`. BamDude mirrors the same 12 BS files under `backend/app/data/calib_assets/` but reaches the same slicing step through our **server-side slicing** sidecar (OrcaSlicer / Bambu Studio API).

So every Filament Calibration mode needs a connected sidecar. To keep that visible:

- The **Filament Calibration** and **Calibration History** kebab entries on the printer card are **hidden when "Server-side slicing" is off** in Settings (General → General).
- If a direct API call slips through, `POST /printers/{id}/calibration/sessions` returns `409 {detail: "slicer_sidecar_required"}` for any manual mode.
- Auto modes (Auto PA / Auto Flow Rate on lidar-equipped X1 / X1E / H2D Pro) are printer-side only — they go through MQTT `extrusion_cali_start` / `flow_rate_cali_start` without any local slicing. But since the rest of the wizard depends on the sidecar, the entry points are gated together.

PA Tower (Phase 1), PA Pattern (Phase 2), and PA Line (Phase 9) are wired end-to-end as of 0.4.5 — pick any of them in the wizard, the slicer sidecar bakes the pattern, BamDude FTPs the gcode to the printer, runs it, and surfaces the manual-save dialog when finished. The remaining manual modes (Temp / Retraction / VFA / Volumetric Speed Towers, Flow Rate) cycle through `verification` (downloads a sliced 3MF for desktop comparison) before flipping to `production` — that staged rollout is **Wave 2** of the calibration roadmap.

### Print options + swap macros *(0.4.5)*

The wizard's preset page includes the same `PrintOptionsPanel` + `SwapMacrosPanel` you get on the regular print dialog. It reads your saved per-printer-model preferences (`PrintModal` and the calibration wizard share the storage key), so settings tuned once for a model — e.g. always-on swap macros on A1 plate-change, or layer inspection on X1E — apply automatically to calibration prints too. Saved preferences upsert on each successful start. Calibration-tuned defaults: `bed_levelling=true`, `flow_cali=false` (otherwise the printer's pre-print flow-cali would overwrite the gcode's M900 K sweep and mask the test), swap macros opt-in. MQTT-action macros (P1S chamber light on/off) fire automatically through the standard `print_started` / `print_finished` event hooks — no per-job toggle.

### State + persistence

- BamDude row written to `filament_calibration` keyed by `(printer_id, filament_id, nozzle_diameter, nozzle_volume_type, extruder_id)` since m063 — per-printer-instance, not per-model. Two X1Cs in the same farm carry independent K values for the same material.
- The printer is the source of truth. BamDude's table is a cache. Whenever BamDude reads `extrusion_cali_get` it mirrors every visible profile into the cache by stable identity (`name` + `filament_id` + `pa_k_value`) — new rows arrive inactive; you promote one row per combo from the History modal.
- Sync runs automatically on every MQTT (re)connect and whenever the printer's live K-profile list actually changes (hash-diff filtered so it doesn't fire on every push_status broadcast). The manage / history dialogs still trigger fresh pulls on demand.
- Every cache row carries the printer-side `nozzle_id` (`HS00-0.4`, `HH00-0.6`, …) so you can see which physical nozzle each calibration was captured on. On P1S / A1 / A1 mini — where the per-profile id isn't shipped — BamDude derives it from the device-level nozzle hardware state.
- `is_active=True` per combo is enforced by a partial unique index. Promoting a row flips its siblings to inactive.
- Spool ↔ K-profile links (m064) are thin: a `spool_k_profile` row carries only `(spool, printer, extruder, filament_calibration_id)`. One hundred PETG spools sharing the same calibration collapse to one cache row + many links instead of duplicated K data.
- Calibration assets are mirrored from BS `resources/calib/` (AGPL-3.0) under `backend/app/data/calib_assets/` — 12 files total (3MF / STL / STEP scaffolds; see *Slicer-sidecar gating* above for why all modes still need a sidecar). PA Line range: 0.0–0.1 step 0.002 (50 lines). Flow Rate coarse: `[-20, -15, -10, -5, 0, 5, 10, 15, 20]` %; fine: `[-5, -2, 0, 2, 5, 10, 15]` %.

### Apply path on a real print

`background_dispatch` calls the unified `apply_active_calibration_to_slot` helper for every AMS slot the job will use. Resolution order: explicit spool→calibration link → active `filament_calibration` row by combo. The helper then re-matches the cached row against `client.state.kprofiles` by **stable identity** (`name` + `filament_id` + `pa_k_value`) to find the LIVE `cali_idx` — the printer reorders slots when you delete a neighbour, so the stored number is a hint only — and fires `extrusion_cali_sel(ams_id, slot_id, cali_idx)` before the print starts.

The same helper now runs from the post-RFID-refresh path, the tray-tag drift detect, the auto-spool tagger, and both inventory + Spoolman slot-assign endpoints — six call sites collapsed onto one. Closes the silent-drift gap where the firmware was falling back to the default profile after RFID re-taps, slot reassignments, or restarts even though your `SpoolAssignment` row was intact.

External-source prints (BS, printer screen) still benefit: the slot binding persists on the printer until explicitly changed, so the last `extrusion_cali_sel` BamDude fired stays in effect.

### History modal

Two sections side by side:

- **BamDude history** — `filament_calibration` rows grouped by nozzle. Per-row actions: **Set Active** (flips siblings + fires `extrusion_cali_sel`), **Delete**. Active row marked with green ring + checkmark.
- **Printer-side history** — 16-slot view pulled via `extrusion_cali_get`. Refresh button forces a re-pull for a given nozzle diameter.

!!! info "Resume banner"
    If you close the wizard mid-flow (after the print finished but before you saved), reopening the wizard shows a yellow banner with **Resume / Discard** for the in-flight session.

### Permissions and audit

`printers:update` gates the wizard entry and all mutation routes. Every action writes a row to `calibration_audit` — `(printer_id, session_id, action, payload_json, sequence_id, result, error_message, created_at)`. Actions: `start_session / save_result / set_active / delete / cancel`, plus the legacy K-profiles UI page mutations from 0.4.5: `kprofile_add / kprofile_edit / kprofile_batch_add / kprofile_delete`. No in-UI viewer yet; query the table directly.

!!! note "Edit-Save with no printer-relevant change skips the printer"
    Since 0.4.5 the K-profiles edit dialog diffs `name` / `k_value` / `filament_id` / `nozzle_id` / `nozzle_diameter` against the loaded row before publishing. Identical → only the note (BamDude-local) is saved; no `extrusion_cali_set` fires. Stops the printer from regenerating `setting_id` on every Save click, which used to drift the cache row.

### What's intentionally NOT in BamDude (yet)

- **PA range customization** — start/end/step are fixed to BS defaults. If you need a different range, calibrate in BS itself and import the value.
- **External spool calibration** — virtual tray `tray_id >= 0x10000` is disabled for the auto path; the manual path allows it but tray binding may not survive printer reboot.
- **Tower-mode result entry in BamDude** — tower modes start the print and finish. Read the result with your eyes, enter it in your slicer's filament profile. (BS does the same.)

---

## :material-arrow-up-down: Bed Jog (Z-Axis)

Move the build plate up or down by a fixed step.

```
POST /api/v1/printers/{id}/bed-jog?distance=N
```

| Param | Validation |
|-------|------------|
| `distance` | Non-zero, `|distance| <= 200` mm |

The `force` parameter was removed in 0.4.7. It wrapped the move in `M211 S0` … `M211 S1` — a command form that does not exist in Bambu's firmware dialect (there, bare `M211 S` means *push* the endstop state and `M211 R` means *pop* it), and the UI sent it on every jog, so every manual move ran without the soft endstops being explicitly enabled. A stray `?force=true` from an old client is ignored.

Step selector in the popover: `1 / 10 / 50 mm`. Only enabled when the printer is **not** running a print.

### G-code sent

Byte-for-byte what Bambu Studio's own jog sends over the same MQTT `gcode_line` channel (`DevAxis::Ctrl_Axis`):

```
M211 S              ; remember the current soft-endstop state
M211 X1 Y1 Z1       ; explicitly ENABLE all three
M1002 push_ref_mode
G91
G1 ZN F600
M1002 pop_ref_mode
M211 R              ; restore the remembered state
```

Enabling the endstops is the point: Bambu's own sliced start G-code turns them **off** (the A1 machine template ends with `M211 X0 Y0 Z0` and never restores it; H2D re-enables only `M211 Z1`), so a printer sitting idle after a print usually has them disabled. Bambu Studio re-enables them before every manual move for exactly this reason.

### Not-homed warning

After a print completes, the Z axis usually isn't referenced. The first jog click in a session shows a Bambu-Studio-style modal:

| Choice | Action |
|--------|--------|
| **Auto Home** | Runs the printer's full auto-home sequence and dismisses the dialog. On success, jogging works for the rest of the browser session |
| **Cancel** | Closes the dialog, no command sent |

The **Move anyway** button was removed in 0.4.7 — it was the path that drove the plate with the soft endstops bypassed. Bambu Studio refuses a manual move outright while the axis is not homed (`check_axis_z_at_home`), and BamDude now does the same: home first, then jog.

!!! warning "Travel limits are not guaranteed"
    BamDude enables the soft endstops before every jog, but Bambu firmware has been observed running a move past the limit anyway, and it reports no axis position — so the move cannot be clamped client-side either. Keep distances small (≤10 mm) until the plate is in a known-safe position and watch the printer.

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

## :material-fan: Fan Status

Live fan badges in the controls row — **Part Cooling**, **Auxiliary**, **Chamber** — showing real-time speeds (0–100 %) reported by the printer.

!!! info "The three standard badges are read-only"
    Their speeds are determined by the slicer profile and the printer firmware.
    BamDude shows them but doesn't expose a control.

### Air-duct fans (P2S / X2D) — controllable

Machines with an **air-duct** carry fans that are never reported as a plain speed field. Those appear as their own badges, **with a speed control on the badge**: `POST /printers/{id}/fan-speed?part_id=<n>&percent=<0-100>`, gated by `printers:control`.

The most visible one is the **second auxiliary fan** — an add-on kit on the **P2S**, fitted from the factory on the **X2D**.

- **Only what is fitted appears.** The printer lists the parts it actually has, so a badge is driven by the hardware rather than by a list of model names. An id the printer never reported is refused (**400**) rather than sent, since the command would be accepted and do nothing.
- **The fans are named the way your printer names them.** The same part id is a different fan on different models — part 10 is the *left* auxiliary on a P2S and the *right* one on an X2D, and on the X2D it is even called something different in cooling and in heating mode. The names come from the Bambu Studio printer definitions BamDude ships, so a P2S says **Right Auxiliary Fan**, not just "Auxiliary".
- **A fan the current air-duct mode holds off is shown but not offered as a control** (**409** if you try) — the printer accepts the command and ignores it.

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

## :material-wrench: Maintenance Mode

Take a printer **out of service** without deleting it — for a nozzle swap, a belt job, or parking a flaky machine. Toggle it from the printer card's :material-dots-vertical: kebab menu or the **Edit** dialog.

While in maintenance, the printer:

- **drops out of queue dispatch and the scheduler** — no new job is sent to it, and it's skipped by [Auto-Queue Routing](auto-queue.md) and model-based assignment;
- **is skipped by auto-drying** — the drying scheduler ignores it;
- **is excluded from metrics and sensor-history recording**;
- **disconnects from MQTT** and stays disconnected until you turn maintenance off (turning it back on reconnects automatically).

The card swaps its connection badge for an amber **Maintenance** pill (:material-wrench:) with an **Exit** button, so it's obvious at a glance which machines are parked.

!!! note "Toggling on mid-print"
    Entering maintenance on a printer that's **printing or paused** asks for confirmation first — the MQTT disconnect stops progress tracking and completion notifications for the in-flight job.

!!! note "Permission"
    Maintenance Mode rides on the printer's `is_active` flag (no separate column), so it needs `printers:update` — the same permission as editing the printer.

!!! info "Not the Maintenance Tracker"
    This is a *service state* for the whole printer. It's unrelated to the [Maintenance](maintenance.md) tracker, which logs rod / nozzle / belt jobs against usage hours: one parks the machine, the other reminds you when a part is due.

!!! info "Retiring for good? Archive instead"
    Maintenance Mode only parks a printer temporarily and keeps its card visible. To *retire* a printer — sold, decommissioned — [Archive](archived-printers.md) it instead: the card is hidden everywhere while its print history is kept.

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
| Bind / unbind a smart plug | `smart_plugs:update` (binding is a field on the plug, set via `PATCH /smart-plugs/{id}`) |
| Add a printer | `printers:create` |
| Archive / restore / delete a printer | `printers:delete` |
| Firmware push | `firmware:update` |

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
