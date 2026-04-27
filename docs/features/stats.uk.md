---
title: Статистика і енергія
description: Сумарна стата друку, облік енергії на друк з розетки та фермові підсумки за період
---

# Статистика і енергія

Сторінка Stats — це BamDude'ів дашборд для "що ферма реально зробила?": кількість друків, спожитий пластик, енергія, час. Усе з `print_archives` (окремої stats-таблиці, що могла б дрейфувати, нема), тож числа завжди відповідають списку архівів під тим самим фільтром.

## :material-chart-bar: Top-level KPI

Хедер показує чотири lifetime-лічильники:

| Метрика | Джерело |
|---|---|
| **Завершені друки** | Рядки `print_archives` зі `status='completed'`. |
| **Витрачено пластика** | Сума `filament_used_grams` по завершених архівах, групована за матеріалом/кольором. |
| **Час друку** | Сума `print_time_seconds`. |
| **Спожита енергія** | Сума `energy_kwh` (per-print delta, обчислена диспатчером на завершенні) по завершених архівах, де на старті була прив'язана розумна розетка. Падає на ranged-sum з `smart_plug_energy_snapshots`, коли individual-print captures відсутні. |

Кожна KPI також показує відповідну ціну, коли `default_filament_cost` і `energy_cost_per_kwh` сконфігуровані під Settings → System.

## :material-calendar-range: Фільтр діапазону

Range-picker над KPI scope-ить усе нижче — last 7 days / last 30 / last quarter / custom range. KPI стають тими самими метриками за обраний період; per-printer breakdown перерендерюється.

## :material-chart-line: Time-series графіки

Нижче KPI — два stacked line-графіки:

- **Друки на день** — bar chart завершених архівів, бакетовані за датою, colour-coded за принтером.
- **Пластик на день** — те саме бакетування, stacked за матеріалом, тож видно "ми перейшли з PLA-важкого на PETG-важкий у березні".

Hover на бар показує breakdown за той день.

## :material-printer-3d-nozzle: Per-printer breakdown

Таблиця внизу складає внесок кожного принтера: друки, пластик, час, енергія, ціна. Клік на рядку дрилить у список архівів, попередньо відфільтрований на цей принтер.

## :material-flash: Per-print облік енергії

Облік енергії — opt-in. Щоб захопити її на кожному друку:

1. Додай розумну розетку під **Settings → Smart Plugs** (Tasmota, Home Assistant, REST/webhook або MQTT — див. [Розумні розетки](smart-plugs.uk.md)).
2. Прив'яжи розетку до конкретного принтера.
3. Розетка має репортити сумарні kWh — Tasmota field `Total`, HA `sensor.<plug>_energy_total` тощо.

На кожному друку:

- На `print_start` BamDude читає поточні kWh розетки в `print_archives.energy_start_kwh`.
- На `print_complete` BamDude читає розетку ще раз, обчислює `current - energy_start_kwh` і зберігає **саму дельту** в `print_archives.energy_kwh`. Окремої колонки `energy_end_kwh` немає — end-readout існує лише на час віднімання й одразу відкидається.
- Зчитування restart-resilient — значення приходять з fresh DB-session щоразу, ніколи з in-memory dict, тож backend-restart між start і complete не ламає capture.

Якщо розетка не прив'язана або offline на одній з двох меж — `energy_kwh` лишається null, і той друк виключається з energy-KPI.

### Hourly snapshot fallback

Per-print capture покладається, що розетка відгукнеться в саме ті два моменти. Щоб згладити її outage-и, BamDude також робить **hourly snapshot** сумарних kWh кожної розетки у `smart_plug_energy_snapshots`. Для запитів "total energy" за період stats-сторінка падає на цю таблицю, коли individual-print поля відсутні — `_sum_snapshot_deltas()` обчислює per-plug `max(0, last_in_range - baseline)` і сумує.

Snapshot-таблиця обмежена — старі рядки prune-ються після налаштовного retention-вікна, щоб не росла вічно.

## :material-bullseye-arrow: Розрахунки ціни

| Ціна | Формула |
|---|---|
| **Ціна пластика на друк** | `filament_used_grams × (spool.cost / spool.weight)`. Падає на `default_filament_cost / 1000` за грам, якщо котушка не призначена. |
| **Ціна енергії на друк** | `energy_kwh × energy_cost_per_kwh`. Нуль, коли capture не було (`energy_kwh IS NULL`). |
| **Total** | Пластик + енергія. |

Це живить per-archive-ціна в архівній картці і totals на проєктах / print-plan.

## :material-database-export: Експорт

Хедер має кнопку "Export CSV", що скидає поточну вибірку (відфільтрований період) як CSV з одним рядком на архів — корисно для виставлення рахунків print-as-a-service або годування іншого інструменту.

Сторінка Maintenance має схожий Excel-експорт для service-інтервалів — див. [Maintenance](maintenance.uk.md).
