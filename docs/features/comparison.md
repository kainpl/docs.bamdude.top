---
title: Archive Comparison
description: Side-by-side comparison of 2–5 archives — slicer settings, outcome, and a success/failure correlation analysis that highlights which settings tracked with success or failure
---

# Archive Comparison

Archive Comparison takes 2–5 archives and lays them out as a side-by-side table — every comparable field as a row, every archive as a column, differences highlighted, plus an automatic analysis of which settings correlate with success vs failure when the selection contains both outcomes.

## :material-compare: What it is

Open the modal with two or more archives selected; BamDude calls `GET /api/v1/archives/compare?archive_ids=...` and renders the result. Useful for:

- **A/B testing a profile change** — same model printed twice, layer height bumped from 0.20 mm to 0.16 mm, see what else moved with it.
- **Regression analysis after a firmware update** — line up the last successful prints before the update against the failures after.
- **Iterating on a calibration print** — calibration cube, temperature tower, retraction tower across multiple attempts.
- **Investigating a specific failure** — pick one bad print and three good ones with the same model; the success-correlation block tells you which numeric settings differed.

## :material-cursor-default-click: Opening the modal

1. Go to **Archives**.
2. Multi-select 2–5 rows (Ctrl/Cmd-click or Shift-click).
3. Click **Compare** in the toolbar.

The modal closes on **Esc** or click on the dimmed backdrop.

!!! tip "Limits enforced server-side"
    Fewer than 2 archives → `400 At least 2 archives required for comparison`. More than 5 → `400 Maximum 5 archives can be compared at once`. The frontend disables the Compare button outside that range.

## :material-table: What's compared

The backend (`backend/app/services/archive_comparison.py`) compares a fixed list of fields:

| Field | Label | Unit |
|---|---|---|
| `layer_height` | Layer Height | mm |
| `nozzle_diameter` | Nozzle Diameter | mm |
| `bed_temperature` | Bed Temperature | °C |
| `nozzle_temperature` | Nozzle Temperature | °C |
| `filament_type` | Filament Type | — |
| `filament_used_grams` | Filament Used | g |
| `print_time_seconds` | Print Time | (rendered as `Nh Mm`) |
| `total_layers` | Total Layers | — |
| `status` | Status | — |

These come from the 3MF metadata BamDude extracts when archiving a print. Each archive is queried by ID and ordered the same way you sent the IDs in.

!!! note "What's NOT in the comparison"
    Some settings the upstream Bambuddy wiki advertised (infill density/pattern, print speed, chamber temp, retract distance, K factor, filament colour, plate count, parts count, file size/hash, predicted vs actual duration, energy consumed, error codes) are **not** part of the BamDude compare response — only the nine fields above. If you need a wider comparison, open the individual archives in side-by-side browser tabs, or query the slicer-settings JSON via `GET /api/v1/archives/{id}` directly.

## :material-alert-circle-outline: Difference highlighting

Each row in the response has a `has_difference` flag. The frontend renders rows with differences with a yellow tint and a small warning icon. A summary block under the table lists up to 5 differing fields explicitly:

> **Layer Height:** 0.16 vs 0.20 vs 0.20 mm
> **Filament Used:** 42 vs 48 vs 45 g
> ...and 2 more

`null` values render as `–` and don't count as a difference (only fields where at least two archives have non-null values that disagree are flagged).

## :material-chart-bell-curve: Success/failure correlation

When the selection contains **both** completed and failed archives, BamDude runs a small heuristic on top of the per-field comparison:

- For numeric fields (`layer_height`, temperatures, filament used, print time, total layers): it averages the value across successful prints and across failed prints separately. If the relative difference exceeds 10%, it emits an insight like *"Successful prints had higher Bed Temperature"*.
- For categorical fields (`filament_type`): if the set of values used in successful prints differs from the set used in failed prints, it emits *"Different Filament Type used in successful vs failed prints"*.

The block also shows the success/failure count from the selection (e.g. *3 successful, 2 failed*).

If the selection has only one outcome, the block is replaced by a hint:

> Need both successful and failed prints for correlation analysis.

!!! warning "Heuristic, not statistics"
    The 10% threshold is a rule-of-thumb, not a statistical test. With 5 archives the sample is too small for inferential conclusions — treat insights as hypotheses ("layer height looks correlated, let me run more prints to check"), not proof.

## :material-link-variant: Related features

- **Chain-of-custody** — when archives differ only because BamDude patched the gcode (e.g. mesh-mode toggle), they share the same `source_content_hash` and the duplicate badge tags them as related. See [Archiving](archiving.md).
- **Aggregate trends** — for "average values across hundreds of archives" rather than 2–5, use [Stats](stats.md).
- **Find similar archives** — `GET /api/v1/archives/{id}/similar` returns up to 10 archives that match by print name, file hash chain, or filament type. Use it to populate the compare modal with relevant siblings.

## :material-shield-key: Permissions

| Permission | Default groups |
|---|---|
| `archives:read` | Administrators, Operators, Viewers |

The compare endpoint is read-only; anyone who can read archives can compare them.

## :material-api: API reference

```
GET /api/v1/archives/compare?archive_ids=12,17,23
```

| Query param | Notes |
|---|---|
| `archive_ids` | Comma-separated list of 2–5 archive IDs. Order is preserved in the response. |

Response:

```json
{
  "archives": [
    {"id": 12, "print_name": "Benchy v1", "status": "completed", ...},
    ...
  ],
  "comparison": [
    {"field": "layer_height", "label": "Layer Height", "unit": "mm",
     "values": [0.20, 0.16, 0.20], "has_difference": true},
    ...
  ],
  "differences": [ ...subset of comparison where has_difference=true... ],
  "success_correlation": {
    "has_both_outcomes": true,
    "successful_count": 2,
    "failed_count": 1,
    "insights": [
      {"field": "bed_temperature", "label": "Bed Temperature",
       "success_avg": 60, "failed_avg": 55,
       "insight": "Successful prints had higher Bed Temperature"}
    ]
  }
}
```

When the selection is single-outcome, `success_correlation` collapses to:

```json
{"has_both_outcomes": false, "message": "Need both successful and failed prints to analyze correlation"}
```

There is no CSV export endpoint and no "show only differences" toggle — the `differences` array in the response already gives you the diff-only view, and the frontend uses it to populate the summary block.
