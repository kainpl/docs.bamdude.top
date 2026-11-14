---
title: A camera wall on the workshop TV
description: A screen on the wall that shows every camera and names no file — a kiosk token in the URL, nothing to log in to
---

# A camera wall on the workshop TV

!!! tip "Need states and completion times instead of video?"
    Use the [status monitor](../features/status-monitor.md): 50 uniform tiles on Full HD, attention-first ordering and separate printer/queue views. It has its own **Status monitor** TV token; the **Cam Wall** token in this scenario is for cameras.

## :material-map-marker-question: The situation

Forty-eight printers in two rooms. The operator walks the rows to see what is going on; from the desk, the Printers page is a wall of cards and the cameras are one click each. A TV is already hanging in the shop. What it should show is every camera at once — and nothing a visitor should not read off a screen in a room anyone can walk into: no file names, no serial numbers, no addresses.

## :material-flag-checkered: The goal

A URL that a TV, or a Raspberry Pi behind it, opens once and keeps showing: the whole farm as camera tiles with a state badge on each, no login, and revocable from Settings the day the TV is retired.

## :material-puzzle: What is involved

| Feature | Its part |
|---|---|
| [Camera wall](../features/camera.md#camera-wall) | The tile grid: snapshots refreshed on an interval, one live tile you pick on the signed-in wall, paused off-screen. |
| [Cam Wall on a TV or kiosk](../features/camera.md#cam-wall-on-a-tv-or-kiosk) | The wall's own URL, `/camwall`, and its token mode. |
| [Long-lived tokens](../features/camera.md#stream-token-gate) | A **Cam Wall**-scoped token: the credential in the URL, revocable, at most a year old. |

## :material-format-list-numbered: Step by step

1. **Try the wall signed in.** On the Printers page switch **Cards / Cam wall**, or open `http://your-bamdude:8000/camwall` in your own browser. That is the full wall — tiles are clickable and the gear opens its settings. Note what looks right: the tile size, the snapshot interval.

2. **Make a token for the TV.** **Settings → API Keys → Camera and monitor tokens → create**: name it after the screen — *Workshop TV* — scope **Cam Wall**, and an expiry (a year at most; *never* is refused by design). Copy the token: it is shown once.

3. **Build the URL.**

    ```text
    http://your-bamdude:8000/camwall?token=bblt_<prefix>_<secret>&interval=10&status=compact&size=m
    ```

    `interval` is the seconds between snapshot refreshes (2–60), `status` the overlay — `off` or `compact`, `size` the tile size — `s`, `m`, `l` or `xl`. A kiosk cannot open the settings gear, so the settings ride in the URL; a value that cannot be read falls back instead of breaking the wall.

4. **Point the TV at it.** A browser in kiosk mode on the Pi, or the TV's own browser, full screen. That is all the configuration there is.

5. **Retire it one day.** **Settings → API Keys → Camera and monitor tokens**, find *Workshop TV* by name or by its prefix, **Revoke**. The wall goes dark on its next request; there is no cache to wait out.

## :material-cogs: What BamDude does on its own after that

- **A token wall shows snapshots, not video.** Its tiles cannot be clicked, so none of them goes live: every tile on screen refreshes a still frame on the interval. A tile counts as visible once 40 % of it is on screen; off-screen or disconnected printers pause entirely — no network for a camera nobody is looking at.
- **The token wall is deliberately less than the signed-in wall.** No click-through, no settings gear, the state badge only: the feed behind it does not serve print file names *at all*, so the part on the bed is never named to the room. Printer addresses and serial numbers are not served either. Archived printers do not appear; printers in maintenance mode still do — they are still on the farm.
- **The wall never competes with a viewer.** Your embedded viewer and a colleague's popup read one shared stream per printer, and a snapshot the TV asks for while somebody is watching is answered with that stream's frame instead of a second connection to the camera.
- **A kiosk never writes settings back.** Opening the kiosk URL in your own browser does not overwrite your own wall preferences — the URL parameters are read, not stored.
- **The token's last use is stamped** (at most once a minute), so a token idle for 30 days gets a warning chip in Settings, and an administrator's **All users** section lists every live token on the install.

## :material-alert: Pitfalls and what-ifs

!!! warning "The URL is the credential"
    Anyone who can read the URL — off the screen, out of the kiosk's config file, out of a browser history — can watch the wall. Treat it like a key: keep it out of screenshots, and revoke it the day a display is retired or a Pi goes missing.

- **A Cam Wall token opens only the wall.** It is refused by the single-camera stream endpoint and by the OBS overlay, and a Camera-stream token is refused by the wall — the scopes are walls in both directions, so a token handed to a TV cannot be repurposed to pull one printer's stream with the file name on it.
- **A Raspberry Pi has no video to decode here.** A token wall is snapshots only, so the load is the number of tiles and how often they refresh. Pick a `size` at which every camera fits the screen — nobody scrolls a TV, and off-screen tiles pause — and raise `interval` if the box or the network struggles.
- **A `full` status overlay is not available on a token wall** — it would show the file name. The URL accepts `off` or `compact`.
- **The wall cannot control a printer.** Nobody is standing at the TV; pausing and stopping stay on the Printers page and in Telegram.
- **The token is tied to nothing but time.** It is not narrowed per printer — a Cam Wall token shows every printer the wall shows. For a per-printer stream use an API key instead.

## :material-link-variant: Related scenarios

- [A night shift with nobody in the shop](unattended-night.md) — the wall shows the night; the alarms are what wake you.
- [Three phases, one bed heating per phase](three-phases.md) — the same tags colour the printer cards you see on the desk.
