---
title: API Keys
description: Service-account tokens for headless scripting, integrations, and webhook callbacks against the BamDude REST API
---

# API Keys

API keys are the way you let a non-human caller talk to BamDude — Home Assistant, Node-RED, a CI script, your own dashboards. Each key is a long random `bb_…` token that satisfies the same permission gates as a human session, so a key that can read printers cannot suddenly start a print just because it asked nicely.

The auth stack is **always on** (see [Authentication](authentication.md)) — a key is the headless equivalent of a logged-in user, not a bypass.

---

## :material-shape: Token format

| Field | Value |
|---|---|
| **Prefix** | `bb_` (literal) |
| **Body** | 32 random bytes, base64-url-encoded — 43 chars |
| **Full length** | 46 characters |
| **At rest** | Hashed (`get_password_hash`); only the prefix + name are stored in clear |
| **Shown** | Once, on the create response. After that, revoke and regenerate if you lose it |

```
bb_VGhpc0lzVGhlVGVzdEtleVNvUGxlYXNlSWdub3JlMTIz
└┬┘ └─────────────────────────────────────────┘
prefix              random body
```

!!! warning "One-shot reveal"
    The full token is returned only in the response of `POST /api/v1/api-keys/`. BamDude never stores it in clear — there's no "show key" button on the list page. If you lose it, delete the row and create a new one.

---

## :material-key-plus: Creating a key

**Settings → API Keys → New API key.**

| Field | Purpose |
|---|---|
| **Name** | Human label — name keys after their consumer (`Home Assistant Dashboard`, `Print-farm Grafana`, `n8n queue-poster`) so you can spot them on the list later |
| **Can queue** | Allow this key to add jobs to the print queue (`POST /queue`) |
| **Can control printer** | Allow start / pause / stop / cancel commands |
| **Can read status** | Allow live printer state, archive lists, statistics — the read surface |
| **Manage Library** | Optional. Upload / rename / move / delete library files — **any owner**, not just the key creator's — plus notes and MakerWorld import (`can_manage_library`). Read-only library access stays under **Can read status** |
| **Manage Inventory** | Optional. Create / edit / delete spools, catalogue entries, and forecast settings (`can_manage_inventory`). Read-only inventory stays under **Can read status** |
| **Use Bambu Cloud** | Optional. When ticked, the key resolves the creating user's per-user Bambu Cloud token for `cloud:*` routes (slicer presets, MakerWorld imports). Off by default so legacy keys can never silently spend the owner's cloud token. Rejected at save time on ownerless keys — see badge note below. |
| **Printer scope** | Optional. Leave empty for "all printers", or pick specific printer IDs to narrow the key. Calls against any other printer return 403 |
| **Expires at** | Optional ISO timestamp. After that, the key is rejected even if it isn't revoked |

The create response carries the full `key` field — **copy it before closing the dialog**. Subsequent reads of the row will only show the `bb_…` prefix.

!!! info "Cloud / Legacy badges"
    UI-created keys are stamped with the creating user's id, so a key shown with the **Cloud** badge can spend that user's Bambu Cloud token. Pre-0.4.3 keys imported from older installs are ownerless and surface a **Legacy** badge — they cannot be promoted to `Use Bambu Cloud` (the toggle is rejected at save time without an owner). Re-create such keys under your user account to enable cloud spend.

!!! tip "Principle of least privilege"
    Don't blanket-tick every scope. A Home Assistant dashboard usually needs only `can_read_status`. A queue-poster from your slicer needs `can_queue` + `can_read_status` and *not* `can_control_printer`. A file-uploader integration can now get `can_manage_library` without `can_queue`. Separate keys per consumer make rotation painless and the audit trail readable.

---

## :material-send-lock: Sending a key

Both header forms are accepted — pick whichever fits your client.

```bash
# X-API-Key header (preferred for tools that distinguish "API key" from "Bearer token")
curl -H "X-API-Key: bb_..." http://localhost:8000/api/v1/printers/

# Authorization: Bearer header — works because the server detects the bb_ prefix
# and routes to the API-key validator instead of JWT validation.
curl -H "Authorization: Bearer bb_..." http://localhost:8000/api/v1/printers/
```

Both reach the same code path. The `bb_` prefix on a `Bearer` token tells BamDude this is an API key, not a session JWT, so the JWT signature path is skipped and the key-hash compare runs instead.

---

## :material-shield-key: Permission model

Two layers gate every API-keyed call:

1. **The endpoint's required permission** is checked. API keys bypass *user* permission checks (they have no group membership), but…
2. **The key's own flags** are evaluated:
    - `can_queue` — required for `POST /queue` and queue-mutation endpoints (+ archive reprint, which enqueues an existing archive)
    - `can_control_printer` — required for start / pause / stop / cancel (+ smart-plug control)
    - `can_read_status` — required for printer-state, archive, stats, monitoring reads (and read-only library / inventory / settings-language)
    - `can_manage_library` — required for library upload / rename / move / delete + notes + MakerWorld import. A key rides the **all-ownership** variants (`library:update_all` / `library:delete_all`): API keys carry no per-row ownership identity, so a Manage-Library key can curate **any** file regardless of owner. Only `library:purge` (hard-delete past the trash window) stays admin-only
    - `can_manage_inventory` — required for spool / catalogue / forecast **writes** (read-only inventory stays under `can_read_status`)
    - `can_access_cloud` — required for cloud-token-backed endpoints (slicer presets, MakerWorld)
    - `can_update_energy_cost` — required for `POST /settings/electricity-price` (the narrowly-scoped Home-Assistant dynamic-tariff endpoint — see [Energy → Tibber / Octopus / Dynamic Tariff Integration](energy.md#tibber--octopus--dynamic-tariff-integration)). Does NOT grant general `SETTINGS_UPDATE`.
3. **`printer_ids` scope** narrows printer-bound calls. A key with `printer_ids = [3, 7]` returns 403 on `/printers/5/status` even if `can_read_status` is on.

!!! warning "Strict scope confinement"
    A key now reaches **only** the endpoints its granted scopes cover. Anything outside them — settings writes, user / group / API-key administration, resource deletion (printers, archives, projects), and network discovery scans — is refused with `403`, even for an otherwise-valid, enabled key. Previously any valid key could reach almost every endpoint (start/stop prints, reorder the queue, reprint archives, delete another user's library files, read every resource) *regardless* of which scope checkboxes were ticked on it — upstream advisory **GHSA-r2qv-8222-hqg3** (CVSS 9.9 critical). The mapping is an allowlist: a permission with no scope entry is denied by default, so a newly-added admin endpoint is never silently reachable by a key.

!!! info "Upgrade inheritance"
    The two scopes added in this cycle — `can_manage_library` and `can_manage_inventory` — are backfilled from each key's existing **Manage Queue** (`can_queue`) setting on upgrade. A queue-enabled key keeps its prior upload + inventory-write workflow, while a hardened read-only key (`can_queue = false`) gains nothing. Adjust either scope afterwards with `PATCH /api-keys/{id}`.

The permissions that gate the **management** of the keys themselves (who can list / create / revoke) are normal user-group permissions:

| Permission | Granted to |
|---|---|
| `api_keys:read` | Administrators |
| `api_keys:create` | Administrators |
| `api_keys:update` | Administrators |
| `api_keys:delete` | Administrators |

Operators and Viewers cannot manage API keys by default — issuing service-account credentials is an admin-level task.

---

## :material-clock-outline: Key lifecycle

| Field | When written |
|---|---|
| `created_at` | At key creation |
| `last_used` | Updated by the validator on every successful request — handy for spotting unused keys |
| `expires_at` | Optional. Once past, the key is rejected with 401 even if `enabled=True` |
| `enabled` | Soft-disable toggle. `PATCH /api-keys/{id}` with `enabled=false` to pause without deleting |

Calls with a disabled, expired, or unknown key get `401 Unauthorized` with a one-line "API key required / invalid" body — no information leak about why.

---

## :material-server-network: Common endpoints

| Endpoint | Method | Required flag |
|---|---|---|
| `/printers/` | GET | `can_read_status` |
| `/printers/{id}/status` | GET | `can_read_status` |
| `/printers/{id}/control/start` | POST | `can_control_printer` |
| `/printers/{id}/control/pause` | POST | `can_control_printer` |
| `/printers/{id}/control/stop` | POST | `can_control_printer` |
| `/queue/` | GET | `can_read_status` |
| `/queue/` | POST | `can_queue` |
| `/queue/{id}` | DELETE | `can_queue` |
| `/archives/` | GET | `can_read_status` |
| `/statistics` | GET | `can_read_status` |

The full schema is at `GET /openapi.json` — every route's `security` block lists which credential variants it accepts.

---

## :material-laptop: Examples

### `curl`

```bash
# Read printer status
curl -s -H "X-API-Key: bb_..." http://localhost:8000/api/v1/printers/3/status \
  | jq '.state, .progress'

# Add a library file to a printer's queue
curl -X POST http://localhost:8000/api/v1/queue/ \
  -H "X-API-Key: bb_..." \
  -H "Content-Type: application/json" \
  -d '{"printer_id": 3, "library_file_id": 142, "quantity": 1}'
```

### Python (`requests`)

```python
import os, requests

BASE = "http://bamdude.lan:8000/api/v1"
KEY = os.environ["BAMDUDE_API_KEY"]
HEADERS = {"X-API-Key": KEY}

# Poll all printers, print the first one that's idle
for p in requests.get(f"{BASE}/printers/", headers=HEADERS).json():
    state = requests.get(f"{BASE}/printers/{p['id']}/status", headers=HEADERS).json()
    if state["state"] == "IDLE":
        print(f"{p['name']} idle, ready to dispatch")
        break
```

### Home Assistant `rest_command`

```yaml
rest_command:
  bamdude_pause_printer:
    url: "http://bamdude.lan:8000/api/v1/printers/{{ printer_id }}/control/pause"
    method: POST
    headers:
      X-API-Key: !secret bamdude_api_key
```

Trigger from any automation: `service: rest_command.bamdude_pause_printer` with `data: {printer_id: 3}`.

### Node-RED

Drop an **HTTP request** node, set the URL to `http://bamdude.lan:8000/api/v1/printers/`, add a header `X-API-Key` with your key, and chain a **debug** or **switch** node. For multiple endpoints, store the key once in a global context variable and inject it via a function node.

### Webhook callbacks (`X-API-Key` on the receiving end)

If you point a notification webhook (see [Notifications](notifications.md)) at your *own* receiver and want it to authenticate against BamDude back, the same `X-API-Key` header convention applies — your receiver gets the BamDude payload, then it calls back into BamDude for context using its own API key. BamDude doesn't sign outgoing webhooks itself; protect the receiver by IP allow-listing or by putting it behind a proxy that requires a secret header.

---

## :material-cancel: Revoking

| Action | Endpoint | Effect |
|---|---|---|
| **Soft disable** | `PATCH /api-keys/{id}` with `enabled=false` | Key returns 401 immediately. Reversible by setting `enabled=true` again |
| **Hard delete** | `DELETE /api-keys/{id}` | Row removed from the DB. Cannot be undone — issue a new key |
| **Expire** | Set `expires_at` in the past | Validator treats as expired, returns 401 |

After any of those, in-flight requests already past the validator finish (the validator runs once per request); the *next* request from that key fails. There's no global cache to wait out.

!!! tip "Audit before you rotate"
    Before deleting a key, peek at `last_used` on the list view. A key that hasn't been used in a year is safe to delete; a key that was used 30 seconds ago has an active consumer that's about to start failing. Coordinate the rotation with the consumer's restart window.

---

## :material-shield-check: Best practices

- **Name keys after their consumer.** `n8n-print-trigger` beats `key1`. Future-you grepping the list at 2 AM will thank present-you.
- **Use one key per consumer.** Easier rotation, easier revoke, individual `last_used` tells you who's still on it.
- **Narrow flags.** A read-only key is one less footgun. A printer-scoped key cannot mass-cancel your farm.
- **Set `expires_at`** for short-lived integrations (CI pipelines, demos). Auto-expiry is cheaper than remembering to revoke.
- **Don't commit keys.** `.env`, secret managers, HA secrets, k8s `Secret` — anywhere but the repo.
- **Rotate periodically.** Especially after a contributor leaves or a laptop walks off. Create new → swap consumer → delete old.
- **Monitor `last_used`.** A read-only key suddenly used at 3 AM from a new IP is a useful early warning.

---

## :material-help-circle: Troubleshooting

??? question "401 Unauthorized — `API key required`"
    No `X-API-Key` header *and* no `Authorization` header on the request. Add one of them. If you're behind a proxy that strips custom headers, switch to `Authorization: Bearer bb_…`.

??? question "401 Unauthorized — but the key looks right"
    Check `enabled` on the row, then `expires_at`. A `PATCH` toggling `enabled` back to `true` revives a soft-disabled key. An expired key needs to be replaced — `expires_at` is a one-way street.

??? question "403 Forbidden on a printer I own"
    The key's `printer_ids` scope is set and doesn't include this printer. Either expand the scope (`PATCH` with the new id list) or use a different key.

??? question "403 Forbidden on `/queue` POST with `can_queue=true`"
    Some queue mutations also touch the library; a payload that uploads a file needs the separate **Manage Library** (`can_manage_library`) scope — it isn't covered by `can_queue`.

??? question "403 Forbidden writing library / inventory with a queue-enabled key"
    Since strict-scope confinement, library writes need `can_manage_library` and inventory writes need `can_manage_inventory` — they're no longer implied by `can_queue`. On upgrade these were backfilled from `can_queue`, but a key edited to read-only, or created after the split, needs them ticked explicitly. `PATCH /api-keys/{id}` with the scope, then retry.

??? question "Key works for status but not for `/control/start`"
    `can_control_printer` is off. Toggle it on with `PATCH`, then retry — no need to recreate the key.
