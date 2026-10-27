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

When a print starts, the lifetime counter is captured on the archive row as `energy_start_kwh`. When the print finishes, BamDude reads the counter again and stores the delta as `energy_kwh`. The starting value lives **on the archive row, not in memory** — so a backend restart mid-print does not lose the baseline, and the delta is still computed when the print completes. (If the print *ends* during the outage, see "If the print ends while BamDude is down" below.)

!!! warning "Figures recorded before 0.5.3 understate prints started outside BamDude"
    "At print start" has always been the intent, and for prints BamDude dispatched itself it was also the fact. For a print started from the printer's screen or sent straight from a slicer, the baseline used to be read once the archive row existed — and that row was only created after BamDude had fetched the print's 3MF back off the printer, which on a P1S measured 8m40s. Everything the printer drew in the meantime, bed heating included, was left out. The error was always in the same direction, so it never averaged out. Historical rows are not recalculated; there is nothing to recalculate them from.

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

**If the print ends while BamDude is down**, there is no `on_print_complete` to run: the printer finishes alone and BamDude only learns about it on the next start. The startup sweep closes that print and reads the counter then, so the archive still gets a figure — but the meter kept counting through however long the printer sat idle in between, so that idle draw is inside the number. Such archives carry `extra_data.energy_is_approximate = true`, and the log line says `(approximate — recovered print)`. The alternative was leaving the field empty, which reads as "this print used no power" — further from the truth than a modest over-count.

**Failed and cancelled prints still record energy.** A 6-hour print that fails at hour 4 still consumed 4 hours of electricity — the delta is still meaningful and is still written.

---

## :material-alert-decagram: When a Plug's Counter Stops

Some plugs keep reporting their watts while their lifetime energy counter stands still. Every print on such a plug used to read **0 kWh** — a frozen counter makes the start and end readings equal. BamDude now compares the counter with the plug's own power history.

**What counts as a suspected stall.** The counter held one value for at least **30 minutes** while the power history of the same plug covers that stretch (at least 95 %) and adds up to at least the plug's **missed-energy threshold** — 100 Wh unless you raise it on the plug. It is a suspicion, not a verdict about the device: a counter that only moves in coarse steps, or a stale cache, looks the same from here. A short or light print whose counter did not step (3 minutes at 120 W is 6 Wh) is not a stall and keeps its measured zero.

**What you see.**

- The plug's card says the counter is suspected stalled, since when, and roughly how much energy the history shows it missed — whether or not anyone subscribed to the warning.
- One **in-app** warning (*Plug energy counter stalled*, group *Sensors*) per episode — not per print or per check. External channels (Telegram, email, …) are not offered for it.
- The episode closes when the counter moves up again. A drop is a counter reset: a new baseline, never a recovery. Changing what the plug measures closes it as *source changed*, not as repaired.

**What happens to a print's energy.**

| Archive shows | When | `energy_kwh` |
|---------------|------|--------------|
| `≈ $0.04`, tooltip *estimated from the plug's power history* with the coverage | The print's measured window meets a suspected stall and the power history covers it well | The whole window integrated **once** from the power history — never the counter's part plus an integral on top |
| *Energy unknown* with the reason | The history does not cover the window, the end of the print was not observed (a print closed after a restart), the plug was reconfigured during the print, the server clock went back before the plug's measurement began, or there was too much history to evaluate | empty — **not** zero |
| the figure as before | The counter moved normally | the counter's difference, as always |

Estimated and unknown prints are counted where print energy is shown: the Statistics page says how many prints are estimated from the power history and how many have no reliable figure (and are not counted as zero), and an order's cost line marks its electricity *≈* when it contains estimates. The plug totals, *Energy At The Plug* and date-range totals never contain an estimate — they are what the counters said. Archives recorded before this version are not recalculated. Once BamDude has written a print's energy — measured, estimated or unknown — that figure is final: a later callback reads a later counter (idle draw, the next job) and never replaces it, and a figure you reconstructed yourself is kept as it is.

**Measurement source.** When you change what a plug measures — its address, entity, topic, JSON path, multiplier, Zigbee device, printer, or the phantom-watts setting below — BamDude starts a new measurement source. Readings and counter snapshots from before the change never feed an estimate made after it; a print that spans the change gets *Energy unknown — source changed*. Renaming a plug changes nothing.

**What the power history must look like.** Readings further apart than the plug's gap limit are a gap, never a straight line between them: 3 minutes for Zigbee, three sampling intervals (at least 3 minutes) for Tasmota, REST and Home Assistant, and three publish intervals (at least 3 minutes) for MQTT — set the plug's *publish interval* if it is not Tasmota's default 300 s. A reading BamDude received but cannot trust stays in the history as a hole: a value that is no number, a burst it could not store, a database write whose outcome is unknown, and — on a plug that may keep repeating old watts after its relay opens (Zigbee by default) — any reading while the relay state is unknown. A known *off* is 0 W on every plug. The power chart shows these holes as gaps.

**Plug settings** (*Settings → Smart plugs → Edit → Energy counter watch*):

| Setting | Default | Meaning |
|---------|---------|---------|
| Missed energy before a stall is suspected | 100 Wh | Raise it for a plug whose counter moves in coarse steps; it cannot go below 100 Wh |
| How often the plug publishes its power (MQTT only) | 300 s | Sets the MQTT gap limit (three intervals, at least 3 minutes) |
| Watts after the relay opens | the type's default | *May keep repeating old watts* makes readings with an unknown relay state unusable (the Zigbee default); *Reports what it measures* trusts them |

!!! warning "Restarting a hung plug"
    BamDude never sends a command because of a suspected stall. If the device has hung, **wait until prints on it have finished**, then unplug it from the mains and plug it back in — the relay button does not restart its electronics. Never cut a printer's power in the middle of a print.

Detection runs at most every five minutes, and only when a new counter reading has arrived — usually the next hourly snapshot or the end of a print, so it is not a promise to notice within half an hour. It reads the last day of history.

---

## :material-counter: Lifetime kWh and Date Ranges

The hourly snapshot loop (`SmartPlugManager._snapshot_loop`) records one row per plug into `smart_plug_energy_snapshots`. A snapshot is **also** written at the start of every print, from the same reading that seeds the archive's baseline — so a print's own start is a real boundary in the history rather than whichever hour the loop last happened to fire:

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

**Which day is "today".** Dates you pick, and "energy used today", are resolved in **your** timezone -- the browser tells BamDude which one you are in. Snapshots are stored in UTC, as above, and the day boundary is converted before the query. Work BamDude does on its own schedule -- nightly backups, digests -- keeps using the server's timezone, which is what those should follow. Callers that cannot send a timezone (the Telegram bot, API keys, webhooks) are answered in the server's.

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

**Settings → API Keys → Create**, and flip the **Update electricity price** toggle on the key's row. This is a narrowly-scoped opt-in for `POST /settings/electricity-price` — it does **not** grant general settings-write capability (the wider `PATCH /settings` route is unchanged). Copy the key.

!!! note "Older docs referenced `PATCH /settings`"
    The general `PATCH /settings` endpoint still works for API keys, but it exposes the entire settings payload (SMTP / LDAP / MQTT credentials, HA token, every UI rendering knob) — a much wider surface than the dynamic-tariff use case needs. The new `POST /settings/electricity-price` endpoint accepts only `{energy_cost_per_kwh}`, returns the full settings response so HA can confirm the new value applied, and is gated by the per-key `Update electricity price` toggle so admins explicitly opt in. Configs pointing at the legacy URL keep working; switch to the narrow URL on your next config refresh.

### 2. Add a REST command in HA

Add to your `configuration.yaml`:

```yaml
rest_command:
  bamdude_electricity_price:
    url: "http://YOUR_BAMDUDE_IP:8000/api/v1/settings/electricity-price"
    method: POST
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

When some prints' energy is estimated from the power history, or unknown, the printing figures say how many — see [When a Plug's Counter Stops](#when-a-plugs-counter-stops).

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
