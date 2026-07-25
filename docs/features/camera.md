---
title: Camera Streaming
description: Watch your prints in real-time with MJPEG streaming
---

# Camera Streaming

Monitor your prints visually with live camera streaming directly from your Bambu Lab printer.

---

## :material-video: Live Streaming

BamDude provides MJPEG video streaming from your printer's built-in camera, or from an external network camera.

### Opening the Camera

1. Click the :material-camera: camera icon on any printer card
2. Choose between embedded overlay or separate window (configurable in Settings)
3. Stream starts automatically

### Stream Controls

| Button | Action |
|:------:|--------|
| **Live** | Real-time MJPEG video stream |
| **Snapshot** | Single still image (lower bandwidth) |
| :material-refresh: | Restart the stream |
| :material-fullscreen: | Enter fullscreen mode |

---

## :material-view-grid: Camera Wall

The Printers page has two layouts, switched with the **Cards / Cam wall** toggle in the page header. **Cam wall** replaces the printer cards with a responsive grid of camera tiles — one glance at every camera in the farm.

To conserve bandwidth and `ffmpeg` processes, the wall streams intelligently rather than opening every camera at once:

- **Only on-screen tiles go live.** An `IntersectionObserver` marks a tile "visible" once ≥40% of it is on screen — the 40% floor stops a scroll-boundary sliver from spinning up a stream.
- **Live is capped.** Up to **4** visible tiles stream live MJPEG at once (the *max live* setting, default 4 — the documented Raspberry Pi 4 ceiling), assigned in list order so the choice is stable. Visible tiles past the cap fall back to snapshots.
- **Snapshots for the rest.** Over-cap tiles refresh a still frame every **8 seconds** by default (the *snapshot interval* setting).
- **Off-screen tiles pause.** Scroll a tile out of view and it stops all network activity until it returns. Disconnected printers also render paused — no live slot is burned on a camera that has nothing to stream.

### Per-tile

Each tile shows:

- an **offline chip** when the printer isn't connected;
- an optional **status overlay** — *off*, a compact **state chip**, or **full** with progress %, layer count, and time remaining on printing/paused tiles;
- an **HMS-error badge** when the printer has active (non-noise) HMS errors;
- **click** opens that camera in your preferred viewer — embedded overlay or separate window, per your Camera settings.

### Wall settings

A gear button on the wall opens per-browser settings: **max live** (1–16), **snapshot interval** (2–60 s), and **status overlay** mode (*off* / *compact* / *full*). All three persist in the browser's local storage — they're per-device, not synced to the account, since a Pi 4 install caps the live count lower than a NUC.

!!! note "Permission"
    The Cam wall toggle needs the `camera:view` permission — the same one the camera viewer uses. Without it the toggle is disabled.

!!! tip "Shared streams, no more frozen tiles"
    Every viewer of a printer — a cam-wall tile, the embedded overlay, a popup window — subscribes to one shared fan-out stream. Closing one viewer no longer freezes another: the stream only tears down when the *last* viewer disconnects.

---

## :material-webcam: External Cameras

Connect external network cameras to replace the built-in printer camera. Useful for better angles, higher resolution, or printers in enclosures where the built-in camera is partially blocked.

### Supported types

| Type | Example URL/path |
|------|------------------|
| **MJPEG** | `http://192.168.1.50/mjpeg` |
| **RTSP** | `rtsp://192.168.1.50:554/stream` |
| **Snapshot** | `http://192.168.1.50/snapshot.jpg` |
| **USB (V4L2)** | `/dev/video0` |

### Configuration

1. **Settings** → **General** → **Camera**.
2. Find your printer in the **External Cameras** section.
3. Toggle the switch to enable.
4. Enter the camera **URL**.
5. Select the camera **Type**.
6. Click **Test** — BamDude opens the stream once, confirms a frame, then disconnects.

!!! tip "RTSP authentication"
    Embed credentials in the URL: `rtsp://user:password@192.168.1.50:554/stream`.

!!! tip "go2rtc and IP cameras: warm-up-frame skip + Snapshot URL override"
    Many MJPEG sources — go2rtc most notably, plus several IP cameras — emit a "warm-up" / often-black frame on the byte that follows connection accept (the encoder's last keyframe before it catches up to live content). Since 0.4.4 BamDude reads past the first frame and returns the second on every single-frame capture path (notification thumbnails, finish photo, layer-timelapse, plate detection, Obico inference). Slow / single-frame streams that don't deliver a second frame within the timeout fall back to the first so callers always get *something*. No configuration needed.

    **Optional: Snapshot URL override.** For **MJPEG**, **RTSP**, and **USB** types you can also fill in a separate **Snapshot URL** below the live-stream URL. When set, BamDude fetches single-frame captures (notification thumbnails, finish photos, layer timelapse, plate detection, Obico inference) from this URL via plain HTTP GET — bypassing the warm-up dance entirely. Useful for go2rtc setups (`http://<host>:1984/api/frame.jpeg?src=<name>` is a dedicated single-frame endpoint that never returns the encoder's stale keyframe) or IP cams with a `/snapshot.jpg`-style endpoint. Click **Test** next to the Snapshot URL to verify it returns a valid frame. The live-view stream always uses the main URL; the override only changes single-frame captures, since polling a snapshot endpoint at 1 fps for live view would be a regression for everyone who doesn't have this problem. Hidden when camera type is `Snapshot` — the live URL is already a single-frame endpoint, so an override would be redundant. Leave blank to use the warm-up-frame skip on the live stream.

### USB / V4L2 setup

USB webcams work via the V4L2 path on Linux hosts:

```bash
# Install device-listing tools
sudo apt install v4l-utils

# Enumerate available video devices
v4l2-ctl --list-devices
```

BamDude reads `/dev/video0` by default. If your camera is at a different node (e.g. `/dev/video2`), enter the path directly into the External Camera URL field.

For Docker, pass the device through:

```yaml
services:
  bamdude:
    devices:
      - /dev/video0:/dev/video0
```

---

## :material-movie-roll: Layer-Based Timelapse (external cameras only)

When an external camera is enabled and the printer publishes per-layer-change MQTT events, BamDude automatically:

1. **Captures a frame** each time the print's layer counter advances.
2. **Stores frames** in a temporary directory during printing.
3. **Stitches a video** with **ffmpeg** when the print completes.
4. **Attaches** the resulting timelapse to the print archive.

!!! note "External cameras only"
    Layer-based timelapse only works with external cameras (MJPEG, RTSP, Snapshot, or USB). Built-in printer cameras use the printer's own timelapse feature instead — the printer does the stitching itself and BamDude attaches the resulting MP4/AVI.

!!! note "ffmpeg required"
    Layer timelapse requires `ffmpeg` to be installed (included in the BamDude Docker image, install via `apt install ffmpeg` on bare metal).

This produces dramatically higher-quality timelapses than fixed-interval capture because each frame corresponds to a clean state of the print (head parked off the part, between layers).

---

## :material-magnify: Zoom & Pan

| Method | Action |
|--------|--------|
| **Mouse wheel** | Zoom in/out (100% - 400%) |
| **Click and drag** | Pan when zoomed |
| **Pinch gesture** | Touch device zoom |

---

## :material-cog: Technical Details

```mermaid
graph LR
    A[Printer Camera] -->|RTSP| B[ffmpeg]
    B -->|MJPEG| C[BamDude API]
    C -->|HTTP Stream| D[Browser]
```

| Requirement | Details |
|-------------|---------|
| **ffmpeg** | Must be installed (included in Docker image). Needed for the RTSP camera on the X1 / X2 / H2 / P2 series; the A1 / P1 chamber-image protocol does not use it. |
| **Camera enabled** | Must be enabled in printer settings |
| **Developer Mode** | Required for camera access |

!!! tip "Pointing at ffmpeg — `FFMPEG_PATH`"
    If `ffmpeg` is installed but not on the running service's PATH — most often a fresh Windows install whose PATH change hasn't reached an already-open shell — an RTSP camera (X1 / X2 / H2 / P2) connects but shows **no frames**. Set **`FFMPEG_PATH`** in your `.env` (or the environment) to the full path of the ffmpeg binary and BamDude uses it directly, skipping the PATH search:

    ```
    FFMPEG_PATH=C:/Users/you/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_.../bin/ffmpeg.exe
    ```

    Left unset, behaviour is unchanged (PATH + common install locations are searched). The Docker image and native installers bundle ffmpeg, so this is typically only needed for local Windows development.

---

## :material-video-box: OBS Overlay

BamDude includes a streaming overlay at `/overlay/{printer_id}` combining camera feed with real-time print status. No login required.

Customize with query parameters: `?size=large&fps=30&show=progress,eta,filename`

---

## :material-key-variant: Stream Token Gate

Camera endpoints (live stream, snapshot, cover thumbnail, plate-detection reference) are not Bearer-token-friendly -- a `<img src>` tag can't attach an `Authorization` header. BamDude routes these through a short-lived query-param token instead:

1. The frontend hits `POST /api/v1/printers/camera/stream-token` to mint a token tied to the current user (TTL 60 min).
2. The token is appended as `?token=...` to every camera URL via `withStreamToken()` in the API client.
3. Already-rendered DOM nodes (e.g. an `<img>` mounted before the token arrived) are retrofitted by `rewriteMediaSrcWithToken()`.
4. The token is keyed by `user.id` in React-Query so login/logout invalidates the cache.

Tokens are stored in `auth_ephemeral_tokens` so they survive backend restarts and work behind multi-worker deploys. Operators don't need to do anything -- this is invisible plumbing -- but the implication is that copying a camera URL out of the browser only works for the lifetime of the embedded token.

### Long-lived tokens for Home Assistant / Frigate / kiosks / OBS

The 60-min UI-side token is the wrong shape for a wall-mounted dashboard, a Home
Assistant camera entity, or a Frigate front-end that re-fetches the same URL for
months. BamDude mints **long-lived tokens** for those cases.

**Settings → API Keys → Camera API Tokens → Create new token.** Give it a name,
pick a **scope** (below) and a lifetime (1–365 days, default 90), and click
Create. The token is shown **exactly once**.

!!! danger "Shown once only"
    BamDude stores only a pbkdf2 hash, so the plaintext can never be retrieved
    again — and a stolen database dump can't be replayed against the camera
    endpoints. If you lose the token, revoke the row and create a new one.

#### Scopes

Each scope is a **separate grant**. They never widen one another, and creating
one never changes what an existing token can do.

| Scope | Reaches |
|---|---|
| **Camera stream only** | The camera stream and snapshot endpoints, nothing else. The right choice for Home Assistant, Frigate, or anything embedding a single camera. |
| **Cam Wall** | Those same streams **plus** the read-only [Cam Wall feed](#cam-wall-on-a-tv-or-kiosk): every printer's name, connection state and print progress — but **never the print filename**. |
| **Streaming Overlay** | One printer's camera stream **plus** the live print status the [OBS overlay](#obs-streaming-overlay) draws — which *does* include the filename shown on screen. |

The boundaries are deliberate and enforced in both directions: a Camera-stream
token is refused by both the Cam Wall and overlay feeds; a Cam Wall token is
refused by the overlay feed (the wall is trusted never to name the part on the
bed, so folding the two together would silently widen every wall token already
handed out) and vice versa. **None** of them exposes a printer's IP address,
serial number or access code, or reaches any other BamDude API.

#### Token properties

| Property | Detail |
|---|---|
| Format | `bblt_<prefix>_<secret>`. The 8-character `prefix` is indexed so a lookup doesn't scan the table; it's also how you tell rows apart in the UI when you've forgotten which device holds which token. |
| Storage | The `long_lived_tokens` table, separate from the 60-minute browser tokens — the ephemeral sweeper never touches these. |
| Hashing | pbkdf2_sha256 over the full token, same as the rest of the codebase's password hashing. |
| Maximum lifetime | **365 days.** "Never expires" is rejected by design: a leaked permanent token would be an irrevocable footgun. Rotate annually as part of normal credential hygiene. |
| Audit | `last_used_at` is stamped on each successful use (rate-limited to once a minute, so an MJPEG keep-alive doesn't hammer the DB). Tokens idle for 30+ days get a warning chip. |
| Revocation | Effective on the next request — there is no caching layer to wait out. |
| Scope of a token | **All printers.** These tokens are not narrowed per printer; a Camera-stream token can pull any printer's stream. Use the per-printer [API keys](api-keys.md) if you need that narrowing. |

Administrators see an extra **All users** section listing every active token in
the install — useful for triage if one is suspected of being leaked, or to
enforce farm-wide hygiene.

Creating and managing these tokens needs the `camera:view` permission — the same
one already required for the ordinary browser-side stream tokens. Default Viewers
and Operators groups have it. To delegate management to a non-admin, put them in
a group with both `camera:view` and `settings:read` (so they can reach Settings).

URL shape: `/api/v1/printers/{id}/camera/stream?token=<token>` — the same
query-param contract as the short-lived flow, so Home Assistant's generic camera
platform, Frigate's `mjpeg_streams`, or a plain `<img src>` all work with no
further plumbing.

### Cam Wall on a TV or kiosk

The Cam Wall has its own URL, so you can bookmark it or point a wall-mounted
screen at it:

```
http://your-bamdude:8000/camwall
```

Opened in a browser you're signed in to, that's the same wall the Printers page
shows — tiles stay clickable and the settings popover works as usual.

A TV or a Raspberry Pi in kiosk mode has no login, so it authenticates with a
**Cam Wall**-scoped token in the URL instead:

```
http://your-bamdude:8000/camwall?token=bblt_<prefix>_<secret>
```

A token wall is deliberately reduced to what a passive display needs:

- **No settings popover, no click-through.** Nobody is standing at a TV.
- **Compact status overlay only.** The state badge is shown; the print filename
  is not. The feed behind the page doesn't serve filenames *at all*, so the part
  on the bed is never named to a room anyone can walk into.
- **No printer addresses or serial numbers**, for the same reason.
- **Archived printers don't appear.** Printers in maintenance mode still do —
  they're still on the farm.

Because a kiosk browser is awkward to configure (you can't open devtools on a
wall-mounted TV), the wall's settings can come from the URL:

| Parameter | Meaning | Range |
|---|---|---|
| `maxLive` | How many tiles stream live at once; the rest poll snapshots | 1–16 |
| `interval` | Seconds between snapshot refreshes on non-live tiles | 2–60 |
| `status` | Status overlay: `off` or `compact` (a token wall cannot select `full`) | — |

```
http://your-bamdude:8000/camwall?token=bblt_…&maxLive=9&interval=10
```

Out-of-range or unreadable values fall back to the defaults rather than producing
a wall you can't fix from the same URL. A kiosk never writes these back to the
browser, so opening a kiosk link once won't overwrite your own wall preferences.

!!! warning "The URL is the credential"
    Anyone who can read that URL — off the screen, out of the browser history,
    out of the kiosk's config file — can watch the wall. Treat it like a key. If
    a display is retired or compromised, revoke the token and the wall goes dark
    on its next request.

### Revoking a token

1. **Settings → Long-lived Tokens**.
2. Find the row by name or by `lookup_prefix`.
3. Click **Revoke**, confirm in the modal.

Any device using that token loses access on the next request — no grace period, no caching layer to wait out. The row's hash is removed from the DB so even DB-dump replay won't work.

---

## :material-image-frame: Cover Thumbnails

`GET /api/v1/printers/{id}/cover` returns the thumbnail of whatever the printer is *currently* printing. It is served exclusively from the local archive directory -- BamDude never initiates an FTP download from this endpoint. While a print is active and the archive's 3MF hasn't been backfilled yet (e.g. a printer-side print where the FTP recovery loop hasn't caught up), the endpoint returns 404 and the UI falls back to a generic placeholder. Once `archive_download_retry` lands the 3MF, the endpoint starts returning the real PNG without any client action.

---

## :material-application: Embedded vs Window Mode

The camera viewer has two modes, configurable per-user in **Settings > Camera**:

- **Embedded** (default) -- The viewer overlays directly on top of the printer card. Multiple printers can have their cameras open at once and each viewer tracks its own size/position via local state. The page header's status bar continues to drive the rest of the UI.
- **Window** -- The viewer launches in a separate browser window (or PWA window). Useful for parking a single camera on a second monitor.

Embedded is the right default for live monitoring; window mode is for setups where the camera lives on a different screen from the printer dashboard.

### Embedded viewer features

When using embedded mode, the camera appears as a floating window with the following affordances:

- **Draggable** — click and drag the header to reposition.
- **Resizable** — drag the bottom-right corner to resize.
- **Persistent position** — position and size are remembered per printer across sessions.
- **Navigation persistence** — open cameras stay open when you navigate away from the Printers page and back.
- **Minimize** — click the minimize button to collapse to the title bar.
- **Close** — click X to close the viewer.
- **Multi-viewer** — open cameras for multiple printers simultaneously, each with its own remembered position and size.

!!! tip "Embedded mode for the whole farm"
    Embedded mode keeps you on the main screen while monitoring prints — no need to switch between browser windows. Open multiple viewers to monitor your entire print farm at once.

---

## :material-tune: Snapshot mode & FPS settings

For lower bandwidth, switch the per-camera mode to **Snapshot** instead of **Live**:

- Captures a single frame on demand, click refresh to fetch a new one.
- Ideal for cellular connections, slow networks, or cheap kiosks that don't need motion.

The default frame rate for live mode is 15 FPS. Tune via the URL `?fps=N` parameter or the per-camera setting:

| FPS | Use case |
|-----|----------|
| **5** | Low bandwidth / A1/P1 cameras (hardware limit) |
| **10–15** | Balanced (15 is default) |
| **20–25** | Smoother video |
| **30** | Maximum quality (X1 / H2 / P2 only — also works for USB) |

!!! note "FPS limits by camera type"
    - **External cameras** — capped at 15 FPS.
    - **A1 / P1 printers** — capped at 5 FPS (hardware limitation).
    - **X1 / H2 / P2 printers** — up to 30 FPS.

!!! note "Higher FPS = more bandwidth"
    Higher frame rates consume more network bandwidth and server resources — for a multi-printer farm running 30 FPS on every viewer at once, plan accordingly.

---

## :material-connection: Stream cleanup & auto-reconnect

BamDude properly cleans up camera streams to prevent orphaned `ffmpeg` processes:

- **Window close** — stream stops automatically.
- **Tab hidden** — stream pauses to save resources.
- **Page unload** — `ffmpeg` process terminated.
- **Refresh** — old stream stopped, new one started.

### Stall detection

The browser periodically checks if the stream is still receiving frames:

- **Check interval** — every 5 seconds.
- **Detection** — compares last frame timestamp.
- **Threshold** — stalled if no new frames received for **>5 seconds**.

### Automatic recovery

When a stall is detected:

1. Detects no frames received within threshold.
2. Closes the stalled connection.
3. Reconnects automatically.
4. Resumes streaming.

!!! tip "Network blips"
    If your network briefly drops, the stream will automatically recover once the connection is restored — no manual intervention needed.

---

## :material-stethoscope: Camera diagnostics

When a camera won't stream, BamDude can run a built-in diagnostic that tests the connection stage by stage and tells you *which* link in the chain is broken. A **Diagnose** button sits next to **Retry** on the viewer's error state, and a small stethoscope icon lives in the always-visible control bar (between :material-refresh: Refresh and :material-fullscreen: Fullscreen) for a pre-flight check before you even start streaming.

It calls `POST /api/v1/printers/{id}/camera/diagnose` and shows the results inline in a modal: one row per stage with a pass / fail / skipped marker, the per-stage duration in milliseconds, and a translated remediation hint. A **Run again** button re-runs the whole check without closing the modal.

### Stages

| Stage | What it checks |
|-------|----------------|
| **`tcp_reachable`** | Opens a raw TCP socket to the camera port — `322` for RTSPS, `6000` for chamber-image — with a 3-second timeout. It distinguishes a **timeout** ("printer not reachable"), a **refused** connection ("camera port closed — check LAN-Only Mode + Developer Mode"), and a **host-unreachable** error. |
| **`first_frame`** | Captures one JPEG end-to-end with a 15-second timeout, using the same pipeline that powers `/camera/snapshot`. Proves the full path actually delivers an image, not just an open port. |

!!! note "Live-stream shortcut"
    If a viewer is already watching the camera **and** the buffered last frame is fresher than 10 seconds, the diagnostic skips the real test and reports the stream as live / healthy. Opening a fresh socket would kick the live viewer off on firmwares that allow only a single camera connection — so when there's already proof the camera works, BamDude doesn't disturb it.

The result also carries metadata for support triage: the protocol (`rtsp` / `chamber_image`), the port, the profile in use (`default` or a model-specific name), and a summary code.

---

## :material-image-area: Camera Snapshot on Print Complete

BamDude can automatically capture a camera snapshot when prints complete:

1. **Settings → General**.
2. Enable **Capture snapshot on print complete**.
3. Snapshots are saved to the print's archive folder and surface in the archive's photo gallery.

This creates a visual record of every completed print — paired with the timelapse and finish photo, you've got a full visual log of farm output.

---

## :material-scan-helper: Build Plate Empty Detection

Automatically detect if objects are left on the build plate before a print starts. If detected, the print is paused and a notification fires.

### How it works

1. **Calibrate** — capture reference images of your empty build plate.
2. **Enable** — toggle plate detection on for the printer.
3. **Auto-check** — when any print starts, BamDude compares the current camera view to your references.
4. **Auto-pause** — if objects are detected, the print is immediately paused.

### Calibration

Store up to **5 reference images** per printer for different plate types (textured, smooth, high-temp, etc.):

1. Click the **scan icon** on the printer card to open the modal.
2. Ensure the build plate is **completely empty** and **chamber light is ON**.
3. Click **Calibrate Empty Plate**.
4. Optionally add a label (e.g. `Textured PEI`, `Cool Plate`).
5. Repeat for each plate type you swap between.

!!! tip "Multiple references"
    The system automatically selects the best-matching reference when checking. Calibrate every plate type you actually use for accurate detection.

### Enabling detection

The printer card has a **split button**:

| Button part | Action |
|-------------|--------|
| **Main (scan icon)** | Toggles detection on/off. |
| **Chevron (▼)** | Opens the calibration / management modal. |

When enabled, the button shows a green border.

### ROI (Region of Interest) editor

Adjust which part of the camera view is analysed:

1. Open the plate-detection modal.
2. Scroll to **Detection Area (ROI)**.
3. Click **Edit**.
4. Use the X / Y / Width / Height sliders to size and position the green ROI box.
5. Save.

The green box in the preview shows the detection area. Focus it on the build plate to avoid false positives from the printer frame, AMS unit, or background.

### Detection mechanics

1. Captures the current camera frame (or uses the buffered frame if a stream is active).
2. Applies heavy Gaussian blur to both current and reference images.
3. Normalises both for consistent comparison.
4. Extracts the ROI region.
5. Calculates pixel-difference percentage.
6. If difference > 1%, plate is considered "not empty".

### Notifications when objects detected

- Print pauses immediately.
- Toast notification appears in BamDude.
- Push notification sent (Telegram / Discord / Email / Pushover / ntfy / HA — whatever you have wired up).
- WebSocket event broadcast for integrations.

### Requirements

| Requirement | Details |
|-------------|---------|
| **OpenCV** | `opencv-python-headless` (already installed in the Docker image). |
| **Chamber light** | Should be ON for reliable detection. |
| **Calibration** | At least one reference image required. |

### Troubleshooting

**False positives (detects objects when plate is empty)**

- Calibrate with chamber light ON (same as during prints).
- Adjust the ROI to exclude printer frame edges and AMS units.
- Add multiple calibrations for different lighting conditions.

**False negatives (doesn't detect objects)**

- Ensure chamber light is ON.
- Recalibrate — plate surface may have changed (resin residue, sticker peel, scratches).
- Confirm objects are within the ROI area — anything outside the green box is ignored by design.

---

## :material-help-circle: Troubleshooting

**Stream won't start**

1. Is the printer on? Camera requires power.
2. Is the camera enabled in printer settings?
3. Is `ffmpeg` installed? (Included in the Docker image.)
4. Is Developer Mode enabled? (Required for camera access on Bambu printers.)
5. For external cameras, verify the URL with `curl` from inside the BamDude host: `curl -I http://192.168.1.50/mjpeg`.
6. Running in Docker? If default bridge networking doesn't reach the printer, switch to `network_mode: host`.

**Stream freezes**

- Network congestion or WiFi drops — try lowering FPS to 5 or 10.
- Check the printer's WiFi signal strength (poor signal causes erratic frame delivery).
- Try snapshot mode instead — it doesn't depend on a continuous stream.

**High latency (1–3 second lag)**

This is normal for MJPEG over HTTP and stems from RTSP buffering, ffmpeg processing pipeline, and HTTP-stream chunk boundaries. Cannot be eliminated entirely. Reduce by:

- Lowering FPS to reduce per-frame buffering.
- Using snapshot mode for monitoring vs streaming.
- Switching to an external camera with hardware MJPEG output (skips the RTSP→MJPEG transcoding).

**Black screen**

- Camera may be initialising — wait 5–10 seconds and refresh.
- Confirm camera works in Bambu Studio first; if it fails there, it's a printer-side issue, not BamDude.
- Check user-permission grants — `camera:view` is required.

**Docker: camera not working**

If camera streaming doesn't work in Docker, try host networking:

```yaml
services:
  bamdude:
    network_mode: host
    # remove the ports: section when using host mode
```

Default bridge networking with NAT works in most setups. Host mode is only needed when your network configuration prevents NAT'd traffic from reaching the printer's RTSP port.

---

## :material-api: API endpoints

For developers and integrations:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/printers/{id}/camera/stream` | GET | MJPEG live stream. |
| `/api/v1/printers/{id}/camera/snapshot` | GET | Single JPEG frame. |
| `/api/v1/printers/{id}/camera/stop` | POST | Stop active streams for the printer. |
| `/api/v1/printers/{id}/camera/test` | GET | Test camera connection (returns success/failure without streaming). |
| `/api/v1/printers/camera/stream-token` | POST | Mint a 60-min query-param stream token (see Stream Token Gate above). |

### OBS Browser Source recipe

Embed the live stream in OBS as a Browser Source:

1. In OBS, click **+** under Sources.
2. Select **Browser**.
3. URL: `http://your-bamdude:8000/api/v1/printers/{id}/stream?token=<long-lived-token>` (use a **long-lived camera token** — short-lived ones expire mid-stream).
4. Width / height to match your scene (e.g. 1920×1080).
5. **OK**.

For a richer overlay with status text, see the next section.

---

## :material-video-box: OBS Streaming Overlay

The dedicated overlay page combines the camera feed with real-time print status — one Browser Source instead of separate camera + text sources. URL shape:

```
http://your-bamdude:8000/overlay/{printer_id}
```

!!! warning "OBS needs a token"
    Everything the overlay draws — print status, printer name, the camera feed —
    is behind authentication. It works in a browser where you are **already
    signed in**, but OBS is a fresh browser with no session, so the plain URL
    above renders a blank overlay.

    This has nothing to do with *how* you reach the server: a reverse proxy,
    Cloudflare Tunnel or remote domain changes nothing, and an incognito window
    fails identically. What OBS needs is a token.

### Streaming Overlay token

1. **Settings → API Keys → Camera API Tokens.**
2. Create a token with the **Streaming Overlay** scope and copy it.
3. Append it to the overlay URL, with the printer number matching the printer's
   own URL on the Printers page (`/overlay/1` is printer 1, and so on):

```
http://your-bamdude:8000/overlay/1?token=bblt_<prefix>_<secret>
```

In token mode the overlay skips the WebSocket entirely and refreshes on a 2-second
poll — the token can't open a WebSocket, and the poll is the feed.

!!! warning "Treat the URL like a key"
    Anyone who can read that URL can watch the printer's stream and see the print
    filename. It cannot reach the printer's address, serial number or access
    code, and it cannot enumerate your other printers — a Streaming Overlay token
    opens one printer's overlay and nothing else. Revoke it from the same
    Settings page to cut the overlay off.

### What's included

| Element | Description |
|---------|-------------|
| **Camera feed** | Full-screen live camera view. |
| **BamDude logo** | Branding in the top-right corner. |
| **Filename** | Current print file name. |
| **Status** | Printing, Paused, Idle, etc. |
| **Progress bar** | Visual progress with percentage. |
| **Layer count** | Current layer / total layers. |
| **Time remaining** | Estimated time left. |
| **ETA** | Estimated completion time. |

### Customising via query parameters

| Param | Values | Effect |
|-------|--------|--------|
| `size` | `small` / `medium` / `large` | Text and logo scale. `medium` is default. |
| `fps` | `1`–`30` | Live-stream FPS. Clamped server-side per camera type. |
| `camera` | `true` (default), `false`/`0` | `false` hides the camera feed and shows status on a black background. |
| `show` | comma-separated: `progress`, `layers`, `eta`, `filename`, `status`, `printer` | Which status elements appear. |

Examples:

```
# Compact corner overlay with full status
/overlay/1?size=small&show=progress,layers,eta,filename,status

# Status-only display, no camera (low-bandwidth scenario)
/overlay/1?camera=false&show=progress,eta,status

# Maximum quality, full screen
/overlay/1?size=large&fps=30&show=progress,layers,eta,filename,status,printer
```

### Idle state

When no print is running, the overlay still works — it shows the camera feed plus an "idle" / "offline" message and the BamDude logo. Useful for streaming farm cleanup, plate swaps, or off-hours.

### Troubleshooting overlay

**Overlay blank in OBS but fine in your browser**

- This is almost always a **missing token**. Your browser is signed in; OBS is
  not. Add `?token=…` with a **Streaming Overlay** token — see above.
- Verify the URL in a **private / incognito** window, not your normal one. If it
  fails there, it will fail in OBS for the same reason.

**Overlay not loading at all**

- Check that OBS can reach your BamDude server (same network, no VPN restrictions).
- Right-click the source in OBS → **Refresh cache of current page**.

**Camera not showing in overlay**

- Confirm the printer is connected.
- Confirm camera streaming works in BamDude directly first — the overlay uses the same stream.
- Signed in, status updates over WebSocket; in token mode it always polls every
  2 seconds instead (a token can't open a WebSocket).

---

## :material-lightbulb: Tips

!!! tip "Multiple Cameras"
    In embedded mode, open multiple camera viewers simultaneously -- each remembers its own position and size.

!!! tip "Bandwidth Conservation"
    Close camera windows when not actively watching to save server resources.

!!! tip "Mobile viewing"
    Camera streaming works on mobile with full touch support — pinch to zoom, drag to pan when zoomed. Access via the camera icon on each printer card.

> Originally based on [Bambuddy](https://github.com/maziggy/bambuddy) documentation.
