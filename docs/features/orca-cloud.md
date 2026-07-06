---
title: Orca Cloud
description: Per-user Orca Cloud sign-in (OrcaSlicer's Supabase profile sync) with a paste-based PKCE flow, alongside Bambu Cloud
---

# Orca Cloud

Orca Cloud is the bridge between your [OrcaSlicer](https://github.com/SoftFever/OrcaSlicer) cloud account and BamDude. It sits **beside** [Cloud Profiles](cloud-profiles.md) (Bambu Cloud) — you can connect to one, both, or neither. Once signed in, your OrcaSlicer filament / process / printer profiles become visible inside the slice modal and the AMS-slot filament picker, ranked above local imports and Bambu Cloud presets.

OrcaSlicer 2.4.0-alpha added a Supabase-backed cloud sync (`sync_pull`). BamDude reads that same store, so profiles you curate in OrcaSlicer show up here without re-importing anything.

The integration is **per-user**. Each BamDude account holds its own Orca Cloud token — signing in doesn't touch anyone else's account.

---

## :material-tab: Where it lives

**Profiles → Orca Cloud** — a tab next to **Bambu Cloud**, **Local Profiles**, and **K-Profiles**. The tab shows the connection state, a sign-in panel when disconnected, and the same rich layout as the Bambu Cloud view (search + filter dropdowns + grouped grid + read-only detail modal) once connected.

---

## :material-login: Sign-in — the paste flow

Orca's Supabase project only allowlists a **localhost** `redirect_to` (`http://localhost:41172/callback`) — the address OrcaSlicer's own desktop agent listens on. A self-hosted BamDude on a different host can't receive that redirect, so sign-in uses a **paste-based PKCE** flow instead of a normal browser callback (tracked upstream as [OrcaSlicer/OrcaSlicer#14028](https://github.com/OrcaSlicer/OrcaSlicer/issues/14028)).

### OAuth (Google / Apple / GitHub)

1. Pick a provider on the **Connect to Orca Cloud** panel
2. A new browser tab opens `auth.orcaslicer.com`'s sign-in page. Sign in with your Orca account
3. Your browser is redirected to a `http://localhost:41172/callback?code=...&state=...` URL that **fails to load** — that is expected; the URL itself is what BamDude needs
4. Copy the **entire** URL from your browser's address bar and paste it into BamDude's **Paste the callback URL here** field
5. BamDude exchanges the `code` (with the PKCE verifier it kept from step 1) for tokens → status flips to **Connected**

!!! tip "If the sign-in tab didn't open"
    The panel shows the authorize URL as a clickable link — open it manually, then continue from step 3.

### Email + password

For accounts with an Orca email/password credential, the OAuth dance is skipped entirely: enter your Orca **email** + **password** and BamDude signs in directly against Supabase's `grant_type=password` endpoint.

---

## :material-clock-end: Token lifetime & refresh

Unlike Bambu Cloud's ~90-day bearer, Orca uses Supabase's short-lived tokens:

| Token | Lifetime | Notes |
|---|---|---|
| Access JWT | ~1 hour | Used for every API call |
| Refresh token | Rotating, single-use | Each refresh returns a **new** refresh token; the old one is spent |

BamDude refreshes the access token **just-in-time** — when a call is about to run and the token has less than ~5 minutes of life left, it rotates first and **persists the new refresh token before making the API call**, so a crash mid-refresh can't strand you with a spent token. If the refresh itself is rejected (revoked server-side), your status flips to **Disconnected** and you re-run sign-in.

The transient PKCE handshake state (verifier / state) lives only between **Connect** and the paste step, with a **10-minute TTL** — click Connect, walk away, and the half-finished handshake expires on its own.

---

## :material-database-search: What gets pulled

Once connected, Orca Cloud profiles feed the same surfaces as Bambu Cloud:

| Surface | How Orca profiles appear |
|---|---|
| Slice modal | A fourth preset tier, `orca_cloud`, ranked **above** local / Bambu Cloud / standard |
| AMS-slot filament picker | Orca filaments listed first (prefixed `orca_` internally); a generic Bambu filament-ID is derived from the parsed material so the printer firmware still recognises the type |
| Profiles → Orca Cloud tab | Grouped printer / process / filament grid with search + filters + a read-only detail modal |

Orca's `sync_pull` returns each profile's **full content inline**, so — unlike Bambu Cloud, where filament type/colour need a separate per-preset fetch that hits a rate limit — Orca filaments carry their `filament_type` and colour for free. The slice modal's metadata-aware pre-pick uses that to rank Orca filaments accurately without extra round-trips.

!!! note "Slice tier priority"
    `orca_cloud` > `local` > `cloud` (Bambu) > `standard`. A profile name that appears in a higher tier is filtered out of every lower one, so each name renders once. Each cloud tier also has its **own** status banner in the slice modal — Bambu and Orca can be signed-out / expired / unreachable independently.

---

## :material-shield-key: Permissions

| Permission | Grants |
|---|---|
| `orca_cloud:auth` | Sign in / out of Orca Cloud, list / inspect profiles, read connection status, and slice using Orca presets |

Default groups grant `orca_cloud:auth` to **Administrators** and **Operators**; **Viewers** don't get it.

For API keys, `orca_cloud:auth` folds into the same **Use Bambu Cloud** (`can_access_cloud`) scope as `cloud:auth` — it's the same trust dimension (third-party cloud access on the owner's behalf), so a key already cleared for cloud access covers Orca too.

### At-rest encryption

Like the Bambu Cloud token, the Orca access + refresh tokens are stored as plain strings on the `users` row (migration **m090** adds `orca_cloud_token`, `orca_cloud_refresh_token`, `orca_cloud_expires_at`, `orca_cloud_email`, `orca_cloud_user_id` + three transient PKCE columns). They aren't Fernet-encrypted today — run BamDude on an encrypted database volume if you need encryption-at-rest. The tokens never leak through API responses (only the connected flag, email, and user id are surfaced).

---

## :material-help-circle: Troubleshooting

??? question "The localhost URL just shows a connection error — did sign-in fail?"
    No — that's the expected behaviour. Nothing is listening on `localhost:41172` on your machine (that's OrcaSlicer's desktop agent, which you aren't running). The failed page still has the `code` + `state` in its address bar, which is all BamDude needs. Copy the full URL and paste it.

??? question "\"That URL does not look like an Orca Cloud callback\""
    The pasted URL has no `code` parameter. Make sure you copied the **whole** address after the redirect (the `http://localhost:41172/callback?...` one), not the Orca sign-in page URL.

??? question "Connected, but no profiles show"
    You may not have synced any profiles from OrcaSlicer yet — Orca Cloud only mirrors what you've pushed from the slicer. Curate a profile in OrcaSlicer, let it sync, then hit **Refresh** on the Orca Cloud tab (5-minute listing cache).

??? question "Status flipped to Disconnected on its own"
    A refresh-token rotation was rejected server-side (revoked, or the single-use token was replayed). Re-run sign-in. Because refresh tokens are single-use, signing into the same Orca account from two places can invalidate one of them.

??? question "Orca and Bambu presets have the same name — which wins?"
    Orca. The slice modal de-duplicates by name across tiers with `orca_cloud` at the top, so a shared name renders only in the Orca tier.
