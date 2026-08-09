---
title: File Manager
description: Browse and manage your local library of print files
---

# File Manager

Browse, upload, and manage files in your local BamDude library. Print directly or add to queue.

---

## :material-folder: Overview

The File Manager lets you:

- **Browse** files in your local library
- **Mount external folders** from NAS, USB, or network shares
- **Upload** files including ZIP archives
- **Print directly** to any printer
- **Add to Queue** sliced files for later printing
- **Rename** and **delete** files and folders

---

## :material-folder-multiple-outline: Sidebar navigation

The folder tree on the left is the primary navigation. Click any folder to enter it; click the breadcrumbs at the top of the file area to step back. Two small toggles in the sidebar header tailor the rendering — both preferences are stored in your browser and applied on every subsequent page load.

| Toggle | What it does |
|---|---|
| **Wrap** | When off (default), long folder names are truncated with an ellipsis. When on, long names wrap across multiple lines so the full name stays visible. |
| **Collapse** | When off (default), the folder tree opens with every level expanded. When on, only the top-level folders are shown on load — click the chevron to expand a branch. Toggling the preference also immediately re-collapses or re-expands the current tree. |

!!! tip "When to enable Collapse"
    If your library has many nested folders, turning on **Collapse** keeps the sidebar compact — you only see top-level folders and drill in when you need them. Small, flat libraries won't notice a difference because the toggle only affects nested folders.

### "All Files" vs "External"

Two top-level entries sit above the folder tree, keeping your own uploads and linked-folder content in separate views instead of one flat list.

| Entry | What it shows |
|---|---|
| **All Files** | Your own uploads in BamDude's managed storage — nothing from linked/mounted folders. This is what "All Files" meant before external folders existed. |
| **External** | The combined view across every linked [external folder](#material-folder-network-external-folder-mounting). It only appears once at least one external folder is linked — a single-folder library doesn't need it, since clicking the folder itself is just as fast. |

The split stops a linked NAS that auto-imported hundreds of files from drowning your own uploads. Clicking an individual folder in the tree is unchanged — it always scopes to just that folder. To get the old combined-everything listing, click **External** once.

---

## :material-sort-variant: Sorting & filtering

### Sort

Sort dropdown above the file grid:

- **Name** — A→Z / Z→A
- **Date** — newest / oldest first
- **Size** — largest / smallest first
- **Type** — grouped by file extension

!!! info "Dates on a mapped (external) folder are the file's own"
    Files on a NAS or USB folder are dated by their **modification time on disk**,
    read on every scan — not by the moment BamDude discovered them. A scan
    discovers a whole folder in the same instant, so the discovery time gave every
    file in it the same timestamp and the order came down to chance. Edit a file on
    the share and it moves to the top the next time you scan.

    **A folder's date is the newest thing anywhere inside it**, however deep — not
    just one level down, which used to make a folder whose models all sit in
    sub-folders look untouched for months. Hover a folder name to see the date it
    is sorted by.

### Not printed

A toggle beside the type dropdown narrows the list to files that have never finished a print. It combines with every other filter rather than replacing them, so "Not printed" plus `.gcode.3mf` answers the question worth asking: what have I sliced and never actually run.

The toggle is not remembered between visits — it is a question, not a preference, and a library that came back half-empty with nothing on screen explaining why would be worse than one extra click.

### File-type chips

Above the grid is a chip row that filters by file extension:

- `.3mf` — sliced or project bundles
- `.gcode.3mf` — sliced files only (subset of `.3mf`)
- `.stl`, `.obj`, `.step` — raw geometry
- `.gcode` — bare gcode (no embedded metadata)

Chips are AND-combined with the [tags](#tags) below — selecting `multiplate` + `.gcode.3mf` returns only multi-plate sliced files. The chip row only renders for types actually present in the loaded list, so flat libraries see a tighter row.

### Clearing filters

When nothing matches, the empty view offers **Clear filters**, and it clears all of them: search, file type, **Not printed**, the "filter by user" box, and the [tag filter](#tags).

The tag filter matters here for a reason that is easy to miss. It is applied by the **server**, so a tag combination matching nothing makes the library itself come back empty — and the reset is offered for that case too, rather than a prompt to upload files, which used to be a dead end.

---

## :material-printer: Print Directly

1. Find a sliced file (`.gcode` or `.gcode.3mf`)
2. Click the printer icon or right-click for context menu
3. Select **Print**
4. Choose printer(s), configure filament mapping, set print options
5. Click **Print** to start

### Multi-printer + plate dispatch

The print modal supports **multi-printer dispatch** — select several printers as targets and the same file is sent to each in parallel; useful for print farms running identical jobs across several machines.

For multi-plate `.gcode.3mf` files (a single bundle exporting several plates), the modal renders a plate-selection grid with thumbnails:

| Step | What you configure |
|---|---|
| **Printer** | One or more target printers (chips) |
| **Plate** | Single-plate select for **Print Now**; multi-plate checkboxes for **Add to Queue** |
| **Filament mapping** | Which loaded AMS slot satisfies each required filament |
| **Schedule** | ASAP, scheduled time, or manual start (queue only) |
| **Options** | Mesh fast-check, swap macros, gcode injection, plate-clear gating |

Each selected plate becomes its own queue item / archive with the plate index recorded — see [Auto-Queue](auto-queue.md).

!!! warning "SD card required"
    The file is FTP-uploaded to the printer's SD card before the print starts. No SD card → upload fails with a clear error. Check the SD slot if your printer reports "card error" right at dispatch time.

### Add to Queue

Queue sliced files for later printing without creating archives upfront. Archives are created automatically when the print actually starts (see [Archives](archiving.md) — deferred archive creation keeps the archive list clean of "queued but never printed" entries).

### Queueing several files at once

Tick the files you want and press **Schedule**. The button only appears when the selection contains something sliced — an STL cannot be printed, so there is nothing to offer.

There is no separate bulk dialog. The ordinary scheduling window opens for the first file, marked **1/3** beside its title, then for the next one, and so on. Every file keeps the full set of choices: a printer or several, or the auto-queue; which plates; filament mapping; print options; quantity; and when to start. Two files in one selection rarely want the same answers — different plates, different colours loaded on different machines — which is why the file, not the batch, is the unit.

Close the window at any point (**Cancel**, the ✕, or Escape) and the run stops there. Whatever you did not get to **stays selected**, so the ticks show what is left to distribute. Everything queued clears the selection.

A submit that fails does not move on: the window stays on that file with its error, which is where the fix is made.

Selecting one file works exactly as it always did — one dialog, no counter.

A file sliced for a printer model that cannot run it is refused rather than quietly queued to fail later. So is a file that was never sliced.


---

## :material-download: Downloading files

### Single file

Click the **Download** action in the file's context menu — the file is served directly with its original name.

### Multiple files

Select multiple files via the checkboxes, then click **Download Selected** in the toolbar. BamDude packages them into a ZIP on the fly and the browser receives a single archive download.

The ZIP preserves folder structure if you selected files from different folders. Filenames are sanitised to avoid duplicates.

---

## :material-folder-zip: ZIP File Uploads

Upload ZIP archives to extract contents into your library:

1. Click **Upload** and select a `.zip` file
2. The upload modal detects ZIP and reveals extraction options
3. Choose extraction behaviour (see options below)
4. Click **Extract**

### Extraction options

| Option | What it does |
|---|---|
| **Preserve folder structure from ZIP** | Maintains the folder hierarchy from inside the ZIP. Folders are created as needed. |
| **Create folder from ZIP filename** | Creates a new folder named after the ZIP (`MyProject.zip` → `MyProject/`) and extracts all files into it. |
| **Flatten** | Default when neither option above is on — every file lands in the current folder, ignoring internal structure. |

Both checkboxes can be combined — enabling both creates a folder from the ZIP filename and preserves the ZIP's internal structure inside it.

### What gets extracted

- `.3mf` — thumbnail and metadata extraction runs on each
- `.gcode` and `.gcode.3mf` — print time / filament weight detection
- `.stl`, `.obj`, `.step` — added with optional thumbnail render (see below)
- Any other supported file type

Progress reporting shows the per-file count during extraction; failures are reported individually so partial extracts are visible. Nested ZIPs are added as regular files, **not** auto-extracted.

---

## :material-cube-outline: STL thumbnail generation

STL / OBJ / STEP files don't carry their own preview, so BamDude can render one for the file card. The renderer uses **Trimesh + matplotlib** at low priority in the background — heavy meshes don't block the upload pipeline.

### Auto on upload

The upload modal has a **Generate thumbnails for STL files** checkbox. When enabled, every STL/OBJ/STEP in the upload (or inside an extracted ZIP) gets a thumbnail rendered as part of the upload flow.

The setting is **off by default install-wide** — enable it in **Settings → File Manager** if you want it on for every upload without ticking the box each time.

### Single-file context menu

For files already in your library:

1. Right-click the file or open its three-dot menu
2. Select **Generate Thumbnail**
3. The thumbnail updates in place when rendering finishes

### Batch generation

The toolbar **Generate Thumbnails** button opens a scope picker:

| Scope | Effect |
|---|---|
| **All missing** | Only files that don't already have a thumbnail |
| **Selected files** | Only files you've checkbox-selected |
| **Entire folder** | Every STL-compatible file in the current folder |

### Technical details

| Property | Value |
|---|---|
| **Renderer** | Trimesh isometric view + matplotlib raster |
| **Colour** | Bambu green (`#00AE42`) on dark background |
| **Format** | PNG, optimised for thumbnail-card size |
| **Priority** | Background task, low priority — won't block uploads or browsing |

Both ASCII and binary STL formats are supported. Very complex meshes (100k+ vertices) render without crashing, just take longer.

---

## :material-cursor-default-click: Drag-and-drop upload

Drop one or more files anywhere over the **files area** (the right-hand pane that holds the toolbar + the file grid/list) — the file upload modal opens with the dropped files preloaded. Same pipeline as the picker / in-modal drop zone, so the ZIP options stay visible and you can still cancel before the upload actually fires. The currently selected folder is preserved as the destination.

The page-level drop is gated on the `library:upload` permission — viewers without that right see no overlay and a drop is a no-op.

---

## :material-database: How files are stored

Every file in the library is a row in the `library_files` table. The row carries:

- **Hash dedup** — uploads are SHA-256'd and matched against existing rows; an identical re-upload returns the existing entry instead of creating a duplicate copy on disk.
- **Thumbnails** — extracted from `Metadata/plate_*.png` inside the 3MF on upload (no on-the-fly extraction). Re-uploads or "reparse" trigger fresh extraction.
- **STL thumbnail render** — STL uploads (`.stl`, `.zip` containing STL) get a thumbnail rendered on upload via the bundled rasteriser, so the card shows the actual part instead of a generic placeholder.
- **`print_count` + `last_printed_at`** — usage counters maintained by dispatch. `print_count` counts **completed** prints only, so a file that was attempted and failed still reads as never printed; a reprint from the archive does advance it. The count appears on the card and in the list beside the file's other facts, and clicking it opens that file's print history. Nothing is shown at zero — the **Not printed** filter above answers that question instead. Backfilled retroactively on upgrade by migration `m014`.
- **`file_metadata` JSON column** — stores parsed slicer metadata: filament weights per spool, object count, sliced-for printer model, plus the `gcode_label_objects` / `exclude_object` flags from the source 3MF's `Metadata/project_settings.config` (extracted in 0.4.1, backfilled by migration `m022`). The label-object flags gate the **skip-objects** button on the printer page during a print — both must be `true` for the button to light up. Bambu Studio has no *Label objects* setting at all and enables *Exclude objects* by default; OrcaSlicer exposes both, with *Label objects* on and ***Exclude objects* off** — so on an OrcaSlicer file that one switch is usually what needs turning on (see [Troubleshooting](../reference/troubleshooting.md) for the slicer-side checklist).
- **`is_multi_plate` + `plates[]` per-plate cache (m023)** — for multi-plate sliced 3MFs (a single `.gcode.3mf` with several `Metadata/plate_N.gcode` entries) BamDude pre-extracts the full per-plate breakdown — thumbnail, print time, filament weight, object count, filament stack, label-object flags — into the same `file_metadata` JSON. The file list returns this without re-opening the 3MF on every query.
- **`swap_compatible` flag** — detected from a `.swap.` or `.swaps.` marker in the filename, e.g. `MyPart.swap.gcode.3mf` or `Tray.swaps.3mf`. The marker must be **dot-delimited**, not underscore-delimited — `MyPart_swap.gcode.3mf` will not be flagged. Swap-compatible files are surfaced separately in the swap-mode picker.
- **Composite `file_tags` column (m036 / m037)** — an unordered JSON list of identity tags drives the badge row on each file. Since m128 the same vocabulary also exists as `is_system` rows in `library_tags`, which is what the tag filter and the tag catalog query; the column stays as a derived cache so the badges and the preview-tab logic read a column on the row they already have. Both are written by one function, `sync_system_tags`. Four semantic groups: **format** (`gcode` / `3mf` / `stl` / `obj` / `step` — sliced `.gcode.3mf` keeps the composite `gcode + 3mf` pair so the visual distinction survives `file_type` collapse), **readiness** (mutually exclusive: `sliced` for slicer-output, `project` for unsliced `.3mf` packages, `geometry` for raw mesh / CAD source — one toggle for "what still needs slicing?"), **modifiers** (`swap` / `multiplate`), **provenance** (`makerworld`). Frontend `sortTagsForDisplay` projects onto an explicit precedence so the row reads right-to-left format → readiness → modifiers → provenance.

## :material-tag-multiple: Tags

There are two kinds of tag and one row of them.

**Automatic tags** — `3MF`, `SLICED`, `MULTI-PLATE`, `MAKERWORLD` and the rest — are worked out from the file itself. They are shown but locked: they cannot be renamed, deleted, or taken off a file, and they are not offered where you apply tags by hand.

**Your own tags** are anything you like — `kid-safe`, `petg-only`, `toys`. Create, rename and delete them from the **Tags** button in the toolbar.

Both sit in one filter row above the file list, automatic ones first. Clicking toggles, and selections AND together, so `SLICED` + `kid-safe` returns only the sliced files you have labelled that way. The filtering is done by the server, not over whatever is currently on screen, so it reaches the whole library rather than the loaded page.

An automatic tag appears in the row only when at least one file in the library carries it. Your own tags always appear, including empty ones — an unused tag is precisely the one you want to see in order to start using it.

The selection is not remembered between visits. A library that comes back narrowed with nothing on screen explaining why costs more than one click.

### Managing tags

The **Tags** dialog lists both kinds, automatic ones in a locked section with their file counts.

- Rename in place — click the name, type, press Enter. Escape abandons it.
- Delete asks first and says how many files it will affect.
- Tick several to delete them together.
- Clicking a row does nothing else. It does not filter, and it does not close the dialog.

### Tagging one file

**⋮ → Tag** on any file opens a short list of your tags with the file's current ones ticked. A tick applies immediately; there is no confirm step. **+ new tag** at the bottom creates one and applies it in the same move.

## :material-eye-outline: 3D / G-code viewer

Library files share the same `<ModelViewerModal>` as archives, with two library-specific touches:

- **Tab visibility from `file_tags` rather than file extension.** A sliced `.gcode.3mf` (which has both extensions) shows only the G-code tab — its embedded mesh is already rasterised into the gcode lines and re-rendering it under "3D Model" duplicates information. An unsliced `project` 3MF or raw `geometry` mesh shows only the 3D tab. Tabs are queried via `GET /library/files/{id}/capabilities` (mirrors the long-standing archive route).
- **Per-plate G-code picker for multi-plate library files.** Library files are browseable, so the G-code tab gets a plate picker that re-keys the gcode-preview URL when you switch plates. Archives keep the single-plate behaviour because they record one specific print.
- **Build-volume wireframe** — the 3D viewer draws a translucent box matching the printer the file was sliced for (read from `printer_settings`). G-code preview already painted a similar box; same visual cue across both tabs now.
- **Shared modal features** — OBJ format support, wireframe / X-ray toggle, theme-synced canvas, dual-handle layer slider (Start + End), travel-moves toggle, layer-play with 1× / 2× / 4× / 8× speeds, streaming download progress, and Export-as-PNG. See [Archives → 3D + G-code Preview](archiving.md#material-cube-scan-3d-g-code-preview) for the full feature breakdown; library uses the same `<ModelViewerModal>` verbatim.

## :material-view-gallery: Per-plate gallery (multi-plate 3MFs)

Sliced 3MFs that contain more than one plate render as a per-plate gallery on the file card:

- A vertical paginator strip on the left — one button per plate, each showing the selected-state dot.
- A big card on the right with that plate's thumbnail, name, print time, total weight, instance count, and per-filament breakdown (color swatch + type + grams).
- Selection (which plates to print) is decoupled from navigation (which plate's card is visible) — you can flip through plates without touching the selection.

When dispatching, you can select one plate, multiple plates, or all of them — every selected plate becomes its own queue item / archive with the plate index recorded on the row.

Single-plate files don't render the gallery — the existing main thumbnail covers that case.

---

## :material-link-variant: Project & Folder Links

- **Per-folder link** -- linking a folder to one or more projects (chip multi-select in the folder edit dialog) attaches every file inside to those projects, and any file moved into that folder later inherits the same project list.
- **Per-file link** -- each file row also has its own `Link2` button that opens the same chip multi-select to attach the file to any number of projects independently of its folder.
- **Many-to-many** (m044) -- a file or folder can belong to several projects at once; the legacy single-FK `project_id` was replaced by `library_file_projects` + `library_folder_projects` pivot tables. The same file in N projects shows up as N independent plan rows on the project pages.
- **Per-chip unlink** -- each selected project chip in the file/folder dialog has a small `×` icon that removes only that one association via `DELETE /library/{files|folders}/{id}/projects/{project_id}`. The bulk "Unlink from all" button is gone — use the chip multi-select to set `project_ids: []` instead.
- **Per-project plan items** (m016, reshaped by m044) -- the project page renders a flat plan list with copies/order/totals; rows auto-appear when files / folders link to the project, and per-row totals (filament, time, cost) feed the project-level grand totals. The unique constraint is now `(project_id, library_file_id)` so a shared file gets independent plan rows per project.

---

## :material-delete: Trash workflow

Deleted files don't disappear immediately — they move to **Trash** and stay there for a configurable retention window (default **30 days**) before a background sweeper hard-deletes them from disk. This gives you an undo window for accidental deletions and bulk operations.

**Every route into deletion behaves the same way.** Deleting one file, deleting a selection, and deleting a folder all put the entries in the trash — the bulk paths used to destroy files outright, with nothing to restore. Files that were inside a deleted folder come back to the **top level** of the library when restored, since the folder they lived in no longer exists.

!!! note "A file that could not be deleted is not reported as deleted"
    Bulk delete skips a file whose print is currently running. The result says what
    actually happened and how many were skipped, rather than counting everything
    you selected.

### Restoring or permanently removing trashed files

Open **Trash** (button in the File Manager header) to see what you've deleted. Regular users see their own trashed files; admins see everyone's.

| Action | Effect |
|---|---|
| **Restore** | Moves the file back to its original folder |
| **Delete now** | Permanently removes the file from disk immediately, bypassing retention |
| **Empty trash** | Hard-deletes every file currently in your scope's trash |

Admins can change the retention window itself on the Trash page — anywhere from **1 to 365 days**, default **30**.

!!! note "External files bypass Trash"
    Files in external / linked folders skip the trash entirely because their bytes live outside BamDude's control and can't be restored. Deleting an external file just removes BamDude's DB record — the file on disk is untouched.

---

## :material-broom: Purge old files (admin)

For libraries that have grown into gigabytes, admins get a bulk **Purge old** action in the File Manager header. Pick an age threshold (e.g. "files not printed in 90 days"), see a live preview of how many files would move and how much disk that frees, then confirm.

### What happens when you click Purge

- Matching files are moved to Trash — **they are not deleted from disk yet**
- You can restore them from Trash at any time until the retention window expires
- After retention, the trash sweeper permanently removes them from disk
- Files in external (linked) folders are skipped — BamDude never deletes bytes it does not own

Because files only move to Trash, the disk doesn't free up immediately. To reclaim the space right away, empty the Trash manually afterwards.

### How "old" is measured

- Files **with** a print history → aged by **last-printed date**
- Files that have **never** been printed → aged by **upload date**, only when the "Include files that have never been printed" checkbox is on (default). Turn it off to limit the purge to files you've actually printed before

The **Purge old** button only appears for users holding the `library:purge` permission, which ships enabled by default on the built-in **Administrators** role. To grant it to an Operator role, add `library:purge` in **Settings → Users → Groups** — see [Authentication](authentication.md).

### Auto-purge (optional)

Don't want to remember to run the purge every month? **Settings → File Manager → Auto-purge old files** runs the same operation automatically once per 24 hours:

- Age threshold (minimum 7 days, maximum 10 years) — uses the same rule as the manual button
- Include-never-printed checkbox
- Default off; opt-in only so existing installs aren't surprised

Auto-purge still respects the trash retention window — files are moved to Trash first, not deleted outright. The sweeper later hard-deletes them after the retention period.

---

## :material-pencil: Renaming files & folders

You can rename files and folders directly in the File Manager without an external client.

### Renaming a file

**Grid view:**

1. Hover over the file card
2. Click the three-dot menu (`:material-dots-vertical:`)
3. Select **Rename**
4. Enter the new name
5. Click **Rename** to save

**List view:**

1. Find the file in the list
2. Click the pencil icon (`:material-pencil:`) in the actions column, or **double-click** the name for in-place editing
3. Enter the new name
4. Press Enter or click **Rename** to save

### Moving one file

**Move** sits in the same three-dot menu as **Rename**, in both grid and list view, and opens the folder picker directly. There is no need to tick the file first — the multi-select toolbar still offers Move for several files at once, but a single file does not have to go through a selection to be moved.

It is gated exactly like Rename: a user holding only the `*_own` library permissions sees it on their own files and nowhere else.

### Renaming a folder

1. Hover over the folder in the sidebar
2. Click the three-dot menu
3. Select **Rename**
4. Enter the new name
5. Click **Rename** to save

!!! note "Filename restrictions"
    Filenames cannot contain path separators (`/` or `\`). The rename API rejects these characters and the modal surfaces the error inline.

### Deleting a folder

Folders have no owner, so deleting one used to need the full "delete anything" permission (`library:delete_all`) — which meant a user could create a folder, delete their own files out of it, and then have to ask an administrator to clear the empty shell.

| Folder | Permission needed |
|---|---|
| **Empty** | `library:delete_own` — the ordinary delete permission |
| Holds files or subfolders | `library:delete_all` |
| An external / mapped folder | `library:delete_all` |
| Linked to a project or an archive | `library:delete_all` |

Removing any of the last three affects more than the folder, which is why they still need an administrator.

!!! warning "'Empty' is decided by the server, not by what you can see"
    A folder holding a file **somebody else** has deleted looks empty in the tree.
    Deleting it would take that file for good and break their restore — so it is
    refused, and says why.

---

## :material-folder-network: External Folder Mounting

Mount host directories (NAS shares, USB drives, network storage) into the File Manager without copying files. BamDude indexes the folder into its database and reads files directly from the original path; no disk space is used for file copies.

### Setting up an external folder

**Step 1: Bind-mount the directory into Docker.** Add the host directory as a volume in your `docker-compose.yml`:

```yaml
services:
  bamdude:
    image: ghcr.io/kainpl/bamdude:latest
    volumes:
      - /mnt/nas/3d-prints:/external/prints:ro
```

Restart the container after changing volumes.

**Step 2: Link the folder in BamDude.**

1. Open **File Manager**
2. Click **Link External** in the toolbar
3. Fill the form:

| Field | Value |
|---|---|
| **Display name** | What appears in the sidebar (e.g. `NAS Prints`) |
| **Container path** | The path inside the container (e.g. `/external/prints`) |
| **Read-only** | Default **on** — blocks uploads, deletions, ZIP-extracts into the folder. Recommended unless you specifically want to manage files via BamDude. |
| **Show hidden files** | Off by default; enables dotfile indexing |

4. Click **Link Folder**

The folder is automatically scanned and files appear immediately.

### Scanning & refreshing

External folders are indexed on creation. To pick up new or removed files:

1. Click the external folder in the sidebar
2. Click **Scan / Refresh** in the info bar
3. New files are added to the index, files removed on disk are dropped from the index

### Read-only protection

When **Read-only** is on (default):

- Uploads to the folder are blocked (`403`)
- Moving files into the folder is blocked
- ZIP extraction targeting the folder is blocked
- Files can still be downloaded, printed, queued, and have thumbnails generated

!!! tip "Defence in depth"
    Use `:ro` in your Docker volume mount for an extra layer of read-only protection at the filesystem level — even if you accidentally untick BamDude's checkbox, the kernel still rejects the write.

### Deleting external folders

When you delete an external folder from BamDude:

- The database index entry is removed
- Generated thumbnails are cleaned up
- **The actual files on disk are never deleted** — BamDude only deletes the link, not the source files

### Supported file types

External folder scanning discovers: `.3mf`, `.gcode`, `.stl`, `.obj`, `.step`, `.stp`, and image files (`.png`, `.jpg`, `.gif`, `.webp`, `.svg`).

---

## :material-link: Linking folders to projects / archives

Right-click a folder (or use its three-dot menu) → **Link to project** / **Link to archive** to attach a folder to a [Project](projects.md) or an existing [Archive](archiving.md). The project picker is a chip multi-select — pick any number of projects in one go.

| Action | Where |
|---|---|
| **Link folder** | Right-click on folder → "Link to project / archive" |
| **Add / drop a project** | Open the link dialog, toggle chips on/off, save |
| **Remove one project** | Click the `×` on the relevant chip in the dialog (single-pivot DELETE) |
| **Remove all projects** | Clear every chip in the dialog and save (`project_ids: []`) |

Linked folders show a colored badge in the sidebar and grid. When a folder is linked to multiple projects the badge carries an `×N` overflow counter and the tooltip lists every project name. Per-folder links propagate the project list to every file inside via the M2M pivot, plus any file moved into the folder later inherits the same list.

---

## :material-api: API endpoints reference

The library is fully accessible via the REST API — useful for scripted ingestion, CI/CD pipelines, or external slicer plugins.

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/v1/library/files` | `GET` | List files (paginated; query params for folder, sort, filter) |
| `/api/v1/library/files/{id}` | `GET` | Single file detail (metadata, plates, file_tags) |
| `/api/v1/library/files/{id}/capabilities` | `GET` | Which viewer tabs to show (3D / G-code / per-plate) |
| `/api/v1/library/files` | `POST` | Multipart upload (one or more files) — needs `library:upload` |
| `/api/v1/library/files/extract-zip` | `POST` | Upload + extract ZIP with options |
| `/api/v1/library/files/{id}` | `DELETE` | Soft-delete (move to trash) |
| `/api/v1/library/bulk-delete` | `POST` | Soft-delete many files at once |
| `/api/v1/queue/` | `POST` | Queue a library file (`library_file_id`) onto a printer's queue — needs `queue:create`, not a library permission |
| `/api/v1/library/folders` | `POST` | Create folder |
| `/api/v1/library/folders/external` | `POST` | Link an external folder |
| `/api/v1/library/folders/{id}/scan` | `POST` | Re-scan an external folder |

All endpoints require an authenticated session (JWT bearer or `X-API-Key` header). The required permission depends on the action — `library:read` for reads, `library:upload` for uploads, `library:delete` for deletes, `library:purge` for the bulk purge action. See [Authentication](authentication.md) and the full [API reference](../reference/api.md).

---

## :material-cellphone: Mobile & PWA

The File Manager is optimised for touch devices and works as an installed Progressive Web App.

### Touch-friendly interface

- **Action buttons** are always visible on mobile — no hover required
- **Selection checkboxes** appear on every file card for easy multi-select
- **Context menus** are accessible via the three-dot button on each card
- **Responsive grid** adjusts column count based on screen width

### Mobile uploads via Share menu

BamDude's PWA registers as a **share target** on iOS Safari and Android Chrome — share a file from any other app and BamDude appears in the picker:

1. **Install** BamDude as a PWA on your phone (Safari → Share → Add to Home Screen; Chrome → menu → Install app)
2. In any app that handles 3MF / STL / gcode (Drive, Mail, AirDrop receiver, slicer), use the **Share** menu
3. Pick **BamDude** as the target
4. The Library opens with the file pre-staged in the upload modal — confirm the destination folder and tap Upload

The currently-selected folder when you land in the Library is the default destination — open the right folder before sharing if you want the upload to land somewhere specific.

### PWA tips

- Add BamDude to your home screen for a native-app experience (no browser chrome)
- File browsing works offline against cached data
- Swipe gestures work naturally on touch devices

---

## :material-lightbulb: Tips

!!! tip "Multi-Printer Support"
    Select multiple printers to send the same file to your entire print farm at once.

!!! tip "File Badges"
    Look for "sliced" badges to identify files ready for printing.

> Originally based on [Bambuddy](https://github.com/maziggy/bambuddy) documentation.
