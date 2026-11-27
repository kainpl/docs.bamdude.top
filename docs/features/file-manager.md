---
title: File Manager
description: Browse and manage your local library of print files
---

# File Manager

Browse, upload, and manage files in your local BamDude library. Print directly or add to queue.

The card grid adapts to the width available beside the folder tree, up to six columns. Each card keeps file size,
printer model and print time on the first information row, followed by material, filament weight and counters on
the second. Narrow layouts use fewer columns so values and actions stay visible.

## On a phone

Search and Filters open only when needed. Closing them keeps the query, file type, user, tags and sorting;
a collapsed search still shows its query, and Filters shows the number of active conditions. Clear filters
resets the search and filters together. The desktop layout keeps its controls expanded.

Upload and the view switch remain visible. The **More library actions** menu contains thumbnail generation,
folder creation/linking, the tag catalog, Select all and trash actions, subject to your permissions.
Disabled menu commands keep their explanations and Trash shows its count. Closing a dialog after rotating the screen returns keyboard focus to the current toolbar. Selection actions appear after you select files. Storage statistics are compact, but low-space warnings remain visible.

## Model previews

STL/OBJ preview generation and missing previews after server-side slicing run
in a separate local process. BamDude includes and manages its local NATS broker
and preview service automatically, in the same installation or Docker container.
There is no external broker address, extra published port or additional container
to configure. Installation downloads the bundled package; normal operation does
not download an executable.

Preview work is bounded and best-effort. An oversized model, a busy worker or a
service failure may leave a file without a picture, but does not discard a valid
upload or slicing result. Use thumbnail regeneration to retry later. Failed
regeneration keeps the previous picture. Existing pictures are ordinary library
files: viewing and backing them up does not require the preview service.

For startup failures, see [local preview recovery](../reference/troubleshooting.md#local-preview-service).

---

## :material-folder: Overview

The File Manager lets you:

- **Browse** files in your local library
- **Mount external folders** from NAS, USB, or network shares
- **Upload** files including ZIP archives
- **Open** models, G-code, images and PDFs in a [viewer](#opening-files)
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

### "Internal" vs "External"

Two top-level entries sit above the folder tree, keeping your own uploads and linked-folder content in separate views instead of one flat list.

| Entry | What it shows |
|---|---|
| **Internal** | Files in BamDude's managed storage — nothing from linked/mounted folders. |
| **External** | The combined view across every linked [external folder](#external-folder-mounting). It only appears once at least one external folder is linked — a single-folder library doesn't need it, since clicking the folder itself is just as fast. |

The split stops a linked NAS that auto-imported hundreds of files from drowning your own uploads. Clicking an individual folder in the tree always scopes to just that folder.

### Moving folders {#moving-folders}

A folder moves together with its subfolders and files. There are two ways to move one:

- **Move…** in the folder's three-dot menu opens a tree of targets with **Library root** at the top. Pick a target and confirm. A target that cannot work is greyed out and says why: *already here*, *this folder*, *its own subfolder*, *external*.
- **Drag** the folder onto another folder in the tree, or onto the library root. While you drag, a folder that can take the drop is outlined in green and one that cannot is dimmed. A drag resting on a collapsed folder for a moment opens its branch, so a target deep in the tree is reachable in one drag.

Files are dragged the same way — onto a folder of the tree, a folder in the [Columns view](#columns-view), or the library root. Dragging a ticked file takes the whole ticked selection with it. A file can be dragged by whoever may edit it; a target marked *changes products* is refused for a user without `products:update`, exactly as in the **Move** dialog.

Touch devices have no drag-and-drop: use **Move…** in the folder's menu and **Move** in the file's.

What cannot be moved:

- **An external folder and its subfolders** — they are directories of their share. The menu entry is disabled and says *An external folder and its subfolders cannot be moved.*
- A folder **into an external folder**, **into itself** or **into one of its own subfolders**.

Folders have no owner, so moving one needs `library:update_all` — the same right as renaming one. The server checks every move again, whatever the dialog showed: a target that has disappeared meanwhile is refused with *The target folder no longer exists.*

---

## :material-view-column-outline: Views {#views}

The view switch in the toolbar offers three views of the same library. The choice is stored in your browser.

| View | What it shows |
|---|---|
| **Cards** | A grid of file cards with thumbnails. |
| **List** | One row per file. |
| **Columns** | One column per folder of the path to the open folder. |

In every view the page address names the open folder, so reloading the page or opening a copied link shows the folder that was on screen.

### Columns {#columns-view}

The first column is the library root, **Library**; every folder you open adds a column to its right, so the columns are the path to the open folder. A column lists the folders of its level first, then its files.

- **Click a folder** to open it in the next column. Each step is also a step of the browser's history, so Back walks up the path.
- **Click a file** to show it in a preview column on the right — the file's card with all its actions, a **Details** button and a close button. **Double-click** a file to [open it](#opening-files).
- **Tick** the box beside a file to add it to the selection for the bulk actions.
- **Move…** in the header of an open folder's column moves that folder.

Each column loads its own files from the server, 50 at a time, under the sort and filters of the page; **Show more (50 of 180)** at the foot of a column loads the next 50.

A search or a filter narrows each column to the matching files **of its own folder**. Folders are always shown, so the path stays open, and the page says so while a filter is on. A column is one folder, so the **This folder and subfolders** switch beside the search box is unavailable in this view.

Columns can be driven from the keyboard:

| Key | Action |
|---|---|
| ++arrow-up++ / ++arrow-down++ | Previous / next row of the column |
| ++home++ / ++end++ | First / last row of the column |
| ++arrow-right++ | Open the focused folder, or show the focused file in the preview column |
| ++arrow-left++ | Back to the parent column |
| ++enter++ | Open the focused folder, or open the focused file in its viewer |
| ++space++ | Tick the focused file for the bulk actions |
| ++m++ | Move the focused folder (opens **Move…**) |

On a screen narrower than 640 px there is room for one column: the open folder, or the preview of a file. A **Back** control above it leads out of the preview, then up one folder at a time.

---

## :material-file-eye-outline: Opening files {#opening-files}

A **double click** on a file's card or row opens it, and so does ++enter++ while the card or row has the keyboard focus. What opens is the viewer the file's menu offers for its type:

| File | Menu entry | Viewer |
|---|---|---|
| `.3mf`, `.gcode`, `.stl`, `.obj` | **3D View** | The [3D / G-code viewer](#model-viewer) |
| `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.bmp` | **View image** | The image viewer |
| `.pdf` | **View PDF** | The PDF viewer |

A file of any other type has no viewer — **Download** it instead. Whoever can see a file in the list can open and download it.

### Image viewer {#image-viewer}

The picture is fitted to the window and can be zoomed from 100 % up to 1600 %:

- **Zoom** — the mouse wheel (towards the pointer), the **Zoom in** / **Zoom out** buttons, a two-finger pinch, or the ++plus++ and ++minus++ keys.
- **Reset** — the percentage button between the zoom buttons, or ++0++.
- **Pan** — drag a zoomed picture; it stops when its edge meets the edge of the window.
- **Close** — ++esc++, the ✕, or a click on the empty area around the picture.

An image file over 100 MB, or a picture of more than 100 megapixels, is not shown: the viewer says *This image is too large to preview. Download it to open it.*

### PDF viewer {#pdf-viewer}

A PDF opens with its pages one under another, fitted to the width of the window.

| Control | What it does |
|---|---|
| **Previous page** / **Next page**, the page box | Step through the document, or type a page number and press ++enter++. They float at the bottom of the viewer. |
| **Zoom in** / **Zoom out** | From 25 % to 500 %. |
| **Fit width** | The widest page fills the width of the window. |
| **Fit page** | The page on screen fits the window whole. |

Keys: ++page-down++ or ++arrow-right++ — next page; ++page-up++ or ++arrow-left++ — previous page; ++home++ / ++end++ — first / last page; ++arrow-up++ / ++arrow-down++ — scroll; ++plus++ / ++minus++ — zoom; ++0++ — fit width; ++esc++ — close.

The viewer draws pages and nothing more:

- **No text selection and no search.** Download the file to work with its text.
- **Scans stored as JPEG 2000 or JBIG2 stay blank** — the page appears, the picture on it does not.
- **A PDF over 64 MB is not opened.** The viewer offers the download instead.

When a document cannot be shown, the viewer says which of these happened:

| Message | What it means |
|---|---|
| *This PDF is too large to preview. Download it to open it.* | The file is over 64 MB. |
| *This PDF is password-protected and cannot be previewed.* | The document asks for a password. |
| *This PDF could not be opened. The file may be damaged.* | The file was read, and it is not a valid PDF. |
| *This file is not available: it was moved or deleted, or you no longer have access to it.* | The server refused the file — it is gone, or your session or rights changed. |
| *The file could not be loaded from the server. Check the connection and try again.* | The request got no answer. |
| *The PDF viewer could not be loaded. Reload the page and try again, or download the file.* | The viewer itself failed to start; the document is not at fault. |
| *This page could not be drawn.* | Shown on one page; the rest of the document is unaffected. |

Four of them — too large, password-protected, damaged, viewer not loaded — come with a **Download** button, since the file itself can still be fetched.

### Fullscreen {#fullscreen}

The 3D / G-code, image and PDF viewers have a **Fullscreen** button that hands the viewer the whole screen (in the 3D / G-code viewer it sits beside **Fill the window**, which only enlarges the dialog inside the browser window).

- ++esc++ leaves fullscreen first; the next ++esc++ closes the viewer. **Exit fullscreen** does the same as the first.
- Toast messages stay visible inside the fullscreen viewer.
- Opening a dialog ends fullscreen by itself, so the dialog is never hidden behind it.
- A browser without element fullscreen — Safari on an iPhone — shows no button.

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
    just one level down, so a folder whose models all sit in
    sub-folders does not look untouched for months. Hover a folder name to see the date it
    is sorted by.

### Search

Typing in **Search files...** searches the whole library, external folders included. With a folder open, a **This folder and subfolders** switch appears beside the box once you type: turn it on to keep the search inside that folder and everything below it. In the [Columns view](#columns-view) the switch is unavailable — each column searches its own folder only.

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

The tag filter matters here for a reason that is easy to miss. It is applied by the **server**, so a tag combination matching nothing makes the library itself come back empty — and the reset is offered for that case too, rather than a prompt to upload files, which would be a dead end.

---

## :material-printer: Print Directly

1. Find a sliced file — a `.gcode`, a `.gcode.3mf`, or a `.3mf` with sliced G-code inside. BamDude looks inside the file rather than at its name, so a plate exported from the slicer as `Part.3mf` prints like `Part.gcode.3mf`
2. Click the printer icon or right-click for context menu
3. Select **Print**
4. Choose printer(s), configure filament mapping, set print options
5. Click **Print** to start

The content decides both ways. A project saved under a `.gcode.3mf` name holds no sliced G-code and is refused: *This 3MF is named like a sliced file but holds no sliced G-code. Slice it first, then print the result.* Only a file whose content cannot be read at all is judged by its name. For a file in an external folder, a recorded "not sliced" is read again from the share before the print is refused, so a project sliced and saved over the same name prints without a new scan.

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

!!! warning "Where the file goes before the print starts"
    The file is uploaded to the printer's SD card over FTP. On **X2D, P2S and the H2 family**, which keep files in built-in storage too, a printer with **no card in** gets the file into that internal storage instead — nothing to set up, and nothing changes when a card *is* in.

    Every other printer needs the card: without one the upload fails with a clear error. A card that is present but **unreadable or write-protected** stops the print on any printer, internal storage or not — an unusable card means something is wrong with the machine, and quietly routing around it would hide that. The message says which of the two situations you are in.

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

## :material-view-grid-plus: Assemble project

Choose **Assemble project** from an STL, OBJ, STEP or STP file's **⋮** menu, or select several models and use the selection bar. BamDude lays out the parts and saves project 3MF files for your printers. See [Assemble Project](assemble-project.md).

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

Where a file's thumbnail comes from depends on its type:

| File | Thumbnail |
|---|---|
| `.3mf` | The plate picture the slicer stored inside the file |
| `.stl`, `.obj` | A render of the model |
| `.step`, `.stp` | A render made in the background — see [STEP thumbnails](#step-thumbnails) |
| `.pdf` | The first page of the document |
| Image files | The picture itself, scaled down |

STL / OBJ / STEP files don't carry their own preview, so BamDude can render one for the file card. The renderer uses **Trimesh + matplotlib** at low priority in the background — heavy meshes don't block the upload pipeline. A STEP file has no mesh for it to draw: its picture takes a different path, described under [STEP thumbnails](#step-thumbnails) below. A PDF's first page is drawn in the same separate preview process as the models; a password-protected or damaged PDF is still stored, without a thumbnail.

### Auto on upload

The upload modal has a **Generate thumbnails for STL, OBJ and STEP models and PDF documents** checkbox. When enabled, every STL, OBJ, STEP and PDF in the upload (or inside an extracted ZIP) gets a thumbnail as part of the upload flow.

The setting is **off by default install-wide** — enable it in **Settings → File Manager** if you want it on for every upload without ticking the box each time.

### Single-file context menu

For files already in your library:

1. Right-click the file or open its three-dot menu
2. Select **Generate Thumbnail**
3. The thumbnail updates in place when rendering finishes

The entry is offered for STL, OBJ, STEP and PDF files. For an STL, OBJ or PDF it follows the file's own edit rule — your own files with `library:update_own`, any file with `library:update_all`; a STEP file needs `library:update_all`.

### Batch generation

The toolbar **Generate Thumbnails** button works on the files that have no thumbnail: it renders every such STL, OBJ and PDF at once and queues the STEP files in the background.

| Your right | What the button covers |
|---|---|
| `library:update_all` | Every file in the library that is missing a thumbnail, STEP files included |
| `library:update_own` | Your own STL, OBJ and PDF files that are missing one |
| Neither | The button is disabled: *You do not have permission to generate thumbnails* |

### Technical details

| Property | Value |
|---|---|
| **Renderer** | Trimesh isometric view + matplotlib raster |
| **Colour** | Shaded Bambu green (`#00AE42`) with a transparent background |
| **Format** | PNG, optimised for thumbnail-card size |
| **Priority** | Background task, low priority — won't block uploads or browsing |

Both ASCII and binary STL formats are supported. Complex meshes may be simplified; preview work has size, time and memory limits. An oversized or failed preview can leave a valid file without a thumbnail.

---

## :material-cube-scan: STEP thumbnails {#step-thumbnails}

A STEP or STP model gets a picture of its shape, made in the background by the **Open CASCADE** geometry kernel. That kernel is an optional component: the Docker image and the Windows installer carry it, and a native install chooses it at install time — see [Installation → STEP previews](../getting-started/installation.md#step-previews). Without it the file is still kept in the library; it just gets no thumbnail, and the reason says so.

### What queues a picture

Every door a new STEP file comes in by queues one, as long as thumbnails are on for the upload (the dialog's **Generate thumbnails for STL, OBJ and STEP models and PDF documents** box, or the install-wide setting under **Settings → File Manager**): a direct upload, a member of an extracted ZIP, a file sent to the Telegram bot, and a product import. The upload dialog says **STEP thumbnail queued — it is made in the background**, or **STEP thumbnail not queued:** with the reason; the card updates when the picture lands.

For a file already in the library, **Generate Thumbnail** in its menu queues one, and the toolbar button — **Generate thumbnails for STL, OBJ and STEP files missing them** — covers STEP files too. The batch queues one batch at a time: when **More STEP files are still missing thumbnails — press again to queue the next batch** appears, press it again. A running job is cancelled from the same menu entry, **Cancel thumbnail**; a picture that is already being saved can no longer be cancelled, and says so.

Only users who may update all library files can generate STEP thumbnails (`library:update_all`) — the menu entry says exactly that to anyone else.

### Priority and limits

Sliced files and STL/OBJ previews always go first. A STEP picture runs in its own time budget, and a slicing job can interrupt it; one interrupted too often ends with *slicing kept interrupting the conversion — try again when the farm is quieter*. A model that is too large, takes too long or cannot be read ends with a reason of its own, and **the previous thumbnail stays** whenever a new one fails.

### When no picture comes

The upload dialog, the toast and the file's menu all use the same sentences:

| The sentence | When |
|---|---|
| *the background queue is full — try again later* | The queue of background jobs has no room now; nothing was queued. |
| *slicing kept interrupting the conversion — try again when the farm is quieter* | Slicing, which goes first, interrupted the job too many times. |
| *waited too long to start* · *ran out of time* | The job's time budget ran out — before it started, or while it ran. |
| *a backup kept the thumbnails paused for too long — try again once it has finished* | A backup paused the thumbnails while the job's time ran out; see [Backups](#step-thumbnails-and-backups) below. |
| *the permission needed is gone* | The right the job was queued with is no longer held. |
| *STEP thumbnails are made in the background* | A STEP file was asked for a picture on the spot; STEP pictures come only from the background queue. |
| *the STEP component is not available on this server* | The Open CASCADE component is missing — Docker on 32-bit ARM, or a native install that declined it. See [Troubleshooting → STEP thumbnails](../reference/troubleshooting.md#step-thumbnails). |
| *the model took too long to convert* · *the model is too large or too complex for a thumbnail* · *the model could not be converted completely* · *the file is too small to contain a usable mesh* · *the file is not a STEP model* | The model itself is over the limits or not readable. The previous thumbnail stays. |
| *the file changed meanwhile* · *the file has no verified content hash* · *the file is missing on disk* | The file is not the one the job was queued for, has no verified content hash, or is gone from disk. |
| *the preview service is not available right now* · *the preview service is busy* | The local preview service is down or busy; see [Local preview service](../reference/troubleshooting.md#local-preview-service). |
| *canceled* · *the thumbnail is already being saved and can no longer be canceled* | A cancel from the menu — in time, or after the picture had started saving. |
| *an internal error occurred* · *something went wrong* | An internal error, or a reason this version of the page does not know (a newer server's). |

### STEP thumbnails and backups {#step-thumbnails-and-backups}

A backup taken while pictures are being made neither fails because of them nor holds up the preview queue: a picture the backup catches is made again once the backup is done, and slicing never waits for it. A STEP job that runs out of time meanwhile says *a backup kept the thumbnails paused for too long*. A restore waits for pictures still being written and says so when it cannot — and keeps saying so until BamDude restarts when the picture service could not be confirmed stopped.

STEP files still have no 3D view.

---

## :material-cursor-default-click: Drag-and-drop upload

Drop one or more files anywhere over the **files area** (the right-hand pane that holds the toolbar + the file grid/list) — the file upload modal opens with the dropped files preloaded. Same pipeline as the picker / in-modal drop zone, so the ZIP options stay visible and you can still cancel before the upload actually fires. The currently selected folder is preserved as the destination.

The page-level drop is gated on the `library:upload` permission — viewers without that right see no overlay and a drop is a no-op.

---

## :material-database: How files are stored

Every file in the library is a row in the `library_files` table. The row carries:

- **Hash dedup, on every path a file can arrive by** — the content is SHA-256'd and matched against the active rows before anything is written, so a file BamDude already holds is never stored twice. This covers uploading, the API, dropping a file on the file manager or on a printer, importing a project, slicing the same model again and Send-to-Printer from a slicer. Whatever you were doing carries on with the row that already exists, and you are told which of your files was used instead of the one you sent.

    **Linked folders join in too.** A scan reads each external file once and remembers its fingerprint next to the size and modification time it stores, so later scans re-read only what actually changed.

    **A row whose bytes went missing gets them back.** If the library still lists a file but the file is gone from disk, sending the same content again restores it in place — keeping the name, folder, notes, tags, projects and print history — rather than starting a fresh entry with none of that.

    ⚠️ Only **active** rows take part. A file you moved to the trash does not pin a fresh arrival to itself; see [Library trash](library-trash.md). Restoring from the trash is the one remaining way to end up with two identical files, and it asks first.
- **Thumbnails** — extracted from `Metadata/plate_*.png` inside the 3MF on upload (no on-the-fly extraction). Re-uploads or "reparse" trigger fresh extraction.
- **STL thumbnail render** — STL uploads (`.stl`, `.zip` containing STL) get a thumbnail rendered on upload via the bundled rasteriser, so the card shows the actual part instead of a generic placeholder.
- **`print_count` + `last_printed_at`** — usage counters maintained by dispatch. `print_count` counts **completed** prints only, so a file that was attempted and failed still reads as never printed; a reprint from the archive does advance it. The count appears on the card and in the list beside the file's other facts, and clicking it opens that file's print history. Nothing is shown at zero — the **Not printed** filter above answers that question instead. Backfilled retroactively on upgrade by migration `m014`.
- **`file_metadata` JSON column** — stores parsed slicer metadata: filament weights per spool, object count, sliced-for printer model, plus the `gcode_label_objects` / `exclude_object` flags from the source 3MF's `Metadata/project_settings.config` (backfilled for existing files by migration `m022`). The label-object flags gate the **skip-objects** button on the printer page during a print — both must be `true` for the button to light up. Bambu Studio has no *Label objects* setting at all and enables *Exclude objects* by default; OrcaSlicer exposes both, with *Label objects* on and ***Exclude objects* off** — so on an OrcaSlicer file that one switch is usually what needs turning on (see [Troubleshooting](../reference/troubleshooting.md) for the slicer-side checklist).
- **`is_multi_plate` + `plates[]` per-plate cache (m023)** — for multi-plate sliced 3MFs (a single `.gcode.3mf` with several `Metadata/plate_N.gcode` entries) BamDude pre-extracts the full per-plate breakdown — thumbnail, print time, filament weight, object count, filament stack, label-object flags — into the same `file_metadata` JSON. The file list returns this without re-opening the 3MF on every query.
- **`swap_compatible` flag** — the file's [declaration](swap-mode.md#a-files-own-swap-sequence) that it carries its own plate-swap sequence, read once from its **own file name** when it comes in (an upload, a ZIP member — the member's name, not the ZIP's —, an external folder scan, the Virtual Printer): a `.swap.` or `.swaps.` marker, e.g. `MyPart.swap.gcode.3mf` or `Tray.swaps.3mf`. The marker must be **dot-delimited**, not underscore-delimited — `MyPart_swap.gcode.3mf` will not be flagged, and neither will a marker in a folder name. Renaming the file later declares nothing; a scan reads the name again only when the file's content changed. A file without a content hash counts as **unknown** until a scan has read it. Swap-compatible files are surfaced separately in the swap-mode picker.
- **Composite `file_tags` column (m036 / m037)** — an unordered JSON list of identity tags drives the badge row on each file. Since m128 the same vocabulary also exists as `is_system` rows in `library_tags`, which is what the tag filter and the tag catalog query; the column stays as a derived cache so the badges and the preview-tab logic read a column on the row they already have. Both are written by one function, `sync_system_tags`. Four semantic groups: **format** (`gcode` / `3mf` / `stl` / `obj` / `step` — sliced `.gcode.3mf` keeps the composite `gcode + 3mf` pair so the visual distinction survives `file_type` collapse), **readiness** (mutually exclusive: `sliced` for slicer-output, `project` for unsliced `.3mf` packages, `geometry` for raw mesh / CAD source — one toggle for "what still needs slicing?"), **modifiers** (`swap` / `multiplate`), **provenance** (`makerworld`). Frontend `sortTagsForDisplay` projects onto an explicit precedence so the row reads right-to-left format → readiness → modifiers → provenance.

## :material-tag-multiple: Tags

There are two kinds of tag and one row of them.

**Automatic tags** — `3MF`, `SLICED`, `MULTI-PLATE`, `MAKERWORLD` and the rest — are worked out from the file itself. They are shown but locked: they cannot be renamed, deleted, or taken off a file, and they are not offered where you apply tags by hand.

**Your own tags** are anything you like — `kid-safe`, `petg-only`, `toys`. Create, rename and delete them from the **Tags** button in the toolbar.

Both sit in one filter row above the file list, automatic ones first. Clicking toggles, and selections AND together, so `SLICED` + `kid-safe` returns only the sliced files you have labelled that way. The filtering is done by the server, not over whatever is currently on screen, so it reaches the whole library rather than the loaded page.

An automatic tag appears in the row only when at least one file in the library carries it. Your own tags always appear, including empty ones — an unused tag is precisely the one you want to see in order to start using it.

Your own tags take at most two rows of the filter, however large the catalog: **Show all (N)** opens the full list in a box that scrolls inside itself, and **Show less** folds it back. Selected tags always come first, so an active filter is never hidden. With 13 or more tags of your own, a **Search tags** box narrows the unselected ones by name.

The selection is not remembered between visits. A library that comes back narrowed with nothing on screen explaining why costs more than one click.

### Managing tags

The **Tags** dialog lists both kinds, automatic ones in a locked section with their file counts.

- Rename in place — click the name, type, press Enter. Escape abandons it.
- Delete asks first and says how many files it will affect.
- Tick several to delete them together.
- Clicking a row does nothing else. It does not filter, and it does not close the dialog.

### Tagging one file

**⋮ → Tag** on any file opens a short list of your tags with the file's current ones ticked. A tick applies immediately; there is no confirm step. **+ new tag** at the bottom creates one and applies it in the same move.

## :material-information-outline: File details {#file-details}

**Details** in a file's menu — and the **Details** button of the preview column in the [Columns view](#columns-view) — opens the **File details** dialog. Anyone who can see the file can open it.

It shows the file's facts, read-only: **Name**, **Type**, **Size**, **Folder**, **Added by**, **Added**, **Updated**, **Hash** (shortened; hover it for the full value), **Source** when the file came with one — a MakerWorld import, for instance — and the number of **Notes**.

A file imported from [Manyfold](manyfold.md) also shows where it came from, as it was at the import: **Model**, **Creator** and **Licence**. Its **Source** is the address of the model's page in Manyfold, and **Open in Manyfold** in the file's menu opens that page.

### Your own link {#file-link}

Below the facts is **Link**: one web address of your choice for the file — a model page, a datasheet. It is kept beside **Source** and never replaces it.

- The address must start with `http://` or `https://` and be at most 2000 characters; anything else is refused.
- **Open link** opens it in a new tab; **Remove link** clears it.
- Everyone who can see the file sees the link. Setting or removing it needs the right to edit the file — your own files with `library:update_own`, any file with `library:update_all`.

### Photos {#file-photos}

The dialog ends with the file's **Photos** — pictures of the printed part, the packaging, an assembly step.

- **Add photos** picks one or several pictures; dropping pictures anywhere on the dialog adds them too. A refused picture is named with its reason and the rest are still added.
- Click a photo to open it in the [image viewer](#image-viewer). Each photo takes a **Caption** of up to 500 characters; **Delete photo** asks first.
- Viewing follows the file's visibility; adding, captioning and deleting need the right to edit the file.

| Limit | Value |
|---|---|
| Formats | PNG, JPEG, WebP |
| Size of one photo | 20 MB |
| Resolution of one photo | 40 megapixels |
| Photos per file | 30 |

**A photo is never stored as it was sent.** It is saved again in its own format, turned upright, and without its metadata — the location a phone recorded, the camera's serial number and any embedded comments are removed before anyone else can see the picture.

Photos belong to the library entry, not to the file's content: another library file with the same bytes has none, and they are not copied to a print's archive. A file in the trash keeps its photos, and restoring it brings them back; removing the file for good removes them — see [Library trash](library-trash.md).

### Marks on the card

A file with a link or photos carries small marks on its card and its list row: a globe that opens the link in a new tab, and a camera with the number of photos that opens **File details**. A file with neither shows no mark.

## :material-note-text-outline: Notes {#file-notes}

Every file has a thread of notes, opened from the notes button on its card or row; **File details** shows how many there are.

- **Notes follow the file.** Reading them needs `library:read` and the file itself to be visible to you; a file you cannot see — someone else's under "own files only" rights, or one in the trash — gives up no notes either.
- **Writing** a note needs `library:notes_write`.
- **A note is its author's**: only the author edits or deletes it.
- **A note without an author** — for example one whose author's account has been deleted — belongs to the file: whoever may edit the file (`library:update_all`, or its owner with `library:update_own`) can edit or delete it.

## :material-eye-outline: 3D / G-code viewer {#model-viewer}

It opens from **3D View** in a file's menu, or by a double click or ++enter++ on the file — see [Opening files](#opening-files). Its **Fullscreen** button is described under [Fullscreen](#fullscreen).

Library files share the same `<ModelViewerModal>` as archives, with two library-specific touches:

- **Tab visibility from `file_tags` rather than file extension.** A sliced `.gcode.3mf` (which has both extensions) shows only the G-code tab — its embedded mesh is already rasterised into the gcode lines and re-rendering it under "3D Model" duplicates information. An unsliced `project` 3MF or raw `geometry` mesh shows only the 3D tab. Tabs are queried via `GET /library/files/{id}/capabilities` (mirrors the long-standing archive route).
- **Per-plate G-code picker for multi-plate library files.** Library files are browseable, so the G-code tab gets a plate picker that re-keys the gcode-preview URL when you switch plates. Archives keep the single-plate behaviour because they record one specific print.
- **Build-volume wireframe** — the 3D viewer draws a translucent box matching the printer the file was sliced for (read from `printer_settings`). G-code preview paints a similar box, so both tabs carry the same visual cue.
- **Shared modal features** — OBJ format support, wireframe / X-ray toggle, theme-synced canvas, dual-handle layer slider (Start + End), travel-moves toggle, layer-play with 1× / 2× / 4× / 8× speeds, streaming download progress, and Export-as-PNG. See [Archives → 3D + G-code Preview](archiving.md#3d-g-code-preview) for the full feature breakdown; library uses the same `<ModelViewerModal>` verbatim.

## :material-view-gallery: Per-plate browsing (multi-plate 3MFs)

### On the card

A file with more than one plate is browsed **one plate at a time**. The card carries arrows and a plate counter, and everything on it belongs to the plate on screen: the picture, the print time, the weight, the object count, and the filament types that plate prints with (`PETG+PLA` for a two-material plate). Those types are shown on single-plate cards too.

There is deliberately no whole-file total. A file is printed plate by plate, so a sum of every plate's time beside a picture of plate 1 described a print nobody makes; the card answers *what does this plate cost* instead. Nothing is fetched to page through it — the figures ride in the file list itself.

In **list view** a row shows plate 1 and an **N plates** count. Clicking the row's thumbnail — or that count — opens the very same card in a window, where the arrows live. That window opens for any file, single-plate ones included, so the way into a file's card is the same everywhere.

### The gallery

The **Plate gallery** button opens the deeper view, on whichever plate the card was showing:

- A vertical paginator strip on the left — one button per plate, each showing the selected-state dot.
- A big card on the right with that plate's thumbnail, name, print time, total weight, instance count, and per-filament breakdown (color swatch + type + grams).
- Selection (which plates to print) is decoupled from navigation (which plate's card is visible) — you can flip through plates without touching the selection.

When dispatching, you can select one plate, multiple plates, or all of them — every selected plate becomes its own queue item / archive with the plate index recorded on the row.

Single-plate files don't render the gallery — one plate has nothing to page through.

---

## :material-link-variant: Product & folder links

- **Per-folder link** — linking a folder to one or more [products](projects.md#products) attaches every file inside to those products, and any file moved into that folder later inherits the same list.
- **Per-file link** — each file row has its own link button that opens the same chip multi-select, independently of its folder.
- **Many-to-many** — a file or folder can belong to several products at once, and a product can hold many files and folders. Linking is a *copy*, never a move: a file already linked to somebody else's product stays linked there too.
- **What the link actually does** — the product gains a plate row for every plate of the file, and every object name on those plates resolves to a printed part of that product. Unlink the file and its plates go; the parts stay, because quantities belong to the product rather than to the file.
- **Per-chip unlink** — the `×` on a chip removes that one association and leaves the rest alone.

Files do not link to a project. An order names its **products**, and a print is filed under an order when it is started or queued — see [Filing a print under its order](projects.md#filing-a-print-under-its-order).

---

## :material-delete: Trash workflow

Deleted files don't disappear immediately — they move to **Trash** and stay there for a configurable retention window (default **30 days**) before a background sweeper hard-deletes them from disk. This gives you an undo window for accidental deletions and bulk operations.

**Every route into deletion behaves the same way.** Deleting one file, deleting a selection, and deleting a folder all put the entries in the trash. Files that were inside a deleted folder come back to the **top level** of the library when restored, since the folder they lived in no longer exists.

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

A file in the trash keeps its [notes](#file-notes) and [photos](#file-photos), out of reach until it is restored; removing it for good removes them with it.

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
2. Open the row's three-dot menu and select **Rename** (a double click on the row [opens the file](#opening-files))
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

The same menu holds **Move…** — see [Moving folders](#moving-folders).

!!! note "Filename restrictions"
    Filenames cannot contain path separators (`/` or `\`). The rename API rejects these characters and the modal surfaces the error inline.

### Deleting a folder

Folders have no owner, so what deleting one needs depends on what it holds — a user who creates a folder and deletes their own files out of it does not have to ask an administrator to clear the empty shell.

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

!!! note "Who may link a folder"
    Linking names a directory of the **host**, so it is an administrator's act: it needs the right to change settings (`settings:update`), not just the right to upload. Without it **Link External** is disabled and says *Linking a folder of the host needs the permission to change settings*. An API key cannot link an external folder at all.

### Who sees external files

Files a scan finds have no owner — nobody uploaded them. They are therefore **visible to every library reader**, including users limited to their own files (`library:read_own`), who see them beside their own uploads. Changing or deleting such a file follows the ordinary edit and delete rights.

### Scanning & refreshing

External folders are indexed on creation. To pick up new or removed files:

1. Click the external folder in the sidebar
2. Click **Scan / Refresh** in the info bar
3. New files are added to the index, files removed on disk are dropped from the index

A scan reads 3MF contents, including every plate, using the same file preparation service as local uploads. A file with sliced G-code inside is marked sliced and gets **Print**, whatever it is called. Existing indexed files gain full metadata on the next scan; changed files are refreshed in place, including their plate list and preview. Unchanged files with complete metadata are skipped. The scan runs in the background in small batches, so a large or slow network share does not hold up the File Manager. Scans still start when you link a folder or click **Scan / Refresh**.

If a file cannot be read or parsed, BamDude keeps its last good metadata and tries again on a later scan. Files already in the library remain available if the preparation service is temporarily unavailable.

Starting a scan needs `library:upload`. Its progress and result can be read by anyone who can read the library (`library:read_all` or `library:read_own`).

!!! note "Renaming or moving a file on the share"
    A scan follows a file that was renamed or moved inside the external folder, or whose directory was renamed: when exactly one file is missing and one new path holds the same bytes, it stays the same library entry, with its notes, photos, tags, product links and queued jobs. Its plate-swap declaration is taken again from the new file name, so a declaration made by hand has to be repeated. A copy placed beside the original, or several new files with the same content, cannot be told apart and come in as new entries. A renamed or moved directory keeps its folder as well, with its link to products, as long as its files show where it went; an empty directory, or one whose files were split between two places or merged with another's, comes in as a new folder.

Subfolders of an external folder mirror the directories of the share: they cannot be moved or renamed in BamDude — rename the directory itself and scan the folder again.

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

External folder scanning discovers: `.3mf`, `.gcode`, `.stl`, `.obj`, `.step`, `.stp`, Markdown (`.md`), and image files (`.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.svg`).

---

## :material-link: Linking files and folders to products

**Add to order…** in a file's menu or plate gallery opens the order-line dialog with the one-off-from-a-file tab and source already selected. From the gallery, the current plate is preselected too. Choose an active order; the action requires permission to update orders and read that library file. A file moved to Trash meanwhile is refused rather than attached silently.

Right-click a folder (or use its three-dot menu) → **Link to products** to attach it to any number of [products](projects.md#products); the picker is a chip multi-select, so several products are chosen in one go. Every file row offers the same thing for a single file.

| Action | Where |
|---|---|
| **Link a folder** | Right-click on folder → "Link to products" |
| **Add / drop a product** | Open the link dialog, toggle chips on/off, save |
| **Remove one product** | Click the `×` on the relevant chip in the dialog |
| **Remove all products** | Clear every chip in the dialog and save |

Linking a **folder** *merges* its list into the files inside: what the folder imposed before is taken away, what it imposes now is added, and a file's own direct link to some **other** product survives. Moving a **file** into a folder is a different statement and *replaces* that file's product list with the folder's — including clearing it when the destination is the root or belongs to no product.

### The model card of a library file

Any `.3mf` in the library carries a **Model card** entry in its menu: the card the designer packed into the file — description, designer, licence, source page — together with the pictures, bill of materials and assembly guide it ships with, read straight off the file and shown read-only. **Nothing is ever written back into the file**, which stays byte-for-byte the file you uploaded.

From that card, **Create product from this file** turns it into a product on the spot; a file already linked to one is offered **Re-read into** that product as well, so both doors are open on the same card. See [The model card](projects.md#the-model-card).

### Printing a file asks which order it is for

**Print** and **Add to Queue** on a library file show an **Order** field — the open orders that still need this plate, how many prints each is short, and the product each is for. The first order that needs it is chosen for you, and **Without an order** is always available. See [Filing a print under its order](projects.md#filing-a-print-under-its-order).

---

## :material-api: API endpoints reference {#api-endpoints}

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
| `/api/v1/library/files/{id}/download` | `GET` | The file's bytes |
| `/api/v1/library/files/{id}/image` | `GET` | An image file's full picture, for the image viewer (media token or headers) |
| `/api/v1/library/files/{id}/external-url` | `PUT` | Set or clear the file's own link (`{"external_url": "https://…"}` or `null`) — needs the right to edit the file |
| `/api/v1/library/files/{id}/photos` | `GET` · `POST` | List the file's photos · add one (multipart) — adding needs the right to edit the file |
| `/api/v1/library/files/{id}/photos/{photo_id}` | `PATCH` · `DELETE` | Change a photo's caption · delete it |
| `/api/v1/library/files/{id}/photos/{photo_id}/image` · `/thumbnail` | `GET` | A photo, full size · its small copy (media token or headers) |
| `/api/v1/library/files/{id}/notes` | `GET` · `POST` | List the file's notes — `library:read` · add one — `library:notes_write` |
| `/api/v1/library/notes/{note_id}` | `PATCH` · `DELETE` | Edit · delete a note — `library:notes_write`, and the note must be yours or have no author |
| `/api/v1/library/generate-stl-thumbnails` | `POST` | Generate thumbnails for STL / OBJ / PDF files — `library:update_all`, or `library:update_own` on your own files |
| `/api/v1/library/folders` | `POST` | Create folder |
| `/api/v1/library/folders/{id}` | `PUT` | Rename or move a folder (`parent_id`; `0` is the library root) — `library:update_all`. A move into or out of an external folder, into itself, into its own subfolder or to a parent that does not exist is refused |
| `/api/v1/library/folders/external` | `POST` | Link an external folder — `settings:update`; not available to API keys |
| `/api/v1/library/folders/{id}/scan` | `POST` | Start a scan of an external folder — `library:upload`; answers `202` with a `job_id` |
| `/api/v1/library/scan-jobs/{job_id}` | `GET` | One scan's state and counters — `library:read_all` / `library:read_own` |

All endpoints require an authenticated session (JWT bearer or `X-API-Key` header). The required permission depends on the action — `library:read_all` / `library:read_own` for reads, `library:upload` for uploads, `library:update_all` / `library:update_own` for changes, `library:delete_all` / `library:delete_own` for deletes, `library:purge` for the bulk purge action. With the `_own` variant a user reaches their own files — and, for reading, the ownerless files of external folders. See [Authentication](authentication.md) and the full [API reference](../reference/api.md).

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

## Validation before queueing {#queue-validation}

For a sliced 3MF, the server validates the selected plate and its used channels before creating a job. Multi-plate files need an explicit plate selection; **Whole file** is accepted for one unambiguous printable plate, preserving its actual number.

Incomplete filament information, missing G-code, or missing required nozzle bindings means the file needs correction or re-slicing. A temporarily unavailable compatible printer means waiting in Auto-Queue. The form distinguishes these situations.

Grouped additions retain common options, but do not transfer one file's channel choices to another without review. AMS, external-feed, color, and repeat rules are covered in [Filament Routing](filament-routing.md).

Optional dense layout search and arbitrary in-plane rotations are described in [Assemble project](assemble-project.md).
