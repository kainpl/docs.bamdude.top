---
title: Mobile & PWA
description: Use BamDude on phones and tablets — install as a Progressive Web App, stream cameras, and manage prints from anywhere
---

# Mobile & PWA

BamDude's frontend is fully responsive and ships as an installable **Progressive Web App (PWA)**. There is no native iOS/Android app — the web app is the app, and on Chromium / iOS Safari it can be added to your home screen for a fullscreen, app-like experience.

This page covers what works on a phone, how to install the PWA, browser compatibility, and the gotchas around HTTPS, push, and remote access.

---

## :material-check-all: What works on mobile

The whole UI is touch-friendly and responsive — there are no "desktop-only" pages.

| Area | Mobile support |
|------|----------------|
| Printer cards & live status | Yes — cards collapse to compact mode below 768px |
| Camera streams (MJPEG / snapshot) | Yes — same endpoints as desktop |
| Print queue management | Yes — drag-and-drop works with touch |
| Archive browser & detail view | Yes — long-press for context menu |
| Library / file manager | Yes |
| Stats dashboards | Yes — charts reflow to a single column |
| Notifications setup | Yes |
| Settings | Yes |

!!! tip "Bottom-nav bar in portrait"
    On phone-sized portrait viewports a compact nav bar replaces the desktop sidebar. The hamburger / drawer expands the full menu.

---

## :material-download: Installing the PWA

BamDude's `manifest.json` declares `display: standalone`, theme color, icons, and four launch shortcuts (Printers, Archives, Queue, Projects) so installed app shortcuts appear on long-press of the home-screen icon (Android).

### iOS Safari (Add to Home Screen)

1. Open BamDude in **Safari** (other iOS browsers can't install PWAs).
2. Tap the **Share** button (square with up-arrow).
3. Scroll down and tap **Add to Home Screen**.
4. Edit the name if you want, then tap **Add**.

The app launches fullscreen with no browser chrome.

### Android Chrome / Edge (Install app)

1. Open BamDude in Chrome or Edge.
2. Tap the **three-dot menu**.
3. Tap **Install app** (or **Add to Home Screen** on older Chromium).
4. Confirm with **Install**.

### Desktop (Chrome / Edge)

Look for the install icon (small computer with down-arrow) in the address bar, or use **Menu → Install BamDude…**. The installed app behaves like any other desktop app — pinnable, alt-tab-able, and with its own window.

---

## :material-lock: HTTPS prerequisite

PWA features (install prompt on Chromium, service worker, offline cache) require **HTTPS or `localhost`**. If you only access BamDude over plain HTTP at e.g. `http://192.168.1.50:8000`:

- The Chrome / Edge install prompt **will not appear** (Safari iOS is more permissive — Add to Home Screen still works over HTTP).
- The service worker still registers on `localhost`, but not on plain-HTTP LAN IPs in newer Chromium.

For LAN deployments you have two clean options:

- **Reverse proxy with TLS** — put nginx, Caddy, or Traefik in front of BamDude and let it terminate HTTPS. See [Reverse proxy & HTTPS](reverse-proxy.md).
- **Tailscale** — reach BamDude (and its virtual printers) over your tailnet with no port-forward. BamDude can show a VP's tailnet address to paste into a slicer; the slicer's own CA import is still required. See [Tailscale](../features/tailscale.md).

Both paths give you a real `https://…` URL that satisfies the PWA install requirement and unlocks every modern browser feature.

---

## :material-web: Browser compatibility

| Browser | Install | Offline cache | Web Push |
|---------|:-------:|:-------------:|:--------:|
| Chrome / Edge (Android) | Yes (HTTPS) | Yes | Yes |
| Chrome / Edge (Desktop) | Yes (HTTPS) | Yes | Yes |
| Safari (iOS 16.4+) | Yes | Yes | Yes (limited) |
| Safari (iOS < 16.4) | Yes | Yes | No |
| Safari (macOS 16.4+) | Yes | Yes | Yes |
| Firefox (Android / Desktop) | No | Yes | No (no Web Push) |

!!! note "Firefox doesn't ship Web Push for sites"
    Firefox's "install" UX is also gone on desktop. The site still works fine in Firefox — you just won't get an icon on the home screen / dock.

---

## :material-bell: Push notifications

BamDude supports several notification channels — most users on mobile run one of the always-online ones rather than relying on browser Web Push:

- **Telegram** — most popular for mobile; the bot pushes through Telegram's app, no PWA install needed.
- **ntfy** — install the ntfy app, subscribe to your topic.
- **Pushover**
- **Discord**, **Email**, **Home Assistant**, **WhatsApp** (via CallMeBot).

Configure them in **Settings → Notifications**. See [Notifications](../features/notifications.md) for per-channel setup.

!!! tip "Why Telegram beats browser push for printers"
    Browser Web Push depends on the device + browser staying registered. Telegram is a separate background service and survives reboots, browser cache wipes, and PWA reinstalls without re-subscribing.

---

## :material-camera: Camera streams on mobile

The same MJPEG / snapshot URLs that work on desktop work on mobile. Streams render inside `<img>` tags with short-lived stream tokens that the frontend rotates automatically.

Some platform quirks to know about:

- **iOS Safari** pauses background tabs after roughly 60 seconds — when you bring the tab back to the foreground the stream reconnects automatically (the stream-token sync hook re-runs on focus).
- **Cellular data** — MJPEG streams burn roughly 5 MB/min depending on resolution and FPS. Consider lowering FPS in **Settings → Camera** or using the snapshot view if you're on a metered connection.
- **Service worker** intentionally does **not** cache `/camera/stream` or `/camera/snapshot` — Safari's SW had streaming-response bugs, so these go straight to the network.

---

## :material-vpn: Remote access (away from your LAN)

To use BamDude from outside your home network you need one of:

| Approach | Setup effort | Best for |
|----------|--------------|----------|
| **VPN home (WireGuard / OpenVPN)** | Medium | Self-hosters who already run a VPN gateway |
| **Tailscale** | Easy | Most users — zero firewall config, automatic HTTPS via MagicDNS |
| **Public reverse proxy + TLS** | Medium | Users with a real domain who want browser-direct access |

See:

- [Tailscale](../features/tailscale.md) — recommended path; gives every device on your tailnet HTTPS access without exposing anything to the public internet.
- [Reverse proxy & HTTPS](reverse-proxy.md) — for users who want a public `https://printer.example.com` URL.

!!! danger "Don't expose plain HTTP to the internet"
    BamDude's auth is robust, but plain HTTP leaks every login over the wire. If you go public, terminate TLS at a proxy or use Tailscale.

---

## :material-cloud-off: Offline cache

The service worker (`/sw.js`) caches the app shell — HTML, JS, CSS, icons — using a network-first strategy for HTML/JS/CSS and cache-first for images. When the network drops:

- **The UI loads** from cache, so you can still navigate the app shell.
- **Live data** (printer status, queue, archives list) is read-only and stale — the WebSocket reconnects automatically when the network comes back.
- **API calls** return a `503 {"error": "offline"}` response so the UI can show offline placeholders.

This is enough to glance at "what was on screen last" without internet, but it isn't an offline mode for actual operations.

---

## :material-battery-alert: Battery & data tips

- **Close camera streams** when you aren't actively monitoring — they're the single biggest battery + data drain.
- **Lower stream FPS** in **Settings → Camera** if you don't need 30 fps for casual checking.
- **Use Wi-Fi** for live monitoring; switch to snapshot-only view on cellular.
- **Telegram > browser tab** for "did the print finish?" alerts — keeps the BamDude tab from sitting open burning battery.

---

## :material-alert-octagon: Limitations

- **No native iOS/Android app** — there is only the PWA. The Bambu Handy app is unrelated to BamDude.
- **iOS Web Push** has tighter background limits than desktop and only works on iOS 16.4+ with the PWA installed (not from a regular Safari tab).
- **Private / incognito mode** in some browsers disables service-worker registration, which means no install prompt and no offline cache.
- **No native share-target upload yet** — you can't "Share to BamDude" a 3MF from another app today. Upload via the in-app file manager or virtual printer FTP instead. See [File manager](../features/file-manager.md).

---

## :material-wrench: Troubleshooting

??? note "Add to Home Screen / Install option missing"
    - On Chrome / Edge make sure you're on **HTTPS** — see [HTTPS prerequisite](#https-prerequisite) above.
    - Make sure you're on the BamDude origin itself, not a docs preview at `docs.bamdude.top`.
    - Reload the page so the manifest and service worker register before triggering install.
    - On Android in private mode the install option is suppressed by Chrome.

??? note "Push notifications never arrive"
    - Browser permission must be **Allowed** for the site (check site settings).
    - Check the browser version — iOS < 16.4 has no Web Push at all.
    - Easier path: use [Telegram or ntfy](../features/notifications.md) instead — they don't depend on browser push subscriptions surviving cache clears.

??? note "Camera shows a black box on mobile after returning from background"
    - The stream token in the cached service worker may have expired. Pull-to-refresh once and the new token is fetched.
    - On iOS Safari this is normal behaviour after a long background pause — the stream auto-reconnects.

??? note "Login redirects in a loop after installing the PWA"
    - Clear the PWA's site data: long-press the icon → App info → Storage → Clear, then reopen.
    - This is almost always a stale refresh-token cookie from before you installed.

---

## :material-arrow-right: Next steps

<div class="quick-start" markdown>

[:material-bell-ring: **Notifications**<br><small>Telegram, ntfy, push, and more</small>](../features/notifications.md)

[:material-shield-lock: **Reverse proxy & HTTPS**<br><small>Get a real https:// URL on your LAN</small>](reverse-proxy.md)

[:material-server-network: **Tailscale**<br><small>Easiest path to remote access</small>](../features/tailscale.md)

[:material-camera: **Camera streaming**<br><small>What works, what costs bandwidth</small>](../features/camera.md)

</div>
