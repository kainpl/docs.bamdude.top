---
title: Auto-Queue Routing
description: Route prints by model compatibility, complete filament requirements, and the current AMS and external feed configuration
---

# Auto-Queue Routing

Auto-Queue distributes work into per-printer queues. Choose the file, plate, and print rules; the router finds a printer that accepts the file and can supply every used filament channel. Exact-model routing is the default. An optional fallback also considers compatible models from Bambu Studio's directed `compatible_machine` data.

Compatibility is checked from the **target printer's** Bambu Studio configuration: a printer accepting a file from another model does not imply the reverse. A P1P with its upgrade kit confirmed by live status uses P1S for this check. The physical nozzle, rack, filament, and build-plate checks still apply. Manual selection of a compatible printer is allowed with a warning; a known incompatible model is refused.

Printers of the same model with and without AMS are checked against their actual configurations. See [Filament Routing](filament-routing.md) for the complete rules, multicolor and dual-nozzle examples, and waiting reasons.

## :material-router-network: How it works

### Self-contained queued files

When BamDude accepts a job it takes one verified immutable copy of the actual bytes into `data/queue-sources/`. Routing, preparation and upload read that copy from then on. A laptop can sleep, an SMB share can disconnect, an external library file can move or be deleted, and archive retention can run without changing work already in either queue. Identical bytes queued many times are stored once. The shared copy is released only when its last printer-queue or Auto-Queue job is removed. Portable backups include the ready queue copies named by their database snapshot, so a restored farm does not need the original folders. The `staging/` subdirectory contains unfinished copies only; it is never queued or backed up.

A row that has no captured copy of its own is a legacy row until a later operation captures it. A missing or checksum-mismatched snapshot, or a vanished legacy source, produces **File error** and is skipped. Other jobs continue; the printer queue is not paused and no failed physical print is counted. Failed AutoQueue jobs remain visible with **Retry** and removal actions; printer queues show them under Issues. Restore access only for a legacy row, then retry explicitly. A ready snapshot never retries an old NAS path.

### Assignment

1. On submission, BamDude validates the selected plate in the sliced 3MF, its matching G-code, model, and used channels. A source error blocks adding the job; a temporary lack of compatible printers does not.
2. The background router reads pending work in queue order, or SJF order when enabled.
3. It looks for a printer of the required model and location with a complete suitable set of feeds. With compatible-model fallback enabled, a compatible printer is considered when no ready exact-model printer can run the file. Each used channel needs its own source.
4. Among eligible printers, a ready exact-model printer wins; otherwise a ready compatible printer may win. The job moves to that printer's queue with its routing rules; if no candidate exists, the panel shows a waiting reason.
5. The printer queue applies its usual plate-clear, drying, staggered-start, and swap-macro gates. Filament and source checks run again before the actual start command.

An active print or a due job that can start automatically keeps the printer out of the next placement pass. A future job or one waiting for manual start leaves the printer available. With equal readiness, model fit and colour match, the router prefers a printer without those jobs. *Assign now* keeps the job's scheduled time on the chosen printer, which can take another AutoQueue job before that time.

Each placement is its own short step, checked against the job as the router read it. A job edited, staged, rescheduled or cancelled in that moment is not placed with its old settings — it waits for the next pass. A reorder is not part of that check: it waits for the placement and then changes the positions of the jobs still waiting, and the placed job keeps its printer. A job is placed only on the printer the router checked — one deleted and replaced by a new printer under the same number meanwhile gets nothing, in the automatic pass and with *Assign now* alike. A placement that fails leaves the placements made before it in the same pass in place.

Both the automatic pass and *Assign now* require the queue identity from the eligibility check. If that identity is missing, the job stays in AutoQueue unless another eligible printer can take it. *Assign now* returns `409` if no eligible printer remains.

## :material-sort-numeric-ascending: SJF + starvation guard

When **Shortest job first** is enabled (**Settings → Printing → Queue & Scheduling → Auto-Queue Routing → Shortest job first**), pending rows are sorted by:

```
ORDER BY target_model,
         been_jumped DESC,
         print_time_seconds ASC NULLS LAST,
         position ASC
```

The `been_jumped` sticky bit prevents starvation: every time SJF promotes a shorter print *past* a longer one, the longer one gets `been_jumped=True` and floats to the top of the next round regardless of its print time. This way a 14 h print can't sit indefinitely behind a stream of 30-min jobs.

Each printer model is its own contest, and a job whose print time is not known yet sorts after every known one rather than first. The Auto-Queue panel lists pending jobs in this same order while the toggle is on, so the row at the top of a model's group is the one placed next; drag handles are hidden, because a manual order would be ignored.

When the toggle is off, items dispatch in FIFO order (by `position`).

---

## :material-cog: Settings

**Settings → Printing → Queue & Scheduling → Auto-Queue Routing**:

| Setting | Effect |
|---------|--------|
| **Shortest job first** | Enables SJF + the starvation guard. Default: off (FIFO). |
| **Rebalance across printer models** | Lets idle printers of another model take an order line's pending copies — see [Rebalancing](#rebalancing-across-printer-models). Default: off. |
| **Use compatible printers in Auto Queue** | Allows compatible-model fallback when no exact-model printer is ready. Default: off. A manual choice of a compatible model does not depend on this switch. |
| **Automatically return failed AutoQueue prints** | Returns a proven failed print to the Auto Queue. See [Automatic return after a failed print](#automatic-return-after-a-failed-print). Default: off. |

The router itself is **always on** — there's no master switch. If no auto-queue items exist, the scheduler is a 30 s no-op.

---

## :material-plus-circle: Adding to the auto-queue

Choose the entry point that fits your workflow:

### 1. Print Modal — "Auto" toggle

Open Print for a library file or archive and choose **Auto**.

| Field | Meaning |
|---|---|
| Target Model | The file's model, or an explicitly compatible model. An empty selection means detect it from the 3MF, not allow any model. |
| Target Location | An optional printer-location restriction. |
| Filament source | Automatic: AMS or external spool; AMS only; External spools only. |
| Force exact color match | Off by default: exact colours are preferred, but another compatible colour is allowed. Material and nozzle requirements remain. |
| Allow match by base material | On by default: compare base materials, such as `PETG`, rather than vendor or profile names — always the material the file itself declares. No profile id refuses while this is on. Turn it off to require the same profile wherever the file and the loaded source both name one. |
| Plate channels | Material and color for each used channel; **Require this color** pins one channel's color. |

Below the fields, **AMS connected / Without AMS / AMS state unknown** groups show compatible, ready, incompatible and unverified counts, with reasons. Normal submission requires at least one confirmed compatible candidate for every plate; zero ready printers does not block it when compatible candidates exist. If compatibility is unverified or all candidates are conclusively incompatible, the normal button is disabled with an explanation. **Queue anyway — wait for compatibility** requires explicit confirmation; an unknown result also offers **Retry**. A complete preview with no target model in the selected scope offers **Save in AutoQueue for the future**, not an ordinary add. This does not permit direct printing on a wrong-model printer. See [the compatibility preview](filament-routing.md#preview). A source-reading error must be resolved before adding it.

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

The auto-mode form offers exact and Bambu Studio compatible targets. A known incompatible target is refused instead of creating a permanently waiting item.

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
  "force_color_match": false,
  "allow_base_material_match": true
}
```

Full schema in [API reference](../reference/api.md). Quantity > 1 creates N rows in one call (same `batch_id` semantics as `print_queue`).

### 5. Order plans and Telegram

An [order plan](projects.md) can send one row or the whole plan to Auto-Queue; plate validation happens before queue items are created. Telegram uses the same source validation. A large quantity does not relax color or feed rules.

---

## :material-monitor-dashboard: AutoQueuePanel on the Queue dashboard

The Queue page has an **Auto-Queue panel** above the per-printer queue cards. **Always rendered** so the drop-zone is permanently available; when there are no pending auto items the panel collapses to a one-line hint inviting a drag-drop.

The panel is a real queue, not just a pile:

- **Items list in true dispatch order.** Adjacent copies of one submission collapse into a compact **×N** row; the row expands into its individual copies.
- **Everything drags.** A collapsed batch moves as a block, an expanded copy moves anywhere in the order — queue five copies of A, add two of B, pull one B to the front and leave the other at the end, and the list shows exactly that. With **Shortest job first** enabled the drag handles hide and a hint explains that the distributor owns the order.
- **Every copy edits in the full Schedule dialog** — the same one the per-printer queue uses: target model and location, schedule, print options, macros. Editing a batch applies the change to all of its copies at once; a single copy can also be edited, deleted or force-assigned on its own.
- Each row shows thumbnail, name, plate, target model, estimated print time, filament types, exact colours for the channels the selected plate uses and the waiting reason when no printer is eligible.

Once an item is assigned to a printer, it disappears from the panel and shows up in that printer's queue card with a small "auto-assigned" badge.

---

## :material-filter-variant: Eligibility rules { #eligibility-rules }

The printer must be active, unarchived, available to the router, and free to take new work. It must also be one the job's **author** reaches, when a group limits the author to printers ([Printer access](authentication.md#printer-access)): a team's job stays on the team's printers, and waits with *among the printers its author may use* in its reason when none of them fits. A job with no author — from a Virtual Printer, or a chat with no linked user — may go to any printer. The route icon on its queue card lets you opt it out of automatic assignment without stopping its ordinary queue.

A printer whose queue you paused gets no new work, and neither does one whose queue stopped after a failed or cancelled print, until you press **Resume queue**. The job is not placed in a stopped queue to wait — any other printer that can take it gets it. When none can, it waits in the Auto-Queue, and its reason names each printer stopped after a failed or cancelled print: *The printer's queue is stopped after a failed or cancelled print; resume it to give it new work.*

A job set to **Only run if the previous print succeeded** also passes over a printer whose newest finished print is a failure nobody has released — reason *The previous print failed.* — until a later print succeeds there or someone presses **Acknowledge failure** on that printer's card; see [Only after a successful previous print](print-queue.md#previous-success).

It needs the exact model, the selected location, and a **complete mapping for every used channel**: material under the saved matching rule, nozzle, source rule, and required colours. One PLA slot does not satisfy two PLA channels. Manual physical selections cannot move arbitrarily between printers.

Among eligible candidates, readiness comes first, then the best color match. See [Filament Routing](filament-routing.md#channels) for worked examples.

!!! note "Drain the emptiest spool first"
    When this setting is on, otherwise equally ranked printers with a known
    remaining level are ordered by the average reported percentage in the
    sources selected for this job. The lower average wins. This is a
    tie-breaker after readiness, model, colour and staged work. A printer with
    unknown levels can still take the job. The setting also governs automatic
    source selection on the chosen printer. The AMS Filament Backup switch
    still governs lowest-remaining tray selection on BamDude's own dispatch
    paths. See [Print Queue](print-queue.md).

### Color, material, and profile variant

Colour and material are separate decisions. With **Allow match by base material** on, a custom PETG profile and Generic PETG match despite different names or vendors — including a profile this install cannot resolve at all, which is the usual shape when several people slice for one farm. With it off, a known `tray_info_idx` variant remains a restriction. A missing variant is never invented. See [material matching](filament-routing.md#material) and [colour rules](filament-routing.md#colors).

---

## :material-directions-fork: Routing is not dispatching

Choosing which printer a job belongs to and deciding when it may start are two different questions, answered in two different places.

The router only answers the first. It will hand a job to a printer that cannot start right now — one waiting for a **Clear Plate** confirmation, mid plate-change, drying, or held by staggered start. The job then sits **visibly** in that printer's queue until the printer is ready, and every safety check still applies at the moment it actually matters.

Refusing to route to such a printer would sound safer and would not be: its queue would stay empty, so nothing on screen would explain the hold-up, and the **Clear Plate** prompt — which appears on a printer's queue — would never have a chance to show. Idle machines would be reported as busy and the farm would look dead. Placing the work is what makes the reason visible.

A printer that *is* ready still wins when there's a choice.

---

## :material-swap-horizontal: Rebalancing across printer models

An order line's work is split between printer models when it is queued — by hand, or with the farm's proposal — and a queued copy belongs to its file's model. When the P1S machines free up faster than the forecast assumed, the X1C copies keep waiting in their own pile. Rebalancing lets the auto-queue **move still-pending copies of an order line to idle printers of another model** when that finishes the line sooner — including a model whose plate makes a different number of parts, in which case the plates and the number of prints are recalculated.

**The rule.** Every printer is asked about *this* copy — its own file, colour and profile rules, feed (AMS or external spool) and nozzle, through the same filament check routing and dispatch use — never about its model alone. A pending copy moves only when *all* of these hold:

- no printer of its own model is free *and able to print it* right now — a free printer holding the wrong filament does not keep the work home;
- the line has a sliced plate for another model, with a print-time estimate, and at least one printer of that model is free, ready and able to print **that plate** — an empty queue is not enough: a printer still waiting for a plate clear, held by a Home Assistant sensor, drying with its queue held, or offline only looks free;
- the prints needed to cover the same parts there finish no later than the copy would at home. «At home» comes from a forecast of the whole auto-queue as it will be dealt out: in its own order (by position, or shortest job first), every job on the printer the auto-queue would give it, with upload time, plate clearing, operator hours and staggered starts — so the last of a long list of copies waits behind the ones ahead of it, and so does work the rebalancer may not move itself. The prints moved there are dated the same way: the converted copy keeps its place, the extra prints are filed after the whole queue, and other work for that model takes its turn. Each job is dated with the preparation its order sets for that printer model — a job whose order switches preheating off is not charged for one — and a printer that would turn a job away, because the order's settings do not fit it or a swap-mode printer would refuse its plate change on that file, is no place for it; the extra prints a move creates are judged by the settings of whoever moves the job. When no home printer can print the copy at all, any able target wins.

Among several models that qualify, the earliest finish wins, then the least surplus. Each free printer is counted once, across plates and lines: copies of the more urgent orders take the free printers first, and a faster plate nobody free can print never hides a slightly slower one that can be printed.

**When it waits.** A print being sent to a printer counts with its own estimate and preparation, and one running past its estimate counts as ending now. If the copy's finish still cannot be forecast — a print without a time estimate, a printer held by a Home Assistant sensor or busy with nothing the forecast can date — the copy stays and says so; it is never compared as if it would start at once, and such a printer makes uncertain only the copies that could start on it. A printer whose queue is paused or in error is no home, and no target either: the auto-queue gives it no new work until it is resumed, so any printer that can take the copy wins. If a free printer of the copy's own model has not reported its filament yet, the copy waits for the next pass instead of moving on a guess. If the farm changes while the target file is being copied — the spool is taken out, the printer gets other work, the copy's settings change, a receiving printer is switched to swap mode or a saved print profile now asks it for swap macros the copied file cannot honour, the "compatible models" setting is switched off, the target file is re-sliced or its recorded yield or print time changes — the move is called off before anything is written and decided again on the next pass. When the scheduled pass and a button both decide to move the same copy, only one of them moves it, and a copy that was assigned or cancelled meanwhile is left alone. A job released for manual start can take a stagger slot shared with other printers, so the rebalancer may leave a copy in place when that makes its finish uncertain. A paused or halted queue cannot take a stagger slot before it is resumed. Manual starts remain available when only AutoQueue routing is disabled.

**Parts, not prints.** A copy is a claim on covering N parts. Moving a 6-part P1S plate to an A1 mini whose plate makes 2 parts turns one print into three; moving 2 parts onto a bigger bed turns them into one print with a surplus of less than one plate's worth, which lands on the shelf like any other surplus.

**Three ways to run it.**

- **Automatically** — **Settings → Printing → Queue & Scheduling → Auto-Queue Routing → Rebalance across printer models** (off by default). The scheduler checks after every placement pass, moves at most one copy per idle printer per pass, and leaves a line alone for five minutes after a move. The pause is not a promise that the next move comes five minutes later: a pass only moves what the farm allows at that moment. The scheduled pass moves a copy only once — after that only the buttons move it again — and when one of a pass's moves cannot be made, the rest of that pass's moves wait for the next pass.
- **Per line** — the **Rebalance** button on an order line's plan, shown while the line has pending auto-queue copies. It runs regardless of the setting and ignores the five-minute pause — nothing else: it never overrides a filament, colour or model rule.
- **Per copy** — **Rebalance** on a pending row or a collapsed `×N` block of the auto-queue panel. A row that cannot move says why.

**What is never moved.** A copy that is already handed to a printer, scheduled for a time, staged for a manual start, pinned to specific filament slots, aimed at a location, queued from an archive rather than a library file, or not filed under an order line. Those either belong to a printer already or carry a decision of yours.

**What you see.** A moved row carries a `← P1S` badge on the panel, naming the model it was queued for before; the copies created with it share its batch. Routing, dispatch and filament rules are untouched: a moved copy is written by the same writer every enqueue uses and passes the same file and filament checks.

!!! note "Estimates decide"
    Rebalancing compares the same print-time estimates the ETA uses. A file without an estimate is never chosen as a target, and a copy without one stays where it is: its finish cannot be compared.

!!! note "What it does not promise"
    The rebalance forecast is an estimate made pass by pass from the queue as it is now: it reserves no printer, and work queued, cancelled or finished early changes the next pass's answer. It is not the order ETA shown in the workshop. A printer of the copy's model that drops off the network for a moment does not count as home either, so a short disconnect can let several copies move at once; the number of free printers able to take them and the five-minute pause per line bound that. Rebalancing is an estimate made pass by pass, not a farm-wide optimiser.

---

## :material-fire-off: Drying takes lower priority than a print

[Queue Auto-Drying](ams.md#queue-auto-drying) keeps idle spools dry between prints. When Queue Auto-Drying is in its default **non-blocking** mode — **Settings → Filament → General → AMS Display Thresholds → Queue Auto-Drying → Wait for drying to complete** switched off (`queue_drying_block=false`), so prints take priority over drying — a job queued **directly** to a printer stops an in-progress dry cycle and starts printing.

The auto-queue router behaves the same way, and it does so by *ranking* rather than excluding: a printer that is free to take work but currently drying still receives jobs, it simply loses to one that can start immediately. The per-printer dispatch then stops the dry cycle and begins the print (the same `_stop_drying` step described in [AMS → Queue Auto-Drying flow](ams.md#queue-auto-drying)).

When Queue Auto-Drying is set to **blocking** (`queue_drying_block=true`), drying still holds the queue — the job waits in that printer's queue until the dry cycle ends, exactly as a directly-queued item would. The router takes that into account: while a cycle holds a printer's queue, an equally suitable printer that is not held wins the job. The held printer still receives it when it is the only one that fits, and the wait is then visible on its row. [Rebalancing](#rebalancing-across-printer-models) does not move work onto a printer whose queue drying holds.

!!! note "A drying printer is not a busy printer"
    The router does not treat a drying printer as plain "busy" and skip it — otherwise an auto-routed job could sit waiting behind a dry cycle that a directly-queued job would simply have stopped. This matters most on P2S / H2 farms with AMS auto-drying enabled.

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
| Edit or cancel a batch while one of its jobs is being placed | Refused with `409` (*This job changed or started while it was being edited. Nothing was saved*; for a cancel, *The selected jobs changed*). Refresh and try again; the placed job keeps its printer. |
| Reorder jobs while one of them is being placed | Waits for that placement, then reorders the jobs still waiting; the placed job keeps its printer. |

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

Jobs saved without the complete routing rules retain their established source restrictions and physical selections. If there is not enough saved evidence to recover their rules, mapping review is required. Schedule edits, copies, and repeats retain the rules; a different printer or plate requires a new answer for a manual mapping. See [Editing and repeats](filament-routing.md#editing).

## Notifications about obstacles

Busy printers and temporarily unavailable feed/nozzle telemetry are normal waiting states: AutoQueue keeps the reason visible without sending a waiting notification. Missing suitable printers, incompatible filament or nozzles, mapping review, a failed previous print and a printer queue stopped after a failed or cancelled print can need attention. Permanent target-model refusals have their own reason rather than appearing as a busy printer.

A completed routing pass sends at most one **AutoQueue needs attention** event, listing up to five new facts and the count of the rest. Provider and Telegram-chat subscriptions still apply. Each due pending job contributes its observed obstacles. Busy, offline or unknown telemetry does not prove an earlier filament mismatch was corrected; the incident ends only after its last current contributor disappears or a complete fresh observation resolves it. Other placements, names, languages, unrelated AMS-slot metadata and copy counts do not rearm it. Queue placements and their UI updates commit before optional rebalancing and the separate notification read; a failed digest cannot undo them.

Only positive acknowledgements from all configured automatic-on plugs create a bounded **waking up** grace. It survives subsequent passes until the existing cooldown deadline; further ON attempts while the printer stays offline do not extend it. After the deadline the offline obstacle may be reported once. A refused or failed plug gives no grace, and does not skip the other plugs. Known incompatible filament in an offline printer continues to prevent unnecessary wake attempts. Source/swap failures already marked failed do not also send a waiting alert. Automatic rebalancing rechecks farm admission after file capture; explicit manual planning remains available during recovery hold.

This deduplication is held in memory: after restarting BamDude, one alert about a current obstacle is possible. Failed delivery and enabling a provider do not replay previously observed incidents. Existing custom notification templates keep `{job_name}`, `{target_model}` and `{waiting_reason}`. A farm recovery hold has its [own banner](farm-startup.md).

## Automatic return after a failed print

Enable **Automatically return failed AutoQueue prints** under **Settings → Printing → Queue & Scheduling → Auto-Queue Routing**. It is off by default. A proven live failed print may return its logical job at most twice, after at least two minutes. The accepted file and saved options are retained. Each physical attempt keeps its own archive and costs; the old failed row shows **Returned to Auto Queue**, and Retry/Repeat stay unavailable for that row. Clear and removal remain separate operator actions.

The failed printer stays in its error/pause state and gets no new work until you press **Resume queue**; after that it ranks last among current eligible candidates. Busy printers remain excluded: BamDude does not hold the job waiting for them. If the failed printer is the only candidate, the job waits in the Auto-Queue, its reason naming the stopped printer. If it is placed on that printer after the queue is resumed, use **Move to AutoQueue** before it starts to return it manually; the automatic-return count is preserved. Returned jobs are excluded from automatic model rebalancing. Explicit reviewed order replanning remains available.

A failure recovered only by reconciliation after a disconnect or restart is not returned automatically. For example, if the farm was offline when a printer failed and only discovers the old failure on reconnect, the job remains failed for review. If the live settlement had already been saved before the restart, it may finish returning after current checks pass. This is not a guarantee that every failed print will retry. The queue shows why a proven return was deferred, including the two-return limit.

## Automatic return before sending

When a printer refuses an upload or becomes unavailable before BamDude sends the start command, an unchanged AutoQueue job with portable settings can return immediately. It keeps its original place, file and options. The failed printer’s queue stops until **Resume queue**. The old row stays in **Issues** and links to the returned job. Its Retry, Repeat and Clone actions are unavailable.

The Auto Queue badge names the refusing printer and shows the count out of two. This limit is separate from the setting and limit for [failed prints](#automatic-return-after-a-failed-print). When the proof is incomplete, the printer copy was edited, the order closed, or the limit was reached, the job stays in the printer’s queue for review. If another printer is ready and eligible, the returned job can go there on the next routing pass.
