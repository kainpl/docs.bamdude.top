---
title: AMS та вологість
description: Моніторинг систем філаменту AMS, вологості та дистанційна сушка
---

# AMS та моніторинг вологості

BamDude забезпечує комплексний моніторинг ваших блоків AMS (Automatic Material System).

---

## :material-tray-full: Статус слотів AMS

Кожен слот AMS відображає:

- **Колір філаменту** -- візуальний зразок кольору
- **Тип матеріалу** -- PLA, PETG, ABS тощо
- **Залишок** -- орієнтовна кількість філаменту
- **Активний** -- індикатор поточної подачі
- **Номер слота** -- 1-based номер з автоконтрастним текстом

### Повторне зчитування RFID

Оновіть інформацію про філамент для окремих слотів, навівши курсор і натиснувши кнопку меню. Корисно, коли ви замінили котушку, але AMS не виявив зміну.

### Налаштування слота AMS

Ручне налаштування слотів для сторонніх філаментів:

1. Наведіть курсор на слот, натисніть меню
2. Оберіть **Configure Slot**
3. Оберіть пресет філаменту (фільтрується за моделлю принтера)
4. Оберіть відповідний K-профіль
5. За бажанням встановіть власний колір

!!! tip "AMS-HT preset stickiness виправлено (#1053)"
    Раніші збірки кешували пресети слотів AMS-HT під ключем `ams_id * 4 + tray_id = 512`, але frontend підтягує їх по `ams_id` напряму для HT (single-slot блоки шарять глобальний tray id з unit id). Слот падав на generic-пресет (`Generic PLA`) на кожен поллінг, навіть після збереження кастомного пресета — операторам доводилося пере-обирати його після кожної заміни котушки. Backend тепер кешує через той самий helper, що й frontend, і збережений пресет лишається на місці.

### Pre-population для налаштованих слотів

Коли відкриваєш модалку Configure AMS Slot для слота, що вже має конфігурацію, BamDude pre-populate-ить форму, щоб міг переглянути / підтвикнути без старту з нуля:

- **Filament preset** — попередньо-налаштований preset обирається (резолвиться зі збереженого mapping-у або матчингом slot-ового `tray_info_idx` до відповідного preset-у).
- **Колір** — color-picker pre-populate-иться поточним кольором філаменту слота, резолвлячи проти [`color_catalog`](inventory.uk.md#каталог-кольорів).
- **K-profile** — активний pressure-advance profile pre-selected матчингом slot-ового `cali_idx` до доступних [K-profile](kprofiles.uk.md) entries.
- **Auto-scroll** — preset-список авто-скролить до обраного запису, тож він видний без manual-скролу. Для empty-слотів список скролить до останнього використаного preset-у, тож common refills — один клік.

### Підтримка кількох AMS

До 4 блоків AMS на принтер (16 слотів загалом). Зовнішні тримачі котушок підтримуються для принтерів без AMS.

### Призначити котушку з інвентаря

Опція меню AMS-слота **Assign Spool** парує фізичний рядок інвентаря (зі сторінки [Філаменти](spoolman.uk.md)) зі слотом. Picker тепер включає:

- **RFID-detected котушки** — теги Bambu Lab, зчитані на слоті.
- **Manually-added рядки інвентаря без RFID** — заправки, сторонні бренди, untagged-котушки (#1047). Раніші збірки вимагали точну рівність `slicer_filament_name` і ховали кожну котушку, що не несла slicer-profile name; picker тепер також приймає partial-material match (котушка `PLA` показується для слота `PLA Basic` і навпаки).
- **Зовнішні слоти (`amsId 254/255`)** — у них немає RFID-рідера, тож picker показує повний інвентар.

!!! tip "Фільтр за slicer filament name"
    Коли на принтері заряджено 3MF, picker можна фільтрувати за expected slicer filament profile (витягнутого з активного 3MF). Звужує список до котушок, що збігаються з required material друку — знижує шанс випадково призначити неправильну котушку. Перемкніть фільтр off, щоб бачити повний список, з one-line warning, коли матеріал не збігається.

### Load / Unload зі слота

Кермуй **Load** і **Unload** прямо з будь-якого AMS-слота чи external spool — без походу до тачскріна:

1. Hover над слотом на картці принтера.
2. Клік :material-dots-vertical: у hover-меню слота.
3. **Load** — щоб подати tray, **Unload** — щоб витягнути те, що зараз заряджено.

!!! note "Доступність"
    Меню Load / Unload приховане, поки принтер у `RUNNING` — чекай idle.

!!! info "H2D dual-extruder поведінка (Ext-L / Ext-R)"
    H2D має дві external spool позиції — **Ext-L** (подає лівий nozzle) і **Ext-R** (подає правий nozzle). Кожна вантажиться проти actual current температури свого nozzle (як BambuStudio); 215 °C fallback використовується, якщо target nozzle репортує cold або unknown.

!!! warning "Дозвіл"
    Load / Unload потребує `printers:control` — той самий scope, що start / stop / pause / resume.

### Custom AMS-лейбли

Дай AMS-юнітам friendly-імена, щоб розрізняти їх у multi-AMS setup-ах.

1. Hover на AMS-label (напр. `AMS-A`) на картці принтера → з'являється AMS info popover.
2. Popover виставляє:
   - **Serial Number** — hardware-серійник з MQTT.
   - **Firmware Version** — розпарсений з `get_version` принтера.
   - **Friendly Name** — editable text-поле.
3. Введи ім'я (напр. *Silk Colours*, *Workshop AMS*) → **Enter** або клік **Save**. Очисти поле + save, щоб прибрати лейбл.

**Лейбли persist-ять по AMS serial number, не по slot-position** — переміщай AMS між принтерами, лейбл їде з ним. Якщо AMS serial не репортується (старіша firmware) — BamDude падає на `(printer_id, ams_position)` ключ. Custom-лейбли видні в [Inventory](inventory.uk.md) location-колонці, тож знайти котушки на farm-і — один погляд.

Редагування лейблів потребує `printers:update` дозвіл.

---

## :material-cog: Діалог налаштувань AMS

Per-printer діалог, який віддзеркалює **Bambu Studio → AMS Settings**. Натисни :material-cog: «шестеренку» у заголовку секції **Filaments** на картці принтера.

Перемикай ту саму AMS-поведінку, що й Bambu Studio — без виходу з BamDude.

- **Оновлення вставки** — авто-зчитування RFID при вставці нової котушки Bambu Lab (~20 с).
- **Оновлення під час увімкнення** — RFID-re-read при старті принтера (~1 хв, прокручує котушки).
- **Оновлення залишкової ємності** — AMS оцінює, скільки філаменту лишилося на котушках Bambu Lab.
- **Резервне копіювання філаменту в AMS** — авто-перемикання на іншу котушку з тими самими властивостями, коли поточна закінчується.
- **Виявлення друку в повітрі** *(тільки A1 / A1 Mini)* — зупиняє друк при засміченні / зриві щоб не марнувати час і матеріал.
- **Калібрувати AMS** — шле `M620 C<ams_id>` на обраний AMS-юніт. Та сама процедура, що з екрана принтера.
- **Тип AMS** *(тільки A1)* — переключити AMS між **FULL** та **LITE** прошивками. Потребує firmware-update на боці принтера (~30 с). Перед відправкою підтвердження.
- **Порядок AMS** *(сімейство H2D)* — шле `ams_reset` для скидання послідовності ID. Принтер чекає що ти потім фізично переключиш AMS у бажаному порядку.

### Видимість — що відображається залежно від принтера

Кожен рядок gated по тому, що реально підтримує принтер — нема сенсу показувати **Тип AMS** на X1C, або **air-print detection** на P1S. BamDude визначає таблицю можливостей за моделлю; рядки з `false`-capability приховуються повністю.

| Рядок | X1 family | P1 / P2 / X2D | A1 | A1 Mini | H2D family |
|---|---|---|---|---|---|
| Оновлення вставки | так | так | так | — | так |
| Оновлення при увімкненні | так | так | так | — | так |
| Оновлення залишкової ємності | так | так | так | — | так |
| Резервне копіювання філаменту | так | так | так | — | так |
| Виявлення друку в повітрі | — | — | так | так | — |
| Тип AMS (firmware) | — | — | так | — | — |
| Порядок AMS | — | — | — | — | так |
| Калібрувати AMS | при ≥1 AMS, для всіх моделей |

AMS Lite на A1 Mini не має RFID-зчитувача, тому всі чотири RFID-залежні прапори для нього приховані.

### Джерело правди — принтер

BamDude **не** зберігає "desired state" на своєму боці. Стан у діалозі читається з MQTT-push принтера (`print.cfg` hex-bitfield для чотирьох основних прапорів + `print.ams.*` як fallback на старіших прошивках). При тогл-у — BamDude публікує відповідну MQTT-команду (`ams_user_setting` для перших трьох, `print_option` для backup / air-print, `M620 C<id>` для калібрування, `mc_for_ams_firmware_upgrade` для firmware switch, `ams_reset` для reorder) і починає 3-секундний hold, щоб рядок не миготів між optimistic і підтвердженим значенням.

Якщо принтер втратив налаштування (factory reset, firmware-update wipe) — BamDude це відобразить. Reconciliation немає. Відкрий діалог знову і перетогль.

### Дозволи й аудит

Шестеренка з'являється тільки для користувачів з `printers:update`. Той самий дозвіл захищає endpoint `POST /api/v1/printers/{id}/ams/settings`.

Кожна застосована зміна пише рядок у таблицю `ams_setting_audit` — `(printer_id, user_id, action, payload_json, sequence_id, result, error_message, created_at)`. UI-viewer-а поки немає; query напряму, якщо треба відповісти "хто вимкнув RFID auto-read минулого четверга?"

!!! warning "Деструктивні дії"
    **Тип AMS (firmware)** та **Порядок AMS** мають confirm-діалоги, бо це не звичайні тогли — firmware switch форсує ~30-секундний AMS reboot, а reorder скидає поточну послідовність ID (після цього треба фізично переключати юніти). Прочитай confirm-текст перед натисканням.

---

## :material-lan: AMS Discovery + Wiring

BamDude авто-discover-ить AMS юніти, коли принтер підключається — без ручного конфігу. Updates течуть, коли AMS-конфігурація міняється (юніт додано / прибрано / перекабельовано).

### Dual-nozzle wiring (H2D / H2D Pro)

На dual-nozzle принтерах кожен AMS-юніт фізично закабельований або до лівого, або до правого nozzle. BamDude показує wiring-діаграму на картці принтера, щоб міг планувати multi-material друки.

### Nozzle-aware filament mapping

Коли 3MF призначає філаменти конкретним nozzle-ам, BamDude обмежує матчинг до AMS-tray-їв, з'єднаних з правильним nozzle:

1. 3MF несе `filament_nozzle_map` + `physical_extruder_map` у `project_settings.config`, мапінг кожного filament-слота на target-nozzle (`0` = right, `1` = left).
2. Принтер репортує `ams_extruder_map` через MQTT, вказуючи, який AMS подає на який nozzle.
3. Matcher розглядає лише tray-ї на правильному nozzle — якщо немає збігів, fallback на повний tray-список.

UI filament-mapping показує **L** / **R** badges поруч із кожним filament-requirement, тож на одному погляді видно, який nozzle задіяний. Це стосується:

- Auto-mapping print-scheduler-а
- Reprint-модалки
- Add-to-Queue модалки
- Multi-printer selection (per-printer mapping для farm-ів)

Single-nozzle принтери (X1C, P1S, A1, A1-mini, P2S, тощо) пропускають nozzle-фільтр — кожен AMS-tray доступний.

### Filament Track Switch (FTS)

Filament Track Switch — це external dual-nozzle accessory, що сидить між AMS і extruder-ами принтера, динамічно роутячи будь-який AMS-слот до будь-якого nozzle. З FTS — AMS більше не закабельований до одного extruder-а.

BamDude детектить FTS через MQTT key `print.device.fila_switch` і **авто-приглушує per-nozzle фільтр** у print-модалці:

- **Без FTS** — кожен AMS подає на фіксований nozzle, dropdown показує лише tray-ї на матчному nozzle (запобігає *position of left hotend is abnormal* failure від cross-nozzle assignment).
- **З FTS** — кожен loaded слот вибірковий для будь-якого nozzle, бо FTS обробляє роутинг на льоту.

**Routing badges:** слоти, наразі подані в track, показують `[L]` або `[R]` поруч із color-swatch і в dropdown, вказуючи, на який extruder FTS наразі їх роутить. Idle-слоти (не в жодному track) не показують badge. Detection автоматичний і re-evaluated на кожен MQTT push, тож plug-in / remove accessory оновлює dropdown-поведінку без refresh.

---

## :material-water-percent: Моніторинг вологості

| Рівень | Статус | Дія |
|:------:|--------|-----|
| < 20% | :material-check-circle:{ style="color: #4caf50" } Відмінно | Не потрібна |
| 20-40% | :material-check-circle:{ style="color: #8bc34a" } Добре | Не потрібна |
| 40-60% | :material-alert:{ style="color: #ff9800" } Задовільно | Розгляньте сушку |
| > 60% | :material-alert-circle:{ style="color: #f44336" } Високо | Замініть осушувач |

Налаштуйте кастомні warning-пороги в **Налаштування** > **Загальні**.

---

## :material-fire: Дистанційна сушка AMS

Керуйте сушкою AMS безпосередньо з BamDude для AMS 2 Pro та AMS-HT — стартуй, моніторь, стопай без походу до тачскріна принтера.

### Підтримуване обладнання

Remote-drying потребує AMS з internal-heater. Original AMS (без heater) можна моніторити, але не сушити.

| Тип AMS | Module key | Макс. температура | Drying-підтримка |
|---|:---:|:---:|:---:|
| AMS 2 Pro | `n3f` | 65 °C | :material-check: |
| AMS-HT | `n3s` | 85 °C | :material-check: (рекомендується для PA / PC / PVA) |
| AMS (original) | `ams` | — | :material-close: лише моніторинг |

### Вимоги до firmware принтера

| Принтер | Min firmware | Примітки |
|---|:---:|---|
| X1 / X1C | 01.09.00.00 | |
| P1P / P1S | 01.08.00.00 | |
| H2D | 01.02.30.00 | |
| H2D Pro | будь-яка | Без version-gate |
| X1E | будь-яка | Без version-gate |
| P2S, A1, A1 mini | — | :material-close: не підтримується |
| H2S, H2C | — | :material-close: не підтримується |

Для моделей не зі списку (майбутнє hardware) — BamDude пропускає drying-команду. Якщо firmware принтера її не підтримує, виклик падає gracefully без side-ефектів.

### Вимоги до живлення

AMS 2 Pro і AMS-HT потребують зовнішнього БП, щоб крутити heater. Без нього AMS може моніторити вологість, але не може активно сушити.

| Hardware | Idle-споживання | Drying-споживання | Рекомендація БП |
|---|:---:|:---:|---|
| AMS 2 Pro × 1 | ~5 W | ~80 W | Bundled адаптер достатній |
| AMS 2 Pro × 4 | — | ~320 W | Виділений bench-БП; **не** ланцюгом через принтер |
| AMS-HT × 1 | ~5 W | ~120 W (нагрів) | Bundled адаптер |

Firmware принтера репортує power-обмеження через `dry_sf_reason` per AMS unit. BamDude їх читає і вимикає drying-кнопку з тултіпом "Power required", коли будь-який код активний. Це стосується manual drying, queue auto-drying і ambient drying — scheduler пропускає AMS-юніти з активними reason-ами.

#### Коди `dry_sf_reason`

| Код | Причина | Опис |
|:---:|---|---|
| `0` | Task occupied | Принтер зайнятий іншою операцією |
| `1` | Insufficient power | Забагато AMS сушать одночасно — від'єднай інші або додай БП |
| `2` | AMS busy | AMS виконує іншу операцію |
| `3` | Consumable at outlet | Філамент детектовано на AMS outlet |
| `4` | Initiating | Drying уже стартує |
| `5` | Not supported in 2D mode | Не можна сушити в поточному режимі |
| `6` | Already drying | Drying-сесія вже активна |
| `7` | Upgrading | Йде firmware-оновлення |
| `8` | Need plugin power | Зовнішній БП не підключений — встроми AMS power-адаптер |

!!! warning "БП не підключений (найпоширеніша причина)"
    Якщо drying-кнопка сіра з тултіпом "Power required" — найімовірніша причина `dry_sf_reason=8` — підключи зовнішній power-адаптер до AMS юніта.

### HMS error codes (AMS power)

Power-related issues також виринають як HMS (Health Management System) errors у HMS-панелі принтера. `XX` репрезентує AMS-unit index (`00`–`07` для юнітів A–H).

#### AMS 2 Pro range (`07XX_*`)

| HMS code | Опис |
|---|---|
| `07XX_9200_0002_0003` | Heater fan 1 не може стартувати — БП не підключено |
| `07XX_9300_0002_0003` | Heater fan 2 не може стартувати — БП не підключено |
| `07XX_9800_0002_0001` | PSU voltage задешеве |
| `07XX_9800_0002_0002` | PSU voltage завелике |

#### AMS-HT range (`18XX_*`)

| HMS code | Опис |
|---|---|
| `18XX_2500_0002_0001` | Використовує живлення принтера замість виділеного адаптера — підключи AMS-HT БП |
| `18XX_9200_0002_0003` | Heater fan 1 не може стартувати — БП не підключено |
| `18XX_9300_0002_0003` | Heater fan 2 не може стартувати — БП не підключено |
| `18XX_9800_0002_0001` | PSU voltage задешеве |
| `18XX_9800_0002_0002` | PSU voltage завелике |

### Запуск сеансу сушки

1. Натисніть іконку :material-fire: полум'я в заголовку картки AMS
2. Оберіть тип філаменту, температуру та тривалість
3. За бажанням увімкніть обертання котушки
4. Натисніть **Start**

### Автоматична сушка через чергу

Автоматично сушить філамент між запланованими друками, коли вологість перевищує поріг.

- Увімкніть в **Налаштування** > **AMS Display Thresholds** > **Queue Auto-Drying** (`queue_drying_enabled`).
- **Неблокувальний** (за замовчуванням, `queue_drying_block=false`) — сушка йде у фоні; друки в черзі мають пріоритет.
- **Блокувальний** (`queue_drying_block=true`) — черга стопається, поки сушка не закінчиться. Використовуйте, коли реально хочете суху котушку перед наступним друком і не проти зачекати.
- Per-filament температура + тривалість беруться з налаштовуваних пресетів (Налаштування → AMS Display Thresholds → Drying Presets), а не з hard-coded дефолтів — AMS 2 Pro і AMS-HT мають окремі колонки, бо досягають різних температур.

#### Деталізований flow

1. Scheduler стежить за кожним idle-принтером, що має хоча б один **scheduled** queue-item — items у чистому "Queue Only" режимі auto-drying не тригерять.
2. Для кожного AMS-юніта BamDude читає live humidity через MQTT.
3. Якщо вологість перевищує **Fair (orange)** поріг із Settings, drying стартує з per-filament preset (нижче).
4. Drying крутиться **мінімум 30 хвилин** — навіть якщо вологість впала нижче порогу раніше. Це зупиняє швидкий start/stop циклінг, коли вологість прямо на порозі.
5. Після 30 хв BamDude перевіряє вологість на кожен scheduler-цикл; як тільки на або нижче порогу — drying зупиняється рано.
6. Коли наступний scheduled-друк готовий стартувати — будь-який in-progress drying зупиняється (non-blocking режим), і друк стартує. У blocking режимі черга чекає.

#### Коли auto-drying зупиняється

- Вологість падає на або нижче Fair-порогу (лише після 30 хв мінімуму)
- Scheduled-друк готовий стартувати (non-blocking режим)
- Розклад queue-item видалено або переключено на "Queue Only"
- Усі scheduled-items залишають чергу
- Auto-drying вимкнуто в Settings
- Принтер вимкнено або відключено

#### Conservative-температура для mixed AMS юнітів

Коли один AMS тримає **кілька типів філаменту** (напр. PLA в слоті 1 + PETG в слоті 2), BamDude вибирає параметри, що нічого не розплавлять:

| Параметр | Правило | Чому |
|---|---|---|
| **Температура** | **Найнижча** max-safe серед усіх loaded філаментів | PLA при 65 °C — каша; запуск обмежений найбільш heat-sensitive філаментом у юніті |
| **Тривалість** | **Найдовша** серед усіх loaded філаментів | Крутитися достатньо довго, щоб висушити slowest-drying філамент |

Приклад: AMS тримає PLA + PETG → температура = 50 °C (PLA cap), тривалість = 8 г (PETG default). Чистий PETG використав би 65 °C / 8 г.

#### Вимоги

- Хоча б один **scheduled** queue-item ("Queue Only" не рахується)
- AMS 2 Pro або AMS-HT (original AMS не має heater)
- Підтримувана firmware принтера (див. [Вимоги до firmware принтера](#вимоги-до-firmware-принтера))
- Вологість вище Fair-порогу
- Без активних `dry_sf_reason` кодів (див. [Коди `dry_sf_reason`](#hms-error-codes-ams-power))
- Принтер online і підключений до BamDude

Якщо хочеш, щоб drying запускався без scheduled-друку — див. [Ambient-сушка](#ambient-сушка).

#### Налаштовувані drying-пресети

Дефолти базуються на офіційних filament drying-профілях BambuStudio. Редагуй під **Settings → AMS Display Thresholds → Drying Presets**; зміни авто-зберігаються і застосовуються до manual drying, queue auto-drying і ambient drying одночасно.

| Філамент | AMS 2 Pro temp | AMS-HT temp | AMS 2 Pro тривалість | AMS-HT тривалість |
|---|:---:|:---:|:---:|:---:|
| PLA | 50 °C | 50 °C | 8 г | 8 г |
| PETG | 65 °C | 65 °C | 8 г | 8 г |
| TPU | 65 °C | 70 °C | 12 г | 12 г |
| ABS | 65 °C | 80 °C | 12 г | 8 г |
| ASA | 65 °C | 80 °C | 12 г | 8 г |
| PA | 65 °C | 90 °C | 12 г | 16 г |
| PC | 65 °C | 80 °C | 12 г | 8 г |
| PVA | 65 °C | 85 °C | 12 г | 18 г |

!!! note "Ліміт температури AMS 2 Pro"
    AMS 2 Pro (`n3f`) обмежений 65 °C у firmware. AMS-HT (`n3s`) обмежений 85 °C. Виставлення вищої температури в preset нешкідливе — clamp-иться до hardware-стелі при command-time.

### Ambient-сушка

Окремий шлях, що не залежить від черги. Увімкніть під **Налаштування** > **Print Queue** > **Ambient Drying** (`ambient_drying_enabled`). На будь-якому idle-принтері, де вологість вища за поріг, BamDude стартує сушку без виставлення target-температури — корисно як 24/7 humidity-keeper для idle-ферми.

---

## :material-chart-line: Історичні графіки

Натисніть на індикатори вологості або температури, щоб переглянути історичні дані.

### Часові діапазони

| Діапазон | Use case |
|---|---|
| **6 годин** | Recent trends — що щойно сталося |
| **24 години** | Daily pattern, day-night humidity swing |
| **48 годин** | Extended view — drying-cycle ефективність |
| **7 днів** | Weekly overview — shop-environment baseline |

### Особливості графіка

- **Line-чарт slot fill-level через час** — для inventory-tracked котушок AMS history накладає remaining-грами проти humidity, тож видно, як sticky-філамент висох (чи ні).
- **Min / max / avg** статистика для обраного діапазону.
- **Threshold-лінії** на Fair / High / Excellent межах — легко бачити, коли humidity справді перетнула trigger.
- **Інтерактивні tooltip-и** показують точне значення + timestamp on hover.
- **Zoom + pan** для drill-у в конкретний інцидент.

---

## :material-database: AMS Data Retention

AMS humidity / temperature samples persist у локальну БД для historical-чартів.

| Setting | Default | Range |
|---|---|---|
| AMS data retention | **90 днів** | 1–365 днів |

Налаштуй під **Settings → General → AMS Data Retention**. Старіші samples прибираються daily cleanup-тіком.

!!! warning "Storage impact"
    Довша retention = більше рядків у `ams_history` і більша БД. На busy farm-і з 4× принтерами × 4× AMS × 4 слотами і update кожні 30 с — 90 днів це приблизно 90 × 86400 / 30 × 64 = ~16 М рядків — нормально на SQLite WAL із default page size, але варто мати на увазі, якщо суттєво збільшуєш вікно.

---

## :material-lightbulb: Поради

!!! tip "Автосушка між друками"
    Увімкніть автоматичну сушку через чергу, щоб тримати філамент сухим під час довгих черг друку, або увімкніть ambient-сушку для всіх idle-принтерів.

!!! tip "Обслуговування осушувача"
    Коли вологість постійно залишається високою, замініть або регенеруйте пакети осушувача.

> Початково базується на документації [Bambuddy](https://github.com/maziggy/bambuddy).
