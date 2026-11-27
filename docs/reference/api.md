---
title: API Reference
description: REST API integration guide for BamDude — auth, permissions, rate limits, endpoint groups, and recipes.
---

# API Reference

BamDude exposes a versioned REST API at `/api/v1` plus a WebSocket channel for realtime printer events. Everything the web UI does is also available to your scripts and integrations.

---

## Workshop API: a product from a file

`POST /api/v1/products/from-file/{id}` returns `{product, notes}`. Read the new product's fields under `product`; `notes` describes what the file supplied. The source must be visible through the caller's library permissions. Orders, Products, Customers and Stock each have their own rights, so a custom group needs the ones for the sections it works in.

## :material-rocket-launch: Quick start

- **Base URL:** `https://<your-bamdude-host>/api/v1`
- **Interactive docs:** [`/docs`](#) (Swagger UI) and [`/redoc`](#) (ReDoc)
- **OpenAPI schema:** `/openapi.json` — drop into Postman, Insomnia, or any OpenAPI-compatible client
- **Realtime channel:** `wss://<your-bamdude-host>/api/v1/ws`

All endpoints return JSON unless explicitly noted (camera streams, 3MF downloads, and thumbnails return binary). Errors follow the FastAPI shape:

```json
{ "detail": "Not authenticated" }
```

`422` validation errors return arrays of field-level issues:

```json
{
  "detail": [
    { "loc": ["body", "name"], "msg": "field required", "type": "value_error.missing" }
  ]
}
```

!!! tip "Use `/docs` first"
    The interactive Swagger UI is generated from the live server, so it always reflects the routes, schemas, and required permissions of the version you're running. Treat this page as orientation; treat `/docs` as ground truth.

---

## :material-key: Authentication methods

BamDude supports two authentication mechanisms. Both enforce the same permission checks. API keys are matched first; if neither header is present, the request falls through to JWT.

=== "API key (recommended for scripts)"

    Generate keys in **Settings → API Keys**. They look like `bd_<random_token>` and never auto-expire — revoke them per-key when no longer needed.

    Send via either header:

    ```bash
    # Preferred: dedicated header
    curl -H "X-API-Key: bd_abc123..." \
      https://bamdude.example.com/api/v1/printers/

    # Equivalent: bearer scheme
    curl -H "Authorization: Bearer bd_abc123..." \
      https://bamdude.example.com/api/v1/printers/
    ```

    Each key carries its own permission set — a subset of the issuing user's permissions. Revoking a user revokes their keys.

=== "JWT session token (used by the web UI)"

    The browser flow:

    ```bash
    curl -X POST -H "Content-Type: application/json" \
      -d '{"username": "admin", "password": "...", "remember_me": true}' \
      https://bamdude.example.com/api/v1/auth/login
    ```

    Response:

    ```json
    {
      "access_token": "eyJhbGc...",
      "token_type": "bearer",
      "requires_2fa": false,
      "user": { "id": 1, "username": "admin", "...": "..." }
    }
    ```

    Send the access token via `Authorization: Bearer <jwt>`. **Access tokens live 1 hour.** A refresh token is set as an HttpOnly cookie (`bamdude_refresh`) on the path `/api/v1/auth` — call `POST /api/v1/auth/refresh` to mint a new access token transparently. Cookie attributes:

    | Attribute | Value |
    |-----------|-------|
    | Path      | `/api/v1/auth` (must be preserved by your client) |
    | HttpOnly  | yes — never exposed to JavaScript |
    | SameSite  | `Lax` |
    | Secure    | auto-detected from request scheme; honors `X-Forwarded-Proto` behind a trusted proxy. Force with the `AUTH_REFRESH_COOKIE_SECURE` env var. |
    | Max-Age   | 30 days when `remember_me=true`; otherwise session cookie + 12 h DB lifetime |

    !!! warning "2FA flow"
        When `requires_2fa: true`, the login response also includes `pre_auth_token` and a 2FA challenge cookie. POST it to `/api/v1/auth/2fa/verify` together with the user's TOTP code (or a backup code) to obtain the access + refresh tokens.

    OIDC SSO follows the same pattern via `/api/v1/auth/oidc/exchange` (PKCE S256 + state + nonce).

---

## :material-speedometer: Rate limiting

BamDude rate-limits authentication endpoints to slow down credential stuffing. Other endpoints are not rate-limited at the API layer — front them with a reverse proxy or firewall if you need a hard ceiling.

| Endpoint | Per-user / email | Per-IP |
|----------|------------------|--------|
| `POST /auth/login` | 10 / 15 min per username | 20 / 15 min |
| `POST /auth/forgot-password` | 3 / 15 min per email | 10 / 15 min |

When the limit trips you receive `429 {"detail": "..."}` and a `Retry-After` header.

!!! tip "Behind a reverse proxy"
    Set `TRUSTED_PROXY_IPS` (comma-separated trusted hops) so rate-limiting reads the real client IP from `X-Forwarded-For` instead of the proxy's IP. See [Reverse Proxy & HTTPS](../getting-started/reverse-proxy.md) for the full nginx / Caddy / Traefik recipes.

---

## :material-shield-lock: Setup gate

On first boot the server only accepts three endpoints. Every other request returns `503 {"detail": "setup_required"}` until an admin is created.

| Endpoint | Purpose |
|----------|---------|
| `GET  /api/v1/auth/status` | Returns `{is_setup, requires_setup, ...}` so installers can detect the empty-DB state. |
| `POST /api/v1/auth/setup`  | One-shot: creates the initial admin and returns the access + refresh tokens. |
| `GET  /api/v1/system/health` | Liveness probe (always whitelisted). |

Once setup completes the gate disables itself in-process; you don't need to restart.

!!! danger "Lost all admins?"
    Run `python -m backend.app.cli reset_admin` on the server to clear the setup flags, then visit the UI to re-enter the setup flow. See [Authentication recovery](../features/authentication.md) for the full recovery protocol.

---

## :material-lock-check: Permissions

Every endpoint is gated by `RequirePermission(Permission.X)` where `X` follows the `resource:action` pattern. There are **80+ permissions** defined in `backend/app/core/permissions.py`. Common ones:

| Resource | Examples |
|----------|----------|
| Printers | `printers:read`, `printers:control`, `printers:create`, `printers:delete`, `printers:files`, `printers:clear_plate` |
| Archives | `archives:read`, `archives:create`, `archives:update_own`, `archives:update_all`, `archives:delete_own`, `archives:delete_all`, `archives:reprint_own`, `archives:reprint_all` |
| Library  | `library:read`, `library:upload`, `library:update_own`, `library:delete_all`, `library:notes_write` |
| Queue    | `queue:read`, `queue:create`, `queue:update_all`, `queue:delete_all`, `queue:reorder` |
| Users    | `users:read`, `users:create`, `users:update`, `users:delete` |
| Settings | `settings:read`, `settings:update`, `settings:backup`, `settings:restore` |
| Camera   | `camera:view` |

Three default groups cover most setups:

- **Administrators** — every permission.
- **Operators** — full control of printers, queue, archives, library; no settings/users administration.
- **Viewers** — read-only.

Create custom groups for granular control. The interactive `/docs` browser shows the required permission for each endpoint.

---

### Deleting an account and its content

`DELETE /api/v1/users/{user_id}?delete_items=true` requires an administrator with `users:delete`, and the normal filing/consequence rights for any affected order work. Success is **200 JSON**, not 204:

```json
{"deleted":true,"counts":{"archives":1,"library_files":0,"queue_items":0,"auto_queue_items":0},"affected_orders":[]}
```

`affected_orders` contains authorized `id`/`name` snapshots and removed `prints`/`jobs` counts. Replan removed pending work as needed; planned quantities are not automatically returned. The whole transaction refuses with **409** and `detail.error` equal to `user_content_delete_active`, `user_content_delete_too_large`, or `user_content_delete_changed`. Resolve retained/active work through ordinary queue or recovery controls; remove large content sets through their normal pages; retry a changed plan. The bound is 8 parents (including referenced library sources) and 1,000 affected rows, including account/session/key descendants. Filing or received-output refusals retain their own status and reason. A refusal changes no account/content rows and unlinks no files.

With `delete_items=false` (the default), success remains **204 with no body** and content becomes ownerless. Self-deletion and removing the last administrator are refused in both modes. Physical stock/usage history and immutable completion facts are preserved.

---

## :material-routes: Endpoint groups

The 43 route modules under `backend/app/api/routes/` are registered under the `/api/v1` prefix. Major groups at a glance:

| Prefix | What it does | Notable endpoints |
|--------|--------------|-------------------|
| `/auth/*` | Login, refresh, setup, OIDC | `login`, `refresh`, `logout`, `setup`, `2fa/verify`, `oidc/exchange`, `forgot-password` |
| `/users/*`, `/groups/*`, `/api-keys/*`, `/mfa/*` | Users, groups, API keys, MFA enrollment | CRUD, group assignment, MFA reset, backup codes |
| `/printers/*`, `/cloud/*`, `/discovery/*` | Printer + AMS + Bambu Cloud | status, control, AMS RFID, snapshot, stream-token, network discovery |
| `/archives/*` | Print history | list (`?outcome=unchecked` for completed prints whose result nobody has checked), get, reprint, delete, **`outcome-checked`**, **`retry-download`**, **`cleanup/preview`**, **`cleanup/run`**, **`cleanup/status`** |
| `/queue/*`, `/queues/*`, `/background-dispatch/*` | Queue management + dispatch | add, reorder, cancel, set-status, dispatch state; a printer queue's own state on `/queues/{id}` (pause, resume, `acknowledge-failure`) |
| `/library/*` | File manager | upload, list, delete, tags, notes (`files/{id}/notes`, `notes/{id}`), photos (`files/{id}/photos`), a file's own link (`files/{id}/external-url`), folder rename and move (`PUT folders/{id}`), external folders and their scans (`folders/external`, `folders/{id}/scan`, `scan-jobs/{id}`) — also the inbox for virtual-printer uploads. Per-route rights: [File Manager → API endpoints](../features/file-manager.md#api-endpoints) |
| `/model-sources/manyfold/*` | Manyfold model source | status, model list and search (`models`), a model with its files (`models/{model_id}`), its preview, the import of one file (`import`), and the connection (`connection`, `connection/test`). Per-route rights: [Manyfold library → Developer reference](../features/manyfold.md#developer-reference) |
| `/projects/*` | Project grouping | CRUD, print plan, archives by project |
| `/macros/*` | G-code + MQTT-action macros | CRUD, execute |
| `/notifications/*`, `/notification-templates/*`, `/user-notifications/*`, `/telegram/*` | Outbound channels | provider CRUD, template overrides, test send, Telegram bot config, [messages from external apps](../features/notifications.md#external-app-messages) (`POST /notifications/external-message`) |
| `/spoolman/*`, `/inventory/*` | Spool tracking | sync, slot mapping, color/spool catalog |
| `/smart-plugs/*` | Smart plug config | CRUD, energy snapshots, manual on/off |
| `/system/*`, `/support/*`, `/updates/*`, `/firmware/*` | Health + diagnostics + updates | `health`, settings, backup, restore, debug bundle, firmware check |
| `/local-backup/*`, `/git-backup/*` | Backup providers | run, restore, schedule |
| `/maintenance/*`, `/kprofiles/*` | Service tracking + K-profiles | log, due, CRUD |
| `/external-links/*`, `/ams-history/*` | Misc UX | dashboard links, AMS slot change history |
| `/metrics`, `/webhook/*`, `/obico/*`, `/octoeverywhere/*`, `/virtual-printers/*` | Integrations | Prometheus metrics, inbound webhooks, AI failure detection (Obico, OctoEverywhere), virtual printer (slicer target) |

The full enumerated list is in `/docs` — this table just shows where to look.

---

## :material-camera-iris: Camera streams and binary endpoints

Some endpoints are consumed by `<img>` / `<video>` tags, which can't send an `Authorization` header, so they also take a short-lived token (60 min TTL) as a `?token=` query parameter. There are two, and they are not interchangeable:

- the **stream token** — the camera: live stream, snapshot, plate-detection reference;
- the **media token** — every other picture and video: thumbnails, plate previews, timelapses, QR codes, covers.

A script or integration does not need either: the same endpoints accept the ordinary `X-API-Key` / `Authorization` header, within the key's scopes.

```bash
# 1. Mint a token (auth required)
TOKEN=$(curl -s -H "X-API-Key: bd_..." \
  -X POST https://bamdude.example.com/api/v1/printers/camera/stream-token \
  | jq -r .token)

# 2. Use it on binary endpoints
curl "https://bamdude.example.com/api/v1/printers/2/camera/snapshot?token=$TOKEN" -o snap.jpg
```

Endpoints behind the stream-token gate (minting one needs `camera:view`):

| Endpoint | Returns |
|----------|---------|
| `GET /printers/{id}/camera/stream?token=...` | MJPEG stream |
| `GET /printers/{id}/camera/snapshot?token=...` | JPEG snapshot |
| `GET /cameras/{id}/stream?token=...` · `GET /cameras/{id}/snapshot?token=...` | The same for a standalone camera |
| `GET /printers/{id}/camera/plate-detection/references/{index}/thumbnail?token=...` | Calibration-reference thumbnail used by plate-clear detection (`{index}` selects which stored reference). |
| `GET /obico/cached-frame/{nonce}` | Frame URL handed to the Obico ML API. Whitelisted in the auth middleware because Obico's GET can't carry a bearer header — the nonce itself is the capability. |

The **media token** is minted by any signed-in user with `POST /auth/media-token` (a JWT, not an API key — a key uses its header instead). It names the user, so each endpoint applies the permission and ownership rule of what it serves — a user limited to their own prints gets only their own pictures:

| Endpoint | Permission |
|----------|------------|
| `GET /archives/{id}/thumbnail` · `/plate-thumbnail/{n}` · `/plate-preview` · `/project-image/{path}` · `/qrcode` · `/timelapse` · `/photos/{file}` | `archives:read_all` / `archives:read_own` |
| `GET /library/files/{id}/thumbnail` · `/plate-thumbnail/{n}` · `/card-file/{path}` · `/image` · `/photos/{photo_id}/image` · `/photos/{photo_id}/thumbnail` · `GET /makerworld/imports/{id}/cover` · `/cover-variant` | `library:read_all` / `library:read_own` |
| `GET /products/{id}/attachment-image/{file}` · `/cover-image` · `GET /projects/{id}/cover-image` | `products:read` for a product's pictures, `orders:read` for an order's cover |
| `GET /printers/{id}/camera-cover` | `printers:read` — the current job's cover, served from the local archive (never triggers an FTP fetch) |
| `GET /makerworld/thumbnail?url=...` | `makerworld:view` |
| `GET /model-sources/manyfold/models/{model_id}/preview` | `manyfold:view` |

Public, no token: `GET /notifications/photos/{file}` (the copy of one photo that a notification links to, for services that fetch without credentials — the address is unguessable and stops working after 3 days), `GET /external-links/{id}/icon` and `GET /auth/oidc/providers/{id}/icon` (the sign-in page). A Cam Wall, overlay or kiosk token opens no media endpoint.

The web UI keeps both tokens cached per session and refreshes them before expiry.

---

## Download jobs

A download of a printer's files, or of a print's videos, is a job: created once, prepared on the server's disk, polled, and then fetched. The older `GET /printers/{id}/files/download` and `POST /printers/{id}/files/download-zip` still answer with the file in one request; they are prepared the same way on disk, are subject to the same limits, and the ZIP one reports files it had to leave out in the `X-Download-Failed` header.

| Endpoint | What it does |
|----------|--------------|
| `POST /printers/{id}/files/download-jobs` | Start a job. Body: `paths` (1–1000 absolute file paths), optional `storage`, `sizes` (path → bytes, as listed), `as_zip`, `filename`. Answers `202` with the job. Several files are always one ZIP. |
| `GET /printers/{id}/files/download-jobs` | The caller's own jobs for this printer. |
| `GET /printers/{id}/files/download-jobs/{job_id}` | The job: `phase`, counts, bytes received, `failures`, `error`. |
| `DELETE /printers/{id}/files/download-jobs/{job_id}` | Cancel a job that is being prepared, or drop a finished one. A cancelled job reads `cancelling` until its transfer has really stopped, then `cancelled`. |
| `GET /printers/{id}/files/download-jobs/{job_id}/artifact` | The finished file, for a client that sends headers (an API key). Add `?accept_partial=true` to take a partial result. |
| `POST /printers/{id}/files/download-jobs/{job_id}/download-token` | Browser sessions only: a one-time URL the browser saves the file from. An API key is refused (`403`) and uses `/artifact`. |
| `GET /archives/{id}/media-sources` | What can be downloaded for a print: `local`, `timelapse` and `camera`, each with its own `status`. Optional `offset_minutes` (the printer's clock ahead of UTC) and `margin_minutes`. |
| `POST /archives/{id}/media-download-jobs` | Start a job over an archive: `assets` (ids from `local`) and/or `remote` (`printer_id`, `storage`, `path`, optional `size` — the archive's own printer only). The other job endpoints mirror the printer ones under `/archives/{id}/media-download-jobs/…`. |

`phase` is one of `queued`, `preparing`, `cancelling`, `ready`, `failed`, `cancelled`, `expired`. A failed job carries an `error` code: `authority_lost`, `limit_exceeded`, `insufficient_storage`, `time_limit`, `nothing_downloaded`, `interrupted`, `cleanup_incomplete` or `internal`. A `ready` job with `partial: true` holds only the files that could be read; `failures` names the rest.

A job belongs to the credential that created it — that browser session, or that API key: another user's job, a job of another session of the same account, another key's job and a job that does not exist are the same `404`. Printer jobs need `printers:files`; archive jobs need the right to read the archive, and `printers:files` only when they read the printer. Every endpoint of a job asks again for what the job was created with: once the caller no longer has it, the job's status, cancel, download token and file answer `403`, and the job leaves the list. When the server cannot check those rights at that moment, the job's endpoints and the list answer `503` with `Retry-After` — the job is still there; ask again. A job whose printer or archive has since been deleted — and its number taken by another — answers `404` (`401` on `/artifact`). `/artifact` takes its credential from the request headers only and refuses a request that also carries `?token=` (`400`). Refusals at creation carry a code in `detail.error`: `download_queue_full` and `download_user_limit` (`429`, with `Retry-After`), `insufficient_storage` (`507`), `limit_exceeded` and `too_many_files` (`413`), `downloads_unavailable` (`503`, during a restore).

The finished file is always sent whole — `200` with `Accept-Ranges: none`; a `Range` header is ignored. Jobs live in memory: a restart forgets them, and a result that nobody fetched is removed after an hour.

### Timelapse edits

An edit of an archive's video runs in the background. Starting, reading and cancelling an edit need `archives:update_all`.

| Endpoint | Description |
|---|---|
| `POST /archives/{id}/timelapse/process` | Start an edit. Query: `trim_start`, `trim_end` (seconds), `speed` (0.25–4), `save_mode` (`new` — the default, keeps the original — or `replace`), `audio_volume` (0–1), `mute`, and `audio_name` when music is sent. **The music is the request body itself** (`Content-Type: application/octet-stream`), 100 MB at most; there is no multipart form. Answers `202` with the job. |
| `GET /archives/{id}/timelapse/edit-jobs` | The caller's own edits of this archive. |
| `GET /archives/{id}/timelapse/edit-jobs/{job_id}` | One edit: `phase`, `progress` (0–1), `error`, `save_mode`, `result`. |
| `DELETE /archives/{id}/timelapse/edit-jobs/{job_id}` | Ask the edit to stop. It reads `cancelled` only once its encoder has ended, and a cancel that is accepted saves nothing. Once the result is being saved the answer is `409 cancel_too_late`. |
| `GET /archives/{id}/timelapse/variants` | The videos saved beside the original with `save_mode=new`. |
| `DELETE /archives/{id}/timelapse/variants/{asset}` | Remove one of them (the right to delete the archive). |

`phase` is one of `queued`, `encoding`, `publishing`, `cancelling`, `done`, `failed`, `cancelled`. `progress` is `1` only in `done`, that is, after the result was saved. A failed edit carries an `error` code: `source_changed` (the archive's video was replaced or removed meanwhile — nothing was saved), `target_gone`, `authority_lost`, `interrupted` (a restore or a restart), `encode_failed`, `encode_timeout`, `encode_stalled`, `output_invalid`, `process_unreaped`, `publish_failed`, `cleanup_failed`.

Refusals at the start: `415 legacy_request` (a multipart or URL-encoded form — the request of before), `409 edit_in_progress` (this video is already being edited), `409 source_changed` (the video changed while the edit was being started), `429 edits_busy`, `400 edit_invalid` / `audio_invalid`, `413 audio_too_large`, `422 video_unreadable`, `503 restoring` / `ffmpeg_missing`. An edit belongs to the credential that created it; another caller's edit and one that does not exist are the same `404`. Edits live in memory: a restart forgets them and removes what they left on disk.

!!! warning "Changed request"
    `POST /archives/{id}/timelapse/process` used to take a multipart form and answer when ffmpeg had finished. It now takes the query parameters above, answers `202` at once, and its result is read from the job. A form is refused with `415 legacy_request` — it is never read as the new request.

## :material-bell-ring: Webhooks and realtime events

BamDude does **not** expose outbound webhooks for application events. Use a [notification provider](../features/notifications.md) (Telegram, Discord, ntfy, Pushover, Email, Home Assistant) when you need a one-way push.

The realtime channel is the WebSocket at `wss://<host>/api/v1/ws`. It carries:

- Printer status updates (temps, progress, AMS state)
- Dispatch and queue progress
- Archive create / update events
- Smart-plug state and energy ticks

!!! warning "WebSocket is currently unauthenticated"
    `/api/v1/ws` is in the auth middleware's public-route allowlist (`backend/app/main.py::PUBLIC_API_ROUTES`) and the handler performs no token check. Anyone able to reach the host on the WebSocket port can subscribe to realtime events. Treat the realtime channel as **read-only and intra-network** — front BamDude with a reverse proxy (see [Reverse Proxy & HTTPS](../getting-started/reverse-proxy.md)) and don't expose `/ws` directly to the public internet. Tightening this is tracked work; do not assume `Authorization: Bearer` will block subscribers today.

### Inbound automation endpoints

The `/webhook/*` group is the other direction: endpoints **your** automation calls, authenticated with an API key. They are the five listed in **Settings → API keys**.

| Endpoint | Scope needed | What it does |
|---|---|---|
| `GET /api/v1/webhook/queue` | `can_read_status` | Queue status for every printer that is not archived, or one via `?printer_id=` |
| `GET /api/v1/webhook/printer/{id}/status` | `can_read_status` | Connection, state, current print, progress, remaining time |
| `POST /api/v1/webhook/printer/{id}/start` | `can_control_printer` | Start the **next queued** print on that printer |
| `POST /api/v1/webhook/printer/{id}/stop` | `can_control_printer` | Stop a running **or paused** print |
| `POST /api/v1/webhook/printer/{id}/cancel` | `can_control_printer` | Cancel a running **or paused** print |

A key scoped to specific printers (`printer_ids`) is refused with **403** on any other printer. A printer that is not connected answers **503**, not an error — retry when it comes back. `start` answers **404** when the queue holds no job that is due (a job scheduled for later is not the next one), and **409** when the printer is busy, its queue is paused, the plate has not been confirmed as cleared, or the job was refused — the answer then says why. Only **200** means the print was started. `stop` and `cancel` answer **409** when no print is running or paused.

A print ended through `stop` or `cancel` is recorded as stopped by a person, the same as a stop from the printer card: it ends as cancelled, not failed. No *print failed* notification goes out, the printer's queue is paused rather than put in error, and the job's owner gets the *stopped* e-mail.

```bash
curl -H "X-API-Key: $KEY" https://<host>/api/v1/webhook/printer/3/status
curl -X POST -H "X-API-Key: $KEY" https://<host>/api/v1/webhook/printer/3/start
```

!!! note "There is no add-to-queue endpoint here"
    Queueing goes through `POST /api/v1/queue/` with an `archive_id`, a `library_file_id`, or a readable existing queue row as `source_queue_item_id` when copying a saved job. The webhook group has no version of its own: a queue row built by hand would skip the paused-queue check, the printer-model compatibility gate and the queue counters. One way in is the point.


---

## :material-script-text-play: Common operations — quick recipes

### List the last 50 archives for a printer

```bash
curl -H "X-API-Key: bd_..." \
  "https://bamdude.example.com/api/v1/archives/?printer_id=2&page=1&per_page=50"
```

### Add a library file to the queue (3 copies, fixed AMS mapping)

```bash
curl -X POST \
  -H "X-API-Key: bd_..." \
  -H "Content-Type: application/json" \
  -d '{
    "library_file_id": 42,
    "queue_id": 2,
    "ams_mapping": [0, 1, 2, 3],
    "quantity": 3
  }' \
  "https://bamdude.example.com/api/v1/queue/"
```

### Get current printer status

```bash
curl -H "X-API-Key: bd_..." \
  "https://bamdude.example.com/api/v1/printers/2/status"
```

### Read the same thing for several printers at once

A page that shows many printers asks once instead of once per printer. Each route takes repeated `ids` (up to 100) and answers an object keyed by printer id, whose values are what the single-printer route answers. A printer outside the key's printer list is left out.

```bash
curl -H "X-API-Key: bd_..." \
  "https://bamdude.example.com/api/v1/printers/status/batch?ids=1&ids=2&ids=3"
```

| Route | Per printer |
|---|---|
| `GET /printers/status/batch` | Live status |
| `GET /printers/ams-labels/batch` | AMS labels by AMS id |
| `GET /archives/last-by-printer` | The newest archive (`id`, `print_name`, `filename`, `status`, `completed_at`); a printer without one is left out |
| `GET /smart-plugs/by-printer/batch` | `main` — the plug the card shows as the printer's power — and `scripts` |
| `GET /ha-sensors/readings/batch` | Card-visible Home Assistant sensor readings |
| `GET /firmware/updates/batch` | The automatic firmware check |

### Skip specific objects mid-print

The body is a JSON array of object IDs reported by the slicer.

```bash
curl -X POST \
  -H "X-API-Key: bd_..." \
  -H "Content-Type: application/json" \
  -d '[100, 200]' \
  "https://bamdude.example.com/api/v1/printers/2/print/skip-objects"
```

### Recover a missing 3MF for an archive

When `on_print_start` couldn't FTP the 3MF (printer unreachable, FTP timeout) the archive row is created with `extra_data.no_3mf_available = true`. Background sweeps retry automatically; you can also trigger it manually:

```bash
curl -X POST \
  -H "X-API-Key: bd_..." \
  "https://bamdude.example.com/api/v1/archives/123/retry-download"
```

### Trigger archive 3MF cleanup (preview, then run)

The cleanup job removes 3MF binaries for archives older than the retention window (the metadata row is kept). The daily cron runs automatically; for an ad-hoc sweep:

```bash
# Dry-run preview — what would be deleted, total bytes
curl -H "X-API-Key: bd_..." \
  "https://bamdude.example.com/api/v1/archives/cleanup/preview"

# Run it
curl -X POST -H "X-API-Key: bd_..." \
  "https://bamdude.example.com/api/v1/archives/cleanup/run"

# Inspect the daily cron's last run + next run
curl -H "X-API-Key: bd_..." \
  "https://bamdude.example.com/api/v1/archives/cleanup/status"
```

### Refresh a JWT session from your own client

```bash
# /auth/refresh reads the HttpOnly bamdude_refresh cookie set during login.
# --cookie-jar / --cookie persists it across calls.
curl -c cookies.txt -X POST \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "..."}' \
  https://bamdude.example.com/api/v1/auth/login

curl -b cookies.txt -c cookies.txt -X POST \
  https://bamdude.example.com/api/v1/auth/refresh
```

The refresh response returns a new access token and rotates the refresh cookie in place. Replaying an already-used refresh token revokes the entire token family across devices (OWASP reuse detection).

---

## :material-code-json: Versioning and stability

- The API version prefix is `/api/v1`. Breaking changes will ship under `/api/v2` rather than mutating v1.
- Additive changes (new endpoints, new optional fields) land in patch / minor releases without notice. Pin the BamDude container version if you depend on response shape stability.
- In a `PATCH` / `PUT` body, a field left out is unchanged. `null` clears a field that may be empty; for a field that cannot be empty, `null` is treated as left out.
- Deprecations are announced in the [changelog](https://github.com/kainpl/bamdude/blob/main/CHANGELOG.md) at least one minor release before removal.

> Originally based on [Bambuddy](https://github.com/maziggy/bambuddy).
