---
title: Сповіщення
description: Push-сповіщення про події друку через різні провайдери
---

# Сповіщення

Вісім каналів доставки, один редактор, одна конфігурація маршрутизації. Підпиши кожен провайдер на потрібні події, постав тихі години й щоденний digest на провайдер, кастомізуй шаблони на мову.

---

## :material-bell-ring: Підтримувані провайдери

| Провайдер | Складність | Можливості |
|-----------|:----------:|------------|
| **Telegram** | Середньо | Через бота BamDude з actionable inline-кнопками (clear plate, mark maintenance done, pause/stop). Розсилається в кожен авторизований чат, який підписаний на подію. |
| **Discord** | Легко | URL webhook каналу, форматування embed, прикріплення картинок. |
| **Email (SMTP)** | Середньо | STARTTLS / SSL / plain. Per-provider `to_email` — різні юзери бачать різні тіла. |
| **Pushover** | Легко | Рівні пріоритету, прикріплення картинок до 2.5 МБ. |
| **ntfy** | Легко | Topic-based, опційний bearer-токен, прикріплення картинок. |
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

## :material-tune: Тригери подій

Кожен провайдер підписується незалежно. Вимкнення події на одному провайдері не зупиняє її на інших.

**Друк:**

| Подія | Спрацьовує коли |
|-------|------------------|
| `print_start` | Друк запустився на принтері |
| `first_layer_complete` | Завершився перший шар (швидко ловить first-layer фейли) |
| `print_progress` | На налаштовних milestone-ах прогресу |
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

**Принтер:**

| Подія | Спрацьовує коли |
|-------|------------------|
| `printer_offline` | MQTT-розрив |
| `printer_error` | Спрацював HMS-код (BamDude додає переклад людською) |
| `plate_not_empty` | Bed-occupancy gate зловив старт наступного друку (auto-pause) |
| `maintenance_due` | Інтервал обслуговування досягнуто |

**Черга:**

| Подія | Спрацьовує коли |
|-------|------------------|
| `queue_job_added` / `queue_job_started` / `queue_job_waiting` / `queue_job_skipped` / `queue_job_failed` / `queue_completed` | Lifecycle черги. Тільки ті події, на які ти підписався. |

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

## :material-clock: Тихі години і щоденний digest

Обидва налаштовуються **на провайдер**, не глобально — Discord-канал може лишатися гучним, а телефон отримати тільки 9:00 summary.

| Налаштування | Де | Ефект |
|---|---|---|
| `quiet_hours_enabled` + `quiet_hours_start` / `quiet_hours_end` | Конфіг провайдера | Події всередині вікна викидаються (не чекають — quiet hours це "мовчати", не "відкласти"). |
| `daily_digest_enabled` + `daily_digest_time` | Конфіг провайдера | Події протягом дня зберігаються в `notification_digest_queue`; коли годинник переходить `daily_digest_time`, BamDude вислає чергу одним digest-повідомленням. |

Список Telegram-чатів (Settings → Notifications → Telegram Chats) має ті самі два toggle-и на чат, плюс `notification_events` фільтр — кожен чат підписується тільки на події, які йому потрібні.

---

## :material-file-document-edit: Редактор шаблонів

Кожна подія має дефолтний шаблон у `data/notification_templates_{en,uk}.json`. Вкладка Templates під Settings → Notifications дозволяє перевизначити будь-який — тітул + тіло — з MarkdownV2 toolbar і live-прев'ю.

Підстановка змінних — простий `{plate_holder}` синтаксис (`{printer_name}`, `{filament_grams}`, `{eta}` і т.д.); схема залочена на подію, тож редактор сам попереджає, коли placeholder не резолвиться.

Шаблон вибирається **за мовою отримувача**: Telegram-чат, прив'язаний до оператора з `settings.language=uk`, отримає українське тіло; email до іншого юзера з `settings.language=en` — англійське. Нові ключі додавайте в **обидва** JSON-файли — BamDude постачається лише з en + uk.

---

## :material-lightbulb: Поради

!!! tip "Почніть з ntfy"
    ntfy -- найпростіший провайдер для налаштування: не потрібен обліковий запис, просто оберіть назву теми та підпишіться на телефоні.

!!! tip "Кілька провайдерів"
    Ви можете налаштувати кілька провайдерів для одночасного отримання сповіщень через різні канали.

> Базується на документації [Bambuddy](https://github.com/maziggy/bambuddy).
