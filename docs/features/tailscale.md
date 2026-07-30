---
title: Tailscale (private tailnet) integration
description: Show a virtual printer's tailnet address so a slicer off your LAN can reach it — no port-forward, no VPN gymnastics
---

# Tailscale integration

BamDude can surface a [virtual printer](virtual-printer.md)'s **tailnet address** — its `100.x.x.x` IP and MagicDNS name — so a slicer running somewhere else on your [Tailscale](https://tailscale.com/) network can connect to it. No port-forward, no extra VPN client, no exposing anything to the public internet.

This is **opt-in per VP**, and it is purely a display of the address to paste into your slicer. It does not change how the VP is secured.

---

## :material-lan-disconnect: When this matters

The shipped alternative — [VP `proxy` mode](virtual-printer.md#modes) — works for remote printing too, but funnels every byte through BamDude's own TCP relay. Tailscale's wire-level mesh is faster (direct peer-to-peer when possible, DERP-relayed otherwise) and lets the slicer talk to the VP as if it were on the same LAN.

| Scenario | Recommended path |
|---|---|
| Slicing on a laptop on the same LAN as BamDude | Plain VP, no Tailscale needed. |
| Slicing on a laptop / phone *off-network* (cafe, on holiday) | Tailscale. |
| Slicing from a CI / GitHub Actions runner | VP `proxy` mode (Tailscale on a VM is overkill). |
| Multi-tenant cloud → BamDude bridge | VP `proxy` mode + your existing TLS. |

Tailscale shines specifically when **the slicer-running machine is already on Tailscale anyway** and you want it to reach the printer directly.

---

## :material-package-variant: Prerequisites

1. **Tailscale daemon on the BamDude host.** BamDude never runs `tailscaled` itself — it reads the host's. Install [tailscaled](https://tailscale.com/kb/1031/install-linux) and run `tailscale up`.

2. **Docker only: mount the daemon socket.** The BamDude image **bundles the `tailscale` CLI**, but the CLI can only talk to a daemon through its socket, which lives on the host:

    ```yaml
    services:
      bamdude:
        volumes:
          - /var/run/tailscale/tailscaled.sock:/var/run/tailscale/tailscaled.sock
    ```

    You may also need to let the container's user talk to the daemon:

    ```bash
    sudo tailscale set --operator=$(id -un)
    ```

    The mount is present but commented out in the shipped `docker-compose.yml` — uncomment it. Native installs need nothing extra: they use the host's own CLI and socket directly.

3. **MagicDNS** enabled on your tailnet (a toggle on the [Tailscale admin DNS page](https://login.tailscale.com/admin/dns)), if you want the friendly `*.ts.net` hostname alongside the raw IP. The IP works without it.

4. **A virtual printer.** The toggle is *per VP*.

---

## :material-cog-outline: Enabling per VP

On the virtual printer's card, switch on **Show Tailscale endpoint**. When the host's daemon is reachable, the card then lists the tailnet IPs and the MagicDNS name, each with a copy button.

Paste the **IP** into your slicer's *Add Printer* dialog.

!!! tip "Use the IP, not the hostname"
    Bambu Studio and OrcaSlicer's Add Printer dialog accepts an IP address, not a hostname. The MagicDNS name is shown because it's useful elsewhere (bookmarks, SSH, your own notes), but the field the slicer wants is the `100.x.x.x` address.

The toggle is per-VP because some installs want VP-A on the LAN (factory floor) and VP-B reachable over the tailnet (remote slicer for the engineering team) **simultaneously**.

---

## :material-certificate: Certificates: unchanged by Tailscale

**Tailscale changes network reach only. It does not change the VP's TLS trust.**

You still import BamDude's CA certificate (`bbl_ca.crt`) into your slicer once, exactly as you would for a LAN VP — see [Virtual Printer](virtual-printer.md).

!!! info "Why there's no Let's Encrypt path"
    An earlier version of this integration provisioned real Let's Encrypt certificates via `tailscale cert` and advertised the tailnet FQDN over SSDP, so the slicer would trust the VP without importing anything. **That was removed**, because it cannot work: Bambu Studio and OrcaSlicer validate a printer's MQTT connection **only against their own bundled Bambu CA store**, not the system trust store. A publicly-signed chain is rejected at the issuer check, before any hostname logic runs — and their Add Printer dialog takes an IP anyway, which a `*.ts.net` certificate would never match.

    So the one-time CA import is unavoidable, and Tailscale's role is strictly network reach: the same trust burden as plain LAN.

---

## :material-shield-key: Permissions & security

- **No new BamDude permissions.** The per-VP toggle is part of the existing virtual-printer update permission; reading the tailnet status needs `settings:read`.
- **No Tailscale auth surface in BamDude.** Who is on the tailnet is entirely Tailscale's business. BamDude runs `tailscale status --json` and reads the answer; it never authenticates, joins, or modifies anything.
- **The VP access code still applies.** Tailscale brings the network to the printer; the access code still gates the printer.
- **The subprocess environment is stripped.** BamDude invokes the CLI with only the OS/shell variables it needs to find its socket and config — application secrets (JWT keys, database URL, SMTP password) are not passed through.

---

## :material-alert-circle-outline: Caveats

- **`tailscaled` must run on the host.** The BamDude image ships the CLI but deliberately not the daemon: tailscaled wants raw netlink, a state directory, and an auth flow that don't compose well with a stateless container. Mounting the host's socket is both lower-blast-radius and respects the Tailscale setup you already have.
- **Private tailnets only.** There is no path here to advertise a VP to the public internet — that is what `proxy` mode is for.
- **Display only.** Turning the toggle off doesn't disconnect anything; it just stops showing the address. Nothing about the VP's certificates, SSDP advertisement, or lifecycle depends on it, and flipping it never restarts the VP.

---

## :material-bug-outline: Troubleshooting

The card shows Tailscale as unavailable, or the toggle reveals nothing:

| Symptom / log message | Cause | Fix |
|---|---|---|
| `tailscale binary not found` | Native install without the CLI. (Docker images ship it.) | Install [tailscale](https://tailscale.com/kb/1031/install-linux) on the host. |
| `Running in Docker but /var/run/tailscale/tailscaled.sock is not mounted` | One-time hint at startup: the CLI is present but has no daemon to talk to. | Add the socket mount shown in [Prerequisites](#prerequisites). |
| The socket is mounted but the CLI still can't reach the daemon | The container's user isn't permitted to use it. | `sudo tailscale set --operator=<container-user>` on the host. |
| `Tailscale not connected (no DNSName)` | Daemon is up but the host hasn't joined a tailnet. | `tailscale up` on the host and authenticate. |
| No MagicDNS name, only IPs | MagicDNS off on the tailnet. | Enable it at [login.tailscale.com/admin/dns](https://login.tailscale.com/admin/dns). The IP still works. |
| Card reports unavailable, logs show a timeout | A wedged `tailscaled` — the CLI call is bounded at 5 seconds. | Restart the daemon on the host. |

The status call never raises: whatever goes wrong, the card degrades to "unavailable" and the VP keeps working on its LAN address.

---

## :material-link-variant: Related

- [Virtual Printer](virtual-printer.md) — the VP modes, and the CA import you still need.
- [Reverse proxy & HTTPS](../getting-started/reverse-proxy.md) — for the BamDude UI itself, not the VP.
