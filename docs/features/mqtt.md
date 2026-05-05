---
title: MQTT Publishing
description: Publish events to external MQTT brokers
---

# MQTT Publishing

BamDude can publish events to an external MQTT broker, enabling integration with **Home Assistant**, **Node-RED**, and other MQTT-based systems.

!!! info "Three different MQTT roles"
    BamDude touches MQTT in three independent places:

    1. **MQTT relay (this page)** -- BamDude *publishes* its own state to your external broker so HA / Node-RED can subscribe.
    2. **Printer-side MQTT** -- BamDude *connects to each printer's* internal MQTT broker (Bambu's protocol) to receive `push_status` and send commands. Configured per-printer when you add the printer; invisible to operators after that.
    3. **Smart-plug MQTT subscriber** -- a separate code path subscribes BamDude *to your broker* to receive smart-plug telemetry (Tasmota / Zigbee2MQTT / Sonoff). Configured per-plug under **Settings > Smart Plugs**.

    This page only covers the relay (#1).

---

## :material-cog: Configuration

Navigate to **Settings > Network > MQTT Publishing**.

| Setting | Description | Default |
|---------|-------------|---------|
| **Enable MQTT** | Toggle publishing on/off | Off |
| **Broker Hostname** | MQTT broker address | -- |
| **Port** | Broker port | 1883 (8883 with TLS) |
| **Username** | Authentication (optional) | -- |
| **Password** | Authentication (optional) | -- |
| **Topic Prefix** | Prefix for all topics | `bambuddy` (legacy default — change to `bamdude` if starting fresh) |
| **Use TLS** | Enable TLS/SSL encryption | Off |

!!! tip "Port auto-population"
    When you toggle **Use TLS** on, the port field auto-fills `8883` (the default MQTT-over-TLS port). Toggle it off and the port snaps back to `1883`. You can override either default — auto-fill only fires when the field still holds the default for the previous mode.

---

## :material-broadcast: Published Topics

All topics are prefixed with your configured prefix. **The default prefix is `bambuddy`** (inherited from upstream Bambuddy and never auto-rotated to avoid breaking existing HA integrations on upgrade). Change it under Settings → Network if you'd rather subscribe to `bamdude/...`. The examples below use `bambuddy/` to match an out-of-the-box install — substitute your actual prefix.

### Service status

| Topic | Description | Retained |
|-------|-------------|----------|
| `bambuddy/status` | LWT-based service status. Payload `online` when BamDude is running, `offline` published as Last-Will when the broker loses the connection. | Yes |

### Printer events

| Topic | Description |
|-------|-------------|
| `bambuddy/printers/{serial}/status` | Real-time printer state (throttled) |
| `bambuddy/printers/{serial}/online` | Printer just came online |
| `bambuddy/printers/{serial}/offline` | Printer just went offline |
| `bambuddy/printers/{serial}/print/started` | Print job started |
| `bambuddy/printers/{serial}/print/completed` | Print completed (status=`completed`) |
| `bambuddy/printers/{serial}/print/failed` | Print failed (status=`failed`) |
| `bambuddy/printers/{serial}/ams/changed` | AMS filament changed |
| `bambuddy/printers/{serial}/error` | HMS / firmware error |

### Queue events

| Topic | Description |
|-------|-------------|
| `bambuddy/queue/job_added` | Job added to queue |
| `bambuddy/queue/job_started` | Job started printing |
| `bambuddy/queue/job_completed` | Job completed successfully |
| `bambuddy/queue/job_failed` | Job ended with status=`failed` (same publisher as `job_completed`, branched on status) |

### Maintenance events

| Topic | Description |
|-------|-------------|
| `bambuddy/maintenance/alert` | A maintenance task tripped its threshold |
| `bambuddy/maintenance/acknowledged` | A maintenance alert was acknowledged in the UI |
| `bambuddy/maintenance/reset` | A maintenance counter was reset (task marked done) |

### Smart plug events

| Topic | Description |
|-------|-------------|
| `bambuddy/smart_plugs/on` | Smart plug just turned on (post-confirmation, not just the request). Payload includes `plug_id`, `plug_name`, `bound_printer_id`. |
| `bambuddy/smart_plugs/off` | Smart plug just turned off. |
| `bambuddy/smart_plugs/energy` | Periodic energy snapshot. Payload includes `kwh_total`, `current_watts`, `voltage`, `printer_id` if bound. |

### Archive events

| Topic | Description |
|-------|-------------|
| `bambuddy/archive/created` | New archive row created (post-3MF parse). Payload: `archive_id`, `printer_id`, `task_name`, `effective_hash`, `created_at`. |
| `bambuddy/archive/updated` | Archive row mutated (status flipped, plate metadata refilled, retry-download succeeded, etc.). Payload includes the changed fields. |

---

## :material-code-json: Payload format

All payloads are JSON objects. Example printer status payload:

```json
{
  "printer_id": 1,
  "printer_name": "X1C-1",
  "printer_serial": "00M09C411500579",
  "timestamp": "2026-05-04T12:00:00.000000",
  "connected": true,
  "state": "PRINTING",
  "progress": 45.5,
  "remaining_time": 3600,
  "layer_num": 150,
  "total_layers": 300,
  "current_print": "benchy.3mf",
  "subtask_name": "Benchy",
  "temperatures": {
    "bed": 60.0,
    "bed_target": 60.0,
    "nozzle": 220.0,
    "nozzle_target": 220.0,
    "chamber": 35.0
  },
  "wifi_signal": -55,
  "chamber_light": true,
  "speed_level": 2,
  "cooling_fan_speed": 100,
  "big_fan1_speed": 50,
  "big_fan2_speed": 50
}
```

The status payload is throttled to roughly 1/second — the printer-side MQTT can fire several times per second on heavy prints, so BamDude coalesces.

---

## :material-home-assistant: Home Assistant Example

BamDude does not currently publish Home Assistant MQTT-discovery messages — you wire sensors manually under your `configuration.yaml`. The flat topic / JSON payload structure is mature, so manual configuration is straightforward.

```yaml
mqtt:
  sensor:
    - name: "X1C Print Progress"
      state_topic: "bambuddy/printers/YOUR_SERIAL/status"
      value_template: "{{ value_json.progress }}"
      unit_of_measurement: "%"

    - name: "X1C State"
      state_topic: "bambuddy/printers/YOUR_SERIAL/status"
      value_template: "{{ value_json.state }}"

    - name: "X1C Bed Temperature"
      state_topic: "bambuddy/printers/YOUR_SERIAL/status"
      value_template: "{{ value_json.temperatures.bed }}"
      unit_of_measurement: "°C"
      device_class: temperature

    - name: "X1C Nozzle Temperature"
      state_topic: "bambuddy/printers/YOUR_SERIAL/status"
      value_template: "{{ value_json.temperatures.nozzle }}"
      unit_of_measurement: "°C"
      device_class: temperature

  binary_sensor:
    - name: "BamDude Online"
      state_topic: "bambuddy/status"
      payload_on: "online"
      payload_off: "offline"
      device_class: connectivity
```

---

## :material-flow-tree: Node-RED switch-by-topic

Subscribe to `bambuddy/#` with an **MQTT in** node, then route by topic:

```
[MQTT in: bambuddy/#] → [Switch (msg.topic)] → [Function / Pushover / Slack]
```

Example switch rules — fire a Pushover notification when an archive is created on printer X1C-1:

```json
{
  "type": "switch",
  "rules": [
    {
      "t": "regex",
      "v": "^bambuddy/archive/created$",
      "case": false
    },
    {
      "t": "else"
    }
  ],
  "checkall": "true",
  "outputs": 2
}
```

Wire the first output to a Function that filters `msg.payload.printer_name === "X1C-1"`, then to a Pushover / Telegram out node. The second output is the catch-all you can drop or log.

---

## :material-lock: TLS / SSL handling

When **Use TLS** is on:

- BamDude opens the broker connection over TLS using the system certificate store.
- **Self-signed broker certificates are not verified by default** — the connection is still encrypted, but the cert chain isn't validated. This makes home-lab setups with a local Mosquitto + self-signed cert work out of the box. For production deployments, sign your broker cert against a CA the system trusts (Let's Encrypt, internal PKI) and the connection upgrades to fully verified.
- Username + password are sent **inside** the TLS tunnel — they're encrypted on the wire even with self-signed certs.

If you need strict cert verification, install your CA into the host's trust store (`/etc/ssl/certs/` + `update-ca-certificates`); BamDude's MQTT client picks it up via the system bundle.

---

## :material-help-circle: Troubleshooting

The Settings page shows a connection-status dot:

| Indicator | Meaning |
|---|---|
| Green | Connected; last `bambuddy/status` payload was `online`. |
| Red | Disconnected. Hover for the last error (auth fail / connection refused / TLS handshake / DNS). |
| Grey | MQTT publishing is disabled. |

### Common issues

| Issue | Solution |
|---|---|
| `Not authorized` / red dot after save | Username / password mismatch on the broker. Test with `mosquitto_sub` first. |
| `Connection refused` | Broker hostname / port wrong, or broker not running. Check from the BamDude host: `nc -vz <broker> 1883`. |
| TLS handshake error | Broker doesn't actually speak TLS on the configured port — `1883` is plain, `8883` is TLS by convention. Toggle Use TLS to match. |
| Topic not publishing | The event isn't firing yet — check the printer / queue is actually doing the thing the topic claims to track. `bambuddy/printers/.../print/started` only fires when a print begins, not on every reconnect. |
| Subscriber sees nothing | Subscriber's topic filter doesn't match. Use `bambuddy/#` to see everything, then narrow once you confirm the prefix. |

### Testing with mosquitto_sub

```bash
# Subscribe to all BamDude topics
mosquitto_sub -h your-broker -t "bambuddy/#" -v

# With authentication
mosquitto_sub -h your-broker -u username -P password -t "bambuddy/#" -v

# With TLS
mosquitto_sub -h your-broker -p 8883 --cafile ca.crt -t "bambuddy/#" -v

# Just the LWT status
mosquitto_sub -h your-broker -t "bambuddy/status" -v
```

---

## :material-lightbulb: Tips

!!! tip "Topic Discovery"
    Use MQTT Explorer to browse published topics and understand the payload structure.

> Originally based on [Bambuddy](https://github.com/maziggy/bambuddy) documentation.
