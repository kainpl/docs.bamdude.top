---
title: Maintenance across fifty printers
description: Nine task types that know which machine has rods and which has rails, intervals in print hours, and a Telegram button for the person holding the grease
---

# Maintenance across fifty printers

## :material-map-marker-question: The situation

Forty-eight printers of five models. A P1S wants its carbon rods wiped every so often and its rods never oiled; an A1 wants its rails oiled and has no carbon rods; the X2D has steel rods that want both. Nobody remembers when `P1S-23` last had its nozzle cleaned, the belts on the old X1Cs are tensioned when a print looks bad, and the one person who does the maintenance is on the shop floor with a rag, not at a desk.

## :material-flag-checkered: The goal

Every printer shows what is due on it and when, measured in **print hours** rather than calendar guesswork; the list on each machine matches its mechanics; the person with the rag closes a task from the phone; and the history is there when a warranty claim asks for it.

## :material-puzzle: What is involved

| Feature | Its part |
|---|---|
| [Maintenance tracker](../features/maintenance.md) | The page: a card per printer, due / due soon / OK, history and per-task settings. |
| Model-aware task types | Nine bundled types filtered by mechanical class — rods, steel rods, rails, universal — plus your own. |
| Print-hour intervals | *Every 100 hours* counted from the printer's own runtime, with a hand-set offset for a used machine. |
| [Notifications → Maintenance Due](../features/notifications.md) and the [Telegram bot](../features/telegram-bot.md) | The nudge, and the **Mark done** button on it. |
| The printer card | The maintenance pill on the card says *due* without opening the page. |

## :material-format-list-numbered: Step by step

1. **Open the Maintenance page.** A card per printer, each already carrying the tasks its model needs: the P1S cards show **Clean Carbon Rods** and never a lubrication task; the A1s show **Lubricate Linear Rails** and **Clean Linear Rails**; the X2D and P2S show the two steel-rod tasks; every card shows the four universal ones — build plate, nozzle, belt tension, PTFE tube. Nothing to assign by hand.

2. **Tell it about the used machines.** The three X1Cs came second-hand with three thousand hours on them. On each card, edit the **total print time** and set the real figure: intervals count from the printer's runtime plus this offset, so a machine that has printed for two years is not treated as new.

3. **Tune an interval for the shop.** The A1 minis run PETG-CF all week and need their nozzles more often. On the card's **Settings** tab, override **Clean Nozzle** on those printers from 100 to 50 print hours; the farm default stays.

4. **Add what the wiki says and the list does not.** **Maintenance Types → Add Custom Type**: *Replace carbon filter*, **Calendar Days** `90`, **Printer models** X1C and P1S only, and the wiki page as its **Documentation Link**. It appears on exactly those cards.

5. **Filter the floor.** The toolbar: **Status** *Overdue* — the cards that need a hand today; **Location** to walk one room at a time; **Hide offline** to skip the machines that are switched off; sort by **Hours** to find the hardest-worked.

6. **Close a task from the floor.** The person with the rag opens Telegram: the *Maintenance due* message for `A1-12` carries a **Mark done** button; press it, and the task resets with the chat as the operator of record. At the desk, the card's **Reset** button does the same, with a note — *cold pull, PTFE looked fine* — that lands in the history.

7. **Export when the warranty asks.** History → Excel, a date range, one printer or all: date, operator, hours at the time, notes.

## :material-cogs: What BamDude does on its own after that

- **The right tasks per model.** The bundled types carry a mechanical class; a printer joins the farm and its card gets the tasks for its class, the moment it is added. A type that does not apply is never offered on that printer.
- **Hours come from the printer.** Every print adds to the printer's runtime; a task's *hours since* is runtime plus your offset minus the hours at its last reset. The bar on the card fills as the interval is consumed.
- **Due soon at 90 %.** A task turns *due soon* inside the last tenth of its interval, *overdue* past it, and the printer card's maintenance pill picks up the worst task on the machine.
- **The nudge is an event.** *Maintenance Due* fires through whichever providers subscribe to it — Telegram with its button, ntfy or Pushover at their *plan-ahead* priority — and the daily digest lists it. It is off by default on a new provider; turn it on there.
- **Who and when is recorded.** A reset from the page records the user; one from Telegram records the chat. Both land in the history with the hours at that moment.
- **Restore Default Tasks** brings back a bundled type you hid, without touching the custom ones.

## :material-alert: Pitfalls and what-ifs

- **Calendar days are the fallback, not the default.** Print hours is what a farm actually wears out; use calendar days for filters and lubricant that age whether or not the printer runs.
- **The offset is per printer and one-off.** It is a correction to what the printer has counted, not a running total; set it once for a used machine and leave it.
- **A type hidden is hidden everywhere.** Deleting a bundled type takes it off every card; **Restore Default Tasks** puts it back for all of them. To silence one task on one printer, disable it on that printer's card instead.
- **Custom types with no model list apply to every printer.** *All models* is the default; narrow it, or the P1S cards grow a rail-oiling task they cannot use.
- **Nothing pauses a printer for maintenance.** Overdue is a colour, not a gate: the queue keeps dispatching. Put the printer in maintenance mode on its card when it must sit out — that *does* take it out of the queue and the auto-queue, and it stays visible.
- **The Telegram button is a reset, not a note.** It closes the task with no text; add the note from the page later if the history needs it.

## :material-link-variant: Related scenarios

- [A night shift with nobody in the shop](unattended-night.md) — maintenance mode is how a machine sits out the night.
- [Keeping the breaker and the power bill in check](power-budget.md) — the plug's power time is not print time; intervals do not care about it.
