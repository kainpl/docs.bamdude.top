---
title: Surplus on the shelf, reused by the next order
description: The plate makes four, the order wanted three — the fourth goes onto a shelf, and the next order takes it instead of printing
---

# Surplus on the shelf, reused by the next order

## :material-map-marker-question: The situation

The lamp is two printed parts, a base and a shade, one of each per lamp. The shade plate makes **four** shades; order A wants **ten** lamps, so three shade plates were printed — twelve shades, two too many. The bases came out exactly ten.

Two shades now sit in a box under the bench. Next month somebody orders five lamps, prints five shades, and the box has four. Nobody ever counts the box.

## :material-flag-checkered: The goal

The two spare shades exist **in BamDude**: on the product's shelf, where the next lamp order finds them and prints two shades fewer — and where a part somebody printed on a whim, outside any order, lands too.

## :material-puzzle: What is involved

| Feature | Its part |
|---|---|
| [Free stock of parts](../features/projects.md#free-stock-of-parts) | The shelf: a ledger of movements per printed part, and a kit count per product. |
| [Bank the surplus](../features/projects.md#banking-a-surplus) | The button on an order that moves its extra parts onto the shelf. |
| [Taking kits from stock](../features/projects.md#taking-kits-from-stock) | **From stock** on a new order line: kits reserved from the shelf count as done. |
| [Prints without an order](../features/projects.md#prints-without-an-order) | A print filed under no order is credited to the shelf by itself — good parts only. |

## :material-format-list-numbered: Step by step

1. **Order A is printed.** On its page, the lamp line expanded shows the shade part with *Surplus 2*, and the header's **Bank the surplus** button is live. Press it. The toast says what moved — *2 → free stock of Lamp* — and the button goes quiet: pressing it again moves nothing, and says so.

2. **Look at the product.** **Products → Lamp**, section **Free stock**: the headline says **0 kits** — two shades and no bases make no whole lamp — and the parts table below reads *shade 2 · base 0*. The movements table has one row: today, shade, `+2`, *Surplus banked*, with a link to order A.

3. **A base from nowhere.** An engineer prints a plate of four bases from the printer's own screen to test a new filament. It belongs to no order, it completes, and the shelf reads *shade 2 · base 4* — **2 kits**. Nobody pressed anything: an order-less print is credited on completion, good parts only. *(A scrapped base would not have counted — see [Recording scrap](recording-defects.md).)*

4. **Order B: five lamps.** **New order**, line *Lamp × 5*. Under the quantity the line row shows **From stock** with `2` already in it — the shelf has two kits and the line wants five, so two is the default. Save. The line reads *5 ordered · from stock 2*; its need is three; the plan asks for three lamps' worth of plates and not five.

5. **The shelf after.** *shade 0 · base 2* — the two kits went out as a reservation for order B's line; the two extra bases stay. The movements table shows `−2` on each part, *Reserved for an order*, linked to order B.

6. **A count that disagrees.** Somebody finds a third shade in the box. **Adjust** on the product's shelf: the part, `+1`, and a note you must write — *found in the box under bench 3*. Corrections are movements too; the ledger never overwrites.

## :material-cogs: What BamDude does on its own after that

- **The shelf is a ledger, never a counter.** A part's balance is the sum of its movements; there are exactly five reasons, and the reason fixes the sign: surplus banked (+), print without an order (+), reserved for an order (−), reservation released (+), hand correction (±). A movement of zero is never written.
- **Kits are the scarcest part.** The product's kit count is the minimum over its counted parts of *balance ÷ per unit* — the same rule that drives a line's progress. Two shades and no bases are two parts and no lamp.
- **A reservation is "done" everywhere at once.** Order B's need, progress bar, plan and *close the order?* banner all count the two kits as made; a line covered entirely from the shelf asks for no prints at all.
- **The reservation follows the line.** Delete the line, drop its quantity below the reservation, cancel the order or delete it, and the kits come back with *the order was deleted* or *reservation released* in the table. Deleting an unfinished order also credits its finished prints back as order-less prints — they belong to nobody now.
- **Filing changes the credit.** File the engineer's base print under an order later and the `+4` is taken back; take it out again and it returns. The books follow your mind-changes.

## :material-alert: Pitfalls and what-ifs

!!! warning "A completed order gives nothing back"
    Cancel a completed order, delete one of its lines, delete the order: the kits it took stay gone, and its prints are not re-credited. They left inside the lamps the customer received. The one door that stays open is typing a new **From stock** number on a completed order's line — that is you correcting what the order took, and a mistake needs somewhere to be fixed.

- **Bank moves the difference.** Surplus grows as prints finish; press the button again later and only what is new goes over. It is never automatic — a surplus is sometimes shipped with the order and sometimes binned, and only you know which.
- **Kits from stock never raise a surplus.** They lower the line's need, progress and plan, but the surplus is measured against the line's *full* quantity. Otherwise the same kits would land on the shelf twice — once banked, once released.
- **Reopening a cancelled order re-reserves nothing.** The shelf may have gone to somebody else in the meantime; type **From stock** again if it is still there.
- **A duplicated order takes nothing.** A reorder must not quietly empty the shelf.
- **Only counted printed parts have a shelf.** A part with *per unit* `0` is not measured; a purchased part is procurement, not stock.
- **History is not swept up.** Prints from before the shelf existed are not counted in; for one you know is still in the box, the archive editor's **Count into stock** does it — one print at a time, on your say-so, and only for a print that finished successfully and belongs to no order.
- **The whole farm's shelves are one tab.** **Projects → Stock** lists every product with anything on its shelf, the orders holding its kits, and one journal of every movement — the place to look when the question is "what do we have" rather than "what does this product have".

## :material-link-variant: Related scenarios

- [Recording scrap](recording-defects.md) — why "good parts only" needs the scrap count to be right.
- [The customer asks when fifty will be ready](when-will-it-be-ready.md) — kits from stock shorten the plan before anything is printed.
- [A hundred parts across five printer models](one-part-five-models.md) — where the seventeenth plate's two spare brackets come from.
