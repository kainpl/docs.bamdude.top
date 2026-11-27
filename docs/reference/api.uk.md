---
title: Довідка API
description: Посібник з інтеграції REST API BamDude — автентифікація, права, rate limits, групи endpoint-ів та рецепти.
---

# Довідка API

BamDude надає версіоноване REST API за адресою `/api/v1` плюс канал WebSocket для подій принтерів у реальному часі. Усе, що робить веб-інтерфейс, доступне і вашим скриптам та інтеграціям.

---

## API майстерні: товар із файлу

`POST /api/v1/products/from-file/{id}` повертає `{product, notes}`. Поля створеного товару читайте під `product`; `notes` пояснює, що заповнив файл. Джерело має бути доступним за правами бібліотеки цього користувача. Замовлення, Товари, Замовники і Склад мають окремі права, тож власній групі потрібні права тих розділів, з якими вона працює.

## :material-rocket-launch: Швидкий старт

- **Базовий URL:** `https://<your-bamdude-host>/api/v1`
- **Інтерактивна документація:** [`/docs`](#) (Swagger UI) та [`/redoc`](#) (ReDoc)
- **OpenAPI-схема:** `/openapi.json` — підключайте до Postman, Insomnia або будь-якого OpenAPI-сумісного клієнта
- **Канал реального часу:** `wss://<your-bamdude-host>/api/v1/ws`

Усі endpoint-и повертають JSON, якщо не вказано інше (потоки камери, завантаження 3MF та мініатюри повертають бінарні дані). Помилки мають форму FastAPI:

```json
{ "detail": "Not authenticated" }
```

Помилки валідації `422` повертають масив проблем рівня поля:

```json
{
  "detail": [
    { "loc": ["body", "name"], "msg": "field required", "type": "value_error.missing" }
  ]
}
```

!!! tip "Спочатку відкрийте `/docs`"
    Інтерактивний Swagger UI генерується з живого сервера, тому завжди відображає маршрути, схеми та потрібні права тієї версії, що у вас запущена. Цю сторінку сприймайте як орієнтир; джерелом істини вважайте `/docs`.

---

## :material-key: Методи автентифікації

BamDude підтримує два механізми автентифікації. Обидва застосовують однакові перевірки прав. API-ключі звіряються першими; якщо жоден заголовок не присутній, запит проходить далі до JWT.

=== "API-ключ (рекомендовано для скриптів)"

    Створіть ключі в **Налаштування → API ключі**. Вони мають вигляд `bd_<random_token>` і ніколи не закінчуються автоматично — відкликайте їх по одному, коли вони більше не потрібні.

    Надсилайте через будь-який заголовок:

    ```bash
    # Preferred: dedicated header
    curl -H "X-API-Key: bd_abc123..." \
      https://bamdude.example.com/api/v1/printers/

    # Equivalent: bearer scheme
    curl -H "Authorization: Bearer bd_abc123..." \
      https://bamdude.example.com/api/v1/printers/
    ```

    Кожен ключ має власний набір прав — підмножину прав користувача, що його випустив. Видалення користувача анулює його ключі.

=== "JWT session token (використовується веб-інтерфейсом)"

    Браузерний потік:

    ```bash
    curl -X POST -H "Content-Type: application/json" \
      -d '{"username": "admin", "password": "...", "remember_me": true}' \
      https://bamdude.example.com/api/v1/auth/login
    ```

    Відповідь:

    ```json
    {
      "access_token": "eyJhbGc...",
      "token_type": "bearer",
      "requires_2fa": false,
      "user": { "id": 1, "username": "admin", "...": "..." }
    }
    ```

    Надсилайте access-токен через `Authorization: Bearer <jwt>`. **Access-токени живуть 1 годину.** Refresh-токен встановлюється як HttpOnly cookie (`bamdude_refresh`) на шляху `/api/v1/auth` — викликайте `POST /api/v1/auth/refresh`, щоб прозоро отримати новий access-токен. Атрибути cookie:

    | Атрибут | Значення |
    |---------|----------|
    | Path     | `/api/v1/auth` (ваш клієнт повинен це зберігати) |
    | HttpOnly | так — ніколи не доступний JavaScript |
    | SameSite | `Lax` |
    | Secure   | автовизначення зі схеми запиту; враховує `X-Forwarded-Proto` за довіреним проксі. Примусово встановлюється env-змінною `AUTH_REFRESH_COOKIE_SECURE`. |
    | Max-Age  | 30 днів коли `remember_me=true`; інакше session cookie + 12 год часу життя в БД |

    !!! warning "Потік 2FA"
        Коли `requires_2fa: true`, відповідь login також містить `pre_auth_token` та cookie 2FA-челенджу. Надішліть POST на `/api/v1/auth/2fa/verify` разом з TOTP-кодом користувача (або резервним кодом), щоб отримати access + refresh токени.

    OIDC SSO працює за тим самим шаблоном через `/api/v1/auth/oidc/exchange` (PKCE S256 + state + nonce).

---

## :material-speedometer: Rate limiting

BamDude обмежує частоту запитів на endpoint-ах автентифікації, щоб уповільнити credential stuffing. Інші endpoint-и не мають rate limit на рівні API — поставте перед ними реверс-проксі або фаєрвол, якщо потрібна жорстка межа.

| Endpoint | На користувача / email | На IP |
|----------|------------------------|-------|
| `POST /auth/login` | 10 / 15 хв на ім'я користувача | 20 / 15 хв |
| `POST /auth/forgot-password` | 3 / 15 хв на email | 10 / 15 хв |

Коли ліміт спрацьовує, ви отримуєте `429 {"detail": "..."}` та заголовок `Retry-After`.

!!! tip "За реверс-проксі"
    Встановіть `TRUSTED_PROXY_IPS` (через кому довірені хопи), щоб rate limit зчитував реальний IP клієнта з `X-Forwarded-For`, а не IP проксі. Повні рецепти для nginx / Caddy / Traefik див. у [Реверс-проксі та HTTPS](../getting-started/reverse-proxy.md).

---

## :material-shield-lock: Setup-шлюз

Під час першого запуску сервер приймає лише три endpoint-и. Усі інші запити повертають `503 {"detail": "setup_required"}`, доки не буде створено адміністратора.

| Endpoint | Призначення |
|----------|-------------|
| `GET  /api/v1/auth/status` | Повертає `{is_setup, requires_setup, ...}`, щоб інсталятори могли визначити стан порожньої БД. |
| `POST /api/v1/auth/setup`  | Одноразовий: створює початкового адміна та повертає access + refresh токени. |
| `GET  /api/v1/system/health` | Перевірка живучості (завжди в білому списку). |

Після завершення setup шлюз вимикає себе у пам'яті процесу; перезапуск не потрібен.

!!! danger "Втратили всіх адмінів?"
    Виконайте `python -m backend.app.cli reset_admin` на сервері, щоб скинути setup-прапорці, потім зайдіть в інтерфейс і пройдіть setup ще раз. Повний протокол відновлення див. у [Відновлення автентифікації](../features/authentication.md).

---

## :material-lock-check: Права

Кожен endpoint захищено через `RequirePermission(Permission.X)`, де `X` слідує шаблону `resource:action`. У `backend/app/core/permissions.py` визначено **80+ прав**. Поширені:

| Ресурс | Приклади |
|--------|----------|
| Printers | `printers:read`, `printers:control`, `printers:create`, `printers:delete`, `printers:files`, `printers:clear_plate` |
| Archives | `archives:read`, `archives:create`, `archives:update_own`, `archives:update_all`, `archives:delete_own`, `archives:delete_all`, `archives:reprint_own`, `archives:reprint_all` |
| Library  | `library:read`, `library:upload`, `library:update_own`, `library:delete_all`, `library:notes_write` |
| Queue    | `queue:read`, `queue:create`, `queue:update_all`, `queue:delete_all`, `queue:reorder` |
| Users    | `users:read`, `users:create`, `users:update`, `users:delete` |
| Settings | `settings:read`, `settings:update`, `settings:backup`, `settings:restore` |
| Camera   | `camera:view` |

Три типові групи покривають більшість сценаріїв:

- **Administrators** — усі права.
- **Operators** — повний контроль над принтерами, чергою, архівами, бібліотекою; без адміністрування налаштувань / користувачів.
- **Viewers** — лише читання.

Створюйте власні групи для тонкого контролю. Інтерактивний браузер `/docs` показує необхідне право для кожного endpoint-у.

---

### Видалення акаунта й контенту

`DELETE /api/v1/users/{user_id}?delete_items=true` вимагає адміністратора з `users:delete` та звичайних прав на зміну прив’язки/наслідки для зачепленої роботи замовлень. Успіх — **200 JSON**, а не 204:

```json
{"deleted":true,"counts":{"archives":1,"library_files":0,"queue_items":0,"auto_queue_items":0},"affected_orders":[]}
```

`affected_orders` містить дозволені знімки `id`/`name` і кількості прибраних `prints`/`jobs`. Потрібну незавершену роботу слід запланувати знову: планові кількості автоматично не повертаються. Уся транзакція відмовляє з **409** і `detail.error`: `user_content_delete_active`, `user_content_delete_too_large` або `user_content_delete_changed`. Владнайте утриману/активну роботу звичайними засобами черги чи відновлення стану; великий контент приберіть через його сторінки; для зміненого плану повторіть операцію. Межа — 8 батьківських записів (разом із використаними джерелами бібліотеки) і 1 000 зачеплених рядків, включно з нащадками акаунта/сесій/ключів. Відмови прив’язки друку чи вже прийнятого результату зберігають власні статус і причину. Відмова не змінює рядків і не видаляє файлів.

З `delete_items=false` (типово) успіх лишається **204 без тіла**, а контент стає без власника. Видалення себе й останнього адміністратора заборонене в обох режимах. Історія фізичних запасів/витрат і незмінні факти завершення зберігаються.

---

## :material-routes: Групи endpoint-ів

43 модулі маршрутів у `backend/app/api/routes/` зареєстровані під префіксом `/api/v1`. Основні групи на одному екрані:

| Префікс | Що робить | Помітні endpoint-и |
|---------|-----------|--------------------|
| `/auth/*` | Логін, refresh, setup, OIDC | `login`, `refresh`, `logout`, `setup`, `2fa/verify`, `oidc/exchange`, `forgot-password` |
| `/users/*`, `/groups/*`, `/api-keys/*`, `/mfa/*` | Користувачі, групи, API-ключі, реєстрація MFA | CRUD, призначення груп, скидання MFA, резервні коди |
| `/printers/*`, `/cloud/*`, `/discovery/*` | Принтер + AMS + Bambu Cloud | статус, керування, RFID AMS, snapshot, stream-токен, мережеве виявлення |
| `/archives/*` | Історія друку | список (`?outcome=unchecked` — завершені друки, результат яких ніхто не перевірив), отримання, передрук, видалення, **`outcome-checked`**, **`retry-download`**, **`cleanup/preview`**, **`cleanup/run`**, **`cleanup/status`** |
| `/queue/*`, `/queues/*`, `/background-dispatch/*` | Керування чергою + dispatch | додавання, перевпорядкування, скасування, set-status, стан dispatch-у; власний стан черги принтера на `/queues/{id}` (пауза, відновлення, `acknowledge-failure`) |
| `/library/*` | Файловий менеджер | завантаження, список, видалення, теги, нотатки (`files/{id}/notes`, `notes/{id}`), фото (`files/{id}/photos`), власне посилання файла (`files/{id}/external-url`), перейменування й переміщення папок (`PUT folders/{id}`), зовнішні папки та їхні скани (`folders/external`, `folders/{id}/scan`, `scan-jobs/{id}`) — і водночас інбокс для аплоадів з віртуального принтера. Права кожного маршруту: [Файловий менеджер → API-ендпоінти](../features/file-manager.uk.md#api-endpoints) |
| `/model-sources/manyfold/*` | Джерело моделей Manyfold | стан, список і пошук моделей (`models`), модель з її файлами (`models/{model_id}`), її зображення, імпорт одного файла (`import`) та підключення (`connection`, `connection/test`). Права для кожного маршруту: [Бібліотека Manyfold → Довідка для розробників](../features/manyfold.md#developer-reference) |
| `/projects/*` | Групування за проєктами | CRUD, план друку, архіви проєкту |
| `/macros/*` | G-code- та MQTT-action-макроси | CRUD, виконання |
| `/notifications/*`, `/notification-templates/*`, `/user-notifications/*`, `/telegram/*` | Вихідні канали | CRUD провайдерів, перевизначення шаблонів, тестове надсилання, конфіг Telegram-бота, [повідомлення від зовнішніх програм](../features/notifications.uk.md#external-app-messages) (`POST /notifications/external-message`) |
| `/spoolman/*`, `/inventory/*` | Облік котушок | синхронізація, мапінг слотів, каталог кольорів/котушок |
| `/smart-plugs/*` | Конфіг розумних розеток | CRUD, енергетичні snapshot-и, ручне on/off |
| `/system/*`, `/support/*`, `/updates/*`, `/firmware/*` | Здоров'я + діагностика + оновлення | `health`, налаштування, бекап, відновлення, debug-bundle, перевірка прошивки |
| `/local-backup/*`, `/git-backup/*` | Провайдери бекапів | запуск, відновлення, розклад |
| `/maintenance/*`, `/kprofiles/*` | Облік сервісного обслуговування + K-профілі | журнал, заплановане, CRUD |
| `/external-links/*`, `/ams-history/*` | Різні UX | посилання дашборду, історія зміни слотів AMS |
| `/metrics`, `/webhook/*`, `/obico/*`, `/octoeverywhere/*`, `/virtual-printers/*` | Інтеграції | метрики Prometheus, вхідні webhook-и, AI-виявлення збоїв (Obico, OctoEverywhere), віртуальний принтер (ціль для slicer-а) |

Повний перелік є в `/docs` — ця таблиця лише вказує, де шукати.

---

## :material-camera-iris: Потоки камери та бінарні endpoint-и { #camera-streams-and-binary-endpoints }

Деякі endpoint-и споживають теги `<img>` / `<video>`, які не можуть надіслати заголовок `Authorization`, тож вони приймають ще й короткоживучий токен (TTL 60 хв) як query-параметр `?token=`. Таких токенів два, і вони не взаємозамінні:

- **stream-токен** — камера: live-потік, знімок, reference детекції столу;
- **медіатокен** — усі інші картинки й відео: мініатюри, прев'ю плит, таймлапси, QR-коди, обкладинки.

Скрипту чи інтеграції жоден не потрібен: ті самі endpoint-и приймають звичайний заголовок `X-API-Key` / `Authorization` у межах дозволів ключа.

```bash
# 1. Mint a token (auth required)
TOKEN=$(curl -s -H "X-API-Key: bd_..." \
  -X POST https://bamdude.example.com/api/v1/printers/camera/stream-token \
  | jq -r .token)

# 2. Use it on binary endpoints
curl "https://bamdude.example.com/api/v1/printers/2/camera/snapshot?token=$TOKEN" -o snap.jpg
```

Endpoint-и за stream-токен-шлюзом (щоб його отримати, потрібен `camera:view`):

| Endpoint | Повертає |
|----------|----------|
| `GET /printers/{id}/camera/stream?token=...` | потік MJPEG |
| `GET /printers/{id}/camera/snapshot?token=...` | JPEG-знімок |
| `GET /cameras/{id}/stream?token=...` · `GET /cameras/{id}/snapshot?token=...` | те саме для окремої камери |
| `GET /printers/{id}/camera/plate-detection/references/{index}/thumbnail?token=...` | мініатюра калібраційного reference-фрейма для детекції очищеного столу (`{index}` вибирає, який зі збережених референсів). |
| `GET /obico/cached-frame/{nonce}` | URL кадру, який передається в ML-API Obico. Стоїть у білому списку auth-middleware, бо GET від Obico не може нести bearer-заголовок — самим капабіліті є nonce. |

**Медіатокен** отримує будь-який залогінений користувач через `POST /auth/media-token` (JWT, не API-ключ — ключ натомість шле свій заголовок). Токен називає користувача, тож кожен endpoint застосовує правило дозволів і власності того, що віддає, — користувач, обмежений власними друками, отримує лише свої картинки:

| Endpoint | Дозвіл |
|----------|--------|
| `GET /archives/{id}/thumbnail` · `/plate-thumbnail/{n}` · `/plate-preview` · `/project-image/{path}` · `/qrcode` · `/timelapse` · `/photos/{file}` | `archives:read_all` / `archives:read_own` |
| `GET /library/files/{id}/thumbnail` · `/plate-thumbnail/{n}` · `/card-file/{path}` · `/image` · `/photos/{photo_id}/image` · `/photos/{photo_id}/thumbnail` · `GET /makerworld/imports/{id}/cover` · `/cover-variant` | `library:read_all` / `library:read_own` |
| `GET /products/{id}/attachment-image/{file}` · `/cover-image` · `GET /projects/{id}/cover-image` | `products:read` для зображень виробу, `orders:read` для обкладинки замовлення |
| `GET /printers/{id}/camera-cover` | `printers:read` — обкладинка поточного завдання з локального архіву (ніколи не ініціює FTP-вибірку) |
| `GET /makerworld/thumbnail?url=...` | `makerworld:view` |
| `GET /model-sources/manyfold/models/{model_id}/preview` | `manyfold:view` |

Публічні, без токена: `GET /notifications/photos/{file}` (копія одного фото, на яку посилається сповіщення, для сервісів, що тягнуть без облікових даних, — адресу неможливо вгадати, і вона перестає працювати через 3 дні), `GET /external-links/{id}/icon` і `GET /auth/oidc/providers/{id}/icon` (сторінка входу). Токен Cam Wall, оверлею чи кіоску не відкриває жодного медіа-endpoint-а.

Веб-інтерфейс кешує обидва токени в межах сесії та оновлює їх перед закінченням терміну.

---

## Завдання завантаження

Завантаження файлів принтера або відео друку — це завдання: воно створюється один раз, готується на диску сервера, опитується, а потім забирається. Старіші `GET /printers/{id}/files/download` і `POST /printers/{id}/files/download-zip` і далі відповідають файлом за один запит; вони так само готуються на диску, мають ті самі межі, а ZIP-варіант повідомляє про пропущені файли в заголовку `X-Download-Failed`.

| Endpoint | Що робить |
|----------|-----------|
| `POST /printers/{id}/files/download-jobs` | Почати завдання. Тіло: `paths` (1–1000 абсолютних шляхів файлів), необов'язкові `storage`, `sizes` (шлях → байти, як у переліку), `as_zip`, `filename`. Відповідає `202` із завданням. Кілька файлів — завжди один ZIP. |
| `GET /printers/{id}/files/download-jobs` | Власні завдання запитувача для цього принтера. |
| `GET /printers/{id}/files/download-jobs/{job_id}` | Завдання: `phase`, лічильники, отримані байти, `failures`, `error`. |
| `DELETE /printers/{id}/files/download-jobs/{job_id}` | Скасувати завдання, що готується, або відкинути готове. Скасоване завдання має `cancelling`, доки передавання справді не зупиниться, потім `cancelled`. |
| `GET /printers/{id}/files/download-jobs/{job_id}/artifact` | Готовий файл для клієнта, що надсилає заголовки (API-ключ). Додайте `?accept_partial=true`, щоб забрати частковий результат. |
| `POST /printers/{id}/files/download-jobs/{job_id}/download-token` | Лише для сесій браузера: одноразова адреса, з якої браузер зберігає файл. API-ключ отримує відмову (`403`) і користується `/artifact`. |
| `GET /archives/{id}/media-sources` | Що можна завантажити для друку: `local`, `timelapse` і `camera`, кожен зі своїм `status`. Необов'язкові `offset_minutes` (на скільки годинник принтера випереджає UTC) і `margin_minutes`. |
| `POST /archives/{id}/media-download-jobs` | Почати завдання для архіву: `assets` (ідентифікатори з `local`) та/або `remote` (`printer_id`, `storage`, `path`, необов'язковий `size` — лише принтер самого архіву). Решта endpoint-ів завдання повторює принтерні під `/archives/{id}/media-download-jobs/…`. |

`phase` — одне з `queued`, `preparing`, `cancelling`, `ready`, `failed`, `cancelled`, `expired`. Завдання з помилкою має код `error`: `authority_lost`, `limit_exceeded`, `insufficient_storage`, `time_limit`, `nothing_downloaded`, `interrupted`, `cleanup_incomplete` або `internal`. Завдання `ready` з `partial: true` містить лише файли, які вдалося прочитати; решту названо у `failures`.

Завдання належить обліковим даним, що його створили, — саме тій сесії браузера або саме тому API-ключу: завдання іншого користувача, завдання іншої сесії того самого облікового запису, іншого ключа й неіснуюче — це той самий `404`. Завданням принтера потрібен `printers:files`; завданням архіву — право читати архів, а `printers:files` лише тоді, коли вони читають принтер. Кожен endpoint завдання знову питає те, з чим завдання створено: щойно запитувач цього більше не має, стан завдання, скасування, токен завантаження і файл відповідають `403`, а завдання зникає з переліку. Коли сервер у цю мить не може перевірити ці права, endpoint-и завдання й перелік відповідають `503` із `Retry-After` — завдання нікуди не зникло, запитайте ще раз. Завдання, чий принтер або архів відтоді видалено — а його номер зайняв інший, — відповідає `404` (`401` на `/artifact`). `/artifact` бере облікові дані лише із заголовків запиту й відмовляє запиту, який несе ще й `?token=` (`400`). Відмови під час створення мають код у `detail.error`: `download_queue_full` і `download_user_limit` (`429`, з `Retry-After`), `insufficient_storage` (`507`), `limit_exceeded` і `too_many_files` (`413`), `downloads_unavailable` (`503`, під час відновлення).

Готовий файл завжди надсилається цілим — `200` з `Accept-Ranges: none`; заголовок `Range` ігнорується. Завдання живуть у пам'яті: перезапуск їх забуває, а результат, який ніхто не забрав, видаляється за годину.

### Редагування таймлапсу

Редагування відео архіву виконується у фоні. Щоб розпочати, прочитати чи скасувати редагування, потрібен `archives:update_all`.

| Endpoint | Опис |
|---|---|
| `POST /archives/{id}/timelapse/process` | Розпочати редагування. Query: `trim_start`, `trim_end` (секунди), `speed` (0.25–4), `save_mode` (`new` — типове, зберігає оригінал — або `replace`), `audio_volume` (0–1), `mute` і `audio_name`, коли надсилається музика. **Музика — це саме тіло запиту** (`Content-Type: application/octet-stream`), щонайбільше 100 МБ; multipart-форми немає. Відповідає `202` із завданням. |
| `GET /archives/{id}/timelapse/edit-jobs` | Власні редагування цього архіву. |
| `GET /archives/{id}/timelapse/edit-jobs/{job_id}` | Одне редагування: `phase`, `progress` (0–1), `error`, `save_mode`, `result`. |
| `DELETE /archives/{id}/timelapse/edit-jobs/{job_id}` | Попросити редагування зупинитися. Воно має `cancelled` лише після того, як кодувальник завершився, і прийняте скасування нічого не зберігає. Коли результат уже зберігається, відповідь — `409 cancel_too_late`. |
| `GET /archives/{id}/timelapse/variants` | Відео, збережені поряд з оригіналом через `save_mode=new`. |
| `DELETE /archives/{id}/timelapse/variants/{asset}` | Прибрати одне з них (право видаляти архів). |

`phase` — одне з `queued`, `encoding`, `publishing`, `cancelling`, `done`, `failed`, `cancelled`. `progress` дорівнює `1` лише в `done`, тобто після збереження результату. Невдале редагування має код `error`: `source_changed` (відео архіву тим часом замінили або прибрали — нічого не збережено), `target_gone`, `authority_lost`, `interrupted` (відновлення або перезапуск), `encode_failed`, `encode_timeout`, `encode_stalled`, `output_invalid`, `process_unreaped`, `publish_failed`, `cleanup_failed`.

Відмови на старті: `415 legacy_request` (multipart- або URL-encoded-форма — запит старого зразка), `409 edit_in_progress` (це відео вже редагують), `409 source_changed` (відео змінилося, поки запускалося редагування), `429 edits_busy`, `400 edit_invalid` / `audio_invalid`, `413 audio_too_large`, `422 video_unreadable`, `503 restoring` / `ffmpeg_missing`. Редагування належить обліковим даним, які його створили; чуже редагування й неіснуюче — це той самий `404`. Редагування живуть у пам'яті: перезапуск їх забуває і прибирає залишене ними на диску.

!!! warning "Змінений запит"
    `POST /archives/{id}/timelapse/process` раніше приймав multipart-форму й відповідав, коли ffmpeg завершувався. Тепер він приймає наведені вище query-параметри, одразу відповідає `202`, а результат читається із завдання. Форма відхиляється з `415 legacy_request` — як новий запит вона не читається ніколи.

## :material-bell-ring: Webhook-и та події в реальному часі

BamDude **не** надає вихідних webhook-ів для подій застосунку. Використовуйте [провайдер сповіщень](../features/notifications.md) (Telegram, Discord, ntfy, Pushover, Email, Home Assistant), коли потрібен односторонній push.

Канал реального часу — це WebSocket за адресою `wss://<host>/api/v1/ws`. Він несе:

- оновлення статусу принтерів (температури, прогрес, стан AMS)
- прогрес dispatch-у та черги
- події створення / оновлення архівів
- стан розумних розеток та тики споживання енергії

!!! warning "WebSocket наразі неавтентифікований"
    `/api/v1/ws` стоїть у public-route allowlist auth-middleware (`backend/app/main.py::PUBLIC_API_ROUTES`), і обробник не перевіряє токен. Будь-хто з мережевим доступом до WebSocket-порту може підписатися на realtime-події. Тримайте realtime-канал як **read-only intra-network** — поставте reverse proxy (див. [Reverse Proxy & HTTPS](../getting-started/reverse-proxy.uk.md)) і не виставляйте `/ws` напряму в публічний інтернет. Тайтенінг цього в roadmap; не сподівайтесь, що `Authorization: Bearer` сьогодні блокує subscribers.

### Вхідні ендпоінти для автоматизацій

Група `/webhook/*` — це протилежний напрямок: ендпоінти, які **ваша** автоматизація викликає сама, з автентифікацією по API-ключу. Це ті п'ять, що перелічені в **Налаштування → API-ключі**.

| Ендпоінт | Потрібне право | Що робить |
|---|---|---|
| `GET /api/v1/webhook/queue` | `can_read_status` | Стан черги всіх принтерів або одного через `?printer_id=` |
| `GET /api/v1/webhook/printer/{id}/status` | `can_read_status` | Зв'язок, стан, поточний друк, прогрес, час до кінця |
| `POST /api/v1/webhook/printer/{id}/start` | `can_control_printer` | Запустити **наступний у черзі** друк на цьому принтері |
| `POST /api/v1/webhook/printer/{id}/stop` | `can_control_printer` | Зупинити поточний **або призупинений** друк |
| `POST /api/v1/webhook/printer/{id}/cancel` | `can_control_printer` | Скасувати поточний **або призупинений** друк |

Ключ, обмежений конкретними принтерами (`printer_ids`), отримує **403** на будь-якому іншому. Непід'єднаний принтер відповідає **503**, а не помилкою — це стан, який варто повторити пізніше. `start` віддає **404**, коли в черзі немає завдання, якому вже час (заплановане на пізніше — не наступне), і **409**, коли принтер зайнятий, його чергу призупинено, стіл не підтверджено як прибраний або завдання відхилено — тоді відповідь каже чому. Лише **200** означає, що друк розпочато. `stop` і `cancel` віддають **409**, коли немає ні поточного, ні призупиненого друку.

Друк, завершений через `stop` чи `cancel`, записується як зупинений людиною — так само, як зупинка з картки принтера: він закінчується як скасований, а не як невдалий. Сповіщення про невдалий друк не надсилається, черга принтера стає на паузу, а не в помилку, а власник завдання отримує лист про зупинку.

```bash
curl -H "X-API-Key: $KEY" https://<host>/api/v1/webhook/printer/3/status
curl -X POST -H "X-API-Key: $KEY" https://<host>/api/v1/webhook/printer/3/start
```

!!! note "Ендпоінта для постановки в чергу тут немає"
    Черга йде через `POST /api/v1/queue/` з `archive_id`, `library_file_id` або `source_queue_item_id` читабельного наявного елемента черги, коли копіюється збережене завдання. У webhook-групі власного варіанта немає: рядок черги, зібраний вручну, оминав би перевірку призупиненої черги, гейт сумісності моделі принтера та лічильники черги. Один вхід — у цьому й суть.


---

## :material-script-text-play: Поширені операції — швидкі рецепти

### Список останніх 50 архівів принтера

```bash
curl -H "X-API-Key: bd_..." \
  "https://bamdude.example.com/api/v1/archives/?printer_id=2&page=1&per_page=50"
```

### Додати файл бібліотеки в чергу (3 копії, фіксований мапінг AMS)

```bash
curl -X POST \
  -H "X-API-Key: bd_..." \
  -H "Content-Type: application/json" \
  -d '{
    "library_file_id": 42,
    "queue_id": 2,
    "ams_mapping": [0, 1, 2, 3],
    "quantity": 3
  }' \
  "https://bamdude.example.com/api/v1/queue/"
```

### Отримати поточний статус принтера

```bash
curl -H "X-API-Key: bd_..." \
  "https://bamdude.example.com/api/v1/printers/2/status"
```

### Прочитати те саме для кількох принтерів одразу

Сторінка з багатьма принтерами питає один раз, а не по разу на принтер. Кожен маршрут приймає повторюваний `ids` (до 100) і відповідає об'єктом з ключами — id принтерів, а значення такі самі, як відповідає маршрут одного принтера. Принтер поза списком принтерів ключа пропускається.

```bash
curl -H "X-API-Key: bd_..." \
  "https://bamdude.example.com/api/v1/printers/status/batch?ids=1&ids=2&ids=3"
```

| Маршрут | На принтер |
|---|---|
| `GET /printers/status/batch` | Живий статус |
| `GET /printers/ams-labels/batch` | Мітки AMS за id AMS |
| `GET /archives/last-by-printer` | Найновіший архів (`id`, `print_name`, `filename`, `status`, `completed_at`); принтер без архіву пропускається |
| `GET /smart-plugs/by-printer/batch` | `main` — розетка, яку картка показує як живлення принтера, — і `scripts` |
| `GET /ha-sensors/readings/batch` | Показники сенсорів Home Assistant, видимих на картці |
| `GET /firmware/updates/batch` | Автоматична перевірка прошивки |

### Пропустити окремі об'єкти посеред друку

Тіло запиту — JSON-масив ID об'єктів, що їх повідомив slicer.

```bash
curl -X POST \
  -H "X-API-Key: bd_..." \
  -H "Content-Type: application/json" \
  -d '[100, 200]' \
  "https://bamdude.example.com/api/v1/printers/2/print/skip-objects"
```

### Відновити втрачений 3MF для архіву

Коли `on_print_start` не зміг забрати 3MF через FTP (принтер недосяжний, FTP-таймаут), рядок архіву створюється з `extra_data.no_3mf_available = true`. Фонові обходи повторюють спробу автоматично; ви також можете запустити це вручну:

```bash
curl -X POST \
  -H "X-API-Key: bd_..." \
  "https://bamdude.example.com/api/v1/archives/123/retry-download"
```

### Запустити очищення 3MF архівів (попередній перегляд, потім запуск)

Завдання очищення видаляє бінарники 3MF для архівів, старших за вікно зберігання (рядок з метаданими залишається). Денний cron виконується автоматично; для разового обходу:

```bash
# Dry-run preview — what would be deleted, total bytes
curl -H "X-API-Key: bd_..." \
  "https://bamdude.example.com/api/v1/archives/cleanup/preview"

# Run it
curl -X POST -H "X-API-Key: bd_..." \
  "https://bamdude.example.com/api/v1/archives/cleanup/run"

# Inspect the daily cron's last run + next run
curl -H "X-API-Key: bd_..." \
  "https://bamdude.example.com/api/v1/archives/cleanup/status"
```

### Оновити JWT-сесію зі свого клієнта

```bash
# /auth/refresh reads the HttpOnly bamdude_refresh cookie set during login.
# --cookie-jar / --cookie persists it across calls.
curl -c cookies.txt -X POST \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "..."}' \
  https://bamdude.example.com/api/v1/auth/login

curl -b cookies.txt -c cookies.txt -X POST \
  https://bamdude.example.com/api/v1/auth/refresh
```

Відповідь refresh повертає новий access-токен і ротує refresh-cookie на місці. Повторне використання вже використаного refresh-токена анулює всю сім'ю токенів на всіх пристроях (детекція повторного використання за OWASP).

---

## :material-code-json: Версіонування та стабільність

- Версійний префікс API — `/api/v1`. Зміни, що ламають сумісність, поставлятимуться під `/api/v2`, а не мутацією v1.
- Адитивні зміни (нові endpoint-и, нові опціональні поля) приходять у patch- / minor-релізах без попередження. Якщо ви залежите від стабільності форми відповіді, фіксуйте версію контейнера BamDude.
- У тілі `PATCH` / `PUT` пропущене поле не змінюється. `null` очищає поле, яке може бути порожнім; для поля, яке порожнім бути не може, `null` вважається пропущеним.
- Депрекації оголошуються в [changelog](https://github.com/kainpl/bamdude/blob/main/CHANGELOG.md) щонайменше за один minor-реліз до видалення.

> Початково базується на [Bambuddy](https://github.com/maziggy/bambuddy).
