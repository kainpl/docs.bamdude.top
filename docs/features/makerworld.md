---
title: MakerWorld import
description: Paste a MakerWorld model URL → BamDude downloads the 3MF straight into the library, dedup-aware and provenance-tracked
---

# MakerWorld import

Paste a [MakerWorld](https://makerworld.com/) model URL into BamDude, pick a plate, and the 3MF lands in your local library — no slicer round-trip, no manual download. Each imported file keeps a provenance link back to the original page, the full design metadata (title, author, license, sliced-for printer, compatibility list, materials), and a locally-cached cover image so the UI never re-hotlinks MakerWorld's CDN.

The integration is **paste-driven**, not search-driven: the public `design/search` endpoint returns empty results from server-originated requests, so duplicating MakerWorld's catalog inside BamDude isn't viable. The actual discovery pattern users already follow — Reddit links, YouTube descriptions, shared chats — fits a paste-first flow cleanly without that limitation.

The MakerWorld page splits into two underline-style tabs:

- **Import** — paste a URL, resolve the design, preview every plate with its compatibility badge and per-variant import state, then click Import on the one (or all) you want.
- **History** — paginated 4-column grid of everything you've already imported, search across filename / title / author, sort by date / title / author, locally-cached cover thumbnails.

The active tab persists in `localStorage`.

---

## :material-cloud-download: How it works

```
You paste MakerWorld URL ─→ BamDude /resolve  ─→  shows plates
        │
        └→ Click Import on a plate ─→ BamDude /import ─→ 3MF in library
```

| Step | What happens |
|------|--------------|
| 1. Paste URL | Accepts any MakerWorld model URL — `/en/models/123-slug?from=search`, `/de/models/123#profileId-456`, scheme-optional. The locale prefix and tracking query are stripped; the `#profileId-N` fragment (if present) selects a specific plate. An inline **Clear** (×) button appears inside the URL input on the right as soon as the field has content or a resolved preview is on screen — one click wipes the URL, the resolved model, and the per-variant import cache. |
| 2. Resolve | Anonymous calls to `api.bambulab.com/v1/design-service/design/{N}` and `…/instances` fetch the design metadata + every published plate. Per-plate printer compatibility (sliced for A1, also marked compatible with H2D / P1S / …) is merged in so the picker can highlight a plate matching your hardware. |
| 3. Pick plate | The resolve response includes a **per-variant** dedupe map (`already_imported_by_profile_id`) — for every plate already in your library it surfaces an **Already imported** badge + a **View in Library** deep-link to the exact row, so you don't pay a redundant download and you can jump straight to the existing file. The legacy whole-model dedupe (URL with no `#profileId-`) lands under the conventional `"0"` bucket. |
| 4. Import | BamDude fetches a signed CDN URL via Bambu Cloud's `iot-service` endpoint, downloads the plate's 3MF (with size cap + SSRF guard), saves it under the library's auto-managed **MakerWorld** folder, downloads the model-level + variant-level cover images locally, captures full design + instance metadata into the `library_file_makerworld_meta` child table, and tags the row with `source_type='makerworld'` + canonical URL. |

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
| **Re-download** | Appears on plates that are already in your library (in place of Save). Re-fetches the 3MF bytes from MakerWorld and **overwrites the existing file in place** at `library_files.file_path`. The `library_file_id` stays stable — queue items, project links, archives, and any other FK references continue to resolve to the same row. `file_size`, `file_hash`, `file_metadata`, the meta-table row (title / author / sliced-for / compatibility / …), and the locally-cached cover images are all refreshed. Use case: the author pushed an update on MakerWorld and you want the fresh bytes without losing your local links. |
| **Delete** | Per-plate trash button on already-imported rows — goes through the standard BamDude confirm modal, removes both the library row and the file on disk. ON DELETE CASCADE drops the meta-table row + cover-image files alongside it. The plate can be re-imported from MakerWorld any time. |
| **View in Library** | Jumps to the library row for the imported plate. Shown both inline on the resolve preview (driven by the per-variant dedupe map) and on every History tab card. |

### :material-import: Import all plates

For multi-plate models, the **Import all** button sequentially downloads every plate of the model in one click. The button shows live progress with the format:

```
Importing 2/5 · Downloading · 12s
```

Plates already in your library are skipped (no redundant download); the counter still advances so you can see progress against the full set.

---

## :material-history: History tab

The **History** tab is a server-paginated 4-column grid (responsive down to 1 column on narrow viewports) of every MakerWorld file you've ever imported. Each card surfaces:

- **Cover image** — the locally-cached variant cover, falling back to the model cover, falling back to the library thumbnail. No hot-linking to MakerWorld's CDN at render time.
- **Title** — the design title captured at import.
- **Author** — name + click-through to the MakerWorld profile.
- **Sliced-for badge** — which printer model the variant was sliced for (A1 / P1S / X1C / H2D / …).
- **Action buttons** — Slice / Open in Bambu Studio / Open in OrcaSlicer / View in Library / Delete.

| Control | Behaviour |
|---|---|
| **Search** | Debounced (300 ms) across `library_files.filename`, `meta.title`, and `meta.author_name` at once — the backend joins `library_files` against `library_file_makerworld_meta` so a single query hits all three fields. |
| **Sort** | `imported_at` (default newest first) / `title` / `author`. Persisted in `localStorage`. |
| **Page size** | `12 / 24 / 48 / 96 / All`. Matches the Archives convention; `All` drops `LIMIT`/`OFFSET` on the SQL side. Persisted in `localStorage`. |
| **Refresh** | The grid auto-refetches after `import` / `delete` / `redownload` mutations via TanStack Query invalidation. |

The legacy `recent-imports` endpoint is still exposed for backwards-compat but the page itself now drives off `/api/v1/makerworld/imports`.

---

## :material-database: Metadata captured per import

Every import writes a 1:1 child row in `library_file_makerworld_meta` (`ON DELETE CASCADE` from `library_files`), capturing the full source-of-truth view that the resolve response surfaces:

| Field | What it holds |
|---|---|
| `title`, `description` | Design title and Markdown/HTML description (sanitised with DOMPurify at render time). |
| `author_name`, `author_url` | MakerWorld user display name + canonical profile URL. |
| `license` | License key as published on the model page (Creative Commons variant, CC BY-SA, etc.). |
| `variant_title`, `variant_description`, `variant_url` | Per-plate name / description / canonical `#profileId-N` URL. |
| `sliced_for` | The printer model the variant was sliced against (e.g. `"P1S"`). |
| `compatible_models` | Full list of compatible printers — used by the resolve UI to highlight a plate matching your hardware. |
| `requires_ams` | Whether the variant is AMS-required. |
| `material_count`, `filaments` | Slot count + per-slot material/colour list as published. |
| `original_design_id` | If the design is a remix, the integer design id of its parent. |
| `makerworld_model_id` | Alphanumeric model id (e.g. `US2bb73b106683e5`) — needed to re-mint download URLs for **Re-download**. |
| `raw_payload` | The combined design + instance JSON, stored verbatim for future-extension forensics — never read by routine code paths. |

Migration **m056** introduces this table; it also best-effort backfills historical imports (rows that exist in `library_files` with `source_type='makerworld'` from before m056). Per-row backfill failures are swallowed (logged) so the migration completes either way — a backfill miss just means the History card falls back to the bare filename until you re-import or Re-download.

---

## :material-camera-image: Cover images

Cover images are **downloaded locally** at import time and served from BamDude, not hot-linked from MakerWorld's CDN. Two flavours per row:

- **Model cover** — the design's hero image. Saved to `<archive_dir>/library/makerworld-covers/<library_file_id>-cover.<ext>`.
- **Variant cover** — the plate-level image (if MakerWorld publishes one separately). Saved to `<archive_dir>/library/makerworld-covers/<library_file_id>-variant.<ext>`.

History-tab cards prefer the variant cover, fall back to the model cover, then fall back to the library file's regular thumbnail. The image endpoints are:

```
GET /api/v1/makerworld/imports/{library_file_id}/cover
GET /api/v1/makerworld/imports/{library_file_id}/cover-variant
```

Both are **public (whitelisted)** rather than permission-gated, because `<img src>` browser fetches can't carry an `Authorization` header. The variant route is named `cover-variant` (not `variant-cover`) so the substring `/cover` matches the auth-middleware whitelist — same mechanism library thumbnails and printer covers already use. The JSON metadata endpoint at `…/meta` keeps its `makerworld:view` permission gate since `fetch()` requests carry the JWT normally.

Re-download refreshes both cover files alongside the 3MF bytes. Deleting a library file CASCADE-drops the meta row, and the cover files are unlinked from disk.

---

## :material-cloud-outline: Legacy thumbnail proxy

For thumbnails on the **Import** tab (the resolve preview shows MakerWorld's hosted gallery images before you click Import), BamDude still exposes an **unauthenticated** thumbnail proxy at `/api/v1/makerworld/thumbnail?url=...` that:

- Server-side fetches the image,
- Restricts the upstream host to the MakerWorld CDN allowlist (`makerworld.bblmw.com`, `public-cdn.bblmw.com`) — not a generic open proxy,
- Returns the bytes with a long `immutable` cache window (filenames are content-hashed).

The proxy endpoint is whitelisted in the always-on auth gate because `<img>` tags can't send `Authorization` headers. Once you click Import, BamDude downloads its own copy of the cover and never proxies the same image again.

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
| `/api/v1/makerworld/resolve` | POST | `makerworld:view` | Resolve URL → design + plate list + flat already-imported IDs + per-variant dedupe map (`already_imported_by_profile_id`). |
| `/api/v1/makerworld/import` | POST | `makerworld:import` | Download a specific plate (`profile_id`) into the library. Writes the meta row + cover images alongside the 3MF. |
| `/api/v1/makerworld/imports` | GET | `makerworld:view` | Server-paginated grid for the History tab. Query params: `page`, `per_page` (12 / 24 / 48 / 96 or `all=true`), `search` (joins library_files + meta), `sort_by` (`imported_at` / `title` / `author`). Returns the standard `{data, meta:{total, current_page, per_page, last_page}}` envelope. |
| `/api/v1/makerworld/imports/{id}/meta` | GET | `makerworld:view` | The captured meta-table row (title / author / license / sliced-for / compatibility / materials / raw_payload). |
| `/api/v1/makerworld/imports/{id}/cover` | GET | public (whitelisted) | Locally-cached model cover image. Whitelisted because `<img src>` can't send auth headers. |
| `/api/v1/makerworld/imports/{id}/cover-variant` | GET | public (whitelisted) | Locally-cached variant cover image. The path is `cover-variant`, not `variant-cover`, so the substring `/cover` matches the same auth whitelist. |
| `/api/v1/makerworld/imports/{id}/redownload` | POST | `makerworld:import` | Re-fetch the 3MF bytes and overwrite the existing file at `library_files.file_path`. Stable `library_file_id`; refreshes `file_size` / `file_hash` / `file_metadata` / meta row / covers. |
| `/api/v1/makerworld/recent-imports` | GET | `makerworld:view` | Legacy: last N MakerWorld library files (default 10, clamped `[1, 50]`). Superseded by `/imports` — kept for backwards-compat. |
| `/api/v1/makerworld/thumbnail` | GET | public (whitelisted) | Proxy MakerWorld / public-cdn for `<img>` rendering on the Import-tab preview — host-allowlisted, no redirects. History-tab cards use the local `/cover` endpoints instead. |

### Upstream flow

The reverse-engineered three-step flow against `api.bambulab.com` (undocumented by Bambu; reverse-engineered via Pr0zak/YASTL#51):

1. `GET https://api.bambulab.com/v1/design-service/design/{designId}` — public metadata. Returns `{id, modelId, title, coverUrl, instances[], …}`. The `modelId` field is the alphanumeric identifier (e.g. `US2bb73b106683e5`) — **different from** the integer `designId` from the URL.
2. `GET https://api.bambulab.com/v1/iot-service/api/user/profile/{profileId}?model_id={modelId}` with `Authorization: Bearer {cloud_token}`. Returns `{url, name}` where `url` is a 5-minute-TTL presigned S3 URL (`s3.<region>.amazonaws.com/...?at=…&exp=…&key=…`).
3. Fetch the presigned URL **without following redirects** and **without re-encoding the query string** — S3 signatures are computed over the exact query bytes, so any normalising HTTP client (httpx default, requests, aiohttp without `raw_path`) breaks them with `SignatureDoesNotMatch`. BamDude uses `urllib.request` with a no-op `HTTPRedirectHandler` for this step.

The older `makerworld.com/api/v1/design-service/instance/{id}/f3mf` path that some reverse-engineering projects document is cookie-gated at Cloudflare and returns "Please log in to download models" regardless of bearer. The `api.bambulab.com` path does not go through that gate.

### Code

- `backend/app/services/makerworld.py` — API client + download logic + thumbnail proxy helpers.
- `backend/app/services/makerworld_meta.py` — `build_meta_dict()` / `download_covers()` / `cleanup_cover_files()` — the m056 meta-table writer + local cover-image fetcher.
- `backend/app/models/library_file_makerworld_meta.py` — SQLAlchemy model for the meta child table (1:1 with `library_files`, `ON DELETE CASCADE`).
- `backend/app/migrations/m056_library_file_makerworld_meta.py` — schema migration + best-effort backfill of historical imports.
- `backend/app/api/routes/makerworld.py` — FastAPI routes.
- `backend/app/schemas/makerworld.py` — Pydantic request/response models (`MakerWorldAlreadyImportedEntry`, `MakerWorldImportsPage`, …).
- `frontend/src/components/MakerWorldImportModal.tsx` + `frontend/src/pages/MakerworldPage.tsx` — UI: Import + History tabs, paste field with inline Clear, preview, plate list with per-variant dedupe badges, image gallery, paginated grid, search, sort, page-size selector.

---

## :material-link-variant: Related

- [File Manager](file-manager.md) — where MakerWorld imports land. The provenance badge column is documented there.
- [Slicer API](slicer-api.md) — pair MakerWorld imports with server-side slicing if a plate isn't pre-sliced for your printer model.
- [Bambu Cloud setup](authentication.md) — required once before the first download.
