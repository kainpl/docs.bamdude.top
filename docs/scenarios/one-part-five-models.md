---
title: A hundred parts across five printer models
description: One part, sliced once per printer model, wanted a hundred times — the library's Calculate wizard builds the plan, the farm proposes the split, one press queues it all
---

# A hundred parts across five printer models

## :material-map-marker-question: The situation

The farm runs five printer models — P1S, X1C, A1, A1 mini and X2D — and a customer wants **100 brackets**. The engineer has done the part of the work that only a human can do: sliced the bracket **once per model**, so the library holds `bracket-p1s.gcode.3mf`, `bracket-x1c.gcode.3mf` and three more, every one of them making six brackets a plate.

The operator used to do the rest by hand: count the free machines of each model, work out *"twelve plates on P1S, four on X1C…"*, and queue each file separately. With a hundred parts and five models that is arithmetic done under pressure, and it goes wrong.

## :material-flag-checkered: The goal

Say the number once — **100** — and have the whole thing land in the queue: the right file on each model, the count split by what the farm can actually take, and a running total on one page that says how many are done, printing, queued and still to go.

## :material-puzzle: What is involved

| Feature | Its part |
|---|---|
| **Calculate** in the [File Manager](../features/file-manager.md) | The wizard: from a selection of sliced files to an order with a plan, without authoring a product by hand. |
| [What to print next](../features/projects.md#what-to-print-next) — the plan block | Picks plates to cover what is still needed, ranked by useful parts per hour; the same block the order page shows. |
| [Alternative files per printer model](../features/projects.md#alternative-files-per-printer-model) | One plan row, five candidate files — and the split of the row's count between them. |
| The farm's split proposal | The forecast's suggestion of how to divide the row between models, applied with one press. |
| [Auto-queue](../features/auto-queue.md) | Takes each queued copy to a free printer of the model its file was sliced for. |

## :material-format-list-numbered: Step by step

1. **Tick the five files** in the File Manager. The **Calculate** button appears in the toolbar as soon as the selection contains something sliced.

2. **Step *Parts*.** The wizard lists the files with their plates, and under them one **unified list of parts** — `bracket`, once, although five files carry it: object names are canonicalised across files, so `bracket`, `bracket_2` and the clone suffixes a slicer adds are one part. Type the **target per part**: `100`. Give the order a name — `Brackets, 100` — or leave the one the wizard suggests.

    *If exactly one catalog product already links all five files, the wizard offers **Use product “…”** instead of creating a one-off one.*

3. **Calculate.** The wizard creates a product for the job — a one-off that never appears in the catalog — and an order with one line, and the dialog turns into step ***Plan***: the same plan block the order page has.

4. **Read the plan.** One row: a plate, *Covers: bracket ×6*, a count of **17** (six a plate, a hundred wanted — the seventeenth plate makes two spare), time, filament and cost **per print**, and *ready ≈* for the row. Because the five files make the same parts, the row carries a **File** switch listing all five, each labelled with its printer model.

5. **Split by the farm.** Next to the switch the row shows the farm's proposal — *by the farm: P1S 8 · X1C 3 · A1 3 · A1 mini 2 · X2D 1* — worked out from how many printers of each model there are and how busy they are. Press **Split by the farm** and the proposal fills the **Split across files** form. Edit any number you disagree with; the counts have to add up to 17 or the row refuses to send.

6. **Queue it.** **× 17 to queue** on the row — or the whole plan at once. Every copy becomes an auto-queue item targeted at the model of *its* file. The wizard says *Queued*; **Open order** takes you to the order page, where the figures start moving as prints finish.

    Not ready to queue yet? **Keep the order** closes the wizard with the order kept; **Cancel** deletes it.

!!! tip "A kit instead of one part"
    The same wizard handles a product of several parts. Tick the lamp's files — base, shade, clip — set **Units** to `20` and fill **One unit is:** with `1`, `1`, `2`. The plan then covers every part with the fewest plates and the least surplus, and the order counts finished *units*, the scarcest part deciding.

!!! tip "The lighter road: a batch from the print dialog"
    Printing one file many times without the wizard? The print dialog's **Order** field offers **New order for this batch** once the quantity is two or more, so the batch becomes an order on its own and shows up with the others — printing, queued, remaining — instead of scattering across printer cards.

## :material-cogs: What BamDude does on its own after that

- **Each copy is routed by its file's model.** `bracket-p1s` copies go to free P1S printers only, `bracket-x1c` to X1C — the router never sends a file to a model it was not sliced for. Within a model, the next free printer wins; one printer gets at most one new item per tick.
- **Every start still passes the usual gates:** filament loaded and mapped, plate-clear confirmation where the printer asks, the staggered-start slot, drying. A copy that cannot start yet waits in that printer's queue with its reason on the row.
- **The order counts from the prints.** As archives complete, the line's *Printed* rises and the plan's *Outstanding* falls; what is queued is subtracted too, so reopening the plan never asks for prints already on their way.
- **The proposal is a proposal.** Nothing about the split is applied until you press the button, and nothing re-splits later by itself unless rebalancing is on.

## :material-alert: Pitfalls and what-ifs

!!! tip "The split is a starting point"
    Once queued, a copy belongs to its file's model — until rebalancing moves it. With **Rebalance across printer models** on (Settings → Printing → Auto-Queue Routing), the auto-queue moves still-pending copies to idle printers of another model whenever that finishes the row sooner, recalculating plates and counts for that model's bed. With it off, the row's **Rebalance** button does the same on demand, and a pending row on the auto-queue panel can be moved on its own. Details: [Rebalancing across printer models](../features/auto-queue.md#rebalancing-across-printer-models).

- **All five files first.** The wizard can only offer the models it has files for; a model with no file simply gets no copies. *Prepare every slice before you calculate.*
- **Same part, same name.** The unified list depends on the object being called the same thing in every file. `bracket` in one slice and `bracket_v2` in another are two parts with two targets — rename in the slicer, or set the stray one's target to `0` and let the other carry the hundred.
- **A file without a recorded model** cannot be routed: the auto-queue needs to know what the file was sliced for. Such a plate shows in the plan but a copy of it would wait forever; re-slice with a current slicer.
- **Machine-hours are not a date.** The wizard's hour total is the sum of print times; the date is the order page's *Ready ≈* — see [The customer asks when fifty will be ready](when-will-it-be-ready.md).
- **The one-off product lives as long as its order.** It is hidden from the catalog and from every picker; delete the order and it goes with it. If the bracket turns out to be a regular, **Add to catalogue** on the product page promotes it.

## :material-link-variant: Related scenarios

- [The customer asks when fifty will be ready](when-will-it-be-ready.md) — the same plan, read for its dates.
- [An urgent print ahead of the queue](urgent-print.md) — one copy that has to go before the hundred.
- [Surplus on the shelf, reused by the next order](spare-parts-on-the-shelf.md) — the two spare brackets from the seventeenth plate.
