---
title: Cloud Profiles
description: Per-user Bambu Cloud вхід з регіональним розділенням, MFA і прямим доступом до presets/девайсів з BamDude
---

# Cloud Profiles

Cloud Profiles — міст між твоїм Bambu Cloud аккаунтом і BamDude. Після входу твої filament / process / printer presets з'являються у slice modal поряд з локально імпортованими (див. [Local Profiles](local-profiles.md)), printer-firmware checks отримують доступ до списку Bambu-девайсів, а slicing-пайплайни можуть резолвити ті самі імена presets, що й Bambu Studio.

Якщо Bambu Cloud повертає порожню категорію пресетів, решта категорій і далі доступна в Cloud Profiles. У діалозі нарізки відображаються доступні хмарні та локальні пресети.

Інтеграція **per-user**. Кожен BamDude-акк тримає свій Bambu Cloud token — твій колега, що логіниться у свій Bambu-акк, не вибиває тебе, і твій токен не тече до нього.

!!! tip "Користуєшся ще й хмарою OrcaSlicer?"
    BamDude може паралельно логінитись в **[Orca Cloud](orca-cloud.md)** — Supabase profile sync з OrcaSlicer 2.4.0-alpha — і показувати ті профілі поряд з Bambu Cloud presets у slice modal (вище за Bambu Cloud). Обидві інтеграції незалежні; підключай одну, обидві або жодну.

---

## :material-earth: Per-user регіон (BamDude розширення)

Bambu Cloud розділений на два регіональні backend-и — `bambulab.com` (global) і `bambulab.cn` (China) — і твій акк живе рівно на одному. Upstream Bambuddy зберігає регіон глобально, тож install з мікс-юзерами не міг мати одного на global і одного на China одночасно.

BamDude піднімає це обмеження міграцією **m011**: кожен `User`-рядок несе свою колонку `cloud_region` (`global` / `china` / `null`). Sign-in пише регіон, який ти обрав, і кожен наступний запит від цього юзера йде до відповідного backend-хоста, навіть після рестарту. Два юзери на різних регіонах в одному install — підтримувана конфігурація.

| Зберігається | Поле | Default |
|---|---|---|
| `users` рядок (auth увімкнений) | `cloud_token`, `cloud_email`, `cloud_region` | `null` до входу |
| `settings` таблиця (auth вимкнений) | `bambu_cloud_token`, `bambu_cloud_email`, `bambu_cloud_region` | Fallback — single global cred bag |

`null` / порожній / unknown регіон трактується як `global` для legacy-рядків, які старіші за колонку.

---

## :material-login: Sign-in флоу

**Settings → Cloud Profiles → Connect to Bambu Cloud.** Три sub-флоу, обираються по MFA-сетапу твого акка або вподобанням:

### 1. Email + пароль + email OTP

Стандартний Bambu Cloud login для акків без TOTP.

1. Обери **регіон** (Global / China)
2. Введи Bambu **email** + **пароль**
3. Submit — BamDude дзвонить `/v1/user-service/user/login` і отримує `needs_verification=true`
4. Bambu емейлить 6-значний код; забий у verify-діалог
5. BamDude дзвонить `/cloud/verify` з кодом → токен зберігається на твоєму user-рядку → статус flips на **Connected**

### 2. Email + пароль + TOTP

Для акків з authenticator-app TOTP.

1. Перші три кроки ті самі, але login-відповідь має `verification_type='totp'` + `tfa_key`
2. Відкрий Google Authenticator / Authy / 1Password
3. Введи поточний 6-значний код
4. BamDude дзвонить `/cloud/verify` з `tfa_key` + кодом

Флоу авто-детектить, який метод використовує твій акк — діалог рендерить правильний промпт, ти не вибираєш.

!!! tip "TOTP > email"
    Якщо акк має обидва — TOTP швидший (без email-round-trip) і працює offline. Перевір, що годинник пристрою синхронізований — TOTP-вікна 30 с, drift > 1 хв і кожен код виглядатиме хибним.

### 3. Direct access-token paste

Для headless-сетапів, SSO-акків або середовищ, де email/OTP round-trip не пройде.

1. Натисни **Використати токен доступу**
2. Дістань Bambu Cloud bearer через [`bambu-lab-cloud-api`](https://pypi.org/project/bambu-lab-cloud-api/), або з браузера, авторизованого в MakerWorld (DevTools → Application → Cookies → `token`). Bambu Studio більше не показує токен у жодному UI, тож старий спосіб «взяти зі Studio» вже не працює. Стався до значення cookie як до секрету.
3. Встав у поле **Токен доступу**, обери регіон. Пробіли довкола вставленого значення обрізаються. Значення, яке взагалі не може бути токеном — порожнє, з пробілом чи розривом рядка всередині або з не-ASCII символами — відхиляється одразу як *Invalid token*, ще до звернення до Bambu
4. BamDude перевіряє токен дзвінком `/v1/user-service/user/profile`. На успіх — токен зберігається на твоєму user-рядку

!!! note "Акаунти регіону Китай мусять входити через токен"
    Китайські Bambu-акаунти прив'язані до номера телефону, а не email, тож email/пароль-флоу недоступний — шлях через access-токен вище єдиний.

!!! note "Cloud Access Token vs Printer Access Code"
    Cloud Access Token — bearer для Bambu API + MQTT, ось що ця сторінка хоче. Printer Access Code на екрані принтера (Network settings) — per-printer LAN-кред, інше поле, інша сторінка ([Printers](printer-control.md)).

### Коли з Bambu Cloud немає зв'язку { #cloud-unreachable }

Збій на боці Bambu відрізняється від хибних облікових даних — в усіх трьох флоу:

| Що сталося | Що ти бачиш |
|---|---|
| Bambu Cloud не відповідає або відповідає помилкою сервера чи сторінкою там, де мають бути дані | *Не вдалося зв'язатися з Bambu Cloud: …* із причиною або *Не вдалося зв'язатися з Bambu Cloud (відповідь HTTP 503)* зі статусом, який він дав. Твій пароль, код чи токен ніхто не оцінював, а вже збережений вхід лишається. Спробуй пізніше. |
| Хибний пароль або код підтвердження | Власне повідомлення Bambu про відмову. |
| Вставлений токен, який Bambu відхиляє | *Invalid token*. |
| Збережена сесія протермінувалась і не поновлюється | Позначка «вхід протермінувався» — див. [Час життя токена](#token-lifetime). |

Те саме діє і після входу: коли з Bambu Cloud немає зв'язку, список пресетів, список пристроїв і перевірка прошивок так і кажуть, а збережений вхід не чіпають. Через API це `502` із повідомленням; `401` відповідає лише тоді, коли Bambu відхилив самі облікові дані.

---

## :material-clock-end: Час життя токена { #token-lifetime }

Bambu Cloud bearer-и не вічні. BamDude зберігає й **refresh-токен** із
відповіді логіну, і коли Bambu повідомляє, що збережений токен протермінувався,
спершу тихо оновлює пару — з'єднання самозцілюється за лічені хвилини замість
вимагати повторний вхід з email-кодом раз на кілька місяців. Лише коли відхилено
саме оновлення, з'являється флоу «вхід протермінувався» нижче. Вставлені вручну
access-токени refresh-токена не мають, тож їхнє протермінування одразу веде до цього флоу.

Поновлення відбувається всюди, де використовується вхід, — на сторінках хмарних
профілів, під час завантажень із [MakerWorld](makerworld.md), у хмарних пресетах
діалогу нарізки та в експорті хмарних профілів Git-бекапу, — а запит, який
натрапив на протермінування, повторюється й проходить. Запити, що натрапили на
нього одночасно, ділять одне поновлення. Якщо для поновлення не вдається
зв'язатися з Bambu Cloud, запит відповідає *Не вдалося зв'язатися з Bambu Cloud,
щоб поновити вхід, термін якого минув. Спробуйте трохи згодом.*, і нічого зі
збереженого не змінюється.

BamDude перевіряє збережений токен **у самої Bambu Lab**, а не припускає, що той
досі працює — тож **Connected** означає, що Bambu його прийняла, а не просто що
він десь збережений. Відповідь кешується на кілька хвилин, щоб кілька місць, які
її опитують, не платили кожне за окремий round-trip.

### Коли вхід протермінувався

Коли токен спливає, **усі** функції Bambu Cloud зупиняються одночасно — хмарні
профілі, MakerWorld, пресети слайсера й перевірка прошивок — бо всі вони несуть
той самий токен. Перше справжнє відхилення записується один раз і поширюється,
тож усі дізнаються про це в один момент, а не кожне окремо. Перевірка оновлень
прошивок повідомляє саме про протермінований вхід, а не показує твої принтери з
невідомою версією прошивки.

Сторінка Профілі знову показує форму входу **з явною позначкою, що вхід
протермінувався**, щоб було зрозуміло, чому вона повернулась. Увійди там знову — і
все відновиться; більше нічого переналаштовувати не треба.

!!! info "Збій — це не протермінування"
    Протермінуванням вважається лише документована відповідь Bambu про
    протермінування. Випадковий 401 — відмова, специфічна для регіону чи
    ендпоінта, сторінка-заглушка Cloudflare, коротка непритомність — вважається
    тимчасовим і не виводить тебе з системи. Якщо Bambu Lab взагалі недосяжна,
    зберігається останній відомий статус, тож збій на їхньому боці ніколи не
    вижене тебе з робочої сесії.

Той самий токен гейтить також [MakerWorld import](makerworld.md) — якщо MakerWorld-сторінка раптом показує `can_download=false`, expired Bambu Cloud token найчастіша причина.

---

## :material-database-search: Що тягнеться

Після підключення slice modal та інші consumers читають твої Bambu Cloud дані live:

| Дані | Endpoint | Хто використовує |
|---|---|---|
| Filament / process / printer presets | `GET /api/v1/cloud/settings` | Slice modal, AMS slot config |
| Single preset detail (повний setting JSON) | `GET /api/v1/cloud/settings/{id}` | "Inspect preset" / inheritance display |
| Bound printer devices | `GET /api/v1/cloud/devices` | Printer-add wizard, Bambu-Cloud firmware check |
| Per-device firmware | `GET /api/v1/cloud/firmware-updates` | Cloud-side firmware check (різний від LAN-only шляху в [Firmware Updates](firmware-updates.md)) |
| Filament-id → name resolution | `POST /api/v1/cloud/filament-info` | AMS tray tooltips, K-profile filament labels |
| Офіційні назви філаментів | `GET /api/v1/cloud/builtin-filaments` | Віддається з вбудованого [каталогу сімей](filament-families.uk.md) |

Custom (private) presets ідуть першими у списку, public (built-in) presets — після. Діалог нарізки показує їх двома групами — **Bambu Cloud — мої пресети** і **Bambu Cloud** — поруч із [Local Profiles](local-profiles.md), Orca Cloud і стандартними пресетами слайсера. За назвою нічого не зливається: пресет, який під однією назвою є в кількох джерелах, стоїть у списку по разу на кожне джерело (див. [Slicer API → Списки профілів](slicer-api.md#preset-lists)).

Сегмент **Джерело пресетів** у діалозі нарізки, [калібруванні філаменту](filament-calibration.md) і [збиранні проєкту](assemble-project.md) рахує пресети, які ти зберіг у Bambu Cloud, як **Мої пресети** — разом з імпортованими профілями й кожним профілем [Orca Cloud](orca-cloud.md), бо в Orca Cloud лише твої власні, — а стокові хмарні пресети Bambu як **Вбудовані**. Те саме правило вирішує, які пресети ця сторінка дає редагувати.

**Матеріал** cloud-пресета філаменту береться з родини філаменту, до якої пресет належить, — за його setting id, інакше за родиною, яку називає сам пресет, інакше з його власного типу філаменту — і ніколи з назви. Тож пресет для принтера, якого комплект слайсера не покриває, однаково має матеріал; а той, чийого матеріалу ніщо не називає, рахується як «невідомий», а не вгадується, і лишається придатним для автоматичного вибору в діалозі нарізки.

!!! note "Вкладка показує лише ваші пресети"
    Вкладка Bambu Cloud перелічує **приватну** половину листингу — ваші власні
    пресети — як і Orca-вкладка. Публічний каталог хмари там
    не гортається: профіль, який хочете бачити, приїздить після того,
    як ви збережете чи ввімкнете його у слайсері. Фільтр принтера перелічує
    моделі з ваших пресетів, а варіанти написання «A1M» / «A1 mini» зведені в
    один рядок.

---

## :material-pencil: CRUD на cloud presets

Список **Тип філаменту** в редакторі пресетів залежить від вибраного слайсера в **Налаштування → Слайсер**. Наприклад, Bambu Studio пропонує `TPU-AMS`, а OrcaSlicer — `SBS`. Поточний тип залишається вибраним після перемикання слайсера й під час редагування імпортованого профілю з типом поза списком.

Cloud Profiles не read-only:

| Дія | Endpoint | Ефект |
|---|---|---|
| **Create** | `POST /api/v1/cloud/settings` | Створює новий preset на Bambu Cloud — inherit-ить від base, зберігає тільки diff |
| **Update** | `PUT /api/v1/cloud/settings/{id}` | Перейменовує або оновлює setting JSON |
| **Delete** | `DELETE /api/v1/cloud/settings/{id}` | Прибирає preset з Bambu Cloud — без undo |

Field-definition каталог `GET /api/v1/cloud/fields/{filament|process|printer}` живить форму — каже UI, які ключі існують для кожного типу, label, одиниці, valid-межі, dropdown-options.

Dropdown **базового пресета** в «Новому пресеті» має дві групи: **ваші власні
пресети і сім'ї** (кастомний філамент, створений у BamDude, з'являється тут
після пушу — новий пресет на його базі стає дитиною тієї сім'ї) та **стандартні
пресети, звужені до моделей принтерів вашої ферми**, а не повний список для
кожної машини Bambu.

Вкладка також має кнопку **Створити філамент** — діалог Create Filament з Bambu
Studio, із сім'єю, що народжується просто у хмарі. Див.
[Сім'ї філаментів](filament-families.uk.md).

---

## :material-shield-key: Permissions і шифрування

| Permission | Дозволяє |
|---|---|
| `cloud:auth` | Sign in / out, list / inspect / create / update / delete cloud presets, read connection status |
| `printers:read` | List bound cloud devices (`/cloud/devices`) |
| `firmware:read` | Read cloud-side firmware status (`/cloud/firmware-updates`) |
| `inventory:read` | Read filament-info / built-in filament fallback (для AMS tray tooltips) |

Дефолтні групи дають `cloud:auth` **Administrators** і **Operators**; **Viewers** — ні (read-only юзери не повинні писати токени на чийсь акк).

### At-rest шифрування

Коли install має `MFA_ENCRYPTION_KEY` (Fernet ключ), TOTP-секрети та інші MFA-cluster поля зашифровані at rest. Bambu Cloud token field **не** Fernet-encrypted сьогодні — зберігається як простий `String(500)` на `users`-рядку. Якщо потрібно encryption-at-rest — крути BamDude на encrypted DB-volume; токен не тече через API-відповіді (наверх вилазять тільки auth-status flag, email, регіон).

---

## :material-power-plug: Headless / API key access

API keys, створені в BamDude, можуть дзвонити cloud routes так само, як будь-які інші. Постав `can_read_status`, якщо ключ читає presets / девайси, і стандартні `X-API-Key` правила (див. [API Keys](api-keys.md)).

Створені через UI API keys **стампляться id юзера-творця**, тож cloud-side дзвінки бігтимуть проти per-user Bambu Cloud-токена цього юзера — за умови, що при створенні ключа ввімкнено тогл **Use Bambu Cloud**. Без цього opt-in `cloud:*` маршрути відмовляються від виклику, замість того щоб мовчки витрачати cloud-token власника. Pre-0.4.3 ownerless ключі (значок "Legacy" у списку API keys) у cloud-spend не підняти — при збереженні з `user_id IS NULL` тогл відхиляється. Щоб мігрувати, перестворіть ключ під своїм юзер-аккаунтом.

Для сетапів без per-user Bambu Cloud (single-user / auth-disabled), global Settings cred-bag — природне сховище, і Cloud-флагнуті ключі все одно падають туди як last resort.

---

## :material-help-circle: Troubleshooting

??? question "Login повертає `Invalid credentials`, але той самий пароль працює у Bambu Studio"
    Region mismatch — найчастіша причина. Обрав **Global**, коли акк зареєстрований на China backend (або навпаки) — повертає generic auth fail без friendly "wrong region" хінта. Перемкни region dropdown і retry.

??? question "Вхід відповідає *Не вдалося зв'язатися з Bambu Cloud*"
    Bambu Cloud не відповів або відповів помилкою сервера — сервер BamDude не зміг до нього достукатися. Твій пароль, код чи токен ніхто не перевіряв, а збережений вхід лишається. Перевір, що хост BamDude має доступ до інтернету, і спробуй пізніше. Див. [Коли з Bambu Cloud немає зв'язку](#cloud-unreachable).

??? question "Вставлений токен відхилено як *Invalid token*"
    Або значення не може бути токеном — воно порожнє чи містить пробіл, розрив рядка або не-ASCII символ (скопіюй саме значення cookie), — або його відхилив Bambu.

??? question "TOTP код відкидається"
    Clock drift. Відкрий Settings → Date & time → ввімкни Network-provided time. TOTP-вікна 30 с, drift > хвилини відкине кожен код. Re-enrol у authenticator app, якщо drift хронічний.

??? question "Connected, але preset list порожній"
    Дві типові причини. **(1)** Зайшов у sub-акк без presets — log out, log in під parent-акком. **(2)** Slicer-presets кеш stale; slice-modal перепопулує його на наступному відкритті (5-min TTL) або форс-перевідкрий modal.

??? question "Статус показує Disconnected через тиждень"
    Токен expired або revoked server-side. Прогони sign-in заново. Якщо постійно повторюється на тому ж акку — Bambu Cloud примусово re-auth; access-token paste тримається довше для деяких акків, ніж email/password.

??? question "Інші юзери бачать мої cloud presets"
    Не повинні — `cloud_token` зберігається на `users.{your-id}` і `/cloud/*` route-handler-и завжди тягнуть `current_user.cloud_token`. Якщо реально бачиш — крутиш з вимкненим auth (де всі юзери шарять global Settings cred bag); ввімкни auth, і кожен отримає свій токен.

??? question "China регіон — login працює, presets не вантажаться"
    TOTP-verify має йти на TFA-endpoint `bambulab.cn`, не `bambulab.com`. BamDude роутить по `region`-полю verify-дзвінка — переконайсь, що регіон, який обрав на login, збігається з тим, що verify-діалог відправляє.
