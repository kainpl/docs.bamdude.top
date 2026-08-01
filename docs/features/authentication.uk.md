---
title: Автентифікація
description: Завжди увімкнена автентифікація з MFA, OIDC SSO, refresh-сесіями та правами на основі груп
---

# Автентифікація

BamDude поставляється з завжди увімкненою автентифікацією: кожен API-ендпоінт захищено, при першому запуску майстер проведе вас через створення адміністратора, а далі користувачі входять за паролем, опціональним 2FA або через OIDC single sign-on. Ця сторінка -- єдине джерело правди про auth-стек: групи, сесії, MFA, SSO, лімітування та відновлення доступу.

---

## :material-lock: Огляд

- **Облікові записи** -- кілька користувачів з унікальними обліковими даними та індивідуальними MFA-налаштуваннями.
- **Права на основі груп** -- 80+ гранулярних прав формату `resource:action`, три стандартні групи (Administrators / Operators / Viewers), довільні власні групи.
- **Sliding-сесії на JWT** -- access-токени на 1 годину, які прозоро оновлюються через HttpOnly-cookie з ротацією, тож користувача не викидає посеред сесії.
- **Багатофакторна автентифікація** -- TOTP (застосунки-аутентифікатори), email OTP та 10 одноразових резервних кодів.
- **OIDC / SSO** -- authorization-code flow з PKCE для будь-якого провайдера, що відповідає стандарту (Authentik, Keycloak, Pocket-ID, Google Workspace, ...).
- **Лімітування частоти запитів** -- sliding-window бакети по користувачу і по IP на login + forgot-password.
- **Setup-gate + відновлення адміна** -- свіжі інсталяції проходять одноразовий setup; втрату всіх адмінів можна відкатати через CLI без втрати даних.

!!! info "Auth завжди увімкнений"
    Перемикача "вимкнути auth" немає. Кожен ендпоінт вимагає валідної сесії або API-ключа. API-ключі (`X-API-Key` або `Authorization: Bearer bb_...`) обходять JWT-перевірку, але все одно проходять ту саму перевірку прав.

---

## :material-rocket-launch: Setup при першому запуску

При найпершому старті BamDude знає, що адміна ще немає, тому блокує API і показує форму setup.

1. Відкрийте UI BamDude. Майстер setup рендериться автоматично.
2. Введіть **username**, **пароль** та (опціонально) **email** першого адміна.
3. Submit. Setup-gate відкривається; вас перекидає на звичайну сторінку логіну і одразу залогінює.

Поки setup-gate активний, відповідають лише три ендпоінти:

| Ендпоінт | Призначення |
|----------|-------------|
| `GET /api/v1/auth/status` | Чи потрібен setup? UI використовує це, щоб обрати login або setup. |
| `POST /api/v1/auth/setup` | Створити першого адміна. |
| `GET /api/v1/system/health` | Liveness-проба. |

Усі інші виклики повертають `503 {"detail": "setup_required"}` поки setup не завершено.

!!! warning "Не виставляйте свіжий контейнер назовні"
    Setup-ендпоінт за дизайном неавтентифікований (адміна, проти якого автентифікуватися, ще не існує). Виставляйте порт 8000 публічно **тільки після** того, як завершите setup, або зробіть setup спочатку через приватну мережу.

---

## :material-account-group: Групи за замовчуванням

| Група | Опис | Права |
|-------|------|-------|
| **Administrators** | Повний доступ | Усі права |
| **Operators** | Керують принтерами та контентом | Керування принтером, черга, архіви, бібліотека |
| **Viewers** | Доступ лише для читання | Перегляд принтерів, архівів, черги |

Власні групи можуть змішувати будь-які права. Користувачі, лінкнуті через OIDC, за замовчуванням потрапляють у **Viewers** (налаштовується для кожного провайдера).

---

## :material-key: Категорії прав

Права мають формат `resource:action` -- наприклад, `printers:control`, `archives:read`. Ендпоінти оголошують потрібне право через `RequirePermission(...)`, тож матриця застосовується однаково на REST, WebSocket і Telegram-поверхнях.

- **Printers** -- `printers:read`, `printers:create`, `printers:update`, `printers:delete`, `printers:control`, `printers:files`, `printers:ams_rfid`, `printers:clear_plate`
- **Archives** -- `archives:read`, `archives:read_own` / `archives:read_all`, `archives:create`, `archives:update_own` / `archives:update_all`, `archives:delete_own` / `archives:delete_all`, `archives:reprint_own` / `archives:reprint_all`
- **Queue** -- `queue:read`, `queue:read_own` / `queue:read_all`, `queue:create`, `queue:update_own` / `queue:update_all`, `queue:delete_own` / `queue:delete_all`, `queue:reorder`
- **Library** -- `library:read`, `library:read_own` / `library:read_all`, `library:upload`, `library:update_own` / `library:update_all`, `library:delete_own` / `library:delete_all`, `library:purge` (минути trash, hard-delete одразу)
- **Inventory** -- `inventory:read`, `inventory:create`, `inventory:update`, `inventory:delete`, `inventory:view_assignments`
- **Cloud** -- `cloud:auth` (per-user логін у Bambu Cloud + CRUD cloud-профілів; `settings:read` НЕ потрібен)
- **Settings** -- `settings:read`, `settings:update`, `settings:backup`, `settings:restore`
- **Notifications** -- `notifications:read`, `notifications:update`, `notifications:user_email` (гейт для per-user email opt-in сторінки)
- **Stats** -- `stats:read`, `stats:filter_by_user` (фільтр дашбордів за `started_by` / `uploaded_by`)
- **Users / Groups** -- `users:read`, `users:create`, `users:update`, `users:delete`, `groups:read`, `groups:create`, `groups:update`, `groups:delete`

!!! tip "Права власності"
    Використовуйте права `*_own` для користувачів, які мають змінювати лише свої власні завантаження та елементи черги. Operators зазвичай отримують `*_all`; Viewers -- ні те, ні інше. `*_all` завжди включає `*_own`.

!!! tip "Cloud-профілі — per-user"
    Кожен користувач має свій логін у Bambu Cloud — вхід User A не впливає на сесію User B. Єдине право `cloud:auth` покриває login, logout і весь CRUD cloud-профілів; `settings:read` **не** потрібен.

!!! tip "Inventory vs видимість AMS-призначень"
    `inventory:view_assignments` показує що завантажено в кожен AMS-слот на сторінці Printers **без** експозиції повного inventory. Видавай окремо операторам, яким треба швидко звірити spool→слот, але які не повинні бачити покупки, lot-коди й залишки.

### Семантика `*_own` vs `*_all`

| Форма права | Ефект |
|---|---|
| `archives:delete_own` | Видаляти лише архіви, **які ти створив / запустив**. |
| `archives:delete_all` | Видаляти будь-який архів, включно з ownerless. Включає `*_own`. |
| `queue:update_own` | Редагувати лише свої queue-айтеми. |
| `library:update_all` | Перейменовувати / переміщувати / видаляти будь-який library-файл. |

**Ownerless-айтеми.** Деякий контент не має власника — наприклад, архіви до увімкнення auth, друки, тригернуті auto-virtual-printer, library-файли через webhook. Для модифікації потрібен `*_all`; користувачі лише з `*_own` бачать їх як read-only.

Користувачі в кількох групах отримують **об'єднання** прав усіх своїх груп — призначення додаються, не мінімізуються.

!!! info "Читання теж розділене за власністю"
    Роути **читання** архівів / черги / бібліотеки застосовують розділ `read_own` / `read_all`, а не плаский прапор `*:read`. Вбудовані **Operators** і **Viewers** несуть варіант `*:read_all`, тож і далі бачать друки, чергу й бібліотеку всієї ферми — BamDude це спільна ферма. **Кастомна** група, що тримає лише legacy-прапор `*:read`, беклфілиться до `*:read_own` (fail-closed): щоб бачити рядки інших користувачів, їй треба явно видати `*:read_all`. Плаcкі прапори `archives:read` / `queue:read` / `library:read` лишаються суто як гейт download / preview на фронтенді — бекенд більше не зважає на них для видимості рядків.

---

## :material-account-multiple-plus: Управління користувачами

**Settings -> Users -> вкладка Users.** Видно всім з `users:read`. Модифікації (create / update / delete) — **лише для адмінів**: самого лише права `users:create` / `users:update` / `users:delete` вже недостатньо. "Адмін" тут означає `User.is_admin`: або legacy `role == "admin"`, **або** членство в групі **Administrators**. Цей admin-гейт стоїть *поверх* права, тож non-admin оператор, якому просто видали `users:update`, не може само-ескалюватися, створивши admin-акаунт. API-ключі не несуть особистості користувача, тож ніколи не проходять admin-гейт — управління користувачами недосяжне через API-ключ.

### Створення користувача

1. Натисни **Add User**.
2. Заповни **Username**, **Password** (за паролевою політикою), **Confirm password**, відміть одну або кілька **Groups**.
3. (Опційно) Додай **Email** — потрібен для email OTP, password-reset поштою і per-user сповіщень про друк.
4. **Create**. Користувач може логінитись одразу.

Коли увімкнено [Advanced Auth via Email](#advanced-auth-via-email), поле password **замінюється** полем email: BamDude генерує безпечний випадковий пароль і шле його напряму користувачу. Жоден адмін пароля не бачить — це строго безпечніше за передачу пароля в чаті.

### Редагування

Клік олівчик на рядку. Username, email, password, group memberships — все редаговане. Збереження зміни пароля штампує `password_changed_at` і вбиває всі існуючі сесії цього користувача.

### Видалення

Клік корзинку. Якщо користувач має контент (архіви, queue items, library files, started prints) — BamDude питає що з ним робити:

| Вибір | Ефект |
|---|---|
| **Delete user AND their items** | Hard-delete архівів, queue items, library files і всього іншого owned-контенту. Cascade. |
| **Delete user, keep items** | Видаляє користувача; його контент стає ownerless і модифікувати може лише `*_all`. Activity-tracking ("Started by alice") зберігається — username показується as-recorded, навіть коли user-row уже немає. |
| **Re-assign to admin** | Переписує власність усіх рядків на обраного адміна одною транзакцією. Зручно при offboarding-у. |

Сам себе видалити не можеш, останнього адміна видалити не можеш — UI грейає кнопки з тултіпом-поясненням.

---

## :material-account-group-outline: UI керування групами

**Settings -> Users -> вкладка Groups.** Кожна група показує name, description, і per-category count badge ("Printers 7/8", "Archives 9/9") — щоб одним поглядом охопити покриття.

Клік **Add Group** (або олівчик на існуючій) відкриває **повносторінковий редактор груп**:

- **Search bar** живо фільтрує permission-grid за назвою чи описом.
- **Select all** / **Clear all** масово тогглять усі чекбокси.
- **Чекбокси на заголовку категорії** тогглять усі права в категорії одним кліком.
- Per-category **count badges** ("5/7") оновлюються по мірі тіку.
- Description — звичайний текст; пиши що насправді планується від групи, майбутній-ти подякує.

Створення, редагування чи видалення групи — і додавання/видалення учасника групи — **лише для адмінів**: потрібне членство в групі Administrators (або legacy admin-роль) *поверх* відповідного права `groups:*`, тож оператор лише з `groups:update` не може ескалюватися через редактор груп.

Системні групи (Administrators / Operators / Viewers) видалити не можна, а їхні **назву й permission-сет більше не можна редагувати** — API відхиляє будь-яку спробу перейменувати системну групу чи змінити її права (обрізання набору Administrators було б само-локаутом). Опис усе ще редагується вільно. Кастомні групи можна створювати, редагувати й видаляти будь-коли; користувачі, що лишились лише у видаленій групі, стають без груп і втрачають усі права до перепризначення.

---

## :material-email-fast: Advanced Auth via Email

Опційний SMTP-шар, що дає passwordless onboarding, self-service password reset і per-user сповіщення про друк. Тогглиться незалежно від базового auth.

### Конфіг SMTP

**Settings -> вкладка Email.**

| Поле | Примітки |
|---|---|
| **SMTP host** | напр. `smtp.gmail.com`, `smtp.fastmail.com`, твій self-hosted Postfix. |
| **SMTP port** | `587` для STARTTLS (типове), `465` для implicit TLS. |
| **Use STARTTLS** | Увімкнено за замовчуванням для 587. Вимкнено для 465 (там уже TLS). |
| **Username / password** | Для Gmail / Fastmail / Apple — app-specific password. |
| **From address** | Адреса відправника. Деякі провайдери вимагають збігу з auth user. |
| **External URL** | Reachable URL твого BamDude — вшивається в reset / welcome листи. Має реально резолвитись з браузера користувача. |

Натисни **Test email** до того, як вмикати тоглер — летить one-shot на твою адмінську адресу і показує SMTP-помилку verbatim, якщо щось не так.

### Вбудовані шаблони

Редагуються під **Settings -> Email -> Templates**:

- **Welcome** — новий акаунт з авто-згенерованим паролем
- **Password reset** — self-service або admin-triggered, містить one-time токен (за замовчуванням 1 година)
- **Two-Factor code** — доставка email OTP
- **Printer error** — per-user лист коли його друк зафейлився
- **Print complete / failed / stopped** — per-user lifecycle листи

Шаблони i18n-aware (en + uk); кожен несе subject і body зі змінними `{username}`, `{printer_name}`, `{archive_url}`.

### Self-service password reset

1. Користувач клікає **Forgot your password?** на login-сторінці.
2. Вводить username або email. Endpoint завжди відповідає success (анти-енумерація), але лист шле лише якщо адреса існує.
3. Лист містить one-shot URL, валідний 1 годину. Токен single-use.
4. Користувач клікає, ставить новий пароль (за паролевою політикою), і одразу залогінений.

Адміни можуть тригернути той самий флоу одним кліком зі сторінки Users — корисно коли тіммейту тільки що здох authenticator і він залочений з TOTP-protected reset.

### Per-user email сповіщення

Коли Advanced Auth увімкнено, окремі користувачі гейтять сповіщення **для своїх власних робіт** під **Notifications** у бічному меню. Список:

- **Print started** — лист коли твоя робота починається
- **Print completed** — успіх
- **Print failed** — HMS-помилка / cancel
- **Print stopped** — manual cancel

Потребує email на акаунті і права `notifications:user_email` (за замовчуванням Administrators + Operators, вимкнено для Viewers). Це **незалежно** від глобальної системи сповіщень — мейлить лише submitter-у, не всій фермі.

---

## :material-server-network: LDAP / Active Directory

BamDude підтримує LDAP-автентифікацію для оточень з Active Directory, FreeIPA чи OpenLDAP. Локальні акаунти співіснують з LDAP — локальний адмін завжди працює як fallback при недосяжному directory.

### Конфіг

**Settings -> Authentication -> вкладка LDAP.**

| Поле | Примітки |
|---|---|
| **Server URL** | `ldaps://ad.example.com:636` (LDAPS) або `ldap://ad.example.com:389` (StartTLS). Чистий plaintext LDAP без StartTLS відхиляється — credentials мають шифруватись на дроті. |
| **Security** | StartTLS (upgrade plain → TLS на 389) або LDAPS (TLS з першого байта на 636). |
| **Bind DN** | Service-account DN для пошуку юзерів (напр. `CN=bamdude-svc,OU=Service,DC=example,DC=com`). |
| **Bind password** | Service-account пароль. Encrypted at rest коли встановлено `MFA_ENCRYPTION_KEY`. |
| **Search base** | Де шукати (напр. `OU=Users,DC=example,DC=com`). |
| **User filter** | LDAP-фільтр; `{username}` підставляється на login. AD: `(sAMAccountName={username})`. OpenLDAP / FreeIPA: `(uid={username})`. |

Натисни **Test connection** до **Enable LDAP** — робить dry-run bind + search і показує raw error при misconfig.

### Group mapping

Маппінг directory-груп на BamDude-групи через JSON-об'єкт:

```json
{
  "BamDudeAdmins": "Administrators",
  "BamDudeOps": "Operators",
  "BamDudeViewers": "Viewers"
}
```

Ключі — LDAP `cn` груп (case-insensitive); значення — імена BamDude-груп. Підтримані обидва стилі: AD `memberOf` і POSIX `memberUid`. Membership **ре-синкається на кожному login** — пониження в AD доїде максимум один BamDude-логін потому.

Якщо мапінгу нема — LDAP-користувачі auto-provision-яться без груп і їх треба призначати руками.

### Provisioning

| Тоглер | Ефект |
|---|---|
| **Auto-provision** | On = перший успішний LDAP-логін авто-створює локальний рядок з `auth_source=ldap`. Off = адміни мають пре-створити користувача через вкладку **LDAP** у Create User модалі (див. нижче); невідомі LDAP-юзернейми відхиляються при логіні. |
| **Sync email on login** | Email юзера переписується з LDAP при кожному логіні (так AD-зміни доходять). |

LDAP-provisioned юзери показують **LDAP** badge у списку Users. Кнопка **Change password** прихована — паролі живуть у directory, не в BamDude. Admin-triggered password reset і self-service forgot-password заблоковані для LDAP-акаунтів з ясним повідомленням "managed by LDAP".

### Manual onboarding (вкладка LDAP)

Коли LDAP увімкнено, **Create User** модал у Settings → Users отримує **Local / LDAP** перемикач вкладок. LDAP-вкладка — це debounced пошук у директорії (≥2 символи), повертає до 25 збігів через service-account bind. Кожен рядок показує `displayName` / email / DN з директорії і має позначку **Already provisioned** для імен, що вже існують як BamDude-користувачі (тож подвійний клік неможливий). Вибрати один + натиснути **Provision user** → BamDude перерезолвить ім'я через service bind і створить BamDude-рядок через ту саму гілку коду, що auto-provision при логіні — group mapping, default-group fallback і email sync застосовуються однаково.

Використовуй це коли **Auto-provision** вимкнено, але треба все-таки пре-створити directory-користувачів вручну без редагування БД.

Потрібний дозвіл: `users:create` (admin за замовчуванням).

### Local admin fallback

Локальний адмін завжди працює незалежно від LDAP-стану. Якщо directory-сервер ліг, LDAP-логіни фейляться з повідомленням "directory unreachable, retry or use local account"; локальний адмін зайде і розрулить. **Не видаляй останнього локального адміна** — це твій get-out-of-jail-free якщо AD коли-небудь злетить.

Якщо локальний і LDAP-юзер ділять username — **локальний виграє**: LDAP не може silently override existing local-row.

---

## :material-account-eye: Трекінг активності користувачів

При діях під автентифікованою сесією BamDude записує хто-що-зробив і світить це на картках по всьому UI:

| Активність | Де показується |
|---|---|
| Library file uploaded | "Uploaded by *username*" badge на картці файла. |
| Архів створено з друку | "Started by *username*" на картці архіву + сторінці деталей. |
| Queue item доданий | Username поряд з queue-рядком. |
| Print started (auto-dispatch / cloud / external) | Трекається коли тригер мав авторизованого користувача; на картці принтера під час активного друку. |

Трекінг автоматичний — privacy-тоглера нема. Історична атрибуція **зберігається** навіть коли користувача потім видалили (username рендериться as-recorded, але не клікабельний). Для team-аудиту видавай `stats:filter_by_user` operator-групам — зможуть пивотити дашборди за `started_by` / `uploaded_by`.

---

## :material-package-down: Backup & Restore

Користувачі та групи входять у стандартний backup, якщо при backup-і відмітити **Include users** та **Include groups**:

- **Group definitions + memberships зберігаються** повністю.
- **Паролі НЕ входять** — backup несе username + email + group memberships, ніколи не PBKDF2-хеш. Це навмисно: leak backup-файла не дорівнює leak credentials.
- На restore у кожного користувача порожній пароль. Адміни мають:
  - Виставити паролі вручну для кожного відновленого юзера (Users -> Edit), **або**
  - При увімкненому Advanced Auth — натиснути **Reset password** на кожному користувачу, щоб надіслати свіжий пароль поштою, **або**
  - Направити юзерів на **Forgot password?** флоу якщо SMTP налаштовано.
- TOTP-секрети та OIDC-зв'язки **входять** (encrypted at rest якщо `MFA_ENCRYPTION_KEY` встановлено і на source, і на destination).
- API-ключі НЕ входять — перегенеруй на новій інсталяції.

Плануй rollover у maintenance window, щоб юзери могли пере-виставити паролі без черги збентежених тікетів.

BamDude використовує модель sliding-сесії: короткоживучий access-токен + довгоживучий refresh-cookie з ротацією.

### Access-токени

- **TTL:** 1 година (до 0.4.0 було 24 год).
- **Несуть `jti` + `iat`.** Logout відкликає `jti` токена до його природного закінчення; зміна пароля штампує `users.password_changed_at`, і токени зі старішим `iat` відхиляються як stale на кожному запиті.

### Refresh-токени

- Видаються через `/auth/login`, `/auth/2fa/verify` та `/auth/oidc/exchange`.
- Зберігаються як SHA-256 хеш у `auth_ephemeral_tokens`; доставляються браузеру як cookie `bamdude_refresh` -- **HttpOnly**, **SameSite=Lax**, **Path=/api/v1/auth**. JavaScript його ніколи не бачить; на не-auth ендпоінти він не йде.
- **Ротуються при кожному використанні.** `POST /auth/refresh` ставить старому рядку `used_at=now`, створює новий рядок у тій самій `family_id` і повертає свіжий access-токен.
- **OWASP reuse detection.** Якщо refresh-токен повторно використано (тобто двічі), BamDude закриває всю сім'ю на всіх пристроях. Користувача викидає на login всюди.
- **Окрім кількох секунд одразу після його ж ротації.** Токен, пред'явлений повторно всередині короткого грейс-вікна, вважається гонкою, а не крадіжкою: запит отримує 401, але нічого не відкликається і кука лишається на місці — вкладка, що програла, просто підхоплює те, що вже зберегла переможниця. Без цього дві вкладки, які оновлювались одночасно, виглядали рівно як викрадена сесія і викидали користувача звідусіль — див. *Кілька вкладок* нижче.
- **Logout / зміна пароля / адмін-ініційований MFA-reset** відкликають УСІ refresh-токени користувача, виганяючи його з усіх пристроїв.

### Remember-me

У формі логіну є чекбокс **"Remember me for 30 days"**.

| Режим | TTL рядка в БД | Час життя cookie |
|-------|----------------|------------------|
| За замовчуванням | 24 години | Session cookie (зникає при закритті браузера) |
| Remember me | 30 днів | `Max-Age=30d` -- переживає рестарт браузера |

### Стеля часу життя сесії (Session Policy)

**Settings -> Users -> Session Policy.** Адмінська стеля на те, як довго може жити будь-який логін. Справжнє життя сесії в BamDude — це TTL refresh-токена (access-токени на 1 годину й авто-оновлюються), тож це обмежує TTL refresh-а (та його cookie `Max-Age`) при логіні та на кожній ротації.

- **Пресети:** 24 години / 7 днів / 30 днів, плюс поле власних годин.
- **Діапазон:** мінімум 1 година, **максимум 720 годин (30 днів)** -- та сама жорстка стеля, що й remember-me.
- **За замовчуванням:** 720 годин (30 днів), тож існуючі remember-me сесії переживають оновлення недоторканими.
- Зниження діє на існуючі сесії при їх **наступному refresh** -- коротший TTL застосовується, коли refresh-cookie наступного разу ротується, не заднім числом.

Картка read-only для користувачів без `settings:update`.

### Поведінка фронтенду

Хелпер `request()` на фронті прозоро ретраїть 401 через `/auth/refresh`, **promise-coalesced**, тож хвиля паралельних запитів породжує рівно один виклик refresh. Коалесинг працює **між вкладками** через Web Locks API: та вкладка, що взяла лок, робить refresh, а решта підхоплює збережений нею токен замість власного запиту. Проактивне оновлення ще й джитериться, щоб вкладки, які залогінились разом, не прокидались усі в один момент. Якщо refresh теж впав, глобальна подія `bamdude:auth-invalidated` чистить React-state і робить hard-redirect на `/login`. Слухач `visibilitychange` проактивно ревалідовує `/auth/me`, коли прихована вкладка повертає фокус.

### Кілька вкладок

Дві чи більше вкладок BamDude ділять одну сесію — і домовляються між собою, а не змагаються.

Кожна вкладка планує тихе оновлення незадовго до того, як спливе access-токен. Якщо їх не координувати, усі вкладки порахують один і той самий момент з одного й того самого токена і вистрелять разом — а сервер, який вважає друге використання refresh-токена ознакою викрадення, закриє всю сім'ю і розлогінить скрізь. При двох відкритих вкладках це траплялось приблизно раз на годину і виглядало як сесія, що протухла без причини.

Тепер цьому заважає три речі:

- **Міжвкладковий лок.** Refresh робить та вкладка, яка взяла запис у Web Locks; решта чекає й підхоплює збережений нею токен.
- **Джитер.** Час оновлення рознесено на кілька секунд, щоб вкладки, залогінені разом, не прокидались у лок-степ.
- **Грейс-вікно на сервері.** Refresh-токен, пред'явлений повторно через секунди після власної ротації, отримує 401 і більше нічого — без відкликання, без чистки куки. Справжній повтор, пізніше, так само закриває сім'ю.

Якщо браузер не має Web Locks API, вкладки відкочуються на коалесинг у межах вкладки плюс серверний грейс — та сама гонка покрита.

### Атрибут `Secure` для cookie

`Secure` авто-визначається зі схеми запиту. За реверс-проксі виставте `TRUSTED_PROXY_IPS` (через кому), щоб BamDude читав оригінальний заголовок `X-Forwarded-Proto`.

```ini
# .env
TRUSTED_PROXY_IPS=10.0.0.1,10.0.0.2
```

Для крайових випадків (наприклад, TLS-термінуючий load balancer не виставляє `X-Forwarded-Proto`) форсуйте полярність:

=== "Force Secure on"

    ```ini
    AUTH_REFRESH_COOKIE_SECURE=true
    ```

=== "Force Secure off"

    ```ini
    AUTH_REFRESH_COOKIE_SECURE=false
    ```

---

## :material-shield-key: Багатофакторна автентифікація

2FA вмикає сам користувач. Кожен може зареєструвати один або кілька факторів через **Settings -> Profile -> Two-Factor Authentication**.

### Фактори

| Фактор | Як працює |
|--------|-----------|
| **TOTP** | Authenticator-застосунок (Google Authenticator, Aegis, Authy, 1Password, ...). Шестизначний rolling-код, генерується з Fernet-зашифрованого секрету. |
| **Email OTP** | Одноразовий код, що приходить на email користувача. Корисно як fallback, коли TOTP незручний. |
| **Резервні коди** | 10 одноразових кодів, згенерованих при реєстрації. Показуються **один раз** -- зберігайте офлайн. Перегенеруйте будь-коли, щоб інвалідувати старий набір. |

### Login-флоу з 2FA

1. Користувач сабмітить username + пароль.
2. Сервер перевіряє облікові дані, повертає `requires_2fa=true`, короткоживучий `pre_auth_token` і 2fa-challenge cookie.
3. UI показує picker 2FA (TOTP / email / резервний код).
4. Користувач сабмітить код у `/auth/2fa/verify`.
5. Сервер повертає access-JWT і виставляє refresh-cookie. Логін завершено.

### Шифрування at rest

TOTP-секрети та OIDC client secrets шифруються Fernet-ом у БД. Резервні коди хешуються через pbkdf2 у будь-якому разі. **Починаючи з 0.4.4, шифрування ввімкнене за замовчуванням** -- BamDude автоматично завантажує / генерує ключ при першому старті, тож свіжа інсталяція ніколи мовчки не зберігає секрети у відкритому вигляді.

**Порядок резолвінгу ключа** (спрацьовує перший):

1. Змінна середовища `MFA_ENCRYPTION_KEY` -- явний пін (рекомендовано для multi-host / multi-worker деплоїв, де один ключ має бути спільним).
2. Файл `DATA_DIR/.mfa_encryption_key` (мод `0o600`) -- single-host інсталяції зазвичай тут.
3. Авто-генерація -- при першому старті BamDude створює свіжий Fernet-ключ і записує його в `.mfa_encryption_key`. Атомарне створення з `O_EXCL` -- мод-біти правильні з першого байта; ніколи world-readable.

```ini
# .env (опційно -- лише коли треба пінити конкретний ключ)
MFA_ENCRYPTION_KEY=<base64 32-byte Fernet key>
```

!!! tip "Згенерувати ключ"
    `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`

!!! info "Панель статусу"
    **Settings → Authentication → Security** показує живу картку статусу з п'ятьма рівнями серйозності:

    - 🟢 **Зелений** -- ключ налаштовано, всі секрети зашифровані.
    - 🟡 **Янтарний** -- ще лишилися рядки у відкритому вигляді (будуть перешифровані при наступному записі) **або** ключ був авто-згенерований (зробіть бекап `DATA_DIR/.mfa_encryption_key`, інакше майбутній restore на новому хості не зможе розшифрувати секрети).
    - 🔴 **Червоний** -- розшифрування зламане (ключ налаштовано, але існуючі рядки не розшифровуються -- буває після ротації ключа або cross-deployment restore, де працююча інсталяція тримає неправильний ключ). Відновлення: відновіть оригінальний файл ключа або пере-зареєструйте задіяних користувачів.
    - ⚫ **Сірий** -- не налаштовано і немає зашифрованих рядків.

!!! warning "Інтеграція з бекапами"
    `.mfa_encryption_key` пакується в backup ZIP поряд з `bamdude.db`. Restore на новому хості розпаковує ключ **до** свопу БД з `chmod 0o600` -- self-contained бекап зберігає доступ до зашифрованих секретів без ручного втручання. Restore переривається з чітким 500, якщо запис ключа провалюється (RO disk / EACCES) до того, як БД підмінено -- так live-інсталяція ніколи не отримає невідповідну пару "БД + ключ".

!!! note "Шлях оновлення legacy-інсталяцій"
    Pre-0.4.4 інсталяції, що працювали з `MFA_ENCRYPTION_KEY` unset, мають у БД відкриті рядки. На наступному старті після оновлення авто-bootstrap згенерує ключ, і одноразова міграція пере-шифрує ці рядки на місці. Per-row транзакції: один пошкоджений рядок не блокує інших, а кількість пропущених рядків виноситься в картку статусу -- так ви бачите poison-row, що потребують уваги.

### Адмін-ініційований reset

Якщо користувач загубив пристрій-аутентифікатор, адмін може запустити для нього 2FA-reset зі сторінки Users. Reset вимикає всі фактори **і відкликає всі refresh-токени** цього акаунта, тож будь-яка залогінена сесія обривається -- користувач заходить наново лише за паролем і реєструє MFA знову.

---

## :material-account-key: OIDC / SSO

BamDude підтримує OpenID Connect single sign-on проти будь-якого провайдера, що відповідає стандарту.

### Налаштування провайдера

**Settings -> Authentication -> OIDC Providers -> Add provider.**

| Поле | Примітки |
|------|----------|
| **Display name** | Підпис на кнопці логіну ("Sign in with Authentik"). |
| **Issuer URL** | База discovery-URL провайдера (наприклад, `https://auth.example.com/`). Має бути HTTPS. |
| **Client ID** | З BamDude-реєстрації застосунку у провайдера. |
| **Client secret** | Fernet-шифрується at rest, коли встановлено `MFA_ENCRYPTION_KEY`. |
| **Scopes** | За замовчуванням `openid profile email`. Додавайте scopes провайдера за потреби. |
| **Claim mapping** | Який OIDC-claim мапиться на BamDude username / email. |
| **Auto-create users** | За замовчуванням вимкнено -- нові логіни мають збігатися з існуючим локальним користувачем за email. Увімкнено = користувач створюється автоматично (потрапляє в групу з поля **Default group** нижче). |
| **Default group** | Група, у яку потрапляють нові авто-створені користувачі. За замовчуванням -- **Viewers (read-only)** для безпеки; обирайте кастомну групу для tenant-internal SSO, де read-only занадто обмежує. Список беремо з живих груп, тож будь-яка група, створена в **Settings → Authentication → Groups**, тут видна. Якщо обрану групу пізніше видалити, нові логіни падатимуть назад на **Viewers**. |

Сторінка логіну рендерить кнопку "Sign in with `<provider>`" для кожного налаштованого провайдера, нижче форми пароля.

### Загартування

- **PKCE S256** -- обов'язковий, без варіантів.
- **State + nonce** -- обидва перевіряються в callback. State-токен атомарно споживається, тому replay-атаки фейляться.
- **JWKS-перевірка** -- ID-токени верифікуються підписом проти JWKS, опублікованого провайдером.
- **SSRF-захист** -- issuer URL має бути HTTPS і не повинен резолвитися на loopback, приватні (RFC 1918) чи link-local адреси.

### Autologin і вимкнення локального входу

Для команди, що живе повністю всередині свого IdP, BamDude може пропустити форму пароля:

- **Autologin** -- per-provider тоглер (нести його може лише один провайдер -- увімкнення на одному скидає його на всіх інших), що перенаправляє неавтентифікованих відвідувачів одразу на authorize-URL цього IdP при завантаженні сторінки, поки той провайдер лишається enabled. Deep-link зберігається через SSO round-trip, тож збережений `/archives/42` повертається туди ж після входу. Запит authorize-URL змагається з 5-секундним таймаутом; при таймауті чи помилці BamDude відкочується на звичайну сторінку логіну й показує банер з поясненням, чому autologin не спрацював.
- **Вимкнути локальний вхід за username/password** -- супутній перемикач (Settings -> Users), що повністю ховає форму пароля, лишаючи тільки OIDC. Він захищений від локауту: увімкнути не вдасться, поки **не увімкнено хоча б один OIDC-провайдер** *і* **твій власний акаунт не залінкований з OIDC** -- інакше ти замкнеш сам себе.

!!! tip "Відновлення, коли SSO лежить"
    Якщо IdP недосяжний і локальний вхід вимкнено, форму пароля повертають два запасні виходи: додай `?fallback=local` до URL логіну (`/login?fallback=local`), або встанови серверну env-змінну `BAMDUDE_LOCAL_LOGIN=true`, яка перекриває збережене налаштування, тож host-адмін завжди зможе зайти локально.

### Self-signed CA

Якщо провайдер ходить за самопідписаним сертифікатом (типово для self-hosted Authentik / Keycloak), зробіть CA-ланцюг видимим для HTTP-клієнта BamDude. **Окремої env-змінної `OIDC_CA_BUNDLE_PATH` немає** — натомість покладайте довірений root у системний bundle, який читає Python `ssl`:

- **Контейнерні деплої**: bind-mount-те ваш CA у `/usr/local/share/ca-certificates/` і запустіть `update-ca-certificates` в образі, або задайте стандартні env `SSL_CERT_FILE` / `REQUESTS_CA_BUNDLE` на mount-нутий PEM-файл.
- **Native-інстали**: киньте CA у trust store ОС (`/etc/ssl/certs/` на Debian/Ubuntu через `update-ca-certificates`).

Це ті самі ручки, які поважає кожен Python HTTPS-клієнт — `httpx` (через нього BamDude робить discovery + token + JWKS-запити) їх читає прозоро.

!!! warning "Не вмикайте auto-link по email легковажно"
    Auto-create + auto-link до існуючих локальних акаунтів означає, що скомпрометований IdP може захопити будь-якого локального користувача зі збіжним email. Лишайте обидва вимкненими, поки не довіряєте провайдеру не менше, ніж власним хешам паролів.

### Microsoft Azure / Entra ID — кастомний email-claim

Microsoft Entra ID (раніше Azure AD) не шле стандартний `email`-claim і прапор `email_verified` — він кладе ідентифікатор користувача в `preferred_username` чи `upn` і припускає верифікацію на стороні IdP. У BamDude для цього кейсу є два додаткові поля на провайдер:

| Поле | Ефект |
|---|---|
| **Email claim** | Який OIDC-claim BamDude читає як email користувача. Default `email`. Для Entra ID — `preferred_username` чи `upn`. Whitelist regex `[a-zA-Z][a-zA-Z0-9_\-]{0,63}` блокує log-injection / dynamic-claims-lookup attack-вектори. |
| **Require email_verified** | Default ON (відмовляє логінити, поки IdP не позначить email верифікованим). Entra ID цей прапор не шле взагалі — для Entra ID вимикай. |

Є жорсткий guard проти небезпечного поєднання: `auto_link_existing_accounts=true` AND `email_claim='email'` AND `require_email_verified=false` відхиляється на save (і як DB-level CHECK на Postgres) — без цього гейта будь-який IdP, що дозволяє self-register з довільним email, міг би мовчки захопити existing локальні акаунти. Кастомні email-claims (`preferred_username`, `upn`, etc.) автоматично оминають вимогу verified-check, бо семантика claim'у інша.

Тоглер "Require email verified" у формі автоматично disabled (сірий) коли `email_claim != "email"` — нема `email_verified`, який можна було б перевіряти на кастомному claim'і. Бонус — два `<datalist>` autocomplete'и з `email` / `preferred_username` / `upn`, щоб не друкувати руками.

!!! tip "Перевірені IdP"
    OIDC-флоу BamDude перевірений з PocketID, Authentik, Keycloak, Authelia, Google і Microsoft Entra ID (Azure AD). Інші стандарт-сумісні провайдери мають працювати — повідом, якщо упрешся в edge-кейс.

---

## :material-speedometer: Лімітування частоти запитів

Sliding-window бакети стоять перед ендпоінтами, що приймають пароль. Бакети зберігаються в таблиці `auth_rate_limit_events` -- глобального локу нема, тож легітимні користувачі в одній мережі не страждають через атакувальника, що б'є коди десь поряд.

| Ендпоінт | На користувача | На IP |
|----------|----------------|-------|
| `POST /auth/login` | 10 / 15 хв | 20 / 15 хв |
| `POST /auth/forgot-password` | 3 / 15 хв (на email) | 10 / 15 хв |

Forgot-password записує спробу **жадібно** -- ендпоінт завжди повертає success (анти-енумерація), тож rate limit -- єдине, що стримує перебір email-ів.

### За реверс-проксі

Якщо BamDude стоїть за nginx / Caddy / Traefik / Cloudflare, виставте `TRUSTED_PROXY_IPS`, щоб лімітер брав **оригінальний IP клієнта** з `X-Forwarded-For`, а не IP проксі -- інакше всі запити поділять IP проксі і ліміт спрацює за кілька логінів.

```ini
# .env -- через кому, без пробілів
TRUSTED_PROXY_IPS=10.0.0.1,172.16.0.1
```

Multi-hop ланцюги (nginx -> Cloudflare -> BamDude) обробляються right-to-left резолвом: BamDude йде по `X-Forwarded-For` справа наліво і приймає крайній правий IP, який **не** в trusted-наборі, як справжнього клієнта.

!!! info "Single-host деплой"
    На інсталяції без проксі лишайте `TRUSTED_PROXY_IPS` незаданим. BamDude фолбекне на прямий TCP peer IP, що в цьому разі коректно.

---

## :material-form-textbox-password: Парольна політика

Узгоджена з [NIST SP 800-63B](https://pages.nist.gov/800-63-3/sp800-63b.html). Композиційні правила, окрім розумного мінімуму, NIST вважає малокорисним тертям; BamDude дотримується тієї ж лінії.

**На create / change / reset:**

- Хоча б одна **велика** літера
- Хоча б одна **мала** літера
- Хоча б одна **цифра**
- Мінімум **8 символів**
- Максимум **256 символів** (розумний верхній ліміт, щоб обмежити вартість pbkdf2)

Без вимоги спецсимволу (видалено в 0.4.0.1 -- раніше було обов'язковим, тепер вважається шумом, що штовхає до передбачуваних замін).

Інші ліміти довжини на auth-ендпоінтах: email **254** (RFC 5321), username **150**, forgot-password token **128**.

### Зміна пароля вбиває сесії

Зміна власного пароля (або reset адміном) штампує `users.password_changed_at`. Будь-який access-токен зі `iat` старішим за цю мітку відхиляється як stale на наступному запиті, а кожен refresh-токен користувача відкликається. Результат: зміна пароля миттєво вилогінює з усіх пристроїв -- так, як і має бути.

---

## :material-tools: Відновлення адміна

Якщо ви якимось чином втратили доступ до всіх адмінських акаунтів -- забутий пароль, втрачений MFA-пристрій без резервних кодів, видалений єдиний адмін -- можна скинути setup-gate з shell-у на хості.

```bash
# Спочатку зупиніть сервер.
docker compose stop bamdude
# АБО для нативної інсталяції:
systemctl stop bamdude

# Запустіть reset CLI проти тієї ж БД, яку використовує сервер.
python -m backend.app.cli reset_admin

# Перезапустіть.
docker compose start bamdude
```

`reset_admin` чистить прапор setup-complete та осиротілі рядки `user_groups`, тож наступний старт знов потрапляє у форму **first-boot setup**. Ви створите нового адміна з нуля -- і **всі ваші існуючі дані (принтери, архіви, черга, користувачі, бібліотека) збережуться**. Перестворюється лише сам адмін-акаунт.

!!! warning "Запускайте при зупиненому сервері"
    І CLI, і сервер тримають SQLite WAL. Запуск їх одночасно може пошкодити БД. Спочатку зупиняйте сервер.

---

## :material-help-circle: Усунення несправностей

### "Cannot access feature" / кнопка сіра

Disabled-контрол з тултіпом ("you need *X* permission") означає, що у твоєму ефективному permission-сеті її нема. Іди по ланцюгу:

1. Відкрий **Settings -> Users**, знайди свій рядок, перевір у яких ти **групах**.
2. Відкрий **Settings -> Users -> Groups**, клікай по кожній своїй групі, упевнись що відсутнього права справді нема.
3. Якщо мав би мати доступ — попроси адміна додати право в одну з твоїх груп (або перенести тебе в групу, де воно вже є).
4. Розбіжність `*_own` vs `*_all`: перевір, чи ресурс **ownerless** — тоді працює лише `*_all`.

### Сесія завершилась посеред дії

Access-токени — 1 година. Зазвичай refresh-cookie тримає тебе залогіненим прозоро; якщо refresh теж впав (cookie expired, сервер рестартанули з новим секретом, пароль змінили деінде), тебе hard-redirect-нуть на `/login`. Залогінься і продовжуй — in-flight-форми не зберігаються.

### "setup_required" 503 після апгрейду

Setup-gate cache думає, що адмін не існує. Рестартни контейнер — gate чиститься на наступному boot якщо хоч один admin-row є в БД. Якщо лишається — admin-юзера, певно, видалили; запусти `python -m backend.app.cli reset_admin` і перестворюй.

### Forgot password (SMTP нема)

Без Advanced Auth лінк **Forgot password** прихований. Попроси адміна reset-нути пароль зі **Settings -> Users -> Edit -> set new password**. З Advanced Auth — просто **Forgot password?** на login-сторінці.

### LDAP-юзери не логіняться, локальний адмін заходить

Майже завжди — connectivity issue з directory. Відкрий **Settings -> Authentication -> LDAP -> Test connection** і прочитай raw error. Типові причини: VPN відвалився, AD service-account password ротувався, LDAPS-серт прострочився, фаєрвол закрив 636/389.

---

## :material-lightbulb: Поради

!!! tip "Зареєструйте TOTP для кожного адміна"
    Адмінські акаунти тримають ключі від ферми. TOTP + офлайн резервні коди -- мінімальна планка для будь-якого акаунта, що може змінювати налаштування або видаляти архіви.

!!! tip "Шифруйте MFA-секрети"
    Виставте `MFA_ENCRYPTION_KEY` до того, як реєструвати користувачів. Plaintext-секрети працюють, але encrypted-at-rest -- це на один пункт менше у списку при наступному backup-аудиті.

!!! tip "Використовуйте OIDC для команд"
    Якщо у вас уже стоїть Authentik / Keycloak / Pocket-ID для решти homelab-у, увімкніть BamDude у нього -- отримаєте групову синхронізацію, MFA та offboarding безкоштовно, не підтримуючи паралельний паролеве сховище.

!!! tip "Роздрукуйте резервні коди"
    Резервні коди показуються **один раз**. Роздрукуйте їх, киньте у secure notes менеджера паролів, або і те, й інше -- але не сподівайтеся, що згадаєте записати їх пізніше.
