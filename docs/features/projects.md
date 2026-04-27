---
title: Projects & Print Plan
description: Group prints into projects with an ordered print plan, BOM tracking, and ZIP / JSON export
---

# Projects & Print Plan

Projects are the way to group a set of related prints — a model with multiple parts, a small batch you'll re-run for clients, an inventory of parts to keep stocked. Each project carries:

- An **ordered print plan** of `.gcode.3mf` files from your library
- A **copies stepper** per file (how many of each to run)
- **Per-row totals** (filament weight, time, energy, cost) and a project-level grand total
- An optional **BOM** (filament type / colour / grams budgeted)
- **Cross-install export** as a ZIP bundle or a JSON manifest

## :material-folder-multiple: Creating a project

1. Open **Projects** in the side nav.
2. **+ New Project**, name it, and (optionally) describe it.
3. Save — you land on the project detail page.

A new project starts empty. Add files by either:

- **Linking a folder** — set the project on a File Manager folder; every file inside gets `project_id` set, plus any file moved into the folder later inherits the link.
- **Linking individual files** — each file row in File Manager has its own "Link to project" button.

Linked files appear automatically as plan items at copies = 1 each.

## :material-playlist-edit: The print plan

The plan is a flat, ordered list of items. Each row carries:

| Column | Meaning |
|---|---|
| **Sequence** | The print order. Drag-and-drop to reorder. |
| **File** | Which 3MF from the library (link goes to its File Manager card). |
| **Copies** | How many copies to run — bumped via the stepper or typed. |
| **Time** | Total time this row (slicer estimate × copies). |
| **Filament** | Total grams across copies, broken down by colour/material if multi-spool. |
| **Cost** | Filament cost × copies, plus energy cost if a smart plug is bound. |
| **Status** | Per-row progress: how many copies have been completed (driven by the archives that link back to the file). |

The grand-totals strip at the bottom sums every row — useful for "do I have enough green PLA on hand for this project?" sanity checks before you click dispatch.

## :material-cart-check: Bill of Materials (BOM)

Each project also accepts a freeform BOM — entries for filament types, colours, and gram budgets you intend to consume. The BOM doesn't auto-deduct from spools (that's what the per-print spool consumption tracking is for); it's a planning aid for "I need 480 g of black PLA + 120 g of grey TPU" so you can compare against current spool stock before you commit.

## :material-rocket-launch: Dispatching the plan

Two paths:

| Action | Effect |
|---|---|
| **Add row to queue** | Sends just that file (× the row's copies) to a printer's queue. |
| **Dispatch entire plan** | Adds every row, in order, to the chosen printer's queue. Per-row copies become individual queue items so you can still cancel / reorder copies after dispatch. |

Plan items are not re-dispatched automatically when their archive completes — finishing a row just bumps its completed counter. To re-run the project, dispatch again.

## :material-tray-arrow-down: Export & import

Projects are portable across BamDude installs.

- **JSON manifest** — small file, lists files by hash + the print plan + BOM. Useful for sharing the *recipe* of a project. The receiving install needs the matching `.3mf` files in its library (otherwise rows show as "missing file").
- **ZIP bundle** — the JSON manifest plus a copy of every referenced 3MF, so the receiving install can re-create the project even if its library is empty.

Import is symmetric: open Projects → Import, drop the file, pick whether to keep existing matches by hash or upload the bundled copies as new library files.

## :material-database: Behind the scenes

The schema (m016) splits state across two tables:

- `projects` — name, description, owner.
- `project_print_plan` — the ordered plan, with per-row `(library_file_id, copies, sequence, notes)`.

Plan rows are FK'd to `library_files` with `ON DELETE SET NULL` (m018) — deleting a file referenced by a plan blanks the row out instead of cascading the project deletion. Archives that came from the file still carry their `library_file_id` link (set NULL on file delete) so completed-copy counters keep tracking even after the source file is gone.

Per-row completed counts are computed on read from `print_archives` rather than stored on the plan row. Reprints, plate-by-plate dispatches, and dedup-by-hash all increment the row consistently — no drift between the live plan and historical archives.
