---
title: Environment Sensors
description: Zigbee temperature and humidity sensors — live readings, history charts, and alerts when a room leaves its limits
---

# Environment Sensors

Pair a Zigbee temperature/humidity sensor and BamDude reads the room your printers stand in: current values wherever you are in the app, a chart of the last week, and a message when it leaves the limits you set.

Sensors use the **same radio as Zigbee smart plugs** — one dongle drives both. If you have not set the radio up yet, do that first on the [Smart Plugs](smart-plugs.md) page; everything below assumes the coordinator is connected.

---

## :material-thermometer: What it is for

Filament cares about humidity. ABS cares about draughts. A print that warps at 3 a.m. and a print that warps at noon usually differ by something nobody was in the room to see.

BamDude does not act on these readings — it does not switch anything on or off because a room got warm. It records them and tells you.

---

## :material-plus-circle: Adding a sensor

1. **Settings → Smart plugs → Zigbee** — press **Pair** and put the sensor in pairing mode (usually a long press on its button).
2. When it appears in the paired list, press **Add as sensor**.
3. Give it a name and a **location**. The location is what makes readings show up beside your printers — see [below](#where-readings-appear).

Removing a sensor from the list is **not** the same as removing it from the network: it stays paired and keeps its settings, so adding it back restores what it had.

!!! tip "Which sensors work"
    Any Zigbee sensor that reports through the standard temperature (`0x0402`), humidity (`0x0405`), CO₂ (`0x040D`) or PM2.5 (`0x042A`) clusters. Tested against the SONOFF SNZB-02DR2. A sensor that reports a quantity BamDude does not yet know is not broken — it simply shows the quantities it does know.

---

## :material-eye: Where readings appear

| Where | What you see |
|---|---|
| **Sidebar**, next to the smart-switches button | Every sensor, its place, and what it reads right now. Available on any page. |
| **Printers page**, grouped by location | The readings for that place, in the group heading itself |
| **Settings → Smart plugs → Sensors** | The full card: every quantity, when it last reported, battery, and the buttons for charts and limits |

A sensor covers **the place it stands in and everything inside it**. One sensor on a workshop reads out above every shelf in that workshop — you do not need one per shelf. Where two sensors apply to the same group, both are shown, nearest first.

---

## :material-chart-line: History

Every reading is recorded. Press the chart button on a sensor — in the sidebar, in a group heading, or on its card — for the last 6 hours, day, two days or week, one quantity at a time.

Readings are grouped into short intervals so a week is a chart your browser can draw rather than tens of thousands of points, and the tooltip says how long each point covers. The lowest and highest the sensor actually reached are shown beside the chart, where the grouping cannot hide them.

How long history is kept is set in **Settings → Data Management → Retention**, alongside the other measurement histories.

---

## :material-bell-ring: Alerts

Press the bell on a sensor's card in **Settings → Smart plugs → Sensors**.

Each quantity gets a row: a lowest value, a highest value, or both. Leave a field empty for no limit — "not above 30" and "not below 20" are separate worries and a sensor may have only one of them.

### The margin

The third field. A reading hovering on the line would otherwise ring, clear, and ring again; the margin is how far back **inside** the limit the value must come before the alarm clears.

With a maximum of `30` and a margin of `1`:

```
32 ──────────╱╲──────────────────
30 ──────╱──────╲─────────── limit
29 ────╱────────╲───────── clears
       ↑ alarm       ↑ all-clear
```

A value bouncing between 29.5 and 30.5 stays silent after the first alarm. The margin applies **only on the way out** — 30.1 alarms immediately, because a limit of 30 means 30.

### Battery

Battery is in the list too. It is the one limit worth setting even if you never set another: a flat cell is what makes a sensor stop reporting, and a warning at 20 % arrives days before the silence.

### When a sensor goes quiet

Reported separately, and it matters more than it sounds. Every other alert depends on readings arriving — without this one, a dead sensor and a perfectly comfortable room look exactly the same.

A sensor is considered silent when it has not reported for longer than its own expected interval allows. You are told again when it starts speaking.

!!! note "After a restart"
    BamDude does not announce silence for sensors it has simply not heard from yet — it waits until it has been running longer than the window it is judging. Restarting does not produce a burst of false alarms.

---

## :material-send: Where alerts go

Alerts travel the same road as every other notification — see [Notifications](notifications.md).

Each provider has two switches under **Event Settings**:

| Switch | Covers |
|---|---|
| **Sensor readings** | A reading left its limits, and when it came back |
| **Sensor went silent** | A sensor stopped reporting, and when it started again |

The pair is deliberate. Being told a room got hot and never told it cooled down is worse than not being told at all, so the alarm and its all-clear are one switch. What people do separate is *the room* from *the device*, which is why there are two.

Both are **off by default** — nothing starts talking to you because you upgraded.

**Telegram** is finer-grained, as everywhere: the switches live per chat, and there each of the five messages (above the limit, below it, back in range, silent, reporting again) can be chosen on its own.

**Quiet hours apply** exactly as they do to every other notification.

---

## :material-tune: Reporting settings

The gear on a sensor's card opens the same dialog smart plugs use: how often the device should report each quantity, and how much a value must change before it is worth sending.

Battery sensors sleep. Saving new settings does not wait for one to wake — the dialog says *accepted*, *confirmed*, *refused*, or *asleep and not yet asked*, so a setting still on its way is visibly still on its way rather than silently pending.

---

## :material-help-circle: Troubleshooting

| What you see | What it means |
|---|---|
| **Not on the network** | The device is not on the mesh at all — a flat cell, out of range, or the radio is down. Its name, place and settings are kept. |
| **Not answering** | On the mesh, but silent past the point where BamDude still vouches for the value |
| A **dimmed** value | That one quantity is older than its own interval. Normal for battery, which reports every few hours. |
| No readings anywhere, all sensors at once | The radio. The sidebar and the sensors section both carry a status dot for it. |
| Readings but no alerts | Check the two provider switches above — both are off until you turn them on |
