---
title: The customer asks when fifty will be ready
description: From an order line to a date — the plan says what to print, the forecast says when the farm gets there, and the filament table says whether the spools last
---

# The customer asks when fifty will be ready

## :material-map-marker-question: The situation

Thirty orders are active. A customer rings and asks the question every farm hears ten times a day: *"When will my fifty lamps be ready?"* The operator used to answer from memory — how many machines are free, what is ahead in the queue, how long a lamp takes — and was usually right within a day. With thirty orders in flight, memory is what fails first.

## :material-flag-checkered: The goal

A date on the order that already accounts for the machines the farm has, the prints running on them, everything queued ahead, and the other orders that outrank this one — and a way to tell whether the filament on the shelf is enough to get there.

## :material-puzzle: What is involved

| Feature | Its part |
|---|---|
| [Orders](../features/projects.md#orders) | The line — *Lamp × 50* — with a priority and a due date. |
| [What to print next](../features/projects.md#what-to-print-next) | How many prints the fifty need, after what is printed, running and queued. |
| The farm forecast | *Ready ≈* on the order and on every plan row, the machine-hours left, and the *after N more urgent orders* date. |
| The filament table under the plan | Need per material and colour against the spools on the shelf. |
| [Staggered start](../features/staggered-start.md) and [plate-clear confirmation](../features/print-queue.md#clear-plate-confirmation) | Two of the things the forecast deliberately does not model — listed on every date it shows. |

## :material-format-list-numbered: Step by step

1. **Open the order** — or create it: **Projects → Orders → New order**, customer, a line *Lamp × 50* with material `PETG`, priority **High**, due date. The product is already in the catalog with its plates linked.

2. **Read the strip.** *Ordered 50 · Printed 12 · Complete 12 · Remaining 38*, and beside them two tiles the forecast fills: **Ready ≈** with a date and **Machine h left**. Under the tiles, when they apply: *after 2 more urgent orders: <date>* — the date if the lamps have to wait for the orders ranked ahead — and the counts of prints *without an estimate* or *with no printer for their model*.

3. **Read the plan.** *What to print next* lists the plates that cover the 38 with their counts, and every row shows its own *ready ≈* — the row's last print, not the order's. Nothing here has been sent yet; the numbers move as you change the counts.

4. **Check the filament.** The table under the plan's totals has a row per material and colour the plan needs: *need*, *on the shelf in this colour*, *on the shelf in this material*, with a shortage in amber. A shelf that could not be read — Spoolman down — says so rather than showing zero.

5. **Answer the customer.** *Ready ≈* is the date if the plan goes to the queue now, on top of what is already there. If two more urgent orders sit ahead, the second date is the honest one.

6. **Send the plan** — the whole of it to the auto-queue, or a row to a specific printer with **To printer…** — and hang up.

7. **Later:** the order page's *Printing* and *Queued* counts tick, *Printed* rises as prints finish, and when every line reaches its quantity the page raises *All lines are printed — close the order?*. Close it there; it never closes itself.

!!! tip "Thirty orders at once"
    The **Orders** tab's table view carries the same two columns — **Ready ≈** and **Machine h** — for every active order, sortable, fetched for the whole table in one request. Above the list, the filament strip sums every active order's need per material and colour: the answer to *"can we take another order in black PETG?"* before the customer asks.

## :material-cogs: What BamDude does on its own after that

- **The forecast is a simulation, recomputed on every request.** It takes a snapshot of the farm — every printer by model, the print running on each with its remaining time, everything pending in both queue tiers — and lays the plan's prints onto the machines of the models their files name, first free machine first. It writes nothing and gates nothing; a queued job does not change because the forecast looked at it.
- **Two dates, one snapshot.** *Now* places this order's plan on top of what is queued. *After* first plays out every active order ranked ahead — by priority, then due date (no due date sorts last), then age — and places this one after them. Raising the priority of an order moves its own *after* date up and pushes the *after* date of everyone below it.
- **A parked printer's work still counts.** A printer in maintenance mode or with a paused queue receives no *new* prints in the simulation, but the print it is running and the rows already in its queue are still played out — otherwise an order whose last print sits on a parked machine would read as finished.
- **Closed orders forecast nothing.** Completed and cancelled orders get no date and place no work; their rows in the table show a dash.
- **Unknowns stay unknown.** A print whose file has no time estimate, or a live print that has not yet handed over its 3MF, is counted as *without an estimate* and never quietly treated as zero hours.

## :material-alert: Pitfalls and what-ifs

!!! note "Four things the date does not include"
    Every date carries the same footnote: **staggered start**, **plate-clear confirmation**, **drying between prints**, and **upload and preheat** are not modelled — and print times are the slicer's estimate, not the archive's actual. A farm that staggers hard, or whose operators clear plates once a shift, finishes later than the date. Read it as *the machines' date*, and add the shop's habits yourself.

- **"No estimate" is a file problem.** A plate the slicer left without a time, or a mesh linked to the product, gives the row nothing to add. Re-slice, or link the sliced file.
- **"No printer for its model."** The plan picked a plate sliced for a model the farm has none of active — perhaps all of them are archived or in maintenance. The count says how many prints are stranded; switch the row's **File** to another model's slice.
- **Priority is for the date, not for the queue.** *High* moves the lamps up in the *after* ranking and in the print dialog's order picker; it does not move a single queued row. When the lamps really must jump the line, see [An urgent print ahead of the queue](urgent-print.md).
- **Prints started on the printer's screen** belong to no order until you file them — the archive editor and the Archives page's **Assign to order** do it after the fact — and until then the order's *Printed* does not see them.
- **Filament on the shelf is filament on the shelf.** The table compares against spools in the inventory, not against what is loaded in the AMS; a spool sitting in the drawer counts, a spool that was thrown away without being closed out counts too.

## :material-link-variant: Related scenarios

- [A hundred parts across five printer models](one-part-five-models.md) — where the plan's split between models comes from.
- [Surplus on the shelf, reused by the next order](spare-parts-on-the-shelf.md) — kits from stock lower the need before anything is printed.
- [Three phases, one bed heating per phase](three-phases.md) — the biggest of the four things the date leaves out.
