---
title: Full-text пошук
description: SQLite FTS5 (або PostgreSQL tsvector) пошук по архівних print name, filename, tags, notes, designer і filament type — з префіксним wildcard, exclusion, phrase-matching і one-click index rebuild
---

# Full-text пошук

BamDude індексує фіксований набір полів архівної метадати у full-text-структуру: SQLite-інстали отримують FTS5 virtual-таблицю (`archive_fts`), PostgreSQL-інстали — `tsvector`-колонку з GIN-індексом. Обидва бекенди обслуговують той самий `GET /api/v1/archives/search?q=...` endpoint. Пошук вмикається автоматично міграцією `m001`; ручної настройки не треба.

## :material-magnify: Що індексується

Індекс покриває шість колонок `print_archives`:

| Поле | Що туди йде |
|---|---|
| `print_name` | Print name з 3MF або відредагований override від користувача. |
| `filename` | Оригінальний 3MF filename. |
| `tags` | Користувацькі теги (comma-separated string). |
| `notes` | Free-form notes, прикріплені до архіву. |
| `designer` | Author / designer string з 3MF metadata. |
| `filament_type` | Material code (PLA, PETG, ABS, ...). |

Все. AMS color names, printer name, project name, plate-level metadata, library files **не** в індексі — див. [Обмеження](#material-alert-outline-) нижче.

!!! note "Два бекенди, один endpoint"
    На SQLite пошук виконує `archive_fts MATCH :term`. На PostgreSQL — `search_vector @@ to_tsquery('simple', :term)` з `ts_rank` ordering. Route автодетектить діалект через `is_postgres()`. Якщо FTS сам падає (corrupt index, malformed query, який parser відкидає), route тихо фолбекається на повільніший `LIKE` scan по тих самих колонках, тож пошук ніколи не дає 500 — просто повільніше.

## :material-keyboard: Тригер пошуку

Search-box живе в Archives toolbar. Frontend синхронізує URL query, тож результати пошуку shareable / bookmarkable.

Глобального `/` keyboard shortcut для archive-пошуку поки немає — `/` shortcut підвʼязаний лише до spool-list search-box на сторінці [Inventory](inventory.uk.md). На Archives використовуй click-and-type у хедері сторінки.

## :material-format-text: Синтаксис

Поведінка route залежить від того, який DB-бекенд у тебе, але в обох однаковий observable feel для типових кейсів:

| Шаблон | Що робить | Бекенд-замітки |
|---|---|---|
| `vase` | Plain word match. | SQLite автододає `*`, тож еквівалент `vase*`. PostgreSQL токенізує в `vase:*`. У будь-якому разі prefix matching — default. |
| `vase*` | Explicit prefix. Матчить `vase`, `vasely`, `vases`. | SQLite: handled natively. PostgreSQL: токенізується так само як `vase`. |
| `"calibration cube"` | Phrase match. Обидва слова мусять зʼявитися сусідньо і в порядку. | FTS5 підтримує phrase queries прямо. |
| `vase OR cup` | Будь-яке слово. | FTS5 підтримує `OR`; PostgreSQL `tsquery` трактує пробіл як `&`, тож на PG-інсталі вживай помірковано. |
| `phone -case` | Виключити слово. Матчить архіви, де згадується `phone`, але не `case`. | FTS5 native. |

!!! tip "На PostgreSQL роби queries простими"
    На PG route ділить твій query за whitespace і джойнить через `&` (AND), потім додає `:*` до кожного слова для prefix matching (напр. `vase calibration` → `vase:* & calibration:*`). Boolean `OR` і exclusion (`-`) не претранслюються в `tsquery` syntax — вони матчатимуть літерально як частину слова. Якщо query фолбекається на LIKE — отримаєш partial-substring matching по всіх шести колонках, що permissive-ніше, але повільніше.

## :material-sort: Ranking і форма результатів

| Бекенд | Ranking |
|---|---|
| SQLite (FTS5) | `ORDER BY rank` — built-in BM25-style ranking FTS5. |
| PostgreSQL | `ORDER BY ts_rank(search_vector, query) DESC`. Per-field ваги: `print_name` = A, `filename` = B, `tags` = B, `designer` = C, `filament_type` = C, `notes` = D. Тож хіт у print name виграє хіт у notes. |

Trashed архіви (`deleted_at IS NOT NULL`) фільтруються **після** FTS-lookup. Тобто trashed-рядки все ще займають слоти в `LIMIT 50`-вікні; якщо query повертає 0 результатів, але ти впевнений, що щось матчить — restore з [Library Trash](library-trash.uk.md) (або archive-еквівалентa — та сама `deleted_at` колонка на archives).

## :material-filter: Комбінування з фільтрами

Окрім free-form `q`, search endpoint приймає:

| Param | Призначення |
|---|---|
| `printer_id` | Обмежити одним принтером. |
| `project_id` | Обмежити одним project-ом. |
| `status` | `completed` / `failed` / `printing`. |
| `limit` | Default 50, max enforce-ється upstream. |
| `offset` | Пагінація. |

Filter chips на Archives-сторінці також fee-дять регулярний `GET /api/v1/archives/?search=...` listing endpoint, який використовує той самий FTS-шлях внутрішньо.

## :material-cog-refresh: Manual index rebuild

Тригери, що підтримують `archive_fts` (SQLite), і BEFORE INSERT/UPDATE trigger (PostgreSQL) тримають індекс синхронізованим автоматично — кожен insert, update, delete на `print_archives` propagate-иться. Ребілдити майже ніколи не доводиться.

Коли ребілдити:

- Після failure-нутої schema-міграції, що зачепила `print_archives`.
- Після імпорту архівів через прямий SQL (минути ORM — означає, що тригери можуть фаєрити нерелайно залежно від driver).
- Якщо search явно повертає неправильні результати, що не відображають поточний стан рядків.

Як ребілдити:

```
POST /api/v1/archives/search/rebuild-index
```

Permission: `archives:update_all`. Повертає `{"message": "Search index rebuilt with N entries"}`.

На SQLite це чистить `archive_fts` і re-INSERT-ить кожен рядок з `print_archives`. На PostgreSQL виконує `UPDATE print_archives SET print_name = print_name`, що фаєрить BEFORE INSERT/UPDATE trigger на кожен рядок і ребілдить `search_vector` in place.

!!! warning "Локає archives-таблицю на короткий час"
    На 100k-archive install rebuild займає кілька секунд і тримає lock на `print_archives`. Не ребілдь під час printing-burst.

## :material-alert-outline: Обмеження

| Що НЕ searchable | Чому |
|---|---|
| Library files | Library використовує окремий ORM-level filter, без FTS index. Library list endpoint-и приймають `search` param, але це `LIKE` по filename/folder. |
| Projects | Те саме — listed через project list endpoint, без full-text index. |
| Settings, users, permission-и | Не індексуються — by design, щоб secret-и не потрапляли в FTS dump-и. |
| AMS color names | Кольори живуть у `color_catalog` таблиці і джойняться під час render-у; вони не денормалізовані на `print_archives`. |
| Printer names | Та сама причина — printer name це джойн, не колонка на `print_archives`. Фільтруй через `printer_id`. |
| Plate-level metadata | Зберігається як JSON всередині `print_archives.extra_data`; FTS5/tsvector не індексують nested JSON. |

Якщо треба фільтрувати по чомусь, чого нема в FTS-індексі — комбінуй search з `printer_id` / `project_id` / `status` query-параметрами, або використовуй регулярний Archives list endpoint з його filter chips.

## :material-shield-key: Permission-и

| Дія | Permission |
|---|---|
| Search archives | `archives:read` |
| Rebuild index | `archives:update_all` |

## :material-api: API reference

```
GET /api/v1/archives/search?q=benchy
GET /api/v1/archives/search?q=benchy&printer_id=2&status=completed
POST /api/v1/archives/search/rebuild-index
```

List endpoint (`GET /api/v1/archives/?search=...`) приймає той самий `search` term і ходить через той самий FTS-шлях внутрішньо, тож будь-який syntax, що працює на `/search`, працює і на listing.
