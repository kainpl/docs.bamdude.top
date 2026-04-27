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
| **Префікс топіків** | Префікс для всіх топіків | `bambuddy` (legacy за замовчуванням — змініть на `bamdude` для нових інсталяцій) |
| **Використовувати TLS** | Увімкнення шифрування TLS/SSL | Вимкнено |

---

## :material-broadcast: Топіки, що публікуються

Усі топіки мають налаштований вами префікс. **Префікс за замовчуванням — `bambuddy`** (успадковано з апстрім Bambuddy і не змінюється авто, щоб не ламати наявні HA-інтеграції на оновленнях). Змініть під Settings → Network, якщо хочете підписатися на `bamdude/...`. Приклади нижче використовують `bambuddy/`, щоб відповідати out-of-the-box-інсталяції — підставте свій реальний префікс.

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

---

## :material-home-assistant: Приклад для Home Assistant

```yaml
mqtt:
  sensor:
    - name: "Printer Status"
      state_topic: "bambuddy/printers/YOUR_SERIAL/status"
      value_template: "{{ value_json.state }}"
```

---

## :material-lightbulb: Поради

!!! tip "Огляд топіків"
    Використовуйте MQTT Explorer для перегляду опублікованих топіків та розуміння структури повідомлень.

> Початково базується на документації [Bambuddy](https://github.com/maziggy/bambuddy).
