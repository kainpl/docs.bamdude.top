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
