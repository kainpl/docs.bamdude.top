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

---

## :material-broadcast: Published Topics

All topics are prefixed with your configured prefix. **The default prefix is `bambuddy`** (inherited from upstream Bambuddy and never auto-rotated to avoid breaking existing HA integrations on upgrade). Change it under Settings → Network if you'd rather subscribe to `bamdude/...`. The examples below use `bambuddy/` to match an out-of-the-box install — substitute your actual prefix.

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

---

## :material-home-assistant: Home Assistant Example

```yaml
mqtt:
  sensor:
    - name: "Printer Status"
      state_topic: "bambuddy/printers/YOUR_SERIAL/status"
      value_template: "{{ value_json.state }}"
```

---

## :material-lightbulb: Tips

!!! tip "Topic Discovery"
    Use MQTT Explorer to browse published topics and understand the payload structure.

> Originally based on [Bambuddy](https://github.com/maziggy/bambuddy) documentation.
