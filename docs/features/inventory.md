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
| **Total Consumed** | Grams consumed across all spools since tracking started — or, for a spool whose counter was reset, since that [reset](#reset-counter). Pairs with [Stats](stats.md) for per-period views. |
| **By Material** | Donut chart broken down by filament type (PLA, PETG, ABS, …). Click a wedge to filter the spool list to that material. |
| **In Printer** | How many spools are currently loaded across all AMS units on all printers (sum of slot assignments). |
| **Low Stock** | Count of spools below either the global `low_stock_threshold` or their per-spool override (whichever is stricter). Click to filter to just the low-stock list — pairs with the `filament_low` notification. |

### Filtering, search, and view modes

The toolbar above the list combines a free-form search box with chip strips and view-mode toggles:

- **Search box** — matches the spool **name your display-name template composes**, not just the raw columns behind it, so anything the list shows is findable: with a template of `{brand}/{material}`, typing `LU/PET` finds it. Brand, material, colour, subtype, note and slicer preset are always matched too, as are the spool's **id** and **lot number** — those two whatever your template says, because they are the numbers written on the reel. The [material number](#material-number) is matched too. Every token has to match something, so `SUN Bl` finds a SUNLU Black spool. A token written as `#123` finds exactly the spool with that number and no other; a bare `123` stays an ordinary substring search. Press `/` from anywhere on the page to focus it.
- **Material dropdown** — single-select.
- **Material number dropdown** — single-select, with a **No material number** entry for spools that carry none. It appears once at least one spool has a [material number](#material-number).
- **Colour dropdown** — single-select. Options are the colours you actually have in stock — built from your existing (non-archived) spools — and grouped by the resolved colour-catalog name, so two near-identical hexes that both read as "Cobalt Blue" filter together regardless of brand. The dropdown only appears once at least one in-stock spool has a resolvable colour.
- **Storage Location chip** — narrows the spool list to a single storage location from the [managed locations catalog](#storage-locations-catalog), so you can see just the spools kept in one box / shelf / dry-box.
- **Status tabs** — Active / Archived / All, plus quick filters Used / New, plus stock filter All / Stock (no slicer profile) / Configured (has slicer profile).
- **Brand dropdown** — single-select.
- **View modes** — **Table** (data-focused, sortable columns), **Cards** (visual swatches), or **[History](#history)** (every consumption record on the farm). *Forecast* sits beside them when you have permission for it.
- **Group** — toggle that visually collapses identical spools into one expandable row with a count badge (e.g. *5 identical spools*). Grouping key is `manufacturer + material + colour name + label weight + subtype`; lot is deliberately **not** part of it, so a batch created with **auto-numbered lots** (see below) still collapses into one row, and a group may span several lots. A spool that is loaded in a printer always appears individually, so you can tell which physical spool is in which slot; a started spool back on the shelf groups with its twins, and the row's remaining weight is the exact sum over the members. Group state persists across sessions.

    **Weight Check** compares the total scale reading with the calculated gross weight when every spool in the group has a reading. A group whose measured total is below its total tare still uses the full gross-weight comparison. Groups with incomplete readings show a dash. Expand the group to see each spool's reading.

!!! info "Grouped sorting"
    Click **ID**, **Lot**, **Purchased**, **Location**, **Label**, **Net** or **Remaining** to sort both groups and their expanded spools. Groups are ordered before pagination. Label and net weights use group totals; remaining percentage uses the group's total remaining divided by its total label weight. ID, lot, purchase date and location use the representative spool (the lowest ID in the group).

## :material-package-variant: Adding spools

**Filament** in the sidebar opens the spool list. **+ Add Spool** asks for:

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

The toolbar's **Bulk edit** button (internal inventory only) opens a dialog to change a field across several spools at once. Pick which spools to edit (it starts with all the currently-filtered ones; deselect any you want to leave alone in the left-hand list) and **tick the fields to apply**: slicer preset, material, brand, subtype, label weight, colour, empty-spool weight, date of purchase, diameter, cost/kg, note, category, low-stock threshold, extra colour stops, visual effect, storage location, material number, **Last dried** and **Unlock weight**.

Two of those are actions rather than values. **Last dried** stamps the selected spools as dried now, or clears the date (**Clear the date**) — for a batch dried in an external dryer; see [Last dried](#last-dried). **Unlock weight** releases the lock a hand-entered weight puts on a spool, so the AMS weight sync may update the selected spools again; the weights themselves stay as they are — see [A weight entered by hand is locked](#hand-entered-weight-lock).

Each ticked field pre-fills only when the selection already shares one value (otherwise it shows *"— varies —"*); **only the fields you tick are written**, the rest are left exactly as they were, and **consumed weight and RFID tags are never touched**. Inputs mirror the single-spool form — preset / effect / diameter / empty-spool / storage location are dropdowns; material / brand / subtype autocomplete from everything the system knows (slicer presets + colour catalog + built-ins, not just the selected spools); the colour list comes from your colour catalog filtered by the brand + material being applied and refreshes when you change them.

### CSV import / export

Two buttons in the inventory header move whole spool lists in and out as CSV — handy for backing up your inventory, editing it in a spreadsheet, or bulk-loading a freshly-received order.

- **Export CSV** downloads a date-stamped `bamdude_inventory_YYYYMMDD.csv`, one row per spool matching the current filters — not just the page on screen.
- **Import CSV** bulk-adds spools from a CSV. Instead of writing straight away, it first shows a **preview table** that marks every row as *valid*, *error*, or *skipped* — and flags rows where a colour was auto-filled from the colour catalogue, or where a matching spool already exists — **before anything is written**. A confirm click then saves only the valid rows.

CSV headers are case- and spacing-tolerant, so a column titled `Label Weight`, `label_weight`, or `LABELWEIGHT` all resolve the same way. Only `material` is required; every other column is optional, and the same validation as the manual add-spool form applies to each row.

The file carries the `material_number` and `last_dried_at` columns as well; `last_dried_at` is an ISO date/time. A blank `material_number` cell means "no number" — an imported spool does not inherit one from its filament.

Spool exports list the cells protected as spreadsheet text in the final `__bamdude_text_escapes_v1` column. Keep this column when re-importing a BamDude export. It lets the importer preserve apostrophes you typed into notes and other text fields. Earlier CSV files still import using their original quoting rules.

CSV import/export is **local-inventory only**. In **Spoolman mode** both buttons are disabled, with a hint pointing you at Spoolman's own CSV tools instead.

### Storage locations catalog

Where a spool physically lives — a shelf, drawer, or dry-box — is a **managed catalog**, not free text. A **Locations** button in the inventory header opens the catalog manager where you create, rename, and delete locations; the spool form's **Storage location** field is a dropdown drawn from that catalog, with an inline *create new* option so you never leave the form to add a shelf.

- **Rename propagates** — renaming a location updates every spool assigned to it in one write, so there's no orphaned free-text drift.
- **Delete is guarded** — move assigned spools and detach Zigbee or Home Assistant sensors before deleting the location.
- **Spoolman sync** — in Spoolman mode the catalog imports Spoolman's distinct locations, and a rename cascades to Spoolman's per-spool `location` field (rolled back locally if Spoolman rejects it, so the two never diverge).

Viewing the catalog needs `inventory:read`; creating / renaming / deleting a location needs `inventory:update`.

A location can show readings from [Zigbee and Home Assistant sensors](sensors.md). The catalog displays each source separately, with a chart for its history. If more than one sensor reports the same quantity, select a primary source for the compact temperature, humidity or battery display; no source is chosen silently. The optional inventory table columns and card footer show the reading for each spool's storage location. Table columns sort the full inventory by current readings, placing unavailable readings last. Sensor setup and readings require the smart-sensor permissions.

### Editing a spool created by Quick Add, CSV import or RFID

Those three routes create a spool with a material and little else — no filament family, no brand, no subtype. **Editing and copying such a spool ask for exactly what the server asks for: the material.** So you can change its shelf location, its cost or a note without filling in anything else.

Family, brand and subtype stay visible and editable; the little `*` markers appear only where a field is genuinely required.

!!! info "The brand and material lists offer every product"
    The colour catalogue knows only some brand/material pairs — Elegoo is
    catalogued for PLA only, yet **Elegoo ASA** is a real filament you can buy.

    Both lists therefore always offer everything: the known pairings ranked first under
    **Suggested**, the rest under **All**. A spool's own brand or material is always
    present in its own dropdown, even if nothing else has heard of it.

### The spool links to a filament family

The spool form carries a single **Filament family** picker — the same identity Bambu Studio uses (`filament_id`), shared with the AMS slot dialog and the K-profile editor. The spool is printer-agnostic by construction: per-printer preset variants are the *family's* business, resolved per printer at slot-assignment and slicing time. Picking a family prefills material and brand; custom families carry a badge saying which cloud they came from; a **Create new family…** row opens the [Create Filament dialog](filament-families.md#creating-your-own-filament) without leaving the form. Full model: [Filament Families](filament-families.md).

### Per-spool category & low-stock override

Two extra optional fields on the spool form fine-tune both filtering and alerting:

| Field | Effect |
|---|---|
| **Category** | A free-form short tag — e.g. `PETG`, `ABS`, `TPU`, `paint`, `experimental`. Inventory page renders a category-filter chip strip at the top so you can show "only TPU" or "only experimental". The chip strip only appears once at least one spool has a category set, so it doesn't clutter the page on day one. The **No category** chip filters to spools with no category. |
| **Low-stock override (%)** | Per-spool override for the global `low_stock_threshold`. Use this when a particular spool needs an earlier warning (e.g. an expensive PA — 50% remaining means time to order; cheap throwaway PLA can wait until 10%). Empty = inherit the global setting. |

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
| **Color** | Visual picker with shade + opacity + finish pickers. Recent-colours strip + brand palettes. |
| **Extra colour stops** | Optional. Comma-separated list of 2–8 hex stops (e.g. `EC984C,#6CD4BC,A66EB9,D87694`) for multi-colour spools. Renders the swatch differently based on the **Visual effect** value below — gradient blend, hard-split bars, or colour-wheel pie. Format matches 3dfilamentprofiles.com so paste-and-go works. |
| **Visual effect** | Layered on top of the colour swatch — does **not** change the slicer profile. Full enumeration: surface effects (*Sparkle*, *Wood*, *Marble*, *Glow*, *Matte*) paint a CSS overlay; sheen variants (*Silk*, *Galaxy*, *Rainbow*, *Metal*, *Translucent*) carry a soft sheen; structural variants drive the colour-layer shape — *Gradient* = smooth 135° blend, *Dual Color* / *Tri Color* = hard-split horizontal bars (each stop occupies its own contiguous segment, no diagonal blend), *Multicolor* = conic-gradient colour-wheel pie. The form has a live preview pane below the dropdown so you see the effect before save. |

#### Quick Add (Stock) mode

Toggle **Quick Add (Stock)** at the top of the form to switch to a minimal mode that drops the filament-family requirement and hides the PA Profile tab. Only **Material** is required; **Brand** and **Subtype** are optional, next to **Label Weight**, **Quantity** and **Color** — perfect for inventorying a freshly-arrived order before you've decided which filament family to associate.

Quick-Add spools are called **stock spools** — they track weight and usage like any other spool, but they aren't linked to a printer filament profile. You can edit a stock spool later to assign a filament family (it becomes a *configured* spool at that point) or filter to just the stock pile via the inventory's stock filter.

The **Quantity** field is only shown in Quick Add and creates that many spools in a single transaction. Quick Add also shows the **Lot** field together with an **Auto-number lots (+1 per copy)** checkbox:

- **Auto-number ticked** — the copies are numbered sequentially **starting from the Lot value you entered**: Lot `5` × Quantity `3` → three spools with lots **5, 6, 7**. Leave Lot empty and numbering starts at 1.
- **Auto-number unticked** — every copy shares the single Lot value you typed (or no lot at all).

!!! tip "Bulk buying"
    A 5-pack of PLA from the same batch → Quantity = 5, Lot = 1, **Auto-number lots** on → five spools with lots 1–5, each traceable by its lot, and still one *5 identical spools* row under the **Group** toggle — lot is not part of the grouping key, so numbering the lots costs you nothing in the list.

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
    2. **Filament family**: pick the closest PETG family (PCTG is a PETG variant). For a custom OrcaSlicer PCTG profile, import via [Local Profiles](local-profiles.md) first.
    3. **Material**: type `PCTG` → click *Use custom material: PCTG*.
    4. **Brand**: `3D-Fuel`. **Subtype**: `Pro`.
    5. Set colour (315 °C max bed, 80 °C bed for PCTG — print/bed defaults are inherited from the base PETG preset; override on the slicer side if needed). Save.

#### Additional section

| Field | Description |
|---|---|
| **Empty Spool Weight** | Pick from the [Spool Catalog](#spool-catalog) (90+ entries) or enter manually — used for accurate remaining-weight calculation. An empty-spool weight of 0 g is a value of its own and is kept as 0. |
| **Remaining Weight** | Live `label_weight - weight_used` with a reference maximum bar. |
| **Cost per kg** | Per-spool cost; feeds [cost tracking](#cost-tracking) and archive cost roll-ups. |
| **Last dried** | When the spool was last dried — see [Last dried](#last-dried). Shown when editing a spool. |
| **Material number** | Your own article code for the filament — see [Material number](#material-number). |
| **Note** | Free-text. |

#### Material number {#material-number}

**Material number** is a free-text internal article code, next to **Lot**: the number your shop or accounting uses for a filament, whatever the brand calls it. The field suggests the numbers already in use.

- A new spool of a filament that already has a number gets it automatically — "the same filament" being what **Group** groups by (brand, material, colour name, label weight, subtype). A number you type is never replaced, and editing a spool never changes it by itself. CSV import does not inherit: a blank cell there states "no number".
- It is available as an optional table column (off by default — enable it in the column settings), as a filter, in the search box, in **Bulk edit**, as a level in [Spool order](#spool-order), as the `{material_number}` variable of the spool display-name template and of label templates, and as the `material_number` column of the CSV export and import.
- [Stats](stats.md#by-material-number) totals consumption and cost per material number.
- In Spoolman mode the field shows the article number of the filament in Spoolman and is read-only — change it in Spoolman.

#### Last dried {#last-dried}

A spool remembers when it was last dried. When a drying cycle in an AMS has run for at least half its time, every spool assigned to a slot of that unit gets the date, together with the temperature and the hours when they are known. The record belongs to the spool, so it stays after the spool moves to another AMS or onto a shelf. A cycle stopped early marks nothing and does not overwrite an earlier drying. This works with the built-in inventory and with Spoolman.

For a spool dried elsewhere, set the date by hand: the **Last dried** field in the spool form has a **Now** button, and clearing the field removes the record; **Bulk edit** does the same for a whole selection. A date set by hand carries no temperature or hours.

The date is shown on the spool card, can be turned on as the **Last dried** table column (off by default), is carried by the CSV export and import as `last_dried_at`, and can be used as a level in [Spool order](#spool-order).

#### A weight entered by hand is locked {#hand-entered-weight-lock}

When you type a spool's used weight yourself, BamDude locks that weight against the AMS weight syncs: neither the automatic sync nor the **Sync Weights from AMS** button overwrites it. Prints still deduct what they use. A weight that came in through CSV import is locked the same way.

Releasing the lock is an explicit action. Open the spool: a note says the weight was entered by hand, with the checkbox **Let the AMS weight sync update this spool again** below it. For many spools at once, tick **Unlock weight** in **Bulk edit**. Either way the stored weight stays as it is; only later syncs may change it.

#### Assign to slot from the form {#assign-to-slot-from-form}

A spool that sits in no slot — and is not archived — has an **Assign to slot** button at the bottom of its form. Choose the printer, the **AMS unit** and the **Slot**, and the usual assignment dialog takes over with all its checks, exactly as if you had started from the printer card. A slot holding a Bambu Lab RFID spool cannot be picked — the printer manages that slot.

### PA Profile tab

The second tab links pressure-advance (K-factor) calibration profiles to the spool. Auto-select matches profiles by brand + material + subtype across all your printers + nozzles, with the matches grouped by printer + nozzle (left / right for dual-nozzle):

- **Auto-select** — fills the matrix from your existing K-profiles automatically.
- **Grouped view** — collapsible printer headings, each with per-nozzle (L / R) sub-rows.
- **K-factor values** displayed inline so you can sanity-check before saving.
- **Nozzle diameter badge** on each row. Profiles are fetched for *every* nozzle size a printer reports, so on a multi-nozzle machine one filament can contribute two rows that share a name — the diameter is what tells them apart. A printer that has not yet reported its hardware is queried for 0.4 mm.
- **Per-printer override** — pick a different profile for one printer if you have brand-specific calibration values that differ between machines.

See [K-Profiles](kprofiles.md) for the calibration workflow that produces these profiles.

## :material-checkbox-multiple-marked: Mass actions

Every row on the Filament page has a checkbox. Tick one, and a toolbar appears above the list with **Edit · Print labels for the selected spools** (**Print label for the selected spool** when one is ticked) **· Reset counter · Archive** (or **Restore**, on the Archived tab) **· Delete**.

Four ways to select:

| Control | Selects |
|---|---|
| Row checkbox | That spool |
| Group checkbox | Every spool in that group (shows a dash when only some are ticked) |
| Header checkbox | Every spool **on the current page** |
| **Select all N matching the filter** | Every spool the current filter returns, including rows on other pages |

The last one is deliberately a separate, explicit action rather than the default. Editing "everything the filter shows" is convenient; *deleting* it is not something that should happen because of a checkbox you could not see. For the same reason the selection clears itself whenever you change the filter, the search box, the tab or the grouping — a toolbar that says "12 selected" over a list which no longer contains those spools is how a bulk delete lands on the wrong rows.

Archive, Restore and Delete ask for confirmation first.

**Archiving a spool takes it out of its AMS slot.** The slot is released on the printer card, and the next print from it is no longer charged to the archived spool. A spool in a slot a running print feeds from cannot be archived until that print ends: a single archive is refused, and a bulk archive skips such spools and says how many were kept — archive them when the print ends. An archived spool that is still shown in a slot leaves it once its printer is idle.

!!! warning "A used spool is archived, not deleted"
    **Delete** removes only a spool that nothing refers to. A spool that has usage history, sits in a slot or belongs to a running print is refused, with a hint to archive it instead — its records, and the prints costed from them, would otherwise lose their spool. In a bulk delete the spools that can go are deleted and the refused ones are reported. Use **Archive** for a reel you have finished.

All of this works in **Spoolman mode** as well as with the built-in inventory. Because Spoolman is a separate service that can be briefly unreachable, individual rows can fail: when that happens you get an honest **"7 done, 2 failed"** rather than a success message, and the selection is kept so you can retry the rest.

!!! tip "The Edit dialog shows what it is about to change"
    The bulk-edit dialog lists the exact spools in the selection. It is read-only — the choosing happens on the page — but it is worth reading before you apply a field to forty spools.

## :material-format-list-checkbox: AMS slot assignments

Once a spool exists, you can park it in a specific AMS slot on a specific printer. The right-side AMS panel on each printer card shows the four slots of each AMS (one, on an AMS HT) and lets you drop a spool into each slot.

Behind the scenes, this is the `spool_assignment` table — one row per `(printer, ams_id, tray_id)` triple. Two assignments to the same physical slot can't exist simultaneously; assigning a new spool releases the previous one (which goes back to "available, not in any printer").

The reverse holds as well: **a spool sits in one slot only**. Assigning a spool that is still recorded in another slot — on the same printer or on another one — takes it out of that slot. The assignment is refused when that other slot is feeding a running print: finish or stop the print, or pick another spool.

Two things do **not** remove an assignment:

- **A single "empty" report from an idle AMS.** A slot that reports no spool while nothing prints loses its assignment only when it still reports empty about 25 seconds later. One stray status message therefore leaves the assignments alone, while a reel you really took out is unlinked shortly afterwards.
- **Unplugging an AMS.** The unit leaves the printer card, and its spools stay assigned for when it is plugged back in.

A few extra niceties:

- **RFID auto-assign** — Bambu spools with intact RFID tags get matched to the catalog the moment the AMS reads the tag. If a tag points at a known catalog entry but no inventory row exists yet, BamDude offers to create one inline. If the tag is unknown (third-party, custom), you can bind it to an existing spool to skip the manual look-up next time.
- **Auto-tracking new Bambu spools** — when an AMS RFID matches no existing tray UUID, BamDude first looks for an **untagged** spool with the same material + colour + brand (`Bambu` / `Bambu Lab` / unspecified) and attaches the RFID to it. So a Quick-Add stock entry you logged ahead of time gets reused (your weight, notes, cost data are preserved) instead of producing a duplicate. If no match is found, a fresh inventory row is created from the AMS data — drawn the way a hand-added spool of the same colour would be: the colour name, extra colour stops and effect come from your colour catalogue, and where the catalogue carries no effect, the subtype supplies one when it names a finish (*Wood*, *Silk*, *Sparkle*, *Gradient*…; *Basic* or *CF* name none).
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

The **Forecast** view, next to **Table** / **Cards** / **History**, turns the raw `spool_usage_history` table into reorder intelligence:

- **Daily-consumption rate** — exponentially-weighted moving average with a 30-day half-life, computed per **colour group** (material / subtype / brand / colour name). Five colours of the same PLA Basic become five independent forecast rows, each with its own runway and reorder date — so running low on black doesn't hide behind a full spool of white. One spool of recent prints weighs more than a year-old burst. A colour with too little recorded history for a trend is estimated from its spools' totals instead: each spool's consumption is spread over the time it was actually printed with — from its first use to its last — and only what falls inside the last 90 days counts. Time a spool spent on the shelf before it was opened is not use, so a filament bought months ago and opened last week forecasts at the pace of that week; a filament not printed for 90 days shows no consumption.
- **Days-left projection** — current stock divided by daily rate, with a 95%-service-level safety stock factored in (`σ × √lead_time × 1.65`).
- **Reorder-by date** — when to place the order so the new spool arrives *before* you run out, given the configured lead time.
- **Reserved by orders** — how many known grams of that colour your active orders still have to take off the shelf: the plan they have not printed yet plus what is already waiting in the queues, counted exactly as the order pages count it and projected onto the SKUs that can serve it (split by remaining weight when several brands match). If any active-order slicer channel has no trustworthy weight, the panel warns that **Reserved** and **Reorder By** cover only the known part; it never invents grams or assigns that uncertainty to a SKU. Beneath it sits what is left to promise, and **Reorder By** counts down from *that* rather than from everything on the shelf — **Empty By** deliberately does not, because the consumption rate already contains those orders being printed. Promise more than the shelf holds and the row reads **Over-committed**, which counts as an alert even before the SKU has a consumption rate. Need in a colour you do not stock is listed under the table instead of being spread over the colours you do.
- **Filter + count controls** — **Material** and **Brand** dropdowns narrow the table; a dedicated **Spools** column shows how many physical spools back each colour row. Every column is sortable.
- **Per-colour expanded editors** — lead-time-days, safety-margin (dual-unit days|grams), alert-snooze toggle. Each setting persists across sessions in the `filament_sku_settings` table; colours with no settings yet fall back to the global lead-time floor (the **Global lead time** field in the Forecast view).
- **Top-5 chart** — stacked-area, multi-series projection of the five fastest-burning colours with ROP reference lines. Timeframe toggle: 1W / 1M / 6M.
- **Shopping list (Logistics view)** — separate panel below the forecast table. Add SKUs to a `pending → purchased → received` queue. Marking an item *received* auto-creates `category='Stock'` spools via bulk-create (uses the average historical spool weight). CSV export + clear-all helpers. Formula-looking names and notes are escaped as text in the CSV. Quantities and weights keep their numeric values.
- **Notification toggles** — two notification-provider events sit under **Settings → Notifications → Inventory Alerts**: *Reorder Alert* (SKU crossed reorder point) and *Stock Break Alert* (will run out before lead time). Both are sent through the provider like any other event. A colour whose every spool is archived is announced once as out of stock instead — and not at all while another brand of the same colour is on the shelf; see [Notifications](notifications.md).

The forecast tab works in **Spoolman mode** too: BamDude keeps its own record of every print it charges to a Spoolman spool and forecasts from it. See [Spoolman → Usage history and Forecast](spoolman.md#spoolman-usage-history).

Permissions: `inventory:forecast_read` (see the panel) and `inventory:forecast_write` (modify SKU settings + shopping list). In the default groups, Viewers have read and Operators have both.

### Pre-load assignment (weigh-then-assign)

You can assign a spool to a slot **before** loading the filament — useful when you've just weighed a fresh spool and want to track it from the very first print. When the target slot is empty (`tray_type` blank in the AMS data), BamDude:

- Persists the `SpoolAssignment` row immediately so the inventory page reflects the pairing.
- **Defers** the `ams_filament_setting` + `extrusion_cali_sel` MQTT publish — Bambu firmware silently drops both commands for unloaded slots (there's no filament context for the K-profile / pressure-advance index to attach to), and pushing them anyway would close the modal with a misleading "Assigned!" while the slicer kept showing default-PLA forever.
- Surfaces this in the confirmation toast: *"Spool assigned. The slot will be configured when you insert the filament."*
- Replays the full configuration automatically the moment the slot transitions to loaded. The "loaded" signal is the AMS state code (`state == 11`, "filament fed to extruder"), not the tray's material string — so 3rd-party spools without readable RFID (which report state=11 but keep `tray_type=""`) trigger the replay too. After the replay the assignment fingerprint is stamped, so subsequent AMS pushes don't re-fire.

### Automatic assignment of a full stock spool {#automatic-stock-assignment}

!!! info "Availability"
    This is an optional feature for **built-in inventory**, not Spoolman, and is off by default on every printer.

Use this when a printer is routinely loaded with new, full, untagged spools of the same filament. BamDude can assign the next matching inventory spool when it observes filament being inserted into an empty AMS slot, including a replacement after runout.

1. Add the full spools on the **Filament** page with their actual material, colour, brand, subtype, filament family and label weight.
2. Open **Printers → Edit Printer**, enable **Assign a full stock spool on loading**, and choose the **Inventory filament group**. Save the printer.
3. While BamDude is connected to the printer, load a new full spool from that group into an empty AMS slot. Check the resulting assignment on the slot or in Inventory.

Editing the policy requires both printer-edit and inventory-update permission; reading the group list requires inventory-read permission.

**What it selects.** The group must match exactly, including colour and filament family. Eligible stock is unarchived, unassigned, untagged, single-colour 1.75 mm filament with positive label weight, zero actual consumption and no previous print use; a spool entered as partial is excluded. The oldest inventory entry is selected first, with ID breaking ties. Resetting the displayed consumption counter does not make a used spool eligible. If the group runs out, it stays selected: BamDude does not substitute another group or create a spool. Add matching stock or assign a spool manually.

**What loading means.** An untagged reel has no readable inventory ID or weight. Enabling this policy is your declaration that new spools loaded this way are full and belong to the selected group. Startup and reconnect only establish the current slot state; they do not assign spools that were already present. RFID identification and manual assignments take priority. Removing and returning a known partial spool without a runout keeps its assignment.

!!! warning "Returning the old spool after runout"
    Removing a partial spool during a print can itself cause runout. If you return that same reel, **assign it manually before inserting it or resuming**. Otherwise, the enabled policy treats the replacement as a new full spool. A manual assignment made after the runout wins, even when it names the same partial reel. To swap a partial reel for a full one without runout, also use manual assignment.

**External holders:** ordinary loading still needs manual assignment because there is no insertion sensor. With this policy enabled, a clearly identified external-spool runout followed by your **Pause → Printing** resume in the same connected session can assign a full replacement from the selected group. BamDude must see that specific external feed loaded; ordinary pauses, reconnects and ambiguous runouts do not qualify. Returning the old reel requires manual assignment before resume. The feature does not resume the printer for you.

This controls physical inventory assignment. It does not change [filament routing](filament-routing.md), queue colour/profile overrides or AMS Backup compatibility settings.

### Replacing the spool on an assigned slot

You do not have to unassign first. Hover an assigned slot and pick **Replace spool** (next to **Unassign**): the dialog shows what is currently assigned, lists only spools that are free — the current one and anything assigned to another slot stay hidden, so you can never pull a spool out of a different printer by mistake — and one confirm swaps the assignment. This works the same on AMS, AMS HT and external slots, with the built-in inventory or Spoolman.

Nothing about accounting changes: a replace runs exactly the code path an unassign followed by an assign did. Mid-print, the same prompt appears — while the printer is paused, or after a pause — asking whether this is a physical spool change (filament usage is split at the pause layer) or a correction of a wrong link (the new spool owns the whole print).

## :material-water-percent: Automatic consumption tracking

Every print BamDude dispatches reads the per-filament `weight` from the source 3MF. On `print_complete`, the dispatched grams are deducted from the spool that was assigned to the matching AMS slot at the time the print started:

- The `spool_usage_history` table records every deduction (one row per filament of a print × spool — two filaments of one file printed from the same spool give two history records).
- `spool.used_grams` is the running total.
- `spool.weight - spool.used_grams` is what's left.

The inventory page colour-codes each spool by remaining percentage, with a configurable **low-stock threshold** (the pencil on the **Low Stock** summary card). When a spool drops below the threshold, the matching `filament_low` notification fires (subscribe to it under whichever providers you care about). A spool already below its threshold is also announced right when it is put into a slot — assigned by hand, matched by its RFID tag or loaded from stock automatically — and when its weight, label weight or own threshold is edited by hand while it sits in a slot. It is still one notification per run-down, and only for a spool in a slot. A Spoolman-bound slot is judged by Spoolman's figure against the same threshold. A slot with no inventory binding is not judged at all: the printer's own counter reads 0 % for any spool without an RFID tag, and that is no answer — assign the spool, and BamDude knows what is on it.

If a print fails partway through, the deducted amount is the slicer-estimate × completion ratio (best effort) rather than the full estimate. External-print fallback archives — the ones from prints started directly on the printer touchscreen — get reconciled the same way once their 3MF is recovered.

Deleting a usage entry returns its weight to the spool. Runout closure and AMS-sync corrections affect lifetime spool consumption, not the print archive’s grams; deleting them leaves the archive unchanged. Ordinary print entries still reduce the archive’s grams when removed. Recalculate Costs also excludes these corrections from print costs. History, export and backup retain them as separate entries.

### Usage tracking detail

The deduction pipeline is more nuanced than a flat "subtract slicer estimate at print end". BamDude picks the most accurate source available per scenario:

| Scenario | Primary source | Fallback |
|---|---|---|
| **3MF available + completed print** | Per-filament `used_g` from the 3MF's `slice_info.config`, mapped to physical AMS trays via the `ams_mapping` captured from the MQTT print command | — |
| **3MF available + failed/aborted partial print** | Per-layer G-code analysis: how many grams went through each filament up to the layer where the print stopped | Linear scaling = `total × completion_ratio` if per-layer data isn't parseable |
| **Slicer-initiated print** (BambuStudio / OrcaSlicer / Handy) | `ams_mapping` captured from the live MQTT print command, ensuring the right tray is billed regardless of which app started it | — |
| **Single-filament print** | The printer's currently-active tray | — |
| **G-code-only print, no 3MF** | AMS `remain%` delta between print start and end (integer-precision, ~10 g per 1 % step on a 1 kg spool) | — |
| **External print, fallback archive recovered later** | Re-uses the 3MF source the moment recovery completes, retroactively reconciling the deduction | — |

#### What the slicer's grams include {#slicer-grams}

The per-filament grams BamDude books (and shows as the print's estimate) are the slicer's **whole consumption** of each filament, not just the model. Bambu Studio adds up, per filament:

- the **model**;
- **supports**;
- the **prime tower**;
- the **flush** on every filament change (the purge the printer discards).

The flush part is the slicer's own calculation from its flush-volume table; the printer purges about that much, but nobody weighs the waste. A plate whose G-code is larger than 1 GB is not analysed — it is booked from the AMS remaining-percentage instead — and analysing a very large plate may take up to 12 minutes.

### Runouts close the spool at exactly empty

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

**A print that moves between trays** — an AMS backup that later returns to the refilled slot, or a loader that reports another tray for a moment on every load (a P1S with a BMCU reports the external holder that way) — is charged stretch by stretch: each stretch once, to the spool the journal recorded for it, so a reel loaded into the same slot after a runout gets its share. A tray reported within a single layer fed nothing the layer count can see and is not charged. Grams no spool can be named for are reported in the **Filament not charged** notification, in built-in inventory and in Spoolman alike. On a two-holder printer, an external filament whose holder the print did not name is likewise reported as not recorded rather than charged to the first holder.

**A print that stopped after a reel change** divides only what it printed. A cancelled print that stopped at layer 50 of 200, with reel B taking over from reel A at layer 40, used — say — 10 g; A printed 40 of those 50 layers and B 10, so A is charged 8 g and B 2 g. A reel that arrived on or after the last printed layer is charged nothing of it. The layer the print stopped at, the plate's layer count and the progress are the ones the printer reported when the print ended, so a print started on the same printer before the books are written cannot change them. Without per-layer G-code the stretches are measured by layer count, which is exact only when the layers use about the same filament. When the printer reported no layer the print stopped at, nothing tells where the change sits relative to the stop: the weight is then reported as not recorded instead of being shared out equally — unless the same reel fed every stretch, which then gets it all. A finished print needs no such layer when its G-code is available.

**Refilling an inactive slot after a backup switch.** A repeated autoswitch status is not a second empty spool.
When the journal shows the backup in another slot of the same four-slot AMS, a different replacement reel
is positively present, and feeding has not returned to the original slot, BamDude ignores that repeated
status for the new reel. Matching events already saved in the journal are left out of the accounting the same way.
A real return to the refilled slot allows its next runout normally. The check uses sensor and feeding
history, not a time delay; it does not infer this condition from another AMS unit or an external holder.

The live check first resolves the spool from the journal when the current slot assignment has already disappeared. It uses one frozen sensor reading for both its decision and the new event. Repeated or folded reports of the same open episode do not notify again; a newly confirmed switch from pause to backup does. The original layer and spool identity stay fixed, and weaker replays do not erase confirmed autoswitch evidence.

#### Replacing a reel while the tube still feeds the old one

When an AMS slot runs dry, the printer keeps printing the filament still in the feed tube and reports the external spool's id meanwhile. You can put the new reel into the slot during that time — and assign it — without moving the books. The tube's filament stays on the **old** reel until the printer feeds from the slot again; the new reel is charged from **that layer**, not from the moment you assigned it. Assigning a reel only names the reel in the slot; the feed boundary comes from the printer. The late runout of the tube is charged to the old reel, and a later runout of the new reel still counts as its own. Internal inventory and Spoolman split the print the same way.

While a print is running, the usage journal records these as separate events — the tail starting and the feed coming back — next to tray changes and runouts. They decide how the print is split at completion; the spool's usage history still shows only what each spool was charged.

If BamDude restarts in the middle of this, it picks the tail back up from the journal. The reports it receives while it rejoins the print keep the layer each one was reported at and the order they came in, so every stretch goes to the reel that was in the slot when it was fed: a reel assigned in that moment still leaves the tube's filament to the old reel, and if you assign twice, the reel between the two assignments keeps its own stretch. An assignment made right after the rejoin waits until those reports are written, so it cannot rename a stretch fed before it. If they cannot be written, what they covered is reported as **not recorded** instead of being charged to the reel in the slot by the end of the print; what came before keeps its reels. This holds even when the printer's connection was down at that moment, or still is when the print is charged; when nothing tells how the print's grams divide over its layers, its filament is reported as **not recorded** rather than split by a guess. A late report of the previous print never lands in the next one and does not disturb what this print remembers. If the print's history cannot be read back, BamDude retries a few times; what it then could not see is reported as **not recorded** instead of being charged to the last reel it knew — also when that unknown stretch is all the print has, and the estimate from the AMS remaining percentage does not charge it afterwards either. A cancelled single-colour print is split the same way in Spoolman as in the internal inventory. If the feed came back while BamDude was not watching, the layer it first sees is used as the boundary and the stretch it did not see is reported as **not recorded** — it is given to neither reel. There is deliberately no "the tube is still feeding" question in the app: an assignment and a feed are different facts, and a dialog could not name the right layer.

### Archive a spool closed by runout

**Settings → Filament → Usage accuracy → Archive the spool it closed** can archive an empty spool after its unambiguous runout episode closes and the printer has demonstrably moved to a backup or replacement. It is **off by default** and works with built-in inventory and Spoolman. A spool reinserted to continue the same print stays active; a low or negative accounting balance alone does not prove a physical runout.

### Two-way AMS weight sync for tagged spools

For spools with a valid Bambu RFID tag, idle AMS readings can correct the books **downward** as well as upward — the firmware's own remaining estimate is the same number Bambu Studio mirrors into its filament manager. A downward correction is deliberately cautious: the same value must repeat across two reports at least a minute apart, so a garbled report after a reconnect can never rewrite a spool. Untagged spools are never touched by this path.

The sync waits for the print to be booked. While a print runs, and until its filament has been charged at completion, no AMS reading is written to the spools of that printer — the remaining-percent reading already contains part of what the print used, and writing it would count that filament twice. A [weight entered by hand](#hand-entered-weight-lock) is not touched by the sync at all.

### Live "filament so far"

While a print runs, the expanded printer card shows how much filament it has consumed so far — per slot on multicolour jobs, refreshed twice a minute — and says **"split across spools"** once a runout has genuinely divided the print between reels. Display-only: inventory is still written once, at completion.

The figure is the slicer's total for each filament ([what it includes](#slicer-grams)) times the share of the print done so far, and that share is measured from the G-code's own extrusion — model, supports and prime tower, layer by layer. The flush on a filament change is not in the G-code (the printer's filament-change routine does it), so the live figure spreads it evenly over the print instead of jumping at each change: in between it is an estimate, and at the end it equals the slicer's total.

#### Mid-print spool change semantics

- **After a runout**, attribution is split at the runout layer as described above — the journal owns the boundary.
- **Without a runout** (you re-assign a slot mid-print to correct a wrong link), the live assignment wins and the whole print is billed to the newly-assigned spool. That is the correction semantic: BamDude assumes the link was wrong from the start, not that you swapped reels.

### Reset counter

Each spool has an eraser action — **Reset counter** — that zeroes the displayed **Total Consumed** counter (**Reset all counters** resets every active spool's counter at once). Crucially, this only zeroes the *displayed* consumption figure — the spool's remaining weight is **not** changed. Mechanically it records a `weight_used_baseline`, so reported consumption becomes "used since the last reset" rather than lifetime — useful when you refill or swap a roll but keep the same inventory entry instead of creating a new one.

The backing API endpoints are `POST /inventory/spools/{id}/reset-consumed-counter` for one spool and `POST /inventory/spools/reset-consumed-counter-bulk` for all of them.

### The History view — every consumption record at once {#history}

The inventory's third view mode, **History**, between Cards and Forecast, lists the whole farm's usage records rather than one spool's: what was printed, off which spool, on which printer, how many grams, what it cost, and how it ended — newest first.

A spool's own tab answers "where did this reel go". This answers "where did the filament go", which is usually the question you start from. It is the same records either way; only the entry point differs.

Every part of the list is computed by the **server** — the page, the sort order, the filters, the search and the totals. A farm with a year of prints has six figures of records here and the browser never downloads them.

- **Search** — the page's own search box serves this view too. Same box, same place; it just searches events, reaching the print's name, the spool and the printer at once.
- **Filters** — printer (including *No printer*, for records charged to no machine), material, brand, outcome, and a date range. Plus the spool's own state: **All / Active / Archived** and **All / In Printer / On the shelf**. Those last two carry an *All* setting the spool table has no equivalent of, and it is the default: retiring or unloading a reel does not un-burn what it printed, so nothing here is hidden until you ask for it to be.
- **Sorting** — any column: date, spool, print, printer, grams, percent, cost, outcome.
- **Totals** — the grams (and money) beside the filters are for the **whole filter**, not the page on screen. "What did August cost me" is one date range away.

Spools you have since archived or deleted keep their rows, marked rather than hidden — the grams they carry were still printed, and dropping them would make these totals disagree with the [archives](archiving.md). Spool names follow your [display-name template](#display-name-follows-your-template) and a retired printer reads as *Printer 5 (Archived)*, exactly as everywhere else. Clicking a spool opens it.

In **Spoolman mode** the view shows BamDude's own record of the prints it charged to Spoolman spools — see [Spoolman → Usage history and Forecast](spoolman.md#spoolman-usage-history).

### Removing usage records

Each row has a hover **×** to delete just that entry — in a spool's own **History** tab and in the farm-wide History view alike; the spool tab's bulk **Clear** button does the same for that spool's whole list. Removing a record treats that consumption as if it never happened: its weight is **returned to the spool** (`weight_used` drops, so remaining weight goes back up) and the same amount is subtracted from the linked print's recorded filament, so the [Stats](stats.md) page stays in step with inventory. For a multi-colour print the deduction is per-record — removing one colour's entry only reclaims that colour's share and leaves the rest of the print intact. Handy for un-counting a mistaken or test print against a roll.

---

## :material-currency-usd: Cost Tracking

Every spool can carry a per-kg cost; BamDude rolls it up into per-print, per-archive, and per-project cost stats.

### Setting cost-per-kg

| Where | Field | Notes |
|---|---|---|
| Spool form → Additional section | **Cost per kg** | Per-spool override; takes precedence over the global default |
| **Settings → Printing → Cost Tracking** | **Default filament cost (per kg)** | Per-kg fallback when a spool has no cost set (default 25.00 in `default_filament_cost`) |
| **Settings → Printing → Cost Tracking** | **Currency** | Symbol used everywhere — USD, EUR, GBP, MYR, and ~25 more |

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

A print keeps the cost it was booked with: every usage record stores what its grams cost at the spool's price at that moment. The **Recalculate Costs** button on the [Stats](stats.md#recalculate-costs) page rebuilds every archive's cost from those records — the recorded prices are kept — in this priority order:

1. `spool_usage_history` records joined to `archive_id` (most accurate, per-spool actuals), plus the default rate for any grams no spool covered or recorded without a price.
2. Legacy usage records joined by print name (for older archives without the FK link).
3. The default filament cost (when no usage records exist at all).

To correct prints that were booked at a wrong spool price, change the spool's **Cost per kg** and use [Re-price usage](stats.md#re-price-usage) on the Stats page — it re-prices the recorded usage of one spool or one period at the spools' current prices.

!!! tip "Set costs early"
    For accurate cost tracking, set `cost_per_kg` on each spool when you add it to inventory. The default is a rough estimate — individual spool prices give you precise per-print data and make the **Recalculate Costs** button useful.

## :material-palette: Colour catalog

Colour names come from the `color_catalog` table — manufacturer-aware. When two brands ship a paint chip with the same hex, the Bambu Lab name wins for clarity in the UI; non-Bambu brands resolve via their own entries. If a spool's hex isn't in the catalog at all, BamDude falls back to an HSL-derived name ("dark cyan", "light yellow") so you never see a raw hex string in the UI. One hex can also be two colours in one brand's range — `#FFFFFF` is Jade White in PLA Basic and Ivory White in PLA Matte — so an AMS slot asks with its own material first, and a slot with an assigned spool shows that spool's colour name. A colour picked on the printer's screen is reported a shade off the catalogue's value, so a slot whose hex has no exact match is named after the nearest Bambu Lab colour of the slot's own product line — the line comes from the spool's RFID data or, without RFID, from the slot's filament preset. Only a colour with no close Bambu match gets the HSL-derived name.

You can extend the catalog manually under **Settings → Filament → Color Catalog**. The frontend pulls a runtime `{hex: name}` map once per session — adding a new entry takes effect on next login (or on a hard refresh).

### Multi-colour gradients

Painted, dual-colour, and silk filaments aren't one hex value — they're a gradient between two or more. BamDude renders these as **actual gradient swatches** on inventory cards, AMS slot indicators, and the colour picker, instead of collapsing them into a single flat hex (which always picks the wrong "dominant" colour). The 3MF metadata carries the colour stops; the catalog resolves the name; the swatch widget paints the gradient in CSS. No hand-curated paint-chip table — purely data-driven.

!!! tip "No hard-coded colour tables anywhere"
    BamDude deliberately carries no hard-coded `tray_id_name` / hex tables — they would inevitably mislabel third-party filaments. The catalog is the only source of truth — even if you're tempted to "shortcut" colour resolution somewhere.

### Transparent / clear filament

Transparent filament is a first-class colour. The spool colour editor has a dedicated **Clear** quick-swatch, and the hex field accepts an 8-digit `RRGGBBAA` value, so you can mark a spool as fully or partially transparent. Clear spools render as a **checkerboard** swatch everywhere the colour appears — inventory cards, AMS slot indicators, the colour picker — instead of showing up as an invisible or solid-black chip.

## :material-printer: Printable PDF labels

Find a specific spool in a closet of 50 partials by sticking a label on each one. The Inventory header has a **Print labels…** action that opens a multi-select picker pre-loaded with the currently filtered spools; every inventory card and table row also has a per-spool printer icon for one-shot label printing, and the selection toolbar's **Print labels for the selected spools** opens the same dialog on the ticked spools.

Once a design is chosen, the dialog shows a **Preview** — the label of the first selected spool, drawn from its real data — before anything is printed. **Print** opens the PDF in a new tab; **Save as PNG** next to it downloads the same labels as pictures at 203, 300 or 600 dpi, one PNG for one spool or a ZIP for several. The designs and sheets themselves are drawn under **Settings → Filament → Marking**. Details, limits and the desk label printer route: [Spool labels](labels.md), [Saving labels as pictures](labels.md#saving-labels-as-pictures).

Six pre-built templates:

| Template | Size | Sheet | Notes |
|---|---|---|---|
| **AMS holder (74 × 33)** | 74 × 33 mm | One per page | `ams_holder_74x33`. Fits popular Makerworld AMS Filament Label Holder inserts. Large enough for the full layout — swatch on the left, QR on the right, multi-line text in the middle (brand, material, hex, spool ID). |
| **AMS holder (75 × 55)** | 75 × 55 mm | One per page | `ams_holder_75x55`. Taller AMS-holder variant; same full layout (swatch + QR + multi-line text) with more vertical room. |
| **Box 40 × 30** | 40 × 30 mm | One per page | Common DK / Brother roll size; fits between the AMS holder and the 62×29 box label. Roomy enough for swatch + QR + full text column including hex code — good for filament-bag and storage-bin labels. |
| **Box label** | 62 × 29 mm | One per page | Sized for Brother PT/QL and Dymo small-label stock. Carries QR + storage location. |
| **Avery L7160** | 38.1 × 63.5 mm | A4, 21 per sheet | EU sheet stock. Carries QR. |
| **Avery 5160** | 25.4 × 66.7 mm | US Letter, 30 per sheet | US sheet stock. Carries QR. |

Every label carries the colour swatch (with multi-colour stripes for spools with `extra_colors`), brand in **bold** at the top so it reads at arm's length, material/subtype, the colour **hex code** (`#RRGGBB`, alpha-stripped, uppercase) so near-identical colour+material spools are still tellable apart from up close, the spool's display name, the **spool ID** as the killer at-a-glance field for telling 8 spools of "PLA White" apart, and (where the size allows) a QR code that a phone can use to open the spool in BamDude.

### Display name follows your template

The bold central line on each label reuses the same **Spool display name** template the Filament page uses (Settings → Filament → **Spool display name**). So if you set the template to `{brand} {material} {color_name} (#{id})` for the inventory list, that's exactly what gets printed on each label too. The 18 placeholders (`{id}`, `{brand}`, `{material}`, `{subtype}`, `{color_name}`, `{slicer_filament_name}`, `{note}`, `{label_weight_g}`, `{label_weight_kg}`, `{remaining_g}`, `{remaining_kg}`, `{remaining_pct}`, `{color_hex}`, `{cost_per_kg}`, `{purchase_date}`, `{filament_diameter}`, `{lot}`, `{material_number}`) are documented in the same Settings panel that lets you edit the template.

### How the QR deeplink resolves

New built-in inventory labels include a key tied to the original spool record. Renaming the spool or editing its lot keeps the label valid. The editor checks that record again when you save from a current label. Deleting the record invalidates its label. A deleted spool's number is not handed out again; a number reused before this rule, or after restoring an older backup, still cannot make the label find another spool. Existing number-only labels still open the inventory by number. Reprint them to use **Scan spool label**. Spoolman labels keep their existing links.

The address printed in the link comes from the first available source below.

1. The `external_url` setting (Settings → Network → External URL) — preferred so a phone scan reaches your public BamDude URL rather than an internal address.
2. The `APP_URL` environment variable.
3. The current request's scheme + host (whatever you'd see in your browser when you fired the export).

For phone-scan workflows, set `external_url` once — then every label across every template prints the right deeplink.

### Assign by scanning a label

In the built-in inventory, open **Assign Spool** on the intended AMS slot and choose **Scan spool label**. To assign a storage location, open **Inventory → Locations** and use the scan button on the intended location's row.

Choose **Use camera** or **Choose photo**. For camera access, open BamDude over HTTPS. Photo selection also works when the camera is unavailable. BamDude retries large photos at higher resolution if the first pass cannot read the QR code. Review the detected spool name and number, then confirm the assignment or move.

### Picker UX for large libraries

The modal scales to large inventories with:

- **Search** — substring across the composed display name, brand, and `#ID`.
- **Material filter chips** — derived from the visible spools.
- **Select all visible / Deselect visible / Clear all** — selections survive filter changes (additive), so you can narrow to "PLA only", select all, then narrow to "PETG", and add those too.
- **Sort toggle (By ID / By colour)** — *By ID* (default) lists spools in ascending-ID order; *By colour* hue-clusters them (chromatic colours ordered by hue, achromatic neutrals ordered by lightness trailing the rainbow) so a printed sheet comes out rainbow-ordered. Session-only — resets to By ID each time you open the picker.

### Server-side rendering

PDFs are rendered server-side via ReportLab + qrcode. Pure Python, no headless browser, output is byte-identical across browsers, Avery sheets align to <0.1 mm. Endpoints (both gated on `inventory:read`):

- `POST /inventory/labels` — local-DB spools.
- `POST /spoolman/labels` — Spoolman-backed spools (only when Spoolman integration is enabled).

Both accept `{spools: [{id, display_name?}], template}` and return `application/pdf` via streaming response. Capped at 500 spools per request.

## :material-account-multiple: Permissions

| Permission | Effect |
|---|---|
| `inventory:read` | View spool list and AMS assignments; **render PDF labels**. |
| `inventory:create` | Add new spools. |
| `inventory:update` | Edit spool fields, assign to slots, set spool-specific K-profile overrides, archive and restore spools — and **delete** them, one at a time or in bulk. A spool with usage history, in a slot or in a running print cannot be deleted and is archived instead — see [Mass actions](#mass-actions). |
| `inventory:delete` | Listed in the group editor and held by the default Administrators and Operators groups, but no inventory action checks it: deleting spools is covered by `inventory:update`. |
| `inventory:view_assignments` | Specifically the spool-on-slot indicators rendered on printer cards. Granted to Viewers separately so a non-operator can see "what's loaded where" without getting `inventory:read`. |

## :material-clipboard-list: Settings reference

The relevant settings keys and where each one is set:

| Setting | Where | Default | Effect |
|---|---|---|---|
| `low_stock_threshold` | The pencil on the **Low Stock** card of the Filament page | `20` | Spool remaining percentage at which the `filament_low` notification fires (range 0.1 – 99.9). |
| `disable_filament_warnings` | Settings → Filament → Filament checks → **Disable filament warnings** | `false` | Master mute for low / out-of-filament alerts. |
| `prefer_lowest_filament` | Settings → Filament → Filament checks → **Drain the emptiest spool first** | `true` | When automatically assigning a source, after compatibility and exact-colour preference favour the lowest remaining source to use up odd ends first. Tracked AMS grams and firmware percentages are separate tiers. |
| `default_filament_cost` | Settings → Printing → Cost Tracking → **Default filament cost (per kg)** | `25` | Per-kg fallback cost when a spool's `cost` field is unset. |
| `spoolman_enabled` | Settings → Filament → Filament Tracking | `false` | Toggle the Spoolman integration. See [Spoolman](spoolman.md). |

### Spool order {#spool-order}

**Settings → Filament → Spool order** sets the order spools are offered in. It is a list of sort levels — a field and a direction (**Ascending** / **Descending**) each — applied top to bottom: the second level orders the spools the first one leaves equal. Material, then brand, then the least remaining first is a typical setup. Pick a field under **Add a level…**, arrange the levels with the up and down arrows, and press **Save order**; **Reset to built-in** removes every level.

Two places follow it:

- **The dialog for putting a spool into a slot** lists the spools in this order.
- **The Filament page**, while no column is chosen: a line above the table reads *Order from settings: …* and names the levels. Clicking a column header still sorts by that column.

The fields are **Name (by template)** — the spool name as your display-name template composes it — **Material**, **Subtype**, **Brand**, **Colour name**, **Slicer profile**, **Remaining, g**, **Remaining, %**, **Used, g**, **Label weight**, **Added**, **Purchased**, **Last used**, **Last dried**, **Storage location**, **Cost per kg**, **Lot**, **Material number** and **Spool number**.

With no levels set, the slot dialog orders by material, brand and colour, and the Filament page by spool number. The order applies to Spoolman inventories too.

### Sync Weights from AMS (recovery tool)

When the built-in inventory is in use, **Settings → Filament** exposes a **Sync Weights from AMS** button below the mode selector. It force-syncs all inventory spool weights from the live AMS `remain%` sensor values on currently-connected printers.

Use this **only** to recover from corrupted weight data — for example, if a printer power-off event reset all spools' tracked grams to zero. The sync overwrites stored `weight_used` values with what the AMS reports right now. Printers must be online for the sync to read sensor values.

Two kinds of spools are left out, and counted as skipped in the result:

- **Spools on a printer whose print is not booked yet** — a print that is running, or finished but not yet charged. The AMS reading already contains part of that print's filament, so syncing it would count the filament twice. A second message says how many printers were left out; sync again once their prints are finished. The **Sync AMS Weights to Spoolman** button of Spoolman mode waits the same way.
- **Spools with a [weight entered by hand](#hand-entered-weight-lock)** — unlock them first if the AMS reading should replace your figure.

!!! warning "Low resolution — recovery only"
    AMS `remain%` is integer-precision (1 % steps = ~10 g for a 1 kg spool). For day-to-day tracking, rely on the automatic 3MF-based deduction described above — it's accurate to the gram. **Sync Weights from AMS** is a recovery tool, not the normal accounting path.

### Spool Catalog

Pre-defined empty-spool weights for quick selection when adding spools. Ships with 90+ entries covering the common manufacturers (Bambu Lab cardboard core, eSun, Polymaker, Overture, etc.). Lives at **Settings → Filament → Spool Catalog**.

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

No. Use **Quick Add (Stock)** mode to add spools with just material + weight. Stock spools track weight, usage, and cost; you can edit them later to assign a profile. In full mode the **Filament family** is required — pick the closest available family (a generic PETG for a third-party PETG, for example), or create your own with the picker's **Create new family…** row.

### I have different printers (P1S + H2D) and nozzles — do presets matter?

The spool inventory itself is **printer-agnostic**. Add a spool once, assign it to any printer's AMS slot. Printer-model filtering only kicks in when you **Configure AMS Slot** (telling the printer which profile to use) — there the preset list is filtered by printer model so you only see compatible profiles.

### Is inventory only for loaded spools?

No. The inventory tracks **all your spools** — loaded and unloaded. You can log every spool you own, even ones sitting on a shelf. The *In Printer* summary card shows how many are currently loaded; the rest are tracked just the same (weight remaining, usage history, cost, drying schedule).

### What's the difference between Assign Spool and Configure Slot?

See [the comparison table](#configure-ams-slot-vs-assign-spool) above. Short version: **Assign Spool** does both — links the inventory row for tracking and configures the slot using the spool's profile. **Configure Slot** only does the printer-side configuration. Use Assign for normal workflow; use Configure when you want to override settings or set up a slot without an inventory spool.

### Where do the filament families come from?

From the built-in catalog (every official Bambu filament, offline) plus your own — cloud-mirrored, locally imported, or created in BamDude. Even without a cloud login the list is never empty. See [Where families come from](#where-families-come-from) and [Filament Families](filament-families.md).
