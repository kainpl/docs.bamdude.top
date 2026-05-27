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
| **Витрачено пластика** | Сума `filament_used_grams` по всіх архівах діапазону (не лише завершених), групована за матеріалом/кольором. Невдалі / скасовані друки рахуються за **фактично** витраченим пластиком, а не повною оцінкою слайсера, тож сума збігається з тим, що було відняте з інвенторі. |
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
| **Ціна пластика на друк** | Сума частки кожної призначеної котушки (`grams_from_spool × spool.cost / spool.weight`). Грами, **не** покриті призначеною котушкою, добиваються за `default_filament_cost / 1000` за грам. Тож багатоколірний друк, де лише частина слотів AMS прив'язана до інвентаря, відображає весь друк, а не лише відстежувані слоти; повністю невідстежуваний друк падає цілком на дефолтну ставку. |
| **Ціна енергії на друк** | `energy_kwh × energy_cost_per_kwh`. Нуль, коли capture не було (`energy_kwh IS NULL`). |
| **Total** | Пластик + енергія. |

Це живить per-archive-ціна в архівній картці і totals на проєктах / print-plan.

## :material-database-export: Експорт

Хедер має кнопку "Export CSV", що скидає поточну вибірку (відфільтрований період) як CSV з одним рядком на архів — корисно для виставлення рахунків print-as-a-service або годування іншого інструменту.

Сторінка Maintenance має схожий Excel-експорт для service-інтервалів — див. [Maintenance](maintenance.uk.md).

### Опції експорту

| Формат | Для чого | Зміст |
|---|---|---|
| **CSV** | Spreadsheet-и, ad-hoc-аналіз, скрипти | Один рядок на архів: принтер, файл, статус, start time, тривалість, грами філаменту, filament details, kWh, ціни |
| **Excel** | Звіти з форматуванням, шерення з нетехнічними стейкхолдерами | Ті самі колонки, що CSV, плюс форматування, заморожений header, типи на колонку |

Обидва експорти поважають **поточно активні фільтри** — діапазон, чіпи printer-selection, per-user-фільтр. Скинь фільтри спочатку, щоб експортувати повний dataset.

---

## :material-view-dashboard: Widget-based дашборд

Сторінка Stats — це конфігурована сітка віджетів, не фіксований звіт. Можна:

- **Перетягувати** будь-який віджет за хедер, щоб переставити
- **Ресайзити** через corner handle — цикл Small → Medium → Large → Full Width
- **Ховати** непотрібні віджети іконкою ока — повертати з меню **Hidden** у хедері дашборда
- **Reset to default** — кнопка в хедері повертає дефолтний layout

Layout **персистнутий per-user** на бекенді, тож той самий логін на іншому пристрої бачить ту ж розкладку.

### Доступні віджети

| Віджет | Що показує |
|---|---|
| **Print Success Rate** | Pie-chart — completed / failed / stopped split. Per-printer filterable. |
| **Filament by Type** | Pie-chart розподілу матеріалів (PLA / PETG / ABS / ...). Клік по сегментах — фільтрує. |
| **Print Activity Calendar** | GitHub-style heatmap, кількість друків на день, клік по дню — drill в архіви того дня. |
| **Print Duration Distribution** | Бакетна bar-діаграма: `<30m`, `30m–1h`, `1–2h`, `2–4h`, `4–8h`, `8–12h`, `12–24h`, `24h+`. Показує твою типову довжину друку. |
| **Time Accuracy** | Predicted-vs-actual часи друку. Per-printer середні і trend — відповідь на "чи дрейфує калібровка?" |
| **Printer Utilization** | Години активного друку на принтер; % idle-часу. |
| **Recent Activity** | Стрічка останніх 10 завершених друків; клік відкриває архівну картку. |
| **Quick Stats** | KPI-плитки (друки, філамент, час, ціна, енергія) для активного діапазону. |

### Printer Selection

Multi-select-чіпи над віджетами scope-ять **увесь дашборд** на підмножину принтерів:

- Клік по чіпу — toggle цього принтера on/off
- Усі віджети одразу перерендерюються проти відфільтрованого набору
- Кнопка експорту поважає той самий фільтр

Корисно для "покажи мені тільки ряд A1 у моєму MakerSpace" або "порівняй X1C-A vs X1C-B side-by-side".

### Per-User фільтрація

Коли в тебе є право `stats:filter_by_user` (за замовчуванням лише в Administrators), у хедері stats з'являється **dropdown користувача** поряд з timeframe-селектором. Вибір юзера фільтрує кожен віджет, failure-analysis і CSV/Excel-експорти на друки цього користувача — корисно для університетів, makerspace-ів чи будь-якого середовища, де треба per-person accountability чи cost-tracking.

| Значення фільтра | Ефект |
|---|---|
| **All Users** | Default — глобальна статистика |
| `<конкретний юзер>` | Тільки його друки |
| **No User (System)** | Друки без user-атрибуції (slicer-initiated, pre-auth, virtual-printer uploads) |

!!! info "Видача права"
    Щоб дати dropdown не-адмінам, створи custom-групу в **Settings → Users** і додай `stats:filter_by_user`. Див. [Authentication](authentication.uk.md).

### Energy "warming-up" indicator

У режимі **Total Consumption** date-range-енергія обчислюється з hourly-snapshot-ів lifetime-лічильника кожної розетки (див. [Smart Plugs](smart-plugs.uk.md)). На свіжому інсталі — або одразу після upgrade — першого snapshot-а до твого діапазону може ще не існувати. Плитки Energy Used / Energy Cost показують маленьку жовту warning-іконку з tooltip-ом, що пояснює ситуацію.

Через ~1 годину runtime-у іконка зникає для будь-якого діапазону, що починається після першого snapshot-а. KPI-значення в межах warming-up-вікна обчислюється проти `0` baseline-а, що завищує на стільки, скільки розетка показувала на момент інсталу — почекай ту годину, перш ніж читати число.

---

## :material-cash: Налаштування ціни

Cost-плитки показують числа лише, коли вхідні дані сконфігуровані.

1. **Settings → System** — постав **Currency** (`USD`, `EUR`, `UAH` тощо) і **`energy_cost_per_kwh`**
2. **Settings → Filaments / Spoolman** — постав per-spool `cost` + `weight` (або глобальний `default_filament_cost` на кг)
3. Stats підхопить ставки одразу; нові друки зберігають їх на архіві в момент завершення

### Recalculate Costs

Існуючі архіви тримають ціни, активні на момент їхнього завершення — історичні дані автоматично не переписуються, коли ставки змінилися. Щоб привести все до поточних цін:

1. Натисни **Recalculate Costs** у хедері дашборда
2. У кожному архіві перераховуються філамент + енергія проти поточних spool / config-ставок
3. Дашборд перерендерюється проти нових totals

!!! info "Поведінка ціни на reprint"
    Reprint-и — **additive**: ціна reprint-а додається до total оригінального архіву, а не перезаписує його, тож per-archive total відображає cumulative-витрати по всіх runs цього файла. Це значить, що числа stats трекають реально витрачені гроші, а не "скільки оригінал коштував би сьогодні".

---

## :material-refresh: Auto-refresh

Сторінка Stats полить кожні **60 с**, тож дашборди, залишені відкритими під час print-сесії, лишаються свіжими без manual reload. Іконка refresh у хедері форсить негайний refetch — корисно одразу після того, як довгий друк завершився, якщо не хочеш чекати наступний tick.

Mutation-и з інших частин додатку (видалення архіву, recalculate costs, редагування ціни філаменту) автоматично інвалідують underlying queries — клікати refresh після них не треба.
