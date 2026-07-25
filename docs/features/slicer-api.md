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
| **Preferred slicer** | `OrcaSlicer` or `Bambu Studio`. Default sidecar for server-side (in-app) slicing. When both sidecars are configured *and* reachable, the Slice modal also shows a per-job "Slice with" radio so you can override this default per source file (the choice is remembered per file in the browser's localStorage). |
| **Enable server-side slicing** (`use_slicer_api`) | Master toggle. When off, the Slice button disappears from the File Manager — slicing falls back to opening the source in the user's local desktop slicer via URI scheme. |
| **OrcaSlicer API URL** (`orcaslicer_api_url`) | URL of the OrcaSlicer sidecar — e.g. `http://localhost:3003` for the default compose recipe. Empty = use `SLICER_API_URL` env default. |
| **BambuStudio API URL** (`bambu_studio_api_url`) | URL of the BambuStudio sidecar — e.g. `http://localhost:3001`. Empty = use `BAMBU_STUDIO_API_URL` env default. |

The desktop **Open in Slicer** button is controlled by a separate, independent setting — **Settings → Slicer → Open in Slicer** — a dropdown that defaults to **Same as API slicer**. Point it at a different slicer to, e.g., slice through the Bambu Studio sidecar but open files locally in OrcaSlicer (or vice versa); existing setups are unchanged until you pick a different value.

Preset tiers (Imported/Local → Orca Cloud → Bambu Cloud → Standard) are listed automatically by the backend at slice time and don't need a per-install setting — see "Slicing a file" below.

---

## :material-cursor-default-click: Slicing a file

From **File Manager**: action menu on an STL / 3MF / STEP / STP file → **Slice**.

The Slice modal opens with three preset dropdowns:

- **Printer profile** — from the unified preset listing. Each entry is sourced from one of four tiers listed in fixed precedence with **no cross-tier dedup** (`local` → `orca_cloud` → `cloud` → `standard`): `local` (your imported/local `.json` profiles), `orca_cloud` (per-user Orca Cloud presets), `cloud` (per-user Bambu Cloud presets), `standard` (bundled defaults baked into the sidecar). Because there is no dedup, a preset with the same name in two tiers is listed once per tier — it is no longer hidden just because another tier has one by that name. The modal labels the tier next to each option. Defaults to the printer the source 3MF was prepared with when that profile is available, otherwise the first listed.
- **Process profile** — same four tiers, but **filtered to the selected printer**: profiles for other printers drop into a trailing **"Other printers"** group instead of disappearing, and profiles with no printer info stay in the main list (never hidden). Defaults to the process the 3MF was prepared with when compatible. Changing the printer re-picks the process if the current one no longer fits.
- **Filament profile(s)** — one dropdown per AMS slot the picked plate uses, filtered the same way (compatible profiles first, "Other printers" group trailing). The modal pre-picks the best match per slot using the source 3MF's filament metadata (type + colour score), with printer-incompatible filaments demoted, so a single click on **Slice** usually does the right thing for multi-color jobs.

The modal caches the cloud and standard preset listings for a few minutes, so if you delete or rename a preset in Bambu Studio / Bambu Handy it can take a while to disappear from the dropdowns. A **Refresh** control on the preset list fetches the latest listings immediately. Importing or deleting a local profile in **Settings** also refreshes the slice dialog's presets right away.

Compatibility is decided by the profile's own `compatible_printers` list when present, then by the `@<printer>` naming convention — in all three shapes the slicer writes: `@BBL <model>`, the full `@Bambu Lab <model> <size> nozzle` form a user-saved preset gets, and a bare `@<size>` tag. A bare size can rule a printer *out* but is never taken as proof of a match, and sizes are compared numerically so `0.20` and `0.2` are the same. Orca Cloud profiles carry their own compatible-printer list, and a copy of a profile that knows its printers shares that list with copies that don't — which is what stops a profile whose name carries no model (`Overture PLA Matte @0.2`) being auto-picked for a printer it was never built for. It is **nozzle-aware**, so a 0.6-nozzle process won't show as compatible for a 0.4-nozzle printer (0.4 is the implicit default that drops the suffix). The same matcher drives the **filament-calibration** wizard's profile picker; there incompatible profiles are hidden outright rather than grouped, since a calibration print sent to the wrong printer just wastes a bed.

A **slicer picker** sits at the top of the Slice modal — two card-buttons (mirroring the "Filament Tracking" pattern in Settings) with their own live health badges. Auto-locks to the only-healthy sidecar when one is down; you pick freely when both are reachable; offline cards are disabled. First-time default is the global *Preferred slicer* setting; subsequent opens of the same source file default to your last pick (per-file localStorage).

A **bed-plate override** picker (5 options: Cool / Engineering / High Temp / Textured PEI / SuperTack) wires through to `--curr-bed-type` on the CLI. Default `Textured PEI Plate` matches the factory plate on the modern Bambu lineup; A1 / A1-mini owners flip to SuperTack once and the choice persists in localStorage. Sliced 3MFs from Bambu Studio still honour their embedded per-plate `bed_type` (BamDude forwards the original bytes) — the override only kicks in for sources without one.

A **preset-source control** above the preset dropdowns is a 3-state segmented owner filter (All / My presets / Built-in) applied across all four tiers. It classifies cloud presets as custom-vs-builtin via the same `setting_id` regex the Profiles page uses, `^(P[FPM]US|PF\d|PP\d)`; local imports are always custom, standard presets are always built-in. The selected filter is persisted in localStorage under `bamdude:slice-modal:filter-owner`. Switching the filter clears any current dropdown selection that no longer matches so a hidden (filtered-out) preset can't silently submit at slice time.

For multi-plate 3MFs the modal embeds an **inline plate selector** at the top of its body, mirroring the Print modal's plate picker — a vertical paginator + details card. Plate 1 auto-selects on load so the filament-requirements + presets queries flow without blocking on user interaction; clicking a different plate re-keys those queries. A **Slice all plates** checkbox sits above the picker: tick it to slice every plate into one multi-plate output (sends `plate=0`) instead of a single picked plate.

**Re-slicing for a different printer** — you can slice a 3MF that was built for another printer model. Pick any printer profile and the slicer re-slices for that target (bed, kinematics, nozzle count and start-gcode all come from the chosen profile). When the target crosses a nozzle class (single-nozzle ↔ dual-nozzle H2D/H2C/X2D), BamDude forwards the slicer's `--arrange` so BambuStudio repositions objects for the target bed and reconciles the embedded project settings; a cross-class "slice all plates" run slices each plate independently and merges them. If the slicer still can't produce a valid result, its reason is shown in a dismissible dialog rather than a vanishing toast.


### Slice as designed (keep the file's embedded settings)

Normally the slice applies your picked **Printer / Process / Filament** presets,
which *override* whatever the file's author baked into its embedded
`project_settings.config`. That override is what makes re-slicing for a different
printer work — but it also means a [MakerWorld](makerworld.md) model set up for,
say, five walls comes out at your process preset's default of two.

When the source 3MF carries embedded settings **and** the printer you've picked
matches the printer the file was designed for, the modal shows a **Use the file's
built-in settings** checkbox. Tick it and BamDude slices with no preset override,
so the designer's own wall count, infill, filament and other process settings
drive the result.

- **The preset dropdowns and the bed-type picker grey out** — printer, process,
  filament and bed type. They're bypassed on this path, so they're locked to make
  that obvious (and so changing the printer can't silently pull you off the
  design and hide the checkbox).
- **Filament comes from the file too**, not your AMS picks. If the file's
  filaments don't match what's loaded, map them on the printer, or leave the
  checkbox off and pick your own.
- **It's offered only when your printer matches the design's target model.**
  Honouring embedded settings for a *different* model would place the object on
  the wrong bed — that's exactly what the preset path is for — so the checkbox
  simply isn't shown when the printer differs.

!!! note "This is not a settings merge"
    It's all-or-nothing: you get the designer's complete profile, or you get
    yours. Keeping the author's walls while swapping in *your* filament isn't
    supported — leave the checkbox off and re-create the tweak in your own
    process preset if you need that combination.

#### Filament slots your plate doesn't use

In a multi-plate project each plate usually paints with only some of the
project's filament slots. The slice dialog labels the others **"— not used by
this plate"** and greys out their dropdowns — but the slicer still wants a
profile for every slot, and it validates all of them.

So before slicing a single plate, BamDude replaces every unused slot's profile
with the one from the plate's **lowest used slot**. That keeps the slot count
(and the file's per-slot references) intact while making the loaded set both
materially homogeneous and scoped to the target printer, so neither validator
fires on a slot the G-code never touches:

- *"the temperature difference of the filaments used is too large"* — an ABS
  default sitting next to the PLA the plate actually prints with.
- *"filament preset (slot N) is not compatible with printer …"* — a profile saved
  for another printer (e.g. an `@Bambu Lab H2D` filament baked into the source
  file) sitting in a slot your plate ignores.

Slicing **all plates** skips this: across the whole project every defined slot is
used by some plate, so each one's profile is honoured as picked.

### Reachability indicators

Sidecar health surfaces in three places, sharing one React Query cache + the `GET /api/v1/slicer/health/{slicer}` endpoint (30 s in-process cache):

- **Settings → Profiles → Slicer API** — small inline status next to each URL field (green check + version, or red X with error).
- **Slice modal** — the picker cards each carry a live health badge (see above).
- **System page → Slicer Sidecars** section — version + reachability + URL for each sidecar (auto-refresh 30 s alongside the rest of system info).

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
