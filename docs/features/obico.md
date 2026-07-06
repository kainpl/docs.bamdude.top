---
title: Obico AI Failure Detection
description: Optional ML-driven print-failure detection with notify / pause / pause-and-power-off responses
---

# Obico AI Failure Detection

BamDude has an optional integration with a **self-hosted** [Obico](https://github.com/TheSpaghettiDetective/obico-server) `ml_api` — a machine-learning service that watches camera frames during a print and flags spaghetti / failures before they get expensive. The integration is **off by default**. When enabled, it polls camera frames, hands them to an Obico ML endpoint, smooths the result over time, and on a sustained failure either notifies you, pauses the print, or pauses and powers the printer off via a smart plug.

!!! info "Self-hosted only — no cloud, no obico.io"
    BamDude talks to **your own** Obico `ml_api` over HTTP on your local network. It never connects to obico.io, never registers a printer with Obico's web app, never opens a WebSocket, and never uploads frames anywhere outside your LAN. Frames live in a 30-second in-process cache; the only external recipient of a snapshot URL is the ML container that you control.

## :material-shield-check: When to use it

Obico is most useful for unattended overnight runs and farm-wide automation. It catches:

- Detachment / spaghetti during the first 20 layers
- Mid-print blob-of-death from a failed retraction or layer shift
- Bed clogging on multi-spool prints

It is **not** a substitute for first-layer monitoring or HMS error notifications — those catch different failure modes faster.

## :material-server: Self-host the Obico ML API

You only need the `ml_api` container from Obico's stack. The web app, Django site, and printer registration are **not required** — BamDude doesn't speak Obico's printer protocol, only the raw classification HTTP endpoint.

### 1. Clone the Obico server

```bash
git clone -b release https://github.com/TheSpaghettiDetective/obico-server.git
cd obico-server
```

### 2. Expose port 3333

Edit `docker-compose.yml` and add a `ports` mapping on the `ml_api` service:

```yaml
ml_api:
  ports:
    - "3333:3333"
```

### 3. Start just `ml_api`

```bash
docker compose up -d ml_api
```

The first start downloads the YOLO model (~100 MB) and allocates roughly 4 GB RAM at runtime. Plan capacity accordingly if you're hosting on a small server.

### 4. Verify

```bash
curl http://<obico-host>:3333/hc/
# → "ok"
```

If `/hc/` returns `ok`, the ML API is ready for BamDude.

---

## :material-cog: Setup

1. Self-host the Obico ML server using the steps above.
2. Open **Settings → Integrations → Obico AI**.
3. Tick **Enable Obico failure detection**.
4. Fill in:

    | Setting | Notes |
    |---|---|
    | **ML API URL** | The full URL Obico exposes for image classification (e.g. `https://obico.example.com/api/v1/octo/`). |
    | **Sensitivity** | `low` / `medium` / `high`. Controls the threshold at which a single frame is classified as "warning" or "failure". |
    | **Action on sustained failure** | `notify`, `pause`, or `pause_and_off`. See below. |
    | **Poll interval** | Seconds between frame captures (5–120). Shorter = faster reaction, more bandwidth + more ML cost. |
    | **Enabled printers** | Per-printer toggle list. Leave all on, or restrict to specific printers (e.g. enable only on the unattended overnight printer). |

5. **Save**. The Obico loop starts immediately for any printer in `RUNNING` state.

!!! warning "External URL must be set"
    **Settings → Network → External URL** has to be the URL the ML container will use to fetch the cached frame. The Obico container fetches `/<external-url>/api/v1/obico/cached-frame/{nonce}` itself; it must resolve from inside that container's network namespace, not from your browser. Usually the LAN IP of the BamDude host. Without it, BamDude refuses to start the loop and you'll see `external_url not set — ML API cannot reach snapshot endpoint`.

### Sensitivity Low / Medium / High

| Setting | Effect |
|---|---|
| **Low** | Higher confidence threshold; fewer false positives but slower to alert and may miss subtle early failures. |
| **Medium** | Obico's original thresholds — recommended starting point. |
| **High** | Lower threshold; alerts earlier, more false positives on retraction blobs / shadows / camera glare. |

## :material-radar: How detection works

The loop polls each enabled, currently-printing printer at the configured interval:

1. **Capture** — BamDude grabs a frame from the printer's local camera (no Bambu Cloud involvement).
2. **Stash** — the JPEG goes into an in-process cache under a 32-byte random nonce, with a 30-second TTL.
3. **Hand off** — BamDude sends the Obico ML API a URL pointing back at `/api/v1/obico/cached-frame/{nonce}`. The Obico server fetches that URL and runs its classifier. (This is why `APP_URL` matters — it has to be reachable from the Obico host.)
4. **Score smoothing** — raw scores are passed through an exponentially-weighted moving average **plus** a dual rolling mean. A single "warning" frame doesn't trigger anything; sustained scores above the failure threshold do.

    Specifically: a **30-frame warmup** at the start of each print is treated as "trust nothing" (~5 minutes at the default 10 s poll interval); after warmup, raw scores feed an EWM with `alpha = 2/13` for short-window smoothing (~5 min equivalent) plus a long rolling-mean baseline (~20 h at 10 s/frame) used for false-positive prevention against gradual environmental drift. This is the same approach Obico's own detector uses upstream.
5. **Action** — when the smoothed score crosses the failure threshold:

    | Action | What happens |
    |---|---|
    | `notify` | Fires the dedicated **AI Failure Detection** notification event — a separate, **opt-in** trigger (off by default) with its own template, split out of `printer_error` so you can page on AI alerts without also being paged for every HMS hardware code. The alert carries the printer, the job name, the confidence score, and the action taken. Subscribe to it independently: each provider has its own **AI Failure Detection** toggle, and Telegram adds a matching per-chat notify item. |
    | `pause` | Sends a pause MQTT command to the printer. Your provider notification still fires. |
    | `pause_and_off` | Pauses the printer **and** turns off the bound smart plug after a short delay so the printer can write its end-state cleanly. Use this for overnight unattended workflows where you'd rather kill power than waste filament. |

## :material-key-variant: Why is the cached-frame URL whitelisted?

`/api/v1/obico/cached-frame/{nonce}` is one of the few endpoints that **bypasses** the always-on auth gate — the Obico ML server has no way to send a bearer token for a one-shot GET. The 32-byte nonce + 30-second TTL is the security surface; without the nonce, the route returns 404. The path is exempt only inside the `auth_middleware` whitelist.

This is also why Obico's URL needs to be reachable from the ML host. If you front BamDude with a reverse proxy, make sure `/api/v1/obico/cached-frame/` is not blocked by an extra auth layer in nginx.

## :material-tune: Sensitivity tuning

Start on `medium`. If Obico screams "failure" at every retraction blob, drop to `low`. If it misses obvious detachments, raise to `high`. Smoothing means single-frame outliers won't trip the action — you need a sustained confidence above threshold.

The exact thresholds live in `backend/app/services/obico_smoothing.py`; they're conservative by default (designed not to false-trip on Obico's reference dataset).

## :material-eye: Watching what Obico sees

The detection panel under **Settings → Integrations → Obico AI** is split into a Status card and a Recent detections strip:

**Status card**

- Background-service running flag (green / red).
- Active threshold values after sensitivity scaling (so you can sanity-check Low / Medium / High really did adjust the numbers).
- For each currently-printing monitored printer:
    - Live classification — `safe` / `warning` / `failure`
    - Smoothed score (the post-EWM number that's compared against the threshold)
    - Frames seen so far this print (so you can see the warmup countdown)

**Recent detections** — a chronological list of the last events with timestamp, printer, classification, score, and a thumbnail of the frame that crossed the threshold. Useful for tuning sensitivity without waiting for a real failure.

---

## :material-alert-circle: Requirements & Gotchas

- **Bidirectional reachability.** BamDude has to reach the ML API at `http://<obico-host>:3333/p/`, **and** the ML container has to reach BamDude at `<external-url>/api/v1/obico/cached-frame/{nonce}`. If they're on the same Docker network, use the BamDude container's hostname; on separate hosts, use the LAN IP. `localhost` only works when both run on the same host.
- **External URL setting required.** Without **Settings → Network → External URL**, BamDude has nothing to hand to the ML API; the loop refuses to start.
- **Public URL caveat under reverse-proxy auth.** The cached-frame route bypasses BamDude's always-on auth gate (the ML container can't send a bearer for a one-shot GET), so make sure your nginx / Caddy / Traefik isn't slapping its **own** auth layer on `/api/v1/obico/cached-frame/`. The route's own security surface is the 32-byte random nonce + 30-second TTL — without the nonce it 404s.
- **Calibration prints are skipped.** The detection loop only runs while the print is in `RUNNING` state, so the calibration / first-layer phase isn't classified — Bambu's own calibration screens cause too many shapes that aren't real failures yet.
- **First 30 frames ignored.** Even within `RUNNING`, the 30-frame warmup means the first ~5 minutes of every print are deliberately quiet — gives EWM time to stabilise before triggering anything.
- **Single-fire per print.** Once an action fires, subsequent failure scores in the same print won't re-trigger. This is intentional — you don't want five "pause" commands stepping on each other when the spaghetti monster is already obvious. Action state resets on the next `print_started`.
- **Camera must be reachable.** The detection loop fetches frames from the printer's local camera the same way the main BamDude UI does. If the camera page in the UI doesn't show a stream, Obico won't get one either.
- **Disk / RAM.** ~4 GB RAM on the Obico host. CPU scales with monitored printer count × poll frequency. A 5 s interval across 8 printers is roughly 1.6 frames/sec, fine on most hardware.

---

## :material-help-circle: Troubleshooting

**`external_url not set — ML API cannot reach snapshot endpoint`**
: Open **Settings → Network** and set the External URL to a hostname or IP that's reachable from inside the Obico container. Test by `curl`-ing it from a shell inside the Obico container.

**Test button returns an error**
: The ML API isn't reachable from BamDude. Check `docker compose ps ml_api` and try `curl http://<obico-host>:3333/hc/` from the BamDude host. If `/hc/` works but Test doesn't, double-check the URL field uses the same scheme (`http://` vs `https://`) and port.

**Service is running but no detections appear**
: No news is good news — entries only land in history when classification leaves `safe` or an action fires. If you genuinely think Obico's missing a real failure, check the Status card to confirm the print is being polled, then raise sensitivity.

**False positives on normal prints**
: Drop sensitivity High → Medium → Low. Also check the camera angle — if the frame includes too much non-print background (filament spools, AMS, the operator's cat) the model has more chances to see "spaghetti" in random shapes.

**Missed obvious failures**
: Raise sensitivity. Remember the 30-frame warmup at the start — the first ~5 min are deliberately quiet. Verify the camera angle actually shows the build plate (not just the toolhead).

**`/api/v1/obico/cached-frame/` returns 401 / 403**
: Your reverse proxy is enforcing its own auth layer on top of BamDude. Carve out an exception for that path; BamDude itself whitelists it from the always-on gate.

---

## :material-license: License & Attribution

Obico's ML model and detection algorithms are licensed **AGPL-3.0** — the same license as BamDude, so derivative-work obligations are aligned. BamDude does **not** vendor or link any Obico code; it only calls the ML API over HTTP. The container image lives in Obico's registry; pull it from the upstream `obico-server` repo, not from `ghcr.io/kainpl/bamdude`.

## :material-power-off: Fail-safe behaviour

If Obico's API is unreachable or returns a non-2xx response:

- The error is logged at `WARNING`, not `ERROR` (no spammy stack traces).
- The detection loop keeps going — a transient outage doesn't disable detection permanently.
- No spurious "failure" action fires from a missing classification.

If `obico_enabled` is toggled off mid-print, the loop stops on the next iteration; the print continues uninterrupted.
