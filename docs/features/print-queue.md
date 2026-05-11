---
title: Per-Printer Queues
description: Independent print queues per printer with scheduling and automation
---

# Per-Printer Queues

Queue and schedule prints with independent per-printer queues, drag-and-drop ordering, batch quantity, and smart automation.

---

## :material-playlist-plus: Overview

The print queue lets you:

- **Queue prints** from archives or the file manager
- **Per-printer queues** -- each printer has its own independent queue
- **Batch quantity** -- print multiple copies at once (every copy lives in the queue, no special "primary" copy)
- **Drag-and-drop** ordering
- **Scheduled** start times
- **Timeline view** -- production schedule with estimated completion times
- **Model-based assignment** -- queue to "any printer of matching model" (legacy single-tier router; for filament/color-aware routing see [Auto-Queue Routing](auto-queue.md))
- **Smart plug automation** -- auto power-on/off

---

!!! warning "SD card required"
    Bambu printers fetch the active job from internal SD storage. **An SD card is mandatory** — without one, every dispatch fails at the FTP-upload step. A1-mini owners often run without one; that printer model can't drive the queue.

---

## :material-list-status: Queue states

Every queue item carries one of these statuses (visible on the queue card chip):

| State | Meaning |
|-------|---------|
| `pending` | In line, will start when the printer is free + scheduled time hits |
| `printing` | Currently dispatched + running |
| `paused` | Print is paused on the printer (operator paused, filament runout, AMS issue) |
| `waiting_for_filament` | Held back because the required filament/colour isn't loaded |
| `waiting_for_plate_clear` | Print finished, waiting on plate-clear confirmation before next dispatch |
| `waiting_for_stagger` | Multi-printer batch — waiting for the staggered-start tick |
| `waiting_for_dispatch` | Dispatcher is in flight (FTP upload + MQTT start_print) |
| `failed` | Dispatch or print failed; verbose `error_message` on hover |
| `cancelled` | Cancelled by user before completion |
| `skipped` | Auto-skipped after a previous failure on the same job |
| `completed` | Print finished — auto-deletes once the matching archive lands (m019) |

The queue card header shows live counters (Total / Pending / Printing / Completed / Failed / Cancelled) recomputed from `print_archives` on every read.

---

## :material-plus: Adding to Queue

### From Archive

1. Go to **Archives** page
2. Click the **Schedule** button on the archive card
3. Choose target printer(s)
4. Optionally configure filament mapping
5. Print is added to queue

### From File Manager

1. Select sliced files in **File Manager**
2. Click **Add to Queue** in toolbar
3. Choose target printer

### Drag-and-drop on a Queue Card

On the **Queue** page each printer's queue card is a drop target. Drag a sliced file (`.gcode` or `.gcode.3mf`) onto the card → the file is uploaded into the library root, then the Add-to-Queue modal opens locked to that printer (no specific/auto toggle, no printer picker — the drop target *is* the choice). Configure plate / AMS / schedule and submit. The card's printer status (idle / printing / paused / error) is **not** checked: queueing is always allowed regardless of what the printer is currently doing.

A `sliced_for_model` mismatch with the card's printer model aborts the upload before the modal opens — the transient library row is rolled back and a toast surfaces the conflict so you can re-slice for the right printer.

Permission-gated on `queue:create` — viewers without that right see no overlay and a drop is a no-op.

### AMS Filament Mapping

When adding multi-color prints, configure which AMS slot to use for each filament. Auto-matching by type and color is available, with manual override.

!!! tip "Stored Mappings"
    AMS mappings are saved with the queued print. When it starts, BamDude uses your configured mapping.

**Dual-nozzle printers (H2D / H2D Pro)** show **[L] / [R]** badges next to each AMS slot so you can see which extruder a slot feeds. The auto-matcher uses the slicer's `sliced_for_model` + per-slot filament metadata; falling back to manual when the printer doesn't have an exact filament match for what the gcode wants.

**Prefer lowest remaining filament** (Settings → Workflow): when the auto-matcher has more than one candidate slot for the same filament, BamDude picks the slot with **the lowest tracked remaining grams** so you burn down nearly-empty spools first instead of always using slot 1.

### Plate selection (multi-plate 3MF)

Multi-plate sliced 3MFs ship every plate inside one file. The Add-to-Queue modal renders a plate grid:

- Click a single plate to dispatch just that plate (queue row gets `plate_index = N`).
- Multi-select plates → one queue row per plate, queued in order.
- The thumbnail + per-plate filament list comes from the m023 plate cache (no re-parse on each render).

Plate index is preserved across restart-recovery + reprint flows. See [archiving](archiving.md) for chain-of-custody on multi-plate dispatches.

### Print options

When adding to queue, expand **Print options**:

| Option | Default | What it does |
|--------|---------|--------------|
| **Use AMS** | `on` | Route filament from AMS instead of external spool. Off = printer expects manually-fed filament. |
| **Bed levelling** | `on` | Run the auto-bed-level cycle before the print. Off speeds up restarts on a known-stable bed. |
| **Flow calibration** | off | Run extrusion-flow cal at print start. Print-quality first vs throughput trade-off. |
| **Vibration calibration** | off | Run vibration-resonance cal. Disabled for fast iteration on identical jobs. |
| **Mesh-mode fast check** | off | Skip the M970 vibration-probe G-code via the [3MF gcode patcher](archiving.md). Disk file stays unpatched; only the bytes shipped to the printer are modified. |
| **Layer inspection** | `on` | Per-layer first-layer inspection AI (X1 + H2 series). |
| **Timelapse** | off | Record a built-in timelapse on the printer. |

Defaults are install-wide and configurable in **Settings → Workflow → Default print options**. Per-printer overrides live on each printer's settings card. Per-job overrides on the Add-to-Queue modal trump everything.

### Auto-print G-code injection

Sometimes you need to mutate the gcode at dispatch — chamber heat-soak, custom purge, swap-mode setup — without re-slicing. Toggle **G-code injection** on the queue item; configure snippets + placeholders (`{max_layer_z}`, `{first_layer_temp}`, etc.) in **Settings → Workflow → G-code injection**.

Full reference: [G-code injection](gcode-injection.md). Reads + applies at dispatch time so different jobs can carry different injections.

!!! warning "Z-safety"
    Injecting absolute Z-moves before the auto-Z-home that Bambu firmware does at print start can crash the head into the print. Use the placeholders (they expand against the slicer's first-layer plan) instead of hard-coded numbers.

### `created_by_id` audit

Adding to queue records *who* added the item. The Telegram bot, library bulk-add, per-printer "Print" button, and File Manager prints all propagate the acting user. Visible per row on the archive that the queue item produces. The VP auto-queue and webhook trigger paths legitimately leave it `NULL` (no authenticated user to attribute).

---

## :material-drag: Drag and Drop Ordering

1. Hover over a queued print
2. Grab the drag handle
3. Drag to new position
4. Prints execute top to bottom

---

## :material-clock-outline: Scheduling

### Immediate

Default. Job starts as soon as the printer is idle and the dispatcher reaches it. The queue is processed strictly in `position` order — **except for** Shortest-Job-First mode (below).

### Scheduled

Pick a future date + time. The job stays in `pending` until the scheduled clock hits, then enters dispatch. Works in combination with smart-plug power-on schedules — the plug fires N minutes before the scheduled start so the printer's warm by the time dispatch hits.

### Schedule priority

When two scheduled jobs hit overlapping times, BamDude orders them by:

1. Manually-pinned `position` (drag-and-drop)
2. Earliest `scheduled_at`
3. Insertion order (FIFO)

### Queue only (staged)

Sets `manual_start = true` on the row — the dispatcher ignores it until you click Start. Useful for staging an entire batch upfront and then releasing it in one go (or for slicer-uploads-to-VP that you want to hold until you've reviewed them).

### Shortest job first (SJF)

**Settings → Workflow → Job ordering = Shortest first** flips the dispatcher to pick the shortest pending job (by predicted print time) instead of the highest-priority one. Comes with a **starvation guard**:

- Each pending job gains an `aging_score` over time
- Once a job has been waiting > **N hours** (default 6, configurable), it's promoted to top of the dispatch queue regardless of duration

This keeps a long farm-printable from sitting forever behind a stream of short jobs while still letting fast jobs slip in between long ones during the day.

---

## :material-cancel: Managing Queue

### Clear Plate Confirmation

After a print finishes, the next print does **not** start automatically. A **"Clear Plate & Start Next"** button appears on the printer card.

Disable this in **Settings > Queue > Require plate-clear confirmation** for automated workflows.

### Bulk Editing

Select multiple queue items via the toolbar checkboxes to apply a bulk edit:

| Field | Tri-state on bulk | Notes |
|-------|-------------------|-------|
| Target printer | ✓ | Reassigns rows. Filament/colour validation runs against the new target. |
| Use AMS | ✓ | Tri-state — leave indeterminate to preserve per-row settings. |
| Bed levelling / Flow / Vibration / Layer inspect / Timelapse | ✓ | Same tri-state semantics. |
| Scheduled-at | ✓ | Bulk-shift schedules forward by an offset, or pin a fixed clock. |
| Cancel | — | Bulk-cancel marks all selected as `cancelled` (no force on currently `printing` rows — those need an explicit per-row Cancel). |

---

## :material-printer-3d-nozzle-alert: Multi-printer queue + staggered start

When you submit one job to **N printers** at once (multi-select in Add-to-Queue), each gets its own queue row. By default they all dispatch immediately — N concurrent FTP uploads, N near-simultaneous start commands. For overhead-constrained farms (single network uplink, single power circuit, shared MQTT broker), enable **Staggered batch start**:

| Setting | Effect |
|---------|--------|
| **Group size** | How many printers fire per wave (e.g. 3 = three at a time, then a pause) |
| **Interval** | Seconds between waves |

Cross-link: full deep-dive in [Staggered start](staggered-start.md).

Per-printer **AMS mappings** are configured per row — the multi-printer modal lets you reuse the same mapping, or pick a different slot per printer when AMS contents differ across the fleet.

---

## :material-router-network: Model-based queue assignment ("Any X1C")

Instead of pinning a job to a specific printer, queue it under **Any [model]**:

- Filament-aware: the scheduler refuses to dispatch onto a printer whose AMS doesn't have the right filament type loaded (and colour, when [Force colour match](virtual-printer.md#auto_queue) is on)
- Location-aware: optional location filter ("any printer in Workshop A")
- **Manual filament override**: if no eligible printer matches automatically, set a manual mapping that the queue uses regardless

When no eligible printer is free, the row sits as `waiting_for_filament` until either:

- An eligible printer goes idle
- You manually reassign the row to a specific printer
- You acknowledge the warning and force-dispatch onto a non-matching printer

For multi-tier filament + colour routing across the whole farm, prefer the **auto-queue router** — see [Auto-Queue Routing](auto-queue.md) for the full priority chain.

---

## :material-timeline-text: Timeline view

Click **List / Timeline** at the top of the queue page to flip into a Gantt-style production schedule:

- One row per printer, time on X-axis
- Each block is a queue item sized by predicted print time + ETA chaining (block N starts when block N-1 ends)
- Day navigation buttons (prev / today / next), filters mirror the list view
- Hover a block for full job details

ETA chaining is a planning tool — it doesn't account for clear-plate confirmation gaps, manual pauses, or filament loads, so real wall-clock will drift longer. Useful for "which printer is the bottleneck this week" answers.

---

## :material-power-plug: Smart plug automation

When a printer has an associated smart plug, the queue can drive power state:

- **Auto power-on** — plug turns on N minutes before the next scheduled job (configurable in **Settings → Smart Plugs → Pre-warm offset**)
- **Auto power-off** — plug turns off N minutes after a printer goes idle with an empty queue + cooldown (default 30 min, configurable)
- **Cooldown awareness** — the plug stays on while the printer reports `bed_temp` or `nozzle_temp` above threshold even after the last job ends

Full setup + per-printer linking → [Smart plugs](smart-plugs.md).

---

## :material-bell-outline: Queue history

Once a job's archive lands, the queue row auto-deletes (m019). To find old queue items:

- **Archives** page filtered by printer — every archive carries `queue_id` + optional `batch_id`
- Failed dispatches surface their verbose `error_message` on hover
- Bulk-print plans launched from a project also stay attributable via `queue_id` linkage

---

## :material-api: API access

Programmatic queue control via REST:

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/print-queue/` | List all queue items (filterable by printer, status) |
| `POST /api/v1/print-queue/` | Add a new queue item from an archive or library file |
| `PATCH /api/v1/print-queue/{id}` | Edit position, schedule, AMS, options |
| `DELETE /api/v1/print-queue/{id}` | Cancel + remove |
| `POST /api/v1/print-queue/{id}/start` | Force-start a `manual_start` or `pending` item |
| `POST /api/v1/print-queue/bulk` | Bulk submit / edit / cancel |
| `POST /api/v1/print-queue/reorder` | Drag-and-drop reorder via API |

Full schema + auth details: [API reference](../reference/api.md).

---

## :material-printer: Multi-Printer Selection

Send the same print to multiple printers at once:

1. Open **Add to Queue** modal
2. Select multiple printers using checkboxes
3. Configure per-printer AMS mapping if needed
4. Submit to all

---

## :material-counter: Batch quantity > 1 — single source of truth

When you set quantity to **N**, **all N copies** are added to the queue at once. They share a `batch_id` (a UUID stamped on every copy) so you can still answer "how many of this batch finished?" after the live queue rows clean up.

- You can reorder, edit AMS, or cancel each copy individually before it starts.
- The very first copy doesn't get "direct dispatched" any more — every copy goes through the same queue path. This eliminates the historical "first archive lands ahead of N-1 copies still in queue" inconsistency.
- The endpoint response status is `"queued"` for the whole N-copy submission; `dispatch_job_id` and `dispatch_position` are nullable in this path.

`quantity == 1` direct dispatch (Print Now from a single archive) keeps the legacy behaviour — one queue item, one immediate dispatch.

---

## :material-database-arrow-right: Dispatch behaviour {#dispatch-behaviour}

Background dispatch runs **in parallel across printers** — three idle printers with three queued items get all three started effectively at the same time.

!!! info "What's serialised, what's parallel"
    The brief DB-write phase (`INSERT INTO print_archives`) sits behind a startup-lock so SQLite doesn't trip on `database is locked` from concurrent inserts. The lock is held only for the few milliseconds the row needs to commit; FTP upload, the `start_print` MQTT command, and any swap-mode macros run in parallel with whatever the next dispatcher does. PostgreSQL inherits the same lock for symmetry, even though it doesn't strictly need it.

The active-job toast in the bottom-right tracks each dispatch independently — multiple FTP-upload progress bars can be on screen at once. Once a print is *running* on a printer, that dispatcher releases its slot; the dispatch tracker doesn't wait for the print to **finish**, only for the upload + start command to land.

The earlier "one job at a time across the whole farm" gate that landed in mid-0.4.1 was scrapped once the startup-lock was in (`c485db1`).

---

## :material-cancel: Cancel during dispatch — what happens to the queue

Cancelling a print **while the dispatcher is still uploading the 3MF or sending `start_print`** (the brief window between you clicking Print Now / queue dispatch firing and the printer reporting `RUNNING`) is treated as an explicit operator action — not a dispatch failure.

| Slice | Queue item status | Queue state | Archive status |
|---|---|---|---|
| Cancel arrives during FTP upload / MQTT start | `cancelled` | `paused` | `cancelled` |
| Dispatcher hits an actual error (FTP timeout, start-print refused) | `failed` | `error` | `failed` |
| Cancel arrives after print is `RUNNING` on the printer | n/a (handled by stop-print path) | running | per stop-print outcome |

The semantic distinction matters: the queue moving to `paused` (not `error`) tells the operator that **nothing failed** — the rest of the queue is fine, they decided to abort one item. They can inspect the remaining items and resume the queue when ready. Before this distinction was wired in, a cancel during the dispatch window left the queue in `error` with the just-cancelled row marked `failed`, which was misleading.

Cancelled queue rows live alongside failed and skipped rows in the queue card's **Issues** section so they don't clutter the live `pending` list but stay visible for retry.

### :material-restart: Restart a cancelled item

Every cancelled item in the Issues section gets a **Restart** button (`RotateCcw` icon) that:

- Resets the item's `status` back to `pending`.
- Re-appends it to the **end** of the queue (so it doesn't jump ahead of anything you queued in the meantime).
- Leaves the archive trail intact — the old cancelled archive stays for forensics; a fresh `printing` archive is created when the item actually dispatches.

The same `POST /api/v1/print-queue/{id}/retry` endpoint that powers the failed-item Retry button also handles cancelled items — it now accepts both `failed` and `cancelled` as source states. The bulk-restart from the Issues section uses `POST /api/v1/print-queue/bulk` with the same retry verb.

---

## :material-history: Queue history & archives

In 0.4.0 the live queue and the durable history were split apart (migration `m019`).

- The **live queue** only shows unfinished items: `pending`, `printing`, `paused`, `waiting_*`, plus failed / cancelled / skipped rows kept around so the "Issues" section retry/unskip/remove UI keeps working.
- Completed queue items **auto-delete** once their archive lands. `on_print_complete` removes the queue row after the corresponding archive transitions to `completed`.
- Past queue items live on as **archives** — every archive row carries `queue_id` (which queue dispatched it) and optional `batch_id` (which N-of-M batch it belongs to). External / direct-dispatch / Print-Now archives fall back to the printer's default queue id so they're attributable too.

The queue counters in the printer queue header (Total / Pending / Printing / Completed / Failed / Cancelled) are **recomputed from `print_archives` on every read**, not stored on the queue. They stay consistent even when archives are renamed or moved between projects, and they don't drift when the queue auto-cleans.

To see archived queue items, open the **Archives** page and filter by printer. Failed dispatches show the verbose `error_message` on hover (short cause codes continue to live in the existing `failure_reason` field).

!!! tip "Dispatch-time archive starts as `printing`"
    Library-file dispatches now create the archive row directly in `status='printing'` — no transient "Archived" badge flash during the FTP+MQTT window. If dispatch fails after the row commits (FTP error, start-print error), a fresh-session helper flips the archive to `failed` / `cancelled` with the verbose `error_message` set, so a zombie `'printing'` row never sits stuck in the UI.

---

## :material-link-variant-off: Library file deletion — what happens to queue items

The `print_queue.library_file_id` foreign key is `ON DELETE SET NULL` (migration `m018`). On top of that, the `DELETE /library/files/{id}` endpoint applies extra in-app logic so SQLite installs (where `PRAGMA foreign_keys` is off by default) get the same behaviour as PostgreSQL:

| Queue item references the file | Result |
|---|---|
| Currently `status='printing'` | API returns **409 `file_in_use`** with `queue_item_ids[]`. Cancel or finish those prints first, then retry the delete. |
| Anything else (`pending`, `paused`, `waiting_*`, etc.) | BamDude **cascade-deletes** the queue items along with the library file. |

Archives keep their separate 3MF copy (the dispatch flow copies the bytes into the archive directory at print start) and survive — `print_archives.library_file_id` is set to NULL on delete instead of cascading.

`POST /library/bulk-delete` applies the same logic per file: blocked-by-printing files are reported under `skipped_files` instead of failing the whole batch.

!!! note "Pre-0.4.0 behaviour was different"
    Earlier versions used a SET NULL FK without the in-app cascade — deleting a library file left orphan queue items pointing at nothing, which the queue couldn't dispatch. Those rows had to be manually cleaned. m018 + the in-app cascade close that hole.

---

## :material-bell-ring: Queue Notifications

| Event | Description |
|-------|-------------|
| **Job Waiting** | Job waiting for filament |
| **Job Skipped** | Job skipped due to previous failure |
| **Job Failed** | Job failed to start |
| **Queue Complete** | All queued jobs finished |

Configure in **Settings > Notifications**.

---

## :material-shield-check: H2D false-reprint guard

H2D Pro firmware (01.01.00.00 series) keeps `gcode_state=FINISH` for 48–55 seconds after accepting a new file before transitioning to `PREPARE`. The scheduler watchdog used to revert queue items to `pending` at 45 s if the state hadn't moved — and the next scheduler tick re-dispatched the job as a "reprint" the printer was already physically running.

The dispatcher now waits up to **90 s** for `subtask_id` to advance past the pre-dispatch value (the printer echoes the `submission_id` BamDude minted in its next `push_status` — that signal lands long before `gcode_state` does on slow firmware) before failing the dispatch. The watchdog also short-circuits as soon as the new `subtask_id` shows up, regardless of whether `gcode_state` has caught up.

You won't see "queue stuck" reports from this any more, including immediately after a print completes on H2D / H2C / H2S models.

---

## :material-lightbulb: Tips

!!! tip "Overnight Prints"
    Schedule longer prints to start overnight -- wake up to finished prints.

!!! tip "Smart Plug Combo"
    Combine scheduling with auto power-off for hands-free operation.

> Originally based on [Bambuddy](https://github.com/maziggy/bambuddy) documentation.
