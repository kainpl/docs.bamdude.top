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
2. The `swap_mode_change_table` macro runs (G-code over MQTT, with idle-state ACK).
3. **Plate-clear confirmation is bypassed** — the swapper handles plate clearing.
4. The next queued print is dispatched.
5. Cycle repeats until the queue is empty.

This is the **unattended batch production** mode for compatible printers.

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
