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

!!! tip "go2rtc and IP cameras: warm-up-frame skip"
    Many MJPEG sources — go2rtc most notably, plus several IP cameras — emit a "warm-up" / often-black frame on the byte that follows connection accept (the encoder's last keyframe before it catches up to live content). Since 0.4.4 BamDude reads past the first frame and returns the second on every single-frame capture path (notification thumbnails, finish photo, layer-timelapse, plate detection, Obico inference). Slow / single-frame streams that don't deliver a second frame within the timeout fall back to the first so callers always get *something*. No configuration needed. If you still see black frames, raise the camera's keep-alive timeout, point BamDude at go2rtc's `/api/stream.mjpeg?src=<name>` rather than the bare camera URL, or open an issue with a packet-capture trace.

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
| **ffmpeg** | Must be installed (included in Docker image) |
| **Camera enabled** | Must be enabled in printer settings |
| **Developer Mode** | Required for camera access |

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

### Long-lived tokens for Home Assistant / Frigate / kiosks

The 60-min UI-side token is wrong shape for a wall-mounted kiosk dashboard, a Home Assistant camera entity, or a Frigate front-end that re-fetches the same URL for months. BamDude can mint **long-lived stream tokens** for those use cases:

1. **Settings → Camera → Long-lived tokens → + New token**.
2. Pick the printer(s) it covers (one token can authorise multiple cameras), an expiry (months / years / never), and an optional label (e.g. `frigate-living-room`).
3. The page shows the token **once** — copy it into your HA / Frigate / kiosk config. It won't be shown again.
4. The token grants only the camera endpoints (`/stream`, `/snapshot`, `/cover`) for the chosen printers — no other API surface.

| Property | Detail |
|---|---|
| Storage | Same `auth_ephemeral_tokens` table, with `token_type='camera_longlived'` so the regular 60-min sweeper leaves them alone. |
| Revocation | Delete the row from the long-lived tokens table — effective on the next request. There's no caching layer to wait out. |
| Audit | Each token records last-used-at + last-used-IP so you can see whether a kiosk is actually consuming it. Stale tokens (no use in 30 days) get a yellow warning chip. |
| Limit | Soft cap of 50 active tokens per install — bumping past this is admin-only via direct DB access (`auth_ephemeral_tokens` is intentionally low-friction by design). |

URL shape: `/api/v1/printers/{id}/stream?token={long_lived_token}` — same query-param contract as the short-lived flow, so HA's generic camera platform / Frigate's `mjpeg_streams` / a `<img src>` in a kiosk dashboard all work without further plumbing.

### Creation flow detail

1. **Settings → Long-lived Tokens** (under Security / API Keys).
2. Enter a descriptive name (e.g. `Home Assistant`, `Kitchen Kiosk`, `Frigate`).
3. Pick a lifetime (1–365 days, default 90 days).
4. Click **Create**.
5. The plaintext token is displayed **exactly once** in a copy-to-clipboard modal.

!!! danger "Token shown once only"
    Save the token now. BamDude stores only a hash (SHA-256) — once the modal closes, the plaintext can never be retrieved again. If you lose it, revoke the row and create a new token.

### `lookup_prefix` and audit fields

Each long-lived token row carries:

- **lookup_prefix** — first 4 characters of the token's hash, used to identify a specific row when you've forgotten which device has which token. Safe to display alongside the row label.
- **last_used_at** — timestamp of the most recent successful authenticated request with this token. Stale tokens (no activity in 30+ days) get a yellow warning chip so you can clean up dead config.
- **last_used_ip** — most recent client IP, useful for spotting unexpected use.

### Admin "All users" view

Administrators see an additional section titled **All users (admin view)** below their own tokens — it lists every active long-lived token across all users in the install. Useful for triage if a token is suspected of being leaked, or to enforce farm-wide hygiene (revoke ancient tokens that haven't been used in months).

### Maximum lifetime: 365 days (m028)

BamDude rejects "never expires" by design — a leaked permanent token would be irrevocable footgun. Maximum TTL is **365 days**, enforced server-side via the `m028` migration that adds the `long_lived_tokens` table. If you want longer-lived access, rotate tokens annually as part of your normal credential-hygiene cycle.

### Permission requirements

Creating and managing long-lived camera tokens requires the `camera:view` permission — same permission already needed for the regular 60-minute browser-side stream tokens. Default Viewers and Operators groups have it.

To delegate token management to a non-admin user, ensure they're in a group with both `camera:view` and `settings:read` (so they can reach the Settings page where tokens are managed).

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

!!! note "No login required"
    The overlay is designed for embedding and does not require authentication. Don't expose this URL publicly without thinking it through.

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

**Overlay not loading in OBS**

- Verify the URL works in a regular browser first.
- Check that OBS can reach your BamDude server (same network, no VPN restrictions).
- Right-click the source in OBS → **Refresh cache of current page**.

**Camera not showing in overlay**

- Confirm the printer is connected.
- Confirm camera streaming works in BamDude directly first — the overlay uses the same stream.
- Status updates over WebSocket; if the WS handshake fails, status falls back to polling every 2 seconds.

---

## :material-lightbulb: Tips

!!! tip "Multiple Cameras"
    In embedded mode, open multiple camera viewers simultaneously -- each remembers its own position and size.

!!! tip "Bandwidth Conservation"
    Close camera windows when not actively watching to save server resources.

!!! tip "Mobile viewing"
    Camera streaming works on mobile with full touch support — pinch to zoom, drag to pan when zoomed. Access via the camera icon on each printer card.

> Originally based on [Bambuddy](https://github.com/maziggy/bambuddy) documentation.
