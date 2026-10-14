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
trusted); a library file without a content hash, until a folder scan has actually read it; a print started from the
printer's screen whose file could not be downloaded.

**Over an unknown source**, asking for BamDude's swap macros is refused rather than guessed:

- the print dialog says the source's swap compatibility is unknown and offers **Print without the extra swap
  macros** for this one job — your saved swap settings, and what a grouped run carries to its next file, stay as
  they are. Without our macros the printer's ordinary plate rules apply: with plate confirmation on, the next job
  waits for the plate to be cleared;
- a job that was already queued with our swap macros fails before it is sent and says why. **Retry** sends it again
  exactly as it was, so it fails again; queue the file again with the swap macros off, or reprint the archive with
  **Print without the extra swap macros**.

**Saving an archive to the library** carries its known declaration across. An unknown one is refused, and so is a
file the library already holds under the other declaration — the archive itself stays.

### :material-pause-circle: A held table swap

When a print ends, BamDude runs its own `swap_mode_change_table` only for a print it can prove it started (its own
dispatch, a start from the printer's screen it saw, or the printer's exact job id), that **completed**, on a printer
still in swap mode with its change-table macro, over a file known to declare **no** sequence of its own. Otherwise —
an unknown or self-swapping file, a finish BamDude cannot tie to its print, a failed or cancelled print, swap mode
off, no macro, an outcome left uncertain by an outage —:

- nothing is sent, and the step stays owed — it is never fired later by itself;
- the plate is not cleared;
- the printer's queue is **paused**, even when plate confirmation is off, with a reason on the job that ran, on the
  next waiting job, and as a **Swap held** badge on the print in the archive. The reason says whether the swap cycle
  had **started**, **may have started**, or did not start.

Inspect the swap mechanism and the plate, clear the plate if it needs it, then resume the queue as usual. Likewise a
print whose file declares its own sequence clears the plate only for such a proven, completed print — never one
BamDude matched only by its name, and never an order with auto-eject, which keeps its own plate handling.

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

> Originally based on [Bambuddy](https://github.com/maziggy/bambuddy) documentation.
