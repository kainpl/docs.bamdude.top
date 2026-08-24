---
title: Filament Families
description: One filament identity across spools, AMS slots, K-profiles and slicing — the way Bambu Studio models it, custom filaments included
---

# Filament Families

Bambu Studio thinks in **families**: one identity (`filament_id`) behind every filament — "Generic PETG" is `GFG99` whichever printer or nozzle preset you slice with, and a custom filament you create gets a `P…` id of its own. Since 0.5.5 BamDude adopts that model outright: spools, AMS slots, K-profiles and slicing all key on the family.

---

## :material-book-open-variant: The catalog

BamDude ships a **built-in catalog of every official Bambu filament** — the family behind each preset, its name, vendor, type, temperatures and which printers it fits — distilled from Bambu Studio and OrcaSlicer themselves rather than hardcoded tables. It resolves locally and offline: slot names, tooltips and assignments never wait on a cloud request.

On top of it, **your own cloud presets are mirrored server-side** from both Bambu Cloud and Orca Cloud — every few minutes, the moment a cloud is connected, and whenever you open a dialog that uses them. A custom filament created in either slicer is known to BamDude minutes later, family included.

## :material-form-dropdown: The family picker

One control serves the spool form, the AMS slot dialog and the K-profile editor. It shows names, never id codes; custom families carry a badge saying which cloud they came from (Bambu / Orca) or that they are local. Browsing lists **your** filaments — the families behind your own presets, spools and calibrations, the analogue of Bambu Studio's "installed filaments" — while typing searches the entire catalog of both ecosystems, deduplicated.

Spools link to a family directly, and existing spools are migrated automatically on first start after upgrading: whatever the old preset field held is resolved into a family, and anything unresolvable is left honestly unlinked rather than guessed. K-profile auto-matching keys on the family too — which is what finally makes **custom filaments match their own calibration profiles** instead of collapsing onto Generic.

## :material-flask-plus: Creating your own filament

The dialog mirrors Bambu Studio's *Create Filament*: **vendor + type + serial** (reserved vendor names refused, the same fixed type list), and the new family gets a **Bambu-Studio-compatible id** — creating the same-named filament in the slicer later converges on the same identity instead of minting a duplicate.

Three ways in:

- **Profiles → Local → Create filament** — the family is saved locally, with optional *"Also push to Bambu Cloud"* / *"Also push to Orca Cloud"*.
- **Profiles → Bambu Cloud → Create filament** — the family is created in the cloud (desktop Bambu Studio sees it on its next sync), with an optional *"Also keep locally"*.
- **Profiles → Orca Cloud → Create filament** — the same, against [Orca Cloud](orca-cloud.md) (needs a write-scoped pairing).
- **The spool form's family picker → "Create new family…"** — enter a spool of a new material without leaving the form.

You pick **printer profiles**, the way the slicers do ("Bambu Lab P1S 0.4 nozzle") — your farm's models come pre-checked. For every profile you tick, a full root preset is cloned: from the generic profile of that type (through the slicer sidecar), or from any preset you already have. Without a configured sidecar the family is still created, identity-only, and clearly says its presets are pending.

### Managing what you authored

The **Authored families** block under **Profiles → Local** lists every family you created, with per-cloud push state (pushed / edited since push / not pushed) and explicit **push / re-push** buttons for Bambu Cloud and Orca Cloud.

!!! note "Editing and deleting"
    A pushed preset edited in BamDude never overwrites the cloud silently — it is marked as changed and waits for an explicit re-push. If the **Orca Cloud** copy was edited over there after your push, BamDude detects it before writing and asks per preset: overwrite the cloud copy, or adopt the cloud version locally. Deleting a family is refused while any spool or calibration still references it; deleting a pushed one can optionally remove the cloud copies too.

## :material-printer-3d-nozzle: What the printer receives

AMS slot assignment goes through the catalog: the printer gets the family id and the proper versioned preset id, temperatures come from the actual preset for that printer and nozzle (spool overrides still win), and multi-colour spools write **all** their colours to the tray, exactly as Bambu Studio does. A custom family is only sent to printers that declare support for user presets — others receive the generic family of the same material.

## :material-link: Related pages

- [Cloud Profiles](cloud-profiles.md) — the Bambu Cloud tab, sign-in and preset CRUD
- [Orca Cloud](orca-cloud.md) — pairing and profile sync
- [Spool Inventory](inventory.md) — the spool form the picker lives in
- [K-Profiles](kprofiles.md) — calibration values that auto-match by family
