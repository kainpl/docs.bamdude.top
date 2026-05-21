---
title: Privacy & Telemetry
description: What anonymized data BamDude sends, what it never sends, and how to opt out
---

# Privacy & Telemetry

BamDude is self-hosted: your prints, files, printer credentials and inventory never leave your server. The only data BamDude ever sends out is (1) **anonymized usage telemetry** to guide development, and (2) the contents of an **in-app bug report** when you explicitly file one. Both are described in full below.

## :material-chart-box: Anonymized usage telemetry

Shipped in BamDude **0.4.5**. On by default (opt-out), with a notice on the first-run setup screen and a toggle in **Settings → General**.

Once a day BamDude sends a small anonymized snapshot to `https://bamdude.top/api/telemetry`, keyed by a random `install_id` generated once at first boot and stored in `DATA_DIR/.install_id` (mode `0600`). The id is **not** linked to any account, email, IP or hardware identifier — it only lets the collector fold a given install's daily snapshots into one row.

### What is sent

- App version + release channel
- OS platform / release / architecture, Python version, whether running in Docker
- Aggregate counts: archives, printers, spools, projects, smart plugs
- Printer **models** (e.g. `P1S`, `A1`)
- Enabled integrations (Spoolman, Obico, Telegram, OIDC, Git backup, slicer API) as on/off flags
- Daily print counts (completed / failed)

### What is never sent or stored

- No IP address — a coarse country is derived from the proxy header, then discarded
- No printer names, serial numbers or IP addresses
- No file names, file paths, project names, model files or thumbnails
- No user names, emails, passwords, tokens or any settings values

### How to opt out

- **Settings → General → Anonymous usage statistics** — toggle it off at any time. It takes effect immediately and also asks the collector to erase this install's data.
- Set `TELEMETRY_DISABLED=true` in the environment to disable it entirely.
- Point `TELEMETRY_RELAY_URL` at your own collector to keep the data in-house.

The daily send is fail-silent — it never blocks or disrupts the app.

## :material-bug: Bug reports

A bug report is sent **only** when you explicitly click **Report a Bug** and submit it. See [In-app Bug Report](features/bug-report.md) for exactly what's included — sanitized logs, an optional screenshot, and a support snapshot that never contains printer names, serials, IPs, access codes, passwords, emails, API keys, hostnames or user names. Submitted reports become GitHub issues on [`kainpl/bamdude`](https://github.com/kainpl/bamdude/issues).

## :material-server: Self-hosting the collector

Both endpoints default to the `bamdude.top` collector, which holds the GitHub PAT and the telemetry database. If you'd rather not use it, run your own collector and point `TELEMETRY_RELAY_URL` and `BUG_REPORT_RELAY_URL` at it — BamDude never holds a PAT itself.
