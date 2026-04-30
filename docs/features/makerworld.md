---
title: MakerWorld import
description: Paste a MakerWorld model URL → BamDude downloads the 3MF straight into the library, dedup-aware and provenance-tracked
---

# MakerWorld import

Paste a [MakerWorld](https://makerworld.com/) model URL into BamDude, pick a plate, and the 3MF lands in your local library — no slicer round-trip, no manual download. Each imported file keeps a provenance link back to the original page so you can jump back any time for ratings, recommended filaments, or alternative plates.

The integration is **paste-driven**, not search-driven: the public `design/search` endpoint returns empty results from server-originated requests, so duplicating MakerWorld's catalog inside BamDude isn't viable. The actual discovery pattern users already follow — Reddit links, YouTube descriptions, shared chats — fits a paste-first flow cleanly without that limitation.

---

## :material-cloud-download: How it works

```
You paste MakerWorld URL ─→ BamDude /resolve  ─→  shows plates
        │
        └→ Click Import on a plate ─→ BamDude /import ─→ 3MF in library
```

| Step | What happens |
|------|--------------|
| 1. Paste URL | Accepts any MakerWorld model URL — `/en/models/123-slug?from=search`, `/de/models/123#profileId-456`, scheme-optional. The locale prefix and tracking query are stripped; the `#profileId-N` fragment (if present) selects a specific plate. |
| 2. Resolve | Anonymous calls to `api.bambulab.com/v1/design-service/design/{N}` and `…/instances` fetch the design metadata + every published plate. Per-plate printer compatibility (sliced for A1, also marked compatible with H2D / P1S / …) is merged in so the picker can highlight a plate matching your hardware. |
| 3. Pick plate | The resolve response surfaces an **Already imported** badge for any plates already in your library, so you don't pay a redundant download. |
| 4. Import | BamDude fetches a signed CDN URL via Bambu Cloud's `iot-service` endpoint, downloads the plate's 3MF (with size cap + SSRF guard), saves it under the library's auto-managed **MakerWorld** folder, and tags the row with `source_type='makerworld'` + canonical URL. |

---

## :material-key: Authentication

BamDude reuses your existing **Bambu Cloud** sign-in for downloads — there's no separate OAuth flow.

- **Anonymous calls** (URL parsing, design metadata, plate enumeration) work without a token.
- **Download calls** (`/iot-service/api/user/profile/{profileId}`) require your stored Bambu Cloud bearer.

If no token is stored, **Settings → MakerWorld → Status** reports `can_download = false` and the Import button is disabled — go to **Settings → Bambu Cloud** to sign in first.

---

## :material-shield-key: Permissions

| Permission | Grants |
|------------|--------|
| `makerworld:view` | Browse the MakerWorld page, paste URLs, see resolved metadata, see Recent imports. |
| `makerworld:import` | Actually trigger a download into the library. |

The default groups grant both to **Operators** and only `makerworld:view` to **Viewers**. Admins get both.

---

## :material-folder-arrow-down: Where files land

| Field | Value |
|-------|-------|
| **Folder** | Top-level `MakerWorld` folder, auto-created on the first import. You can manually move files into sub-folders afterwards — the provenance row stays attached. |
| **Filename** | Server-provided human-readable name from MakerWorld; on-disk storage uses a UUID, so you can rename freely. |
| **`source_type`** | `'makerworld'` — drives the MakerWorld glyph badge in File Manager. |
| **`source_url`** | Canonical `https://makerworld.com/models/{m}#profileId-{p}` — the badge becomes a one-click link back to the page. |
| **Plate-keyed dedup** | Two different plates of the same model = two library entries (each plate is downloaded independently from MakerWorld). The same plate imported a second time returns the existing row instead of re-downloading. |

---

## :material-history: Recent imports

The **MakerWorld** page shows a sidebar of the last 10 imports (newest first), keyed off `source_type='makerworld'`. Useful for quickly re-printing something you imported the day before without retyping the URL.

---

## :material-camera-image: Thumbnails & CSP

MakerWorld's CDN images can't be hot-linked from your browser — BamDude's strict `img-src 'self' data: blob:` Content-Security-Policy blocks cross-origin images. To work around that, BamDude exposes an **unauthenticated** thumbnail proxy at `/api/v1/makerworld/thumbnail?url=...` that:

- Server-side fetches the image,
- Restricts the upstream host to the MakerWorld CDN allowlist (`makerworld.bblmw.com`, `public-cdn.bblmw.com`) — not a generic open proxy,
- Returns the bytes with a long `immutable` cache window (filenames are content-hashed).

The proxy endpoint is whitelisted in the always-on auth gate because `<img>` tags can't send `Authorization` headers.

---

## :material-alert-circle-outline: Limitations

!!! warning "MakerWorld 418 — application-level CAPTCHA"
    MakerWorld occasionally challenges your IP with a CAPTCHA (`HTTP 418` with `{"captchaId":...}`). This is **application-level**, not Cloudflare-edge — there's no server-side solve, since CAPTCHAs are intentionally unsolvable without a real browser. BamDude does one short-backoff retry, then surfaces the upstream message verbatim. Wait 1–4 hours of quiet traffic, or use **Open on MakerWorld** to import manually via your browser.

- **No search/browse UI.** MakerWorld's public `design/search` returns empty results from server-side requests, so BamDude doesn't try to mirror the catalog. Workflow is paste-driven by design.
- **No price/points handling.** Plates that are content-gated (paid, region-locked, points-required) return `HTTP 403` with MakerWorld's own refusal message, surfaced verbatim in the toast.
- **3MF size cap: 200 MB.** Larger plates fail the SSRF-guarded download with a clear error.

---

## :material-cog-outline: Settings

**Settings → MakerWorld** carries:

- **Status** — `has_cloud_token` / `can_download`. Read-only.
- **Default folder** — defaults to the auto-created top-level `MakerWorld` folder. Override per import via the folder picker on the import button.

There are no other tunables — credentials live in **Settings → Bambu Cloud**, the proxy host allowlist is hard-coded for security.

---

## :material-link-variant: Related

- [File Manager](file-manager.md) — where MakerWorld imports land. The provenance badge column is documented there.
- [Slicer API](slicer-api.md) — pair MakerWorld imports with server-side slicing if a plate isn't pre-sliced for your printer model.
- [Bambu Cloud setup](authentication.md) — required once before the first download.
