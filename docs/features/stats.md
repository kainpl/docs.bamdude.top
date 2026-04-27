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
| **Filament consumed** | Sum of `filament_grams` across completed archives, grouped by material/colour. |
| **Print time** | Sum of `duration_seconds`. |
| **Energy used** | Sum of `(energy_end_kwh − energy_start_kwh)` over completed archives that had a smart-plug bound at print start. Falls back to a ranged sum from `smart_plug_energy_snapshots` when individual-print captures are missing. |

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
- At `print_complete` it reads it again (`energy_end_kwh`) and the delta becomes that print's consumption.
- The reads are restart-resilient — values come from a fresh DB session each time, never an in-memory dict, so a backend restart between start and complete doesn't break the capture.

If a plug isn't bound, or the plug is offline at one of the two boundaries, the archive's energy fields stay null and that print is excluded from the energy KPI.

### Hourly snapshot fallback

Per-print capture relies on the plug being responsive at exactly the right two moments. To smooth over plug outages, BamDude also takes an **hourly snapshot** of every plug's cumulative kWh into `smart_plug_energy_snapshots`. For date-range "total energy" queries the stats page falls back to this table when individual-print fields are missing — `_sum_snapshot_deltas()` computes per-plug `max(0, last_in_range - baseline)` and sums across plugs.

The snapshot table is bounded — old rows are pruned after a configurable retention window so it doesn't grow forever.

## :material-bullseye-arrow: Cost calculations

| Cost | Formula |
|---|---|
| **Per-print filament cost** | Filament grams × spool's `cost / weight`. Falls back to `default_filament_cost / 1000` per gram if no spool was assigned. |
| **Per-print energy cost** | `(energy_end - energy_start) × energy_cost_per_kwh`. Zero when no plug capture. |
| **Total** | Filament + energy. |

These feed the per-archive cost line in the archive detail card and the project / print-plan totals.

## :material-database-export: Exporting

The header has an "Export CSV" button that dumps the current view (filtered range) as a CSV with one row per archive — useful for invoicing print-as-a-service runs or feeding the data into another tool.

The Maintenance page has a similar Excel export for service intervals — see [Maintenance](maintenance.md).
