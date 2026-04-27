---
title: Virtual Printer
description: Emulate a Bambu printer for slicer uploads, with review/auto-dispatch routes and PASV-NAT support
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

A VP runs in **exactly one of three modes**. The mode is set per-VP and validated server-side — anything else is rejected with HTTP 400.

| Mode | What happens to uploads | Use case |
|------|-------------------------|----------|
| **`file_manager`** (default) | Upload lands in `/pending-uploads` as a **review item**. From the review modal an operator can dispatch to a real printer, archive in bulk (no print), or reject. | Multi-user / multi-machine inbox where every upload gets a sanity check before printing — also the right mode if you only want to **archive** without printing (use the bulk-archive action in the review modal). |
| **`print_queue`** | Upload is archived **and** queued on a target printer. With `auto_dispatch=true` the queue item starts immediately; with `auto_dispatch=false` it waits for an explicit Start click. | Hands-off production: slice → send → BamDude prints it. |
| **`proxy`** | The slicer's TLS session is TCP-proxied to a real `target_printer_id` — BamDude is just the public endpoint. | Remote printing — slicer reaches BamDude over LAN/VPN, BamDude reaches the printer. |

!!! info "There is no separate ‘archive only’ mode"
    Earlier versions of this page mentioned an `immediate` mode that auto-created an archive row without involving the queue or library. **That mode was never in the code** — the docs were wrong. The code's mode enum is exactly the three above (see `backend/app/models/virtual_printer.py` and the validator in `backend/app/api/routes/virtual_printers.py`). To get archive-only behaviour, use `file_manager` mode and bulk-archive uploads from the review modal — they get a `print_archives` row without ever touching a printer.

---

## :material-cog: Setup

**Settings → Virtual Printer → Add Virtual Printer**:

| Field | Notes |
|-------|-------|
| Name | Display label (e.g. `Studio inbox`). |
| Model | SSDP model code — pick the printer model you want the VP to impersonate so slicer compatibility checks pass. |
| Bind IP | Optional. Leave empty to listen on `0.0.0.0` (host's all interfaces) — fine if you only need one VP on the standard ports. Set a dedicated IP only when running **multiple VPs side-by-side** so each gets its own FTPS / MQTT / SSDP listener. On Linux the easiest way to provision extra IPs is a virtual interface (alias) on the host. |
| Access code | 8-character code the slicer authenticates with. |
| Mode | One of the three above (`file_manager` / `print_queue` / `proxy`). |
| Auto-dispatch | `print_queue` mode only — see below. |
| Target printer | `proxy` mode only — the real printer to forward to. |

Slicers discover the new VP automatically via SSDP within a minute or two. If discovery fails, add it manually by IP + access code.

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

## :material-flash: Auto-Dispatch (print_queue mode)

A VP in `print_queue` mode with `auto_dispatch=true` skips review entirely:

- Slicer "Send to Printer" → VP receives upload over FTPS
- VP creates a queue item targeting whichever real printer policy you've configured
- Background dispatch picks it up like any other queue item — no operator step

Set `auto_dispatch=false` if you want every queued upload to wait for an explicit Start click in the queue UI before dispatch.

!!! tip "Trusted upstream only"
    Auto-dispatch removes the human gate. Use it when the upstream source is yourself or a trusted automation (slicer plugin, CI job, MakerWorld webhook). For shared / multi-tenant uploads, prefer `file_manager` mode + the review modal.

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
- **Hands-off dispatch** — `print_queue` + `auto_dispatch=true` is the closest you get to "Cloud Print but local".
- **Manual gate on a queue** — `print_queue` + `auto_dispatch=false` queues the upload but waits for an explicit Start click before the dispatcher picks it up.
- **Remote printing** — `proxy` mode forwards a remote slicer's TLS session straight to a real printer, with BamDude's certificate as the public face.

---

## :material-lightbulb: Tips

!!! tip "One VP per workflow"
    Nothing stops you running multiple VPs at once on different IPs — one for production auto-dispatch, one for review, one for archiving. They share the same backend so all data stays unified.

!!! tip "Slicer auth caching"
    Bambu Studio / OrcaSlicer cache the access code per discovered printer. Rotate the VP access code and slicers will prompt again — no manual cache-clear needed.

> Originally based on [Bambuddy](https://github.com/maziggy/bambuddy) documentation.
