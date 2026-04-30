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
                │  slicer_api   │   POST /v1/slice         │ slicer-api       │
                │  HTTP bridge  │ ──────────────────►      │ sidecar          │
                │               │                          │   OrcaSlicer чи  │
                │               │   GET /v1/jobs/{id}      │   BambuStudio    │
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

Обидва говорять одним і тим самим `/v1/slice` HTTP API; обираєш сам у **Settings → Slicer API**.

---

## :material-docker: Setup через Docker Compose

Найпростіший варіант — додати slicer-api сервіс у твій існуючий `docker-compose.yml`. Обери варіант, що відповідає sidecar'у:

=== "OrcaSlicer"
    ```yaml
    services:
      slicer-api:
        image: ghcr.io/<community-image>/orca-slicer-api:latest
        container_name: bamdude-slicer-api
        restart: unless-stopped
        environment:
          - SLICER_MAX_CONCURRENT_JOBS=2
        volumes:
          - slicer_cache:/cache
        ports:
          - "127.0.0.1:8765:8765"
    
    volumes:
      slicer_cache:
    ```

=== "BambuStudio"
    ```yaml
    services:
      slicer-api:
        image: ghcr.io/<community-image>/bambustudio-api:latest
        container_name: bamdude-slicer-api
        restart: unless-stopped
        volumes:
          - slicer_cache:/cache
        ports:
          - "127.0.0.1:8765:8765"
    
    volumes:
      slicer_cache:
    ```

Потім у `docker-compose.yml` BamDude'у додай sidecar у ту ж мережу і вкажи URL:

```yaml
services:
  bamdude:
    # …існуючий конфіг…
    environment:
      - SLICER_API_URL=http://slicer-api:8765
```

!!! info "Мережа"
    Найкраще — sidecar у мережі BamDude'у і **порт назовні не публікувати** взагалі. Тільки BamDude'у потрібен доступ. Рядок `127.0.0.1:8765` вище — це лише для дев-дебагу.

---

## :material-cog: Settings → Slicer API

| Опція | Що робить |
|-------|-----------|
| **Enable Slicer API** | Master-тоглер. Коли off — кнопка Slice пропадає з file manager і archive page. |
| **API URL** | URL sidecar'а — наприклад `http://slicer-api:8765`. |
| **Health check** | Пінгує `/v1/health` і показує green/red + версію + queue-глибину. Перевір перед збереженням, щоб зловити одруку. |
| **Default profile tier** | `cloud` (Bambu Studio cloud-пресети), `local` (локальні OrcaSlicer-профілі імпортовані через [K-Profiles](kprofiles.md)) чи `standard` (community-defaults у sidecar'і). |
| **Max concurrent jobs** | Default 1. Підняти має сенс лише якщо sidecar-image зібраний з підтримкою конкуренції — інакше job'и шерезі. |

---

## :material-cursor-default-click: Слайсинг файлу

З **File Manager**:

1. Right-click на STL чи unsliced-3MF → **Slice**.
2. Відкривається Slice-modal:
   - **Target printer model** — список усіх лінкнутих моделей + standard-моделей із sidecar'а.
   - **Filament profile** — приходить з resolution-tier'а (Cloud / Local / Standard). Pinned default per model.
   - **Plate** — для multi-plate 3MF обираєш плиту/плити.
   - **Override snippets** — опційно. Якщо є [G-code Injection](#) сніпети для моделі — auto-apply при слайсингу.
3. Тисни **Slice**. Job-tracker (top-right) показує прогрес; toast при завершенні.
4. Sliced output лягає в ту ж папку бібліотеки як `.gcode.3mf` з `source_type='sliced'` provenance — оригінал не чіпається.

З **Archives → reprint flow**: та сама modal, але output зберігається як свіжий архів (link'нутий на джерело), щоб репринтнути напряму.

---

## :material-file-cog-outline: 3MF embedded-settings fallback

Деякі 3MF приходять зі вже вбудованими settings (`Metadata/slice_info.config` + per-plate `.gcode` settings, успадковані з оригінального слайсу). Якщо слайсиш такий 3MF без явного override'а — sidecar бере embedded-settings як source-of-truth, і result'на бібліотечна рядка несе `used_embedded_settings: true` в metadata для traceability.

Це правильний default — embedded-settings уже дали printable-результат на чиїйсь машині; сліпо overrid'ити їх ризиковано. Щоб force-re-slice'нути зі своїм профілем — обери профіль явно в modal'і замість "auto".

---

## :material-shield-key: Дозволи

| Permission | Що дозволяє |
|------------|--------------|
| `library:upload` | Тригерити слайсинг (sliced-output — це свіжий upload бібліотеки). |
| `archives:reprint` | Тригерити слайсинг із archive-reprint flow. |

URL Slicer API + tier-defaults гейтяться `settings:update`.

---

## :material-alert-circle-outline: Режими провалу

- **Sidecar offline** → чистий error toast, job marked failed; оригінал не чіпається.
- **Profile not found** → помилка називає відсутній профіль — додай через [K-Profiles](kprofiles.md) або обери інший tier.
- **Sidecar відмовив файл** (corrupt 3MF, unsupported plate, etc.) → toast показує дослівне повідомлення sidecar'а — не треба копати в логах контейнера.
- **Slice timeout** (default 10 хв) → job скасовується, partial-output відкидається.

---

## :material-link-variant: Дивись також

- [File Manager](file-manager.md) — де живе кнопка Slice.
- [K-Profiles](kprofiles.md) — як завантажити локальні OrcaSlicer-профілі філаменту в `local`-tier.
- [MakerWorld import](makerworld.md) — поєднай імпорти з server-side слайсингом, коли жодна плита не підходить твоєму принтеру.
