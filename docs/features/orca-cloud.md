---
title: Orca Cloud
description: Per-user Orca Cloud pairing (OrcaSlicer's profile sync) via a device code, alongside Bambu Cloud
---

# Orca Cloud

Orca Cloud is the bridge between your [OrcaSlicer](https://github.com/SoftFever/OrcaSlicer) cloud account and BamDude. It sits **beside** [Cloud Profiles](cloud-profiles.md) (Bambu Cloud) — you can connect to one, both, or neither. Once signed in, your OrcaSlicer filament / process / printer profiles become visible inside the slice modal and the AMS-slot family picker, in their own preset tier beside local imports and Bambu Cloud presets.

OrcaSlicer 2.4.0-alpha added a Supabase-backed cloud sync (`sync_pull`). BamDude reads that same store, so profiles you curate in OrcaSlicer show up here without re-importing anything.

The integration is **per-user**. Each BamDude account holds its own Orca Cloud token — signing in doesn't touch anyone else's account.

Since 0.5.5, BamDude pairs under its **own registered app identity**, issued by the Orca Cloud team — the approval card names BamDude (and your instance URL), and you can find and disconnect it in your Orca Cloud connected-apps list under its real name. The pairing requests **write access** (`sync:write`, which includes read), powering the [profile push](#pushing-profiles) below.

!!! warning "Upgrading to 0.5.5: re-pair once"
    The app identity and the granted scope are baked into the issued tokens, and **both changed together** in 0.5.5 — every existing Orca Cloud pairing stops working after the upgrade and asks to be reconnected. One re-pair covers both changes; nothing else is lost.

---

## :material-tab: Where it lives

**Profiles → Orca Cloud** — a tab next to **Bambu Cloud**, **Local Profiles**, and **K-Profiles**. The tab shows the connection state, a sign-in panel when disconnected, and the same rich layout as the Bambu Cloud view (search + filter dropdowns + grouped grid + read-only detail modal) once connected.

---

## :material-login: Sign-in — device pairing

Pairing uses the **OAuth 2.0 Device Authorization Grant** (RFC 8628) — the
flow made for an app that cannot receive a browser redirect, which is exactly
what a self-hosted server is:

1. Click **Connect** on the **Connect to Orca Cloud** panel
2. BamDude shows a short **user code** and a verification link
3. Open the link (any device, any browser), sign in to your Orca account and
   approve the code in your Orca Cloud settings — the card shows **BamDude**,
   your instance URL and the requested permissions
4. BamDude polls in the background and flips to **Connected** the moment the
   approval lands

A pairing attempt expires on its own after a few minutes — click Connect
again to start a fresh one. No URL pasting, no localhost callback: the old
paste-based PKCE flow this replaced is gone.

## :material-clock-end: Token lifetime & refresh

Unlike Bambu Cloud's long-lived bearer, Orca pairing tokens are short-lived
and rotate:

| Token | Lifetime | Notes |
|---|---|---|
| Access token | ~24 hours | Used for every API call |
| Refresh token | ~90 days, rotating, single-use | Each refresh returns a **new** refresh token and renews the 90 days; the old one is spent |

BamDude refreshes the access token **just-in-time** — when a call is about to
run on an expiring token it rotates first and **persists the new pair before
making the API call**, so a crash mid-refresh can't strand you with a spent
token. If the refresh itself is rejected (revoked server-side), your status
flips to **Disconnected** and you pair again.

## :material-database-search: What gets pulled

Once connected, Orca Cloud profiles feed the same surfaces as Bambu Cloud:

| Surface | How Orca profiles appear |
|---|---|
| Slice modal | A fourth preset tier, `orca_cloud`, ranked **above** local / Bambu Cloud / standard |
| AMS-slot family picker | Orca custom filaments are first-class [families](filament-families.md) — mirrored server-side into the family catalog alongside Bambu Cloud's, badge and all; the printer receives the family id, or the generic family of the material on printers without user-preset support |
| Profiles → Orca Cloud tab | Grouped printer / process / filament grid with search + filters + a read-only detail modal |

Orca's `sync_pull` returns each profile's **full content inline**, so — unlike Bambu Cloud, where filament type/colour need a separate per-preset fetch that hits a rate limit — Orca filaments carry their `filament_type` and colour for free. The slice modal's metadata-aware pre-pick uses that to rank Orca filaments accurately without extra round-trips.

!!! note "Slice tier priority"
    `local` > `orca_cloud` > `cloud` (Bambu) > `standard`. There is deliberately **no cross-tier dedup**: every tier surfaces its full list, so the same name may appear in several groups and you pick the source. Each cloud tier also has its **own** status banner in the slice modal — Bambu and Orca can be signed-out / expired / unreachable independently.

---

## :material-cloud-upload: Pushing profiles { #pushing-profiles }

With a write-scoped pairing, [authored filament families](filament-families.md) can be **pushed to Orca Cloud** — the same way they push to Bambu Cloud, from the same places:

- creating a family with *"Also push to Orca Cloud"* (or creating it straight into the cloud from **Profiles → Orca Cloud → Create filament**);
- the **Authored families** block under **Profiles → Local**: push or re-push a family to either cloud, see per-cloud state (pushed / edited since push / not pushed), and delete a family together with its pushed cloud copies.

An edit in BamDude never overwrites the cloud silently — the preset is marked as changed and waits for an explicit **re-push**. And the respect runs both ways: if a profile was edited in Orca Cloud (say, from OrcaSlicer) after your last push, BamDude detects it **before writing anything** and asks, per preset:

- **Overwrite cloud copy** — your local version wins;
- **Adopt cloud version** — the cloud content is taken into your local preset.

A pairing made without write access (an env-pinned `sync:read`, or a pre-0.5.5 pairing that somehow survived) shows the push controls disabled with an explanation — reconnect to grant writing.

## :material-shield-key: Permissions

| Permission | Grants |
|---|---|
| `orca_cloud:auth` | Sign in / out of Orca Cloud, list / inspect profiles, read connection status, and slice using Orca presets |

Default groups grant `orca_cloud:auth` to **Administrators** and **Operators**; **Viewers** don't get it.

For API keys, `orca_cloud:auth` folds into the same **Use Bambu Cloud** (`can_access_cloud`) scope as `cloud:auth` — it's the same trust dimension (third-party cloud access on the owner's behalf), so a key already cleared for cloud access covers Orca too.

Pushing a filament family (to either cloud) rides the `cloud:auth` permission — the push button and the create-dialog checkboxes follow it.

### At-rest encryption

Like the Bambu Cloud token, the Orca access + refresh tokens are stored as plain strings on the `users` row (migration **m090** adds `orca_cloud_token`, `orca_cloud_refresh_token`, `orca_cloud_expires_at`, `orca_cloud_email`, `orca_cloud_user_id` + three transient PKCE columns). Migration **m154** adds `orca_cloud_scope` — the scope actually granted at pairing, which is what gates the push controls. They aren't Fernet-encrypted today — run BamDude on an encrypted database volume if you need encryption-at-rest. The tokens never leak through API responses (only the connected flag, email, user id and granted scope are surfaced).

---

## :material-help-circle: Troubleshooting

??? question "The pairing code expired before I approved it"
    A pairing attempt is short-lived by design. Click **Connect** again — a
    fresh code costs nothing, and nothing about the old attempt lingers.

??? question "Connected, but no profiles show"
    You may not have synced any profiles from OrcaSlicer yet — Orca Cloud only mirrors what you've pushed from the slicer. Curate a profile in OrcaSlicer, let it sync, then hit **Refresh** on the Orca Cloud tab (5-minute listing cache).

??? question "Status flipped to Disconnected on its own"
    A refresh-token rotation was rejected server-side (revoked, or the single-use token was replayed). Pair again from the Orca Cloud tab.

??? question "After updating BamDude it asked me to reconnect Orca Cloud"
    Expected, once: 0.5.5 switched to BamDude's own app identity and the write
    scope, and both are baked into the issued tokens. Pair again and it stays.

??? question "The push buttons are disabled and say the pairing is read-only"
    The granted scope is fixed at pairing time. Disconnect and pair again — the
    new pairing requests write access (unless your deployment pins
    `ORCA_CLOUD_SCOPE=sync:read`, in which case that's the reason).

??? question "Orca and Bambu presets have the same name — which wins?"
    Neither silently: every tier surfaces its full list, so a shared name shows in both groups and you pick the source.
