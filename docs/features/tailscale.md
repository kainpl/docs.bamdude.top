---
title: Tailscale (private tailnet) integration
description: Advertise virtual printers on your Tailnet with auto-rotated Let's Encrypt certs and tailnet-FQDN SSDP, so remote slicers reach BamDude securely without VPN gymnastics
---

# Tailscale integration

BamDude can advertise its [virtual printers](virtual-printer.md) over a private [Tailscale](https://tailscale.com/) network instead of (or alongside) the LAN. Every VP gets a real Let's Encrypt cert tied to its `*.tailnet-name.ts.net` FQDN, the SSDP advertisement uses that FQDN, and remote slicers — Bambu Studio / OrcaSlicer running on a phone or laptop somewhere on the Tailnet — discover the VP exactly like they would on the local network. No port-forward, no extra VPN client, no manual cert juggling.

This is **opt-in per VP**: existing setups keep advertising on LAN by default, and the tailnet flow is enabled only for VPs you explicitly mark.

---

## :material-lan-disconnect: When this matters

The shipped alternative — [VP `proxy` mode](virtual-printer.md#proxy) — works for remote printing too, but funnels every byte through BamDude's own TCP relay. Tailscale's wire-level mesh is faster (direct peer-to-peer when possible, DERP-relayed otherwise), zero-config from the slicer side, and lets the slicer think it's talking to a regular Bambu printer.

| Scenario | Recommended path |
|---|---|
| Slicing on a laptop on the same LAN as BamDude | Plain VP, no Tailscale needed. |
| Slicing on a laptop / phone *off-network* (cafe, on holiday) | Tailscale per-VP. |
| Slicing from a CI / GitHub Actions runner | VP `proxy` mode (Tailscale on a VM is overkill). |
| Multi-tenant cloud → BamDude bridge | VP `proxy` mode + your existing TLS. |

Tailscale shines specifically when **the slicer-running machine is already on Tailscale anyway** and you want it to "just see" the printer.

---

## :material-package-variant: Prerequisites

1. **Tailscale daemon on the BamDude host.** Native installs: install [tailscaled](https://tailscale.com/kb/1031/install-linux) and `tailscale up`. Docker installs: mount the host's tailscaled socket / state into the container (`/var/run/tailscale/tailscaled.sock`) so BamDude can shell out to `tailscale cert`. There's no in-image tailscaled — ship the daemon on the host, BamDude just consumes it.
2. **MagicDNS + HTTPS certificates enabled** on your tailnet — both are toggles on the [Tailscale admin DNS page](https://login.tailscale.com/admin/dns). Without them you don't get the `*.ts.net` FQDN BamDude needs to mint a cert against.
3. **A virtual printer.** Tailscale flips a flag *per VP*; you need at least one VP to flip it on.

---

## :material-cog-outline: Enabling per VP

**Settings → Virtual Printer → edit a VP** — there's a toggle near the bottom:

| Field | Default | Effect |
|---|---|---|
| **Tailscale enabled** | off | When on, BamDude calls `tailscale cert <vp-name>.<tailnet>.ts.net` at startup, swaps in the resulting cert atomically before the FTPS / MQTT TLS listeners come up, and uses the tailnet FQDN as the SSDP `Location:` URL. |
| **Tailscale FQDN** | auto | Read-only display of the resolved FQDN. Auto-derived from the host's `tailscale status` + the VP name; override only if you have multiple VPs on the same machine that need explicit names. |

The toggle is per-VP because some installs want VP-A on the LAN (factory floor) and VP-B on the tailnet (remote slicer for the engineering team) **simultaneously** — no global switch would do.

---

## :material-certificate: Cert lifecycle

- **First mint** — on VP startup with Tailscale enabled, BamDude shells out to `tailscale cert <fqdn>` (which calls Let's Encrypt via Tailscale's broker) and writes the resulting `.crt + .key` next to the existing self-signed pair.
- **Atomic swap** — the FTPS + MQTT TLS listeners are restarted with the new cert before the SSDP advert goes out, so a slicer that pings the FQDN never sees a self-signed fallback.
- **Daily renewal** — a 24h background loop calls `tailscale cert` again well before expiry. Self-cancelling on shutdown so the loop doesn't outlive the asyncio event loop.
- **Failure mode** — if `tailscale cert` returns an error (daemon offline, FQDN typo, rate limit), BamDude logs it and falls back to the existing self-signed cert. The VP keeps running; remote slicers see a cert error until you fix the upstream and retry.

---

## :material-lan-connect: SSDP advertise

Standard VP SSDP advertises the LAN IP of the host, which is unreachable from the tailnet. With Tailscale enabled, the SSDP `Location:` URL points at the tailnet FQDN — Bambu Studio / OrcaSlicer running on any other tailnet device sees the VP exactly as if it were a real printer on the same network.

LAN advertising still happens too — local slicers pick up the LAN IP, remote slicers (only reachable via tailnet) pick up the tailnet FQDN. They don't compete.

---

## :material-shield-key: Permissions & security

- **No new BamDude permissions.** Tailscale config is part of the existing `virtual_printer:update` permission gate.
- **No Tailscale auth surface in BamDude.** All auth (who's on the tailnet) is Tailscale's job. BamDude reads the daemon, doesn't impersonate it.
- **Same VP access code** still required to authenticate the slicer to the VP. Tailscale brings the network to the printer; the access code still gates the printer.

---

## :material-alert-circle-outline: Caveats

!!! info "Docker variant deferred"
    The Docker image deliberately doesn't bundle `tailscaled`. Reasons: tailscaled wants raw netlink + a state directory + an auth flow that don't compose well with stateless containers. The runtime path is "host has tailscaled → mount its socket into BamDude's container" — that's both lower-blast-radius and respects the user's existing Tailscale setup.

- **`tailscaled` must be on the host (or mounted from a sidecar) — BamDude can't bring it up.** This is a deliberate split: Tailscale's auth + state model is a host concern.
- **Private tailnets only** — there's no path to advertise a VP to the public internet through this. That's by design (and what `proxy` mode is for).
- **Cert renewal needs daemon access at runtime** — if the host's tailscaled goes offline, the daily renewal will start failing 30+ days before the cert expires; check the alerts.

---

## :material-link-variant: Related

- [Virtual Printer](virtual-printer.md) — the VP modes that benefit from this.
- [Reverse proxy & HTTPS](../getting-started/reverse-proxy.md) — for the BamDude UI itself, not the VP.
