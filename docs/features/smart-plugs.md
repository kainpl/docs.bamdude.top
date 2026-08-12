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

Pulled every 5 s while the plug is on; cached when off.

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

1. **Settings → Smart Plugs → Add → Home Assistant** (one-time per BamDude install).
2. Fill in:
    - **HA URL** — e.g. `http://homeassistant.local:8123` or `https://ha.example.com`
    - **HA Long-Lived Access Token** — HA → click profile → bottom of page → Long-lived access tokens → **Create token**

3. Hit **Test** — BamDude pings `/api/states` to verify URL + token. The form is locked behind that check.

!!! tip "HA add-on auto-config"
    If you run BamDude as a **Home Assistant add-on**, the install pre-populates `HA_URL` + `HA_TOKEN` env vars from the supervisor. The fields show locks (:material-lock:) — no manual config needed.

### Adding a plug

After the HA URL is set, the **Add Plug → Home Assistant** dropdown lists every `switch.*` / `light.*` / `input_boolean.*` entity exposed by HA.

- Pick the entity that controls the plug (`switch.x1c_smart_plug` etc.).
- For **separate energy sensor entities** (Tapo P110M, IKEA Tradfri, Shelly Plus Plug — they expose power/energy as `sensor.*` entities, not on the switch), the form has secondary dropdowns for the matching sensor:
    - **Power sensor** — `sensor.x1c_smart_plug_current_consumption`
    - **Energy sensor** — `sensor.x1c_smart_plug_total_consumption`

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

Then create a Smart Plug entry pointing at `script.x1c_full_power_on` (HA scripts also expose the standard `switch.*` interface). On the plug card:

- :material-checkbox-marked: **Run when on** — fire the script on power-on
- :material-checkbox-marked: **Show on Printer Card** — surface the toggle directly on the card instead of behind the cog

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

!!! important "Fill in the Lifetime Energy path if your plug has one"
    The two energy paths are separate because a given endpoint may expose either, both, or neither — and they are **not interchangeable**. Anything that spans time needs a counter that only goes up:

    - **Energy per print** (and its cost, on the archive card) is the difference between the counter at print start and at print end.
    - **Date-range energy** on the Stats page is the difference between hourly snapshots of that counter.

    A daily figure resets at midnight, so it can't answer either. Before 0.4.7b4 BamDude filed whatever a REST plug returned under "today" and never had a cumulative value at all — which is why REST plugs showed no per-print energy and a blank figure for any date range. Fill in the Lifetime Energy path and both start working; the daily path is optional and only feeds the live "today" reading.

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
    The MQTT plug type was monitor-only from the day it was added until migration `m113`. The **Control** block — command topic plus **Payload to turn ON** / **Payload to turn OFF** — is what gives it a command channel. Leave the topic empty and the plug stays monitor-only, which is also what an existing plug does after the upgrade, since the columns arrive empty.

    The payloads are free text on purpose, because they belong to the device: Zigbee2MQTT expects `{"state": "ON"}` on `<name>/set`, Tasmota a bare `ON` on `cmnd/<name>/POWER`.

    Before `m113` a switch attempt did not fail — it silently did nothing, because the plug fell through to the Tasmota driver and got an HTTP call aimed at an `ip_address` an MQTT plug has no reason to have. Auto-on at print start, auto-off afterwards, schedules, the manual buttons and Obico's pause-and-power-off were all affected alike.

!!! tip "Per-print energy needs the Lifetime Energy block"
    **Lifetime JSON path** is separate from the ordinary energy path because a plug may publish either a counter that resets at midnight (Tasmota's `ENERGY.Today`) or a running total that never resets (Zigbee2MQTT's `energy`), and only you know which yours points at. Per-print energy and cost need the running total: a print that crosses midnight would otherwise measure as **negative**.

---

## :material-power-plug-outline: Switchbar quick access

Click the plug icon in the **sidebar footer** to open the global switchbar — every plug across the install with one-click toggle, regardless of which printer it's linked to. Useful for "kill power to the entire farm before I leave the workshop" workflows.

---

## :material-robot: Automation

### Which plug powers the printer

A printer can have several plugs linked to it: its own mains feed plus accessories — a chamber filter, enclosure lights, a filament dryer. The **"This plug powers the printer"** switch (under Link to Printer) tells BamDude which is which.

It's **on by default**, so nothing changes for a setup that has one plug per printer. Turn it off on accessories, because only the plug that's marked as the power source:

- **marks the printer offline** when it's switched off. An accessory doing that used to blank the printer's state and stop the queue from sending it work, even though the printer was running fine.
- **gets switched on** to wake the printer for a queued print. Powering up a filter fan would never bring the printer online, and the queue would sit waiting for a connection that can't happen.

Accessory plugs still switch on and off normally, and still report power and energy — they just don't speak for the printer's state.

### Auto Power On

When a queued print is ready, BamDude turns on the plug that powers the printer, waits for it to boot, then starts the print.

### Auto Power Off

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

### Energy Display Mode

In **Settings → System → "Energy display mode"**:

| Mode | Source | Use Case |
|------|--------|----------|
| `print` | Sum of per-print archive deltas | "How much electricity did the prints I ran cost?" |
| `total` (default) | Lifetime plug counter via snapshot range | "How much did the printer's plug consume?" |

The two modes can diverge when the printer is powered (heating, idle, standby) without an active print — only `total` captures that.

---

## :material-wrench-cog: Reliability and Maintenance

Smart plugs are auto-resubscribed to MQTT on every BamDude startup via the `subscribe_plug_to_mqtt` helper. Most "plug stopped responding" cases are fixed by a single restart.

**If a plug doesn't respond after restart**

1. Confirm the plug works in its native app (Tasmota web UI / HA dashboard / Tasmota Console).
2. Check the plug's MQTT topic config in **Settings → Smart Plugs** — the per-type fields must match the plug's actual broker topics.
3. Restart BamDude one more time after fixing the topic.

The startup-restore code path, the create route, and the update route all funnel through the same helper, so the topic configuration can't drift between create and reconnect.

---

## :material-help-circle: Per-type troubleshooting

=== "Tasmota"
    **Plug shows offline / red dot**

    1. Plug's IP changed (DHCP renewal). Check Tasmota web UI at suspected new IP, update the plug's **IP address** field in BamDude.
    2. `curl "http://PLUG_IP/cm?cmnd=Power"` from BamDude host — if that returns 401, set the plug's web auth in BamDude. If it times out, it's a network-routing issue (VLAN, firewall) between BamDude and plug.

    **Power state desyncs (UI says off, plug is on)**

    Tasmota's native MQTT discovery is off by default. BamDude polls every 5 s. Toggle the plug from BamDude — it'll resync. If it doesn't, the polling URL is wrong (rare, only if you hand-edited `IPAddress`).

    **Energy reading flatlines at zero**

    Plug doesn't have an energy meter. Verify with `Status 10` in Tasmota Console — if `ENERGY` block is missing, the plug is a relay-only model (e.g., Sonoff Basic without metering).

=== "Home Assistant"
    **Test button fails**

    1. Verify HA URL is reachable from BamDude: `curl -H "Authorization: Bearer YOUR_TOKEN" $HA_URL/api/states` — should return JSON. If it returns 401, regenerate the long-lived token.
    2. HA URL needs the protocol prefix (`http://` or `https://`) — bare hostnames fail.
    3. If HA is behind a reverse proxy, make sure the proxy passes `Authorization` header through (some default configs strip it).

    **Entity dropdown is empty**

    BamDude only lists `switch.*`, `light.*`, `input_boolean.*`. If your HA integration exposes the plug as a `binary_sensor.*` (read-only), it won't appear — wrap it in an `input_boolean.*` template.

    **Energy values stuck at zero**

    The selected switch/light entity probably doesn't carry energy attributes. Pick the matching `sensor.*_total_consumption` in the **Energy sensor** dropdown — most modern integrations expose energy as a separate sensor entity.

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

!!! info "`auto_light_off` is gone — macros replaced it"
    The legacy `auto_light_off` flag on each printer was dropped in
    migration `m021`. Recreate the behaviour with a `chamber_light_off`
    MQTT-action macro on `print_finished` (and a symmetric
    `chamber_light_on` on `print_started` if you want full cycling).
    The macro framework adds delay control, on/off symmetry, per-model
    targeting, and per-swap-profile filtering — none of which the old
    boolean had.

!!! tip "Energy reporting"
    Switch the energy display mode to `print` if you charge customers
    per-print. Use `total` for personal "what does my farm cost"
    reporting — it includes idle/standby draw that `print` misses.

> Originally based on [Bambuddy](https://github.com/maziggy/bambuddy) documentation.
