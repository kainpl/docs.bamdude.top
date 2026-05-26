---
title: Firmware Updates
description: LAN-only оновлення прошивки Bambu Lab через SD карту — детект версій, завантаження, FTP upload, rollback, без Bambu Cloud
---

# Firmware Updates

BamDude може тримати твої Bambu Lab принтери оновленими без Bambu Cloud-акка. Флоу — **LAN-only**: BamDude тягне останню прошивку з офіційного Bambu CDN, кладе `.bin` на SD-карту принтера через FTP, а ти тригериш install з екрана принтера. Cloud-вхід не потрібен ні на якому кроці.

Те ж саме механізм підтримує **rollback** — обери будь-яку версію, яку Bambu колись публікувала, і BamDude її качне і staging-не так само.

---

## :material-update: Що покриває

- Per-printer **firmware status badge** на кожній printer-картці.
- Сповіщення "Update available" через стандартні канали (див. [Notifications](notifications.md)).
- LAN-only **download → SD upload → trigger from printer screen** флоу.
- **Масові (bulk) оновлення** багатьох принтерів за раз, згруповані по моделі, з **Журналом оновлень** на кожен запуск (див. [нижче](#mass-bulk-updates)).
- Rollback / reinstall до будь-якої **published** версії.
- Wiki-vs-download-page reconciliation — версії, які Bambu *оголосив*, але офлайн-файл не *опублікував*, маркуються як unavailable, а не вдають, що installable.
- **Cloudflare bypass**, щоб EU/UA install-и, які 403-яться на простому HTTP, могли говорити з `bambulab.com`.

Чого свідомо не робить: **Bambu Cloud firmware-update флоу** (`/api/v1/cloud/firmware-updates`) — окремий route, що потребує cloud auth і читає firmware availability через Cloud API. LAN-флоу для LAN-only принтерів; cloud-флоу — коли вже залогінений через [Cloud Profiles](cloud-profiles.md).

---

## :material-bell-badge: Status badge

Кожна printer-картка несе firmware-бейдж. Колір і іконка кажуть стан з першого погляду:

| Бейдж | Що означає |
|---|---|
| **Зелений / галочка** | Встановлена прошивка збігається з останньою опублікованою. Клік — release-notes. |
| **Помаранчевий / download** | Update опубліковано. Hover — `current → latest`. Клік — update modal. |
| **Жовтий / знак запитання** | Версія невідома — принтер offline, або ще не відправив свою прошивку через MQTT. |
| **Сірий** | Firmware checking вимкнено (див. [Disabling checks](#disabling-checks) нижче). |

Текст бейджа — **встановлена** версія (напр. `01.09.00.00`), тягнеться з MQTT-стану принтера — без FTP-pollу, без cloud round-trip-а, бейдж безкоштовний.

Бейдж гейтиться permission-ом `firmware:read`. Дефолтні групи дають його **Administrators** і **Operators**; **Viewers** не бачать.

### Disabling checks

**Settings → General → Updates → Check printer firmware.** Коли вимкнено:

- Жодного запиту до `bambulab.com` чи `wiki.bambulab.com`.
- Бейдж зникає з кожної printer-картки.
- Сповіщення про нову прошивку перестають фаєритись.

Корисно для offline-only deployment-ів, deployment-ів за strict outbound-firewall-ом, або коли просто хочеш керувати firmware вручну без помаранчевих крапок.

---

## :material-download: Update флоу

Однаковий для forward upgrades і rollback-ів — різниться тільки версія, яку обираєш.

```
Click badge → Update modal → Pick version → Prepare → Upload → Trigger from printer screen
```

### 1. Відкрий modal

Клік на бейдж. Рендеряться три секції:

| Секція | Що показує |
|---|---|
| **Current** | Встановлена версія з MQTT |
| **Latest / Selected** | Версія, яка піде на install після Upload — за замовчуванням найновіша published |
| **Available Versions** | Кожна версія, яку Bambu коли-небудь оголосив для цієї моделі |

### 2. Обери версію (опціонально)

Available Versions list несе два бейджа на рядок:

| Version-relation бейдж | Значення |
|---|---|
| `newer` | Вище за встановлене |
| `current` | Те, що зараз встановлено |
| `older` | Нижче за встановлене (rollback) |

| File-status бейдж | Значення |
|---|---|
| :material-check-circle: **Usable** (зелений) | Bambu опублікував offline `.bin`. Selectable, installable. |
| :material-cancel: **Unavailable** (сірий) | Bambu оголосив, але файл не опублікував. Типово для hot-fix point releases (`01.01.03.00` тощо) — лише cloud-OTA. Через LAN не встановити. |
| :material-information: **Installed** (синій) | Поточна на принтері. |

Клік по **Usable** рядку обирає його як install target — release-notes і `firmware_filename` оновлюються відповідно. **Unavailable** не обирається.

### 3. Prepare

Перед upload-ом BamDude робить prepare-check (`GET /firmware/updates/{printer_id}/prepare?version=...`):

| Перевірка | Source |
|---|---|
| **SD card present** | MQTT state (`state.sdcard`) |
| **Free space** | Live FTP `STAT` (реальні байти, не оцінка) |
| **Update available** | Wiki vs installed-version comparison |
| **Target version is publishable** | Download page lookup |

Минимальний free-space buffer — **100 MB** на додачу до розміру firmware. Типова Bambu firmware 50-150 MB; prepare-check estimates 100 MB і відмовляє, якщо на SD менше ~200 MB вільно.

### 4. Upload

`POST /firmware/updates/{printer_id}/upload?version=...` запускає background task, який:

1. Качає `.bin` з Bambu CDN (або переюзує локальне сховище — див. [Сховище](#firmware-store) нижче).
2. FTP-ить файл у **корінь** SD-карти. Filename відповідає Bambu published naming.
3. Бродкастить прогрес через WebSocket (`firmware_upload_progress`) і через polling-fallback endpoint (`GET /firmware/updates/{printer_id}/upload/status`).

Зазвичай 2-5 хвилин на ~300 MB по локальному Wi-Fi. Прогрес — реальні передані байти, не fake-анімація.

### 5. Тригерни на екрані принтера

BamDude не пушить install через MQTT — фінішуєш на принтері:

1. **Settings** → **Firmware** на екрані.
2. **Update from SD card**.
3. Чекай 10-20 хв. Не вимикай живлення поки не закінчиться.

!!! warning "Не вимикай живлення посеред update"
    Half-applied firmware може заб'ючити принтер. Підключи принтер до UPS на час, якщо живлення нестабільне.

---

## :material-layers-triple: Масові (bulk) оновлення {#mass-bulk-updates}

Оновлювати по одному принтеру на фермі — втомливо. Сторінка **Firmware** (сайдбар → :material-cpu-64-bit: **Прошивка**) оновлює багато принтерів за один прохід.

```
Сайдбар → Прошивка → обери версію для кожної моделі → Upgrade
```

- **Згруповано по моделі.** Принтери розкладені по табах моделей (`P1P/P1S (4)`, `A1 mini (2)`, …) — файл прошивки та крок застосування на екрані відрізняються per-model.
- **Одна версія на модель, в обидва боки.** Обери версію для кожної моделі — новішу **або** старішу (відкат — first-class). Список показує всі опубліковані версії плюс ті, що вже є у твоєму сховищі.
- **Завантаження раз, аплоад паралельно.** Прошивка кожної моделі качається **один раз**, потім FTP-иться на SD кожного обраного принтера паралельно, з лімітом **Settings → General → File Manager → bulk concurrency** (дефолт **2** — Bambu-контролери не люблять багато одночасних TLS-handshake-ів).
- **Принтери в друці пропускаються**, позначаються в рядку й не чіпаються. Помилка одного принтера **не зупиняє решту** — кожен отримує власний результат.
- **«Оновити всі доступні»** пресетить усі принтери з доступним апдейтом; версію per-model ти все одно підтверджуєш перед запуском.
- Як і в single-printer флоу, фінальне **застосування** — крок на екрані кожного принтера; запуск завершується показом модель-залежної інструкції для принтерів, на які залив.

### Журнал оновлень

Таб **Журнал оновлень** на сторінці Firmware записує кожен запуск — час, джерело (`bulk` / `single`), per-printer `from → to` та результат. **Single-printer оновлення з per-printer модалки теж пишуться сюди**, тож журнал — єдине місце, де видно всю firmware-активність ферми.

---

## :material-history: Rollback

Вибір старшої **Usable** версії вмикає install-кнопку для цього build-а. Завантажений `.bin` йде в SD root так само, як forward upgrade — принтер не дивиться напрямок руху версії; firmware loader на принтері приймає будь-яку signed Bambu firmware незалежно від version-comparison-у.

Це означає, що можна закріпити принтер на старшій firmware без hand-flash-у — корисно коли:

- Нова firmware ламає сумісність зі старими slicer 3MF-ами, від яких ти залежиш.
- Нова firmware ввела регресію з твоїм AMS / TPU воркфлоу.
- Хочеш A/B-тестнути зміну поведінки між двома версіями.

Rollback не гейтиться окремо — `firmware:update` покриває обидва напрямки.

---

## :material-shield-bug: Cloudflare bypass

`bambulab.com` сидить за Cloudflare з TLS-fingerprint фільтрацією. Простий `httpx` з EU/UA install-ів стабільно отримує **403 Forbidden**, бо JA3-fingerprint Python TLS handshake-у збігається з Cloudflare-правилом "automated traffic".

BamDude обходить це двома HTTP-клієнтами в `firmware_check.py`:

| Host | Клієнт | Чому |
|---|---|---|
| `wiki.bambulab.com` | `httpx` (plain) | Wiki *не* за тим самим блоком — version listing читається чисто |
| `bambulab.com` (Next.js download page + data endpoint) | `curl_cffi` з `impersonate="chrome120"` | Шле справжній Chrome TLS handshake → 200 OK |
| Bambu firmware CDN | `httpx` (plain) | CDN на іншому host-і без JA3-фільтра |

### buildId self-heal

Download page — Next.js app — кожен page render несе build-specific `buildId`, запечений у data-endpoint path-у (`/_next/data/<buildId>/...`). Cloudflare ротує цей `buildId` за своїм графіком, часто **всередині нашого 1-годинного cache TTL**.

Stale `buildId` повертає 403 (Cloudflare challenge) або 404 (path moved). BamDude детектить обидва і робить **один** retry, що:

1. Re-fetch-ить download-page через CF-impersonating клієнт.
2. Грепає свіжий `buildId` з HTML сторінки.
3. Replay-ить original data-endpoint дзвінок з новим path-ом.

Якщо retry теж фейлиться — рядок маркується unavailable для цього fetch-у і кеш не пишеться; наступна спроба стартує з нуля. User-visible ефект: UI не застрягає на "unavailable" на новому release-і просто тому, що Cloudflare ротував `buildId` 12 хв після останнього BamDude fetch-у.

---

## :material-format-letter-matches: Wiki anchor parsing

Версії детектяться зі сторінок "Firmware release history" Bambu Wiki (`wiki.bambulab.com/<model>/manual/<model>-firmware-release-history`). Парсер тягне section-heading anchor IDs:

| Формат | Приклад | Моделі |
|---|---|---|
| Dashed | `id="h-01030000-20260303"` | X1 / X1C / X1E / P1 / A1 / A1-mini / H2D / H2C / H2S / X2D |
| Undashed | `id="h-0102000020260409"` | P2S, X2D-варіанти |

Fallback-heuristic також скан-ить heading-текст по патерну `XX.XX.XX.XX (YYYYMMDD)`, приймаючи і ASCII-парени `()`, і **full-width парени `（）`** (U+FF08/U+FF09) — останні з'являються на A1 / A1-mini / P2S сторінках, бо Bambu wiki editor іноді інжектить CJK-пунктуацію.

Якщо бачиш "0 versions detected" на моделі одразу після зміни лайауту вікі — цей regex місце куди дивитись.

---

## :material-folder-arrow-down: Сховище прошивок {#firmware-store}

Завантажена прошивка лежить у довговічному, **індексованому** локальному сховищі під `<DATA_DIR>/firmware/`, з ключем **модель + версія** (та sha256-чексумою). Переюзається через принтери й re-upload-и — і, головне, ключем є **модель+версія, а не download-URL**, тож версія лишається installable **навіть після того, як Bambu прибере її з сайту**.

| Коли сховище допомагає | Деталь |
|---|---|
| Bulk update тієї ж моделі | П'ять A1 mini на тій самій firmware → один CDN download, п'ять FTP upload-ів |
| Failed upload retry | Повтор upload-у переюзає вже завантажений файл (звіряється sha256) |
| Rollback після зіпсованого upgrade | Попередня firmware скоріше за все ще у сховищі |
| Вендор прибрав версію | Версію, яку Bambu вже видалив, усе ще можна встановити зі сховища |

- **Завантаження наперед, без принтера.** На сторінці Firmware можна завантажити будь-яку версію у сховище заздалегідь (щоб мати її ще до потреби, або до того, як вендор її прибере).
- **Індикатори у сховищі.** Пікер версій показує, які версії вже у сховищі, а які — ні.
- У сховища нема TTL — файли живуть, поки не видалиш. Кожен `.bin` 50-150 MB; сховище росте ~1 GB через життя busy install-у.

---

## :material-shield-key: Permissions

| Permission | Дозволяє |
|---|---|
| `firmware:read` | Read installed version, list available versions, badge rendering, prepare check |
| `firmware:update` | Тригернути власне upload на SD-карту принтера |

Дефолтні групи: **Administrators** обидва, **Operators** обидва, **Viewers** жодного (їм бейдж би все одно не давав щось зробити).

---

## :material-printer-3d: Підтримувані моделі

Кожен Bambu Lab принтер, для якого вікі публікує release-history page, підтримується, разом з їхніми SSDP-кодами (тож парсер працює, чи зберіг ти friendly name `A1 Mini`, чи raw-код `N1` у printer-record-і):

| Серія | Моделі | Wiki path key |
|---|---|---|
| X1 | X1, X1C, X1 Carbon, X1E | `x1`, `x1e` |
| P1 | P1P, P1S | `p1` |
| P2 | P2S | `p2s` |
| A1 | A1, A1 Mini | `a1`, `a1-mini` |
| H2 | H2D, H2D Pro, H2C, H2S | `h2d`, `h2d-pro`, `h2c`, `h2s` |
| X2 | X2D | `x2d` |

Якщо твій принтер репортить SSDP model-код, якого нема в `MODEL_TO_API_KEY` — firmware check повертає `Unknown model`. Відкрий issue з raw `DevModel` хедером з твого принтера, додамо мапінг.

---

## :material-help-circle: Troubleshooting

??? question "Бейдж застряг на `Version unknown`"
    Принтер ще не відправив `firmware_version` через MQTT. Почекай 30-60 с після того, як принтер прийшов online, або refresh printer-картку. Якщо лишається unknown — MQTT-репорт принтера не містить поля; firmware-check сервіс трактує як "no current version" і пропонує latest як upgrade candidate.

??? question "`Update failed` toast — no SD card"
    Встав SD-карту і retry. SD-card check non-cached — наступний prepare побачить новий стан.

??? question "`Insufficient SD card space`"
    Bambu firmware потребує ~100 MB плюс 100 MB safety buffer. Помилка містить реальні числа — типово через leftover-gcode-файли. Очисти через екран принтера або через [File Manager](file-manager.md), потім retry.

??? question "`Cloudflare 403` у логах"
    Або `curl_cffi` застара, щоб імпресонатити поточний Chrome-fingerprint (рідко — chrome120 стабільний давно), або CF-impersonation-профіль нарешті старий, і Cloudflare bumped-нув свій фільтр. Onaverage до останнього BamDude release-у; impersonation-профіль котиться вперед на кожному release-і.

??? question "`buildId` помилки заповнюють логи"
    Bambu ротував Next.js `buildId`. Self-heal retry резолвить це прозоро — ці log-лінії інформаційні, не actionable. Якщо retry *теж* фейлиться — wiki version все одно детектиться з `wiki.bambulab.com`; тільки file-availability маркер на рядку буде `Unavailable`.

??? question "Версія firmware на вікі, але бейдж `Unavailable`"
    Bambu оголосив (wiki listing), але offline `.bin` не опублікував (download page). Типово для hot-fix-релізів, що йдуть тільки cloud-connected принтерам. BamDude нема що качати — чекай поки Bambu опублікує, або прийми як cloud-only.

??? question "Upload застряг на 0%"
    Або FTP недосяжний (wrong access code, wrong IP, firewall), або файл такий великий, що перший байт ще не пройшов. Tail `bamdude` логи на FTP-connect лінію. Якщо connect успішний, а upload не рухається — мережа throttle-ить; спробуй upload на Ethernet замість 2.4 GHz Wi-Fi.

??? question "Update завершився на стороні BamDude, але принтер його не бачить"
    `.bin` має бути в **корені** SD-карти з оригінальним filename. BamDude upload-ить у `/`, тож це завжди має бути правильно — але якщо ти руками перекидав файли на карті, принтер може дивитись не туди. Витягни карту, переконайся що файл у корені, встав назад і retry **Update from SD card** на екрані.
