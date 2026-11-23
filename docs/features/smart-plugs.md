---
title: Smart Plugs
description: Zigbee, Tasmota, Home Assistant, MQTT, and REST/Webhook power control with per-print energy tracking
---

# Smart Plugs

Control your printers with Zigbee, Tasmota, Home Assistant, REST/Webhook, or MQTT smart plugs for power monitoring, automation, and per-print energy tracking.

!!! tip "The same radio also reads sensors"
    A Zigbee dongle set up here drives temperature and humidity sensors too — see [Environment Sensors](sensors.md).

---

## :material-power-plug: Overview

Smart plug integration enables:

- **Power control** -- Turn printers on/off remotely
- **Energy monitoring** -- Track power consumption (lifetime + per-print)
- **Auto power-on** -- Start printer before scheduled prints
- **Auto power-off** -- Shut down after cooldown

---

## :material-cog: Supported Types

| Type | Control | Energy | Description |
|------|:-------:|:------:|-------------|
| **Tasmota** | :material-check: | :material-check: | Direct control of Tasmota-flashed plugs (Athom, Sonoff S31, Shelly with Tasmota firmware) |
| **Home Assistant** | :material-check: | :material-check: | Any HA `switch.*` / `light.*` / `input_boolean.*` entity |
| **REST / Webhook** | :material-check: | :material-check: | Custom HTTP — openHAB, ioBroker, FHEM, Node-RED, Shelly Cloud, Tapo Cloud |
| **MQTT** | :material-check: | :material-check: | Zigbee2MQTT, Shelly Gen2 native MQTT, ESPHome, custom MQTT broker plugs |
| **Zigbee** | :material-check: | :material-check: | Zigbee plugs driven by BamDude itself through a dongle — no Home Assistant, no Zigbee2MQTT, no extra service |

!!! info "Plug picks for Bambu printers"
    A1 / A1 mini draw ~140 W peak; X1 / P1 series peak ~350 W; H2 series peak ~500 W. Any 10A / 16A plug fits, but **for energy reporting** the popular options are:

    - **Athom Plug Pro** (US/EU/UK, Tasmota pre-flashed) — best price/feature, native Tasmota
    - **Tapo P110M / P115** (HA integration via `tapo-control`) — cheap + reliable, HA-only
    - **Shelly Plus Plug** (HA + native MQTT + REST) — most flexible, three integration paths
    - **IKEA Tradfri** outlet (HA via Zigbee2MQTT) — energy reporting requires Zigbee2MQTT v1.30+

---

## :material-flash: Choosing an integration path

Each plug usually supports more than one type. Pick by:

| You already run | Best path | Why |
|-----------------|-----------|-----|
| Home Assistant | **Home Assistant** | One-stop entity dropdown, HA does the auth |
| Bare Tasmota plug | **Tasmota** | Native Tasmota commands, no broker needed |
| Zigbee2MQTT / ESPHome | **MQTT** | Subscribe direct, no extra hop |
| openHAB / FHEM / ioBroker | **REST / Webhook** | Their REST APIs map cleanly to ON/OFF + status URLs |
| Nothing yet, and you bought Zigbee plugs | **Zigbee** | BamDude runs the radio itself — nothing else to install or keep running |
| Just-bought stock plug | **Tasmota** (after flashing) | Best long-term reliability + open source |

!!! tip "Zigbee vs Zigbee2MQTT"
    Both drive the same plugs. The difference is what has to be running: the **MQTT** path needs Zigbee2MQTT (or Home Assistant) alive alongside BamDude, and the **Zigbee** path needs only a dongle plugged in. If you already run Zigbee2MQTT and it works, keep it — there is nothing to gain by moving. If you are starting from nothing, the Zigbee path is one service instead of three.

    Only one program can own a dongle. If Zigbee2MQTT or Home Assistant already has it, BamDude cannot take it as well — see [Troubleshooting](#per-type-troubleshooting).

---

## :material-zigbee: Zigbee setup

BamDude talks to Zigbee plugs itself. You plug a dongle into the machine running BamDude, pair the plugs from Settings, and that is the whole stack — no Home Assistant, no Zigbee2MQTT, no broker.

Verified end to end on a **SONOFF Zigbee Dongle-M** over Ethernet with a **SONOFF S60ZBTPF** plug. Other plugs should work if they expose a standard On/Off cluster; BamDude refuses to pair anything that does not, because it could not switch it anyway.

### 1. Connect the dongle

**Settings → Smart Plugs → Zigbee coordinator**:

| Field | What to enter |
|-------|---------------|
| **Transport** | `Ethernet` for a network dongle, `USB` for one plugged into the host |
| **Path** (Ethernet) | `host:port` — for example `192.168.1.50:6638` |
| **Path** (USB) | Chosen from the list of detected ports — no typing |

Press **Connect**. It takes effect immediately; BamDude does not need restarting.

!!! warning "The port is not optional on Ethernet"
    A bare address with no port is rejected on purpose. Left to itself the radio library would simply wait forever, and you would see "Zigbee is broken" with nothing to act on.

!!! tip "Ethernet survives more than USB"
    Ethernet is the default because it keeps working through things USB does not — a Docker container, a NAS, or a Windows host that renumbers COM ports across reboots. The dongle behaves identically either way; only the transport differs.

On Linux, prefer the `/dev/serial/by-id/...` form for USB — it survives replugging, while `/dev/ttyUSB0` can move.

### 2. Pair a plug

Press **Pair**, then walk to the plug and hold its pairing button. The card reports what the radio sees as it happens, so you are not guessing.

The pairing window is **60 seconds**. It closes on its own — an unattended window is not left open.

A device that BamDude cannot switch is **refused and removed from the network**, and the card says so rather than leaving you wondering where it went. That is the project's scope showing in the code: this is a plug feature, not a general Zigbee hub.

### 3. Add it as a plug

**Settings → Smart Plugs → Add → Zigbee**, then pick the device from the paired list. There is no address to type, and devices already used by another plug are left out of the list.

From here it behaves exactly like any other smart plug — printer binding, schedules, auto power-on/off, and per-print energy where the plug reports it.

### Power readings

BamDude loads the same per-model workaround library Home Assistant uses, so plugs with known firmware faults are handled rather than believed. On top of that it applies one rule of its own: **a socket that is switched off reports zero watts.** An open relay carries no load, whatever the plug claims — and cheap plugs do claim otherwise, which is how an empty socket once read 33 W.

Between switching a socket and the plug producing a fresh measurement, no wattage is shown at all rather than the previous one. Readings refresh every 30–45 seconds.

### Disconnecting and starting over

Two separate actions, because they cost very different amounts to undo:

| Action | What it does | Reversible |
|--------|--------------|:----------:|
| **Disconnect** | Stops the radio. Network, paired devices and plugs all kept | :material-check: Press Connect |
| **Forget network** | Erases the network key | :material-close: Re-pair every plug by hand |

**Forget network** is worth understanding before you press it. Your plugs go on believing they belong to a network BamDude can no longer speak to, so each one has to be paired again in person, wherever it is installed. Your plug entries and their settings are kept either way — they show as unreachable and come back on their own once re-paired, so a printer keeps its power automation and its recorded energy history.

!!! tip "Backups include the Zigbee network"
    A [backup](backup.md) taken beforehand can restore the network, so this is survivable. It is the only way back short of walking to every plug.

### Swapping the dongle

A dongle carries its network with it. Point BamDude at a different physical stick and it comes up perfectly healthy with **none** of your devices on it — they were never on that one's network.

BamDude recognises this and says so, naming the previous dongle, instead of leaving you with a green radio and every plug unreachable. Two ways back: plug the original dongle in again, or restore a backup taken while it was in use.

---

## :material-tasmota: Tasmota setup

### Adding a plug

**Settings → Smart Plugs → Add → Tasmota**:

=== "Automatic discovery"
    BamDude scans the LAN for Tasmota's mDNS broadcast. Plugs that respond appear in the **Discovered** list — pick one, give it a name, link it to a printer.

=== "Manual entry"
    | Field | Value |
    |-------|-------|
    | Name | "X1C plug" or whatever |
    | IP address | Plug's LAN IP (find via Tasmota web UI → Information, or your router's DHCP page) |
    | Username / Password | Only if web auth is set on the plug |

!!! tip "Static IP"
    Reserve the plug's IP in your router. DHCP renewal can flip the IP and break BamDude's link until you re-enter the address.

!!! note "One Tasmota plug per printer"
    A printer can have one Tasmota plug. Linking a second one is refused — when you add a plug, when you move a plug to another printer, and when you change an existing plug's type to Tasmota. Plugs of the other types can share a printer with it; see [Which plug powers the printer](#which-plug-powers-the-printer).

### Power control

Once linked, the printer card grows a **plug icon**. Click → toggles power state. Tooltip shows current draw + cumulative kWh.

| Icon | Meaning |
|:----:|---------|
| :material-power: green | Plug is on |
| :material-power-off: grey | Plug is off |
| :material-alert: red | Plug unreachable |

### Real-time data

When energy reporting is supported (almost all Tasmota plugs except basic relays), the card surfaces:

| Field | Source |
|-------|--------|
| Power (W) | `Status10.StatusSNS.ENERGY.Power` |
| Voltage (V) | `Status10.StatusSNS.ENERGY.Voltage` |
| Current (A) | `Status10.StatusSNS.ENERGY.Current` |
| Energy (kWh) | `Status10.StatusSNS.ENERGY.Total` (lifetime cumulative) |

Refreshed every 10 s while a BamDude tab showing the plug is open — the Printers page or the Smart Plugs settings tab. Nothing polls a Tasmota plug when no tab is watching, apart from the hourly energy snapshot; the reading you see is as fresh as the page you are looking at.

### Tasmota commands BamDude uses

For debugging, the same commands you'd run from the Tasmota Console:

```bash
# State
curl "http://PLUG_IP/cm?cmnd=Power"

# Turn on / off
curl "http://PLUG_IP/cm?cmnd=Power%20ON"
curl "http://PLUG_IP/cm?cmnd=Power%20OFF"

# Energy snapshot
curl "http://PLUG_IP/cm?cmnd=Status%2010"
```

If those work but BamDude doesn't see the plug, the issue is auth or IP routing — not the plug.

---

## :material-home-assistant: Home Assistant setup

### Initial config

The connection to Home Assistant is set up once per BamDude install, in its own card — not in the plug dialog.

1. Open **Settings → Network** and find the **Home Assistant** card. Turn on **Enable Home Assistant**.
2. Fill in:
    - **Home Assistant URL** — e.g. `http://homeassistant.local:8123` or `https://ha.example.com`
    - **Long-Lived Access Token** — in Home Assistant: Profile → Long-Lived Access Tokens → Create Token

3. Press **Test Connection**. When the test fails it names the cause — see [Troubleshooting](#per-type-troubleshooting).
4. Press **Save connection**. Connection changes stay a draft until you save them; testing does not save.

!!! tip "Set by environment variables"
    When `HA_URL` and `HA_TOKEN` are set in BamDude's environment, the connection is enabled automatically and the two fields are read-only, marked *(Environment Managed)* — no manual config needed.

### Adding a plug

**Settings → Smart Plugs → Add → Home Assistant**. While Home Assistant is not connected, the dialog says *Home Assistant is not configured. Set it up in Settings → Network → Home Assistant* and the entity list is disabled. Once it is connected, the **Select Entity** list loads every `switch.*` / `light.*` / `input_boolean.*` / `script.*` entity exposed by HA, without the entities another plug already uses.

- Pick the entity that controls the plug (`switch.x1c_smart_plug` etc.).
- For **separate energy sensor entities** (Tapo P110M, IKEA Tradfri, Shelly Plus Plug — they expose power/energy as `sensor.*` entities, not on the switch), the dialog has an **Energy Monitoring (Optional)** block with three searchable sensor lists:
    - **Power Sensor (W)** — current draw, e.g. `sensor.x1c_smart_plug_current_consumption`
    - **Energy Today (kWh)** — the day's figure, if the device has one
    - **Total Energy (kWh)** — the cumulative counter, e.g. `sensor.x1c_smart_plug_total_consumption`. Per-print energy and the date-range figures need this one

### HA scripts (multi-device control)

For "the printer plug + the chamber light + the enclosure fan all toggle together" workflows, build a **script** in HA:

```yaml
script:
  x1c_full_power_on:
    sequence:
      - service: switch.turn_on
        target:
          entity_id: switch.x1c_smart_plug
      - service: light.turn_on
        target:
          entity_id: light.x1c_chamber
      - delay: '00:00:15'
      - service: switch.turn_on
        target:
          entity_id: switch.x1c_chamber_fan
```

Then add a Home Assistant plug whose entity is `script.x1c_full_power_on` and link it to the printer. A printer can have several scripts. A script entry has the same controls as any Home Assistant plug:

- **Show on Printer Card** (in the add / edit dialog) — puts a button on the printer card. For a script the button runs it; for a switch, light or input boolean it toggles the entity.
- **Enabled** (on the plug card, under **Automation Settings**) — the script's automation switch. With it off, nothing runs the script except its own button.
- **Auto On** — the script runs when a print starts and when the printer's power is switched on.
- **Auto Off** — the script runs when the printer's power is switched off.
- **Show in Switchbar** — adds the entry to the quick-access switchbar in the sidebar.

#### When a linked script runs

A script linked to a printer follows that printer's power. A script with **Auto On** runs when the printer's plug is switched on, one with **Auto Off** when it is switched off — and at print start, like any plug with **Auto On**.

- **Switched by hand.** An explicit on or off of any plug of that printer runs the printer's scripts for that direction. A toggle — the single switch-style button of a Home Assistant entity shown on the printer card — runs none.
- **Switched by BamDude.** The scripts also run when BamDude switches the plug itself: a scheduled switch (**Daily Schedule**), the delayed or temperature-based switch-off after a print, a switch-off that was pending when BamDude restarted and is carried out after the restart, and a switch-off by [failure detection](obico.md). Here only the plug marked **This plug powers the printer** counts — an accessory switching off is not the printer switching off.
- **Once per direction within two minutes.** When several plugs feed one printer and all switch off after a print, the scripts run once, not once per plug.
- **A disabled script is not run.** A script whose **Enabled** switch is off is run by nothing but its own button — on the manual path as well as the automatic one.
- **A script is never "turned off".** Scripts are one-shot: BamDude only ever runs them. Failure detection's power-off switches the plugs and runs the **Auto Off** scripts; it sends no "turn off" to a script.

An automatic switch-on, and the scripts that follow it, wait while the [crash-start pause](farm-startup.md) is in effect, like every other automatic power-on.

---

## :material-api: REST / Webhook setup

For systems with a documented HTTP API (openHAB, ioBroker, FHEM, Node-RED, Shelly Cloud, Tapo Cloud, custom shell-script wrappers).

### Control URLs

**Settings → Smart Plugs → Add → REST/Webhook**:

| Field | Required | Example |
|-------|:--------:|---------|
| **ON URL** | ✓ | `http://openhab:8080/rest/items/X1C_Plug` |
| **ON body** |  | `ON` (text/plain) or `{"command": "on"}` (JSON) |
| **OFF URL** | ✓ | `http://openhab:8080/rest/items/X1C_Plug` |
| **OFF body** |  | `OFF` |
| **HTTP method** |  | `POST` (default), `PUT`, `GET` |
| **Headers (JSON)** |  | `{"Authorization": "Bearer abc123", "Content-Type": "application/json"}` |

### Status monitoring

If your system has a status endpoint:

| Field | Purpose |
|-------|---------|
| **Status URL** | `GET` endpoint returning current state |
| **Status path** | JSON path (`state`, `data.value`) or empty for plain-text response |
| **ON value** | What value indicates "on" (`ON`, `true`, `1`) |

### Energy monitoring (optional)

When power / energy live on a separate URL or path:

| Field | Purpose |
|-------|---------|
| **Power URL** | URL returning current watts (omit to share Status URL) |
| **Power path** | JSON path to power value (e.g. `data.power_w`) |
| **Power multiplier** | Unit fix (e.g. `0.001` if API returns mW) |
| **Energy URL** | URL returning the energy figures |
| **Energy path** | JSON path to the **daily** ("today") kWh value |
| **Energy multiplier** | Unit fix |
| **Lifetime Energy path** | JSON path to the **cumulative** kWh counter, if the plug reports one |
| **Lifetime multiplier** | Unit fix for the cumulative counter |

A multiplier is any number above 0, up to 10000 — however small. A plug that counts energy in **watt-seconds** (myStrom, for example) needs about `0.00000028` to arrive at kWh (1 Ws = 1 / 3 600 000 kWh). The same holds for the multipliers of an [MQTT plug](#mqtt-plug-setup).

!!! important "Fill in the Lifetime Energy path if your plug has one"
    The two energy paths are separate because a given endpoint may expose either, both, or neither — and they are **not interchangeable**. Anything that spans time needs a counter that only goes up:

    - **Energy per print** (and its cost, on the archive card) is the difference between the counter at print start and at print end.
    - **Date-range energy** on the Stats page is the difference between hourly snapshots of that counter.

    A daily figure resets at midnight, so it can't answer either — a REST plug without a cumulative value shows no per-print energy and a blank figure for any date range. Fill in the Lifetime Energy path and both work; the daily path is optional and only feeds the live "today" reading.

### Examples

=== "openHAB"
    ```
    ON URL:   http://openhab:8080/rest/items/X1C_Plug
    ON body:  ON
    OFF URL:  http://openhab:8080/rest/items/X1C_Plug
    OFF body: OFF
    Method:   POST
    Headers:  {"Content-Type": "text/plain"}

    Status URL:  http://openhab:8080/rest/items/X1C_Plug/state
    Status path: (empty - plain-text response)
    ON value:    ON
    ```

=== "ioBroker (simple-api)"
    ```
    ON URL:    http://iobroker:8087/set/sonoff.0.X1C.SWITCH?value=true
    OFF URL:   http://iobroker:8087/set/sonoff.0.X1C.SWITCH?value=false
    Method:    GET

    Status URL:  http://iobroker:8087/get/sonoff.0.X1C.SWITCH
    Status path: val
    ON value:    true
    ```

=== "FHEM"
    ```
    ON URL:    http://fhem:8083/fhem?cmd=set X1C_Plug on&XHR=1
    OFF URL:   http://fhem:8083/fhem?cmd=set X1C_Plug off&XHR=1
    Method:    GET

    Status URL: http://fhem:8083/fhem?cmd=get X1C_Plug STATE&XHR=1
    ```

=== "Node-RED"
    Wire two HTTP-In nodes (`/plug/on`, `/plug/off`) to relay nodes, then:
    ```
    ON URL:  http://node-red:1880/plug/on
    OFF URL: http://node-red:1880/plug/off
    Method:  POST
    ```

=== "Shelly Cloud (HTTPS)"
    ```
    ON URL:  https://shelly-XX-eu.shelly.cloud/device/relay/control
    ON body: {"channel": 0, "turn": "on", "id": "DEVICE_ID", "auth_key": "KEY"}
    Method:  POST
    Headers: {"Content-Type": "application/json"}
    ```

---

## :material-message-arrow-right-outline: MQTT plug setup

For Zigbee2MQTT, Shelly Gen2 native MQTT, ESPHome, custom broker plugs.

### Broker connection

BamDude uses **the broker config from Settings → MQTT**. Smart-plug MQTT plugs share that connection — no separate broker setup.

### Topic config

**Settings → Smart Plugs → Add → MQTT**:

| Field | Purpose | Example (Zigbee2MQTT) |
|-------|---------|------------------------|
| **Power topic** | Topic that publishes current watts | `zigbee2mqtt/x1c_plug` |
| **Power path** | JSON path inside the message | `power` |
| **Power multiplier** | Unit fix | `1.0` |
| **Energy topic** | Topic that publishes kWh | `zigbee2mqtt/x1c_plug` |
| **Energy path** | JSON path | `energy` |
| **Energy multiplier** | Unit fix | `1.0` |
| **State topic** | Topic that publishes ON/OFF | `zigbee2mqtt/x1c_plug` |
| **State path** | JSON path | `state` |
| **ON value** | What value means "on" | `ON` |

When state / energy / power live on **the same topic** (Zigbee2MQTT default), use the same topic for all three; only the JSON paths differ.

### Examples

=== "Zigbee2MQTT (IKEA Tradfri / Aqara / generic Zigbee plugs)"
    ```
    Power topic:  zigbee2mqtt/x1c_plug
    Power path:   power
    Energy topic: zigbee2mqtt/x1c_plug
    Energy path:  energy
    State topic:  zigbee2mqtt/x1c_plug
    State path:   state
    ON value:     ON
    ```

=== "Shelly Gen2 native MQTT"
    Three separate topics — Shelly Gen2 splits them:
    ```
    Power topic:  shellies/x1c_plug/status/switch:0
    Power path:   apower
    Energy topic: shellies/x1c_plug/status/switch:0
    Energy path:  aenergy.total
    State topic:  shellies/x1c_plug/status/switch:0
    State path:   output
    ON value:     true
    ```

=== "ESPHome"
    ```
    Power topic:  esphome/x1c_plug/sensor/power/state
    Power path:   (empty - plain-number payload)
    Energy topic: esphome/x1c_plug/sensor/total_energy/state
    Energy path:  (empty)
    State topic:  esphome/x1c_plug/switch/relay/state
    State path:   (empty)
    ON value:     ON
    ```

!!! warning "Switching an MQTT plug needs the Control block filled in"
    An MQTT plug is monitor-only by itself. The **Control** block — command topic plus **Payload to turn ON** / **Payload to turn OFF** — is what gives it a command channel. Leave the topic empty and the plug stays monitor-only.

    The payloads are free text on purpose, because they belong to the device: Zigbee2MQTT expects `{"state": "ON"}` on `<name>/set`, Tasmota a bare `ON` on `cmnd/<name>/POWER`.

    Power automation skips a plug with an empty command topic. It still reports measurements, while the queues can use a controllable plug to wake the printer. Obico reports the pause alone when its attempt to switch off the printer's mains did not succeed.

    Changing a plug's type or linked printer cancels its pending automatic shutdown. If you edit the command topic of a controllable MQTT plug, a shutdown that is still pending uses the new topic.

!!! tip "Per-print energy needs the Lifetime Energy block"
    Set **Lifetime JSON path** to a cumulative counter such as Zigbee2MQTT's `energy`. BamDude uses the difference between the start and end readings for per-print energy, including across midnight. A daily counter such as Tasmota's `ENERGY.Today` feeds the live daily reading and resets at midnight.

---

## :material-power-plug-outline: Switchbar quick access

Click the plug icon in the **sidebar footer** to open the global switchbar — every plug across the install with one-click toggle, regardless of which printer it's linked to. Useful for "kill power to the entire farm before I leave the workshop" workflows.

---

## :material-robot: Automation

### Which plug powers the printer

A printer can have several plugs linked to it: its own mains feed plus accessories — a chamber filter, enclosure lights, a filament dryer. The **"This plug powers the printer"** switch (under Link to Printer) tells BamDude which is which.

It's **on by default**, so nothing changes for a setup that has one plug per printer. Turn it off on accessories, because only the plug that's marked as the power source:

- **marks the printer offline** when it's switched off. An accessory doing that would blank the printer's state and stop the queue from sending it work, even though the printer is running fine.
- **is switched on first** when the printer's own queue wakes it for a job. The queue switches one plug — among the printer's enabled plugs with **Auto On**, a power-source plug first, then the lowest id — and the other enabled Auto On plugs follow once the printer has connected. Powering up a filter fan first would never bring the printer online, and the queue would sit waiting for a connection that can't happen.

The [Auto-Queue](auto-queue.md) wakes an offline printer differently: when a job aimed at a model finds every such printer off, it switches on **all** enabled Auto On plugs of the one printer it picks, at once.

Accessory plugs still switch on and off normally, and still report power and energy — they just don't speak for the printer's state.

**Per-print energy** is read from the first plug, in that order (the power source first), that actually reports an energy counter — so a mains switch with no power sensor does not hide the plug that meters the printer. The print's end is read from the **same** plug its start was, so two counters never make one figure. On the Smart Plugs tab, a plug counts as online when it answers, whether or not it measures energy.

### Auto Power On

When a queued print is ready and its printer is off, BamDude turns on the printer's power plug (see [Which plug powers the printer](#which-plug-powers-the-printer)) and goes on with the rest of the queue instead of waiting for this printer. The job shows *Printer powering on* while the printer boots and starts once it has connected; the printer's other enabled Auto On plugs are switched on then. A printer that has not connected within three minutes is left alone for ten minutes before it is switched on again, and so is one whose plug could not be reached or would not switch.

### Auto Power Off

Completion automation remains active while its own print finishes background work. Starting a new print permanently cancels the old run's delayed power-off authority, so a late timer cannot switch off the next print. This does not enable auto-off: the plug's own settings still decide whether to use it.

After a print completes, BamDude waits for bed cooldown, checks for more queued prints, then powers off.

Configure in **Settings → Smart Plugs** with cooldown temperature and time settings.

**Keep enabled toggle**: per-plug **Keep enabled** flag overrides auto-off — useful for the print-room HVAC plug or chamber lights you don't want auto-cycling. The Auto Power Off block on the plug card greys out when Keep enabled is on.

### Auto Off After Drying

A separate per-plug toggle, **Auto Off After Drying**, powers the plug down after an AMS drying cycle finishes — independent of the print-finish auto-off above. It fires whenever **any** AMS unit on the linked printer completes a drying cycle. Because the trigger is read from firmware state, all three drying paths are caught: queue-triggered drying, ambient drying, and a manually started cycle.

It has its own delay field, **defaulting to 10 minutes** (vs. 5 minutes for print-finish auto-off). The AMS chamber stays hot right after a cycle, so the longer default gives the filament and chamber more time to cool before power is cut.

It honours the same guards as the print-finish auto-off:

- The master plug **enabled** flag must be on.
- Home Assistant `script.*` entities can be *triggered* but never *turned off* (scripts are one-shot, not stateful).
- It always uses the **time-delay branch**. The temperature-based cooldown path applies to the hotend and isn't meaningful after a drying cycle, so it's bypassed here.

!!! note "Trigger granularity is per-printer, not per-AMS"
    The plug model is plug→printer, so per-AMS routing (a dedicated plug for just one AMS unit) isn't supported. The toggle fires when *any* AMS on the linked printer finishes drying — not a specific unit.

### Power Alerts

The **Power Alerts** toggle in the plug form adds two limits: **Alert if above (W)** and **Alert if below (W)**. Leave one empty to switch that direction off.

- **Checked in the background, for every plug type.** The alert is judged from the plug's recorded power readings, so it does not depend on anyone having the page open.
- **Once per excursion.** An alert is sent when the reading leaves its range, and the next one only after the reading has come back inside — not repeatedly while it stays out. One plug sends at most one alert in 5 minutes.
- **A plug that is off is never "low".** The lower limit applies only to a plug known to be switched on; a plug that is off, or whose switch state is unknown, is not reported.
- **Only fresh readings count.** A reading older than 20 minutes says nothing about now and raises nothing.
- **Delivered as Printer Error.** The alert goes through the `printer_error` notification event — to every provider, Telegram chat and inbox subscribed to it. See [Notifications](notifications.md).

After a restart of BamDude a plug that is still outside its range is announced once more.

### Safety considerations

- Auto-off **never fires** while bed temp is above the cooldown threshold (default 50 °C, configurable per-plug). Stops you from yanking power off a still-hot bed.
- Auto-off **never fires** while a print is `paused` (paused-by-user, paused-by-AMS, paused-by-runout). Resume the print first; if you cancel it instead, auto-off fires once cooldown completes.
- Auto-off **never fires** while the queue still has any non-completed jobs targeted at this printer. The next dispatch wakes the plug back up anyway, so spinning down would just add a wake-cycle delay.
- Auto-off **does fire** from `failed` and `cancelled` states once the bed is cool — same logic as `completed`.

If the plug is wired to control more than just the printer (PSU, chamber heater, lights — see the HA scripts section above), the Keep-enabled flag is what stops auto-off from killing your chamber heater mid-cooldown.

---

## :material-flash: Per-Print Energy Tracking

For smart plugs that report a kWh meter, BamDude captures the meter reading at print start and again on print complete. The delta is the energy consumed by **that specific print**, persisted on the archive row.

**How it works**

- Print starts → BamDude reads the plug's current kWh and writes it to `PrintArchive.energy_start_kwh`.
- Print completes → a fresh DB session re-reads the plug, computes `current - energy_start_kwh`, and stores the result on the archive.
- Failed and cancelled prints record partial energy — the delta from start to abort is still meaningful.

**Restart resilience**

`energy_start_kwh` is persisted on the archive row, never held in an in-memory dict. Restarting BamDude mid-print preserves the starting baseline and the print-end handler still produces the correct delta.

**Lifetime aggregation**

For "kWh used by printer X this month" reports, BamDude takes hourly snapshots in the `smart_plug_energy_snapshots` table. Date-range totals compute per-plug `max(0, last_in_range - baseline)` so meter resets (firmware reflashes, plug power cycles) don't cause negative deltas.

### Printing and at the plug

The Statistics page always shows both answers, as two pairs of tiles — there is no setting to choose one:

| Tiles | Source | Answers |
|-------|--------|---------|
| **Energy While Printing** · **Cost While Printing** | Sum of per-print archive deltas | "How much electricity did the prints I ran cost?" |
| **Energy At The Plug** · **Cost At The Plug** | The plugs' lifetime counters; hourly snapshots for a date range | "How much did the printers' plugs consume?" |

The two diverge when a printer is powered (heating, idle, standby) without an active print — only the plug pair captures that, and the gap is what standing still costs. See [Energy → Two Energy Figures](energy.md#two-energy-figures-printing-and-at-the-plug).

---

## :material-chart-line: Power draw over time

The plug row on a printer card has a chart button. It opens the plug's recorded power draw over the last six hours, day, two days or week — the same ranges and the same shape as the sensor charts, so a reader who knows one knows the other.

Readings are kept for a month while the chart window reaches a week. The gap is deliberate: a month of readings for one plug is far more points than any chart can usefully draw, and the retention is there for the range statistics rather than for the picture.

!!! info "How dense the line is depends on the plug type"
    Zigbee and MQTT plugs **report** on their own, so every report is recorded and the line is dense. Tasmota, REST and Home Assistant plugs never report — they are sampled by a background loop instead. Their history is therefore regular rather than event-driven, and coarser.

    There is deliberately **no de-duplication**: a plug that keeps reporting the same wattage and a plug that has gone silent must not look alike on the chart.

A reading BamDude received but cannot trust — no number, a relay state it does not know on a plug that may repeat old watts, a write that may not have landed — is a **gap** on the chart, never a zero and never joined to its neighbours. The same history checks whether the plug's energy counter keeps up: see [When a Plug's Counter Stops](energy.md#when-a-plugs-counter-stops).

---

## :material-wrench-cog: Reliability and Maintenance

Smart plugs are auto-resubscribed to MQTT on every BamDude startup via the `subscribe_plug_to_mqtt` helper. Most "plug stopped responding" cases are fixed by a single restart.

**If a plug doesn't respond after restart**

1. Confirm the plug works in its native app (Tasmota web UI / HA dashboard / Tasmota Console).
2. Check the plug's MQTT topic config in **Settings → Smart Plugs** — the per-type fields must match the plug's actual broker topics.
3. Restart BamDude one more time after fixing the topic.

The startup-restore code path, the create route, and the update route all funnel through the same helper, so the topic configuration can't drift between create and reconnect.

### A plug whose settings need correcting

A plug stored with settings its type cannot work with — a Tasmota plug without an IP address, a Home Assistant plug without an entity, an MQTT plug without any topic, a REST plug with neither an ON nor an OFF address, a Zigbee plug without a paired device, or a type BamDude does not know — is still listed. Its card, and its row on the printer card, carry the note **This plug's settings need correcting** with what is missing. The other plugs are not affected.

BamDude does not switch or poll such a plug until it is corrected. Open **Edit**, fill in what is missing and save — the note clears.

---

## :material-help-circle: Per-type troubleshooting

=== "Tasmota"
    **Plug shows offline / red dot**

    1. Plug's IP changed (DHCP renewal). Check Tasmota web UI at suspected new IP, update the plug's **IP address** field in BamDude.
    2. `curl "http://PLUG_IP/cm?cmnd=Power"` from BamDude host — if that returns 401, set the plug's web auth in BamDude. If it times out, it's a network-routing issue (VLAN, firewall) between BamDude and plug.

    **Power state desyncs (UI says off, plug is on)**

    Tasmota's native MQTT discovery is off by default. BamDude polls every 10 s while the page is open. Toggle the plug from BamDude — it'll resync. If it doesn't, the polling URL is wrong (rare, only if you hand-edited `IPAddress`).

    **Energy reading flatlines at zero**

    Plug doesn't have an energy meter. Verify with `Status 10` in Tasmota Console — if `ENERGY` block is missing, the plug is a relay-only model (e.g., Sonoff Basic without metering).

=== "Home Assistant"
    **Test button fails**

    The test names the cause instead of a general "failed":

    | The test says | What to do |
    |---------------|------------|
    | The address is not accepted | Enter an `http://` or `https://` address of your Home Assistant |
    | Home Assistant refused the access token | Create a new long-lived token and paste it |
    | Nothing answered at this address | Check the host, the port and that Home Assistant is running |
    | Home Assistant did not answer in time | Check the address and the network |
    | The certificate is not issued by an authority this server trusts | Use a certificate from a trusted authority, or add your own authority to the trust store of the machine BamDude runs on |
    | The certificate was issued for another name | Enter the host name the certificate was issued for, not an IP address or another name |
    | The certificate has expired | Renew it |
    | The secure connection failed | Check that this address and port serve https, or enter the address with `http://` |
    | The server answered with a redirect | Enter the address Home Assistant itself answers at |
    | Something answered, but not Home Assistant | Check the address and the port |

    To check from the command line:

    1. Verify HA URL is reachable from BamDude: `curl -H "Authorization: Bearer YOUR_TOKEN" $HA_URL/api/states` — should return JSON. If it returns 401, regenerate the long-lived token.
    2. HA URL needs the protocol prefix (`http://` or `https://`) — bare hostnames fail.
    3. If HA is behind a reverse proxy, make sure the proxy passes `Authorization` header through (some default configs strip it).

    **Entity dropdown is empty**

    BamDude only lists `switch.*`, `light.*`, `input_boolean.*`. If your HA integration exposes the plug as a `binary_sensor.*` (read-only), it won't appear — wrap it in an `input_boolean.*` template.

    **Energy values stuck at zero**

    The selected switch/light entity probably doesn't carry energy attributes. Pick the matching `sensor.*_total_consumption` in the **Total Energy (kWh)** list — most modern integrations expose energy as a separate sensor entity.

=== "REST / Webhook"
    **ON works, status check fails**

    Either:
    - Status URL returns a different shape than ON (use **Status path** to drill into JSON)
    - **ON value** doesn't match what the API returns. Run the status URL in `curl`, eyeball the response, set ON value to the literal that means "on".

    **Energy works in Postman, fails in BamDude**

    BamDude follows redirects but doesn't drink cookies. APIs that gate energy behind a session cookie (some Shelly Cloud paths, certain ioBroker setups) need a **persistent token** in headers, not cookie-based auth.

=== "MQTT"
    **Plug never updates**

    1. **Settings → MQTT → Connection status** must be green. If MQTT broker is offline, all MQTT plugs go silent.
    2. Verify the plug is publishing: `mosquitto_sub -t 'zigbee2mqtt/x1c_plug' -v` — should print messages every few seconds. If silent, fix at the plug side first.
    3. **State topic** matches the actual topic exactly (no typos). Trailing slashes matter.

    **Power reading is 1000× off**

    Wrong **multiplier**. Some integrations report watts, others report milliwatts. Run `mosquitto_sub` once, eyeball the value, set the multiplier so the result is in watts.

=== "Zigbee"
    **The coordinator will not start**

    The card shows the reason the radio itself gave — read it, it usually says what to do. The common ones:

    1. **Something else owns the dongle.** Only one program can. Stop Zigbee2MQTT or Home Assistant's ZHA, or use a second dongle. This is the most likely cause by far, and it applies across machines too — a Z2M instance elsewhere that opened the same `socket://` address holds it just as firmly.
    2. **No port on an Ethernet address.** `192.168.1.50` is refused; `192.168.1.50:6638` is what it wants.
    3. **Wrong USB port.** Pick from the detected list rather than typing.

    **Pairing finds nothing**

    Hold the plug's button until *it* signals pairing mode — most need several seconds, and a short press does nothing. Stay near the dongle for the first pairing. If the card reports a device and then refuses it, that device has no On/Off cluster: BamDude does not pair things it cannot switch.

    **The plug pairs but shows unreachable**

    Zigbee is a mesh with real range limits. A plug behind a wall or a floor from the dongle may pair at close range and then drop when installed. Mains-powered Zigbee devices repeat the signal, so a plug in between helps.

    **Every plug went unreachable at once**

    Look at the coordinator card first, not the plugs. Either the radio is down — the card says why — or you are on a different dongle, which BamDude reports explicitly. A dongle carries its network with it, so a swapped stick has none of your devices on it.

    **Power reads zero on a switched-off plug**

    That is deliberate, and correct: an open relay carries no load. Some plugs keep reporting the last measured value after switching off, which is a firmware fault, not a measurement — BamDude does not pass it on. Lifetime energy, which per-print cost is calculated from, is never zero-filled.

    **Wattage is blank right after switching**

    Also deliberate. The plug updates its own register in its own time, so any value in that moment describes a load that is no longer there. It fills in within 30–45 seconds.

    **A plug I unplugged still showed online for a while**

    Two different cases, answered at two different speeds on purpose. If the *dongle* goes down, every plug on it reads unreachable at once — that is the case people notice, and it needs no waiting. A *single* plug going quiet on an otherwise healthy mesh takes about two minutes to be called offline. That delay is deliberate: a plug wrongly marked offline is worse than one marked late, because that is the reading you act on.

    **Energy used today is blank on a new plug**

    Zigbee has no "today" figure in the protocol — the meter reports only a lifetime counter. BamDude works the day's use out from its own history since your local midnight, so until there is a reading to measure from, it shows nothing rather than a zero. A zero would read as "this plug used nothing", which is a different claim.

---

## :material-lightbulb: Tips

!!! tip "Start Simple"
    Start with manual power control before enabling automation.
    Build confidence in the plug's reliability before letting BamDude
    auto-cycle power.

!!! tip "Test Cooldown"
    Monitor a few prints to find the right cooldown temperature for
    your printer.

!!! tip "Pair with macros"
    Combine auto power-off with a `print_finished` macro to turn off
    chamber lights at the same time. See [Macros](macros.md).

!!! info "Automatic chamber light is a macro"
    There is no per-printer "auto light off" switch. Use a `chamber_light`
    MQTT-action macro with the value `off` on `print_finished` (and a
    symmetric one with `on` on `print_started` if you want full cycling).
    The macro framework adds delay control, on/off symmetry, per-model
    targeting, and per-swap-profile filtering.

!!! tip "Energy reporting"
    Read **Cost While Printing** if you charge customers per-print.
    Read **Cost At The Plug** for "what does my farm cost" reporting —
    it includes the idle/standby draw the printing figure leaves out.

> Originally based on [Bambuddy](https://github.com/maziggy/bambuddy) documentation.
