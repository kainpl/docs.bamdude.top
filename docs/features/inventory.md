---
title: Spool Inventory
description: Built-in filament tracking with cost / lot / purchase-date, AMS slot assignment, automatic per-print consumption, and a manufacturer-aware colour catalog
---

# Spool Inventory

BamDude has its own inventory of physical filament spools, separate from (and complementary to) the [Spoolman integration](spoolman.md). The internal inventory tracks every spool with brand, colour, weight, cost, purchase date, and lot number; BamDude deducts consumption from spool weight automatically on every print, alerts you when a spool drops below a threshold, and remembers which AMS slot on which printer holds which spool.

Use this page if you want to track filament without standing up a separate Spoolman service. If you already use Spoolman, see [Spoolman](spoolman.md) for the two-way sync layer.

## :material-package-variant: Adding spools

**Inventory** in the sidebar opens the spool list. **+ Add Spool** asks for:

| Field | Notes |
|---|---|
| Brand / vendor | Free-form, but BamDude auto-completes against vendors it has seen before. |
| Material | PLA, PETG, ABS, ASA, TPU, PA, PC, … (matches Bambu's list, but accepts custom values). |
| Colour | Hex picker — the colour catalog (below) suggests names. |
| Weight | Net weight in grams. Bambu spools default to 1000 g; AMS-HT cardboard core is ~250 g. |
| Diameter | `1.75` (default) or `2.85`. Stored verbatim so non-Bambu brands work. |
| Cost | Per-spool cost; feeds project / archive cost calculations. |
| Purchase date | Optional; useful for "rotate stock" reminders. |
| Lot number | Optional; for matching across multiple spools from the same batch (some brands shift hue between lots). |
| Notes | Whatever else you want to remember. |

Spools are owned by the user that created them. `inventory:create` is required to add new ones; `inventory:read` lets a Viewer see the list.

### Per-spool category & low-stock override

Two extra optional fields on the spool form fine-tune both filtering and alerting:

| Field | Effect |
|---|---|
| **Category** | A free-form short tag — e.g. `PETG`, `ABS`, `TPU`, `paint`, `experimental`. Inventory page renders a category-filter chip strip at the top so you can show "only TPU" or "only experimental". The chip strip only appears once at least one spool has a category set, so it doesn't clutter the page on day one. The special chip `__none__` filters to spools with no category. |
| **Low-stock threshold (override)** | Per-spool override for the global `low_stock_threshold`. Use this when a particular spool needs an earlier warning (e.g. an expensive PA — 50% remaining means time to order; cheap throwaway PLA can wait until 10%). Empty = inherit the global setting. |

Both columns are surfaced in the inventory table and editable inline.

## :material-format-list-checkbox: AMS slot assignments

Once a spool exists, you can park it in a specific AMS slot on a specific printer. The right-side AMS panel on each printer card shows the four slots (or eight, on AMS-HT) and lets you drop a spool into each slot.

Behind the scenes, this is the `spool_assignment` table — one row per `(printer, ams_id, tray_id)` triple. Two assignments to the same physical slot can't exist simultaneously; assigning a new spool releases the previous one (which goes back to "available, not in any printer").

Two extra niceties:

- **RFID auto-assign** — Bambu spools with intact RFID tags get matched to the catalog the moment the AMS reads the tag. If a tag points at a known catalog entry but no inventory row exists yet, BamDude offers to create one inline. If the tag is unknown (third-party, custom), you can bind it to an existing spool to skip the manual look-up next time.
- **Drying schedules + AMS humidity tracking** — see [AMS & Humidity](ams.md) — the inventory and AMS pages share state so a "drying" spool is visibly marked as in-progress in both places.

## :material-water-percent: Automatic consumption tracking

Every print BamDude dispatches reads the per-filament `weight` from the source 3MF. On `print_complete`, the dispatched grams are deducted from the spool that was assigned to the matching AMS slot at the time the print started:

- The `spool_usage_history` table records every deduction (one row per print × per spool).
- `spool.used_grams` is the running total.
- `spool.weight - spool.used_grams` is what's left.

The inventory page colour-codes each spool by remaining percentage, with a configurable **low-stock threshold** (Settings → Inventory). When a spool drops below the threshold, the matching `filament_low` notification fires (subscribe to it under whichever providers you care about).

If a print fails partway through, the deducted amount is the slicer-estimate × completion ratio (best effort) rather than the full estimate. External-print fallback archives — the ones from prints started directly on the printer touchscreen — get reconciled the same way once their 3MF is recovered.

## :material-palette: Colour catalog

Colour names come from the `color_catalog` table — manufacturer-aware. When two brands ship a paint chip with the same hex, the Bambu Lab name wins for clarity in the UI; non-Bambu brands resolve via their own entries. If a spool's hex isn't in the catalog at all, BamDude falls back to an HSL-derived name ("dark cyan", "light yellow") so you never see a raw hex string in the UI.

You can extend the catalog manually under **Settings → Inventory → Colour Catalog**. The frontend pulls a runtime `{hex: name}` map once per session — adding a new entry takes effect on next login (or on a hard refresh).

### Multi-colour gradients

Painted, dual-colour, and silk filaments aren't one hex value — they're a gradient between two or more. BamDude renders these as **actual gradient swatches** on inventory cards, AMS slot indicators, and the colour picker, instead of collapsing them into a single flat hex (which always picks the wrong "dominant" colour). The 3MF metadata carries the colour stops; the catalog resolves the name; the swatch widget paints the gradient in CSS. No hand-curated paint-chip table — purely data-driven.

!!! tip "Don't reintroduce hard-coded colour tables anywhere"
    BamDude deliberately removed hard-coded `tray_id_name` / hex tables that would inevitably mislabel third-party filaments. The catalog is the only source of truth — even if you're tempted to "shortcut" colour resolution somewhere.

## :material-account-multiple: Permissions

| Permission | Effect |
|---|---|
| `inventory:read` | View spool list and AMS assignments. |
| `inventory:create` | Add new spools. |
| `inventory:update` | Edit spool fields, assign to slots, set spool-specific K-profile overrides. |
| `inventory:delete` | Remove spools (deletes related assignments too). |
| `inventory:view_assignments` | Specifically the spool-on-slot indicators rendered on printer cards. Granted to Viewers separately so a non-operator can see "what's loaded where" without getting `inventory:read`. |

## :material-clipboard-list: Settings reference

The relevant settings keys (all under Settings → Inventory):

| Setting | Default | Effect |
|---|---|---|
| `low_stock_threshold` | `20` | Spool remaining percentage at which the `filament_low` notification fires (range 0.1 – 99.9). |
| `disable_filament_warnings` | `false` | Master mute for low / out-of-filament alerts. |
| `prefer_lowest_filament` | `false` | When auto-assigning a spool to a print, prefer the spool with the lowest remaining percentage to use up odd ends first. |
| `default_filament_cost` | `25` | Per-kg fallback cost when a spool's `cost` field is unset. |
| `spoolman_enabled` | `false` | Toggle the Spoolman integration. See [Spoolman](spoolman.md). |
