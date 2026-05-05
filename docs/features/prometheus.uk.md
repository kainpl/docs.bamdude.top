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
| **Bearer Token** | `prometheus_token` | Необов'язкова Bearer-token автентифікація на `/metrics` | Порожній (відкрито) |

!!! info "Автентифікація на /metrics"
    `/api/v1/metrics` ігнорує звичайний стек автентифікації BamDude — він має власний шлюз. Коли `prometheus_enabled=false`, він повертає 404 (виглядає як неналаштований). Коли увімкнено без `prometheus_token`, він відкритий. Коли увімкнено з токеном, виклики мають надсилати `Authorization: Bearer <token>`. Встановлюйте токен щоразу, коли Prometheus працює на окремому хості, якому ви повністю не довіряєте.

!!! warning "Відкрито за замовчуванням коли токен не виставлено"
    З `prometheus_enabled=true` і `prometheus_token=""` ендпоінт **публічно доступний** — будь-хто в мережі, хто дотягнеться до порту 8000, отримає повний дамп метрик (імена принтерів, серійники, queue depth, total filament burn). Для будь-якого деплою, що не є повністю ізольованим home LAN, виставте `prometheus_token` і налаштуйте Prometheus його надсилати.

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

Кожна метрика на рівні принтера має лейбли `printer_id`, `printer_name` та `serial`. Агрегатні counters/gauges не мають лейблів або мають лейбли `result` / `fan` / `nozzle` залежно від ситуації.

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
| `bamdude_prints_total` | counter | Загальна кількість друків за весь час, лейбл `result="completed"`/`"failed"`/тощо |
| `bamdude_printer_prints_total` | counter | Загальна кількість друків за весь час по кожному принтеру |
| `bamdude_filament_used_grams` | counter | Загальна витрата філаменту |
| `bamdude_print_time_seconds` | counter | Загальний задокументований час друку |
| `bamdude_queue_pending` | gauge | Кількість завдань у черзі |
| `bamdude_queue_printing` | gauge | Кількість завдань, які зараз друкуються |
| `bamdude_printers_connected` | gauge | Підключених принтерів зараз |
| `bamdude_printers_total` | gauge | Налаштованих принтерів зараз |

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
| `result` | Результат друку на агрегатних counter-ах — `completed`, `failed`, `cancelled`, `archived`. |

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
    # Якщо використовуєш bearer-token:
    bearer_token: 'YOUR_TOKEN'
```

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

Додай BamDude як Prometheus data source у Grafana, далі будуй панелі цими запитами:

**Температури принтера** — конкретний принтер або всі одразу:

```promql
bamdude_nozzle_temp_celsius{printer_name="X1C-1", nozzle="0"}
bamdude_bed_temp_celsius{printer_name="X1C-1"}
```

**Live прогрес друку** по парку:

```promql
bamdude_print_progress
```

**Success rate за останній день** (rate-of-change completed vs all-results counter-ів):

```promql
rate(bamdude_prints_total{result="completed"}[1d])
/
rate(bamdude_prints_total[1d])
```

**Швидкість витрати філаменту** (грам/год, остання година ковзним):

```promql
rate(bamdude_filament_used_grams[1h]) * 3600
```

**Глибина черги** одним поглядом:

```promql
bamdude_queue_pending + bamdude_queue_printing
```

### Sample dashboard panels

Стартовий дашборд:

| Панель | Тип | Запит |
|---|---|---|
| Printers online | Stat | `bamdude_printers_connected` |
| Print progress per printer | Gauge | `bamdude_print_progress` |
| Bed / nozzle / chamber temperatures | Time series | `bamdude_bed_temp_celsius`, `bamdude_nozzle_temp_celsius`, `bamdude_chamber_temp_celsius` |
| Success rate (24 год) | Stat | (success-rate запит вище) |
| Filament burn rate | Time series | `rate(bamdude_filament_used_grams[1h]) * 3600` |
| Queue depth | Bar chart | `bamdude_queue_pending` + `bamdude_queue_printing` |
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
# TYPE bamdude_prints_total counter
bamdude_prints_total{result="completed"} 342
bamdude_prints_total{result="failed"} 18

# HELP bamdude_filament_used_grams Total filament used in grams
# TYPE bamdude_filament_used_grams counter
bamdude_filament_used_grams 2042.0

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

### Endpoint відкритий і повертає 200, але метрик немає

Якщо body порожнє або містить лише `bamdude_build_info` — BamDude поки що нічого не зібрав. Більшість метрик заповнюються ліниво — з'являються після першого `push_status` від принтера (або після першого завершеного друку, для агрегатних counter-ів). Зачекай хвилину або клік **Connect** на принтері, щоб форсонути status push.

### Prometheus dashboard каже BamDude "down"

- Перевір network reachability — `curl http://bamdude-host:8000/api/v1/metrics` зсередини самого Prometheus-контейнера.
- Фаєрвол може блокувати порт 8000 між контейнерами / хостами.
- Bearer-token mismatch показується як `down` з 401 на сторінці targets у Prometheus.
- Якщо юзаєш `host.docker.internal` — підтверди, що Docker Desktop / Docker Engine реально експонує цей hostname на твоїй платформі.

---

## :material-lightbulb: Поради

!!! tip "Інтервал scrape"
    Інтервал scrape 15-30 секунд достатній для телеметрії принтерів.

> Початково базується на документації [Bambuddy](https://github.com/maziggy/bambuddy).
