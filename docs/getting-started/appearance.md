---
title: Appearance
description: Dark / Light / System theme, per-mode style, background, and accent colour — all client-side and per-device
---

# Appearance

BamDude's look is fully customisable per device from **Settings → Appearance**. Every choice is stored in the browser (`localStorage`), so each device / browser you use can look different — the theme is a display preference, never pushed to the server or shared between users.

---

## :material-theme-light-dark: Theme mode

Three modes, chosen with the three-button selector in **Settings → Appearance** (or cycled with the theme button in the sidebar, **Dark → Light → System**):

| Mode | Behaviour |
|---|---|
| **Dark** | Always dark. |
| **Light** | Always light. |
| **System** | Follows your operating system's light/dark setting and switches automatically when the OS does (via `prefers-color-scheme`). |

**System** resolves live to whichever mode your OS is currently in, and applies that mode's own style / background / accent (below). Switching your OS between light and dark at night flips BamDude with it — no reload needed.

---

## :material-palette-outline: Per-mode styling

Dark and Light each keep their **own independent** style, background, and accent — so you can, for example, run a vibrant dark theme by night and a plain light one by day, and **System** picks the right set automatically.

| Setting | Dark options | Light options |
|---|---|---|
| **Style** | Classic · Glow · Vibrant | Classic · Glow · Vibrant |
| **Background** | Neutral · Warm · Cool · OLED · Slate · Forest | Neutral · Warm · Cool |
| **Accent** | Green · Teal · Blue · Orange · Purple · Red | Green · Teal · Blue · Orange · Purple · Red |

- **Style** controls the overall surface treatment (flat *Classic*, soft-glow *Glow*, or saturated *Vibrant*).
- **Background** sets the base canvas tint — *OLED* is a true black for OLED-panel power savings; *Slate* / *Forest* are darker tinted variants.
- **Accent** recolours buttons, links, active states, and highlights.

Your dark and light selections are remembered separately and re-applied whenever that mode becomes active (including when **System** switches between them).

---

## :material-tab: Print progress in the browser tab

**Off by default.** Turn on **Show print progress in the browser tab** and the tab title carries the percentage of the print finishing soonest, while the tab icon becomes a matching progress ring in your accent colour.

A browser window parked on another screen then tells you how the farm is doing without switching to it — useful on a wall display, less so on the laptop you actually work in. That is why it is a **per-browser** preference rather than a per-account one, like everything else on this page.

Turning it off hands the tab back exactly as it was.

---

!!! note "Per-device, not per-account"
    Appearance lives in the browser, not on your BamDude user. Signing in on a new device starts from the defaults (Dark, Classic, Neutral, Green) until you customise it there. Clearing the browser's site data resets it.
