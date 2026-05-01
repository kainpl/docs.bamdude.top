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
| **Preferred slicer** | `OrcaSlicer` чи `Bambu Studio`. Sidecar за замовчуванням для server-side слайсингу і desktop "Open in Slicer" URI на архівах, що не слайсилися server-side. Коли обидва sidecar'и налаштовані *і* доступні, Slice-modal показує per-job радіо "Slice with" для перевизначення цього default'а per source file (вибір запам'ятовується для кожного файлу в browser localStorage). |
| **Enable server-side slicing** (`use_slicer_api`) | Master-тоглер. Коли off — кнопка Slice пропадає з File Manager і Archives, слайсинг падає на open-in-desktop-slicer через URI scheme. |
| **OrcaSlicer API URL** (`orcaslicer_api_url`) | URL OrcaSlicer-sidecar'а — наприклад `http://localhost:3003` для дефолтного compose-рецепту. Порожнє = використати `SLICER_API_URL` env-дефолт. |
| **BambuStudio API URL** (`bambu_studio_api_url`) | URL BambuStudio-sidecar'а — наприклад `http://localhost:3001`. Порожнє = `BAMBU_STUDIO_API_URL` env-дефолт. |

Preset-tiers (cloud / local / standard) backend об'єднує автоматично у момент слайсингу — per-install setting не потрібен, див. "Слайсинг файлу" нижче.

---

## :material-cursor-default-click: Слайсинг файлу

З **File Manager**: меню дій на STL / 3MF / STEP / STP файлі → **Slice**.

Відкривається Slice-modal з трьома preset-dropdown'ами:

- **Printer profile** — з уніфікованого preset-listing'а. Кожен запис прийшов з одного з трьох tier'ів, об'єднаних з name-based dedup (cloud > local > standard): `cloud` (per-user Bambu Cloud-пресети), `local` (твої імпортовані `.json`-профілі), `standard` (bundled-defaults у sidecar'і). Modal лейбл показує tier поряд із кожним варіантом.
- **Process profile** — ті самі три tier'и.
- **Filament profile(s)** — один dropdown на AMS-слот, який використовує обрана плита. Modal pre-pick'ає найкращий match per-slot використовуючи filament-metadata з вихідного 3MF (type + colour score), щоб один клік **Slice** робив правильне для multi-color jobs.

Над dropdown'ами з'являється радіо **"Slice with"**, коли обидва sidecar'и (OrcaSlicer і BambuStudio) доступні — обери, який слайсер запустити саме для *цього* job'а. Перший раз default — глобальний *Preferred slicer*; наступні відкриття того самого source file'а пам'ятають твій останній вибір. Коли доступний лише один sidecar — радіо ховається (вибирати нема з чого), і використовується саме той, що працює, незалежно від глобального default.

Для multi-plate 3MF modal спершу питає, яку плиту/плити (single-plate / non-3MF — пропускає picker). **Printer-mismatch warning** з'являється коли вихідний 3MF слайсився під іншу модель принтера ніж обраний профіль — кнопка Slice залишається disabled поки не зміниш профіль, бо CLI слайсера тихо falls-back на embedded-settings джерела замість видавати помилку.

Persistent-toast у нижньому правому кутку трекає job: live progress percent + elapsed time, заміняється transient success/error toast при завершенні. Sliced-output лягає в ту ж папку бібліотеки як `.gcode.3mf` з `source_type='sliced'` provenance — оригінал не чіпається.

З **Archives**: меню дій на архіві з джерелом STL чи unsliced-3MF → **Slice**. Та сама modal; output зберігається як свіжий архів (з суфіксом " (re-sliced)" у print name), успадковуючи printer / project / makerworld metadata з джерела.

---

## :material-shield-key: Дозволи

| Permission | Що дозволяє |
|------------|--------------|
| `library:upload` | Тригерити слайсинг із File Manager **і** з Archives (sliced-output — це свіжий library-upload або archive-row, тож одна permission гейтить обидва шляхи). |
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
