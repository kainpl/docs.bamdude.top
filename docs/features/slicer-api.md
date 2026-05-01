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
                │  slicer_api   │   POST /slice            │ slicer-api       │
                │  HTTP bridge  │ ──────────────────►      │ sidecar          │
                │               │                          │   OrcaSlicer or  │
                │               │   GET /slice/progress    │   BambuStudio    │
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

Both speak the same `/slice` HTTP API. You can run either one or both at once; pick the active one(s) in **Settings → Profiles → Slicer API**.

---

## :material-docker: Setup with Docker Compose

The BamDude repo ships a ready-made stack at [`slicer-api/`](https://github.com/kainpl/bamdude/tree/main/slicer-api) — the simplest route is to use it directly:

```bash
git clone https://github.com/kainpl/bamdude.git
cd bamdude/slicer-api/
cp .env.example .env       # optional — pin slicer versions / ports

# Pick exactly one:
docker compose --profile orca   up -d   # OrcaSlicer only      (host port 3003)
docker compose --profile bambu  up -d   # BambuStudio only     (host port 3001)
docker compose --profile all    up -d   # both
```

A bare `docker compose up -d` (no profile) starts nothing — you must include `--profile orca`, `--profile bambu`, or `--profile all`. Then in BamDude → **Settings → Profiles → Slicer API**, fill the URL field for the slicer(s) you started (`http://localhost:3003` for Orca, `http://localhost:3001` for BambuStudio).

!!! warning "Docker Desktop 4.71 first-build workaround"
    Docker Desktop 4.71 (engine 29.4.1 / compose v5.1.x / buildx 0.33.x-desktop) ships a broken `buildx bake` compose-bridge: `docker compose build` dies immediately with `failed to execute bake: exit status 1` and no further detail, regardless of profile shape. `COMPOSE_BAKE=false` does NOT disable it on this version.

    **Workaround for the first build** — force the legacy classic builder; the image is then cached and `compose up -d` reuses it:

    ```bash
    # bash / zsh
    DOCKER_BUILDKIT=0 COMPOSE_DOCKER_CLI_BUILD=0 \
      docker compose --profile all build
    docker compose --profile all up -d
    ```

    ```powershell
    # PowerShell
    $env:DOCKER_BUILDKIT = "0"; $env:COMPOSE_DOCKER_CLI_BUILD = "0"
    docker compose --profile all build
    $env:DOCKER_BUILDKIT = $null; $env:COMPOSE_DOCKER_CLI_BUILD = $null
    docker compose --profile all up -d
    ```

    Or use buildx directly (modern BuildKit, parallel-friendly, faster):

    ```bash
    docker buildx bake -f docker-compose.yml orca-slicer-api
    docker buildx bake -f docker-compose.yml bambu-studio-api
    docker compose --profile all up -d
    ```

    Older Docker Desktop releases (4.70 and below) and Docker CE on Linux are unaffected — no env vars needed.

### Running the sidecar(s) on a different host

If your BamDude server can't run the sidecar containers itself (resource limits, no Docker available, etc.), put the sidecar(s) on another host and point BamDude at them via URL. Use the same `slicer-api/docker-compose.yml` from the BamDude repo on the sidecar host, then in BamDude's `Settings → Profiles → Slicer API` set the URL to `http://<sidecar-host>:3003` / `:3001` instead of `localhost`. The sidecar exposes no auth — keep it on a trusted network (LAN, Tailscale, WireGuard).

You can also override the env-var defaults that BamDude reads at startup: `SLICER_API_URL` (default `http://localhost:3003`) and `BAMBU_STUDIO_API_URL` (default `http://localhost:3001`). The UI URL fields take precedence when set.

---

## :material-cog: Settings → Profiles → Slicer API

| Setting | What it does |
|---------|--------------|
| **Preferred slicer** | `OrcaSlicer` or `Bambu Studio`. Default sidecar for server-side slicing and the desktop "Open in Slicer" URI on archives that aren't sliced server-side. When both sidecars are configured *and* reachable, the Slice modal also shows a per-job "Slice with" radio so you can override this default per source file (the choice is remembered per file in the browser's localStorage). |
| **Enable server-side slicing** (`use_slicer_api`) | Master toggle. When off, the Slice button disappears from the File Manager — slicing falls back to opening the source in the user's local desktop slicer via URI scheme. |
| **OrcaSlicer API URL** (`orcaslicer_api_url`) | URL of the OrcaSlicer sidecar — e.g. `http://localhost:3003` for the default compose recipe. Empty = use `SLICER_API_URL` env default. |
| **BambuStudio API URL** (`bambu_studio_api_url`) | URL of the BambuStudio sidecar — e.g. `http://localhost:3001`. Empty = use `BAMBU_STUDIO_API_URL` env default. |

Preset tiers (cloud / local / standard) are merged automatically by the backend at slice time and don't need a per-install setting — see "Slicing a file" below.

---

## :material-cursor-default-click: Slicing a file

From **File Manager**: action menu on an STL / 3MF / STEP / STP file → **Slice**.

The Slice modal opens with three preset dropdowns:

- **Printer profile** — from the unified preset listing. Each entry is sourced from one of three tiers, merged with name-based dedup (cloud > local > standard): `cloud` (per-user Bambu Cloud presets), `local` (your imported `.json` profiles), `standard` (bundled defaults baked into the sidecar). The modal labels the tier next to each option.
- **Process profile** — same three tiers.
- **Filament profile(s)** — one dropdown per AMS slot the picked plate uses. The modal pre-picks the best match per slot using the source 3MF's filament metadata (type + colour score) so a single click on **Slice** usually does the right thing for multi-color jobs.

A **"Slice with" radio** sits above the dropdowns when both OrcaSlicer and BambuStudio sidecars are reachable — pick which slicer should run *this* job. First-time default is the global *Preferred slicer* setting; subsequent opens of the same source file default to your last pick. When only one sidecar is reachable the radio stays hidden (there's nothing to pick) and the reachable one is used regardless of the global default.

For multi-plate 3MFs the modal asks which plate(s) before opening (single-plate / non-3MF skips the picker). A **printer-mismatch warning** appears when the source 3MF was sliced for a different printer model than the picked profile — the Slice button stays disabled until you switch profiles, since the slicer CLI silently falls back to the source's embedded settings instead of raising an error.

A persistent toast in the bottom-right tracks the job: live progress percent + elapsed time, replaced by a transient success / error toast on completion. The sliced output lands in the same library folder with `.gcode.3mf` extension and `source_type='sliced'` provenance — the original file is untouched.

---

## :material-shield-key: Permissions

| Permission | Grants |
|------------|--------|
| `library:upload` | Trigger a slice from the File Manager (the sliced output is a fresh library upload). |
| `library:read` | Poll the job-tracker toast (`/api/v1/slice-jobs/{id}`) and the filament-discovery preview slice progress (`/api/v1/slicer/preview-progress/{id}`). |
| `cloud:auth` | Required to fetch the `cloud` preset tier — without it, the modal shows only `local` + `standard` tiers. |

The Settings → Profiles → Slicer API toggle and URL fields are gated by `settings:update`.

---

## :material-alert-circle-outline: Failure modes

- **Sidecar offline** → 502 surfaced as toast, job marked failed; original file untouched.
- **Profile not found** → 400 names the missing profile so you can add it via [K-Profiles](kprofiles.md) or pick a different tier.
- **Sidecar rejects the file** (corrupt 3MF, unsupported plate format, malformed preset, etc.) → toast surfaces the sidecar's verbatim CLI stdout/stderr so you don't have to dig in container logs.
- **Embedded-settings fallback** — for 3MF sources, a 5xx from the sidecar with `--load-settings` triggers ONE retry without profiles. The slice then uses the source's embedded settings (the ones the original slicer baked into `Metadata/slice_info.config`); the resulting row carries `used_embedded_settings: true` in its metadata. STL has no embedded settings, so 5xx is terminal there.
- **Cloud presets unreachable** (token expired / network down) → the modal renders the `cloud` tier with a status banner and falls back to `local` + `standard` only.

---

## :material-link-variant: Related

- [File Manager](file-manager.md) — where the Slice button lives.
- [K-Profiles](kprofiles.md) — how to feed your local OrcaSlicer filament profiles into the `local` tier.
- [MakerWorld import](makerworld.md) — pair imported plates with server-side slicing when no plate matches your printer.
