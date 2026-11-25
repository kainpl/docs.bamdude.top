---
title: Метрики Prometheus
description: Експорт телеметрії принтерів для дашбордів Grafana
---

# Метрики Prometheus

BamDude може надавати телеметрію принтерів у форматі Prometheus для інтеграції з **Grafana**, **Prometheus** та іншими системами моніторингу.

---

## :material-cog: Налаштування

Перейдіть до **Налаштування > Мережа > Метрики Prometheus**.

| Параметр | Ключ у БД | Опис | За замовчуванням |
|----------|-----------|------|------------------|
| **Увімкнути метрики** | `prometheus_enabled` | Увімкнення/вимкнення ендпоінту | Вимкнено |
| **Bearer Token** | `prometheus_token` | Обов’язкова Bearer-token автентифікація на `/metrics` | Порожній (встановіть перед увімкненням) |

!!! info "Автентифікація"
    Метрики мають власний обов'язковий Bearer-token, незалежний від входу до застосунку. Вимкнено — 404; відсутній/неправильний Bearer — 401. Увімкнена стара конфігурація з порожнім токеном повертає 503: спочатку збережіть токен у налаштуваннях. Endpoint містить виробництво й склад; токен надає читання на рівні всього сервера.

---

## :material-api: Ендпоінт

```
GET /api/v1/metrics
```

Повертає метрики у [текстовому форматі експозиції Prometheus](https://prometheus.io/docs/instrumenting/exposition_formats/).

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://bamdude:8000/api/v1/metrics
```

---

## :material-chart-line: Доступні метрики

Стара телеметрія принтерів має `printer_id`, `printer_name`, `serial`; виробничі gauge використовують ID та описані нижче мітки.

### Build info

| Метрика | Тип | Опис |
|---------|-----|------|
| `bamdude_build_info` | gauge | `version`, `python_version`, `platform`, `architecture` (завжди = 1) |

### Стан окремого принтера

| Метрика | Тип | Опис |
|---------|-----|------|
| `bamdude_printer_connected` | gauge | Статус з'єднання (1/0) |
| `bamdude_printer_state` | gauge | 0=unknown, 1=idle, 2=running, 3=pause, 4=finish, 5=failed, 6=prepare, 7=slicing |
| `bamdude_print_progress` | gauge | Поточний прогрес друку (0-100) |
| `bamdude_print_remaining_seconds` | gauge | Орієнтовний залишковий час (секунди) |
| `bamdude_print_layer_current` | gauge | Номер поточного шару |
| `bamdude_print_layer_total` | gauge | Загальна кількість шарів у поточному друці |

### Температури + вентилятори

| Метрика | Тип | Опис |
|---------|-----|------|
| `bamdude_bed_temp_celsius` | gauge | Поточна температура столу |
| `bamdude_bed_target_celsius` | gauge | Цільова температура столу |
| `bamdude_nozzle_temp_celsius` | gauge | Поточна температура сопла (лейбл `nozzle="0"`/`"1"` для подвійного сопла H2D) |
| `bamdude_nozzle_target_celsius` | gauge | Цільова температура сопла |
| `bamdude_chamber_temp_celsius` | gauge | Температура камери (надається лише для моделей із сенсором) |
| `bamdude_fan_speed_percent` | gauge | Швидкість вентилятора (лейбл `fan="part"`/`"aux"`/`"chamber"`) |
| `bamdude_wifi_signal_dbm` | gauge | Рівень сигналу WiFi у dBm |

### Агрегатні (з БД)

| Метрика | Тип | Опис |
|---------|-----|------|
| `bamdude_prints_total` | gauge | Загальна кількість друків за весь час, лейбл `result="completed"`/`"failed"`/тощо |
| `bamdude_printer_prints_total` | gauge | Загальна кількість друків за весь час по кожному принтеру |
| `bamdude_filament_used_grams` | gauge | Загальна витрата філаменту |
| `bamdude_print_time_seconds` | gauge | Загальний задокументований час друку |
| `bamdude_queue_pending` | gauge | Кількість завдань у черзі |
| `bamdude_queue_printing` | gauge | Кількість завдань, які зараз друкуються |
| `bamdude_printers_connected` | gauge | Підключених принтерів зараз |
| `bamdude_printers_total` | gauge | Налаштованих принтерів зараз |

---

## Знімки виробництва та складу

Той самий захищений `/api/v1/metrics` експортує **gauge**, прочитані з наявного обліку Workshop і журналу катушок. Запит нічого не резервує, не приймає випуск, не списує пластик і не виправляє чергу. Окремої бази обліку немає.

| Метрика | Значення та мітки |
|---|---|
| `bamdude_stock_full_spools`, `bamdude_stock_full_grams` | Невикористані вільні котушки, придатні для штатного автовибору зі складу; це не всі котушки на полиці. Грами — вага за етикеткою. |
| `bamdude_inventory_spools{scope}` | Активні/усі записи котушок. |
| `bamdude_inventory_remaining_grams`, `bamdude_inventory_low_stock_spools` | Ті самі оцінки залишку й пороги, що в Inventory. Від'ємний залишок кожної активної котушки обмежено нулем. |
| `bamdude_inventory_overdrawn_spools` | Активні котушки зі списанням понад вагу за етикеткою. Це не доказ фізично порожньої котушки. |
| `bamdude_assigned_spool_balance_grams`, `bamdude_assigned_spool_archived` | За `printer_id`, `ams_id`, `tray_id`: оцінка залишку зі знаком та ознака архівної призначеної котушки. |
| `bamdude_accounted_filament_window_grams{printer_id,kind,window}` | Проведені грами зі знаком за рухомі `24h`, `7d`, `30d`, за **часом запису в журнал**. `kind=print` включає невдалі спроби та старі типи результатів. `service_adjustment` охоплює поправки runout та AMS. Записаний ID може зберігатися після видалення принтера. Для рядків без ID використовується `unassigned`. Оцінки активної нарізки виключено. |
| `bamdude_pending_jobs{tier}` | `auto` — ще не розподілені; `printer` — очікують запуску. Переданий запис AutoQueue вдруге не рахується. |
| `bamdude_printer_maintenance`, `bamdude_printer_queue_paused`, `bamdude_printer_auto_distribute_eligible`, `bamdude_printer_awaiting_plate_clear` | Незалежні записані ознаки за `printer_id`, включно з режимом обслуговування. Не є фізичним підтвердженням. Якщо заголовка черги немає, її ознаки пропущено. |
| `bamdude_printer_telemetry_timestamp_known`, `bamdude_printer_telemetry_age_seconds` | Чи відомий час останнього локально отриманого MQTT-повідомлення та його вік. Невідомий вік пропущено. Нове повідомлення не доводить свіжість кожного поля. |
| `bamdude_running_order_archives{printer_id,order_id,line_id}` | Архіви зі станом друку за справжніми зовнішніми ключами; відсутній зв'язок — `unknown`. Не доказ фізичного друку. |
| `bamdude_active_orders`, `bamdude_order_details_available` | Кількість активних замовлень і доступність усієї деталізації в межах лімітів. |
| `bamdude_order_line_units{order_id,line_id,unit,quantity}` | `ordered`, `ui_printed`, `ui_covered`, `ui_remaining`, `from_finished_stock`, `from_part_kits`, `held`, `issued`. Одиниці — `product_units` або `parts`; різні одиниці не підсумовувати. Покриття UI включає неперевірені результати, резерви та перерахунок. Приймання/склад не є додатковим виробництвом. |
| `bamdude_order_line_jobs{order_id,line_id,stage}` | Штатно віднесені до позиції архіви `running` та завдання `queued` обох черг. |
| `bamdude_order_part_pieces{order_id,line_id,part_id,quantity}` | `ui_usable`, `ui_remaining`, поправка зі знаком `recount_adjustment`, `allocated_stock`, `checked_net`, `unchecked_net`. Останні два — розподіл тих самих штатно зарахованих деталей **до поправок перерахунку**, не складські приймання. Назви файлів не визначають замовлення. |
| `bamdude_order_part_quality_known` | Чи відомий розподіл за перевіркою; невідомі перевірені/неперевірені кількості мають `NaN`, а не нуль. |
| `bamdude_order_quality_coverage_complete`, `bamdude_order_unchecked_archives`, `bamdude_order_unattributed_archives`, `bamdude_order_recorded_defective_pieces` | Повнота історії, неперевірені й нерозподілені архіви, записаний брак деталей включно з невдалими спробами. Якщо у завершених архівів немає рядків деталей, брак — `NaN`. |
| `bamdude_order_can_complete` | Штатна умова завершення Workshop; запит нічого не підтверджує. |
| `bamdude_production_snapshot_timestamp_seconds` | Час збору UTC. Кілька SQL-запитів не є незмінним знімком виробництва. |

Деталізація охоплює **лише активні замовлення**. У мітках немає замовників, назв файлів та ID архівів. Перед завантаженням перевіряються сумарні межі: 50 замовлень, 1 000 позицій, 10 000 живих архівів, 100 000 рядків деталей архівів. При перевищенні `order_details_available=0`, **уся деталізація замовлень пропускається**, а не перетворюється на нулі чи непомітно обрізається. Метрики складу й черг залишаються. ID стосуються поточної БД, не переносяться між відновленнями. Назви й подробиці — у `/projects/{order_id}`.

Усі ці значення — знімки обліку, залишки котушок — оцінки. Поправки, видалення, скидання та старіння вікон можуть їх зменшувати. **Не застосовуйте `rate()` або `increase()`**. Історія Prometheus починається лише після реального опитування; увімкнення endpoint не створює scrape job. Рухомі суми читають збережений журнал, не відновлюють відсутню історію.

```promql
# Списані на друк грами за попередні 24 години, без службових поправок
sum(bamdude_accounted_filament_window_grams{kind="print",window="24h"})
# Вільні повні котушки в кілограмах
bamdude_stock_full_grams / 1000
# Очікують у двох чергах без дублювання
sum(bamdude_pending_jobs)
# Залишок виробів за активними замовленнями, без позицій окремих деталей
sum by (order_id) (bamdude_order_line_units{quantity="ui_remaining",unit="product_units"})
```

---

## :material-tag-multiple: Reference лейблів

Більшість метрик несуть один або кілька лейблів для фільтрації та групування. Повний набір:

| Лейбл | Опис |
|---|---|
| `printer_id` | Числовий ID принтера, призначений при створенні. |
| `printer_name` | Людино-читабельне ім'я принтера з Settings. |
| `serial` | Серійний номер принтера. |
| `model` | Код моделі (`X1C`, `X1E`, `H2D`, `P1S`, `A1`, `A1-Mini`, `P2S`, …). |
| `nozzle` | Індекс сопла — `0` / `1` для H2D dual-nozzle, `0` для single-nozzle моделей. |
| `fan` | Слот вентилятора — `part`, `aux`, `chamber`. |
| `result` | Стан архіву на знімках gauge — `completed`, `failed`, `cancelled`, `archived`. |

---

## :material-prometheus: Конфіг scrape-у Prometheus

Додай BamDude у свій `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'bamdude'
    scrape_interval: 15s
    metrics_path: '/api/v1/metrics'
    static_configs:
      - targets: ['bamdude-host:8000']
    authorization:
      type: Bearer
      credentials_file: '/etc/prometheus/bamdude.token'
```

Запиши в цей файл той самий токен, що й у BamDude, та надай Prometheus доступ до читання.

Коли Prometheus крутиться в сусідньому Docker-контейнері поруч з BamDude — використовуй `host.docker.internal` (Docker Desktop) або ім'я BamDude-контейнера в спільній мережі:

```yaml
static_configs:
  - targets: ['host.docker.internal:8000']
```

```yaml
# На спільній user-defined bridge-мережі:
static_configs:
  - targets: ['bamdude:8000']
```

15-30-секундний scrape interval — більш ніж достатньо для printer telemetry, температури і прогрес не змінюються швидше будь-яким значущим чином.

---

## :material-chart-bar: Запити Grafana (PromQL)

Створюючи панель у Grafana, вибери джерело даних Prometheus, яке опитує BamDude.

**Температури принтера** — конкретний принтер або всі одразу:

```promql
bamdude_nozzle_temp_celsius{printer_name="X1C-1", nozzle="0"}
bamdude_bed_temp_celsius{printer_name="X1C-1"}
```

**Live прогрес друку** по парку:

```promql
bamdude_print_progress
```

**Списані на друк грами за попередню добу** (рухомий gauge, не rate):

```promql
sum(bamdude_accounted_filament_window_grams{kind="print",window="24h"})
```

**Очікують в обох чергах**:

```promql
sum(bamdude_pending_jobs)
```

### Sample dashboard panels

Стартовий дашборд:

| Панель | Тип | Запит |
|---|---|---|
| Printers online | Stat | `bamdude_printers_connected` |
| Print progress per printer | Gauge | `bamdude_print_progress` |
| Bed / nozzle / chamber temperatures | Time series | `bamdude_bed_temp_celsius`, `bamdude_nozzle_temp_celsius`, `bamdude_chamber_temp_celsius` |
| Booked print grams (24h) | Time series | `sum(bamdude_accounted_filament_window_grams{kind="print",window="24h"})` |
| Queue depth | Bar chart | `sum(bamdude_pending_jobs)` |
| Prints by result | Bar chart | `bamdude_prints_total` |
| WiFi signal | Time series | `bamdude_wifi_signal_dbm` |

---

## :material-file-document: Sample `/metrics` output

```
# HELP bamdude_build_info BamDude build information
# TYPE bamdude_build_info gauge
bamdude_build_info{version="0.4.2",python_version="3.11.7",platform="Linux",architecture="x86_64"} 1

# HELP bamdude_printer_connected Printer connection status (1=connected, 0=disconnected)
# TYPE bamdude_printer_connected gauge
bamdude_printer_connected{printer_id="1",printer_name="X1C-1",serial="00M09C411500579",model="X1C"} 1

# HELP bamdude_printer_state Printer state
# TYPE bamdude_printer_state gauge
bamdude_printer_state{printer_id="1",printer_name="X1C-1",serial="00M09C411500579"} 2

# HELP bamdude_bed_temp_celsius Current bed temperature
# TYPE bamdude_bed_temp_celsius gauge
bamdude_bed_temp_celsius{printer_id="1",printer_name="X1C-1",serial="00M09C411500579"} 60.0

# HELP bamdude_nozzle_temp_celsius Current nozzle temperature
# TYPE bamdude_nozzle_temp_celsius gauge
bamdude_nozzle_temp_celsius{printer_id="1",printer_name="X1C-1",serial="00M09C411500579",nozzle="0"} 220.0

# HELP bamdude_prints_total Total number of prints by result
# TYPE bamdude_prints_total gauge
bamdude_prints_total{result="completed"} 342
bamdude_prints_total{result="failed"} 18

# HELP bamdude_filament_used_grams Total filament used in grams
# TYPE bamdude_filament_used_grams gauge
bamdude_filament_used_grams 2042.0

# HELP bamdude_accounted_filament_window_grams Signed booked spool-ledger grams by settlement time in a rolling window; gauge, do not rate or increase
# TYPE bamdude_accounted_filament_window_grams gauge
bamdude_accounted_filament_window_grams{printer_id="1",kind="print",window="24h"} 175.0
bamdude_accounted_filament_window_grams{printer_id="1",kind="service_adjustment",window="24h"} -15.0

# HELP bamdude_printers_connected Number of connected printers
# TYPE bamdude_printers_connected gauge
bamdude_printers_connected 2
```

---

## :material-help-circle: Усунення несправностей

### `/metrics` повертає 404

Метрики Prometheus вимкнені. Увімкни в **Налаштування → Мережа → Метрики Prometheus** і повтори.

### `/metrics` повертає 401

Bearer-token виставлений, але запит його не приніс (або приніс не той). Підтверди, що `Authorization: Bearer <token>` точно збігається з токеном у Settings — copy/paste-помилки типова причина.

### `/metrics` повертає 503, якщо токен порожній

Збережи токен Prometheus у BamDude та вкажи його в конфігурації опитування.

### Немає виробничої деталізації

Перевірте `bamdude_order_details_available` та ознаки повноти QC. Невідомі або пропущені через ліміт дані не є нульовим виробництвом. Агрегати складу/черги не потребують MQTT-повідомлення; телеметрія потребує локального спостереження. Помилка HTTP-збору не є порожньою фермою.
