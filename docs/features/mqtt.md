---
title: MQTT Publishing
description: Publish events to external MQTT brokers
---

# MQTT Publishing

BamDude can publish events to an external MQTT broker, enabling integration with **Home Assistant**, **Node-RED**, and other MQTT-based systems.

Status lights need no broker: BamDude drives a [WLED](wled.md) controller directly.

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
| **Topic Prefix** | Prefix for all topics | `bamdude` (set to `bambuddy` to keep the topics of an install that still used the old default) |
| **Use TLS** | Enable TLS/SSL encryption | Off |
| **Verify the broker's certificate** | Shown when Use TLS is on. Check the certificate and the host name against the system's trusted authorities; refuse to connect when the check fails. | Off |

!!! tip "Port auto-population"
    When you toggle **Use TLS** on, the port field auto-fills `8883` (the default MQTT-over-TLS port). Toggle it off and the port snaps back to `1883`. You can override either default — auto-fill only fires when the field still holds the default for the previous mode.

---

## :material-broadcast: Published Topics

All topics are prefixed with your configured prefix. **The default prefix is `bamdude`** (the old default was `bambuddy`, inherited from upstream). If you publish to an external broker and never set a prefix explicitly, upgrading from an install that still used the old default moves your topics from `bambuddy/...` to `bamdude/...` — update your Home Assistant / Node-RED subscriptions accordingly, or set the prefix back to `bambuddy` under Settings → Network to keep the old topics. The example topics below are written with the `bambuddy/` prefix for continuity — substitute your actual prefix.

### Service status

| Topic | Description | Retained |
|-------|-------------|----------|
| `bambuddy/status` | Service status, a JSON object: `{"status": "online", "timestamp": …}` while BamDude is connected, `"offline"` on shutdown — and, as the broker's last-will message, when the connection is lost without one. | Yes |

### Printer events

| Topic | Description |
|-------|-------------|
| `bambuddy/printers/{serial}/status` | Real-time printer state (throttled, retained), including the door, the active extruder, the loaded tray, the AMS, the external spool, active HMS errors and `awaiting_plate_clear` |
| `bambuddy/printers/{serial}/plate_clear` | Retained plate-clear gate: `awaiting: true` means waiting for an operator to clear the plate; refreshed after reconnect, including offline printers |
| `bambuddy/printers/{serial}/online` | Printer just came online. Fires on the **connection edge**, so it is a transition, not a heartbeat. |
| `bambuddy/printers/{serial}/offline` | Printer just went offline — the same edge, the other direction. |
| `bambuddy/printers/{serial}/print/started` | Print job started |
| `bambuddy/printers/{serial}/print/completed` | Print completed (status=`completed`). Also published on the next start for a print that ended while BamDude was stopped. |
| `bambuddy/printers/{serial}/print/failed` | Print ended any other way; `status` says how (`failed`, `cancelled`, …) |
| `bambuddy/printers/{serial}/ams/changed` | AMS filament changed |
| `bambuddy/printers/{serial}/filament/low` | A loaded spool crossed its low mark — once per crossing. Payload: `slot`, `remaining_percent`, `color`, `spool_id` (BamDude's own inventory; `null` with Spoolman). |
| `bambuddy/printers/{serial}/error` | HMS / firmware error |

### Queue events

| Topic | Description |
|-------|-------------|
| `bambuddy/queue/job_added` | A job landed in a printer's queue — however it arrived: the queue page or API, the slicer plugin, Auto-Queue handing it to a printer, a Virtual Printer, Retry / Clone / Repeat, the Telegram bot. A job waiting in Auto-Queue is announced when a printer receives it. A job whose library file or archive is gone is named by the file it was queued from; a calibration test print is not announced. |
| `bambuddy/queue/job_started` | Job started printing |
| `bambuddy/queue/job_completed` | Job completed successfully |
| `bambuddy/queue/job_failed` | Job ended any other way; `status` says how (`failed`, `cancelled`, …) |

### Maintenance events

| Topic | Description |
|-------|-------------|
| `bambuddy/maintenance/alert` | A maintenance task is due or close to it. Payload: `maintenance_type`, `current_value` (what has passed since it was last done), `threshold` (its interval) and `unit` (`hours` of printing or `days`). |
| `bambuddy/maintenance/reset` | A maintenance counter was reset (task marked done) |

!!! note "There is no `maintenance/acknowledged`"
    It would describe an action BamDude does not have: an alert is **raised**, and then
    **reset** when the work is done. There is no separate acknowledgement step —
    `alert` and `reset` are the whole lifecycle.

### Smart plug events

| Topic | Description |
|-------|-------------|
| `bambuddy/smart_plugs/on` | BamDude switched a plug on and the device accepted the command — by the button, the schedule, the automation around a print, the queue waking a printer. Payload: `plug_id`, `plug_name`, `state`, `printer_id`, `printer_name`. |
| `bambuddy/smart_plugs/off` | The same for switching off, including the delayed and temperature-based auto-off and failure detection. A plug switched by hand on the device itself is not published. |
| `bambuddy/smart_plugs/energy` | **Hourly**, alongside the energy snapshot BamDude already records. Payload: `plug_id`, `plug_name`, `power_watts`, `energy_today_kwh`, `energy_total_kwh`, `timestamp`. A figure the plug does not report is `null`, never 0. |

### Archive events

| Topic | Description |
|-------|-------------|
| `bambuddy/archive/created` | An archive row was created — at print start. Payload: `archive_id`, `print_name`, `printer_name`, `status`. |
| `bambuddy/archive/updated` | The archive's status changed when its print ended. Payload: `archive_id`, `print_name`, `status`. |

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
  "big_fan2_speed": 50,
  "left_aux_fan_speed": null,
  "exhaust_fan_present": null,
  "door_open": false,
  "active_extruder": 0,
  "tray_now": 2,
  "ams": [
    {"id": 0, "humidity": 31, "temp": 25.0, "tray": [{"id": 0, "tray_type": "PLA", "tray_color": "FF0000FF"}]}
  ],
  "vt_tray": [],
  "hms_errors": [],
  "awaiting_plate_clear": false
}
```

The status payload is throttled to roughly 1/second — the printer-side MQTT can fire several times per second on heavy prints, so BamDude coalesces. A printer going offline or coming back is published at once, never held back by the throttle.

`door_open`, `active_extruder`, `tray_now`, `ams`, `vt_tray` and `hms_errors` are built by the same code as the printer's REST status (`GET /api/v1/printers/{id}/status`) and the web interface's live updates, in the same shape; the AMS example above is shortened. One case reads differently from the REST answer: on a printer without an AMS `ams` is `null` (REST: `[]`). A drying cycle started from BamDude shows its filament and target temperature, as the card does. `vt_tray` and `hms_errors` are empty lists when there is nothing to report.

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
      value_template: "{{ value_json.status }}"
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

- BamDude opens the broker connection over TLS.
- **By default the broker's certificate is not verified** — the connection is encrypted, but neither the certificate chain nor the host name is checked. This is what lets a local Mosquitto with a self-signed certificate work out of the box; it also means the encryption does not prove which broker answered. Keep such a broker on a network you trust.
- Turn on **Verify the broker's certificate** to have both checked against the authorities the system trusts (a certificate from Let's Encrypt, or your own CA installed in the host's trust store). BamDude then does not connect to a broker that fails the check. Changing the switch asks for the broker password again, because it changes where the password may be sent. MQTT smart plugs use the same broker connection settings.
- Username + password are sent **inside** the TLS tunnel — they're encrypted on the wire even with self-signed certs.

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
