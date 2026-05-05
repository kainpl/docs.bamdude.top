---
title: Stats & Energy
description: Cumulative print stats, per-print energy capture from your smart plug, and date-range farm-wide totals
---

# Stats & Energy

The Stats page is BamDude's dashboard for "what did the farm actually do?" — print counts, filament consumed, energy used, time spent. It's driven entirely by `print_archives` (no separate stats table to drift), so the numbers always match the archive list under the same filter.

## :material-chart-bar: Top-level KPIs

The header bar shows four lifetime counters:

| Metric | Source |
|---|---|
| **Prints completed** | `print_archives` rows with `status='completed'`. |
| **Filament consumed** | Sum of `filament_used_grams` across completed archives, grouped by material/colour. |
| **Print time** | Sum of `print_time_seconds`. |
| **Energy used** | Sum of `energy_kwh` (the per-print delta the dispatcher computed at completion) over completed archives that had a smart-plug bound at print start. Falls back to a ranged sum from `smart_plug_energy_snapshots` when individual-print captures are missing. |

Each KPI also shows the matching cost when `default_filament_cost` and `energy_cost_per_kwh` are configured under Settings → System.

## :material-calendar-range: Time-range filter

A range picker above the KPIs scopes everything below — last 7 days / last 30 / last quarter / custom range. The KPIs become the same metrics over the chosen range; the per-printer breakdown re-renders to match.

## :material-chart-line: Time-series charts

Below the KPIs, two stacked line charts:

- **Prints per day** — bar chart of completed archives bucketed by date, colour-coded by printer.
- **Filament per day** — same bucketing, stacked by material so you can see "we shifted from PLA-heavy to PETG-heavy in March".

Hover any bar to see the breakdown for that day.

## :material-printer-3d-nozzle: Per-printer breakdown

A table at the bottom rolls every printer's contribution: prints, filament, time, energy, cost. Click a row to drill into the archive list pre-filtered to that printer.

## :material-flash: Per-print energy capture

Energy tracking is opt-in. To capture it on each print:

1. Add a smart plug under **Settings → Smart Plugs** (Tasmota, Home Assistant, REST/webhook, or MQTT — see [Smart Plugs](smart-plugs.md)).
2. Bind the plug to a specific printer.
3. The plug must report cumulative kWh — Tasmota's `Total` field, HA's `sensor.<plug>_energy_total`, etc.

On each print:

- At `print_start`, BamDude reads the plug's current kWh into `print_archives.energy_start_kwh`.
- At `print_complete` it reads the plug again, computes `current - energy_start_kwh`, and stores **the delta directly** in `print_archives.energy_kwh`. There is no separate `energy_end_kwh` column — the end reading is consumed during the subtraction and discarded.
- The reads are restart-resilient — values come from a fresh DB session each time, never an in-memory dict, so a backend restart between start and complete doesn't break the capture.

If a plug isn't bound, or the plug is offline at one of the two boundaries, `energy_kwh` stays null and that print is excluded from the energy KPI.

### Hourly snapshot fallback

Per-print capture relies on the plug being responsive at exactly the right two moments. To smooth over plug outages, BamDude also takes an **hourly snapshot** of every plug's cumulative kWh into `smart_plug_energy_snapshots`. For date-range "total energy" queries the stats page falls back to this table when individual-print fields are missing — `_sum_snapshot_deltas()` computes per-plug `max(0, last_in_range - baseline)` and sums across plugs.

The snapshot table is bounded — old rows are pruned after a configurable retention window so it doesn't grow forever.

## :material-bullseye-arrow: Cost calculations

| Cost | Formula |
|---|---|
| **Per-print filament cost** | `filament_used_grams × (spool.cost / spool.weight)`. Falls back to `default_filament_cost / 1000` per gram if no spool was assigned. |
| **Per-print energy cost** | `energy_kwh × energy_cost_per_kwh`. Zero when no plug capture (`energy_kwh IS NULL`). |
| **Total** | Filament + energy. |

These feed the per-archive cost line in the archive detail card and the project / print-plan totals.

## :material-database-export: Exporting

The header has an "Export CSV" button that dumps the current view (filtered range) as a CSV with one row per archive — useful for invoicing print-as-a-service runs or feeding the data into another tool.

The Maintenance page has a similar Excel export for service intervals — see [Maintenance](maintenance.md).

### Export options

| Format | Best for | Contents |
|---|---|---|
| **CSV** | Spreadsheets, ad-hoc analysis, scripts | One row per archive: printer, file, status, start time, duration, filament grams, filament details, energy kWh, costs |
| **Excel** | Reports with formatting, sharing with non-technical stakeholders | Same columns as CSV plus formatting, frozen header, per-column types |

Both exports respect the **currently active filters** — date range, printer-selection chips, per-user filter. Reset filters first to export the full dataset.

---

## :material-view-dashboard: Widget-based dashboard

The Stats page is a customisable grid of widgets, not a fixed report. You can:

- **Drag** any widget by its header to reorder
- **Resize** via the corner handle — cycles through Small → Medium → Large → Full Width
- **Hide** widgets you don't need with the eye icon — restore them from the **Hidden** menu in the dashboard header
- **Reset to default** — the header has a button that restores the original layout

Layout is **persisted per-user** in the backend, so the same login on a different device sees the same arrangement.

### Available widgets

| Widget | What it shows |
|---|---|
| **Print Success Rate** | Pie chart — completed / failed / stopped split. Per-printer filterable. |
| **Filament by Type** | Pie chart of material distribution (PLA / PETG / ABS / ...). Click segments to filter. |
| **Print Activity Calendar** | GitHub-style heatmap, daily print count, click any day to drill into that day's archives. |
| **Print Duration Distribution** | Bucket bar chart: `<30m`, `30m–1h`, `1–2h`, `2–4h`, `4–8h`, `8–12h`, `12–24h`, `24h+`. Surfaces your typical print length. |
| **Time Accuracy** | Predicted-vs-actual print times. Per-printer averages and trend — answers "is calibration drifting?" |
| **Printer Utilization** | Hours of active printing per printer; idle-time percentage. |
| **Recent Activity** | Feed of the last 10 completed prints; click to open the archive card. |
| **Quick Stats** | KPI tiles (prints, filament, time, cost, energy) for the active range. |

### Printer Selection

Multi-select chips above the widgets scope the **entire dashboard** to a subset of printers:

- Click a chip to toggle that printer on/off
- All widgets re-render against the filtered set immediately
- The export button respects the same filter

Useful for "show me just my MakerSpace's row of A1s" or "compare X1C-A vs X1C-B side by side".

### Per-User filtering

When you hold the `stats:filter_by_user` permission (Administrators only by default), a **user dropdown** appears in the stats header next to the timeframe selector. Selecting a user filters every widget, the failure-analysis report, and CSV/Excel exports to that user's prints — useful for universities, makerspaces, or any environment that needs per-person accountability or cost tracking.

| Filter value | Effect |
|---|---|
| **All Users** | Default — global statistics |
| `<specific user>` | Only that user's prints |
| **No User (System)** | Prints without user attribution (slicer-initiated, pre-auth, virtual-printer uploads) |

!!! info "Granting the permission"
    To give the dropdown to non-admins, create a custom group in **Settings → Users** and add `stats:filter_by_user`. See [Authentication](authentication.md).

### Energy "warming-up" indicator

In **Total Consumption** energy mode, date-range energy is computed from hourly snapshots of each smart plug's lifetime counter (see [Smart Plugs](smart-plugs.md)). On a brand-new install — or shortly after upgrading — the first snapshot before your selected range may not exist yet. The Energy Used / Energy Cost tiles show a small yellow warning icon with a tooltip explaining the situation.

After ~1 hour of runtime the indicator disappears for any range that starts after the first snapshot. The KPI value during the warming-up window is computed against `0` baseline, which over-counts by whatever the plug was at install time — wait the hour before reading the number.

---

## :material-cash: Cost configuration

Cost tiles only show numbers when the underlying inputs are configured.

1. **Settings → System** — set **Currency** (`USD`, `EUR`, `UAH`, etc.) and **`energy_cost_per_kwh`**
2. **Settings → Filaments / Spoolman** — set per-spool `cost` + `weight` (or a global `default_filament_cost` per kg)
3. Stats picks up the rates immediately; new prints store them on the archive at completion time

### Recalculate Costs

Existing archives keep the prices that were active when they completed — historical data isn't auto-rewritten when you bump rates. To bring everything up to current pricing:

1. Click **Recalculate Costs** in the dashboard header
2. Every archive's filament + energy costs are recomputed against current spool / config rates
3. The dashboard re-renders against the new totals

!!! info "Reprint cost behaviour"
    Reprints are **additive** — a reprint cost adds to the original archive's total instead of overwriting it, so the per-archive total reflects the cumulative spend across every run of that file. This means stats numbers track real money spent, not "what the original print would cost at today's rate."

---

## :material-refresh: Auto-refresh

The Stats page polls every **60 s** so dashboards left open during a print session stay fresh without a manual reload. The refresh icon in the header forces an immediate refetch — useful right after a long print finishes if you don't want to wait the next tick.

Mutations from elsewhere in the app (deleting an archive, recalculating costs, editing a filament price) invalidate the underlying queries automatically — you don't need to click refresh after them.
