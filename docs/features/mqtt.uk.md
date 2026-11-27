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
| **Префікс топіків** | Префікс для всіх топіків | `bamdude` (виставте `bambuddy`, щоб лишити топіки інсталяції, яка ще працювала зі старим типовим префіксом) |
| **Використовувати TLS** | Увімкнення шифрування TLS/SSL | Вимкнено |
| **Перевіряти сертифікат брокера** | Показується, коли TLS увімкнено. Звіряти сертифікат та ім'я хоста з довіреними центрами системи; не підключатися, якщо перевірка не пройшла. | Вимкнено |

!!! tip "Auto-заповнення порту"
    Коли вмикаєш **Use TLS**, поле порту авто-заповнюється `8883` (стандартний порт MQTT-over-TLS). Вимикаєш — повертається `1883`. Можеш override-нути будь-яке з default-значень — auto-fill спрацьовує тільки коли поле тримає default попереднього режиму.

---

## :material-broadcast: Топіки, що публікуються

Усі топіки мають налаштований вами префікс. **Префікс за замовчуванням — `bamdude`** (раніше типовим був `bambuddy`, успадкований з апстріму). Якщо ви публікуєте на зовнішній брокер і ніколи не задавали префікс явно, оновлення з інсталяції, яка ще працювала зі старим типовим префіксом, переносить ваші топіки з `bambuddy/...` на `bamdude/...` — оновіть підписки Home Assistant / Node-RED відповідно, або поверніть префікс на `bambuddy` під Settings → Network, щоб лишити старі топіки. Приклади топіків нижче написані з префіксом `bambuddy/` для наступності — підставте свій реальний префікс.

### Статус сервісу

| Топік | Опис | Retained |
|-------|------|----------|
| `bambuddy/status` | Статус сервісу, JSON-об'єкт: `{"status": "online", "timestamp": …}`, поки BamDude підключений, `"offline"` при зупинці — і, як last-will повідомлення брокера, коли з'єднання втрачено без неї. | Так |

### Події принтера

| Топік | Опис |
|-------|------|
| `bambuddy/printers/{serial}/status` | Стан принтера (з обмеженням частоти, retained), включно з дверцятами, активним екструдером, заправленим лотком, AMS, зовнішньою котушкою, активними помилками HMS і `awaiting_plate_clear` |
| `bambuddy/printers/{serial}/plate_clear` | Retained-стан очищення плити: `awaiting: true` означає очікування підтвердження оператора; оновлюється після перепідключення, зокрема для офлайн-принтерів |
| `bambuddy/printers/{serial}/online` | Принтер щойно зайшов у мережу. Спрацьовує на **межі з'єднання**, тобто це перехід, а не heartbeat. |
| `bambuddy/printers/{serial}/offline` | Принтер щойно вийшов із мережі — та сама межа, в інший бік. |
| `bambuddy/printers/{serial}/print/started` | Друк розпочато |
| `bambuddy/printers/{serial}/print/completed` | Друк завершено (status=`completed`). Публікується й після наступного старту для друку, що закінчився, поки BamDude був зупинений. |
| `bambuddy/printers/{serial}/print/failed` | Друк закінчився будь-як інакше; `status` каже як (`failed`, `cancelled`, …) |
| `bambuddy/printers/{serial}/ams/changed` | Зміна філаменту в AMS |
| `bambuddy/printers/{serial}/filament/low` | Завантажена котушка перетнула поріг малого залишку — один раз на перетин. Payload: `slot`, `remaining_percent`, `color`, `spool_id` (власний облік BamDude; `null` зі Spoolman). |
| `bambuddy/printers/{serial}/error` | HMS / firmware-помилка |

### Події черги

| Топік | Опис |
|-------|------|
| `bambuddy/queue/job_added` | Завдання потрапило в чергу принтера — хоч як воно прийшло: сторінка черги чи API, плагін слайсера, Auto-Queue передав його принтеру, Virtual Printer, Retry / Clone / Repeat, Telegram-бот. Завдання, що чекає в Auto-Queue, оголошується, коли його отримує принтер. Завдання, чий файл бібліотеки чи архів уже зник, названо за файлом, з якого його поставили в чергу; тестовий друк калібрування не оголошується. |
| `bambuddy/queue/job_started` | Завдання почало друкуватися |
| `bambuddy/queue/job_completed` | Завдання завершено успішно |
| `bambuddy/queue/job_failed` | Завдання закінчилось будь-як інакше; `status` каже як (`failed`, `cancelled`, …) |

### Події обслуговування

| Топік | Опис |
|-------|------|
| `bambuddy/maintenance/alert` | Завдання обслуговування настало або наближається. Payload: `maintenance_type`, `current_value` (скільки минуло від останнього виконання), `threshold` (інтервал) і `unit` (`hours` друку або `days`). |
| `bambuddy/maintenance/reset` | Maintenance-counter скинуто (завдання позначено виконаним) |

!!! note "Топіка `maintenance/acknowledged` немає"
    Він описував би дію, якої в BamDude немає: алерт **піднімається**, а потім
    **скидається**, коли роботу виконано. Окремого кроку підтвердження не існує —
    `alert` і `reset` — це весь життєвий цикл.

### Події розумних розеток

| Топік | Опис |
|-------|------|
| `bambuddy/smart_plugs/on` | BamDude увімкнув розетку, і пристрій прийняв команду — кнопкою, за розкладом, автоматикою навколо друку, чергою, що будить принтер. Payload: `plug_id`, `plug_name`, `state`, `printer_id`, `printer_name`. |
| `bambuddy/smart_plugs/off` | Те саме для вимкнення, включно з відкладеним і температурним автовимкненням та виявленням збоїв. Розетка, перемкнута кнопкою на самому пристрої, не публікується. |
| `bambuddy/smart_plugs/energy` | **Щогодини**, разом зі знімком енергії, який BamDude і так записує. Payload: `plug_id`, `plug_name`, `power_watts`, `energy_today_kwh`, `energy_total_kwh`, `timestamp`. Значення, якого розетка не повідомляє, — `null`, а не 0. |

### Події архіву

| Топік | Опис |
|-------|------|
| `bambuddy/archive/created` | Створено рядок архіву — на старті друку. Payload: `archive_id`, `print_name`, `printer_name`, `status`. |
| `bambuddy/archive/updated` | Статус архіву змінився, коли його друк закінчився. Payload: `archive_id`, `print_name`, `status`. |

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

Статус публікується не частіше ніж приблизно раз на секунду: на важких друках принтер може слати по MQTT кілька повідомлень на секунду, тож BamDude їх об'єднує. Принтер, що зник зі зв'язку чи повернувся, публікується одразу — обмеження частоти його не затримує.

`door_open`, `active_extruder`, `tray_now`, `ams`, `vt_tray` і `hms_errors` будує той самий код, що й REST-статус принтера (`GET /api/v1/printers/{id}/status`) та оновлення в інтерфейсі, і вигляд у них той самий; приклад AMS вище скорочено. Від відповіді REST вони відрізняються у двох випадках: на принтері без AMS `ams` — `null` (у REST — `[]`), а поки триває сушіння, запущене з BamDude, `dry_filament` і `dry_target_temp` блока заповнені, лише коли котушки в ньому одного матеріалу; значення самого циклу є в REST-статусі. `vt_tray` і `hms_errors` — порожні списки, коли нічого немає.

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
      value_template: "{{ value_json.status }}"
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

- BamDude відкриває з'єднання з брокером по TLS.
- **Типово сертифікат брокера не перевіряється** — з'єднання зашифроване, але ні ланцюжок сертифікатів, ні ім'я хоста не звіряються. Саме тому локальний Mosquitto із самопідписаним сертифікатом працює одразу; це також означає, що шифрування не доводить, який саме брокер відповів. Тримайте такий брокер у мережі, якій довіряєте.
- Увімкніть **Перевіряти сертифікат брокера**, щоб звіряти і те, і те з центрами, яким довіряє система (сертифікат Let's Encrypt або власний CA, встановлений у сховище довіри хоста). Тоді BamDude не підключається до брокера, що не пройшов перевірку. Зміна перемикача знову просить пароль брокера, бо змінює те, куди пароль може бути надіслано. MQTT-розетки використовують ті самі налаштування з'єднання з брокером.
- Username + password йдуть **всередині** TLS-тунелю — шифровані на дроті навіть з self-signed.

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
