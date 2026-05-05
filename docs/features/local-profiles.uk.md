---
title: Local Profiles
description: Імпорт OrcaSlicer / Bambu Studio presets без Bambu Cloud — file-based filament, process, printer presets з inheritance resolution
---

# Local Profiles

Local Profiles — no-cloud шлях для слайсер-presets. Кидай OrcaSlicer- чи Bambu Studio-експорт у BamDude, і filament / process / printer presets опиняються в локальній БД — та сама поверхня, що й [Cloud Profiles](cloud-profiles.md), але без Bambu-акка, без internet round-trip-а на кожному читанні і з повною підтримкою community-профілів, що ніколи не йшли через Bambu Cloud.

Два preset-source-и співіснують. Де імена колідують, **Local перемагає** — див. [Tier priority](#tier-priority) нижче.

---

## :material-target: Коли використовувати

- Не маєш (або не хочеш) Bambu Cloud акка.
- Друкуєш на **community-філаментах**, яких нема в Bambu-каталозі (Hatchbox, eSUN, Polymaker, FormFutura тощо).
- Куреш свої **process presets** під конкретні use-кейси (production-quality vs prototype-fast) і хочеш мати їх version-controlled поза Bambu-серверами.
- Друкуєш на **non-Bambu принтері** через BamDude slicer integration і потрібен його OrcaSlicer machine-config.
- Хочеш **детермінованої** preset-поведінки — ті самі байти, той самий slice output, без сюрпризного upstream-rev.

---

## :material-file-import: Підтримувані формати

| Розширення | Що містить | Детектиться як |
|---|---|---|
| `.json` | Один OrcaSlicer preset | filament / process / printer (auto) |
| `.orca_filament` | OrcaSlicer single-filament бандл | filament |
| `.bbscfg` | OrcaSlicer / Bambu Studio config бандл (filament + process + printer) | mixed — split по директоріях |
| `.bbsflmt` | Bambu Studio filament бандл | filament |
| `.zip` | ZIP з вищеназваним | mixed — auto-classify per file |

Type detection багатоступенева:

1. Explicit `type` field у JSON
2. ZIP directory layout (`filament/`, `process/`, `machine/`)
3. Settings ID keys (`filament_settings_id`, `print_settings_id`, `printer_settings_id`)
4. Content keys (`layer_height` → process; `filament_type` → filament)
5. Name patterns (`0.20mm` в імені → process)

Якщо heuristics не вгадала — запусти **Reclassify** (`POST /local-presets/reclassify`), щоб переоцінити все за новими правилами.

---

## :material-upload: Імпорт

**Settings → Local Profiles → drop file or click to pick.** Import endpoint приймає або form-encoded `multipart/form-data` upload (UI), або програмний POST (`POST /api/v1/local-presets/import` з полем `file`).

Після імпорту побачиш один з трьох toast-результатів:

| Колір | Що значить |
|---|---|
| **Зелений** | N presets імпортовано — імя + count |
| **Помаранчевий** | M presets пропущено — дублі по імені |
| **Червоний** | Помилки — типово malformed JSON всередині бандла |

Bundle-імпорти **all-or-nothing per file**: corrupt JSON всередині ZIP не аборт-ить решту бандла, але bad-entry рапортується окремо.

---

## :material-file-tree: Inheritance resolution

OrcaSlicer presets часто `inherit` Bambu base-profile і override-ять кілька полів ("PLA Basic at 215 °C замість 220 °C, інакше як parent"). На імпорті BamDude:

1. Детектить `inherits` field.
2. Шукає parent-а у **OrcaSlicer GitHub mirror** (`raw.githubusercontent.com/SoftFever/OrcaSlicer/main/resources/profiles/BBL/...`).
3. Рекурсивно резолвить ланцюг (max **10 рівнів** — далі трактує як malformed і стоп).
4. Мерджить parent → child (child fields перемагають на конфлікті).
5. Зберігає **повністю resolved** preset у локальній БД, плюс літеральний `inherits`-name на рядку для display-у.
6. Кешує кожного fetched parent-а в `orca_base_profiles` (TTL **7 днів**).

Кеш робить повторні імпорти швидкими і тримає тебе подалі від GitHub anonymous rate-limit.

!!! tip "Offline-імпорти"
    Presets без `inherits` імпортуються повністю offline. Presets, що потребують parent-а — потребують GitHub reachable на **першому** імпорті. Далі parent кешований, і той самий parent живить будь-який майбутній preset, що inherit-ить від нього. Щоб pre-warm-нути кеш, заімпортуй малий known-parent preset з мережею до того, як підеш offline.

!!! note "GitHub недосяжний"
    Якщо GitHub недосяжний коли preset потребує parent — імпорт не фейлиться; preset зберігається тільки з override-полями. Працює, але missing-from-parent поля порожні поки не reimport-неш після того, як кеш заповниться.

---

## :material-database-search: Що живе на preset-рядку

| Поле | Source |
|---|---|
| `name` | `name` з JSON |
| `preset_type` | `filament` / `process` / `printer` (auto-classified) |
| `source` | `orcaslicer` (file import) або `manual` (створено через UI) |
| `filament_type` / `filament_vendor` | Витягнуто на filament-presets |
| `nozzle_temp_min` / `nozzle_temp_max` | Range з `nozzle_temperature` array |
| `pressure_advance` | K-factor (string для OrcaSlicer-сумісності) |
| `default_filament_colour` | Hex типу `#FF6633` |
| `filament_cost`, `filament_density` | Per-spool економіка |
| `compatible_printers` | JSON array — драйвить "for printer" фільтр |
| `setting` | Повний resolved JSON блоб (post-inheritance merge) |
| `inherits` | Літеральний parent-name для display |
| `version`, `created_at`, `updated_at` | Bookkeeping |

Повний resolved блоб — те, що споживають slicing-пайплайни. Усе, що нормально читається з OrcaSlicer preset JSON, там.

---

## :material-water-percent: AMS slot integration

Filament local presets з'являються у AMS slot-config modal так само, як cloud filament presets:

- Dropdown показує local presets з зеленим **Local** бейджем, потім cloud, потім built-in fallback.
- Вибір local-preset-а пише його `nozzle_temp_*`, `filament_type`, `default_filament_colour` у slot-record — ті самі поля, що й cloud preset поставив би.
- AMS-tray tooltip і K-profile UI обидва консультуються з `_enrich_from_local_presets` (у `cloud.py`), коли cloud / built-in таблиці пропускають `setting_id` — local presets третій tier резолвера.

Див. [AMS](ams.md) як slot-config флоу йде від "preset selected" до "MQTT command issued".

---

## :material-layers-triple: Tier priority

Три source-и можуть відповісти "що таке preset X?". Коли slice modal просить merged-список:

1. **Local** (ця сторінка) — file-imported, DB-backed, `source='orcaslicer'` чи `'manual'`. **Перемагає на name-колізії.**
2. **Cloud** — fetched per-user з Bambu Cloud (див. [Cloud Profiles](cloud-profiles.md)).
3. **Bundled** — slicer-sidecar fallback. Bambu stock-каталог, як shipped всередині OrcaSlicer-image.

Unifier (`/api/v1/slicer/...`) дедуплікує по імені через tier-и, тримає highest-priority entry. Тож якщо ти заімпортував `Bambu PLA Basic @BBL X1C` локально і маєш cloud-версію — показується тільки local. Саме та поведінка, що ти хочеш, коли community-preset розходиться з upstream.

---

## :material-pencil: Редагування

Cards розгортаються на клік. Detail view показує кожне поле resolved JSON-а. Щоб редагувати:

| Дія | Endpoint | Нотатки |
|---|---|---|
| **Update name** | `PUT /api/v1/local-presets/{id}` з `{name}` | Косметика |
| **Update settings** | `PUT /api/v1/local-presets/{id}` з `{setting: {...}}` | Re-run `resolve_preset()` — inheritance резолвиться заново проти нового `inherits`, потім re-extract core fields |
| **Manual create** | `POST /api/v1/local-presets/` | Обходить file-import path — корисно для on-the-fly твіків |

В UI нема "save as new" affordance — це робиться через duplicate-then-edit на source-файлі до повторного імпорту.

---

## :material-delete: Видалення

| Scope | Endpoint |
|---|---|
| **Single** | `DELETE /api/v1/local-presets/{id}` |
| **Bulk** | List-view чекбокси + Delete-selected кнопка (дзвонить single endpoint per row) |

Deletes **миттєві** — без trash, без undo. On-disk файл під `<DATA_DIR>/local_presets/` (кеш імпорту) теж не trash; реконструюється з DB-рядка, тож cache-layer прибирає видалені рядки на наступному sweep-і.

---

## :material-cached: Управління base-profile cache

Два admin-endpoint-и виставляють parent-profile cache:

| Endpoint | Що |
|---|---|
| `GET /api/v1/local-presets/base-cache/status` | Скільки parent-ів кешовано, oldest fetch timestamp, total bytes |
| `POST /api/v1/local-presets/base-cache/refresh` | Force-refetch кожного кешованого parent-а з GitHub (ігнорує TTL) |

Запускай **refresh** після major OrcaSlicer release — Bambu іноді silently фіксить base-profile (bumped temp range, corrected K factor), а твоя кешована копія лагає до 7 днів інакше.

---

## :material-shield-key: Permissions

| Permission | Дозволяє |
|---|---|
| `settings:read` | List presets, inspect повний JSON, read base-cache status |
| `settings:update` | Import, manual-create, edit, delete, reclassify, refresh base cache |

Дефолтні групи: **Administrators** обидва, **Operators** обидва, **Viewers** — тільки `settings:read` (можуть переглядати, але не імпортувати).

!!! info "Чому `settings:*`?"
    Local presets — конфігурація. Живуть у тому ж trust-tier-і, що й будь-що в **Settings**. Окремої `presets:*` permission-family нема, бо permission-model трактує "edit preset" і "edit smart-plug config" як той самий risk-клас.

---

## :material-folder-open: Куди файли потрапляють на диск

DB зберігає resolved preset JSON inline. Оригінальний uploaded-файл тримається як working-copy під:

```
<DATA_DIR>/local_presets/<id>/<original-filename>
```

Це не авторитативне — DB-рядок є. On-disk копія — debugging-aid (можна `unzip` `.bbscfg` і inspect-нути raw OrcaSlicer source). Видалення рядка видаляє директорію; видалення директорії руками тригерить re-import на наступному доступі.

Base-profile кеш живе окремо у таблиці `orca_base_profiles` — DB-resident, не на диску, тож переживає `<DATA_DIR>` restore чисто.

---

## :material-help-circle: Troubleshooting

??? question "Import каже `0 imported`, файл начебто валідний"
    Скоріше за все duplicate-detection — кожен preset у файлі вже існує у DB по імені. Помаранчевий skip-toast count твій сигнал. Щоб re-import-нути після редагування — спочатку видали наявний рядок, потім re-upload.

??? question "Inheritance не резолвиться — preset має менше полів, ніж мав би"
    GitHub був недосяжний на імпорті. Запусти `POST /local-presets/base-cache/refresh`, коли мережа повернулась, потім re-upload (або `PUT` preset-у `setting` field, щоб тригернути re-resolution).

??? question "Preset класифіковано не тим типом"
    Запусти `POST /local-presets/reclassify`. Якщо heuristics все одно помиляються — JSON не має ні explicit `type` field, ні традиційних content keys; додай `"type": "filament"` (або `"process"` / `"printer"`) у source-файл і re-import.

??? question "AMS slot dropdown не показує мій новий local preset"
    Slice-modal кеш має 5-min TTL. Закрий і відкрий modal, або перезапусти AMS slot-config dialog.

??? question "Хочу шерити preset bundle через install-и"
    Експорти з OrcaSlicer / Bambu Studio (`File → Export → Export Preset Bundle`), кидай `.bbscfg` у import-zone кожного install-а. DB row-format спеціально не stable interchange format — round-trip через slicer-export.

??? question "Можна Cloud + Local разом?"
    Так — співіснують. Local перемагає на name-колізії. Якщо хочеш, щоб cloud-preset перебивав local-ний — переіменуй local (його DB `name` field) до наступного slice.
