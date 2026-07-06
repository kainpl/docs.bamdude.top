---
title: Orca Cloud
description: Per-user вхід в Orca Cloud (Supabase profile sync від OrcaSlicer) через paste-based PKCE flow, поряд з Bambu Cloud
---

# Orca Cloud

Orca Cloud — міст між твоїм [OrcaSlicer](https://github.com/SoftFever/OrcaSlicer) cloud-аккаунтом і BamDude. Він стоїть **поряд** з [Cloud Profiles](cloud-profiles.md) (Bambu Cloud) — можеш підключити один, обидва або жоден. Після входу твої OrcaSlicer filament / process / printer профілі з'являються у slice modal і в AMS-slot filament picker, вище за локальні імпорти та Bambu Cloud presets.

OrcaSlicer 2.4.0-alpha додав Supabase-backed cloud sync (`sync_pull`). BamDude читає той самий store, тому профілі, які ти налаштував в OrcaSlicer, з'являються тут без повторного імпорту.

Інтеграція **per-user**. Кожен BamDude-аккаунт тримає власний Orca Cloud токен — вхід не чіпає чужі аккаунти.

---

## :material-tab: Де це живе

**Profiles → Orca Cloud** — вкладка поряд з **Bambu Cloud**, **Local Profiles** і **K-Profiles**. Вкладка показує стан підключення, панель входу коли не підключено, і той самий rich-layout, що й Bambu Cloud view (пошук + фільтри + згрупована сітка + read-only detail modal) після підключення.

---

## :material-login: Вхід — paste flow

Supabase-проєкт Orca allowlist-ить лише **localhost** `redirect_to` (`http://localhost:41172/callback`) — адресу, яку слухає власний desktop-agent OrcaSlicer. Self-hosted BamDude на іншому хості не може прийняти цей redirect, тому вхід використовує **paste-based PKCE** flow замість звичайного browser callback (відстежується в апстрімі як [OrcaSlicer/OrcaSlicer#14028](https://github.com/OrcaSlicer/OrcaSlicer/issues/14028)).

### OAuth (Google / Apple / GitHub)

1. Вибери провайдера на панелі **Connect to Orca Cloud**
2. Відкриється нова вкладка зі сторінкою входу `auth.orcaslicer.com`. Увійди у свій Orca-аккаунт
3. Браузер перенаправить на адресу `http://localhost:41172/callback?code=...&state=...`, яка **не завантажиться** — це нормально; сама адреса і є те, що BamDude потрібно
4. Скопіюй **усю** адресу з рядка браузера і встав у поле **Paste the callback URL here**
5. BamDude обмінює `code` (разом з PKCE verifier, який зберіг на кроці 1) на токени → стан стає **Connected**

!!! tip "Якщо вкладка входу не відкрилася"
    Панель показує authorize URL як клікабельне посилання — відкрий вручну і продовжуй з кроку 3.

### Email + пароль

Для аккаунтів з Orca email/password-credential OAuth-танець повністю пропускається: введи Orca **email** + **пароль**, і BamDude увійде напряму через Supabase-ендпоінт `grant_type=password`.

---

## :material-clock-end: Час життя токена та refresh

На відміну від ~90-денного bearer Bambu Cloud, Orca використовує короткоживучі токени Supabase:

| Токен | Час життя | Примітки |
|---|---|---|
| Access JWT | ~1 година | Використовується для кожного API-виклику |
| Refresh token | Ротаційний, одноразовий | Кожен refresh повертає **новий** refresh token; старий витрачається |

BamDude оновлює access-токен **just-in-time** — коли виклик от-от запуститься, а токену лишилось менше ~5 хвилин життя, він спершу ротує і **зберігає новий refresh token перед API-викликом**, тому краш посеред refresh не залишить тебе з витраченим токеном. Якщо сам refresh відхилено (revoked на сервері), стан стає **Disconnected** і ти проходиш вхід знову.

Тимчасовий стан PKCE-handshake (verifier / state) живе лише між **Connect** і кроком paste, з **10-хвилинним TTL** — натисни Connect, відійди, і незавершений handshake сам протухне.

---

## :material-database-search: Що підтягується

Після підключення Orca Cloud профілі живлять ті самі поверхні, що й Bambu Cloud:

| Поверхня | Як з'являються Orca-профілі |
|---|---|
| Slice modal | Четвертий tier presets, `orca_cloud`, вище за local / Bambu Cloud / standard |
| AMS-slot filament picker | Orca-філаменти йдуть першими (внутрішньо з префіксом `orca_`); з розпарсеного матеріалу виводиться generic Bambu filament-ID, щоб прошивка принтера все одно розпізнала тип |
| Profiles → Orca Cloud tab | Згрупована printer / process / filament сітка з пошуком + фільтрами + read-only detail modal |

Orca `sync_pull` повертає **повний content кожного профілю inline**, тому — на відміну від Bambu Cloud, де filament type/колір потребують окремого per-preset fetch, який впирається в rate limit — Orca-філаменти несуть `filament_type` і колір безкоштовно. Metadata-aware pre-pick у slice modal використовує це, щоб точно ранжувати Orca-філаменти без зайвих round-trip.

!!! note "Пріоритет tier'ів у slicing"
    `orca_cloud` > `local` > `cloud` (Bambu) > `standard`. Ім'я профілю, яке є у вищому tier, відфільтровується з кожного нижчого, тому кожне ім'я рендериться один раз. Кожен cloud-tier також має **власний** status-банер у slice modal — Bambu і Orca можуть бути signed-out / expired / unreachable незалежно.

---

## :material-shield-key: Дозволи

| Дозвіл | Дає |
|---|---|
| `orca_cloud:auth` | Вхід/вихід з Orca Cloud, список / перегляд профілів, читання стану підключення, і slicing з Orca-presets |

Дефолтні групи дають `orca_cloud:auth` **Administrators** і **Operators**; **Viewers** — ні.

Для API-ключів `orca_cloud:auth` зливається в той самий **Use Bambu Cloud** (`can_access_cloud`) scope, що й `cloud:auth` — це той самий вимір довіри (доступ до third-party cloud від імені власника), тому ключ, уже допущений до cloud, покриває й Orca.

### Шифрування at-rest

Як і Bambu Cloud токен, Orca access + refresh токени зберігаються як plain-рядки в рядку `users` (міграція **m090** додає `orca_cloud_token`, `orca_cloud_refresh_token`, `orca_cloud_expires_at`, `orca_cloud_email`, `orca_cloud_user_id` + три тимчасові PKCE-колонки). Вони сьогодні не Fernet-шифровані — запусти BamDude на зашифрованому томі БД, якщо потрібне encryption-at-rest. Токени ніколи не витікають через API-відповіді (наверх виходять лише connected-флаг, email і user id).

---

## :material-help-circle: Вирішення проблем

??? question "localhost-адреса показує помилку з'єднання — вхід провалився?"
    Ні — це очікувана поведінка. На твоїй машині ніхто не слухає `localhost:41172` (це desktop-agent OrcaSlicer, якого ти не запускаєш). Провалена сторінка все одно має `code` + `state` в адресному рядку, а це все, що потрібно BamDude. Скопіюй усю адресу і встав.

??? question "\"That URL does not look like an Orca Cloud callback\""
    У вставленій адресі немає параметра `code`. Переконайся, що скопіював **усю** адресу після redirect (ту, що `http://localhost:41172/callback?...`), а не адресу сторінки входу Orca.

??? question "Підключено, але профілі не показуються"
    Можливо, ти ще не синхронізував жодного профілю з OrcaSlicer — Orca Cloud дзеркалить лише те, що ти запушив зі слайсера. Налаштуй профіль в OrcaSlicer, дай йому синхронізуватись, тоді натисни **Refresh** на вкладці Orca Cloud (5-хвилинний listing-кеш).

??? question "Стан сам перескочив на Disconnected"
    Ротацію refresh-токена відхилено на сервері (revoked, або одноразовий токен відтворили повторно). Пройди вхід знову. Оскільки refresh-токени одноразові, вхід у той самий Orca-аккаунт з двох місць може інвалідувати один з них.

??? question "Orca і Bambu presets мають однакове ім'я — хто виграє?"
    Orca. Slice modal де-дублює за іменем по tier'ах з `orca_cloud` нагорі, тому спільне ім'я рендериться лише в Orca-tier.
