---
title: System Info і діагностика
description: Сторінка Інформація — версія, DB stats, storage breakdown, log viewer, debug-logging toggle, support bundle, optimize-DB, rebuild search index, update checker
---

# System Info і діагностика

Сторінка **Інформація** (бокова панель → Інформація, route `/system`) — це адмін-діагностична поверхня BamDude — version metadata, DB row counts, storage breakdown, log viewer, debug-logging toggle, support bundle generator і кнопки maintenance (optimize DB, rebuild search index, check for updates).

## :material-information: Що це

Read-only дашборд, що тягне з `GET /api/v1/system/info` (більшість сторінки), `GET /api/v1/system/storage-usage` (storage breakdown) і `GET /api/v1/support/logs` (log viewer). Maintenance-actions — POST endpoint-и за відповідними permission-ами. Стан повідомляє локальна інсталяція; зовнішня metrics-БД не потрібна (для цього див. [Prometheus](prometheus.uk.md)).

Сторінка також окремо показує стан локальних сервісів прев’ю, камер і аналізу
витрати філаменту з 3MF. Збій камер впливає на камерні функції, збій аналізу —
на нові прогнози витрати; друк і черги, не залежні від камерної перевірки,
працюють далі. Завдання з обов’язковою перевіркою може чекати на камеру.
Аналізатор читає 3MF
з архіву локально й передає через вбудований брокер лише обмежений результат,
а не весь файл до віддаленого сервісу. Уже обчислений контекст зберігається
до завершення відповідного друку.

**Воркер файлів бібліотеки** готує завантажені й підключені файли та метадані плит 3MF. Його відмова перешкоджає підготовці нових файлів і скануванню тек; наявні файли доступні. Перевірте цю панель, якщо журнал завантаження чи сканування містить `library file service unavailable`.

**Воркер мініатюр деталей** (після 0.7.0) рендерить [зображення деталей](projects.md#part-pictures). Його панель показує **Доступний**, **Лише запасні методи** (для цієї машини немає офіційної збірки Node.js) чи **Недоступний**; причину реченням із кодом поруч; закріплену версію Node.js і її дату; чергу — скільки плит чекає і скільки з помилкою; результат і час останньої спроби. Коли воркер недоступний, панель веде на [його діагностику](../reference/troubleshooting.md#part-thumbnail-worker). Збій зупиняє лише нові картинки: вироби, замовлення й склад працюють, а плити, що чекають, не рахуються невдалими.

Рядок **Компонент прев’ю STEP** (після 0.7.0) у тій самій секції прев’ю показує компонент, що створює [мініатюри STEP](file-manager.uk.md#step-thumbnails): вибір адміністратора — **Увімкнено адміністратором: оновлення підтримують його актуальним**, **Вимкнено адміністратором: оновлення його не чіпають** або **Вибір ще не зроблено** — і стан самого компонента — **Встановлено**, **Не встановлено**, **Недоступний для цієї машини**, **Стан невідомий** або **Непридатний (причина)**. *Встановлено* — не те саме, що «працює»: що він справді рендерить, перевіряє лише `install/step-preview.sh status`, запущений на сервері. На нативній інсталяції рядок показує ще й дві команди — **Щоб встановити або відновити його, виконайте на сервері:** `install/step-preview.sh enable` та **Щоб перевірити, що він рендерить:** `install/step-preview.sh status`; Docker та інсталятор Windows несуть компонент із собою і показують лише його стан. Див. [Встановлення → Прев’ю STEP](../getting-started/installation.uk.md#step-previews) і [Вирішення проблем → Мініатюри STEP](../reference/troubleshooting.uk.md#step-thumbnails).

Стан БД показано окремо від воркерів. Після 0.7.0 невдала SQL-перевірка більше не зриває інші: без `pg_stat_statements` лишається попередження про статистику, але версія, розмір та інші доступні поля читаються. У [посібнику PostgreSQL](postgresql.md) описано ввімкнення розширення; саме оновлення BamDude не налаштовує сторонній сервер PostgreSQL.

## :material-tag-outline: Version info

| Поле | Source |
|---|---|
| `version` | `APP_VERSION` з `backend/app/core/config.py`, ставиться при build-time через `node scripts/set_version.js`. |
| `python_version` | Версія Python interpreter running-процесу. |
| Database engine + version | `SHOW server_version` на PostgreSQL, `SELECT sqlite_version()` на SQLite. |
| `platform` / `architecture` / `hostname` | З Python-модуля `platform`. |
| `boot_time` / `uptime` | System boot time з `psutil`, форматоване в `Nd Nh Nm`. |

Build date і git SHA через цей endpoint не експонуються — release-білди печуть version string при `set_version.js` time, це канонічний ідентифікатор. Node version теж не репортиться; React-bundle шипиться pre-built під `static/`.

## :material-database: Database stats

`GET /api/v1/system/info` агрегує row counts і кілька sum-ів:

| Stat | Що рахує |
|---|---|
| `archives` | Загальна кількість рядків `print_archives`. |
| `archives_completed` / `archives_failed` / `archives_printing` | Те саме, partition за status. |
| `printers` | Усі зареєстровані принтери. |
| `spools` | Усі spool-records (live inventory rows). |
| `projects` | Усі projects. |
| `smart_plugs` | Усі зареєстровані smart-plug-и. |
| `total_print_time_seconds` / `_formatted` | Сума `print_time_seconds` крізь усі архіви. |
| `total_filament_grams` / `_kg` | Сума `filament_used_grams`. |
| `database.size` (під `storage`) | Розмір файлу `bambuddy.db` або PostgreSQL DB size, якщо PG. |
| `archive_size_bytes` / `_formatted` (під `storage`) | Загальний розмір теки архіву. Обходиться в робочому потоці — ніколи не в головному циклі сервера — один раз для всіх відкритих сторінок і використовується повторно до 60 с. |

## :material-harddisk: Storage usage breakdown

`GET /api/v1/system/storage-usage` ходить по data-директоріях і класифікує кожен файл в один з buckets, повертаючи size + percentage of total:

| Bucket | Roots |
|---|---|
| `database` | `bambuddy.db` (і legacy `bambutrack.db`, якщо є). |
| `library_thumbnails` / `library_files` / `library_other` | `<data_dir>/library/...`. |
| `archive_files` / `archive_thumbnails` / `archive_timelapses` | Сама archive-директорія. |
| `virtual_printer_uploads` / `virtual_printer_upload_cache` / `virtual_printer_certs` / `virtual_printer_other` | `<base_dir>/virtual_printer/...`. |
| `downloads` | `<base_dir>/firmware/`. |
| `attachments` | `<data_dir>/projects/` і `<data_dir>/products/` — вкладення замовлень і виробів. |
| `plate_calibration` | Директорія plate-detection reference image. |
| `logs` | Сконфігурована log-директорія. |
| `other_data` | Все під data-теками, що не зматчилось правилом, з per-bucket sub-breakdown, що відрізняє `system` (deletable=false) від `data` (deletable=true). |

Scan кешується на 5 хвилин (`STORAGE_USAGE_CACHE_SECONDS = 300`). Передай `?refresh=true`, щоб форсити re-scan; передай `max_age_seconds=N` (clamped 0–3600), щоб override-нути cache TTL.

!!! tip "Дивись перед backup-ом"
    Окидаючи поглядом breakdown перед backup, бачиш — чи archive-тека є домінантною часткою (зазвичай так), і чи є headroom тримати timelapse-и, чи прунити їх спочатку.

## :material-memory: Resource usage

| Stat | Source |
|---|---|
| CPU count + percent | `psutil.cpu_count()` / `psutil.cpu_percent(interval=0.1)`. |
| Memory total / available / used / percent | `psutil.virtual_memory()`. |
| Disk total / used / free / percent | `psutil.disk_usage(base_dir)`. |
| `connected_printers` | Live MQTT-connected принтери з `printer_manager`. |

Значення — point-in-time — refresh сторінки re-семплить їх (розмір архіву вище може бути до хвилини давнім). Вибірка CPU теж знімається поза головним циклом. Historical rollup тут немає. Для time-series скрейпай [Prometheus](prometheus.uk.md).

## :material-text-box-search: Log viewer

`GET /api/v1/support/logs` тейлить `<log_dir>/bamdude.log`, парсить кожен рядок у структурований entry, і повертає найсвіжіші entry-ї першими.

| Param | Замітки |
|---|---|
| `limit` | 1–1000, default 200. |
| `level` | `DEBUG`, `INFO`, `WARNING` або `ERROR`. Case-insensitive. |
| `search` | Substring-match по message body і logger name. Case-insensitive. |

Multi-line entry-ї (особливо stack traces) пересобираються — continuation-рядок прикріплюється до next-parsed entry над ним.

| Дія | Endpoint | Permission |
|---|---|---|
| List recent logs | `GET /api/v1/support/logs` | `settings:read` |
| Truncate log-файл | `DELETE /api/v1/support/logs` | `settings:update` |
| Toggle DEBUG-level logging | `POST /api/v1/support/debug-logging` | `settings:update` |

!!! note "DEBUG-level logging gated"
    Helper `_apply_log_level` пінить `httpcore` і `httpx` на WARNING навіть у DEBUG mode — full request URL logging would leak bearer-токени в Discord / generic-webhook URL-ах. `paho.mqtt` перемикається на DEBUG, коли toggle on — там і живе більшість корисного printer-protocol detail.

### Ротація + retention логів

Активний файл `bamdude.log` ротується під час першого запису після опівночі за локальним часом сервера. Архіви — звичайні текстові файли `bamdude-YYYY-MM-DD.log`. Перезапуск посеред дня не запускає ротацію примусово.

У **Системній інформації → Файли логів** першим показано `bamdude.log` із позначкою **Поточний**, розміром, часом зміни й кнопкою **Завантажити**. Він доступний, навіть якщо добових архівів ще немає. Завантажується повний файл станом на початок копіювання; запис логів триває. Перезапуск і ввімкнення DEBUG не потрібні, обмеження на хвіст логу з support bundle тут немає. Розмір у списку оновлюється кнопкою **Оновити** й може відрізнятися від пізнішого завантаження через нові записи.

Далі йдуть добові архіви, від найновішого, з кнопками **Завантажити** та **Видалити** з підтвердженням другим кліком. У поточного рядка кнопки видалення немає; наявна дія **Обрізати** у переглядачі логу залишається окремо.

Завантаження поточного логу використовує `GET /api/v1/support/logs/download` і потребує `settings:read`. Віддається необроблений текст, як і для архівів. Бекенд копіює знімок обмеженого розміру в робочому потоці, закриває активний файл до передачі мережею та видаляє тимчасову копію після передачі або обриву з'єднання. Якщо лог очистили під час копіювання, повторіть завантаження.

`log_retention_days` за замовчуванням — **7** (діапазон 1–365). Оператори з `settings:update` можуть змінити його в налаштуваннях. Новий ліміт одразу застосовується до хендлера, а зайві архіви видаляються під час наступної успішної ротації; саме збереження налаштування їх не видаляє.

## :material-lifebuoy: Support bundle

`GET /api/v1/support/bundle` створює ZIP-файл з:

| Файл | Вміст |
|---|---|
| `support-info.json` | Version, OS info, DB row counts, sanitised printer/integration info, anonymized settings, dependency versions, log-file size, network interfaces з masked subnets, WebSocket connection count, Docker memory limit (якщо containerised) — **і сам процес BamDude**, див. нижче. |
| `bamdude.log` | Tail `bamdude.log`, sanitised. |

Bundle вимагає, щоб **debug logging був наразі ввімкнений** — endpoint відмовляється генерувати інакше (`400 Debug logging must be enabled before generating a support bundle`). Workflow:

1. Settings → System → перемкни DEBUG logging on.
2. Відтвори issue.
3. Згенеруй bundle.
4. Перемкни DEBUG logging back off (інакше залишається on — стан персистить у `Settings`-таблиці і re-apply при рестарті).

### Сам процес BamDude

Раніше бандл описував машину, базу, принтери й налаштування — усе, крім процесу, який власне працює. Тож звіт «пам'ять росте днями, поки його не вб'ють» приходив без нічого, з чим можна працювати: числа, які вказують на причину, існують лише **поки це відбувається**, а на момент запитання контейнер уже перезапущено.

Тепер бандли несуть:

| Поле | Чому важливо |
|---|---|
| **Пам'ять у користуванні проти зарезервованої** | Різниця між цими двома й відрізняє справжній витік від нешкідливого адресного простору |
| **Кількість потоків і дочірніх процесів** | Зростання кількості потоків — це інший баг, ніж зростання купи |
| **Відкриті файли й сокети** | Витік дескрипторів ззовні виглядає як витік пам'яті |
| **Uptime** | Дає масштаб усім іншим числам |
| **Розбивка того, чим заповнена пам'ять** | Вказує, *яке саме* виділення росте |

!!! note "На вже дуже великому процесі розбивка пропускається — і про це сказано"
    Генерація бандла для діагностики некерованого росту пам'яті не має стати тим,
    що добиває машину.

    **Дочірні процеси записуються лише за іменем, ніколи за командним рядком** —
    у командному рядку `ffmpeg` лежить пароль камери.

Це потрапляє і в бандл, який ти завантажуєш, і в пакет, доданий до [звіту про баг](bug-report.md).

### Sanitisation

`_sanitize_log_content` і `_collect_support_info` працюють разом, щоб тримати secret-и зовні:

- Printer names → `[PRINTER]`, serial numbers → `[SERIAL]`, IP addresses → `[IP]`, access codes → `[ACCESS_CODE]`, usernames → `[USER]`, email-и → `[EMAIL]`.
- URL credentials (`http://user:pass@host`, `rtsps://bblp:code@host`) → `[CREDENTIALS]@`.
- LDAP Distinguished Name-и → `[DN]`. Провідний `CN=` у DN — це справжнє ім'я користувача, тож поводимось із ним як з email. На відміну від решти списку, DN не візьмеш із БД — він per-user і приходить із твого каталогу — тому ловиться **за формою**: два або більше `attr=value`-компонентів через кому. Тобто `CN=Joe Schmoe,OU=Staff,DC=example,DC=com` прибирається всюди, де трапиться, включно з текстом помилки від бібліотеки каталогу. Одинокий `key=value` у сторонньому рядку не чіпається.
- Path-компоненти типу `/home/<user>/`, `/Users/<user>/`, `/opt/<user>/` колапсуються в `/home/[user]/` тощо.
- MQTT relay broker → masked: bare IP стає `[IP]`, hostname стає `*.tld`.
- Subnets в network info → перші два октети стають `x.x` (тож `192.168.1.0/24` → `x.x.1.0/24`).
- Settings values — ключі, що містять будь-яке з `access_code`, `password`, `token`, `secret`, `api_key`, `cloud_token`, `mqtt_password`, `email`, `username`, `vapid`, `private_key`, `public_key`, `webhook`, `url`, `path`, `config`, `_ip`, `host`, `credential` редактяться у `[REDACTED]` (або `""` якщо порожнє). Будь-які інші settings passthrough as-is, тож feature flags і themes видно в bundle.

Bundle — правильна штука, щоб приклеїти до [GitHub-issue](https://github.com/kainpl/bamdude/issues) при репорті бага.

## :material-tools: Maintenance actions

| Дія | Endpoint | Permission |
|---|---|---|
| **Optimize / vacuum SQLite** — виконує `ANALYZE`, `PRAGMA wal_checkpoint(TRUNCATE)`, потім `VACUUM` | `POST /api/v1/settings/optimize-db` | `settings:backup` |
| **Rebuild archive search index** — див. [Search](search.uk.md) | `POST /api/v1/archives/search/rebuild-index` | `archives:update_all` |
| **Check for updates** — див. [Updates](#update-checker) нижче | `GET /api/v1/updates/check` | `system:read` |

**Окремої "Clear Cache" кнопки** на BamDude System-сторінці немає — page-level кеші (storage breakdown, system info) автоекспайряться самі; єдиний manual flush — `?refresh=true` query-param на `/system/storage-usage`.

**"Restart application" кнопки** теж немає — upstream Bambuddy-концепт in-app restart має сенс тільки для bare-metal/systemd-інсталів, а target-deployment BamDude — Docker. Рестартуй контейнер через `docker compose restart bamdude` (або що там в твоєму orchestrator-і).

## :material-update: Update checker

`GET /api/v1/updates/check` poll-ить GitHub Releases і порівнює latest-tag до `APP_VERSION`. Два setting keys кермують поведінкою:

| Setting key | Ефект |
|---|---|
| `check_updates` (default `true`) | Коли `false`, endpoint повертає `{update_available: false, message: "Update checks are disabled"}` без походу на GitHub. |
| `include_beta_updates` (default `false`) | Коли `true`, prerelease-и (`X.Y.ZbN`) — eligible matches. Коли `false`, тільки stable-релізи. Detection — dual-signal: реліз вважається prerelease якщо тег матчить `bN`/`betaN`/`alphaN`/`rcN` **АБО** якщо marked-prerelease у GitHub UI. |

Check-response несе `is_prerelease`, `is_docker`, `latest_version` — UI рендерить правильні install-команди per-channel + per-install-shape.

### In-app apply (native-інстали)

`POST /api/v1/updates/apply` робить фактичний git checkout + dependency install. Поведінка з **0.4.4**:

- Приймає опційний `tag_name` body field — frontend передає те, що тільки що отримав з `/check`, щоб apply ударив exact-реліз який юзер бачив.
- Резолвить у `vX.Y.Z[bN]` git-ref через `_resolve_git_ref()` (працює і з `v`-prefixed і з bare формами).
- Виконує `git fetch origin --tags --prune --force` потім `git reset --hard refs/tags/<ref>`. Працює для **будь-якого tag незалежно від гілки** — pre-fix хардкодив `git reset --hard origin/main`, що тихо no-op'ило бета-інстали (бо бета-теги на `dev`, не `main`).
- Встановлює Python-deps (`pip install -r requirements.txt`) і ребілдить frontend-бандл (`npm install && npm run build`) коли npm доступний.

Endpoint потребує `settings:update`. Запуск з **Settings → System → Install Update** коли update показано як available.

### Docker-інстали

Docker-інсталам `/apply` відмовляє з `is_docker: True` — запуск `git fetch` / `pip install` / `npm build` всередині запущеного контейнера зіпсує image. Замість того UI surface-ить дві бокові секції з конкретними командами що використовують resolved `latest_version` + `is_prerelease`:

**Image-based (типове)** — більшість операторів запускає `image: kainpl/bamdude:<tag>` у compose-файлі:

```yaml
# docker-compose.yml
image: kainpl/bamdude:0.4.5b1     # для бет — явний пін обов'язковий
# АБО
image: kainpl/bamdude:latest      # останній стабільний релізний тег
```

```bash
docker compose pull && docker compose up -d
```

Підказка пояснює, чому `:latest` не підтягне бету: стабільний релізний тег оновлює `:latest`, а beta-теги публікують `:X.Y.ZbN` і оновлюють `:dev`. Сам push гілки не оновлює жодного релізного каналу.

**Source-build** — для операторів які склонували репо і використовують `build:` у compose:

```bash
git fetch origin --tags --prune --force
git checkout v0.4.5b1
docker compose build --pull
docker compose up -d
```

Це BamDude self-update path. Для **printer firmware** оновлень див. [Firmware Updates](firmware-updates.md) — повністю окремий flow.

## :material-shield-key: Permission-и

| Дія | Permission |
|---|---|
| Дивитись system info, storage usage, update check | `system:read` |
| Дивитись logs, отримати debug-logging state, генерувати support bundle | `settings:read` |
| Toggle debug logging, clear logs | `settings:update` |
| Optimize/vacuum DB, restore backup | `settings:backup` |
| Rebuild archive search index | `archives:update_all` |

`system:maintenance` чи `support_bundle:create` permission-у немає — support bundle і log endpoint-и сидять під namespace `settings`.

## :material-api: API reference

### Діагностика станів друку й відновлення

Блок **«Діагностика станів друку»** показує невирішені розбіжності між блокуваннями черги й архівами виконання. Він читає поточні записи та свіжі спостереження принтера; **«Перевірити повторно»** нічого не змінює. Сама недоступність принтера не доводить завислого друку. Якщо список частковий, перегляньте наступні сторінки.

Оператор спочатку готує адресну правку, переглядає **«Було → стане»** й підтверджує її. За наявності доказів можна узгодити старе завдання із завершеним архівом, зняти завислий заголовок черги або доповнити час завершення за формулою «старт архіву + тривалість зі слайсера». Остання дія потребує явного підтвердження, що архів належить цьому завершеному друку. Час назавжди позначається як **оціночний** і не дає дозволу на видалення.

Кнопка **«Видалити старе завдання, зберегти архів»** з’являється лише для доведеного успішного виконання з фактичним часом завершення, без залежних записів AutoQueue, калібрування, квитанцій чи замовлення. Неоднозначна належність, невирішені наслідки завершення чи зміни столу, невизначений стан принтера прибирають дію повністю. Примусового видалення немає. Архів, облік і файли джерела зберігаються.

Правка неактивного принтера лишає чергу на паузі: перед відновленням перевірте стіл. Доведено старе завдання можна виправити й під час однозначно визначеного нового друку; цей друк та його заголовок черги зберігаються. Панель не надсилає команд принтеру й не повторює облік чи макроси завершення. Якщо стан змінився або перегляд застарів, потрібні нові перегляд і підтвердження. Успішні дії записуються в історію відновлень принтера.

**Перервана відправка.** Якщо BamDude зупинився, поки запускав завдання з черги, завдання та його архів можуть лишатися в стані *друкується*, хоча принтер ніколи не почав його друкувати. Таке завдання ніколи не закривається як надруковане лише тому, що принтер показує завершеним попередній друк того самого файла. Завдання, команду старту якого доведено не надіслано, саме повертається в чергу, щойно принтер повідомить, що він вільний, а нові друки дозволені. Інакше панель показує *Відправку перервано до того, як принтер почав друкувати*. **«Закрити перервану спробу»** доступна лише тоді, коли процес BamDude, якому належала спроба, завершився, принтер вільний і на ньому нічого іншого не друкується, — або коли сам поточний процес BamDude не зміг прочитати відповідь принтера на надісланий старт і перестав за ним стежити (принтер при цьому теж має бути вільний, і до нього не прив'язано нічого, крім цієї спроби). Дія позначає завдання та його архів невдалими й зупиняє чергу цього принтера з помилкою; вона не доводить, що нічого не надрукувалося, тож спершу перевірте принтер і стіл. Щоб надрукувати завдання знову, натисніть на ньому **«Повторити»**, а потім відновіть чергу.

**Завершений друк досі утримується в пам’яті.** *З’єднання* з принтером може бути здоровим, а *стан* принтера в BamDude — ні: окрім архіву й черги, BamDude тримає в пам’яті прогін, на якому, на його думку, зараз принтер. Якщо друк завершився, поки зв’язку не було, перевірка під час повторного підключення закриває його в архіві та черзі, але прогін у пам’яті може лишитися — і тоді кожен наступний запуск на цьому принтері знову й знову відкладається ще до надсилання, хоча й принтер, і його черга виглядають вільними. Панель показує *Завершений друк досі утримується в пам’яті* («Принтер вільний. Архів №123 завершений, але його контекст лишився активним.») і поруч — *Запуск знову й знову відкладається без прогресу*: скільки разів, як довго, яке завдання, і посилання на рядок, що тримає принтер. Рядок з’являється, коли той самий стан побачено двічі з проміжком щонайменше десять секунд.

**«Звільнити завершений контекст»** пропонується лише тоді, коли доведено, що цей прогін закінчився: його архів завершився на цьому принтері й у цій черзі, принтер надсилає свіжий стан «вільний», жоден запуск, завершення, макрос, дія розумної розетки, завантаження файла чи охолодження столу його більше не використовує, заміна столу за ним не лишилася винною, і нічого новішого не почалося. Інакше рядок називає, що його тримає, і кнопки не показує. Звільнення спершу ставить чергу принтера на паузу, а потім прибирає з пам’яті лише цей прогін, записаний для нього старт, а також вибір макросів і конфігурацію заміни столу, які зареєструвала його відправка, — архів, облік і статус черги не змінюються, принтеру нічого не надсилається, а перевірка очищення столу лишається як була. Це **не** підтвердження чистого столу: перевірте принтер і стіл, а потім самі натисніть **«Відновити чергу»**; наступний прохід запустить завдання, що чекає, звичайним шляхом. Якщо пауза вже була, перегляд про це скаже, і «Відновити» зніме її теж.

Діалог лишається відкритим на результаті й показує його як є: *звільнено*; *не змінено* — принтер або його контекст змінився після перегляду, черга лишається на паузі, нових запусків під паузою не буде, але вже розпочату спробу ремонт не скасовує; або *не записано* — перш ніж робити щось іще, перевірте історію відновлень принтера. Історія показує кожен такий ремонт одним записом із результатом або каже, що результат невідомий чи що процес завершився до підтвердженого результату.

**Залишковий преднагрів.** Запуск, відхилений уже після преднагріву, може лишити запит на нагрів. Рядок називає його поруч зі свіжими показами столу й камери або каже, що вони невідомі. Він не блокує звільнення, а ні звільнення, ні пауза нагрівачі не вимикають — скористайтеся засобами керування принтера.

**Стан системи.** Розділ **«Стан системи»** згадує, скільки проблем зі станом друку зараз бачить фонова перевірка й на скількох принтерах, і веде до цих рядків; сам він ремонту не пропонує. Перевірка, яка не вдалася або ще не обійшла всі принтери, каже про це, а не виглядає здоровою. Пакет підтримки містить те саме обмежене прочитання, лише для принтерів, доступних ключу, що його запитує. Зберіть його **до** перезапуску BamDude: перезапуск стирає стан у пам’яті, який пояснює зупинку.

Читання потребує `system:read`, `printers:read`, `queue:read_all` та `archives:read_all`. Для правок додатково потрібні `queue:update_all` і `printers:control`; для оцінки завершення — також `archives:update_all`, для видалення — `queue:delete_all`. Для звільнення завершеного контексту, окрім читання, достатньо `queue:update_all` — принтеру воно нічого не надсилає. Обмеження API-ключа за принтерами діють на список, кожну дію та згадку в «Стані системи».

```
GET  /api/v1/system/print-state-issues
POST /api/v1/system/printers/{printer_id}/print-state/preview
POST /api/v1/system/printers/{printer_id}/print-state/apply
GET  /api/v1/system/printers/{printer_id}/print-state/history
```

```
GET    /api/v1/system/info             # full system snapshot
GET    /api/v1/system/storage-usage    # bucketed storage breakdown
GET    /health                         # unauthenticated liveness probe ({"status":"healthy"})
GET    /api/v1/support/logs            # tail bamdude.log
DELETE /api/v1/support/logs            # truncate log-файл
GET    /api/v1/support/debug-logging   # поточний debug-logging state
POST   /api/v1/support/debug-logging   # toggle debug logging
GET    /api/v1/support/bundle          # download support ZIP
POST   /api/v1/settings/optimize-db    # ANALYZE + WAL checkpoint + VACUUM
POST   /api/v1/archives/search/rebuild-index  # rebuild FTS index
GET    /api/v1/updates/version         # current version (unauthenticated)
GET    /api/v1/updates/check           # check GitHub for newer release
```

Unauthenticated `/health` whitelist-нутий setup-gate middleware-ом, тож скрейпай його ще до того, як initial setup completes.
