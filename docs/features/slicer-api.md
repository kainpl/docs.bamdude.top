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

### Publish on one host address

Set `SIDECAR_BIND` in `slicer-api/.env` to choose one host address for both sidecar ports. Unset or empty keeps publication on all interfaces. When BamDude runs on the same machine with host networking, set `SIDECAR_BIND=127.0.0.1` and use the IPv4 loopback address in the sidecar URLs. For a bridged BamDude container or a remote server, use a host address that BamDude can reach. Use brackets with IPv6, for example `SIDECAR_BIND=[::1]`.

### Run with an unprivileged UID

Rebuild the sidecar images before switching to an unprivileged UID. In a local Compose override, set `user: "10001:10001"` and put `HOME: /app/data` under `environment` for each enabled sidecar service. Use your chosen UID and GID in place of 10001. Its mounted data directory and any existing files must be writable by that account. The main Compose recipe keeps the image's default user.

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

### Updating the sidecars { #updating-the-sidecars }

There are two reasons to rebuild the containers, and the second needs no version change:

- **A newer slicer** — change `ORCA_VERSION` / `BAMBU_VERSION`.
- **A newer sidecar** — the HTTP wrapper around the slicer is built together with the container, so it is as old as your last build, whatever BamDude it serves. BamDude asks each sidecar for its code version, and when the running one is older than BamDude needs, the Slice dialog says so under the slicer cards: *"This slicer container is older than this BamDude needs: …"*, with the commands below. Slicing keeps working meanwhile, as far as the older container can: some presets may be missing from the lists, and a preset the slicer cannot resolve is sliced on the slicer's built-in defaults instead of being [refused](#failure-modes).

Either way, rebuild and restart:

```bash
cd slicer-api
docker compose --profile all build --no-cache
docker compose --profile all up -d
```

Substitute `orca` / `bambu` for `all` if you run only one. The `--profile` flag belongs on both commands: without it Compose skips both services, reports success, and the old container keeps serving.

Two traps, both silent:

- **The build context is the sidecar's GitHub repository** (`https://github.com/kainpl/orca-slicer-api.git#bamdude/profile-resolver`), not a folder on your disk. A rebuild fetches the sidecar's code from there; `--no-cache` is what makes Docker fetch it — and the slicer itself — again instead of reusing the layers of the previous build.
- **The slicer version is stated twice** — as the default in `docker-compose.yml` and in `.env` — and `.env` wins. An `.env` copied from an older `.env.example` keeps building the older slicer however new the compose file is; change both.

---

## :material-cog: Settings → Profiles → Slicer API

| Setting | What it does |
|---------|--------------|
| **Preferred slicer** | `OrcaSlicer` or `Bambu Studio`. Default sidecar for server-side (in-app) slicing. The Slice dialog and both [filament calibration](filament-calibration.md#choosing-presets) pages show **Slice with** cards to override it — remembered per source file in the Slice dialog and per printer in calibration (in the browser's localStorage). |
| **Enable server-side slicing** (`use_slicer_api`) | Master toggle. When off, the Slice button disappears from the File Manager — slicing falls back to opening the source in the user's local desktop slicer via URI scheme. |
| **OrcaSlicer API URL** (`orcaslicer_api_url`) | URL of the OrcaSlicer sidecar — e.g. `http://localhost:3003` for the default compose recipe. Empty = use `SLICER_API_URL` env default. |
| **BambuStudio API URL** (`bambu_studio_api_url`) | URL of the BambuStudio sidecar — e.g. `http://localhost:3001`. Empty = use `BAMBU_STUDIO_API_URL` env default. |
| **Slicer stall timeout** (`slicer_stall_timeout_minutes`) | Under **Settings → General → Slicer**. Minutes to keep waiting **with no progress** from the sidecar. Default **15**, range 1–240. See below. |

!!! info "The stall timeout is not a limit on how long a model may take"
    While a slice runs, BamDude asks the sidecar for progress once a second — that
    is what drives the progress toast. **The clock resets on every progress
    update**, so a heavy model that keeps reporting runs to completion however long
    it needs, and only real silence ends the wait.

    On an older sidecar that cannot report progress there is nothing to judge
    liveness by, so the same number bounds **total** slicing time instead.

    A sidecar that won't accept a connection at all is still reported as
    unreachable, immediately.

The desktop **Open in Slicer** button is controlled by a separate, independent setting — **Settings → Slicer → Open in Slicer** — a dropdown that defaults to **Same as API slicer**. Point it at a different slicer to, e.g., slice through the Bambu Studio sidecar but open files locally in OrcaSlicer (or vice versa); existing setups are unchanged until you pick a different value.

The handoff is a link, and the two slicers do not take the same files over one: **Bambu Studio accepts only a 3MF** — it refuses an STL or STEP link before downloading anything — while **OrcaSlicer takes 3MF, STL and STEP**. So the file menu offers Open in Slicer only for a file the configured slicer will take, and the 3D preview opens an STL in OrcaSlicer (naming it on the button) when Bambu Studio is the one configured.

Preset tiers (Imported/Local → Orca Cloud → Bambu Cloud → Standard) are listed automatically by the backend at slice time and don't need a per-install setting — see "Slicing a file" below.

---

## :material-cursor-default-click: Slicing a file

From **File Manager**: action menu on an STL / 3MF / STEP / STP file → **Slice**.

The Slice modal opens with three preset dropdowns:

- **Printer profile** — from the unified preset listing. Each entry is sourced from one of four tiers listed in fixed precedence with **no cross-tier dedup** (`local` → `orca_cloud` → `cloud` → `standard`): `local` (your imported/local `.json` profiles), `orca_cloud` (per-user Orca Cloud presets), `cloud` (per-user Bambu Cloud presets), `standard` (bundled defaults baked into the sidecar). Because there is no dedup, a preset with the same name in two tiers is listed once per tier — it is not hidden just because another tier has one by that name. The dropdown groups its entries by source — see [Preset lists](#preset-lists). Defaults to the printer the source 3MF was prepared with when that profile is available. Otherwise it takes a printer profile with a 0.4 mm nozzle from all the lists — whatever the filters below show — then any other nozzle; a bare model entry such as `Bambu Lab A1`, which states no nozzle, is never picked by itself.
- **Process profile** — same four tiers, but **filtered to the selected printer**: profiles for other printers drop into a trailing **"Other printers"** group instead of disappearing, and profiles with no printer info stay in the main list (never hidden). Defaults to the process the 3MF was prepared with when compatible; otherwise to the compatible one nearest a 0.20 mm layer height (the slicer's own "Standard"), rather than the alphabetically first — which on Bambu's naming was always the finest and slowest. Changing the printer re-picks an automatically picked process that no longer fits; a process you picked yourself [stays](#explicit-choice).
- **Filament profile(s)** — one dropdown per filament slot **the project declares**, not just the ones this plate paints with, filtered the same way (compatible profiles first, "Other printers" group trailing). A slot starts on the filament profile the 3MF project itself names for it, when that profile is in the lists, fits the selected printer and is of the plate's material; when several sources hold a profile of that name, the one from the same source as the chosen printer profile is taken. Otherwise the modal pre-picks the best match per slot using the source 3MF's filament metadata: a profile of the slot's own **base material** (PLA, PETG, ABS… — the type the profile states, not a particular brand or profile family; the PA-CF / PA12-CF / PAHT-CF group counts as one, as it does when printing), an exact type ahead of an equivalent one, colour breaking ties and printer-incompatible profiles demoted. A profile of another material is picked only when there is nothing else — and then one the selected printer can use comes ahead of one made for another printer — and a profile **you** chose — by hand or from a saved pipeline — is never swapped out for its material, so slicing a PLA-labelled model in PETG stays your call. A single click on **Slice** usually does the right thing for multi-color jobs. Beside each dropdown sits a **colour** control — the colour that slot is printed in, written into the sliced file so its thumbnail and the print dialog show it. It starts at the colour the source plate was designed with, or the slicer's default green for a source with none (an STL); set it to the spool you will load. Neither slicer keeps a colour on a filament profile, so without it every sliced file came back Bambu green. It is a record, not a requirement: the print dialog still maps the slot to a spool of any colour.

    !!! warning "Why every declared slot is listed, even the unused ones"
        The slicer binds this list **by position**. Take a model that declares four
        filaments but paints with slot 4 alone — a common MakerWorld shape. With
        a single dropdown, your pick would land in **slot 1**; slot 4, the
        one the model actually prints with, would be sliced with whatever the author
        had left in it, and the print would come out in the wrong material with nothing
        on screen to suggest anything was off.

        Slots this plate doesn't use are shown greyed out (see below), so choosing
        a filament for slot 4 sets slot 4.

    The **Print** dialog is deliberately different: it asks which spools the job
    needs, and it needs the narrow answer — otherwise it would have you load three
    spools the print never touches.

The modal caches the cloud and standard preset listings for a few minutes, so if you delete or rename a preset in Bambu Studio / Bambu Handy it can take a while to disappear from the dropdowns. A **Refresh** control on the preset list fetches the latest listings immediately. Importing or deleting a local profile in **Settings** also refreshes the slice dialog's presets right away.

Compatibility is decided by the profile's own `compatible_printers` list when present, then by the `@<printer>` naming convention — in all three shapes the slicer writes: `@BBL <model>`, the full `@Bambu Lab <model> <size> nozzle` form a user-saved preset gets, and a bare `@<size>` tag. A bare size can rule a printer *out* but is never taken as proof of a match, and sizes are compared numerically so `0.20` and `0.2` are the same. Orca Cloud profiles carry their own compatible-printer list, and a copy of a profile that knows its printers shares that list with copies that don't — which is what stops a profile whose name carries no model (`Overture PLA Matte @0.2`) being auto-picked for a printer it was never built for. Built-in (standard) profiles carry the slicer's own compatible-printer list too, as long as the slicer sidecar is recent enough to report it — which is what gives a P1S, an X1, an X1E or an H2D Pro its processes, since the slicer ships none named after them. A printer filter that would leave a dropdown empty shows the whole list instead, and the field says so: *No profile is known to fit this printer, so every profile is shown.* It is **nozzle-aware**, so a 0.6-nozzle process won't show as compatible for a 0.4-nozzle printer (0.4 is the implicit default that drops the suffix). The same matcher drives the **filament-calibration** wizard's profile picker; there incompatible profiles are hidden outright rather than grouped, since a calibration print sent to the wrong printer just wastes a bed, and the page that prints asks more of a printer profile than a match — see [Choosing the slicer, the plate and the presets](filament-calibration.md#choosing-presets).

A **slicer picker** sits at the top of the Slice modal — two card-buttons (mirroring the "Filament Tracking" pattern in Settings) with their own live health badges. Auto-locks to the only-healthy sidecar when one is down; you pick freely when both are reachable; offline cards are disabled. First-time default is the global *Preferred slicer* setting; subsequent opens of the same source file default to your last pick (per-file localStorage). Only a pick you make on a card is remembered: the slicer the dialog falls back to while one sidecar is down is not.

For multi-plate 3MFs the modal embeds an **inline plate selector** at the top of its body, mirroring the Print modal's plate picker — a vertical paginator + details card. Plate 1 auto-selects on load so the filament-requirements + presets queries flow without blocking on user interaction; clicking a different plate re-keys those queries. A **Slice all plates** checkbox sits above the picker: tick it to slice every plate into one multi-plate output (sends `plate=0`) instead of a single picked plate.

**Re-slicing for a different printer** — you can slice a 3MF that was built for another printer model. Pick any printer profile and the slicer re-slices for that target (bed, kinematics, nozzle count and start-gcode all come from the chosen profile). When the target crosses a nozzle class (single-nozzle ↔ dual-nozzle H2D/H2C/X2D), BamDude forwards the slicer's `--arrange` so BambuStudio repositions objects for the target bed and reconciles the embedded project settings; a cross-class "slice all plates" run slices each plate independently and merges them. If the slicer still can't produce a valid result, its reason is shown in a dismissible dialog rather than a vanishing toast.


### Preset lists: groups, order and search { #preset-lists }

Each preset dropdown is grouped by **source**, your own first:

1. **Imported** — the profiles imported into BamDude ([Local Profiles](local-profiles.md)).
2. **Orca Cloud** — your [Orca Cloud](orca-cloud.md) profiles.
3. **Bambu Cloud — my presets** — the presets you saved in your [Bambu Cloud](cloud-profiles.md) account.
4. **Bambu Cloud** — Bambu's stock presets, as your account lists them.
5. **Standard** — the presets bundled with the slicer in the sidecar.

A group with nothing in it is not shown. In a process or filament field, profiles made for another printer than the selected one follow in the trailing **Other printers** group, where each entry names its source after its name.

A name is not an identity. A stock preset that Bambu Cloud and the slicer's bundle both carry under one name is **two entries**, one under **Bambu Cloud** and one under **Standard**: they are different content — the Standard one is the running sidecar's — and neither stands in for the other.

Inside a group the order is Bambu presets, then Generic, then every other brand; in the filament lists the support materials (support, PVA, BVOH, HIPS) come after all the rest. Within that, names are sorted without regard to case and with numbers by value, so `0.08mm` comes before `0.20mm` and `PA6` before `PA12`. A preset cloned in the slicer under its default `# …` name is listed where the preset it copies would be.

A **Preset source** segment above the fields chooses whose profiles the lists show: **All**, **My Presets** or **Built-in**. My presets are the imported ones, your Orca Cloud profiles and the presets you saved in Bambu Cloud; built-in ones are the Standard presets and Bambu's stock cloud presets. The first time it is **My Presets**. The choice is one setting for every place that shows it — this dialog, [filament calibration](filament-calibration.md) and [Assemble project](assemble-project.md) — and is remembered in this browser. Changing it picks the dialog's own process and filament choices again; the ones you made stay. When it hides every fitting profile of a field, the field shows the built-in ones too and says so: *No profile of your own fits here, so built-in profiles are shown too.*, with **Show all**, which sets the segment to **All**.

The magnifier button beside a list opens a search box (**Search presets…**). The words you type narrow that list: every word has to occur in the entry, in any order and any case. The chosen preset always stays listed. **Enter** takes the first match, **↓** moves into the narrowed list, and **Esc** closes the search without closing the dialog. A query nothing matches says **No matching presets.**

### A profile you pick stays picked { #explicit-choice }

The dialog makes automatic picks, and it replaces only its own. A process or filament profile **you** choose — from the list, or by applying [saved settings](slicer-pipelines.md) — is an explicit choice, and no automatic pass replaces it: not **Refresh**, not another plate of the project, not **Slice all plates**, not a change of printer, and not the material check that re-picks an automatic filament pick.

- **A chosen profile made for another printer stays.** It sits in the **Other printers** group, and the field says so underneath: *"This profile is listed for another printer than the selected one."* Automatic picks follow the printer; yours wait for you.
- **A chosen profile that is no longer in the lists** — deleted, or gone after a refresh — is replaced by an automatic pick, and a banner names the fields to look at: *"A profile you chose is no longer in the list, so another one was selected. Check: …"*.
- **A printer profile that is no longer in the lists is not replaced**, whoever chose it. The field says *The chosen profile is no longer in the list. Choose one to continue.*, and **Slice** and saving the settings wait until you choose a printer profile — also when the same profile comes back on a later **Refresh**.
- **Applying saved settings** is the one action besides your own pick that replaces a choice, and it says what it did: *"Applied "name". Changed: Printer profile, Process profile"* — or *"Applied "name". Nothing changed — these were already the selection."*

### Only models of my farm, only loaded filaments { #farm-filters }

Two switches above the preset fields narrow the lists to what the farm can print. Both are off by default and remembered per browser.

| Switch | Narrows | To |
|---|---|---|
| **Only models of my farm** | **Printer profile** | Profiles of the printer models of your farm — every printer that is not archived, online or not, paused or in maintenance, and of the models whose files Bambu Studio lets that printer print (a P1S also takes P1P and X1-series profiles) — and of a nozzle size fitted on one of them, when the profile states a size. A printer whose nozzles are not known rules out no size. |
| **Only filaments that are loaded** | Every filament field | Profiles of the filaments loaded on the online printers. Once a printer profile is chosen, only the online printers of that model count. |

- **Online**, for the loaded filaments, means connected, active and not archived.
- **Loaded** means the spool assigned to a slot — its own filament profile, not what the slot shows the printer. A slot advertised as a Generic profile for [AMS Backup](ams.md) counts as the filament that is really in it. A spool without a filament profile of its own is matched by material: every profile of that material counts. External spool holders count; an empty slot does not.
- **The lists follow the farm while the dialog is open**: a printer connecting or disconnecting, a spool assigned or unassigned.
- **A filter narrows what a list offers and nothing else.** The profile you chose stays chosen and stays listed even when the filter would hide it, and a filter never changes a profile you picked by hand. The automatic picks follow the source and the loaded filament: a process or filament field the dialog fills by itself takes a profile those filters offer — of the source you chose, and loaded while **Only filaments that are loaded** is on — when one suits the plate's material and the printer, and the usual pick otherwise. **Only models of my farm** changes no pick, and the printer's own automatic pick ignores every filter.

When a filter would leave a field with nothing that fits, the field does not stay empty: it sets that filter aside for itself, shows what is left, and says which filter it set aside, with **Show all**, which switches that filter off for good. The farm switch is set aside first, then the source:

| Field | Message |
|---|---|
| Printer profile | *No profile of a printer model in your farm fits here, so every printer profile is shown.* |
| Filament profiles | *No profile of a loaded filament fits here, so every filament profile is shown.* |
| Any field | *No profile of your own fits here, so built-in profiles are shown too.* |

The switches need the right to view printers (`printers:read`) and are not shown without it. When the printers cannot be read, nothing is narrowed and the dialog says so — *"The printers could not be read, so every profile is shown."* — with **Retry**. Both switches are answered by one read, `GET /api/v1/slicer/loaded-filaments`; an [API key](api-keys.md) limited to some printers sees only those.

### Bed plate { #bed-plate }

The **Bed plate** picker sets the plate the slice is made for (`--curr-bed-type` on the CLI):

| Plate | Offered with |
|---|---|
| **Cool Plate** | both slicers |
| **Engineering Plate** | both slicers |
| **Smooth PEI / High Temp Plate** | both slicers |
| **Textured PEI Plate** | both slicers |
| **Cool Plate SuperTack** | both slicers |
| **Textured Cool Plate** | OrcaSlicer only |

The default, **Textured PEI Plate**, matches the factory plate on the modern Bambu lineup; A1 / A1-mini owners flip to SuperTack once, and the plate you choose is remembered in the browser. Sliced 3MFs from Bambu Studio still honour their embedded per-plate `bed_type` (BamDude forwards the original bytes) — the override only kicks in for sources without one.

**Textured Cool Plate** exists in OrcaSlicer only, so it is listed while OrcaSlicer is the slicer of this job. When the slicer is Bambu Studio and that plate is the current one, the dialog changes it to the default and says so under the field — *"Textured Cool Plate is available only with OrcaSlicer. The bed plate was changed to Textured PEI Plate."* — and switching back to OrcaSlicer puts it back. A slice request that names it for Bambu Studio is refused (422): *"Textured Cool Plate is available only with OrcaSlicer. Pick another bed plate, or slice with OrcaSlicer."*

The same picker, remembering the same plate, is on both [filament calibration](filament-calibration.md#choosing-presets) pages, and a calibration request that names Textured Cool Plate for Bambu Studio is refused the same way.

### Presets the slicer offers { #standard-presets }

The **Standard** group is the preset set of the slicer inside the sidecar:

- **Presets a brand keeps in a folder of its own** (P1P, Polymaker, SUNLU and others) are listed with the rest.
- **A preset with `/` in its name** (`Bambu Support For PLA/PETG …`) is listed under that name and sliced with its own settings.
- **OrcaSlicer's filament library** — the presets named `… @System` — is offered with OrcaSlicer; Bambu Studio has no such library. A library preset that names its printers (`Polymaker PolyLite PLA @BBL A1`) is offered for those printers. A generic one (`Generic PLA @System`) is offered for a printer only when that printer has **no preset of its own for the same filament** — "the same filament" being the name up to its `@` — so a printer with a `Generic PLA @BBL X1C` is not offered `Generic PLA @System` beside it.
- **A printer preset saved under a name of your own** (`Bambu Lab H2D 0.4 nozzle - Skew`) is the printer it was saved from: its model, nozzle and compatible process and filament profiles are the parent's, and it slices as that printer with your changes. A printer preset cloned in the slicer under its default `# …` name is matched as the preset it copies.

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
    supported — for that, use **The designer's print settings** below, which is
    per-setting and works across printers.

### The designer's print settings (per-setting, across printers)

The middle ground between "your preset" and "slice as designed": pick your own
printer, process and filaments, and carry **only the individual settings the
author changed**.

When the source 3MF declares deviations from its stock profile, the Slice modal
adds a **The designer's print settings** panel listing exactly which process
settings the author changed and what each was set to, with a checkbox per
setting. Only what you tick is applied.

| Group | Examples | Default |
|---|---|:---:|
| **Design intent** | wall count, infill density and pattern, supports, seam position, brim, ironing | :material-check: ticked |
| **Defines the preset** — badged `overrides preset` | layer height, first-layer height | :material-close: unticked |
| **Machine-tuned** — badged `machine-tuned` | speeds, accelerations, jerk, fan speeds, temperatures, prime-tower geometry | :material-close: unticked |

Layer height and first-layer height *are* the process preset you picked — "0.08mm High Quality" is its
layer height — so the file's value is offered, with the preset's own beside it, but never ticked for you:
a file's 0.2 never slices quietly over an explicitly picked 0.08 preset.

Machine-tuned values were chosen for the *author's* printer. On yours they can be
merely wrong, or outside the range your profile accepts — which fails the slice
outright — so they are listed with a badge and left off for you to decide.

**Supports follow the ticks.** A file with supports switched on turns them on
for your slice too — they are design intent, ticked by default. Untick them and
the slice keeps your preset's own support settings; an unticked support setting
is not carried in behind your back. A file that records no deviations at
all (an OrcaSlicer export, say) has nothing to tick, and its supports are
carried as they are.

The same ticks appear beside each option in the **Process settings** panel, and
a tick in either place is the same tick. That panel greys out an option only
when the slice itself would switch it off — judged by your preset's values, the
file's values you ticked and anything you typed, not by the slicer's built-in
defaults, which would grey the whole Support page for a preset with supports
on. A greyed option's "from file" tick can still be cleared.

!!! info "Nothing here is guessed"
    Bambu Studio writes the list of deviations into the 3MF itself
    (`different_settings_to_system` in `Metadata/project_settings.config`).
    BamDude reads that list; it does not diff profiles or infer intent.

    A file whose list doesn't match its own filament count is **ignored rather
    than interpreted** — misreading it would risk carrying the author's machine
    start-up G-code onto your printer.

The panel works when re-slicing for a **different** printer, which is exactly
where "Slice as designed" isn't offered. It also appears when re-printing from an
archive.

When you export a sliced 3MF using Bambu Studio with a built-in or stock Bambu Cloud process, BamDude records the process settings it changed. Bambu Studio uses that list to retain your overrides and selected designer settings when it reopens the project with the system preset.

### Filament slots your plate doesn't use

In a multi-plate project each plate usually paints with only some of the
project's filament slots. The slice dialog labels the others **"— not used by
this plate"** and greys out their dropdowns — but the slicer still wants a
profile for every slot, and it validates all of them.

So before slicing a single plate, BamDude replaces every unused slot's profile
with the one from the plate's **lowest used slot** — the profile only: the slot keeps its own colour in the sliced file. That keeps the slot count
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

### Painted multi-colour models { #painted-models }

A model painted with several filaments in the slicer keeps its colours when sliced here. Which slots a plate prints with is read from the objects' filament assignments **and** from the paint data on their surfaces, and every painted area counts, however small — a colour used on one small detail makes its slot a used one, sliced with the profile picked for it. A slot the plate really does not use keeps its own colour in the sliced file, whatever profile stands in for it.

### Reachability indicators

Sidecar health surfaces in three places, sharing one React Query cache + the `GET /api/v1/slicer/health/{slicer}` endpoint (30 s in-process cache):

- **Settings → Profiles → Slicer API** — small inline status next to each URL field (green check + version, or red X with error).
- **Slice modal** — the picker cards each carry a live health badge (see above), and a note under them when the picked slicer's container is older than BamDude needs — see [Updating the sidecars](#updating-the-sidecars).
- **Information → Slicer Sidecars** section — version + reachability + URL for each sidecar (auto-refresh 30 s alongside the rest of system info).

A persistent toast in the bottom-right tracks the job: live progress percent + elapsed time, replaced by a transient success / error toast on completion. The sliced output lands in the same library folder with `.gcode.3mf` extension and `source_type='sliced'` provenance — the original file is untouched.

---

## :material-shield-key: Permissions

| Permission | Grants |
|------------|--------|
| `library:upload` | Trigger a slice from the File Manager (the sliced output is a fresh library upload). |
| `archives:reprint_own` / `archives:reprint_all` | Slice an archive — beside `library:upload`. Re-slicing makes new print work from the archive, so it asks the right to reprint it: your own prints, or any. An API key cannot re-slice an archive its owner may not see. |
| `library:read` | Poll the job-tracker toast (`/api/v1/slice-jobs/{id}`) and the filament-discovery preview slice progress (`/api/v1/slicer/preview-progress/{id}`). |
| `cloud:auth` | Required to fetch the `cloud` preset tier — without it, the modal shows only `local` + `standard` tiers. |
| `printers:read` | The **Only models of my farm** / **Only filaments that are loaded** switches of the Slice modal — without it they are not shown. |

The Settings → Profiles → Slicer API toggle and URL fields are gated by `settings:update`.

---

## :material-alert-circle-outline: Failure modes { #failure-modes }

- **Sidecar offline** → 502 surfaced as toast, job marked failed; original file untouched. "Could not connect" and "gave up waiting" are reported as **different** things, and the timeout message names the limit that was reached and where to change it.
- **Slice produced nothing** → a reply that is "OK" with a few bytes — a misconfigured slicer service, a reverse proxy returning its own error page, a truncated response, the slicer crashing without writing output — is **rejected before the file is stored**, rather than being saved, queued, and sent to a printer that then does nothing. A slice refused as too large is named for what it is: a size limit on the proxy in front of the slicer, not a fault of the slicer.
- **Profile not found** → 400 names the missing profile so you can add it via [K-Profiles](kprofiles.md) or pick a different tier.
- **A preset the slicer cannot resolve** → a preset is a chain: it inherits from a parent, and the slicer has to find every link. When one is missing the slice is refused and nothing is sliced — never sliced on the slicer's built-in defaults — and the message names the preset and the missing parent: *"The preset 'X' cannot be sliced: its parent preset 'Y' is not among the slicer's profiles, so nothing was sliced. Pick another preset, or rebuild the slicer containers if the parent belongs to a newer slicer version."* For a **Standard** pick that the running slicer does not have: *"The preset 'X' is not among the slicer's profiles, so nothing was sliced. …"* What to do: pick another preset — a stock one of the same printer or filament; for an imported preset whose parent was not fetched at import, re-import it once the parent can be fetched ([Local Profiles](local-profiles.md)); when the parent belongs to a newer slicer, raise the slicer version and [rebuild the containers](#updating-the-sidecars). This refusal does not fall back to the file's embedded settings (below), and it needs a current sidecar.
- **Sidecar rejects the file** (corrupt 3MF, unsupported plate format, malformed preset, etc.) → toast surfaces the sidecar's verbatim CLI stdout/stderr so you don't have to dig in container logs.
- **Embedded-settings fallback** — after a slicer crash with the selected profiles, BamDude can retry a 3MF once using the settings in `Metadata/project_settings.config`. It retries only when the file and the selected printer profile identify the same known printer model. Otherwise the original error is shown. A successful retry marks the result with `used_embedded_settings: true`.
- **Cloud presets unreachable** (token expired / network down) → the modal renders the `cloud` tier with a status banner and falls back to `local` + `standard` only.

---

## :material-link-variant: Related

- [File Manager](file-manager.md) — where the Slice button lives.
- [K-Profiles](kprofiles.md) — how to feed your local OrcaSlicer filament profiles into the `local` tier.
- [MakerWorld import](makerworld.md) — pair imported plates with server-side slicing when no plate matches your printer.
