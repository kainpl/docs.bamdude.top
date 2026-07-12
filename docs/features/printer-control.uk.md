---
title: Керування принтером
description: Усі runtime-дії на картці принтера у BamDude
---

# Керування принтером (Printer Control)

Кожна картка принтера на дашборді відкриває in-app еквівалент кнопок на тачскрині фізичного принтера. Ця сторінка — каталог: що робить кожна кнопка, який BamDude-дозвіл її закриває, і яка MQTT-команда реально летить на принтер.

---

## :material-information: Що це

Картка принтера — тонкий клієнт перед `PrinterManager` (`backend/app/services/printer_manager.py`), який спілкується з принтером по MQTT через `BambuMqttClient`. Картка показує:

- **Статус** (idle / printing / paused / error) і живу телеметрію (temps, fans, AMS)
- **Print actions** (start / pause / resume / stop / clear plate / skip object)
- **Hardware controls** (chamber light, bed jog, full home, print speed, airduct mode)
- **Smart-plug actions** (power on / off через прив'язану розетку)
- **Debug helpers** (force MQTT refresh)

Більшість дій закриті дозволом `printers:control`. Дві підмножини відрізують lower-privilege дії: `printers:clear_plate` (тільки post-print "next job ready" handshake) і `printers:read` (статус + object lists, без команд).

---

## :material-printer: Print Actions

### Старт друку з картки

Перетягніть sliced `.gcode` або `.gcode.3mf` файл на картку принтера або клікніть зелену **Print**. Файл заливається у бібліотеку, відкривається print-modal з вибраним саме цим принтером, і робота диспетчерізується через стандартну print queue.

Картка також показує червоний overlay **"Printer busy"**, коли ви кидаєте файл на non-idle принтер — щоб не перебити running-job. Що відбувається після dispatch — у [Print Queue](print-queue.md).

!!! note "Дозвіл"
    `printers:control`. Сам upload у бібліотеку також перевіряє `library:write`.

### Nozzle Offset Calibration (лише dual-nozzle)

На **H2D, H2D Pro, H2C і X2D** діалог друку показує тогл **"Nozzle Offset Calibration"** — **увімкнений за замовчуванням**, як у Bambu Studio. Він керує тим, чи запускає принтер свою nozzle-offset калібровку перед стартом друку.

Раніше ця калібровка завжди пропускалася, без можливості її увімкнути — і, що не менш важливо, без можливості *свідомо* тримати її вимкненою. А цей вимкнений кейс важливий для diamond-nozzle сетапів, які **не мають** її ганяти.

Тогл **з'являється лише на dual-nozzle принтерах**. Single-nozzle машини завжди пропускають калібровку незалежно від будь-якого налаштування. Твій вибір запам'ятовується per queue item і застосовується на кожному dispatch-шляху (queue, drag-and-drop, повторний друк).

### Pause / Resume

| Кнопка | Коли видима | Endpoint | Що шле |
|--------|-------------|----------|--------|
| :material-pause: **Pause** | State = printing | `POST /api/v1/printers/{id}/print/pause` | MQTT `pause` |
| :material-play: **Resume** | State = paused | `POST /api/v1/printers/{id}/print/resume` | MQTT `resume` |

Обидві дії показують підтвердження, щоб уникнути fat-finger.

### Stop print

`POST /api/v1/printers/{id}/print/stop` — шле MQTT `stop` і **також** маркує принтер як user-stopped у dispatch tracking dict. Цей другий крок важливий: без нього HMS-евристика у `_dispatch_archive_update` пізніше неправильно класифікує cancel-sequence HMS-код (наприклад, H2D module-`0x0C`) як справжній "Layer shift" fail. Зупинка друку незворотна — друк рестартує з початку, якщо ви ставите його у чергу заново.

### Skip object

Для multi-object plates: пропустити окремий об'єкт, що падає, поки решта дофрахаються.

```
GET  /api/v1/printers/{id}/print/objects     → список об'єктів зі skip status
POST /api/v1/printers/{id}/print/skip-objects → скіпнути обрані ID
```

Список береться з активного 3MF (`subtask_name`). Якщо in-memory object list порожній (наприклад, після backend restart), передайте `?reload=true` — і BamDude витягне 3MF з принтерного FTP та переспасить його. Підтримує кілька варіантів імен (`{name}.3mf`, `{name}.gcode.3mf`, з пробілами і underscored).

!!! warning "Зачекайте до layer 2"
    Прошивка принтера відмовляє у skip-командах, поки не покладено перший шар. Skip-modal показує жовтий банер на layer 0/1.

!!! tip "Збігайте ID з принтером"
    ID у BamDude-modal збігаються з ID на тачскрині (plate visualisation) — саме так ви ідентифікуєте, яка фізична частина яка.

### Clear plate

Після завершення (або падіння) друку, коли є jobs у черзі, з'являється кнопка **Clear Plate & Start Next**. Клік викликає:

```
POST /api/v1/printers/{id}/clear-plate
```

Це **не шле MQTT-команду** на принтер — лише фліпає server-side флаг `awaiting_plate_clear`, який розблоковує queue scheduler, щоб наступна start-команда пішла. Принтер прийме новий друк і автоматично переб'є свій `FINISH` / `FAILED` стан.

Прийнятні стани принтера: `FINISH`, `FAILED`, **`IDLE`**. IDLE-кейс покриває Auto-Off цикли — коли принтер був вимкнений smart plug'ом після job, persisted `awaiting_plate_clear` флаг ще стоїть, коли той бутиться назад в IDLE, і оператору все одно треба ack'нути cleared plate.

!!! note "Окремий дозвіл"
    Clear-plate юзає `printers:clear_plate` — більш гранульований дозвіл, ніж `printers:control`. Можна дати техніку можливість OK'ати наступний job без права на stop / pause / chamber-light.

### Clear HMS errors

`POST /api/v1/printers/{id}/hms/clear` — шле `clean_print_error` через MQTT і одразу чистить HMS-список з картки. Корисно після cancel'у, що залишив stale `print_error` коди.

---

## :material-cog: Діалог налаштувань принтера

Per-printer діалог, який віддзеркалює **Bambu Studio → Print Options + Printer Parts**. Відкрий його з kebab :material-dots-vertical: меню на картці принтера → **Printer Settings**.

Дві вкладки:

- **Print Options** — усі тогли, що BS показує для конкретної моделі: AI-детекції, сенсори, поведінка plate, звук, auto-recovery.
- **Printer Parts** — read-only вид встановлених сопел (тип, діаметр, тип потоку). Редагування parts на принтері залишене на наступну фазу; зараз API повертає `409 parts_not_editable` на спроби запису.

### Print Options — що там є

| Група | Налаштування | Значення | MQTT |
|---|---|---|---|
| AI-детекції | Spaghetti detector | On/Off + Low/Medium/High | `xcam_control_set` (`spaghetti_detector`) |
| | Pile-up at purge chute | On/Off + Low/Medium/High | `xcam_control_set` (`purgechutepileup_detector`) |
| | Nozzle-clumping | On/Off + Low/Medium/High | `xcam_control_set` (`nozzleclumping_detector`) |
| | Air-printing | On/Off + Low/Medium/High | `xcam_control_set` (`airprinting_detector`) |
| | First-layer inspector | On/Off | `xcam_control_set` (`first_layer_inspector`) |
| | AI monitoring (general) | On/Off | `xcam_control_set` (`ai_monitoring`) |
| Сенсори | FOD check (foreign-object) | On/Off | `xcam_control_set` (`fod_check`) |
| | Displacement detection | On/Off | `xcam_control_set` (`displacement_detection`) |
| | Filament tangle detect | On/Off | `print_option` (`filament_tangle_detect`) |
| | Nozzle-blob detect | On/Off | `print_option` (`nozzle_blob_detect`) |
| Plate | Build-plate marker detect | On/Off | `print_option` (`build_plate_marker_detect`) |
| | Plate alignment check | On/Off | `print_option` (`plate_align_check`) |
| Камера | Purify air at print end | Off / Inside / Outside | `print_option` (`air_purification`) |
| | Open-door check | Off / Pause / Halt | `print_option` (`xcam_door_open_check`) |
| Інше | Auto recovery on step loss | On/Off | `print_option` (`auto_recovery`) |
| | Prompt sound | On/Off | `print_option` (`sound_enable`) |
| | Camera snapshot enable | On/Off | `ipcam_cap_pic_set` |
| | Save remote print to storage | On/Off | `print_option` (`xcam__save_remote_print_file_to_storage`) |

### Видимість — що відображається залежно від принтера

Per-model capability gating, та сама ідея, що й у [діалозі налаштувань AMS](ams.md#діалог-налаштувань-ams). Рядки з `false`-capability приховуються повністю — нема сенсу показувати **AI monitoring** на P1S чи **Purify air** на non-H2D Pro.

| Група | X1 family | P1 / P2 / X2D | A1 / A1 Mini | H2D family | H2D Pro |
|---|---|---|---|---|---|
| AI-детекції (spaghetti / pile-up / clumping / air-print / first-layer / monitoring) | так | — | — | так | так |
| FOD + displacement | так | — | — | так | так |
| Open-door check | так | так | — | так | так |
| Purify air | — | — | — | — | **так** (тільки H2D Pro) |
| Filament tangle | так | так | так | так | так |
| Nozzle blob | так | так | — | так | так |
| Plate marker / alignment, sound, auto-recovery, snapshot, save-remote | усі моделі | | | | |

### Джерело правди — принтер

BamDude **не** зберігає "desired state" на своєму боці. Стан у діалозі читається з MQTT-push принтера (`print.print_option` echoes). При тогл-у — BamDude публікує відповідну MQTT-команду і починає 3-секундний hold (`printer_settings_hold` per-key), щоб рядок не миготів між optimistic і підтвердженим значенням — той самий патерн, що й у AMS Settings dialog.

Якщо принтер втратив налаштування (factory reset, firmware-update wipe) — BamDude це відобразить. Reconciliation немає. Відкрий діалог знову і перетогль.

### Дозволи й аудит

Kebab-пункт з'являється тільки для користувачів з `printers:update`. Той самий дозвіл захищає endpoint `POST /api/v1/printers/{id}/settings`.

Кожна застосована зміна пише рядок у таблицю `printer_setting_audit` (m061) — `(printer_id, user_id, tab, action, payload_json, sequence_id, result, error_message, created_at)`. UI-viewer-а поки немає; query напряму, якщо треба відповісти "хто вимкнув spaghetti-детекцію минулого четверга?"

!!! info "Calibration залишається окремо"
    Calibrate Belt / Nozzle Offset / Resonance Test досі живуть у власному kebab-пункті **Calibration** — це не тогли, а довгі рутини. Фаза-2 може їх злити; фаза-1 тримає окремо.

---

## :material-flask: Калібровка філаменту

Майстер, що відображає **Bambu Studio → Calibrate → Pressure Advance / Flow Rate / Towers** без виходу з BamDude. Відкривається через kebab :material-dots-vertical: на картці принтера → **Filament Calibration**. Перегляд історії — на сусідньому kebab-пункті → **Calibration History**.

### Що калібруємо

| Режим | Шлях | Результат |
|---|---|---|
| **PA Line** | Manual: плаский одношаровий блок зі сходинковими K-рядками (у кожному slow / fast / slow витискання) + цифровий tab збоку — обери найчистіший рядок, K = мітка біля нього. Зовні як PA Pattern, лише замість V-стінок — прямі лінії | `pa_k_value` per (filament, nozzle, extruder) |
| **PA Tower** | Manual: вертикальна вежа зі сходинками PA — виміряй висоту (мм) де кути найчистіші, K = Start + (Step × height) | `pa_k_value` per (filament, nozzle, extruder) |
| **PA Pattern** | Manual: гребінь V-стінок зі сходинковими K + цифровий tab знизу — обери найчистішу колонку, прочитай K за цифрою | `pa_k_value` per (filament, nozzle, extruder) |
| **Auto PA** | X1 / X1E / H2D Pro: лідар сканує + рахує K/N | те саме (наперед заповнений save-діалог) |
| **Flow Rate** | Manual: 9-блочний coarse (−20…+20 %) → 7-блочний fine | `flow_ratio` per combo |
| **Auto Flow Rate** | Auto-варіант на лідарних X1 | те саме |
| **Temp / VolSpeed / VFA / Retraction Tower** | Тільки manual-друк; результат читаєш очима і вписуєш у slicer | у БД нічого не пишеться |

### Per-model capability gating

Auto-шляхи потребують лідар + флаг підтримки у прошивці; manual-шляхи доступні універсально.

| Шлях | X1-серія | P1 / P2 / X2D | A1 / A1 Mini | H2D / H2D Pro |
|---|---|---|---|---|
| Manual PA / Flow Rate / Towers | yes | yes | yes | yes |
| Auto PA (lidar) | yes | — | — | yes (Pro) |
| Auto Flow Rate (lidar) | yes | — | — | yes (Pro) |
| Dual-extruder (per-extruder cali) | — | — | — | yes |

### Гейтування за слайсер-сайдкаром *(0.4.5)*

Калібровочний майстер Bambu Studio завжди запускає повне slicing — навіть режими, що виглядають «pre-sliced» (PA Pattern, Flow Rate, Auto PA), вантажать геометрію з `resources/calib/` як скаффолд, потім BS накладає активний printer / process / filament-пресет плюс per-mode g-code-інжект через `Plater::calib_*` / `CalibUtils::*`. BamDude дзеркалить ті ж 12 BS-файлів у `backend/app/data/calib_assets/`, але доходить до того ж slicing-кроку через **серверне нарізання** через сайдкар (OrcaSlicer / Bambu Studio API).

Тож кожен режим Filament Calibration потребує підключеного сайдкара. Щоб це було очевидно:

- Kebab-пункти **Filament Calibration** і **Calibration History** на картці принтера **сховані коли "Серверне нарізання" вимкнено** в Налаштуваннях (Загальне → Загальне).
- Якщо прямий API-виклик проскочить — `POST /printers/{id}/calibration/sessions` повертає `409 {detail: "slicer_sidecar_required"}` для будь-якого manual-режиму.
- Auto-режими (Auto PA / Auto Flow Rate на лідарних X1 / X1E / H2D Pro) — суто printer-side; ідуть через MQTT `extrusion_cali_start` / `flow_rate_cali_start` без локального slicing. Але оскільки решта майстра залежить від сайдкара — вхід гейтиться разом.

PA Tower (Phase 1), PA Pattern (Phase 2) і PA Line (Phase 9) зведені end-to-end станом на 0.4.5 — обираєш будь-який з них у майстрі, сайдкар-слайсер пече pattern, BamDude льотить gcode на принтер, друкує, і вибиває діалог збереження по завершенню. Решта manual-режимів (Temp / Retraction / VFA / Volumetric Speed Towers, Flow Rate) проходять стадію `verification` (завантажуєш сирий нарізаний 3MF для порівняння на десктопі) перед переходом у `production` — це послідовний rollout **Wave 2** калібровочної дорожньої карти.

### Опції друку + swap-макроси *(0.4.5)*

Сторінка пресетів майстра містить ті ж `PrintOptionsPanel` + `SwapMacrosPanel` що й звичайний діалог друку. Вона читає твої збережені преференції per-printer-model (PrintModal і калібровочний майстер ділять той самий storage-ключ), тож налаштування зроблені раз для моделі — наприклад завжди-увімкнені swap-макроси для зміни столу A1, чи layer inspection для X1E — автоматично застосовуються і до калібровочних друків. Збережене upsert-иться на кожен успішний start. Калібровочно-підлаштовані дефолти: `bed_levelling=true`, `flow_cali=false` (інакше pre-print flow-cali принтера перепише M900 K-sweep з gcode і замаскує тест), swap-макроси — opt-in. MQTT-action макроси (P1S світло on/off) автоматично спрацьовують через стандартні `print_started` / `print_finished` івент-хуки — без per-job-тогла.

### Стан + персистентність

- Рядок у BamDude пишеться в `filament_calibration` з ключем `(printer_id, filament_id, nozzle_diameter, nozzle_volume_type, extruder_id)` починаючи з m063 — per-printer-instance, не per-model. Два X1C в одній фермі тримають незалежні K-значення для того ж матеріалу.
- Принтер — джерело істини. Таблиця BamDude — це кеш. Щоразу як BamDude читає `extrusion_cali_get`, він віддзеркалює кожен видимий профіль у кеш за стабільною ідентичністю (`name` + `filament_id` + `pa_k_value`) — нові рядки приходять неактивними; ти явно промотиш один рядок на combo з модалки історії.
- Sync запускається автоматично на кожен (ре)коннект MQTT і коли список K-profile принтера реально змінюється (hash-diff фільтр, щоб не смикати БД на кожен push_status). Manage / History-діалоги все ще тригерять свіжі тяги по запиту.
- Кожен рядок кешу несе printer-side `nozzle_id` (`HS00-0.4`, `HH00-0.6`, …) — видно, на якому фізичному соплі було знято калібровку. На P1S / A1 / A1 mini (де per-profile id не приходить) BamDude деривує його з device-level стану сопла.
- `is_active=True` на combo гарантує partial unique-індекс. Промотиш рядок — siblings автоматично стають неактивними.
- Spool ↔ K-profile-зв'язки (m064) тепер тонкі: рядок `spool_k_profile` несе лише `(spool, printer, extruder, filament_calibration_id)`. Сотня PETG-котушок з однаковою калібровкою колапсує в один рядок кешу + багато link-рядків замість дублювати K-дані.
- Калібровочні assets дзеркаляться з BS `resources/calib/` (AGPL-3.0) у `backend/app/data/calib_assets/` — 12 файлів (3MF / STL / STEP-скаффолди; див. *Гейтування за слайсер-сайдкаром* вище — усі режими все одно потребують сайдкар). PA Line range: 0.0–0.1 step 0.002 (50 ліній). Flow Rate coarse: `[-20, -15, -10, -5, 0, 5, 10, 15, 20]` %; fine: `[-5, -2, 0, 2, 5, 10, 15]` %.

### Шлях застосування на реальному друку

`background_dispatch` викликає уніфікований хелпер `apply_active_calibration_to_slot` для кожного AMS-слоту, який буде задіяний завданням. Порядок резолву: явний spool→calibration link → активний `filament_calibration` рядок за combo. Далі хелпер пере-зіставляє кешований рядок з `client.state.kprofiles` за **стабільною ідентичністю** (`name` + `filament_id` + `pa_k_value`), щоб знайти ЖИВИЙ `cali_idx` — принтер переставляє слоти після видалення сусіда, тому збережений номер це лише підказка — і фаєрить `extrusion_cali_sel(ams_id, slot_id, cali_idx)` перед стартом друку.

Той самий хелпер тепер ганяє з post-RFID-refresh шляху, tray-tag drift detect, auto-spool-теггера, і обох slot-assign ендпоінтів (inventory + Spoolman) — шість call-сайтів злиті в один. Закриває діру з тихим дрейфом, коли прошивка відкочувалася на дефолтний профіль після RFID-перетеггань, перепризначень слотів або рестартів, навіть якщо `SpoolAssignment` рядок був на місці.

Друки із зовнішніх джерел (BS, екран принтера) теж отримують вигоду: bind зберігається на принтері до явної зміни, тож останній `extrusion_cali_sel`, що відправив BamDude, залишається в силі.

### History modal

Дві секції поряд:

- **BamDude history** — рядки `filament_calibration` згруповані за nozzle. Per-row дії: **Set Active** (flip siblings + emit `extrusion_cali_sel`), **Delete**. Активний рядок виділений зеленим колечком + чекмарком.
- **Printer-side history** — 16-слотний вид, підтягнутий через `extrusion_cali_get`. Кнопка Refresh форсує re-pull для заданого nozzle diameter.

!!! info "Resume banner"
    Якщо закрити майстер посеред потоку (друк закінчився, але збереження ще не пройшло), при повторному відкритті побачиш жовтий banner з **Resume / Discard** для цієї in-flight сесії.

### Permissions та audit

`printers:update` гейтить вхід у майстер і всі mutation-роути. Кожна дія пише рядок у `calibration_audit` — `(printer_id, session_id, action, payload_json, sequence_id, result, error_message, created_at)`. Actions: `start_session / save_result / set_active / delete / cancel`, плюс мутації зі старої сторінки K-profiles з 0.4.5: `kprofile_add / kprofile_edit / kprofile_batch_add / kprofile_delete`. UI-viewer-а поки немає; query напряму.

!!! note "Edit-Save без printer-relevant зміни не торкає принтер"
    З 0.4.5 діалог редагування K-профіля порівнює `name` / `k_value` / `filament_id` / `nozzle_id` / `nozzle_diameter` з завантаженим рядком перед publish'ем. Усе збігається → зберігається лише нотатка (BamDude-local); `extrusion_cali_set` не йде. Тримає принтер від реґенерації `setting_id` на кожен клік Save, через що раніше плив cache-рядок.

### Що навмисно НЕМАЄ в BamDude (поки що)

- **PA range customization** — start/end/step зафіксовані під BS-defaults. Якщо потрібен інший діапазон — калібруй у самому BS і імпортуй значення.
- **External spool calibration** — virtual tray `tray_id >= 0x10000` вимкнено для auto-шляху; manual дозволяє, але прив'язка до tray може не пережити перезавантаження принтера.
- **Tower-mode result entry в BamDude** — tower-режими лише запускають друк і закінчуються. Результат читаєш очима і вписуєш у профіль філаменту в slicer-і. (BS робить так само.)

---

## :material-arrow-up-down: Bed Jog (Z-вісь)

Рухати plate вгору/вниз на фіксований step.

```
POST /api/v1/printers/{id}/bed-jog?distance=N[&force=true]
```

| Param | Валідація |
|-------|-----------|
| `distance` | Non-zero, `|distance| <= 200` мм |
| `force` | Якщо `true`, обгортає рух у `M211 S0` … `M211 S1`, щоб обійти soft endstops |

Step-селектор у поповері: `1 / 10 / 50 мм`. Активний лише коли принтер **не** друкує.

### G-code, що шле

| Mode | Послідовність |
|------|---------------|
| Normal | `G91` → `G1 ZN F600` → `G90` |
| Force | `M211 S0` → `G91` → `G1 ZN F600` → `G90` → `M211 S1` |

### Not-homed warning

Після завершення друку Z-вісь зазвичай не reference'нута. Перший jog-клік у сесії показує модалку у стилі Bambu Studio:

| Вибір | Дія |
|-------|-----|
| **Home Z** | Шле `G28 Z` і закриває діалог — клікніть jog знову після homing |
| **Move anyway** | Викликає `bed-jog` з `force=true` (single-move soft-endstop bypass) і запам'ятовує вибір на решту browser-сесії |
| **Cancel** | Закриває діалог, нічого не шле |

!!! warning "Soft-endstop bypass"
    `force=true` вимикає soft-limits лише на один рух. Тримайте дистанції малими (≤10 мм), доки plate не у відомо-безпечній позиції — прошивка все ще тримає hard physical limits, але це на вас слідкувати, щоб commanded-move був осмислений.

---

## :material-home: Home Axes

```
POST /api/v1/printers/{id}/home-axes?axes={z|xy|all}
```

Параметр `axes` **тримається лише для backward compat** — кожен виклик шле bare `G28`, незалежно від того, що ви передали. Причина — upstream issue #1052: на H2C bed homes рухом **вгору** до top endstop'у, і bare `G28 Z` пропускає toolhead-park step, який повний `G28` робить першим. Результат — bed врізався у toolhead. Тому BamDude безумовно шле `G28` і дає прошивці виконати її safe park-XY-then-home-Z послідовність.

Невалідні значення `axes` все ще повертають 400, щоб typo'и спливали.

---

## :material-lightbulb-on: Chamber Light

```
POST /api/v1/printers/{id}/chamber-light?on={true|false}
```

Тогл chamber LED через MQTT. Optimistic UI update на клік, toast confirmation на round-trip success.

!!! info "H2D dual lights"
    На H2D обидва chamber lights керуються разом — у прошивці немає per-light тогла.

---

## :material-snowflake: Airduct Mode (P2S / X2D / H2 series)

Доступне лише на принтерах з активним airduct (P2S, X2D, H2D, H2C, H2S). Картка показує airduct-badge у controls row; принтери без airduct ховають його повністю.

| Mode | Іконка | З чим |
|------|--------|-------|
| **Cooling** | :material-snowflake: | PLA / PETG / TPU — фільтрує і охолоджує chamber |
| **Heating** | :material-fire: | ABS / ASA / PC / PA — циркулює і гріє chamber, закриває top exhaust flap |

Зміна mode виходить як MQTT `set_airduct` (`BambuMqttClient.set_airduct_mode`). Поточний mode reflect'иться через `airduct.modeCur` у status push принтера — badge оновлюється, тільки-но принтер підтвердить.

---

## :material-speedometer: Print Speed Presets

Змінюйте швидкість друку посеред job без виходу з картки.

```
POST /api/v1/printers/{id}/print-speed?mode=N
```

| Mode | Preset | Швидкість | Коли |
|------|--------|-----------|------|
| `1` | Silent | 50% | Нічні друки, шумо-чутливі кімнати |
| `2` | Standard | 100% | Default slicer speed |
| `3` | Sport | 124% | Проста геометрія, time-pressure |
| `4` | Ludicrous | 166% | Maximum speed |

Badge у controls row показує поточний % швидкості і dimmed коли друк не активний.

---

## :material-fan: Fan Status (display only)

Три живих fan-badge у controls row: **Part Cooling**, **Auxiliary**, **Chamber**. Показують real-time швидкості (0–100%), що репортить принтер.

!!! info "Read-only"
    Швидкості вентиляторів визначає slicer-профіль і прошивка принтера — BamDude їх показує, але не дає контролу.

---

## :material-power: Power Controls (smart plug)

Якщо до принтера прив'язана [smart plug](smart-plugs.md):

| Дія | Що відбувається |
|-----|-----------------|
| **Power On** | Розетка вмикається. Принтер бутиться і реконнектиться у MQTT через кілька секунд. |
| **Power Off** | Розетка вимикається. BamDude **не** шле MQTT-команду shutdown — просто рубає живлення. |

Auto-power-off конфігурується per printer: після завершення друку і коли bed/nozzle падають нижче configurable cooldown threshold на configurable wait time, прив'язана розетка вимикається. Поля threshold + wait-time і типи інтеграції (Tasmota / HA / REST / MQTT) — у [Smart Plugs](smart-plugs.md).

!!! warning "BamDude не має "soft shutdown" MQTT-команди"
    Немає MQTT-команди, яка чисто гасить Bambu-принтер. Power-off іде через smart plug. Якщо її немає, єдиний спосіб погасити — кнопка на корпусі.

---

## :material-refresh: Force Refresh (MQTT pushall)

```
POST /api/v1/printers/{id}/refresh-status
```

Просить принтер ре-броудкастити повний статус (MQTT `pushall`). Корисно, коли значення на картці виглядає stale, а ви не хочете повного реконнекту — full reconnect рве існуючу MQTT/FTP сесію і повільніший. Endpoint у three-dot меню картки.

Для важчого reset'у логіка `printer_manager.ensure_fresh_connection_for_printer` запускається автоматично перед будь-якою control-командою — це підіймає stalled MQTT-конект без втручання оператора.

---

## :material-wrench: Режим обслуговування (Maintenance Mode)

Виведи принтер **з експлуатації** без видалення — для заміни сопла, роботи з ременем чи паркування нестабільної машини. Перемкни з :material-dots-vertical: kebab-меню картки принтера або з діалогу **Edit**.

Поки в режимі обслуговування, принтер:

- **випадає з queue dispatch і scheduler** — на нього не відправляється новий джоб, і його пропускає [Auto-Queue Routing](auto-queue.md) та model-based assignment;
- **пропускається auto-drying** — drying scheduler його ігнорує;
- **виключений з метрик і запису sensor-history**;
- **відключається від MQTT** і лишається відключеним, поки не вимкнеш режим обслуговування (увімкнення назад реконнектить автоматично).

Картка міняє connection-бейдж на бурштиновий пілл **Maintenance** (:material-wrench:) з кнопкою **Exit**, тож одразу видно, які машини запарковані.

!!! note "Увімкнення mid-print"
    Вхід у режим обслуговування на принтері, що **друкує або на паузі**, спершу питає підтвердження — MQTT-відключення зупиняє трекінг прогресу і completion-нотифікації для активного джоба.

!!! note "Дозвіл"
    Maintenance Mode їде на прапорці `is_active` принтера (без окремої колонки), тож потребує `printers:update` — того самого дозволу, що й редагування принтера.

!!! info "Це не Maintenance Tracker"
    Це *сервісний стан* усього принтера. Він не пов'язаний із трекером [Maintenance](maintenance.md), що логує роботи по rod / nozzle / belt проти годин напрацювання: один паркує машину, інший нагадує, коли деталь на черзі.

!!! info "Виводиш назавжди? Краще архівуй"
    Режим обслуговування лише тимчасово паркує принтер і лишає його картку видимою. Щоб *вивести* принтер у відставку — продано, списано — [Архівуй](archived-printers.md) його: картка ховається всюди, а історія друку зберігається.

---

## :material-checkbox-multiple-marked: Bulk Actions

Виберіть кілька карток (Select-mode toolbar зверху сторінки принтерів) і застосуйте ту саму дію до всіх одразу. Smart-enabled кнопки — активні лише коли хоча б один обраний принтер у відповідному стані для дії.

| Bulk action | Потрібен стан | Дозвіл |
|-------------|---------------|--------|
| Stop | Хоча б один printing або paused | `printers:control` |
| Pause | Хоча б один printing | `printers:control` |
| Resume | Хоча б один paused | `printers:control` |
| Clear Notifications | Завжди | `printers:control` |
| Clear Bed | Хоча б один у `FINISH` / `FAILED` / `IDLE` з `awaiting_plate_clear` | `printers:clear_plate` |

Selection helpers у floating toolbar:

- **Select All** — кожна видима картка
- **Select by State** — виберіть стан (Printing / Paused / Finished / Idle / Error / Offline) і оберіть усі картки в ньому
- **Select by Location** — видно лише коли хоча б у одного принтера є location

Вийти з selection mode — **Esc** або **X** на floating toolbar.

---

## :material-information-outline: Status Badges

Три невеликих icon-only badge у top status row кожної картки:

| Badge | Зелений | Червоний / жовтий | Нотатки |
|-------|:-------:|:-----------------:|---------|
| :material-sd: SD Card | inserted | red коли missing | Усі принтери |
| :material-door-closed: Door | closed | yellow коли відчинено | X1 / P1S / P2S / X2D / H2 series only |

Door state декодується з відповідного MQTT-поля per family (X1: `home_flag` bit 23; інші: `stat` bit 23) і пушиться live по WebSocket — без чекання на наступний status poll.

---

## :material-shield-account: Permission Matrix

| Дія | Дозвіл |
|-----|--------|
| Читати статус, AMS, object list | `printers:read` |
| Start / pause / resume / stop print | `printers:control` |
| Bed jog, home, chamber light, print speed, airduct, skip-object, clear-HMS | `printers:control` |
| Clear plate (ack наступного job) | `printers:clear_plate` |
| Прив'язати/відв'язати smart plug | `printers:control` + `smart_plugs:write` |
| Додати/видалити принтери, factory-reset, firmware push | `printers:admin` |

---

## :material-link: Дивіться також

- [Monitoring](monitoring.md) — live status display, на якому ці контроли сидять
- [Print Queue](print-queue.md) — clear-plate handshake, dispatch flow
- [Smart Plugs](smart-plugs.md) — power on/off, auto-power-off thresholds, plug bindings
- [Macros](macros.md) — multi-step custom actions, які можна запалити з меню картки
- [AMS](ams.md) — load / unload / calibrate
- [Notifications](notifications.md) — маршрутизація pause / stop / fail подій

---

## :material-lightbulb: Поради

!!! tip "Підтверджуйте перед bulk stop"
    Bulk Stop незворотний. Toolbar показує одне підтвердження на весь batch — перечитайте count перед клік-через.

!!! tip "Skip кращий за stop"
    Якщо один з восьми об'єктів на plate відвалився, але решта ОК — **Skip Object** дотягує друк. Stop втрачає все.

!!! tip "Спершу force MQTT refresh"
    Коли картка виглядає застряглою на stale-значенні, **Force Refresh** (pushall) — найдешевший фікс. Restart коннекту — лише якщо pushall не допоміг.

!!! tip "Auto-power-off потребує thermal cool-down"
    Не виставляйте cooldown threshold надто агресивно — ріжучи живлення гарячого chamber, ви стресите ABS-друки і можете лишити toolhead теплою без fan'у.
