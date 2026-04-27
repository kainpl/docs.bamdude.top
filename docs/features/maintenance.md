---
title: Maintenance Tracker
description: Schedule and track printer maintenance tasks with history
---

# Maintenance Tracker

Schedule and track maintenance tasks to keep your printers running reliably. BamDude includes model-aware maintenance types and detailed history logging.

---

## :material-tools: Overview

The maintenance tracker helps you:

- **Schedule** recurring maintenance tasks
- **Track** when maintenance was last performed
- **Get notified** when maintenance is due
- **Log** detailed maintenance history with notes

---

## :material-format-list-checks: Maintenance Types

### Default Types

BamDude includes nine bundled maintenance task types with **model-aware filtering**: a "Lubricate Linear Rails" task only appears on A1 / H2 series, never on X1 (which doesn't have linear rails). The filter is keyed by the printer's mechanical class, derived from its model code:

| Mechanical class | Models | Tasks that appear |
|---|---|---|
| **Carbon rods** | X1, X1 Carbon, X1E, P1P, P1S | Clean Carbon Rods *(no lubricate task — carbon rods are intentionally run dry)* |
| **Steel rods** | P2S, X2D | Clean / Lubricate Steel Rods |
| **Linear rails** | A1, A1 Mini, H2D, H2D Pro, H2C, H2S | Clean / Lubricate Linear Rails |
| **Universal** | every model | Clean Build Plate / Clean Nozzle / Check Belt Tension / Check PTFE Tube |

| Type | Default interval | Applies to |
|---|---|---|
| **Clean Build Plate** | Every 25 hours | All printers |
| **Clean Nozzle / Hotend** | Every 100 hours | All printers |
| **Check Belt Tension** | Every 200 hours | All printers |
| **Check PTFE Tube** | Every 500 hours | All printers |
| **Clean Carbon Rods** | Every 100 hours | X1 series, P1 series |
| **Lubricate Steel Rods** | Every 50 hours | P2S, X2D |
| **Clean Steel Rods** | Every 100 hours | P2S, X2D |
| **Lubricate Linear Rails** | Every 50 hours | A1, A1 Mini, H2 series |
| **Clean Linear Rails** | Every 100 hours | A1, A1 Mini, H2 series |

Defaults seed once on first boot. Hidden defaults can be restored later via **Restore Default Tasks**.

### Custom Types

Create your own maintenance tasks in **Settings** > **Maintenance**.

### Hiding Default Types

Remove irrelevant default types by clicking the delete icon. Restore all defaults with **Restore Default Tasks**.

---

## :material-calendar-clock: Interval Types

| Type | Description |
|------|-------------|
| **Print Hours** | Based on actual print time (e.g., every 100 hours) |
| **Calendar Days** | Based on wall-clock time (e.g., every 30 days) |

---

## :material-check-circle: Logging Maintenance

1. Go to **Maintenance** page
2. Find the due/overdue item
3. Click **Mark Complete**
4. Add notes (what you did, parts replaced)
5. Counter resets

---

## :material-alert: Due Status

| Status | Meaning |
|:------:|---------|
| :material-check-circle:{ style="color: #4caf50" } OK | Not due yet |
| :material-alert:{ style="color: #ff9800" } Due Soon | Within the last 10 % of the interval (90 % consumed) |
| :material-alert-circle:{ style="color: #f44336" } Overdue | Past due |

---

## :material-history: Maintenance History

View detailed history for each printer:

| Field | Description |
|-------|-------------|
| **Date** | When performed |
| **Type** | Maintenance task type |
| **Notes** | What was done |
| **Parts** | Any parts replaced |

Export history to **Excel (.xlsx)** with date range selection, per-printer or all printers. The export includes operator, date, hours-at-performance, and notes — useful for warranty / service records.

---

## :material-bell-ring: Notifications

Get notified when maintenance is due via any configured notification provider. Enable **Maintenance Due** event in **Settings** > **Notifications**.

Telegram bot users receive actionable notifications with a **Mark Done** inline button.

---

## :material-lightbulb: Tips

!!! tip "Bed Cleaning"
    Clean with IPA between prints for best adhesion. Deep clean with dish soap weekly.

!!! tip "Document Everything"
    Add notes when logging maintenance to build a history of what works.

!!! tip "Preventive is Better"
    Follow intervals rather than waiting for problems. Preventive maintenance avoids costly failures.

> Originally based on [Bambuddy](https://github.com/maziggy/bambuddy) documentation.
