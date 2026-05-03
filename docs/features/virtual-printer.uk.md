---
title: Віртуальний принтер
description: Емуляція принтера Bambu для надсилання друків зі слайсера — review, per-printer queue, auto-queue або proxy
---

# Віртуальний принтер

Віртуальний принтер (VP) робить так, що BamDude з'являється у вашій LAN як один або кілька принтерів Bambu Lab. "Send to Printer" з Bambu Studio / OrcaSlicer лягає на VP так само, як він лягав би на справжній принтер — через захищений TLS (MQTT + FTPS) з access-кодом принтера. Далі BamDude роутить аплоад згідно з режимом VP.

---

## :material-printer-3d: Огляд

Кожен VP:

- Анонсує себе через **SSDP** з реальним кодом моделі Bambu (X1C / P1S / A1 Mini / H2D / …), щоб слайсери виявляли його автоматично.
- Запускає **власні FTPS + MQTT + SSDP сервери**. За замовчуванням слухає на `0.0.0.0` (усі інтерфейси хоста); якщо потрібно кілька VP одночасно — даєте кожному свій `bind_ip`, щоб вони не конфліктували за порти.
- Несе **access-код**, як справжній принтер — слайсери питають його при першому використанні і кешують потім.
- Має **серійний номер** і **код моделі**, що збігаються з реальним форматом Bambu, — тож compatibility checks слайсера проходять.

---

## :material-swap-horizontal: Режими

VP працює в **рівно одному режимі**. Режим задається per-VP і валідується сервером — будь-що інше відхиляється з HTTP 400.

| Режим | Що відбувається з аплоадами | Use case |
|-------|----------------------------|----------|
| **`file_manager`** (дефолт) | Аплоад лягає в `/pending-uploads` як **review-item**. З review-модалки оператор може диспатчити на реальний принтер, масово заархівувати (без друку) або відхилити. | Multi-user / multi-machine inbox, де кожен аплоад проходить sanity-check перед друком — також правильний режим, якщо ви хочете лише **архівувати** без друку (через bulk-archive у review-модалці). |
| **`print_queue`** | Аплоад архівується **і** ставиться в чергу на **конкретний** цільовий принтер. З `auto_dispatch=true` queue item стартує одразу; з `auto_dispatch=false` чекає на explicit Start-клік. | Аплоади з цього VP завжди їдуть на ту саму машину. |
| **`auto_queue`** | Аплоад архівується і кидається в **[авто-чергу](auto-queue.md)** — без фіксованого таргету. Планувальник сам обирає будь-який придатний вільний принтер (за моделлю + філаментом + кольором). | Hands-off load-balancing на ферму з кількох принтерів. |
| **`proxy`** | TLS-сесія слайсера TCP-проксується на реальний `target_printer_id` — BamDude лише публічний endpoint. | Віддалений друк — слайсер достукується до BamDude через LAN/VPN, BamDude достукується до принтера. |

!!! info "Окремого режиму ‘тільки архівувати’ немає"
    Раніше ця сторінка згадувала режим `immediate`, який нібито автоматично створює archive-рядок без черги і бібліотеки. **Такого режиму в коді не було ніколи** — документація брехала. Mode-енум у коді — це рівно чотири варіанти вище (див. `backend/app/models/virtual_printer.py` та валідатор у `backend/app/api/routes/virtual_printers.py`). Щоб отримати "тільки архівувати", використовуйте `file_manager` + bulk-archive у review-модалці — це створить рядок у `print_archives` і навіть не зачепить принтер.

---

## :material-cog: Налаштування

**Налаштування → Virtual Printer → Add Virtual Printer**:

| Поле | Примітки |
|------|----------|
| Name | Display-лейбл (наприклад, `Studio inbox`). |
| Model | SSDP model code — оберіть модель принтера, яку VP має імперсонувати, щоб compatibility checks слайсера проходили. |
| Bind IP | Опціональне. Залиште порожнім — VP слухатиме `0.0.0.0` (усі інтерфейси хоста), цього досить для одного VP на стандартних портах. Виділений IP потрібен лише коли запускаєте **кілька VP одночасно**, щоб у кожного був свій FTPS / MQTT / SSDP-listener. На Linux найпростіший шлях додати IP — virtual interface (alias) на хості. |
| Access code | 8-символьний код, яким автентифікується слайсер. |
| Mode | Один з чотирьох вище. |
| Auto-dispatch | Активний у режимах `print_queue` і `auto_queue` — див. нижче. |
| Target printer | Тільки для режиму `print_queue` (конкретний таргет) і `proxy`. Прихований коли вибрано `auto_queue` або `file_manager`. |

Слайсери виявляють новий VP через SSDP автоматично за хвилину-дві. Якщо discovery не спрацював, додайте вручну за IP + access-кодом.

---

## :material-form-select: UI вибору режиму

Діалог Add / Edit показує чотири режими як **три великі кнопки** + sub-toggle — бо `print_queue` і `auto_queue` це по суті два варіанти одного й того самого (диспатч у чергу, з фіксованим таргетом vs без):

```
┌──────────────────────────────────────────────────────────┐
│  Mode                                                    │
│  ┌─────────────┬───────────────┬──────────────────────┐  │
│  │   Queue     │  File Manager │    ⇄  Proxy          │  │
│  └─────────────┴───────────────┴──────────────────────┘  │
│                                                          │
│  Коли вибрано Queue:                                     │
│    [ ] Auto-select printer  ← тогл                       │
│        on  → mode = auto_queue                           │
│        off → mode = print_queue + поле Target Printer    │
│                                                          │
│  Auto-dispatch                          [ ]              │
└──────────────────────────────────────────────────────────┘
```

Коли **Queue → Auto-select printer = on** — VP у режимі `auto_queue`, дропдаун Target Printer зникає (будь-який принтер відповідної моделі підбере). Коли **Auto-select = off** — режим `print_queue` і дропдаун Target Printer, на який завжди йдуть аплоади.

`file_manager` і `proxy` — це окремі повноширокі кнопки.

### Звʼязка Model ↔ Target Printer

У режимі `print_queue` діалог звʼязує Model і Target Printer, щоб не вийшло несумісної пари:

- Вибираєш **Target Printer** — Model автоматично заповнюється з моделі того принтера.
- Вибираєш **Model** — список Target Printer фільтрується за цією моделлю. Якщо раніше вибраний таргет не підходить новій моделі — діалог чистить його.
- В полі Target Printer є явна **кнопка очистки (×)**, якщо хочеш скинути вибір без зміни моделі.

---

## :material-shield-alert: Правила валідації

Backend (`POST /virtual-printers/`, `PUT /virtual-printers/{id}`) енфорсить:

| Правило | Помилка |
|---------|---------|
| `mode='print_queue'` + `auto_dispatch=true` + немає `target_printer_id` (і не перемикаєшся в auto-select) | **400** — *"Auto-dispatch in Queue mode requires a Target Printer. Pick a target, enable Auto-select printer, or turn Auto-dispatch off."* |
| `mode='proxy'` без `target_printer_id` | **400** — *"Proxy mode requires a Target Printer."* |
| Будь-яке інше значення `mode` | **400** — *"Invalid mode."* |

Маршрут `PUT` перевіряє **остаточний** стан після застосування body — не можна обійти правило, чистячи поля по одному. Якщо треба прибрати існуючий таргет — шли `clear_target_printer: true` (кнопка × в діалозі це й робить).

Frontend дзеркалить це жовтим попередженням, що відключає тогл Auto-dispatch, коли комбінація небезпечна — обмеження видно ще до сабміту.

---

## :material-clipboard-check: Review-модалка (режим file_manager)

У режимі `file_manager` кожен завантажений 3MF лягає в **review queue** на `/pending-uploads`. З review-модалки оператор:

1. Відкриває аплоад, бачить розпарсений metadata + мініатюру.
2. Обирає цільовий реальний принтер.
3. Перевіряє AMS slot mapping, вибір плити і будь-які per-print опції.
4. Натискає **Send to Printer** — 3MF диспатчиться через стандартний background-dispatch pipeline (FTP-аплоад, swap macros, archive linkage).

Review-батчі також можна **архівувати масово** (без друку, просто заскладувати metadata) або **відхилити** (видаляє аплоад). Корисно, коли кілька юзерів / машин слайсять у один і той же VP, і ви хочете sanity-check, перш ніж це справді доб'ється до принтера.

API: `GET /api/v1/pending-uploads/`, `POST /api/v1/pending-uploads/{id}/archive`, `POST /api/v1/pending-uploads/archive-all`.

---

## :material-flash: Auto-dispatch (режими черги) {#auto-dispatch}

VP у будь-якому режимі черги (`print_queue` чи `auto_queue`) підкоряється флагу `auto_dispatch`:

| `auto_dispatch` | `print_queue` | `auto_queue` |
|-----------------|---------------|--------------|
| **true** | Аплоад зі слайсера → архівується → ставиться в чергу → диспатчиться одразу. | Аплоад зі слайсера → архівується → кидається в [авто-чергу](auto-queue.md) → наступний 30-секундний тік призначає елемент придатному вільному принтеру. |
| **false** | Аплоад зі слайсера → архівується → стає в чергу як `pending`, чекає на explicit Start-клік у queue UI. | Аплоад зі слайсера → архівується → router-рядок створюється з `manual_start=true`, тож планувальник його ігнорує, поки не звільниш через панель авто-черги. |

!!! tip "Тільки trusted upstream"
    Auto-dispatch прибирає human gate. Використовуйте його, коли upstream-джерело — це ви самі або trusted-автоматизація (slicer plugin, CI job, MakerWorld webhook). Для shared / multi-tenant аплоадів краще режим `file_manager` + review-модалка.

---

## :material-router-network: Режим auto_queue {#auto_queue}

`auto_queue` — це природна спарка ВП з [авто-чергою](auto-queue.md). На отриманні аплоада ВП:

1. Архівує 3MF (повна per-plate metadata, мініатюри, source-hash chain).
2. Викликає `extract_auto_queue_requirements` на заархівованому файлі — витягує:
    - `target_model` (з `sliced_for_model` у 3MF)
    - `required_filament_types` (з `slice_info.config`)
    - `plate_id`, якщо слайсер вказав конкретний плейт
3. Створює `AutoQueueItem` з `manual_start = !auto_dispatch`.
4. Повертає FTPS-успіх слайсеру — той самий UX, що й справжній принтер, який прийняв файл.

Далі підхоплює маршрутизатор: 30-секундний тік, пошук придатного принтера, AMS-мапінг на момент призначення. Повний потік маршрутизації — у [доку про авто-чергу](auto-queue.md).

У режимі `auto_queue` поля Target Printer не існує — це й сенс. Діалог приховує його і чистить значення, якщо лишилося після переключення режиму.

---

## :material-file-edit-outline: Джерело імені архіву

За замовчуванням 3MF, заархівований через VP, бере display-name з `print_name` з project-метадаt — це зазвичай людськочитабельне "Calibration Cube v3", набране оператором у Bambu Studio. Деякі workflow'и віддадуть перевагу **upload-filename** замість того — наприклад, batch-система, що називає кожен upload `2026-04-30_jobid-1234.gcode.3mf` і хоче зберегти ці ідентифікатори як є.

**Settings → Virtual Printer → Archive name source**:

| Значення | Ефект |
|---|---|
| `metadata` (default) | Брати 3MF-метадані `print_name`. Падає на filename, якщо метадані відсутні. |
| `filename` | Брати stem upload-filename'а. Падає на метадані, якщо filename порожній / generic. |

Тоглер install-wide, застосовується до кожного VP крім `proxy`-mode (proxy-uploads BamDude'ом не архівуються — flow архіву реального принтера бере на себе).

---

## :material-network-outline: PASV Address (NAT / Docker bridge)

FTPS використовує команду PASV — сервер каже клієнту, на який IP передзвонити для data-каналу. Коли BamDude працює в Docker bridge мережі (або за будь-яким NAT), PASV-відповідь інакше анонсувала б **внутрішній IP контейнера** — слайсери в LAN не зможуть до нього достукатися, і data-канал зафейлиться посеред handshake-у.

Поставте env-змінну `VIRTUAL_PRINTER_PASV_ADDRESS` на **externally-reachable IP** (LAN-адресу хоста — більшість слайсерів тут не резолвлять hostnames):

```bash
VIRTUAL_PRINTER_PASV_ADDRESS=192.168.1.100
```

FTPS-сервер стартує, логує `FTP PASV address override: 192.168.1.100`, і відтепер кожна PASV-відповідь використовує цю адресу. Не має ефекту, коли BamDude крутиться на host-мережі — там не задавайте.

---

## :material-rocket: Use cases

- **Multi-user farm inbox** — `file_manager` + review-модалка дозволяє кільком людям слайсити у той же VP, не наступаючи одне одному на ноги.
- **Архівування друку без друку** — `file_manager` + дія **bulk-archive** у review-модалці перетворює slice → send на постійний запис (мініатюри, metadata, source 3MF) без коміту до друку.
- **Збирання бібліотеки** — той самий `file_manager`: архівуйте аплоади з review-модалки, щоб прикріплювати їх до проєктів, batch-друкувати або шарити з командою до першого білда.
- **Hands-off на одну машину** — `print_queue` з фіксованим Target Printer + `auto_dispatch=true` — це найближче до "Cloud Print, але локально" для одного принтера.
- **Ручний gate на черзі** — `print_queue` + `auto_dispatch=false` ставить аплоад у чергу, але чекає на explicit Start-клік перед тим, як диспетчер його забере.
- **Load-balancing на фермі** — `auto_queue` + `auto_dispatch=true` — це killer-флоу для багатопринтерної ферми: слайсер не знає, який принтер виконуватиме друк, маршрутизатор обирає на момент диспатчу.
- **Віддалений друк** — режим `proxy` пробрасує remote-слайсера TLS-сесію прямо в реальний принтер, з сертифікатом BamDude як публічним обличчям.

---

## :material-lightbulb: Поради

!!! tip "Один VP на workflow"
    Ніщо не заважає крутити кілька VP одночасно на різних IP — один на production auto-dispatch, один на review, один на архівування. Вони шарять той самий backend, тож усі дані залишаються уніфікованими.

!!! tip "Slicer auth caching"
    Bambu Studio / OrcaSlicer кешують access-код per discovered принтер. Поверніть VP access-код — і слайсери знову спитають, без ручної очистки кешу.

> Початково базується на документації [Bambuddy](https://github.com/maziggy/bambuddy).
