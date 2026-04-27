---
title: Віртуальний принтер
description: Емуляція принтера Bambu для надсилання друків зі слайсера, з review/auto-dispatch маршрутами і підтримкою PASV-NAT
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

VP працює в **рівно одному з трьох режимів**. Режим задається per-VP і валідується сервером — будь-що інше відхиляється з HTTP 400.

| Режим | Що відбувається з аплоадами | Use case |
|-------|----------------------------|----------|
| **`file_manager`** (дефолт) | Аплоад лягає в `/pending-uploads` як **review-item**. З review-модалки оператор може диспатчити на реальний принтер, масово заархівувати (без друку) або відхилити. | Multi-user / multi-machine inbox, де кожен аплоад проходить sanity-check перед друком — також правильний режим, якщо ви хочете лише **архівувати** без друку (через bulk-archive у review-модалці). |
| **`print_queue`** | Аплоад архівується **і** ставиться в чергу на цільовий принтер. З `auto_dispatch=true` queue item стартує одразу; з `auto_dispatch=false` чекає на explicit Start-клік. | Hands-off production: slice → send → BamDude друкує. |
| **`proxy`** | TLS-сесія слайсера TCP-проксується на реальний `target_printer_id` — BamDude лише публічний endpoint. | Віддалений друк — слайсер достукується до BamDude через LAN/VPN, BamDude достукується до принтера. |

!!! info "Окремого режиму ‘тільки архівувати’ немає"
    Раніше ця сторінка згадувала режим `immediate`, який нібито автоматично створює archive-рядок без черги і бібліотеки. **Такого режиму в коді не було ніколи** — документація брехала. Mode-енум у коді — це рівно три варіанти вище (див. `backend/app/models/virtual_printer.py` та валідатор у `backend/app/api/routes/virtual_printers.py`). Щоб отримати "тільки архівувати", використовуйте `file_manager` + bulk-archive у review-модалці — це створить рядок у `print_archives` і навіть не зачепить принтер.

---

## :material-cog: Налаштування

**Налаштування → Virtual Printer → Add Virtual Printer**:

| Поле | Примітки |
|------|----------|
| Name | Display-лейбл (наприклад, `Studio inbox`). |
| Model | SSDP model code — оберіть модель принтера, яку VP має імперсонувати, щоб compatibility checks слайсера проходили. |
| Bind IP | Опціональне. Залиште порожнім — VP слухатиме `0.0.0.0` (усі інтерфейси хоста), цього досить для одного VP на стандартних портах. Виділений IP потрібен лише коли запускаєте **кілька VP одночасно**, щоб у кожного був свій FTPS / MQTT / SSDP-listener. На Linux найпростіший шлях додати IP — virtual interface (alias) на хості. |
| Access code | 8-символьний код, яким автентифікується слайсер. |
| Mode | Один з трьох вище (`file_manager` / `print_queue` / `proxy`). |
| Auto-dispatch | Тільки для режиму `print_queue` — див. нижче. |
| Target printer | Тільки для режиму `proxy` — реальний принтер, на який пробрасувати. |

Слайсери виявляють новий VP через SSDP автоматично за хвилину-дві. Якщо discovery не спрацював, додайте вручну за IP + access-кодом.

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

## :material-flash: Auto-dispatch (режим print_queue)

VP у режимі `print_queue` з `auto_dispatch=true` повністю пропускає review:

- Слайсер "Send to Printer" → VP приймає аплоад через FTPS
- VP створює queue item, цільований на реальний принтер за вашою політикою
- Background dispatch підбирає його як будь-який інший queue item — без operator-кроку

Поставте `auto_dispatch=false`, якщо хочете, щоб кожен поставлений у чергу аплоад чекав explicit Start-кліку в queue UI перед диспатчем.

!!! tip "Тільки trusted upstream"
    Auto-dispatch прибирає human gate. Використовуйте його, коли upstream-джерело — це ви самі або trusted-автоматизація (slicer plugin, CI job, MakerWorld webhook). Для shared / multi-tenant аплоадів краще режим `file_manager` + review-модалка.

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
- **Hands-off диспатч** — `print_queue` + `auto_dispatch=true` — це найближче, що ви отримаєте до "Cloud Print, але локально".
- **Ручний gate на черзі** — `print_queue` + `auto_dispatch=false` ставить аплоад у чергу, але чекає на explicit Start-клік перед тим, як диспетчер його забере.
- **Віддалений друк** — режим `proxy` пробрасує remote-слайсера TLS-сесію прямо в реальний принтер, з сертифікатом BamDude як публічним обличчям.

---

## :material-lightbulb: Поради

!!! tip "Один VP на workflow"
    Ніщо не заважає крутити кілька VP одночасно на різних IP — один на production auto-dispatch, один на review, один на архівування. Вони шарять той самий backend, тож усі дані залишаються уніфікованими.

!!! tip "Slicer auth caching"
    Bambu Studio / OrcaSlicer кешують access-код per discovered принтер. Поверніть VP access-код — і слайсери знову спитають, без ручної очистки кешу.

> Початково базується на документації [Bambuddy](https://github.com/maziggy/bambuddy).
