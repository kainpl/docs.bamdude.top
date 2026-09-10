---
title: An urgent print ahead of the queue
description: Four brackets by lunchtime on a farm the auto-queue feeds — three ways to cut in, and which one fits which kind of queue
---

# An urgent print ahead of the queue

## :material-map-marker-question: The situation

Forty-eight printers, and most of the work reaches them through the [auto-queue](../features/auto-queue.md): jobs are queued as *"any P1S"* and the router hands each one to the next P1S that frees up. Each printer's own queue therefore holds only the job it is running; everything else waits in the auto-queue panel.

At 11:10 a customer rings: four brackets by 13:00. `brackets.gcode.3mf` is sliced for the P1S and takes 55 minutes. Every P1S is printing; three of them will finish within twenty minutes.

## :material-flag-checkered: The goal

The brackets start on the first P1S that frees up — **before** anything the router would otherwise hand it — without interrupting the prints already running and without re-sorting the rest of the farm.

## :material-puzzle: What is involved

| Feature | Its part |
|---|---|
| [Per-printer queues](../features/print-queue.md) | A list per printer, walked strictly top to bottom. **Move to top**, drag, up/down, batches that move as a block. |
| [Auto-queue panel](../features/auto-queue.md) | The pile of work not yet given a printer: drag to reorder, **Assign now** to try immediately. |
| The print dialog | **Print** starts now on one machine, bypassing every queue; **Add to Queue** puts a row into one printer's own list. |
| [Staggered start](../features/staggered-start.md#direct-prints-and-strict-mode) | Every start takes a slot; strict mode turns a wait into a refusal. |

## :material-format-list-numbered: Three roads

Which road is right depends on what kind of queue the printer has. Two of them apply here; the first is for a farm that does not use the auto-queue at all.

### Road 1 — the printer has its own list: reorder it

When a printer's queue is a list you built by hand — no auto-queue in play — the queue is walked in **position** order and nothing else. So:

1. Put the brackets into that printer's queue: drag the file onto its queue card, or tick the printer in **Schedule Print** from the File Manager, quantity `4`. The four rows land at the bottom as one batch.
2. On the queue card, **Move to top** on the batch — or drag the grip handle when the card is expanded; the up/down arrows are the always-available fallback. A batch moves as a block.
3. The running print is untouched. The brackets start when it ends — and after **Clear Plate & Start Next** if that printer asks for plate confirmation.

### Road 2 — the auto-queue is the distributor: give the job to one printer directly

This is the farm in the situation. The router hands a printer its next job only when the printer is free, so a printer's own queue is nearly always empty apart from the running job. **Anything you put into a specific printer's own queue therefore goes next on that printer**, ahead of whatever the router would have handed it.

1. Pick the P1S that will finish first. On the Printers page or the Queue page, sort by **ETA (job)** — the running job's own remaining time.
2. Put the brackets into **that printer's** queue, not into the auto-queue: drag the file onto its queue card, or open **Schedule Print** and tick that one printer (not **Auto**). Quantity `4`.
3. That is all. The four rows are first — and only — in line on that printer.

What happens next is the router's doing, described below: the printer stops receiving auto-queue work until its own queue is empty again, the brackets run back to back, and then the router resumes feeding it.

**If a P1S is idle right now**, skip the queue altogether: open the print dialog for the file and press **Print** rather than **Add to Queue**. That is a direct dispatch — the file uploads and starts, no position anywhere. It still takes a staggered-start slot like every other start.

### Road 3 — reorder inside the auto-queue

Use this when the urgent job should *stay* model-routed — "any P1S, whichever is first" — or is already sitting in the auto-queue.

1. On the Queue page, the **Auto-Queue panel** lists pending items in true dispatch order. Drag the item, or its `×4` block, to the top.
2. The next P1S to free up gets it.
3. **Assign now** on the row forces an immediate attempt: if an eligible P1S is free *at this moment* the item is assigned to it; if none is, nothing changes and the panel says so. It is a *try now*, not a pin.

!!! warning "With Shortest job first on, position means nothing"
    **Settings → Printing → Queue & Scheduling → Auto-Queue Routing → Shortest job first** hands the order to the distributor: shortest predicted print first, with a sticky flag that stops long jobs from starving. The panel hides the drag handles and says so. A 55-minute urgent job cannot be dragged ahead of a pile of 20-minute ones — take Road 2 instead, or switch the setting off for the moment.

## :material-cogs: What BamDude does on its own after that

- **A printer with something pending in its own queue is busy to the router.** The auto-queue's busy set is *"a print is running"* **or** *"a pending row exists in the printer's queue"*. That is what makes Road 2 work: your rows are pending, so the router gives that printer nothing more until they are gone — then it resumes as if nothing had happened. It is also why the router never stacks two new jobs on one printer in a tick.
- **A per-printer queue is walked by position.** A scheduled time is a gate that makes the scheduler skip a row and move on; it never re-sorts the queue. A row added with **Queue only** (staged) waits for **Start**.
- **Every running print claims its printer.** A direct **Print** claims the queue before the upload begins, so the router cannot dispatch over it while the file is still transferring.
- **Every start takes a stagger slot** — queued or direct — and waits for one. With **Strict mode for direct dispatch** on, a direct **Print** on a full phase is refused with *Stagger cap reached* instead of waiting; the queued rows just wait.
- **The last print on that printer failed?** A row with **Only run if the previous print succeeded** is held as *skipped* until you press **Unskip** — one press clears the whole queue behind it.

## :material-alert: Pitfalls and what-ifs

- **Cutting in never means stopping what is running.** If the running part really is worthless, stop it from the printer card and answer the plate-clear prompt; only then does the queue move.
- **Order priority is not a queue position.** An order's *Low / Normal / High / Urgent* ranks the forecast and the order picker in the print dialog; it moves nothing in any queue. Moving is done with the roads above.
- **The material has to be loaded.** The print dialog maps the brackets' filament to AMS slots on the printer you chose; on the wrong printer the row waits with *waiting for filament* as its reason. Check the mapping in the dialog at 11:10, not at 12:50.
- **Print takes one plate, Add to Queue takes several.** For a multi-plate file the direct print dialog runs one plate; queue several and each becomes its own row.
- **Two operators, one printer.** Road 2 rows stay pending and visible; a colleague dragging the printer's queue sees them and can move them. Nothing here is hidden from the queue page.

## :material-link-variant: Related scenarios

- [Three phases, one bed heating per phase](three-phases.md) — where the slot the urgent print waits for comes from.
- [A hundred parts across five printer models](one-part-five-models.md) — the opposite problem: not one job first, but a hundred jobs everywhere.
- [A night shift with nobody in the shop](unattended-night.md) — the same busy rule keeping an unattended farm fed.
