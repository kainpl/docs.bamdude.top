---
title: Slicer API (server-side slicing)
description: Send STL or 3MF to a containerised OrcaSlicer / BambuStudio sidecar and get a printable .gcode.3mf back without leaving BamDude
---

# Slicer API (server-side slicing)

BamDude can slice STL and unsliced 3MF files **on the server** by talking to a containerised **OrcaSlicer** or **BambuStudio** sidecar over HTTP. Drop a file in the library, click **Slice**, pick a printer model + filament profile, and a printable `.gcode.3mf` lands back in the library a minute later — no laptop, no slicer round-trip, no dragging files around.

This is opt-in: no slicer ships in the BamDude image itself. You run the sidecar separately (Docker Compose recipe below) and tell BamDude where it lives.

---

## :material-architecture: Architecture

```
                ┌───────────────┐
   Library file │   BamDude     │   STL / 3MF (settings)
  ──────────►   │   backend     │ ──────────────────►
                │               │                          ┌──────────────────┐
                │  slicer_api   │   POST /v1/slice         │ slicer-api       │
                │  HTTP bridge  │ ──────────────────►      │ sidecar          │
                │               │                          │   OrcaSlicer or  │
                │               │   GET /v1/jobs/{id}      │   BambuStudio    │
                │               │ ◄──────────────────      │   CLI inside     │
                │               │                          │                  │
                │               │   .gcode.3mf bytes       │                  │
                │               │ ◄──────────────────      │                  │
                │               │                          └──────────────────┘
                │  Library row  │
                │  + archive    │
                └───────────────┘
```

The bridge keeps the sliced output **in the library** (or the archive, depending on which page you sliced from), records every parameter that went into the slice, and falls back to a clean error if the sidecar is offline or rejects the file.

---

## :material-package-variant: Supported sidecars

| Slicer | Container | Notes |
|--------|-----------|-------|
| **OrcaSlicer** | Open-source community-maintained image | Recommended — actively developed, broad printer/filament coverage. |
| **BambuStudio** | Bambu Lab's official slicer | Use when you need an exact byte-for-byte match with what Bambu Studio Desktop would produce. |

Both speak the same `/v1/slice` HTTP API; you choose which one in **Settings → Slicer API**.

---

## :material-docker: Setup with Docker Compose

The simplest setup is to add a slicer-api service to your existing `docker-compose.yml`. Pick the variant that matches your sidecar:

=== "OrcaSlicer"
    ```yaml
    services:
      slicer-api:
        image: ghcr.io/<community-image>/orca-slicer-api:latest
        container_name: bamdude-slicer-api
        restart: unless-stopped
        environment:
          # Optional: tweak job concurrency for big farms
          - SLICER_MAX_CONCURRENT_JOBS=2
        volumes:
          - slicer_cache:/cache
        ports:
          # Internal-only; expose via the BamDude network instead
          - "127.0.0.1:8765:8765"
    
    volumes:
      slicer_cache:
    ```

=== "BambuStudio"
    ```yaml
    services:
      slicer-api:
        image: ghcr.io/<community-image>/bambustudio-api:latest
        container_name: bamdude-slicer-api
        restart: unless-stopped
        volumes:
          - slicer_cache:/cache
        ports:
          - "127.0.0.1:8765:8765"
    
    volumes:
      slicer_cache:
    ```

Then in BamDude's `docker-compose.yml`, add the sidecar to the same network and point BamDude at it:

```yaml
services:
  bamdude:
    # …existing config…
    environment:
      # Same network → use the service name, no exposed port needed
      - SLICER_API_URL=http://slicer-api:8765
```

!!! info "Networking"
    Best practice: keep the sidecar on the BamDude network and **don't expose the port to the host** at all — only BamDude needs to reach it. The `127.0.0.1:8765` line above is just for development debugging.

---

## :material-cog: Settings → Slicer API

| Setting | What it does |
|---------|--------------|
| **Enable Slicer API** | Master toggle. When off, the Slice button disappears from the file manager and archive pages. |
| **API URL** | The sidecar's URL — e.g. `http://slicer-api:8765` for the Docker Compose recipe above. |
| **Health check** | Pings `/v1/health` and reports green / red + version + queue depth. Run before saving to catch typos. |
| **Default profile tier** | `cloud` (Bambu Studio cloud presets), `local` (per-user OrcaSlicer profiles imported via [K-Profiles](kprofiles.md)), or `standard` (community defaults baked into the sidecar). |
| **Max concurrent jobs** | Default 1. Bumping this only helps if your sidecar's image was built with concurrency support — otherwise jobs queue. |

---

## :material-cursor-default-click: Slicing a file

From **File Manager**:

1. Right-click an STL or unsliced 3MF → **Slice**.
2. The Slice modal opens:
   - **Target printer model** — list of every model you have linked, plus any standard model the sidecar exposes.
   - **Filament profile** — comes from the resolution tier (Cloud / Local / Standard). Pinned default per model.
   - **Plate** — for multi-plate 3MFs, pick which plate(s) to slice.
   - **Override snippets** — optional. If you have [G-code Injection](#) snippets configured for the printer model, they auto-apply at slice time.
3. Click **Slice**. The job tracker (top-right) shows progress; toast on completion.
4. Sliced output lands in the same library folder with `.gcode.3mf` extension and `source_type='sliced'` provenance — the original file is untouched.

From **Archives → reprint flow**: same modal, but the sliced output is saved as a fresh archive (linked back to the source) so you can reprint it directly.

---

## :material-file-cog-outline: 3MF embedded-settings fallback

Some 3MFs ship with the slicer's settings already baked in (`Metadata/slice_info.config` + per-plate `.gcode` settings inherited from the original slice). If you slice such a 3MF without explicitly overriding, the sidecar uses the embedded settings as the source of truth and the resulting library row carries `used_embedded_settings: true` in its metadata for traceability.

This is the right default — the embedded settings already produced a printable result on someone's machine; overriding them blindly would risk rejected slices. To force a re-slice with your own profile, pick a profile in the modal explicitly instead of leaving "auto".

---

## :material-shield-key: Permissions

| Permission | Grants |
|------------|--------|
| `library:upload` | Trigger a slice (the sliced output is a fresh library upload). |
| `archives:reprint` | Trigger a slice from the archive reprint flow. |

The Slicer API URL + tier defaults are gated by `settings:update`.

---

## :material-alert-circle-outline: Failure modes

- **Sidecar offline** → clean error toast, job marked failed; original file untouched.
- **Profile not found** → error names the missing profile so you can add it via [K-Profiles](kprofiles.md) or pick a different tier.
- **Sidecar rejects the file** (corrupt 3MF, unsupported plate format, etc.) → toast surfaces the sidecar's verbatim error so you don't have to dig in container logs.
- **Slice timeout** (default 10 min) → job cancelled, partial output discarded.

---

## :material-link-variant: Related

- [File Manager](file-manager.md) — where the Slice button lives.
- [K-Profiles](kprofiles.md) — how to feed your local OrcaSlicer filament profiles into the `local` tier.
- [MakerWorld import](makerworld.md) — pair imported plates with server-side slicing when no plate matches your printer.
