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

Allowing new starts preserves individual queue pauses, dirty-plate checks, swap holds and other printer conditions. A printer must supply fresh status and finish reconciliation after its current MQTT connection before it can receive a new print. An offline printer does not prevent the rest of the farm from recovering.

Reconnecting the same MQTT client starts a fresh check. Temporary reconciliation errors retry automatically; the affected printer card shows **Waiting for printer state reconciliation** until its current connection passes.

## What remains paused

- New queued and direct prints, reprints, firmware Resume commands and calibration starts.
- AutoQueue assignment, automatic plug ON, scheduled ON, new automatic drying and preheat.
- New automatic completion macros, including an owed table change. An already attempted table change with an uncertain result is never replayed.

Enqueueing, reordering and canceling waiting jobs remain available. Existing print-state and energy accounting continue. A blocked scheduled ON is not recorded as executed: it can run only if its original schedule window is still current when the pause ends. Missed starts are not replayed as a backlog.

## Prints restored by the printer

A printer may resume a print and heating through its own power-loss recovery. BamDude observes and reconciles that run using its existing identity; it does not send another print or Resume command just because the server restarted. Ambiguous runs keep their local hold for review. The global pause is not a power interlock and does not stop a printer's own recovery.

Explicit typed manual plug ON, temperature, jog, home, motor release, fan and AMS-calibration controls remain available to authorized operators, subject to their ordinary printer-state checks. Arbitrary G-code, macros and Home Assistant scripts require the global pause to be released because their effects cannot be determined safely from their text. Stop, Cancel, Off and cooling remain available through their typed controls.

Protective Obico power-off may act on a freshly observed, still-current failed print while new starts are paused. A stale or changed run does not receive that exception, and a refused OFF is reported as a refusal. An accessory explicitly configured not to supply printer mains may turn on for the current print; this grants no permission to start a printer or run a script.

## If the pause cannot be released

While startup recovery is still in progress, wait for it to finish. If the startup record cannot be saved, check the data volume's availability and permissions and collect a support bundle; automation remains held. Restart after correcting the underlying storage or startup failure. Removing the startup record is not a way to bypass the review: a missing record requires confirmation again.

The startup record belongs to this installation. It is excluded from backups; restoring another installation's backup cannot bring a saved “clean shutdown” decision with it. This protection assumes one controlling backend per installation, not several backends sharing one farm database.

A known pending table-change action is retained for reconciliation after release. Arbitrary print-finish macros are suppressed during the hold; BamDude does not replay a new backlog of arbitrary macros after release.

If admission refuses the table change before any command is sent, it stays owed. Once a command might have left, an uncertain result still requires review and is never automatically replayed.
