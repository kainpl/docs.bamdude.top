---
title: Export
description: Bulk export of archive metadata and statistics to CSV / Excel
---

# Export

Pull archive history and statistics out of BamDude as CSV or XLSX for Excel pivots, BI tools, customer billing, or tax reporting. The export is filter-aware — whatever you have selected in the UI is what you get in the file.

---

## :material-information: What It Is

Two endpoints, each backed by `ExportService` (`backend/app/services/export.py`):

| Endpoint | Returns |
|----------|---------|
| `GET /api/v1/archives/export` | One row per archive (the print log) |
| `GET /api/v1/archives/stats/export` | Failure-analysis summary + correlation breakdowns + weekly trend |

Both produce CSV by default and accept `?format=xlsx` for native Excel `.xlsx`.

!!! info "Permissions"
    - **Archive export** requires `archives:read`
    - **Stats export** requires `stats:read`

    Operators and Administrators have both by default; Viewers have read-only access to both.

---

## :material-filter: Filter-Aware Export

Whatever filter chips you have selected on the Archives page propagate into the export query. The same filters the UI uses — `printer_id`, `project_id`, `status`, `date_from`, `date_to`, `search` — are applied server-side before the export is generated.

| Filter | Effect on export |
|--------|------------------|
| Printer | Only that printer's archives |
| Project | Only that project |
| Status | Only that status (e.g. `success`, `failed`) |
| Date range | Inclusive `date_from` … `date_to` (ISO 8601) |
| Search | Matches `print_name`, `filename`, `tags`, `notes`, `designer` |

Two exclusions are always on: `status='archived'` (uploaded but never printed) and trashed archives (`deleted_at IS NOT NULL`). This keeps the export numerically consistent with what the [Statistics](stats.md) dashboard shows.

---

## :material-file-delimited: CSV Format

- **Encoding:** UTF-8
- **Separator:** comma (`,`)
- **Quoting:** Python `csv.writer` defaults — values containing commas, quotes, or newlines are double-quoted with `"`
- **Line ending:** platform default (`\r\n` on Windows, `\n` elsewhere)

!!! warning "Excel + CSV double-click"
    Excel sometimes mis-detects UTF-8 CSVs on double-click. If you see mojibake characters, import via **Data → From Text/CSV** and explicitly pick UTF-8.

---

## :material-microsoft-excel: Excel (.xlsx) Format

When you pick `format=xlsx`, BamDude generates a styled workbook via `openpyxl`:

| Feature | Detail |
|---------|--------|
| Header row | Bold white text, blue (`#4472C4`) fill, centred |
| Frozen header | Row 1 stays pinned when you scroll |
| Auto-width columns | Each column width = max content length (capped at 50 chars) |
| Sheet name | `Archives` for archive export, `Statistics` for stats export |

The stats workbook is a single sheet with Metric / Value pairs and a weekly-trend block at the bottom.

---

## :material-format-list-checkbox: Archive Columns

These are the default fields emitted for every archive row. You can narrow the set with the `fields` query parameter (`fields=id,print_name,energy_kwh,cost`).

| Field | Header | Description |
|-------|--------|-------------|
| `id` | ID | Archive primary key |
| `print_name` | Print Name | Display name (falls back to filename) |
| `filename` | Filename | Original 3MF filename |
| `status` | Status | `success` / `failed` / `aborted` / `cancelled` |
| `quantity` | Items Printed | How many copies on the plate |
| `printer_id` | Printer ID | FK to `printers.id` |
| `project_name` | Project | Joined from `projects.name` |
| `filament_type` | Filament Type | PLA, PETG, ABS, … |
| `filament_used_grams` | Filament (g) | Grams consumed (sum across spools) |
| `print_time_seconds` | Print Time (s) | Wall-clock duration |
| `layer_height` | Layer Height (mm) | Slicer setting |
| `nozzle_diameter` | Nozzle (mm) | Hardware setting |
| `bed_temperature` | Bed Temp (°C) | Slicer setting |
| `nozzle_temperature` | Nozzle Temp (°C) | Slicer setting |
| `total_layers` | Total Layers | Slicer metadata |
| `cost` | Cost | Filament + energy combined cost |
| `designer` | Designer | From 3MF metadata or manual edit |
| `tags` | Tags | Comma-separated tags string |
| `notes` | Notes | Free-text notes added to the archive |
| `failure_reason` | Failure Reason | Set on `failed` / `aborted` archives |
| `started_at` | Started At | ISO 8601 UTC |
| `completed_at` | Completed At | ISO 8601 UTC |
| `created_at` | Created At | ISO 8601 UTC |

!!! info "Energy columns"
    `energy_kwh` and `energy_cost` aren't in the default `fields` set — pass them explicitly via `?fields=...` if you need them in the same export. They're populated only for archives whose printer has a [smart plug](smart-plugs.md) with kWh metering.

---

## :material-chart-bar: Stats Export Layout

`GET /api/v1/archives/stats/export?days=30` produces:

```
Metric                 | Value
Period (days)          | 30
Total Prints           | 412
Failed Prints          | 27
Failure Rate (%)       | 6.6

Failures by Reason
Adhesion failure       | 8
Layer shift            | 5
…

Failures by Filament
ABS                    | 11
PETG                   | 9
…

Failures by Printer
Garage A1              | 18
Office P1S             | 7
…

Weekly Trend
Week        | Total | Failed | Rate (%)
2026-04-06  | 92    | 5      | 5.4
2026-04-13  | 89    | 8      | 9.0
…
```

The same data drives the [Failure Analysis](failure-analysis.md) dashboard.

---

## :material-api: API Reference

### Archive export

```
GET /api/v1/archives/export
```

| Query param | Type | Default | Notes |
|-------------|------|---------|-------|
| `format` | `csv` \| `xlsx` | `csv` | |
| `fields` | comma-list | all defaults | E.g. `id,print_name,energy_kwh` |
| `printer_id` | int | — | Filter by printer |
| `project_id` | int | — | Filter by project |
| `status` | string | — | Exact status match |
| `date_from` | ISO datetime | — | Inclusive |
| `date_to` | ISO datetime | — | Inclusive |
| `search` | string | — | LIKE match across name / filename / tags / notes / designer |

Auth: `archives:read` permission. Send your JWT in `Authorization: Bearer …` or your API key in `X-API-Key`.

### Stats export

```
GET /api/v1/archives/stats/export
```

| Query param | Type | Default | Notes |
|-------------|------|---------|-------|
| `format` | `csv` \| `xlsx` | `csv` | |
| `days` | int | `30` | Lookback window in days |
| `printer_id` | int | — | Filter by printer |
| `project_id` | int | — | Filter by project |

Auth: `stats:read` permission.

### Example

```bash
# Last quarter's failed prints, as Excel
curl -H "X-API-Key: bb_..." \
  "https://bamdude.local/api/v1/archives/export?format=xlsx&status=failed&date_from=2026-02-01&date_to=2026-04-30" \
  -o failed_q1.xlsx
```

---

## :material-clock-time-eight: Recurring / Scheduled Exports

BamDude does not run an internal cron for exports — keep the API key flow simple and use whatever scheduler your environment already has:

=== "Linux / cron"

    ```bash
    # Weekly snapshot every Sunday 00:00
    0 0 * * 0 curl -H "X-API-Key: $BAMDUDE_KEY" \
      "http://localhost:8000/api/v1/archives/export?format=csv" \
      -o "/backup/archives_$(date +\%Y\%m\%d).csv"
    ```

=== "systemd timer"

    Pair an `OnCalendar=Sun *-*-* 00:00:00` timer with a service unit that runs the same `curl`.

=== "Home Assistant"

    Use a `rest_command:` + `automation:` pair. HA can drop the file into a samba share or attach it to an email-notification service.

=== "GitHub Actions / GitLab CI"

    Schedule a workflow / pipeline that hits the export endpoint and uploads the artifact. Store `BAMDUDE_KEY` as a CI secret.

---

## :material-script-text-outline: Use Cases

- **Customer billing** — filter by date + project, export, hand to your invoicing tool. The combination of filament weight, cost, and energy gives a defensible per-job total.
- **Tax / accounting** — quarterly export filtered by date range; the `cost` column already sums filament + energy.
- **QA log** — `status=failed` + `date_from=YYYY-MM-01` is the failure log you hand a vendor when warranty-claiming a printer.
- **Capacity planning** — six months of `print_time_seconds` per printer tells you which machine is the bottleneck.

---

## :material-link: Related

- [Statistics](stats.md) — visual analytics for the same data
- [Failure Analysis](failure-analysis.md) — the source of stats-export numbers
- [Archiving](archiving.md) — filter chips reused for export scope; the underlying `print_archives` table
- [Energy Tracking](energy.md) — `energy_kwh` / `energy_cost` columns
- [Authentication → API Keys](authentication.md) — bearer / `X-API-Key` headers for scripted exports

---

## :material-lightbulb: Tips

!!! tip "Filter first, export second"
    The export honours the current filter chips. Setting them in the UI first is faster than building the query string by hand.

!!! tip "Pin a filename pattern"
    Include the date in the saved filename (`archives_20260504.csv`) so you can diff month-over-month and spot regressions.

!!! tip "XLSX for stakeholders, CSV for pipelines"
    XLSX has the bold header / frozen pane / autosize that humans expect; CSV is the format your scripts and pandas pipelines actually want.

!!! tip "Use API keys, not personal JWTs, for cron"
    A JWT expires in an hour. An [API key](authentication.md) doesn't — that's exactly what you want for an unattended scheduled export.
