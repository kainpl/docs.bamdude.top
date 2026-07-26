---
title: Slicer Pipelines
description: Save a slice setup once and load it back into the Slice dialog with a single pick
---

# Slicer Pipelines

A **pipeline** is a saved slice setup: the four picks you normally make by hand in the Slice dialog — printer preset, process preset, a filament preset per AMS slot, and the bed type. Save it once, and next time pick it from a dropdown instead of choosing all four again.

That's the whole feature. It's a shortcut for repeatable work, not a dispatcher: you still slice and queue exactly the way you always do.

!!! info "Printing many copies? That's the auto-queue's job"
    Pipelines don't set a quantity or pick printers. To print a batch, use [Auto-Queue Routing](auto-queue.md) — set how many you want and which printer model, and BamDude spreads them across every matching printer, matching filament type and colour as it goes.

    Earlier betas (`0.4.7b2`–`0.4.7b5`) had pipelines do this too, which meant two ways to do one job. The duplicate half was removed; the auto-queue does it and always did.

---

## :material-cog-outline: What a pipeline stores

| Field | What it is |
|---|---|
| **Name / description** | Your label for the setup. |
| **Printer preset** | The printer profile to slice against (source + id — local, Orca Cloud, Bambu Cloud, or standard). |
| **Process preset** | The process/quality profile. |
| **Filament presets** | One preset **per AMS slot**, so a multi-material job maps each slot to the right filament. |
| **Bed type** | The build-plate type to slice for. |

---

## :material-play-circle-outline: Saving and using one

**Save one** straight from the Slice dialog with **Save as pipeline** — it captures the presets you've already picked there.

**Use one** from the same dialog: pick it in the pipeline dropdown and all four selections fill in at once. Then slice as usual and queue the result however you normally would — [straight to a printer](print-queue.md) or [into the auto-queue](auto-queue.md).

### When a saved preset has been deleted

Presets change. If a pipeline references one that no longer exists, BamDude **does not** apply that slot — it keeps whatever the dialog picked automatically and names the affected slots in a warning above the picker.

This matters: silently applying a dead reference would leave that dropdown blank while the dialog still looked ready to slice, and you'd send a job with a preset you never chose. Re-pick the flagged slot by hand and the warning clears.

---

## :material-shield-key: Permissions

| Permission | Grants |
|---|---|
| `pipelines:read` | See saved pipelines and load one in the Slice dialog. |
| `pipelines:write` | Create, edit, and delete pipelines. |

**Administrators** and **Operators** get both; **Viewers** get read only.

| Endpoint | Method | Permission |
|---|---|---|
| `/slicer-pipelines/` | GET / POST | read / write |
| `/slicer-pipelines/{id}` | GET / PUT / DELETE | read / write / write |

An [API key](api-keys.md) with read scope can list saved pipelines; creating and editing them is an operator action.

Manage, rename, and delete pipelines under **Settings → Pipelines**.

---

## :material-link-variant: Related

- [Auto-Queue Routing](auto-queue.md) — print a set quantity across every printer of a model.
- [Per-Printer Queues](print-queue.md) — where a sliced job lands.
- [Slicer API](slicer-api.md) — the containerised OrcaSlicer / Bambu Studio sidecar that does the actual slicing.
- [Cloud Profiles](cloud-profiles.md) / [Orca Cloud](orca-cloud.md) — preset sources a pipeline can reference.
