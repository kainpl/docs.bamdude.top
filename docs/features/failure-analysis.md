---
title: Failure Analysis
description: Identify patterns in print failures across the BamDude archive history
---

# Failure Analysis

Understand *why* prints fail by analysing patterns across materials, printers, time-of-day, and print duration. Failure Analysis is the **retrospective** complement to [Obico AI Detection](obico.md), which catches failures **proactively** while they happen.

---

## :material-information: What It Is

The Failure Analysis dashboard reads every row in your `print_archives` table whose `status` is `failed`, `aborted`, or `cancelled` and groups it across multiple dimensions, so you can spot whether a particular printer, filament, or time-of-day is dragging your success rate down.

The data is computed live by `FailureAnalysisService` (`backend/app/services/failure_analysis.py`) — no separate aggregation table. Every query honours your selected date range and optional printer / project filters.

!!! info "Permission Required"
    All failure-analysis views are gated by `stats:read`. Viewers and Operators have it by default; Administrators always do.

---

## :material-chart-pie: Failure Rate Dashboard

Top of the Statistics page shows the overall picture for the selected period:

| Metric | Description |
|--------|-------------|
| **Total prints** | Every archive that wasn't a pure upload (status `archived` is excluded) |
| **Failed prints** | Sum of `failed` + `aborted` + `cancelled` |
| **Failure rate (%)** | `failed / total × 100`, rounded to one decimal |
| **Trend** | Weekly bucket of failure-rate over the period — improving, stable, or worsening |

```
Total: 412   Failed: 27   Rate: 6.6%
```

The trend chart bins archives by week (`created_at`) and plots `failure_rate` per bucket. Older buckets first, current week last.

---

## :material-link-variant: Correlation Views

Slice the failure set by four independent axes. Each chart is a server-side `GROUP BY` on the failed-archive subset.

### By Filament Type

| Material | Failures |
|----------|:--------:|
| PLA | 4 |
| PETG | 9 |
| ABS | 11 |
| TPU | 3 |

Pulled from `PrintArchive.filament_type`. A single material dominating the failure column usually means moisture, temperature, or bed-adhesion tuning for that material — not a global problem.

### By Printer

| Printer | Failures |
|---------|:--------:|
| Workshop X1C | 2 |
| Office P1S | 7 |
| Garage A1 | 18 |

Pulled from `PrintArchive.printer_id`, joined to `printers.name`. A single machine carrying most of the failures is a strong signal for hardware service — dirty nozzle, worn belts, mis-calibrated bed.

### By Time-of-Day

24-hour heatmap built from `PrintArchive.started_at.hour`. Useful for catching environmental issues:

- Overnight peaks → shop temperature drop, ABS warping
- Afternoon peaks → direct sunlight on the printer, drafts
- Concentrated "Monday morning" failures → first-run cold-start issues

### By Print Duration

Long prints have more opportunities to fail. The view bins archives into:

| Bucket | Typical Risk |
|--------|--------------|
| < 1 h | Bed adhesion, first-layer |
| 1–4 h | Layer adhesion, light warping |
| 4–12 h | AMS swap mid-print, filament tangles |
| > 12 h | Power events, room temp swings, AI detection saves |

---

## :material-text-box-search: Common Failure Modes

A glossary of what the failures usually mean — useful when reading `failure_reason` strings on archive cards.

### Adhesion / First-Layer

- Print pops off the bed
- Warped corners on first 5–10 layers
- Likely causes: dirty bed, wrong bed temp, filament humidity, missing brim

### Layer Shift

- Sudden offset along X or Y
- Likely causes: belt slip, gantry collision, head crashed into print, vibration from neighbouring printer

### Spaghetti

- Tangled blob of filament where the model used to be
- Root cause is almost always a previous layer-shift or adhesion failure that wasn't caught
- This is exactly what [Obico](obico.md) is meant to detect proactively

### Stringing / Oozing

- Strings between separated parts
- Blobs on top surfaces
- Quality issue, not a hard failure — but if severe enough you'll mark the archive as failed

### Filament Jam / Runout

- AMS reports tray empty
- Extruder grinds, temperature spikes
- Multi-colour prints with bad swap calibration trigger this most often

### AMS Swap Mid-Print

- Wrong colour at swap point
- Tower contamination
- Often correlates with `subtask_id` retries after a queue reschedule

### OOM During Slicing

- Not a print failure per se, but the slicer ran out of memory during prep, the gcode got truncated, and the printer aborted partway through
- Usually caught upstream of the queue but logged as `failed` if the print actually started

---

## :material-magnify: Drilldown

Click any cell in any of the correlation views and BamDude opens the [Archives](archiving.md) page **pre-filtered to that scope** — for example clicking *Failures by Printer → Garage A1* filters the archive list to that printer's failed prints. From there you can:

- Open each archive's 3MF to see exactly which plate / which objects
- Add a `failure_reason` if the printer didn't report one
- Tag the archive (`adhesion-fail`, `layer-shift`, `ams-jam`, …) for future filtering
- Compare against a known-good print of the same model

---

## :material-calendar-range: Date Range Picker

The dashboard supports four built-in ranges plus a custom picker:

| Range | Effective Window |
|-------|------------------|
| Last 7 days | `now − 7d` to `now` |
| Last 30 days | `now − 30d` to `now` |
| Last 90 days | `now − 90d` to `now` |
| Last 365 days | `now − 365d` to `now` |
| Custom | Inclusive `date_from` … `date_to` |

When `date_from` / `date_to` are present, the trend's weekly buckets cover the explicit range; otherwise they follow the rolling `days` window. The default when no range is set is **30 days**.

---

## :material-eye: Proactive vs Retrospective

Failure Analysis tells you *what already broke*. To stop a print mid-failure rather than autopsying it later:

| Tool | When |
|------|------|
| [Obico AI Detection](obico.md) | While the print is running — captures the camera feed, classifies frames, fires a notify / pause / pause+power-off action |
| **Failure Analysis** | After the fact — slice the archive history to find systemic patterns |
| [Notifications](notifications.md) | At the moment of failure — Telegram/Discord/email/Pushover/ntfy/HA push |

Use them together: Obico catches the next spaghetti, Failure Analysis tells you *which printer* keeps producing them.

---

## :material-export: Export

The same numbers feed the [Export](export.md) page. `GET /api/v1/archives/stats/export` returns a CSV/XLSX with the summary, per-reason / per-filament / per-printer breakdowns, and the weekly trend — handy for monthly reporting or for feeding a BI tool.

---

## :material-link: Related

- [Statistics](statistics.md) — broader analytics (filament usage, energy, costs)
- [Archiving](archiving.md) — the underlying `print_archives` table and its `status` / `failure_reason` fields
- [Obico AI Detection](obico.md) — proactive failure detection
- [Notifications](notifications.md) — alert routing for failure events

---

## :material-lightbulb: Tips

!!! tip "Don't delete failed prints"
    They're the data. Every deleted failure is a hole in the analysis.

!!! tip "Tag consistently"
    Pick a small tag vocabulary (`adhesion-fail`, `layer-shift`, `ams-jam`, `spaghetti`, `warping`) and stick to it — that's what makes the drilldown filters useful months later.

!!! tip "Photograph the bed"
    Add a photo to each failed archive. The Statistics page won't show photos, but when you're cross-referencing a run of `Garage A1` failures the bed photos tell you in two seconds whether it's adhesion or a head crash.

!!! tip "Compare with success"
    The most useful debugging move is opening a failed archive next to a successful print of the same model on the same printer — the slicing-parameter delta usually points right at the cause.
