---
title: Archived Printers
description: Soft-retire a printer instead of deleting it — hide it everywhere while keeping its print history
---

# Archived Printers

A printer you've retired — sold, decommissioned, swapped out for a newer model — doesn't have to be **deleted**. Archiving *soft-retires* it: the printer disappears from the whole app and drops its MQTT connection, but its full print history stays intact so you never lose the archive of what it produced.

---

## :material-information: What It Is

Archiving is a one-click "put this machine away" action. An archived printer:

- **vanishes from the Printers page**, every printer picker, and the print-queue view;
- **is excluded from dispatch** — the scheduler, [Auto-Queue Routing](auto-queue.md), model-based assignment, and the virtual printer never route to it;
- **is dropped from metrics** and sensor-history recording;
- **is left out of PA-profile assignment** — the spool form's K-profile picker (and the count on its PA Profile tab) only offers non-archived printers, so a retired machine's old calibrations don't clutter new spools;
- **disconnects from MQTT** and stays disconnected until you restore it;
- **keeps every one of its [print archives](archiving.md)** — the history is preserved, not deleted.

It's the graceful alternative to **Delete Printer**, which throws the machine (and, by default, its archives) away for good.

!!! note "Permission"
    Archiving, restoring, and permanently deleting a printer all require `printers:delete` — an admin-grade permission held by the **Administrators** group. Operators and Viewers can't archive a printer.

---

## :material-swap-horizontal: Archive vs. Maintenance Mode

Archiving and [Maintenance Mode](printer-control.md#maintenance-mode) are **two independent axes** — a printer can be in either, both, or neither. They solve different problems:

| | :material-wrench: Maintenance Mode | :material-archive-arrow-down: Archive |
|---|---|---|
| **Intent** | Temporarily park a working printer (nozzle swap, belt job, flaky machine) | Retire a printer you're done with (sold, decommissioned) |
| **Card on Printers page** | Stays **visible** with an amber *Maintenance* pill | **Hidden** entirely |
| **Underlying field** | `is_active` flag | separate `archived` / `archived_at` columns |
| **Permission** | `printers:update` | `printers:delete` |
| **How you exit** | *Exit* button on the card | Restore under Settings → Printing |

Because they're separate flags, a printer archived while it was also in Maintenance Mode stays parked (`is_active=False`) when restored — it won't silently reconnect just because you unarchived it.

---

## :material-archive-arrow-down: What Happens When You Archive

Triggering an archive (`POST /api/v1/printers/{id}/archive`) runs, in one transaction:

1. **Blocked while printing.** If the printer is running a job, the request is refused with **`409 — Stop the active print before archiving this printer`**. Stop the print first, then archive.
2. **Pending queue items are cancelled.** Every `pending` item on that printer's queue(s) flips to `cancelled`, and the response reports how many were cancelled (`cancelled_items`). Nothing is left orphaned in a queue that's about to disappear.
3. **`archived` is set** (with `archived_at` stamped to the current time).
4. **MQTT is disconnected.** The printer drops off the wire and won't reconnect until restored.

From that moment the printer is invisible to every availability query in the app.

!!! warning "Can't re-add the same serial"
    An archived printer keeps its serial number. If you try to *add* a new printer with a serial that belongs to an archived one, BamDude refuses with **`409 — This serial belongs to an archived printer — unarchive it instead of re-adding`**. Restore it instead.

---

## :material-restore: Restore or Delete

Archived printers resurface in exactly one place: **Settings → Printing → Archived printers**. Each row shows the printer's name, model, and when it was archived, with two actions:

| Action | Icon | What it does |
|--------|------|--------------|
| **Restore** | :material-restore: | Unarchive the printer (`POST /api/v1/printers/{id}/unarchive`). It reappears everywhere and reconnects to MQTT — **unless** it's also in Maintenance Mode (`is_active=False`), in which case it stays parked. |
| **Delete forever** | :material-trash-can: | Permanently delete the printer (`DELETE /api/v1/printers/{id}`). This is irreversible and, by default, also removes the printer's archives. Confirmation is required. |

The panel only appears for users with `printers:delete`.

---

## :material-history: History Is Preserved

Archiving never touches `print_archives`. Everything the printer ever produced stays in the [Print Archive](archiving.md), and the **Archives page keeps archived printers in its printer filter** — so you can still filter history by a retired machine long after it's gone from the dashboard. That's the whole point of archiving over deleting: the record outlives the hardware.

Wherever those past prints surface — the [Statistics](stats.md) per-printer breakdowns and bar chart, the Archives list / grid / calendar, and that printer filter — a retired printer is labelled **Printer N (Archived)** instead of its old name, so it reads unmistakably and is never mixed up with an active machine. In those same lists archived printers also sort to the **bottom**, below the active ones.

---

## :material-link: Related

- [Printer Control → Maintenance Mode](printer-control.md#maintenance-mode) — the temporary-park counterpart
- [Per-Printer Queues](print-queue.md) — an archived printer's queue disappears from the queue view
- [Auto-Queue Routing](auto-queue.md) — archived printers are never picked as dispatch targets
- [Print Archiving](archiving.md) — the history that survives an archive
