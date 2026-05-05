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
| **Bearer Token** | `prometheus_token` | Optional Bearer-token auth on `/metrics` | Empty (open) |

!!! info "Auth on /metrics"
    `/api/v1/metrics` ignores BamDude's normal auth stack -- it has its own gate. When `prometheus_enabled=false` it returns 404 (looks unconfigured). When enabled with no `prometheus_token`, it's open. When enabled with a token, callers must send `Authorization: Bearer <token>`. Set the token whenever Prometheus runs on a separate host you don't fully trust.

!!! warning "Open by default when token unset"
    With `prometheus_enabled=true` and `prometheus_token=""` the endpoint is **publicly accessible** -- anyone on the network who can reach port 8000 will get the full metrics dump (printer names, serials, queue depth, total filament burn). For any deployment that isn't a fully isolated home LAN, set `prometheus_token` and configure Prometheus to send it.

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

Each per-printer metric is labelled with `printer_id`, `printer_name`, and `serial`. Aggregate counters/gauges are unlabelled or labelled by `result` / `fan` / `nozzle` as appropriate.

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
| `bamdude_prints_total` | counter | Lifetime print count, label `result="completed"`/`"failed"`/etc. |
| `bamdude_printer_prints_total` | counter | Lifetime print count per printer |
| `bamdude_filament_used_grams` | counter | Total filament consumed |
| `bamdude_print_time_seconds` | counter | Total print time logged |
| `bamdude_queue_pending` | gauge | Number of pending queue items |
| `bamdude_queue_printing` | gauge | Number of currently printing queue items |
| `bamdude_printers_connected` | gauge | Connected printers right now |
| `bamdude_printers_total` | gauge | Configured printers right now |

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
| `result` | Print outcome on aggregate counters — `completed`, `failed`, `cancelled`, `archived`. |

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
    # If using bearer token auth:
    bearer_token: 'YOUR_TOKEN'
```

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

Add BamDude as a Prometheus data source in Grafana, then build panels with these queries:

**Printer temperatures** — pick a specific printer or graph all of them:

```promql
bamdude_nozzle_temp_celsius{printer_name="X1C-1", nozzle="0"}
bamdude_bed_temp_celsius{printer_name="X1C-1"}
```

**Live print progress** across the fleet:

```promql
bamdude_print_progress
```

**Success rate over the last day** (rate-of-change of completed vs all-results counters):

```promql
rate(bamdude_prints_total{result="completed"}[1d])
/
rate(bamdude_prints_total[1d])
```

**Filament burn rate** (grams per hour, last hour rolling):

```promql
rate(bamdude_filament_used_grams[1h]) * 3600
```

**Queue depth** at a glance:

```promql
bamdude_queue_pending + bamdude_queue_printing
```

### Sample dashboard panels

A solid starter dashboard:

| Panel | Type | Query |
|---|---|---|
| Printers online | Stat | `bamdude_printers_connected` |
| Print progress per printer | Gauge | `bamdude_print_progress` |
| Bed / nozzle / chamber temperatures | Time series | `bamdude_bed_temp_celsius`, `bamdude_nozzle_temp_celsius`, `bamdude_chamber_temp_celsius` |
| Success rate (24h) | Stat | (success-rate query above) |
| Filament burn rate | Time series | `rate(bamdude_filament_used_grams[1h]) * 3600` |
| Queue depth | Bar chart | `bamdude_queue_pending` + `bamdude_queue_printing` |
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
# TYPE bamdude_prints_total counter
bamdude_prints_total{result="completed"} 342
bamdude_prints_total{result="failed"} 18

# HELP bamdude_filament_used_grams Total filament used in grams
# TYPE bamdude_filament_used_grams counter
bamdude_filament_used_grams 2042.0

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

### Endpoint open and returns 200 but no metrics

If the body is empty or only contains `bamdude_build_info`, BamDude hasn't collected anything yet. Most metrics are populated lazily — they only show up after the first `push_status` from a printer (or first finished print, for aggregate counters). Wait a minute, or click **Connect** on a printer to force a status push.

### Prometheus dashboard says BamDude is "down"

- Verify network reachability — `curl http://bamdude-host:8000/api/v1/metrics` from the Prometheus container itself.
- Firewall might be blocking port 8000 between containers / hosts.
- Bearer token mismatch shows as `down` with a 401 in Prometheus's targets page.
- If using `host.docker.internal`, confirm Docker Desktop / Docker Engine actually exposes that hostname on your platform.

---

## :material-lightbulb: Tips

!!! tip "Scrape Interval"
    A 15-30 second scrape interval is sufficient for printer telemetry.

> Originally based on [Bambuddy](https://github.com/maziggy/bambuddy) documentation.
