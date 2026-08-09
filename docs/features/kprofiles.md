---
title: K-Profiles
description: Per-printer print profiles with dual-nozzle gating, import/export, and Git-backup integration
---

# K-Profiles

K-Profiles are BamDude's representation of slicer-grade print parameters tuned per printer — pressure-advance / linear-advance values, nozzle/bed temps, flow ratios, retraction settings. Profiles travel with your install: backed up over Git on a schedule, exported as a single JSON file when you want to migrate, applied per spool from the inventory page.

This page covers the profile mechanics. For the spool side (assigning a profile override to a specific spool / colour) see [Spool Inventory](inventory.md).

---

## :material-speedometer: What is Pressure Advance?

Pressure advance (also called "K-factor", "linear advance", or just "K") compensates for the lag between the extruder motor pushing filament and the molten plastic actually leaving the nozzle. The wrong K value shows up at every direction change of the print head — corners, perimeter starts, retract→prime points:

- **Too low** — bulged corners, blobby seams, over-extrusion at perimeter starts. The motor keeps pushing while the head is still decelerating.
- **Too high** — gaps at corners, thin lines, weak perimeter joins. The motor backs off too aggressively and the nozzle starves.
- **Just right** — sharp clean corners, consistent line width across the layer, no blobs at line starts.

Different filaments compress differently — softer/wetter materials (PETG, TPU) need higher K than stiff PLA — so you need a separate value per material, sometimes per brand within a material.

## :material-database: Storage model

BamDude keys K-profiles on a **3-tuple composite**: printer × filament × nozzle.

| Dimension | Why it matters |
|-----------|----------------|
| **Printer** | Same filament on different printers may need different K — different extruder geometry, different bowden length, different firmware tuning. |
| **Filament** | PLA needs different K than PETG, TPU, ABS, PA — material compressibility varies by an order of magnitude. |
| **Nozzle** | A 0.2 mm nozzle has a different pressure profile from a 0.6 mm — the K value tracks nozzle diameter, not just material. |

So a 3-printer farm running 4 materials at 2 nozzle sizes ends up with up to `3 × 4 × 2 = 24` distinct profiles. The profile picker filters down to the relevant subset for whatever printer/filament/nozzle you're configuring.

---

## :material-cog: Where profiles live

| Surface | What it does |
|---|---|
| **Profiles** in the sidebar | The profile list. Filter by printer model, search by name, edit, clone, import, export. |
| Spool detail (under Inventory) | "K-profile override" — pick a profile to use whenever this spool is assigned to an AMS slot. Useful for off-spec filaments. |
| Settings → Backup → Git | Schedule profiles + cloud profile snapshots to GitHub / GitLab. |

## :material-content-duplicate: Cloning vs editing

A profile can be in three states:

- **System default** — shipped with BamDude, read-only. Clone to customise.
- **User-owned** — created by you, fully editable.
- **Imported** — pulled in from another install / Git restore. Editable, but the import metadata stays attached so you can tell where it came from.

Cloning a system default produces a user-owned copy with the same parameters; the original system row is untouched. Most BamDude operators end up with one user-owned per `(printer model × material)` pair.

## :material-printer-3d: Dual-nozzle gating

H2D / H2D Pro carry a second nozzle; their profiles need to expose two parallel sets of flow / temperature parameters. BamDude detects dual-nozzle at runtime from MQTT telemetry — specifically, when the printer publishes a `nozzle_2` key in its temperature stream BamDude flips the printer's dual-nozzle flag. There is no serial-prefix lookup table for this; the detection is purely capability-based, so any future Bambu model that publishes a second nozzle key will be picked up automatically. Once detected, BamDude:

- Filters the profile picker to dual-nozzle profiles when the target is a dual-nozzle printer.
- Hides the secondary-nozzle UI block on single-nozzle profiles to reduce noise.
- Refuses to assign a single-nozzle profile to a dual-nozzle printer (and vice versa) — you'll see a clear error in the UI rather than a silent malfunction during print.

## :material-download: Fetch from Printer / :material-upload: Push to Printer

Profiles round-trip with the printer over MQTT. Two directions:

### Fetch from Printer

1. Open **K-Profiles**, select the printer.
2. Click **Fetch from Printer**.
3. BamDude reads the printer's currently-stored K values for every loaded filament and creates / updates the matching profile rows.

Use this after manual on-printer calibration — it pulls the freshly-tuned values straight into BamDude.

### Push to Printer

1. Select the profiles you want to send.
2. Click **Push to Printer**.
3. BamDude writes the K values via MQTT command.

!!! warning "Push overwrites the printer's current K"
    Pushing profiles overwrites the printer's stored K values for the matching filament. If you've been tuning on-printer, **fetch first** to avoid clobbering uncommitted tuning work.

**Saving and deleting wait for the printer's verdict.** They used to be fire-and-forget — BamDude reported success the moment the bytes left the process, and the printer's actual answer was thrown away in a debug log. If the printer says no, you now see **its own reason**.

!!! note "A printer that stays silent is still treated as success"
    No answer is not evidence of refusal.

### Nozzle size on a profile

The printer reports the nozzle size **once**, on the envelope of its reply. On single-nozzle models the individual profile entries carry no size at all, so a profile's size is read from that envelope.

If you run a **0.6 or 0.8 mm nozzle** on a printer older than this release, every profile was listed as 0.4 mm — and it was not only a wrong label:

- Editing a profile is delete-and-re-add on single-nozzle printers, and the dialog rebuilds the nozzle fields from what it was shown — so **saving an untouched 0.6 mm profile stored it back as 0.4**.
- Deleting one aimed the command at the wrong nozzle the same way.
- Assigning a spool's saved calibration to an AMS slot matches on nozzle size, so on a 0.6 or 0.8 nozzle it never found the printer's own entry and **the assignment silently failed to stick**.

The H2D was never affected — its firmware does repeat the size per entry.

### Flow Type (Standard / High Flow)

A K-profile can be **Standard** or **High Flow**, but only some firmware stores the choice; the rest accept it and keep Standard whatever you pick. BamDude follows the same rule Bambu Studio uses for its own calibration window, read from the printer definitions it ships:

| Flow Type field | Models |
|---|---|
| **Shown** | H2 series, X2D, P2S |
| **Hidden** | X1, X1 Carbon, X1E, P1P, P1S |

This is **not** the single- versus dual-nozzle split — the P2S is single-nozzle and does offer both flows.

A profile carrying no flow type at all reads as **Standard**, the way the slicer reads it, rather than the High Flow that used to be assumed on import.

### Sync status indicators

Each profile shows one of three sync states:

| Status | Meaning |
|:------:|---------|
| :material-check-circle:{ style="color: #4caf50" } **Synced** | BamDude's value matches the printer's last known K. |
| :material-sync-alert:{ style="color: #ff9800" } **Modified** | BamDude has local edits that haven't been pushed yet. |
| :material-help-circle:{ style="color: #2196f3" } **New** | Profile created in BamDude, never pushed to this printer. |

After firmware updates or factory resets the printer's stored K may diverge from BamDude's view — re-Fetch to re-establish ground truth.

---

## :material-pencil: Editing K-profiles & value guidelines

Click any profile row to edit. The K-factor field accepts a decimal number; typical starting points per material:

| Material | Typical K range |
|----------|:--------------:|
| PLA | 0.02 – 0.04 |
| PETG | 0.03 – 0.06 |
| ABS / ASA | 0.02 – 0.04 |
| TPU | 0.05 – 0.10 |

!!! note "Starting points, not absolutes"
    These are calibration starting points. Actual optimal K depends on your specific printer, filament brand, nozzle diameter, and even ambient temperature. Always run a calibration pass after picking a starting value — see below.

Add a free-form note per profile (`brand`, `purchase batch`, `tested 2026-04-01`, …) so you remember why a value was set the way it is.

---

## :material-plus-circle: Adding K-profiles

Three ways to create a profile from scratch:

### Manual entry

1. Click **Add K-Profile**.
2. Pick the material, nozzle diameter, and (if multiple) target printer.
3. Enter the K-factor.
4. Save — sync state lands as **New** until you push.

### From calibration result

After running flow / pressure-advance calibration on the printer:

1. Note the optimal K reported by the calibration screen.
2. Either **Fetch from Printer** (if the printer stored the result) or add it manually.
3. The profile is now reusable across slicer round-trips.

### Bundle import

Drop in a previously-exported profile bundle — see **Import & export** below.

---

## :material-ruler: Calibration walkthrough

### Built-in flow calibration (Bambu Lab printers)

Bambu printers ship with a flow / pressure-advance calibration routine:

1. Load the filament you want to calibrate.
2. From the printer's **Calibration** menu (or via Bambu Studio → Calibration → Pressure Advance), run flow calibration.
3. Inspect the test pattern on the build plate — the optimal K is the one that produces the cleanest corners and most consistent extrusion.
4. Note the value, then either **Fetch from Printer** in BamDude (printer-side calibration writes back to the printer's K store) or update the profile manually.

### Third-party methods

If you prefer to calibrate by eye:

- **Pressure-advance line test** — print a series of single-perimeter lines at increasing K. The cleanest line wins.
- **Pressure-advance tower** — vertical tower with K incrementing per layer, measure the layer where corners are sharpest.
- **Corner flow test** — print a test cube and inspect the four corners under raking light.

Whatever method you use, the resulting K value goes into the BamDude profile via **Add K-Profile** or by editing the existing row.

---

## :material-content-copy: Copying profiles between printers

Right-click any profile row → **Copy to printer…**, pick the destination printer. BamDude clones the profile (same K, material, nozzle) onto the new printer with sync status **New**.

!!! tip "Fine-tune after copying"
    Different printers — even of the same model — can have subtly different extruder behaviour. Treat a copied profile as a starting point and re-run calibration on the destination if you want best-quality output.

---

## :material-compare: Comparing values across printers

The K-profiles page has a **Compare** view — pick a material + nozzle and BamDude shows a column-per-printer table of the K values stored for that combination. Use this to:

- Spot one outlier printer that needs re-tuning,
- Decide which printer's profile to use as the canonical "copy from" source,
- Audit drift after firmware updates across the farm.

---

## :material-import: Import & export

Three import paths:

| Source | Notes |
|---|---|
| **Single profile JSON** | The Profiles page accepts an upload of a previously-exported profile. |
| **Bundle import** | Profiles + matching spool-overrides as one ZIP; useful when migrating between installs. |
| **OrcaSlicer preset** | OrcaSlicer ships filament presets that map cleanly onto K-profile parameters. Drop a folder of `.json` Orca filament presets and BamDude imports them in one click. |

Export is the inverse — single profile, full bundle, or "everything modified since X" diff bundle.

## :material-cloud-upload: Git-backup integration

Settings → Backup → Git can push your profile catalogue (plus the BamDude config snapshot) to a GitHub or GitLab repo on a schedule. The repo holds:

- A flat directory of profile JSONs under `kprofiles/` (one file per profile, named by ID).
- A `kprofiles_index.json` listing every profile by hash + name + printer-model so a partial restore is unambiguous.
- The matching spool overrides (`spool_kprofiles/`).
- An audit log entry per scheduled commit.

Restore from Git is partial-by-default: you can pick specific profiles to pull back, or "everything since the last backup". The Git history itself is your version archive — every commit is a profile catalogue snapshot you can roll back to.

## :material-account-multiple: Permissions

| Permission | Effect |
|---|---|
| `kprofiles:read` | View profile list, see settings. Default for Viewers. |
| `kprofiles:create` | Make new profiles or clone existing ones. |
| `kprofiles:update` | Edit user-owned / imported profiles. |
| `kprofiles:delete` | Remove user-owned profiles (system defaults can never be deleted). |

Spool overrides (`spool_kprofile`) are governed by `inventory:update` — same surface as editing a spool.

---

## :material-cog-refresh: RFID re-tap and live calibration preservation

When an AMS slot reads a Bambu RFID tag and the matching spool has a K-profile registered for the **same printer + nozzle diameter**, BamDude pushes that profile's calibration index to the slot. So any time you re-insert a calibrated spool, the slot snaps back to the correct K immediately — you don't have to re-pick it from the printer screen.

If the spool has **no stored K-profile** for that specific printer + nozzle combo (you've calibrated this filament on Printer A but just inserted it into Printer B for the first time, or you've changed the nozzle and haven't re-calibrated yet), BamDude preserves the slot's **currently-selected calibration** instead of letting the firmware silently snap it to slot 0. The exact behaviour:

- The slot's live `cali_idx` (whatever profile was already loaded — manually picked from the printer screen, or carried over from the previous spool in the same slot) is re-issued to the AMS so it sticks.
- If the slot has no calibration loaded at all (`cali_idx < 0`), no command is sent — the firmware default behaviour stands.
- A diagnostic log line records `No stored K-profile for spool … — preserved live cali_idx=N` so the choice is observable in Settings → System → Diagnostics.

Why this matters: prior versions left the slot un-touched on re-tap when no stored profile existed, which on some firmware revisions produced a silent regression to slot 0 that operators only noticed mid-print as a quality drop. The new behaviour is a strict no-op for slots that already have your manually-picked calibration, but a corrective re-issue for the rare slots that would have regressed.

---

## :material-alert: Troubleshooting

**Fetch from Printer fails**

- Verify the printer is online and BamDude shows a green status dot.
- Make sure the printer isn't mid-print or actively running its own calibration — MQTT commands can be queued behind the active operation.
- Check the printer's MQTT logs (Settings → System → Diagnostics) — fetch is a regular MQTT command and surfaces the same way as any other.

**Push to Printer fails**

- Confirm the printer is idle. Some firmware versions reject K-write commands while a job is loaded but not yet started.
- Try a known-good profile to rule out a malformed K value (BamDude clamps to sensible ranges, but a manually-imported bundle could theoretically contain garbage).
- After firmware updates, the printer may temporarily reject commands until its first reboot completes — wait, retry.

**Pushed values don't seem to apply during printing**

- Re-slice the model after the push — slicer-embedded K values can override printer-side K depending on slicer/firmware version.
- Verify the material name in your slicer matches the profile's material — BamDude maps profiles to materials by name, so a mismatch silently bypasses the profile.
- Some firmware versions need a printer reboot before K-write takes effect.
