---
title: Сповіщення
description: Push-сповіщення про події друку через різні провайдери
---

# Сповіщення

Дев'ять каналів доставки, один редактор, одна конфігурація маршрутизації. Підпиши кожен провайдер на потрібні події, постав тихі години й щоденний digest на провайдер, кастомізуй шаблони на мову.

---

## :material-bell-ring: Підтримувані провайдери

| Провайдер | Складність | Можливості |
|-----------|:----------:|------------|
| **Telegram** | Середньо | Через бота BamDude з actionable inline-кнопками (clear plate, mark maintenance done, pause/stop). Розсилається в кожен авторизований чат, який підписаний на подію. |
| **Discord** | Легко | URL webhook каналу, форматування embed, прикріплення картинок. |
| **Email (SMTP)** | Середньо | STARTTLS / SSL / plain. Per-provider `to_email` — різні юзери бачать різні тіла. |
| **Pushover** | Легко | Рівні пріоритету, прикріплення картинок до 2.5 МБ. |
| **ntfy** | Легко | Topic-based, опційний bearer-токен, прикріплення картинок. |
| **Bark** | Легко | Тільки iOS, без акаунта. Рівні переривання — **Critical** доставляє крізь Silent mode і Focus. Публічний релей або власний `bark-server`. |
| **CallMeBot** | Легко | Bridge до WhatsApp / Signal — телефон + API-ключ, URL-encoded повідомлення. |
| **Home Assistant** | Легко | `persistent_notification.create` або будь-який `notify.*` сервіс. Глобальний URL/token Home Assistant з Settings (або `HA_URL` / `HA_TOKEN` env). |
| **Webhook** | Гнучко | Generic JSON або Slack-format POST, кастомні імена полів, base64 картинка, опційний bearer. |

---

## :material-plus-circle: Додавання провайдера

1. Перейдіть до **Settings** > **Notifications**
2. Натисніть **Add Provider**
3. Виберіть тип провайдера та введіть конфігурацію
4. Натисніть **Send Test** для перевірки
5. Налаштуйте тригери подій
6. Натисніть **Add**

---

## :material-cog: Налаштування на провайдер

### ntfy

Topic-based, безкоштовно, без облікового запису. Найпростіший канал, щоб підняти.

| Поле | Значення |
|---|---|
| **Server** | `https://ntfy.sh` (default) або URL власної self-hosted інстанції |
| **Topic** | Унікальний рядок — будь-хто, хто його знає, може писати, тож роби невідгадуваним |
| **Bearer token** | Опційно; потрібно для self-hosted topic-ів за ACL |

Підпишись на телефоні через [ntfy Android](https://play.google.com/store/apps/details?id=io.heckel.ntfy) чи [iOS](https://apps.apple.com/app/ntfy/id1625396347). ntfy підтримує **5 рівнів priority**, які BamDude мапить на подію:

| Priority | ntfy value | Типове використання |
|---|---|---|
| **Min** | 1 | Diagnostics-style ping-и — без звуку, без бейджа |
| **Low** | 2 | Інформаційне, не-термінове (напр. "first layer complete") |
| **Default** | 3 | Стандартне сповіщення |
| **High** | 4 | Audible / urgent (напр. "filament low") |
| **Urgent** | 5 | Будить пристрій, ігнорує Do-Not-Disturb (напр. "print failed") |

### WhatsApp / Signal (CallMeBot)

Безкоштовний міст до WhatsApp / Signal — без власної бот-інфраструктури.

1. Додай CallMeBot у контакти: **+34 644 51 95 23**
2. Надішли `I allow callmebot to send me messages` через WhatsApp
3. CallMeBot відповість твоїм **API-ключем**

| Поле | Значення |
|---|---|
| **Phone number** | Твій номер у форматі E.164 (напр. `+1234567890`) |
| **API key** | Ключ, який повернув CallMeBot |

### Discord

URL webhook каналу — найпростіший спосіб закинути rich embed-повідомлення з мініатюрами в Discord-сервер.

1. У Discord відкрий settings цільового каналу → **Integrations** → **Webhooks**
2. Натисни **New Webhook**, кастомізуй ім'я/аватар, **Copy Webhook URL**
3. Встав URL у форму провайдера BamDude

BamDude постить як embed-и зі snapshot-картинкою inline, коли вона є.

### Pushover

Per-user push-сервіс з нативними iOS/Android-додатками і on-device priority-ескалацією.

1. Створи акаунт на [pushover.net](https://pushover.net/) і встанови додаток
2. Створи **Application** у дашборді

| Поле | Значення |
|---|---|
| **User key** | Зі сторінки твого акаунту Pushover |
| **API token** | З Application, який ти щойно створив |

Pushover priority мапиться на numeric levels `-2…+2` на подію в BamDude — ідея та сама, що й у ntfy, але зі шкалою Pushover.

!!! info "Priority 2 (Emergency) вимагає двох додаткових полів"
    Pushover **обов'язково** вимагає інтервал повтору й термін дії для Emergency-сповіщень: вони повторюються, доки їх не підтвердять, тож сервіс відхиляє будь-яке повідомлення з priority 2, де не вказано як часто і як довго. Виставте **Priority** у `2` — і з'являться два поля:

    | Поле | Значення | За замовчуванням |
    |---|---|---|
    | **Повтор екстреного сигналу (с)** | Як часто Pushover повторює | 60 с (мін. 30 с) |
    | **Термін дії екстреного сигналу (с)** | Коли припинити | 3600 с (макс. 10800 с) |

    Надсилаються лише при priority 2 — на решті рівнів Pushover їх ігнорує. До 0.4.7b4 BamDude не надсилав їх узагалі, тож провайдер із Emergency-пріоритетом валив кожне сповіщення.

### Bark (iOS)

[Bark](https://bark.day.app/) — безкоштовний iOS-застосунок для push, узагалі без акаунта: встанови, скопіюй device key, який він показує, встав сюди. Більше нічого не обов'язково.

| Поле | Значення |
|---|---|
| **Device Key** | Ключ, який Bark показує на першому екрані — **обов'язковий** |
| **Server** | `https://api.day.app` (типово) або власний `bark-server` |
| **Group** | Опційно — складе сповіщення BamDude в окрему групу в застосунку |
| **Sound** | Опційно — одна зі звукових назв зі списку Bark |
| **Interruption Level** | `Default` / `Active` / `Time Sensitive` / `Critical` |

!!! tip "Critical — саме те, заради чого Bark поруч із ntfy і Pushover"
    | Рівень | Що робить iOS |
    |---|---|
    | **Critical** | Доставляє **крізь Silent mode і крізь Focus** — друк, що став о 03:00, таки достукається |
    | **Time Sensitive** | Пробиває заплановані зведення, не заходячи так далеко |
    | **Active** | Звичайне сповіщення |
    | **Passive** | Приходить без звуку — записане, але не оголошене |

    Заведи *print failed* і *filament runout* на Critical-провайдер Bark, а решту лиши на Default-провайдері, замість будити себе кожною подією.

Самохостний `bark-server` підпадає під ті самі правила адрес, що й самохостний ntfy: у власній мережі — можна, усе, що не є справжнім HTTP-сервісом, — відхиляється. Якщо він за Cloudflare-челенджем, BamDude так і скаже, замість вивалити сторінку челенджа.

!!! info "«OK», який не OK"
    `bark-server` подекуди повідомляє про помилку **всередині** тіла з HTTP 200. BamDude читає тіло, а не довіряє статусу, — тож хибний device key у **Send Test** буде помилкою, а не «надіслано», яке нікуди не дійшло.

### SMTP / Gmail

Звичайний SMTP — працює з будь-яким провайдером, що дає username + password auth.

| Поле | Приклад |
|---|---|
| **SMTP host** | `smtp.gmail.com` |
| **Port** | `587` (STARTTLS) або `465` (SSL) |
| **Security** | `STARTTLS` / `SSL` / `plain` |
| **Username** | Повна email-адреса |
| **Password** | App password (не пароль акаунту — Gmail відхилить останній) |
| **From address** | Адреса відправника, яку бачать отримувачі |
| **To address** | Per-provider; дозволяє різним членам команди отримувати різні тіла |

Для Gmail: увімкни 2FA, потім згенеруй [App Password](https://myaccount.google.com/apppasswords) і використай його тут.

### Home Assistant

Zero-config, коли HA вже підключений у **Settings** → **Network** → **Home Assistant** (або через `HA_URL` / `HA_TOKEN` env vars). Якщо лишити поля порожніми, події стають викликами `persistent_notification.create` в дашборді HA.

| Поле | Значення |
|---|---|
| **Service** | Опційно — будь-який сервіс HA, напр. `notify.mobile_app_myphone`. Приймається як `notify.x`, `notify/x` або `api/services/notify/x`. Порожнє = `persistent_notification.create` |
| **Data (JSON)** | Опційно — JSON-**об'єкт**, який іде у вкладене `data` HA, тобто саме туди, куди його кладе автоматизація |

Поле **Data** — це те, від чого залежить поведінка Android-push. Опції mobile-app інтеграції HA живуть там, а не в заголовку й тексті:

```json
{ "priority": "high", "ttl": 0, "channel": "BamDude" }
```

`priority: high` + `ttl: 0` — саме те, від чого сповіщення приходить *негайно*, а не коли телефон наступного разу прокинеться; `channel` дає алертам принтерів власний звук, замість ховати їх серед усього іншого, що надсилає HA.

!!! info "Чому JSON, а не рядки `key=value`"
    Щоб `ttl: 0` лишався числом, якого чекає HA, і щоб вкладені опції взагалі були можливі. Поле перевіряється при збереженні **і** ще раз при надсиланні — некоректне відхиляється перед тобою, а не перетворюється на сповіщення, яке тихо ніколи не приходить.

    Лиши порожнім — і нічого не зміниться: воно надсилається, лише коли заповнене, бо `persistent_notification.create` відхиляє зайві ключі.

!!! tip "Форвард HA-сповіщень в інші канали"
    Використовуй HA-автоматизації, щоб дзеркалити persistent-сповіщення на HA Companion app, Telegram, ntfy тощо — отримаєш єдиний audit log в HA плюс звичний мобільний push.

### Generic Webhook

Для всього іншого — n8n, Node-RED, кастомні HTTP-ендпоінти, Slack-format інтеграції.

| Поле | Значення |
|---|---|
| **URL** | Твій ендпоінт (HTTPS рекомендовано) |
| **Headers** | Опційно — для `Authorization: Bearer …` тощо |
| **Format** | `generic` (структурований BamDude JSON) або `slack` (тільки `{"text": "..."}`) |

Дивись **Webhook Payload Schema** нижче для форми структурованого JSON.

---

## :material-code-json: Webhook Payload Schema

Generic-format webhooks шлють стандартизований JSON-конверт: `title`, `message`, `timestamp`, `source`, `event` (рядок типу події), плюс усі event-specific поля піднімаються на top-level ключі, тож automation-tools можуть branch-итися на `event` без парсингу message-тексту.

**`print_complete`:**

```json
{
  "title": "Print Complete",
  "message": "Workshop X1C: benchy.3mf completed in 2h 15m",
  "timestamp": "2026-04-02T14:30:00.123456",
  "source": "BamDude",
  "event": "print_complete",
  "printer": "Workshop X1C",
  "filename": "benchy.3mf",
  "duration": "2h 15m",
  "filament_grams": "15.2",
  "filament_details": "AMS-A T1 PLA: 15.2g"
}
```

**`print_failed`** (і `print_stopped`) несуть додаткові поля `progress` + `reason`:

```json
{
  "title": "Print Failed",
  "message": "Workshop X1C: benchy.3mf failed at 50%",
  "timestamp": "2026-04-02T15:15:00.123456",
  "source": "BamDude",
  "event": "print_failed",
  "printer": "Workshop X1C",
  "filename": "benchy.3mf",
  "duration": "0h 45m",
  "filament_grams": "7.6",
  "filament_details": "PLA: 7.6g",
  "progress": "50",
  "reason": "Filament runout"
}
```

**`printer_offline`** — мінімальний payload, тільки те, що релевантне:

```json
{
  "title": "Printer Offline",
  "message": "Workshop X1C is offline",
  "timestamp": "2026-04-02T14:30:00.123456",
  "source": "BamDude",
  "event": "printer_offline",
  "printer": "Workshop X1C"
}
```

**`first_layer_complete`** — включає base64-encoded JPEG-snapshot у полі `image`:

```json
{
  "title": "First Layer Complete",
  "message": "Workshop X1C: benchy.3mf — Layer 1/200 done",
  "timestamp": "2026-04-02T14:30:00.123456",
  "source": "BamDude",
  "event": "first_layer_complete",
  "printer": "Workshop X1C",
  "filename": "benchy.3mf",
  "total_layers": "200",
  "image": "/9j/4AAQSkZJRg..."
}
```

!!! tip "Декодування картинки"
    Поле `image` — стандартний base64-encoded JPEG. Home Assistant: передай у `notify.mobile_app_*` як `image` data через template. Node-RED: `Buffer.from(msg.payload.image, 'base64')`. Поле присутнє лише, коли snapshot реально був захоплений — не всі події його містять.

!!! info "Slack / Mattermost format compatibility"
    З **format = slack** шлеться тільки `{"text": "..."}` — структуровані поля події відкидаються. Юзай generic-формат для будь-якої automation, що читає структуровані дані; slack — лише для людино-читабельних channel-постів.

---

## :material-tune: Тригери подій

Кожен провайдер підписується незалежно. Вимкнення події на одному провайдері не зупиняє її на інших.

**Друк:**

| Подія | Спрацьовує коли |
|-------|------------------|
| `print_start` | Друк запустився на принтері |
| `first_layer_complete` | Завершився перший шар (швидко ловить first-layer фейли) |
| `print_progress` | На 25% / 50% / 75% прогресу. Глобальне налаштування **мінімальної тривалості** (Налаштування → Сповіщення) глушить їх для друків, коротших за N хвилин — тривалість оцінюється із власного remaining-time принтера на кожному milestone, а невідома оцінка шле, а не вгадує. `0` (типово) — слати завжди. Діє однаково на всі канали, включно з per-chat підписками Telegram. |
| `print_paused` | Принтер перейшов RUNNING→PAUSE — у тілі нормалізована `{reason}` (двері відкриті / філамент скінчився / presence-check / G-code pause / AI defect / об'єкти на платі / paused by user / HMS-other) плюс `{hms_code}` для forensics. За замовчуванням **ON** для нових провайдерів + входить у дефолтний event-набір Telegram-чату. |
| `print_resumed` | Принтер перейшов PAUSE→RUNNING — у тілі `{paused_for}` (mm:ss) обчислений по delta між edge'ами. За замовчуванням **ON** для нових провайдерів; opt-in для Telegram-чатів. |

Стан паузи також візуалізується на сторінці Принтерів у реальному часі — на картці paused-принтера поряд зі статусом з'являється маленький `<PauseChip>` із класифікованою причиною і живим mm:ss-лічильником, плюс жовта попереджувальна піпка в кутку. Чіп зникає у мить resume; resume-нотифікація несе те саме значення `{paused_for}`, що і chip відраховував.

| `print_complete` | Друк завершився успішно |
| `print_failed` | HMS-помилка / hardware-фейл зупинили друк |
| `print_stopped` | Користувач зупинив друк |
| `bed_cooled` | Стіл охолов до порогу (сигнал готовності зняти деталь) |

**AMS / філамент:**

| Подія | Спрацьовує коли |
|-------|------------------|
| `print_missing_spool_assignment` | Друк стартував без повного мапінгу spool→AMS |
| `filament_low` | Залишок котушки нижче `low_stock_threshold` |
| `ams_humidity_high` / `ams_temperature_high` | AMS перевищив свій поріг |
| `sensor_above_max` / `sensor_below_min` | Показ [датчика](sensors.md) вийшов за задані для нього межі |
| `sensor_back_in_range` | …і повернувся |
| `sensor_silent` / `sensor_speaking_again` | Датчик перестав звітувати — і почав знову |

**Принтер:**

| Подія | Спрацьовує коли |
|-------|------------------|
| `printer_offline` | MQTT-розрив |
| `printer_error` | Спрацював HMS-код (BamDude додає переклад людською) |
| `ai_failure_detection` | AI-детекція збою (Obico) позначила ймовірний провал друку — **opt-in, вимкнено за замовчуванням**. Виділено з `printer_error`, тож можна отримувати AI-алерти без кожного HMS-коду. Має власний шаблон, власний per-provider тоглер і власний per-chat Telegram-пункт; тіло несе принтер, назву роботи, оцінку впевненості та дію, яку виконав BamDude (notify / pause / pause + power off). |
| `plate_not_empty` | Bed-occupancy gate зловив старт наступного друку (auto-pause) |
| `maintenance_due` | Інтервал обслуговування досягнуто |

**Черга:**

| Подія | Спрацьовує коли |
|-------|------------------|
| `queue_job_added` / `queue_job_started` / `queue_job_waiting` / `queue_job_skipped` / `queue_job_failed` | Lifecycle черги. Тільки ті події, на які ти підписався. |
| `queue_completed` | Спорожніли черги **всієї інсталяції** — спрацьовує лише раз, коли кожен принтер idle і нічого не лишилось у черзі. |
| `printer_queue_completed` | Спорожніла **власна черга окремого принтера** — спрацьовує у мить, коли цей принтер завершив свою останню задачу, незалежно від того, що роблять інші принтери. |

!!! note "Глобальне vs. per-printer завершення черги"
    На setup-і з одним принтером ці дві події еквівалентні. На **багатопринтерній фермі** вони різняться: `queue_completed` чекає, поки idle стане *кожен* принтер, тож довга задача на одному принтері придушує подію для всіх інших. `printer_queue_completed` спрацьовує per-printer у мить, коли власна черга принтера спорожніла — обери цю, якщо хочеш ping "ця машина вільна, став наступну плату" на кожен принтер. `printer_queue_completed` **ON** за замовчуванням для нових провайдерів; `queue_completed` — off за замовчуванням.

**Користувач / система:**

| Подія | Спрацьовує коли |
|-------|------------------|
| `user_created`, `password_reset` | Account-management емейли (HTML + plain). |
| `user_print_start` / `user_print_complete` / `user_print_failed` / `user_print_stopped` | Per-user email коли користувач — власник друку. |
| `test` | Тест-надсилання з редактора провайдера. |

---

## :material-send: Інтерактивні сповіщення Telegram

При використанні Telegram як провайдера сповіщень BamDude надсилає інтерактивні сповіщення з вбудованими кнопками:

| Подія | Дії |
|-------|-----|
| **Print Complete** | Кнопка очищення пластини |
| **Maintenance Due** | Кнопка підтвердження виконання |
| **Print Progress** | Кнопки паузи / зупинки |

Докладніше у розділі [Налаштування Telegram-бота](telegram-bot.md).

!!! tip "Маршрутизація подій по чатах"
    Telegram-сповіщення не йдуть в один захардкоджений чат -- вони розсилаються в кожен авторизований чат, у якого `telegram_chats.notification_events` містить активну подію. Тож один чат може підписатися лише на "Print Complete" + "HMS Error", а інший -- забирати все. Підписки кожного чату налаштовуються в **Settings > Notifications > Telegram Chats**.

!!! tip "Локалізовані шаблони на користувача"
    Тіла сповіщень рендеряться з `notification_templates_{en,uk}.json`. Мова шаблону вибирається на отримувача -- Telegram бере `settings.language` користувача-власника чату, email бере мову користувача-отримувача тощо. Додавання нового ключа шаблону означає оновлення *обох* JSON-файлів `en` та `uk` (BamDude постачається лише з en + uk).

---

## :material-priority-high: Пріоритет на подію (ntfy і Pushover)

І ntfy, і Pushover підтримують priority-рівні — `default` / `high` / `urgent` для ntfy, `-2…+2` для Pushover. BamDude дає обрати priority **на тип події** на кожному провайдері, тож завершений друк не пушитиме на lock-screen, а провал друку — пушитиме:

| Тип події | Рекомендований ntfy-priority | Чому |
|---|---|---|
| `print_complete`, `bed_cooled` | `default` | Інформаційне — прочитається коли зручно. |
| `print_failed`, `printer_error`, `plate_not_empty` | `high` чи `urgent` | Потребує дії. |
| `filament_low`, `maintenance_due` | `default` | Plan-ahead, не interrupt-now. |
| `ams_humidity_high` | `high` | Стосується пластика, який ось-ось у роботу. |

Налаштовується в edit-формі провайдера: dropdown priority поряд з тоглером підписки на подію. Defaults мапять кожну подію на `default`-priority — opt-in escalation тільки де треба. Той самий контроль у Pushover приймає numeric levels.

Це незалежне від нижче daily-digest / quiet-hours pipeline'у — quiet-hour-suppressed подія не відсилається жодним priority; активна подія все одно поважає вибраний per-event priority.

---

## :material-clock: Тихі години і щоденний digest

Форма конфіга залежить від типу провайдера — Telegram-бот окремий випадок.

**Не-telegram провайдери (email / ntfy / pushover / discord / webhook / homeassistant / callmebot)** тримають обидва налаштування на самому provider-row:

| Налаштування | Де | Ефект |
|---|---|---|
| `quiet_hours_enabled` + `quiet_hours_start` / `quiet_hours_end` | Конфіг провайдера | Події всередині вікна викидаються (не чекають — quiet hours це "мовчати", не "відкласти"). |
| `daily_digest_enabled` + `daily_digest_time` | Конфіг провайдера | Події протягом дня зберігаються в `notification_digest_queue`; коли годинник переходить `daily_digest_time`, BamDude вислає чергу одним digest-повідомленням. |

**Telegram (m045)** структурований інакше: бот/provider-row тримає тільки **розклад** (`daily_digest_enabled` + `daily_digest_time`), а per-event opt-in, тихий час і per-chat digest opt-in живуть на кожному рядку `TelegramChat`. Один чат може бути в quiet-годинах, а інший залишатися гучним — обидва живляться одним ботом. Деталі per-chat-полів див. [Налаштування Telegram-бота](telegram-bot.uk.md).

---

## :material-file-document-edit: Редактор шаблонів

Кожна подія має дефолтний шаблон у `data/notification_templates_{en,uk}.json`. Вкладка Templates під Settings → Notifications дозволяє перевизначити будь-який — тітул + тіло — з MarkdownV2 toolbar і live-прев'ю.

Вкладка Templates групує дефолтні шаблони за призначенням, щоб одним поглядом було видно, який dispatch-шлях кожен з них живить:

| Група | К-ть | Для чого |
|---|---|---|
| **Print events** | 9 | `print_start/complete/failed/stopped/progress`, `plate_not_empty`, `bed_cooled`, `first_layer_complete`, `print_missing_spool_assignment` |
| **Printer status** | 4 | `printer_offline`, `printer_error`, `filament_low`, `maintenance_due` |
| **AMS environmental** | 2 | `ams_humidity_high`, `ams_temperature_high` (також reuse-яться у runtime для AMS-HT-подій) |
| **Print queue** | 7 | `queue_job_added/started/waiting/skipped/failed`, `queue_completed`, `printer_queue_completed` |
| **Job owner emails** | 4 | `user_print_start/complete/failed/stopped` — SMTP-only, шлеться власнику задачі друку |
| **System emails** | 2 | `user_created` (welcome), `password_reset` |
| **Test** | 1 | `test` — для кнопок "Send test" |

Кожна картка несе маленький UPPERCASE-бейдж каналу:

- **Зелений `ALL`** — фан-аут до всіх типів провайдерів (TG / email / ntfy / pushover / discord / webhook / homeassistant / callmebot). Записи у перших 4 групах.
- **Синій `EMAIL`** — SMTP-only флоу. 4× `user_print_*` job-owner emails плюс `user_created` / `password_reset`.
- **Амбер `TEST`** — внутрішній test-button helper.

Маппінг — це метадані про те, який dispatch-шлях кожен шаблон живить; не зберігаються на рядку, рендеряться зі статичної таблиці у frontend-і.

Підстановка змінних — простий `{plate_holder}` синтаксис (`{printer_name}`, `{filament_grams}`, `{eta}` і т.д.); схема залочена на подію, тож редактор сам попереджає, коли placeholder не резолвиться.

Шаблон вибирається **за мовою отримувача**: Telegram-чат, прив'язаний до оператора з `settings.language=uk`, отримає українське тіло; email до іншого юзера з `settings.language=en` — англійське. Нові ключі додавайте в **обидва** JSON-файли — BamDude постачається лише з en + uk.

---

## :material-email-newsletter: Приклад Daily Digest

Коли провайдер має `daily_digest_enabled` + `daily_digest_time` встановлене, кожна подія, яка спрацювала за день, кладеться в чергу і об'єднується в одне summary-повідомлення на digest-час:

```
Daily Print Summary (Apr 14)

3 prints completed
1 print failed
Total time: 8h 45m
Filament used: 245g

Details:
- Benchy (2h 15m) - completed
- Phone Stand (45m) - completed
- Cable Clip (15m) - completed
- Prototype v3 (3h 30m) - failed
```

Digest-повідомлення поважає той самий вибір мови шаблону, що й immediate-сповіщення — Telegram-чати, прив'язані до операторів з uk-мовою, отримують українське summary, а англомовний email-отримувач — англійське.

---

## :material-file-document-edit: Змінні шаблонів

Шаблони підставляють `{variable}`-плейсхолдери. Схема залочена на подію, тож редактор попереджає, коли використано невідомий плейсхолдер. Змінні згруповані за категорією події:

**Print events** (`print_start`, `print_complete`, `print_failed`, `print_stopped`, `print_progress`):

| Змінна | Значення |
|---|---|
| `{printer_name}` (alias `{printer}`) | Display-ім'я принтера |
| `{print_name}` (alias `{filename}`) | Файл, який зараз друкується |
| `{progress}` | % завершення (тільки failed/stopped) |
| `{eta_minutes}` / `{eta}` | Wall-clock час завершення |
| `{estimated_time}` | Прогнозована тривалість друку (напр. `1h 23m`) |
| `{duration}` | Реальний elapsed-час друку |
| `{filament_used_g}` (alias `{filament_grams}`) | Загальні грами (scaled by progress для фейлів) |
| `{filament_details}` | Per-spool breakdown (напр. `AMS-A T1 PLA: 15.2g`) |
| `{material}` | Aggregate material name |
| `{reason}` | Причина фейлу (тільки failed/stopped) |
| `{finish_photo_url}` | URL camera-snapshot (див. нижче) |

**Printer events** (`printer_offline`, `printer_error`):

| Змінна | Значення |
|---|---|
| `{printer_name}` | Display-ім'я принтера |
| `{error_code}` (alias `{error_type}`) | HMS error code |
| `{error_message}` (alias `{error_detail}`) | Людино-читабельний опис (BamDude перекладає каталог 853 кодів) |

**AMS events** (`ams_humidity_high`, `ams_temperature_high`, `filament_low`, `print_missing_spool_assignment`):

| Змінна | Значення |
|---|---|
| `{ams_id}` | AMS-юніт (`AMS-A`, `AMS-B`, …) |
| `{slot}` | Tray index (`T1`–`T4`) |
| `{material}` | Матеріал, призначений на слот |
| `{remaining_percent}` | Залишок філаменту (`filament_low`) |
| `{humidity}` | % вологості (humidity events) |
| `{missing_slots}` | Comma-separated лейбли слотів (`A1, A3`) для `print_missing_spool_assignment` |
| `{missing_slot_details}` | Per-slot breakdown з очікуваним профілем (`- A1: PLA Basic`) |

**Common для будь-якої події:** `{timestamp}`, `{app_name}` (завжди `"BamDude"`).

Натисни **Reset to default** у редакторі, щоб відновити оригінальний шаблон з `notification_templates_{en,uk}.json`.

### Finish Photo URL

Плейсхолдер `{finish_photo_url}` кладе camera-snapshot готової плити в сповіщення про завершення / провал. Потребує доступної external URL:

1. **Settings** → **System** → **External URL** — постав адресу, до якої отримувачі мають доступ (напр. `https://bamdude.example.com` чи `http://192.168.1.100:8000`)
2. Налаштування auto-detect-иться з браузера, коли вперше відкриваєш System settings
3. Відредагуй шаблон і додай `{finish_photo_url}` куди хочеш фото

!!! tip "Email вшиває фото inline, не лише посилання"
    Для **email**-провайдерів, коли підставлений `{finish_photo_url}` присутній у тілі **і** finish-фото справді зроблено, BamDude шле лист як `multipart/related` зі вбудованим inline JPEG (через `Content-ID`, на який посилається HTML-частина) — фото видно прямо в тілі листа, а не як голе посилання. Plain-text альтернатива й далі несе клікабельний URL для text-only клієнтів. Коли шаблон не містить `{finish_photo_url}` (або фото немає), використовується звичайний single-part text-лист — без несподіваного attachment-а. Не-email канали (WhatsApp / webhook / …) й далі отримують посилання — тому External URL нижче має бути досяжним.

!!! note "External URL — обов'язкова умова"
    Без сконфігурованого External URL плейсхолдер рендериться порожнім. Camera-snapshot-и також ходять через [stream-token camera flow](authentication.uk.md) — URL вшиває short-lived токен, тож отримувач забирає JPEG без Authorization-хедера.

---

## :material-bell-off: Quick Disable

Глобальний mute-toggle живе у sidebar-і — клік по іконці дзвоника гасить **усі** вихідні сповіщення на **усіх** провайдерах, поки не клікнеш ще раз. Корисно під maintenance-вікно, demo-прогон чи галасливу міграцію, коли не хочеться флудити team-чат.

Toggle не видаляє digest-и-в-роботі — події, що впали в digest-чергу до mute, все одно вийдуть на наступний `daily_digest_time`. Щоб затримати digest, відключи daily-digest на самому провайдері.

---

## :material-printer: Per-Printer фільтрація

Кожен провайдер має picker **Printers** — обери **All** для підписки на всі принтери (default) або прив'яжи провайдер до підмножини. Події з принтерів поза вибраною множиною ніколи не доходять до цього провайдера, незалежно від event-toggle-ів. Корисні патерни:

- Один Discord-webhook на майстерню — кожен прив'язаний до її принтерів
- "VIP printer" Telegram-чат, прив'язаний до однієї production-одиниці, що генерує дохід
- Maintenance-only ntfy провайдер, прив'язаний до принтерів, у яких підходять заміни фільтрів / ременів

---

## :material-account-bell: Per-User Email сповіщення

Окремо від системи провайдерів вище — BamDude вміє писати email **власнику** друку напряму, коли той завершиться / провалиться / зупиниться — корисно у shared / multi-tenant deployment-ах, де кожен юзер хоче пошту своїх друків в особисту скриньку.

### Вимоги

- Authentication увімкнена (вона завжди увімкнена з 0.4.0+)
- SMTP сконфігурований у **Settings** → **System** → **Email**
- **Settings** → **Notifications** → **User Notifications** перемкнуто on
- У користувача є email на акаунті
- Користувач має право `notifications:user_email` (за замовчуванням у **Administrators** + **Operators** — див. [Authentication](authentication.uk.md))

### Підтримувані події

| Подія | Спрацьовує на |
|---|---|
| `user_print_start` | Друк користувача стартує |
| `user_print_complete` | Його друк завершився успішно |
| `user_print_failed` | Його друк збився |
| `user_print_stopped` | Він сам скасував свій друк |

Користувач може opt in/out на кожну подію окремо в персональному пункті sidebar **Notifications**. Майстер-перемикач "User Notifications" — у operator-а / admin-а під **Settings** → **Notifications**.

---

## :material-bed: Як пропустити подію, що вимагає дії, крізь ніч

Деякі події зупиняють ферму, доки хтось не втрутиться:

- **`plate_not_empty`** — перед стартом queue-job-а зловили непорожній стіл, і диспетч тепер на паузі. Проспати — означає, що черга стоятиме до пробудження.
- **`bed_cooled`** — стіл упав нижче налаштованого порога (типово 35 °C) після друку, тобто деталь можна знімати.
- **Порогові алерти сенсорів** — у кімнаті надто холодно чи надто волого для філаменту, який зараз друкується.

!!! warning "Тихі години — на провайдер, а не на подію"
    Обходу на рівні події немає. Провайдер усередині свого тихого вікна відкидає **все**, зокрема й три пункти вище, — тож провайдер, тихий із 22:00, не скаже тобі, що черга стала о 01:00.

    Замість цього маршрутизуй: заведи для подій, що вимагають дії, **окремий провайдер** із вимкненими тихими годинами, а балакучі (прогрес, старт друку) лиши на тому, який спить. На iOS найсильніший варіант цього — провайдер [Bark](#bark-ios) на рівні **Critical**: він проходить ще й крізь Silent mode і Focus.

**Щоденний digest** — окремий opt-in канал, і він нічого не затримує: кожне сповіщення надсилається тоді, коли сталося, а digest — це додаткове зведення зверху.

---

## :material-check-circle: Тестування

Кожен провайдер має кнопку **Send Test** поряд із save-action. Клік запускає синтетичну подію через повний pipeline (template render, quiet-hour gate, priority mapping, transport-specific wrap), тож результуюче повідомлення — точне прев'ю того, як виглядатимуть реальні події, не stripped-down "hello world".

Re-test після редагування шаблонів, зміни priority чи transport-level полів типу SMTP credentials. Тест обходить digest-чергу (завжди шлеться одразу), тож не треба чекати digest-час, щоб побачити результат.

---

## :material-lightbulb: Поради

!!! tip "Почніть з ntfy"
    ntfy -- найпростіший провайдер для налаштування: не потрібен обліковий запис, просто оберіть назву теми та підпишіться на телефоні.

!!! tip "Кілька провайдерів"
    Ви можете налаштувати кілька провайдерів для одночасного отримання сповіщень через різні канали.

> Базується на документації [Bambuddy](https://github.com/maziggy/bambuddy).
