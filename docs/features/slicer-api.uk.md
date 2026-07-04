---
title: Slicer API (серверний слайсинг)
description: Кидай STL чи 3MF у контейнерний OrcaSlicer / BambuStudio sidecar і отримуй готовий .gcode.3mf, не виходячи з BamDude
---

# Slicer API (серверний слайсинг)

BamDude вміє слайсити STL і unsliced-3MF файли **на сервері**, спілкуючись з контейнерним **OrcaSlicer** чи **BambuStudio** sidecar по HTTP. Кидаєш файл у бібліотеку, тиснеш **Slice**, обираєш модель принтера + філамент-профіль — і за хвилину готовий `.gcode.3mf` лежить у бібліотеці. Без ноутбука, без слайсера-проксі, без перетягування файлів.

Опційно: жоден слайсер не їде в самому BamDude-образі. Sidecar запускається окремо (Docker Compose рецепт нижче), а BamDude'у кажеш, де він живе.

---

## :material-architecture: Архітектура

```
                ┌───────────────┐
   Файл бібл-и  │   BamDude     │   STL / 3MF (settings)
  ──────────►   │   backend     │ ──────────────────►
                │               │                          ┌──────────────────┐
                │  slicer_api   │   POST /slice            │ slicer-api       │
                │  HTTP bridge  │ ──────────────────►      │ sidecar          │
                │               │                          │   OrcaSlicer чи  │
                │               │   GET /slice/progress    │   BambuStudio    │
                │               │ ◄──────────────────      │   CLI всередині  │
                │               │                          │                  │
                │               │   .gcode.3mf bytes       │                  │
                │               │ ◄──────────────────      │                  │
                │               │                          └──────────────────┘
                │  Library row  │
                │  + archive    │
                └───────────────┘
```

Bridge тримає sliced-output **у бібліотеці** (чи в архіві, залежно з якої сторінки слайсив), записує кожен параметр, що пішов у слайсинг, і чисто фейлиться, якщо sidecar offline чи відмовив файл.

---

## :material-package-variant: Підтримувані sidecar'и

| Слайсер | Контейнер | Примітки |
|---------|-----------|----------|
| **OrcaSlicer** | Open-source community-image | Рекомендований — активно розвивається, широка підтримка принтерів/пластиків. |
| **BambuStudio** | Офіційний Bambu Lab | Коли треба байт-в-байт повтор результату десктопного Bambu Studio. |

Обидва говорять одним і тим самим `/slice` HTTP API. Можеш запускати один з них або обидва одразу; активний(і) обираєш у **Settings → Profiles → Slicer API**.

---

## :material-docker: Setup через Docker Compose

В репо BamDude уже шипиться готовий стек у [`slicer-api/`](https://github.com/kainpl/bamdude/tree/main/slicer-api) — найпростіший спосіб через нього:

```bash
git clone https://github.com/kainpl/bamdude.git
cd bamdude/slicer-api/
cp .env.example .env       # опційно — pin версії слайсерів / порти

# Обери рівно один:
docker compose --profile orca   up -d   # тільки OrcaSlicer    (host port 3003)
docker compose --profile bambu  up -d   # тільки BambuStudio   (host port 3001)
docker compose --profile all    up -d   # обидва
```

Голий `docker compose up -d` (без profile) не запустить нічого — треба явно вказати `--profile orca`, `--profile bambu` чи `--profile all`. Потім у BamDude → **Settings → Profiles → Slicer API** заповни URL для слайсерів, які запустив (`http://localhost:3003` для Orca, `http://localhost:3001` для BambuStudio).

!!! warning "Docker Desktop 4.71 — обхід для першого білда"
    Docker Desktop 4.71 (engine 29.4.1 / compose v5.1.x / buildx 0.33.x-desktop) має зламаний `buildx bake` compose-bridge: `docker compose build` миттєво падає з `failed to execute bake: exit status 1` без жодних деталей, незалежно від форми profiles. `COMPOSE_BAKE=false` НЕ вимикає bake на цій версії.

    **Обхід для першого білда** — форснути legacy classic builder; image тоді кешується і `compose up -d` перевикористовує його:

    ```bash
    # bash / zsh
    DOCKER_BUILDKIT=0 COMPOSE_DOCKER_CLI_BUILD=0 \
      docker compose --profile all build
    docker compose --profile all up -d
    ```

    ```powershell
    # PowerShell
    $env:DOCKER_BUILDKIT = "0"; $env:COMPOSE_DOCKER_CLI_BUILD = "0"
    docker compose --profile all build
    $env:DOCKER_BUILDKIT = $null; $env:COMPOSE_DOCKER_CLI_BUILD = $null
    docker compose --profile all up -d
    ```

    Або викликай buildx напряму (modern BuildKit, паралельно, швидше):

    ```bash
    docker buildx bake -f docker-compose.yml orca-slicer-api
    docker buildx bake -f docker-compose.yml bambu-studio-api
    docker compose --profile all up -d
    ```

    Старіші релізи Docker Desktop (4.70 і нижче) та Docker CE на Linux баг не зачепив — env vars не потрібні.

### Запустити sidecar(и) на іншій машині

Якщо BamDude-сервер сам не може крутити sidecar-контейнери (resource-ліміти, немає Docker, тощо) — постав sidecar(и) на окремій машині й вкажи їхні URL у BamDude. Той самий `slicer-api/docker-compose.yml` з репо BamDude використовуй на хості sidecar'ів, потім у `Settings → Profiles → Slicer API` встанови URL'и `http://<sidecar-host>:3003` / `:3001` замість `localhost`. Sidecar не має auth — тримай у trusted network (LAN, Tailscale, WireGuard).

Можеш також override'нути env-дефолти, які BamDude читає на старті: `SLICER_API_URL` (default `http://localhost:3003`) і `BAMBU_STUDIO_API_URL` (default `http://localhost:3001`). UI-поля URL мають пріоритет, якщо встановлені.

---

## :material-cog: Settings → Profiles → Slicer API

| Опція | Що робить |
|-------|-----------|
| **Preferred slicer** | `OrcaSlicer` чи `Bambu Studio`. Sidecar за замовчуванням для server-side (in-app) слайсингу. Коли обидва sidecar'и налаштовані *і* доступні, Slice-modal показує per-job радіо "Slice with" для перевизначення цього default'а per source file (вибір запам'ятовується для кожного файлу в browser localStorage). |
| **Enable server-side slicing** (`use_slicer_api`) | Master-тоглер. Коли off — кнопка Slice пропадає з File Manager, слайсинг падає на open-in-desktop-slicer через URI scheme. |
| **OrcaSlicer API URL** (`orcaslicer_api_url`) | URL OrcaSlicer-sidecar'а — наприклад `http://localhost:3003` для дефолтного compose-рецепту. Порожнє = використати `SLICER_API_URL` env-дефолт. |
| **BambuStudio API URL** (`bambu_studio_api_url`) | URL BambuStudio-sidecar'а — наприклад `http://localhost:3001`. Порожнє = `BAMBU_STUDIO_API_URL` env-дефолт. |

Desktop-кнопка **Open in Slicer** керується окремим, незалежним налаштуванням — **Settings → Slicer → Open in Slicer** — dropdown'ом, що за замовчуванням стоїть на **Same as API slicer**. Вкажи інший слайсер, щоб, наприклад, слайсити через Bambu Studio sidecar, а файли відкривати локально в OrcaSlicer (чи навпаки); наявні налаштування не змінюються, поки ти сам не вибереш інше значення.

Preset-tiers (cloud / local / standard) backend об'єднує автоматично у момент слайсингу — per-install setting не потрібен, див. "Слайсинг файлу" нижче.

---

## :material-cursor-default-click: Слайсинг файлу

З **File Manager**: меню дій на STL / 3MF / STEP / STP файлі → **Slice**.

Відкривається Slice-modal з трьома preset-dropdown'ами:

- **Printer profile** — з уніфікованого preset-listing'а. Кожен запис прийшов з одного з трьох tier'ів, об'єднаних з name-based dedup (cloud > local > standard): `cloud` (per-user Bambu Cloud-пресети), `local` (твої імпортовані `.json`-профілі), `standard` (bundled-defaults у sidecar'і). Modal лейбл показує tier поряд із кожним варіантом. За замовчуванням обирається принтер, під який готувався вихідний 3MF (якщо такий профіль доступний), інакше — перший у списку.
- **Process profile** — ті самі три tier'и, але **відфільтровані під обраний принтер**: профілі для інших принтерів зсуваються в кінцеву групу **«Other printers»** замість того, щоб зникати, а профілі без інформації про принтер лишаються в основному списку (ніколи не ховаються). За замовчуванням — process, під який готувався 3MF, якщо він сумісний. Зміна принтера перевибирає process, якщо поточний більше не підходить.
- **Filament profile(s)** — один dropdown на AMS-слот, який використовує обрана плита, відфільтрований так само (сумісні профілі спершу, група «Other printers» в кінці). Modal pre-pick'ає найкращий match per-slot використовуючи filament-metadata з вихідного 3MF (type + colour score), з пониженням несумісних із принтером філаментів, щоб один клік **Slice** робив правильне для multi-color jobs.

Modal кешує cloud- і bundled-preset-listing'и на кілька хвилин, тож якщо ти видалиш чи перейменуєш пресет у Bambu Studio / Bambu Handy — він може ще якийсь час висіти в dropdown'ах. Контрол **Refresh** на списку пресетів одразу тягне свіжі listing'и. Імпорт чи видалення локального профілю в **Settings** також миттєво оновлює пресети Slice-діалогу.

Сумісність визначається власним списком `compatible_printers` профілю (якщо є), потім будь-яким завантаженим [Slicer Bundle](#slicer-preset-bundles-bbscfg), потім за конвенцією іменування BambuStudio `@BBL <model> <nozzle>` — і вона **враховує сопло**, тож process під сопло 0.6 не буде сумісним для принтера із соплом 0.4 (0.4 — неявне за замовчуванням, що не несе суфікса). Той самий matcher керує підбором профілів у майстрі **калібрування філаменту**; там несумісні профілі ховаються повністю, а не групуються, бо калібрувальний друк на не тому принтері просто марнує стіл.

**Slicer-picker** сидить угорі Slice-діалогу — дві картки-кнопки (дзеркалять "Filament Tracking"-патерн з Settings) з власними live-індикаторами здоров'я. Авто-локається на єдиний здоровий sidecar, коли інший лежить; ти вибираєш вільно, коли обидва доступні; offline-картки disabled. Перший раз default — глобальний *Preferred slicer*; наступні відкриття того самого source file пам'ятають твій останній вибір (per-file localStorage).

**Override типу столу** (5 варіантів: Cool / Engineering / High Temp / Textured PEI / SuperTack) пробрасується в `--curr-bed-type` на CLI. Default `Textured PEI Plate` відповідає заводській плиті на сучасній лінійці Bambu; власники A1 / A1-mini переключаються на SuperTack один раз і вибір зберігається в localStorage. Сліцені 3MF із Bambu Studio все ще шанують свій вбудований per-plate `bed_type` (BamDude форвардить оригінальні байти) — override спрацьовує тільки для джерел без нього.

**Контрол джерела пресетів** над пресет-dropdown'ами вмикає режим резолва modal'а в одному місці. Коли жодного `.bbscfg`-бандла не імпортовано, він рендериться як standalone 3-станковий segmented owner-фільтр (All / My presets / Built-in). Коли імпортовано хоча б один бандл, над sub-control'ом з'являється top-level **Manual / Bundle**-segmented: у режимі **Manual** sub-control — той самий 3-станковий owner-фільтр (класифікує cloud-пресети як custom-vs-builtin за `setting_id`-regex'ом сторінки Profiles, `^(P[FPM]US|PF\d|PP\d)`; local-імпорти завжди custom, standard-бандли завжди built-in); у режимі **Bundle** sub-control — bundle-dropdown описаний нижче. Зберігається в localStorage (owner-фільтр під ключем `bamdude:slice-modal:filter-owner`, останній вибраний бандл — `bamdude:slice-modal:last-bundle-id`). Перемикання owner-фільтра скидає поточний вибір у dropdown'ах, що тепер не матчиться, щоб прихований (відфільтрований) пресет не міг тихо засабмітити при slice. Перемикання у Bundle підхоплює останній використаний бандл, якщо він ще в поточному списку, інакше — перший доступний (ніколи не відновлює застарілий id).

Для multi-plate 3MF modal вбудовує **inline plate-selector** угорі body, дзеркаля picker плит з Print modal — вертикальний paginator + details-картка. Плита 1 авто-вибирається на load, щоб filament-requirements + presets-запити йшли без блокування на user-interaction; клік по іншій плиті пере-ключає ці запити. Чекбокс **Нарізати всі плити** над picker'ом: познач його, щоб нарізати всі плити в один multi-plate вихід (`plate=0`) замість однієї обраної.

**Перенарізання під інший принтер** — можна нарізати 3MF, зроблений під іншу модель. Обери будь-який профіль/bundle принтера, і слайсер перенаріже під цю ціль (стіл, кінематика, к-сть сопел і start-gcode беруться з обраного профілю). Коли ціль перетинає клас сопла (одне ↔ два сопла H2D/H2C/X2D), BamDude пробрасує `--arrange`, щоб BambuStudio переставив об'єкти під цільовий стіл і узгодив вбудовані налаштування; крос-клас «нарізати всі плити» нарізає кожну плиту окремо й зливає в один файл. Якщо слайсер усе одно не може дати валідний результат — його причина показується в діалозі, який треба закрити, а не в тості, що зникає.

### Слайсерні бандли пресетів (.bbscfg)

Оператори, які тримають єдиний відлагоджений набір printer / process / filament на кожен слайс, можуть один раз імпортувати "Printer Preset Bundle" (`.bbscfg`) з BambuStudio і обирати його у Slice-modal — це повністю замінює резолв cloud / local / standard tier'ів.

**Навіщо бандли** — резолв пресетів має довгий хвіст corner-кейсів, які резолвер ловить на кожен слайс: cloud-пресети за стійким loginом, `# `-префікс який BambuStudio додає для user-clones, "from User"-сентинели в cloud-профілях, dangling `inherits:` посилання після rename. Бандл — це один зазипований снапшот curated триплета на конкретний принтер; ніяких живих резолвів, тільки `bundle_id + printer_name + process_name + filament_names[]` посилається у sidecar за іменами.

**Імпорт** — Settings → Profiles → Slicer API → панель **Slicer Bundles** (видна лише коли `use_slicer_api` ввімкнено, бо upload round-trip'ить через sidecar). Натисни **Upload bundle** і вибери `.bbscfg` експортований з BambuStudio (File → Export → Export Preset Bundle → "Printer preset bundle"). Sidecar дедуплікує uploads за SHA-256-префіксом zip-контенту — повторний upload того ж файлу ідемпотентний. Панель показує кожен імпортований бандл з ім'ям принтера, кількістю process/filament-пресетів і версією; per-row Delete просить confirm перед видаленням.

**Використання у Slice-modal** — коли імпортований хоча б один бандл, у контролі джерела пресетів стає доступним перемикач **Manual / Bundle**. Натисни **Bundle** і modal перемикається на bundle-scope pickers: принтер рендериться як read-only label (кожен `.bbscfg` несе рівно один printer-пресет, тож вибір не має сенсу), а dropdown'и process + per-slot filament заповнюються тільки з вмісту обраного бандла — глобальні cloud / local / standard пресети у цьому режимі сховані. Submit йде через `SliceRequest.bundle`, і sidecar матеріалізує JSON-триплет зі збереженого бандла за іменами. Щоб вийти з bundle-режиму, натисни **Manual** у тому ж перемикачі — `selectedBundleId` очищається й оригінальні 3-tier dropdown'и повертаються.

**Версіонування sidecar'а** — bundle-ендпоінти живуть на гілці `bamdude/profile-resolver` нашого форку (cherry-pick з upstream-гілки `bambuddy/bundle-import` у `maziggy/orca-slicer-api`, перебілджено в наші образи `bamdude-orca-slicer-api:orca2.3.2` + `bamdude-bambu-studio-api:bambu02.06.00.51`), тож `docker compose --profile all build --pull` з `slicer-api/` тягне свіжі sidecar'и з підключеними роутами. Перемикач Manual / Bundle у Slice-modal'і тихо не рендериться, якщо `GET /api/v1/slicer/bundles` повертає `[]` (sidecar offline, не імпортовано жодного бандла, або sidecar до bundle-support'у) — інсталяції без бандлів бачать саме оригінальний 3-tier modal з owner-фільтром угорі.

**3MF embedded-settings fallback** — якщо CLI sidecar'а відмовив на bundle-резолв-триплеті для конкретного 3MF (range-validation reject на corner-case і т.д.), dispatcher fall-back'ить до слайсингу без триплета з embedded-настройками файла (`used_embedded_settings=true` у відповіді). Bundle-aware preview-слайсинг для незакам'янілих project-файлів теж використовує bundle-контекст, тож грами в modal'і збігаються з тим, що насправді нарізає реальний слайс.

### Індикатори доступності

Здоров'я sidecar'ів виходить на трьох поверхнях, всі шерять один React-Query-кеш + ендпоінт `GET /api/v1/slicer/health/{slicer}` (30 с in-process cache):

- **Settings → Profiles → Slicer API** — невеликий inline-статус біля кожного URL-поля (зелений чек + версія, або червоний хрестик з помилкою).
- **Slice modal** — кожна картка picker'а несе live-індикатор здоров'я (див. вище).
- **System page → Slicer Sidecars** секція — версія + доступність + URL кожного sidecar (auto-refresh 30 с разом із рештою system info).

Persistent-toast у нижньому правому кутку трекає job: live progress percent + elapsed time, заміняється transient success/error toast при завершенні. Sliced-output лягає в ту ж папку бібліотеки як `.gcode.3mf` з `source_type='sliced'` provenance — оригінал не чіпається.

---

## :material-shield-key: Дозволи

| Permission | Що дозволяє |
|------------|--------------|
| `library:upload` | Тригерити слайсинг із File Manager (sliced-output — це свіжий library-upload). |
| `library:read` | Поллити job-tracker toast (`/api/v1/slice-jobs/{id}`) і filament-discovery preview-slice progress (`/api/v1/slicer/preview-progress/{id}`). |
| `cloud:auth` | Потрібно щоб тягнути `cloud` preset-tier — без неї modal показує тільки `local` + `standard` tier'и. |

Settings → Profiles → Slicer API toggle і URL-поля гейтяться `settings:update`.

---

## :material-alert-circle-outline: Режими провалу

- **Sidecar offline** → 502 у toast'і, job marked failed; оригінал не чіпається.
- **Profile not found** → 400 називає відсутній профіль — додай через [K-Profiles](kprofiles.md) або обери інший tier.
- **Sidecar відмовив файл** (corrupt 3MF, unsupported plate, malformed preset, etc.) → toast показує дослівний CLI stdout/stderr sidecar'а — не треба копати в логах контейнера.
- **Embedded-settings fallback** — для 3MF-джерел 5xx від sidecar'а з `--load-settings` тригерить ОДИН retry без profiles. Тоді слайсинг використовує embedded-settings джерела (ті, що оригінальний слайсер запік у `Metadata/slice_info.config`); результат несе `used_embedded_settings: true` у metadata. У STL embedded-settings нема, тож 5xx там terminal.
- **Cloud presets unreachable** (token expired / network down) → modal рендерить `cloud`-tier зі status-banner'ом і фолится на `local` + `standard` only.

---

## :material-link-variant: Дивись також

- [File Manager](file-manager.md) — де живе кнопка Slice.
- [K-Profiles](kprofiles.md) — як завантажити локальні OrcaSlicer-профілі філаменту в `local`-tier.
- [MakerWorld import](makerworld.md) — поєднай імпорти з server-side слайсингом, коли жодна плита не підходить твоєму принтеру.
