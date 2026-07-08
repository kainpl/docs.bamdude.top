---
title: Slicer Pipelines
description: Save a slice setup once, then slice-and-queue any file with a single click — onto a specific printer or a whole model class
---

# Slicer Pipelines

A **pipeline** bundles the four picks you normally make in the Slice dialog — printer preset, process preset, a filament preset per AMS slot, and the bed type — together with a **dispatch target** and a **copy-fanout strategy**. Save it once and a repeatable job stops being a re-pick-everything chore: **Run with pipeline** on any file slices the source once and enqueues however many copies you asked for onto the target.

It's built on BamDude's [two-tier queue](auto-queue.md) — a class-targeted pipeline hands its copies to the auto-queue distributor, so they balance across your matching printers exactly like any other model-assigned job.

---

## :material-cog-outline: What a pipeline stores

| Field | What it is |
|---|---|
| **Name / description** | Your label for the setup. |
| **Printer preset** | The printer profile to slice against (source + id — local, Orca Cloud, Bambu Cloud, or standard). |
| **Process preset** | The process/quality profile. |
| **Filament presets** | One preset **per AMS slot**, so a multi-material job maps each slot to the right filament. |
| **Bed type** | The build-plate type to slice for. |
| **Dispatch target** | A [specific printer or a printer-model class](#targeting). |
| **Fanout strategy** | How copies spread across a class target — `max_parallel`, `fill_one_first`, or `round_robin`. |

The **number of copies isn't part of the pipeline** — you pick it each time you run, so the same pipeline can make one part today and twenty tomorrow.

---

## :material-play-circle-outline: Saving and running

**Save one** straight from the Slice dialog with **Save as pipeline** — it captures the presets you've already picked there.

**Run with pipeline** from any of:

- a **library file**,
- an **archive**, or
- the **Slice dialog** itself.

BamDude slices the source **once** with the pipeline's presets, then enqueues the copies onto the target. One slice, N queue items — no re-slicing per copy.

---

## :material-target: Targeting

A pipeline dispatches to one of two kinds of target:

- **A specific printer** — every copy goes to that exact machine's queue.
- **A whole printer-model class** — e.g. *any X1C*. Class targets are handed to the **auto-queue distributor**, which balances the copies across every matching printer in the farm using the pipeline's fanout strategy:

| Strategy | Behaviour |
|---|---|
| `max_parallel` | Spread copies across as many matching printers as possible for the fastest wall-clock finish. |
| `fill_one_first` | Load one printer's queue before moving to the next. |
| `round_robin` | Deal copies out evenly, one per printer in rotation. |

---

## :material-clipboard-check-outline: Pre-flight eligibility check

Before it commits, a pipeline run is checked against the target and flags mismatches — a target that's **offline or disabled**, an AMS slot whose **loaded filament type or colour differs** from the pipeline's, or a **missing slot**. For a class target the report reads like *"3 of 5 X1Cs eligible"* with a per-printer breakdown of why each one does or doesn't qualify.

If issues are found the run stops and shows the report. A **Run anyway** escape hatch lets you dispatch regardless (the override is recorded on the run), for when you know better than the check.

---

## :material-view-dashboard-outline: The Pipelines tab

The Print Queue page has a **Pipelines** tab (alongside Queue, History, and Timeline) that tracks every run **live**:

- **Per-copy status** — watch each copy move through slicing → queued → printing → done/failed.
- **Cancel** an in-flight run.
- **Retry just the failed copies** — no need to re-run the whole batch.
- **Clear the log** when you're done reviewing.

Manage, rename, and delete the pipelines themselves under **Settings → Pipelines**.

---

## :material-shield-key: Permissions

Pipelines are gated by three permissions. **Administrators** and **Operators** get all three; **Viewers** get read only.

| Permission | Grants |
|---|---|
| `pipelines:read` | See pipelines, their run history, and the eligibility pre-flight. |
| `pipelines:write` | Create, edit, delete pipelines, and clear the run log. |
| `pipelines:run` | Launch a run, cancel it, and retry its failed copies. |

Mapped to the REST surface:

| Endpoint | Method | Permission |
|---|---|---|
| `/slicer-pipelines/` | GET / POST | read / write |
| `/slicer-pipelines/{id}` | GET / PUT / DELETE | read / write / write |
| `/slicer-pipelines/{id}/check-eligibility` | POST | read |
| `/slicer-pipelines/{id}/run` | POST | run |
| `/pipeline-runs` | GET | read |
| `/pipeline-runs/{id}/cancel` | POST | run |
| `/pipeline-runs/{id}/retry-failed` | POST | run |
| `/pipeline-runs/clear` | POST | write |

An [API key](api-keys.md) with read scope can read pipelines and runs; running a pipeline is a human/operator action.

---

## :material-link-variant: Related

- [Auto-Queue Routing](auto-queue.md) — the two-tier distributor that fans a class-targeted pipeline's copies across matching printers.
- [Per-Printer Queues](print-queue.md) — where the copies land; the Pipelines dashboard lives on this page.
- [Slicer API](slicer-api.md) — the containerised OrcaSlicer / Bambu Studio sidecar that does the actual slicing.
- [Cloud Profiles](cloud-profiles.md) / [Orca Cloud](orca-cloud.md) — preset sources a pipeline can reference.
