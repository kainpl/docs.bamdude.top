---
title: Firmware Updates
description: LAN-only Bambu Lab firmware updates via SD card — version detection, download, FTP upload, rollback, no Bambu Cloud required
---

# Firmware Updates

BamDude can keep your Bambu Lab printers patched without a Bambu Cloud account. The flow is **LAN-only**: BamDude pulls the latest firmware from Bambu's official CDN, drops the `.bin` onto the printer's SD card via FTP, and you trigger the install from the printer's screen. No cloud sign-in is required for any of this.

The same machinery also supports **rollback** — pick any version Bambu has ever published, and BamDude will fetch and stage it the same way.

---

## :material-update: What it covers

- Per-printer **firmware status badge** on each printer card.
- "Update available" notifications wired into the standard channels (see [Notifications](notifications.md)).
- LAN-only **download → SD upload → trigger from printer screen** flow.
- **Mass / bulk updates** across many printers at once, grouped per model, with a per-run **Update log** (see [below](#mass-bulk-updates)).
- Rollback / reinstall to any **published** version.
- Wiki-vs-download-page reconciliation — versions that Bambu *announced* but never *published* an offline file for are marked unavailable instead of pretending they're installable.
- **Cloudflare bypass** so the EU/UA installs that get 403'd on plain HTTP can still talk to `bambulab.com`.

What it deliberately doesn't cover: the **Bambu Cloud firmware-update flow** (`/api/v1/cloud/firmware-updates`) — that's a separate route that requires cloud auth and reads firmware availability via the Cloud API. Use the LAN flow for LAN-only printers; use the cloud flow when you're already signed in via [Cloud Profiles](cloud-profiles.md).

---

## :material-bell-badge: Status badge

Each printer card carries a firmware badge. The colour and icon tell you the state at a glance:

| Badge | Meaning |
|---|---|
| **Green / checkmark** | Installed firmware matches the latest published version. Click to read the release notes. |
| **Orange / download** | An update is published. Hover for `current → latest`. Click to open the update modal. |
| **Yellow / question mark** | Version unknown — printer is offline or hasn't sent its firmware over MQTT yet. |
| **Grey** | Firmware checking is disabled (see [Disabling checks](#disabling-checks) below). |

The badge text is the **installed** version (e.g. `01.09.00.00`), pulled from the printer's MQTT state — there's no FTP poll, no cloud round-trip, the badge is free.

The badge is gated by the `firmware:read` permission. Default groups grant it to **Administrators** and **Operators**; **Viewers** don't see it.

### Disabling checks

**Settings → General → Updates → Check printer firmware.** When off:

- No requests go to `bambulab.com` or `wiki.bambulab.com`.
- The badge disappears from every printer card.
- Notifications about new firmware stop firing.

Useful for offline-only deployments, deployments behind strict outbound firewalls, or when you just want to manage firmware manually without seeing the orange dot.

---

## :material-download: Update flow

The flow is the same for forward upgrades and rollbacks — only the version you pick differs.

```
Click badge → Update modal → Pick version → Prepare → Upload → Trigger from printer screen
```

### 1. Open the modal

Click the badge on the printer card. Three sections render:

| Section | What it shows |
|---|---|
| **Current** | Installed version pulled from MQTT |
| **Latest / Selected** | The version that will be installed once you click Upload — defaults to the newest published |
| **Available Versions** | Every version Bambu ever announced for this model |

### 2. Pick a version (optional)

The Available Versions list carries two badges per row:

| Version relation badge | Meaning |
|---|---|
| `newer` | Higher than installed |
| `current` | Currently installed |
| `older` | Lower than installed (rollback territory) |

| File-status badge | Meaning |
|---|---|
| :material-check-circle: **Usable** (green) | Bambu published an offline `.bin` for this version. Selectable, installable. |
| :material-cancel: **Unavailable** (grey) | Bambu announced this version but didn't publish a download. Typical for hot-fix point releases (`01.01.03.00` etc.) — they were cloud-OTA only. Cannot be installed via LAN. |
| :material-information: **Installed** (blue) | The version currently on the printer. |

Clicking a **Usable** row picks it as the install target — release notes and the `firmware_filename` update accordingly. **Unavailable** rows can't be selected.

### 3. Prepare

Before upload, BamDude runs the prepare check (`GET /firmware/updates/{printer_id}/prepare?version=...`):

| Check | Source |
|---|---|
| **SD card present** | MQTT state (`state.sdcard`) |
| **Free space** | Live FTP `STAT` (real bytes, not estimate) |
| **Update available** | Wiki vs installed-version comparison |
| **Target version is publishable** | Download page lookup |

The minimum free-space buffer is **100 MB** on top of the firmware size. A typical Bambu firmware is 50-150 MB; the prepare check estimates 100 MB and refuses if the SD card has less than ~200 MB free.

### 4. Upload

`POST /firmware/updates/{printer_id}/upload?version=...` kicks off a background task that:

1. Downloads the `.bin` from Bambu's CDN (or reuses the local store — see [Store](#firmware-store) below).
2. FTPs the file to the **root** of the printer's SD card. Filename matches Bambu's published naming.
3. Broadcasts progress via WebSocket (`firmware_upload_progress`) and a polling-fallback endpoint (`GET /firmware/updates/{printer_id}/upload/status`).

The whole thing typically takes 2-5 minutes for ~300 MB on local Wi-Fi. Progress is real bytes transferred, not a fake animation.

### 5. Trigger from the printer's screen

BamDude doesn't push the install over MQTT — you finish the job from the printer:

1. **Settings** → **Firmware** on the printer screen.
2. **Update from SD card**.
3. Wait 10-20 minutes. Don't power-cycle until it's done.

!!! warning "Don't power off mid-update"
    A half-applied firmware can brick the printer. Plug the printer into a UPS for the duration if you're somewhere with iffy power.

---

## :material-layers-triple: Mass (bulk) updates {#mass-bulk-updates}

Updating one printer at a time gets old on a farm. The **Firmware** page (sidebar → :material-cpu-64-bit: **Firmware**) updates many printers in one pass.

```
Sidebar → Firmware → pick a version per model → Upgrade
```

- **Grouped by model.** Printers split into per-model tabs (`P1P/P1S (4)`, `A1 mini (2)`, …) — the firmware file and the on-screen apply step differ per model.
- **One version per model, either direction.** Pick the version for each model — newer **or** older (rollback is first-class). The list shows every published version plus any you already hold in the store.
- **Download once, push in parallel.** Each model's firmware is downloaded **once**, then FTP'd to every selected printer's SD card concurrently, capped by **Settings → General → File Manager → bulk concurrency** (default **2** — Bambu controllers don't love many simultaneous TLS handshakes).
- **Mid-print printers are skipped**, flagged on their row, never touched. A failure on one printer **doesn't stop the rest** — every printer gets its own result.
- **"Update all available"** preselects every printer with a pending update; you still confirm the per-model version before launching.
- As with the single-printer flow, the final **apply** is a step on each printer's own screen — the run finishes by showing the model-specific instruction for the printers it uploaded to.

### Update log

The Firmware page's **Update log** tab records every run — timestamp, source (`bulk` vs `single`), per-printer `from → to` version and result. **Single-printer updates from the per-printer modal are logged here too**, so the journal is the one place to see all firmware activity across the farm.

---

## :material-history: Rollback

Selecting an older **Usable** version enables the install button for that build. The downloaded `.bin` goes to SD root same as a forward upgrade — the printer doesn't care which direction the version moves; the firmware loader on the printer accepts any signed Bambu firmware regardless of version comparison.

This means you can pin a printer to an older firmware without hand-flashing — useful when:

- A new firmware breaks compatibility with older slicer 3MFs you depend on.
- A new firmware introduces a regression with your AMS / TPU workflow.
- You want to A/B-test a behaviour change between two versions.

Rollback isn't gated separately — `firmware:update` covers both directions.

---

## :material-shield-bug: Cloudflare bypass

`bambulab.com` sits behind Cloudflare with TLS-fingerprint filtering. Plain `httpx` from EU/UA installs gets a consistent **403 Forbidden** because the JA3 fingerprint of Python's TLS handshake matches Cloudflare's "automated traffic" rule.

BamDude works around this with two HTTP clients in `firmware_check.py`:

| Host | Client | Why |
|---|---|---|
| `wiki.bambulab.com` | `httpx` (plain) | Wiki is *not* behind the same block — version listing reads cleanly |
| `bambulab.com` (Next.js download page + data endpoint) | `curl_cffi` with `impersonate="chrome120"` | Sends a real Chrome TLS handshake → 200 OK |
| Bambu firmware CDN | `httpx` (plain) | CDN is on a different host without the JA3 filter |

### buildId self-heal

The download page is a Next.js app — every page render carries a build-specific `buildId` baked into the data-endpoint path (`/_next/data/<buildId>/...`). Cloudflare rotates this `buildId` on its own schedule, often **inside our 1-hour cache TTL**.

A stale `buildId` returns 403 (Cloudflare challenge) or 404 (path moved). BamDude detects either and runs **one** retry that:

1. Re-fetches the download page via the CF-impersonating client.
2. Greps the fresh `buildId` out of the page HTML.
3. Replays the original data-endpoint call with the new path.

If the retry also fails, the row is marked unavailable for that fetch and the cache stays unwritten — next attempt starts fresh. The user-visible effect: the UI doesn't get stuck reporting "unavailable" on a new release just because Cloudflare rotated `buildId` 12 minutes after BamDude's last fetch.

---

## :material-format-letter-matches: Wiki anchor parsing

Versions are detected from the Bambu Wiki's "Firmware release history" pages (`wiki.bambulab.com/<model>/manual/<model>-firmware-release-history`). The parser pulls section-heading anchor IDs:

| Format | Example | Models |
|---|---|---|
| Dashed | `id="h-01030000-20260303"` | X1 / X1C / X1E / P1 / A1 / A1-mini / H2D / H2C / H2S / X2D |
| Undashed | `id="h-0102000020260409"` | P2S, X2D variants |

A fallback heuristic also scans heading text for the pattern `XX.XX.XX.XX (YYYYMMDD)`, accepting both ASCII parens `()` and **full-width parens `（）`** (U+FF08/U+FF09) — the latter shows up on the A1 / A1-mini / P2S pages because Bambu's wiki editor sometimes injects CJK punctuation.

If you see "0 versions detected" on a model right after a wiki layout change, this regex is the place to look.

---

## :material-folder-arrow-down: Firmware store {#firmware-store}

Downloaded firmware is kept in a durable, **indexed** local store under `<DATA_DIR>/firmware/`, keyed by **model + version** (with a sha256 checksum). It's reused across printers and re-uploads — and, crucially, it's **keyed by model+version rather than the download URL**, so a version stays installable **even after Bambu removes it from their site**.

| When the store helps | Detail |
|---|---|
| Same-model bulk update | Five A1 minis on the same firmware → one CDN download, five FTP uploads |
| Failed upload retry | Re-running the upload reuses the already-downloaded file (sha256-verified) |
| Rollback after a botched upgrade | The previous firmware is probably still in the store |
| Vendor pulled the version | A version Bambu has since removed is still installable from the store |

- **Pre-download without touching a printer.** On the Firmware page you can download any version into the store ahead of time (so you have it before it's ever needed, or before the vendor drops it).
- **In-store indicators.** The version picker shows at a glance which versions are already in the store vs. not.
- The store has no TTL — files live until you delete them. Each `.bin` is 50-150 MB; the store grows ~1 GB over the lifetime of a busy install.

---

## :material-shield-key: Permissions

| Permission | Grants |
|---|---|
| `firmware:read` | Read installed version, list available versions, badge rendering, prepare check |
| `firmware:update` | Trigger the actual upload to the printer's SD card |

Default groups: **Administrators** get both, **Operators** get both, **Viewers** don't get either (they wouldn't be able to act on the badge anyway).

---

## :material-printer-3d: Supported models

Every Bambu Lab printer the wiki publishes a release-history page for is supported, along with their SSDP-reported model codes (so the parser works whether you stored the friendly name `A1 Mini` or the raw code `N1` in the printer record):

| Series | Models | Wiki path key |
|---|---|---|
| X1 | X1, X1C, X1 Carbon, X1E | `x1`, `x1e` |
| P1 | P1P, P1S | `p1` |
| P2 | P2S | `p2s` |
| A1 | A1, A1 Mini | `a1`, `a1-mini` |
| H2 | H2D, H2D Pro, H2C, H2S | `h2d`, `h2d-pro`, `h2c`, `h2s` |
| X2 | X2D | `x2d` |

If your printer reports an SSDP model code that isn't in `MODEL_TO_API_KEY`, the firmware check returns `Unknown model` — open an issue with the raw `DevModel` header from your printer and we'll add the mapping.

---

## :material-help-circle: Troubleshooting

??? question "Badge stuck on `Version unknown`"
    The printer hasn't sent its `firmware_version` over MQTT yet. Wait 30-60 seconds after the printer comes online, or refresh the printer card. If it stays unknown, the printer's MQTT report is missing the field — the firmware check service will treat it as "no current version" and offer the latest as an upgrade candidate.

??? question "`Update failed` toast — no SD card"
    Insert an SD card and retry. The SD-card check is non-cached — the next prepare-call sees the new state.

??? question "`Insufficient SD card space`"
    Bambu firmware needs ~100 MB plus a 100 MB safety buffer. The error message includes the actual numbers — typically caused by leftover gcode files. Clear them via the printer's screen or via [File Manager](file-manager.md), then retry.

??? question "`Cloudflare 403` in the logs"
    Either `curl_cffi` is too old to impersonate Chrome's current TLS fingerprint (rare — chrome120 has been stable a long time) or the CF impersonation profile finally aged out and Cloudflare bumped its filter. Upgrade to the latest BamDude release; the impersonation profile rolls forward with each release.

??? question "`buildId` errors filling the logs"
    Bambu rotated the Next.js `buildId`. The self-heal retry will resolve it transparently — these log lines are informational, not actionable. If the retry *also* fails, the wiki version is still detected from `wiki.bambulab.com`; only the file-availability marker on the row will read `Unavailable`.

??? question "Firmware version on the wiki but `Unavailable` badge"
    Bambu announced the version (wiki listing) but hasn't published an offline `.bin` (download page). Common for hot-fix releases pushed only to cloud-connected printers. There's nothing for BamDude to download — wait for Bambu to publish, or accept the version as cloud-only.

??? question "Upload stuck at 0%"
    Either FTP isn't reachable (wrong access code, wrong IP, firewall) or the file size is so big that the first byte hasn't transferred yet. Tail `bamdude` logs for the FTP connect line. If the connect succeeds and the upload still doesn't progress, your network is throttling — try the upload again on Ethernet rather than 2.4 GHz Wi-Fi.

??? question "Update completes on BamDude side but the printer doesn't see it"
    The `.bin` must be in the **root** of the SD card with its original filename. BamDude uploads to `/`, so this should always be right — but if you've manually moved files around on the SD card, the printer might be looking elsewhere. Pop the card, confirm the file is in root, reinsert, and retry **Update from SD card** on the printer screen.
