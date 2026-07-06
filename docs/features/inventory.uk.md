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
- **Material dropdown** — single-select.
- **Color dropdown** — single-select. Опції — кольори, які реально є в наявності (з твоїх існуючих, не архівованих котушок), згруповані за resolved color-catalog name, тож два близьких hex, що обидва читаються як "Cobalt Blue", фільтруються разом незалежно від бренду. Дропдаун зʼявляється, лише коли хоча б одна котушка в наявності має резолвабельний колір.
- **Storage Location chip** — звужує список котушок до однієї локації зберігання з [керованого каталогу локацій](#storage-locations-catalog), тож можна бачити лише котушки з однієї коробки / полиці / dry-box.
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

### Copy Spool — дублювати існуючий рядок

Кожен рядок котушки (cards / table / grouped) має кнопку **Copy** поряд з Edit. Клік відкриває форму котушки, попередньо заповнену всім з вихідного рядка крім `weight_used` — він скидається в **0**. Корисно коли ти щойно купив другу / третю / n-ну котушку існуючого філаменту. Заголовок читає **Copy Spool** замість Edit Spool, footer-кнопка читає **Copy Spool** замість Save. **Quick Add (bulk `quantity` toggle) доступний і в copy** — тож можна склонувати котушку одразу в цілий batch; кожна копія стартує чистою (usage = 0, без RFID-tag). Вихідний рядок не чіпається; збереження створює нові котушки, кожна з власним `id`. Форма котушки printer-agnostic, тож та сама Copy працює і в Spoolman-режимі — існуючий create-mutation routing обробляє обидва шляхи.

### Bulk edit — змінити багато котушок одразу

Кнопка **Масове редагування** в тулбарі (тільки internal inventory) відкриває діалог, де можна змінити поле одразу для кількох котушок. Обери, які котушки редагувати (стартує з усіх відфільтрованих; зніми у лівому списку ті, що чіпати не треба) і **познач поля для застосування**: slicer preset, матеріал, бренд, підтип, вага на етикетці, колір, вага порожньої котушки, дата придбання, діаметр, ціна/кг, примітка, категорія, поріг low-stock, додаткові кольори, візуальний ефект, місце зберігання.

Кожне позначене поле префілиться лише коли вибрані котушки вже мають спільне значення (інакше показує *«— різні —»*); **записуються тільки позначені поля**, решта лишається як було, а **використана вага й RFID-tag не чіпаються**. Інпути дзеркалять одиничну форму — preset / ефект / діаметр / порожня котушка / місце зберігання це дропдауни; матеріал / бренд / підтип автокомпліт з усього, що знає система (slicer-пресети + колор-каталог + built-ins, не лише з вибраних); список кольорів — з колор-каталогу, відфільтрований за брендом + матеріалом, що застосовуються, і оновлюється при їх зміні.

### Імпорт / експорт CSV

Дві кнопки в хедері інвентарю переносять цілі списки котушок туди-сюди як CSV — зручно для backup-у інвентарю, редагування в таблиці або bulk-завантаження свіжо-прибулого замовлення.

- **Export** скачує date-stamped файл `bamdude_inventory_YYYYMMDD.csv`, один рядок на активну котушку.
- **Import** bulk-додає котушки з CSV. Замість того щоб писати одразу, він спершу показує **preview-таблицю**, що позначає кожен рядок як *valid*, *error* або *skipped* — і флагує рядки, де колір авто-заповнився з колор-каталогу, або де вже існує збіжна котушка — **до того, як щось запишеться**. Клік підтвердження потім зберігає лише valid-рядки.

CSV-заголовки толерантні до регістру й пробілів, тож колонка з назвою `Label Weight`, `label_weight` чи `LABELWEIGHT` резолвиться однаково. Обов'язковий лише `material`; решта колонок опційні, і до кожного рядка застосовується та сама валідація, що й у ручній формі додавання котушки.

Імпорт/експорт CSV — **тільки для локального інвентарю**. У **режимі Spoolman** обидві кнопки вимкнені, з підказкою, що вказує на власні CSV-інструменти Spoolman.

### Каталог локацій зберігання {#storage-locations-catalog}

Де котушка фізично лежить — полиця, шухляда чи dry-box — це **керований каталог**, а не вільний текст. Кнопка **Locations** у шапці інвентарю відкриває менеджер каталогу, де ти створюєш, перейменовуєш і видаляєш локації; поле **Storage location** у формі котушки — це дропдаун із цього каталогу, з inline-опцією *create new*, тож не треба виходити з форми, щоб додати полицю.

- **Перейменування пропагується** — перейменування локації одним записом оновлює кожну прив'язану до неї котушку, тож нема осиротілого free-text дрейфу.
- **Видалення захищене** — локацію з усе ще прив'язаними котушками не можна видалити, доки не перенесеш ці котушки в іншу.
- **Legacy free-text мігрує** — на першому запуску після оновлення BamDude бекфілить каталог з унікальних free-text storage-значень, що вже є на котушках, і лінкує кожну котушку з її каталог-рядком.
- **Синк зі Spoolman** — у режимі Spoolman каталог імпортує унікальні локації Spoolman, а перейменування каскадиться на per-spool поле `location` у Spoolman (з локальним відкатом, якщо Spoolman відхилить, тож двоє ніколи не розходяться).

Перегляд каталогу потребує `inventory:read`; створення / перейменування / видалення локації потребує `inventory:update`.

### Дропдаун Slicer Preset показує всі per-printer / per-nozzle варіанти

Поле Slicer Preset у формі котушки тепер перелічує всі імпортовані варіанти окремо — тож усі P1S / X1C / A1 варіанти "Bambu PLA Basic" відображаються як окремі рядки з повним `@printer`-суфіксом, замість того щоб згортатися в один. Сама котушка printer-agnostic — обраний варіант записується як `slicer_filament` і нормалізується через `normalize_slicer_filament` під час слайсингу. (AMS Slot — per-printer і фільтрує; форма котушки — union-of-all і не фільтрує.) Локальні профілі, імпортовані з OrcaSlicer / BambuStudio, показуються поряд з cloud-пресетами — раніше локальні профілі ховались, як тільки користувач залогінювався в Bambu Cloud, що було багом.

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

Material-dropdown поставляється з baseline-набором — PLA, PETG, ABS, TPU, ASA, PC, PA, PVA, HIPS — плюс carbon-fibre, glass-fibre і specialty-варіанти (PLA-CF/GF, PLA Aero, PETG-CF, ABS/ASA-GF, ASA-CF, PCTG, PAHT-CF, PA6-CF/GF, PPS/PPS-CF/GF), згруповані за material-family. Якщо твого матеріалу все ще немає (напр. PHA, PP, PVDF) — введи його напряму в Material-поле, у дропдауні з'явиться опція *Use custom material: …* унизу. Клік — commit.

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

!!! note "Вимкни тихе створення для невідомих тегів"
    Авто-створення свіжого рядка для нерозпізнаного RFID керується через **Settings → Filament → Auto-add unknown RFID spools** (`auto_add_unknown_rfid`, за замовчуванням **on**). Вимкни його — і невідомий тег натомість покаже **картку підтвердження** з матеріалом і кольором, префіленими з AMS-читання, тож нічого не запишеться в інвентар, доки ти не підтвердиш. Зручно, якщо ти створюєш котушки вручну наперед і не хочеш дублікатів.

!!! tip "Знайти котушку за її тегом"
    NFC-інтеграції можуть знайти одну котушку, не листаючи весь інвентар: `GET /api/v1/inventory/spools/by-tag?tray_uuid=<uuid>` (або `&tag_uid=<uid>`). Матчинг hex-нормалізований і case-insensitive; архівні котушки виключені, доки не передаси `include_archived=true`. Читається з `inventory:read` АБО `inventory:update`, тож Manage-Inventory API-ключ може дедупити скан без глобального read-scope.

### Стабільні assignments на startup-і

Spool-assignments зберігаються через рестарти BamDude за **spool ID**, не за slot ID. Якщо AMS реконнектиться в іншому порядку при boot-і — RFID slot 3 приземлиться там, де був slot 1 минулої сесії, тощо — BamDude відновлює за RFID-identifier-ом, тож правильна котушка лишається прив'язана до правильного фізичного tray, без ручного фіксу. Якщо та сама котушка все ще в тому самому фізичному слоті (verified by RFID) — reconfigure-команда принтеру не відсилається.

### Configure AMS Slot vs Assign Spool

Ці дві дії виглядають сусідніми в slot-меню, але роблять різне. Дивись таблицю нижче, коли вагаєшся:

| Дія | Що змінює | Lifetime | Коли використовувати |
|---|---|---|---|
| **Configure Slot** | Каже **принтеру**, який filament-profile (температури, flow, pressure advance) використовувати для того фізичного слота | До reconfigure або поки RFID не overwrite-не | "Я щойно завантажив third-party PETG у slot 1 — set profile, щоб принтер використовував правильні temps." |
| **Assign Spool** | Каже **BamDude**, який inventory-рядок білити за consumption з того слота — і **також** запускає Configure Slot з spool's filament-profile, color, K-profile | До reassign-у або поки AMS не задетектить інший RFID | "Трекати, яка фізична котушка в якому слоті, тож usage / cost білиться правильно." Працює і на empty, і на configured слотах. |

Assigning spool — найпростіший workflow — він обробляє tracking + printer configuration в один крок. Використовуй Configure Slot напряму лише коли хочеш override settings або налаштувати слот без inventory-котушки.

### Прогноз запасів + логістична панель

Третя вкладка інвентарю поряд із **Таблиця** / **Картки** — перетворює сирий `spool_usage_history` у систему прийняття рішень про повторне замовлення:

- **Темп витрати на день** — експоненційно зважена середня з періодом напіввитрати 30 днів, рахується на **групу кольору** (матеріал / підтип / бренд / назва кольору). П'ять кольорів одного PLA Basic стають п'ятьма незалежними forecast-рядками, кожен зі своїм запасом і датою замовлення — тож нестача чорного не ховається за повною котушкою білого. Одна котушка зі свіжих друків важить більше, ніж річний сплеск.
- **Прогноз днів, що лишились** — поточний запас ділимо на темп з урахуванням 95%-довірчого запасу безпеки (`σ × √термін × 1.65`).
- **Дата повторного замовлення** — коли ставити замовлення, щоб нова котушка прибула *до* того, як ти закінчиш поточну, з урахуванням налаштованого терміну постачання.
- **Фільтри + лічильник** — дропдауни **Material** і **Brand** звужують таблицю; окрема колонка **Spools** показує, скільки фізичних котушок стоїть за кожним рядком кольору. Кожна колонка сортовна.
- **Розгортувані редактори кольору** — lead-time-days, запас безпеки (подвійна одиниця — дні чи грами), перемикач сповіщень-снуз. Кожне налаштування зберігається у таблиці `filament_sku_settings`; кольори без налаштувань падають до глобального floor-у (**Налаштування → Інвентар → Глобальний термін постачання**). Оверрайди, збережені до розділення по кольору, переносяться на відповідні рядки кольору при першому завантаженні, тож жоден per-SKU tuning не губиться в міграції.
- **Топ-5 діаграма** — stacked-area, multi-series прогноз п'яти найшвидших кольорів з пунктирними ROP-лініями. Перемикач періоду: 1Т / 1М / 6М.
- **Список покупок (Логістика)** — окрема панель під таблицею прогнозу. Додавай SKU в чергу `pending → purchased → received`. Позначення *received* автоматично створює котушки з `category='Stock'` через bulk-create (використовує середню історичну вагу котушки). CSV-експорт + clear-all.
- **Перемикачі сповіщень** — дві нові події з'являються у провайдерах сповіщень (**Налаштування → Сповіщення → Сповіщення про запаси**): *Час замовляти* (SKU досяг точки повторного замовлення) і *Ризик закінчення* (закінчиться до прибуття поповнення). **Перемикачі наразі лише візуальні** — forecast-панель відображає сповіщення в інтерфейсі; майбутній планувальник зможе викликати їх через існуючі шаблони без зміни схеми.

Forecast-вкладка **прихована в режимі Spoolman**, бо BamDude там проксує список котушок і не наповнює per-print usage history. Щоб користуватися прогнозом, запусти BamDude у режимі локального інвентарю.

Дозволи: `inventory:forecast_read` (бачити панель) і `inventory:forecast_write` (змінювати налаштування SKU + список покупок) додаються до існуючих груп автоматично при оновленні — Viewer отримує read, Operator — обидва.

### Pre-load assignment (зважив-призначив до завантаження)

Можна призначити котушку у слот **до того, як** завантажиш філамент — зручно, коли щойно зважив свіжу котушку і хочеш трекати її з першого ж друку. Коли цільовий слот порожній (`tray_type` blank в AMS-data), BamDude:

- Одразу зберігає рядок `SpoolAssignment`, тож inventory-сторінка показує pairing.
- **Відкладає** публікацію `ams_filament_setting` + `extrusion_cali_sel` через MQTT — firmware Bambu тихо відкидає обидві команди для незавантажених слотів (немає filament-context, до якого міг би прив'язатися K-profile / pressure-advance index), і слати їх все одно означало б закрити модалку фальшивим «Призначено!» поки слайсер далі показує дефолтний PLA назавжди.
- Показує це в підтверджувальному тості: *«Котушку призначено. Слот налаштується, коли ви вставите філамент.»*
- Автоматично повторно надсилає повну конфігурацію в момент, коли слот стає завантаженим. «Завантажено»-сигнал — це AMS state-код (`state == 11`, «філамент подано в екструдер»), а не material-string з tray-data — тож сторонні котушки без читабельного RFID (які репортять state=11 але тримають `tray_type=""`) теж тригерять replay. Після replay-у assignment-fingerprint штампується, тож наступні AMS-пуші не re-firать.

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

### Reset counter

Кожна котушка має дію-ластик — **Reset counter** — що обнуляє відображуваний лічильник **Total Consumed** (варіант reset-all скидає лічильник усіх котушок одразу). Кнопка, її confirmation-діалоги й tooltip-и — усі читають «Reset counter». Важливо: це обнуляє лише *відображувану* цифру витрати — залишок ваги котушки при цьому **не** змінюється (стара назва «Reset usage» оманливо натякала, ніби вона стирає використані грами). Механічно це записує `weight_used_baseline`, тож звітована витрата стає «використано від останнього скидання», а не за весь час — корисно, коли ти доливаєш чи міняєш рулон, але лишаєш той самий inventory-запис замість створення нового.

Backing API endpoints перейменовані відповідно — per-spool і reset-all шляхи тепер закінчуються на `.../reset-consumed-counter` (раніше `.../reset-usage`).

### Видалення записів витрати

Кожен рядок у **Історії використання** котушки має **×** при наведенні, щоб видалити саме цей запис; кнопка **Clear** робить те саме для всього списку. Видалення запису трактує ту витрату так, ніби її не було: його вага **повертається до котушки** (`weight_used` зменшується, тож залишок росте), і та сама величина віднімається від облікованого пластику привʼязаного друку, тож сторінка [Stats](stats.uk.md) лишається синхронною з інвенторі. Для мультиколірного друку віднімання — поелементне: видалення запису одного кольору повертає лише його частку й лишає решту друку без змін. Зручно, щоб «не рахувати» помилковий чи тестовий друк проти рулону.

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

### Прозорий / clear пластик

Прозорий пластик — це first-class колір. Редактор кольору котушки має окремий quick-swatch **Clear**, а hex-поле приймає 8-значне значення `RRGGBBAA`, тож ти можеш позначити котушку як повністю чи частково прозору. Clear-котушки малюються як **шахова дошка** (checkerboard) swatch скрізь, де зʼявляється колір — картки інвентаря, AMS-індикатори слотів, colour-picker — замість того, щоб показуватись як невидимий або суцільно-чорний чіп.

## :material-printer: Друкові PDF-наліпки

Знайти конкретну котушку у шафі з 50 залишками — наклей на кожну наліпку. У хедері Inventory є кнопка **Друк наліпок…**, що відкриває multi-select picker, попередньо заповнений котушками за поточним фільтром. Кожна картка інвентарю та рядок таблиці теж має per-spool printer-іконку для one-shot друку наліпки.

Шість готових шаблонів:

| Шаблон | Розмір | Аркуш | Примітки |
|---|---|---|---|
| **AMS holder (74 × 33)** | 74 × 33 мм | По одній на сторінку | `ams_holder_74x33`. Підходить для популярних Makerworld AMS Filament Label Holder вставок. Достатньо великий для повного layout-у — swatch ліворуч, QR праворуч, багаторядковий текст посередині (бренд, матеріал, hex, spool ID). |
| **AMS holder (75 × 55)** | 75 × 55 мм | По одній на сторінку | `ams_holder_75x55`. Вищий варіант AMS-holder; той самий повний layout (swatch + QR + багаторядковий текст) з більшим запасом по висоті. |
| **Box 40 × 30** | 40 × 30 мм | По одній на сторінку | Типовий розмір рулону DK / Brother; влучає між AMS holder і 62×29 box label. Достатньо місця для swatch + QR + повної текстової колонки з hex-кодом — добре під наліпки на пакети філаменту й коробки зберігання. |
| **Box label** | 62 × 29 мм | По одній на сторінку | Розмір під Brother PT/QL та Dymo small-label stock. Несе QR + storage location. |
| **Avery L7160** | 38.1 × 63.5 мм | A4, 21 на аркуш | Європейський формат. Несе QR. |
| **Avery 5160** | 25.4 × 66.7 мм | US Letter, 30 на аркуш | Американський формат. Несе QR. |

Кожна наліпка має кольоровий swatch (з multi-color смугами для котушок з `extra_colors`), бренд **жирним** зверху, щоб читалось з відстані, матеріал/subtype, **hex-код** кольору (`#RRGGBB`, без альфи, uppercase) — щоб біля-ідентичні комбінації колір+матеріал було видно зблизька, відображувану назву котушки, **spool ID** як killer-поле для розрізнення 8 котушок "PLA White" одна від одної, і (де розмір дозволяє) QR-код, що deep-лінкує на `/inventory?spool=<id>` — скан з телефона стрибає прямо в BamDude на рядок цієї котушки.

### Назва на наліпці слідує шаблону

Жирний центральний рядок на наліпці використовує той самий **шаблон відображувальної назви котушки**, що й сама сторінка Inventory (Settings → Inventory → Spool display name template). Тож якщо ти задав шаблон `{brand} {material} {color_name} (#{id})` для списку — саме це й буде друкуватися на кожній наліпці. 16 placeholder-ів (`{brand}`, `{material}`, `{color_name}`, `{remaining_pct}`, `{filament_diameter}`, `{lot}`, …) задокументовані в тій самій Settings-панелі, де редагується шаблон.

### Як резолвиться QR-deeplink

QR кодує `<base>/inventory?spool=<id>`. Base резолвиться в порядку:

1. Налаштування `external_url` (Settings → Server → External URL) — preferred, щоб скан з телефону потрапив на твій публічний URL BamDude, а не на внутрішню адресу.
2. Змінна оточення `APP_URL`.
3. Scheme + host поточного запиту (те, що у браузері в момент експорту).

Для phone-scan workflow задай `external_url` один раз — і кожна наліпка з кожного шаблону друкуватиме правильний deeplink.

### UX picker-а для великих бібліотек

Modal масштабується для великого інвентарю:

- **Пошук** — substring по composed display name + бренд + `#ID`.
- **Material filter chips** — виводяться з видимих котушок.
- **Обрати всі видимі / Зняти видимі / Скинути все** — selections survive при зміні фільтра (additive), тож можна звузити до "PLA only", обрати всі, потім звузити до "PETG", і додати ще.
- **Перемикач сортування (By ID / By colour)** — *By ID* (default) перелічує котушки за зростанням ID; *By colour* hue-кластеризує їх (хроматичні кольори за hue, ахроматичні нейтралі за світлістю в хвості веселки), тож надрукований аркуш виходить упорядкованим за веселкою. Лише на сесію — скидається до By ID при кожному відкритті picker-а.

### Server-side rendering

PDF-и рендеряться на сервері через ReportLab + qrcode (додані як deps). Чистий Python, без headless-браузера, output байт-ідентичний у всіх браузерах, аркуші Avery вирівнюються до <0.1 мм. Endpoints (обидва gated на `inventory:read`):

- `POST /inventory/labels` — local-DB котушки.
- `POST /spoolman/labels` — Spoolman-backed котушки (тільки якщо Spoolman-інтеграція ввімкнена).

Обидва приймають `{spools: [{id, display_name?}], template}` і повертають `application/pdf` через streaming response. Cap — 500 котушок на запит.

## :material-account-multiple: Дозволи

| Permission | Ефект |
|---|---|
| `inventory:read` | Переглянути список котушок і AMS-призначення; **рендерити PDF-наліпки**. |
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
