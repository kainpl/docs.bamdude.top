# Deploy

The site is built by GitHub Actions on every `main`-branch push and rsynced to the production nginx server. Cloudflare sits in front of nginx (proxied DNS, `Full (Strict)` SSL).

## Pipeline

```
push to main → .github/workflows/deploy.yml
              ├─ pip install -r requirements.txt
              ├─ mkdocs build --strict          # fails on broken links / missing anchors
              ├─ rsync ./site/ → server:DEPLOY_PATH
              └─ purge Cloudflare cache         # optional, only if CF secrets are set
```

A separate `ci.yml` runs `mkdocs build --strict` on PRs into `main` / `dev` so broken links are caught before merge.

## Required GitHub secrets

Set under **Repo → Settings → Secrets and variables → Actions** (Repository secrets, not environment-scoped unless you also create a `production` environment for a manual approval gate).

| Secret | Required | Description |
| --- | --- | --- |
| `DEPLOY_SSH_KEY` | yes | Private SSH key (ed25519 recommended) for the deploy user. The matching public key goes into `~/.ssh/authorized_keys` on the server. **Use a dedicated key for this workflow only** — don't reuse a personal key. |
| `DEPLOY_HOST` | yes | Server hostname or IP (e.g. `bamdude.top` or `1.2.3.4`). |
| `DEPLOY_USER` | yes | SSH user. Recommend a non-root account that owns `DEPLOY_PATH`, e.g. `bamdude-docs`. |
| `DEPLOY_PORT` | optional | SSH port. Defaults to `22` when unset. |
| `DEPLOY_PATH` | yes | Absolute path on the server where the static site lands (rsync target). E.g. `/var/www/docs.bamdude.top/html`. |
| `CLOUDFLARE_ZONE_ID` | optional | Cloudflare zone ID for the `bamdude.top` zone — needed only for the cache-purge step. Skip both CF secrets to leave caching to TTL expiry. |
| `CLOUDFLARE_API_TOKEN` | optional | API token scoped to **Zone → Cache Purge → Purge** for the same zone. |

## Server setup (one-time)

### 1. Deploy user

```bash
sudo useradd --system --create-home --shell /bin/bash bamdude-docs
sudo mkdir -p /home/bamdude-docs/.ssh
sudo cp /path/to/id_ed25519.pub /home/bamdude-docs/.ssh/authorized_keys
sudo chown -R bamdude-docs:bamdude-docs /home/bamdude-docs/.ssh
sudo chmod 700 /home/bamdude-docs/.ssh
sudo chmod 600 /home/bamdude-docs/.ssh/authorized_keys
```

Optional hardening — restrict the key to rsync-only by prefixing the `authorized_keys` line:

```text
command="rrsync -wo /var/www/docs.bamdude.top/html",no-pty,no-port-forwarding,no-X11-forwarding ssh-ed25519 AAAA...
```

(`rrsync` ships with rsync; on Debian/Ubuntu it's at `/usr/share/doc/rsync/scripts/rrsync.gz` — `gunzip` it into `/usr/local/bin/rrsync`.)

### 2. Site directory

```bash
sudo mkdir -p /var/www/docs.bamdude.top/html
sudo chown -R bamdude-docs:bamdude-docs /var/www/docs.bamdude.top
```

### 3. nginx server block

`/etc/nginx/sites-available/docs.bamdude.top`:

```nginx
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name docs.bamdude.top;

    root /var/www/docs.bamdude.top/html;
    index index.html;

    # TLS terminates here — Cloudflare's "Full (Strict)" mode requires a
    # valid cert. Use the Cloudflare Origin CA cert (free, 15-year), or
    # Let's Encrypt with HTTP-01 (works fine since CF DNS-01 isn't needed).
    ssl_certificate     /etc/ssl/cloudflare-origin/docs.bamdude.top.pem;
    ssl_certificate_key /etc/ssl/cloudflare-origin/docs.bamdude.top.key;
    ssl_protocols       TLSv1.2 TLSv1.3;

    # MkDocs Material's i18n plugin emits clean URLs (no trailing .html).
    # try_files maps /getting-started/upgrading/ → index.html lookup so the
    # path resolves the same way the dev server (mkdocs serve) does.
    location / {
        try_files $uri $uri/ $uri/index.html =404;
    }

    # Hashed assets (CSS/JS chunks under /assets/) can cache for a year —
    # MkDocs renames them on every content change, so a "stale" copy is
    # impossible. Everything else gets a short TTL so a typo fix is live
    # within minutes even when CF doesn't get a purge call.
    location ~* \.(?:css|js|woff2?|ttf|otf|eot|png|jpg|jpeg|gif|svg|webp|ico)$ {
        expires 30d;
        add_header Cache-Control "public, max-age=2592000, immutable";
    }

    location ~* \.html$ {
        expires 5m;
        add_header Cache-Control "public, max-age=300, must-revalidate";
    }

    # Optional gzip — Cloudflare also gzips on its end, but origin gzip
    # cuts internal bandwidth between CF and the server when CF re-fetches.
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript image/svg+xml;
    gzip_min_length 1024;
}

# Plain :80 → 301 to https. Cloudflare also handles this, but the redirect
# at origin keeps things sane if a request ever bypasses the proxy.
server {
    listen 80;
    listen [::]:80;
    server_name docs.bamdude.top;
    return 301 https://$host$request_uri;
}
```

```bash
sudo ln -s /etc/nginx/sites-available/docs.bamdude.top /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

## Cloudflare settings

DNS:
- `A` record for `docs.bamdude.top` → server IP, **Proxied (orange cloud)**.

SSL/TLS:
- Encryption mode: **Full (strict)** — requires a valid origin cert. Use the **Cloudflare Origin CA cert** (Dashboard → SSL/TLS → Origin Server) for a free 15-year cert that chains to a CF root only Cloudflare trusts.
- Always Use HTTPS: **on**.
- Automatic HTTPS Rewrites: **on**.
- TLS 1.3: **on**.

Caching:
- Browser Cache TTL: **Respect Existing Headers** (the nginx block above already sets sensible per-asset headers).
- Cache rules: a single rule that caches `/assets/*` aggressively (`Edge Cache TTL: 1 month`) is enough — html stays at the default short TTL.

## Cache-purge token

The optional cache-purge step in `deploy.yml` skips itself when `CLOUDFLARE_ZONE_ID` / `CLOUDFLARE_API_TOKEN` aren't set. To enable:

1. Cloudflare Dashboard → My Profile → API Tokens → **Create Token**.
2. Use the **Zone → Cache Purge** template; restrict to the `bamdude.top` zone only.
3. Copy the generated token into the `CLOUDFLARE_API_TOKEN` GH secret.
4. Zone ID is on the zone overview page (right sidebar) — copy it into `CLOUDFLARE_ZONE_ID`.

## First deploy (manual)

Until the workflow runs once, the rsync target is empty. Either:

- **Trigger the workflow manually** — Repo → Actions → `deploy` → Run workflow → branch `main`.
- **Or rsync from a local checkout** — useful for verifying the SSH key works before relying on the GH runner:

  ```bash
  pip install -r requirements.txt
  mkdocs build --strict
  rsync -avz --delete -e "ssh -i ~/.ssh/bamdude-docs-deploy" \
    ./site/ bamdude-docs@bamdude.top:/var/www/docs.bamdude.top/html/
  ```

## Promoting `dev` → `main`

```bash
git checkout main
git merge --ff-only dev
git push
```

The deploy workflow runs automatically on the `main` push. If `--ff-only` fails, rebase `dev` on `main` first — the docs repo doesn't carry a release-cut history that would benefit from merge commits.
