---
title: Filament Inventory & Spoolman
description: Built-in BamDude spool inventory plus optional bi-directional sync with a self-hosted Spoolman instance
---

# Filament Inventory & Spoolman

BamDude ships with a **first-class filament inventory** (Settings → Filaments). It is the source of truth for spool weight, RFID, location, and cost — no external service required. If you already run [Spoolman](https://github.com/Donkie/Spoolman), the optional sync layer keeps both systems in step; if you don't, BamDude does the whole job on its own.

!!! tip "You don't need Spoolman"
    Built-in inventory works fully standalone. Spoolman sync is purely an integration choice for users who already centralise spools across multiple tools (e.g. OctoPrint, Mainsail, Klipper, multiple slicer hosts). Pick whichever flow matches your setup.

=== ":material-package-variant: Built-in inventory"

    BamDude-native — no external service, no network round-trips, every column lives in `data/bamdude.db`.

=== ":material-sync: Spoolman sync"

    Add-on integration with a self-hosted Spoolman server. Bidirectional, tunable per concern (weight vs. location vs. partial-usage reporting).

---

## :material-package-variant: Built-in Inventory

Open **Settings → Filaments**. Each row is a physical spool — manually added, RFID-imported, or auto-created from an AMS scan.

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

The Filaments page synthesises a human label per spool via a user-configurable template — search and sort use the same string. Edit it under **Settings → System → Spool Display Template**.

Default: `{brand} {material} {color_name}` (renders as e.g. `Polymaker PLA Jade White`).

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

Click **Column Config** on the Filaments page to toggle which columns are visible and in what order. Settings are per-user.

**Visible by default:** `brand`, `material`, `color_name`, `remaining`, `location`, `note`, `purchase_date`.
**Hidden by default:** `created_at` ("added time" — superseded by `purchase_date`).

Newly-added columns land at their default position rather than being appended to the end, so post-upgrade existing users don't have to re-arrange.

### :material-magnify-scan: Auto-assign by RFID

The Filaments page header has an **Auto-assign** action: BamDude scans every connected printer's AMS slots, matches each slot's `tag_uid` / `tray_uuid` against inventory rows, and creates `SpoolAssignment` records in bulk. Useful after a multi-spool reload — one click, no manual picking.

### :material-link-plus: Bind unknown RFID to a manual spool

When an unknown RFID tag appears on a printer, the AMS slot popover offers to bind it to an existing inventory row that doesn't have a tag yet. Use case: third-party brands without RFID, refilled cores, or a spool you bought before you started using BamDude. Pick the row, confirm, and the tag is now attached — next scan auto-resolves.

---

## :material-sync: Spoolman Sync

Optional. Connect BamDude to a [Spoolman](https://github.com/Donkie/Spoolman) instance and the two systems mirror each other.

### :material-spool: What is Spoolman?

[Spoolman](https://github.com/Donkie/Spoolman) is an open-source, self-hosted filament inventory manager for 3D printing. It runs as a separate service (Docker, bare metal, or a Spoolman-compatible cloud instance) and exposes a REST API for spool tracking, usage history, vendor/material taxonomy, low-stock alerts, and — most importantly for multi-tool setups — a single source of truth that other tools (OctoPrint, Mainsail, Klipper, multiple slicer hosts) can sync against.

If you only run BamDude, the built-in inventory above already does everything Spoolman does. The integration is for users who **already** have Spoolman because some other host in their setup needs it.

### :material-link: Connecting

1. **Settings** → **Integrations** → **Spoolman**
2. Set the **URL** (e.g. `http://192.168.1.50:7912` or a docker-compose service alias like `http://spoolman:7912`)
3. (Optional) **API Key** — required only if your Spoolman instance is behind authentication; leave blank for the default open setup.
4. **Test Connection**
5. **Save**

!!! tip "Network reachability"
    BamDude must be able to reach the Spoolman URL from inside its own process. On docker-compose, put both services on the same network and use the service alias; on bare metal, a LAN hostname or static IP is enough.

### :material-tune: Sync controls

| Setting | Effect |
|---------|--------|
| `spoolman_enabled` | Master switch. |
| `spoolman_sync_mode` | `auto` (push every AMS change immediately) or `manual` (wait for an explicit Sync button click). |
| `spoolman_disable_weight_sync` | Skip `remaining_weight` updates on existing Spoolman spools — only push location. Use this when Spoolman is your authoritative weight tracker (its granular usage reporting beats AMS estimates). |
| `spoolman_report_partial_usage` | When a print fails or is cancelled, report the **estimated grams used up to the abort point** based on layer progress, instead of dropping the whole estimate. Helps Spoolman keep an accurate weight after failures. |

### :material-sync-circle: What syncs

- **AMS slot ↔ Spoolman spool** — Each loaded slot maps to a Spoolman spool ID. Material, brand, colour, and (unless `disable_weight_sync` is on) remaining weight are kept in step.
- **Print consumption** — Each completed print reports the grams used to Spoolman as a usage event. Cancelled / failed prints respect `spoolman_report_partial_usage`.
- **Location** — BamDude writes the printer name + AMS coordinates to Spoolman's `location` field (`H2D-1 AMS-A Slot 3` etc.). Always synced even with weight sync disabled.
- **RFID** — Bambu Lab tray UUIDs are passed through to Spoolman's tag field.

### :material-link-off: Unlinking

In `manual` sync mode, each Bambu spool card shows an **Unlink** button — useful when you want to migrate a spool from Spoolman back to BamDude-only inventory without breaking the AMS assignment.

### :material-poll: Sync Results

After every sync (auto or manual) BamDude shows a result panel:

- **Synced count** — number of spools successfully synced.
- **Skipped spools** — list of spools that couldn't sync, with a per-row reason (e.g. "Non-Bambu Lab spool", "No matching material in Spoolman", "Manual unlink in effect"). Each skipped row shows its location, color swatch, and the reason text.
- **Errors** — any HTTP / network / data errors encountered during the run.

!!! note "Bambu Lab RFID detection"
    Auto-sync only fires for **official Bambu Lab spools with RFID** — third-party, refilled, or SpoolEase spools are intentionally skipped to avoid creating bogus rows in Spoolman. Bambu Lab spools are identified by their hardware identifiers (`tray_uuid` and `tag_uid`), not by filament preset name. Non-Bambu spools can still be **manually linked** (see below).

### :material-chart-line: Usage tracking detail

Each completed print reports per-filament consumption to Spoolman as a usage event:

1. BamDude extracts per-filament usage data from the archived 3MF file (slicer estimates).
2. For partial prints (failures, cancellations), per-layer G-code analysis provides precise consumption up to the exact failure layer.
3. On completion, each spool's usage is reported individually — multi-material prints update each linked spool separately.
4. **AMS remain-% fallback for slots the 3MF didn't cover.** When a slot has no 3MF estimate — a no-3MF "Untitled" print (the `.gcode.3mf` was never downloadable, so the archive is a fallback row) **or** partial 3MF coverage where a loaded slot wasn't in the slice info — BamDude falls back per-slot to the AMS remaining-percentage drop. At completion it writes `(remain% at start − remain% at end) × the spool's Spoolman filament reference weight` grams as the usage event. It uses the Spoolman reference weight (not the AMS's unreliable reported tray weight) and **skips any slot swapped mid-print** (tray UUID changed), since it can't split consumption across two spools. Before this, no-3MF "Untitled" prints reported zero weight change to Spoolman.

This matches BamDude's per-spool tracking model — the same numbers feeding the Stats page also feed Spoolman, just routed through Spoolman's usage-history table on top of BamDude's local archive.

### :material-tray-full: AMS slot mapping (hover card)

Hover over any AMS slot on the Printers page to see:

| Field | Source |
|-------|--------|
| **Vendor** | Bambu Lab or Generic — read from the RFID tag. |
| **Profile** | Filament type and subtype (`PLA Basic`, `PETG Translucent`, …). |
| **Color** | Color name + swatch — resolved through the BamDude color catalog (single source of truth). |
| **K Factor** | Pressure-advance value currently active for this slot. |
| **Fill Level** | Remaining percentage, with visual bar. |
| **Spool ID** | Linked Spoolman spool ID (only when Spoolman is enabled and the slot is linked). |

#### Fill Level for AMS Lite / external spools

AMS Lite units (e.g. A1 series) have **no weight sensor** and always report 0% fill level. When a spool is linked to Spoolman and Spoolman has weight data, BamDude uses Spoolman's remaining weight instead:

- **AMS with weight sensor** — uses AMS percentage directly (no change).
- **AMS Lite (reports 0%)** — falls back to Spoolman: `(remaining_weight / filament_weight) × 100`.
- **External spool** — shows fill level from Spoolman if linked (otherwise shows `—`).

When Spoolman data is the source, the hover card displays "(Spoolman)" next to the percentage so you can distinguish the data source.

### :material-link: Open / Link / Manual link buttons

Each AMS slot's hover card carries a primary action button whose label depends on link state:

| State | Button | What it does |
|-------|--------|--------------|
| **Linked** | **Open in Spoolman** | Opens the spool's page in Spoolman in a new tab — edit vendor, cost, notes, weight directly there. |
| **Unlinked, Bambu Lab spool, candidates available** | **Link to Spoolman** | Opens a picker showing all unlinked Spoolman spools — pick one, click **Link** to confirm. |
| **Unlinked, Bambu Lab spool, no candidates** | **Link to Spoolman** (disabled) | No unlinked Spoolman spools currently available — add one in Spoolman first. |
| **Non-Bambu Lab spool** | **Manual Link** | Manually associate this slot with a Spoolman spool — bypasses RFID matching for refilled cores or third-party spools. |

To **unlink**: open the spool in Spoolman and clear the `extra.tag` field.

### :material-database: Adding spools — AMS vs Inventory view comparison

| Surface | Action | When to use |
|---------|--------|-------------|
| **From AMS hover** | **Add to Spoolman** when an unknown filament appears in a slot | First-time onboarding, adding a freshly-loaded Bambu spool to Spoolman. |
| **In Spoolman directly** | Add Spool form on Spoolman's web UI | Bulk-import historical spools, adding spools you haven't loaded yet, vendor/cost data entry. |
| **Inventory view** (BamDude) | Add via Settings → Filaments | When you want the spool to live in BamDude's inventory regardless of Spoolman state — useful for full-detail rows that Spoolman doesn't track (e.g. lot number, custom notes). |

Both backends co-exist; the link is what lets the AMS hover card resolve a slot to a Spoolman row.

### :material-robot: Auto-features

Three independent automation toggles (Settings → Spoolman):

- **Auto-sync on print complete** — every completed print reports per-filament usage individually to Spoolman, so spool quantities update automatically.
- **Auto-detect on AMS change** — when AMS filament changes, BamDude detects the new configuration, matches against Spoolman, and updates slot mappings without intervention.
- **Auto-clear location on removal** — when spools are removed from AMS, BamDude detects the empty slot, finds Spoolman spools with the matching location string, and clears the `location` field. The spool is now available for other printers.

!!! info "Location format"
    Spoolman locations follow the format `Printer Name - AMS X Slot Y`, e.g. `H2D-Workshop - AMS A Slot 3`.

### :material-server-network: Multi-printer sync

A single Spoolman instance serves multiple BamDude printers (and other tools) simultaneously:

- Each printer's AMS syncs independently.
- Different spools per printer, separate usage tracking.
- Unified inventory in Spoolman — one source of truth across the farm.

This is the main reason most farm operators choose to run Spoolman alongside BamDude even when BamDude's built-in inventory works standalone — Spoolman is the cross-tool hub.

---

## :material-table-cog: Inventory UI (BamDude-side, Spoolman-backed)

When you run BamDude against Spoolman, the **Inventory page** (`/inventory`) and **Printers page** (`/`) light up a full first-class Spoolman experience: AMS slot assignments live in BamDude's own tables (so the assignment survives reboots and travels in BamDude backups), K-profiles per spool round-trip across BamDude installs that share the same Spoolman backend, and a free-form storage label sits next to every spool. Built on upstream Bambuddy [#1241](https://github.com/maziggy/bambuddy/pull/1241) ported in BamDude **0.4.4**.

### :material-table-row: Three new pieces of state

| Where | What | Why it isn't on Spoolman directly |
|-------|------|-----------------------------------|
| `spoolman_slot_assignments` (BamDude DB) | Which Spoolman spool ID lives in `(printer_id, ams_id, tray_id)`. AMS 0..7 + 255 (external feed). One spool per slot. | Spoolman's own `location` is free text — using it as the source of truth for "this spool is in printer X AMS A slot 3" loses structure (e.g. you can't filter inventory by "all spools currently loaded"). The structured table is queryable and gets cleared automatically on slot empty. |
| `spoolman_k_profile` (BamDude DB) | Pressure-advance + setting_id per `(spoolman_spool_id, printer_id, extruder, nozzle_diameter)`. Single + dual extruder. | A K-profile is bound to physical filament ↔ physical printer + nozzle, not to a Spoolman row alone. Storing it BamDude-side means re-tapping the same Bambu RFID on a different printer doesn't lose the calibration done elsewhere. |
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
| **Link to Spoolman** | Slot has a Bambu RFID tag, no assignment exists yet, and there's at least one unlinked Spoolman spool whose `extra.tag` matches. |
| **Manual Link** | Slot has no RFID match (refilled core, third-party spool). Picker shows every unlinked Spoolman spool. |
| **Assign** | Slot is empty in inventory but operator wants to manually point it at a Spoolman spool (no RFID involved). |
| **Unassign** | Slot has either a Spoolman SlotAssignment OR a local SpoolAssignment — clears the BamDude-side assignment. |
| **Open in Spoolman** | Slot is RFID-linked. Opens the spool's Spoolman edit page in a new tab. |

The Link button auto-suppresses when a slot already has either a Spoolman SlotAssignment OR a local SpoolAssignment, so the operator can't accidentally double-bind.

### :material-flash: K-profile auto-reapply on AMS change

When an AMS slot's contents change (RFID re-tap, slot reset, slicer-side `extrusion_cali_sel` issued from another path), BamDude looks up the assigned spool's stored K-profile for the exact `(printer_id, extruder, nozzle_diameter)` triplet. If the printer's live `cali_idx` differs from the stored K-profile's, BamDude re-issues the right `extrusion_cali_sel` over MQTT to restore the K-value the operator chose last time. Without this, firmware would reset the K back to slot index 0 on every re-tap.

Drift detection is bounded — BamDude only re-issues when there's a genuine difference, so the steady-state push doesn't spam the printer.

### :material-storage: Storage location column

`Settings → Filaments` (Inventory page) gains a **Storage location** column shipped on every backend (local-DB inventory + Spoolman). Edit per row inline; the value is stored on `spool.storage_location` and surfaced everywhere the spool is rendered (cards, hover-cards, spool form, search). On Spoolman-mode installs the field is BamDude-local — Spoolman's own `location` field stays for the operator to manage independently if they prefer that flow.

### :material-tag-multiple: Wider RFID UID support

BamDude widens `spool.tag_uid` from 16 to 32 chars on Postgres (SQLite ignores VARCHAR length). Bambu's RFID UIDs are 16 hex chars, but third-party tags (e.g. NTAG216 stickers) carry up to 32 hex chars — the wider column lets you bind those tags to refilled cores without truncation.

### :material-api: API surface

The full Spoolman inventory feature ships under `/api/v1/spoolman/inventory/*` (19 endpoints, all gated on `RequirePermission(INVENTORY_*)`). Highlights worth knowing about for scripting:

- `GET /spoolman/inventory/spools` + `GET /spoolman/inventory/spools/{id}` — list / single spool with BamDude joins (slot assignment, storage location, K-profile counts).
- `POST /spoolman/inventory/spools` + `POST /spoolman/inventory/spools/bulk` + `PATCH /spoolman/inventory/spools/{id}` — create / bulk-create / update.
- `POST /spoolman/inventory/spools/{id}/archive` + `/restore` — soft-delete via Spoolman's archive flag.
- `POST /spoolman/inventory/slot-assignments` + `DELETE /spoolman/inventory/slot-assignments/{id}` — assign / unassign.
- `GET /spoolman/inventory/slot-assignments` — list-all-enriched (joined with spool data).
- `POST /spoolman/inventory/spools/{id}/sync-weight` — pull current AMS weight into the spool row.
- `POST /spoolman/inventory/ams-weights/sync` — bulk sync every assigned slot's weight in one call.
- `GET /spoolman/inventory/spools/{id}/k-profiles` + `POST /spoolman/inventory/spools/{id}/k-profiles` — per-spool K-profile read / save.
- `PATCH /spoolman/inventory/filaments/{id}` — rename + propagate `spool_weight` to every spool of that filament (toggle `keep_existing_spools` to cap the cascade).
- `GET /spoolman/inventory/filaments` + `POST /spoolman/inventory/spools/{id}/link-tag` — picker queries.

Full API contract: [API Reference → Spoolman Inventory](../reference/api.md).

---

## :material-help-circle: Troubleshooting

**Connection failed**

- Verify the Spoolman URL — open it in a browser to confirm Spoolman itself is up.
- Check network reachability from inside the BamDude container/process to Spoolman (e.g. `curl http://spoolman:7912/api/v1/info` from inside the BamDude container).
- If Spoolman has authentication enabled, double-check the API Key.
- Firewall / Docker network isolation — both services need to be on the same network or have explicit routing.

**Sync not working**

- Confirm `spoolman_enabled` is on and **Test Connection** still passes.
- Check Spoolman's own logs — newer / older Spoolman versions occasionally tighten or change their REST contract.
- Verify the spool is recognised as Bambu Lab (auto-sync only fires for Bambu RFID — see above). For non-Bambu spools, use **Manual Link**.
- For multi-printer setups, confirm the printer name in BamDude matches the location string Spoolman expects.

**Wrong spool linked**

- Open the spool in Spoolman, clear the `extra.tag` field to unlink.
- From BamDude's AMS hover card, **Manual Link** → pick the correct Spoolman spool.
- Verify the RFID tag UUID matches what Spoolman has stored — mismatched UUIDs are the most common cause of "linked, but pointing at the wrong row".

---

> Originally based on [Bambuddy](https://github.com/maziggy/bambuddy) documentation.
