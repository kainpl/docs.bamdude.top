---
title: Virtual Printer
description: Emulate a Bambu printer for slicer uploads — review, per-printer queue, auto-queue, or proxy
---

# Virtual Printer

The Virtual Printer (VP) makes BamDude appear as one or more Bambu Lab printers on your LAN. Bambu Studio / OrcaSlicer's "Send to Printer" lands files on a VP exactly the way it would on a real printer — over secure TLS (MQTT + FTPS) with the printer's access code. From there BamDude routes the upload according to the VP's mode.

---

## :material-printer-3d: Overview

Each VP:

- Advertises itself over **SSDP** with a real Bambu model code (X1C / P1S / A1 Mini / H2D / …) so slicers discover it automatically.
- Runs its **own FTPS + MQTT + SSDP servers**. By default they listen on `0.0.0.0` (the host's all interfaces); when you want multiple VPs side-by-side, give each a dedicated `bind_ip` so they don't fight for the same ports.
- Carries an **access code** like a real printer — slicers prompt for it on first use and cache it afterwards.
- Has a **serial number** and **model code** that match Bambu's real format, so the slicer's compatibility checks pass.

---

## :material-swap-horizontal: Modes

A VP runs in **exactly one mode**. The mode is set per-VP and validated server-side — anything else is rejected with HTTP 400.

| Mode | What happens to uploads | Use case |
|------|-------------------------|----------|
| **`file_manager`** (default) | Upload lands in `/pending-uploads` as a **review item**. From the review modal an operator can dispatch to a real printer, archive in bulk (no print), or reject. | Multi-user / multi-machine inbox where every upload gets a sanity check before printing — also the right mode if you only want to **archive** without printing (use the bulk-archive action in the review modal). |
| **`print_queue`** | Upload is archived **and** queued on a **specific** target printer. With `auto_dispatch=true` the queue item starts immediately; with `auto_dispatch=false` it waits for an explicit Start click. | You always print this VP's uploads on the same machine. |
| **`auto_queue`** | Upload is archived and dropped into the **[auto-queue router](auto-queue.md)** — no fixed target. The scheduler picks any eligible idle printer (model + filament + color match). | Hands-off load-balancing across a multi-printer farm. |
| **`proxy`** | The slicer's TLS session is TCP-proxied to a real `target_printer_id` — BamDude is just the public endpoint. | Remote printing — slicer reaches BamDude over LAN/VPN, BamDude reaches the printer. |

!!! info "There is no separate ‘archive only’ mode"
    Earlier versions of this page mentioned an `immediate` mode that auto-created an archive row without involving the queue or library. **That mode was never in the code** — the docs were wrong. The code's mode enum is exactly the four above (see `backend/app/models/virtual_printer.py` and the validator in `backend/app/api/routes/virtual_printers.py`). To get archive-only behaviour, use `file_manager` mode and bulk-archive uploads from the review modal — they get a `print_archives` row without ever touching a printer.

---

## :material-broadcast: Live-state mirroring in non-proxy modes

When a non-proxy VP (`file_manager` / `print_queue` / `auto_queue`) is configured with a **target printer**, the slicer talking to the VP sees the **real printer's live state** — not a frozen idle stub. AMS slot detection, FTS routing, nozzle-type identification, per-filament k-profiles, and the live camera all work as if the slicer were talking to the printer directly. You keep BamDude's queue / archive / dispatch features and gain slicer-as-remote ergonomics in the same VP.

How it works (operator-relevant subset):

- BamDude's existing per-printer MQTT subscription is reused — no second session on the printer, so firmware in-flight budget is unaffected.
- The VP caches the printer's last `push_status` and `info.get_version` and serves a near-byte-identical copy to the slicer. Only the upload-state fields BamDude owns (`gcode_state`, `gcode_file`, `prepare_percent`, `subtask_name`) are overridden.
- Slicer-issued commands (AMS load / unload, xcam toggles, `extrusion_cali_get` k-profile fetches, …) are forwarded to the real printer. `project_file` / `gcode_file` still terminate locally — the file lives on BamDude.
- Camera streaming uses a raw TCP passthrough on `<bind_ip>:322` → `printer:322` (same approach proxy mode uses).

!!! warning "Same access code on the VP and its target"
    BambuStudio authenticates RTSPS with whatever access code is in its slicer profile — the VP and its target printer must share the same access code, or the camera button will hit "LAN connection failed". MQTT and FTPS work either way. Set both via **Settings → Virtual Printer → Edit** and **Settings → Printers → Edit**.

!!! info "Proxy mode unaffected"
    Proxy mode owns its own RTSP / FTP / MQTT proxies and routes everything end-to-end at the TCP layer — there's no caching layer to mirror. The behaviour described above is opt-in for the three non-proxy modes only.

---

## :material-cog: Setup

**Settings → Virtual Printer → Add Virtual Printer**:

| Field | Notes |
|-------|-------|
| Name | Display label (e.g. `Studio inbox`). |
| Model | SSDP model code — pick the printer model you want the VP to impersonate so slicer compatibility checks pass. |
| Bind IP | Optional. Leave empty to listen on `0.0.0.0` (host's all interfaces) — fine if you only need one VP on the standard ports. Set a dedicated IP only when running **multiple VPs side-by-side** so each gets its own FTPS / MQTT / SSDP listener. On Linux the easiest way to provision extra IPs is a virtual interface (alias) on the host. |
| Access code | 8-character code the slicer authenticates with. |
| Mode | One of the four above. |
| Auto-dispatch | Active in `print_queue` and `auto_queue` modes — see below. |
| Target printer | `print_queue` mode (specific target) and `proxy` mode only. Hidden when `auto_queue` or `file_manager` is selected. |

Slicers discover the new VP automatically via SSDP within a minute or two. If discovery fails, add it manually by IP + access code.

---

## :material-ethernet: Required Ports

!!! tip "You usually don't have to configure these"
    The container / native install opens the right ports automatically — this table is reference material for firewall rules, Docker NAT, advanced multi-NIC setups, and proxy mode.

Each VP uses these ports on its bind IP:

| Service | Port | Protocol | Purpose |
|---------|------|----------|---------|
| Bind / detect | 3000, 3002 | TCP | Slicer's "Add Printer" handshake — required for all modes |
| SSDP | 2021 | UDP | Auto-discovery on the LAN (skip for VPN / Docker bridge / remote) |
| MQTT | 8883 | TCP/TLS | Printer control + status |
| File transfer tunnel | 6000 | TCP/TLS | Verify-job + file upload (proxy mode + A1/P1 camera) |
| RTSP camera | 322 | TCP/TLS | Camera streaming for X1 / H2 / P2 series — proxy mode **and** non-proxy modes when a target printer is set (slicer's live camera goes through this port) |
| FTPS | 990 | TCP/TLS | File transfer control |
| FTP PASV data | 50000–50100 | TCP | FTP passive data channel |
| Slicer proprietary | 2024–2026 | TCP/TLS | A1 / P1S printer ↔ slicer protocol (proxy mode) |

!!! note "Why two bind ports"
    Different versions of Bambu Studio and OrcaSlicer use different ports for the bind handshake. BamDude listens on **both 3000 and 3002** so any slicer build connects.

!!! note "Privileged port 990"
    Port 990 is privileged (<1024). The process needs `CAP_NET_BIND_SERVICE` or root to bind it. The shipped Docker image and the systemd unit already grant the capability — no manual action needed for either of those install paths.

---

## :material-printer-3d-nozzle: Adding the VP to a slicer

### Automatic discovery (same LAN)

1. Make sure the VP is **enabled** (Settings → Virtual Printer → toggle on, status `Running`).
2. In Bambu Studio / OrcaSlicer open **Device** → click **Refresh** (or wait — it polls).
3. The VP appears in the device list under the model you picked. Pick it, paste the access code, done.

### Manual add (VPN / Docker bridge / remote / different subnet)

SSDP is **link-local** — broadcasts don't cross routers, VPN tun mode, or Docker bridge networks. In those cases:

1. **Device → Add Printer → Add printer manually** (or "Bind with access code" depending on slicer build).
2. **IP**: BamDude host's reachable IP (or the per-VP bind IP if you set one).
3. **Access code**: the 8-character code from the VP card.

!!! warning "Bind ports must be reachable"
    The handshake uses port 3000 or 3002 — the slicer machine has to be able to TCP-connect to that port on the BamDude host. Firewall, port forwarding, Docker `ports:` mapping — any of those can break it.

---

## :material-send: Sending prints — Send vs Print

!!! warning "Click **Send**, not **Print**"
    - **Send** → ships the 3MF to BamDude, hits the VP mode (review / queue / auto-queue / archive). **Correct.**
    - **Print** → tells the slicer to start printing immediately on a real printer. The VP isn't a printer — it'll either time out or trigger an error.

In Bambu Studio / OrcaSlicer the **Send** button is right next to **Print** (or hidden behind the dropdown arrow on the Print button, depending on slicer version). What happens after Send depends on the VP's mode — see [Modes](#modes) above.

For `proxy`-mode VPs, you click **Print** as normal — proxy mode is transparent and forwards to the real printer.

---

## :material-certificate: Certificate Installation

The VP serves MQTT + FTPS + RTSP behind a self-signed CA that BamDude generates the first time you enable a VP. **Bambu Studio and OrcaSlicer don't trust it out of the box** — they ship with a hard-coded list of Bambu's own CAs and (on macOS / Windows) ignore the system trust store. You have to add BamDude's CA to the slicer's bundled `printer.cer` file (or, on Linux, to the system CA store if your slicer build honours it).

!!! info "When you must repeat this"
    - First-time setup (every new install)
    - You moved BamDude to a new host (each install regenerates a unique CA — unless you copy the `certs/` dir over)
    - The slicer auto-updated and overwrote `printer.cer` (common on Windows / macOS package updates)

### Step 1 — Locate the BamDude CA

The CA is at `<DATA_DIR>/virtual_printer/certs/bbl_ca.crt`.

=== "Native install"
    ```bash
    # default DATA_DIR is ./data next to the bamdude install
    cat data/virtual_printer/certs/bbl_ca.crt
    ```

=== "Docker"
    ```bash
    docker cp bamdude:/app/data/virtual_printer/certs/bbl_ca.crt ./bamdude-ca.crt
    ```

!!! note "Cert is generated lazily"
    `bbl_ca.crt` only appears after you **enable** a VP for the first time. If the file doesn't exist, create + enable a VP in the UI, then re-run the cp.

### Step 2 — Append the CA to the slicer's `printer.cer`

`printer.cer` is a PEM bundle of the CAs the slicer trusts for printer connections. Open it, **append** the BamDude CA at the end (after the last `-----END CERTIFICATE-----`), save, then **fully restart** the slicer (Cmd+Q on macOS — closing the window isn't enough; Task Manager → End Task on Windows).

!!! tip "Append, don't replace"
    Appending preserves your trust for real Bambu Lab printers. Replacing the file breaks Bambu Cloud / direct-MQTT to physical hardware.

**Where `printer.cer` lives:**

=== "macOS"
    - Bambu Studio: `/Applications/BambuStudio.app/Contents/Resources/cert/printer.cer`
    - OrcaSlicer: `/Applications/OrcaSlicer.app/Contents/Resources/cert/printer.cer`

=== "Windows"
    - Bambu Studio: `C:\Program Files\Bambu Studio\resources\cert\printer.cer`
    - OrcaSlicer: `C:\Program Files\OrcaSlicer\resources\cert\printer.cer`

=== "Linux — `.deb` / `.rpm`"
    Native packages link against system OpenSSL and pick up the system CA bundle when `tls_cert_store_accepted: yes` is set in `~/.config/BambuStudio/BambuStudio.conf` (the default after first launch). In that case install the CA system-wide:

    Debian / Ubuntu / Mint / Raspberry Pi OS:

    ```bash
    sudo cp bbl_ca.crt /usr/local/share/ca-certificates/bamdude-ca.crt   # extension MUST be .crt
    sudo update-ca-certificates
    ```

    Fedora / RHEL / openSUSE:

    ```bash
    sudo cp bbl_ca.crt /etc/pki/ca-trust/source/anchors/bamdude-ca.crt
    sudo update-ca-trust
    ```

    Arch:

    ```bash
    sudo trust anchor --store bbl_ca.crt
    ```

    Then **fully quit and relaunch** the slicer.

    !!! warning "Common pitfall"
        Dropping the file into `/etc/ssl/certs/` and running `update-ca-certificates` is a no-op — only files under `/usr/local/share/ca-certificates/` with a `.crt` extension are picked up.

    If the system store doesn't take, fall back to direct edit (these are root-owned, so `sudo`):

    - Bambu Studio: `/usr/share/Bambu Studio/resources/cert/printer.cer`
    - OrcaSlicer: `/usr/share/OrcaSlicer/resources/cert/printer.cer`

    Direct edits get reverted on every package update.

=== "Linux — AppImage"
    The system CA store is unreliable for AppImage builds (they ship their own networking stack). Extract, edit the bundled `printer.cer`, run from the extracted tree:

    ```bash
    ./Bambu_Studio_linux_*.AppImage --appimage-extract
    # edit squashfs-root/usr/share/Bambu Studio/resources/cert/printer.cer
    ./squashfs-root/AppRun
    ```

    Repeat each time you update the AppImage to a new version.

### Cert persistence

The CA is generated once and persists across BamDude restarts. **Keep `<DATA_DIR>/virtual_printer/certs/` in your backup** — losing it means every slicer has to re-import the new CA after the next restart.

If you switch between Docker and native installs and want a single CA across both, share the cert dir as a bind-mount:

```yaml
volumes:
  - ./virtual_printer:/app/data/virtual_printer
```

### Multiple BamDude hosts

Each install generates its own CA. Two clean approaches:

**Share the CA (recommended for farms)**

```bash
scp -r host1:/path/to/data/virtual_printer/certs/ host2:/path/to/data/virtual_printer/
# restart bamdude on host2
```

All hosts now use the same CA — one cert in the slicer covers all of them.

**Or: re-import per host**

When switching slicer focus to a different BamDude host, remove the old BamDude CA block from `printer.cer`, append the new one, restart slicer.

!!! warning "One BamDude CA at a time"
    Stacking multiple BamDude CAs in `printer.cer` doesn't break anything cryptographically, but it makes it easy to point the slicer at the wrong host by accident. Clean up old ones.

---

## :material-ip-network: Dedicated bind IPs (multiple VPs)

Each VP that runs on the standard ports needs its own IP — the FTPS / MQTT / SSDP listeners can't share a port across VPs on the same address. With one VP on `0.0.0.0` the host's primary IP is enough; for two or more VPs you give each its own bind IP via interface aliases (extra IPs on the same NIC).

Example layout:

| | IP |
|---|---|
| BamDude web UI | `192.168.1.100` (host primary) |
| VP 1 | `192.168.1.101` |
| VP 2 | `192.168.1.102` |
| VP 3 | `192.168.1.103` |

!!! warning "Pick free IPs"
    Use addresses **outside your DHCP range**, or reserve them on the router. Verify with `ping 192.168.1.101` before adding — if anything answers, pick another.

### Adding interface aliases

=== "Linux (native or Docker host mode)"

    Find your interface name:

    ```bash
    ip -br addr show
    # eth0  UP  192.168.1.100/24
    ```

    Add aliases (transient — gone after reboot):

    ```bash
    sudo ip addr add 192.168.1.101/24 dev eth0
    sudo ip addr add 192.168.1.102/24 dev eth0
    sudo ip addr add 192.168.1.103/24 dev eth0
    ```

    **Persist them:**

    === "Netplan (Ubuntu 18.04+, Debian 12+)"

        Edit `/etc/netplan/*.yaml`:

        ```yaml
        network:
          version: 2
          ethernets:
            eth0:
              dhcp4: true
              addresses:
                - 192.168.1.101/24
                - 192.168.1.102/24
                - 192.168.1.103/24
        ```

        Apply with `sudo netplan apply`.

    === "/etc/network/interfaces (Debian, Raspberry Pi OS)"

        ```
        auto eth0:1
        iface eth0:1 inet static
            address 192.168.1.101
            netmask 255.255.255.0

        auto eth0:2
        iface eth0:2 inet static
            address 192.168.1.102
            netmask 255.255.255.0
        ```

        `sudo ifup eth0:1 eth0:2`.

    === "NetworkManager (Fedora, RHEL, Arch)"

        ```bash
        sudo nmcli con mod "Wired connection 1" +ipv4.addresses "192.168.1.101/24"
        sudo nmcli con mod "Wired connection 1" +ipv4.addresses "192.168.1.102/24"
        sudo nmcli con up "Wired connection 1"
        ```

        Find connection name with `nmcli con show`.

=== "Unraid"

    SSH or use the web terminal:

    ```bash
    ip addr add 192.168.1.101/24 dev eth0
    ip addr add 192.168.1.102/24 dev eth0
    ```

    Persist via `/boot/config/go`:

    ```bash
    echo "ip addr add 192.168.1.101/24 dev eth0" >> /boot/config/go
    echo "ip addr add 192.168.1.102/24 dev eth0" >> /boot/config/go
    ```

=== "Synology NAS"

    SSH:

    ```bash
    sudo ip addr add 192.168.1.101/24 dev eth0
    sudo ip addr add 192.168.1.102/24 dev eth0
    ```

    Persist via Control Panel → **Task Scheduler** → Triggered Task → User-defined script, event **Boot-up**, user **root**, with the same `ip addr add …` lines.

=== "TrueNAS SCALE"

    Network → Interfaces → Edit → add **Aliases** (`192.168.1.101/24`, etc.) → Save → Apply. Persists automatically.

=== "Proxmox LXC"

    **Inside the container** — install `iproute2` if missing, then use the Linux instructions above (netplan or `/etc/network/interfaces`).

    **From the Proxmox host** — edit `/etc/pve/lxc/<CTID>.conf`:

    ```
    net0: name=eth0,bridge=vmbr0,ip=192.168.1.100/24,gw=192.168.1.1
    net1: name=eth1,bridge=vmbr0,ip=192.168.1.101/24
    net2: name=eth2,bridge=vmbr0,ip=192.168.1.102/24
    ```

    Or `pct set <CTID> -net1 name=eth1,bridge=vmbr0,ip=192.168.1.101/24`. Restart the container after.

=== "Docker Desktop (macOS / Windows)"

    !!! warning "One VP only"
        Docker Desktop runs everything inside a Linux VM and doesn't let you add host interface aliases reachable from inside the container. With bridge networking you're capped at **one VP** per host. For multiple VPs, use Linux (native or a VM with host networking).

!!! tip "Docker host mode"
    With `network_mode: host` add the aliases on the **Docker host**, not inside the container — host mode shares all the host's IPs into the container automatically.

---

## :material-list-box: Printer model SSDP codes

The VP impersonates a real Bambu model so the slicer's compatibility check passes. Pick the model matching the slicer profile you'll use to send to it.

| SSDP code | Display name | Serial prefix |
|---|---|---|
| `BL-P001` | X1C *(default)* | 00M |
| `BL-P002` | X1 | 00M |
| `C13` | X1E | 03W |
| `N6` | X2D | 20P9 |
| `C11` | P1P | 01S |
| `C12` | P1S | 01P |
| `N7` | P2S | 22E |
| `N2S` | A1 | 039 |
| `N1` | A1 Mini | 030 |
| `O1D` | H2D | 094 |
| `O1C` / `O1C2` | H2C *(O1C2 = dual-nozzle variant)* | 094 |
| `O1S` | H2S | 094 |

!!! note "Model change restarts the VP"
    Changing the model regenerates the serial and restarts the listeners. The slicer will see a new printer and you'll likely need to re-add it (the cached pairing on the slicer side keys on serial).

---

## :material-network-strength-4: Network interface override

When the host has multiple NICs (Tailscale, multiple LAN bridges, Docker overlay networks, dual-homed routing), BamDude's auto-detected IP can land on the wrong interface — slicers on the right network won't reach it, and the IP baked into the TLS SAN will fail the cert check.

**Settings → Virtual Printer → Network Interface Override** picks which interface BamDude:

- advertises in **SSDP** discovery
- bakes into the **TLS certificate's SAN** field

Applies to **all modes** (server modes + proxy SSDP relay). Pick the interface the slicer side actually reaches.

---

## :material-shield-check: Tailscale

Tailscale is BamDude's recommended path for **remote slicer access** — your slicer reaches the VP over a private WireGuard mesh from anywhere, no port forwarding, no public exposure.

The Tailscale toggle on each VP card surfaces the host's Tailscale IP / MagicDNS hostname so you know what to paste into the slicer. The CA still has to be imported into the slicer (Tailscale doesn't change cert trust).

Full setup (native + Docker + LXC), prerequisites, and troubleshooting live in the dedicated guide:

[:material-arrow-right: **Tailscale integration**](tailscale.md){ .md-button }

---

## :material-server-network: Platform setup

Open the [ports listed above](#required-ports) in your firewall.

=== "Linux native"

    Port 990 needs `CAP_NET_BIND_SERVICE`. The shipped systemd unit already has:

    ```ini
    AmbientCapabilities=CAP_NET_BIND_SERVICE
    ```

    For a manual run, grant it on the Python binary:

    ```bash
    sudo setcap cap_net_bind_service=+ep $(readlink -f $(which python3))
    ```

    UFW:

    ```bash
    sudo ufw allow 3000/tcp
    sudo ufw allow 3002/tcp
    sudo ufw allow 2021/udp
    sudo ufw allow 8883/tcp
    sudo ufw allow 990/tcp
    sudo ufw allow 6000/tcp
    sudo ufw allow 322/tcp
    sudo ufw allow 2024:2026/tcp
    sudo ufw allow 50000:50100/tcp
    ```

    firewalld:

    ```bash
    sudo firewall-cmd --permanent --add-port=3000/tcp
    sudo firewall-cmd --permanent --add-port=3002/tcp
    sudo firewall-cmd --permanent --add-port=2021/udp
    sudo firewall-cmd --permanent --add-port=8883/tcp
    sudo firewall-cmd --permanent --add-port=990/tcp
    sudo firewall-cmd --permanent --add-port=6000/tcp
    sudo firewall-cmd --permanent --add-port=322/tcp
    sudo firewall-cmd --permanent --add-port=2024-2026/tcp
    sudo firewall-cmd --permanent --add-port=50000-50100/tcp
    sudo firewall-cmd --reload
    ```

=== "Docker (Linux, host mode)"

    Host networking is required for SSDP discovery. Stock compose snippet:

    ```yaml
    services:
      bamdude:
        image: ghcr.io/kainpl/bamdude:latest
        container_name: bamdude
        network_mode: host          # required for SSDP
        cap_add:
          - NET_BIND_SERVICE        # required for port 990
        volumes:
          - bamdude_data:/app/data
          - bamdude_logs:/app/logs
        environment:
          - TZ=Europe/Kyiv
        restart: unless-stopped
    ```

    No port mapping needed — host mode binds straight to the host's interfaces. Apply the UFW / firewalld rules from the Linux native tab on the host.

=== "Docker Desktop (macOS / Windows)"

    !!! warning "Limited support"
        No `network_mode: host` on Docker Desktop — SSDP **will not work**, you must add the VP manually by IP. Bridge mode also caps you at **one VP** (no interface aliases inside the VM).

    Bridge mode compose:

    ```yaml
    services:
      bamdude:
        image: ghcr.io/kainpl/bamdude:latest
        container_name: bamdude
        cap_add:
          - NET_BIND_SERVICE
        ports:
          - "${PORT:-8000}:8000"
          - "3000:3000"
          - "3002:3002"
          - "990:990"
          - "6000:6000"
          - "8883:8883"
          - "322:322"
          - "2024-2026:2024-2026"
          - "50000-50100:50000-50100"
        volumes:
          - bamdude_data:/app/data
          - bamdude_logs:/app/logs
        environment:
          - TZ=Europe/Kyiv
          - VIRTUAL_PRINTER_PASV_ADDRESS=192.168.1.100  # your Docker host's LAN IP
        restart: unless-stopped
    ```

    `VIRTUAL_PRINTER_PASV_ADDRESS` is **mandatory** in bridge mode — without it FTP PASV advertises the container's internal IP and the data channel fails. See [PASV Address](#pasv-address-nat-docker-bridge) below.

=== "Unraid / Synology / TrueNAS SCALE"

    Use **Host Network** in the container settings. The FTP server binds 990 directly — no extra config needed beyond enabling the VP in the UI.

=== "Proxmox LXC"

    No special config — the FTP server binds directly to 990. Ensure BamDude runs as root **or** with `CAP_NET_BIND_SERVICE` granted to the Python binary (see Linux native tab).

---

## :material-form-select: Mode picker UI

The Add / Edit dialog lays the four modes out as **three big buttons** plus a sub-toggle — because `print_queue` and `auto_queue` are really two flavours of the same thing (queue dispatch, with vs without a fixed target):

```
┌──────────────────────────────────────────────────────────┐
│  Mode                                                    │
│  ┌─────────────┬───────────────┬──────────────────────┐  │
│  │   Queue     │  File Manager │    ⇄  Proxy          │  │
│  └─────────────┴───────────────┴──────────────────────┘  │
│                                                          │
│  When Queue is picked:                                   │
│    [ ] Auto-select printer  ← toggle                     │
│        on  → mode = auto_queue                           │
│        off → mode = print_queue + Target Printer field   │
│                                                          │
│  Auto-dispatch                          [ ]              │
└──────────────────────────────────────────────────────────┘
```

When **Queue → Auto-select printer = on**, the VP is in `auto_queue` and the Target Printer dropdown disappears (any printer of the matching model can pick it up). When **Auto-select = off**, you get `print_queue` and a Target Printer dropdown the upload always lands on.

`file_manager` and `proxy` are full-width buttons of their own.

### Model ↔ Target Printer linking

In `print_queue` mode the dialog also wires Model and Target Printer together so you can't end up with an inconsistent pair:

- Pick a **Target Printer** → the VP's Model auto-fills from that printer's model.
- Pick a **Model** → the Target Printer dropdown filters down to printers of that model. If your previously-selected target doesn't match the new model, the dialog clears it.
- An explicit **clear (×) button** sits inside the Target Printer field if you want to wipe the selection without changing model.

---

## :material-shield-alert: Validation rules

The backend (`POST /virtual-printers/`, `PUT /virtual-printers/{id}`) enforces these:

| Rule | Error |
|------|-------|
| `mode='print_queue'` + `auto_dispatch=true` + no `target_printer_id` (and not switching to auto-select) | **400** — *"Auto-dispatch in Queue mode requires a Target Printer. Pick a target, enable Auto-select printer, or turn Auto-dispatch off."* |
| `mode='proxy'` without `target_printer_id` | **400** — *"Proxy mode requires a Target Printer."* |
| Any other `mode` value | **400** — *"Invalid mode."* |

The `PUT` route revalidates the **effective** state after applying the body, so you can't sneak past the rule by clearing one field at a time. If you need to clear an existing target, send `clear_target_printer: true` — the dialog's × button does this for you.

The frontend mirrors this with a yellow warning banner that disables the Auto-dispatch toggle when the combination would be unsafe, so you see the constraint before you submit.

---

## :material-clipboard-check: Review Modal (file_manager mode)

In `file_manager` mode, every uploaded 3MF lands in a **review queue** at `/pending-uploads`. From the review modal an operator:

1. Opens an upload, sees the parsed metadata + thumbnail.
2. Picks the target real printer.
3. Verifies AMS slot mapping, plate selection, and any per-print options.
4. Clicks **Send to Printer** — the 3MF is dispatched through the standard background-dispatch pipeline (FTP upload, swap macros, archive linkage).

Review batches can also be **archived in bulk** (no print, just stash the metadata) or **rejected** (deletes the upload). Use this when multiple users / machines slice into the same VP and you want a sanity check before it actually hits a printer.

API: `GET /api/v1/pending-uploads/`, `POST /api/v1/pending-uploads/{id}/archive`, `POST /api/v1/pending-uploads/archive-all`.

---

## :material-flash: Auto-Dispatch (Queue modes) {#auto-dispatch}

A VP in either Queue mode (`print_queue` or `auto_queue`) honours the `auto_dispatch` flag:

| `auto_dispatch` | `print_queue` | `auto_queue` |
|-----------------|---------------|--------------|
| **true** | Slicer upload → archived → queued → dispatched immediately. | Slicer upload → archived → dropped into the [auto-queue router](auto-queue.md) → next 30 s tick assigns it to an eligible idle printer. |
| **false** | Slicer upload → archived → queued in `pending`, waits for an explicit Start click in the queue UI. | Slicer upload → archived → router row is created with `manual_start=true` so it's ignored by the scheduler until released from the auto-queue panel. |

!!! tip "Trusted upstream only"
    Auto-dispatch removes the human gate. Use it when the upstream source is yourself or a trusted automation (slicer plugin, CI job, MakerWorld webhook). For shared / multi-tenant uploads, prefer `file_manager` mode + the review modal.

---

## :material-router-network: auto_queue mode {#auto_queue}

`auto_queue` is the natural pairing between the VP and the [auto-queue router](auto-queue.md). On upload the VP:

1. Archives the 3MF (full per-plate metadata, thumbnails, source-hash chain).
2. Calls `extract_auto_queue_requirements` on the archived file to pull out:
    - `target_model` (from `sliced_for_model` in the 3MF)
    - `required_filament_types` (from `slice_info.config`)
    - `plate_id` if the slicer specified a single plate
3. Creates an `AutoQueueItem` with `manual_start = !auto_dispatch`.
4. Returns an FTPS success to the slicer — same UX as a real printer accepting the file.

The router takes over from there: 30 s tick, eligible-printer search, AMS mapping at assign time. See the [auto-queue doc](auto-queue.md) for the full routing flow.

There's no Target Printer to set on an `auto_queue` VP — that's the whole point. The dialog hides the field and clears any value left over from a mode switch.

---

## :material-file-edit-outline: Archive name source

By default a VP-archived 3MF takes its display name from the slicer-set `print_name` baked into the project metadata — that's usually the human-readable "Calibration Cube v3" the operator typed in Bambu Studio. Some workflows prefer the **upload filename** instead — for example a batch system that names each upload `2026-04-30_jobid-1234.gcode.3mf` and wants those identifiers preserved as-is.

**Settings → Virtual Printer → Archive name source**:

| Value | Effect |
|---|---|
| `metadata` (default) | Use 3MF metadata `print_name`. Falls back to filename if metadata is missing. |
| `filename` | Use the upload filename's stem. Falls back to metadata if the filename is empty / generic. |

The toggle is install-wide and applies to every VP except `proxy`-mode (proxy uploads aren't archived by BamDude — the real printer's archive flow takes over).

---

## :material-network-outline: PASV Address (NAT / Docker bridge)

FTPS uses the PASV command, where the server tells the client which IP to dial back on for the data channel. When BamDude runs in a Docker bridge network (or behind any NAT), the PASV response would otherwise advertise the **container's internal IP** — slicers on the LAN can't reach it and the data channel fails mid-handshake.

Set the `VIRTUAL_PRINTER_PASV_ADDRESS` env var to the **externally-reachable IP** (the host's LAN address — most slicers don't resolve hostnames here):

```bash
VIRTUAL_PRINTER_PASV_ADDRESS=192.168.1.100
```

The FTPS server boots, logs `FTP PASV address override: 192.168.1.100`, and from then on every PASV reply uses that address. No effect when BamDude runs on the host network — leave it unset there.

---

## :material-help-circle: Troubleshooting

### Slicer can't find the VP (auto-discovery)

1. **VP enabled and running?** Status pill on the VP card must be `Running` — if it says `Error` open the card and read the failure reason.
2. **Same LAN segment?** SSDP is link-local — won't cross VPN tun mode, Docker bridge, or routed subnets. Add manually by IP instead.
3. **Bind ports reachable?** From the slicer machine:
   ```bash
   nc -zv BAMDUDE_IP 3000
   nc -zv BAMDUDE_IP 3002
   ```
4. **Firewall**: 3000/tcp, 3002/tcp, 2021/udp must be open between slicer and BamDude.
5. **Multiple NICs?** Use [Network Interface Override](#network-interface-override) to pin SSDP to the right interface.

### "Failed to connect" / TLS error -1 / cert untrusted

The slicer doesn't trust BamDude's CA. In order:

1. **CA appended to `printer.cer`?**
   ```bash
   grep -c "BEGIN CERTIFICATE" "/path/to/slicer/resources/cert/printer.cer"
   ```
   Stock = 1. After appending = 2 (or more if you use multi-host CAs).
2. **Right CA?** If you migrated BamDude to a new host, the CA changed. Compare fingerprints:
   ```bash
   # Native
   openssl x509 -in data/virtual_printer/certs/bbl_ca.crt -noout -fingerprint -sha1

   # Docker
   docker exec bamdude openssl x509 -in /app/data/virtual_printer/certs/bbl_ca.crt -noout -fingerprint -sha1
   ```
   The output's `SHA1 Fingerprint=…` line must match one of the certs inside `printer.cer`.
3. **Slicer fully restarted?** Cmd+Q on macOS, End Task on Windows. Closing the window doesn't reload `printer.cer`.
4. **Linux AppImage / Flatpak**: `printer.cer` inside the bundle is read-only. Either extract the AppImage and edit the bundled cert, or install the CA into the system trust store + verify `tls_cert_store_accepted: yes` is set in `~/.config/BambuStudio/BambuStudio.conf`.
5. **Last resort — regenerate**:
   ```bash
   rm -rf /path/to/data/virtual_printer/certs/
   # disable + re-enable the VP in UI to regenerate
   ```
   Then re-import the new CA in every slicer.

### "Wrong printer model" rejection

The slicer profile model and the VP's [SSDP code](#printer-model-ssdp-codes) don't match. Pick the same model on both sides — the VP's model code is what the slicer's compatibility check reads.

### Authentication failed

- Access code is exactly **8 characters** — no more, no less.
- Slicer caches the access code per discovered printer; if you changed it on BamDude, remove + re-add the printer in the slicer.

### Wrong IP advertised in SSDP / TLS SAN mismatch

Multi-NIC host (Tailscale, Docker bridges, dual LAN) — auto-detection picks the wrong interface:

1. **Settings → Virtual Printer**
2. **Network Interface Override** → pick the interface your slicer reaches BamDude through
3. The VP restarts; SSDP and the TLS cert SAN both update

### FTP error / connection reset

1. **Permissions** on `<DATA_DIR>/virtual_printer/` — must be writable by the user running BamDude.
2. **Port 990 already in use?** `sudo ss -tlnp | grep :990` — disable any conflicting FTP server.
3. **`CAP_NET_BIND_SERVICE` missing** — see the [Linux native tab](#platform-setup) above.
4. **Bridge-mode Docker** — `VIRTUAL_PRINTER_PASV_ADDRESS` is mandatory; without it PASV advertises the container's internal IP and the data channel fails mid-handshake.

### Proxy mode: printer offline in slicer

- Target printer is online in BamDude? Card on Printers page should show `Online`.
- Printer is in **LAN Mode** (Developer Mode in Bambu Handy)? Proxy mode requires LAN mode — Cloud Mode rejects the proxied MQTT session.
- Toggle the proxy off + on to force a reconnect.

### Proxy mode: "Connect using IP and access code" pop-up when you click Print

1. **Port 6000 reachable?** Bambu Studio uses it for the file transfer tunnel.
   ```bash
   nc -zv BAMDUDE_IP 6000
   ```
2. **Firewall**: 6000/tcp open between slicer and BamDude.
3. **Different VLANs / subnets** — check BamDude logs for `IP rewrite active`. The MQTT IP-rewrite step rewrites the printer's LAN IP in MQTT payloads to BamDude's IP so the slicer reaches the proxy, not the printer directly.

### Proxy mode: camera not loading

- **X1 / H2 / P2 series**: RTSP on port 322. Open it between slicer and BamDude.
- **A1 / P1 series**: camera rides port 6000 (shared with file transfer).

### Proxy mode: connection drops mid-transfer

Large 3MFs over slow uplinks. Either run a VPN (Tailscale / WireGuard) so the data channel rides one stable tunnel, or upload the 3MF locally first and dispatch via Print Queue.

---

## :material-shield-account: Technical details

### Security per protocol

- **Bind** (3000, 3002): unencrypted TCP — transmits printer identity only, no sensitive payload. In proxy mode BamDude responds with the VP's identity and never forwards the bind to the printer.
- **MQTT control** (8883): TLS 1.2, terminated at BamDude. Proxy mode rewrites the printer's IP inside MQTT payloads so the slicer can't bypass the proxy.
- **File transfer tunnel** (6000): end-to-end TLS, transparent proxy.
- **RTSP camera** (322): end-to-end TLS, transparent proxy.
- **A1 / P1S proprietary** (2024–2026): end-to-end TLS, transparent proxy.
- **FTPS control** (990): end-to-end TLS, transparent proxy.
- **FTP data** (50000–50100): in proxy mode it's a transparent proxy — actual encryption depends on slicer/printer negotiation. Bambu Studio sends file data **in cleartext** even when it negotiates `PROT P`. Use a VPN if you care about data-channel confidentiality.
- All connections require the 8-char access code — slicer auth on every TLS handshake.
- CA persists in `<DATA_DIR>/virtual_printer/certs/`; per-VP device certs in `<DATA_DIR>/virtual_printer/certs/{id}/` regenerate when serial changes.

### Limitations

- Multiple VPs need a **dedicated bind IP each** — interface aliases per the table above.
- **SSDP works only on the same LAN / routed subnets**. VPN tun mode and Docker bridge networks need manual add by IP.
- The slicer must trust BamDude's self-signed CA — see [Certificate Installation](#certificate-installation).
- **FTP data channel is unencrypted** on the slicer side — VPN if you need full encryption.
- **Docker Desktop on macOS / Windows = one VP only** (no interface aliases inside the VM).

---

## :material-rocket: Use Cases

- **Multi-user farm inbox** — `file_manager` + review modal lets several people slice into the same VP without stepping on each other.
- **Print archiving without printing** — `file_manager` + the **bulk-archive** action in the review modal turns slice → send into a permanent record (thumbnails, metadata, source 3MF) without committing to a print.
- **Library building** — same `file_manager` mode: archive uploads from the review modal so you can attach them to projects, batch-print, or share with the team before the first build.
- **Single-target hands-off** — `print_queue` + a fixed Target Printer + `auto_dispatch=true` is the closest you get to "Cloud Print but local" for one machine.
- **Manual gate on a queue** — `print_queue` + `auto_dispatch=false` queues the upload but waits for an explicit Start click before the dispatcher picks it up.
- **Farm load-balancing** — `auto_queue` + `auto_dispatch=true` is the killer workflow for a multi-printer farm: slicer doesn't know which printer will run the job, the router decides at dispatch time.
- **Remote printing** — `proxy` mode forwards a remote slicer's TLS session straight to a real printer, with BamDude's certificate as the public face.

---

## :material-lightbulb: Tips

!!! tip "One VP per workflow"
    Nothing stops you running multiple VPs at once on different IPs — one for production auto-dispatch, one for review, one for archiving. They share the same backend so all data stays unified.

!!! tip "Slicer auth caching"
    Bambu Studio / OrcaSlicer cache the access code per discovered printer. Rotate the VP access code and slicers will prompt again — no manual cache-clear needed.

> Originally based on [Bambuddy](https://github.com/maziggy/bambuddy) documentation.
