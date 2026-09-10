---
title: Keeping the breaker and the power bill in check
description: Staggered starts against the peak, smart-plug auto-off against the idle draw, and a kWh figure on every print so the cost is known rather than guessed
---

# Keeping the breaker and the power bill in check

## :material-map-marker-question: The situation

Forty-eight printers draw a lot of electricity, in two very different ways. At the **start** of a print the bed heaters spike — a dozen beds climbing at once trips a breaker. At the **end** of a print nothing happens at all: the part cools, the printer sits powered with its screen on and its fans idling, and forty-eight of those add up to a heater's worth of nothing all night.

The bill arrives once a month with one number on it, and nobody can say what a lamp costs to print.

## :material-flag-checkered: The goal

Three things at once: no breaker trips on a plate-change round, no printer idling powered through the night, and a **kWh and a cost on every print** — so the order page's *Cost* is a measurement, not a guess.

## :material-puzzle: What is involved

| Feature | Its part |
|---|---|
| [Staggered start](../features/staggered-start.md) | Caps how many beds heat at once — the peak. |
| [Smart plugs → Automation](../features/smart-plugs.md#automation) | **Auto Power Off** after a print and cooldown; **Auto Power On** for the next queued print — the idle draw. |
| [Per-print energy](../features/smart-plugs.md#per-print-energy-tracking) and [Energy tracking](../features/energy.md) | The plug's meter read at print start and print end; the delta is the print's kWh, and × your rate is its cost. |
| [Stats → Energy](../features/stats.md) | Lifetime and per-printer totals; the `print` / `total` switch. |

## :material-format-list-numbered: Step by step

1. **A plug per printer, with a meter.** Any of the supported plug types that reports energy — Tasmota, Zigbee, Home Assistant, MQTT, a REST plug with an energy URL. Link each plug to its printer and leave **This plug powers the printer** on; turn it *off* on accessory plugs (a filter, a dryer, the lights), otherwise switching the filter off would mark the printer offline.

2. **Cap the peak.** **Settings → Printing → Queue & Scheduling → Staggered Start**: enable, **Concurrent starts** to what the circuit takes, **Wait for bed to heat** on. On a three-phase feed split it per phase — the whole recipe is [Three phases, one bed heating per phase](three-phases.md).

3. **Cut the idle.** On each plug card: **Auto Power Off** with the cooldown threshold (default **50 °C** bed) and a delay; **Auto Power On** so a queued print can wake the printer. Leave **Keep enabled** on the plug that runs the chamber heater or the room's HVAC — that one must not cycle.

4. **Put a price on a kWh.** **Settings → System → Energy**: your rate per kWh. It is a plain multiplier — enter it in the currency you pay in.

5. **Choose what "energy" means.** **Settings → System → Energy display mode**: `print` sums the per-print deltas — *what did the prints cost*; `total` reads the plug's lifetime counter — *what did the printer's socket consume*, idle included. The two diverge by exactly the idle draw you are trying to see.

6. **Read it back.** Every archive card now carries the print's kWh and cost; the order page sums them into *Cost* and, with a price on the order, *Margin*. **Stats → Energy** shows per-printer totals for a date range, so the machine that idles most is the one with the biggest gap between `total` and `print`.

## :material-cogs: What BamDude does on its own after that

- **At print start** the plug's meter reading is written onto the print's record. **At print end** the meter is read again — freshly, forcing a read on plugs that cache their values — and the difference is the print's kWh. A failed or cancelled print records what it burned up to the stop.
- **The baseline survives a restart.** The start reading lives on the print, not in memory; restart BamDude mid-print and the end still computes the right delta.
- **Auto-off waits for four things:** the bed below the threshold; the print not *paused* (resume or cancel it first); **no pending job in that printer's queue** — the next dispatch would only wake the plug again; and the plug not marked **Keep enabled**. From a *failed* or *cancelled* end it fires once the bed is cool, like from a completed one.
- **Auto-on** switches the printer's power plug on when a queued print — including a scheduled one, at its time — needs the printer, waits for it to come up, and dispatches. Accessory plugs are never used to wake a printer.
- **A switched-off plug reports 0 W.** Some cheap plugs keep reporting the last measured watts after the relay opens; BamDude does not pass that on. The lifetime counter is never zero-filled, so a plug that is off does not create a phantom consumption when it comes back.
- **Hourly snapshots** of every plug's counter feed the date-range totals, and a counter reset (firmware flash, power cut) is clamped to zero rather than showing as negative energy.

## :material-alert: Pitfalls and what-ifs

- **Stagger costs throughput on purpose.** It spreads *starts*; a running print is never slowed by a neighbour waiting for a slot. If the circuit takes simultaneous heating, do not stagger.
- **Auto-off will not fire while the queue has work** — that is a feature, not a fault: with the auto-queue feeding a printer all night, its plug stays on all night, and the idle saving comes from the printers that genuinely have nothing queued.
- **Print-hour maintenance intervals run on print time, not on plug time.** Cutting power does not reset anything there.
- **A plug without a meter** still switches, but leaves the print's kWh empty; the order's *Cost* then carries filament only for those prints.
- **The archive's kWh is the printer's kWh.** A plug that also feeds the chamber heater or the lights measures them too. Put accessories on their own plug if the per-print figure has to mean *the printer*.
- **`total` can be smaller than `print` after a reset.** A plug that lost its counter starts from zero; the per-print deltas from before are still on their prints. The date-range clamp keeps the total from going negative; it cannot invent the lost history.

## :material-link-variant: Related scenarios

- [Three phases, one bed heating per phase](three-phases.md) — the peak half of this scenario in full.
- [A night shift with nobody in the shop](unattended-night.md) — auto-off and the auto-queue on the same farm at the same time.
- [The customer asks when fifty will be ready](when-will-it-be-ready.md) — where the per-print cost ends up on the order.
