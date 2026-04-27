---
title: Staggered Start
description: Roll out batch prints in groups to avoid power spikes
---

# Staggered Start

When sending prints to multiple printers simultaneously, staggered start prevents power spikes from concurrent bed heating by rolling out starts in configurable groups.

---

## :material-timer-sand: Why Stagger?

Starting 10+ printers at the same time can cause significant power draw as all beds heat simultaneously. Staggered start distributes the load by starting printers in groups with intervals between them.

---

## :material-cog: How It Works

1. Select multiple printers in the **Print** or **Add to Queue** dialog
2. Enable **Stagger printer starts** (appears automatically with multiple printers)
3. Configure:

| Setting | Description | Default |
|---------|-------------|---------|
| **Group size** | How many printers start at once | 2 |
| **Interval** | Minutes between each group starting | 5 min |

4. A preview shows the schedule, e.g., "6 printers -> 3 groups of 2, starting every 5 min (total: 10 min)"

---

## :material-play-circle: Execution

- **First group** starts immediately (or at the scheduled time)
- **Subsequent groups** start at computed intervals
- The scheduler uses `scheduled_time` on queue items -- no special logic needed

### Example

With 6 printers, group size 2, interval 5 minutes:

| Time | Action |
|------|--------|
| 0 min | Printers A and B start |
| 5 min | Printers C and D start |
| 10 min | Printers E and F start |

---

## :material-tune: Default Settings

Configure default stagger values in **Settings > Queue > Staggered Start**. These can be overridden per batch in the Print or Schedule dialog.

---

## :material-shield-check: Stagger vs. dispatch parallelism

Stagger is a **soft** schedule layered on top of the queue — it spreads queue items across time by stamping `scheduled_time` on each one. It does **not** serialize the dispatcher.

BamDude's dispatcher itself runs **in parallel across printers** since `c485db1` (mid-0.4.1 reverted the brief "always-serialised" gate). The only thing serialised is the millisecond-long `INSERT INTO print_archives` write, which sits behind a startup-lock so SQLite doesn't trip on concurrent writers. FTP upload, the `start_print` MQTT command, and swap-mode macros all run concurrently. See [Print queue → Dispatch behaviour](print-queue.md#dispatch-behaviour) for the full breakdown.

What this means for stagger:

- **Stagger is what spreads the bed-heating load** across time. Without stagger, three queued items on three idle printers will all start essentially simultaneously and you'll get three beds heating at once.
- **You don't need stagger to avoid SQLite write races** — the startup-lock already handles that, regardless of stagger setting.
- **`stagger_wait_for_bed=true`** (the default) holds the next slot open until the previous print's bed reaches target temp ±1 °C, which is what most operators actually want. With it off, a slot frees the moment the print starts (so the *next* heat-up begins while the previous bed is still climbing).

Use stagger when peak power draw during heating is the constraint. Skip it when your circuit can handle simultaneous bed heating.

---

## :material-monitor-dashboard: Bed Temperature Monitoring

BamDude monitors bed temperatures across all printers. Combined with staggered start, this helps:

- **Avoid circuit overloads** from simultaneous heating
- **Spread power draw** across time
- **Monitor heat-up times** per printer

---

## :material-lightbulb: Tips

!!! tip "Power Management"
    Combine staggered starts with smart plug auto-off for full power management: stagger prevents peak draw at start, auto-off cuts idle power at finish.

!!! tip "Interval Tuning"
    Set the interval to the time your printers take to reach bed temperature (usually 2-5 minutes). This ensures each group has finished heating before the next starts.

!!! tip "Per-Printer Intervals"
    For mixed farms with different printer models, use a longer interval to account for the slowest heater.
