---
title: Cloud Profiles
description: Per-user Bambu Cloud sign-in with regional split, MFA, and direct preset/device access from BamDude
---

# Cloud Profiles

Cloud Profiles is the bridge between your Bambu Cloud account and BamDude. Once signed in, your filament / process / printer presets become visible inside the slice modal alongside any locally imported ones (see [Local Profiles](local-profiles.md)), printer-firmware checks gain access to the Bambu device list, and slicing pipelines can resolve the same preset names as Bambu Studio.

The integration is **per-user**. Each BamDude account holds its own Bambu Cloud token — your colleague signing into their own Bambu account doesn't kick you out, and your token doesn't leak into theirs.

---

## :material-earth: Per-user region (BamDude addition)

Bambu Cloud is split across two regional backends — `bambulab.com` (global) and `bambulab.cn` (China) — and your account lives on exactly one of them. Upstream Bambuddy stores the region globally, so an install with mixed users couldn't have one account on global and one on China at the same time.

BamDude lifts that limit with migration **m011**: every `User` row carries its own `cloud_region` column (`global` / `china` / `null`). Sign-in writes the region you picked, and every subsequent request from that user uses the matching backend host, even after a restart. Two users on different regions in the same install is a supported configuration.

| Stored on | Field | Default |
|---|---|---|
| `users` row (auth enabled) | `cloud_token`, `cloud_email`, `cloud_region` | `null` until signed in |
| `settings` table (auth disabled) | `bambu_cloud_token`, `bambu_cloud_email`, `bambu_cloud_region` | Fallback path — single global cred bag |

A `null` / empty / unknown region is treated as `global` for legacy rows that predate the column.

---

## :material-login: Sign-in flows

**Settings → Cloud Profiles → Connect to Bambu Cloud.** Three sub-flows are supported, picked by your account's MFA setup or your preference:

### 1. Email + password + email OTP

Standard Bambu Cloud login for accounts without TOTP.

1. Pick your **region** (Global / China)
2. Enter Bambu **email** + **password**
3. Submit — BamDude calls `/v1/user-service/user/login` and gets back `needs_verification=true`
4. Bambu emails a 6-digit code; type it into BamDude's verify dialog
5. BamDude calls `/cloud/verify` with the code → token stored on your user row → status flips to **Connected**

### 2. Email + password + TOTP

For accounts with an authenticator-app TOTP enrolled.

1. Same first three steps as above, but the login response has `verification_type='totp'` + a `tfa_key`
2. Open Google Authenticator / Authy / 1Password
3. Enter the current 6-digit code
4. BamDude calls `/cloud/verify` with `tfa_key` + code

The flow auto-detects which method your account uses — the dialog renders the right prompt without you choosing.

!!! tip "TOTP > email"
    If your account has both, TOTP is faster (no email round-trip) and works offline. Make sure your device clock is in sync — TOTP windows are 30 s, a clock drift > 1 minute will make every code look wrong.

### 3. Direct access-token paste

For headless setups, SSO accounts, or environments where the email/OTP round-trip won't work.

1. Click **Use access token instead**
2. Obtain a Bambu Cloud bearer via [`bambu-lab-cloud-api`](https://pypi.org/project/bambu-lab-cloud-api/), or from a browser logged into MakerWorld (DevTools → Application → Cookies → `token`). Bambu Studio no longer exposes the token in any UI, so the old "grab it from Studio" route no longer works. Treat the cookie value as a secret.
3. Paste it into the **Access token** field, pick the region
4. BamDude verifies the token by calling `/v1/user-service/user/profile`. On success the token is stored against your user row

!!! note "China-region accounts must use token login"
    China-region Bambu accounts are bound to a phone number rather than an email, so the email/password flow can't be used — the access-token path above is the only way in.

!!! note "Cloud Access Token vs Printer Access Code"
    The Cloud Access Token is the bearer used for the Bambu API + MQTT — that's what this page wants. The Printer Access Code on the printer's screen (Network settings) is the per-printer LAN credential — different field, different page (the [Printers](printer-control.md) form).

---

## :material-clock-end: Token lifetime

Bambu Cloud bearers are valid for ~90 days. BamDude does **not** silently refresh them — when the token expires, the next call returns 401 and the route handler clears your stored token (`clear_token()` in `cloud.py`). Your status flips back to **Disconnected** and you re-run the sign-in flow.

The same token also gates [MakerWorld import](makerworld.md) downloads — if your MakerWorld page suddenly shows `can_download=false`, an expired Bambu Cloud token is the most common cause.

---

## :material-database-search: What gets pulled

Once connected, the slice modal and other consumers can read your Bambu Cloud data live:

| Data | Endpoint | Used by |
|---|---|---|
| Filament / process / printer presets | `GET /api/v1/cloud/settings` | Slice modal, AMS slot config |
| Single preset detail (full setting JSON) | `GET /api/v1/cloud/settings/{id}` | "Inspect preset" / inheritance display |
| Bound printer devices | `GET /api/v1/cloud/devices` | Printer-add wizard, Bambu-Cloud firmware check |
| Per-device firmware | `GET /api/v1/cloud/firmware-updates` | Cloud-side firmware check (different from the LAN-only path in [Firmware Updates](firmware-updates.md)) |
| Filament-id → name resolution | `POST /api/v1/cloud/filament-info` | AMS tray tooltips, K-profile filament labels |
| Built-in filament fallback table | `GET /api/v1/cloud/builtin-filaments` | Used when cloud + local both miss the ID |

Custom (private) presets land first in the list, public (built-in) presets after. The slicer-presets unifier (`/slicer/...`) merges these with [Local Profiles](local-profiles.md) by name and surfaces a single deduplicated list to the slice modal.

---

## :material-pencil: CRUD on cloud presets

Cloud Profiles isn't read-only:

| Action | Endpoint | Effect |
|---|---|---|
| **Create** | `POST /api/v1/cloud/settings` | Creates a new preset on Bambu Cloud — inherits from a base, stores only the diff |
| **Update** | `PUT /api/v1/cloud/settings/{id}` | Renames or updates the setting JSON |
| **Delete** | `DELETE /api/v1/cloud/settings/{id}` | Removes the preset from Bambu Cloud — cannot be undone |

The field-definition catalog at `GET /api/v1/cloud/fields/{filament|process|printer}` powers the form — it tells the UI which keys exist for each type, their label, units, validation bounds, and dropdown options.

---

## :material-shield-key: Permissions & encryption

| Permission | Grants |
|---|---|
| `cloud:auth` | Sign in / out, list / inspect / create / update / delete cloud presets, read connection status |
| `printers:read` | List bound cloud devices (`/cloud/devices`) |
| `firmware:read` | Read cloud-side firmware status (`/cloud/firmware-updates`) |
| `inventory:read` | Read filament-info / built-in filament fallback (used to label AMS tray tooltips) |

Default groups grant `cloud:auth` to **Administrators** and **Operators**; **Viewers** don't get it (read-only users shouldn't be writing tokens to anyone's account).

### At-rest encryption

When the install has `MFA_ENCRYPTION_KEY` set (Fernet key), TOTP secrets and other MFA cluster fields are encrypted at rest. The Bambu Cloud token field is **not** Fernet-encrypted today — it's stored as a plain `String(500)` on the `users` row. If you need encryption-at-rest for it, run BamDude on an encrypted database volume; the token doesn't leak through API responses (only the auth-status flag, email, and region are surfaced).

---

## :material-power-plug: Headless / API key access

API keys created in BamDude can call the cloud routes the same way they call any other route. Grant `can_read_status` if the key needs to read presets / devices, and the standard `X-API-Key` header rules apply (see [API Keys](api-keys.md)).

UI-created API keys are **stamped with the creating user's id**, so the cloud-side calls run against that user's per-user Bambu Cloud token — provided the key has the **Use Bambu Cloud** toggle ticked at create time. Without that opt-in flag, `cloud:*` routes refuse the call rather than silently spending the owner's cloud token. Pre-0.4.3 ownerless keys (the "Legacy" badge in the API-keys list) cannot be promoted to cloud-spend — the toggle is rejected at save time on rows without `user_id`. To migrate, re-create the key under your user account.

For setups without per-user Bambu Cloud (single-user / auth-disabled), the global Settings-table cred bag is the natural store and Cloud-flagged keys still fall through to it as a last resort.

---

## :material-help-circle: Troubleshooting

??? question "Login returns `Invalid credentials` but the same password works in Bambu Studio"
    Region mismatch is the usual cause — picking **Global** when the account is registered on the China backend (or vice versa) returns generic auth failures, not a friendly "wrong region" hint. Toggle the region dropdown and retry.

??? question "TOTP code rejected"
    Clock drift. Open your phone's settings → Date & time → enable Network-provided time. TOTP windows are 30 s, anything over a minute of drift will reject every code. Re-enrol in your authenticator app if the drift is persistent.

??? question "Connected, but the preset list is empty"
    Two common causes. **(1)** You signed into a sub-account that has no presets — log out and back in with the parent account. **(2)** The slicer-presets cache is stale; the slice-modal will repopulate it on the next open (5-minute TTL) or you can force-reopen the modal.

??? question "Status shows Disconnected after a week"
    Token expired or revoked server-side. Run the sign-in flow again. If this keeps happening on the same account, Bambu Cloud is forcing re-auth — the access-token paste flow lasts longer for some accounts than the email/password flow.

??? question "Other users see my cloud presets"
    They shouldn't — `cloud_token` is stored on `users.{your-id}` and the `/cloud/*` route handlers always pull `current_user.cloud_token`. If you actually see this, you're running with auth disabled (where everyone shares the global Settings cred bag) — enable auth and each user gets their own token.

??? question "China region — login works but presets won't load"
    The TOTP verification has to hit `bambulab.cn`'s TFA endpoint, not `bambulab.com`'s. BamDude routes by the `region` field on the verify call — make sure the region you picked at login matches what the verify dialog sends.
