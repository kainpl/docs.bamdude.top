---
title: Energy Tracking
description: Per-print and lifetime electricity tracking via smart plugs
---

# Energy Tracking

Track electricity consumed by every print and across the whole lifetime of a printer, then multiply by your kWh rate to get cost. The numbers come straight from a smart plug's energy register — not from estimates.

---

## :material-information: What It Is

BamDude reads two values from each smart plug:

1. **Live wattage** — how many watts the printer is drawing right now.
2. **Lifetime energy counter** — total kWh the plug has measured since it was reset.

When a print starts, the lifetime counter is captured on the archive row as `energy_start_kwh`. When the print finishes, BamDude reads the counter again and stores the delta as `energy_kwh`. The starting value lives **on the archive row, not in memory** — so if the backend restarts mid-print, the per-print delta is still computed correctly at completion.

For lifetime / date-range views, an hourly background loop snapshots each plug's lifetime counter into `smart_plug_energy_snapshots`. Date-range totals are then computed as `last_snapshot_in_range − last_snapshot_before_range` per plug.

!!! info "Permission Required"
    Reading energy data requires `stats:read`. Tracking starts automatically once a smart plug is bound to a printer — there is no separate "enable energy tracking" toggle.

---

## :material-power-plug: Requirements

Energy tracking needs a smart plug with **kWh metering** wired between the wall outlet and the printer. The plug type, power monitoring details, and configuration steps are covered in [Smart Plugs](smart-plugs.md).

| Plug Type | kWh Metering | Notes |
|-----------|:------------:|-------|
| Tasmota | :material-check: | Native HTTP energy endpoint |
| Home Assistant | :material-check: | Bind a HA energy sensor entity |
| REST / Webhook | :material-check: | Configure JSON path to extract kWh |
| MQTT | :material-check: | Configure MQTT topic + JSON path |

Plugs without an energy register (basic on/off plugs) still work for power control, but their archive rows will have `NULL` `energy_kwh` and won't contribute to lifetime totals.

---

## :material-meter-electric: Per-Print kWh

Captured on `PrintArchive`:

| Column | Captured When | Meaning |
|--------|---------------|---------|
| `energy_start_kwh` | At print start | Plug's lifetime counter at the moment the print began |
| `energy_kwh` | At print complete | `(end_counter − energy_start_kwh)`, the kWh this single print consumed |
| `energy_cost` | At print complete | `energy_kwh × cost_per_kwh` (denominated in your configured currency) |

**Restart-resilient.** Because `energy_start_kwh` is persisted to the archive row inside the same transaction that records `started_at`, a backend crash or container restart mid-print does not lose the baseline — the next `on_print_complete` will compute the delta correctly.

**Failed and cancelled prints still record energy.** A 6-hour print that fails at hour 4 still consumed 4 hours of electricity — the delta is still meaningful and is still written.

---

## :material-counter: Lifetime kWh and Date Ranges

The hourly snapshot loop (`SmartPlugManager._snapshot_loop`) records one row per plug into `smart_plug_energy_snapshots`:

| Column | Meaning |
|--------|---------|
| `plug_id` | FK to the smart plug |
| `recorded_at` | UTC timestamp of the snapshot |
| `lifetime_kwh` | Plug's lifetime energy register at that moment |

For a date range `[date_from, date_to]`, BamDude computes per plug:

```
range_total = max(0, last_snapshot_in_range − last_snapshot_before_range)
```

The `max(0, …)` clamps to zero when the lifetime counter has been reset (e.g. after a plug factory-reset) so you never get negative energy.

---

## :material-cash: Cost Calculation

Cost is a single-rate calculation against the lifetime / per-print delta:

```
cost = energy_kwh × energy_cost_per_kwh
```

Configure the rate in **Settings → System → Energy**:

| Setting | Description |
|---------|-------------|
| `energy_cost_per_kwh` | Your electricity price per kWh (default `0.15`) |

The numeric rate is dimensionless — display the cost in whatever currency matches your real tariff. BamDude doesn't convert currencies; it just multiplies.

---

## :material-toggle-switch: Energy Tracking Mode

**Settings → System → Energy → Energy Tracking Mode** (`energy_tracking_mode`):

| Mode | What "Energy used" Means on Stats |
|------|----------------------------------|
| `print` | Sum of per-archive `energy_kwh` values over the date range. Excludes idle, standby, chamber-only heating. Pure printing cost. |
| `total` *(default)* | Lifetime plug counter via snapshot range — `last_in_range − baseline_before_range`. Includes idle / standby / chamber heating / firmware-update sessions / anything the printer drew while plugged in. |

Pick `print` if you bill customers per job. Pick `total` if you want to know what your printer farm actually costs to keep running.

---

## :material-clock-alert: "Warming-Up" Indicator

The `total` mode needs **at least one snapshot before the start of your selected range** to compute a baseline. On a fresh install, immediately after upgrading to a build that ships snapshot support, or right after `Last 7 days` is shifted into a window with no prior snapshot, that baseline doesn't exist yet.

When this happens, the Stats page shows a yellow warning icon next to **Energy Used** and **Energy Cost**:

> :material-alert-outline: *Still warming up — at least one plug doesn't have a snapshot from before the start of your range.*

The icon disappears as soon as enough snapshots exist. No configuration needed; the system is just collecting data. Backend flag: `energy_data_warming_up=True` on the stats response.

---

## :material-home-automation: Tibber / Octopus / Dynamic Tariff Integration

If you're on a dynamic electricity tariff (Tibber, Octopus, Nordpool, …), push the live rate into BamDude from Home Assistant — every cost calculation will then use the current rate instead of a static value.

### 1. Create an API key

**Settings → API Keys → Create** with `settings:write` permission. Copy the key.

### 2. Add a REST command in HA

Add to your `configuration.yaml`:

```yaml
rest_command:
  bamdude_electricity_price:
    url: "http://YOUR_BAMDUDE_IP:8000/api/v1/settings"
    method: PATCH
    headers:
      X-API-Key: "YOUR_API_KEY"
    content_type: "application/json"
    payload: '{"energy_cost_per_kwh": {{ states("sensor.electricity_price") }}}'
```

### 3. Trigger the REST command on price change

```yaml
automation:
  - id: bamdude_push_electricity_price
    alias: "Update BamDude electricity price"
    mode: restart
    trigger:
      - platform: state
        entity_id: sensor.electricity_price
        for: "00:00:05"
    condition:
      - condition: template
        value_template: >
          {{ states('sensor.electricity_price')|float(none) is not none }}
    action:
      - service: rest_command.bamdude_electricity_price
```

| Provider | Typical sensor entity |
|----------|-----------------------|
| Tibber | `sensor.tibber_prices` (current price attribute) |
| Octopus Energy | `sensor.octopus_energy_electricity_current_rate` |
| Nordpool | `sensor.nordpool_kwh_*` |

!!! tip "Verify the sensor returns a number"
    BamDude expects a numeric value for `energy_cost_per_kwh`. If your sensor returns a string with a currency symbol, adjust the template (`{{ states('sensor.x')|float }}`) before pushing.

For more on the Home Assistant integration architecture see [Smart Plugs → Home Assistant](smart-plugs.md).

---

## :material-chart-line: Stats-Page Widgets

The Statistics page surfaces energy in three places:

- **Energy used** (kWh) for the selected date range, respecting `energy_tracking_mode`
- **Energy cost** in your configured currency
- **Per-printer breakdown** so you can see which machine is drawing most

Charts and totals are kept in sync with the `print` vs `total` switch — toggling rebuilds them server-side. See [Statistics](stats.md) for the full widget tour.

---

## :material-link: Related

- [Smart Plugs](smart-plugs.md) — plug types, configuration, HA / Tasmota / REST / MQTT setup
- [Archiving](archiving.md) — `energy_kwh` / `energy_cost` fields on each archive row
- [Statistics](stats.md) — energy widget, cost charts, date-range filters
- [Print Queue](print-queue.md) — auto-power-off after print + smart-plug-driven queue automation
- [Export](export.md) — CSV/XLSX with per-print energy + cost columns

---

## :material-lightbulb: Tips

!!! tip "Use your real tariff"
    Pull the all-in rate from your last electricity bill (energy + delivery + taxes + fees). A "headline" rate from your supplier's website usually understates the true cost.

!!! tip "Failed prints still cost"
    `energy_kwh` is recorded for `failed` and `cancelled` archives too — that's another data point arguing for [Failure Analysis](failure-analysis.md) and [Obico](obico.md). Every fail is real money on the meter.

!!! tip "Snapshot baselines need uptime"
    The hourly snapshot loop only runs while BamDude is running. If you stop the container for two days and ask for a 7-day total, the missing 48h shows up as a flat baseline — the warming-up icon will surface this.

!!! tip "Print mode for invoicing, total mode for ROI"
    Switch to `print` mode when exporting customer invoices — they shouldn't pay for your standby. Switch to `total` mode when calculating whether the farm is paying for itself.
