---
title: Публікація MQTT
description: Публікація подій до зовнішніх MQTT-брокерів
---

# Публікація MQTT

BamDude може публікувати події до зовнішнього MQTT-брокера, що дозволяє інтеграцію з **Home Assistant**, **Node-RED** та іншими системами на базі MQTT.

!!! info "Три різні ролі MQTT"
    BamDude взаємодіє з MQTT у трьох незалежних місцях:

    1. **MQTT-relay (ця сторінка)** — BamDude *публікує* власний стан до вашого зовнішнього брокера, щоб HA / Node-RED могли підписатися.
    2. **MQTT з боку принтера** — BamDude *підключається до внутрішнього MQTT-брокера кожного принтера* (протокол Bambu), щоб отримувати `push_status` і надсилати команди. Налаштовується для кожного принтера під час його додавання; після цього невидимий для операторів.
    3. **MQTT-підписник для розумних розеток** — окремий код підписує BamDude *до вашого брокера*, щоб отримувати телеметрію розумних розеток (Tasmota / Zigbee2MQTT / Sonoff). Налаштовується для кожної розетки в **Налаштування > Розумні розетки**.

    Ця сторінка охоплює лише relay (#1).

---

## :material-cog: Налаштування

Перейдіть до **Налаштування > Мережа > Публікація MQTT**.

| Параметр | Опис | За замовчуванням |
|----------|------|------------------|
| **Увімкнути MQTT** | Увімкнення/вимкнення публікації | Вимкнено |
| **Адреса брокера** | Адреса MQTT-брокера | -- |
| **Порт** | Порт брокера | 1883 (8883 з TLS) |
| **Ім'я користувача** | Автентифікація (необов'язково) | -- |
| **Пароль** | Автентифікація (необов'язково) | -- |
| **Префікс топіків** | Префікс для всіх топіків | `bamdude` (виставте `bambuddy`, щоб лишити топіки, що були до 0.4.5 включно) |
| **Використовувати TLS** | Увімкнення шифрування TLS/SSL | Вимкнено |

!!! tip "Auto-заповнення порту"
    Коли вмикаєш **Use TLS**, поле порту авто-заповнюється `8883` (стандартний порт MQTT-over-TLS). Вимикаєш — повертається `1883`. Можеш override-нути будь-яке з default-значень — auto-fill спрацьовує тільки коли поле тримає default попереднього режиму.

---

## :material-broadcast: Топіки, що публікуються

Усі топіки мають налаштований вами префікс. **Префікс за замовчуванням — `bamdude`** (релізи до 0.4.5 включно використовували `bambuddy`, успадкований з апстріму). Якщо ви публікуєте на зовнішній брокер і ніколи не задавали префікс явно, оновлення з такого старішого релізу переносить ваші топіки з `bambuddy/...` на `bamdude/...` — оновіть підписки Home Assistant / Node-RED відповідно, або поверніть префікс на `bambuddy` під Settings → Network, щоб лишити старі топіки. Приклади топіків нижче написані з префіксом `bambuddy/` для наступності — підставте свій реальний префікс.

### Статус сервісу

| Топік | Опис | Retained |
|-------|------|----------|
| `bambuddy/status` | LWT-based статус сервісу. Payload `online` коли BamDude крутиться, `offline` публікується як Last-Will коли брокер втратив зв'язок. | Так |

### Події принтера

| Топік | Опис |
|-------|------|
| `bambuddy/printers/{serial}/status` | Стан принтера в реальному часі (з обмеженням частоти) |
| `bambuddy/printers/{serial}/online` | Принтер щойно зайшов у мережу |
| `bambuddy/printers/{serial}/offline` | Принтер щойно вийшов із мережі |
| `bambuddy/printers/{serial}/print/started` | Друк розпочато |
| `bambuddy/printers/{serial}/print/completed` | Друк завершено (status=`completed`) |
| `bambuddy/printers/{serial}/print/failed` | Друк не вдався (status=`failed`) |
| `bambuddy/printers/{serial}/ams/changed` | Зміна філаменту в AMS |
| `bambuddy/printers/{serial}/error` | HMS / firmware-помилка |

### Події черги

| Топік | Опис |
|-------|------|
| `bambuddy/queue/job_added` | Завдання додано до черги |
| `bambuddy/queue/job_started` | Завдання почало друкуватися |
| `bambuddy/queue/job_completed` | Завдання завершено успішно |
| `bambuddy/queue/job_failed` | Завдання завершилось зі status=`failed` (той самий publisher, що й `job_completed`, гілкується за статусом) |

### Події обслуговування

| Топік | Опис |
|-------|------|
| `bambuddy/maintenance/alert` | Завдання обслуговування перетнуло поріг |
| `bambuddy/maintenance/acknowledged` | Maintenance-alert підтверджено в UI |
| `bambuddy/maintenance/reset` | Maintenance-counter скинуто (завдання позначено виконаним) |

### Події розумних розеток

| Топік | Опис |
|-------|------|
| `bambuddy/smart_plugs/on` | Розетка щойно увімкнулась (post-confirmation, не просто запит). Payload містить `plug_id`, `plug_name`, `bound_printer_id`. |
| `bambuddy/smart_plugs/off` | Розетка щойно вимкнулась. |
| `bambuddy/smart_plugs/energy` | Періодичний знімок енергії. Payload містить `kwh_total`, `current_watts`, `voltage`, `printer_id` якщо прив'язана. |

### Події архіву

| Топік | Опис |
|-------|------|
| `bambuddy/archive/created` | Створено новий рядок архіву (post-3MF parse). Payload: `archive_id`, `printer_id`, `task_name`, `effective_hash`, `created_at`. |
| `bambuddy/archive/updated` | Архів-рядок змінено (статус flip-нувся, plate-metadata refilled, retry-download succeed-нуло, etc.). Payload містить змінені поля. |

---

## :material-code-json: Формат payload

Усі payload-и — JSON-об'єкти. Приклад printer status payload:

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

Status payload throttle-нутий приблизно до 1/секунди — printer-side MQTT може фірити кілька разів на секунду на важких друках, тож BamDude коалесить.

---

## :material-home-assistant: Приклад для Home Assistant

BamDude поки що не публікує Home Assistant MQTT-discovery — сенсори вписуєш руками в `configuration.yaml`. Структура топіків / JSON-payload-ів стабільна, тож manual-конфіг прямолінійний.

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

Підпишись на `bambuddy/#` через **MQTT in** ноду і роутай за топіком:

```
[MQTT in: bambuddy/#] → [Switch (msg.topic)] → [Function / Pushover / Slack]
```

Приклад switch-правил — фірити Pushover-сповіщення, коли архів створено на принтері X1C-1:

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

Перший вихід — на Function, що фільтрує `msg.payload.printer_name === "X1C-1"`, далі на Pushover / Telegram out node. Другий вихід — catch-all, можна дропнути або логувати.

---

## :material-lock: TLS / SSL

Коли **Use TLS** увімкнено:

- BamDude відкриває з'єднання з брокером по TLS, використовуючи системний trust store.
- **Self-signed broker-серти не верифікуються за замовчуванням** — з'єднання все одно зашифроване, але cert chain не валідується. Це робить home-lab сетапи з локальним Mosquitto + self-signed серт працюючими out of the box. Для production — підпиши broker-серт під CA, якій довіряє система (Let's Encrypt, internal PKI), і з'єднання стане повністю верифікованим.
- Username + password йдуть **всередині** TLS-тунелю — шифровані на дроті навіть з self-signed.

Якщо потрібен strict cert verification, постав CA в host trust store (`/etc/ssl/certs/` + `update-ca-certificates`); MQTT-клієнт BamDude підбере його через системний bundle.

---

## :material-help-circle: Усунення несправностей

Сторінка Settings показує крапку статусу:

| Індикатор | Значення |
|---|---|
| Зелена | Конект; останній `bambuddy/status` payload — `online`. |
| Червона | Disconnected. Ховер для останньої помилки (auth fail / connection refused / TLS handshake / DNS). |
| Сіра | MQTT publishing вимкнено. |

### Типові проблеми

| Проблема | Розв'язок |
|---|---|
| `Not authorized` / червона після save | Username / password mismatch у брокері. Тестуй `mosquitto_sub` спершу. |
| `Connection refused` | Невірний hostname / port, або брокер не запущений. Перевір з BamDude-хоста: `nc -vz <broker> 1883`. |
| TLS handshake error | Брокер не говорить TLS на цьому порту — `1883` plain, `8883` TLS за конвенцією. Тогглі Use TLS відповідно. |
| Топік не публікується | Подія ще не фірить — перевір, що принтер / черга реально робить те, що топік трекає. `bambuddy/printers/.../print/started` фірить лише на старт друку, не на кожен reconnect. |
| Subscriber нічого не бачить | Topic-фільтр subscriber-а не збігається. Юзай `bambuddy/#` щоб побачити все, потім звужуй коли підтвердив префікс. |

### Тестування з mosquitto_sub

```bash
# Підписка на всі BamDude-топіки
mosquitto_sub -h your-broker -t "bambuddy/#" -v

# З автентифікацією
mosquitto_sub -h your-broker -u username -P password -t "bambuddy/#" -v

# З TLS
mosquitto_sub -h your-broker -p 8883 --cafile ca.crt -t "bambuddy/#" -v

# Тільки LWT-статус
mosquitto_sub -h your-broker -t "bambuddy/status" -v
```

---

## :material-lightbulb: Поради

!!! tip "Огляд топіків"
    Використовуйте MQTT Explorer для перегляду опублікованих топіків та розуміння структури повідомлень.

> Початково базується на документації [Bambuddy](https://github.com/maziggy/bambuddy).
