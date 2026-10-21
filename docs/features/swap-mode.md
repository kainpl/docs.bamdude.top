---
title: Swap Mode
description: A1 Mini plate swapper support with macros, restart resilience, and serialized dispatch
---

# Swap Mode

Swap mode supports automated plate swappers — mechanical add-ons that eject the finished build plate and position a fresh one between prints. When swap mode is enabled, BamDude coordinates with the swapper to run unattended batches without manual plate-clear confirmation.

---

## :material-swap-horizontal: What is Swap Mode?

A plate swapper is a hardware accessory (most commonly for the A1 Mini) that handles plate rotation between prints. With swap mode enabled, the queue scheduler:

1. Runs a **`swap_mode_start`** macro before the first print
2. Runs the print itself
3. Runs a **`swap_mode_change_table`** macro after the print completes
4. Bypasses the plate-clear confirmation
5. Starts the next queued print automatically

The cycle continues until the queue is empty.

---

## :material-cog: Configuration

### Enabling Swap Mode

1. Go to **Settings → Queue**.
2. Enable **Swap Mode** for your A1 Mini printer.
3. Pick a **Swap Profile** matching your hardware:

    | Profile | For |
    |---|---|
    | `a1mini_kit` | Bambu's official A1 Mini Plate Swapper Kit |
    | `a1mini_stl` | Community-printable A1 Mini swappers (printable kit / STL designs) |
    | `jobox-a1` | JoBox plate-swap automation |

    The profile binds to the right set of `swap_mode_start` / `swap_mode_change_table` macros. **`a1mini_stl` and `jobox-a1` ship pre-seeded built-in macros**; **`a1mini_kit` does not** (Bambu's official kit currently relies on operator-supplied G-code — write your own pair under **Settings → Macros** and tag them with `swap_profile=a1mini_kit`). Any profile's built-ins can be overridden by editing the macro in the UI.

### Swap G-code Macros

Swap mode is driven by G-code macros bound to the `swap_mode_start` and `swap_mode_change_table` events. Configure them under **Settings → Macros**. See [Macros](macros.md) for the full event + filter system.

```gcode
; Example swap_mode_change_table snippet
G28 X Y         ; Home X and Y
G1 Y 180 F3000  ; Move bed forward for plate swap
M400            ; Wait for moves to complete
G4 S5           ; Pause 5 seconds for swap
G28             ; Home all axes
```

!!! warning "Custom Hardware Required"
    Swap mode requires a physical plate swapper attached to your printer.
    Tailor the `swap_mode_change_table` G-code to your specific
    mechanism — there is no universal swap routine.

---

## :material-shield-check: Restart-Resilient Event Tracking

Swap intent is **persisted to disk**, not held in memory. Restarting BamDude mid-print never loses a pending plate-swap.

If a print is still running when BamDude reconnects, its active execution archive and the printer queue's existing
started job restore ownership of that print. Its later successful finish executes the pending change-table macro;
the printer does not have to supply a unique job ID. This uses the surviving queue claim, not just a matching filename.
An already attempted change-table command is never sent a second time. A global recovery pause keeps the macro owed
until the operator resumes the farm.

**How it works**

- At dispatch, every swap event the job is going to fire is added to `print_archives.extra_data["swap_macro_events_pending"]` (a JSON list).
- When `swap_mode_start` fires successfully, the dispatcher removes it from the list immediately.
- When `swap_mode_change_table` fires successfully (in `on_print_complete`), the same write removes it.
- Once the list is empty, the key drops entirely so the archive's `extra_data` stays clean.
- A `swap_mode_change_table` that cannot run when the print ends ([held](#a-held-table-swap)) stays on the
  list as the record of what was not done — it is never fired later by itself.

**Why this matters**

- A backend restart between print start and print complete used to wipe the in-memory `_active_swap_config` dict, leaving `on_print_complete` with nothing to act on. Now the pending list is read from the archive row and only the events still in it fire.
- A duplicate `on_print_complete` (MQTT replay, reconnect flap) finds the event already removed and does nothing — no double swap.

!!! info "Where the marker lives"
    For library-file dispatches, the initial pending list is folded
    into `archive_print()`'s `INSERT` (single statement, no extra
    writer). For reprints, the existing archive row is updated in
    the dispatcher's open session before FTP upload — keeping
    everything inside one transaction avoids racing the runtime
    tracker on the same row.

---

## :material-lock-clock: Dispatch and the DB-write startup-lock

Background dispatch runs **in parallel across printers** — sending prints to two A1 Minis with swappers really does start both jobs concurrently.

**What's serialised**

The brief DB-insert phase (`INSERT INTO print_archives`) sits behind a startup-lock so SQLite's single-writer semantics don't trip on `database is locked`. The lock is released as soon as the row is committed; FTP upload and the `start_print` MQTT round-trip then run concurrently.

**What you'll observe**

- Two printers get their `swap_mode_start` macros nearly simultaneously.
- Their FTP uploads happen in parallel (you'll see two upload progress bars in the dispatch toast).
- The earlier "one job at a time across the whole farm" gate that landed in mid-0.4.1 was scrapped once the startup-lock was in.

---

## :material-playlist-play: Queue Behaviour with Swap Mode

When swap mode is active for a printer:

1. Print completes on the printer.
2. The `swap_mode_change_table` macro runs (G-code over MQTT, with idle-state ACK) — for a print BamDude can
   prove it started, over a file known to declare no swap sequence of its own (see
   [A held table swap](#a-held-table-swap)).
3. **Plate-clear confirmation is bypassed** — the swapper handles plate clearing.
4. The next queued print is dispatched.
5. Cycle repeats until the queue is empty.

This is the **unattended batch production** mode for compatible printers.

!!! warning "Start prints from BamDude, not from the printer's screen"

    Swap macros only run for prints **BamDude dispatched** — from a queue, from
    Auto-Queue, from an archive re-print or from Send-to-Printer. A print you
    start on the printer's own touchscreen (or from a slicer straight to the
    machine) never passes through BamDude's dispatcher, so:

    - the `swap_mode_change_table` macro **does not run** — the table is not
      swapped, and the finished part stays where it is;
    - because nothing swapped the plate, BamDude asks for the manual
      **Clear Plate** confirmation before the next queued print, exactly as it
      would for a non-swap printer.

    The result is a printer that looks idle while its queue does not advance.
    Press **Clear Plate** on the printer card once the bed is actually empty and
    the queue resumes.

    The one exception is a file that **declares its own swap sequence** (what
    swaplist.app exports — see [A File's Own Swap Sequence](#a-files-own-swap-sequence)):
    the table changes are baked into its G-code, so it swaps correctly even when
    started from the printer. When BamDude saw that start and downloaded the file,
    no confirmation is asked for; a print it only matched by its name later still
    asks.

!!! note "A cancelled or failed print always asks for confirmation"

    Swap macros are deliberately skipped when a print does not end successfully —
    the part (or its remains) is still attached to the bed, and swapping then
    would either jam the rig or rotate a fouled plate into the next print. That
    is why the queue stops and waits for you after a failure: it is the safe
    outcome, not a fault.

    If a print was marked failed because BamDude **lost contact with the printer
    while a swap macro was running**, the message says so explicitly — that is a
    network problem, not a macro problem. Short connection drops are ridden out
    for 30 seconds before the print is given up on.

---

## :material-file-check: A File's Own Swap Sequence

Some files carry the table changes **inside their G-code** — what swaplist.app exports. BamDude must not add its own
swap macros to those, or the table would be swapped twice. Whether a file does is a **declaration** the file makes
once, and the print keeps it.

**How a file declares it.** By its own file name when it first comes in — an upload, a ZIP member (the member's name,
not the ZIP's), an external folder scan, the Virtual Printer, a MakerWorld import, a file saved off a printer: a
`.swap.` or `.swaps.` marker **between dots** (`Tray.swaps.gcode.3mf`). Renaming the file later declares nothing; an
external folder scan reads it again only when the file's content has changed. Files BamDude slices itself declare no
sequence of their own.

**The print keeps it.** A queued job captures the declaration together with the file's bytes: renaming the library
file, copying the job or deleting the original changes nothing, and the print's archive records it, so a reprint
carries it too.

| The file… | BamDude's swap macros | Printer list |
|---|---|---|
| declares its own sequence | not added | narrowed to swap-mode printers |
| declares none | the swap macros you chose | every printer |
| is **unknown** | not guessed — see below | every printer |

**What is unknown.** A print archived before this was recorded (BamDude never wrote it down, so an old "no" is not
trusted); a library file without a content hash — one in an external folder until a folder scan has actually read
it, a managed one until it is uploaded again as a new copy — and its SWAP tag is not shown meanwhile; a print started
from the printer's screen whose file could not be downloaded. Any of them can be [declared by you](#declaring-a-file-yourself).

**Older external files.** A file an external folder scan brought in before this version recorded only "no", whatever
it held. BamDude now judges such a file by its name **on the share** — the same `.swap.` / `.swaps.` rule a new file
gets — never by the name the library shows, which a rename in BamDude changes. The upgrade records that answer once,
so the SWAP tag and the tag filter agree with it. A managed library file from before keeps the answer it had: BamDude
cannot tell any more whether that "no" was a declaration or an old default. The name on disk can be wrong about what
the G-code does — it is the same trust a new file's name gets; when in doubt, declare the file yourself.

**Over an unknown source**, asking for BamDude's swap macros is refused rather than guessed:

- the print dialog says the source's swap compatibility is unknown and offers **Print without the extra swap
  macros** for this one job — your saved swap settings, and what a grouped run carries to its next file, stay as
  they are. Without our macros the printer's ordinary plate rules apply: with plate confirmation on, the next job
  waits for the plate to be cleared;
- a job that was already queued with our swap macros fails before it is sent and says why. **Retry** sends it again
  exactly as it was, so it fails again; queue the file again with the swap macros off, or reprint the archive with
  **Print without the extra swap macros**;
- an AutoQueue job waits for a printer without swap mode when one could print it, busy or not, and fails the same
  way only when none could.

**Saving an archive to the library** carries its known declaration across — yours included, see below. An unknown
one is refused, and so is a file the library already holds under the other declaration — the archive itself stays.

### :material-account-check: Declaring a file yourself

When the name does not say, or says wrong, you can say it: **Swap declaration…** in an archive's menu and in the
menu of a 3MF or G-code library file, or **Declare this source…** in the print dialog's unknown note. You need the right to edit that
archive or file.

1. BamDude **reads the file** a reprint would print and shows its name, size, content hash and what is declared now.
2. You choose **The file carries its own plate-change sequence** or **The file does not carry its own plate-change
   sequence** — neither is chosen for you. This is your statement about the file, not an analysis of its G-code:
   "does not carry" lets the swap macros a job asks for run; "carries its own" means BamDude adds none of its swap
   macros. Your saved swap settings are not changed.
3. **Save declaration** reads the file again and saves the declaration only for **exactly the bytes you saw**. If
   the file changed in between, or someone declared it first, nothing is saved — read it again and decide again.
   Who declared it and when is kept with it, and the dialog shows it whenever you open it — a declaration a
   backup restored says so.

For an archive this is a declaration of its **file**, for future reprints. What the print that was archived ran with
— and anything still owed at its end, such as a held table swap — stays exactly as it was recorded.

**Jobs already queued keep their own answer.** A job captured the declaration together with its bytes when it was
queued, so a new declaration does not reach it by itself. After saving — or when you open the dialog on a file that
already has your declaration — it lists the waiting and failed jobs that print this file and lets you **apply** the declaration to the ones you select — none is selected for you. Only a
job whose own answer is unknown, that holds exactly these bytes and that was never sent to a printer can take it; a
job that already has its own answer is never overwritten (queue the file again to print with the new one). The
selected jobs change together or not at all. If someone declares the file differently while the dialog is open,
the list goes and the dialog asks you to read the file again — nothing is applied under a declaration you were not
shown. Applying is not a retry: a failed job stays failed until you press
**Retry**.

### :material-pause-circle: A held table swap

BamDude runs its selected change-table macro only after a proved successful completion of the exact print, on a printer still in swap mode, over a source known not to contain its own swap sequence.

If the change is refused, fails or has an uncertain outcome, the printer gets a **plate inspection gate**, even when ordinary plate confirmation is off. The printer card and queue show the inspection without needing another queued job. An uncertain or partial attempt asks you to inspect the mechanism as well as the plate. BamDude does not automatically resend that macro.

After inspecting the mechanism and freeing the plate, press **Checked, plate is clear** on the current inspection. This records your answer, closes the old swap obligation and releases its gate together. It does not report the macro as successful. **Repeat print** also answers the inspection before queuing a fresh print. Old tabs and Telegram buttons cannot clear a newer inspection.

The gate itself blocks dispatch; this condition does not add a queue pause. Any existing manual queue pause or farm recovery hold remains in force. Legacy queue pauses are not resumed automatically because their original cause cannot be established reliably.

A table change deferred solely by farm recovery remains owed under its execution claim. Once the farm and printer are admitted, its normal resolver may perform that still-unattempted change once. A final manual inspection is a separate state and is not automatically retried after recovery.

If the print identity is unresolved, use **System → Print state diagnostics** first. A clean plate does not prove which print finished. Confirmation of identity does not bypass an existing manual inspection. A successful, proved table swap does not create an inspection gate.


---

## :material-lightbulb-on: Pair with `print_started` / `print_finished` Macros

The newer `print_started` and `print_finished` events (see [Macros](macros.md)) fire *in addition to* swap macros, on every print regardless of swap mode. Use them for orthogonal automation — chamber lights, external relays, etc.

**Example: chamber lights on for swap-mode prints only**

| Macro 1 | Macro 2 |
|---------|---------|
| Action: MQTT-action | Action: MQTT-action |
| Event: `print_started` | Event: `print_finished` |
| Command: `chamber_light_on` | Command: `chamber_light_off` |
| `swap_mode_only`: `true` | `swap_mode_only`: `true` |
| `delay_seconds`: `10` | `delay_seconds`: `0` |

Lights cycle only on actual swap-mode runs; manual prints from the same printer leave the light untouched.

---

## :material-alert: Requirements

| Requirement | Details |
|-------------|---------|
| **Printer** | A1 Mini (primary target) |
| **Hardware** | Plate swapper installed |
| **Macros** | `swap_mode_change_table` G-code macro configured |
| **Queue items** | At least 2 prints queued for the printer |

---

## :material-lightbulb: Tips

!!! tip "Test the swap macro manually"
    Run the `swap_mode_change_table` G-code from the printer's file
    browser (or via **Macros → Run Now**) before enabling swap mode
    in production. A bad swap routine wedges the entire queue.

!!! tip "Combine with batch quantity"
    Use the queue's batch-quantity feature to enqueue N copies, then
    let swap mode run them back-to-back. Combine with smart-plug
    auto power-off for fully unattended overnight runs.

!!! tip "Monitor remotely"
    Camera streaming + the Telegram bot let you watch the swap
    operation and get notified on queue completion or failure. See
    [Telegram Bot](telegram-bot.md) and [Camera](camera.md).

## After a restart or connection gap

BamDude keeps the execution archive, queue claim and selected unfinished table change. It compares a fresh printer job ID with the ID saved when that print was sent. A matching filename or an old cached ID cannot establish that the printer is still running the same job.

If the ID is missing, open **System → Print state diagnostics**, select the affected printer and review **Confirm this is the queued print**. Confirm only after checking that the physical print is the exact queue item and archive shown. Preview and Apply are separate steps, and the confirmation is recorded in recovery history. If the printer reports a different positive ID, confirmation is unavailable.

Confirmation applies only to the current connection and print. For a running print, its selected completion actions wait for FINISH. For an already finished print, its still-unattempted owed table change may proceed through the normal resolver, unless it already requires a manual plate inspection. This does not repeat print-start events or material accounting and does not release farm or manual queue pauses. Another disconnect requires fresh proof again; a previously attempted table change is never resent automatically.

> Originally based on [Bambuddy](https://github.com/maziggy/bambuddy) documentation.
