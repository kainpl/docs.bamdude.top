---
title: Імпорт з MakerWorld
description: Встав посилання на модель MakerWorld → BamDude качає 3MF прямо в бібліотеку, з дедупом і провенансом
---

# Імпорт з MakerWorld

Встав посилання на модель з [MakerWorld](https://makerworld.com/), обери плиту — і 3MF опиняється у твоїй локальній бібліотеці. Без слайсера-проксі, без ручного завантаження. Кожен імпорт зберігає лінк-провенанс на оригінальну сторінку, щоб ти міг повернутись по рейтинги, рекомендовані пластики чи альтернативні плити.

Інтеграція **paste-driven**, не search-driven: публічний `design/search` повертає порожні результати з server-side запитів, тож дублювати каталог MakerWorld усередині BamDude нереально. Реальний шлях, як юзери знаходять моделі — Reddit, YouTube, чати — лягає на paste-flow без цієї обмеженості.

---

## :material-cloud-download: Як це працює

```
Встав MakerWorld URL ─→ /resolve  ─→  список плит
        │
        └→ Натисни Import ─→ /import ─→ 3MF у бібліотеці
```

| Крок | Що відбувається |
|------|-----------------|
| 1. Встав URL | Приймає будь-яку форму — `/en/models/123-slug?from=search`, `/de/models/123#profileId-456`, без схеми. Локаль і трекери в querystring видаляються; фрагмент `#profileId-N` (якщо є) обирає конкретну плиту. |
| 2. Resolve | Анонімні запити до `api.bambulab.com/v1/design-service/design/{N}` і `…/instances` тягнуть метадані дизайну + усі плити. На кожну плиту мерджиться інформація про сумісність принтерів (sliced for A1, marked compatible with H2D / P1S / …) — щоб у пікері можна було підсвітити плиту під твоє залізо. |
| 3. Обери плиту | Resolve-відповідь маркує плити, які вже є у твоїй бібліотеці, бейджем **Already imported** — не платиш за повторне завантаження. |
| 4. Import | BamDude отримує підписаний CDN-URL через `iot-service` Bambu Cloud, качає 3MF плити (з cap'ом розміру + SSRF-захистом), кладе у автоматично створену папку **MakerWorld** і ставить рядку `source_type='makerworld'` + canonical URL. |

---

## :material-key: Авторизація

BamDude перевикористовує вже збережений вхід у **Bambu Cloud** для скачування — окремого OAuth-флоу немає.

- **Анонімні дзвінки** (парсинг URL, метадані, перелік плит) працюють без токена.
- **Скачування** (`/iot-service/api/user/profile/{profileId}`) потребує твій збережений Bambu Cloud bearer.

Якщо токена нема — **Settings → MakerWorld → Status** показує `can_download = false` і кнопка Import disabled. Зайди в **Settings → Bambu Cloud** і авторизуйся спершу.

---

## :material-shield-key: Дозволи

| Permission | Що дозволяє |
|------------|--------------|
| `makerworld:view` | Заходити на сторінку MakerWorld, парсити URL, бачити метадані, бачити Recent imports. |
| `makerworld:import` | Власне тригерити завантаження в бібліотеку. |

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
| **Delete** | Кнопка trash на вже імпортованих рядах — проходить через стандартний confirm modal BamDude, видаляє і рядок у бібліотеці, і файл на диску. Плиту можна реімпортувати з MakerWorld будь-коли. |
| **View in File Manager** | Стрибок до рядка бібліотеки для імпортованої плити. |

### :material-import: Import all plates

Для multi-plate моделей кнопка **Import all** послідовно тягне кожну плиту моделі в один клік. Кнопка показує live-progress у форматі:

```
Importing 2/5 · Downloading · 12s
```

Плити, вже наявні в бібліотеці, скіпаються (без redundant download); лічильник усе одно рухається, щоб ти бачив прогрес проти повного набору.

---

## :material-history: Recent imports

Сторінка **MakerWorld** показує бічну панель з останніми 10 імпортами (newest first), фільтр `source_type='makerworld'`. Корисно для швидкого реприну того, що ти імпортував учора, без повторного встромляння URL.

---

## :material-camera-image: Мініатюри і CSP

CDN-картинки MakerWorld не можна hot-link'ати з браузера — суворий BamDude'івський CSP `img-src 'self' data: blob:` блокує крос-оріджинні зображення. Для обходу BamDude піднімає **неавторизований** thumbnail-проксі на `/api/v1/makerworld/thumbnail?url=...`, який:

- Server-side тягне картинку,
- Обмежує upstream-host MakerWorld'івським allowlist'ом (`makerworld.bblmw.com`, `public-cdn.bblmw.com`) — це не generic open-proxy,
- Повертає байти з довгим `immutable` cache (filename'и hash-вмістимі).

Endpoint вайтлістнутий в auth-gate бо `<img>` не вміє слати `Authorization`.

---

## :material-alert-circle-outline: Обмеження

!!! warning "MakerWorld 418 — application-level CAPTCHA"
    MakerWorld інколи кидає виклик твоїй IP CAPTCHA-ою (`HTTP 418` з `{"captchaId":...}`). Це **application-рівень**, не Cloudflare-edge — server-side розв'язку немає, бо CAPTCHA принципово не розв'язується без браузера. BamDude робить один retry з коротким backoff'ом, потім кидає upstream-повідомлення verbatim. Чекай 1–4 години тиші, або тисни **Open on MakerWorld** і качай вручну через браузер.

- **Без search/browse UI.** Публічний `design/search` повертає порожнє з server-side, тож BamDude не намагається мірорити каталог. Workflow paste-driven — це навмисно.
- **Без обробки ціни/балів.** Плити, замкнуті paywall'ом / регіоном / балами, повертають `HTTP 403` з повідомленням MakerWorld'у — воно показується дослівно в toast.
- **3MF size cap: 200 МБ.** Більше — fail з ясною помилкою.

!!! warning "Bambu Cloud токен живе ~90 днів"
    Bambu Cloud bearer-и експайряться приблизно через 90 днів. Якщо MakerWorld-імпорти раптом починають падати з `401` / "Please log in to download models" після місяців роботи — вийди і знов авторизуйся в Bambu Cloud під **Settings → Bambu Cloud**, щоб освіжити токен. Fetch K-профілів і firmware-чек теж зламаються — re-auth лагодить усі три одночасно.

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

**Settings → MakerWorld** містить:

- **Status** — `has_cloud_token` / `can_download`. Read-only.
- **Default folder** — за замовчуванням auto-created top-level `MakerWorld`. Можна перевизначити через folder-picker на кнопці Import.

Інших тумблерів нема — облік повноваження живе в **Settings → Bambu Cloud**, allowlist хостів проксі hard-coded задля безпеки.

---

## :material-file-code: Розробницький референс

### Ендпоінти

| Ендпоінт | Метод | Auth | Призначення |
|---|---|---|---|
| `/api/v1/makerworld/status` | GET | `makerworld:view` | Звітує наявність Bambu Cloud токена + регіональний host. |
| `/api/v1/makerworld/resolve` | POST | `makerworld:view` | URL → дизайн + список плит + already-imported profile ID-и. |
| `/api/v1/makerworld/import` | POST | `makerworld:import` | Завантажити конкретну плиту (`profile_id`) у бібліотеку. |
| `/api/v1/makerworld/recent-imports` | GET | `makerworld:view` | Останні N MakerWorld library-файлів (default 10, clamp `[1, 50]`). |
| `/api/v1/makerworld/thumbnail` | GET | публічний (whitelisted) | Проксі MakerWorld / public-cdn для рендеру `<img>` — host-allowlisted, без редиректів. |

### Upstream flow

Реверс-інженерений 3-кроковий flow проти `api.bambulab.com` (не задокументовано Bambu; розкопано через Pr0zak/YASTL#51):

1. `GET https://api.bambulab.com/v1/design-service/design/{designId}` — публічні метадані. Повертає `{id, modelId, title, coverUrl, instances[], …}`. Поле `modelId` — алфавітно-цифровий ідентифікатор (наприклад, `US2bb73b106683e5`) — **відрізняється** від integer `designId` з URL.
2. `GET https://api.bambulab.com/v1/iot-service/api/user/profile/{profileId}?model_id={modelId}` з `Authorization: Bearer {cloud_token}`. Повертає `{url, name}`, де `url` — presigned S3 URL з 5-хвилинним TTL (`s3.<region>.amazonaws.com/...?at=…&exp=…&key=…`).
3. Тягнути presigned-URL **без слідування редиректам** і **без re-encoding query-стрінга** — S3-підписи рахуються над точними байтами query, тож будь-який нормалізуючий HTTP-клієнт (httpx default, requests, aiohttp без `raw_path`) зламає їх з `SignatureDoesNotMatch`. BamDude використовує `urllib.request` з no-op `HTTPRedirectHandler` для цього кроку.

Старіший шлях `makerworld.com/api/v1/design-service/instance/{id}/f3mf`, який документують деякі reverse-engineering-проєкти, cookie-gated на Cloudflare і повертає "Please log in to download models" незалежно від bearer. Шлях `api.bambulab.com` через цей gate не йде.

### Код

- `backend/app/services/makerworld.py` — API-клієнт + download-логіка + thumbnail-proxy helper-и.
- `backend/app/api/routes/makerworld.py` — FastAPI-роути.
- `backend/app/schemas/makerworld.py` — Pydantic request/response моделі.
- `frontend/src/components/MakerWorldImportModal.tsx` + `frontend/src/pages/MakerworldPage.tsx` — UI: paste, preview, plate list, image gallery, recent imports sidebar, confirm modal, in-flight progress.

---

## :material-link-variant: Дивись також

- [File Manager](file-manager.md) — куди MakerWorld-імпорти потрапляють. Колонка з provenance-бейджем описана там.
- [Slicer API](slicer-api.md) — поєднай MakerWorld-імпорти зі server-side слайсингом, якщо плита не пресляйснута під твою модель.
- [Bambu Cloud setup](authentication.md) — потрібно зробити перед першим імпортом.
