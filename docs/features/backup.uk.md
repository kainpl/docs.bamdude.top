---
title: Резервне копіювання та відновлення
description: Ручні ZIP-бекапи, заплановані локальні бекапи та Git-пуш профілів принтерів
---

# Резервне копіювання та відновлення

Три незалежні шляхи захищають вашу інсталяцію: on-demand ZIP з UI, scheduled job на локальний диск, що тримає N останніх знімків, і Git-пуш, що архівує профілі принтерів у GitHub або GitLab.

---

## :material-backup-restore: Що всередині Backup ZIP

On-demand і scheduled локальні бекапи продукують ту саму структуру ZIP. Записи верхнього рівня:

| Запис | Вміст |
|-------|-------|
| `bamdude.db` | Повна база даних, **завжди експортується як portable SQLite** — навіть коли runtime у вас PostgreSQL, дамп проходить через `dump_to_sqlite()`, тож той самий ZIP відновлюється на будь-який backend. |
| `archive/` | Кожна директорія per-print архіву: `.3mf`, мініатюра PNG, plate-N.png і per-archive folder. |
| `virtual_printer/` | Pending-аплоди + working state віртуального принтера. |
| `plate_calibration/` | Reference-кадри + ROI-визначення для plate detection. |
| `icons/` | Кастомні іконки, завантажені для принтерів / проєктів. |
| `projects/` | Вкладення проєктів. |

Виключено за дизайном: `logs/`, кеші, тимчасові файли, bundled frontend (він шипиться в образі / репі). Деякі sensitive поля також фільтруються перед дампом БД — LDAP bind password ніколи не повертається в API responses, а API-ключі зберігаються як one-way хеші.

!!! note "PostgreSQL → SQLite → PostgreSQL"
    Навіть на PostgreSQL runtime `dump_to_sqlite()` нормалізує експорт. Відновлення на свіжій PostgreSQL інсталяції запускає зворотний `import_sqlite_to_postgres()` і пере-створює рядки в живій БД. Той самий ZIP також відновлюється на SQLite-інсталяцію без жодних додаткових кроків.

---

## :material-download: Ручний бекап

1. **Налаштування → Система → Backup & Restore**
2. Натисніть **Create Backup**
3. Браузер качає `bamdude-backup-YYYYMMDD-HHMMSS.zip`

ZIP стримиться з тимчасового файлу, а не буферизується в пам'яті, тож multi-gigabyte бекапи не OOM-ять процес. Тимчасовий файл видаляється автоматично, як тільки response завершується.

API: `GET /api/v1/settings/backup` (потрібно `settings:backup`).

---

## :material-clock-outline: Заплановані локальні бекапи

Налаштовуються в **Налаштування → Система → Local Backup Schedule**. Шедулер тікає раз на хвилину і запускає due-jobs у той самий ZIP-builder, що використовує ручна кнопка, потім обрізає старіші бекапи понад retention limit.

| Налаштування | За замовчуванням | Примітки |
|--------------|------------------|----------|
| `local_backup_enabled` | `false` | Master switch. |
| `local_backup_schedule` | `daily` | `hourly`, `daily` або `weekly`. |
| `local_backup_time` | `03:00` | `HH:MM` для daily/weekly запусків (server-local time). Hourly це поле ігнорує. |
| `local_backup_retention` | `5` | Тримати N останніх бекапів; старіші автоматично обрізаються. Діапазон 1–100. |
| `local_backup_path` | порожньо | Output-директорія. Порожньо = `data/backups/`. |

Сторінка налаштувань показує last-run timestamp + outcome (`success` / `failed`), наступний запланований запуск і список наявних retention-бекапів з розмірами файлів. Ручні запуски "Create Backup" зберігаються в тій самій директорії і враховуються в retention.

Legacy `bambuddy-backup-*.zip` файли (від upstream-інсталяцій) досі лістяться і піддаються відновленню, тож апгрейд не залишає попередні знімки сиротами.

### Коли тека виводу недоступна для запису

BamDude перевіряє теку реальним записом у момент збереження шляху і при відкритті картки бекапів, тож непридатний шлях виявляється одразу, а не о 03:00 протягом тижня. Картка називає причину і дає команду для виправлення з уже підставленим вашим шляхом.

Найчастіше людей ловить **systemd-пісочниця**. Юніт служби постачається з `ProtectSystem=strict`, який монтує все поза `ReadWritePaths=<install> <data> <logs>` лише для читання *всередині власного mount-namespace служби*. NAS-шара, яку ви змонтували самі й у яку пишете зі своєї оболонки, до цих трьох не належить, тож запис падає з `EROFS` («Read-only file system») — що виглядає як проблема прав, але нею не є. На читання це не впливає, тож UI спокійно показує наявні копії з шари, не маючи змоги записати нову.

Надайте службі доступ через drop-in — він до того ж переживає перевстановлення:

```bash
sudo systemctl edit bamdude
```

```ini
[Service]
ReadWritePaths=/mnt/your-nas-share
```

```bash
sudo systemctl restart bamdude
```

Перевстановлення робить резервну копію старого юніта як `bamdude.service.bak-<timestamp>` і переносить додаткові `ReadWritePaths` далі, тож доданий вручну виняток більше не зникає при наступному оновленні.

У Docker збій тихіший: хостовий шлях, який ніколи не був bind-mount'нутий, усе одно доступний для *запису* — запис потрапляє в ефемерний шар контейнера і зникає при наступному `docker compose up`. BamDude порівнює пристрій теки з кореневим і попереджає, показуючи compose-сніпет, який монтує її правильно.

---

## :material-source-branch: Git-бекап (профілі в GitHub / GitLab)

Окремий від ZIP-флоу. **Налаштування → Система → Git Backup** пушить вибрані дані профілів принтерів у GitHub або GitLab репозиторій — корисно для off-site синку профілів, координації multi-host ферми і PR-based історії змін у налаштуваннях принтера.

### :material-cog-outline: Конфігурація

| Налаштування | Примітки |
|--------------|----------|
| Provider | `github`, `gitlab`, `gitea` або `forgejo`. |
| Repository URL | Повний clone URL (HTTPS-форма). |
| Access Token | Personal Access Token. Зберігається зашифрованим at rest. |
| Гілка | Цільова гілка (за замовчуванням `main`). |
| API base URL | Тільки для self-hosted GitLab. |
| Schedule | `hourly` / `daily` / `weekly` або off. |

### :material-account-key: Покрокові гайди по провайдерах

=== ":material-github: GitHub"

    1. **Створи GitHub-репозиторій** (private підходить).
    2. **Згенеруй Personal Access Token (PAT)**:
        - Зайди в [GitHub Personal Access Tokens](https://github.com/settings/tokens){ target="_blank" rel="noopener" }.
        - Натисни **Generate new token** → **Generate new token (classic)**.
        - Обери expiration (`No expiration` рекомендується для unattended scheduled-бекапів).
        - У **Select scopes** відмітьте `repo` (потрібно для репо-доступу і коммітів).
    3. **Налаштуй у BamDude**:
        - **Settings** → **Backup & Restore** → Git Backup.
        - Provider: `github`.
        - Repository URL: наприклад `https://github.com/username/bamdude-backup`.
        - Введи PAT.
        - Натисни **Test Connection**.

    !!! note "Fine-grained tokens"
        Замість classic токенів можна fine-grained. Дай `Read access to Metadata` — `Read and Write access to code` додасться автоматично при створенні.

=== ":material-gitlab: GitLab"

    1. **Створи GitLab-репозиторій** (private OK).
    2. **Згенеруй PAT**:
        - Зайди в [GitLab Personal Access Tokens](https://gitlab.com/-/user_settings/personal_access_tokens){ target="_blank" rel="noopener" }.
        - Натисни **Add new token** (Legacy / classic).
        - У scopes відмітьте `api` (потрібно для репо-доступу і коммітів).
    3. **Налаштуй у BamDude**:
        - Provider: `gitlab`.
        - Для self-hosted GitLab заповни **API base URL**.
        - Repository URL: наприклад `https://gitlab.com/username/bamdude-backup`.
        - Введи PAT.
        - Натисни **Test Connection**.

    !!! note "Project Access Tokens"
        Project Access Tokens теж працюють — дай scope `api` і `write_repository`, інакше комміти впадуть з access errors.

=== ":material-git: Gitea"

    1. **Створи репо** (private OK).
    2. **Згенеруй PAT**:
        - **Settings** → **Applications** у профілі Gitea.
        - Під **Access Tokens** дай ім'я.
        - Scope `All (public, private, and limited)`.
        - У **repository** permissions постав `Read and write`.
        - Натисни **Generate token**.
    3. **Налаштуй у BamDude**:
        - Provider: `gitea`.
        - Repository URL: наприклад `https://gitea.example.com/username/bamdude-backup` (URL-валідатор приймає `http://` теж — для self-hosted локальних інстансів на тій же формі).
        - Вкажи правильну **Branch** (`main`, `master`, тощо).
        - Введи PAT.
        - Натисни **Test Connection**.

    !!! note "Розбіжності API Gitea від GitHub (обробляються внутрішньо)"
        `GiteaBackend` BamDude перекриває три GitHub-несумісні форми відповідей, які Gitea ввела з часом: list-shape `GET /git/refs/heads/{branch}` (один матч все одно повертає масив), refusal Git Data API на пустий репо (кожен blob POST 404 поки немає коміта — bootstrap йде через Contents API в одній транзакції), і wrapped Commit schema у Gitea 1.24+ (`commit.tree.sha` замість плоского `tree.sha` GitHub'а). Все прозоро для оператора — згадано тут лише як референс для self-hosted деплоїв з зазначенням сумісних версій (1.18+ і 1.24+ перевірені).

=== ":material-git: Forgejo"

    1. **Створи репо** (private OK).
    2. **Згенеруй PAT**:
        - **Settings** → **Applications** у профілі Forgejo.
        - Під **Manage Access Tokens** дай ім'я токена.
        - Натисни **Generate Token**.
    3. **Налаштуй у BamDude**:
        - Provider: `forgejo`.
        - Repository URL: наприклад `https://forgejo.example.com/username/bamdude-backup` (плоска `http://` теж приймається для локальних інстансів на тій же формі).
        - Введи PAT.
        - Натисни **Test Connection**.

    !!! note "API-сумісний з Gitea"
        API Forgejo наразі `/api/v1`-сумісний з Gitea, і `ForgejoBackend` BamDude успадковує всю поведінку `GiteaBackend`. Якщо два проєкти розійдуться у майбутніх релізах Forgejo, override-by-override патчі в `forgejo.py` з'являться тут.

!!! warning "Bambu Cloud login обов'язковий для K-profiles + Cloud profiles"
    Для бекапу *Cloud profiles* і *K-profiles* потрібен активний Bambu Cloud login. Авторизуйся через **Profiles → Cloud Profiles** перед тим, як планувати Git-бекап з цими категоріями — інакше відповідні директорії будуть пусті в репо.

### :material-checkbox-marked: Що пушиться

Перемикається незалежно. Дефолти налаштовані так, щоб "бекапити те, що більшості потрібно, шумне/велике лишити вимкненим":

| Категорія | Опис | Дефолт |
|-----------|------|:------:|
| **K-profiles** | Per-printer pressure-advance профілі (за серійниками). | :material-check: On |
| **Cloud profiles** | Filament, printer, process профілі з Bambu Cloud. | :material-check: On |
| **Spools** | Повний дамп інвентаря (ряди + usage history). | :material-check: On |
| **Archives (метадані)** | Метадані історії друку — філамент, температури, час, вартість, енергія (без 3MF / без мініатюр). | :material-check: On |
| **App settings** | Таблиця application settings (sensitive поля виключені). | :material-close: Off |
| **Archives (3MF + мініатюри)** | Bulk 3MF + thumbnail-вміст — додає ~50–500 МБ репо на 100 друків. | :material-close: Off |

Тільки змінені файли генерують комміти — no-op запуск пишеться як `skipped`.

### :material-folder-tree: Структура репозиторію

Після успішного запуску репо має такий вигляд:

```
repo/
├── backup_metadata.json
├── kprofiles/
│   └── {serial_number}/
│       ├── 0.2.json
│       ├── 0.4.json
│       └── ...
├── cloud_profiles/
│   ├── filament.json
│   ├── printer.json
│   └── process.json
├── settings/
│   └── app_settings.json
├── spools/
│   ├── inventory.json
│   └── usage_history.json
└── archives/
    └── print_history.json
```

Плоска структура робить partial restore однозначним — можна витягнути лише `kprofiles/{serial}/` для одного принтера або лише `spools/inventory.json` для відновлення інвентаря, не чіпаючи решти.

### :material-monitor-dashboard: Панель статусу

Сторінка налаштувань показує live-статус:

- **Last backup** — timestamp, статус (`success` / `failed` / `skipped`), commit SHA і повідомлення.
- **Next scheduled run** — коли шедулер фаєрне далі.
- **Log table** — історичні запуски з тригером (`manual` / `scheduled`), тривалістю і будь-яким error message.
- **Run Now** — кнопка миттєвого пушу незалежно від розкладу.

Frequency пушу, content-чекбокси і креденшали редагуються наживо без рестарту BamDude.

---

## :material-upload: Відновлення з Backup ZIP

1. **Зупиніть BamDude** перед відновленням (інакше upload нижче замінить файли під запущеним процесом — ризиково).
2. Або киньте ZIP у data-директорію і дайте BamDude задетектити його при наступному boot, або скористайтесь **Налаштування → Система → Restore** і завантажте через форму.
3. На boot / submit форми BamDude:
   - Розпаковує ZIP у temp-dir
   - Закриває поточні DB-конекшени
   - Замінює базу (`bamdude.db` import на SQLite, `import_sqlite_to_postgres` на PG)
   - Замінює `archive/`, `virtual_printer/`, `plate_calibration/`, `icons/`, `projects/`
   - Re-ініціалізує базу (запускає pending міграції на відновлених даних)
   - Видаляє source ZIP після успіху

!!! danger "Restore замінює поточний стан"
    Restore перезаписує живу БД і перелічені вище data-директорії. **Зробіть свіжий бекап поточного стану перед цим**, якщо може знадобитися відкатити сам restore.

API: `POST /api/v1/settings/restore` (multipart `file=…`, потрібно `settings:restore`).

### :material-database-arrow-right: Cross-backend restore

Portable SQLite-дамп означає, що ви можете:

- Зробити бекап з **SQLite** інсталяції → відновити на **PostgreSQL** (loader мігрує рядки).
- Зробити бекап з **PostgreSQL** інсталяції → відновити на **SQLite** (БД уже експортовано як SQLite).
- Зробити бекап з PG → відновити на свіжий PG (loader реімпортує SQLite у PG).

Конфліктні primary keys мерджаться або скіпаються per-row залежно від таблиці — referential integrity зберігається через міграцію.

---

## :material-folder-download: Bulk archive export

3MF-файли і мініатюри не входять у дефолтний layout Backup ZIP (вони в `archive/` лише при explicit opt-in). Для цільового експорту архівів:

1. Зайди в **Archives**.
2. Натисни **Export**.
3. У модалі експорту відмітьте **Include 3MF files**.
4. Опційно звузьте по даті, принтеру або статусу.
5. Завантаж результуючий ZIP.

Корисно для hand-off на іншу ферму, archival у cold storage або одноразової міграції без перетягування повної бази.

---

## :material-database-export: Ручний бекап SQLite / PostgreSQL

Якщо хочеш CLI / scripted-бекап поза UI BamDude — наприклад, для включення в системний бекап ширше або PostgreSQL-specific point-in-time recovery — йди прямо в DB-движок:

=== ":material-database: SQLite (default)"

    Спершу зупини BamDude для consistent-снімку, далі:

    ```bash
    # Plain copy (найшвидше)
    cp /path/to/bamdude.db bamdude_$(date +%Y%m%d).db

    # SQL-дамп (portable між версіями)
    sqlite3 /path/to/bamdude.db ".dump" > bamdude.sql

    # Restore з SQL-дампа
    sqlite3 new_bamdude.db < bamdude.sql
    ```

=== ":material-elephant: PostgreSQL"

    Підключайся через свій `DATABASE_URL`:

    ```bash
    # Custom-format dump (рекомендую — підтримує parallel restore + selective restore)
    pg_dump -Fc bamdude > bamdude.backup
    # або з explicit DSN:
    pg_dump -Fc "postgresql://user:pass@host:5432/bamdude" > bamdude.backup

    # Restore (drop + recreate об'єктів при імпорті)
    pg_restore -d bamdude bamdude.backup
    # або з explicit DSN:
    pg_restore --clean --if-exists \
        -d "postgresql://user:pass@host:5432/bamdude" bamdude.backup
    ```

    !!! tip "Built-in бекап BamDude простіше"
        Сторінка Settings → Backup продукує portable-бекапи, що працюють і на SQLite, і на PostgreSQL. Ручний `pg_dump` потрібен лише коли хочеш PG-specific фічі типу point-in-time recovery, logical-replication snapshotting або інтеграцію з існуючим PG backup pipeline.

!!! warning "Зупини BamDude перед raw file copy"
    Прямий `cp` `bamdude.db` під час роботи BamDude може схопити inconsistent WAL-стан. Portable Settings → Backup безпечно це обробляє — ручний копіпейст потребує зупиненого процесу.

---

## :material-restore: Сценарії відновлення

Три типові форми, що приймає recovery-flow:

### Втрачена база

DB пошкоджена, видалена, не recoverable:

1. Зупини BamDude.
2. Видали пошкоджений `bamdude.db` (або drop PostgreSQL базу).
3. Стартуй BamDude — він створить свіжу пусту DB при першому boot.
4. **Settings → System → Restore** → завантаж останній backup ZIP.
5. BamDude замінить пусту DB відновленою і запустить pending міграції.

### Нова інсталяція

Переїзд на новий сервер / новий Docker-хост:

1. Інсталюй BamDude на новому хості (Docker compose, bare metal, як заведено).
2. Бутни раз, щоб data-директорія створилася і setup-gate висів на `setup_required`.
3. Скопіюй backup ZIP на новий хост.
4. **Settings → System → Restore** → завантаж ZIP — зауваж, що setup-gate whitelist'ить `/restore`-style flow коли ще нема адміна, але на практиці найпростіший шлях — завершити setup placeholder-адміном, потім restore (який замінить placeholder-а реальними юзерами).

### Міграція даних

Міграція між DB-backend-ами, OS-хостами або переїзд Docker-volume-ів:

1. Зніми бекап на старій інсталяції (Settings → Backup → Create Backup).
2. Підніми BamDude на новому хості.
3. Restore з backup ZIP — portable SQLite-шар BamDude автоматично транслює SQLite ↔ PostgreSQL (див. "Cross-backend restore" вище).
4. Перевір: принтери реконнектяться, профілі на місці, архіви відкриваються. Тоді demolition старого хоста.

---

## :material-file-chart: Орієнтири розміру бекапу

Грубе sizing, щоб планувати сховище:

| Профіль | Приблизний розмір | Вміст |
|---------|------------------:|-------|
| **Малий** | < 50 МБ | DB only — без архівів, без 3MF, без library-файлів. |
| **Середній** | 100–500 МБ | DB + метадані архівів + мініатюри (без 3MF). |
| **Великий** | 1–50 ГБ | DB + повний 3MF + мініатюри + library-файли + timelapse. |

Якщо у тебе багато timelapse-відео — це "великий" профіль; періодичне чищення старих timelapse (або виключення `archive/` з окремого full-data бекапу) — найпростіший шлях тримати ZIP керованим.

---

## :material-shield-check: Best practices

- **Daily для prod** — комбінуй **Заплановані локальні бекапи** з `daily` (наприклад, 03:00) і `retention=7` для роллінг-тижня.
- **Off-site хоча б один** — тримай один знімок не на BamDude-хості: NAS-share, хмарне сховище (Dropbox / Google Drive / S3 через rclone) або зовнішній USB, який ротуєш щотижня. Hardware loss б'є тебе тільки коли обидві копії на одному залізі.
- **Періодичний restore-drill** — раз на кілька місяців бери backup ZIP і пробуй відновити на throwaway-інсталяції BamDude. Бекап, який ти ніколи не відновлював — бекап, що може не працювати.
- **Backup перед апгрейдом** — протокол [`UPDATING.md`](https://github.com/kainpl/bamdude/blob/main/UPDATING.md) рекомендує свіжий ручний бекап перед кожним minor-апгрейдом. Міграції ідемпотентні і one-shot, але автоматичного шляху downgrade немає.
- **Date-suffix у назвах ручних бекапів** — коли робиш ручний бекап перед ризиковою зміною, назви по тригеру (`bamdude-pre-0.5.0-upgrade.zip`), щоб знайти потім.

---

## :material-docker: Docker volume bind-mount приклад

Для Docker-користувачів — змонтуй output-директорію бекапу як volume, щоб бекапи переживали контейнер, а ідеально — на NAS-share для off-site.

!!! warning "Шлях фіксований — ручка це монтування"
    Бекапи завжди пишуться в `backups/` усередині директорії даних. Змінної оточення, яка їх переносить, не існує: наводь volume на `/app/data/backups`, а з боку хоста монтуй що завгодно.

```yaml
services:
  bamdude:
    image: ghcr.io/kainpl/bamdude:latest
    container_name: bamdude
    network_mode: host
    volumes:
      - bamdude_data:/app/data
      - bamdude_logs:/app/logs
      - ./backups:/app/data/backups          # local relative path
      # або
      - /mnt/nas/bamdude-backups:/app/data/backups   # NAS / network share
    environment:
      - TZ=Europe/Kyiv
    restart: unless-stopped

volumes:
  bamdude_data:
  bamdude_logs:
```

Або через `docker run`:

```bash
docker run -d \
  --network host \
  -v bamdude_data:/app/data \
  -v bamdude_logs:/app/logs \
  -v /mnt/nas/bamdude-backups:/app/data/backups \
  -e TZ=Europe/Kyiv \
  --name bamdude \
  --restart unless-stopped \
  ghcr.io/kainpl/bamdude:latest
```

!!! tip "NAS / Samba / NFS"
    Направ bind-mount на NAS-share, Samba-mount чи NFS-шлях для автоматичних off-site бекапів без додаткових скриптів. У парі з retention-rotation — hands-off off-site backup pipeline.

---

## :material-lightbulb: Поради

!!! tip "Off-site покриття"
    Скомбінуйте **Заплановані локальні бекапи** (повні дані, on-disk) з **Git-бекапом** (профілі, off-site) — локальний переживе software wipe, git — переживе hardware loss.

!!! tip "Бекап перед оновленням"
    [`UPDATING.md`](https://github.com/kainpl/bamdude/blob/main/UPDATING.md) рекомендує свіжий ручний бекап перед кожним minor-апгрейдом. Міграції ідемпотентні і one-shot, але автоматичного шляху для downgrade немає.

> Початково базується на документації [Bambuddy](https://github.com/maziggy/bambuddy).
