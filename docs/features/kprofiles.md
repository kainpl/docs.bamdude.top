---
title: K-Profiles
description: Per-printer print profiles with dual-nozzle gating, import/export, and Git-backup integration
---

# K-Profiles

K-Profiles are BamDude's representation of slicer-grade print parameters tuned per printer — pressure-advance / linear-advance values, nozzle/bed temps, flow ratios, retraction settings. Profiles travel with your install: backed up over Git on a schedule, exported as a single JSON file when you want to migrate, applied per spool from the inventory page.

This page covers the profile mechanics. For the spool side (assigning a profile override to a specific spool / colour) see [Spool Inventory](inventory.md).

## :material-cog: Where profiles live

| Surface | What it does |
|---|---|
| **Profiles** in the sidebar | The profile list. Filter by printer model, search by name, edit, clone, import, export. |
| Spool detail (under Inventory) | "K-profile override" — pick a profile to use whenever this spool is assigned to an AMS slot. Useful for off-spec filaments. |
| Settings → Backup → Git | Schedule profiles + cloud profile snapshots to GitHub / GitLab. |

## :material-content-duplicate: Cloning vs editing

A profile can be in three states:

- **System default** — shipped with BamDude, read-only. Clone to customise.
- **User-owned** — created by you, fully editable.
- **Imported** — pulled in from another install / Git restore. Editable, but the import metadata stays attached so you can tell where it came from.

Cloning a system default produces a user-owned copy with the same parameters; the original system row is untouched. Most BamDude operators end up with one user-owned per `(printer model × material)` pair.

## :material-printer-3d: Dual-nozzle gating

H2D / H2D Pro / H2C / H2S have two nozzles; their profiles need to expose two parallel sets of flow / temperature parameters. BamDude detects dual-nozzle from the printer's serial prefix and:

- Filters the profile picker to dual-nozzle profiles when the target is a dual-nozzle printer.
- Hides the secondary-nozzle UI block on single-nozzle profiles to reduce noise.
- Refuses to assign a single-nozzle profile to a dual-nozzle printer (and vice versa) — you'll see a clear error in the UI rather than a silent malfunction during print.

## :material-import: Import & export

Three import paths:

| Source | Notes |
|---|---|
| **Single profile JSON** | The Profiles page accepts an upload of a previously-exported profile. |
| **Bundle import** | Profiles + matching spool-overrides as one ZIP; useful when migrating between installs. |
| **OrcaSlicer preset** | OrcaSlicer ships filament presets that map cleanly onto K-profile parameters. Drop a folder of `.json` Orca filament presets and BamDude imports them in one click. |

Export is the inverse — single profile, full bundle, or "everything modified since X" diff bundle.

## :material-cloud-upload: Git-backup integration

Settings → Backup → Git can push your profile catalogue (plus the BamDude config snapshot) to a GitHub or GitLab repo on a schedule. The repo holds:

- A flat directory of profile JSONs under `kprofiles/` (one file per profile, named by ID).
- A `kprofiles_index.json` listing every profile by hash + name + printer-model so a partial restore is unambiguous.
- The matching spool overrides (`spool_kprofiles/`).
- An audit log entry per scheduled commit.

Restore from Git is partial-by-default: you can pick specific profiles to pull back, or "everything since the last backup". The Git history itself is your version archive — every commit is a profile catalogue snapshot you can roll back to.

## :material-account-multiple: Permissions

| Permission | Effect |
|---|---|
| `kprofiles:read` | View profile list, see settings. Default for Viewers. |
| `kprofiles:create` | Make new profiles or clone existing ones. |
| `kprofiles:update` | Edit user-owned / imported profiles. |
| `kprofiles:delete` | Remove user-owned profiles (system defaults can never be deleted). |

Spool overrides (`spool_kprofile`) are governed by `inventory:update` — same surface as editing a spool.
