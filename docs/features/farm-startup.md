---
title: Farm recovery after a restart
description: Review the farm before allowing new automatic starts after an unconfirmed shutdown
---

# Farm recovery after a restart

After an unconfirmed shutdown, BamDude starts with **new automatic starts paused**. You can sign in, inspect the farm, stop a print or switch a plug off before allowing new work. There is no automatic countdown.

The same review is required on the first start after upgrading from a version without this protection, when the local startup record is missing or unreadable, and after restoring a backup. An orderly restart normally resumes automation after startup checks. A pause that was already awaiting your confirmation survives an orderly restart too.

A newly created, empty installation can skip this first review only when BamDude proves it created the storage and there are no configured devices or jobs. An existing empty database or an unfinished setup screen is insufficient.

**After a restore begins applying data or stopping services, restart BamDude first.** The banner asks for a restart and cannot release the pause in that process. A rejected backup that fails preflight leaves the current pause unchanged.

## Allow new starts

1. Check the printers, plates and power supply. In particular, check the load that caused a power failure or inverter trip.
2. Read the persistent banner on the dashboard, Queue or System page.
3. Choose **Allow new starts** and confirm. Administrators have this permission by default; it can be granted separately as **Allow new farm starts after recovery**.

An API key must have the corresponding control scope and owner permission, with access to the whole farm. A key limited to selected printers cannot release a global pause. A confirmation from an old browser tab cannot release a newer startup pause.

Allowing new starts preserves individual queue pauses and plate-clear checks. The acknowledgement belongs to the whole installation: a printer reconnect does not revoke it or create a new per-printer admission gate. Offline or busy printers still follow their ordinary queue checks.

## What remains paused

- New queued and direct prints, reprints and calibration starts.
- AutoQueue assignment, automatic plug ON, scheduled ON, new automatic drying and preheat.

Enqueueing, reordering and canceling waiting jobs remain available. Existing print-state and energy accounting continue. A blocked scheduled ON is not recorded as executed: it can run only if its original schedule window is still current when the pause ends. Missed starts are not replayed as a backlog.

## Existing prints and operator controls

A printer may resume a print and heating through its own power-loss recovery. BamDude observes that print through its existing recovery logic; a server restart does not itself send another print or a Resume command. The global pause is not a power interlock and does not stop a printer's own recovery.

The pause applies to new work. It does not suppress the completion or table-change macro of a print already in progress. Reconnecting does not introduce an additional confirmation of that print's identity. The normal print and macro checks still apply.

Manual controls, including Resume, Stop, Cancel, lights, temperatures, movement, G-code and macros, remain available under their existing permissions and printer-state checks. Automatic OFF and the normal protective power-off path remain available too. Operators remain responsible for the physical effects of manual commands.

**Info → Print-state recovery** keeps the existing diagnostic and confirmed repair tools. It also reports a terminal queue item still retained by a printing queue header. Seeing a pending physical effect there does not automatically clear it or replay it.

## If the pause cannot be released

While startup recovery is still in progress, wait for it to finish. If the startup record cannot be saved, check the data volume's availability and permissions and collect a support bundle; automation remains held. Restart after correcting the underlying storage or startup failure. Removing the startup record is not a way to bypass the review: a missing record requires confirmation again.

The startup record belongs to this installation. It is excluded from backups; restoring another installation's backup cannot bring a saved “clean shutdown” decision with it. This protection assumes one controlling backend per installation, not several backends sharing one farm database.
