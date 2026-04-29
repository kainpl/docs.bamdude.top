---
title: Virtual Printer
description: Emulate a Bambu printer for slicer uploads — review, per-printer queue, auto-queue, or proxy
---

# Virtual Printer

The Virtual Printer (VP) makes BamDude appear as one or more Bambu Lab printers on your LAN. Bambu Studio / OrcaSlicer's "Send to Printer" lands files on a VP exactly the way it would on a real printer — over secure TLS (MQTT + FTPS) with the printer's access code. From there BamDude routes the upload according to the VP's mode.

---

## :material-printer-3d: Overview

Each VP:

- Advertises itself over **SSDP** with a real Bambu model code (X1C / P1S / A1 Mini / H2D / …) so slicers discover it automatically.
- Runs its **own FTPS + MQTT + SSDP servers**. By default they listen on `0.0.0.0` (the host's all interfaces); when you want multiple VPs side-by-side, give each a dedicated `bind_ip` so they don't fight for the same ports.
- Carries an **access code** like a real printer — slicers prompt for it on first use and cache it afterwards.
- Has a **serial number** and **model code** that match Bambu's real format, so the slicer's compatibility checks pass.

---

## :material-swap-horizontal: Modes

A VP runs in **exactly one mode**. The mode is set per-VP and validated server-side — anything else is rejected with HTTP 400.

| Mode | What happens to uploads | Use case |
|------|-------------------------|----------|
| **`file_manager`** (default) | Upload lands in `/pending-uploads` as a **review item**. From the review modal an operator can dispatch to a real printer, archive in bulk (no print), or reject. | Multi-user / multi-machine inbox where every upload gets a sanity check before printing — also the right mode if you only want to **archive** without printing (use the bulk-archive action in the review modal). |
| **`print_queue`** | Upload is archived **and** queued on a **specific** target printer. With `auto_dispatch=true` the queue item starts immediately; with `auto_dispatch=false` it waits for an explicit Start click. | You always print this VP's uploads on the same machine. |
| **`auto_queue`** | Upload is archived and dropped into the **[auto-queue router](auto-queue.md)** — no fixed target. The scheduler picks any eligible idle printer (model + filament + color match). | Hands-off load-balancing across a multi-printer farm. |
| **`proxy`** | The slicer's TLS session is TCP-proxied to a real `target_printer_id` — BamDude is just the public endpoint. | Remote printing — slicer reaches BamDude over LAN/VPN, BamDude reaches the printer. |

!!! info "There is no separate ‘archive only’ mode"
    Earlier versions of this page mentioned an `immediate` mode that auto-created an archive row without involving the queue or library. **That mode was never in the code** — the docs were wrong. The code's mode enum is exactly the four above (see `backend/app/models/virtual_printer.py` and the validator in `backend/app/api/routes/virtual_printers.py`). To get archive-only behaviour, use `file_manager` mode and bulk-archive uploads from the review modal — they get a `print_archives` row without ever touching a printer.

---

## :material-cog: Setup

**Settings → Virtual Printer → Add Virtual Printer**:

| Field | Notes |
|-------|-------|
| Name | Display label (e.g. `Studio inbox`). |
| Model | SSDP model code — pick the printer model you want the VP to impersonate so slicer compatibility checks pass. |
| Bind IP | Optional. Leave empty to listen on `0.0.0.0` (host's all interfaces) — fine if you only need one VP on the standard ports. Set a dedicated IP only when running **multiple VPs side-by-side** so each gets its own FTPS / MQTT / SSDP listener. On Linux the easiest way to provision extra IPs is a virtual interface (alias) on the host. |
| Access code | 8-character code the slicer authenticates with. |
| Mode | One of the four above. |
| Auto-dispatch | Active in `print_queue` and `auto_queue` modes — see below. |
| Target printer | `print_queue` mode (specific target) and `proxy` mode only. Hidden when `auto_queue` or `file_manager` is selected. |

Slicers discover the new VP automatically via SSDP within a minute or two. If discovery fails, add it manually by IP + access code.

---

## :material-form-select: Mode picker UI

The Add / Edit dialog lays the four modes out as **three big buttons** plus a sub-toggle — because `print_queue` and `auto_queue` are really two flavours of the same thing (queue dispatch, with vs without a fixed target):

```
┌──────────────────────────────────────────────────────────┐
│  Mode                                                    │
│  ┌─────────────┬───────────────┬──────────────────────┐  │
│  │   Queue     │  File Manager │    ⇄  Proxy          │  │
│  └─────────────┴───────────────┴──────────────────────┘  │
│                                                          │
│  When Queue is picked:                                   │
│    [ ] Auto-select printer  ← toggle                     │
│        on  → mode = auto_queue                           │
│        off → mode = print_queue + Target Printer field   │
│                                                          │
│  Auto-dispatch                          [ ]              │
└──────────────────────────────────────────────────────────┘
```

When **Queue → Auto-select printer = on**, the VP is in `auto_queue` and the Target Printer dropdown disappears (any printer of the matching model can pick it up). When **Auto-select = off**, you get `print_queue` and a Target Printer dropdown the upload always lands on.

`file_manager` and `proxy` are full-width buttons of their own.

### Model ↔ Target Printer linking

In `print_queue` mode the dialog also wires Model and Target Printer together so you can't end up with an inconsistent pair:

- Pick a **Target Printer** → the VP's Model auto-fills from that printer's model.
- Pick a **Model** → the Target Printer dropdown filters down to printers of that model. If your previously-selected target doesn't match the new model, the dialog clears it.
- An explicit **clear (×) button** sits inside the Target Printer field if you want to wipe the selection without changing model.

---

## :material-shield-alert: Validation rules

The backend (`POST /virtual-printers/`, `PUT /virtual-printers/{id}`) enforces these:

| Rule | Error |
|------|-------|
| `mode='print_queue'` + `auto_dispatch=true` + no `target_printer_id` (and not switching to auto-select) | **400** — *"Auto-dispatch in Queue mode requires a Target Printer. Pick a target, enable Auto-select printer, or turn Auto-dispatch off."* |
| `mode='proxy'` without `target_printer_id` | **400** — *"Proxy mode requires a Target Printer."* |
| Any other `mode` value | **400** — *"Invalid mode."* |

The `PUT` route revalidates the **effective** state after applying the body, so you can't sneak past the rule by clearing one field at a time. If you need to clear an existing target, send `clear_target_printer: true` — the dialog's × button does this for you.

The frontend mirrors this with a yellow warning banner that disables the Auto-dispatch toggle when the combination would be unsafe, so you see the constraint before you submit.

---

## :material-clipboard-check: Review Modal (file_manager mode)

In `file_manager` mode, every uploaded 3MF lands in a **review queue** at `/pending-uploads`. From the review modal an operator:

1. Opens an upload, sees the parsed metadata + thumbnail.
2. Picks the target real printer.
3. Verifies AMS slot mapping, plate selection, and any per-print options.
4. Clicks **Send to Printer** — the 3MF is dispatched through the standard background-dispatch pipeline (FTP upload, swap macros, archive linkage).

Review batches can also be **archived in bulk** (no print, just stash the metadata) or **rejected** (deletes the upload). Use this when multiple users / machines slice into the same VP and you want a sanity check before it actually hits a printer.

API: `GET /api/v1/pending-uploads/`, `POST /api/v1/pending-uploads/{id}/archive`, `POST /api/v1/pending-uploads/archive-all`.

---

## :material-flash: Auto-Dispatch (Queue modes) {#auto-dispatch}

A VP in either Queue mode (`print_queue` or `auto_queue`) honours the `auto_dispatch` flag:

| `auto_dispatch` | `print_queue` | `auto_queue` |
|-----------------|---------------|--------------|
| **true** | Slicer upload → archived → queued → dispatched immediately. | Slicer upload → archived → dropped into the [auto-queue router](auto-queue.md) → next 30 s tick assigns it to an eligible idle printer. |
| **false** | Slicer upload → archived → queued in `pending`, waits for an explicit Start click in the queue UI. | Slicer upload → archived → router row is created with `manual_start=true` so it's ignored by the scheduler until released from the auto-queue panel. |

!!! tip "Trusted upstream only"
    Auto-dispatch removes the human gate. Use it when the upstream source is yourself or a trusted automation (slicer plugin, CI job, MakerWorld webhook). For shared / multi-tenant uploads, prefer `file_manager` mode + the review modal.

---

## :material-router-network: auto_queue mode {#auto_queue}

`auto_queue` is the natural pairing between the VP and the [auto-queue router](auto-queue.md). On upload the VP:

1. Archives the 3MF (full per-plate metadata, thumbnails, source-hash chain).
2. Calls `extract_auto_queue_requirements` on the archived file to pull out:
    - `target_model` (from `sliced_for_model` in the 3MF)
    - `required_filament_types` (from `slice_info.config`)
    - `plate_id` if the slicer specified a single plate
3. Creates an `AutoQueueItem` with `manual_start = !auto_dispatch`.
4. Returns an FTPS success to the slicer — same UX as a real printer accepting the file.

The router takes over from there: 30 s tick, eligible-printer search, AMS mapping at assign time. See the [auto-queue doc](auto-queue.md) for the full routing flow.

There's no Target Printer to set on an `auto_queue` VP — that's the whole point. The dialog hides the field and clears any value left over from a mode switch.

---

## :material-network-outline: PASV Address (NAT / Docker bridge)

FTPS uses the PASV command, where the server tells the client which IP to dial back on for the data channel. When BamDude runs in a Docker bridge network (or behind any NAT), the PASV response would otherwise advertise the **container's internal IP** — slicers on the LAN can't reach it and the data channel fails mid-handshake.

Set the `VIRTUAL_PRINTER_PASV_ADDRESS` env var to the **externally-reachable IP** (the host's LAN address — most slicers don't resolve hostnames here):

```bash
VIRTUAL_PRINTER_PASV_ADDRESS=192.168.1.100
```

The FTPS server boots, logs `FTP PASV address override: 192.168.1.100`, and from then on every PASV reply uses that address. No effect when BamDude runs on the host network — leave it unset there.

---

## :material-rocket: Use Cases

- **Multi-user farm inbox** — `file_manager` + review modal lets several people slice into the same VP without stepping on each other.
- **Print archiving without printing** — `file_manager` + the **bulk-archive** action in the review modal turns slice → send into a permanent record (thumbnails, metadata, source 3MF) without committing to a print.
- **Library building** — same `file_manager` mode: archive uploads from the review modal so you can attach them to projects, batch-print, or share with the team before the first build.
- **Single-target hands-off** — `print_queue` + a fixed Target Printer + `auto_dispatch=true` is the closest you get to "Cloud Print but local" for one machine.
- **Manual gate on a queue** — `print_queue` + `auto_dispatch=false` queues the upload but waits for an explicit Start click before the dispatcher picks it up.
- **Farm load-balancing** — `auto_queue` + `auto_dispatch=true` is the killer workflow for a multi-printer farm: slicer doesn't know which printer will run the job, the router decides at dispatch time.
- **Remote printing** — `proxy` mode forwards a remote slicer's TLS session straight to a real printer, with BamDude's certificate as the public face.

---

## :material-lightbulb: Tips

!!! tip "One VP per workflow"
    Nothing stops you running multiple VPs at once on different IPs — one for production auto-dispatch, one for review, one for archiving. They share the same backend so all data stays unified.

!!! tip "Slicer auth caching"
    Bambu Studio / OrcaSlicer cache the access code per discovered printer. Rotate the VP access code and slicers will prompt again — no manual cache-clear needed.

> Originally based on [Bambuddy](https://github.com/maziggy/bambuddy) documentation.
