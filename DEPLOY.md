# Deploy

The site is built **on the production server itself** by a self-hosted GitHub Actions runner that listens for `main`-branch pushes, then rsync's the static build into the nginx web root. Cloudflare sits in front of nginx (proxied DNS, `Full (Strict)` SSL).

No SSH key in GH Secrets, no `ssh-keyscan` round-trip — the runner is already on the host, so the deploy is a local file copy.

## Pipeline

```
push to main → .github/workflows/deploy.yml
              └─ self-hosted runner (label: docs-deploy)
                 ├─ checkout
                 ├─ pip install -r requirements.txt
                 ├─ mkdocs build --strict       # fails on broken links / missing anchors
                 ├─ rsync -a --delete ./site/ → $DEPLOY_PATH
                 └─ purge Cloudflare cache       # optional, only if CF secrets are set
```

A separate `ci.yml` runs on **`ubuntu-latest` (GitHub-hosted)** for PRs into `main` / `dev` so PR build checks don't depend on the production runner being online.

## Required GitHub secrets

Set under **Repo → Settings → Secrets and variables → Actions** (Repository secrets).

| Secret | Required | Description |
| --- | --- | --- |
| `DEPLOY_PATH` | yes | Absolute path on the server where the static site lands (rsync target). E.g. `/var/www/docs.bamdude.top/html`. The runner user must own this path so rsync can write without sudo. |
| `CLOUDFLARE_ZONE_ID` | optional | Cloudflare zone ID for `bamdude.top` — needed only for the cache-purge step. Skip both CF secrets to leave caching to TTL expiry. |
| `CLOUDFLARE_API_TOKEN` | optional | API token scoped to **Zone → Cache Purge → Purge** for the same zone. |

## One-time server setup

### 1. Site directory

```bash
sudo mkdir -p /var/www/docs.bamdude.top/html
# nginx (www-data) reads it; the runner user (created in step 2) writes it.
sudo chown -R bamdude-runner:www-data /var/www/docs.bamdude.top
sudo chmod -R 750 /var/www/docs.bamdude.top
```

### 2. Self-hosted runner

Run the runner under a dedicated unprivileged user — never `root`, and never your personal account.

```bash
sudo useradd --system --create-home --shell /bin/bash bamdude-runner
sudo -u bamdude-runner -i
mkdir actions-runner && cd actions-runner
```

Get the latest runner release URL from **Repo → Settings → Actions → Runners → New self-hosted runner** — the page shows the exact `curl` + `tar` + `./config.sh` commands for your OS, including a one-time registration token.

```bash
# Example — replace VERSION + REGISTRATION_TOKEN with values from the
# repo's runner-add page.
curl -o actions-runner.tar.gz -L \
  https://github.com/actions/runner/releases/download/vVERSION/actions-runner-linux-x64-VERSION.tar.gz
tar xzf ./actions-runner.tar.gz

# Add the docs-deploy label so the workflow's `runs-on` selector targets
# this runner specifically. Linux + self-hosted are added by default.
./config.sh \
  --url https://github.com/kainpl/docs.bamdude.top \
  --token REGISTRATION_TOKEN \
  --name docs-deploy-prod \
  --labels docs-deploy \
  --unattended
```

Install as a systemd service so it survives reboots:

```bash
exit  # leave bamdude-runner shell — svc.sh install needs root
cd /home/bamdude-runner/actions-runner
sudo ./svc.sh install bamdude-runner
sudo ./svc.sh start
sudo ./svc.sh status   # should show "active (running)"
```

The runner now appears as **Idle** under **Repo → Settings → Actions → Runners**. Trigger a workflow (e.g. **Actions → deploy → Run workflow → main**) to verify.

### 3. Python on the runner

`actions/setup-python` provisions Python 3.12 into the runner's tool cache on first run (downloads from `actions/python-versions`, works out of the box on Linux distros with `glibc 2.31+` — covers Ubuntu 20.04+ / Debian 11+). **You usually don't need to do anything on the server.** The first workflow run will fetch Python and cache it for subsequent runs.

If you want a system Python 3.12 separately (e.g. for running `mkdocs build` by hand outside the runner), and your distro doesn't ship 3.12 in the default repo (Ubuntu 22.04 ships 3.10, for example):

```bash
# Debian / Ubuntu — add deadsnakes PPA, then install 3.12.
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.12 python3.12-venv
# Note: python3.12-distutils does NOT exist — distutils was removed from
# Python 3.12's stdlib. setuptools provides the replacement and pip pulls
# it in automatically.
```

### 4. nginx server block

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
    # Let's Encrypt with HTTP-01.
    ssl_certificate     /etc/ssl/cloudflare-origin/docs.bamdude.top.pem;
    ssl_certificate_key /etc/ssl/cloudflare-origin/docs.bamdude.top.key;
    ssl_protocols       TLSv1.2 TLSv1.3;

    # MkDocs Material's i18n plugin emits clean URLs (no trailing .html).
    # try_files maps /getting-started/upgrading/ → index.html lookup so
    # the path resolves the same way ``mkdocs serve`` did.
    location / {
        try_files $uri $uri/ $uri/index.html =404;
    }

    # Hashed assets (CSS/JS chunks under /assets/) can cache for a year —
    # MkDocs renames them on every content change, so a "stale" copy is
    # impossible. HTML gets a short TTL so a typo fix is live within
    # minutes even when CF doesn't get a purge call.
    location ~* \.(?:css|js|woff2?|ttf|otf|eot|png|jpg|jpeg|gif|svg|webp|ico)$ {
        expires 30d;
        add_header Cache-Control "public, max-age=2592000, immutable";
    }

    location ~* \.html$ {
        expires 5m;
        add_header Cache-Control "public, max-age=300, must-revalidate";
    }

    # Optional — Cloudflare also gzips, but origin gzip cuts internal
    # bandwidth between CF and the server when CF re-fetches.
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

## Cache-purge token (optional)

The cache-purge step in `deploy.yml` skips itself when `CLOUDFLARE_ZONE_ID` / `CLOUDFLARE_API_TOKEN` aren't set. To enable:

1. Cloudflare Dashboard → My Profile → API Tokens → **Create Token**.
2. Use the **Zone → Cache Purge** template; restrict to the `bamdude.top` zone only.
3. Copy the generated token into the `CLOUDFLARE_API_TOKEN` GH secret.
4. Zone ID is on the zone overview page (right sidebar) — copy it into `CLOUDFLARE_ZONE_ID`.

Without these the html short-TTL (5 min, see nginx block) gets a stale doc out within a few minutes anyway. CF purge just skips that wait.

## First deploy

The runner has to be Idle on the server before the first `main` push will land. After the runner is registered + the `DEPLOY_PATH` secret is set:

- **Trigger manually** — Repo → Actions → `deploy` → Run workflow → branch `main`.
- **Or push** — `git checkout main && git merge --ff-only dev && git push` runs the workflow automatically.

## Promoting `dev` → `main`

```bash
git checkout main
git merge --ff-only dev
git push
```

The `deploy` workflow runs on the `main` push and the runner copies the freshly-built site into `DEPLOY_PATH`. If `--ff-only` fails, rebase `dev` on `main` first — the docs repo doesn't carry a release-cut history that would benefit from merge commits.

## Security notes

- **The runner trusts whatever is in `main`.** Don't accept PRs into `main` from external contributors without review — anything that lands triggers a build that runs on your server. Self-hosted runners + public PRs is a known footgun; this repo is private (or accepts PRs only into `dev` with manual promotion to `main`), so it's fine.
- **The runner user does NOT need sudo.** rsync writes inside `DEPLOY_PATH` which the runner user owns; nginx reads via group permissions (`www-data` group on the directory). Keep it that way — sudo on a runner is a privilege escalator if a workflow is ever compromised.
- **Outbound network from the runner** is wide open by default (it talks to GitHub for jobs, to PyPI for `pip install`, optionally to Cloudflare for cache purge). Lock that down with a host firewall if you want the runner sandboxed.
