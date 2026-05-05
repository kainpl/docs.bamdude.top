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

## :material-cursor-default-click: Per-plate actions

Once a model is resolved, each plate row carries its own action strip:

| Action | What it does |
|--------|--------------|
| **Save** | Downloads the 3MF and files it into the library. The plate row gets a green "Already in library" badge afterwards. |
| **Save & Slice in Bambu Studio** | Same as Save, plus opens the saved file in Bambu Studio if you've configured Slicer Integration. |
| **Save & Slice in OrcaSlicer** | Same as Save, plus opens it in OrcaSlicer. MakerWorld plates are **unsliced source files** so the slicer is the right next step before printing. |
| **Delete** | Per-plate trash button on already-imported rows — goes through the standard BamDude confirm modal, removes both the library row and the file on disk. The plate can be re-imported from MakerWorld any time. |
| **View in File Manager** | Jumps to the library row for the imported plate. |

### :material-import: Import all plates

For multi-plate models, the **Import all** button sequentially downloads every plate of the model in one click. The button shows live progress with the format:

```
Importing 2/5 · Downloading · 12s
```

Plates already in your library are skipped (no redundant download); the counter still advances so you can see progress against the full set.

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

!!! warning "Bambu Cloud token has ~90-day lifetime"
    Bambu Cloud bearers expire after roughly 90 days. If MakerWorld imports suddenly start failing with `401` / "Please log in to download models" after months of working, sign out and back into Bambu Cloud under **Settings → Bambu Cloud** to refresh the token. K-profile fetches and firmware checks would also break — re-auth fixes all three at once.

---

## :material-shield-check: Privacy, security, and compliance

- BamDude is **not affiliated with or endorsed by** MakerWorld or Bambu Lab.
- The integration only uses community-documented endpoints — `api.bambulab.com/v1/design-service/*` for metadata and `api.bambulab.com/v1/iot-service/api/user/profile/{pid}` for the download URL. Credit to **Pr0zak/YASTL#51** for publishing the iot-service endpoint shape that makes the import flow possible.
- Thumbnails and CDN images are proxied through `/api/v1/makerworld/thumbnail` so the user's IP is never exposed to MakerWorld's CDN on page render. The proxy enforces a host allowlist and does **not** follow redirects.
- The MakerWorld description HTML (model summary, instructions) is sanitised with **DOMPurify** before rendering — user-authored content can't inject scripts, event handlers, or `javascript:` URLs.
- The Bambu Cloud bearer is sent **only** to `api.bambulab.com`; it is never forwarded to the MakerWorld CDN or to S3 presigned fetches.
- Filenames returned by MakerWorld responses are sanitised with `os.path.basename` before persistence so a malicious response cannot surface path-traversal strings into the UI. **On-disk storage uses UUID filenames** regardless of the human-readable name shown in the library.

---

## :material-cog-outline: Settings

**Settings → MakerWorld** carries:

- **Status** — `has_cloud_token` / `can_download`. Read-only.
- **Default folder** — defaults to the auto-created top-level `MakerWorld` folder. Override per import via the folder picker on the import button.

There are no other tunables — credentials live in **Settings → Bambu Cloud**, the proxy host allowlist is hard-coded for security.

---

## :material-file-code: Developer reference

### Endpoints

| Endpoint | Method | Auth | Purpose |
|---|---|---|---|
| `/api/v1/makerworld/status` | GET | `makerworld:view` | Report Bambu Cloud token presence and regional host. |
| `/api/v1/makerworld/resolve` | POST | `makerworld:view` | Resolve URL → design + plate list + already-imported profile IDs. |
| `/api/v1/makerworld/import` | POST | `makerworld:import` | Download a specific plate (`profile_id`) into the library. |
| `/api/v1/makerworld/recent-imports` | GET | `makerworld:view` | Last N MakerWorld library files (default 10, clamped `[1, 50]`). |
| `/api/v1/makerworld/thumbnail` | GET | public (whitelisted) | Proxy MakerWorld / public-cdn for `<img>` rendering — host-allowlisted, no redirects. |

### Upstream flow

The reverse-engineered three-step flow against `api.bambulab.com` (undocumented by Bambu; reverse-engineered via Pr0zak/YASTL#51):

1. `GET https://api.bambulab.com/v1/design-service/design/{designId}` — public metadata. Returns `{id, modelId, title, coverUrl, instances[], …}`. The `modelId` field is the alphanumeric identifier (e.g. `US2bb73b106683e5`) — **different from** the integer `designId` from the URL.
2. `GET https://api.bambulab.com/v1/iot-service/api/user/profile/{profileId}?model_id={modelId}` with `Authorization: Bearer {cloud_token}`. Returns `{url, name}` where `url` is a 5-minute-TTL presigned S3 URL (`s3.<region>.amazonaws.com/...?at=…&exp=…&key=…`).
3. Fetch the presigned URL **without following redirects** and **without re-encoding the query string** — S3 signatures are computed over the exact query bytes, so any normalising HTTP client (httpx default, requests, aiohttp without `raw_path`) breaks them with `SignatureDoesNotMatch`. BamDude uses `urllib.request` with a no-op `HTTPRedirectHandler` for this step.

The older `makerworld.com/api/v1/design-service/instance/{id}/f3mf` path that some reverse-engineering projects document is cookie-gated at Cloudflare and returns "Please log in to download models" regardless of bearer. The `api.bambulab.com` path does not go through that gate.

### Code

- `backend/app/services/makerworld.py` — API client + download logic + thumbnail proxy helpers.
- `backend/app/api/routes/makerworld.py` — FastAPI routes.
- `backend/app/schemas/makerworld.py` — Pydantic request/response models.
- `frontend/src/components/MakerWorldImportModal.tsx` + `frontend/src/pages/MakerworldPage.tsx` — UI: paste, preview, plate list, image gallery, recent imports sidebar, confirm modal, in-flight progress labels.

---

## :material-link-variant: Related

- [File Manager](file-manager.md) — where MakerWorld imports land. The provenance badge column is documented there.
- [Slicer API](slicer-api.md) — pair MakerWorld imports with server-side slicing if a plate isn't pre-sliced for your printer model.
- [Bambu Cloud setup](authentication.md) — required once before the first download.
