---
title: A night shift with nobody in the shop
description: The auto-queue keeps the printers fed, swap mode clears plates, the alarms that matter get through quiet hours, and a failing print pauses itself
---

# A night shift with nobody in the shop

## :material-map-marker-question: The situation

The last operator leaves at 22:00 and the first one is back at 07:00. Nine hours is two or three prints on most of the forty-eight machines — if somebody clears the plates. Nobody will. Left alone, the farm prints one plate per printer and waits for a hand that arrives at seven; left alone *badly*, a spaghetti print runs for six hours on a machine nobody is watching.

## :material-flag-checkered: The goal

Every printer that can run unattended runs all night: the auto-queue keeps handing out work, plates are cleared by a swapper where there is one, a failing print stops itself, and exactly the events that need a human wake one — through a phone that is otherwise silent.

## :material-puzzle: What is involved

| Feature | Its part |
|---|---|
| [Auto-queue](../features/auto-queue.md) | The pile of tonight's work; the router feeds each printer as it frees up. |
| [Plate-clear confirmation](../features/print-queue.md#clear-plate-confirmation) — per printer | Off on the machines that can go on by themselves, on where a human must look at the bed first. |
| [Swap mode](../features/swap-mode.md) | The plate swapper on the A1 minis: no confirmation, the next print starts by itself. |
| **Only run if the previous print succeeded** | A gate on the queue row: a printer whose last print failed is not handed the next one. |
| [Obico AI failure detection](../features/obico.md) | Watches the camera; a sustained failure pauses the printer, or pauses it and cuts its power. |
| [Notifications → through the night](../features/notifications.md#getting-an-action-required-event-through-the-night) | A separate provider for the alarms, with no quiet hours. |
| [Smart plugs → Auto Power Off](../features/smart-plugs.md#auto-power-off) | Powers down what has nothing left to do. |

## :material-format-list-numbered: Step by step

1. **Decide which printers run unattended.** On the edit form of each: **Require plate-clear confirmation** *off* for the swap-mode A1 minis and for the machines whose parts pop off a cold PEI sheet by themselves; *on* for the rest — those print one plate tonight and wait. A printer in maintenance mode or with a paused queue gets nothing either way.

2. **Turn the swappers on.** **Settings → Queue → Swap Mode** for each A1 mini, with the swap profile that matches the hardware. The swap macros run after every print BamDude dispatched; the confirmation is bypassed; the next print starts.

3. **Fill the auto-queue.** From an order's plan (**× N to queue**, see [A hundred parts across five printer models](one-part-five-models.md)), the print dialog's **Auto** target, or files dropped on the Auto-Queue panel. Tick **Only run if the previous print succeeded** on the rows that must not be printed onto a failed bed.

4. **Give the AI the night watch.** **Settings → Integrations → Obico AI**: enable, **Sensitivity** medium, **Action on sustained failure** `pause_and_off` for printers with a power plug, `pause` for the others, and **Enabled printers** — all of tonight's. **Settings → Network → External URL** has to be set, or the loop refuses to start.

5. **Route the alarms.** Two providers in **Settings → Notifications**: the everyday one, with quiet hours 22:00–07:00 and *print complete*, *progress* and the rest; and an **alarm** provider with **no** quiet hours and only the events that stall the farm or need a person — *print failed*, *printer error*, *plate not empty*, *AI failure detection*, *queue job waiting*. On iOS a Bark provider at **Critical** is the loud version. Telegram gets the same events with **Clear plate** on the failed-print message.

6. **Let the plugs handle the end.** **Auto Power Off** on the printers' plugs, cooldown at the default 50 °C. It will not fire while the printer's queue still holds work — so it powers down exactly the machines that have finished their night.

7. **Read the morning.** The Queue page: what ran, what is waiting on a plate clear, what a failure held back. Press **Clear Plate & Start Next** on the row of printers that were told to wait; **Unskip** on the one whose neighbour failed and whose gate held its queue.

## :material-cogs: What BamDude does on its own after that

- **The router feeds each printer as it empties.** A printer is busy while a print runs *or* its queue holds a pending row, so each machine gets one job at a time and the next when that one is gone. Every start still passes plate-clear, the staggered-start slot, drying and the filament check.
- **A swap-mode printer chains prints.** Print ends → `swap_mode_change_table` macro → no confirmation → next print. A cancelled or failed print **always** waits for confirmation instead: the part, or its remains, is still on the bed, and swapping it would jam the rig — the queue stopping there is the safe outcome.
- **A printer whose last print failed is skipped, not stopped.** With the gate on, the router walks past that printer and gives the work to another; the row it would have taken waits with *Previous print failed* on it. Only if *every* candidate has failed does the item wait for a printer. A print you cancelled yourself is neutral — cancelling is a decision, not a failure.
- **Obico watches after warm-up.** The first thirty frames of a print are trusted for nothing (about five minutes); after that a smoothed score, not one frame, decides. On a sustained failure the printer pauses, the *AI failure detection* event fires with the confidence and the action taken, and with `pause_and_off` the plug is cut after a short delay so the printer writes its state cleanly.
- **The auto-queue says why it is stuck.** A tick that could place nothing logs the reason and sends *queue job waiting* once per cause — *waiting for filament: A1M-03 (needs PETG)* — rather than staying silent until seven.
- **Plate-clear and stagger keep working with nobody there.** An unattended printer waiting for confirmation waits *visibly*, with its row on the Queue page and its button on the card; nothing is dispatched onto it.

## :material-alert: Pitfalls and what-ifs

!!! warning "Quiet hours drop everything, including the alarms"
    Quiet hours are per **provider**, not per event: a provider that is quiet from 22:00 will not tell you the queue stalled at 01:00, whatever events it subscribes to. The alarm events need a provider of their own with quiet hours off. There is no per-event bypass.

- **A print started on the printer's screen breaks the swap chain.** The swap macro runs only for prints BamDude dispatched; a print begun on the touchscreen leaves the plate where it is, and BamDude then asks for a manual **Clear Plate** — the printer looks idle while its queue does not advance. Start night work from BamDude.
- **`pause_and_off` needs the plug marked as the printer's power plug** — the one with **This plug powers the printer** on. An accessory plug is never switched to cut a printer.
- **A paused printer is never powered off by auto-off**, and a paused print blocks nothing else; it waits for the morning. That is the point of `pause` over `stop`: the part is still recoverable when a person looks.
- **The bed-occupancy camera check** (`plate_not_empty`) pauses dispatch when it sees a part still on the bed — a good gate on a non-swap printer, and one more thing to answer at seven.
- **Filament runs out at three in the morning.** A printer with **AMS Filament Backup** carries on from the twin spool; one without pauses on runout, which is a *print paused* event on the alarm provider if you want to be told.
- **Nothing here overrides stagger.** The night runs under the same slot cap; a farm that staggers hard finishes fewer prints by morning, and the breaker stays in.

## :material-link-variant: Related scenarios

- [An urgent print ahead of the queue](urgent-print.md) — the same busy rule, used by hand.
- [Keeping the breaker and the power bill in check](power-budget.md) — auto-off and stagger in detail.
- [A camera wall on the workshop TV](camera-wall-tv.md) — for the person who does come in at three.
