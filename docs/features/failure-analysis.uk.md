---
title: Аналіз невдач
description: Знаходьте патерни у невдалих друках через історію архіву BamDude
---

# Аналіз невдач (Failure Analysis)

Розумійте *чому* друки падають, аналізуючи патерни за матеріалом, принтером, часом доби та тривалістю друку. Failure Analysis — це **ретроспективне** доповнення до [Obico AI Detection](obico.md), який ловить fail'и **проактивно**, поки вони відбуваються.

---

## :material-information: Що це

Дашборд Failure Analysis читає кожен рядок таблиці `print_archives`, чий `status` дорівнює `failed`, `aborted` або `cancelled`, і групує його за кількома вимірами — щоб ви побачили, чи якийсь конкретний принтер, філамент або час доби тягне ваш success-rate донизу.

Дані рахуються наживо у `FailureAnalysisService` (`backend/app/services/failure_analysis.py`) — окремої агрегованої таблиці немає. Кожен запит враховує обраний діапазон дат і опціональні фільтри printer / project.

!!! info "Потрібен дозвіл"
    Усі вьюхи Failure Analysis закриті дозволом `stats:read`. Viewers і Operators мають його за замовчуванням; Administrators — завжди.

---

## :material-chart-pie: Дашборд Failure Rate

Зверху сторінки Statistics — загальна картина за вибраний період:

| Метрика | Опис |
|---------|------|
| **Total prints** | Кожен архів, що не був чистим аплоудом (status `archived` виключено) |
| **Failed prints** | Сума `failed` + `aborted` + `cancelled` |
| **Failure rate (%)** | `failed / total × 100`, до однієї десяткової |
| **Trend** | Тижневий бакет failure-rate за період — improving, stable, worsening |

```
Total: 412   Failed: 27   Rate: 6.6%
```

Trend chart складає архіви у тижневі бакети (`created_at`) і малює `failure_rate` по кожному. Старіші бакети — спершу, поточний тиждень — останній.

---

## :material-link-variant: Кореляційні вьюхи

Розрізайте набір невдач за чотирма незалежними осями. Кожна діаграма — це серверний `GROUP BY` по підмножині failed-архівів.

### За типом філаменту

| Матеріал | Невдач |
|----------|:------:|
| PLA | 4 |
| PETG | 9 |
| ABS | 11 |
| TPU | 3 |

Береться з `PrintArchive.filament_type`. Якщо один матеріал домінує — це майже завжди вологість, температура або тюнінг bed-adhesion для цього матеріалу, а не глобальна проблема.

### За принтером

| Принтер | Невдач |
|---------|:------:|
| Workshop X1C | 2 |
| Office P1S | 7 |
| Garage A1 | 18 |

Береться з `PrintArchive.printer_id`, join до `printers.name`. Один принтер з більшістю невдач — сильний сигнал на сервіс заліза: брудне сопло, зношені ременi, збита bed calibration.

### За часом доби

24-годинний heatmap із `PrintArchive.started_at.hour`. Корисно для environmental issues:

- Нічні піки → падіння температури в майстерні, ABS warping
- Денні піки → пряме сонце на принтер, протяги
- Концентровані "Monday morning" fail'и → cold-start issues

### За тривалістю друку

Довгі друки мають більше шансів зламатись. Вьюха бінить архіви на:

| Бакет | Типовий ризик |
|-------|---------------|
| < 1 г | Bed adhesion, first-layer |
| 1–4 г | Layer adhesion, легкий warping |
| 4–12 г | AMS swap mid-print, заплутування філаменту |
| > 12 г | Power events, перепади температури, AI detection saves |

---

## :material-text-box-search: Поширені failure modes

Глосарій того, що ці fail'и зазвичай означають — корисно при читанні рядків `failure_reason` на картках архівів.

### Adhesion / First-Layer

- Друк зриває з столу
- Warped кути на перших 5–10 шарах
- Причини: брудний стіл, неправильна bed temp, вологий філамент, відсутній brim

### Layer Shift

- Раптовий зсув по X або Y
- Причини: проковзування ременя, удар гантри, головка врізалась у друк, вібрація від сусіднього принтера

### Spaghetti

- Заплутана купа філаменту там, де колись стояла модель
- Корінна причина — майже завжди попередній layer-shift або adhesion fail, який не зловили вчасно
- Саме це [Obico](obico.md) має детектити проактивно

### Stringing / Oozing

- Нитки між окремими частинами
- Краплі на top-surface
- Це quality issue, не hard fail — але якщо сильно, ви помітите архів як failed

### Filament Jam / Runout

- AMS повідомляє про порожній tray
- Екструдер шкребе, температура стрибає
- Multi-color друки з поганою swap-калібровкою тригерять це найчастіше

### AMS Swap Mid-Print

- Неправильний колір на точці свопу
- Tower contamination
- Часто корелює з retry'ями `subtask_id` після пере-планування черги

### OOM During Slicing

- Це не fail друку як такий, але слайсер впав по пам'яті під час prep, gcode обрубився, і принтер aborted посередині
- Зазвичай ловиться до черги, але логується як `failed` якщо друк реально стартував

---

## :material-magnify: Drilldown

Клік по будь-якій клітинці у будь-якій кореляційній вьюсі — і BamDude відкриває сторінку [Archives](archiving.md) з **відповідним фільтром**: наприклад, *Failures by Printer → Garage A1* фільтрує архів-лист до failed-друків саме цього принтера. Звідти ви можете:

- Відкрити 3MF кожного архіву і побачити, яка plate / які об'єкти
- Дописати `failure_reason`, якщо принтер сам нічого не повідомив
- Затегати архів (`adhesion-fail`, `layer-shift`, `ams-jam`, …) для майбутніх фільтрів
- Порівняти з відомо-успішним друком тієї ж моделі

---

## :material-calendar-range: Date Range Picker

Дашборд підтримує чотири built-in діапазони + custom picker:

| Діапазон | Ефективне вікно |
|----------|-----------------|
| Last 7 days | `now − 7d` до `now` |
| Last 30 days | `now − 30d` до `now` |
| Last 90 days | `now − 90d` до `now` |
| Last 365 days | `now − 365d` до `now` |
| Custom | Включно `date_from` … `date_to` |

Коли є `date_from` / `date_to`, тижневі бакети trend'у покривають явний діапазон; інакше йдуть за rolling-вікном `days`. Default коли діапазон не задано — **30 днів**.

---

## :material-eye: Proactive vs Retrospective

Failure Analysis каже вам, *що вже зламалося*. Щоб зупинити друк посеред fail'у замість autopsy потім:

| Інструмент | Коли |
|------------|------|
| [Obico AI Detection](obico.md) | Поки друк іде — захоплює камеру, класифікує кадри, тригерить notify / pause / pause+power-off |
| **Failure Analysis** | Постфактум — ріжете історію архіву на патерни |
| [Notifications](notifications.md) | У момент fail'у — Telegram/Discord/email/Pushover/ntfy/HA push |

Використовуйте разом: Obico ловить наступний spaghetti, Failure Analysis каже, *який саме принтер* їх постійно продукує.

---

## :material-export: Експорт

Ті самі числа годують сторінку [Export](export.md). `GET /api/v1/archives/stats/export` повертає CSV/XLSX з summary, розбивкою per-reason / per-filament / per-printer і тижневим trend'ом — зручно для monthly reporting або для подачі у BI tool.

---

## :material-link: Дивіться також

- [Statistics](stats.uk.md) — ширша аналітика (витрата філаменту, енергія, кости)
- [Archiving](archiving.md) — таблиця `print_archives` та її поля `status` / `failure_reason`
- [Obico AI Detection](obico.md) — proactive failure detection
- [Notifications](notifications.md) — маршрутизація алертів для failure events

---

## :material-lightbulb: Поради

!!! tip "Не видаляйте failed-друки"
    Це і є дані. Кожен видалений fail — це діра в аналізі.

!!! tip "Тегайте послідовно"
    Виберіть невеликий тег-словник (`adhesion-fail`, `layer-shift`, `ams-jam`, `spaghetti`, `warping`) і дотримуйтесь — саме це робить drilldown-фільтри корисними через місяці.

!!! tip "Фотографуйте стіл"
    Додавайте фото до кожного failed архіву. Сторінка Statistics не покаже фото, але коли ви крос-референсите серію fail'ів `Garage A1`, bed-фото за дві секунди скажуть, чи це adhesion, чи head crash.

!!! tip "Порівнюйте з успіхом"
    Найкорисніший дебаг-крок — відкрити failed архів поруч із успішним друком тієї ж моделі на тому ж принтері. Дельта slicing-параметрів зазвичай показує причину прямо.
