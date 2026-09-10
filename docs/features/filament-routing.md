---
title: Filament Routing
description: Choose AMS or external feeds, preserve color requirements, and understand waiting jobs across Auto-Queue, printer queues, projects, and reprints
---

# Filament Routing

BamDude checks **every filament channel used by the selected plate** before assigning a sliced 3MF to a printer. The printer model alone is not enough: two printers of the same model may have different AMS units, external spools, or nozzle configurations.

These rules apply when adding work through [Auto-Queue](auto-queue.md), [printer queues](print-queue.md), [order plans](projects.md), library files, archives, and queue-mode [virtual printers](virtual-printer.md).

## Choose the source {#source}

In the Auto form, **Filament source** offers:

| Choice | What may supply the plate |
|---|---|
| **Automatic: AMS or external spool** | Any complete supported combination of AMS and external feeds. |
| **AMS only** | Every used channel must have a suitable AMS source. |
| **External spools only** | Only supported external feeds, including on a printer that also has AMS connected. |

Automatic source does not mean that an empty AMS slot or an unknown configuration is acceptable. Each used channel needs a loaded source with the required material and the correct nozzle binding. A known filament variant also matters: matching `PLA` alone does not make known PLA Basic and PLA Matte interchangeable. An explicit material override changes the requirement for that channel; allowing a different color does not.

An explicit physical slot selection stays tied to that printer and source. BamDude does not silently replace it with another tray or external spool.

## Decide which colors matter {#colors}

**Force exact color match** is off by default. With it off, exact colors are preferred, but another color of the required material may be used. Turning it on requires the colors for every used channel.

For a mixed requirement, set a channel's color and tick **Require this color**. That channel stays color-constrained even when the global switch is off. For example, a visible logo can require red while another channel may use whichever suitable color is loaded.

The number of copies never changes these rules. A batch of one and a batch of one hundred use the choices you made; there is no automatic “mass production” mode that grants permission to change colors.

## Multiple channels and nozzles {#channels}

**Multicolor jobs can use Auto-Queue.** Every used channel needs a distinct physical source, even if two channels have the same material and color. Turning off exact color matching does not combine them into one channel.

| Plate and available printer | Result |
|---|---|
| One PLA channel; matching model with one loaded external PLA spool | Can route with automatic or external-only source rules, subject to color and nozzle requirements. |
| Two channels; a single-nozzle printer with one external spool and no AMS | Cannot route: one spool cannot supply both channels automatically. |
| Two channels on one nozzle; enough suitable AMS slots | Can route when each channel has its own compatible slot. |
| A supported dual-nozzle printer; AMS on one nozzle and external on the other | Can route when the file and current printer state establish those nozzle bindings, with automatic source rules. |
| A supported dual-nozzle printer; one external feed for each nozzle | Can route if the plate uses those two feeds and both meet its requirements. |

Dual-nozzle support follows the printer's capabilities; it is not limited to one model. Two available spools do not help if they feed the wrong nozzle. Missing nozzle or feed information causes a wait or a source error, depending on which information is missing.

Only channels actually used by the selected plate count. An unused color in the 3MF does not add a requirement, but a channel with a very small positive usage still counts.

## Read the compatibility preview {#preview}

The Auto form groups printers by **model, nozzle count, and AMS state**:

- **AMS connected**;
- **Without AMS**;
- **AMS state unknown**.

For example, ten P2S printers with AMS fitted on only five appear in separate configuration groups. P1P, P1S, and P2S remain separate models; a similar name is not a model match.

**Compatible** means the loaded sources can satisfy the whole plate under its rules. **Ready** also accounts for the printer's current state. Plate-clear confirmation, drying, and staggered start can hold a compatible job; see [Routing is not dispatching](auto-queue.md#routing-is-not-dispatching).

The preview does not reserve a printer. A valid file can be queued with zero compatible or ready printers, or when live compatibility is temporarily unavailable. It waits for suitable conditions. Unknown AMS state is never treated as proof that no AMS is connected.

## Plate selection and source errors {#plates}

Requirements come from the selected plate in the sliced 3MF and its matching G-code. For a multi-plate file, choose the plates explicitly. **Whole file** is accepted only when one printable plate can be identified unambiguously; its actual number is preserved, even if it is not plate 1.

A missing selected plate, missing G-code, unreadable filament usage, or missing required nozzle bindings blocks adding the job. Recheck the file or re-slice it with the correct model and plate. Loading a spool cannot repair missing file information.

Order plans use the same check before creating queue items. A product recipe may keep its **Whole file** selection while the queued print receives the resolved plate number. Counts, order-line attribution, and the chosen alternative file stay with that work.

## What happens before printing {#before-printing}

The server checks the source and routing before preparation and again immediately before sending the start command. If the spool, printer connection, file, or ownership of the pending job changes, an attempt can be deferred.

- A queued job returns to waiting with a reason. Check that reason, the printer's reported feed state, and the saved requirements.
- A refused **Print Now** attempt does not create a hidden future print.
- Preparation that never starts a print is excluded from print and production totals, and the original source file is retained.

The slot mapping actually sent to the printer is used for filament attribution. “Drain the emptiest spool first” ranks suitable sources only after the complete requirements are met; it does not override color pins, material, nozzle, or source restrictions. Its [AMS Filament Backup gate](print-queue.md#ams-filament-mapping) still applies.

## Edit, copy, retry, and repeat {#editing}

Each printer-queue item keeps its own routing rules after Auto-Queue assigns it. Removing the original Auto-Queue row does not remove those rules. Changing only the schedule, cloning, retrying, or repeating retains them.

Moving a manually mapped job to another printer or plate requires a new mapping answer. A tray number on one machine does not identify a spool on another. In grouped additions, channel-specific choices belong to the current file: the next file opens for review instead of silently inheriting those choices.

After upgrading, older jobs keep restrictions that can be established from their saved data. An explicit external-only choice stays external-only; a saved physical AMS mapping remains physical intent. Missing or unrecognized routing evidence requires review rather than a guessed mapping.

Raw G-code and server-created calibration jobs have separate workflows. Their special handling does not bypass validation for an ordinary sliced 3MF.
