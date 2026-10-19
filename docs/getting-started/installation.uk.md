---
title: Встановлення
description: Встановлення BamDude на вашу систему, включно з first-boot setup-гейтом автентифікації
---

# Встановлення

Цей посібник описує ручну інсталяцію BamDude. Для Docker (рекомендовано) дивіться [посібник з Docker](docker.uk.md).

---

## :material-check-all: Вимоги

| Вимога | Деталі |
|--------|--------|
| **Python** | 3.12+ (лише для нативної інсталяції — Docker і Windows-інсталятор везуть власний) |
| **macOS** | 12 або новіша для нативної інсталяції |
| **Мережа** | Та сама локальна мережа, що й принтер Bambu Lab |
| **Принтер** | Увімкнений Developer Mode ([інструкція](index.uk.md#developer-mode)) |
| **SD-карта** | Вставлена в принтер (потрібна для передачі файлів) |

!!! tip "Альтернатива -- Docker"
    Якщо ви віддаєте перевагу контейнерам, перегляньте [посібник зі встановлення Docker](docker.uk.md) -- це ще простіше!

---

## :material-download: Ручна інсталяція

!!! note "Необов’язкові мініатюри STEP"
    `git clone`, створення Python venv і `pip install -r requirements.txt` **не встановлюють** CAD-компонент. Для мініатюр STEP виконайте окремий [крок встановлення компонента STEP](#step-previews) нижче. Запуск BamDude також не завантажує цей необов’язковий компонент.

=== ":material-ubuntu: Ubuntu/Debian"

    ```bash
    # Install prerequisites
    sudo apt update
    sudo apt install python3 python3-venv python3-pip git

    # Clone and setup
    git clone https://github.com/kainpl/bamdude.git
    cd bamdude
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

    # Закріплений Node.js для мініатюр деталей (після 0.7.0; завантажується раз)
    python -m backend.app.services.render_runtime provision --runtime runtime

    # Run
    uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --loop asyncio --timeout-graceful-shutdown 15
    ```

=== ":material-apple: macOS"

    ```bash
    # Install prerequisites (if needed)
    brew install python@3.12

    # Clone and setup
    git clone https://github.com/kainpl/bamdude.git
    cd bamdude
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

    # Закріплений Node.js для мініатюр деталей (після 0.7.0; завантажується раз)
    python -m backend.app.services.render_runtime provision --runtime runtime

    # Run
    uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --loop asyncio --timeout-graceful-shutdown 15
    ```

!!! warning "macOS: принтер недоступний, хоча все інше працює"
    macOS видає доступ до локальної мережі підпису коду, а Python з Homebrew на Intel-маках його не має — тоді кожне з'єднання з принтером мовчки відкидається, без помилки й без запиту. `install/install.sh` під час встановлення на macOS підписує інтерпретатор (лише якщо він не підписаний), а повторний запуск після `brew upgrade python` підписує новий. Вручну: `codesign --force --sign - "$(python3 -c 'import os,sys;print(os.path.realpath(sys._base_executable))')"`. Перевірка **Дозвіл macOS на доступ до локальної мережі** в діагностиці з'єднання каже, який у вас випадок.

Мініатюри деталей (після 0.7.0) рендеряться закріпленим Node.js. `install/install.sh`, `update.sh` і оновлення з налаштувань BamDude завантажують його раз у `runtime/` встановлення — 26–30 МіБ залежно від платформи, близько 118 МіБ розпакованим на Linux, — а ручне встановлення виконує рядок `provision` вище. Нативне встановлення, що стартує без нього — ручний `git clone` чи `git pull`, чекаут для розробки або перше оновлення з 0.7.0, чий оновлювач старший за цей крок, — ставить його саме у фоні, раз на старт; тим часом сторінка System показує `runtime_provisioning`. Те, що лишило перерване встановлення, прибирає наступне. Не підтримується, коли кілька машин одночасно ставлять Node.js в один каталог встановлення — каталог на мережевій теці, з якого працює більше однієї машини; це стосується лише каталогу встановлення, не спільного каталогу даних. Якщо Node.js так і не з'явився, сторінка System показує **Воркер мініатюр деталей** зі станом `runtime_missing`; див. [Воркер мініатюр деталей](../reference/troubleshooting.md#part-thumbnail-worker). Інсталятор Windows і образ Docker уже несуть Node.js.

Який Node.js отримує машина: Linux і macOS на x64 чи arm64, а також Windows x64 працюють на Node.js 24. Raspberry Pi з 32-бітною Raspberry Pi OS (armhf — Pi 2, 3, 4, 5, Zero 2 W) працює на Node.js 22 — останній лінійці, яку Node.js випускає для 32-бітного ARM, — до кінця її підтримки 30 квітня 2027 року; після цього оновлення BamDude повертає його до запасної картинки. Там рекомендовано 2 ГБ оперативної пам'яті й більше: що Pi з 1 ГБ відрендерить важку плиту поряд зі службою, не обіцяється. armv6 (Pi 1, Zero, Zero W), 32-бітна система armel чи musl і RISC-V не мають офіційної збірки Node.js: деталі отримують лише запасну картинку, яку дозволяє файл.

### :material-cube-scan: Прев’ю STEP {#step-previews}

[Мініатюрам STEP](../features/file-manager.uk.md#step-thumbnails) (після 0.7.0) потрібен необов'язковий компонент близько 170 МБ — збірка Open CASCADE. Образ Docker та інсталятор Windows несуть його з собою; на нативній інсталяції це вибір адміністратора:

- `install/install.sh` питає *"Install the STEP preview component?"*. Типова відповідь — **yes**, якщо на цій інсталяції компонент уже ввімкнено, і **no** в усіх інших випадках, тож `--yes` зберігає ввімкнений компонент і лишає свіжу інсталяцію без нього. `--with-step-preview` встановлює його без запитань.
- Він пропонується на Debian/Ubuntu та Fedora/RHEL — скрипт від root ставить потрібні системні бібліотеки: `libgl1 libx11-6 libexpat1 zlib1g` або `mesa-libGL libX11 expat zlib` — і на macOS (нічого додаткового), на x86_64 та arm64. На Arch Linux і openSUSE він не пропонується: встановіть libGL, libX11 та expat самі, а потім запустіть `install/step-preview.sh enable`.
- Без нього файли STEP так само лишаються в бібліотеці, просто без мініатюри, а завдання завершується з *компонент STEP недоступний на цьому сервері* (`cad_unavailable`).

Для ручної інсталяції з Git і venv спочатку встановіть звичайні Python-залежності, а потім окремо ввімкніть CAD-компонент. Помічник завантажить запінені пакети в каталог `runtime/` інсталяції, окремо від основного venv. Він також запам’ятає ваш вибір, щоб оновлення з налаштувань підтримували компонент актуальним.

**Linux / macOS:** щоб увімкнути його пізніше або полагодити, запустіть із каталогу встановлення — BamDude може працювати далі, а наступна мініатюра STEP уже використає компонент:

```bash
sudo install/step-preview.sh enable    # records the choice, installs the libraries, then the component
sudo install/step-preview.sh status    # checks that it really renders, and says what to do if not
```

На macOS обидві команди запускають без `sudo`. `--path DIR` вказує їм на іншу інсталяцію. Вони завершуються з кодом `0`, коли все зроблено (або коли компонент працює), `1` у разі збою — з його причиною — і `3`, коли компонент недоступний для цієї машини чи її Python. `enable` чекає щонайбільше 15 хвилин на інше встановлення компонента, 15 хвилин на завантаження та 120 секунд на кожну його перевірку; читання його файлів і доведення, що його процеси завершились, не обмежені в часі.

**Windows, клон Git із Python venv:** відкрийте PowerShell у корені репозиторію та використовуйте той самий venv, з якого працює BamDude. За цих явних шляхів активувати venv не потрібно:

```powershell
# Запам’ятати вибір для майбутніх оновлень
.\venv\Scripts\python.exe -m backend.app.step_runtime choose enabled --by cli

# Завантажити й встановити запінений CAD-компонент
.\venv\Scripts\python.exe -m backend.app.step_runtime install

# Перевірити файли та справжнє перетворення STEP на PNG
.\venv\Scripts\python.exe -m backend.app.step_runtime status --check
```

Переходьте до наступної команди лише після успіху попередньої. Остання перевірка в разі успіху поверне `"bundle": "works"`. Якщо BamDude вже працює на коді з підтримкою мініатюр STEP, встановлення компонента не потребує перезапуску. Для наявних STEP-файлів після цього можна вибрати **Створити мініатюру** в бібліотеці.

Після ручного `git pull` та оновлення Python-залежностей знову виконайте `install` і `status --check` через Python цієї інсталяції, щоб встановити й перевірити поточний пін. Сам `pip install` CAD-компонент не оновлює.

!!! note "Гілки розробки з піном-кандидатом"
    Якщо в чекауті для розробки CAD-пін ще має статус `candidate`, для локального тестування замініть `install` на `install --allow-candidate`. Цей прапорець призначений лише для розробки; з релізним піном використовуйте звичайну команду. Для випущеного Docker-образу чи Windows-інсталятора він не потрібний.

| Причина | Що робити |
|---------|-----------|
| `smoke_failed:system_library:<soname>` | Бракує системної бібліотеки: встановіть пакет, який називає `status`, потім запустіть `enable` |
| `permission` | Щось у `runtime/` не доступне для запису власникові інсталяції (часто лишається після запуску через `sudo`): `sudo chown -R <owner> <install>/runtime`, потім `enable` |
| `lock_timeout` | Інше встановлення компонента тримало блокування 15 хвилин: дайте йому завершитись, потім запустіть `enable` ще раз |
| `helper_unproven` | Оновлення з налаштувань не змогло довести, що попередній запуск помічника завершився: перезапустіть BamDude, потім оновіться знову або запустіть `enable` |
| `pip_timeout`, `pip_failed` | Завантаження не завершилось: перевірте мережу, потім запустіть `enable` |

Оновлення підтримують увімкнений компонент актуальним — `update.sh` і оновлення з налаштувань оновлюють його, ніколи не ставлять той, від якого ви відмовились, і ніколи не падають через нього; див. [Оновлення → Компонент прев’ю STEP під час оновлення](upgrading.uk.md#step-component-on-update). Відповідь *no* (або `disabled`) забороняє оновленням чіпати компонент, але не прибирає вже встановлений. Сторінка System показує стан компонента — встановлено чи ні, але ніколи «працює»: це перевіряє лише `status` — і на нативній інсталяції ці дві команди; див. [System Info](../features/system-info.uk.md).

!!! note "Де лежить вихідний код компонента"
    Частини компонента під ліцензією, що вимагає їхнього вихідного коду, — Open CASCADE Technology, LibRaw, FreeImage і, на Linux, libgomp — мають цей код прикріпленим до кожного релізу, що несе компонент: ресурс `bamdude-step-preview-sources-<id>.tar` на сторінці [Releases](https://github.com/kainpl/bamdude/releases) із SHA-256 поруч — вихідний код кожного компонента разом із тим, що його зібрало. Повідомлення, які йдуть із компонентом, кажуть, де він, а той самий код доступний на запит, не дорожче за вартість його надання, щонайменше три роки після того, як BamDude востаннє поширював версію з цим компонентом, — відкрийте issue.

Відкрийте [http://localhost:8000](http://localhost:8000) у браузері.

---

## :material-microsoft-windows: Windows (нативний інсталятор)

Для Windows 10/11 є самодостатній **`.exe`-інсталятор** — без Docker, без WSL і **без окремого встановлення Python чи Node**. Setup несе в собі embedded Python runtime, статичний `ffmpeg` і — після 0.7.0 — закріплений Node.js, що рендерить мініатюри деталей (близько 21 МіБ інсталятора; заміряно 2026-10-12, Node v24.17.0), розкладає все по місцях і реєструє BamDude як **Windows Service**, що стартує при завантаженні системи.

Після 0.7.0 інсталятор несе ще й компонент, що створює [мініатюри STEP](../features/file-manager.uk.md#step-thumbnails) (близько 167 МБ після встановлення), і перевіряє його — справжній STEP, перетворений на картинку, — перш ніж запустити службу: інсталяція, чий компонент цю перевірку не проходить, лишає службу зупиненою і каже про це, а не стартує зі зламаним компонентом. Вихідний код його copyleft-частин публікується з кожним релізом; див. [Прев’ю STEP](#step-previews) вище.

1. Завантаж останній **`bamdude-<version>-windows-x64-setup.exe`** зі [сторінки Releases](https://github.com/kainpl/bamdude/releases).
2. Запусти його (потрібні права Administrator — він реєструє сервіс і пише в `ProgramData`).
3. Коли завершиться, браузер відкриє [http://localhost:8000](http://localhost:8000).

От і все — сервіс уже працює.

!!! note "SmartScreen: інсталятор не підписаний"
    Windows SmartScreen на першому запуску показує *«Windows protected your PC»* — натисни **More info → Run anyway**. Чужі бінарники всередині інсталятора (embedded Python, NSSM, ffmpeg) несуть підписи своїх вендорів або не несуть жодного. Що застосунок надсилає назовні і як вимкнути телеметрію: [Приватність і телеметрія](../privacy.uk.md).

### :material-folder-cog: Що розкладає інсталятор

| Що | Куди |
|----|------|
| **Файли програми** (embedded Python 3.12, backend + зібраний frontend, NSSM, ffmpeg) | `C:\Program Files\BamDude` |
| **Твої дані** (база, архіви, plate calibration) | `C:\ProgramData\BamDude\data` |
| **Логи** | `C:\ProgramData\BamDude\logs` |

Інсталятор також додає ярлики в Start-Menu (**Open BamDude Dashboard**, **BamDude Logs**, **Uninstall**), опціональний ярлик на робочому столі, і — якщо не знімати галочку — правило **Windows Firewall**, що відкриває порт `8000`.

!!! info "Твої дані переживають uninstall + оновлення"
    Усе під `C:\ProgramData\BamDude` лишається недоторканим при uninstall. Перевстановлення (чи встановлення новішого білда поверх) автоматично підхоплює ту саму базу й архіви.

### :material-service-toggle: Сервіс BamDude

Інсталятор реєструє Windows Service з іменем **BamDude** (під наглядом [NSSM](https://nssm.cc/)), що працює як `LocalSystem`, стартує автоматично при завантаженні й обслуговує дашборд на `http://localhost:8000`. Керуй ним стандартними cmdlet-ами:

```powershell
Get-Service BamDude          # Статус
Start-Service BamDude        # Старт
Stop-Service BamDude         # Стоп
Restart-Service BamDude      # Рестарт
```

### :material-update: Оновлення

Завантаж новіший `bamdude-<version>-windows-x64-setup.exe` і запусти — він зупиняє сервіс, перезаписує файли програми на місці й перезапускає. Твоя база, архіви та логи під `C:\ProgramData\BamDude` зберігаються.

Далі відкрий [http://localhost:8000](http://localhost:8000).

---

## :material-tune: Конфігурація

Налаштуйте BamDude через змінні середовища або файл `.env`:

```bash
cp .env.example .env
nano .env
```

### Змінні середовища

#### Основні

| Змінна | За замовчуванням | Опис |
|--------|------------------|------|
| `DEBUG` | `false` | Увімкнення debug-режиму (детальне логування; у dev також перезапускає останню міграцію при кожному старті) |
| `LOG_LEVEL` | `INFO` | Рівень логування: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_TO_FILE` | `true` | Запис логів у `logs/bamdude.log` |
| `DATA_DIR` | `<repo>/data` | Перевизначити директорію персистентних даних (БД + архіви + plate calibration) |
| `LOG_DIR` | `<repo>/logs` | Перевизначити директорію логів |
| `PORT` | `8000` | Порт, на якому слухає вбудований entrypoint `python -m backend.app.main` |
| `TZ` | system | Часовий пояс, що передається в Python (наприклад, `Europe/Kyiv`) |

#### База даних

| Змінна | За замовчуванням | Опис |
|--------|------------------|------|
| `DATABASE_URL` | не задано (SQLite) | `embedded` — вбудований PostgreSQL 18; або URL на кшталт `postgresql+asyncpg://user:pass@host:5432/bamdude` для власного сервера. Порожнє значення означає SQLite. Див. [Підтримка PostgreSQL](../features/postgresql.md). |
| `EMBEDDED_PG_PORT` | обирається один раз і запам'ятовується | Запінити порт вбудованого сервера (наприклад `6432`), щоб до нього діставали `psql` чи DBeaver. |

!!! tip "Інсталятор питає сам"
    `install.sh` пропонує SQLite, вбудований PostgreSQL або зовнішній сервер — в інтерактиві або без нього через `--db sqlite|embedded|external` (плюс `--database-url` для останнього). Повторний запуск поверх наявної інсталяції лишає той бекенд, яким ви вже користуєтесь.

!!! important "Зовнішній PostgreSQL: увімкніть статистику запитів"
    Для повної діагностики бази на сервері PostgreSQL потрібен `pg_stat_statements`. Задання `DATABASE_URL` чи оновлення образу BamDude його не вмикає. Див. [налаштування й перевірку для Docker або власного сервера](../features/postgresql.uk.md#pg-stat-statements).

#### Автентифікація та реверс-проксі

| Змінна | За замовчуванням | Опис |
|--------|------------------|------|
| `JWT_SECRET_KEY` | автогенерація, зберігається в `data/` | Перевизначити ключ підпису JWT. Не змінюйте на запущеній інсталяції -- усі видані токени стануть недійсними. |
| `TRUSTED_PROXY_IPS` | порожньо | Розділені комою IP реверс-проксі, чий `X-Forwarded-For` довіряємо (резолвінг справа наліво). Потрібно за nginx для коректного per-IP rate limit. |
| `AUTH_REFRESH_COOKIE_SECURE` | не задано (автовизначення) | Примусово виставити полярність `Secure` на cookie refresh-токена. Автовизначення зі схеми запиту -- правильний дефолт; ставте `true`, щоб примусово увімкнути, `false` -- щоб вимкнути (тільки для LAN HTTP dev). |
| `MFA_ENCRYPTION_KEY` | не задано | URL-safe base64 Fernet-ключ. Якщо задано, TOTP-секрети та OIDC client secrets шифруються at-rest. Plaintext fallback працює без нього, але логує попередження при старті. |
| `APP_URL` | `http://localhost:5173` | Публічний базовий URL BamDude. Використовується для абсолютних посилань у password-reset / MFA-recovery листах, OIDC callback URL і Obico cached-frame URL, який ML-API Obico забирає назад. Налаштування `external_url` під Settings → System перебиває цю змінну, якщо задане. |

#### Інтеграції (опціонально)

| Змінна | Опис |
|--------|------|
| `HA_URL`, `HA_TOKEN` | Базовий URL Home Assistant + long-lived token. Якщо задано **обидва**, HA-інтеграція авто-увімкнена і відповідні DB-сетинги стають read-only (env переб'є). Рекомендовано для HA Add-on; нативні інсталяції можуть вмикати HA через Settings → Integrations без env-змінних. |
| `VIRTUAL_PRINTER_PASV_ADDRESS` | Перевизначити FTP-PASV адресу, яку анонсує віртуальний принтер (встановіть, якщо BamDude працює за NAT і слайсери не можуть досягти bind IP). |
| `VIRTUAL_PRINTER_ADVERTISE_ADDRESS` | Адреса завантаження, яку віртуальний принтер, привʼязаний до справжнього, повідомляє слайсеру (встановіть, якщо BamDude працює за NAT, напр. Docker bridge). |

#### Container detection

Будь-яка з цих env-змінних (будь-яке непорожнє значення) маркує середовище як container, що змінює поведінку SSDP-discovery. Зазвичай ставиться автоматично container-runtime — перевизначай тільки якщо запускаєш натив, але хочеш container-style discovery.

| Змінна | Опис |
|--------|------|
| `CONTAINER` | Generic container marker. |
| `DOCKER_CONTAINER` | Docker-specific marker. |

#### Docker compose helpers (читаються `docker-compose.yml`, не самим BamDude)

| Змінна | Опис |
|--------|------|
| `PUID` / `PGID` | UID / GID, від яких запускається bamdude-контейнер. Виставляй у відповідність власника твоїх mounted volumes, щоб уникнути permission-помилок при запису архівів. Дізнатись: `id -u && id -g`. |

---

## :material-account-key: First-boot setup

Автентифікація в BamDude **завжди увімкнена** — режиму "no-auth" не існує. На самому першому запуску API відхиляє кожен запит з `503 {"detail": "setup_required"}`, поки не буде створено початкового адміністратора. Whitelist, що обходить гейт, — це рівно три маршрути (`/api/v1/auth/status`, `/api/v1/auth/setup`, `/api/v1/system/health`); login і всі інші ендпоінти лишаються закритими, поки setup не завершиться.

### :material-web: Setup wizard (браузер)

Відкрийте BamDude у браузері. Frontend читає `/api/v1/auth/status`, бачить `requires_setup=true` і рендерить форму setup-у:

| Поле | Обов'язкове | Примітки |
|------|-------------|----------|
| Username | так | Стає першим адміном. Макс 150 символів. |
| Password | так | Мін 8 символів, має містити мінімум одну велику + одну малу + одну цифру. Правила на спецсимвол немає — BamDude слідує NIST SP 800-63B, який явно радить проти composition-rules поза length + basic mix. Макс 256 символів. Зберігається як bcrypt-хеш. |
| Email | опціонально | Макс 254 символи. Використовується для password-reset флоу + email-OTP MFA пізніше. |

Submit створює адміністратора, скидає setup-гейт і логінить вас. Форма більше ніколи не показується — як тільки існує будь-який адмін, навігація на `/setup` редіректить на `/login`.

### :material-api: Setup через API

Скрипти і bootstrap-автоматизація можуть `POST /api/v1/auth/setup` напряму:

```bash
curl -X POST http://localhost:8000/api/v1/auth/setup \
  -H "Content-Type: application/json" \
  -d '{"admin_username":"admin","admin_password":"ChangeMe123","admin_email":"ops@example.com"}'
```

Ендпоінт one-shot — як тільки існує будь-який адмін, наступні виклики повертають `403 Forbidden` з `"Setup has already been completed."`. Виклики до setup-у не потребують токена; виклики після setup-у мають використовувати JWT.

### :material-key-remove: Recovery — втрата всіх адмінів

Якщо всі акаунти адмінів видалено або відключено і ніхто не може залогінитися, запустіть rescue-CLI, щоб скинути setup-completed flag. Наступний boot знову входить у wizard. **Усі інші дані зберігаються** — скидається лише прапорець гейту.

=== ":material-server: Native install"

    ```bash
    cd /path/to/bamdude
    source venv/bin/activate
    python -m backend.app.cli reset_admin
    ```

=== ":material-docker: Docker"

    ```bash
    docker compose exec bamdude python -m backend.app.cli reset_admin
    ```

CLI відмовляється запускатися, поки існує хоча б один адмін — спочатку видаліть мертві акаунти прямо в БД (або через admin UI, якщо в вас лишився хоч один робочий адмін), потім запустіть знову.

!!! tip "Повна документація з автентифікації"
    Сесії, ротація refresh-токенів, MFA (TOTP / email OTP / backup-коди), OIDC, LDAP, API-ключі та rate limiting — усе живе в [Автентифікація](../features/authentication.md). Setup-гейт — це лише крок зеро.

---

## :material-cog: Запуск як сервіс

=== ":material-linux: systemd (Linux)"

    Створіть файл сервісу:

    ```bash
    sudo nano /etc/systemd/system/bamdude.service
    ```

    ```ini
    [Unit]
    Description=BamDude Print Farm Manager
    After=network.target

    [Service]
    Type=simple
    User=YOUR_USERNAME
    Group=YOUR_USERNAME
    WorkingDirectory=/home/YOUR_USERNAME/bamdude
    Environment="PATH=/home/YOUR_USERNAME/bamdude/venv/bin"
    ExecStartPre=-/usr/bin/pkill -9 ffmpeg
    ExecStopPost=-/usr/bin/pkill -9 ffmpeg
    ExecStart=/home/YOUR_USERNAME/bamdude/venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --loop asyncio --timeout-graceful-shutdown 15
    Restart=always
    RestartSec=10

    [Install]
    WantedBy=multi-user.target
    ```

    Активація та запуск:

    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable bamdude
    sudo systemctl start bamdude
    ```

---

## :material-network: Мережеві вимоги

**Вихідне до принтерів** (BamDude → принтер):

| Порт | Протокол | Призначення |
|------|----------|-------------|
| 8883 | MQTT/TLS | Live-стан, керуючі команди |
| 990 | FTPS | Завантаження 3MF, скачування архіву |

**Вхідне до BamDude** (браузер / слайсер / Telegram → BamDude):

| Порт | Протокол | Призначення |
|------|----------|-------------|
| 8000 | HTTP / WS | Web UI + REST API + WebSocket для live-апдейтів |

**Вхідне до BamDude, якщо ввімкнений віртуальний принтер** (слайсер "Send to Printer" → BamDude вдає принтера). Потрібно лише якщо використовуєш Virtual Printer; нативні інсталяції можуть жити з одним 8000:

| Порт | Протокол | Призначення |
|------|----------|-------------|
| 322 | RTSP | Camera-проксі (X1 / H2 / P2) |
| 990 | FTPS control | Сесія завантаження зі слайсера |
| 3000, 3002 | TCP | Bambu proprietary bind/detect |
| 6000 | TCP | Тунель file-transfer |
| 8883 | MQTTS | Емуляція MQTT слайсер→принтер |
| 50000–50100 | TCP | FTP passive-mode data range |

Linux-деплой з `network_mode: host` у compose забирає всі ці порти автоматом. Bridge-mode Docker на macOS / Windows вимагає явного маппінгу кожного порта — див. [гайд по Docker](docker.uk.md#bridge-mode).

---

## :material-folder-cog: Збірка frontend з вихідного коду

Репозиторій містить попередньо зібрані файли frontend. Для збірки з вихідного коду:

```bash
cd frontend
npm install
npm run build
cd ..
```

---

## :checkered_flag: Наступні кроки

<div class="quick-start" markdown>

[:material-printer-3d: **Додайте принтер**<br><small>Підключіть свій перший принтер</small>](first-printer.uk.md)

[:material-docker: **Спробуйте Docker**<br><small>Ще простіше налаштування</small>](docker.uk.md)

[:material-help-circle: **Вирішення проблем**<br><small>Проблеми з інсталяцією?</small>](../reference/troubleshooting.uk.md)

</div>

> Початково базується на документації [Bambuddy](https://github.com/maziggy/bambuddy).
