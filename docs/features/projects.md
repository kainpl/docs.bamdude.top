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

## :material-format-list-checks: Use cases

| Project | What goes in it |
|---|---|
| **Voron Build** | Frame plates + electronics enclosure + tools + spare wear parts. Track plate progress vs total parts so you know when the kit is print-complete. |
| **Gift Set** | A handful of unrelated prints (vase + planter + keychains) that ship together for a birthday. Use cover image + URL pointing at the order email. |
| **Customer order** | 10 copies of the same model for a client. Set Target Plates × copies on the plan row; the live counter tells you how many are left. |
| **Calibration suite** | Test prints for a new filament — flow ratio, temp tower, retraction tower. Group them so the calibration archives don't pollute the main archive list. |
| **Single big print** | One model with one large 3MF — still useful for a project so the cover image, URL, and BOM live next to the print. |

---

## :material-folder-multiple: Creating a project

1. Open **Projects** in the side nav.
2. **+ New Project**, name it, and (optionally) describe it.
3. Save — you land on the project detail page.

A new project starts empty. Add files by either:

- **Linking a folder** — pick one or more projects on a File Manager folder via the chip multi-select; every file inside gets attached to the same project list, plus any file moved into the folder later inherits the link.
- **Linking individual files** — each file row in File Manager has its own "Link to project" button that opens the same chip multi-select.

A library file (or folder) can belong to **multiple projects at once** — the link is many-to-many (m044). The same file in N projects shows up as N independent plan rows, each with its own `copies` and `order_index`. Linked files appear automatically as plan items at copies = 1 each per project.

To remove a single association without affecting the rest, click the small `×` on the relevant project chip in the file/folder edit dialog (or use the per-row "remove from project" button on the project detail page) — both go through the dedicated `DELETE /library/{files|folders}/{id}/projects/{project_id}` endpoint, so a file in 3 projects can be detached from 1 without read-modify-write on the whole list.

## :material-content-duplicate: Duplicating a project

**Duplicate** on a project copies its *setup* into a new project and leaves its *history* behind — the point being that you are about to run the same build again, for a second machine or another customer.

Copied: the print plan (every row with its copies and order), the file and folder links, the BOM, both targets, the description, notes, attachments, tags, due date, priority, budget, colour, cover image and URL. Not copied: the archives, which belong to the prints that actually happened.

Two things are deliberate rather than incidental:

- **The copy is always `active`**, whatever the original was. Duplicating a completed or archived project is new work about to start — that is the whole reason to do it.
- **A duplicate of a template is another template.** The flag describes what the project *is*, not what has happened to it.

Give the copy a name or let BamDude pick one; it lands as a **sibling** of the source, under the same parent. Sub-projects come along only if you ask (`include_children`), and a parent cycle cannot make it loop.

```http
POST /api/v1/projects/{id}/duplicate
{ "name": "Voron #2", "include_children": true }
```

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
| **Printed / Remaining** | Per-row progress: `✓N` shows how many copies of this file have completed inside this project (only `status='completed'` archives count — failures/aborts/external prints don't decrement); `📋M` shows `max(0, copies − printed)` remaining work. The progress is keyed by `(project_id, library_file_id)`, so a file in two projects has independent progress in each. |

The grand-totals strip at the bottom sums every row — useful for "do I have enough green PLA on hand for this project?" sanity checks before you click dispatch.

The three headline stat cards at the top of the project detail page (Print Jobs / Print Time / Filament Used) carry a second-line "remaining" subtitle driven from the same plan rows: jobs sums `remaining_count`, time sums `print_time_seconds × remaining_count`, filament sums `filament_grams × remaining_count`. The subtitle is **green** when the plan is fully delivered (`всі надруковано` / `all printed`) and **amber** otherwise — a glance tells you whether the project still has work to do.

## :material-link-variant: External URL & cover image

Each project can carry an external URL plus a hero cover image — both surface on the project card and on the detail page so a glance tells you "this is the rocket-shelf project" instead of staring at a generic folder icon.

| Field | Notes |
|---|---|
| **URL** | Free-form `http://` or `https://` link, capped at 2 048 chars. Validated on save (anything that doesn't start with `http(s)://` is rejected inline). Edit-with-cleared-value sends `null` so the column actually clears. Surfaces as a clickable `↗` icon next to the project name on cards and the detail page. |
| **Cover image** | 80 × 80 preview in the project modal, full-size on the detail page hero strip + as a thumbnail strip on the cards grid. Accepts `.jpg / .jpeg / .png / .gif / .webp`. **Edit-mode only**: a brand-new project has no `project_id` yet, so the upload widget appears after the first save (matches upstream's shape). The preview URL is cache-busted on every upload/remove so you don't have to hard-refresh to see the new image. |

Typical use: paste the MakerWorld / Printables / Thingiverse link the model came from into URL, drop a photo of the assembled product into Cover. Future-you will thank present-you when revisiting a project a year later.

## :material-target: Target Plates vs Target Parts

A project can carry two independent progress counters:

| Target | Counts |
|---|---|
| **Target Plates** | Number of distinct print jobs (each time you click Print = +1). |
| **Target Parts** | Total objects across all jobs (a plate with 4 copies of a bracket = 4 parts). |

Set both for a multi-plate build that ships a precise count of objects, e.g. a Voron BOM might be 25 plates / 150 parts. The project card surfaces dual progress bars:

```
Plates  [████████░░░░░░░░░░] 40%   2 of 5 print jobs
Parts   [████████░░░░░░░░░░] 40%   10 of 25 parts
```

### Pre-fill from the print plan

You don't have to add up the numbers manually. Two zero-friction shortcuts feed the targets from the plan rows:

- **Edit modal** auto-pre-fills empty Target Plates / Target Parts inputs with the plan totals on open, and shows a `From plan: N` link under each input — click to re-sync after the plan changed (link hides when the input already matches).
- **`Apply to project`** button on the print plan totals row + the BOM totals row writes Target Plates (= sum of plate copies), Target Parts (= total objects), AND Budget (= filament cost + materials cost) onto the project in one click. Tooltip shows the exact values that will land before the click. The button hides when the project already matches all three (no-op write avoidance).

Manual edits still win — once you change a value, the auto-fill won't overwrite it on subsequent modal opens. Use the `Apply to project` / `From plan: N` controls when you've reworked the plan and want the project numbers to follow.

### Auto-detection from 3MF

When an archive lands, BamDude reads `slice_info.config` from the 3MF, counts the non-skipped objects, and stamps that count onto the archive's `quantity` column automatically. A plate with 4 instances of a bracket → archive quantity 4 → project parts counter +4.

### Manual quantity override

Open the archive in edit mode and set **Items printed** to the right number — handy when the slicer config disagreed with reality (e.g. you skipped 2 of 4 objects mid-print). The project parts counter recomputes immediately.

### Defective parts

A print archive records how many objects were on the plate. It now also records how many of them came out **unusable** — warped, under-extruded, snapped on removal. Set the scrap count on the archive and the project's parts tally is net of it.

This matters because a project that needs forty usable parts is not finished when forty come off the plates. Without it, the counter reaches the target and the work is not done. The project card shows the defective figure alongside the total, so a run that is quietly producing scrap is visible before you reach the end of it.

!!! tip "A target of zero means 'don't measure it this way'"
    If you work strictly to a number of parts, set **Target Plates** to `0` and the plate progress bar disappears instead of sitting there at a number nobody is tracking. The same works the other way round.

---

## :material-palette: Color coding

Each project carries a colour badge for visual identification across the UI:

- :material-circle:{ style="color: #f44336" } Red
- :material-circle:{ style="color: #ff9800" } Orange
- :material-circle:{ style="color: #ffeb3b" } Yellow
- :material-circle:{ style="color: #4caf50" } Green
- :material-circle:{ style="color: #2196f3" } Blue
- :material-circle:{ style="color: #9c27b0" } Purple
- :material-circle:{ style="color: #607d8b" } Grey

Badges show on the project card, on every archive card linked to the project, and as a chip-filter on the Archives page.

---

## :material-view-dashboard: Project card

Each project displays as a card with progress + quick stats:

- **Color badge + name** — primary identifier
- **Cover image thumbnail** strip if a cover is uploaded
- **Plates progress** bar with raw "2 of 5" text
- **Parts progress** bar with raw "10 of 25" text
- **Print-time elapsed** — sum of every linked archive's logged print duration
- **Last activity** — timestamp of the most recent linked archive
- **File count** — how many library files are linked to this project
- **External URL** icon (if set) — clickable :material-arrow-top-right:

---

## :material-folder-arrow-down: Adding archives to projects

In addition to folder-link / per-file-link auto-population, you can attach archives manually:

- **Right-click** any archive card → **Add to project** → pick the project. Same gesture works on archive list rows.
- **Bulk assignment** — click **Select** on the Archives page (or hold Shift/Ctrl while clicking), pick multiple archives, then click **Project** in the bottom toolbar. Same modal has **Remove from project** to bulk-detach.

The project picker on individual archive detail pages auto-saves on selection — no separate Save click.

---

## :material-filter: Filtering archives by project

The Archives page has a project chip-filter at the top. Click any project chip to narrow the grid to just that project's archives. Combine with the date / printer / status filters to slice further.

---

## :material-printer: Printing files from a project

If a project links one or more library folders, the project detail page lists every printable file inline — no detour through File Manager.

Each plan-row gets two inline action buttons (only on `.gcode` and `.gcode.3mf` files):

- :material-play: **Print Now** — opens the print dialog (printer picker + AMS mapping + options) and dispatches.
- :material-calendar-plus: **Add to Queue** — opens the schedule dialog to add to the queue.

**Auto-linking.** Prints triggered from the project detail page auto-attach the resulting archive back to this project. No "Assign to project" step. Reprints from elsewhere (Archives / File Manager / direct link) are **not** auto-linked — only the project-page launch creates the implicit association.

---

## :material-cart-check: Bill of Materials (BOM)

Each project also accepts a freeform BOM — entries for filament types, colours, and gram budgets you intend to consume. The BOM doesn't auto-deduct from spools (that's what the per-print spool consumption tracking is for); it's a planning aid for "I need 480 g of black PLA + 120 g of grey TPU" so you can compare against current spool stock before you commit.

## :material-rocket-launch: Dispatching the plan

Two paths:

| Action | Effect |
|---|---|
| **Add row to queue** | Sends just that file (× the row's copies) to a printer's queue. |
| **Dispatch entire plan** | Adds every row, in order, to the chosen printer's queue. Per-row copies become individual queue items so you can still cancel / reorder copies after dispatch. |

Plan items are not re-dispatched automatically when their archive completes — finishing a row just bumps its completed counter. To re-run the project, dispatch again.

---

## :material-archive-arrow-up: Project archives view

Open any project to land on the detail page. The **Archives** sub-tab shows just the archives linked to this project — same filtering / sorting as the main Archives page, but pre-filtered. Useful for jumping into "show me all the prints from the Voron build" without typing a search.

---

## :material-paperclip: File attachments

A project can also carry reference files that aren't the print itself — assembly instructions, datasheets, photos, parametric source.

| Category | Extensions |
|---|---|
| **3D files** | `.3mf`, `.stl`, `.step`, `.f3d`, `.scad`, `.obj` |
| **Documents** | `.pdf`, `.md`, `.txt`, `.doc`, `.docx` |
| **Images** | `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.svg` |
| **Other** | `.zip`, `.json`, `.yaml`, `.gcode`, `.cfg` |

Upload via drag-drop into the project detail page's Attachments section, or click **Upload** to pick a file. Attachments are stored alongside the project and shipped in ZIP exports.

---

## :material-currency-usd: Cost tracking

The grand-totals strip and per-row Cost column compute three categories:

| Category | Source |
|---|---|
| **Material** | Filament weight × spool cost (from Inventory) per linked archive. |
| **Energy** | kWh delta from a bound smart plug × your configured tariff (Settings → General). |
| **Labor** | Manual hours you log against the project (optional) × your configured hourly rate. |

Material + energy are computed automatically from the underlying archives. Labor is freeform — type how many hours you spent post-processing / packaging / shipping and the rate is pulled from project settings.

---

## :material-delete: Deleting projects

Hit the trash icon on a project card and confirm. Deleting a project does **not** delete the archives or library files linked to it — they stay in the main Archives / Library, just without a project association.

If you want a hard cascade ("delete the project AND every archive AND every library file linked to it"), an admin can use the cascade option in the deletion modal. Default is preserve-archives.

## :material-tray-arrow-down: Export & import

Projects are portable across BamDude installs.

- **JSON manifest** — small file, lists files by hash + the print plan + BOM. Useful for sharing the *recipe* of a project. The receiving install needs the matching `.3mf` files in its library (otherwise rows show as "missing file").
- **ZIP bundle** — the JSON manifest plus a copy of every referenced 3MF, so the receiving install can re-create the project even if its library is empty.

Import is symmetric: open Projects → Import, drop the file, pick whether to keep existing matches by hash or upload the bundled copies as new library files.

## :material-database: Behind the scenes

The schema splits state across three tables:

- `projects` — name, description, status, color, target counts, notes, attachments, tags, due date, priority, budget, plus self-FK `parent_id` for sub-projects and a `is_template` flag. Projects do **not** carry an `owner_id` — they're install-wide objects, gated by the `projects:*` permission set rather than ownership.
- `library_file_projects` + `library_folder_projects` (m044) — pivot tables linking library files / folders to projects, both with composite primary key `(file_id, project_id)` / `(folder_id, project_id)` and `ON DELETE CASCADE` on every FK. The legacy single-FK `library_files.project_id` and `library_folders.project_id` columns were dropped in m044; library code reads / writes the M2M relationship instead.
- `project_print_plan_items` (m016, reshaped by m044) — the ordered plan, one row per `(project_id, library_file_id)` thanks to the m044 unique constraint reshape from `(library_file_id)` → `(project_id, library_file_id)`. Columns: `copies` and `order_index`. Per-row "notes" / "sequence" don't exist as columns — sequence is `order_index`, and notes belong on the project itself.

All FKs are `ON DELETE CASCADE`. Deleting a project removes its pivot rows + plan rows; deleting a library file removes its pivot rows + plan rows. Archives that came from the file are independent — `print_archives.library_file_id` is `ON DELETE SET NULL` (m018, separately) so completed-copy counters keep tracking even after the source file is gone.

Per-row completed counts (`printed_count` / `remaining_count`) are computed on read with one bulk `SELECT library_file_id, count(id) FROM print_archives WHERE project_id = ? AND status = 'completed' GROUP BY library_file_id` per request — no N+1 traffic, and reprints / plate-by-plate dispatches / dedup-by-hash all increment the right row consistently. The `project_id` column on `print_archives` keeps the count scoped to the project, so a file shared across two projects gets two independent printed counters.
