---
title: Slice settings
description: Save a slice setup once and load it back into the Slice dialog with a single pick
---

# Slice settings

**Slice settings** are a saved setup: the four picks you normally make by hand in the Slice dialog — printer preset, process preset, a filament preset per AMS slot, and the bed type. Save it once, and next time pick it from a dropdown instead of choosing all four again.

That's the whole feature. It's a shortcut for repeatable work, not a dispatcher: you still slice and queue exactly the way you always do.

!!! info "Printing many copies? That's the auto-queue's job"
    Saved settings don't set a quantity or pick printers. To print a batch, use [Auto-Queue Routing](auto-queue.md) — set how many you want and which printer model, and BamDude spreads them across every matching printer, matching filament type and colour as it goes.
---

## :material-cog-outline: What gets saved

| Field | What it is |
|---|---|
| **Name / description** | Your label for the setup. |
| **Printer preset** | The printer profile to slice against (source + id — local, Orca Cloud, Bambu Cloud, or standard). |
| **Process preset** | The process/quality profile. |
| **Filament presets** | One preset **per AMS slot**, so a multi-material job maps each slot to the right filament. |
| **Bed type** | The build-plate type to slice for — one of the plates the [Slice dialog](slicer-api.md#bed-plate) offers. A name outside that list is refused when the settings are saved. |

---

## :material-play-circle-outline: Saving and using one

Use **Save these settings** in the Slice dialog or in a printer row in **Assemble project** to save its presets and bed plate.

**Use one** from the same dialog: pick it under **Apply saved settings** and all four selections fill in at once. Then slice as usual and queue the result however you normally would — [straight to a printer](print-queue.md) or [into the auto-queue](auto-queue.md).

A line under the picker says what the set changed — *"Applied "name". Changed: Printer profile, Bed plate"* — or that nothing changed because these were already the selection. The process and filament profiles a set fills count as [your own choice](slicer-api.md#explicit-choice): the dialog's later automatic picks do not replace them. Filament presets go **by slot**: a set with fewer filaments than the file has slots fills the first ones, and the rest keep theirs.

### Where saved settings can be applied

The same **Saved settings** list is offered in Slice, filament calibration and Assemble project. Each fills the fields it has.

| Place | Fills |
|---|---|
| Slice dialog | Printer, process, every filament slot the set names, bed plate. |
| [Filament calibration](filament-calibration.md) — the page that prints | Printer, process and bed plate. Only sets whose printer profile fits this printer and the chosen nozzle are listed; the filament stays the one of the chosen slot. |
| [Filament calibration](filament-calibration.md) — the download page | Printer, process, bed plate and the first filament. |
| [Assemble project](assemble-project.md) | Printer, process, first filament and bed plate, in the row whose list you used. |

### When a saved preset has been deleted

Presets change. If a saved set references a preset that disappeared or belongs to the other slicer's cloud, BamDude **does not** apply that slot — the field is not filled from the set — it keeps what it holds, and an automatic pick follows the printer the set chose — and the affected fields are named in a warning under the picker.

This matters: silently applying a dead reference would leave that dropdown blank while the dialog still looked ready to slice, and you'd send a job with a preset you never chose. Re-pick the flagged slot by hand and the warning clears.

### When the saved bed plate is not applied

A saved bed plate is applied only when the slicer of this job has it. Otherwise the dialog leaves the bed plate as it is and says so under the **Bed plate** field:

- **Textured Cool Plate with Bambu Studio** — the plate exists in OrcaSlicer only: *"The saved settings name Textured Cool Plate, which is available only with OrcaSlicer. The bed plate was left as it is."* Switch the job to OrcaSlicer and apply the settings again.
- **A plate name that is not on the list** — possible only in a set stored before names were checked: *"The saved settings name a bed plate that is not known here ("…"). The bed plate was left as it is."* Pick a plate and save the set again.

---

## :material-shield-key: Permissions

| Permission | Grants |
|---|---|
| `pipelines:read` | See saved settings and apply them in the Slice dialog, filament calibration and Assemble project. Without it the list is not shown. |
| `pipelines:write` | Create, edit, and delete saved settings. |

**Administrators** and **Operators** get both; **Viewers** get read only.

| Endpoint | Method | Permission |
|---|---|---|
| `/slicer-pipelines/` | GET / POST | read / write |
| `/slicer-pipelines/{id}` | GET / PUT / DELETE | read / write / write |

An [API key](api-keys.md) with read scope can list saved settings; creating and editing them is an operator action.

!!! note "Called `pipelines` in the API"
    The endpoints and permissions still say `pipelines` — the feature arrived from upstream Bambuddy under that name, and renaming the API would break anyone already calling it. Only the interface wording changed.

Manage, rename, and delete saved settings under **Settings → Slicing**.

---

## :material-link-variant: Related

- [Auto-Queue Routing](auto-queue.md) — print a set quantity across every printer of a model.
- [Per-Printer Queues](print-queue.md) — where a sliced job lands.
- [Slicer API](slicer-api.md) — the containerised OrcaSlicer / Bambu Studio sidecar that does the actual slicing.
- [Cloud Profiles](cloud-profiles.md) / [Orca Cloud](orca-cloud.md) — preset sources a saved set can reference.
