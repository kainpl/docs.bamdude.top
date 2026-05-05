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
| **Printer scope** | Optional. Leave empty for "all printers", or pick specific printer IDs to narrow the key. Calls against any other printer return 403 |
| **Expires at** | Optional ISO timestamp. After that, the key is rejected even if it isn't revoked |

The create response carries the full `key` field — **copy it before closing the dialog**. Subsequent reads of the row will only show the `bb_…` prefix.

!!! tip "Principle of least privilege"
    Don't blanket-tick all three flags. A Home Assistant dashboard usually needs only `can_read_status`. A queue-poster from your slicer needs `can_queue` + `can_read_status` and *not* `can_control_printer`. Separate keys per consumer make rotation painless and the audit trail readable.

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
    - `can_queue` — required for `POST /queue` and queue-mutation endpoints
    - `can_control_printer` — required for start / pause / stop / cancel
    - `can_read_status` — required for printer-state, archive, stats, monitoring reads
3. **`printer_ids` scope** narrows printer-bound calls. A key with `printer_ids = [3, 7]` returns 403 on `/printers/5/status` even if `can_read_status` is on.

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
    Some queue mutations also touch the library; check that the call's payload doesn't try to upload a file (which is a separate `library:upload` permission and isn't covered by `can_queue`).

??? question "Key works for status but not for `/control/start`"
    `can_control_printer` is off. Toggle it on with `PATCH`, then retry — no need to recreate the key.
