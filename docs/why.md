---
title: Why BamDude
description: BamDude is a fleet manager — not a passive backend listening to your slicer. Why that distinction matters and how to think about plugging it into your workflow.
---

# Why BamDude

## Two ways to drive a 3D printer

**The classic way:** slicer → printer. You hit Print in BambuStudio or Orca and the file flies to the printer over LAN. In this model BamDude — like any external service — is a passive listener: it catches events from the printer, builds history "where it can," and tries to track filament usage on a best-effort basis.

That flow works fine when you have one or two printers and the cost of fuzzy history / fuzzy spool accounting is acceptable. The moment your fleet grows — or the moment accurate logs and real spool control start driving business decisions — the "slicer is in charge" model stops holding water.

**The fleet-first way:** slicer → BamDude → printers. You slice as usual, but the Print button now sends the file to BamDude instead of straight to a printer — through a [virtual printer](features/virtual-printer.md) running in **File Manager** mode. Inside BamDude you pick which printers run the job and in how many copies. From there BamDude:

- distributes the file to each printer,
- runs the macros (including [swap mode](features/swap-mode.md)),
- watches progress and catches completion,
- writes a complete print [history](features/archiving.md),
- tracks every gram of filament that actually went into the print.

This is the canonical shape of a fleet manager: **one source of truth orchestrating everything else.** Bambu Farm Manager and Bambu Handy do the same job — BamDude does it self-hosted, with its own history, swap mode, queue, energy tracking, flexible notifications, and a full access-control system.

---

## Example: Benchy on 10 printers at once

10 A1 minis, [swap mode](features/swap-mode.md), one copy per printer.

**Without BamDude:**

1. Slice the Benchy.
2. Save the `.3mf` to disk.
3. Open SwapList.app → load the file → configure swaps → save the swap file.
4. Open Bambu Farm Manager → upload the swap file.
5. Hit Print → pick all 10 printers → start.

**With BamDude:**

1. Slice the Benchy.
2. Hit Print → pick the BamDude virtual printer in File Manager mode.
3. Switch to BamDude → "Schedule" or "Print."
4. Select all the minis, set 10 plates, hit "Print."

That's it. Files dispatch across the fleet, swap macros run, history is written, spools are accounted for.

---

## What this replaces

BamDude steps in for Bambu Farm Manager and Bambu Handy when you want:

- self-hosted, with no mandatory cloud dependency (Bambu Cloud is opt-in, not required);
- print history that's guaranteed, not "best effort";
- spool accounting tied to actual print events;
- equally capable control from [Telegram](features/telegram-bot.md), mobile, and the web UI;
- flexible notifications with per-chat / per-channel preferences;
- a full API plus integrations ([Spoolman](features/spoolman.md), [Home Assistant](features/mqtt.md), [OrcaSlicer / BambuStudio as sidecars](features/slicer-api.md), [Prometheus](features/prometheus.md), webhooks).

---

## What if I start a print from the slicer directly, or from the printer screen?

BamDude knows how to pick that up after the fact — it'll add it to history and try to fetch the 3MF from the printer. But that path is **the exception, not the rule.**

Bambu's firmware is closed, which puts a hard ceiling on what an external server can learn after the event. If BamDude is offline at the moment something happens (link drops, server restart, anything), and the operator does 10 reprints by hand in that window — those 10 reprints stay invisible to BamDude forever. No passive listener can recover them with full accuracy, because they were never in the event stream the server got to see.

---

## The architectural takeaway

As long as 3D-printer firmware stays closed, there's only one shape that holds up for a serious fleet:

> **Slicer ↔ Fleet manager ↔ Printers.**

Not "slicer talks to printers directly while a manager somewhere listens in." Not "three different UIs steering the same printers with no knowledge of each other." **One centre that sees everything — because everything passes through it.**

[Virtual printers](features/virtual-printer.md) exist precisely to make that shift painless: you don't have to break the slice-and-Print habit. You just point the same Print button at the right place.

---

[Get Started :material-arrow-right:](getting-started/index.md){ .md-button .md-button--primary }
[Set up a Virtual Printer :material-printer-3d-nozzle:](features/virtual-printer.md){ .md-button }
