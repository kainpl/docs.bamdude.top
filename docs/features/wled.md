---
title: WLED
description: WLED lights show each printer's status
---

# WLED

A [WLED](https://kno.wled.ge/) controller beside a printer can show what the printer is doing — idle, printing, paused, finished, failed, waiting for its plate, short of filament, an HMS fault, offline — so the farm reads its state across the room, with no screen and no Home Assistant in between.

Colours, effects and segments stay in WLED. BamDude only switches the **presets** you saved there.

---

## :material-lightbulb-outline: Prepare the presets in WLED

1. Open the WLED controller's own page and create one preset for each state you want to show.
2. If the strip has several segments, select the segment the preset should change and turn on **Checked segments only** when you save the preset, so it leaves the other segments alone.
3. Note the WLED address (for example `http://192.168.1.60` or `http://wled-x1c.local`).

---

## :material-cog: Map the states

Open **Settings → WLED** (you need the right to edit printers).

1. Pick the printer.
2. Turn on **Enable WLED integration** and enter the **WLED URL**. **Test connection** shows the name and version WLED reports.
3. **Load presets** reads the presets saved in WLED. Choose one for each state, or leave **Disabled — no preset**. **Test** shows a preset now without saving it; the next status update brings the mapped one back.
4. Optionally set **Finished timeout (seconds)**: after that long on Finished, the light switches to the Idle preset. 0 turns it off.
5. Save.

When WLED is not reachable, the preset numbers you saved are kept and the page says so.

The address must be an `http://` or `https://` address on your network; an address with a login in it is refused.

---

## :material-swap-vertical: Which preset shows

On every status update BamDude takes the first state that applies **and has a preset**, in this order:

| State | When |
|---|---|
| **Offline** | the printer is not connected |
| **Filament problem** | the printer paused because the filament ran out |
| **HMS error** | the printer reports an HMS fault |
| **Awaiting plate clear** | the printer is idle, finished or failed and its queue waits for the plate to be cleared |
| **Failed / Error** · **Paused** · **Finished** · **Printing** · **Preparing** · **Idle** | the printer's own state |

A state without a preset falls through to the next one that has one: a filament runout without its own preset shows **Paused**. When nothing that applies has a preset, the light is left as it is.

!!! note "Awaiting plate clear"
    It shows only while the printer's own **Require plate-clear confirmation** (Edit Printer) holds the queue. A printer that does not require it never shows it.

!!! note "HMS error"
    The light counts the same faults the printer card shows. A notice a printer keeps through a whole print — the top cover open while printing PLA, «chamber hot, fan speed increased» — keeps the light on HMS error for that print. To show printing instead, hide that entry on that printer: **Hide until it goes away** in the printer's HMS list. The card, the camera wall, notifications and the light go quiet together, and the entry comes back when the printer reports it anew.

A printer you disconnect, put in maintenance mode (**Enter maintenance mode**) or archive shows its **Offline** preset; so does an inactive or archived printer when BamDude starts.

If WLED stops answering, BamDude keeps working: it logs the outage once, tries the same preset again at most every 30 seconds, and logs once when WLED answers again.
