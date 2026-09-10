---
title: Recording scrap
description: Three of the eight lids warped — where the number goes, what it changes on the order, and what is counted for you when you skip an object mid-print
---

# Recording scrap

## :material-map-marker-question: The situation

`X1C-07` printed a plate of eight lids for the lamp order. Two of them lifted off the bed an hour in and the operator **skipped** them from the printer card so the other six could finish; when the plate came off, one more lid turned out to be warped. Eight printed, five usable.

The order page says *Printed 8*. Unless somebody tells it otherwise, the lamp order will believe it has eight lids, plan no replacement plate, and come up three short at packing.

## :material-flag-checkered: The goal

The print carries the truth — **8 printed, 3 defective** — in a place the order reads, so the order's need, its plan and its stock credit all move by three without anybody rewriting the print count itself.

## :material-puzzle: What is involved

| Feature | Its part |
|---|---|
| [Skip objects](../features/printer-control.md) | Cancels one object mid-print; the printer's own report of what was skipped raises the print's scrap count for you. |
| [Print archiving](../features/archiving.md) — the archive editor | Where a scrap count is typed: per print, and per part on the plate. |
| [Orders](../features/projects.md#the-figures) | *Usable = printed − defective*; the scrap becomes need, and need becomes a plate in the plan. |
| [Free stock of parts](../features/projects.md#free-stock-of-parts) | An order-less print is credited to the shelf with its *good* parts only. |

## :material-format-list-numbered: Step by step

1. **Mid-print: skip the failed objects.** On the printer card, the skip-objects button opens the plate with every object numbered; tick the two lifting lids, confirm. The printer stops printing them and carries on with the rest. *(The button is offered only while the file carries per-object markers and more than one object is still printing.)*

2. **When the print finishes, open it in Archives.** The card already reads *2 defective part(s)* — the two skips, counted from the printer's own report. Open the print's editor (the pencil on the card).

3. **Type the third.** The editor has **Defective Parts** — *how many came out unusable* — and, under it, a table **Defective parts** with a row per part on the plate, the skips already pre-filled. Change the lid row from `2` to `3`; **Total scrap** follows. Save.

    *Why per part:* a plate that carries lids **and** bases must say which of them warped, because the order needs the two parts separately. On a plate of one part the single field is enough.

4. **Look at the order.** The lamp line's *Usable* for the lid part reads 5, *Remaining* rose by three, and the plan under the lines now asks for another lid plate. The order strip's **Defective** tile shows the three. Nothing else changed: *Printed* still says 8.

## :material-cogs: What BamDude does on its own after that

- **Skips are counted from the printer, not from your click.** The scrap counter follows the printer's own list of skipped objects — so a skip made on the printer's touchscreen, or from the Bambu app, counts too, and a skip the firmware refused (the object was already finished) does not. The automatic count only ever **raises** the number: it takes the larger of what you typed and what the printer reported.
- **The order subtracts, the archive does not.** *Usable = printed − defective* lives in the order's figures. The print itself and the farm-wide statistics keep saying *8 printed* — two numbers side by side, on purpose, so a figure you already reported is never rewritten under you.
- **The shelf gets good parts only.** Had this print belonged to no order, it would have been credited to the product's free stock as *5 lids*, not eight — see [Surplus on the shelf](spare-parts-on-the-shelf.md).
- **The plan reacts on its next read.** Nothing is cached: reopen the order and the extra plate is already there.

## :material-alert: Pitfalls and what-ifs

- **The number is typed on the print, not on the order.** The order page shows the total but has no field for it — the road is Archives → the print → its editor. Filter Archives by printer to see one machine's scrap history: the defect sits on the print, and the print sits on the printer.
- **A skipped object stays on screen, greyed out.** Removing it would shift every other number on the plate, and the object you were aiming at between two screens would be a different lid.
- **You cannot skip the last object.** Skipping the only thing still printing is a stop with extra steps; stop the print instead.
- **A failed print's scrap is moot.** The line counts *usable* over **completed** prints only; a print that failed or was cancelled contributes nothing to the lid count whatever its scrap field says — it is already outside the figures.
- **Automatic never lowers.** If the printer reported two skips and you type `1`, the print keeps `2`. Typing a higher number is always honoured; lower means the skip really was refused, and the printer would not have reported it.
- **Scrap is per print, not per spool.** Filament used by a scrapped part is still filament used; the order's *Filament* sum keeps it, deliberately.

## :material-link-variant: Related scenarios

- [Surplus on the shelf, reused by the next order](spare-parts-on-the-shelf.md) — what "good parts only" means for the shelf.
- [The customer asks when fifty will be ready](when-will-it-be-ready.md) — three more lids move the date.
- [A night shift with nobody in the shop](unattended-night.md) — when it is the AI, not the operator, that stops a failing print.
