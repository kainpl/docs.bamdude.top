---
title: Swap Mode
description: Підтримка плейт-свопера A1 Mini з макросами, restart-стійкістю та серіалізованим диспатчем
---

# Swap Mode

Swap mode підтримує автоматизовані плейт-свопери -- механічні додатки, що виштовхують готову робочу пластину та позиціонують свіжу між друками. Коли swap mode увімкнено, BamDude координується зі свопером, щоб виконувати unattended-батчі без ручного підтвердження очищення пластини.

---

## :material-swap-horizontal: Що таке Swap Mode?

Плейт-свопер -- це апаратний аксесуар (найчастіше для A1 Mini), що бере на себе ротацію пластин між друками. Зі swap mode увімкненим планувальник черги:

1. Виконує макрос **`swap_mode_start`** перед першим друком
2. Запускає сам друк
3. Виконує макрос **`swap_mode_change_table`** після завершення друку
4. Обходить підтвердження plate-clear
5. Автоматично запускає наступний друк з черги

Цикл триває, поки черга не спорожніє.

---

## :material-cog: Налаштування

### Увімкнення Swap Mode

1. Перейдіть до **Settings → Queue**.
2. Увімкніть **Swap Mode** для свого A1 Mini.
3. Виберіть **Swap Profile** під своє залізо:

    | Профіль | Для |
    |---|---|
    | `a1mini_kit` | Офіційний Bambu A1 Mini Plate Swapper Kit |
    | `a1mini_stl` | Community-printable A1 Mini свопери (printable kit / STL дизайни) |
    | `jobox-a1` | JoBox plate-swap автоматика |

    Профіль прив'язує правильний набір макросів `swap_mode_start` / `swap_mode_change_table` (кожна BamDude-інсталяція постачається з built-ins на кожен профіль; перевизначити можна під **Settings → Macros**).

### Swap G-code макроси

Swap mode керується G-code макросами, прив'язаними до подій `swap_mode_start` та `swap_mode_change_table`. Налаштовуйте їх у **Settings → Macros**. Див. [Макроси](macros.md) для повної системи подій + фільтрів.

```gcode
; Приклад сніпета swap_mode_change_table
G28 X Y         ; Home X and Y
G1 Y 180 F3000  ; Move bed forward for plate swap
M400            ; Wait for moves to complete
G4 S5           ; Pause 5 seconds for swap
G28             ; Home all axes
```

!!! warning "Потрібне власне обладнання"
    Swap mode потребує фізичного плейт-свопера, прикрученого до принтера.
    Підлаштовуйте G-code `swap_mode_change_table` під ваш конкретний
    механізм -- універсальної swap-рутини не існує.

---

## :material-shield-check: Restart-стійке відстеження подій

Swap-намір **зберігається на диск**, а не в пам'яті. Рестарт BamDude посеред друку ніколи не втрачає очікуваний plate-swap.

**Як це працює**

- На диспатчі кожна swap-подія, яку завдання збирається виконати, додається в `print_archives.extra_data["swap_macro_events_pending"]` (JSON-список).
- Коли `swap_mode_start` спрацьовує успішно, диспатчер одразу видаляє його зі списку.
- Коли `swap_mode_change_table` спрацьовує успішно (в `on_print_complete`), той самий запис видаляє його.
- Щойно список порожніє, ключ зникає взагалі, тож `extra_data` архіву залишається чистим.

**Чому це важливо**

- Рестарт бекенду між print start та print complete раніше витирав in-memory dict `_active_swap_config`, лишаючи `on_print_complete` без нічого, на чому діяти. Тепер pending-список читається з рядка архіву, і спрацьовують лише ті події, що в ньому ще лишилися.
- Дубльований `on_print_complete` (MQTT replay, reconnect flap) знаходить подію вже видаленою і нічого не робить -- жодного подвійного swap.

!!! info "Де живе маркер"
    Для диспатчів файлів бібліотеки початковий pending-список загортається
    в `INSERT` всередині `archive_print()` (один statement, без додаткового
    writer). Для повторних друків існуючий рядок архіву оновлюється у
    відкритій сесії диспатчера до FTP-завантаження -- тримання всього в
    одній транзакції уникає гонки з runtime-трекером по тому ж рядку.

---

## :material-lock-clock: Диспатч і startup-lock на DB-write

Background dispatch працює **паралельно по принтерах** — відправка друків на два A1 Mini зі сваперами справді стартує обидва завдання одночасно.

**Що серіалізовано**

Коротка фаза DB-insert (`INSERT INTO print_archives`) обгорнута в startup-lock, щоб single-writer семантика SQLite не падала на `database is locked`. Лок звільняється, як тільки рядок закомічений; FTP-завантаження і `start_print` MQTT round-trip далі біжать паралельно.

**Що ти побачиш**

- На двох принтерах `swap_mode_start` спрацьовує практично одночасно.
- Їхні FTP-завантаження йдуть паралельно (у dispatch-тості будуть два прогрес-бари).
- Тимчасовий "одне за раз через усю ферму" gate, що приземлився в середині 0.4.1, прибрали, як тільки startup-lock у диспатчер заїхав.

---

## :material-playlist-play: Поведінка черги в Swap Mode

Коли swap mode активний для принтера:

1. Друк завершується на принтері.
2. Виконується макрос `swap_mode_change_table` (G-code через MQTT, з ACK у idle-стані).
3. **Підтвердження plate-clear обходиться** -- свопер сам розбирається з очищенням.
4. Наступний друк з черги диспатчиться.
5. Цикл повторюється, поки черга не спорожніє.

Це режим **unattended batch production** для сумісних принтерів.

---

## :material-lightbulb-on: Парування з макросами `print_started` / `print_finished`

Новіші події `print_started` та `print_finished` (див. [Макроси](macros.md)) спрацьовують *додатково до* swap-макросів, на кожному друку незалежно від swap mode. Використовуйте їх для ортогональної автоматизації -- світло корпусу, зовнішні реле тощо.

**Приклад: світло корпусу тільки на swap-mode друках**

| Macro 1 | Macro 2 |
|---------|---------|
| Action: MQTT-action | Action: MQTT-action |
| Event: `print_started` | Event: `print_finished` |
| Command: `chamber_light_on` | Command: `chamber_light_off` |
| `swap_mode_only`: `true` | `swap_mode_only`: `true` |
| `delay_seconds`: `10` | `delay_seconds`: `0` |

Світло цикл лише на справжніх swap-mode прогонах; ручні друки з того ж принтера лишають світло недоторканим.

---

## :material-alert: Вимоги

| Вимога | Деталі |
|--------|--------|
| **Принтер** | A1 Mini (основний таргет) |
| **Обладнання** | Встановлений плейт-свопер |
| **Макроси** | Налаштований G-code макрос `swap_mode_change_table` |
| **Елементи черги** | Щонайменше 2 друки в черзі для принтера |

---

## :material-lightbulb: Поради

!!! tip "Перевірте swap-макрос вручну"
    Запустіть G-code `swap_mode_change_table` з файлового браузера принтера
    (або через **Macros → Run Now**) перш ніж вмикати swap mode у
    проді. Поганий swap-роутин заклинює всю чергу.

!!! tip "Поєднуйте з batch quantity"
    Використовуйте функцію batch-quantity у черзі, щоб поставити N копій,
    а далі дайте swap mode прогнати їх підряд. Поєднайте з авто-вимкненням
    розумних розеток для повністю unattended нічних прогонів.

!!! tip "Моніторте дистанційно"
    Стрім із камери + Telegram-бот дозволяють спостерігати за swap-операцією
    та отримувати сповіщення про завершення черги або збій. Див.
    [Telegram-бот](telegram-bot.md) і [Камеру](camera.md).

> Початково базується на документації [Bambuddy](https://github.com/maziggy/bambuddy).
