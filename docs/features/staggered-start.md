---
title: Staggered Start
description: Cap how many printers heat at once — farm-wide, or per electrical phase and room
---

# Staggered Start

Staggered start is a **farm setting**, not a per-batch option. It caps how many printers may be heating their beds at the same time, so a plate change across the shop doesn't put every bed on the circuit at once. The cap can also be split **per group** — one cap per electrical phase, per room, or per phase-and-room pair.

---

## :material-timer-sand: Why stagger?

A bed heater is the biggest single load a printer draws, and it draws it at the start of the print. Clear ten plates in one round and the queue will happily start all ten within the same scheduler tick — which is exactly the moment a breaker trips.

Stagger answers one question: *how many beds may be climbing right now?* Everything else — plate-clear confirmation, drying, filament matching — stays where it was.

---

## :material-cog: How it works

Every print start takes a **slot**. While the configured number of slots is taken, the next print waits.

A slot is freed by one of two rules, depending on **Wait for bed to heat**:

- **On (default)** — the slot is held until that printer's bed reaches its target (within **±1 °C**), and then for the **interval** on top.
- **Off** — the slot frees the moment the print starts, and the interval counts from there.

Slots live **in memory**. A backend restart forgets them; a few seconds after MQTT reconnects, BamDude scans the farm and re-registers a slot for any printer it finds actively heating, so a restart mid-heat doesn't hand out a free pass. A print you start **on the printer's own screen** takes a slot too — BamDude registers one when it sees that print begin with the bed still below target. A printer already at temperature is skipped: its heating spike is behind it.

### Where it lives

**Settings → Printing → Queue & Scheduling → Staggered Start**

| Setting | Default | What it does |
|---------|---------|--------------|
| **Enable staggered start** | Off | Turns the cap on. Everything below is hidden while it's off. |
| **Concurrent starts** | 2 | How many printers may be heating at the same time. Relabels itself to **Concurrent starts per group** once a split is on. |
| **Interval (minutes)** | 5 | Wait after a slot frees before the next start is allowed. |
| **Wait for bed to heat** | On | Slot frees when the bed reaches target (±1 °C). Off → it frees right after the start. |
| **Strict mode for direct dispatch** | Off | See [Direct prints and strict mode](#direct-prints-and-strict-mode). |
| **Split by printer tags** | Off | Each chosen tag becomes its own cap. |
| **Split by location** | Off | Each chosen location becomes its own cap. |

### On the queue page

A **stagger banner** sits above the queue whenever stagger is enabled. It shows occupancy (`Stagger: 2/2 slots occupied`, or one `label: occupied/capacity` segment per group) and **next free in** with a countdown. Its tooltip lists every printer holding a slot, whether it is **heating bed** or in **grid recovery** (the interval wait), and how long until that slot frees.

A queue item held back by the cap shows its reason on the row:

```text
Staggered start: waiting for P1S-04 to heat up
Staggered start: waiting for interval
```

The item is **skipped for this tick**, not rescheduled — nothing is stamped on it, and it dispatches on the first tick that finds it a slot.

### Per-printer interval

The printer form has **Stagger interval (minutes)**, where **0 = use system default**. Set it on a slow-heating machine so its slot is held longer than the farm-wide value.

!!! tip "The interval is a recovery gap, not the heat-up time"
    With **Wait for bed to heat** on, the interval starts counting *after* the bed is up — the climb is already covered by the bed wait. Two to five minutes is usually plenty.

---

## :material-transmission-tower: Groups: phases and rooms

A farm on one 16 A circuit needs one number. A farm split across three phases needs three, and "two at once" farm-wide either under-uses two phases or overloads one. The split turns the single cap into **one cap per group**.

There are two axes, and they can be used together:

| Axis | How a printer joins a group | Where the group is named |
|------|-----------------------------|--------------------------|
| **Split by printer tags** | It carries that tag | **Settings → Printing → Tags**, picked on the printer form |
| **Split by location** | Its own location, or the nearest picked place **above** it in the location tree | **Settings → Printing → Locations**, picked on the printer form |

Turn an axis on and pick which tags (or which locations) are groups — an axis that is on but has nothing picked changes nothing. With **both** axes on, every **tag × location** pair is its own cap.

**Concurrent starts** then means *per group*, and the field relabels itself to say so. Two phases with a cap of 2 means up to four beds farm-wide — two on each — and never three on one phase.

The banner grows a segment per group, and a waiting item names the group it is waiting on:

```text
Staggered start [Phase 2]: waiting for P1S-04 to heat up
```

When both axes are on, the group's name joins them with a middle dot — `Phase 1 · Workshop 2`.

!!! warning "An untagged printer counts in every group"
    A printer carrying **none** of the picked tags (or with **no** picked location above it) is a **wildcard**: BamDude does not know which phase it is on, so it is treated as if it could be on any of them. It joins **every** group and starts only when **all** of them have room — and while it heats, it occupies a slot in every group at once.

    The practical consequence: **nothing changes until you have tagged your printers.** Turn the split on with an untagged farm and the cap gets stricter, not smarter. Tag every printer with its phase first, then turn the split on.

    The banner marks such a printer *no group, counts everywhere*.

A tag or a location that is currently picked as a stagger group **cannot be deleted** — the API answers `409` with *"This tag is a staggered-start group. Un-choose it under Queue & Scheduling first."* Removing it would silently redraw which printers share a cap, which is not something a delete button should do quietly. Un-pick it in Settings first, then delete.

---

## :material-play-circle: Direct prints and strict mode {#direct-prints-and-strict-mode}

**Print Now** and **Re-print** go through the same gate as the queue — the cap is about the electrical panel, and the panel does not care which button started the print.

| Strict mode for direct dispatch | Behaviour |
|---------------------------------|-----------|
| **Off** (default) | The direct print **waits** for a free slot in its group, exactly like a queued one, then uploads and starts. |
| **On** | The direct print is **refused** with a message while the printer's group has no free slot. Nothing is uploaded. |

Off is the right default for most farms: you pressed the button, you want the print, and waiting a couple of minutes is not a failure. Turn strict on when a person is standing at the machine and would rather be told *"not now"* than watch a dialog spin — or when an operator pressing Print Now repeatedly would otherwise line up a burst of delayed starts.

---

## :material-shield-check: Stagger vs. dispatch parallelism

Stagger gates the **start** of a print. It does not serialise the dispatcher.

BamDude's dispatcher runs **in parallel across printers** since `c485db1` (mid-0.4.1 reverted the brief "always-serialised" gate). The only serialised step is the millisecond-long `INSERT INTO print_archives` write, which sits behind a startup-lock so SQLite doesn't trip on concurrent writers. FTP upload, the `start_print` MQTT command, and swap-mode macros all run concurrently. See [Print queue → Dispatch behaviour](print-queue.md#dispatch-behaviour) for the full breakdown.

What this means:

- **Stagger is what spreads the bed-heating load** across time. Without it, three queued items on three idle printers all start essentially simultaneously and three beds heat at once.
- **You don't need stagger to avoid SQLite write races** — the startup-lock already handles that, regardless of the stagger setting.
- **Stagger costs throughput, deliberately.** Slots serialise starts and nothing else; a print already running is never slowed down by another printer waiting for a slot.

Use stagger when peak power draw during heating is the constraint. Skip it when your circuit can handle simultaneous bed heating.

---

## :material-lightbulb: Tips

!!! tip "Tag before you split"
    Tag **every** printer with its phase before turning **Split by printer tags** on — an untagged printer holds a slot on every phase at once, so a half-tagged farm staggers harder than an untagged one.

!!! tip "Power Management"
    Combine staggered starts with smart plug auto-off for full power management: stagger prevents peak draw at start, auto-off cuts idle power at finish.

!!! tip "Interval Tuning"
    Set the interval to the time your printers take to reach bed temperature (usually 2-5 minutes). This ensures each group has finished heating before the next starts.

!!! tip "Per-Printer Intervals"
    For mixed farms with different printer models, use a longer interval to account for the slowest heater — or set **Stagger interval (minutes)** on that one printer and leave the farm default alone.
