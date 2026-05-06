---
title: Інвентар котушок
description: Вбудований облік пластику з ціною / lot / датою покупки, призначенням слотів AMS, авто-обліком витрати на друк і manufacturer-aware каталогом кольорів
---

# Інвентар котушок

BamDude має власний інвентар фізичних котушок — окремий (і комплементарний) до [інтеграції зі Spoolman](spoolman.uk.md). Внутрішній інвентар трекає кожну котушку з виробником, кольором, вагою, ціною, датою покупки і lot-номером; BamDude автоматично віднімає витрату з ваги на кожен друк, алертить, коли котушка падає нижче порогу, і пам'ятає, в якому слоті AMS на якому принтері яка котушка.

Користуйся цією сторінкою, якщо хочеш трекати пластик без піднімання окремого Spoolman-сервісу. Якщо вже використовуєш Spoolman — див. [Spoolman](spoolman.uk.md) для шару двосторонньої синхронізації.

## :material-view-dashboard: Огляд інвентаря

Сторінка Inventory відкривається з п'ятьма summary-картками над списком котушок, кожна — click-through до фільтрованого view:

| Картка | Що показує |
|---|---|
| **Total Inventory** | Кількість котушок + сумарна вага в кг по всьому інвентарю. |
| **Consumed (this month)** | Грами, відняті з котушок у поточному календарному місяці. Парується зі [Stats](stats.uk.md) для довших діапазонів. |
| **By Material** | Donut-чарт, розбитий за filament-type (PLA, PETG, ABS, ...). Клік на сегмент фільтрує spool-список до того матеріалу. |
| **In Printer** | Скільки котушок наразі завантажено по всіх AMS-юнітах усіх принтерів (сума slot-assignments). |
| **Low Stock** | Кількість котушок нижче або глобального `low_stock_threshold`, або їхнього per-spool override (строжча з двох). Клік фільтрує до low-stock пілки — парується з нотифікацією `filament_low`. |

### Фільтри, пошук, режими перегляду

Тулбар над списком комбінує free-form search-box з chip-стрічками і view-mode toggle-ами:

- **Search-box** — матчить за іменем, брендом, матеріалом, hex-кольором. Натисни `/` будь-де на сторінці, щоб сфокусуватися.
- **Material chips** — multi-select OR (PLA + PETG → будь-який).
- **Color chips** — multi-select OR за замовчуванням; матчить на resolved color-catalog name, тож усі "Cobalt Blue" котушки групуються незалежно від бренду.
- **Status tabs** — Active / Archived / All, плюс quick filters Used / New, плюс stock filter All / Stock (без slicer profile) / Configured (зі slicer profile).
- **Brand dropdown** — single-select.
- **View modes** — **Table** (data-focused, sortable columns) або **Cards** (visual swatches).
- **Group similar** — toggle, що візуально колапсує ідентичні unused / unassigned котушки в один expandable рядок з count-бейджем (напр. *5 identical spools*). Grouping-key — `manufacturer + material + color name + label_weight + subtype`. Used або AMS-assigned котушки завжди видні окремо, тож знаєш, яка фізична котушка в якому слоті. Group-state persist-ить через сесії.

## :material-package-variant: Додавання котушок

**Inventory** у бічному меню відкриває список котушок. **+ Add Spool** питає:

| Поле | Примітки |
|---|---|
| Brand / vendor | Вільний рядок, але BamDude автодоповнює з вендорів, яких уже бачив. |
| Material | PLA, PETG, ABS, ASA, TPU, PA, PC, … (відповідає списку Bambu, але приймає кастомні значення). |
| Colour | Hex-picker — каталог кольорів (нижче) пропонує імена. |
| Weight | Чиста вага в грамах. Bambu-котушки за замовчуванням 1000 г; картон AMS-HT — ~250 г. |
| Diameter | `1.75` (default) або `2.85`. Зберігається verbatim, тож non-Bambu бренди працюють. |
| Cost | Ціна на котушку; живить розрахунки ціни проєкту / архіву. |
| Purchase date | Опційно; корисно для "rotate stock" нагадувань. |
| Lot number | Опційно; для матчингу по партії з кількох котушок (деякі бренди здвигають відтінок між lot-ами). |
| Notes | Що завгодно для пам'яті. |

Котушки належать користувачу, що їх створив. `inventory:create` потрібен щоб додавати нові; `inventory:read` дає Viewer-у бачити список.

### Категорія + low-stock на котушку

Два додаткові опціональні поля у формі котушки точніше керують і фільтрацією, і сповіщеннями:

| Поле | Ефект |
|---|---|
| **Категорія** | Вільний короткий тег — наприклад, `PETG`, `ABS`, `TPU`, `paint`, `experimental`. Сторінка інвентаря над списком малює стрічку чіпів-фільтрів, тож можна показувати "тільки TPU" чи "тільки experimental". Стрічка чіпів з'являється лише коли хоча б одна котушка має категорію — щоб не клатати сторінку в перший день. Спецчіп `__none__` фільтрує котушки без категорії. |
| **Low-stock threshold (override)** | Per-spool override для глобального `low_stock_threshold`. Корисний коли конкретна котушка потребує раннішого попередження (наприклад, дорогий PA — 50% залишку = час замовляти; дешевий PLA може почекати до 10%). Порожньо = успадковує глобальне значення. |

Обидві колонки видні у таблиці інвентаря і редагуються inline.

### Повна форма: вкладка Filament Info

"+ Add Spool" має дві вкладки. Перша — Filament Info — покриває все, потрібне для ідентифікації котушки і резолвлення правильного slicer-preset.

| Поле | Опис |
|---|---|
| **Slicer Preset** | Search-and-select filament-profile (Bambu Cloud, local OrcaSlicer-імпорти або built-in fallback — див. [Звідки беруться preset-и](#звідки-беруться-slicer-profiles) нижче). Вибір preset auto-fill-ить *Material*, *Brand*, *Subtype* з імені preset-у. |
| **Material** | PLA, PETG, ABS, ASA, TPU, PA, PC, … — приймає кастомні значення, див. [Custom materials](#custom-materials). |
| **Brand** | Виробник; auto-complete з previously-seen брендів. |
| **Subtype** | Basic, Matte, Silk, HF, Metal, CF, … |
| **Label Weight** | Чиста вага як надрукована на котушці (default 1000 г; AMS-HT cardboard core ~250 г). |
| **Quantity (bulk)** | 1–100 котушок створюються в одній операції. Корисно для "купив 5-pack PLA" — кожна котушка створюється з ідентичним material / color / weight / cost. |
| **Color** | Visual picker з shade + opacity + finish picker-ами. Recent-colors-стрічка + brand-палітри. |
| **Extra colours** | Опційно. Comma-separated list з 2–8 hex-стопів (напр. `EC984C,#6CD4BC,A66EB9,D87694`) для multi-colour котушок. Малює swatch по-різному залежно від значення **Effect** нижче — плавний blend, hard-split смуги або color-wheel pie. Формат як на 3dfilamentprofiles.com, тож paste-and-go працює. |
| **Effect** | Накладається поверх color-swatch — **не** змінює slicer-profile. Surface-effects (*Sparkle*, *Wood*, *Marble*, *Glow*, *Matte*) малюють CSS-overlay; sheen-варіанти (*Silk*, *Galaxy*, *Rainbow*, *Metal*, *Translucent*) дають м'який sheen; structural-варіанти задають форму color-layer — *Gradient* = плавний 135° blend, *Dual Color* / *Tri Color* = hard-split горизонтальні смуги (кожен стоп у власному сегменті, без діагонального blend), *Multicolor* = conic-gradient color-wheel. Форма має live-preview pane під dropdown'ом, тож ви бачите ефект до збереження. |

#### Quick Add (Stock) режим

Toggle **Quick Add (Stock)** зверху форми перемикає на minimal-режим, що ховає slicer preset + PA Profile вкладку. Видні лише **Material** (required), **Brand**, **Subtype** (обидва опційні), **Label Weight**, **Quantity** і **Color** — ідеально для інвентаризації свіжо-прибулого замовлення до того, як ти вирішив, який slicer-profile асоціювати.

Quick-Add котушки називаються **stock spools** — вони трекають вагу і витрату як будь-яка інша котушка, але не прив'язані до printer filament-profile. Можна редагувати stock-котушку пізніше, призначити slicer-preset (вона стане *configured* у той момент) або відфільтрувати лише stock-пілку через inventory's stock-фільтр.

Поле **Quantity** показується лише в Quick Add і створює batch-и з auto-incremented lot-номерами при заповненні.

!!! tip "Bulk buying"
    5-pack PLA → set Quantity = 5 → BamDude створює 5 ідентичних котушок в одній транзакції. Парується з **Group similar** toggle на inventory-списку, щоб колапсувати їх назад в один рядок з count-бейджем.

#### Звідки беруться preset-и

Dropdown **Slicer Preset** мерджить filament-profile з трьох джерел, перевірених у priority-порядку:

| Джерело | Priority | Бейдж | Опис |
|---|:---:|---|---|
| **Bambu Cloud** | 1 | — | Personal cloud presets, синхронізовані з BambuStudio. Включає офіційні Bambu-preset-и і будь-які кастомні (напр. *# Overture Matte PLA @BBL P1S*). Потребує [Cloud Profiles](cloud-profiles.uk.md) login. |
| **Local Profiles** | 2 | `Local` (зелений) | OrcaSlicer-preset-и, імпортовані через [Local Profiles](local-profiles.uk.md). Корисно, якщо не використовуєш Bambu Cloud або юзаєш OrcaSlicer-only profiles. |
| **Built-in Fallback** | 3 | `Built-in` (бурштиновий) | Static-таблиця ~150 Bambu Lab filament-ID (PLA Basic, PETG HF, ABS, ...). Завжди доступна, без login-у. |

Preset-и з усіх трьох джерел мерджаться + дедуплікуються. Якщо cloud-login падає — local + built-in усе одно з'являються — preset-список ніколи не порожній.

User-preset-и, що inherit-ять з Bambu-preset-ів (напр. *# Overture Matte PLA @BBL H2D*), повністю підтримуються — BamDude резолвить underlying filament-ID з inheritance-ланцюжка.

#### Custom materials

Material-dropdown поставляється з PLA, PETG, ABS, TPU, ASA, PC, PA, PVA, HIPS, PA-CF, PETG-CF, PLA-CF. Якщо твого матеріалу немає (напр. PCTG, PHA, PP, PVDF) — введи його напряму в Material-поле, у дропдауні з'явиться опція *Use custom material: PCTG* унизу. Клік — commit.

Custom-матеріали працюють як built-in для inventory-tracking, usage-history, фільтрування і нотифікацій.

!!! example "Додавання PCTG (3D-Fuel Pro)"
    1. **+ Add Spool**.
    2. **Slicer Preset**: пікни найближчий PETG-preset (PCTG це PETG-варіант). Для кастомного OrcaSlicer PCTG-profile — імпортуй через [Local Profiles](local-profiles.uk.md) спочатку.
    3. **Material**: введи `PCTG` → клік *Use custom material: PCTG*.
    4. **Brand**: `3D-Fuel`. **Subtype**: `Pro`.
    5. Set color (315 °C max bed, 80 °C bed для PCTG — print/bed defaults inherit-яться з base-PETG-preset; override на slicer-side, якщо треба). Save.

#### Additional section

| Поле | Опис |
|---|---|
| **Empty Spool Weight** | Пікни зі [Spool Catalog](#spool-catalog) (90+ entries) або введи вручну — потрібно для accurate remaining-weight calculation. |
| **Remaining Weight** | Live `label_weight - weight_used` з reference-maximum bar. |
| **Cost per kg** | Per-spool cost; живить [cost-tracking](#cost-tracking) і archive cost roll-up. |
| **Note** | Free-text. |

### PA Profile вкладка

Друга вкладка прив'язує pressure-advance (K-factor) calibration-profile до котушки. Auto-select матчить profiles за brand + material + subtype через усі твої принтери + nozzle-и, з матчами, згрупованими за принтером + nozzle-ом (left / right для dual-nozzle):

- **Auto-select** — заповнює матрицю з твоїх існуючих K-profile автоматично.
- **Grouped view** — collapsible printer-headings, кожен з per-nozzle (L / R) sub-row.
- **K-factor values** показані inline, тож можна sanity-check перед save.
- **Per-printer override** — пікни інший profile для одного принтера, якщо маєш brand-specific calibration values, що відрізняються між машинами.

Див. [K-Profiles](kprofiles.uk.md) для calibration-workflow, що породжує ці profiles.

## :material-format-list-checkbox: Призначення слотів AMS

Як котушка існує — її можна припаркувати в конкретний слот AMS на конкретному принтері. Права AMS-панель на картці кожного принтера показує чотири слоти (або вісім на AMS-HT) і дає кинути котушку в кожен.

За кулісами це таблиця `spool_assignment` — один рядок на трійку `(printer, ams_id, tray_id)`. Два призначення на той самий слот одночасно існувати не можуть; присвоєння нової котушки звільняє попередню (вона повертається в "available, не в принтері").

Дві приємні фічі поверху:

- **RFID auto-assign** — Bambu-котушки з цілими RFID-тегами матчаться на каталог моментально, як AMS читає тег. Якщо тег вказує на відому каталог-сутність, але інвентар-рядка ще немає — BamDude пропонує створити inline. Якщо тег невідомий (third-party, custom) — можна прив'язати його до наявної котушки, щоб наступного разу не лазити вручну.
- **Auto-tracking нових Bambu-котушок** — коли AMS RFID не матчить жодного існуючого tray UUID, BamDude спочатку шукає **untagged**-котушку зі збіжним матеріалом + кольором + брендом (`Bambu` / `Bambu Lab` / unspecified) і прив'язує RFID до неї. Тож Quick-Add stock-запис, що ти залогував наперед, реюзається (твоя вага, нотатки, cost-data зберігаються) замість того, щоб видавати дублікат. Якщо збігу немає — створюється свіжий inventory-рядок з AMS-data.
- **Drying schedules + AMS humidity tracking** — див. [AMS та вологість](ams.uk.md) — inventory- і AMS-сторінки шерять стан, тож "drying" котушка візуально позначена як in-progress в обох місцях.

### Стабільні assignments на startup-і

Spool-assignments зберігаються через рестарти BamDude за **spool ID**, не за slot ID. Якщо AMS реконнектиться в іншому порядку при boot-і — RFID slot 3 приземлиться там, де був slot 1 минулої сесії, тощо — BamDude відновлює за RFID-identifier-ом, тож правильна котушка лишається прив'язана до правильного фізичного tray, без ручного фіксу. Якщо та сама котушка все ще в тому самому фізичному слоті (verified by RFID) — reconfigure-команда принтеру не відсилається.

### Configure AMS Slot vs Assign Spool

Ці дві дії виглядають сусідніми в slot-меню, але роблять різне. Дивись таблицю нижче, коли вагаєшся:

| Дія | Що змінює | Lifetime | Коли використовувати |
|---|---|---|---|
| **Configure Slot** | Каже **принтеру**, який filament-profile (температури, flow, pressure advance) використовувати для того фізичного слота | До reconfigure або поки RFID не overwrite-не | "Я щойно завантажив third-party PETG у slot 1 — set profile, щоб принтер використовував правильні temps." |
| **Assign Spool** | Каже **BamDude**, який inventory-рядок білити за consumption з того слота — і **також** запускає Configure Slot з spool's filament-profile, color, K-profile | До reassign-у або поки AMS не задетектить інший RFID | "Трекати, яка фізична котушка в якому слоті, тож usage / cost білиться правильно." Працює і на empty, і на configured слотах. |

Assigning spool — найпростіший workflow — він обробляє tracking + printer configuration в один крок. Використовуй Configure Slot напряму лише коли хочеш override settings або налаштувати слот без inventory-котушки.

## :material-water-percent: Автоматичний облік витрати

Кожен друк, який BamDude диспатчить, читає per-filament `weight` з source-3MF. На `print_complete` витрачені грами віднімаються з котушки, що була призначена відповідному AMS-слоту на момент старту друку:

- Таблиця `spool_usage_history` записує кожне віднімання (один рядок на друк × котушку).
- `spool.used_grams` — running-total.
- `spool.weight - spool.used_grams` — те, що залишилося.

Inventory-сторінка кольорує кожну котушку за залишком %, з налаштовним **low-stock threshold** (Settings → Inventory). Коли котушка падає нижче — спрацьовує нотіфікація `filament_low` (підпишись на тих провайдерах, де це треба).

Якщо друк впав посеред — віднята кількість це slicer-estimate × completion-ratio (best effort), а не повний estimate. External-print fallback archives — ті, що з друків, запущених прямо з тачскріна принтера — реконсилюються тим самим шляхом, як їхній 3MF відновлюється.

### Деталізоване usage-tracking

Pipeline відняття складніше, ніж плоске "відняти slicer-estimate в кінці друку". BamDude обирає найточніше доступне джерело per-сценарій:

| Сценарій | Primary-джерело | Fallback |
|---|---|---|
| **3MF доступний + completed-друк** | Per-filament `used_g` з `slice_info.config.json` 3MF, мапнуте на physical AMS tray-ї через `ams_mapping`, захоплене з MQTT print-команди | — |
| **3MF доступний + failed/aborted partial-друк** | Per-layer G-code analysis: скільки грамів пройшло через кожен філамент до layer-у, де друк зупинився | Linear scaling = `total × completion_ratio`, якщо per-layer data не парситься |
| **Slicer-initiated друк** (BambuStudio / OrcaSlicer / Handy) | `ams_mapping` захоплене з live MQTT print-команди — гарантує, що правильний tray білиться, незалежно від того, який app стартував | — |
| **Single-filament друк** | Принтер's currently-active tray | — |
| **G-code-only друк, без 3MF** | AMS `remain%` дельта між print-start і print-end (integer-precision, ~10 г на 1 % step для 1 кг котушки) | — |
| **External print, fallback archive recovered later** | Реюзає 3MF source у момент завершення recovery, ретроактивно реконсилює відняття | — |

#### Mid-print spool-change семантика

Якщо ре-assign-аєш котушку до слота **під час** друку:

- BamDude порівнює timestamp assignment-зміни з timestamp print-start-у.
- Якщо зміна сталася **після** print-start — використовується live-assignment, тобто витрата перемикається на нову котушку від точки swap і далі.
- Та частина, що вже надрукована до зміни, лишається білитись попередній котушці.
- Якщо mid-print зміни не було — snapshot, взятий на print-start, зберігається, і повне відняття йде на ту котушку.

Це робить mid-batch refills коректними без ручної реконсиляції: завантаж свіжу котушку, коли одна закінчується, ре-assign її в BamDude, і решта друку білиться новій котушці.

---

## :material-currency-usd: Cost Tracking

Кожна котушка може нести per-kg cost; BamDude підбиває це в per-print, per-archive, per-project cost-stat-и.

### Setting cost-per-kg

| Де | Поле | Примітки |
|---|---|---|
| Spool form → Additional section | **Cost per kg** | Per-spool override; має пріоритет над глобальним default-ом |
| **Settings → Filament** | **Default Filament Cost** | Per-kg fallback, коли в котушки нема cost (default 25.00 в `default_filament_cost`) |
| **Settings → Filament** | **Currency** | Символ, що використовується скрізь — USD, EUR, GBP, MYR і ще ~25 |

### Як обчислюються cost-и

Для кожного друку BamDude виводить per-spool cost у міру віднімання грамів:

```
cost = (weight_used_grams / 1000) × cost_per_kg
```

- Per-spool `cost_per_kg` виграє; якщо unset — використовується глобальний default.
- Обчислений cost зберігається на кожному `spool_usage_history` рядку і агрегується в `print_archive.cost`.
- Print-modal preview показує **real-time cost estimate**, базований на завантажених котушках + їхніх cost/kg, перед стартом друку.
- Картки архівів показують total filament-cost; inventory-таблиця має sortable Cost/kg колонку (hidden by default — увімкни через column-settings); [Stats](stats.uk.md) сумує cost через усі друки.

### Перерахунок cost-ів

Якщо оновлюєш ціни котушок або додаєш cost-data ретроактивно — кнопка **Recalculate Costs** на Archives-сторінці перевиводить cost кожного архіву, використовуючи поточні spool-data, у цьому priority-порядку:

1. `spool_usage_history` records, joined to `archive_id` (найточніші, per-spool actuals).
2. Legacy usage records, joined by print-name (для старіших архівів без FK link-у).
3. Filament-catalog ціни (коли usage records взагалі немає).

!!! tip "Зведи cost-и рано"
    Для accurate cost-tracking — зведи `cost_per_kg` на кожній котушці, коли додаєш її в inventory. Default — груба оцінка; індивідуальні spool-ціни дають тобі точні per-print дані і роблять кнопку **Recalculate Costs** корисною.

## :material-palette: Каталог кольорів

Імена кольорів приходять з таблиці `color_catalog` — manufacturer-aware. Коли два бренди постачають paint-chip з тим самим hex — для UI виграє Bambu Lab; non-Bambu резолвиться через свої записи. Якщо hex котушки взагалі не в каталозі — BamDude падає на HSL-derived ім'я ("dark cyan", "light yellow"), тож в UI ніколи не побачиш голий hex.

Каталог можна розширювати руками під **Settings → Inventory → Colour Catalog**. Frontend підтягує runtime-мапу `{hex: name}` один раз на сесію — додавання нового запису діє на наступний логін (або hard-refresh).

### Багатоколірні градієнти

Painted, dual-color і silk-пластики — це не одне hex-значення, а градієнт між двома чи більше. BamDude малює їх як **справжні градієнтні swatch'і** на картках інвентаря, AMS-індикаторах слотів і colour-picker'і, замість колапсу до одного плоского hex (який завжди обирає не той "домінуючий" колір). Метадані 3MF несуть color stops; каталог резолвить ім'я; widget-swatch малює градієнт у CSS. Жодних ручних paint-chip-таблиць — суто data-driven.

!!! tip "Не реінтроʼдьюс хардкод-таблиці кольорів"
    BamDude свідомо викинув хардкод `tray_id_name` / hex-таблиці, які неминуче mislabel-или third-party пластики. Каталог — єдина точка істини, навіть коли спокусливо "shortcut-нути" резолвлення кольору десь в коді.

## :material-account-multiple: Дозволи

| Permission | Ефект |
|---|---|
| `inventory:read` | Переглянути список котушок і AMS-призначення. |
| `inventory:create` | Додати нові котушки. |
| `inventory:update` | Редагувати поля котушки, призначати слоти, ставити spool-specific K-profile overrides. |
| `inventory:delete` | Видаляти котушки (також видаляє пов'язані assignments). |
| `inventory:view_assignments` | Конкретно spool-on-slot індикатори, що рендеряться на картках принтерів. Дано Viewers окремо, щоб не-оператор бачив "що де лежить", не отримуючи `inventory:read`. |

## :material-clipboard-list: Reference налаштувань

Релевантні settings-ключі (всі під Settings → Inventory):

| Setting | Default | Ефект |
|---|---|---|
| `low_stock_threshold` | `20` | % залишку котушки, при якому стріляє нотифікація `filament_low` (діапазон 0.1 – 99.9). |
| `disable_filament_warnings` | `false` | Master mute для low / out-of-filament алертів. |
| `prefer_lowest_filament` | `false` | При авто-присвоєнні котушки до друку — перевага котушці з найменшим залишком (щоб дотиснути огризки). |
| `default_filament_cost` | `25` | Per-kg fallback-ціна, коли поле `cost` не задано. |
| `spoolman_enabled` | `false` | Toggle інтеграції зі Spoolman. Див. [Spoolman](spoolman.uk.md). |

### Sync Weights from AMS (recovery-tool)

Коли built-in inventory використовується — **Settings → Filament** виставляє кнопку **Sync Weights from AMS** під mode-селектором. Вона force-синкає всі inventory spool-weights з live AMS `remain%` sensor-values на наразі-підключених принтерах.

Використовуй це **тільки** для відновлення зіпсованих weight-data — наприклад, якщо printer power-off event скинув tracked grams усіх котушок до нуля. Sync overwrite-ить збережені `weight_used` тим, що AMS репортує прямо зараз. Принтери мають бути online, щоб sync читав sensor-values.

!!! warning "Низька роздільна здатність — лише recovery"
    AMS `remain%` — integer-precision (1 % step = ~10 г для 1 кг котушки). Для day-to-day tracking — покладайся на автоматичне 3MF-based deduction вище — воно точне до граму. **Sync Weights from AMS** — це recovery-tool, не normal accounting-path.

### Spool Catalog

Pre-defined empty-spool weights для швидкого вибору при додаванні котушок. Ships з 90+ entries, що покривають common manufacturers (Bambu Lab cardboard core, eSun, Polymaker, Overture, тощо). Живе під **Settings → Inventory → Spool Catalog**.

| Кнопка | Опис |
|---|---|
| **Export** | Скачати весь каталог як JSON-файл для backup-у або community-sharing |
| **Import** | Завантажити JSON-файл, щоб додати entries. Дублікати (та сама name) пропускаються автоматично |
| **Reset** | Відновити built-in default-каталог (overwrite-ить усі entries — confirmation required) |
| **+ Add** | Вручну додати новий spool-weight entry |

#### Формат імпорту

```json
[
  { "name": "Brand - Spool Type", "weight": 210 }
]
```

### Color Catalog

Єдина точка істини для резолвлення hex-кольорів у display-імена — AMS popover, inventory-список, print-modal filament-картки, Reprint AMS-mapping модалка і auto-provisioned inventory entries — усі дивляться імена в цій таблиці. Ships з 600+ кольорами через 20 брендів.

| Кнопка | Опис |
|---|---|
| **Export** | Скачати весь каталог як JSON |
| **Import** | Завантажити JSON-файл, щоб додати кольори. Дублікати (той самий manufacturer + color name + material) пропускаються |
| **Sync** | Тягне нові кольори з [FilamentColors.xyz](https://filamentcolors.xyz/) — community-database виміряних filament-кольорів. **Лише додає нові entries**, ніколи не змінює існуючі |
| **Reset** | Відновити built-in default-каталог (overwrite-ить усі entries) |
| **+ Add** | Вручну додати новий color-entry (manufacturer, color name, hex, material) |

#### Формат імпорту

```json
[
  { "manufacturer": "eSUN", "color_name": "Silk Gold", "hex_color": "#C48E2F", "material": "PLA Silk" }
]
```

!!! info "Авторитет display-імен"
    BamDude резолвить кожне spool-color-ім'я, дивлячись hex у цьому каталозі (Bambu Lab entries вигрують, коли той самий hex зареєстрований під кількома брендами). Жодного hardcoded `tray_id_name` → name mapping нігде в кодбазі — додавання або редагування кольору тут — це supported шлях для виправлення або розширення display-імен. Restart-free: frontend перетягує каталог при наступному page-load.

---

## :material-frequently-asked-questions: FAQ

### Мого матеріалу немає у dropdown (напр. PCTG, PHA, PP)

Введи material-ім'я напряму в Material-поле. Зелена опція *Use custom material* з'явиться внизу dropdown-у — клік. Custom-матеріали працюють як built-in для tracking, usage-history, фільтрування і нотифікацій.

### Чи треба обирати slicer-profile для кожної котушки?

Ні. Використовуй **Quick Add (Stock)** режим, щоб додавати котушки з лише material + weight. Stock-котушки трекають вагу, витрату і cost; можна редагувати їх пізніше і призначити profile. У full-режимі Slicer Preset обов'язковий — пікни найближчий доступний preset (generic *PETG Basic* для third-party PETG, наприклад) або імпортуй кастомні OrcaSlicer-profiles через [Local Profiles](local-profiles.uk.md), щоб вони з'явились у dropdown.

### Маю різні принтери (P1S + H2D) і nozzle-и — чи preset-и важливі?

Spool-inventory сам по собі **printer-agnostic**. Додай котушку раз, призначай у будь-який AMS-слот будь-якого принтера. Printer-model filtering kick-ає в, лише коли **Configure AMS Slot** (кажеш принтеру, який profile використовувати) — там preset-список фільтрується за printer-model, тож бачиш лише compatible profiles.

### Inventory лише для loaded-котушок?

Ні. Inventory трекає **усі твої котушки** — loaded і unloaded. Можна логати кожну котушку, що маєш, навіть ті, що сидять на полиці. *In Printer* summary-картка показує, скільки наразі завантажено; решта трекаються так само (weight remaining, usage history, cost, drying schedule).

### У чому різниця між Assign Spool і Configure Slot?

Див. [таблицю порівняння](#configure-ams-slot-vs-assign-spool) вище. Коротко: **Assign Spool** робить обидва — link-ує inventory-рядок для tracking-у і конфігурує слот, використовуючи spool's profile. **Configure Slot** робить лише printer-side configuration. Використовуй Assign для normal-workflow; використовуй Configure, коли хочеш override settings або налаштувати слот без inventory-котушки.

### Звідки беруться slicer-profiles?

Три джерела, перевірені у priority-порядку: **Bambu Cloud** (твої synced presets, включно з кастомними) → **Local Profiles** (OrcaSlicer-імпорти) → **Built-in Fallback** (~150 Bambu Lab filament-ID). Навіть без cloud-login-у останні два гарантують, що preset-список ніколи не порожній. Див. [Звідки беруться preset-и](#звідки-беруться-slicer-profiles) для деталей.
