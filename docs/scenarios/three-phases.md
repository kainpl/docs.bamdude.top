---
title: Three phases, one bed heating per phase
description: A farm on a three-phase supply names each printer's phase with a tag and lets the staggered start cap every phase on its own
---

# Three phases, one bed heating per phase

## :material-map-marker-question: The situation

Forty-eight printers on a three-phase supply, roughly sixteen per phase. A bed heater is the single biggest load a printer draws, and it draws it at the start of the print. When a shift ends the operator walks the shop and clears plates; the queue starts a dozen prints inside one scheduler tick, twelve beds climb at once, and the breaker on one of the phases goes.

A farm-wide cap of two starts stops the breaker and wastes two phases: "two beds anywhere" is one phase's worth of load, and the other two phases sit idle while the queue waits.

## :material-flag-checkered: The goal

On every phase, at most **one** bed climbing at a time — or two, whatever that circuit tolerates — and the three phases independent of each other. A plate-change round then runs three starts at once, one per phase, and the queue never needs to know which socket a printer is plugged into.

## :material-puzzle: What is involved

| Feature | Its part |
|---|---|
| [Printer tags](../features/monitoring.md) | Name the phase on each printer. A tag is a label with a colour; here it means *"this printer is on phase 2"*. |
| [Staggered start → Groups](../features/staggered-start.md#groups-phases-and-rooms) | Turns the one farm-wide cap into a cap per tag — and, if you want, per room as well. |
| [The stagger banner](../features/staggered-start.md#on-the-queue-page) | On the Queue page: occupancy per phase, and which printer a waiting item is waiting on. |

## :material-format-list-numbered: Step by step

1. **Name the phases.** **Settings → Printing → Tags**: create `Phase 1`, `Phase 2`, `Phase 3`. Give each a colour from the palette — the banner and the printer cards will wear it, which is how you tell at a glance which phase is full.

2. **Tag every printer.** Edit each printer and pick its phase tag in the field under the location. On the Printers page, group the cards by **Tag**: the section **No tag** at the bottom is your to-do list, and it has to be **empty** before the next step (see the first pitfall for why).

3. **Turn the split on.** **Settings → Printing → Queue & Scheduling → Staggered Start**:

    | Setting | Value for this farm |
    |---|---|
    | **Enable staggered start** | On |
    | **Concurrent starts** | `1` — the field relabels itself to **Concurrent starts per group** the moment a split is on, and that is what it now means |
    | **Interval (minutes)** | `3` — the recovery gap *after* a bed has reached temperature, not the heat-up time |
    | **Wait for bed to heat** | On |
    | **Split by printer tags** | On, and tick `Phase 1`, `Phase 2`, `Phase 3` |

4. **A weaker phase, optionally.** Beside each ticked tag there is a small number field. Leave it empty and the phase uses the number above; put `1` on the phase with the smaller breaker and `2` elsewhere and each phase runs on its own limit.

5. **Two workshops, optionally.** If two rooms have separate feeds, turn **Split by location** on as well and tick the two rooms. The groups become *phase × room* — `Phase 1 · Workshop 2` — and each pair has its own cap, the smallest of its tag limit, its location limit and the global number.

6. **Look at the Queue page.** The banner above the queues now has one segment per phase — `Phase 1: 1/1`, `Phase 2: 0/1`, `Phase 3: 1/1` — and *next free in* with a countdown. Clear plates exactly as before.

## :material-cogs: What BamDude does on its own after that

- **Every print start takes a slot in the printer's phase** — a queued job, **Print**, a re-print from the archive, and a print you start on the printer's own screen with a cold bed. Once a phase's slot is taken, the next item on *that* phase waits with the reason on its row:

    ```text
    Staggered start [Phase 2]: waiting for P1S-04 to heat up
    ```

    Items on the other two phases do not wait for it.

- **The slot is held until the bed is at target** (within ±1 °C), then for the interval on top, and only then does the next start on that phase go. A printer that is already at temperature when its print starts is skipped — its spike is behind it.

- **A direct print waits like a queued one.** Press **Print** on a phase that is full and the dialog waits for a slot, then uploads. With **Strict mode for direct dispatch** on it is refused instead — *Stagger cap reached* — and nothing is uploaded.

- **A restart forgets the slots and finds them again.** A few seconds after MQTT is back, every printer found heating a bed gets its slot re-registered, so a restart mid-heat does not hand out a free pass.

- **A tag pinned mid-heat counts from the next tick.** Groups are re-read on every scheduler pass; nothing has to be restarted after re-tagging a printer.

## :material-alert: Pitfalls and what-ifs

!!! warning "An untagged printer counts on every phase"
    A printer with none of the picked tags is a **wildcard**: BamDude does not know which phase it is on, so it is treated as if it could be on any of them. It starts only when **every** phase has room, and while it heats it occupies a slot on every phase at once.

    Turn the split on with a half-tagged farm and starts get *rarer*, not smarter. Tag everything first — the **No tag** group on the Printers page is the check.

- **The interval is the recovery gap, not the heat-up time.** With **Wait for bed to heat** on, the climb is already covered by the bed wait. Two to five minutes is plenty; ten just slows the farm.
- **One slow heater on the phase.** Set **Stagger interval (minutes)** on that printer's edit form (`0` = the farm default) rather than raising the whole farm's interval.
- **A phase tag cannot be deleted while it is a group.** The API answers `409` — un-tick it under Queue & Scheduling first, then delete. Silently redrawing which printers share a cap is not something a delete button should do.
- **The forecast does not see stagger.** *Ready ≈* on an order is computed without it and says so in its list of assumptions. A farm that staggers hard will finish a little later than the date — see [The customer asks when fifty will be ready](when-will-it-be-ready.md).
- **Nothing here slows the dispatcher.** Uploads to several printers still run in parallel; the cap gates the *start* of the print and nothing else, so a print already running is never slowed by a neighbour waiting for a slot.
- **A tag means whatever you say it means.** The same mechanism splits by *room* through locations; splitting by tag is for anything a room does not describe — a phase, a UPS, an extension lead.

## :material-link-variant: Related scenarios

- [Keeping the breaker and the power bill in check](power-budget.md) — stagger at the start, smart-plug auto-off at the end, energy per print in between.
- [An urgent print ahead of the queue](urgent-print.md) — what strict mode means for the person pressing **Print** in a hurry.
- [A night shift with nobody in the shop](unattended-night.md) — the cap keeps working while nobody is watching the breaker.
