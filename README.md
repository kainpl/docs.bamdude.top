# BamDude Documentation

Source for the BamDude documentation site at **<https://docs.bamdude.top/>** (built with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/)).

The companion code repository lives at [kainpl/bamdude](https://github.com/kainpl/bamdude); issues, releases, and the application itself stay there. This repo only ships docs content + the static-site build config.

## Layout

- `docs/` — Markdown pages, structured by topic (`getting-started/`, `features/`, `reference/`). Each English page has a sibling `*.uk.md` with the Ukrainian translation.
- `overrides/` — small theme overrides (custom partials).
- `mkdocs.yml` — site config (theme, navigation tree, i18n plugin, markdown extensions).
- `requirements.txt` — pinned mkdocs + plugin versions; mirrors the dev-requirements pins on the main repo so local + CI builds match.

## Local development

```bash
# 1. Create a virtualenv (Python 3.10+).
python -m venv .venv
source .venv/bin/activate          # on Windows: .venv\Scripts\activate

# 2. Install build deps.
pip install -r requirements.txt

# 3. Live-reload server on http://127.0.0.1:8000/.
mkdocs serve
```

`make serve` and `make build` are also available — see `Makefile`.

## Branches

- **`main`** — production. The published site at <https://docs.bamdude.top/> tracks this branch.
- **`dev`** — active development; default working branch. Promote to `main` (fast-forward merge) when a doc set is ready to publish.

## Contributing

Pages are language-paired: `topic.md` (English) + `topic.uk.md` (Ukrainian). Keep them in sync — every English change should land with a matching Ukrainian update in the same PR. Add new pages in both locales, then register them once in the `nav:` tree of `mkdocs.yml`.

## Deploy

`main`-branch pushes auto-build via `mkdocs build --strict` on a **self-hosted GitHub Actions runner running on the production server itself**, then rsync the static site into the local nginx web root. Cloudflare sits in front of nginx (proxied DNS, `Full (Strict)` SSL). No SSH keys in GH Secrets — the runner is already on the host. PRs into `main` / `dev` run the same strict build on `ubuntu-latest` as a CI gate so broken cross-links are caught before merge.

See **[`DEPLOY.md`](DEPLOY.md)** for required GitHub Actions secrets, the runner-install recipe, the nginx server block, and Cloudflare settings.
