---
title: Auto-Queue Routing
description: Route prints by exact model, complete filament requirements, and the current AMS and external feed configuration
---

# Auto-Queue Routing

Auto-Queue distributes work into per-printer queues. Choose the file, plate, and print rules; the router finds a printer of the exact model that can supply every used filament channel.

Printers of the same model with and without AMS are checked against their actual configurations. See [Filament Routing](filament-routing.md) for the complete rules, multicolor and dual-nozzle examples, and waiting reasons.

## :material-router-network: How it works

1. On submission, BamDude validates the selected plate in the sliced 3MF, its matching G-code, model, and used channels. A source error blocks adding the job; a temporary lack of compatible printers does not.
2. The background router reads pending work in queue order, or SJF order when enabled.
3. It looks for a printer of the required model and location with a complete suitable set of feeds. Each used channel needs its own source.
4. Among eligible printers, one ready to start wins. The job moves to that printer's queue with its routing rules; if no candidate exists, the panel shows a waiting reason.
5. The printer queue applies its usual plate-clear, drying, staggered-start, and swap-macro gates. Filament and source checks run again before the actual start command.

## :material-sort-numeric-ascending: SJF + starvation guard

When **Queue Shortest First** is enabled (Settings → Printing → Queue & Scheduling → Auto-Queue Routing → Queue Shortest First), pending rows are sorted by:

```
ORDER BY been_jumped DESC,
         estimated_print_time_seconds ASC,
         position ASC
```

The `been_jumped` sticky bit prevents starvation: every time SJF promotes a shorter print *past* a longer one, the longer one gets `been_jumped=True` and floats to the top of the next round regardless of its print time. This way a 14 h print can't sit indefinitely behind a stream of 30-min jobs.

When the toggle is off, items dispatch in FIFO order (by `position`).

---

## :material-cog: Settings

**Settings → Printing → Queue & Scheduling → Auto-Queue Routing**:

| Setting | Effect |
|---------|--------|
| **Queue Shortest First** | Enables SJF + the starvation guard. Default: off (FIFO). |

The router itself is **always on** — there's no master switch. If no auto-queue items exist, the scheduler is a 30 s no-op.

---

## :material-plus-circle: Adding to the auto-queue

Choose the entry point that fits your workflow:

### 1. Print Modal — "Auto" toggle

Open Print for a library file or archive and choose **Auto**.

| Field | Meaning |
|---|---|
| Target Model | The exact model from the sliced file. An empty selection means detect it from the 3MF, not allow any model. |
| Target Location | An optional printer-location restriction. |
| Filament source | Automatic: AMS or external spool; AMS only; External spools only. |
| Force exact color match | Off by default: exact colors are preferred, but another color is allowed. Material, known variant, and nozzle requirements remain. |
| Plate channels | Material and color for each used channel; **Require this color** pins one channel's color. |

Below the fields, **AMS connected / Without AMS / AMS state unknown** groups show compatible and ready counts separately, with reasons. A valid job may be added with zero counts and wait. A source-reading error must be resolved before adding it.

For a **library file**, the same dialog carries an **Order** field — the open orders that still
need this plate, ranked so the ones that need it come first (a reprint from an archive keeps the
original print's own filing, so it is not asked again). Choosing one files the item under that order and, where the
plate belongs to exactly one of its lines, under that line too, so the order's plan stops asking
for work you have already queued. **Without an order** is always available. See
[Filing a print under its order](projects.md#filing-a-print-under-its-order).

### 2. Virtual Printer `auto_queue` mode

Slicer "Send to Printer" → VP saves the file in the library → validates its plate → adds it to Auto-Queue. See [Virtual Printer → auto_queue](virtual-printer.md#auto_queue) for the UI side.

The router chooses the machine under the job's rules. Plate-clear confirmation and the other start gates still apply.

### 3. Drag-and-drop on the Auto-Queue panel

Drop **as many sliced files as you like** anywhere over the **Auto-Queue panel** at the top of the Queue page. Each is uploaded into the library root, and then the files that would be answered the same way are grouped — one Print Modal per group, with a `group 1 of 3 · 12 items` badge — locked to **Auto** mode (no specific/auto toggle, no printer picker, the Auto rules: model, location, filament source, and colors).

**Each item's target model is pinned to that file's own `sliced_for_model`, and cannot be changed.** Per file, not per run: two files sliced for two different machines keep two different targets in one drop. Setting it explicitly rather than leaving it blank matters — blank means "work it out from the 3MF", which usually lands on the same answer but shows nothing on screen where the constraint is, so a run of ten files would say nothing about what any of them is waiting for.

**A file with no recorded model is refused**, by name, before the dialog opens. There is nothing to pin and nothing to verify; queueing it on a guess would leave an item waiting for a machine nobody chose.

The auto-mode form no longer offers a target the file cannot run on either. Choosing a mismatched model never failed — it produced an item waiting for a printer that would never take it, with nothing explaining the wait.

The **Load from library** button on the panel opens the same [file picker](print-queue.md#load-a-queue-from-the-library), with every printable file offered rather than one machine's worth.

Permission-gated on `queue:create`. The panel renders even when empty so the drop target is permanently available; an empty-state hint nudges first-time operators.

Channel-specific choices belong to the file: after such an answer, the next file in the group opens for review.

### 4. REST API

```http
POST /api/v1/auto-queue/
{
  "library_file_id": 42,
  "target_model": "P1S",
  "plate_id": 1,
  "feed_policy": "external_only",
  "force_color_match": false
}
```

Full schema in [API reference](../reference/api.md). Quantity > 1 creates N rows in one call (same `batch_id` semantics as `print_queue`).

### 5. Order plans and Telegram

An [order plan](projects.md) can send one row or the whole plan to Auto-Queue; plate validation happens before queue items are created. Telegram uses the same source validation. A large quantity does not relax color or feed rules.

---

## :material-monitor-dashboard: AutoQueuePanel on the Queue dashboard

The Queue page has an **Auto-Queue panel** above the per-printer queue cards. **Always rendered** so the drop-zone is permanently available; when there are no pending auto items the panel collapses to a one-line hint inviting a drag-drop.

Since **0.5.5** the panel is a real queue, not just a pile:

- **Items list in true dispatch order.** Adjacent copies of one submission collapse into a compact **×N** row; the row expands into its individual copies.
- **Everything drags.** A collapsed batch moves as a block, an expanded copy moves anywhere in the order — queue five copies of A, add two of B, pull one B to the front and leave the other at the end, and the list shows exactly that. With **Queue Shortest First** enabled the drag handles hide and a hint explains that the distributor owns the order.
- **Every copy edits in the full Schedule dialog** — the same one the per-printer queue uses: target model and location, schedule, print options, macros. Editing a batch applies the change to all of its copies at once; a single copy can also be edited, deleted or force-assigned on its own.
- Each row still shows thumbnail, name, plate, target model, estimated print time and the waiting reason when no printer is eligible.

Once an item is assigned to a printer, it disappears from the panel and shows up in that printer's queue card with a small "auto-assigned" badge.

---

## :material-filter-variant: Eligibility rules

The printer must be active, unarchived, available to the router, and free to take new work. The route icon on its queue card lets you opt it out of automatic assignment without stopping its ordinary queue.

It needs the exact model, the selected location, and a **complete mapping for every used channel**: material, known variant, nozzle, source rule, and required colors. One PLA slot does not satisfy two PLA channels. Manual physical selections cannot move arbitrarily between printers.

Among eligible candidates, readiness comes first, then the best color match. See [Filament Routing](filament-routing.md#channels) for worked examples.

!!! note "«Drain the emptiest spool first» picks the tray, not the printer"
    `prefer_lowest_filament` plays no part in choosing **which printer** gets the
    job. It decides, on the printer already chosen, **which of its slots** an
    equally-good match is mapped to: the one with the least filament left, so a
    nearly-empty spool is burned down instead of a fresh one. The same switch
    governs automatic matching for print-dialog and virtual-printer jobs.
    An explicit physical slot selection is retained instead of ranked again.

    It is off by default and lives under **Settings → Filament → Filament
    checks → «Drain the emptiest spool first»**. On BamDude's own dispatch paths
    — this router and the queue scheduler — it is additionally skipped for a
    printer whose **AMS Filament Backup** is off; see
    [Print Queue](print-queue.md) for why.

### Color and filament variant

Color and variant are checked separately. Two known PLA variants do not become interchangeable when exact color matching is off. If a variant code is not reported, known material, color, and other requirements are checked; the missing code is not invented. See [Choosing colors](filament-routing.md#colors).

---

## :material-directions-fork: Routing is not dispatching

Choosing which printer a job belongs to and deciding when it may start are two different questions, answered in two different places.

The router only answers the first. It will hand a job to a printer that cannot start right now — one waiting for a **Clear Plate** confirmation, mid plate-change, drying, or held by staggered start. The job then sits **visibly** in that printer's queue until the printer is ready, and every safety check still applies at the moment it actually matters.

Before **0.5.1.2** the router refused to route to such a printer at all. That sounded safer and was not: the printer's queue stayed empty, so nothing on screen explained the hold-up, and the **Clear Plate** prompt — which appears on a printer's queue — never had a chance to show. Operators saw idle machines reported as busy and a farm that looked dead. Placing the work is what makes the reason visible.

A printer that *is* ready still wins when there's a choice.

---

## :material-fire-off: Drying takes lower priority than a print

[Queue Auto-Drying](ams.md#queue-auto-drying) keeps idle spools dry between prints. When **Settings → AMS Display Thresholds → Queue Auto-Drying** is in its default **non-blocking** mode (`queue_drying_block=false`, *"prints take priority over drying"*), a job queued **directly** to a printer already stops an in-progress dry cycle and starts printing.

The auto-queue router behaves the same way, and since **0.5.1.2** it does so by *ranking* rather than excluding: a printer that is free to take work but currently drying still receives jobs, it simply loses to one that can start immediately. The per-printer dispatch then stops the dry cycle and begins the print (the same `_stop_drying` step described in [AMS → Queue Auto-Drying flow](ams.md#queue-auto-drying)).

When Queue Auto-Drying is set to **blocking** (`queue_drying_block=true`), drying still holds the queue — the job waits in that printer's queue until the dry cycle ends, exactly as a directly-queued item would.

!!! note "Behaviour added in 0.4.5"
    Before 0.4.5 the auto-queue treated a drying printer as plain "busy" and skipped it, so an auto-routed job could sit waiting behind a dry cycle even though a directly-queued job would have taken priority. This is most noticeable on P2S / H2 farms with AMS auto-drying enabled.

---

## :material-clipboard-text: AMS mapping at assign time

Mapping is computed from the chosen printer's current sources and the job's saved rules. The printer-queue item keeps those rules independently of the original Auto-Queue row.

Checks repeat before preparation and immediately before the start command. A changed spool, connection, file, or current job can return the print to waiting with a reason; a partial mapping is not sent. See [Before printing](filament-routing.md#before-printing).

## :material-link-variant-off: Cancel / edit semantics

| Action | Effect |
|--------|--------|
| Cancel a `pending` auto-queue item | Row deleted. No printer ever saw it. |
| Cancel an `assigned` auto-queue item | Cancels the **per-printer queue item** the router created. The auto row stays in `assigned` for audit. |
| Edit a `pending` item | The full Schedule dialog — target model / location, schedule, print options, macros. A batch edit applies to every copy; a single copy edits alone. |
| Edit after assignment | Edit the per-printer queue item instead. |

---

## :material-lightbulb: When to use it

| Use case | Recommendation |
|----------|----------------|
| Single printer | Skip the auto-queue, use the regular per-printer queue — no router overhead, simpler UI. |
| 2-3 printers, one model | Auto-queue is great for load-balancing — drop jobs in, the scheduler picks the next free one. |
| Mixed-model farm | Auto-queue with explicit `target_model` per job — same load-balancing within the model, no cross-pollination. |
| Color-critical jobs (logos, signage) | Turn on `force_color_match` so a job won't dispatch to a printer with the wrong color loaded. |
| Hands-off slicer flow | VP `auto_queue` mode + auto-queue → routing under the job's rules with the usual start gates. |

---

## :material-history: Migration from per-printer queues

Per-printer queues remain the way to choose a specific machine; Auto-Queue defers that choice. Both paths apply complete filament checks before starting.

After an upgrade, older jobs retain established source restrictions and physical selections. If there is not enough saved evidence to recover their rules, mapping review is required. Schedule edits, copies, and repeats retain the rules; a different printer or plate requires a new answer for a manual mapping. See [Editing and repeats](filament-routing.md#editing).
