---
title: Spool Inventory
description: Built-in filament tracking with cost / lot / purchase-date, AMS slot assignment, automatic per-print consumption, and a manufacturer-aware colour catalog
---

# Spool Inventory

BamDude has its own inventory of physical filament spools, separate from (and complementary to) the [Spoolman integration](spoolman.md). The internal inventory tracks every spool with brand, colour, weight, cost, purchase date, and lot number; BamDude deducts consumption from spool weight automatically on every print, alerts you when a spool drops below a threshold, and remembers which AMS slot on which printer holds which spool.

Use this page if you want to track filament without standing up a separate Spoolman service. If you already use Spoolman, see [Spoolman](spoolman.md) for the two-way sync layer.

## :material-view-dashboard: Inventory overview

The Inventory page opens with five summary cards above the spool list, each click-through to a filtered view:

| Card | What it shows |
|---|---|
| **Total Inventory** | Count of spools + total weight in kg across the whole inventory. |
| **Consumed (this month)** | Grams deducted from spools in the current calendar month. Pairs with [Stats](stats.md) for longer-range views. |
| **By Material** | Donut chart broken down by filament type (PLA, PETG, ABS, …). Click a wedge to filter the spool list to that material. |
| **In Printer** | How many spools are currently loaded across all AMS units on all printers (sum of slot assignments). |
| **Low Stock** | Count of spools below either the global `low_stock_threshold` or their per-spool override (whichever is stricter). Click to filter to just the low-stock list — pairs with the `filament_low` notification. |

### Filtering, search, and view modes

The toolbar above the list combines a free-form search box with chip strips and view-mode toggles:

- **Search box** — matches on name, brand, material, or hex colour. Press `/` from anywhere on the page to focus it.
- **Material chips** — multi-select OR (PLA + PETG → either).
- **Colour chips** — multi-select OR by default; matches on the resolved colour-catalog name so all "Cobalt Blue" spools group regardless of brand.
- **Status tabs** — Active / Archived / All, plus quick filters Used / New, plus stock filter All / Stock (no slicer profile) / Configured (has slicer profile).
- **Brand dropdown** — single-select.
- **View modes** — **Table** (data-focused, sortable columns) or **Cards** (visual swatches).
- **Group similar** — toggle that visually collapses identical unused / unassigned spools into one expandable row with a count badge (e.g. *5 identical spools*). Grouping key is `manufacturer + material + colour name + label_weight + subtype`. Used or AMS-assigned spools always appear individually so you can tell which physical spool is in which slot. Group state persists across sessions.

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

### Full form: Filament Info tab

The "+ Add Spool" form has two tabs. The first one — Filament Info — covers everything needed to identify the spool and resolve the right slicer preset.

| Field | Description |
|---|---|
| **Slicer Preset** | Search-and-select the filament profile (Bambu Cloud, local OrcaSlicer imports, or built-in fallback — see [Where presets come from](#where-presets-come-from) below). Selecting a preset auto-fills *Material*, *Brand*, and *Subtype* from the preset name. |
| **Material** | PLA, PETG, ABS, ASA, TPU, PA, PC, … — accepts custom values, see [Custom materials](#custom-materials). |
| **Brand** | Filament manufacturer; auto-completes from previously-seen brands. |
| **Subtype** | Basic, Matte, Silk, HF, Metal, CF, … |
| **Label Weight** | Net weight as printed on the spool (default 1000 g; AMS-HT cardboard core ~250 g). |
| **Quantity (bulk)** | 1–100 spools created in one operation. Useful for "I bought a 5-pack of PLA" scenarios — every spool is created with identical material / colour / weight / cost. |
| **Colour** | Visual picker with shade + opacity + finish pickers. Recent-colours strip + brand palettes. |
| **Extra colours** | Optional. Comma-separated list of 2–8 hex stops (e.g. `EC984C,#6CD4BC,A66EB9,D87694`) for multi-colour spools. Renders the swatch as a gradient strip; with **Effect = Multicolor** it becomes a colour-wheel pie. Format matches 3dfilamentprofiles.com so paste-and-go works. |
| **Effect** | Optional rendering hint. Layered on top of the colour swatch — does **not** change the slicer profile. Full enumeration: surface effects (*Sparkle*, *Wood*, *Marble*, *Glow*, *Matte*), sheen variants (*Silk*, *Galaxy*, *Rainbow*, *Metal*, *Translucent*), structural variants (*Gradient*, *Dual Color*, *Tri Color*, *Multicolor*, *Silk Dual*, *Glow Dual*, *Matte Dual*). |

#### Quick Add (Stock) mode

Toggle **Quick Add (Stock)** at the top of the form to switch to a minimal mode that hides the slicer preset + PA Profile tab. Only **Material** (required), **Brand**, **Subtype** (both optional), **Label Weight**, **Quantity**, and **Colour** are shown — perfect for inventorying a freshly-arrived order before you've decided which slicer profile to associate.

Quick-Add spools are called **stock spools** — they track weight and usage like any other spool, but they aren't linked to a printer filament profile. You can edit a stock spool later to assign a slicer preset (it becomes a *configured* spool at that point) or filter to just the stock pile via the inventory's stock filter.

The **Quantity** field is only shown in Quick Add and creates batches with auto-incremented lot-number suffixes when filled.

!!! tip "Bulk buying"
    A 5-pack of PLA → set Quantity = 5 → BamDude creates 5 identical spools in a single transaction. Pair with the **Group similar** toggle on the inventory list to collapse them back to one row with a count badge.

#### Where presets come from

The **Slicer Preset** dropdown merges filament profiles from three sources, checked in priority order:

| Source | Priority | Badge | Description |
|---|:---:|---|---|
| **Bambu Cloud** | 1 | — | Personal cloud presets synced from BambuStudio. Includes Bambu's official presets and any custom presets you created (e.g. *# Overture Matte PLA @BBL P1S*). Requires [Cloud Profiles](cloud-profiles.md) login. |
| **Local Profiles** | 2 | `Local` (green) | OrcaSlicer presets imported via [Local Profiles](local-profiles.md). Useful if you don't use Bambu Cloud or use OrcaSlicer-only profiles. |
| **Built-in Fallback** | 3 | `Built-in` (amber) | Static table of ~150 Bambu Lab filament IDs (PLA Basic, PETG HF, ABS, …). Always available, no login needed. |

Presets from all three sources are merged + deduplicated. If cloud login fails, local + built-in still appear — the preset list is never empty.

User presets that inherit from Bambu presets (e.g. *# Overture Matte PLA @BBL H2D*) are fully supported — BamDude resolves the underlying filament ID from the inheritance chain.

#### Custom materials

The material dropdown ships with PLA, PETG, ABS, TPU, ASA, PC, PA, PVA, HIPS, PA-CF, PETG-CF, PLA-CF. If your material isn't listed (e.g. PCTG, PHA, PP, PVDF), type it directly into the Material field — a *Use custom material: PCTG* option appears at the bottom of the dropdown. Click it to commit.

Custom materials work like built-ins for inventory tracking, usage history, filtering, and notifications.

!!! example "Adding PCTG (3D-Fuel Pro)"
    1. **+ Add Spool**.
    2. **Slicer Preset**: pick the closest PETG preset (PCTG is a PETG variant). For a custom OrcaSlicer PCTG profile, import via [Local Profiles](local-profiles.md) first.
    3. **Material**: type `PCTG` → click *Use custom material: PCTG*.
    4. **Brand**: `3D-Fuel`. **Subtype**: `Pro`.
    5. Set colour (315 °C max bed, 80 °C bed for PCTG — print/bed defaults are inherited from the base PETG preset; override on the slicer side if needed). Save.

#### Additional section

| Field | Description |
|---|---|
| **Empty Spool Weight** | Pick from the [Spool Catalog](#spool-catalog) (90+ entries) or enter manually — used for accurate remaining-weight calculation. |
| **Remaining Weight** | Live `label_weight - weight_used` with a reference maximum bar. |
| **Cost per kg** | Per-spool cost; feeds [cost tracking](#cost-tracking) and archive cost roll-ups. |
| **Note** | Free-text. |

### PA Profile tab

The second tab links pressure-advance (K-factor) calibration profiles to the spool. Auto-select matches profiles by brand + material + subtype across all your printers + nozzles, with the matches grouped by printer + nozzle (left / right for dual-nozzle):

- **Auto-select** — fills the matrix from your existing K-profiles automatically.
- **Grouped view** — collapsible printer headings, each with per-nozzle (L / R) sub-rows.
- **K-factor values** displayed inline so you can sanity-check before saving.
- **Per-printer override** — pick a different profile for one printer if you have brand-specific calibration values that differ between machines.

See [K-Profiles](kprofiles.md) for the calibration workflow that produces these profiles.

## :material-format-list-checkbox: AMS slot assignments

Once a spool exists, you can park it in a specific AMS slot on a specific printer. The right-side AMS panel on each printer card shows the four slots (or eight, on AMS-HT) and lets you drop a spool into each slot.

Behind the scenes, this is the `spool_assignment` table — one row per `(printer, ams_id, tray_id)` triple. Two assignments to the same physical slot can't exist simultaneously; assigning a new spool releases the previous one (which goes back to "available, not in any printer").

Two extra niceties:

- **RFID auto-assign** — Bambu spools with intact RFID tags get matched to the catalog the moment the AMS reads the tag. If a tag points at a known catalog entry but no inventory row exists yet, BamDude offers to create one inline. If the tag is unknown (third-party, custom), you can bind it to an existing spool to skip the manual look-up next time.
- **Auto-tracking new Bambu spools** — when an AMS RFID matches no existing tray UUID, BamDude first looks for an **untagged** spool with the same material + colour + brand (`Bambu` / `Bambu Lab` / unspecified) and attaches the RFID to it. So a Quick-Add stock entry you logged ahead of time gets reused (your weight, notes, cost data are preserved) instead of producing a duplicate. If no match is found, a fresh inventory row is created from the AMS data.
- **Drying schedules + AMS humidity tracking** — see [AMS & Humidity](ams.md) — the inventory and AMS pages share state so a "drying" spool is visibly marked as in-progress in both places.

### Stable assignments on startup

Spool assignments are preserved across BamDude restarts by **spool ID**, not slot ID. If the AMS reconnects in a different order at boot — slot 3's RFID lands in what was slot 1 last session, etc. — BamDude restores by RFID identifier so the right spool stays bound to the right physical tray, no manual fix-up. If the same spool is still in the same physical slot (verified by RFID), no reconfigure command is sent to the printer.

### Configure AMS Slot vs Assign Spool

These two actions look adjacent in the slot menu but do different things. Use the table below when in doubt:

| Action | What it changes | Lifetime | When to use |
|---|---|---|---|
| **Configure Slot** | Tells the **printer** which filament profile (temperatures, flow, pressure advance) to use for that physical slot | Until the slot is reconfigured or RFID overwrites it | "I just loaded a third-party PETG into slot 1 — set the profile so the printer uses the right temps." |
| **Assign Spool** | Tells **BamDude** which inventory row to bill for consumption from that slot — and **also** runs Configure Slot using the spool's filament profile, colour, and K-profile | Until reassigned or the AMS detects a different RFID | "Track which physical spool is in which slot so usage / cost are billed correctly." Works on both empty and configured slots. |

Assigning a spool is the simplest workflow — it handles tracking + printer configuration in one step. Use Configure Slot directly only when you want to override settings or set up a slot without an inventory spool.

## :material-water-percent: Automatic consumption tracking

Every print BamDude dispatches reads the per-filament `weight` from the source 3MF. On `print_complete`, the dispatched grams are deducted from the spool that was assigned to the matching AMS slot at the time the print started:

- The `spool_usage_history` table records every deduction (one row per print × per spool).
- `spool.used_grams` is the running total.
- `spool.weight - spool.used_grams` is what's left.

The inventory page colour-codes each spool by remaining percentage, with a configurable **low-stock threshold** (Settings → Inventory). When a spool drops below the threshold, the matching `filament_low` notification fires (subscribe to it under whichever providers you care about).

If a print fails partway through, the deducted amount is the slicer-estimate × completion ratio (best effort) rather than the full estimate. External-print fallback archives — the ones from prints started directly on the printer touchscreen — get reconciled the same way once their 3MF is recovered.

### Usage tracking detail

The deduction pipeline is more nuanced than a flat "subtract slicer estimate at print end". BamDude picks the most accurate source available per scenario:

| Scenario | Primary source | Fallback |
|---|---|---|
| **3MF available + completed print** | Per-filament `used_g` from the 3MF's `slice_info.config.json`, mapped to physical AMS trays via the `ams_mapping` captured from the MQTT print command | — |
| **3MF available + failed/aborted partial print** | Per-layer G-code analysis: how many grams went through each filament up to the layer where the print stopped | Linear scaling = `total × completion_ratio` if per-layer data isn't parseable |
| **Slicer-initiated print** (BambuStudio / OrcaSlicer / Handy) | `ams_mapping` captured from the live MQTT print command, ensuring the right tray is billed regardless of which app started it | — |
| **Single-filament print** | The printer's currently-active tray | — |
| **G-code-only print, no 3MF** | AMS `remain%` delta between print start and end (integer-precision, ~10 g per 1 % step on a 1 kg spool) | — |
| **External print, fallback archive recovered later** | Re-uses the 3MF source the moment recovery completes, retroactively reconciling the deduction | — |

#### Mid-print spool change semantics

If you re-assign a spool to a slot **during** a print:

- BamDude compares the assignment-change timestamp to the print-start timestamp.
- If the change happened **after** print start, the live assignment is used — i.e. consumption flips to the new spool from the swap point onwards.
- The portion already printed before the change stays billed to the previous spool.
- If no mid-print change happened, the snapshot taken at print start is preserved and the full deduction goes to that spool.

This makes mid-batch refills work correctly without manual reconciliation: load a fresh spool when one runs low, re-assign it in BamDude, and the rest of the print is billed to the new spool.

---

## :material-currency-usd: Cost Tracking

Every spool can carry a per-kg cost; BamDude rolls it up into per-print, per-archive, and per-project cost stats.

### Setting cost-per-kg

| Where | Field | Notes |
|---|---|---|
| Spool form → Additional section | **Cost per kg** | Per-spool override; takes precedence over the global default |
| **Settings → Filament** | **Default Filament Cost** | Per-kg fallback when a spool has no cost set (default 25.00 in `default_filament_cost`) |
| **Settings → Filament** | **Currency** | Symbol used everywhere — USD, EUR, GBP, MYR, and ~25 more |

### How costs are calculated

For every print BamDude derives the per-spool cost as it deducts grams:

```
cost = (weight_used_grams / 1000) × cost_per_kg
```

- Per-spool `cost_per_kg` wins; if unset, the global default is used.
- The calculated cost is stored on each `spool_usage_history` row and aggregated into `print_archive.cost`.
- The print modal preview shows a **real-time cost estimate** based on loaded spools + their cost/kg before you start the print.
- Archive cards display total filament cost; the inventory table has a sortable Cost/kg column (hidden by default — enable via column settings); [Stats](stats.md) totals cost across all prints.

### Recalculating costs

If you update spool prices or add cost data retroactively, the **Recalculate Costs** button on the Archives page re-derives every archive's cost using the current spool data, in this priority order:

1. `spool_usage_history` records joined to `archive_id` (most accurate, per-spool actuals).
2. Legacy usage records joined by print name (for older archives without the FK link).
3. Filament catalog prices (when no usage records exist at all).

!!! tip "Set costs early"
    For accurate cost tracking, set `cost_per_kg` on each spool when you add it to inventory. The default is a rough estimate — individual spool prices give you precise per-print data and make the **Recalculate Costs** button useful.

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

### Sync Weights from AMS (recovery tool)

When the built-in inventory is in use, **Settings → Filament** exposes a **Sync Weights from AMS** button below the mode selector. It force-syncs all inventory spool weights from the live AMS `remain%` sensor values on currently-connected printers.

Use this **only** to recover from corrupted weight data — for example, if a printer power-off event reset all spools' tracked grams to zero. The sync overwrites stored `weight_used` values with what the AMS reports right now. Printers must be online for the sync to read sensor values.

!!! warning "Low resolution — recovery only"
    AMS `remain%` is integer-precision (1 % steps = ~10 g for a 1 kg spool). For day-to-day tracking, rely on the automatic 3MF-based deduction described above — it's accurate to the gram. **Sync Weights from AMS** is a recovery tool, not the normal accounting path.

### Spool Catalog

Pre-defined empty-spool weights for quick selection when adding spools. Ships with 90+ entries covering the common manufacturers (Bambu Lab cardboard core, eSun, Polymaker, Overture, etc.). Lives at **Settings → Inventory → Spool Catalog**.

| Button | Description |
|---|---|
| **Export** | Download the entire catalog as a JSON file for backup or community sharing |
| **Import** | Load a JSON file to add entries. Duplicates (same name) are skipped automatically |
| **Reset** | Restore the built-in default catalog (overwrites all entries — confirmation required) |
| **+ Add** | Manually add a new spool-weight entry |

#### Import format

```json
[
  { "name": "Brand - Spool Type", "weight": 210 }
]
```

### Colour Catalog

The single source of truth for resolving hex colours to display names — the AMS popover, the inventory list, the print-modal filament cards, the Reprint AMS-mapping modal, and auto-provisioned inventory entries all look up names from this table. Ships with 600+ colours across 20 brands.

| Button | Description |
|---|---|
| **Export** | Download the entire catalog as JSON |
| **Import** | Load a JSON file to add colours. Duplicates (same manufacturer + colour name + material) are skipped |
| **Sync** | Pull new colours from [FilamentColors.xyz](https://filamentcolors.xyz/) — a community database of measured filament colours. **Adds new entries only**, never modifies existing ones |
| **Reset** | Restore the built-in default catalog (overwrites all entries) |
| **+ Add** | Manually add a new colour entry (manufacturer, colour name, hex, material) |

#### Import format

```json
[
  { "manufacturer": "eSUN", "color_name": "Silk Gold", "hex_color": "#C48E2F", "material": "PLA Silk" }
]
```

!!! info "Display-name authority"
    BamDude resolves every spool colour name by looking up the hex in this catalog (Bambu Lab entries are preferred when the same hex is registered under multiple brands). There is **no** hardcoded `tray_id_name` → name mapping anywhere in the codebase — adding or editing a colour here is the supported way to correct or extend display names. Restart-free: the frontend refetches the catalog on next page load.

---

## :material-frequently-asked-questions: FAQ

### My material isn't in the dropdown (e.g. PCTG, PHA, PP)

Type the material name directly into the Material field. A green *Use custom material* option appears at the bottom of the dropdown — click it. Custom materials work like built-ins for tracking, usage history, filtering, and notifications.

### Do I need to pick a slicer profile for every spool?

No. Use **Quick Add (Stock)** mode to add spools with just material + weight. Stock spools track weight, usage, and cost; you can edit them later to assign a profile. In full mode the Slicer Preset is required — pick the closest available preset (a generic *PETG Basic* for a third-party PETG, for example), or import your custom OrcaSlicer profiles via [Local Profiles](local-profiles.md) so they appear in the dropdown.

### I have different printers (P1S + H2D) and nozzles — do presets matter?

The spool inventory itself is **printer-agnostic**. Add a spool once, assign it to any printer's AMS slot. Printer-model filtering only kicks in when you **Configure AMS Slot** (telling the printer which profile to use) — there the preset list is filtered by printer model so you only see compatible profiles.

### Is inventory only for loaded spools?

No. The inventory tracks **all your spools** — loaded and unloaded. You can log every spool you own, even ones sitting on a shelf. The *In Printer* summary card shows how many are currently loaded; the rest are tracked just the same (weight remaining, usage history, cost, drying schedule).

### What's the difference between Assign Spool and Configure Slot?

See [the comparison table](#configure-ams-slot-vs-assign-spool) above. Short version: **Assign Spool** does both — links the inventory row for tracking and configures the slot using the spool's profile. **Configure Slot** only does the printer-side configuration. Use Assign for normal workflow; use Configure when you want to override settings or set up a slot without an inventory spool.

### Where do the slicer profiles come from?

Three sources, checked in priority order: **Bambu Cloud** (your synced presets, including custom ones) → **Local Profiles** (OrcaSlicer imports) → **Built-in Fallback** (~150 Bambu Lab filament IDs). Even without cloud login, the latter two ensure the preset list is never empty. See [Where presets come from](#where-presets-come-from) for details.
