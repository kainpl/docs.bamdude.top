---
title: Filament Inventory & Spoolman
description: Built-in BamDude spool inventory plus optional bi-directional sync with a self-hosted Spoolman instance
---

# Filament Inventory & Spoolman

BamDude ships with a **first-class filament inventory** — the **Filament** page in the sidebar. It is the source of truth for spool weight, RFID, location, and cost — no external service required. If you already run [Spoolman](https://github.com/Donkie/Spoolman), the optional sync layer keeps both systems in step; if you don't, BamDude does the whole job on its own.

!!! tip "You don't need Spoolman"
    Built-in inventory works fully standalone. Spoolman sync is purely an integration choice for users who already centralise spools across multiple tools (e.g. OctoPrint, Mainsail, Klipper, multiple slicer hosts). Pick whichever flow matches your setup.

=== ":material-package-variant: Built-in inventory"

    BamDude-native — no external service, no network round-trips, every column lives in `data/bamdude.db`.

=== ":material-sync: Spoolman sync"

    Add-on integration with a self-hosted Spoolman server. Bidirectional, tunable per concern (weight vs. location vs. partial-usage reporting).

---

## :material-package-variant: Built-in Inventory

Open **Filament** in the sidebar. Each row is a physical spool — manually added, RFID-imported, or auto-created from an AMS scan.

### :material-plus-box: Adding spools

The "Add Spool" form covers everything BamDude tracks per spool:

| Field | Notes |
|-------|-------|
| `brand` | Free text (e.g. `Polymaker`, `Bambu Lab`, `SUNLU`). |
| `material` | `PLA`, `PETG`, `ABS`, `TPU`, `PA`, `PC`, `PVA`, `ASA`, … |
| `subtype` | `Basic`, `Matte`, `Silk`, `CF`, `Tough`, … |
| `color_name` + hex | Free-text colour name plus an `#RRGGBBAA` swatch. The hex input normalises every keystroke — paste `#FFAA00` and BamDude pads it to `FFAA00FF`. |
| `purchase_date` | When you actually bought it. Distinct from `created_at` (when the row was imported). The "Added" column prefers this when set. |
| `filament_diameter` | `1.75` or `2.85`. Defaulted to `1.75`. |
| `label_weight_g` | Advertised net weight on the label (default 1000 g). |
| `core_weight` | Empty-spool weight, used for scale-based remaining calculations. Looked up from the catalog when brand+spool match. |
| `lot` | 1-based position inside a purchase bundle. The bulk-add path can auto-number `1..N` server-side via the **auto-increment lots** checkbox. |
| `cost_per_kg` | Bare number, no currency symbol. Multiplied by per-print weight for the archive's cost field. |
| `note` | Free-form text (`Kitchen shelf`, `Open since Apr 12`, …). |
| `tag_uid` / `tray_uuid` | RFID identifiers. Empty for manually-added spools — bind a tag later via the matcher. |

Bulk-add takes a quantity and creates N rows in one go — combine with **auto-increment lots** to number a 5-spool bundle as `lot 1..5` without typing each one.

### :material-format-text: Spool display-name template

The Filament page synthesises a human label per spool via a user-configurable template. Edit it under **Settings → Filament → General → Spool display name**.

Default: `{brand} {material} {subtype} {color_name}` (renders as e.g. `Polymaker PLA Matte Jade White`; a spool with no subtype simply leaves that word out). The template changes only how a spool is named — searching finds a spool by its brand, material, subtype, colour, note or lot whatever the template shows.

| Token | Source | Example |
|-------|--------|---------|
| `{brand}` | column | `Polymaker` |
| `{material}` | column | `PLA` |
| `{subtype}` | column | `Matte` |
| `{color_name}` | column | `Jade White` |
| `{slicer_filament_name}` | column | `Polymaker PolyTerra PLA @Bambu Lab X1C` |
| `{note}` | column | `Kitchen shelf` |
| `{label_weight_g}` | column | `1000` |
| `{label_weight_kg}` | computed | `1` (round) or `0.75` (fractional) |
| `{remaining_g}` | computed `label − used` | `750` |
| `{remaining_kg}` | computed | `0.75` |
| `{remaining_pct}` | computed | `75%` |
| `{color_hex}` | computed from `rgba` | `#FF3300` |
| `{cost_per_kg}` | column | `25` |
| `{purchase_date}` | column | `2026-04-15` |
| `{filament_diameter}` | column | `1.75` |
| `{lot}` | column | `3` |

!!! tip "Unknown tokens stay verbatim"
    Typo a token like `{brnd}` and the live preview keeps it as-is — that surfaces the mistake immediately instead of silently collapsing to an empty space.

### :material-view-column: Column visibility

Click **Configure Columns** on the Filament page to toggle which columns are visible and in what order. Settings are per-user.

**Visible by default:** `brand`, `material`, `color_name`, `remaining`, `location`, `note`, `purchase_date`.
**Hidden by default:** `created_at` ("added time" — superseded by `purchase_date`).

A column your saved layout does not know yet lands at its default position rather than at the end, so a saved layout needs no re-arranging.

### :material-magnify-scan: Auto-assign by RFID

The Filament page header has an **Auto-assign** action: BamDude scans every connected printer's AMS slots, matches each slot's `tag_uid` / `tray_uuid` against inventory rows, and creates `SpoolAssignment` records in bulk. Useful after a multi-spool reload — one click, no manual picking.

### :material-link-plus: Bind unknown RFID to a manual spool

When an unknown RFID tag appears on a printer, the AMS slot popover offers to bind it to an existing inventory row that doesn't have a tag yet. Use case: third-party brands without RFID, refilled cores, or a spool you bought before you started using BamDude. Pick the row, confirm, and the tag is now attached — next scan auto-resolves.

---

## :material-sync: Spoolman Sync

Optional. Connect BamDude to a [Spoolman](https://github.com/Donkie/Spoolman) instance and the two systems mirror each other.

### :material-spool: What is Spoolman?

[Spoolman](https://github.com/Donkie/Spoolman) is an open-source, self-hosted filament inventory manager for 3D printing. It runs as a separate service (Docker, bare metal, or a Spoolman-compatible cloud instance) and exposes a REST API for spool tracking, usage history, vendor/material taxonomy, low-stock alerts, and — most importantly for multi-tool setups — a single source of truth that other tools (OctoPrint, Mainsail, Klipper, multiple slicer hosts) can sync against.

If you only run BamDude, the built-in inventory above already does everything Spoolman does. The integration is for users who **already** have Spoolman because some other host in their setup needs it.

### :material-link: Connecting {#spoolman-connecting}

1. **Settings** → **Filament** → **General** → **Filament Tracking** → **Spoolman**
2. Type the **Spoolman URL** (e.g. `http://192.168.1.50:7912` or a docker-compose service alias like `http://spoolman:7912`)
3. **Save address**

The address is saved only with **Save address** — never while you type, and never together with another setting. BamDude cannot tell whether a new address leads to the same Spoolman database, so it treats it as another one: before saving, the page says how many slot assignments and K-profile links made in Spoolman mode will be removed, and saves only when you confirm. Assign spools to the slots again afterwards. Emptying the address removes nothing.

There is no API-key field: BamDude talks to Spoolman's open HTTP API, so a Spoolman behind an authenticating proxy has to be reachable from BamDude without credentials.

The status beside the URL asks the configured Spoolman whether it answers, every time — not whether BamDude happened to talk to it earlier. While it does not answer, a **Connect** button retries. There is no Disconnect: Spoolman is a plain HTTP API with no session to close, and the enable switch is what turns the integration off.

The extra fields BamDude keeps on a spool (the RFID tag, the slicer preset, the colour name) are registered in Spoolman by the first write that carries them, so enabling the integration from Settings is enough — nothing has to be created in Spoolman by hand for the first AMS sync. A field that already exists is left alone, including one you renamed or retyped in Spoolman's own UI.

!!! tip "Network reachability"
    BamDude must be able to reach the Spoolman URL from inside its own process. On docker-compose, put both services on the same network and use the service alias; on bare metal, a LAN hostname or static IP is enough.

### :material-tune: Sync controls

| Setting | Effect |
|---------|--------|
| `spoolman_enabled` | Master switch. |
| `spoolman_sync_mode` | `auto` (push every AMS change immediately) or `manual` (wait for an explicit Sync button click). |
| `spoolman_disable_weight_sync` | Skip `remaining_weight` updates on existing Spoolman spools. Use this when Spoolman is your authoritative weight tracker (its granular usage reporting beats AMS estimates). |
| `spoolman_report_partial_usage` | When a print fails or is cancelled, report the **estimated grams used up to the abort point** based on layer progress, instead of dropping the whole estimate. Helps Spoolman keep an accurate weight after failures. |

!!! warning "Switching the tracking mode removes slot assignments"
    Choosing **Built-in Inventory** or **Spoolman** under **Settings → Filament → General → Filament Tracking** removes every AMS slot assignment of the mode you leave — each mode keeps its own, and in the new one spools are assigned to slots anew. The page therefore asks before it switches, saying how many assignments go and which printers are printing right now: filament those prints use reaches neither inventory. Nothing is switched by the click alone.

    A spool being put into a slot at that moment is waited for, and its assignment goes with the others; if that takes too long, the switch says so and asks to try again. An assignment that arrives during the switch is refused — make it again in the mode now in use. The same holds when the mode changes through a settings restore from Git or a reset of all settings through the API (a reset returns to the built-in inventory).

    A print that finishes and cannot charge a slot it drew from — its assignment was removed during the print, or it never had one — sends a **Filament not charged** notification naming the slots and the grams. It rides the **Missing spool assignment** toggle of your notification providers.

### :material-sync-circle: What syncs

- **AMS slot ↔ Spoolman spool** — Each loaded slot maps to a Spoolman spool ID. Material, brand, colour, and (unless `disable_weight_sync` is on) remaining weight are kept in step. A clear or translucent spool keeps its transparency in Spoolman's `color_hex` (eight characters); an opaque one stays six characters, exactly as your existing filaments are stored, so nothing already there is rewritten or duplicated.
- **Print consumption** — Each completed print reports the grams used to Spoolman as a usage event. Cancelled / failed prints respect `spoolman_report_partial_usage`.
- **Location** — the **Storage Location** you pick for a spool is written to Spoolman's `location` field, and Spoolman's location names appear in BamDude's Storage Location list. A printer slot is not a storage location: which spool is loaded where is tracked by slot assignments, not written to `location`.
- **RFID** — Bambu Lab tray UUIDs are passed through to Spoolman's `extra.tag` field and, on Spoolman 0.27 and newer, linked as Spoolman's native tags as well (see [Tags](#spoolman-tags)).

!!! note "Weights wait for the print to be booked"
    While a print is running, and until its usage has been charged, the automatic weight sync of tagged spools and **Sync AMS Weights to Spoolman** leave that printer out — otherwise the printer's remaining-percent reading would be written first and the print's own grams taken off on top of it. Sync again once the print is finished and booked.

### :material-link-off: Unlinking

There is no separate **Unlink** button on a slot, in either sync mode. A spool is taken apart from a slot or from its tag in two places:

- **Unassign** on the AMS slot's hover card removes the slot assignment. The spool stays in Spoolman.
- **Clear RFID Tag** in the spool's form on the **Filament** page removes the tag link — `extra.tag` and, on Spoolman 0.27 and newer, the spool's native tags (see [Tags](#spoolman-tags)).

### :material-tag-multiple: Tags {#spoolman-tags}

BamDude keeps a spool's tag in Spoolman's `extra.tag` field. Spoolman 0.27 and newer also links tags to spools itself; with such a server BamDude works with both:

- A spool tagged in Spoolman itself is recognised as that spool when its reel shows up in an AMS — no second spool is created beside it.
- Linking a tag writes `extra.tag` **and** Spoolman's native tag, so Spoolman and other tag readers find the same spool. `extra.tag` is always written, so an older reader loses nothing.
- Unlinking a spool, or **Clear RFID Tag** in the spool form, removes both.
- Linking a tag that another spool already holds is refused, and the refusal names that spool — an archived one included. Unlink the tag there first.

Spools linked while the server had no native tags carry `extra.tag` alone. **Settings → Filament → Filament Tracking** shows a **Spoolman native tags** block for a connected Spoolman that supports them: **Check tags** lists what would be copied, what is already in Spoolman, and every conflict (two spools sharing one tag, a tag that belongs to another or an archived spool, a tag linked to a filament); **Copy tags** then copies the ones without a conflict. Conflicts are never settled for you — decide in Spoolman which spool each tag belongs to and check again. AMS slot IDs that stand in for a tag and the tags of archived spools are not copied.

Older Spoolman versions work through `extra.tag` alone.

### :material-poll: Sync Results

After every sync (auto or manual) BamDude shows a result panel:

- **Synced count** — number of spools successfully synced.
- **Skipped spools** — list of spools that couldn't sync, with a per-row reason (e.g. "Non-Bambu Lab spool", "No matching material in Spoolman", "Manual unlink in effect"). Each skipped row shows its location, color swatch, and the reason text.
- **Errors** — any HTTP / network / data errors encountered during the run.

!!! note "Bambu Lab RFID detection"
    Auto-sync only fires for **official Bambu Lab spools with RFID** — third-party, refilled, or SpoolEase spools are intentionally skipped to avoid creating bogus rows in Spoolman. Bambu Lab spools are identified by their hardware identifiers (`tray_uuid` and `tag_uid`), not by filament preset name. Non-Bambu spools can still be **assigned to a slot by hand** (see below).

### :material-chart-line: Usage tracking detail

Each completed print reports per-filament consumption to Spoolman as a usage event:

1. BamDude extracts per-filament usage data from the archived 3MF file (slicer estimates).
2. For partial prints (failures, cancellations), per-layer G-code analysis provides precise consumption up to the exact failure layer. If the reel changed during the print — an AMS backup taking over, or a new reel loaded into the same slot, on single- and multi-colour prints alike — that consumption is divided by the stretch each reel actually printed before the stop, exactly as the built-in inventory divides it (see [Inventory](inventory.md)).
3. On completion, each spool's usage is reported individually — multi-material prints update each linked spool separately. The tray each filament came from is the one the print was sent with; for a print BamDude did not send and whose mapping it could not see (an A1 publishes none), a one-filament print is charged to the tray the printer itself reported feeding from. Only when nothing names a tray is it charged by tray position — a guess, logged as a warning, and then the archive keeps the colour and material the file was sliced with rather than taking them from a spool picked by position. On a printer with two external holders (X2D, H2D) a print fed from an external spool charges the holder that was actually used.
4. **AMS remain-% fallback for slots the 3MF didn't cover.** When a slot has no 3MF estimate — a no-3MF "Untitled" print (the `.gcode.3mf` was never downloadable, so the archive is a fallback row) **or** partial 3MF coverage where a loaded slot wasn't in the slice info — BamDude falls back per-slot to the AMS remaining-percentage drop. At completion it writes `(remain% at start − remain% at end) × the spool's size in Spoolman` grams as the usage event — the spool's own size, or its filament's weight when the spool states none (see [Spool size, tare and price](#spoolman-spool-size)). It uses that Spoolman weight (not the AMS's unreliable reported tray weight) and **skips any slot swapped mid-print** (tray UUID changed), since it can't split consumption across two spools.

This matches BamDude's per-spool tracking model — the same numbers feeding the Stats page also feed Spoolman. A failed or cancelled print is charged by the same calculation in both inventories. Spoolman itself keeps a spool's totals and no per-print log; the per-print record is BamDude's own (see [Usage history and Forecast](#spoolman-usage-history)).

**Usage Spoolman did not take is reported.** If Spoolman does not answer when a print ends, that print's usage is not written and is not retried later. BamDude sends the **Filament not charged** notification naming the slots and the grams, and the server log names the print, the spools and the grams, so the weight can be corrected by hand.

**The archive learns what was charged.** Each charge that lands is priced from its own spool — the spool's price over the spool's size when set, else its filament's price over the filament's weight — so a multi-material print bills each slot at its own rate, and grams no spool could price are covered at the farm's default filament rate. The archive's filament weight follows the same rule as the built-in inventory: a failed print, or one whose 3MF never arrived, records the grams actually charged; a completed print keeps its slicer estimate. A spool with no price leaves the recorded cost alone. **Recalculate Costs** on the Stats page keeps a cost priced this way rather than re-pricing it at the default rate, and says how many it kept.

### :material-tray-full: AMS slot mapping (hover card)

Hover over any AMS slot on the Printers page to see:

| Field | Source |
|-------|--------|
| **Vendor** | Bambu Lab or Generic — read from the RFID tag. |
| **Profile** | Filament type and subtype (`PLA Basic`, `PETG Translucent`, …). |
| **Color** | Color name + swatch — resolved through the BamDude color catalog (single source of truth). Spoolman has no colour-name field, so a spool whose name BamDude never stored shows the catalog's name for its swatch rather than its subtype (`Silk+` is not a colour); searching finds a spool by the colour name you can see. |
| **K Factor** | Pressure-advance value currently active for this slot. |
| **Fill Level** | Remaining percentage, with visual bar. |
| **Spool ID** | Linked Spoolman spool ID (only when Spoolman is enabled and the slot is linked). |

#### Fill Level for AMS Lite / external spools

AMS Lite units (e.g. A1 series) have **no weight sensor** and always report 0% fill level. When a spool is linked to Spoolman and Spoolman has weight data, BamDude uses Spoolman's remaining weight instead:

- **AMS with weight sensor** — uses AMS percentage directly (no change).
- **AMS Lite (reports 0%)** — falls back to Spoolman: `(remaining_weight / filament_weight) × 100`.
- **External spool** — shows fill level from Spoolman if linked (otherwise shows `—`).

When Spoolman data is the source, the hover card displays "(Spoolman)" next to the percentage so you can distinguish the data source.

### :material-link: Slot actions on the hover card

Each AMS slot's hover card carries the actions for the spool in that slot; which ones appear depends on the slot's state:

| State | Button | What it does |
|-------|--------|--------------|
| **A spool is assigned or tag-linked** | **Open in inventory** | Opens that spool on BamDude's **Filament** page. Spoolman's own interface opens from the **Open Spoolman** button in that page's header. |
| **A spool is assigned** | **Replace spool** | Opens the spool picker and puts another Spoolman spool into the slot in one step. |
| **A spool is assigned** | **Unassign** | Removes the slot assignment. The spool stays in Spoolman. |
| **No spool assigned** | **Assign Spool** | Opens the spool picker — this is also how a refilled core or a third-party spool with no RFID is bound to a slot. Disabled, with the reason, while Spoolman is unreachable. |

The card has no **Link to Spoolman**, **Manual Link** or **Open in Spoolman** button: a slot is bound to a spool by assigning it.

To remove a **tag link**: open the spool's form on the **Filament** page and press **Clear RFID Tag** — it clears `extra.tag` and, on Spoolman 0.27 and newer, the spool's native tags.

### :material-database: Adding spools — AMS vs Inventory view comparison

| Surface | Action | When to use |
|---------|--------|-------------|
| **From the AMS** | A Bambu Lab RFID spool that Spoolman does not know yet is created there by the AMS sync | First-time onboarding, adding a freshly-loaded Bambu spool to Spoolman. |
| **In Spoolman directly** | Add Spool form on Spoolman's web UI | Bulk-import historical spools, adding spools you haven't loaded yet, vendor/cost data entry. |
| **Filament page** (BamDude) | **Add Spool** on the **Filament** page | In Spoolman mode the form works on Spoolman's spools, so the spool is created in Spoolman without leaving BamDude. |

The slot assignment is what lets the AMS hover card resolve a slot to a Spoolman row.

### :material-robot: Auto-features

Three things happen without a click while Spoolman is enabled. They have no switches of their own — the AMS-driven ones follow **Sync Mode** (**Automatic** / **Manual Only**), and usage reporting for stopped prints follows **Report Partial Usage for Failed Prints**:

- **Auto-sync on print complete** — every completed print reports per-filament usage individually to Spoolman, so spool quantities update automatically.
- **Auto-detect on AMS change** — when AMS filament changes, BamDude detects the new configuration, matches against Spoolman, and updates slot mappings without intervention.
- **Auto-clear location on removal** — when spools are removed from AMS, BamDude detects the empty slot, finds Spoolman spools with the matching location string, and clears the `location` field. The spool is now available for other printers.

!!! info "Slot markers in `location`"
    A Spoolman spool's `location` field may hold a slot marker — `H2D-Workshop - AMS A1`, `AMS-HT A1`, `External Spool` — naming the slot the spool was once loaded into. BamDude does not write such markers. The ones that exist are left on your Spoolman spools, but they are not offered as storage locations (unless a spool here is filed under one). A marker is cleared from a Bambu Lab spool once it leaves the AMS.

### :material-server-network: Multi-printer sync

A single Spoolman instance serves multiple BamDude printers (and other tools) simultaneously:

- Each printer's AMS syncs independently.
- Different spools per printer, separate usage tracking.
- Unified inventory in Spoolman — one source of truth across the farm.

This is the main reason most farm operators choose to run Spoolman alongside BamDude even when BamDude's built-in inventory works standalone — Spoolman is the cross-tool hub.

---

## :material-table-cog: Inventory UI (BamDude-side, Spoolman-backed)

When you run BamDude against Spoolman, the **Filament page** (`/inventory`) and **Printers page** (`/`) light up a full first-class Spoolman experience: AMS slot assignments live in BamDude's own tables (so the assignment survives reboots and travels in BamDude backups), K-profiles per spool round-trip across BamDude installs that share the same Spoolman backend, and a free-form storage label sits next to every spool.

### :material-table: The Filament page in Spoolman mode

With Spoolman switched on, the **Filament** page is BamDude's own page fed by Spoolman's data — the table and the cards, the spool form, labels and bulk actions all work on Spoolman's spools. A Spoolman spool's [label](labels.md) carries the same fields as a local one. When a Spoolman address is set, an **Open Spoolman** button in the page header opens Spoolman's own interface in a new tab.

A few things differ from the built-in inventory:

- **Material number** shows the filament's article number from Spoolman and is read-only — change it in Spoolman.
- **Last dried** is recorded for Spoolman spools as well: by a drying cycle in the AMS the spool sits in, or by hand in the spool form.
- **Reset counter** zeroes the consumed figure BamDude shows and leaves Spoolman's own numbers — used and remaining weight — alone. A bulk reset says which spools could not be reset.
- **Import CSV** / **Export CSV** are disabled — use Spoolman's own CSV import and export.
- **Re-price usage** on the **Statistics** page works on the built-in inventory's records only and is not available in Spoolman mode.

To remove a saved preset, use **Clear filament family or preset** in the spool editor. The spool still shows its catalog filament name in inventory. See [Filament Families](filament-families.md) for how copying a spool carries its preset forward.

BamDude reads a known finish and color from Spoolman product names. For example, `Matte Scarlet Red` shows `Matte` as the subtype and `Scarlet Red` as the color. Recognized finishes include `Aero`, `Lite` and `High Speed`. Extra spaces within a finish are normalized for display. A saved color name takes priority. Editing a spool keeps the original catalog name when the material and subtype stay the same, including when a shared filament needs a separate catalog entry for the edited spool.

### :material-history: Usage history and Forecast {#spoolman-usage-history}

Spoolman keeps a spool's totals and no per-print log, so BamDude keeps its own record of every print it charges to a Spoolman spool. That record feeds the **History** view of the Filament page, the usage history in the spool form, the **Forecast** tab and the **Reorder Alert** / **Stock Break Alert** notifications — the same views the built-in inventory has (see [Inventory → History](inventory.md#history)).

- **The record starts with the first print BamDude charges.** Prints charged before BamDude kept this record cannot be recovered from Spoolman, which stores no per-print data.
- **Removing records does not touch Spoolman.** Deleting one record or clearing a spool's history removes BamDude's records only; the spool's weight in Spoolman is not changed.
- **History belongs to a Spoolman address.** When the Spoolman URL changes, the records made for the previous address are kept aside and the views start empty for the new one; putting the previous address back brings its history back. If the new address is the same Spoolman database (the host was renamed or moved), **History** says how many records are kept aside and offers **Same database — keep the history** to bring them over. A new address also removes every slot assignment and K-profile link made in Spoolman mode (see [Connecting](#spoolman-connecting)); **Same database** brings the history over, not the assignments.
- **The address or database cannot change during a print.** While any print is accounted in Spoolman, saving a new Spoolman address or declaring a new database behind the same address is refused until the print ends — the spool numbers that print recorded belong to the database it started on. Switching Spoolman on or off and **Same database** still work. While a finished print is being charged, any change of these settings is refused for a moment.
- **Forecast needs Spoolman.** The stock is kept in Spoolman, so while Spoolman does not answer there is no forecast to show.

The [Git backup](backup.md) carries this history with the **Spool Inventory** category and restores it onto the Spoolman the restoring installation uses.

### :material-weight-gram: Spool size, tare and price {#spoolman-spool-size}

Spoolman keeps how much filament a full spool holds on the spool itself and falls back to the filament's weight only when the spool has none — so one filament can have spools of different sizes. BamDude reads it the same way everywhere: the list, the weight syncs, usage tracking and the price per gram all use the spool's own size.

- **Label Weight** — creating a spool writes its size to that spool; editing it changes only that spool, never the filament or its other spools.
- **Empty Spool Weight** — the spool's own tare, then its filament's, then the vendor's empty-spool weight, in Spoolman's own order.
- **Cost per kg** — Spoolman stores a spool's price as what *that spool* cost, not as a rate. The spool form shows it converted through the spool's size and converts back when you save: a 250 g spool that cost 10 reads as 40 per kg, and typing 40 per kg for a 250 g spool stores a price of 10. A price set on the filament is spread over the filament's weight.
- **What a print is charged** — the spool's price, or the filament's when the spool has none. The **Cost/kg** column shows that charged rate, and the print dialog prices each slot and shows its grams left from the Spoolman spool bound to that slot.

!!! note "A price that was meant as a rate"
    Because the price on a Spoolman spool is the price of that spool, a spool that is not 1 kg and whose price was entered as a per-kg rate reads a different cost per kg: a 250 g spool carrying a price of 40 shows 160 per kg. Nothing stored is rewritten — correct the cost in the spool form.

**Spools whose size differs from their filament.** A spool's size in Spoolman is set when the spool is created and does not follow a later change of the filament's weight, so a spool can show a size other than the one you expect from its filament. For a connected Spoolman, **Settings → Filament → Filament Tracking** lists every such active spool with its own size, its filament's size and the grams left. **Use the filament's size for this spool** changes that one spool after a confirmation; what it has consumed stays, so its grams left change with the size.

### :material-table-row: Three pieces of state

| Where | What | Why it isn't on Spoolman directly |
|-------|------|-----------------------------------|
| `spoolman_slot_assignments` (BamDude DB) | Which Spoolman spool ID lives in `(printer_id, ams_id, tray_id)`, with that spool's Spoolman creation stamp. AMS 0..7 + 255 (external feed). One spool per slot. | Spoolman's own `location` is free text — using it as the source of truth for "this spool is in printer X AMS A slot 3" loses structure (e.g. you can't filter inventory by "all spools currently loaded"). The structured table is queryable and gets cleared automatically on slot empty. |
| `spoolman_k_profile` (BamDude DB) | Pressure-advance + setting_id per `(spoolman_spool_id, printer_id, extruder, nozzle_diameter)`, with the spool's Spoolman creation stamp. Single + dual extruder. | A K-profile is bound to physical filament ↔ physical printer + nozzle, not to a Spoolman row alone. Storing it BamDude-side means re-tapping the same Bambu RFID on a different printer doesn't lose the calibration done elsewhere. |
| `spool.storage_location` (BamDude DB column) | Free-form label like `Drybox 3`, `Shelf A4`, `Workshop / locker 2`. | Mirrors the Spoolman `location` field but lives BamDude-side too so it shows in the Inventory page columns + the spool form even on Spoolman-mode installs. |

The Spoolman `location` field is left untouched on Spoolman's side — operators can still populate it manually from Spoolman's own UI as a free-text label. BamDude's structured assignment table is the source of truth for "what's currently in printer X".

### :material-printer: Printers page — Spoolman-mode slot integration

Every slot kind on the Printers page reads Spoolman state when Spoolman mode is on:

- **Regular AMS slots** (AMS 0..7, tray 0..3) — fill bar, preset name, color swatch, and the hover card "Assigned spool" pill all read from `spoolman_slot_assignments` joined against `spoolman_inventory/spools`. When the slot has no RFID-linked spool, the slot-assignment row drives the fill computation.
- **HT (high-temperature) slots** — same flow as regular AMS, plus the H2D Ext-R single-tray external slot.
- **External Spool 254 / 255** — reads from the same assignment table; the slot's hover card shows the assigned spool name + remaining weight + storage location.

Per slot the hover card carries:

| Button | When it appears |
|--------|-----------------|
| **Assign Spool** | No spool is assigned to the slot. Opens the picker of Spoolman spools — no RFID involved, so it also covers a refilled core or a third-party spool. |
| **Replace spool** | A spool is assigned. Puts another spool into the slot in one step. |
| **Unassign** | A spool is assigned. Clears the BamDude-side assignment; the spool stays in Spoolman. |
| **Open in inventory** | A spool is assigned or RFID-linked. Opens that spool on the **Filament** page. |

The card carries no separate tag-link buttons (**Link to Spoolman**, **Manual Link**, **Open in Spoolman**), so one slot never shows two ways to bind a spool.

What an assignment does to the slot:

- **The spool's own filament preset configures the slot.** When no calibration is linked to the spool, the preset stored on it — set in the spool form, or taken from the tray when BamDude created the spool — tells the printer what is loaded. A preset of another material than the spool's is ignored, and the slot gets a stand-in profile for the spool's material instead.
- **A pressure-advance profile is selected by default.** When no profile was linked to the spool by hand, the slot gets the active calibration for that printer, filament, nozzle diameter, flow type and extruder — as in the built-in inventory.
- **An archived spool cannot be assigned** to a slot.
- **Archiving or deleting a spool releases its slot.** The slot is freed on the printer card and the next print from it is not charged to that spool. While the spool sits in a slot of a printer that is printing, archiving and deleting are refused until the print ends.
- **A spool BamDude has printed with is archived, not deleted.** **Delete** is refused for a Spoolman spool that has usage history in BamDude for the Spoolman database in use (records kept aside for a previous address, or made before a new database was declared behind the same address, do not count), or that a running print can still charge (by its slot, its tray tag or the print's journal) — archive it instead. While a finished print is being charged, every delete is refused for a moment; try again. A delete Spoolman confirms also removes the spool's slot and K-profile links in BamDude; if those could not be removed, or a slot of a running print keeps the spool until the print ends, the message says so. If Spoolman does not confirm a delete, BamDude says so and changes nothing locally — check the spool in Spoolman.
- **While Spoolman is switched on but unreachable**, the printer card neither offers nor accepts an assignment — it says *Spoolman is unreachable. Spools can be assigned once it responds again.* Spools of the built-in inventory are not offered in its place.

### :material-shield-check: Assignments know their spool {#spoolman-binding-identity}

Spoolman gives the number of a deleted spool to the next spool it creates, and another Spoolman database uses the same numbers, so a number alone does not say which spool an assignment was made for. BamDude remembers the spool of every slot assignment and K-profile link by Spoolman's own creation stamp, and checks it before it charges a print, writes a weight from the AMS, records drying, re-applies slots after a backup-compatibility change or picks a K-profile:

- **An assignment whose number now names another spool — or a spool deleted in Spoolman — is not charged.** The print sends **Filament not charged: spool changed** (through the *Missing spool assignment* notification), and the slot's assignment and that number's K-profile links made for the other spool are removed. While the printer's print is still being accounted, the assignment stays until the print ends, and that print's own record is checked at its end.
- **Sync** moves an assignment to the spool whose tag is in the tray. For a tray without a tag it only checks the assignment against the spool its number names now.
- **Assignments and links made before this check** are trusted the first time they are read and remembered from then on.
- **A 404 from a reverse proxy** in front of a restarting Spoolman is Spoolman not answering, not a deleted spool: nothing is removed.

### :material-flash: K-profile auto-reapply on AMS change

When an AMS slot's contents change (RFID re-tap, slot reset, slicer-side `extrusion_cali_sel` issued from another path), BamDude looks up the assigned spool's stored K-profile for the exact `(printer_id, extruder, nozzle_diameter)` triplet. If the printer's live `cali_idx` differs from the stored K-profile's, BamDude re-issues the right `extrusion_cali_sel` over MQTT to restore the K-value the operator chose last time. Without this, firmware would reset the K back to slot index 0 on every re-tap.

Drift detection is bounded — BamDude only re-issues when there's a genuine difference, so the steady-state push doesn't spam the printer.

### :material-storage: Storage location column

The **Filament** page has a **Storage location** column on every backend (local-DB inventory + Spoolman). Edit per row inline; the value is stored on `spool.storage_location` and surfaced everywhere the spool is rendered (cards, hover-cards, spool form, search). On Spoolman-mode installs the field is BamDude-local — Spoolman's own `location` field stays for the operator to manage independently if they prefer that flow.

### :material-tag-multiple: Wider RFID UID support

`spool.tag_uid` holds up to 32 characters. Bambu's RFID UIDs are 16 hex chars, but third-party tags (e.g. NTAG216 stickers) carry up to 32 hex chars — the column is wide enough to bind those tags to refilled cores without truncation.

### :material-api: API surface

The full Spoolman inventory feature ships under `/api/v1/spoolman/inventory/*` (19 endpoints, all gated on `RequirePermission(INVENTORY_*)`). Highlights worth knowing about for scripting:

- `GET /spoolman/inventory/spools` + `GET /spoolman/inventory/spools/{id}` — list / single spool with BamDude joins (slot assignment, storage location, K-profile counts).
- `POST /spoolman/inventory/spools` + `POST /spoolman/inventory/spools/bulk` + `PATCH /spoolman/inventory/spools/{id}` — create / bulk-create / update.
- `POST /spoolman/inventory/spools/{id}/archive` + `/restore` — soft-delete via Spoolman's archive flag. Archiving releases the spool's slot and answers `409` while that slot feeds a running print.
- `DELETE /spoolman/inventory/spools/{id}` + `POST /spoolman/inventory/spools/bulk-delete` — delete in Spoolman. Answers `409` with a code — `spool_in_use` (with `reasons`), `spool_feeds_print`, `print_closing`, `spool_state_changed` or `spoolman_source_changed` (try again) — and no `DELETE` reaches Spoolman (the checks before it may read the spool from Spoolman); `504` / `502` `spoolman_outcome_unknown` when Spoolman did not confirm. A confirmed delete answers `{"status": "deleted"}`, with a `warning` when its local cleanup has something to say. The bulk answer counts `deleted`, lists `warnings` and `errors` (with `code` and `reasons`); duplicates are ignored.
- `POST /spoolman/inventory/slot-assignments` + `DELETE /spoolman/inventory/slot-assignments/{id}` — assign / unassign.
- `GET /spoolman/inventory/slot-assignments` — list-all-enriched (joined with spool data).
- `POST /spoolman/inventory/spools/{id}/sync-weight` — pull current AMS weight into the spool row.
- `POST /spoolman/inventory/ams-weights/sync` — bulk sync every assigned slot's weight in one call.
- `GET /spoolman/inventory/spools/{id}/k-profiles` + `POST /spoolman/inventory/spools/{id}/k-profiles` — per-spool K-profile read / save.
- `PATCH /spoolman/inventory/filaments/{id}` — rename + propagate `spool_weight` to every spool of that filament (toggle `keep_existing_spools` to cap the cascade).
- `GET /spoolman/inventory/filaments` + `POST /spoolman/inventory/spools/{id}/link-tag` — picker queries.

Full API contract: [API Reference → Spoolman Inventory](../reference/api.md).

---

## :material-database-import: Moving off Spoolman: one-way import

Sync above keeps Spoolman as the source of truth. If you would rather **stop**
running Spoolman and keep its data, `scripts/import_spoolman.py` copies its
spools into BamDude's own inventory once, over the API:

```bash
python scripts/import_spoolman.py \
    --spoolman-url http://localhost:7912 \
    --bamdude-url  http://localhost:8000 \
    --api-key      <a BamDude API key with inventory:update> \
    --dry-run
```

Drop `--dry-run` to write. Each spool carries over its material, colour, brand,
label weight, used weight, cost per kg (computed from Spoolman's per-spool
price) and tag UID; the note records the Spoolman id it came from, so a second
run is easy to spot and undo.

!!! warning "It is an import, not a sync"
    It runs once and does not look back. Turn Spoolman sync **off** first, or
    the two will each believe they own the same spools.

---

## :material-help-circle: Troubleshooting

**Connection failed**

- Verify the Spoolman URL — open it in a browser to confirm Spoolman itself is up.
- Check network reachability from inside the BamDude container/process to Spoolman (e.g. `curl http://spoolman:7912/api/v1/info` from inside the BamDude container).
- If Spoolman sits behind authentication, BamDude cannot sign in to it — there is no API-key setting. Make it reachable from BamDude without credentials.
- Firewall / Docker network isolation — both services need to be on the same network or have explicit routing.

**Sync not working**

- Confirm `spoolman_enabled` is on and the status beside the URL says **Connected**.
- Check Spoolman's own logs — newer / older Spoolman versions occasionally tighten or change their REST contract.
- Verify the spool is recognised as Bambu Lab (auto-sync only fires for Bambu RFID — see above). For non-Bambu spools, use **Assign Spool** on the slot's hover card.
- For multi-printer setups, confirm the printer name in BamDude matches the location string Spoolman expects.

**Wrong spool linked**

- Open the spool's form on the **Filament** page and press **Clear RFID Tag** to unlink.
- From BamDude's AMS hover card, **Replace spool** → pick the correct Spoolman spool.
- Verify the RFID tag UUID matches what Spoolman has stored — mismatched UUIDs are the most common cause of "linked, but pointing at the wrong row".

---

> Originally based on [Bambuddy](https://github.com/maziggy/bambuddy) documentation.
