---
title: Smart Plugs
description: Tasmota, Home Assistant, MQTT, and REST/Webhook power control with per-print energy tracking
---

# Smart Plugs

Control your printers with Tasmota, Home Assistant, REST/Webhook, or MQTT smart plugs for power monitoring, automation, and per-print energy tracking.

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

!!! info "Plug picks for Bambu printers"
    A1 / A1 mini draw ~140 W peak; X1 / P1 series peak ~350 W; H2 series peak ~500 W. Any 10A / 16A plug fits, but **for energy reporting** the popular options are:

    - **Athom Plug Pro** (US/EU/UK, Tasmota pre-flashed) — best price/feature, native Tasmota
    - **Tapo P110M / P115** (HA integration via `tapo-control`) — cheap + reliable, HA-only
    - **Shelly Plus Plug** (HA + native MQTT + REST) — most flexible, three integration paths
    - **IKEA Tradfri** outlet (HA via Zigbee2MQTT) — energy reporting requires Zigbee2MQTT v1.30+

---

## :material-flash: Choosing an integration path

Each plug usually supports more than one of the four types. Pick by:

| You already run | Best path | Why |
|-----------------|-----------|-----|
| Home Assistant | **Home Assistant** | One-stop entity dropdown, HA does the auth |
| Bare Tasmota plug | **Tasmota** | Native Tasmota commands, no broker needed |
| Zigbee2MQTT / ESPHome | **MQTT** | Subscribe direct, no extra hop |
| openHAB / FHEM / ioBroker | **REST / Webhook** | Their REST APIs map cleanly to ON/OFF + status URLs |
| Just-bought stock plug | **Tasmota** (after flashing) | Best long-term reliability + open source |

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
| **Energy URL** | URL returning lifetime kWh |
| **Energy path** | JSON path to energy value |
| **Energy multiplier** | Unit fix |

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

!!! warning "Control via MQTT"
    The native MQTT plug type was monitor-only in early 0.4.x. Power control (`mqtt_command_topic` / `mqtt_command_on` / `mqtt_command_off` fields) was added in m020+; if your install was upgraded from <0.4.0 and the fields are blank, the plug is read-only until you fill them.

---

## :material-power-plug-outline: Switchbar quick access

Click the plug icon in the **sidebar footer** to open the global switchbar — every plug across the install with one-click toggle, regardless of which printer it's linked to. Useful for "kill power to the entire farm before I leave the workshop" workflows.

---

## :material-robot: Automation

### Auto Power On

When a queued print is ready, BamDude turns on the plug, waits for the printer to boot, then starts the print.

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
