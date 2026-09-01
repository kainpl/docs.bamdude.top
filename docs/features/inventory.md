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

- **Search box** — matches the spool **name your display-name template composes**, not just the raw columns behind it, so anything the list shows is findable: with a template of `{brand}/{material}`, typing `LU/PET` finds it. Brand, material, colour, subtype, note and slicer preset are always matched too, as are the spool's **id** and **lot number** — those two whatever your template says, because they are the numbers written on the reel. Every token has to match something, so `SUN Bl` finds a SUNLU Black spool. Press `/` from anywhere on the page to focus it.
- **Material dropdown** — single-select.
- **Colour dropdown** — single-select. Options are the colours you actually have in stock — built from your existing (non-archived) spools — and grouped by the resolved colour-catalog name, so two near-identical hexes that both read as "Cobalt Blue" filter together regardless of brand. The dropdown only appears once at least one in-stock spool has a resolvable colour.
- **Storage Location chip** — narrows the spool list to a single storage location from the [managed locations catalog](#storage-locations-catalog), so you can see just the spools kept in one box / shelf / dry-box.
- **Status tabs** — Active / Archived / All, plus quick filters Used / New, plus stock filter All / Stock (no slicer profile) / Configured (has slicer profile).
- **Brand dropdown** — single-select.
- **View modes** — **Table** (data-focused, sortable columns), **Cards** (visual swatches), or **[History](#history)** (every consumption record on the farm). *Forecast* sits beside them when you have permission for it.
- **Group similar** — toggle that visually collapses identical unused / unassigned spools into one expandable row with a count badge (e.g. *5 identical spools*). Grouping key is `manufacturer + material + colour name + label_weight + subtype + lot` — because lot is part of the key, a batch created with **auto-numbered lots** (see below) stays as distinct cards rather than collapsing; only same-lot (or lot-less) copies merge. Used or AMS-assigned spools always appear individually so you can tell which physical spool is in which slot. Group state persists across sessions.

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

### Copy Spool — duplicate an existing row

Every spool row (cards view + table view + grouped rows) has a **Copy** button next to Edit. Clicking it opens the spool form pre-filled with everything from the source row except `weight_used`, which resets to **0** — useful when you've just bought a second / third / nth spool of an existing filament. The header reads **Copy Spool** instead of Edit Spool, the footer button reads **Copy Spool** instead of Save. **Quick Add (the bulk `quantity` toggle) is available in copy too**, so you can clone a spool into a whole batch in one go — each copy still starts fresh (usage reset to 0, no RFID tag carried over). The source row is untouched; saving creates brand-new spools each with their own `id`. Spool form is printer-agnostic, so the same Copy button works in Spoolman mode — the existing create-mutation routing handles both paths.

### Bulk edit — change many spools at once

The toolbar's **Bulk edit** button (internal inventory only) opens a dialog to change a field across several spools at once. Pick which spools to edit (it starts with all the currently-filtered ones; deselect any you want to leave alone in the left-hand list) and **tick the fields to apply**: slicer preset, material, brand, subtype, label weight, colour, empty-spool weight, date of purchase, diameter, cost/kg, note, category, low-stock threshold, extra colour stops, visual effect, storage location.

Each ticked field pre-fills only when the selection already shares one value (otherwise it shows *"— varies —"*); **only the fields you tick are written**, the rest are left exactly as they were, and **consumed weight and RFID tags are never touched**. Inputs mirror the single-spool form — preset / effect / diameter / empty-spool / storage location are dropdowns; material / brand / subtype autocomplete from everything the system knows (slicer presets + colour catalog + built-ins, not just the selected spools); the colour list comes from your colour catalog filtered by the brand + material being applied and refreshes when you change them.

### CSV import / export

Two buttons in the inventory header move whole spool lists in and out as CSV — handy for backing up your inventory, editing it in a spreadsheet, or bulk-loading a freshly-received order.

- **Export** downloads a date-stamped `bamdude_inventory_YYYYMMDD.csv`, one row per active spool.
- **Import** bulk-adds spools from a CSV. Instead of writing straight away, it first shows a **preview table** that marks every row as *valid*, *error*, or *skipped* — and flags rows where a colour was auto-filled from the colour catalogue, or where a matching spool already exists — **before anything is written**. A confirm click then saves only the valid rows.

CSV headers are case- and spacing-tolerant, so a column titled `Label Weight`, `label_weight`, or `LABELWEIGHT` all resolve the same way. Only `material` is required; every other column is optional, and the same validation as the manual add-spool form applies to each row.

CSV import/export is **local-inventory only**. In **Spoolman mode** both buttons are disabled, with a hint pointing you at Spoolman's own CSV tools instead.

### Storage locations catalog

Where a spool physically lives — a shelf, drawer, or dry-box — is a **managed catalog**, not free text. A **Locations** button in the inventory header opens the catalog manager where you create, rename, and delete locations; the spool form's **Storage location** field is a dropdown drawn from that catalog, with an inline *create new* option so you never leave the form to add a shelf.

- **Rename propagates** — renaming a location updates every spool assigned to it in one write, so there's no orphaned free-text drift.
- **Delete is guarded** — a location with spools still assigned can't be deleted until you move those spools elsewhere.
- **Legacy free-text migrates** — on first launch after upgrade, BamDude backfills the catalog from the distinct free-text storage values already on your spools and links each spool to its matching catalog row.
- **Spoolman sync** — in Spoolman mode the catalog imports Spoolman's distinct locations, and a rename cascades to Spoolman's per-spool `location` field (rolled back locally if Spoolman rejects it, so the two never diverge).

Viewing the catalog needs `inventory:read`; creating / renaming / deleting a location needs `inventory:update`.

### Editing a spool created by Quick Add, CSV import or RFID

Those three routes create a spool with a material and little else — no slicer preset, no brand, no subtype. **Editing and copying now ask for exactly what the server asks for: the material.**

Reopening such a spool in Edit used to demand preset, brand *and* subtype before it would save anything, so changing its shelf location, its cost or a note was simply impossible — and the Quick Add toggle that waives those fields only exists when creating. Copy Spool hit the same wall with no way around it at all.

Preset, brand and subtype stay visible and editable; the little `*` markers appear only where a field is genuinely required.

!!! info "The brand and material lists no longer hide real products"
    They used to filter themselves down to the brand/material pairs the colour
    catalogue happens to know. Elegoo is catalogued for PLA only — so **Elegoo
    ASA**, a real filament you can buy, looked impossible to enter.

    Both lists now always offer everything: the known pairings ranked first under
    **Suggested**, the rest under **All**. A spool's own brand or material is always
    present in its own dropdown, even if nothing else has heard of it.

### The spool links to a filament family (0.5.5)

The per-variant Slicer Preset dropdown is gone: the spool form carries a single **Filament family** picker — the same identity Bambu Studio uses (`filament_id`), shared with the AMS slot dialog and the K-profile editor. The spool is printer-agnostic by construction now: per-printer preset variants are the *family's* business, resolved per printer at slot-assignment and slicing time. Picking a family prefills material and brand; custom families carry a badge saying which cloud they came from; a "Create new family…" row opens the [Create Filament dialog](filament-families.md#creating-your-own-filament) without leaving the form. Existing spools were migrated onto families automatically on the first start after upgrading. Full model: [Filament Families](filament-families.md).

### Per-spool category & low-stock override

Two extra optional fields on the spool form fine-tune both filtering and alerting:

| Field | Effect |
|---|---|
| **Category** | A free-form short tag — e.g. `PETG`, `ABS`, `TPU`, `paint`, `experimental`. Inventory page renders a category-filter chip strip at the top so you can show "only TPU" or "only experimental". The chip strip only appears once at least one spool has a category set, so it doesn't clutter the page on day one. The special chip `__none__` filters to spools with no category. |
| **Low-stock threshold (override)** | Per-spool override for the global `low_stock_threshold`. Use this when a particular spool needs an earlier warning (e.g. an expensive PA — 50% remaining means time to order; cheap throwaway PLA can wait until 10%). Empty = inherit the global setting. |

Both columns are surfaced in the inventory table and editable inline.

### Full form: Filament Info tab

The "+ Add Spool" form has two tabs. The first one — Filament Info — covers everything needed to identify the spool and resolve its filament family.

| Field | Description |
|---|---|
| **Filament family** | Search-and-select the family (built-in catalog + your cloud/local/custom families — see [Filament Families](filament-families.md)). Selecting one auto-fills *Material* and *Brand*. |
| **Material** | PLA, PETG, ABS, ASA, TPU, PA, PC, … — accepts custom values, see [Custom materials](#custom-materials). |
| **Brand** | Filament manufacturer; auto-completes from previously-seen brands. |
| **Subtype** | Basic, Matte, Silk, HF, Metal, CF, … |
| **Label Weight** | Net weight as printed on the spool (default 1000 g; AMS-HT cardboard core ~250 g). |
| **Quantity (bulk)** | 1–100 spools created in one operation. Useful for "I bought a 5-pack of PLA" scenarios — every spool shares the same material / colour / weight / cost (lots can differ, see **Lot** + auto-numbering below). |
| **Colour** | Visual picker with shade + opacity + finish pickers. Recent-colours strip + brand palettes. |
| **Extra colours** | Optional. Comma-separated list of 2–8 hex stops (e.g. `EC984C,#6CD4BC,A66EB9,D87694`) for multi-colour spools. Renders the swatch differently based on the **Effect** value below — gradient blend, hard-split bars, or colour-wheel pie. Format matches 3dfilamentprofiles.com so paste-and-go works. |
| **Effect** | Layered on top of the colour swatch — does **not** change the slicer profile. Full enumeration: surface effects (*Sparkle*, *Wood*, *Marble*, *Glow*, *Matte*) paint a CSS overlay; sheen variants (*Silk*, *Galaxy*, *Rainbow*, *Metal*, *Translucent*) carry a soft sheen; structural variants drive the colour-layer shape — *Gradient* = smooth 135° blend, *Dual Color* / *Tri Color* = hard-split horizontal bars (each stop occupies its own contiguous segment, no diagonal blend), *Multicolor* = conic-gradient colour-wheel pie. The form has a live preview pane below the dropdown so you see the effect before save. |

#### Quick Add (Stock) mode

Toggle **Quick Add (Stock)** at the top of the form to switch to a minimal mode that hides the slicer preset + PA Profile tab. Only **Material** (required), **Brand**, **Subtype** (both optional), **Label Weight**, **Quantity**, and **Colour** are shown — perfect for inventorying a freshly-arrived order before you've decided which slicer profile to associate.

Quick-Add spools are called **stock spools** — they track weight and usage like any other spool, but they aren't linked to a printer filament profile. You can edit a stock spool later to assign a slicer preset (it becomes a *configured* spool at that point) or filter to just the stock pile via the inventory's stock filter.

The **Quantity** field is only shown in Quick Add and creates that many spools in a single transaction. Quick Add also shows the **Lot** field together with an **Auto-number lots (+1 per copy)** checkbox:

- **Auto-number ticked** — the copies are numbered sequentially **starting from the Lot value you entered**: Lot `5` × Quantity `3` → three spools with lots **5, 6, 7**. Leave Lot empty and numbering starts at 1.
- **Auto-number unticked** — every copy shares the single Lot value you typed (or no lot at all).

!!! tip "Bulk buying"
    A 5-pack of PLA from the same batch → Quantity = 5, Lot = 1, **Auto-number lots** on → five spools with lots 1–5, shown as five distinct cards (lot is part of the grouping key). Want them collapsed into one *5 identical spools* row instead? Leave the lot empty (or auto-number off) so the copies are truly identical, then use the **Group similar** toggle.

#### Where families come from

The **Filament family** picker draws on two tiers, both resolved locally (see [Filament Families](filament-families.md)):

| Tier | Description |
|---|---|
| **Built-in catalog** | Every official Bambu filament family, distilled from Bambu Studio and OrcaSlicer themselves. Always available, no login needed. |
| **Your own** | Families behind your Bambu Cloud / Orca Cloud presets (mirrored server-side in the background), your local imports, and families you created in BamDude. Badged with their origin. |

Browsing shows *your* families first (the ones behind your presets, spools and calibrations); typing searches the full catalog of both ecosystems, deduplicated. The list is never empty, cloud or no cloud.

Custom presets that inherit from Bambu presets (e.g. *# Overture Matte PLA @BBL H2D*) are fully supported — the family is resolved from the inheritance chain.

#### Custom materials

The material dropdown ships with the baseline set — PLA, PETG, ABS, TPU, ASA, PC, PA, PVA, HIPS — plus carbon-fibre, glass-fibre and specialty variants (PLA-CF/GF, PLA Aero, PETG-CF, ABS/ASA-GF, ASA-CF, PCTG, PAHT-CF, PA6-CF/GF, PPS/PPS-CF/GF), grouped by material family. If your material still isn't listed (e.g. PHA, PP, PVDF), type it directly into the Material field — a *Use custom material: …* option appears at the bottom of the dropdown. Click it to commit.

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
- **Nozzle diameter badge** on each row. Profiles are fetched for *every* nozzle size a printer reports, so on a multi-nozzle machine one filament can contribute two rows that share a name — the diameter is what tells them apart. A printer that has not yet reported its hardware is queried for 0.4 mm, as before.
- **Per-printer override** — pick a different profile for one printer if you have brand-specific calibration values that differ between machines.

See [K-Profiles](kprofiles.md) for the calibration workflow that produces these profiles.

## :material-checkbox-multiple-marked: Mass actions

Every row on the Filament tab has a checkbox. Tick one, and a toolbar appears above the list with **Edit · Print labels · Reset usage · Archive** (or **Restore**, on the Archived tab) **· Delete**.

Four ways to select:

| Control | Selects |
|---|---|
| Row checkbox | That spool |
| Group checkbox | Every spool in that group (shows a dash when only some are ticked) |
| Header checkbox | Every spool **on the current page** |
| **Select all N matching the filter** | Every spool the current filter returns, including rows on other pages |

The last one is deliberately a separate, explicit action rather than the default. Editing "everything the filter shows" is convenient; *deleting* it is not something that should happen because of a checkbox you could not see. For the same reason the selection clears itself whenever you change the filter, the search box, the tab or the grouping — a toolbar that says "12 selected" over a list which no longer contains those spools is how a bulk delete lands on the wrong rows.

Archive, Restore and Delete ask for confirmation first.

All of this works in **Spoolman mode** as well as with the built-in inventory. Because Spoolman is a separate service that can be briefly unreachable, individual rows can fail: when that happens you get an honest **"7 done, 2 failed"** rather than a success message, and the selection is kept so you can retry the rest.

!!! tip "The Edit dialog shows what it is about to change"
    The bulk-edit dialog lists the exact spools in the selection. It is read-only — the choosing happens on the page — but it is worth reading before you apply a field to forty spools.

## :material-format-list-checkbox: AMS slot assignments

Once a spool exists, you can park it in a specific AMS slot on a specific printer. The right-side AMS panel on each printer card shows the four slots (or eight, on AMS-HT) and lets you drop a spool into each slot.

Behind the scenes, this is the `spool_assignment` table — one row per `(printer, ams_id, tray_id)` triple. Two assignments to the same physical slot can't exist simultaneously; assigning a new spool releases the previous one (which goes back to "available, not in any printer").

Two extra niceties:

- **RFID auto-assign** — Bambu spools with intact RFID tags get matched to the catalog the moment the AMS reads the tag. If a tag points at a known catalog entry but no inventory row exists yet, BamDude offers to create one inline. If the tag is unknown (third-party, custom), you can bind it to an existing spool to skip the manual look-up next time.
- **Auto-tracking new Bambu spools** — when an AMS RFID matches no existing tray UUID, BamDude first looks for an **untagged** spool with the same material + colour + brand (`Bambu` / `Bambu Lab` / unspecified) and attaches the RFID to it. So a Quick-Add stock entry you logged ahead of time gets reused (your weight, notes, cost data are preserved) instead of producing a duplicate. If no match is found, a fresh inventory row is created from the AMS data.
- **Drying schedules + AMS humidity tracking** — see [AMS & Humidity](ams.md) — the inventory and AMS pages share state so a "drying" spool is visibly marked as in-progress in both places.

!!! note "Turn off silent creation for unknown tags"
    Auto-creation of a fresh row for an unrecognised RFID is governed by **Settings → Filament → Auto-add unknown RFID spools** (`auto_add_unknown_rfid`, default **on**). Switch it off and an unknown tag instead surfaces a **confirmation card** — material and colour pre-filled from the AMS read — so nothing is written to inventory until you approve it. Handy if you pre-create spools by hand and don't want duplicates.

!!! tip "Look up a spool by its tag"
    NFC integrations can resolve a single spool without listing the whole inventory: `GET /api/v1/inventory/spools/by-tag?tray_uuid=<uuid>` (or `&tag_uid=<uid>`). Matching is hex-normalised and case-insensitive; archived spools are excluded unless you pass `include_archived=true`. It's readable with either `inventory:read` or `inventory:update`, so a Manage-Inventory API key can dedupe a scan without the global read scope.

### Stable assignments on startup

Spool assignments are preserved across BamDude restarts by **spool ID**, not slot ID. If the AMS reconnects in a different order at boot — slot 3's RFID lands in what was slot 1 last session, etc. — BamDude restores by RFID identifier so the right spool stays bound to the right physical tray, no manual fix-up. If the same spool is still in the same physical slot (verified by RFID), no reconfigure command is sent to the printer.

### Configure AMS Slot vs Assign Spool

These two actions look adjacent in the slot menu but do different things. Use the table below when in doubt:

| Action | What it changes | Lifetime | When to use |
|---|---|---|---|
| **Configure Slot** | Tells the **printer** which filament profile (temperatures, flow, pressure advance) to use for that physical slot | Until the slot is reconfigured or RFID overwrites it | "I just loaded a third-party PETG into slot 1 — set the profile so the printer uses the right temps." |
| **Assign Spool** | Tells **BamDude** which inventory row to bill for consumption from that slot — and **also** runs Configure Slot using the spool's filament profile, colour, and K-profile | Until reassigned or the AMS detects a different RFID | "Track which physical spool is in which slot so usage / cost are billed correctly." Works on both empty and configured slots. |

Assigning a spool is the simplest workflow — it handles tracking + printer configuration in one step. Use Configure Slot directly only when you want to override settings or set up a slot without an inventory spool.

### Stock forecasting + Logistics view

A third inventory tab next to **Table** / **Cards** that turns the raw `spool_usage_history` table into reorder intelligence:

- **Daily-consumption rate** — exponentially-weighted moving average with a 30-day half-life, computed per **colour group** (material / subtype / brand / colour name). Five colours of the same PLA Basic become five independent forecast rows, each with its own runway and reorder date — so running low on black doesn't hide behind a full spool of white. One spool of recent prints weighs more than a year-old burst.
- **Days-left projection** — current stock divided by daily rate, with a 95%-service-level safety stock factored in (`σ × √lead_time × 1.65`).
- **Reorder-by date** — when to place the order so the new spool arrives *before* you run out, given the configured lead time.
- **Filter + count controls** — **Material** and **Brand** dropdowns narrow the table; a dedicated **Spools** column shows how many physical spools back each colour row. Every column is sortable.
- **Per-colour expanded editors** — lead-time-days, safety-margin (dual-unit days|grams), alert-snooze toggle. Each setting persists across sessions in the `filament_sku_settings` table; colours with no settings yet fall back to the global lead-time floor (Settings → Inventory → **Forecast global lead time**). Overrides you saved before the colour split are carried onto the matching colour rows on first load, so no per-SKU tuning is lost in the migration.
- **Top-5 chart** — stacked-area, multi-series projection of the five fastest-burning colours with ROP reference lines. Timeframe toggle: 1W / 1M / 6M.
- **Shopping list (Logistics view)** — separate panel below the forecast table. Add SKUs to a `pending → purchased → received` queue. Marking an item *received* auto-creates `category='Stock'` spools via bulk-create (uses the average historical spool weight). CSV export + clear-all helpers.
- **Notification toggles** — two new notification-provider events appear in **Settings → Notifications → Inventory Alerts**: *Reorder Alert* (SKU crossed reorder point) and *Stock Break Alert* (will run out before lead time). **These toggles are currently visual-only on the provider** — the forecast panel surfaces alerts in-app; a future scheduled aggregator can fire them via the existing templates without a schema change.

The forecast tab is **hidden in Spoolman mode** because BamDude proxies the spool list there and doesn't populate the per-print usage history. To use forecasting, run BamDude in local-inventory mode.

Permissions: `inventory:forecast_read` (see the panel) and `inventory:forecast_write` (modify SKU settings + shopping list) are added to existing groups automatically on upgrade — viewers get read, operators get both.

### Pre-load assignment (weigh-then-assign)

You can assign a spool to a slot **before** loading the filament — useful when you've just weighed a fresh spool and want to track it from the very first print. When the target slot is empty (`tray_type` blank in the AMS data), BamDude:

- Persists the `SpoolAssignment` row immediately so the inventory page reflects the pairing.
- **Defers** the `ams_filament_setting` + `extrusion_cali_sel` MQTT publish — Bambu firmware silently drops both commands for unloaded slots (there's no filament context for the K-profile / pressure-advance index to attach to), and pushing them anyway would close the modal with a misleading "Assigned!" while the slicer kept showing default-PLA forever.
- Surfaces this in the confirmation toast: *"Spool assigned. The slot will be configured when you insert the filament."*
- Replays the full configuration automatically the moment the slot transitions to loaded. The "loaded" signal is the AMS state code (`state == 11`, "filament fed to extruder"), not the tray's material string — so 3rd-party spools without readable RFID (which report state=11 but keep `tray_type=""`) trigger the replay too. After the replay the assignment fingerprint is stamped, so subsequent AMS pushes don't re-fire.

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

### Runouts close the spool at exactly empty (0.5.5)

A filament runout is the one moment reality reports an exact figure: the spool holds **0 g**, whatever the books said. BamDude listens for the printer's **own runout codes** — an AMS slot waiting for new filament, the AMS auto-switching to a backup slot, or the external holder running dry — and turns each into precise accounting. Jams and tangles are *never* mistaken for runouts (only the exact firmware codes count), and a spool whose slot can't be positively identified is never touched.

What happens, in order:

1. The runout is journalled at the exact layer, with the spool that was feeding **frozen at that moment**.
2. You get the **Filament runout** notification (enable it on your provider): either *"waiting for filament — assign the replacement in BamDude so the rest of the print is booked to the right spool"*, or the informational *"switched to the backup slot"*.
3. Load the new spool. On RFID spools BamDude spots the new tag by itself; on tagless spools (external holders included) **assigning the replacement to the slot is the signal** — do it any time before the print ends.
4. At completion the print is split **at the runout layer** (per-layer G-code accuracy): each spool is billed only the segment it actually fed. Then the spent spool gets one final **Runout close-out** row for whatever the books never saw, so its history sums to exactly the label weight — remaining hits precisely zero.

**Worked example.** Spool A's books say 2 kg remaining; a 600 g print runs out mid-way, at a point where the print had consumed 250 g; you load spool B and finish.

| Row | Spool | Grams |
|---|---|---|
| Print segment up to the runout layer | A | 250 g |
| Print segment after | B | 350 g |
| Runout close-out (orange row in history) | A | **+1750 g** |

A ends at exactly 0 g remaining (250 + 1750 = its 2 kg label); B carries only its honest 350 g. The archive still records the print as 600 g at 600 g's cost — the close-out is the spool's lifetime drift being recognised, not this print's consumption. If you *don't* assign B, the whole 600 g stays on A and the close-out shrinks to 1400 g — A still ends at zero, B stays untracked, which is why the notification nudges you to assign.

Two runouts of the same slot in one long print (two short reels back-to-back) are handled as separate episodes, each with its own boundary and close-out. Everything works identically in Spoolman mode. Tune it under **Settings → Filament → Usage accuracy**: the close-out toggle, an optional per-auto-switch purge charge (the emergency purge isn't in the slicer's estimate), the two-way AMS sync below, and how long the per-print event journal is kept for troubleshooting (72 h default).

### Two-way AMS weight sync for tagged spools (0.5.5)

For spools with a valid Bambu RFID tag, idle AMS readings can now correct the books **downward** as well as upward — the firmware's own remaining estimate is the same number Bambu Studio mirrors into its filament manager. A downward correction is deliberately cautious: the same value must repeat across two reports at least a minute apart, so a garbled report after a reconnect can never rewrite a spool. Untagged spools are never touched by this path.

### Live "filament so far" (0.5.5)

While a print runs, the expanded printer card shows how much filament it has consumed so far — per-layer G-code accuracy, per slot on multicolour jobs, refreshed twice a minute — and says **"split across spools"** once a runout has genuinely divided the print between reels. Display-only: inventory is still written once, at completion.

#### Mid-print spool change semantics

- **After a runout**, attribution is split at the runout layer as described above — the journal owns the boundary.
- **Without a runout** (you re-assign a slot mid-print to correct a wrong link), the live assignment wins and the whole print is billed to the newly-assigned spool. That is the correction semantic: BamDude assumes the link was wrong from the start, not that you swapped reels.

### Reset counter

Each spool has an eraser action — **Reset counter** — that zeroes the displayed **Total Consumed** counter (a reset-all variant resets every spool's counter at once). The button, its confirmation dialogs, and tooltips all read "Reset counter". Crucially, this only zeroes the *displayed* consumption figure — the spool's remaining weight is **not** changed (the old "Reset usage" name misleadingly implied it wiped the used grams). Mechanically it records a `weight_used_baseline`, so reported consumption becomes "used since the last reset" rather than lifetime — useful when you refill or swap a roll but keep the same inventory entry instead of creating a new one.

The backing API endpoints were renamed accordingly — the per-spool and reset-all paths now end in `.../reset-consumed-counter` (previously `.../reset-usage`).

### The History view — every consumption record at once {#history}

The inventory's third view mode, **History**, between Cards and Forecast, lists the whole farm's usage records rather than one spool's: what was printed, off which spool, on which printer, how many grams, what it cost, and how it ended — newest first.

A spool's own tab answers "where did this reel go". This answers "where did the filament go", which is usually the question you start from. It is the same records either way; only the entry point differs.

Every part of the list is computed by the **server** — the page, the sort order, the filters, the search and the totals. A farm with a year of prints has six figures of records here and the browser never downloads them.

- **Search** — the page's own search box serves this view too. Same box, same place; it just searches events, reaching the print's name, the spool and the printer at once.
- **Filters** — printer (including *No printer*, for records charged to no machine), material, brand, outcome, and a date range. Plus the spool's own state: **All / Active / Archived** and **All / In Printer / On the shelf**. Those last two carry an *All* setting the spool table has no equivalent of, and it is the default: retiring or unloading a reel does not un-burn what it printed, so nothing here is hidden until you ask for it to be.
- **Sorting** — any column: date, spool, print, printer, grams, percent, cost, outcome.
- **Totals** — the grams (and money) beside the filters are for the **whole filter**, not the page on screen. "What did August cost me" is one date range away.

Spools you have since archived or deleted keep their rows, marked rather than hidden — the grams they carry were still printed, and dropping them would make these totals disagree with the [archives](archiving.md). Spool names follow your [display-name template](#display-name-follows-your-template) and a retired printer reads as *Printer 5 (Archived)*, exactly as everywhere else. Clicking a spool opens it.

The view is **hidden in Spoolman mode**, where Spoolman keeps this record instead.

### Removing usage records

Each row has a hover **×** to delete just that entry — in a spool's own **History** tab and in the farm-wide History view alike; the spool tab's bulk **Clear** button does the same for that spool's whole list. Removing a record treats that consumption as if it never happened: its weight is **returned to the spool** (`weight_used` drops, so remaining weight goes back up) and the same amount is subtracted from the linked print's recorded filament, so the [Stats](stats.md) page stays in step with inventory. For a multi-colour print the deduction is per-record — removing one colour's entry only reclaims that colour's share and leaves the rest of the print intact. Handy for un-counting a mistaken or test print against a roll.

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

### Transparent / clear filament

Transparent filament is a first-class colour. The spool colour editor has a dedicated **Clear** quick-swatch, and the hex field accepts an 8-digit `RRGGBBAA` value, so you can mark a spool as fully or partially transparent. Clear spools render as a **checkerboard** swatch everywhere the colour appears — inventory cards, AMS slot indicators, the colour picker — instead of showing up as an invisible or solid-black chip.

## :material-printer: Printable PDF labels

Find a specific spool in a closet of 50 partials by sticking a label on each one. The Inventory header has a **Print labels…** action that opens a multi-select picker pre-loaded with the currently filtered spools; every inventory card and table row also has a per-spool printer icon for one-shot label printing.

Six pre-built templates:

| Template | Size | Sheet | Notes |
|---|---|---|---|
| **AMS holder (74 × 33)** | 74 × 33 mm | One per page | `ams_holder_74x33`. Fits popular Makerworld AMS Filament Label Holder inserts. Large enough for the full layout — swatch on the left, QR on the right, multi-line text in the middle (brand, material, hex, spool ID). |
| **AMS holder (75 × 55)** | 75 × 55 mm | One per page | `ams_holder_75x55`. Taller AMS-holder variant; same full layout (swatch + QR + multi-line text) with more vertical room. |
| **Box 40 × 30** | 40 × 30 mm | One per page | Common DK / Brother roll size; fits between the AMS holder and the 62×29 box label. Roomy enough for swatch + QR + full text column including hex code — good for filament-bag and storage-bin labels. |
| **Box label** | 62 × 29 mm | One per page | Sized for Brother PT/QL and Dymo small-label stock. Carries QR + storage location. |
| **Avery L7160** | 38.1 × 63.5 mm | A4, 21 per sheet | EU sheet stock. Carries QR. |
| **Avery 5160** | 25.4 × 66.7 mm | US Letter, 30 per sheet | US sheet stock. Carries QR. |

Every label carries the colour swatch (with multi-colour stripes for spools with `extra_colors`), brand in **bold** at the top so it reads at arm's length, material/subtype, the colour **hex code** (`#RRGGBB`, alpha-stripped, uppercase) so near-identical colour+material spools are still tellable apart from up close, the spool's display name, the **spool ID** as the killer at-a-glance field for telling 8 spools of "PLA White" apart, and (where the size allows) a QR code that deep-links to `/inventory?spool=<id>` so a phone scan jumps straight back into BamDude at that spool's row.

### Display name follows your template

The bold central line on each label reuses the same **Spool display name template** the Inventory page uses (Settings → Inventory → Spool display name template). So if you set the template to `{brand} {material} {color_name} (#{id})` for the inventory list, that's exactly what gets printed on each label too. The 16 placeholders (`{brand}`, `{material}`, `{color_name}`, `{remaining_pct}`, `{filament_diameter}`, `{lot}`, …) are documented in the same Settings panel that lets you edit the template.

### How the QR deeplink resolves

The QR encodes `<base>/inventory?spool=<id>`. The base is resolved in this order:

1. The `external_url` setting (Settings → Server → External URL) — preferred so a phone scan reaches your public BamDude URL rather than an internal address.
2. The `APP_URL` environment variable.
3. The current request's scheme + host (whatever you'd see in your browser when you fired the export).

For phone-scan workflows, set `external_url` once — then every label across every template prints the right deeplink.

### Picker UX for large libraries

The modal scales to large inventories with:

- **Search** — substring across the composed display name, brand, and `#ID`.
- **Material filter chips** — derived from the visible spools.
- **Select all visible / Deselect visible / Clear all** — selections survive filter changes (additive), so you can narrow to "PLA only", select all, then narrow to "PETG", and add those too.
- **Sort toggle (By ID / By colour)** — *By ID* (default) lists spools in ascending-ID order; *By colour* hue-clusters them (chromatic colours ordered by hue, achromatic neutrals ordered by lightness trailing the rainbow) so a printed sheet comes out rainbow-ordered. Session-only — resets to By ID each time you open the picker.

### Server-side rendering

PDFs are rendered server-side via ReportLab + qrcode (added as deps). Pure Python, no headless browser, output is byte-identical across browsers, Avery sheets align to <0.1 mm. Endpoints (both gated on `inventory:read`):

- `POST /inventory/labels` — local-DB spools.
- `POST /spoolman/labels` — Spoolman-backed spools (only when Spoolman integration is enabled).

Both accept `{spools: [{id, display_name?}], template}` and return `application/pdf` via streaming response. Capped at 500 spools per request.

## :material-account-multiple: Permissions

| Permission | Effect |
|---|---|
| `inventory:read` | View spool list and AMS assignments; **render PDF labels**. |
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

### Where do the filament families come from?

From the built-in catalog (every official Bambu filament, offline) plus your own — cloud-mirrored, locally imported, or created in BamDude. Even without a cloud login the list is never empty. See [Where families come from](#where-families-come-from) and [Filament Families](filament-families.md).
