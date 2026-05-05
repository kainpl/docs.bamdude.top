---
title: Експорт
description: Bulk-експорт метаданих архіву та статистики у CSV / Excel
---

# Експорт (Export)

Витягуйте історію архіву та статистику з BamDude як CSV або XLSX для Excel pivot, BI-tools, customer billing або tax reporting. Експорт враховує фільтри — що ви бачите в UI, те і отримуєте у файлі.

---

## :material-information: Що це

Два endpoint'и, обидва на `ExportService` (`backend/app/services/export.py`):

| Endpoint | Що повертає |
|----------|-------------|
| `GET /api/v1/archives/export` | Один рядок на архів (the print log) |
| `GET /api/v1/archives/stats/export` | Failure-analysis summary + кореляційні breakdown'и + weekly trend |

Обидва видають CSV за замовчуванням і приймають `?format=xlsx` для native Excel `.xlsx`.

!!! info "Дозволи"
    - **Archive export** потребує `archives:read`
    - **Stats export** потребує `stats:read`

    Operators і Administrators мають обидва за замовчуванням; Viewers — read-only до обох.

---

## :material-filter: Filter-Aware Export

Які чіпи ви виставили на сторінці Archives — ті і йдуть у запит експорту. Ті ж самі фільтри, що й UI: `printer_id`, `project_id`, `status`, `date_from`, `date_to`, `search` — застосовуються серверно перед генерацією експорту.

| Фільтр | Ефект на експорт |
|--------|------------------|
| Printer | Лише архіви цього принтера |
| Project | Лише цей проєкт |
| Status | Лише цей статус (наприклад, `success`, `failed`) |
| Date range | Включно `date_from` … `date_to` (ISO 8601) |
| Search | Match по `print_name`, `filename`, `tags`, `notes`, `designer` |

Два виключення завжди увімкнено: `status='archived'` (uploaded but never printed) і trashed архіви (`deleted_at IS NOT NULL`). Це тримає експорт чисельно консистентним з тим, що показує дашборд [Statistics](statistics.md).

---

## :material-file-delimited: Формат CSV

- **Encoding:** UTF-8
- **Separator:** кома (`,`)
- **Quoting:** дефолти Python `csv.writer` — значення з комами, лапками або newlines double-quoted з `"`
- **Line ending:** платформний default (`\r\n` на Windows, `\n` інакше)

!!! warning "Excel + CSV double-click"
    Excel іноді неправильно детектить UTF-8 CSV на double-click. Якщо бачите kраказябри — імпортуйте через **Data → From Text/CSV** і явно виберіть UTF-8.

---

## :material-microsoft-excel: Формат Excel (.xlsx)

Коли ви вибираєте `format=xlsx`, BamDude генерує styled workbook через `openpyxl`:

| Feature | Деталі |
|---------|--------|
| Header row | Жирний білий текст, синій (`#4472C4`) fill, центровано |
| Frozen header | Рядок 1 пінниться при scroll |
| Auto-width columns | Ширина колонки = max content length (cap 50 chars) |
| Sheet name | `Archives` для archive export, `Statistics` для stats export |

Stats workbook — це single sheet з парами Metric / Value та weekly-trend блоком знизу.

---

## :material-format-list-checkbox: Колонки архіву

Це default-поля для кожного рядка архіву. Звузити можна через query-параметр `fields` (`fields=id,print_name,energy_kwh,cost`).

| Поле | Header | Опис |
|------|--------|------|
| `id` | ID | Primary key архіву |
| `print_name` | Print Name | Display-ім'я (fallback на filename) |
| `filename` | Filename | Оригінальне ім'я 3MF |
| `status` | Status | `success` / `failed` / `aborted` / `cancelled` |
| `quantity` | Items Printed | Скільки копій на plate |
| `printer_id` | Printer ID | FK до `printers.id` |
| `project_name` | Project | Joined з `projects.name` |
| `filament_type` | Filament Type | PLA, PETG, ABS, … |
| `filament_used_grams` | Filament (g) | Грами spent (sum по spool'ах) |
| `print_time_seconds` | Print Time (s) | Wall-clock тривалість |
| `layer_height` | Layer Height (mm) | Slicer setting |
| `nozzle_diameter` | Nozzle (mm) | Hardware setting |
| `bed_temperature` | Bed Temp (°C) | Slicer setting |
| `nozzle_temperature` | Nozzle Temp (°C) | Slicer setting |
| `total_layers` | Total Layers | Slicer metadata |
| `cost` | Cost | Filament + energy combined |
| `designer` | Designer | З 3MF metadata або manual edit |
| `tags` | Tags | Comma-separated теги |
| `notes` | Notes | Free-text нотатки |
| `failure_reason` | Failure Reason | Set на `failed` / `aborted` архівах |
| `started_at` | Started At | ISO 8601 UTC |
| `completed_at` | Completed At | ISO 8601 UTC |
| `created_at` | Created At | ISO 8601 UTC |

!!! info "Energy-колонки"
    `energy_kwh` і `energy_cost` не входять у default `fields` — передайте їх явно через `?fields=...`, якщо потрібні у тому ж експорті. Заповнюються лише для архівів, чий принтер має [smart plug](smart-plugs.md) з kWh metering.

---

## :material-chart-bar: Layout Stats-експорту

`GET /api/v1/archives/stats/export?days=30` дає:

```
Metric                 | Value
Period (days)          | 30
Total Prints           | 412
Failed Prints          | 27
Failure Rate (%)       | 6.6

Failures by Reason
Adhesion failure       | 8
Layer shift            | 5
…

Failures by Filament
ABS                    | 11
PETG                   | 9
…

Failures by Printer
Garage A1              | 18
Office P1S             | 7
…

Weekly Trend
Week        | Total | Failed | Rate (%)
2026-04-06  | 92    | 5      | 5.4
2026-04-13  | 89    | 8      | 9.0
…
```

Ті самі дані живлять дашборд [Failure Analysis](failure-analysis.md).

---

## :material-api: API Reference

### Archive export

```
GET /api/v1/archives/export
```

| Query param | Type | Default | Нотатки |
|-------------|------|---------|---------|
| `format` | `csv` \| `xlsx` | `csv` | |
| `fields` | comma-list | усі defaults | Напр., `id,print_name,energy_kwh` |
| `printer_id` | int | — | Фільтр по принтеру |
| `project_id` | int | — | Фільтр по проєкту |
| `status` | string | — | Exact match |
| `date_from` | ISO datetime | — | Включно |
| `date_to` | ISO datetime | — | Включно |
| `search` | string | — | LIKE по name / filename / tags / notes / designer |

Auth: дозвіл `archives:read`. Шліть JWT у `Authorization: Bearer …` або API key у `X-API-Key`.

### Stats export

```
GET /api/v1/archives/stats/export
```

| Query param | Type | Default | Нотатки |
|-------------|------|---------|---------|
| `format` | `csv` \| `xlsx` | `csv` | |
| `days` | int | `30` | Lookback вікно у днях |
| `printer_id` | int | — | Фільтр по принтеру |
| `project_id` | int | — | Фільтр по проєкту |

Auth: дозвіл `stats:read`.

### Приклад

```bash
# Failed-друки за останній квартал, як Excel
curl -H "X-API-Key: bb_..." \
  "https://bamdude.local/api/v1/archives/export?format=xlsx&status=failed&date_from=2026-02-01&date_to=2026-04-30" \
  -o failed_q1.xlsx
```

---

## :material-clock-time-eight: Recurring / Scheduled Exports

BamDude не має внутрішнього cron'у для експортів — тримайте API-key flow простим і використовуйте scheduler, який вже є у вашому оточенні:

=== "Linux / cron"

    ```bash
    # Weekly snapshot щонеділі 00:00
    0 0 * * 0 curl -H "X-API-Key: $BAMDUDE_KEY" \
      "http://localhost:8000/api/v1/archives/export?format=csv" \
      -o "/backup/archives_$(date +\%Y\%m\%d).csv"
    ```

=== "systemd timer"

    Зкомбінуйте `OnCalendar=Sun *-*-* 00:00:00` timer з service-unit, що крутить той самий `curl`.

=== "Home Assistant"

    Пара `rest_command:` + `automation:`. HA може кинути файл у samba-share або прикріпити до email-notification service.

=== "GitHub Actions / GitLab CI"

    Заплануйте workflow / pipeline, який б'є по export endpoint і викладає артефакт. Зберігайте `BAMDUDE_KEY` як CI secret.

---

## :material-script-text-outline: Use Cases

- **Customer billing** — фільтр по даті + проєкту, експорт, віддавайте в invoicing tool. Filament weight + cost + energy = захищаємий per-job total.
- **Tax / accounting** — quarterly експорт по date range; колонка `cost` уже сумує filament + energy.
- **QA log** — `status=failed` + `date_from=YYYY-MM-01` — це failure log, який ви віддаєте вендору при warranty claim.
- **Capacity planning** — пів року `print_time_seconds` per printer показують, який принтер — bottleneck.

---

## :material-link: Дивіться також

- [Statistics](statistics.md) — візуальна аналітика тих же даних
- [Failure Analysis](failure-analysis.md) — джерело stats-export чисел
- [Archiving](archiving.md) — фільтр-чіпи переюзані для export scope; underlying таблиця `print_archives`
- [Energy Tracking](energy.md) — колонки `energy_kwh` / `energy_cost`
- [Authentication → API Keys](authentication.md) — bearer / `X-API-Key` заголовки для scripted експортів

---

## :material-lightbulb: Поради

!!! tip "Спочатку фільтр, потім експорт"
    Експорт враховує поточні чіпи. Виставити їх у UI швидше, ніж збирати query-string руками.

!!! tip "Закладіть pattern імені файлу"
    Включайте дату у saved filename (`archives_20260504.csv`), щоб можна було diff'ити month-over-month і ловити регресії.

!!! tip "XLSX для stakeholders, CSV для pipelines"
    XLSX має жирний header / frozen pane / autosize, що очікують люди; CSV — це формат, який ваші скрипти та pandas pipelines реально хочуть.

!!! tip "API key, не персональний JWT, для cron"
    JWT exp'ить через годину. [API key](authentication.md) — ні; саме це і треба для unattended scheduled export.
