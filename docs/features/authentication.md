---
title: Authentication
description: Always-on authentication with MFA, OIDC SSO, refresh-token sessions, and group-based permissions
---

# Authentication

BamDude ships with always-on authentication: every API endpoint is protected, the first boot walks you through creating an admin, and from there users sign in with passwords, optional 2FA, or OIDC single sign-on. This page is the single source of truth for the auth stack -- groups, sessions, MFA, SSO, rate limits, and recovery.

---

## :material-lock: Overview

- **User accounts** -- multiple users with unique credentials and per-user MFA settings.
- **Group-based permissions** -- 80+ granular `resource:action` permissions, three default groups (Administrators / Operators / Viewers), arbitrary custom groups.
- **Sliding-session JWTs** -- 1 hour access tokens, transparently refreshed via an HttpOnly rotating cookie so users don't get bounced mid-session.
- **Multi-factor authentication** -- TOTP (authenticator apps), email OTP, and 10 single-use backup codes.
- **OIDC / SSO** -- authorization-code flow with PKCE for any standards-compliant provider (Authentik, Keycloak, Pocket-ID, Google Workspace, ...).
- **Rate limiting** -- per-username and per-IP sliding-window buckets on login + forgot-password.
- **Setup-gate + admin recovery** -- fresh installs walk through a one-time setup; lost-all-admins is recoverable via a CLI without losing data.

!!! info "Auth is always on"
    There is no "disable auth" toggle. Every endpoint requires a valid session or API key. API keys (`X-API-Key` or `Authorization: Bearer bb_...`) bypass JWT validation but still satisfy the same permission checks.

---

## :material-rocket-launch: First-Boot Setup

On its very first boot BamDude knows it has no admin yet, so it locks down the API and shows a setup form.

1. Open the BamDude UI. The setup wizard is rendered automatically.
2. Enter the initial admin's **username**, **password**, and (optional) **email**.
3. Submit. Setup-gate flips off; you are redirected to the regular login page and signed in.

While the setup gate is up, only three endpoints respond:

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/auth/status` | Is setup needed? Used by the UI to pick login vs setup. |
| `POST /api/v1/auth/setup` | Create the initial admin. |
| `GET /api/v1/system/health` | Liveness probe. |

Every other call returns `503 {"detail": "setup_required"}` until setup completes.

!!! warning "Don't expose a fresh container"
    The setup endpoint is unauthenticated by design (there is no admin yet to authenticate against). Only expose port 8000 publicly **after** you've completed setup, or run setup over a private network first.

---

## :material-account-group: Default Groups

| Group | Description | Permissions |
|-------|-------------|-------------|
| **Administrators** | Full access | All permissions |
| **Operators** | Control printers and manage content | Printer control, queue, archives, library |
| **Viewers** | Read-only access | View printers, archives, queue |

Custom groups can mix and match permissions. Newly OIDC-linked users land in **Viewers** by default (configurable per provider).

---

## :material-key: Permission Categories

Permissions follow a `resource:action` pattern -- e.g. `printers:control`, `archives:read`. Endpoints declare the permission they need with `RequirePermission(...)` so the matrix is enforced consistently across REST, WebSocket, and Telegram surfaces.

- **Printers** -- `printers:read`, `printers:create`, `printers:update`, `printers:delete`, `printers:control`, `printers:files`, `printers:ams_rfid`, `printers:clear_plate`
- **Archives** -- `archives:read`, `archives:create`, `archives:update_own` / `archives:update_all`, `archives:delete_own` / `archives:delete_all`, `archives:reprint_own` / `archives:reprint_all`
- **Queue** -- `queue:read`, `queue:create`, `queue:update_own` / `queue:update_all`, `queue:delete_own` / `queue:delete_all`, `queue:reorder`
- **Library** -- `library:read`, `library:upload`, `library:update_own` / `library:update_all`, `library:delete_own` / `library:delete_all`, `library:purge` (skip trash, hard-delete immediately)
- **Inventory** -- `inventory:read`, `inventory:create`, `inventory:update`, `inventory:delete`, `inventory:view_assignments`
- **Cloud** -- `cloud:auth` (per-user Bambu Cloud sign-in + cloud-profile CRUD; no `settings:read` needed)
- **Settings** -- `settings:read`, `settings:update`, `settings:backup`, `settings:restore`
- **Notifications** -- `notifications:read`, `notifications:update`, `notifications:user_email` (gates the per-user email opt-in page)
- **Stats** -- `stats:read`, `stats:filter_by_user` (filter dashboards by `started_by` / `uploaded_by`)
- **Users / Groups** -- `users:read`, `users:create`, `users:update`, `users:delete`, `groups:read`, `groups:create`, `groups:update`, `groups:delete`

!!! tip "Ownership permissions"
    Use `*_own` permissions for users who should only modify their own uploads and queue items. Operators typically get `*_all`; Viewers get neither. `*_all` always implies `*_own`.

!!! tip "Cloud profiles are per-user"
    Each user has their own Bambu Cloud login -- signing in as User A doesn't affect User B's session. The single `cloud:auth` permission covers login, logout, and all cloud-profile CRUD; `settings:read` is **not** required.

!!! tip "Inventory vs AMS-assignment visibility"
    `inventory:view_assignments` shows what's loaded in each AMS slot on the Printers page **without** exposing the full inventory. Grant it on its own to operators who need to verify spool-to-slot mapping at a glance but shouldn't see purchase history, lot codes, or stock levels.

### Ownership semantics: `*_own` vs `*_all`

| Permission shape | Effect |
|---|---|
| `archives:delete_own` | Delete only archives **you uploaded / started**. |
| `archives:delete_all` | Delete any archive, including ownerless ones. Implies `*_own`. |
| `queue:update_own` | Edit only queue items you added. |
| `library:update_all` | Rename / move / delete any library file. |

**Ownerless items.** Some content has no owner -- e.g. archives created before authentication existed, prints triggered by an auto-virtual-printer, or webhook-uploaded library files. These require `*_all` to modify; users with only `*_own` see them as read-only.

Users in multiple groups inherit the **union** of all groups' permissions -- assignments are additive, not least-privilege-min.

---

## :material-account-multiple-plus: User Management

**Settings -> Users -> Users tab.** Visible to anyone with `users:read`; mutating actions need `users:create` / `users:update` / `users:delete`.

### Creating users

1. Click **Add User**.
2. Fill in **Username**, **Password** (subject to the password policy), **Confirm password**, and tick one or more **Groups**.
3. (Optional) Add an **Email** -- required for email OTP, password-reset by mail, and per-user print notifications.
4. **Create**. The new user can sign in immediately.

When [Advanced Auth via Email](#advanced-auth-via-email) is enabled, the password field is **replaced** with an email field: BamDude generates a secure random password and mails it directly to the user. No admin ever sees the password, which is strictly stronger than handing one over in chat.

### Editing users

Click the pencil on a user row. Username, email, password, and group memberships are all editable. Saving a password change stamps `password_changed_at`, killing every existing session for that user.

### Deleting users

Click the trash icon. If the user owns content (archives, queue items, library files, started prints), BamDude prompts for the disposition:

| Choice | Effect |
|---|---|
| **Delete user AND their items** | Hard-deletes archives, queue items, library files, and any other owned content. Cascades. |
| **Delete user, keep items** | Removes the user; their content becomes ownerless and only `*_all` holders can modify it afterwards. Activity-tracking history (e.g. "Started by alice") is preserved -- the username is shown as-recorded, even though the user row is gone. |
| **Re-assign to admin** | Transfers ownership of every owned row to the chosen admin in one transaction. Useful for offboarding employees. |

You cannot delete yourself, and you cannot delete the last administrator -- the UI greys those out with a tooltip explaining why.

---

## :material-account-group-outline: Group Management UI

**Settings -> Users -> Groups tab.** Each group shows its name, description, and a per-category count badge ("Printers 7/8", "Archives 9/9") so you can eyeball coverage at a glance.

Click **Add Group** (or pencil on an existing group) to open the **full-page group editor**:

- **Search bar** filters the permission grid live by permission name or description.
- **Select all** / **Clear all** bulk-toggle every checkbox at once.
- **Category checkboxes** at each section header toggle every permission in that category in one click.
- Per-category **count badges** ("5/7") update as you tick boxes.
- Description supports plain text -- write what you actually intend the group to do, future-you will be grateful.

System groups (Administrators / Operators / Viewers) cannot be deleted, but their permission sets are editable. Custom groups can be deleted at any time; users in only that group end up group-less and lose all permissions until reassigned.

---

## :material-email-fast: Advanced Auth via Email

Optional SMTP layer that enables passwordless onboarding, self-service password reset, and per-user print notifications. Toggle independently of basic auth.

### Configure SMTP

**Settings -> Email tab.**

| Field | Notes |
|---|---|
| **SMTP host** | e.g. `smtp.gmail.com`, `smtp.fastmail.com`, your self-hosted Postfix. |
| **SMTP port** | `587` for STARTTLS (most common), `465` for implicit TLS. |
| **Use STARTTLS** | On by default for port 587. Off for 465 (already TLS). |
| **Username / password** | App-specific password recommended for Gmail / Fastmail / Apple. |
| **From address** | Sender address shown to recipients. Some providers require it to match the auth user. |
| **External URL** | The reachable URL of your BamDude instance -- baked into reset / welcome email links. Has to actually resolve from the user's browser. |

Click **Test email** before flipping the toggle on -- it sends a one-shot to your own admin address and surfaces the SMTP error verbatim if anything's wrong.

### Built-in templates

Editable under **Settings -> Email -> Templates**:

- **Welcome** -- new account with auto-generated password
- **Password reset** -- self-service or admin-triggered, includes one-time token (defaults to 1-hour expiry)
- **Two-Factor code** -- email OTP delivery
- **Printer error** -- per-user mail when their print errors out
- **Print complete / failed / stopped** -- per-user lifecycle mails

Templates are i18n-aware (en + uk); each template carries a subject line and a body with substitution variables like `{username}`, `{printer_name}`, `{archive_url}`.

### Self-service password reset flow

1. User clicks **Forgot your password?** on the login page.
2. Enters username or email. Endpoint returns success either way (anti-enumeration), but only mails the link if the address exists.
3. Email contains a one-shot token URL valid for 1 hour. Token is single-use.
4. User clicks, sets a new password (subject to the password policy), and is signed in.

Admins can also fire the same flow with one click from the Users page -- handy when a team-mate's authenticator just died and they're locked out of TOTP-protected reset.

### Per-user email notifications

When Advanced Auth is on, individual users gate notifications **for their own jobs** under **Notifications** in the sidebar. The toggle list:

- **Print started** -- email when one of your jobs begins
- **Print completed** -- success
- **Print failed** -- HMS error / cancelled
- **Print stopped** -- manual cancel

Requires the user to have an email address on file and the `notifications:user_email` permission (default for Administrators + Operators, off for Viewers). This is **independent** of the global notification system -- it only mails the submitter, not the whole farm.

---

## :material-server-network: LDAP / Active Directory

BamDude supports LDAP authentication for environments running Active Directory, FreeIPA, or OpenLDAP. Local accounts coexist with LDAP -- the local admin always works as a fallback if the directory is unreachable.

### Configure

**Settings -> Authentication -> LDAP tab.**

| Field | Notes |
|---|---|
| **Server URL** | `ldaps://ad.example.com:636` (LDAPS) or `ldap://ad.example.com:389` (StartTLS). Plaintext LDAP without StartTLS is rejected -- credentials must be encrypted on the wire. |
| **Security** | StartTLS (upgrade plain to TLS on port 389) or LDAPS (TLS from byte one on port 636). |
| **Bind DN** | Service-account DN used to search for users (e.g. `CN=bamdude-svc,OU=Service,DC=example,DC=com`). |
| **Bind password** | Service-account password. Stored encrypted at rest when `MFA_ENCRYPTION_KEY` is set. |
| **Search base** | Where to look (e.g. `OU=Users,DC=example,DC=com`). |
| **User filter** | LDAP filter; `{username}` is substituted at login. AD: `(sAMAccountName={username})`. OpenLDAP / FreeIPA: `(uid={username})`. |

Click **Test connection** before flipping **Enable LDAP** -- it does a dry-run bind + search and shows the raw error if anything's misconfigured.

### Group mapping

Map directory groups to BamDude groups via a JSON object:

```json
{
  "BamDudeAdmins": "Administrators",
  "BamDudeOps": "Operators",
  "BamDudeViewers": "Viewers"
}
```

Keys are LDAP group `cn` values (case-insensitive); values are BamDude group names. Both AD-style `memberOf` and POSIX-style `memberUid` are supported. Group membership is **re-synced on every login** -- demoting a user in AD takes effect at most one BamDude login later.

If no mapping is configured, LDAP users are auto-provisioned with no group memberships and have to be assigned manually.

### Provisioning

| Toggle | Effect |
|---|---|
| **Auto-provision** | On = first successful LDAP login auto-creates a local row tagged `auth_source=ldap`. Off = admins must pre-create the user first via the **LDAP** tab in the Create User modal (see below); unknown LDAP usernames are rejected on login. |
| **Sync email on login** | The user's email attribute is overwritten from LDAP on every login (so AD changes propagate). |

LDAP-provisioned users show an **LDAP** badge in the Users list. Their **Change password** button is hidden -- passwords live at the directory, not in BamDude. Admin-triggered password resets and self-service forgot-password are blocked for LDAP accounts with a clear "managed by LDAP" message.

### Manual onboarding (LDAP tab)

When LDAP is enabled, the **Create User** modal in Settings → Users gains a **Local / LDAP** tab toggle. The LDAP tab is a debounced directory search (≥2 chars) that returns up to 25 matches via the service-account bind. Each row shows the directory's `displayName` / email / DN and is annotated **Already provisioned** for usernames that already exist as BamDude users (so a duplicate-click is impossible). Picking one and clicking **Provision user** re-resolves the username via the service bind and creates the BamDude row through the same code path the auto-provision login uses — group mapping, default-group fallback, and email sync apply identically.

Use this when **Auto-provision** is off but you still want to pre-create directory users one at a time without hand-editing the database.

Permission required: `users:create` (admin by default).

### Local admin fallback

The local admin account always works regardless of LDAP status. If the directory server is down, LDAP logins fail with a clear "directory unreachable, retry or use local account" message; the local admin can still sign in and unblock things. **Do not delete the last local admin** -- that's your get-out-of-jail-free if AD ever goes sideways.

If a local user and an LDAP user share a username, **the local account wins** -- LDAP cannot silently override an existing local row.

---

## :material-account-eye: User Activity Tracking

When you act under an authenticated session, BamDude records who did what and surfaces it on cards across the UI:

| Activity | Where it shows |
|---|---|
| Library file uploaded | "Uploaded by *username*" badge on the file card. |
| Archive created from a print | "Started by *username*" on the archive card + detail page. |
| Queue item added | Username next to the queue row. |
| Print started (auto-dispatch / cloud / external) | Tracked when the trigger had an authenticated user; shows on the printer card during the active print. |

Tracking is automatic -- there is no privacy toggle. Historical attribution is **preserved** even when a user is later deleted (the username is rendered as-recorded, but no longer clickable). For team auditing add `stats:filter_by_user` to operator groups so they can pivot dashboards by `started_by` / `uploaded_by`.

---

## :material-package-down: Backup & Restore

Users and groups are included in the standard backup if you tick **Include users** and **Include groups** at backup time:

- **Group definitions + memberships are preserved** in full.
- **Passwords are NOT included** -- backups only carry username + email + group memberships, never the PBKDF2 hash. This is intentional: a leaked backup file shouldn't equal leaked credentials.
- On restore, every user has an empty password. Admins must:
  - Set passwords manually for each restored user (Users page -> Edit), **or**
  - With Advanced Auth enabled, hit **Reset password** on each user to mail them a fresh password, **or**
  - Direct users to the **Forgot password?** flow if SMTP is configured.
- TOTP secrets and OIDC bindings **are** included (encrypted at rest if `MFA_ENCRYPTION_KEY` is set on both source and destination).
- API keys are NOT included -- regenerate them on the new install.

Plan the rollover during a maintenance window so users can re-set passwords without a queue of confused tickets.

BamDude uses a sliding-session model: short-lived access tokens, long-lived rotating refresh cookie.

### Access tokens

- **TTL:** 1 hour (was 24 h pre-0.4.0).
- **Carry `jti` + `iat`.** Logout revokes the token's `jti` until natural expiry; password changes stamp `users.password_changed_at`, and tokens older than that timestamp are rejected as stale on every request.

### Refresh tokens

- Issued by `/auth/login`, `/auth/2fa/verify`, and `/auth/oidc/exchange`.
- Stored as a SHA-256 hash in `auth_ephemeral_tokens`; delivered to the browser as the `bamdude_refresh` cookie -- **HttpOnly**, **SameSite=Lax**, **Path=/api/v1/auth**. JavaScript never sees it; non-auth endpoints never receive it.
- **Rotated on every use.** `POST /auth/refresh` marks the old row `used_at=now`, mints a new row in the same `family_id`, and returns a fresh access token.
- **OWASP reuse detection.** If a refresh token is replayed (i.e. used twice), BamDude collapses the entire family across every device. The user is forced back to the login page everywhere.
- **Logout / password change / admin-initiated MFA reset** revoke ALL refresh tokens for the user, signing out every device.

### Remember-me

The login form has a **"Remember me for 30 days"** checkbox.

| Mode | DB row TTL | Cookie lifetime |
|------|------------|-----------------|
| Default | 12 hours | Session cookie (cleared when browser closes) |
| Remember me | 30 days | `Max-Age=30d` -- survives browser restarts |

### Frontend behaviour

The frontend `request()` helper transparently retries 401s through `/auth/refresh`, **promise-coalesced** so a wave of parallel queries spawns exactly one refresh call. If refresh also fails, a global `bamdude:auth-invalidated` event clears React state and hard-redirects to `/login`. A visibility-change listener proactively revalidates `/auth/me` when a hidden tab regains focus.

### `Secure` cookie attribute

`Secure` is auto-detected from the request scheme. Behind a reverse proxy, set `TRUSTED_PROXY_IPS` (comma-separated) so BamDude reads the original `X-Forwarded-Proto` header.

```ini
# .env
TRUSTED_PROXY_IPS=10.0.0.1,10.0.0.2
```

For edge cases (e.g. TLS-terminating load balancer that doesn't set `X-Forwarded-Proto`), force the polarity:

=== "Force Secure on"

    ```ini
    AUTH_REFRESH_COOKIE_SECURE=true
    ```

=== "Force Secure off"

    ```ini
    AUTH_REFRESH_COOKIE_SECURE=false
    ```

---

## :material-shield-key: Multi-Factor Authentication

2FA is per-user opt-in. Each user can enrol one or more factors from **Settings -> Profile -> Two-Factor Authentication**.

### Factors

| Factor | How it works |
|--------|--------------|
| **TOTP** | Authenticator app (Google Authenticator, Aegis, Authy, 1Password, ...). Six-digit rolling code, generated from a Fernet-encrypted secret. |
| **Email OTP** | One-time code sent to the user's email. Useful as a fallback when TOTP isn't practical. |
| **Backup codes** | 10 single-use codes generated at enrolment. Shown **once** -- store them offline. Re-generate anytime to invalidate the old set. |

### Login flow with 2FA

1. User submits username + password.
2. Server verifies credentials, returns `requires_2fa=true`, a short-lived `pre_auth_token`, and a 2fa-challenge cookie.
3. UI shows the 2FA picker (TOTP / email / backup code).
4. User submits the code to `/auth/2fa/verify`.
5. Server returns the access JWT + sets the refresh cookie. Login complete.

### Encryption at rest

TOTP secrets and OIDC client secrets are Fernet-encrypted in the database. Backup codes are pbkdf2-hashed regardless. **As of 0.4.4, encryption is on by default** -- BamDude bootstraps a key automatically on first start, so a fresh install never silently writes plaintext secrets.

**Key resolution order** (first hit wins):

1. `MFA_ENCRYPTION_KEY` environment variable -- the explicit pin (recommended for multi-host or multi-worker deployments where one key has to be shared).
2. `DATA_DIR/.mfa_encryption_key` file (mode `0o600`) -- single-host installs typically end up here.
3. Auto-generated -- on first boot, BamDude creates a fresh Fernet key and writes it to `.mfa_encryption_key`. Atomic create with `O_EXCL` so the mode bits are right from the first byte; never world-readable.

```ini
# .env (optional -- only set this when you want to pin a specific key)
MFA_ENCRYPTION_KEY=<base64 32-byte Fernet key>
```

!!! tip "Generate a key"
    `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`

!!! info "Status panel"
    **Settings → Authentication → Security** surfaces a live status card with five severity levels:

    - 🟢 **Green** -- key configured, every secret encrypted.
    - 🟡 **Amber** -- legacy plaintext rows still exist (will be re-encrypted on next write) **or** the key was auto-generated (back up `DATA_DIR/.mfa_encryption_key` so a future restore on a fresh host can decrypt secrets).
    - 🔴 **Red** -- decryption broken (key configured but cannot decrypt existing rows -- happens after a key rotation or a cross-deployment restore where the running install holds the wrong key). Recovery: restore the original key file or re-enrol affected users.
    - ⚫ **Grey** -- not configured at all and no encrypted rows exist.

!!! warning "Backup integration"
    `.mfa_encryption_key` is bundled into the backup ZIP alongside `bamdude.db`. Restore on a fresh host extracts the key **before** the database swap with `chmod 0o600` -- so a self-contained backup keeps access to encrypted secrets without manual intervention. The restore aborts with a clear 500 if the key write fails (RO disk / EACCES) before the DB is replaced, so a live install can never end up with the wrong-key combination.

!!! note "Legacy install upgrade path"
    Pre-0.4.4 installs that ran with `MFA_ENCRYPTION_KEY` unset have plaintext rows in the database. On the next startup after the upgrade, the auto-bootstrap generates a key and a one-shot migration re-encrypts those rows in place. Per-row transactions: a single corrupt row doesn't block the others, and the skipped count is surfaced on the status card so you can spot poison rows that need attention.

### Admin-initiated reset

If a user loses their authenticator device, an admin can trigger a 2FA reset for that user from the Users page. The reset disables all factors **and revokes every refresh token** for that account, so any logged-in session is killed -- the user signs in fresh with just a password and re-enrols.

---

## :material-account-key: OIDC / SSO

BamDude supports OpenID Connect single sign-on against any standards-compliant provider.

### Configure a provider

**Settings -> Authentication -> OIDC Providers -> Add provider.**

| Field | Notes |
|-------|-------|
| **Display name** | Label on the login button ("Sign in with Authentik"). |
| **Issuer URL** | The provider's discovery URL base (e.g. `https://auth.example.com/`). Must be HTTPS. |
| **Client ID** | From the provider's BamDude app registration. |
| **Client secret** | Fernet-encrypted at rest when `MFA_ENCRYPTION_KEY` is set. |
| **Scopes** | Default `openid profile email`. Add provider-specific scopes if needed. |
| **Claim mapping** | Which OIDC claim maps to BamDude username / email. |
| **Auto-create users** | Off by default -- new logins must match an existing local user by email. On = auto-create the user automatically (placed in the group set by **Default group** below). |
| **Default group** | Group new auto-created users land in. Defaults to **Viewers (read-only)** for safety; pick a custom group for tenant-internal SSO setups where read-only is too restrictive. The picker is sourced from the live group list, so any custom group you create in **Settings → Authentication → Groups** is selectable here. If the chosen group is later deleted, new logins fall back to **Viewers**. |

The login page renders an "Sign in with `<provider>`" button per configured provider, below the password form.

### Hardening

- **PKCE S256** -- mandatory, non-negotiable.
- **State + nonce** -- both verified on callback. The state token is atomically consumed, so replays fail.
- **JWKS verification** -- ID tokens are signature-verified against the provider's published JWKS.
- **SSRF guards** -- the issuer URL must be HTTPS and must not resolve to loopback, private (RFC 1918), or link-local addresses.

### Self-signed CAs

If your provider runs behind a self-signed certificate (common for self-hosted Authentik / Keycloak), make the CA chain visible to BamDude's HTTP client. There is **no dedicated `OIDC_CA_BUNDLE_PATH` env var** — instead, mount the trusted root onto the system bundle the Python `ssl` module reads:

- **Container deploys**: bind-mount your CA into `/usr/local/share/ca-certificates/` and run `update-ca-certificates` in your image, or set the standard env vars `SSL_CERT_FILE` / `REQUESTS_CA_BUNDLE` to a PEM file mounted into the container.
- **Native installs**: drop the CA into the OS trust store (`/etc/ssl/certs/` on Debian/Ubuntu via `update-ca-certificates`).

These are the same knobs every Python HTTPS client respects — `httpx` (used for the discovery + token + JWKS fetches) reads them transparently.

!!! warning "Don't auto-link by email lightly"
    Auto-create + auto-link to existing local accounts means a compromised IdP can hijack any local user with a matching email. Leave both off unless you trust the provider as much as your local password hashes.

### Microsoft Azure / Entra ID — custom email claim

Microsoft Entra ID (formerly Azure AD) doesn't ship the standard `email` claim or the `email_verified` flag — it puts the user identifier into `preferred_username` or `upn` and assumes verification on the IdP side. BamDude has two extra fields per provider for that case:

| Field | Effect |
|---|---|
| **Email claim** | Which OIDC claim BamDude reads as the user's email. Default `email`. For Entra ID set to `preferred_username` or `upn`. Whitelist regex `[a-zA-Z][a-zA-Z0-9_\-]{0,63}` blocks log-injection / dynamic-claims-lookup attack vectors. |
| **Require email_verified** | Default ON (refuses to log a user in unless the IdP marks their email verified). Entra ID never sends this flag, so for Entra ID flip it OFF. |

There's a hard guard against the unsafe combo: `auto_link_existing_accounts=true` AND `email_claim='email'` AND `require_email_verified=false` is rejected at save time (and as a DB-level CHECK constraint on Postgres) — without that gate, any IdP that lets users self-register with an arbitrary email could silently hijack existing local accounts. Custom email claims (`preferred_username`, `upn`, etc.) bypass the verified-check requirement automatically because the claim semantics are different.

The form's "Require email verified" toggle is auto-disabled (greyed out) when `email_claim != "email"` — there's no `email_verified` to consult on a custom claim. The bonus shape control is two `<datalist>` autocomplete suggestions: `email` / `preferred_username` / `upn` so you don't have to type it.

!!! tip "Tested IdPs"
    BamDude's OIDC flow has been validated against PocketID, Authentik, Keycloak, Authelia, Google, and Microsoft Entra ID (Azure AD). Other standards-compliant providers should work — let us know if you hit edge cases.

---

## :material-speedometer: Rate Limiting

Sliding-window buckets sit in front of password-bearing endpoints. Buckets are stored in the `auth_rate_limit_events` table -- no global lock, so legit users on the same network aren't held back by an attacker burning through codes elsewhere.

| Endpoint | Per-username | Per-IP |
|----------|--------------|--------|
| `POST /auth/login` | 10 / 15 min | 20 / 15 min |
| `POST /auth/forgot-password` | 3 / 15 min (per email) | 10 / 15 min |

Forgot-password records the attempt **eagerly** -- the endpoint always returns success (anti-enumeration), so the rate limit is the only thing pacing brute-force email guessing.

### Behind a reverse proxy

If BamDude sits behind nginx / Caddy / Traefik / Cloudflare, set `TRUSTED_PROXY_IPS` so the rate limiter reads the **original client IP** from `X-Forwarded-For` instead of the proxy's IP -- otherwise every request shares the proxy's IP and the cap bites within a few logins.

```ini
# .env -- comma-separated, no spaces
TRUSTED_PROXY_IPS=10.0.0.1,172.16.0.1
```

Multi-hop chains (nginx -> Cloudflare -> BamDude) are handled by right-to-left resolution: BamDude walks `X-Forwarded-For` from the right and accepts the rightmost IP that **isn't** in the trusted set as the real client.

!!! info "Single-host deploys"
    Leave `TRUSTED_PROXY_IPS` unset on a no-proxy install. BamDude falls back to the direct TCP peer IP, which is correct in that case.

---

## :material-form-textbox-password: Password Policy

Aligned with [NIST SP 800-63B](https://pages.nist.gov/800-63-3/sp800-63b.html). Composition rules beyond a sane minimum are deprecated by NIST as low-value friction; BamDude follows that lead.

**On create / change / reset:**

- At least one **uppercase** letter
- At least one **lowercase** letter
- At least one **digit**
- Minimum **8 characters**
- Maximum **256 characters** (sane upper bound to cap pbkdf2 cost)

No special-character requirement (dropped in 0.4.0.1 -- previously enforced, now considered noise that pushes users to predictable substitutions).

Other length caps across auth endpoints: email **254** (RFC 5321), username **150**, forgot-password token **128**.

### Password change kills sessions

Changing your password (or having an admin reset it) stamps `users.password_changed_at`. Any access token with `iat` older than that timestamp is rejected as stale on the next request, and every refresh-token row for that user is revoked. Result: a password change instantly logs you out of every device, the way it should.

---

## :material-tools: Admin Recovery

If you somehow lose access to every admin account -- forgotten password, lost MFA device with no backup codes, deleted the only admin user -- you can reset the setup gate from a shell on the host.

```bash
# Stop the running server first.
docker compose stop bamdude
# OR for native installs:
systemctl stop bamdude

# Run the reset CLI against the same DB the server uses.
python -m backend.app.cli reset_admin

# Restart.
docker compose start bamdude
```

`reset_admin` clears the setup-complete flag and orphan `user_groups` rows so the next boot re-enters the **first-boot setup form**. You'll create a new admin from scratch -- and **all your existing data (printers, archives, queue, users, library) is preserved**. Only the admin account itself is recreated.

!!! warning "Run with the server stopped"
    Both the CLI and the server hold the SQLite WAL. Running them simultaneously can corrupt the database. Stop the server first.

---

## :material-help-circle: Troubleshooting

### "Cannot access feature" / button is greyed out

A control disabled with a tooltip ("you need *X* permission") means your effective permission set is missing it. Walk the chain:

1. Open **Settings -> Users**, find your row, and verify which **groups** you're in.
2. Open **Settings -> Users -> Groups**, click each of your groups, confirm the missing permission is ticked.
3. If you should have access but don't see it, ask an admin to add the permission to one of your groups (or move you to a group that already has it).
4. For `*_own` vs `*_all` mismatch: check whether the resource is **ownerless** -- if so, only `*_all` works.

### Session expired mid-action

Access tokens are 1 hour. Normally the refresh cookie keeps you signed in transparently; if refresh also fails (cookie expired, server restarted with new secret, password changed elsewhere), you're hard-redirected to `/login`. Sign in and resume -- in-flight forms are not preserved.

### "setup_required" 503 after upgrade

The setup-gate cache thinks no admin exists. Restart the container -- the gate is cleared on next boot if any admin row is present in the DB. If it persists after restart, the admin user was likely deleted; run `python -m backend.app.cli reset_admin` and re-create.

### Forgot password (no SMTP)

Without Advanced Auth, the **Forgot password** link is hidden. Ask an admin to reset your password from **Settings -> Users -> Edit -> set new password**. With Advanced Auth, just use **Forgot password?** on the login page.

### LDAP users can't log in but local admin can

Almost always a directory connectivity issue. Open **Settings -> Authentication -> LDAP -> Test connection** and read the raw error. Common causes: VPN dropped, AD service-account password rotated, LDAPS cert expired, firewall closed 636/389.

---

## :material-lightbulb: Tips

!!! tip "Enrol TOTP for every admin"
    Admin accounts hold the keys to the farm. TOTP + offline backup codes is the minimum bar for any account that can change settings or delete archives.

!!! tip "Encrypt MFA secrets"
    Set `MFA_ENCRYPTION_KEY` before enrolling users. Plaintext secrets work, but encrypted-at-rest is one less thing on the list when you do your next backup audit.

!!! tip "Use OIDC for teams"
    If you already run Authentik / Keycloak / Pocket-ID for the rest of your homelab, wire BamDude into it -- you get group sync, MFA, and offboarding for free instead of maintaining a parallel password store.

!!! tip "Print the backup codes"
    Backup codes are shown **once**. Print them, drop them in your password manager's secure notes, or both -- but don't trust yourself to remember to write them down later.
