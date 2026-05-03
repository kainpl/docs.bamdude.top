---
title: Auto-Queue Routing
description: Router queue layer that distributes prints to any eligible idle printer based on model, filament, and color match
---

# Auto-Queue Routing

The auto-queue is a **router layer above the per-printer queues**. Drop a print into it without naming a target — the scheduler picks an eligible idle printer (by model + filament + color match), copies the item into that printer's queue, and lets the existing per-printer dispatch handle the rest.

Introduced in **0.4.2**.

---

## :material-router-network: How it works

```
┌────────────────┐   eligible idle printer found?
│ AutoQueueItem  │────────┐
│ (target_model, │        │ yes → copy into printer's print_queue
│  filaments,    │        │       mark auto row "assigned"
│  colors)       │        │
└────────────────┘        ▼
                     PrintScheduler picks it up
                     within ~1 tick (background_dispatch)
```

A background loop (`AutoQueueScheduler`, started from `main.py` lifespan) wakes every **30 seconds** and on each tick:

1. **Snapshots busy printers** — anything currently `status='printing'` in `print_queue` is excluded from this round.
2. **Reads pending auto-queue rows** ordered by SJF (Shortest Job First) + `been_jumped` if the **Queue Shortest First** setting is on, else by `position`.
3. **For each item, calls `find_eligible_printer`** — picks an idle printer that matches:
    - the item's `target_model` (e.g. `X1C`, `P1S`, `A1MINI`, `H2D`)
    - all `required_filament_types` (extracted from the 3MF, user-overridable)
    - color requirements (when `force_color_match=true`)
    - the optional `target_location` (room / shelf tag) if you've grouped printers by location.
4. **If a match exists**: the item is copied into that printer's `print_queue` with AMS mapping computed from the printer's current spool state. The auto row flips to `status='assigned'` and back-references the new per-printer item.
5. **If no match**: `waiting_reason` is updated so the queue UI can explain *why* the item is still parked (e.g. `"all P1S busy"`, `"need PETG (red), no printer has it loaded"`).

Once a row lands in a per-printer queue, the **existing dispatch flow** takes over — plate-clear gate, staggered start, swap macros, drying, the lot. The router doesn't bypass anything.

---

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

There are four ways to drop something into the auto-queue:

### 1. Print Modal — "Auto" toggle

In the per-archive / per-library-file Print Modal there's a **Specific / Auto** toggle. Pick **Auto** and the modal shows:

| Field | Notes |
|-------|-------|
| Target Model | Pre-filled from the 3MF's sliced-for model. Defaults to "any" — leave blank to let any compatible printer pick it up. |
| Target Location | Optional room / shelf tag if you've labelled your printers. |
| Force Color Match | When on, the eligibility check requires a printer that has every filament *and the right color* loaded. Off by default — match by type only. |

Submit and an `AutoQueueItem` is created.

### 2. Virtual Printer `auto_queue` mode

Slicer "Send to Printer" → VP receives upload → archived → dropped into the auto-queue. See [Virtual Printer → auto_queue](virtual-printer.md#auto_queue) for the UI side.

This is the hands-off "slice and forget" path: the slicer doesn't know which printer will run the job, and neither does the operator until the router decides.

### 3. Drag-and-drop on the Auto-Queue panel

Drop a sliced file (`.gcode` / `.gcode.3mf`) anywhere over the **Auto-Queue panel** at the top of the Queue page. The file is uploaded into the library root, then the same Print Modal opens locked to **Auto** mode (no specific/auto toggle, no printer picker — only the auto-mode constraints: target model / location / force-color). Submit and an `AutoQueueItem` is created.

No model-compatibility check on drop (unlike the per-printer queue card drop) — the auto-router already filters candidates by `sliced_for_model` at dispatch time, so an incompatible file just sits in the panel with a `waiting_reason` until a matching printer appears or the operator cancels it.

Permission-gated on `queue:create`. The panel renders even when empty so the drop target is permanently available; an empty-state hint nudges first-time operators.

### 4. REST API

```http
POST /api/v1/auto-queue/
{
  "library_file_id": 42,
  "target_model": "P1S",
  "force_color_match": false
}
```

Full schema in [API reference](../reference/api.md). Quantity > 1 creates N rows in one call (same `batch_id` semantics as `print_queue`).

---

## :material-monitor-dashboard: AutoQueuePanel on the Queue dashboard

The Queue page has an **Auto-Queue panel** above the per-printer queue cards. **Always rendered** so the drop-zone is permanently available; when there are no pending auto items the panel collapses to a one-line hint inviting a drag-drop. Otherwise it lists pending auto-queue items with:

- thumbnail, name, plate, target model
- estimated print time
- waiting reason if no eligible printer
- inline buttons: edit (target model / location / force-color), cancel

Once an item is assigned to a printer, it disappears from the panel and shows up in that printer's queue card with a small "auto-assigned" badge.

---

## :material-filter-variant: Eligibility rules

The `find_eligible_printer` helper considers a printer eligible when **all** of these hold:

| Check | Detail |
|-------|--------|
| **Idle** | Not currently `status='printing'`, `paused`, `error`, or otherwise busy. |
| **Model match** | If `target_model` is set, the printer's model code must equal it. |
| **Location match** | If `target_location` is set, the printer's location tag must equal it. |
| **Filament types** | Every required filament type must appear in some loaded slot (AMS or external spool). |
| **Color match** | When `force_color_match=true`, color hex must also match per filament. |
| **Filament-overrides** | Any per-print override (e.g. "use PLA Tough instead of PLA") is honoured before checking the loaded slots. |

Tie-breaker — when multiple printers are eligible:

1. **Lowest filament use** (when `prefer_lowest_filament` setting is on, default off). Picks the printer whose AMS slots have the lowest total grams remaining for the required filaments — keeps "fresh" spools for harder jobs.
2. Falls back to the lowest-id printer.

---

## :material-clipboard-text: AMS mapping at assign time

When the router copies an auto-queue item into a per-printer `print_queue`, it **computes AMS mapping right then** from the printer's current spool state — not at submission time. So if you swap a spool between submission and dispatch, the assigned mapping reflects the new spool. The original `filament_overrides` on the auto row are still applied first, then auto-mapped slots are filled in.

---

## :material-link-variant-off: Cancel / edit semantics

| Action | Effect |
|--------|--------|
| Cancel a `pending` auto-queue item | Row deleted. No printer ever saw it. |
| Cancel an `assigned` auto-queue item | Cancels the **per-printer queue item** the router created. The auto row stays in `assigned` for audit. |
| Edit `target_model` / location / force-color | Allowed only while `pending`. After assignment, edit the per-printer queue item instead. |

---

## :material-lightbulb: When to use it

| Use case | Recommendation |
|----------|----------------|
| Single printer | Skip the auto-queue, use the regular per-printer queue — no router overhead, simpler UI. |
| 2-3 printers, one model | Auto-queue is great for load-balancing — drop jobs in, the scheduler picks the next free one. |
| Mixed-model farm | Auto-queue with explicit `target_model` per job — same load-balancing within the model, no cross-pollination. |
| Color-critical jobs (logos, signage) | Turn on `force_color_match` so a job won't dispatch to a printer with the wrong color loaded. |
| Hands-off slicer flow | VP `auto_queue` mode + auto-queue → fully unattended slice → print pipeline. |

---

## :material-code-tags: Internals

| File | Role |
|------|------|
| `backend/app/models/auto_queue.py` | `AutoQueueItem` ORM model |
| `backend/app/services/auto_queue_scheduler.py` | Background loop, 30 s tick |
| `backend/app/services/auto_queue_eligibility.py` | `find_eligible_printer` + match helpers |
| `backend/app/services/auto_queue_ams.py` | `compute_ams_mapping_for_printer` |
| `backend/app/services/auto_queue_threemf.py` | `extract_auto_queue_requirements` (3MF parser) |
| `backend/app/api/routes/auto_queue.py` | REST endpoints |
| `backend/app/migrations/m024_*.py` | Schema migration |
| `frontend/src/components/Queue/AutoQueuePanel.tsx` | Dashboard panel |
| `frontend/src/components/PrintModal/AutoModeOptions.tsx` | Print Modal "Auto" mode form |

---

## :material-history: Migration from per-printer queues

If you've been using the **"any printer of model X"** target option in the per-printer queue picker, that's the legacy single-tier router. It still works but is being superseded by the auto-queue:

| Capability | Legacy "any of model X" | Auto-Queue |
|-----------|--------------------------|------------|
| Picks idle printer of given model | yes | yes |
| Filament type match | no — assumes operator checks | yes |
| Color match | no | optional (`force_color_match`) |
| SJF + starvation guard | no | yes |
| Location filter | no | yes |
| Visible "waiting" panel with reasons | no | yes |
| VP integration | proxy only | dedicated `auto_queue` mode |

No automatic conversion — existing per-printer queue items keep working as-is. Use the auto-queue going forward when the routing decision can be deferred.
