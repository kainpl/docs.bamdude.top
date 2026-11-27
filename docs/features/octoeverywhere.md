---
title: OctoEverywhere AI Failure Detection
description: Cloud AI print-failure detection through OctoEverywhere's Gadget API, beside Obico
---

# OctoEverywhere AI Failure Detection

BamDude can watch running prints with [OctoEverywhere](https://octoeverywhere.com)'s cloud AI — the **Gadget API** — instead of a self-hosted [Obico](obico.md) server. Use it when there is no hardware to run Obico on, or when you already have an OctoEverywhere account. It is **off by default**.

!!! warning "Frames leave your network"
    While OctoEverywhere is on, BamDude sends camera snapshots of the watched, running prints to OctoEverywhere's servers for analysis. Nothing is sent while it is off. OctoEverywhere states that the images are deleted after the check and are not used to train its AI; see its [privacy policy](https://octoeverywhere.com/privacy#gadget-developer-api).

!!! info "Costs"
    The Gadget API has a free quota per account. Checks beyond it are billed by OctoEverywhere, not by BamDude. More printers and a shorter inspection interval use more checks.

## :material-swap-horizontal: Obico or OctoEverywhere

**Settings → Failure Detection** starts with the **Provider** selector: **Obico** or **OctoEverywhere**. It chooses which panel is shown; each panel has its own on/off switch in its header. One provider runs at a time: turning OctoEverywhere on turns Obico off, and the other way round. Only an administrator can turn either on or off.

## :material-cog: Setup

1. Get a Gadget API key at [octoeverywhere.com/gadgetapi](https://octoeverywhere.com/gadgetapi).
2. Open **Settings → Failure Detection** and choose **OctoEverywhere** in **Provider**.
3. Under **Gadget API key**, set **Credential action** to **Replace credential**, paste the key into **New credential** and press **Save key**. The key is write-only: BamDude never shows it again, and only an administrator can change it.
4. Press **Test** to check the key. The test creates an OctoEverywhere context and uploads no frame. It uses the key you typed, or the saved key when you have not typed one, and saves nothing.
5. Set the rest of the panel; it saves itself:

    | Setting | Notes |
    |---|---|
    | **Confidence** | **Lowest** … **Highest**. Lower confidence warns and pauses sooner, with more false positives; higher confidence waits until the model is more certain. |
    | **Action on detected failure** | **Notify only**, **Pause print** or **Pause and cut power** — the same actions as Obico's. |
    | **Inspection interval** | How often each printing printer is checked, 5–30 seconds. OctoEverywhere may ask for a longer pause; BamDude never checks faster than it allows. |
    | **Monitored Printers** | All connected printers, or a list. A printer you delete leaves it. |

6. Turn OctoEverywhere on with the switch in the panel's header.

## :material-radar: How detection works

For each watched printer whose print is **running**, BamDude takes a camera frame through its camera worker, the same way Obico does: when someone is watching the printer's live view, its frame is reused rather than opening a second camera connection. While the camera worker is unavailable, no frame is taken. A frame larger than 6 MiB is reduced first. Each print gets its own OctoEverywhere context, so the model judges frames over time rather than one by one.

OctoEverywhere answers with a print quality from 1 (worst) to 10 (best) and with its own suggestions:

| Answer | Verdict | What BamDude does |
|---|---|---|
| neither | `safe` | nothing |
| **Warning suggested** | `warning` | a notification |
| **Pause suggested** | `failure` | the configured action — **Pause print** / **Pause and cut power** — once per print; **Notify only** sends a notification |

BamDude follows these suggestions and never sets its own threshold on the print quality. A pause or a power cut always comes with a notification, and happens once per print. A problem still suggested three hours after the last notification is told again; a reminder never pauses.

A print ends when the printer reports it finished, failed or idle, or a new print starts. A pause or a reconnect keeps it, so a print that was already paused is not paused again.

The action itself — the pause, the smart plugs and the notification — is the one [Obico](obico.md#how-detection-works) uses. The notification names the provider and carries the print quality and the camera frame that was checked.

## :material-eye: Watching it

The panel's **Status** card shows **Monitoring** — **Disabled**, **Gadget API key required**, **Service unavailable**, **Waiting for the first result**, **Detection results available** or **Monitoring needs attention** — and, for each running watched print, its verdict and print quality. **Detection history** lists the last warnings and failures held in memory; restarting BamDude clears it.

On the **Printers** page the **AI** badge shows OctoEverywhere's verdict while it is the provider that is on; its tooltip carries the print quality. **AI starting** means no result for this print yet; **AI not checking** means the last check produced none, and its tooltip names the reason for users who can read settings.

## :material-alert-circle: When checks stop

- **The account.** When OctoEverywhere refuses the key, reports it disabled or restricted, or reports that the account's free quota is used up, checks stop for **every** printer. For the usage limit the panel shows **Usage limit reached.** with a link to set up billing. A successful **Test** with the same key, a new key, or a restart resumes them.
- **Temporary trouble.** A timeout, a busy service or a camera without a frame affects only that printer: it is retried with a growing delay, up to 16 minutes, or longer if OctoEverywhere asks.

No message contains the key.

## :material-backup-restore: Restore

A full restore from a backup ZIP turns OctoEverywhere **off** when the backup had it on, so a restored copy — from another farm or another time — never starts sending frames by itself. The key and the other OctoEverywhere settings are kept. After the restart every administrator finds an inbox notice: turn it on again in **Settings → Failure Detection** if this is the same farm. Obico is restored as it was. See [Backup & Restore](backup.md).

A Git restore brings back the confidence, the action, the interval and the printer list, but never turns OctoEverywhere on and never restores the key.

## :material-shield-check: The key

The key is sent only in a request header, and only to OctoEverywhere's own `https` addresses. BamDude does not follow redirects, and the key never appears in logs, statuses or error messages. Backups contain it like the other saved credentials.
