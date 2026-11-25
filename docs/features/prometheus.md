---
title: Prometheus Metrics
description: Export printer telemetry for Grafana dashboards
---

# Prometheus Metrics

BamDude can expose printer telemetry in Prometheus format for integration with **Grafana**, **Prometheus**, and other monitoring systems.

---

## :material-cog: Configuration

Navigate to **Settings > Network > Prometheus Metrics**.

| Setting | DB key | Description | Default |
|---------|--------|-------------|---------|
| **Enable Metrics** | `prometheus_enabled` | Toggle endpoint on/off | Off |
| **Bearer Token** | `prometheus_token` | Required Bearer-token auth on `/metrics` | Empty (must be set before enabling) |

!!! info "Authentication"
    Metrics use their own mandatory Bearer token, independent of application sign-in. Disabled returns 404; missing/wrong Bearer returns 401. An enabled legacy configuration with a blank token returns 503: save a token in Settings before scraping. The endpoint includes production and warehouse accounting; treat its token as installation-wide read access.

---

## :material-api: Endpoint

```
GET /api/v1/metrics
```

Returns metrics in [Prometheus text exposition format](https://prometheus.io/docs/instrumenting/exposition_formats/).

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://bamdude:8000/api/v1/metrics
```

---

## :material-chart-line: Available Metrics

Legacy per-printer telemetry carries `printer_id`, `printer_name` and `serial`; production gauges use stable IDs and the labels documented below.

### Build info

| Metric | Type | Description |
|--------|------|-------------|
| `bamdude_build_info` | gauge | `version`, `python_version`, `platform`, `architecture` (always = 1) |

### Per-printer state

| Metric | Type | Description |
|--------|------|-------------|
| `bamdude_printer_connected` | gauge | Connection status (1/0) |
| `bamdude_printer_state` | gauge | 0=unknown, 1=idle, 2=running, 3=pause, 4=finish, 5=failed, 6=prepare, 7=slicing |
| `bamdude_print_progress` | gauge | Current print progress (0-100) |
| `bamdude_print_remaining_seconds` | gauge | Estimated remaining time (seconds) |
| `bamdude_print_layer_current` | gauge | Current layer number |
| `bamdude_print_layer_total` | gauge | Total layers in current print |

### Temperatures + fans

| Metric | Type | Description |
|--------|------|-------------|
| `bamdude_bed_temp_celsius` | gauge | Current bed temperature |
| `bamdude_bed_target_celsius` | gauge | Target bed temperature |
| `bamdude_nozzle_temp_celsius` | gauge | Current nozzle temperature (label `nozzle="0"`/`"1"` for H2D dual-nozzle) |
| `bamdude_nozzle_target_celsius` | gauge | Target nozzle temperature |
| `bamdude_chamber_temp_celsius` | gauge | Chamber temperature (only emitted for models with the sensor) |
| `bamdude_fan_speed_percent` | gauge | Fan speed (label `fan="part"`/`"aux"`/`"chamber"`) |
| `bamdude_wifi_signal_dbm` | gauge | WiFi signal strength in dBm |

### Aggregate (DB-derived)

| Metric | Type | Description |
|--------|------|-------------|
| `bamdude_prints_total` | gauge | Current archive count, label `result="completed"`/`"failed"`/etc. |
| `bamdude_printer_prints_total` | gauge | Current archive count per printer |
| `bamdude_filament_used_grams` | gauge | Raw archive grams, including estimates |
| `bamdude_print_time_seconds` | gauge | Raw archive time, including estimates |
| `bamdude_queue_pending` | gauge | Number of pending queue items |
| `bamdude_queue_printing` | gauge | Number of currently printing queue items |
| `bamdude_printers_connected` | gauge | Connected printers right now |
| `bamdude_printers_total` | gauge | Configured printers right now |

---

## Production and warehouse snapshots

The same authenticated `/api/v1/metrics` endpoint also exports the following **gauges**. No read reserves stock, accepts output, books filament or repairs a queue. The source is BamDude's existing Workshop readers and spool ledger; there is no second accounting database.

| Metric | Meaning and labels |
|---|---|
| `bamdude_stock_full_spools`, `bamdude_stock_full_grams` | Unused, unassigned stock eligible for the existing automatic stock selector (not every shelf spool). Grams are label weights. |
| `bamdude_inventory_spools{scope}` | Active/all spool records. |
| `bamdude_inventory_remaining_grams`, `bamdude_inventory_low_stock_spools` | Same estimates and threshold rules as Inventory; remaining is clamped per active spool. |
| `bamdude_inventory_overdrawn_spools` | Active records whose lifetime use exceeds label weight; investigate, do not assume physically empty. |
| `bamdude_assigned_spool_balance_grams`, `bamdude_assigned_spool_archived` | Per `printer_id`, `ams_id`, `tray_id`; signed remaining estimate and archived-assignment warning. |
| `bamdude_accounted_filament_window_grams{printer_id,kind,window}` | Booked signed grams during rolling `24h`, `7d`, `30d`, by **ledger settlement time**. `kind=print` includes failed attempts and legacy print outcomes. `service_adjustment` covers runout and AMS corrections. The ledger's printer ID can outlive a deleted printer. Rows without an ID use `unassigned`. Active slicer estimates are excluded. |
| `bamdude_pending_jobs{tier}` | `auto` awaiting distribution and `printer` awaiting dispatch; promoted AutoQueue rows are counted only in the printer tier. |
| `bamdude_printer_maintenance`, `bamdude_printer_queue_paused`, `bamdude_printer_auto_distribute_eligible`, `bamdude_printer_awaiting_plate_clear` | Independent stored gates, keyed by `printer_id`, including printers in Maintenance Mode. Not physical proof. Missing queue headers omit queue flags. |
| `bamdude_printer_telemetry_timestamp_known`, `bamdude_printer_telemetry_age_seconds` | Whether a last locally received MQTT timestamp is known and its age. Unknown age is omitted. A recent message does not prove every individual field is fresh. |
| `bamdude_running_order_archives{printer_id,order_id,line_id}` | Count of archives recorded as printing, using real foreign keys; missing links are `unknown`. Not proof that the printer is physically printing. |
| `bamdude_active_orders`, `bamdude_order_details_available` | Active order count and whether all detail fits the bounded reader. |
| `bamdude_order_line_units{order_id,line_id,unit,quantity}` | `ordered`, `ui_printed`, `ui_covered`, `ui_remaining`, `from_finished_stock`, `from_part_kits`, `held`, `issued`. Units are `product_units` or `parts`; do not sum unlike units. UI coverage includes unchecked outcomes, reservations and recounts. Receipts/stock are not additional production. |
| `bamdude_order_line_jobs{order_id,line_id,stage}` | Canonically attributed `running` archives and `queued` jobs from both tiers. |
| `bamdude_order_part_pieces{order_id,line_id,part_id,quantity}` | `ui_usable`, `ui_remaining`, signed `recount_adjustment`, `allocated_stock`, `checked_net`, `unchecked_net`. The last two partition the same canonical part awards **before recounts**; neither is a stock receipt. No filename inference or independent reallocation of checked prints. |
| `bamdude_order_part_quality_known` | Whether part QC attribution is known; unknown checked/unchecked quantities are `NaN`, not zero. |
| `bamdude_order_quality_coverage_complete`, `bamdude_order_unchecked_archives`, `bamdude_order_unattributed_archives`, `bamdude_order_recorded_defective_pieces` | QC/history coverage, unchecked and unattributed archive counts, and recorded defective part rows including failed attempts. Missing completed part rows make the defect quantity `NaN`. |
| `bamdude_order_can_complete` | Existing Workshop completion rule, not an automatic confirmation. |
| `bamdude_production_snapshot_timestamp_seconds` | UTC collection time. Multiple SQL reads are not an immutable production snapshot. |

Order detail covers **active orders only**, with no customer names, filenames or archive IDs in labels. Before hydration the reader checks aggregate limits: 50 orders, 1,000 lines, 10,000 live archives and 100,000 archive-part rows. If exceeded, `order_details_available=0` and **all order detail is omitted**, not reported as zero or silently truncated. Global stock/queue metrics remain available. IDs are current database IDs, not identities portable across restores. Open `/projects/{order_id}` for names and details.

All new values are accounting snapshots, and spool balances remain estimates. Corrections, deletion, aging windows and resets can decrease them. **Do not apply `rate()` or `increase()`**. Historical series begin only when Prometheus actually scrapes the endpoint; enabling it alone does not configure a scrape job. Rolling totals use existing retained ledger rows and do not reconstruct missing past usage.

For example:

```promql
# Booked print grams in the preceding 24 hours, excluding service corrections
sum(bamdude_accounted_filament_window_grams{kind="print",window="24h"})
# Free full-stock kilograms
bamdude_stock_full_grams / 1000
# Waiting work, without counting the router and executor twice
sum(bamdude_pending_jobs)
# Remaining product units by active order (do not mix parts-line units)
sum by (order_id) (bamdude_order_line_units{quantity="ui_remaining",unit="product_units"})
```

---

## :material-tag-multiple: Labels reference

Most metrics carry one or more labels for filtering and grouping. The complete label set:

| Label | Description |
|---|---|
| `printer_id` | Numeric printer ID assigned at creation. |
| `printer_name` | Human-readable printer name from Settings. |
| `serial` | Printer serial number. |
| `model` | Printer model code (`X1C`, `X1E`, `H2D`, `P1S`, `A1`, `A1-Mini`, `P2S`, …). |
| `nozzle` | Nozzle index — `0` / `1` for H2D dual-nozzle, `0` for single-nozzle models. |
| `fan` | Fan slot — `part`, `aux`, `chamber`. |
| `result` | Archive state on snapshot gauges — `completed`, `failed`, `cancelled`, `archived`. |

---

## :material-prometheus: Prometheus scrape configuration

Add BamDude to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'bamdude'
    scrape_interval: 15s
    metrics_path: '/api/v1/metrics'
    static_configs:
      - targets: ['bamdude-host:8000']
    authorization:
      type: Bearer
      credentials_file: '/etc/prometheus/bamdude.token'
```

Put the same token you saved in BamDude in that file, readable by Prometheus.

When Prometheus runs in a sibling Docker container next to BamDude, use `host.docker.internal` (Docker Desktop) or the BamDude container name on a shared network:

```yaml
static_configs:
  - targets: ['host.docker.internal:8000']
```

```yaml
# On a shared user-defined bridge network:
static_configs:
  - targets: ['bamdude:8000']
```

A 15-30 second scrape interval is plenty for printer telemetry — temperatures and progress don't change faster than that in any meaningful way.

---

## :material-chart-bar: Grafana queries (PromQL)

Select the Prometheus data source that scrapes BamDude when creating a Grafana panel.

**Printer temperatures** — pick a specific printer or graph all of them:

```promql
bamdude_nozzle_temp_celsius{printer_name="X1C-1", nozzle="0"}
bamdude_bed_temp_celsius{printer_name="X1C-1"}
```

**Live print progress** across the fleet:

```promql
bamdude_print_progress
```

**Booked print grams in the preceding day** (rolling gauge; not a rate):

```promql
sum(bamdude_accounted_filament_window_grams{kind="print",window="24h"})
```

**Waiting work across both tiers**:

```promql
sum(bamdude_pending_jobs)
```

### Sample dashboard panels

A solid starter dashboard:

| Panel | Type | Query |
|---|---|---|
| Printers online | Stat | `bamdude_printers_connected` |
| Print progress per printer | Gauge | `bamdude_print_progress` |
| Bed / nozzle / chamber temperatures | Time series | `bamdude_bed_temp_celsius`, `bamdude_nozzle_temp_celsius`, `bamdude_chamber_temp_celsius` |
| Booked print grams (24h) | Time series | `sum(bamdude_accounted_filament_window_grams{kind="print",window="24h"})` |
| Queue depth | Bar chart | `sum(bamdude_pending_jobs)` |
| Prints by result | Bar chart | `bamdude_prints_total` |
| WiFi signal | Time series | `bamdude_wifi_signal_dbm` |

---

## :material-file-document: Sample `/metrics` output

```
# HELP bamdude_build_info BamDude build information
# TYPE bamdude_build_info gauge
bamdude_build_info{version="0.4.2",python_version="3.11.7",platform="Linux",architecture="x86_64"} 1

# HELP bamdude_printer_connected Printer connection status (1=connected, 0=disconnected)
# TYPE bamdude_printer_connected gauge
bamdude_printer_connected{printer_id="1",printer_name="X1C-1",serial="00M09C411500579",model="X1C"} 1

# HELP bamdude_printer_state Printer state
# TYPE bamdude_printer_state gauge
bamdude_printer_state{printer_id="1",printer_name="X1C-1",serial="00M09C411500579"} 2

# HELP bamdude_bed_temp_celsius Current bed temperature
# TYPE bamdude_bed_temp_celsius gauge
bamdude_bed_temp_celsius{printer_id="1",printer_name="X1C-1",serial="00M09C411500579"} 60.0

# HELP bamdude_nozzle_temp_celsius Current nozzle temperature
# TYPE bamdude_nozzle_temp_celsius gauge
bamdude_nozzle_temp_celsius{printer_id="1",printer_name="X1C-1",serial="00M09C411500579",nozzle="0"} 220.0

# HELP bamdude_prints_total Total number of prints by result
# TYPE bamdude_prints_total gauge
bamdude_prints_total{result="completed"} 342
bamdude_prints_total{result="failed"} 18

# HELP bamdude_filament_used_grams Total filament used in grams
# TYPE bamdude_filament_used_grams gauge
bamdude_filament_used_grams 2042.0

# HELP bamdude_accounted_filament_window_grams Signed booked spool-ledger grams by settlement time in a rolling window; gauge, do not rate or increase
# TYPE bamdude_accounted_filament_window_grams gauge
bamdude_accounted_filament_window_grams{printer_id="1",kind="print",window="24h"} 175.0
bamdude_accounted_filament_window_grams{printer_id="1",kind="service_adjustment",window="24h"} -15.0

# HELP bamdude_printers_connected Number of connected printers
# TYPE bamdude_printers_connected gauge
bamdude_printers_connected 2
```

---

## :material-help-circle: Troubleshooting

### `/metrics` returns 404

Prometheus metrics are disabled. Enable them in **Settings → Network → Prometheus Metrics**, then retry.

### `/metrics` returns 401

A bearer token is configured but the request didn't carry it (or carried the wrong one). Confirm `Authorization: Bearer <token>` matches the token in Settings exactly — copy/paste mistakes are the usual culprit.

### `/metrics` returns 503 with an empty token

Save a Prometheus token in BamDude and use it in the scrape configuration.

### Missing production detail

Check `bamdude_order_details_available` and the QC coverage gauges. Unknown or bounded-out detail is not zero production. Stock/queue aggregates do not require an MQTT push; telemetry needs a locally observed message. A failed HTTP scrape must be diagnosed rather than treated as an empty farm.
