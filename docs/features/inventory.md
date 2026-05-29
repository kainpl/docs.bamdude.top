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
- **Material dropdown** — single-select.
- **Colour dropdown** — single-select. Options are the colours you actually have in stock — built from your existing (non-archived) spools — and grouped by the resolved colour-catalog name, so two near-identical hexes that both read as "Cobalt Blue" filter together regardless of brand. The dropdown only appears once at least one in-stock spool has a resolvable colour.
- **Storage Location chip** — narrows the spool list to a single storage location, so you can see just the spools kept in one box / shelf / dry-box.
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

### Copy Spool — duplicate an existing row

Every spool row (cards view + table view + grouped rows) has a **Copy** button next to Edit. Clicking it opens the spool form pre-filled with everything from the source row except `weight_used`, which resets to **0** — useful when you've just bought a second / third / nth spool of an existing filament. The header reads **Copy Spool** instead of Edit Spool, the footer button reads **Copy Spool** instead of Save. **Quick Add (the bulk `quantity` toggle) is available in copy too**, so you can clone a spool into a whole batch in one go — each copy still starts fresh (usage reset to 0, no RFID tag carried over). The source row is untouched; saving creates brand-new spools each with their own `id`. Spool form is printer-agnostic, so the same Copy button works in Spoolman mode — the existing create-mutation routing handles both paths.

### Bulk edit — change many spools at once

The toolbar's **Bulk edit** button (internal inventory only) opens a dialog to change a field across several spools at once. Pick which spools to edit (it starts with all the currently-filtered ones; deselect any you want to leave alone in the left-hand list) and **tick the fields to apply**: slicer preset, material, brand, subtype, label weight, colour, empty-spool weight, date of purchase, diameter, cost/kg, note, category, low-stock threshold, extra colour stops, visual effect, storage location.

Each ticked field pre-fills only when the selection already shares one value (otherwise it shows *"— varies —"*); **only the fields you tick are written**, the rest are left exactly as they were, and **consumed weight and RFID tags are never touched**. Inputs mirror the single-spool form — preset / effect / diameter / empty-spool are dropdowns; material / brand / subtype autocomplete from everything the system knows (slicer presets + colour catalog + built-ins, not just the selected spools); the colour list comes from your colour catalog filtered by the brand + material being applied and refreshes when you change them.

### Slicer Preset dropdown shows every per-printer / per-nozzle variant

The Slicer Preset field on the spool form lists all imported variants individually — so all P1S / X1C / A1 variants of "Bambu PLA Basic" render as separate rows with the full `@printer` suffix visible, instead of collapsing into one. The spool itself is printer-agnostic — the variant you pick is what gets persisted as `slicer_filament` and consumed by `normalize_slicer_filament` during slicing. (AMS Slot is per-printer, so it filters down; the spool form is union-of-all, so it doesn't.) Local profiles imported from OrcaSlicer / BambuStudio show alongside cloud presets — earlier versions hid local profiles whenever the user was logged into Bambu Cloud, which was a bug.

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
| **Extra colours** | Optional. Comma-separated list of 2–8 hex stops (e.g. `EC984C,#6CD4BC,A66EB9,D87694`) for multi-colour spools. Renders the swatch differently based on the **Effect** value below — gradient blend, hard-split bars, or colour-wheel pie. Format matches 3dfilamentprofiles.com so paste-and-go works. |
| **Effect** | Layered on top of the colour swatch — does **not** change the slicer profile. Full enumeration: surface effects (*Sparkle*, *Wood*, *Marble*, *Glow*, *Matte*) paint a CSS overlay; sheen variants (*Silk*, *Galaxy*, *Rainbow*, *Metal*, *Translucent*) carry a soft sheen; structural variants drive the colour-layer shape — *Gradient* = smooth 135° blend, *Dual Color* / *Tri Color* = hard-split horizontal bars (each stop occupies its own contiguous segment, no diagonal blend), *Multicolor* = conic-gradient colour-wheel pie. The form has a live preview pane below the dropdown so you see the effect before save. |

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

### Stock forecasting + Logistics view

A third inventory tab next to **Table** / **Cards** that turns the raw `spool_usage_history` table into reorder intelligence:

- **Daily-consumption rate** — exponentially-weighted moving average with a 30-day half-life, computed per SKU group (material / subtype / brand). One spool of recent prints weighs more than a year-old burst.
- **Days-left projection** — current stock divided by daily rate, with a 95%-service-level safety stock factored in (`σ × √lead_time × 1.65`).
- **Reorder-by date** — when to place the order so the new spool arrives *before* you run out, given the configured lead time.
- **Per-SKU expanded editors** — lead-time-days, safety-margin (dual-unit days|grams), alert-snooze toggle. Each setting persists across sessions in the `filament_sku_settings` table; SKUs with no settings yet fall back to the global lead-time floor (Settings → Inventory → **Forecast global lead time**).
- **Top-5 chart** — stacked-area projection of the five fastest-burning SKUs with ROP reference lines. Timeframe toggle: 1W / 1M / 6M.
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

#### Mid-print spool change semantics

If you re-assign a spool to a slot **during** a print:

- BamDude compares the assignment-change timestamp to the print-start timestamp.
- If the change happened **after** print start, the live assignment is used — i.e. consumption flips to the new spool from the swap point onwards.
- The portion already printed before the change stays billed to the previous spool.
- If no mid-print change happened, the snapshot taken at print start is preserved and the full deduction goes to that spool.

This makes mid-batch refills work correctly without manual reconciliation: load a fresh spool when one runs low, re-assign it in BamDude, and the rest of the print is billed to the new spool.

### Reset usage to 0

Each spool has an eraser action that resets its tracked usage to zero (a reset-all variant clears every spool's usage at once). Mechanically it records a `weight_used_baseline`, so reported consumption becomes "used since the last reset" rather than lifetime — useful when you refill or swap a roll but keep the same inventory entry instead of creating a new one.

### Removing usage records

Each row in a spool's **Usage History** has a hover **×** to delete just that entry; the bulk **Clear** button does the same for the whole list. Removing a record treats that consumption as if it never happened: its weight is **returned to the spool** (`weight_used` drops, so remaining weight goes back up) and the same amount is subtracted from the linked print's recorded filament, so the [Stats](stats.md) page stays in step with inventory. For a multi-colour print the deduction is per-record — removing one colour's entry only reclaims that colour's share and leaves the rest of the print intact. Handy for un-counting a mistaken or test print against a roll.

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

### Where do the slicer profiles come from?

Three sources, checked in priority order: **Bambu Cloud** (your synced presets, including custom ones) → **Local Profiles** (OrcaSlicer imports) → **Built-in Fallback** (~150 Bambu Lab filament IDs). Even without cloud login, the latter two ensure the preset list is never empty. See [Where presets come from](#where-presets-come-from) for details.
