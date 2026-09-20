---
title: Recording scrap
description: Three of the eight lids warped — where the number goes, what it changes on the order, and what is counted for you when you skip an object mid-print
---

# Recording scrap

A plate comes off with two of six parts warped. Where do you say so — and what changes when you do?

## What you need

| Feature | Why it matters here |
|---|---|
| [Orders](../features/projects.md) | An order's figures subtract defects live: two bad parts are two parts still to print. |
| Defects on the print | Every print keeps its own count — per part when the plate's parts are known, else one flat number. |
| [Telegram](../features/telegram-bot.md) | The completion message and the plate answers ask for the count right there. |
| [Statistics](../features/stats.md) | Defects by printer, over any timeframe. |

## Where you say it

1. **On the order page.** Under *Prints*, every card shows `6 · 2 defective`. Its menu has **Defects…**: one counter per part, capped at what the plate made. Save, and the order's *Defective*, *Remaining* and progress move at once.
2. **When you clear the plate.** On the printer card, the finished print's counters sit beside **Clear plate** and **Repeat** — fill in what came out bad and press either; the count travels with the answer. Only the print on the plate can be graded this way, under the same permission as clearing.
3. **In Telegram.** The completion message offers **Defects…**, and answering **Plate cleared** or **Repeat print** asks the same question: one tap per part (0–5, or *other…* to type a number), *no defects, done* ends it.
4. **Later, on any print.** The archive editor keeps its counters for prints of any age.

Skipped objects are counted for you: a part you skip from the printer's screen or from BamDude is already in the count when you get there.

## What changes when you do

- **The order's figures.** Defective parts are not usable parts: they come off the line's progress and go back into *what to print next*.
- **The shelf.** A print that belonged to no order was put on the product's shelf when it finished — as *printed − defective*. Record two bad parts the next morning and the shelf gives them up, with a line in the stock journal saying why. If those parts have already gone out of the door, the shelf cannot follow: BamDude says so where you recorded the defects — on the printer card or in the Telegram prompt — and you correct the shelf by hand on the product page.
- **Statistics.** *Defects by printer* shows printed, defective and the rate per machine, so a printer that eats every third part shows up.

!!! warning "Surplus you already banked stays banked"
    Banking an order's surplus to the shelf is a button, and recording defects afterwards does not un-bank it — the order's *bankable surplus* simply drops to zero. Correct the shelf by hand if the banked parts turn out to be the bad ones.
