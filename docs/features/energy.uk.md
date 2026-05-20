---
title: Облік енергії
description: Per-print і lifetime облік електроенергії через smart plugs
---

# Облік енергії (Energy Tracking)

Відстежуйте електроенергію, спожиту кожним друком, і за весь lifetime принтера, потім помножте на ваш kWh-тариф для cost. Числа йдуть прямо з energy register розумної розетки — не з оцінок.

---

## :material-information: Що це

BamDude читає два значення з кожної розумної розетки:

1. **Live wattage** — скільки ват принтер тягне зараз.
2. **Lifetime energy counter** — загальні kWh, які розетка нарахувала з моменту скиду.

Коли друк стартує, lifetime counter записується на рядок архіву як `energy_start_kwh`. Коли друк завершується, BamDude читає counter знову і зберігає дельту як `energy_kwh`. Стартове значення живе **на рядку архіву, а не у пам'яті** — тож якщо backend перезапуститься посеред друку, per-print дельта все одно правильно порахується при completion.

Для lifetime / date-range вьюх щогодинний background-loop робить snapshot lifetime counter кожної розетки у `smart_plug_energy_snapshots`. Date-range total потім рахується як `last_snapshot_in_range − last_snapshot_before_range` per plug.

!!! info "Потрібен дозвіл"
    Читання даних про енергію вимагає `stats:read`. Tracking стартує автоматично, як тільки розетка прив'язана до принтера — окремого тогла "enable energy tracking" немає.

---

## :material-power-plug: Вимоги

Облік енергії потребує розумної розетки з **kWh metering** між розеткою у стіні та принтером. Тип розетки, деталі power monitoring і кроки конфігурації — у [Smart Plugs](smart-plugs.md).

| Тип розетки | kWh Metering | Нотатки |
|-------------|:------------:|---------|
| Tasmota | :material-check: | Native HTTP energy endpoint |
| Home Assistant | :material-check: | Bind HA energy sensor entity |
| REST / Webhook | :material-check: | Вкажіть JSON path для kWh |
| MQTT | :material-check: | Вкажіть MQTT topic + JSON path |

Розетки без energy register (прості on/off) теж працюють для power control, але їхні рядки архіву матимуть `NULL` `energy_kwh` і не зайдуть у lifetime totals.

---

## :material-meter-electric: Per-Print kWh

Зберігається на `PrintArchive`:

| Колонка | Коли пишеться | Що означає |
|---------|---------------|------------|
| `energy_start_kwh` | На старті друку | Lifetime counter розетки на момент початку друку |
| `energy_kwh` | При завершенні | `(end_counter − energy_start_kwh)`, скільки kWh з'їв саме цей друк |
| `energy_cost` | При завершенні | `energy_kwh × cost_per_kwh` (у вашій валюті) |

**Restart-resilient.** Оскільки `energy_start_kwh` персиститься на рядок архіву у тій самій транзакції, що і `started_at`, краш backend'у або перезапуск контейнера посеред друку **не втрачає baseline** — наступний `on_print_complete` правильно порахує дельту.

**Failed і cancelled друки теж записують енергію.** 6-годинний друк, який впав на 4-й годині, спожив 4 години електрики — дельта все ще змістовна і все ще пишеться.

---

## :material-counter: Lifetime kWh та діапазони дат

Щогодинний snapshot-loop (`SmartPlugManager._snapshot_loop`) пише один рядок на розетку у `smart_plug_energy_snapshots`:

| Колонка | Що означає |
|---------|------------|
| `plug_id` | FK до розумної розетки |
| `recorded_at` | UTC timestamp снапшоту |
| `lifetime_kwh` | Lifetime energy register розетки на той момент |

Для діапазону `[date_from, date_to]` BamDude рахує per plug:

```
range_total = max(0, last_snapshot_in_range − last_snapshot_before_range)
```

`max(0, …)` клампить до нуля, коли lifetime counter був скинутий (наприклад, factory-reset розетки), щоб ви ніколи не отримали від'ємну енергію.

---

## :material-cash: Калькуляція cost

Cost — це single-rate проти lifetime / per-print дельти:

```
cost = energy_kwh × energy_cost_per_kwh
```

Налаштуйте rate у **Settings → System → Energy**:

| Setting | Опис |
|---------|------|
| `energy_cost_per_kwh` | Ваша ціна за kWh (default `0.15`) |

Numeric rate безрозмірний — показуйте cost у тій валюті, що відповідає вашому реальному тарифу. BamDude не конвертує валюти; він просто множить.

---

## :material-toggle-switch: Energy Tracking Mode

**Settings → System → Energy → Energy Tracking Mode** (`energy_tracking_mode`):

| Mode | Що означає "Energy used" на Stats |
|------|------------------------------------|
| `print` | Сума per-archive `energy_kwh` за діапазон. Без idle, standby, chamber-only heating. Pure printing cost. |
| `total` *(default)* | Lifetime plug counter через snapshot range — `last_in_range − baseline_before_range`. Включає idle / standby / chamber heating / firmware-update сесії / усе, що принтер тягнув, поки був у розетці. |

Виберіть `print`, якщо білите клієнтів per job. Виберіть `total`, якщо хочете знати, скільки реально коштує тримати ферму ввімкнутою.

---

## :material-clock-alert: Індикатор "Warming-Up"

Mode `total` потребує **хоча б один snapshot до початку обраного діапазону**, щоб порахувати baseline. На свіжому install, відразу після апгрейду на білд, що везе snapshot support, або одразу після зсуву `Last 7 days` у вікно без попереднього snapshot — цього baseline ще немає.

Коли так, сторінка Stats показує жовту іконку попередження поруч з **Energy Used** і **Energy Cost**:

> :material-alert-outline: *Still warming up — at least one plug doesn't have a snapshot from before the start of your range.*

Іконка зникає, як тільки накопичиться достатньо snapshot'ів. Налаштовувати нічого не треба; система просто збирає дані. Backend-флаг: `energy_data_warming_up=True` у відповіді stats.

---

## :material-home-automation: Tibber / Octopus / Dynamic Tariff

Якщо у вас динамічний тариф (Tibber, Octopus, Nordpool, …), пушайте live-rate у BamDude з Home Assistant — кожна cost-калькуляція тоді користуватиметься поточним тарифом замість static value.

### 1. Створіть API key

**Settings → API Keys → Create** і ввімкніть на ключі toggle **Update electricity price**. Це вузько-обмежений opt-in для `POST /settings/electricity-price` — він **не** надає загальний settings-write дозвіл (старий `PATCH /settings` лишається). Скопіюйте ключ.

!!! note "Старі docs згадували `PATCH /settings`"
    Загальний `PATCH /settings` все ще працює з API key, але виставляє увесь settings payload (SMTP / LDAP / MQTT credentials, HA token, всі UI-ручки) — значно ширшу поверхню, ніж потрібно для dynamic-tariff кейсу. Новий `POST /settings/electricity-price` приймає тільки `{energy_cost_per_kwh}`, повертає повну settings response щоб HA міг переконатись що значення прийнялось, і захищений per-key toggle-ом — адмін має явно opt-in. Конфіги що вказують на legacy URL продовжать працювати; перейдіть на новий URL при наступному оновленні конфігу.

### 2. Додайте REST command у HA

У `configuration.yaml`:

```yaml
rest_command:
  bamdude_electricity_price:
    url: "http://YOUR_BAMDUDE_IP:8000/api/v1/settings/electricity-price"
    method: POST
    headers:
      X-API-Key: "YOUR_API_KEY"
    content_type: "application/json"
    payload: '{"energy_cost_per_kwh": {{ states("sensor.electricity_price") }}}'
```

### 3. Тригерніть REST command на зміну ціни

```yaml
automation:
  - id: bamdude_push_electricity_price
    alias: "Update BamDude electricity price"
    mode: restart
    trigger:
      - platform: state
        entity_id: sensor.electricity_price
        for: "00:00:05"
    condition:
      - condition: template
        value_template: >
          {{ states('sensor.electricity_price')|float(none) is not none }}
    action:
      - service: rest_command.bamdude_electricity_price
```

| Постачальник | Типовий sensor entity |
|--------------|-----------------------|
| Tibber | `sensor.tibber_prices` (current price attribute) |
| Octopus Energy | `sensor.octopus_energy_electricity_current_rate` |
| Nordpool | `sensor.nordpool_kwh_*` |

!!! tip "Перевірте, що sensor повертає число"
    BamDude чекає numeric value для `energy_cost_per_kwh`. Якщо ваш sensor повертає рядок із currency symbol, поправте template (`{{ states('sensor.x')|float }}`) перед push.

Більше про архітектуру HA-інтеграції — у [Smart Plugs → Home Assistant](smart-plugs.md).

---

## :material-chart-line: Віджети на Stats Page

Сторінка Statistics показує енергію у трьох місцях:

- **Energy used** (kWh) за діапазон, з урахуванням `energy_tracking_mode`
- **Energy cost** у вашій валюті
- **Per-printer breakdown** — який саме принтер тягне найбільше

Графіки і totals синхронізовані з тогл `print` vs `total` — перемикання перебудовує їх серверно. Повний тур по віджетах — у [Statistics](stats.uk.md).

---

## :material-link: Дивіться також

- [Smart Plugs](smart-plugs.md) — типи розеток, конфігурація, HA / Tasmota / REST / MQTT setup
- [Archiving](archiving.md) — поля `energy_kwh` / `energy_cost` на кожному рядку архіву
- [Statistics](stats.uk.md) — energy віджет, cost charts, date-range фільтри
- [Print Queue](print-queue.md) — auto-power-off після друку + smart-plug-driven автоматизація черги
- [Export](export.md) — CSV/XLSX з колонками per-print energy + cost

---

## :material-lightbulb: Поради

!!! tip "Беріть реальний тариф"
    Витягніть all-in rate з останнього рахунку (energy + delivery + taxes + fees). "Headline" rate з сайту постачальника зазвичай занижує реальну вартість.

!!! tip "Failed-друки теж коштують"
    `energy_kwh` записується для `failed` і `cancelled` архівів теж — це ще один аргумент за [Failure Analysis](failure-analysis.md) і [Obico](obico.md). Кожен fail — це реальні гроші на лічильнику.

!!! tip "Snapshot baselines потребують uptime"
    Щогодинний snapshot loop працює лише поки BamDude працює. Якщо ви зупинили контейнер на два дні і питаєте 7-day total, відсутні 48 годин виглядають як flat baseline — warming-up іконка це підкаже.

!!! tip "Print mode для інвойсів, total mode для ROI"
    Перемикайтеся на `print`, експортуючи інвойси клієнтам — вони не повинні платити за ваш standby. Перемикайтеся на `total`, коли рахуєте, чи ферма окуповує себе.
