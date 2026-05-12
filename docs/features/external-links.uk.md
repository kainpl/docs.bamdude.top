---
title: Зовнішні посилання
description: Адмін-кастомні посилання в сайдбарі BamDude — wiki, helpdesk, дашборди, тощо. Lucide-іконки або власне зображення
---

# Зовнішні посилання

External Links дозволяють адміну додати в сайдбар BamDude кастомні пункти, що ведуть кудись зовні — на team-wiki, форму helpdesk-тикета, Grafana-дашборд, інстанс OctoPrint, сторінку завантаження Bambu Studio. Посилання зберігаються в БД BamDude, рендеряться під вбудованою навігацією і входять до стандартного backup/restore циклу.

## :material-link: Що це

Невеличка адмін-керована таблиця рядків `(name, url, icon, open_in_new_tab, nav_group, sort_order)`. Будь-хто з permission-ом `external_links:read` бачить рендер у сайдбарі; тільки користувачі з `external_links:create` / `external_links:update` / `external_links:delete` можуть ними керувати. URL валідується — повинен починатися з `http://` або `https://` (інші схеми типу `mailto:` чи `ssh://` бекенд відкидає).

На external_links **немає per-user visibility-скоупу** — кожен авторизований користувач з `external_links:read` бачить той самий список. Якщо треба group-scoped посилання, використовуй якийсь dashboard-tool з власною авторизацією і клади посилання на нього.

Кожне посилання належить до **групи сайдбара** (`nav_group`) — Operations / Workshop / Resources / Care / System / Links — тож адмінські посилання потрапляють у те саме 6-бакетне групування, що й вбудована навігація, замість того щоб телепатися flat-списком у кінці сайдбару. Бакет `links` (`external`) стоїть **перед** `system`, тож нові посилання видно одразу без скролу.

## :material-plus-circle: Додавання посилання

**Settings → External Links → Add Link** відкриває форму:

| Поле | Замітки |
|---|---|
| **Name** | 1–50 символів. Відображається біля іконки в сайдбарі. |
| **URL** | 1–500 символів. Має починатися з `http://` або `https://`. |
| **Icon** | Або вибрати [Lucide](https://lucide.dev/icons/) icon за іменем з icon-picker, або завантажити власне зображення. |
| **Sidebar group** | Дропдаун: Operations / Workshop / Resources / Care / System / Links. Для нових записів дефолт — `external` (бакет Links): вони з'являються прямо перед групою System, замість того щоб тонути під рештою навігації. |
| **Open in new tab** | Якщо `true`, посилання відкривається з `target="_blank"`, тож BamDude залишається у поточній вкладці. Лиши off для in-app навігації (корисно тільки якщо URL на тому ж origin, що і BamDude). |

Нові посилання додаються в кінець обраної групи (`sort_order` авто-ставиться `max(existing у групі) + 1`).

!!! tip "Lucide vs Material icon names"
    Upstream Bambuddy wiki вказувала на mkdocs-material icon names — BamDude насправді використовує [Lucide](https://lucide.dev/icons/) icon names (бо frontend імпортує `lucide-react`). Якщо своєї іконки не бачиш — дивись Lucide-каталог, не Material Design Icons.

### Кастомні іконки-зображення

Якщо Lucide-іконка не підходить (наприклад, треба vendor-логотип) — клікни **Upload custom icon** в модалці:

| Обмеження | Значення |
|---|---|
| Дозволені розширення | `.png`, `.jpg`, `.jpeg`, `.gif`, `.svg`, `.webp`, `.ico` |
| Макс. розмір файлу | 1 MB |
| Storage | `<base_dir>/icons/<uuid>.<ext>` на диску |
| Віддається через | `GET /api/v1/external-links/{id}/icon` (без авторизації, щоб `<img>`-теги могли вантажити без Authorization-хедера) |

Перемикання назад з custom-іконки на Lucide-preset видаляє uploaded-файл з диска при збереженні.

## :material-sidebar: Позиція і поведінка в сайдбарі

External links рендеряться **всередині свого бакету `nav_group`** у сайдбарі, в одній групі з тематично пов'язаними вбудованими пунктами. Дефолтна група `external` стоїть між `care` і `system` — тож щойно створене посилання видно одразу, а не похованим у самому кінці сайдбару. Per-user toggle, щоб приховати, немає — якщо посилання в таблиці, кожен авторизований користувач з `external_links:read` його бачить.

| Поведінка | Що відбувається |
|---|---|
| `open_in_new_tab = true` | Клік відкриває URL в новій вкладці (`target="_blank"`, `rel="noopener noreferrer"`). Корисно для зовнішніх tool-ів side-by-side з BamDude. |
| `open_in_new_tab = false` | Клік навігує поточну вкладку. Роби так тільки для URL-ів того ж origin (інакше SPA втрачає стан). |
| Custom-іконка вибрана | Рендериться завантажене зображення. Поле `icon` ігнорується. |
| Немає custom-іконки | Рендериться Lucide-іконка з імені в `icon`. За замовчуванням `link` якщо не задано. |

## :material-sort: Reordering

Drag-and-drop **прямо на сайдбарі** (або в **Settings → External Links**) змінює порядок. Перетаскування **обмежене групою**:

- **Всередині групи** — тягни будь-який елемент вгору або вниз всередині своєї групи. Drop-індикатор з'являється лише на валідних таргетах (тій самій групі); cross-group drop'и тихо відкидаються.
- **Цілі групи** — хапай header-ряд групи (показує `GripVertical` handle на hover у розгорнутому сайдбарі) і тягни цілу групу вгору/вниз як блок. Порядок зберігається у тому самому `sidebarOrder` `localStorage`-ключі, що й порядок елементів.
- **Зміна групи** — щоб перенести посилання в іншу групу, відредагуй його і поміняй `nav_group` (drag-and-drop цього навмисно не вміє, щоб ти випадково не розламав групування).

Frontend відсилає `PUT /api/v1/external-links/reorder` зі списком ID; бекенд проставляє `sort_order = index` кожному. Новий порядок діє одразу.

## :material-pencil: Редагування і видалення

| Дія | Endpoint | Permission |
|---|---|---|
| Редагування полів (name / URL / icon / new-tab toggle) | `PATCH /api/v1/external-links/{id}` | `external_links:update` |
| Видалити посилання | `DELETE /api/v1/external-links/{id}` | `external_links:delete` |
| Замінити custom-іконку | `POST /api/v1/external-links/{id}/icon` (multipart) | `external_links:update` |
| Видалити custom-іконку | `DELETE /api/v1/external-links/{id}/icon` | `external_links:update` |

Видалення посилання з custom-іконкою також видаляє файл з `<base_dir>/icons/`.

## :material-lightbulb: Приклади

### Внутрішня wiki

| Поле | Значення |
|---|---|
| Name | `Team Wiki` |
| URL | `https://wiki.lan/3d-printing` |
| Icon | `book-open` |
| Open in new tab | так |

### Ticket-система / helpdesk

| Поле | Значення |
|---|---|
| Name | `Print Request` |
| URL | `https://helpdesk.example.com/forms/print-request` |
| Icon | `ticket` |
| Open in new tab | так |

### Grafana / monitoring-дашборд

| Поле | Значення |
|---|---|
| Name | `Farm Metrics` |
| URL | `https://grafana.lan/d/printers` |
| Icon | `chart-line` |
| Open in new tab | так |

Для власного metrics endpoint BamDude див. [Prometheus](prometheus.uk.md).

### OctoPrint / Mainsail (мікс-ферма)

| Поле | Значення |
|---|---|
| Name | `Voron 2.4` |
| URL | `http://192.168.1.50` |
| Icon | `printer` |
| Open in new tab | так |

## :material-backup-restore: Backup і restore

External links — частина стандартної БД BamDude, тож вони їдуть з кожним backup. Див. [Backup](backup.uk.md) для повного протоколу backup/restore.

!!! warning "Custom-іконки НЕ в backup"
    DB-рядки бекапляться; самі файли в `<base_dir>/icons/` не входять у SQLite/PostgreSQL dump. Якщо відновлюєш backup на свіжому хості без копіювання теки `icons/`, рядки виживають, але `<img>`-теги повертають 404, і сайдбар відкочується на Lucide-preset з імені в `icon`. Копіюй `icons/` директорію вручну при міграції хостів.

## :material-shield-key: Permission-и

| Permission | Дефолтні групи |
|---|---|
| `external_links:read` | Administrators, Operators, Viewers |
| `external_links:create` | Administrators, Operators |
| `external_links:update` | Administrators, Operators |
| `external_links:delete` | Administrators, Operators |

`update` покриває reordering, редагування і icon upload/delete (окремого `external_links:edit` немає — permission називається `external_links:update`).

## :material-api: API reference

Усі endpoint-и під `/api/v1/external-links` і вимагають відповідного permission-у, якщо не зазначено інакше.

| Method | Path | Призначення |
|---|---|---|
| `GET` | `/external-links/` | Список усіх посилань, відсортованих за `sort_order`, потім `id`. |
| `POST` | `/external-links/` | Створити посилання. Body: `{name, url, icon, open_in_new_tab, nav_group}`. Якщо `nav_group` опущено, береться `external`. |
| `GET` | `/external-links/{id}` | Отримати одне посилання. |
| `PATCH` | `/external-links/{id}` | Оновити одне або декілька полів. |
| `DELETE` | `/external-links/{id}` | Видалити посилання (і custom-іконку, якщо є). |
| `PUT` | `/external-links/reorder` | Body: `{ids: [...]}`. Перепризначає `sort_order` за позицією у списку. |
| `POST` | `/external-links/{id}/icon` | Multipart upload custom-іконки. |
| `DELETE` | `/external-links/{id}/icon` | Видалити custom-іконку і відкотитися на Lucide-preset. |
| `GET` | `/external-links/{id}/icon` | Повертає файл іконки. **Без авторизації** за дизайном — `<img>` теги не можуть відсилати bearer-токени. |
