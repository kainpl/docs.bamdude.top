---
title: Slicer Pipelines
description: Збережи налаштування слайсу один раз, потім слайсь-і-в-чергу будь-який файл одним кліком — на конкретний принтер чи цілий клас моделей
---

# Slicer Pipelines

**Pipeline** пакує чотири вибори, які ти зазвичай робиш у діалозі Slice — printer preset, process preset, filament preset на кожен слот AMS і тип столу — разом із **dispatch-таргетом** і **стратегією fanout копій**. Збережи його один раз — і повторюване завдання перестає бути рутиною «перевибери-все»: **Run with pipeline** на будь-якому файлі слайсить джерело один раз і ставить у чергу стільки копій, скільки попросиш, на таргет.

Побудовано на [дворівневій черзі](auto-queue.md) BamDude — pipeline із class-таргетом віддає свої копії auto-queue distributor'у, тож вони балансуються по відповідних принтерах точно як будь-яке інше model-assigned завдання.

---

## :material-cog-outline: Що зберігає pipeline

| Поле | Що це |
|---|---|
| **Name / description** | Твоя мітка налаштування. |
| **Printer preset** | Профіль принтера, під який слайсити (source + id — local, Orca Cloud, Bambu Cloud чи standard). |
| **Process preset** | Профіль process/якості. |
| **Filament presets** | Один preset **на слот AMS**, тож multi-material завдання мапить кожен слот на правильний філамент. |
| **Bed type** | Тип build-plate, під який слайсити. |
| **Dispatch target** | [Конкретний принтер чи клас моделей](#таргетинг). |
| **Fanout strategy** | Як копії розходяться по class-таргету — `max_parallel`, `fill_one_first` чи `round_robin`. |

**Кількість копій — не частина pipeline**: ти обираєш її щоразу при запуску, тож той самий pipeline може зробити одну деталь сьогодні й двадцять завтра.

---

## :material-play-circle-outline: Збереження і запуск

**Збережи** прямо з діалогу Slice через **Save as pipeline** — він захоплює presets, які ти вже там вибрав.

**Run with pipeline** з будь-якого:

- **файлу бібліотеки**,
- **архіву**, чи
- самого **діалогу Slice**.

BamDude слайсить джерело **один раз** з presets pipeline'у, потім ставить копії у чергу на таргет. Один слайс, N елементів черги — без реслайсу на копію.

---

## :material-target: Таргетинг

Pipeline диспатчить на один із двох видів таргету:

- **Конкретний принтер** — кожна копія йде в чергу саме тієї машини.
- **Цілий клас моделей** — напр. *будь-який X1C*. Class-таргети віддаються **auto-queue distributor'у**, який балансує копії по кожному відповідному принтеру на фермі за стратегією fanout pipeline'у:

| Стратегія | Поведінка |
|---|---|
| `max_parallel` | Розкидати копії по якомога більшій кількості принтерів для найшвидшого фінішу за годинником. |
| `fill_one_first` | Заповнити чергу одного принтера, перш ніж переходити до наступного. |
| `round_robin` | Роздавати копії рівномірно, по одній на принтер по колу. |

---

## :material-clipboard-check-outline: Pre-flight перевірка eligibility

Перед тим як закомітити, запуск pipeline перевіряється проти таргету й позначає невідповідності — таргет **offline чи вимкнено**, слот AMS, чий **завантажений тип чи колір філаменту відрізняється** від pipeline'у, чи **відсутній слот**. Для class-таргету звіт читається як *«3 з 5 X1C eligible»* з розбивкою по кожному принтеру, чому саме він проходить чи ні.

Якщо знайдено проблеми — запуск зупиняється й показує звіт. Escape-люк **Run anyway** дозволяє диспатчити попри все (override записується на run), для випадків, коли ти знаєш краще за перевірку.

---

## :material-view-dashboard-outline: Вкладка Pipelines

Сторінка Print Queue має вкладку **Pipelines** (поряд з Queue, History і Timeline), що трекає кожен запуск **вживу**:

- **Статус на копію** — дивись, як кожна копія рухається слайс → у черзі → друкується → готово/провал.
- **Cancel** in-flight запуск.
- **Retry лише провалених копій** — не треба перезапускати весь batch.
- **Clear log**, коли переглянув.

Керуй, перейменовуй і видаляй самі pipelines під **Settings → Pipelines**.

---

## :material-shield-key: Дозволи

Pipelines гейтяться трьома дозволами. **Administrators** і **Operators** отримують усі три; **Viewers** — лише read.

| Дозвіл | Дає |
|---|---|
| `pipelines:read` | Бачити pipelines, історію їхніх запусків і pre-flight eligibility. |
| `pipelines:write` | Створювати, редагувати, видаляти pipelines і чистити лог запусків. |
| `pipelines:run` | Запускати run, скасовувати його й ретраїти провалені копії. |

Мапінг на REST-поверхню:

| Ендпоінт | Метод | Дозвіл |
|---|---|---|
| `/slicer-pipelines/` | GET / POST | read / write |
| `/slicer-pipelines/{id}` | GET / PUT / DELETE | read / write / write |
| `/slicer-pipelines/{id}/check-eligibility` | POST | read |
| `/slicer-pipelines/{id}/run` | POST | run |
| `/pipeline-runs` | GET | read |
| `/pipeline-runs/{id}/cancel` | POST | run |
| `/pipeline-runs/{id}/retry-failed` | POST | run |
| `/pipeline-runs/clear` | POST | write |

[API-ключ](api-keys.md) з read-scope може читати pipelines і runs; запуск pipeline — це людська/операторська дія.

---

## :material-link-variant: Пов'язане

- [Авто-черга](auto-queue.md) — дворівневий distributor, що розкидає копії class-таргетованого pipeline'у по відповідних принтерах.
- [Черги друку](print-queue.md) — куди лягають копії; дашборд Pipelines живе на цій сторінці.
- [Slicer API](slicer-api.md) — контейнеризований сайдкар OrcaSlicer / Bambu Studio, що робить власне слайс.
- [Cloud-профілі](cloud-profiles.md) / [Orca Cloud](orca-cloud.md) — джерела presets, на які може посилатися pipeline.
