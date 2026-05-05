---
title: Local Profiles
description: Import OrcaSlicer / Bambu Studio presets without Bambu Cloud — file-based filament, process, and printer presets with inheritance resolution
---

# Local Profiles

Local Profiles is the no-cloud path for slicer presets. Drop an OrcaSlicer or Bambu Studio export onto BamDude and the filament / process / printer presets land in the local DB — same surface area as [Cloud Profiles](cloud-profiles.md), but without a Bambu account, without an internet round-trip on every read, and with full support for community-maintained profiles that never went through Bambu Cloud.

The two preset sources coexist. Where a name collides, **Local wins** — see [Tier priority](#tier-priority) below.

---

## :material-target: When to use it

- You don't have (or don't want) a Bambu Cloud account.
- You print with **community filaments** that aren't in Bambu's catalog (Hatchbox, eSUN, Polymaker, FormFutura, etc.).
- You curate your own **process presets** for specific use-cases (production-quality vs prototype-fast) and want them version-controlled outside Bambu's servers.
- You run a **non-Bambu printer** through BamDude's slicer integration and need its OrcaSlicer machine config.
- You want **deterministic** preset behaviour — the same preset bytes, the same slice output, no surprise upstream rev.

---

## :material-file-import: Supported formats

| Extension | Contents | Detected as |
|---|---|---|
| `.json` | Single OrcaSlicer preset file | filament / process / printer (auto) |
| `.orca_filament` | OrcaSlicer single-filament bundle | filament |
| `.bbscfg` | OrcaSlicer / Bambu Studio config bundle (filament + process + printer) | mixed — split by directory |
| `.bbsflmt` | Bambu Studio filament bundle | filament |
| `.zip` | ZIP containing the above | mixed — auto-classified per file |

Type detection is multi-stage:

1. Explicit `type` field in the JSON
2. ZIP directory layout (`filament/`, `process/`, `machine/`)
3. Settings ID keys (`filament_settings_id`, `print_settings_id`, `printer_settings_id`)
4. Content keys (`layer_height` → process; `filament_type` → filament)
5. Name patterns (`0.20mm` in the name → process)

If the heuristic gets the type wrong, run **Reclassify** (`POST /local-presets/reclassify`) to re-evaluate everything with the latest rules.

---

## :material-upload: Importing

**Settings → Local Profiles → drop file or click to pick.** The import endpoint accepts either form-encoded `multipart/form-data` upload (UI) or programmatic POST (`POST /api/v1/local-presets/import` with `file` field).

After import you'll see one of three toast results:

| Colour | Meaning |
|---|---|
| **Green** | N presets imported successfully — name + count |
| **Orange** | M presets skipped — duplicates by name |
| **Red** | Errors — typically a malformed JSON inside a bundle |

Bundle imports are **all-or-nothing per file**: a corrupt JSON inside a ZIP doesn't abort the rest of the bundle, but the bad entry is reported separately.

---

## :material-file-tree: Inheritance resolution

OrcaSlicer presets often `inherit` a Bambu base profile and only override a few fields ("PLA Basic at 215 °C instead of 220 °C, otherwise like the parent"). On import, BamDude:

1. Detects the `inherits` field.
2. Looks up the parent in the **OrcaSlicer GitHub mirror** (`raw.githubusercontent.com/SoftFever/OrcaSlicer/main/resources/profiles/BBL/...`).
3. Recursively resolves the chain (max **10 levels** deep — anything beyond is treated as malformed and stops there).
4. Merges parent → child (child fields win on conflict).
5. Stores the **fully resolved** preset in the local DB, plus the literal `inherits` name on the row for display.
6. Caches each fetched parent in `orca_base_profiles` (TTL **7 days**).

The cache makes repeat imports fast and keeps you out of GitHub's anonymous rate limit.

!!! tip "Offline imports"
    Presets without `inherits` import fully offline. Presets that need a parent need GitHub reachable on the **first** import — afterwards the parent is cached and the same parent serves any future preset that inherits from it. To pre-warm the cache, import a small known-parent preset over a network connection before going offline.

!!! note "GitHub unreachable"
    If GitHub is unreachable when a preset needs its parent, the import doesn't fail — the preset is stored with only its override fields. It works, but missing-from-the-parent fields stay empty until you re-import after the cache fills.

---

## :material-database-search: What lives on a preset row

| Field | Source |
|---|---|
| `name` | `name` from the JSON |
| `preset_type` | `filament` / `process` / `printer` (auto-classified) |
| `source` | `orcaslicer` (file import) or `manual` (created via the UI) |
| `filament_type` / `filament_vendor` | Extracted on filament presets |
| `nozzle_temp_min` / `nozzle_temp_max` | Range from `nozzle_temperature` array |
| `pressure_advance` | K factor (string for OrcaSlicer compatibility) |
| `default_filament_colour` | Hex like `#FF6633` |
| `filament_cost`, `filament_density` | Per-spool economics |
| `compatible_printers` | JSON array — drives the "for printer" filter |
| `setting` | The full resolved JSON blob (post-inheritance merge) |
| `inherits` | Literal parent name for display |
| `version`, `created_at`, `updated_at` | Bookkeeping |

The full resolved blob is what slicing pipelines consume. Anything you can normally read out of OrcaSlicer's preset JSON is in there.

---

## :material-water-percent: AMS slot integration

Filament local presets surface in the AMS slot configuration modal exactly the same way cloud filament presets do:

- The dropdown lists local presets with a green **Local** badge, then cloud presets, then built-in fallbacks.
- Picking a local preset writes its `nozzle_temp_*`, `filament_type`, and `default_filament_colour` to the slot record — same fields a cloud preset would set.
- The AMS-tray tooltip and the K-profile UI both consult `_enrich_from_local_presets` (in `cloud.py`) when the cloud / built-in tables miss a `setting_id` — local presets are the third resolution tier.

See [AMS](ams.md) for how slot config flows from "preset selected" to "MQTT command issued".

---

## :material-layers-triple: Tier priority

Three sources can answer "what's preset X?". When the slice modal asks for the merged list:

1. **Local** (this page) — file-imported, DB-backed, `source='orcaslicer'` or `'manual'`. **Wins on name collision.**
2. **Cloud** — fetched per-user from Bambu Cloud (see [Cloud Profiles](cloud-profiles.md)).
3. **Bundled** — slicer-sidecar fallback. Bambu's stock catalog as shipped inside the OrcaSlicer image.

The unifier (`/api/v1/slicer/...`) deduplicates by name across tiers, keeping the highest-priority entry. So if you import `Bambu PLA Basic @BBL X1C` locally and have the cloud-side version too, only the local one shows — exactly the behaviour you want when a community preset diverges from upstream.

---

## :material-pencil: Editing a preset

Cards expand on click. The detail view shows every field of the resolved JSON. To edit:

| Action | Endpoint | Notes |
|---|---|---|
| **Update name** | `PUT /api/v1/local-presets/{id}` with `{name}` | Cosmetic only |
| **Update settings** | `PUT /api/v1/local-presets/{id}` with `{setting: {...}}` | Re-runs `resolve_preset()` so inheritance resolves against any new `inherits` value, then re-extracts core fields |
| **Manual create** | `POST /api/v1/local-presets/` | Bypasses the file import path — useful for on-the-fly tweaks |

There's no "save as new" affordance in the UI — that's done via duplicate-then-edit on the source file before re-importing.

---

## :material-delete: Deleting

| Scope | Endpoint |
|---|---|
| **Single** | `DELETE /api/v1/local-presets/{id}` |
| **Bulk** | The list view's checkboxes + Delete-selected button (calls the single endpoint per row) |

Deletes are **immediate** — no trash, no undo. The on-disk file under `<DATA_DIR>/local_presets/` (cache for the import) isn't trash either; it's reconstructable from the DB row, so the cache layer reaps deleted rows on the next sweep.

---

## :material-cached: Base profile cache management

Two admin endpoints expose the parent-profile cache:

| Endpoint | What |
|---|---|
| `GET /api/v1/local-presets/base-cache/status` | How many parents are cached, oldest fetch timestamp, total bytes |
| `POST /api/v1/local-presets/base-cache/refresh` | Force-refetch every cached parent from GitHub (ignores TTL) |

Use **refresh** after a major OrcaSlicer release — Bambu sometimes silently fixes a base profile (bumped temp range, corrected K factor) and your cached copy lags by up to 7 days otherwise.

---

## :material-shield-key: Permissions

| Permission | Grants |
|---|---|
| `settings:read` | List presets, inspect a preset's full JSON, read base-cache status |
| `settings:update` | Import, manual-create, edit, delete, reclassify, refresh base cache |

Default groups: **Administrators** get both, **Operators** get both, **Viewers** get only `settings:read` (they can browse but not import).

!!! info "Why `settings:*`?"
    Local presets are configuration data — they live in the same trust tier as anything in **Settings**. There's no separate `presets:*` permission family because the permission model treats "edit a preset" and "edit smart-plug config" as the same risk class.

---

## :material-folder-open: Where files land on disk

The DB stores the resolved preset JSON inline. The original uploaded file is held as a working copy under:

```
<DATA_DIR>/local_presets/<id>/<original-filename>
```

This isn't authoritative — the DB row is. The on-disk copy is a debugging aid (you can `unzip` a `.bbscfg` and inspect the raw OrcaSlicer source). Deleting the row deletes the directory; deleting the directory by hand triggers a re-import on the next access.

The base-profile cache lives separately in the `orca_base_profiles` table — DB-resident, not on disk, so it survives a `<DATA_DIR>` restore cleanly.

---

## :material-help-circle: Troubleshooting

??? question "Import says `0 imported` but the file looks valid"
    Probably duplicate detection — every preset in the file already exists in the DB by name. The orange skip-toast count is your signal. To re-import after editing, delete the existing row first, then re-upload.

??? question "Inheritance not resolving — preset has fewer fields than it should"
    GitHub was unreachable on the import. Run `POST /local-presets/base-cache/refresh` once the network is back, then re-upload (or `PUT` the preset's `setting` field to trigger re-resolution).

??? question "Preset classified as the wrong type"
    Run `POST /local-presets/reclassify`. If the heuristics still get it wrong, the JSON is missing both an explicit `type` field and the conventional content keys — add `"type": "filament"` (or `"process"` / `"printer"`) to the source file and re-import.

??? question "AMS slot dropdown doesn't show my new local preset"
    The slice-modal cache has a 5-minute TTL. Close and reopen the modal, or restart the AMS slot-config dialog.

??? question "I want to share a preset bundle across installs"
    Export from OrcaSlicer / Bambu Studio (`File → Export → Export Preset Bundle`), drop the `.bbscfg` into the import zone on each install. The DB row format is intentionally not a stable interchange format — round-trip via the slicer's export.

??? question "Can I use both Cloud and Local at once?"
    Yes — they coexist. Local wins on name collision. If you want a cloud preset to override a local one, rename the local one (its DB `name` field) before the next slice.
