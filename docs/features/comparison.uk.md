---
title: Порівняння архівів
description: Side-by-side порівняння 2–5 архівів — slicer-налаштування, outcome, плюс автоаналіз кореляції success/failure, що підсвічує, які налаштування йшли з успіхом чи з failure
---

# Порівняння архівів

Archive Comparison бере 2–5 архівів і викладає їх у вигляді side-by-side таблиці — кожне порівнюване поле — рядок, кожен архів — колонка, відмінності підсвічуються, плюс автоаналіз того, які налаштування корелюють з success vs failure, коли в підбірці є обидва outcome.

## :material-compare: Що це

Відкрий модалку з двома або більше вибраними архівами; BamDude робить запит до `GET /api/v1/archives/compare?archive_ids=...` і рендерить результат. Корисно для:

- **A/B тестування profile-зміни** — та сама модель надрукована двічі, layer height підняли з 0.20 mm до 0.16 mm, дивишся що ще змінилось разом.
- **Regression-аналіз після firmware-оновлення** — вирівняй останні успішні друки до апдейту проти failure-ів після.
- **Ітерацій по калібрувальному друку** — calibration cube, temperature tower, retraction tower через декілька спроб.
- **Розслідування конкретного failure** — обери один поганий друк і три хороших з тією самою моделлю; success-correlation блок скаже, які numeric-налаштування різнилися.

## :material-cursor-default-click: Відкривання модалки

1. Перейди в **Archives**.
2. Multi-select 2–5 рядків (Ctrl/Cmd-click або Shift-click).
3. Клікни **Compare** в тулбарі.

Модалка закривається на **Esc** або клік по затемненому фону.

!!! tip "Ліміти enforce-ляться server-side"
    Менше 2 архівів → `400 At least 2 archives required for comparison`. Більше 5 → `400 Maximum 5 archives can be compared at once`. Frontend disable-ить кнопку Compare поза цим діапазоном.

## :material-table: Що порівнюється

Бекенд (`backend/app/services/archive_comparison.py`) порівнює фіксований список полів:

| Поле | Label | Одиниця |
|---|---|---|
| `layer_height` | Layer Height | mm |
| `nozzle_diameter` | Nozzle Diameter | mm |
| `bed_temperature` | Bed Temperature | °C |
| `nozzle_temperature` | Nozzle Temperature | °C |
| `filament_type` | Filament Type | — |
| `filament_used_grams` | Filament Used | g |
| `print_time_seconds` | Print Time | (рендериться як `Nh Mm`) |
| `total_layers` | Total Layers | — |
| `status` | Status | — |

Усі ці значення BamDude витягає з 3MF-метадати під час архівування друку. Кожен архів запитується за ID і впорядковується так само, як ти передав ID-и.

!!! note "Чого НЕМА у порівнянні"
    Деякі налаштування, які rekламувала upstream Bambuddy wiki (infill density/pattern, print speed, chamber temp, retract distance, K factor, filament color, plate count, parts count, file size/hash, predicted vs actual duration, energy consumed, error codes), у compare-response BamDude **немає** — тільки дев'ять полів вище. Якщо треба ширше порівняння — відкрий індивідуальні архіви у side-by-side вкладках браузера, або запитай slicer-settings JSON через `GET /api/v1/archives/{id}` напряму.

## :material-alert-circle-outline: Підсвічення відмінностей

Кожен рядок response має флаг `has_difference`. Frontend рендерить рядки з відмінностями з жовтим відтінком і маленькою warning-іконкою. Summary-блок під таблицею перелічує до 5 different-полів явно:

> **Layer Height:** 0.16 vs 0.20 vs 0.20 mm
> **Filament Used:** 42 vs 48 vs 45 g
> ...and 2 more

`null` значення рендеряться як `–` і не рахуються як difference (флагуються тільки поля, де хоча б два архіви мають non-null значення, що не збігаються).

## :material-chart-bell-curve: Success/failure кореляція

Коли підбірка містить **обидва** completed і failed архіви, BamDude запускає невелику евристику зверху per-field-порівняння:

- Для numeric-полів (`layer_height`, температури, filament used, print time, total layers): усереднює значення серед успішних і серед failure-ів окремо. Якщо відносна різниця перевищує 10%, видає insight типу *"Successful prints had higher Bed Temperature"*.
- Для категоріальних полів (`filament_type`): якщо набір значень в успішних відрізняється від набору в failure-ах, видає *"Different Filament Type used in successful vs failed prints"*.

Блок також показує success/failure count з підбірки (напр. *3 successful, 2 failed*).

Якщо підбірка має тільки один outcome, блок замінюється на підказку:

> Need both successful and failed prints for correlation analysis.

!!! warning "Евристика, не статистика"
    10%-ний поріг — rule-of-thumb, не статистичний тест. На 5 архівах вибірка надто мала для інференц-висновків — трактуй insights як гіпотези ("layer height виглядає корельованим, дай зроблю ще друків і перевірю"), не proof.

## :material-link-variant: Пов'язані фічі

- **Chain-of-custody** — коли архіви відрізняються тільки тому, що BamDude пропатчив gcode (напр. mesh-mode toggle), вони ділять той самий `source_content_hash` і duplicate-бейдж теги́ть їх як споріднені. Див. [Archiving](archiving.uk.md).
- **Aggregate-тренди** — для "середніх значень крізь сотні архівів" а не 2–5, використовуй [Stats](stats.uk.md).
- **Find similar archives** — `GET /api/v1/archives/{id}/similar` повертає до 10 архівів, що матчать за print name, file hash chain або filament type. Використовуй це, щоб наповнити compare-модалку релевантними siblings.

## :material-shield-key: Permission-и

| Permission | Дефолтні групи |
|---|---|
| `archives:read` | Administrators, Operators, Viewers |

Compare endpoint — read-only; будь-хто, хто може читати архіви, може їх порівнювати.

## :material-api: API reference

```
GET /api/v1/archives/compare?archive_ids=12,17,23
```

| Query param | Замітки |
|---|---|
| `archive_ids` | Comma-separated list з 2–5 archive ID. Порядок зберігається у response. |

Response:

```json
{
  "archives": [
    {"id": 12, "print_name": "Benchy v1", "status": "completed", ...},
    ...
  ],
  "comparison": [
    {"field": "layer_height", "label": "Layer Height", "unit": "mm",
     "values": [0.20, 0.16, 0.20], "has_difference": true},
    ...
  ],
  "differences": [ ...підсет comparison де has_difference=true... ],
  "success_correlation": {
    "has_both_outcomes": true,
    "successful_count": 2,
    "failed_count": 1,
    "insights": [
      {"field": "bed_temperature", "label": "Bed Temperature",
       "success_avg": 60, "failed_avg": 55,
       "insight": "Successful prints had higher Bed Temperature"}
    ]
  }
}
```

Коли підбірка single-outcome, `success_correlation` колапсує в:

```json
{"has_both_outcomes": false, "message": "Need both successful and failed prints to analyze correlation"}
```

CSV-export endpoint-у немає, "show only differences" toggle-у теж — `differences` array у response вже дає diff-only view, і frontend його використовує, щоб наповнити summary-блок.
