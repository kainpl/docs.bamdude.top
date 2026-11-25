---
title: Filament Calibration
description: BamDude's in-app calibration wizard — pressure-advance and speed/quality towers sliced against your own presets, with Bambu Studio parity
---

# Filament Calibration

BamDude ships an **in-app Filament Calibration wizard** that tunes per-filament print parameters — pressure-advance K, flow ratio, speed and temperature limits — from inside BamDude. You no longer need the Bambu Studio desktop application open just to run a calibration: the wizard reproduces the Bambu Studio calibration flow against your own connected printer.

The wizard's pressure-advance result feeds straight into a [K-Profile](kprofiles.md) — see that page for how the resulting K value is stored, synced, and applied per spool.

---

## :material-gesture-tap-button: Opening the wizard

Every printer card has a kebab (⋮) menu with two sibling calibration entries:

| Menu entry | What it opens |
|---|---|
| **Filament Calibration** | The calibration wizard itself — pick a mode, slice, print, save the result. |
| **Calibration History** | A modal listing BamDude's stored calibration rows next to the printer's live K-profile table. |

---

## :material-cog-sync: How it slices

This is the key difference from a fixed test print. The wizard does **not** ship a canned, pre-sliced 3MF and blindly print it. For each mode it slices the calibration scaffold geometry against **your active printer / process / filament presets** through a connected **OrcaSlicer or Bambu Studio sidecar** — exactly the way the Bambu Studio desktop calibration wizard does it.

Per-mode preset overrides (wall loops, line width, initial-layer speed, spiral mode, and so on) are applied before slicing, so the calibration object behaves identically to a Bambu Studio calibration.

The sliced `.gcode.3mf` is then FTP'd to the printer and run as a **real print through the normal dispatch pipeline**. Because it goes through the same path as any library job, plate-change macros and chamber-light MQTT actions fire just as they would for a regular print.

### Choosing the slicer, the plate and the presets { #choosing-presets }

The page that prints and the download page share one set of controls: the slicer cards (the choice is remembered for this printer), **Bed plate**, **Saved settings**, the cloud status with **Refresh**, the **Preset source** segment — **All**, **My Presets**, **Built-in**, the same remembered choice as in the [slice dialog](slicer-api.md#preset-lists) — and the **Printer profile**, **Process profile** and **Filament profile** fields. Process and filament profiles made for another printer are hidden here rather than grouped: a calibration print for the wrong printer only wastes a bed. The selected slicer shows its own cloud alongside imported and bundled presets. A renamed process or filament preset can inherit its printer and nozzle compatibility from its base profile. Automatic picks prefer suitable profiles from the selected printer's source.

**On the page that prints:**

- **Printer profile** lists only the profiles proven for this printer: the profile's name, or the name of the preset it was saved from, states this printer's model and the chosen nozzle size. A bare model entry (`Bambu Lab A1`) or a profile of another model is never proven. The first proven profile is picked for you. When none is proven, every printer profile is shown and the start waits: *This printer profile is not known to be this printer with the chosen nozzle. Choose a profile of this printer to start.* A profile you chose that stops being proven — after a change of nozzle — stays, carries the same note and holds the start until you choose another.
- **Process profile** is picked only from processes that fit the chosen printer. When none fits, nothing is picked and the start waits for your choice.
- **Filament profile** is picked by the **filament family** of the slot you selected: a profile of that family that fits the printer. Until the printers have said which family the slot holds, or when that cannot be read, or when no profile of the family is found, nothing is picked and the field names the slot — *Waiting for the printer to say which filament family is in …*, *The filament family in … could not be read*, *No profile of the filament family in … was found* — and you choose the profile yourself. You can choose it at any time, and a profile you chose stays when the answer arrives. Selecting another slot picks again for that slot.
- **Saved settings** lists only the sets whose printer profile is proven, and fills the printer, process and bed plate; the filament stays the slot's.

**On the download page** any printer profile can be chosen. A profile of another model is allowed, and the field says so: *This printer profile is for another model, so the file is for that model.* The filament is the first profile that fits the printer, and **Saved settings** also fills it.

**The bed plate** is the one the file is built for and the one it is sliced with. **Textured Cool Plate** is offered with OrcaSlicer only; for Bambu Studio — chosen or by default — it is refused before anything is built or sliced.

Choosing presets needs the right to upload to the library (`library:upload`): without it the controls give way to *Choosing presets here needs the right to slice files.*, and the start and the sliced download are unavailable. The pre-slice download keeps working.

!!! note "Slicer sidecar required"
    The wizard needs a reachable OrcaSlicer or Bambu Studio sidecar to slice. Configure it under **Settings** before running a calibration. Without a slicer the wizard cannot produce a printable 3MF.

---

## :material-format-list-bulleted-type: Calibration modes

### Pressure Advance

Three pressure-advance modes, all **fully production**:

| Mode | What it prints |
|---|---|
| **PA Line** | A series of single-perimeter lines, each at an increasing K value. |
| **PA Pattern** | A grid pattern that exposes K quality across a 2D field. |
| **PA Tower** | A vertical tower with K incrementing by height. |

All three follow the full flow: slice → FTP → print → save dialog → K-profile saved and bound to the AMS slot.

### Towers

| Mode | What it prints |
|---|---|
| **Temperature Tower** | A tower whose nozzle temperature steps down 5 °C every 10 mm band — each band carries an embossed temperature number. |
| **Volumetric Speed Tower** | A spiral-mode tower whose outer-wall speed ramps up with height. |
| **VFA Tower** | Vibration Fine Artifacts tower — also spiral-mode, outer-wall speed ramps with height. |
| **Retraction Tower** | A two-pillar stringing tower — each 1 mm of height retracts a little more filament. |

All four are **production**. They are print-and-eyeball calibrations: the operator reads the cleanest band (Temperature), the failure height (Volumetric Speed, VFA), or the height where stringing between the pillars cleans up (Retraction) by eye, then uses the finish-step calculator (see below). For the Temperature Tower, the start/end temperatures default to the right range for the loaded filament's material — PLA 230→190 °C, PETG 250→230 °C, ABS/ASA 270→230 °C, and so on.

### Flow Rate

A two-pass test that calibrates the filament's flow ratio — the multiplier that scales every extrusion move so the right amount of plastic comes out. **Pass 1** (coarse) prints a plate of 9 patches at modifiers from −20 % to +20 % in 5 % steps centred on your filament's current `filament_flow_ratio`. The operator picks the smoothest patch in the wizard's coarse-save dialog; **pass 2** (fine) then prints 10 patches at modifiers from −9 % to 0 %, centred on the coarse pick. The final flow ratio is `coarse_pick × (100 + fine_modifier) / 100` — written into the calibration history and ready to copy into the slicer's filament profile.

The baseline the test prints at is the picked filament preset's `filament_flow_ratio`, auto-prefilled in the verify-download page when the preset is local or resolvable; the operator can also override it to test from a fresh `1.0` without editing the slicer profile.

**Production.** The wizard's two-pass auto-dispatch runs end-to-end — pass 1 slices, prints, you pick the block, pass 2 slices automatically with the picked baseline, prints, you pick the block, the wizard saves.

### In development

Only **Auto** (lidar-driven, X1 / H2D Pro) calibration is still rolling out. It appears greyed-out in the wizard on supported printers until it lands.

---

## :material-state-machine: Mode lifecycle

Every mode is in one of three states. This is how BamDude rolls a calibration mode out safely — modes graduate from `disabled` through `verification` to `production`.

| State | In the wizard | Meaning |
|---|---|---|
| `disabled` | Greyed out, not selectable | Not yet shipped in this build. |
| `verification` | Selectable, with a **Download sliced 3MF** button | Transitional sign-off state. An operator can download the wizard's sliced output and diff it against Bambu Studio desktop before the mode is trusted to drive a real print. |
| `production` | Full wizard flow | Slice → FTP → print → save. The mode is trusted. |

---

## :material-content-save-check: The save / finish step

How a calibration finishes depends on the mode family.

### Pressure Advance modes

Pressure-advance modes end on a **save dialog**:

- **PA Line / PA Pattern** — the operator reads the K label printed next to the cleanest line or column and types it in directly.
- **PA Tower** — the operator measures the height (mm) where the corners are sharpest, and BamDude computes the K value:

    ```
    K = start + step × height_mm
    ```

The result is written to a `filament_calibration` row, pushed to the printer's 16-slot K-profile history over MQTT, and bound to the AMS slot — so subsequent prints automatically use it.

### Tower modes (Temperature, VFA, Volumetric Speed, Retraction)

Tower modes are print-and-eyeball. The result is a **slicer-side setting** with no printer runtime knob. The finish step provides a **calculator**: enter the measured height (mm) and BamDude applies the per-mode formula, showing the result inline.

| Mode | Formula | Unit |
|---|---|---|
| **Temperature Tower** | `result = start − ⌊height / 10⌋ × 5` | °C |
| **Volumetric Speed Tower** | `result = start + height × step` | mm³/s |
| **VFA Tower** | `result = start + ⌊height / 5⌋ × step` | mm/s |
| **Retraction Tower** | `result = start + ⌊max(0, height − 0.4)⌋ × step` | mm |

The Temperature Tower descends 5 °C per 10 mm band; VFA bands the speed every 5 mm; the Retraction Tower bands every 1 mm above a 1.4 mm base — hence the floor division in all three.

Pressing **Save result** records the value in the calibration history as a farm record — "this filament, on this printer + nozzle, calibrated to X".

!!! note "A tower result is an inert record"
    Unlike a pressure-advance result, a tower result is **not** auto-applied to anything — it is a slicer-side setting with no printer-side knob to push. The saved row is a record for your reference. Copy the value into your slicer's filament profile yourself.

---

## :material-fingerprint: Result identity

Every calibration result is keyed on a **5-tuple**:

`(printer, filament, nozzle diameter, nozzle volume type, extruder)`

The identity is **per-printer-instance**: two identical printers in a farm can carry independent calibration values for the same filament. The wizard never assumes that calibrating a filament on one printer covers the others.

---

## :material-link-variant: Auto-bind on print start

The active pressure-advance calibration **auto-binds on every print start**. BamDude re-matches the printer's live calibration index via the stable 5-tuple identity each time a print begins.

This means AMS slot reorders and RFID re-taps cannot silently fall back to the wrong K — even if the slot's index has shifted, the correct calibration is re-bound from BamDude's stored identity before the print runs.

---

## :material-history: Calibration History modal

The **Calibration History** kebab entry opens a modal that lists BamDude's stored calibration rows side-by-side with the printer's live 16-slot K-profile table.

Per row you can:

- **Set active** — make this calibration the bound one for its slot.
- **Delete** — remove the stored row.
- **Refresh from printer** — re-read the printer's live calibration index for that row.

Tower results appear here too, shown with the mode-derived unit (VFA in mm/s, Volumetric Speed in mm³/s) so the history reads correctly regardless of mode family.

---

## :material-printer-3d: H2D dual-extruder

On H2D / H2D Pro the wizard exposes **per-extruder tabs**. Each extruder calibrates independently — its own modes, its own results, its own 5-tuple identity (the extruder is part of the key). Calibrating the left extruder never touches the right.

---

## :material-account-multiple: Permissions

| Permission | Effect |
|---|---|
| `printers:update` | Run the calibration wizard. |
| `kprofiles:read` | View the Calibration History modal. |

---

## :material-alert: Troubleshooting

**A mode is greyed out**

- The mode is in the `disabled` state in this build — it has not shipped yet. Auto (lidar-driven) calibration rolls out separately; check the changelog for the build that enables it.

**Calibration print didn't dispatch**

- The wizard slices through a slicer sidecar. Confirm the OrcaSlicer or Bambu Studio sidecar is configured and reachable under **Settings**.
- Verify the printer is online with a green status dot and not mid-print — the calibration job dispatches through the normal pipeline and queues behind any active print.

**Saved K doesn't seem to apply on the next print**

- Pressure-advance results auto-bind on print start via the 5-tuple identity. Check **Calibration History** to confirm the row is **set active** for the slot.
- Verify the nozzle diameter and nozzle volume type match — the result is keyed on both, so a nozzle change produces a separate, unmatched identity until you re-calibrate.

**A tower result had no effect**

- Expected — a tower result (VFA, Volumetric Speed, Retraction) or a Flow Rate result is an inert record, not a printer-side setting. Copy the value into your slicer's filament profile yourself.
