---
title: Імпорт з MakerWorld
description: Встав посилання на модель MakerWorld → BamDude качає 3MF прямо в бібліотеку, з дедупом і провенансом
---

# Імпорт з MakerWorld

Встав посилання на модель з [MakerWorld](https://makerworld.com/), обери плиту — і 3MF опиняється у твоїй локальній бібліотеці. Без слайсера-проксі, без ручного завантаження. Кожен імпорт зберігає лінк-провенанс на оригінальну сторінку, повні метадані дизайну (назва, автор, ліцензія, sliced-for-принтер, список сумісності, матеріали) та локально-кешовану обкладинку — UI ніколи не hot-link'ає CDN MakerWorld повторно.

Інтеграція **paste-driven**, не search-driven: публічний `design/search` повертає порожні результати з server-side запитів, тож дублювати каталог MakerWorld усередині BamDude нереально. Реальний шлях, як юзери знаходять моделі — Reddit, YouTube, чати — лягає на paste-flow без цієї обмеженості.

Сторінка MakerWorld розділена на дві underline-style вкладки:

- **Import** — встав URL, розв'яжи дизайн, переглянь усі плити з бейджем сумісності та per-variant статусом імпорту, тисни Import на ту (чи всі), яка потрібна.
- **History** — server-paginated 4-колоночна сітка всього, що ти вже імпортував — пошук по filename / title / author, сортування по даті / назві / автору, локально-кешовані обкладинки.

Активна вкладка зберігається в `localStorage`.

---

## :material-cloud-download: Як це працює

```
Встав MakerWorld URL ─→ /resolve  ─→  список плит
        │
        └→ Натисни Import ─→ /import ─→ 3MF у бібліотеці
```

| Крок | Що відбувається |
|------|-----------------|
| 1. Встав URL | Приймає будь-яку форму — `/en/models/123-slug?from=search`, `/de/models/123#profileId-456`, без схеми. Локаль і трекери в querystring видаляються; фрагмент `#profileId-N` (якщо є) обирає конкретну плиту. Inline-кнопка **Clear** (×) з'являється всередині URL-поля справа, як тільки в полі є текст або resolved-прев'ю — один клік знімає URL, resolved-модель і per-variant cache імпортів. |
| 2. Resolve | Анонімні запити до `api.bambulab.com/v1/design-service/design/{N}` і `…/instances` тягнуть метадані дизайну + усі плити. На кожну плиту мерджиться інформація про сумісність принтерів (sliced for A1, marked compatible with H2D / P1S / …) — щоб у пікері можна було підсвітити плиту під твоє залізо. |
| 3. Обери плиту | Resolve-відповідь містить **per-variant** dedupe-мапу (`already_imported_by_profile_id`) — для кожної плити, яка вже є в бібліотеці, виставляється бейдж **Already imported** + deep-link **View in Library** на точний рядок. Не платиш за повторне завантаження і можеш стрибнути одразу до існуючого файлу. Legacy whole-model дедуп (URL без `#profileId-`) лягає в конвенційний `"0"` bucket. |
| 4. Import | BamDude отримує підписаний CDN-URL через `iot-service` Bambu Cloud, качає 3MF плити (з cap'ом розміру + SSRF-захистом), кладе у автоматично створену папку **MakerWorld**, тягне локально model-level + variant-level обкладинки, записує повні метадані дизайну + інстансу в дочірню таблицю `library_file_makerworld_meta` і ставить рядку `source_type='makerworld'` + canonical URL. |

---

## :material-key: Авторизація

BamDude перевикористовує вже збережений вхід у **Bambu Cloud** для скачування — окремого OAuth-флоу немає.

- **Анонімні дзвінки** (парсинг URL, метадані, перелік плит) працюють без токена.
- **Скачування** (`/iot-service/api/user/profile/{profileId}`) потребує твій збережений Bambu Cloud bearer.

Якщо токена нема — сторінка MakerWorld показує банер **Для завантаження потрібен Bambu Cloud**, а кнопки Import і Print вимкнені. Спершу увійди в Bambu Cloud на сторінці **Профілі**.

Якщо токен збережено, але Bambu більше його не приймає, банер каже **Вхід у Bambu Cloud протермінувався**, і кнопки лишаються вимкненими, доки не увійдеш знову. Завантаження, відхилене з цієї причини, відповідає *Вхід у Bambu Cloud протермінувався. Відкрийте сторінку «Профілі» й увійдіть у Bambu Cloud знову.* Одна випадкова відповідь `401` не виписує тебе: мертвим токен позначає лише власна відповідь Bambu про протермінування.

!!! note "API-ключі використовують токен власника ключа"
    Запити, автентифіковані **API-ключем** (`X-API-Key` / `Bearer bd_…`) зі scope доступу до хмари, тепер резолвлять збережений Bambu Cloud токен **власника ключа**, тож `has_cloud_token` / `can_download` відображають того користувача, а не завжди повертають `false`. Імпорти з розширення й Home Assistant, які раніше падали з "requires Bambu Cloud login", тепер проходять — доки власник ключа увійшов у Bambu Cloud.

---

## :material-shield-key: Дозволи

| Permission | Що дозволяє |
|------------|--------------|
| `makerworld:view` | Заходити на сторінку MakerWorld, парсити URL, бачити метадані, бачити вкладку History. |
| `makerworld:import` | Власне тригерити завантаження в бібліотеку. Те саме потрібно і для Re-download. |

Дефолтні групи: **Operators** отримують обидва, **Viewers** — тільки `makerworld:view`. Адміни — обидва.

---

## :material-folder-arrow-down: Куди файли потрапляють

| Поле | Значення |
|------|----------|
| **Папка** | Top-level папка `MakerWorld`, створюється автоматично на першому імпорті. Можна вручну переносити в підпапки — провенанс залишається. |
| **Filename** | Людськочитабельне ім'я з MakerWorld; на диску — UUID, тож можна вільно переменовувати. |
| **`source_type`** | `'makerworld'` — драйвить MakerWorld-бейдж у File Manager. |
| **`source_url`** | Канонічний `https://makerworld.com/models/{m}#profileId-{p}` — бейдж стає клікабельним лінком назад на сторінку. |
| **Дедуп per-plate** | Дві різні плити одного дизайну = два записи в бібліотеці (кожна плита качається окремо). Та сама плита, імпортована вдруге, повертає існуючий рядок без перекачування. |

---

## :material-cursor-default-click: Дії на плиту

Коли модель розв'язана, кожен ряд плити має свій набір дій:

| Дія | Що робить |
|-----|-----------|
| **Save** | Завантажує 3MF і кладе у бібліотеку. Ряд плити після цього отримує зелений бейдж "Already in library". |
| **Save & Slice in Bambu Studio** | Те саме, що Save, плюс відкриває збережений файл у Bambu Studio (якщо ти налаштував Slicer Integration). |
| **Save & Slice in OrcaSlicer** | Те саме, але в OrcaSlicer. Плити MakerWorld — це **unsliced source-файли**, тож слайсер — правильний наступний крок перед друком. |
| **Re-download** | З'являється на плитах, які вже в бібліотеці (замість Save). Перетягує 3MF з MakerWorld і **перезаписує існуючий файл на місці** в `library_files.file_path`. `library_file_id` стабільний — queue items, project links, archives та інші FK-зсилки далі резолвляться на той самий рядок. `file_size`, `file_hash`, `file_metadata`, рядок meta-таблиці (title / author / sliced-for / compatibility / …) і локальні обкладинки — усе оновлюється. Use case: автор пушнув update в MakerWorld, ти хочеш свіжі байти без втрати локальних лінків. |
| **Delete** | Кнопка trash на вже імпортованих рядах — проходить через стандартний confirm modal BamDude, видаляє і рядок у бібліотеці, і файл на диску. ON DELETE CASCADE забирає рядок meta-таблиці + файли обкладинок разом. Плиту можна реімпортувати з MakerWorld будь-коли. |
| **View in Library** | Стрибок до рядка бібліотеки для імпортованої плити. Показується і inline на resolve-прев'ю (з per-variant dedupe-мапи), і на кожній картці History. |

### :material-import: Import all plates

Для multi-plate моделей кнопка **Import all** послідовно тягне кожну плиту моделі в один клік. Кнопка показує live-progress у форматі:

```
Importing 2/5 · Downloading · 12s
```

Плити, вже наявні в бібліотеці, скіпаються (без redundant download); лічильник усе одно рухається, щоб ти бачив прогрес проти повного набору.

---

## :material-history: Вкладка History

**History** — це server-paginated 4-колоночна сітка (responsive до 1 колонки на вузьких viewport'ах) кожного MakerWorld-файлу, який ти коли-небудь імпортував. Кожна картка показує:

- **Обкладинка** — локально-кешована variant-обкладинка з fallback'ом на model-обкладинку і далі fallback'ом на звичайний library thumbnail. Жодного hot-link'у до CDN MakerWorld на рендері.
- **Title** — назва дизайну, зафіксована на момент імпорту.
- **Author** — ім'я + клік на профіль MakerWorld.
- **Sliced-for бейдж** — модель принтера, під яку нарізали варіант (A1 / P1S / X1C / H2D / …).
- **Кнопки дій** — Slice / Open in Bambu Studio / Open in OrcaSlicer / View in Library / Delete.

| Контрол | Поведінка |
|---|---|
| **Пошук** | Debounced (300 мс) одразу по `library_files.filename`, `meta.title` і `meta.author_name` — бекенд джоїнить `library_files` з `library_file_makerworld_meta`, тож один запит шукає по всіх трьох полях. |
| **Сортування** | `imported_at` (за замовчуванням newest first) / `title` / `author`. Зберігається в `localStorage`. |
| **Розмір сторінки** | `12 / 24 / 48 / 96 / Усі`. Той самий конвеншн, як на Archives; `Усі` дропає `LIMIT`/`OFFSET` на стороні SQL. Зберігається в `localStorage`. |
| **Оновлення** | Сітка авто-перетягує дані після `import` / `delete` / `redownload` через TanStack Query invalidation. |

Legacy `recent-imports` endpoint досі експозований для backwards-compat, але сама сторінка тепер тягне `/api/v1/makerworld/imports`.

---

## :material-database: Метадані, які записуються на імпорті

Кожен імпорт пише 1:1 дочірній рядок у `library_file_makerworld_meta` (`ON DELETE CASCADE` з `library_files`), фіксуючи повний source-of-truth, який видає resolve-відповідь:

| Поле | Що тримає |
|---|---|
| `title`, `description` | Назва дизайну і Markdown/HTML опис (санітайзиться DOMPurify-ом на рендері). |
| `author_name`, `author_url` | Display-ім'я користувача MakerWorld + canonical URL профілю. |
| `license` | Ліцензія, як її опубліковано на сторінці моделі (варіант Creative Commons, CC BY-SA тощо). |
| `variant_title`, `variant_description`, `variant_url` | Назва / опис / canonical `#profileId-N` URL конкретної плити. |
| `sliced_for` | Модель принтера, під яку нарізали варіант (наприклад, `"P1S"`). |
| `compatible_models` | Повний список сумісних принтерів — resolve UI використовує його, щоб підсвітити плиту під твоє залізо. |
| `requires_ams` | Чи вимагає варіант AMS. |
| `material_count`, `filaments` | Кількість слотів + per-slot матеріал/колір, як опубліковано. |
| `original_design_id` | Якщо дизайн — ремікс, integer-id батьківського дизайну. |
| `makerworld_model_id` | Алфавітно-цифровий model id (наприклад, `US2bb73b106683e5`) — потрібен, щоб переемітити download-URL для **Re-download**. |
| `raw_payload` | Об'єднаний design + instance JSON, збережений verbatim для майбутніх forensics — рутинний код його не читає. |

Міграція **m056** додає цю таблицю; вона також робить best-effort backfill для історичних імпортів (рядків у `library_files` зі `source_type='makerworld'` до m056). Per-row фейли backfill'у проковтуються (з логом), тож міграція в будь-якому разі завершується — пропущений рядок просто означає, що картка History показує bare filename, поки ти не переімпортуєш або не зробиш Re-download.

---

## :material-camera-image: Обкладинки

Обкладинки **завантажуються локально** на момент імпорту і обслуговуються BamDude, а не hot-link'аються з CDN MakerWorld. Дві штуки на рядок:

- **Model cover** — hero-картинка дизайну. Записується у `<data_dir>/library/makerworld-covers/<library_file_id>-cover.<ext>`.
- **Variant cover** — картинка plate-рівня (якщо MakerWorld публікує її окремо). Записується у `<data_dir>/library/makerworld-covers/<library_file_id>-variant.<ext>`.

Картки History спершу беруть variant-обкладинку, потім model-обкладинку, потім fallback на звичайний thumbnail library-файлу. Endpoint'и:

```
GET /api/v1/makerworld/imports/{library_file_id}/cover
GET /api/v1/makerworld/imports/{library_file_id}/cover-variant
```

Обидва — **публічні (whitelisted)**, а не permission-gated, бо `<img src>` браузера не вміє слати `Authorization`. Кожен роут має в whitelist'і auth-middleware свій власний заякорений запис. JSON-метадані endpoint `…/meta` тримає `makerworld:view` permission-gate, бо `fetch()` спокійно несе JWT.

Re-download оновлює обидва файли обкладинок поряд з 3MF-байтами. Delete library-файлу CASCADE-дропає рядок meta-таблиці, файли обкладинок розв'язуються з диску.

---

## :material-cloud-outline: Legacy thumbnail-проксі

Для мініатюр на вкладці **Import** (resolve-прев'ю показує hosted-галерею MakerWorld до того, як ти натиснеш Import) BamDude досі піднімає **неавторизований** thumbnail-проксі на `/api/v1/makerworld/thumbnail?url=...`, який:

- Server-side тягне картинку,
- Обмежує upstream-host MakerWorld'івським allowlist'ом (`makerworld.bblmw.com`, `public-cdn.bblmw.com`) — це не generic open-proxy,
- Повертає байти з довгим `immutable` cache (filename'и hash-вмістимі).

Endpoint вайтлістнутий в auth-gate бо `<img>` не вміє слати `Authorization`. Як тільки ти натискаєш Import, BamDude тягне свою копію обкладинки і вже ніколи цю саму картинку через проксі не несе.

---

## :material-alert-circle-outline: Обмеження

!!! note "Presigned-завантаження з S3 довіряє тим самим сертифікатам, що й решта"
    MakerWorld часто віддає 3MF як посилання Amazon S3. BamDude перевіряє це завантаження тим самим набором сертифікатів, що й усі інші з'єднання, а не сховищем операційної системи — на Windows системне сховище наповнюється ліниво, і імпорт падав з `unable to get local issuer certificate` на машині, яка ще не зустрічала цей корінь Amazon. За проксі з TLS-інспекцією вкажи його CA у `SSL_CERT_FILE` (або `SSL_CERT_DIR`): кожне з'єднання, і це теж, його враховує.

!!! warning "MakerWorld 418 — application-level CAPTCHA"
    MakerWorld інколи кидає виклик твоїй IP CAPTCHA-ою (`HTTP 418` з `{"captchaId":...}`). Це **application-рівень**, не Cloudflare-edge — server-side розв'язку немає, бо CAPTCHA принципово не розв'язується без браузера. BamDude робить один retry з коротким backoff'ом, потім кидає upstream-повідомлення verbatim. Чекай 1–4 години тиші, або тисни **Open on MakerWorld** і качай вручну через браузер.

- **Без search/browse UI.** Публічний `design/search` повертає порожнє з server-side, тож BamDude не намагається мірорити каталог. Workflow paste-driven — це навмисно.
- **Без обробки ціни/балів.** Плити, замкнуті paywall'ом / регіоном / балами, повертають `HTTP 403` з повідомленням MakerWorld'у — воно показується дослівно в toast.
- **3MF size cap: 200 МБ.** Більше — fail з ясною помилкою.

!!! warning "Bambu Cloud токен живе ~90 днів"
    Bambu Cloud bearer-и експайряться приблизно через 90 днів. Тоді сторінка MakerWorld показує **Вхід у Bambu Cloud протермінувався** — вийди і знов увійди в Bambu Cloud на сторінці **Профілі**, щоб освіжити токен. Fetch K-профілів і firmware-чек теж зламаються — re-auth лагодить усі три одночасно.

---

## :material-shield-check: Приватність, безпека, compliance

- BamDude **не афілійований і не схвалений** MakerWorld або Bambu Lab.
- Інтеграція використовує лише community-задокументовані ендпоінти — `api.bambulab.com/v1/design-service/*` для метаданих і `api.bambulab.com/v1/iot-service/api/user/profile/{pid}` для download URL. Кредит **Pr0zak/YASTL#51** за публікацію форми iot-service ендпоінта, що робить flow можливим.
- Мініатюри і CDN-картинки проксяться через `/api/v1/makerworld/thumbnail`, тож IP юзера ніколи не зливається CDN MakerWorld'у при рендері. Проксі enforce-ить host-allowlist і **не** слідує редиректам.
- MakerWorld-описи (model summary, інструкції) санітайзяться **DOMPurify**'ом перед рендером — user-authored контент не може ін'єктити скрипти, event-handler'и чи `javascript:` URL-и.
- Bambu Cloud bearer надсилається **тільки** на `api.bambulab.com`; ніколи не пробрасується на CDN MakerWorld або S3-presigned-fetch.
- Імена файлів з MakerWorld-respons-ів санітайзяться через `os.path.basename` перед збереженням, тож зловмисний response не може засіяти path-traversal-рядки в UI. **На диску використовуються UUID-імена** незалежно від human-readable назви, що показується в бібліотеці.

---

## :material-cog-outline: Налаштування

Розділу MakerWorld у Settings нема:

- **Стан входу** — банер на сторінці MakerWorld, коли завантаження вимкнені (токена нема або він протермінувався); те саме повертає `GET /api/v1/makerworld/status`.
- **Default folder** — auto-created top-level `MakerWorld`. Можна перевизначити через folder-picker на кнопці Import.

Облікові дані живуть на сторінці **Профілі** (вхід у Bambu Cloud); allowlist хостів CDN зафіксовано задля безпеки.

---

## :material-file-code: Розробницький референс

### Ендпоінти

| Ендпоінт | Метод | Auth | Призначення |
|---|---|---|---|
| `/api/v1/makerworld/status` | GET | `makerworld:view` | `has_cloud_token`, `can_download` і `sign_in_expired` — збережений токен, який Bambu відхилив (`can_download` тоді `false`). |
| `/api/v1/makerworld/resolve` | POST | `makerworld:view` | URL → дизайн + список плит + плоский already-imported ID-список + per-variant dedupe-мапа (`already_imported_by_profile_id`). |
| `/api/v1/makerworld/import` | POST | `makerworld:import` | Завантажити конкретну плиту (`profile_id`) у бібліотеку. Записує рядок meta + обкладинки поряд з 3MF. Необов'язковий `source_type` називає постачальника моделей (типове і єдине зареєстроване значення — `makerworld`); невідомий — `400` ще до будь-якого запису. |
| `/api/v1/makerworld/imports` | GET | `makerworld:view` | Server-paginated сітка для вкладки History. Query-параметри: `page`, `per_page` (1–200, типово 24), `search` (ім'я файла, назва або автор з meta), `sort_by` (`date-desc` / `date-asc` / `name-asc` / `name-desc`). Повертає стандартний envelope `{data, meta:{total, current_page, per_page, last_page}}`. |
| `/api/v1/makerworld/imports/{id}/meta` | GET | `makerworld:view` | Зафіксований рядок meta-таблиці (title / author / license / sliced-for / compatibility / materials / raw_payload). |
| `/api/v1/makerworld/imports/{id}/cover` | GET | публічний (whitelisted) | Локально-кешована model-обкладинка. Whitelisted, бо `<img src>` не може слати auth-хедер. |
| `/api/v1/makerworld/imports/{id}/cover-variant` | GET | публічний (whitelisted) | Локально-кешована variant-обкладинка. У whitelist'і — свій заякорений запис, як і `/cover`. |
| `/api/v1/makerworld/imports/{id}/redownload` | POST | `makerworld:import` | Перетягнути 3MF-байти і перезаписати існуючий файл у `library_files.file_path`. `library_file_id` стабільний; оновлює `file_size` / `file_hash` / `file_metadata` / рядок meta / обкладинки. |
| `/api/v1/makerworld/recent-imports` | GET | `makerworld:view` | Legacy: останні N MakerWorld library-файлів (default 10, clamp `[1, 50]`). Замінений на `/imports` — тримається для backwards-compat. |
| `/api/v1/makerworld/thumbnail` | GET | публічний (whitelisted) | Проксі MakerWorld / public-cdn для рендеру `<img>` на прев'ю вкладки Import — host-allowlisted, без редиректів. Картки History натомість використовують локальні `/cover` endpoint'и. |

### Upstream flow

Реверс-інженерений 3-кроковий flow проти `api.bambulab.com` (не задокументовано Bambu; розкопано через Pr0zak/YASTL#51):

1. `GET https://api.bambulab.com/v1/design-service/design/{designId}` — публічні метадані. Повертає `{id, modelId, title, coverUrl, instances[], …}`. Поле `modelId` — алфавітно-цифровий ідентифікатор (наприклад, `US2bb73b106683e5`) — **відрізняється** від integer `designId` з URL.
2. `GET https://api.bambulab.com/v1/iot-service/api/user/profile/{profileId}?model_id={modelId}` з `Authorization: Bearer {cloud_token}`. Повертає `{url, name}`, де `url` — presigned S3 URL з 5-хвилинним TTL (`s3.<region>.amazonaws.com/...?at=…&exp=…&key=…`).
3. Тягнути presigned-URL **без слідування редиректам** і **без re-encoding query-стрінга** — S3-підписи рахуються над точними байтами query, тож будь-який нормалізуючий HTTP-клієнт (httpx default, requests, aiohttp без `raw_path`) зламає їх з `SignatureDoesNotMatch`. BamDude використовує `urllib.request` з no-op `HTTPRedirectHandler` для цього кроку, і явний TLS-контекст з набору `certifi` (інакше urllib бере сховище операційної системи).

Старіший шлях `makerworld.com/api/v1/design-service/instance/{id}/f3mf`, який документують деякі reverse-engineering-проєкти, cookie-gated на Cloudflare і повертає "Please log in to download models" незалежно від bearer. Шлях `api.bambulab.com` через цей gate не йде.

### Код

- `backend/app/services/model_providers/` — інтерфейс постачальника моделей (`base.py`) і реєстр (`registry.py`). Сайт моделей — це дескриптор `ModelProvider` плюс per-request `ProviderService`; роути вибирають постачальника через реєстр і ніколи не звертаються до сайту напряму. MakerWorld — перший постачальник.
- `backend/app/services/model_providers/makerworld/` — `provider.py` (дескриптор), `service.py` (API-клієнт, завантаження, thumbnail-проксі), `http.py` (константи, User-Agent, S3-завантаження), `url.py` (розбір URL + канонічний ключ дедупу), `errors.py`, `meta.py` (`build_meta_dict()` / `download_covers()` / `cleanup_cover_files()` — m056 meta-table writer + локальний cover-image fetcher).
- `backend/app/services/bambu_cloud_credentials.py` — де лежить збережений Bambu Cloud токен і чи Bambu його відхилив; спільне з cloud-роутами.
- `backend/app/models/library_file_makerworld_meta.py` — SQLAlchemy-модель дочірньої meta-таблиці (1:1 з `library_files`, `ON DELETE CASCADE`).
- `backend/app/migrations/m056_library_file_makerworld_meta.py` — schema-міграція + best-effort backfill історичних імпортів.
- `backend/app/api/routes/makerworld.py` — FastAPI-роути.
- `backend/app/schemas/makerworld.py` — Pydantic request/response моделі (`MakerWorldAlreadyImportedEntry`, `MakerWorldImportsPage`, …).
- `frontend/src/components/MakerWorldImportModal.tsx` + `frontend/src/pages/MakerworldPage.tsx` — UI: вкладки Import + History, поле-вставлення з inline Clear, preview, plate-list з per-variant dedupe-бейджами, галерея, paginated сітка, пошук, сортування, page-size селектор.

---

## :material-link-variant: Дивись також

- [File Manager](file-manager.md) — куди MakerWorld-імпорти потрапляють. Колонка з provenance-бейджем описана там.
- [Slicer API](slicer-api.md) — поєднай MakerWorld-імпорти зі server-side слайсингом, якщо плита не пресляйснута під твою модель.
- [Bambu Cloud setup](authentication.md) — потрібно зробити перед першим імпортом.
