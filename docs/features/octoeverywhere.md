---
title: OctoEverywhere AI Failure Detection
description: Cloud AI print-failure detection through OctoEverywhere's Gadget API, as the farm's one failure detector
---

# OctoEverywhere AI Failure Detection

BamDude can watch running prints with [OctoEverywhere](https://octoeverywhere.com)'s cloud AI — the **Gadget API** — instead of a self-hosted [Obico](obico.md) server. Use it when there is no hardware to run Obico on, or when you already have an OctoEverywhere account. It is **off by default** and works only after you choose it.

!!! warning "Frames leave your network"
    While OctoEverywhere is the chosen detector, BamDude sends camera snapshots of the watched, running prints to OctoEverywhere's servers for analysis. Nothing is sent while another detector — or **Off** — is chosen. OctoEverywhere states that the images are deleted after the check and are not used to train its AI; see its [privacy policy](https://octoeverywhere.com/privacy#gadget-developer-api).

!!! info "Costs"
    The Gadget API has a free quota per account. Checks beyond it are billed by OctoEverywhere, not by BamDude. More printers and a shorter inspection interval use more checks.

## :material-swap-horizontal: One detector per farm

**Settings → Failure Detection** starts with the **Failure detector** field: **Off**, **Obico (self-hosted)** or **OctoEverywhere (cloud)**. The farm runs one detector at a time. The choice is saved the moment you pick it, and only an administrator can change it.

- While **Off** is chosen, both panels are shown so you can set either detector up before choosing it.
- Before you choose OctoEverywhere, the field says which printers it would watch: all of them, or the ones in its list.
- While a panel below is still saving its changes — say, a printer you just took off the list — the field waits, so a detector is never switched on with a list the server has not received yet.
- Switching detectors stops the old one before its next camera frame or API call. The new one starts watching the running prints from scratch.
- A pause or a power cut happens **once per print for both detectors together**. Switching the detector mid-print may send another notification, never a second pause.

## :material-cog: Setup

1. Get a Gadget API key at [octoeverywhere.com/gadgetapi](https://octoeverywhere.com/gadgetapi).
2. Open **Settings → Failure Detection**. In the OctoEverywhere panel, set **Credential action** to **Replace credential**, paste the key into **New credential** and press **Save connection**. The key is write-only: BamDude never shows it again, and only an administrator can change it.
3. Press **Test** to check the key. The test creates an OctoEverywhere context and uploads no frame. It uses the key in the form, or the saved key when you have not typed a new one, and saves nothing.
4. Set the rest of the panel; it saves itself:

    | Setting | Notes |
    |---|---|
    | **Confidence** | **Lowest** … **Highest**. Lower confidence warns and pauses sooner, with more false positives; higher confidence waits until the model is more certain. |
    | **Action on detected failure** | **Notify only**, **Pause print** or **Pause and cut power**. |
    | **Inspection interval (seconds)** | How often each printing printer is checked, 5–30 s. OctoEverywhere may ask for a longer pause; BamDude never checks faster than it allows. |
    | **Monitored Printers** | All printers, or a list. Only an administrator can change this list. A printer you delete leaves it. |

5. In **Failure detector**, choose **OctoEverywhere (cloud)**.

## :material-radar: How detection works

For each watched printer whose print is **running**, BamDude takes a camera frame — the same way Obico does — and uploads it to OctoEverywhere. A frame larger than 6 MiB is reduced first. Each print gets its own OctoEverywhere context, so the model judges frames over time rather than one by one.

OctoEverywhere answers with a print quality from 1 to 10 and with its own suggestions:

| Answer | Verdict | What BamDude does |
|---|---|---|
| neither | `safe` | nothing |
| **Warning suggested** | `warning` | one notification for the print, whatever the action |
| **Pause suggested** | `failure` | **Pause print** / **Pause and cut power** act — once per print; **Notify only** sends the one notification |

BamDude follows these suggestions and never sets its own threshold on the print quality. A failure still suspected three hours after the print's last notification is told again; a reminder never pauses.

A print is the run the printer reports: a pause, a resume or a late job number does not make it a new print, a new start does — also a reprint of the same file. After a reconnect, BamDude waits for the printer's first real status and starts a new analysis with a new context; a pause already done for the print is not repeated.

The action itself — the pause, the plugs and the notification — is described on the [Obico page](obico.md#how-detection-works): both detectors share it. The notification names the detector and carries the print quality.

## :material-eye: Watching it

The panel's **Status** card shows whether detection is active (OctoEverywhere chosen, a key that works, the camera worker running) and, for each running watched print, its verdict, print quality and the number of frames checked. **Recent signals** lists the last warnings and failures held in memory; restarting BamDude clears it.

On the **Printers** page the **AI** badge reads the same state for the chosen detector and adds the print quality, for example **AI Warning 4/10**. A verdict is shown only while the print runs or is paused; when the print ends or the printer disconnects, it disappears at once. **AI not watching** means the detector cannot check right now; **AI starting** means no result for this print yet.

## :material-alert-circle: When checks stop

- **The usage limit.** When OctoEverywhere reports that the account's free quota is used up, checks stop for **every** printer. The panel shows **API usage limit reached** with a link to set up billing, and the card badge reads **AI limit reached** for users who can read settings. A successful **Test** with the same key, or a restart, resumes them.
- **The key is refused or disabled.** Checks stop for every printer until you save a working key or **Test** succeeds with the same key. Testing a different key in the form never stops the saved one.
- **Temporary trouble.** A timeout, a busy service or a camera without a frame affects only that printer: it is retried with a growing delay (up to 16 minutes, or longer if OctoEverywhere asks), and its badge reads **AI not checking**.

Error messages are shown in your language; none of them contains the key.

## :material-backup-restore: Restore

A full restore from a backup ZIP turns OctoEverywhere **off** when the backup had it chosen, so a restored copy — from another farm or another time — never starts sending frames by itself. The key, the list and the other OctoEverywhere settings are kept. After the restart every administrator finds an inbox notice: turn it on again in **Settings → Failure Detection** if this is the same farm. Obico is restored as it was. See [Backup & Restore](backup.md).

A Git restore never changes the chosen detector or OctoEverywhere's printer list, and never restores the key.

## :material-shield-check: The key

The key is sent only in a request header, and only to OctoEverywhere's own `https` addresses. BamDude does not follow redirects, and the key never appears in logs, statuses or error messages. Backups contain it like the other saved credentials.
