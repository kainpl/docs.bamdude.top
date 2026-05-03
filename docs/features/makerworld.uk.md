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

---

## :material-cog-outline: Налаштування

**Settings → MakerWorld** містить:

- **Status** — `has_cloud_token` / `can_download`. Read-only.
- **Default folder** — за замовчуванням auto-created top-level `MakerWorld`. Можна перевизначити через folder-picker на кнопці Import.

Інших тумблерів нема — облік повноваження живе в **Settings → Bambu Cloud**, allowlist хостів проксі hard-coded задля безпеки.

---

## :material-link-variant: Дивись також

- [File Manager](file-manager.md) — куди MakerWorld-імпорти потрапляють. Колонка з provenance-бейджем описана там.
- [Slicer API](slicer-api.md) — поєднай MakerWorld-імпорти зі server-side слайсингом, якщо плита не пресляйснута під твою модель.
- [Bambu Cloud setup](authentication.md) — потрібно зробити перед першим імпортом.
