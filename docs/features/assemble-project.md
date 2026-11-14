---
title: Assemble Project
description: Lay library models out densely and save ready project 3MF files for your printers
---

# Assemble Project

!!! info "Current development after 0.7.3"
    Assemble project is in the development line after 0.7.3. It is not in the `0.7.3` release image.

Pick models in the [File Manager](file-manager.md), and BamDude lays them out on plates and saves **project 3MF files** next to the sources — one per printer you name, each with the printer, process and filament presets already inside, so it opens in Bambu Studio or OrcaSlicer ready to slice.

The layout is denser than a slicer's own auto-arrange: small parts go **into the holes and hollows of larger ones**. A frame with a lid lying inside it takes one place on the plate, not two.

## :material-cursor-default-click: Starting an assembly

1. Select one or more **STL**, **OBJ** or **STEP / STP** files in the library.
2. Press **Assemble project** in the selection bar.

If the selection holds another kind of file (a sliced 3MF, a G-code file), the button is disabled and its tooltip names the files that do not fit — the dialog never opens on a silently shortened list.

The action needs the right to upload to the library (`library:upload`).

## :material-format-list-numbered: Parts

Each selected file is a row:

| Field | What it does |
|---|---|
| **Copies** | How many of this part to place. Up to 2000 copies in one assembly, all parts together. |
| **Fill a plate** | Instead of a number: as many as one plate takes. A filled part gets a plate of its own. |
| **Orientation** | *As in the file*, a quarter turn about X or Y, or *Upside down*. The part is then put on the bed on its lowest point. |

## :material-printer-3d: Printers

Each printer row is a set of three presets — **Printer**, **Process**, **Filament** — from the same lists the slice dialog uses: your local presets, Orca Cloud, Bambu Cloud and the standard ones. **Add printer** adds another row, up to 8.

Every row produces **its own project**, laid out for that printer's print area and saved with those presets. Assembling for an X1 Carbon and an A1 mini at once gives two files with two different layouts.

- **Two-nozzle printers** (H2D, H2C and similar) show **Print with** — *Left nozzle* or *Right nozzle*. Parts are kept inside the reach of the nozzle you choose, and the project is saved with that nozzle pinned.
- Areas the printer cannot print in are left free.
- A printer preset that does not describe a print area — a model card rather than a machine preset, or a printer that counts its coordinates from the centre of the bed — shows a warning on its row, and **Assemble** stays disabled until you pick another.

No slicer sidecar is needed for assembling. The presets are read by BamDude itself; the standard ones are fetched from the OrcaSlicer profile repository the first time and kept, so a farm without internet keeps working with what it already has.

## :material-tune: Layout

| Setting | Default | Meaning |
|---|---|---|
| **Gap between parts, mm** | 2 | 0 to 50. |
| **Rotation of parts on the plate** | In steps of 90° | *Do not rotate*, *Only by 180°*, 90° or 45° steps. Finer steps pack tighter and take longer. |
| **Centre the group on the plate** | on | Off leaves the parts where the packing put them, starting from the corner. |
| **A separate file for each plate** | off | Off: one multi-plate project. On: a file per plate. |
| **Name of the result** | from the first file | The printer's model is added to the name. A name that is already taken in the folder gets a number, never overwrites. |

## :material-progress-clock: While it runs

Assembling is a background job in its own worker; you can close the dialog and keep working — the job tracker in the corner follows it and tells you when it is done.

The dialog shows where the job is: waiting behind another assembly, converting STEP files, placing parts for each printer, saving. **Stop** ends it and saves nothing. Once the job has started saving files it can no longer be stopped — a stop at that moment would leave files behind a message saying nothing was saved.

One assembly runs at a time; the next ones wait in a queue.

## :material-check-circle-outline: The result

The summary lists every printer with a **picture of each plate**, how many of each part landed where, and a link to each saved file. The files appear in the folder of the first selected model.

- A part that fits no plate of a printer — too large for its area, or taller than it prints — fails **that printer only**, and is named with the reason. The other printers still get their projects.
- A printer row whose preset could not be read fails alone, too.
- When you closed the dialog and something did not work out for one of the printers, the tracker asks you to acknowledge it instead of showing a green "done".

## :material-cube-scan: STEP models

A STEP or STP file is converted on the server before packing, at the precision Bambu Studio imports STEP with, so round surfaces stay round. It needs the same optional component as [STEP thumbnails](file-manager.md#step-thumbnails): the Docker image and the Windows installer carry it, a native install chooses it at install time. Without it, a selection with a STEP file is refused with a message saying so, and STL / OBJ assemblies work as usual.

The conversion is strict on purpose. A model is taken only whole: a file that refers to geometry in another file, a surface that is not a closed body, a mirrored assembly the kernel cannot reproduce, or a model too detailed for the limits stops the assembly and **names the part** — a layout is never made without one of the parts you asked for. A STEP file may be up to 64 MB.

## :material-refresh: Re-layout

A project assembled here remembers what it was made from: the parts, their quantities, the presets and the layout settings. Its menu has **Re-layout**, which opens the same dialog with those values — change a quantity, the gap or the rotation and lay it out again. The models come from the project itself, so the original STL / STEP files may already be gone.

- **Move the previous file to the trash** (on by default) replaces the old project. It needs the right to delete that file; a file a print job is using is kept. A file in a linked external folder has no trash — it is removed from the library and stays on its share, and the summary says so.
- For a project saved as a file per plate, re-layout works on the whole set and needs every file of it in the library.
- A sliced copy of the project does not carry these values, so it has no **Re-layout**.

## :material-ruler: Limits

| | |
|---|---|
| Files in one assembly | 100 |
| Copies in total | 2000 |
| Printers | 8 |
| Source files together | 200 MB |
| One STEP file | 64 MB |
| Time for one assembly | 15 minutes |
| Assemblies waiting in the queue | 16 |

Single-filament projects only: every part is saved with the one filament preset of its printer row.

## :material-help-circle-outline: When something fails

| Message | What to do |
|---|---|
| *Some parts do not fit this printer* | The named part is larger or taller than the printer's area. Turn it with **Orientation**, or leave that printer out. |
| *The STEP file could not be converted into a printable model* | Open it in your CAD program or slicer and export it as STL, or as a STEP with all geometry embedded. |
| *The STEP model is too large or too detailed to convert* | Export it as STL at the precision you need. |
| *STEP support is not installed on this server* | Install the STEP preview component — see [Installation → STEP previews](../getting-started/installation.md#step-previews). |
| *A source file changed while the project was being assembled — nothing was saved* | The file was replaced during the job. Start again. |
| *Assembling took too long and was stopped* | Fewer copies, coarser rotation steps, or fewer printers in one go. |

The state of the assembly worker is reported with the other workers by `GET /api/v1/system/info` (`assembly_worker`) and is part of a support bundle.
