---
title: Проєкти та print plan
description: Групуй друки в проєкти зі впорядкованим print plan, BOM-обліком та експортом у ZIP / JSON
---

# Проєкти та print plan

Проєкти — спосіб згрупувати набір зв'язаних друків: модель з кількома частинами, невелика партія, яку ти регулярно перезапускаєш для клієнтів, інвентар запасних частин. Кожен проєкт несе:

- **Впорядкований print plan** з `.gcode.3mf` файлів бібліотеки
- **Stepper копій** на файл (скільки запустити)
- **Per-row підсумки** (вага пластика, час, енергія, ціна) і grand-total на проєкт
- Опційний **BOM** (тип / колір / грами заплановані)
- **Cross-install експорт** як ZIP-bundle або JSON-маніфест

## :material-format-list-checks: Кейси використання

| Проєкт | Що в нього іде |
|---|---|
| **Voron Build** | Frame plates + electronics enclosure + інструменти + запасні wear-частини. Трекай plate progress vs total parts — знаєш коли kit print-complete. |
| **Gift Set** | Кілька неспоріднених друків (ваза + кашпо + брелоки), що йдуть разом на день народження. Юзай cover image + URL на email замовлення. |
| **Customer order** | 10 копій однієї моделі для клієнта. Постав Target Plates × копії на plan-рядку; живий лічильник каже скільки лишилось. |
| **Calibration suite** | Test prints для нового пластика — flow ratio, temp tower, retraction tower. Згрупуй, щоб calibration-архіви не сміттили основний archive list. |
| **Single big print** | Одна модель з одним великим 3MF — все одно корисно як проєкт, щоб cover image, URL і BOM жили поряд з друком. |

---

## :material-folder-multiple: Створення проєкту

1. Відкрий **Projects** в бічному меню.
2. **+ New Project**, дай ім'я, опційно опиши.
3. Save — потрапляєш на сторінку деталей.

Новий проєкт пустий. Додавай файли одним з двох способів:

- **Лінк папки** — обери один або кілька проєктів на папці у File Manager через chip multi-select; усі файли всередині отримують той самий список проєктів, і файли, переміщені пізніше, теж його успадковують.
- **Лінк окремих файлів** — кожен рядок файла у File Manager має кнопку "Link to project", яка відкриває той самий chip multi-select.

Файл бібліотеки (або папка) може належати **кільком проєктам одночасно** — зв'язок many-to-many (m044). Один файл у N проєктах дає N незалежних plan-рядків, кожен зі своїм `copies` і `order_index`. Залінковані файли автоматично з'являються як plan items по 1 копії на проєкт.

Щоб видалити одну прив'язку без зачіпання інших, тисни маленький `×` на потрібному chip-у в діалозі редагування файлу/папки (або кнопку "remove from project" на рядку проєкт-сторінки) — обидва шляхи йдуть через окремий `DELETE /library/{files|folders}/{id}/projects/{project_id}` ендпоінт, тож файл у 3 проєктах можна відв'язати від 1, не торкаючись решти.

## :material-playlist-edit: Print plan

Plan — це плаский впорядкований список. Кожен рядок несе:

| Колонка | Що значить |
|---|---|
| **Sequence** | Порядок друку. Drag-and-drop для перетягування. |
| **File** | Який 3MF з бібліотеки (лінк веде на його картку у File Manager). |
| **Copies** | Скільки копій — bumped стейпером або вписаний руками. |
| **Time** | Час на рядок (slicer-estimate × копії). |
| **Filament** | Грами на копії, розбиті за кольором/матеріалом якщо multi-spool. |
| **Cost** | Ціна пластика × копії плюс ціна енергії якщо є прив'язана розумна розетка. |
| **Printed / Remaining** | Прогрес на рядок: `✓N` показує скільки копій цього файлу завершилось у цьому проєкті (рахуються тільки `status='completed'` — невдалі / aborted / external prints не зменшують); `📋M` показує `max(0, copies − printed)`. Прогрес ключований по `(project_id, library_file_id)`, тому файл у двох проєктах має незалежний прогрес у кожному. |

Grand-totals strip знизу сумує кожен рядок — корисно для "у мене вистачить зеленого PLA на цей проєкт?" перевірки до того, як натиснути dispatch.

Три головні плашки нагорі сторінки проєкту (Print Jobs / Print Time / Filament Used) несуть другорядний "remaining" subtitle з тих самих plan-рядків: jobs сумує `remaining_count`, time сумує `print_time_seconds × remaining_count`, filament сумує `filament_grams × remaining_count`. Subtitle **зелений** коли план повністю виконано (`всі надруковано`) і **амбер** інакше — оператор бачить одним поглядом, чи лишилась робота.

## :material-link-variant: Зовнішній URL і обкладинка

До кожного проєкту можна прикріпити зовнішній URL і hero-обкладинку — обидва світяться на картці проєкту і на детальній сторінці, тож одного погляду досить, щоб упізнати "ах, той проєкт з полицею для ракет", замість витрішкуватись на стандартну іконку папки.

| Поле | Примітки |
|---|---|
| **URL** | Вільний `http://` чи `https://` лінк, до 2 048 символів. Валідація на save (все, що не починається з `http(s)://`, відхиляється inline). Edit-with-cleared-value відсилає `null`, тож колонка реально чиститься. Світиться як клікабельна іконка `↗` поряд з ім'ям проєкту на картках і детальці. |
| **Cover image** | Прев'ю 80 × 80 в модалці проєкту, повний розмір на детальці в hero-стрічці + thumbnail-стрічка на сітці карток. Приймає `.jpg / .jpeg / .png / .gif / .webp`. **Тільки в edit-mode**: новостворений проєкт ще не має `project_id`, тож upload-віджет з'являється після першого збереження (відповідає upstream-формі). Cache-busted preview URL оновлюється при upload/remove без hard-refresh. |

Типове застосування: вставив посилання на MakerWorld / Printables / Thingiverse, з якого взяв модель, у URL, дропнув фото зібраного виробу в Cover. Майбутній-ти подякує теперішньому-собі, повертаючись до проєкту через рік.

## :material-target: Target Plates vs Target Parts

Проєкт може нести два незалежні progress-лічильники:

| Target | Що рахує |
|---|---|
| **Target Plates** | Кількість окремих print jobs (кожен раз що клікаєш Print = +1). |
| **Target Parts** | Загальна кількість об'єктів по всіх роботах (плата з 4 копіями кронштейна = 4 parts). |

Постав обидва для multi-plate build, що шипає точну кількість об'єктів — наприклад, Voron BOM може бути 25 plates / 150 parts. Картка проєкту світить dual progress bars:

```
Plates  [████████░░░░░░░░░░] 40%   2 of 5 print jobs
Parts   [████████░░░░░░░░░░] 40%   10 of 25 parts
```

### Pre-fill з print-плану

Не треба додавати числа руками. Два zero-friction шорткати підставляють targets з рядків плану:

- **Edit-модалка** авто-pre-fill-ить порожні поля Target Plates / Target Parts підрахунками плану при відкритті, і показує лінк `From plan: N` під кожним інпутом — клік ресинкає коли план змінився (лінк ховається коли значення вже збігається з плановим).
- **Кнопка `Apply to project`** на рядку summary print-плану + на рядку summary BOM пише Target Plates (= сума копій по платах), Target Parts (= total objects) ТА Budget (= вартість філаменту + вартість матеріалів) у властивості проєкту одним кліком. Tooltip показує точні значення що приземляться до кліку. Кнопка ховається коли проєкт вже збігається по всіх трьох (no-op write avoidance).

Manual edits все одно перемагають — раз ти змінив значення, авто-fill його не перезапише при наступних відкриттях модалки. Використовуй `Apply to project` / `From plan: N` контролки коли переробив план і хочеш щоб числа проєкту слідували.

### Auto-detection з 3MF

При створенні архіву BamDude читає `slice_info.config` з 3MF, рахує non-skipped objects і штампує цей count у колонку `quantity` архіву автоматично. Плата з 4 інстансами кронштейна → archive quantity 4 → project parts +4.

### Manual quantity override

Відкрий архів у edit-mode і виставь **Items printed** на правильне число — зручно коли slicer-конфіг не зійшовся з реальністю (наприклад skip-нув 2 з 4 об'єктів посеред друку). Project parts counter перерахується миттєво.

---

## :material-palette: Кольорове кодування

Кожен проєкт несе колір-badge для візуальної ідентифікації по UI:

- :material-circle:{ style="color: #f44336" } Червоний
- :material-circle:{ style="color: #ff9800" } Оранжевий
- :material-circle:{ style="color: #ffeb3b" } Жовтий
- :material-circle:{ style="color: #4caf50" } Зелений
- :material-circle:{ style="color: #2196f3" } Синій
- :material-circle:{ style="color: #9c27b0" } Фіолетовий
- :material-circle:{ style="color: #607d8b" } Сірий

Badge показується на картці проєкту, на кожній картці архіву залінкованого з проєктом, і як chip-фільтр на Archives-сторінці.

---

## :material-view-dashboard: Картка проєкту

Кожен проєкт відображається як картка з progress + quick stats:

- **Color badge + ім'я** — основний ідентифікатор
- **Cover image thumbnail** strip якщо завантажено cover
- **Plates progress** bar з raw "2 of 5"
- **Parts progress** bar з raw "10 of 25"
- **Print-time elapsed** — сума logged print duration усіх залінкованих архівів
- **Last activity** — timestamp останнього залінкованого архіву
- **File count** — скільки library-файлів залінковано
- **External URL** іконка (якщо виставлено) — клікабельна :material-arrow-top-right:

---

## :material-folder-arrow-down: Додавання архівів до проєктів

На додачу до folder-link / per-file-link auto-population, можна прикріпляти архіви руками:

- **Right-click** на будь-якій картці архіву → **Add to project** → вибери проєкт. Той же жест працює і на рядках archive-list.
- **Bulk assignment** — натисни **Select** на Archives-сторінці (або тримай Shift/Ctrl при кліках), вибери кілька архівів, потім **Project** у нижньому toolbar-і. Та ж модалка має **Remove from project** для bulk-detach.

Project picker на сторінках деталей архівів auto-save-иться при виборі — окремого Save кліка нема.

---

## :material-filter: Фільтр архівів за проєктом

Archives-сторінка має project chip-filter згори. Клік на будь-який чіп звужує grid до архівів того проєкту. Комбінуй з date / printer / status фільтрами для тоншого зрізу.

---

## :material-printer: Друк файлів з проєкту

Якщо проєкт лінкає одну чи більше library-папок, project detail page показує кожен printable-файл inline — без обходу через File Manager.

Кожен plan-рядок отримує дві inline-action кнопки (тільки на `.gcode` і `.gcode.3mf`):

- :material-play: **Print Now** — відкриває print dialog (вибір принтера + AMS mapping + опції) і диспатчить.
- :material-calendar-plus: **Add to Queue** — відкриває schedule dialog щоб додати в чергу.

**Auto-linking.** Друки тригернуті з project detail page авто-привʼязують результуючий архів назад до цього проєкту. Жодного "Assign to project" кроку. Reprints звідусіль інде (Archives / File Manager / прямий лінк) **не** auto-link-нуться — тільки запуск з project-page створює неявну асоціацію.

---

## :material-cart-check: Bill of Materials (BOM)

Кожен проєкт також приймає вільний BOM — записи про типи пластика, кольори і грам-бюджети, що плануються спожити. BOM не auto-deduct-ить з котушок (це робить per-print spool consumption tracking); це planning-aid для "мені треба 480 г чорного PLA + 120 г сірого TPU", щоб порівняти з наявним стоком до того, як коммітишся.

## :material-rocket-launch: Запуск плану

Два шляхи:

| Action | Ефект |
|---|---|
| **Add row to queue** | Шле тільки цей файл (× копії рядка) у чергу принтера. |
| **Dispatch entire plan** | Додає кожен рядок, у порядку, в чергу обраного принтера. Per-row копії стають окремими queue-items, тож можна скасовувати/перевпорядковувати копії після диспатчу. |

Plan items не передиспатчуються автоматично при завершенні архіву — завершення рядка просто збільшує його completed-лічильник. Щоб перезапустити проєкт — dispatch ще раз.

---

## :material-archive-arrow-up: Project archives view

Відкрий будь-який проєкт — потрапиш на detail page. Sub-tab **Archives** показує лише архіви залінковані з цим проєктом — те ж filtering / sorting що й на головній Archives-сторінці, але pre-filtered. Зручно для "покажи мені всі друки з Voron build" без друкування пошуку.

---

## :material-paperclip: File attachments

Проєкт може також нести reference-файли, які не є самим друком — інструкції зі складання, datasheets, фото, parametric source.

| Категорія | Розширення |
|---|---|
| **3D-файли** | `.3mf`, `.stl`, `.step`, `.f3d`, `.scad`, `.obj` |
| **Документи** | `.pdf`, `.md`, `.txt`, `.doc`, `.docx` |
| **Зображення** | `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.svg` |
| **Інше** | `.zip`, `.json`, `.yaml`, `.gcode`, `.cfg` |

Завантажуй drag-drop у секцію Attachments на сторінці деталей проєкту, або клік **Upload** щоб вибрати файл. Attachments зберігаються поряд з проєктом і шипаються в ZIP-експортах.

---

## :material-currency-usd: Cost tracking

Grand-totals strip і per-row Cost колонка обчислюють три категорії:

| Категорія | Джерело |
|---|---|
| **Material** | Вага філаменту × ціна котушки (з Inventory) на залінкований архів. |
| **Energy** | kWh delta з прив'язаної розумної розетки × твій налаштований тариф (Settings → General). |
| **Labor** | Manual hours, які ти логуєш на проєкт (опційно) × твоя налаштована погодинна ставка. |

Material + energy обчислюються автоматично з underlying-архівів. Labor — freeform: впиши скільки годин потратив на post-processing / packaging / shipping, ставку — з project settings.

---

## :material-delete: Видалення проєктів

Натисни trash на картці проєкту і підтверди. Видалення проєкту **не** видаляє архіви чи library-файли залінковані з ним — вони лишаються в основних Archives / Library, просто без project-association.

Якщо хочеш hard cascade ("видали проєкт І кожен архів І кожен library-файл залінкований з ним") — адмін може використати cascade-опцію в delete-модалці. За замовчуванням preserve-archives.

## :material-tray-arrow-down: Експорт та імпорт

Проєкти портабельні між BamDude-інсталяціями.

- **JSON manifest** — маленький файл, списує файли за хешем + print plan + BOM. Корисно для шерингу *рецепта* проєкту. Приймаюча інсталяція має мати ті ж самі `.3mf` файли в бібліотеці (інакше рядки покажуться "missing file").
- **ZIP bundle** — JSON manifest плюс копія кожного referenced 3MF, щоб приймаюча інсталяція могла відтворити проєкт навіть якщо її бібліотека пуста.

Імпорт симетричний: відкрий Projects → Import, кинь файл, вибери: тримати наявні мечі за хешем чи апнути bundled-копії як нові library-файли.

## :material-database: За кулісами

Схема розділяє стан на три таблиці:

- `projects` — name, description, status, color, target counts, notes, attachments, tags, due date, priority, budget, плюс self-FK `parent_id` для sub-проєктів і прапор `is_template`. Проєкти **не** мають `owner_id` — це install-wide об'єкти, гейтовані набором прав `projects:*`, а не власністю.
- `library_file_projects` + `library_folder_projects` (m044) — pivot-таблиці, що пов'язують library-файли / папки з проєктами. Композитний primary key `(file_id, project_id)` / `(folder_id, project_id)` і `ON DELETE CASCADE` на кожному FK. Legacy single-FK колонки `library_files.project_id` і `library_folders.project_id` дроплено в m044; код бібліотеки тепер читає / пише M2M-зв'язок.
- `project_print_plan_items` (m016, переформатовано m044) — впорядкований план, один рядок на `(project_id, library_file_id)` завдяки m044-reshape unique constraint з `(library_file_id)` → `(project_id, library_file_id)`. Колонки: `copies` і `order_index`. Per-row "notes" / "sequence" як колонок немає — sequence це `order_index`, а notes належать самому проєкту.

Усі FK — `ON DELETE CASCADE`. Видалення проєкту прибирає його pivot-рядки + plan-рядки; видалення library-файла прибирає його pivot-рядки + plan-рядки. Архіви, що з файла прийшли, незалежні — `print_archives.library_file_id` має `ON DELETE SET NULL` (m018, окремо), тож per-copy completed-лічильники продовжують трекати навіть після зникнення source-файла.

Per-row completed-counts (`printed_count` / `remaining_count`) обчислюються при читанні одним bulk-запитом `SELECT library_file_id, count(id) FROM print_archives WHERE project_id = ? AND status = 'completed' GROUP BY library_file_id` — без N+1, і reprints / plate-by-plate dispatches / dedup-by-hash всі інкрементять правильний рядок консистентно. Колонка `project_id` на `print_archives` тримає лічильник у межах проєкту, тож файл у двох проєктах отримує два незалежних printed-лічильники.
