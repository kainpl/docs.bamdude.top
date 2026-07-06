---
title: Інвентар філаменту та Spoolman
description: Вбудований інвентар котушок BamDude плюс опціональна двостороння синхронізація з self-hosted Spoolman
---

# Інвентар філаменту та Spoolman

BamDude постачається з **повноцінним інвентарем філаменту** (Налаштування → Філаменти). Це джерело істини для ваги котушок, RFID, локації та вартості — жодного зовнішнього сервісу не потрібно. Якщо ви вже використовуєте [Spoolman](https://github.com/Donkie/Spoolman), опціональний шар синхронізації тримає обидві системи в актуальному стані; якщо ні — BamDude робить усе сам.

!!! tip "Spoolman не обов'язковий"
    Вбудований інтентар повністю працює standalone. Синхронізація зі Spoolman — це суто інтеграційний вибір для тих, хто вже централізує котушки в кількох інструментах (наприклад, OctoPrint, Mainsail, Klipper, кілька slicer-хостів). Обирайте те, що підходить вашому workflow.

=== ":material-package-variant: Вбудований інвентар"

    BamDude-native — без зовнішніх сервісів, без мережевих round-trip-ів, кожна колонка лежить у `data/bamdude.db`.

=== ":material-sync: Синхронізація зі Spoolman"

    Add-on інтеграція з self-hosted сервером Spoolman. Двостороння, з тонким налаштуванням по концернах (вага vs локація vs звіт про часткове використання).

---

## :material-package-variant: Вбудований інвентар

Відкрийте **Налаштування → Філаменти**. Кожен рядок — фізична котушка: додана вручну, імпортована за RFID або автоматично створена при скануванні AMS.

### :material-plus-box: Додавання котушок

Форма "Add Spool" покриває все, що BamDude трекає по котушці:

| Поле | Примітки |
|------|----------|
| `brand` | Вільний текст (наприклад, `Polymaker`, `Bambu Lab`, `SUNLU`). |
| `material` | `PLA`, `PETG`, `ABS`, `TPU`, `PA`, `PC`, `PVA`, `ASA`, … |
| `subtype` | `Basic`, `Matte`, `Silk`, `CF`, `Tough`, … |
| `color_name` + hex | Вільнотекстова назва кольору + `#RRGGBBAA` зразок. Hex-input нормалізується на кожен keystroke — вставте `#FFAA00` і BamDude доповнить його до `FFAA00FF`. |
| `purchase_date` | Коли ви її реально купили. Відрізняється від `created_at` (коли рядок було імпортовано). Колонка "Added" віддає перевагу цьому полю, якщо воно задане. |
| `filament_diameter` | `1.75` або `2.85`. За замовчуванням `1.75`. |
| `label_weight_g` | Заявлена нетто-вага на етикетці (за замовчуванням 1000 г). |
| `core_weight` | Вага порожньої котушки, використовується для розрахунку залишку через ваги. Підтягується з каталогу при збігу brand+spool. |
| `lot` | 1-based позиція всередині закупки. Шлях масового додавання може автонумерувати `1..N` server-side через checkbox **auto-increment lots**. |
| `cost_per_kg` | Просто число, без знака валюти. Множиться на вагу друку для поля cost в архіві. |
| `note` | Вільнотекстова нотатка (`Kuhonna polychnia`, `Відкрита 12 квіт`, …). |
| `tag_uid` / `tray_uuid` | RFID-ідентифікатори. Порожні для котушок, доданих вручну — прив'яжіть тег пізніше через matcher. |

Масове додавання приймає кількість і створює N рядків за раз — комбінуйте з **auto-increment lots**, щоб пронумерувати пакет з 5 котушок як `lot 1..5` без ручного набору кожної.

### :material-format-text: Шаблон display-name котушки

Сторінка Філаменти синтезує людський лейбл по котушці через user-configurable шаблон — пошук і сортування використовують той самий рядок. Редагуйте під **Налаштування → Система → Spool Display Template**.

За замовчуванням: `{brand} {material} {color_name}` (рендериться як, наприклад, `Polymaker PLA Jade White`).

| Токен | Джерело | Приклад |
|-------|---------|---------|
| `{brand}` | колонка | `Polymaker` |
| `{material}` | колонка | `PLA` |
| `{subtype}` | колонка | `Matte` |
| `{color_name}` | колонка | `Jade White` |
| `{slicer_filament_name}` | колонка | `Polymaker PolyTerra PLA @Bambu Lab X1C` |
| `{note}` | колонка | `Kuhonna polychnia` |
| `{label_weight_g}` | колонка | `1000` |
| `{label_weight_kg}` | обчислене | `1` (round) або `0.75` (дробове) |
| `{remaining_g}` | обчислене `label − used` | `750` |
| `{remaining_kg}` | обчислене | `0.75` |
| `{remaining_pct}` | обчислене | `75%` |
| `{color_hex}` | обчислене з `rgba` | `#FF3300` |
| `{cost_per_kg}` | колонка | `25` |
| `{purchase_date}` | колонка | `2026-04-15` |
| `{filament_diameter}` | колонка | `1.75` |
| `{lot}` | колонка | `3` |

!!! tip "Невідомі токени залишаються verbatim"
    Зробите друкарську помилку типу `{brnd}` — live-preview залишить її як є. Це одразу показує помилку, замість того, щоб тихо схлопнутися в порожній проміжок.

### :material-view-column: Видимість колонок

Натисніть **Column Config** на сторінці Філаменти, щоб перемкнути, які колонки видимі і в якому порядку. Налаштування — per-user.

**Видимі за замовчуванням:** `brand`, `material`, `color_name`, `remaining`, `location`, `note`, `purchase_date`.
**Приховані за замовчуванням:** `created_at` ("added time" — витіснений `purchase_date`).

Свіжододані колонки лягають на свою дефолтну позицію, а не в кінець, щоб після оновлення існуючі юзери не мусили переставляти.

### :material-magnify-scan: Auto-assign по RFID

У хедері сторінки Філаменти є дія **Auto-assign**: BamDude сканує всі AMS-слоти підключених принтерів, матчить `tag_uid` / `tray_uuid` кожного слота з рядками інвентаря і масово створює записи `SpoolAssignment`. Корисно після перезавантаження кількох котушок — один клік, без ручного підбору.

### :material-link-plus: Прив'язка невідомого RFID до ручної котушки

Коли на принтері з'являється невідомий RFID-тег, popover слота AMS пропонує прив'язати його до існуючого рядка інвентаря, у якого ще немає тега. Use case: сторонні бренди без RFID, заправлені core-и або котушка, яку ви купили до того, як почали користуватися BamDude. Виберіть рядок, підтвердіть — тег прикріплено, наступне сканування авторезолвиться.

---

## :material-sync: Синхронізація зі Spoolman

Опціонально. Підключіть BamDude до інстансу [Spoolman](https://github.com/Donkie/Spoolman) — і дві системи дзеркалитимуть одна одну.

### :material-spool: Що таке Spoolman?

[Spoolman](https://github.com/Donkie/Spoolman) — це open-source self-hosted менеджер інвентарю філаменту для 3D-друку. Він живе як окремий сервіс (Docker, bare metal або Spoolman-сумісний хмарний інстанс) і експонує REST API для трекінгу котушок, історії використання, vendor/material таксономії, low-stock-alert-ів і — найважливіше для multi-tool сетапів — є єдиним джерелом правди, проти якого можуть синкатися інші інструменти (OctoPrint, Mainsail, Klipper, кілька slicer-хостів).

Якщо у тебе тільки BamDude, вбудований інвентар вище вже робить усе, що робить Spoolman. Інтеграція — для тих, хто **вже** має Spoolman через якийсь інший хост у своєму сетапі.

### :material-link: Підключення

1. **Налаштування** → **Інтеграції** → **Spoolman**
2. Задайте **URL** (наприклад, `http://192.168.1.50:7912` або docker-compose service alias типу `http://spoolman:7912`)
3. (Опційно) **API Key** — потрібен лише якщо твій Spoolman за авторизацією; для дефолтного відкритого сетапу залиш пустим.
4. **Test Connection**
5. **Save**

!!! tip "Доступність по мережі"
    BamDude має змогу досягти Spoolman URL зсередини власного процесу. На docker-compose тримайте обидва сервіси в одній мережі і використовуйте service alias; на bare metal достатньо LAN-хостнейму або статичного IP.

### :material-tune: Контроль синхронізації

| Налаштування | Ефект |
|--------------|-------|
| `spoolman_enabled` | Master switch. |
| `spoolman_sync_mode` | `auto` (пушити кожну зміну AMS одразу) або `manual` (чекати explicit натискання Sync). |
| `spoolman_disable_weight_sync` | Скіпати оновлення `remaining_weight` на існуючих spool-ах Spoolman — пушити лише локацію. Використовуйте, якщо Spoolman — ваш authoritative weight tracker (його гранулярний звіт з'їдає AMS-оцінки). |
| `spoolman_report_partial_usage` | Коли друк падає або скасовується, звітувати **орієнтовну кількість грамів, використаних до точки переривання**, на основі прогресу по шарах, замість того щоб скидати всю оцінку. Допомагає Spoolman тримати точну вагу після фейлів. |

### :material-sync-circle: Що синхронізується

- **Слот AMS ↔ Spoolman spool** — кожен заряджений слот мапиться на Spoolman spool ID. Матеріал, бренд, колір і (якщо `disable_weight_sync` не увімкнено) залишок ваги тримаються в курсі один одного.
- **Споживання друку** — кожен завершений друк звітує грами в Spoolman як usage event. Скасовані / провалені друки поважають `spoolman_report_partial_usage`.
- **Локація** — BamDude пише ім'я принтера + AMS-координати у поле `location` Spoolman (`H2D-1 AMS-A Slot 3` тощо). Завжди синхронізується, навіть якщо синхронізацію ваги вимкнуто.
- **RFID** — Bambu Lab tray UUID-и пробрасуються в поле tag Spoolman.

### :material-link-off: Відв'язка

У режимі `manual` кожна картка Bambu spool показує кнопку **Unlink** — корисно, коли треба перевести котушку зі Spoolman назад у BamDude-only інвентар, не ламаючи призначення в AMS.

### :material-poll: Результати синхронізації

Після кожного синку (auto чи manual) BamDude показує панель результатів:

- **Synced count** — скільки котушок успішно синхронізовано.
- **Skipped spools** — список котушок, які не змогли синкатися, з причиною per-row (наприклад, "Non-Bambu Lab spool", "No matching material in Spoolman", "Manual unlink in effect"). Кожен скіпнутий ряд показує локацію, кольоровий swatch і текст причини.
- **Errors** — будь-які HTTP / network / data помилки під час запуску.

!!! note "Детекція Bambu Lab RFID"
    Auto-sync фаєриться лише для **офіційних Bambu Lab котушок з RFID** — third-party, refilled, SpoolEase скіпаються спеціально, щоб не плодити фейкові ряди в Spoolman. Bambu Lab котушки ідентифікуються за hardware-ідентифікаторами (`tray_uuid` і `tag_uid`), не за іменем filament-preset. Не-Bambu котушки можна **manually link** (див. нижче).

### :material-chart-line: Трекінг використання

Кожен завершений друк звітує per-filament споживання у Spoolman як usage event:

1. BamDude дістає per-filament дані використання з архівованого 3MF-файлу (slicer estimates).
2. Для часткових друків (фейли, скасування) per-layer G-code-аналіз дає точне споживання до точно того шару, де друк впав.
3. На завершенні кожна котушка звітується індивідуально — multi-material-друк оновлює кожну прив'язану котушку окремо.
4. **Fallback за AMS remain-% для слотів, які 3MF не покрив.** Коли для слота немає 3MF-оцінки — no-3MF "Untitled" друк (`.gcode.3mf` не завантажився, тож архів це fallback-рядок) **або** часткове покриття 3MF, де завантажений слот не був у slice-info — BamDude падає на per-slot просадку залишкового відсотка AMS. На завершенні він пише `(remain% на старті − remain% в кінці) × референсну вагу філаменту котушки в Spoolman` грамів як usage event. Він бере референсну вагу Spoolman (а не ненадійну tray-вагу з AMS) і **пропускає будь-який слот, свопнутий посеред друку** (змінився tray UUID), бо не може розділити споживання між двома котушками. До цього no-3MF "Untitled" друки звітували нульову зміну ваги в Spoolman.

Це збігається з BamDude-моделлю per-spool — ті самі цифри, що годують сторінку Stats, годують і Spoolman, просто маршрутно через usage-history таблицю Spoolman поверх локального архіву BamDude.

### :material-tray-full: AMS-слот мапінг (hover-картка)

Наведи на будь-який AMS-слот на сторінці Printers і побачиш:

| Поле | Джерело |
|------|---------|
| **Vendor** | Bambu Lab або Generic — читається з RFID-тега. |
| **Profile** | Тип і subtype філаменту (`PLA Basic`, `PETG Translucent`, …). |
| **Color** | Назва кольору + swatch — резолвиться через color-каталог BamDude (єдине джерело правди). |
| **K Factor** | Pressure-advance значення активне для цього слота. |
| **Fill Level** | Залишок у відсотках, з візуальним bar'ом. |
| **Spool ID** | Прив'язаний Spoolman spool ID (тільки коли Spoolman увімкнено і слот прив'язаний). |

#### Fill Level для AMS Lite / зовнішніх котушок

AMS Lite (наприклад, A1 серія) **не має сенсора ваги** і завжди звітує 0% fill level. Коли котушка прив'язана до Spoolman і там є weight-дані, BamDude використовує remaining-вагу зі Spoolman:

- **AMS з ваговим сенсором** — використовує AMS-відсоток напряму (без змін).
- **AMS Lite (звітує 0%)** — fallback на Spoolman: `(remaining_weight / filament_weight) × 100`.
- **External spool** — показує fill з Spoolman, якщо прив'язано (інакше `—`).

Коли джерело — Spoolman, hover-картка показує "(Spoolman)" поряд з відсотком, щоб видно було, звідки число.

### :material-link: Кнопки Open / Link / Manual link

Кожна hover-картка слота має основну кнопку, label якої залежить від стану прив'язки:

| Стан | Кнопка | Що робить |
|------|--------|-----------|
| **Linked** | **Open in Spoolman** | Відкриває сторінку котушки в Spoolman у новій вкладці — редагуй vendor, cost, нотатки, вагу прямо там. |
| **Unlinked, Bambu Lab spool, є кандидати** | **Link to Spoolman** | Відкриває picker з усіма unlinked Spoolman-котушками — обери, натисни **Link** для підтвердження. |
| **Unlinked, Bambu Lab spool, нема кандидатів** | **Link to Spoolman** (disabled) | Зараз нема unlinked-котушок у Spoolman — додай у Spoolman спочатку. |
| **Не-Bambu Lab котушка** | **Manual Link** | Вручну прив'язати слот до Spoolman-котушки — обходить RFID-матчинг для refilled-core-ів і third-party. |

Для **unlink**: відкрий котушку в Spoolman, очисти поле `extra.tag`.

### :material-database: Додавання котушок — AMS vs Inventory view

| Поверхня | Дія | Коли використовувати |
|----------|-----|----------------------|
| **З hover AMS** | **Add to Spoolman** коли невідомий філамент з'являється у слоті | First-time onboarding, додати свіжо завантажену Bambu-котушку до Spoolman. |
| **У Spoolman напряму** | Add Spool на web UI Spoolman | Bulk-import історичних котушок, додавання котушок, які ще не завантажував, vendor/cost data entry. |
| **Inventory view** (BamDude) | Додавання через Settings → Filaments | Коли хочеш, щоб котушка жила в інвентарі BamDude незалежно від стану Spoolman — корисно для full-detail рядів, які Spoolman не трекає (lot number, custom notes). |

Обидва backend-и співіснують; прив'язка це те, що дозволяє AMS-hover-картці резолвити слот до Spoolman-ряду.

### :material-robot: Автофічі

Три незалежні automation-тумблери (Settings → Spoolman):

- **Auto-sync on print complete** — кожен завершений друк звітує per-filament usage індивідуально у Spoolman, тож spool-quantities оновлюються автоматично.
- **Auto-detect on AMS change** — коли AMS-філамент змінюється, BamDude детектує нову конфігурацію, матчить проти Spoolman і оновлює slot mapping без втручання.
- **Auto-clear location on removal** — коли котушку прибирають з AMS, BamDude детектує порожній слот, знаходить Spoolman-котушки з відповідним рядком локації і чистить поле `location`. Котушка тепер доступна іншим принтерам.

!!! info "Формат локації"
    Spoolman-локації слідують формату `Printer Name - AMS X Slot Y`, наприклад `H2D-Workshop - AMS A Slot 3`.

### :material-server-network: Multi-printer синк

Один інстанс Spoolman обслуговує кілька BamDude-принтерів (та інші тулзи) одночасно:

- Кожен AMS принтера синкається незалежно.
- Різні котушки на принтер, окремий usage-tracking.
- Уніфікований інвентар у Spoolman — одне джерело правди по всій фермі.

Це головна причина, чому більшість farm-операторів обирають крутити Spoolman поряд з BamDude навіть коли built-in інвентар працює standalone — Spoolman це cross-tool хаб.

---

## :material-table-cog: Інвентарний UI (BamDude-сторона, бекенд — Spoolman)

Коли BamDude підключений до Spoolman, **сторінка інвентарю** (`/inventory`) і **сторінка принтерів** (`/`) розгортаються у повноцінний Spoolman-flow: AMS-присвоєння слотів живе у власних таблицях BamDude (присвоєння переживає рестарт і їде разом з бекапами), K-профайли по котушці їдуть між інсталами BamDude, що ділять один Spoolman-бекенд, а вільне сторадж-полe лежить біля кожної котушки. Базується на upstream Bambuddy [#1241](https://github.com/maziggy/bambuddy/pull/1241), портовано в BamDude **0.4.4**.

### :material-table-row: Три нові шари стану

| Де | Що | Чому не на стороні Spoolman |
|----|-----|-----------------------------|
| `spoolman_slot_assignments` (БД BamDude) | Який Spoolman spool ID живе в `(printer_id, ams_id, tray_id)`. AMS 0..7 + 255 (зовнішня подача). Один spool на слот. | Власне `location` у Spoolman — це вільний текст; використовувати його як джерело істини для "котушка зараз у слоті 3 AMS A принтера X" втрачає структуру (наприклад, не можна відфільтрувати "усі котушки, зараз завантажені"). Структурна таблиця піддається query і автоматично очищається коли слот спорожнів. |
| `spoolman_k_profile` (БД BamDude) | Pressure-advance + setting_id по `(spoolman_spool_id, printer_id, extruder, nozzle_diameter)`. Один + два екструдери. | K-профайл прив'язаний до фізичного філамент ↔ фізичний принтер + сопло, не лише до Spoolman-рядка. Зберігання на BamDude-стороні значить, що повторне тапання тієї самої Bambu RFID на іншому принтері не втратить калібрування, зроблене в іншому місці. |
| `spool.storage_location` (колонка БД BamDude) | Вільний текст типу `Drybox 3`, `Полиця A4`, `Цех / шафа 2`. | Дзеркалить Spoolman-полe `location`, але живе теж BamDude-сторінкою — щоб поле відображалось у колонках сторінки інвентарю + у формі котушки навіть на Spoolman-mode інсталах. |

Spoolman-полe `location` лишається недоторканим зі сторони Spoolman — оператори далі можуть заповнювати його з власного UI Spoolman як вільний текстовий лейбл. Структурна таблиця присвоєнь BamDude — джерело істини для "що зараз у принтері X".

### :material-printer: Сторінка принтерів — Spoolman-mode інтеграція слотів

Кожен тип слота на сторінці принтерів читає Spoolman-стан коли Spoolman-mode увімкнений:

- **Звичайні AMS-слоти** (AMS 0..7, лоток 0..3) — fill bar, ім'я пресета, swatch кольору і "Assigned spool" пілюлька в hover-карті — все читається з `spoolman_slot_assignments` приєднаних до `spoolman_inventory/spools`. Коли в слоті немає RFID-прив'язаної котушки, обчислення fill керується рядком присвоєння.
- **HT (high-temperature) слоти** — той самий flow, що й звичайні AMS, плюс H2D Ext-R single-tray зовнішній слот.
- **External Spool 254 / 255** — читає з тієї ж таблиці присвоєнь; hover-карта слота показує ім'я призначеної котушки + залишок ваги + сторадж.

На слот hover-карта несе:

| Кнопка | Коли з'являється |
|--------|------------------|
| **Link to Spoolman** | Слот має Bambu RFID-таг, присвоєння ще немає, і є хоч одна непов'язана Spoolman-котушка з `extra.tag`, що співпадає. |
| **Manual Link** | Слот не має RFID-співпадіння (перезаряджена бобіна, third-party). Пікер показує кожну непов'язану Spoolman-котушку. |
| **Assign** | Слот пустий в інвентарі, але оператор хоче вручну вказати Spoolman-котушку (без RFID). |
| **Unassign** | Слот має або Spoolman SlotAssignment, або локальний SpoolAssignment — очищає BamDude-стороннє присвоєння. |
| **Open in Spoolman** | Слот RFID-прив'язаний. Відкриває Spoolman-сторінку котушки в новій вкладці. |

Кнопка Link авто-приховується коли слот уже має або Spoolman SlotAssignment, або локальний SpoolAssignment — щоб оператор не зміг випадково подвійно прив'язати.

### :material-flash: Авто-перепризначення K-профайлу при зміні AMS

Коли вміст AMS-слота змінюється (повторне RFID-тапання, скид слота, slicer-side `extrusion_cali_sel` зі сторони), BamDude підіймає збережений K-профайл присвоєної котушки для точного triplet'у `(printer_id, extruder, nozzle_diameter)`. Якщо живий `cali_idx` принтера відрізняється від збереженого — BamDude перевидає правильний `extrusion_cali_sel` через MQTT, відновлюючи K-значення, яке оператор обрав минулого разу. Без цього прошивка скидала б K на slot index 0 при кожному ре-тапі.

Drift-detection обмежений — BamDude перевидає тільки коли є справжня різниця, тож steady-state push не спамить принтер.

### :material-storage: Колонка Storage location

`Налаштування → Філаменти` (сторінка інвентарю) отримує колонку **Storage location**, що шипається на будь-якому бекенді (локальна БД + Spoolman). Редагування inline по рядку; значення зберігається в `spool.storage_location` і виводиться скрізь, де рендериться котушка (карти, hover-карти, форма, пошук). На Spoolman-mode інсталах поле — BamDude-локальне; власне `location` Spoolman лишається оператору на самостійне ведення, якщо звичніше.

### :material-tag-multiple: Ширша підтримка RFID UID

BamDude розширює `spool.tag_uid` з 16 до 32 символів на Postgres (SQLite VARCHAR-довжину ігнорує). Bambu RFID UID — 16 hex; third-party таги (наприклад, NTAG216 стікери) несуть до 32 hex — ширша колонка дозволяє прив'язувати такі таги до перезаряджених бобін без обрізки.

### :material-api: API-поверхня

Повний Spoolman-inventory шипається під `/api/v1/spoolman/inventory/*` (19 endpoint'ів, усі gate на `RequirePermission(INVENTORY_*)`). Корисне для скриптів:

- `GET /spoolman/inventory/spools` + `GET /spoolman/inventory/spools/{id}` — list / single з BamDude-приєднаннями (slot assignment, storage_location, лічильники K-профайлів).
- `POST /spoolman/inventory/spools` + `POST /spoolman/inventory/spools/bulk` + `PATCH /spoolman/inventory/spools/{id}` — створення / bulk / update.
- `POST /spoolman/inventory/spools/{id}/archive` + `/restore` — soft-delete через Spoolman archive-флаг.
- `POST /spoolman/inventory/slot-assignments` + `DELETE /spoolman/inventory/slot-assignments/{id}` — присвоїти / зняти.
- `GET /spoolman/inventory/slot-assignments` — list-all з даними котушок.
- `POST /spoolman/inventory/spools/{id}/sync-weight` — підтягнути поточну AMS-вагу в рядок котушки.
- `POST /spoolman/inventory/ams-weights/sync` — bulk-sync ваги по всіх присвоєних слотах одним запитом.
- `GET /spoolman/inventory/spools/{id}/k-profiles` + `POST /spoolman/inventory/spools/{id}/k-profiles` — per-spool K-профайл read/save.
- `PATCH /spoolman/inventory/filaments/{id}` — переіменування + propagate `spool_weight` на кожну котушку цього філамента (`keep_existing_spools` обмежує каскад).
- `GET /spoolman/inventory/filaments` + `POST /spoolman/inventory/spools/{id}/link-tag` — пікер-запити.

Повний контракт API: [API Reference → Spoolman Inventory](../reference/api.md).

---

## :material-help-circle: Траблшутинг

**Connection failed**

- Перевір Spoolman URL — відкрий у браузері, щоб переконатися, що сам Spoolman живий.
- Глянь network reachability зсередини контейнера/процесу BamDude до Spoolman (наприклад, `curl http://spoolman:7912/api/v1/info` зсередини контейнера BamDude).
- Якщо у Spoolman увімкнена авторизація — перевір API Key.
- Файервол / Docker network isolation — обидва сервіси мають бути в одній мережі або мати explicit routing.

**Sync not working**

- Підтверди, що `spoolman_enabled` on і **Test Connection** і досі проходить.
- Подивись логи самого Spoolman — нові / старіші версії інколи затягують або змінюють REST-контракт.
- Перевір, що котушка розпізнана як Bambu Lab (auto-sync лише для Bambu RFID — див. вище). Для не-Bambu використовуй **Manual Link**.
- Для multi-printer сетапів — підтверди, що ім'я принтера в BamDude збігається з рядком локації, який Spoolman очікує.

**Wrong spool linked**

- Відкрий котушку в Spoolman, очисти поле `extra.tag` для unlink.
- З hover-картки AMS у BamDude, **Manual Link** → обери правильну Spoolman-котушку.
- Перевір, що RFID-tag UUID збігається з тим, що зберігає Spoolman — mismatched UUID найчастіша причина "linked, але вказує на неправильний ряд".

---

> Початково базується на документації [Bambuddy](https://github.com/maziggy/bambuddy).
