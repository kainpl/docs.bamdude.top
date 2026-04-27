---
title: Obico AI Failure Detection
description: Optional ML-driven print-failure detection with notify / pause / pause-and-power-off responses
---

# Obico AI Failure Detection

BamDude has an optional integration with [Obico](https://www.obico.io/) — a machine-learning service that watches camera frames during a print and flags spaghetti / failures before they get expensive. The integration is **off by default**. When enabled, it polls camera frames, hands them to an Obico ML endpoint, smooths the result over time, and on a sustained failure either notifies you, pauses the print, or pauses and powers the printer off via a smart plug.

## :material-shield-check: When to use it

Obico is most useful for unattended overnight runs and farm-wide automation. It catches:

- Detachment / spaghetti during the first 20 layers
- Mid-print blob-of-death from a failed retraction or layer shift
- Bed clogging on multi-spool prints

It is **not** a substitute for first-layer monitoring or HMS error notifications — those catch different failure modes faster.

## :material-cog: Setup

1. Self-host the Obico ML server (or use the public endpoint — see Obico docs).
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

## :material-radar: How detection works

The loop polls each enabled, currently-printing printer at the configured interval:

1. **Capture** — BamDude grabs a frame from the printer's local camera (no Bambu Cloud involvement).
2. **Stash** — the JPEG goes into an in-process cache under a 32-byte random nonce, with a 30-second TTL.
3. **Hand off** — BamDude sends the Obico ML API a URL pointing back at `/api/v1/obico/cached-frame/{nonce}`. The Obico server fetches that URL and runs its classifier. (This is why `APP_URL` matters — it has to be reachable from the Obico host.)
4. **Score smoothing** — raw scores are passed through an exponentially-weighted moving average **plus** a dual rolling mean. A single "warning" frame doesn't trigger anything; sustained scores above the failure threshold do.
5. **Action** — when the smoothed score crosses the failure threshold:

    | Action | What happens |
    |---|---|
    | `notify` | Fires a notification through every provider subscribed to `obico_failure` (Telegram with snapshot, email, etc.). |
    | `pause` | Sends a pause MQTT command to the printer. Your provider notification still fires. |
    | `pause_and_off` | Pauses the printer **and** turns off the bound smart plug after a short delay so the printer can write its end-state cleanly. Use this for overnight unattended workflows where you'd rather kill power than waste filament. |

## :material-key-variant: Why is the cached-frame URL whitelisted?

`/api/v1/obico/cached-frame/{nonce}` is one of the few endpoints that **bypasses** the always-on auth gate — the Obico ML server has no way to send a bearer token for a one-shot GET. The 32-byte nonce + 30-second TTL is the security surface; without the nonce, the route returns 404. The path is exempt only inside the `auth_middleware` whitelist.

This is also why Obico's URL needs to be reachable from the ML host. If you front BamDude with a reverse proxy, make sure `/api/v1/obico/cached-frame/` is not blocked by an extra auth layer in nginx.

## :material-tune: Sensitivity tuning

Start on `medium`. If Obico screams "failure" at every retraction blob, drop to `low`. If it misses obvious detachments, raise to `high`. Smoothing means single-frame outliers won't trip the action — you need a sustained confidence above threshold.

The exact thresholds live in `backend/app/services/obico_smoothing.py`; they're conservative by default (designed not to false-trip on Obico's reference dataset).

## :material-eye: Watching what Obico sees

The detection panel under **Settings → Integrations → Obico AI** shows the latest decision per printer (smoothed score, classification, last action), plus a live thumbnail of the frame Obico just looked at. Useful for tuning sensitivity without waiting for a real failure.

## :material-power-off: Fail-safe behaviour

If Obico's API is unreachable or returns a non-2xx response:

- The error is logged at `WARNING`, not `ERROR` (no spammy stack traces).
- The detection loop keeps going — a transient outage doesn't disable detection permanently.
- No spurious "failure" action fires from a missing classification.

If `obico_enabled` is toggled off mid-print, the loop stops on the next iteration; the print continues uninterrupted.
