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
| **Python** | 3.10+ (рекомендується 3.11 або 3.12) |
| **Мережа** | Та сама локальна мережа, що й принтер Bambu Lab |
| **Принтер** | Увімкнений Developer Mode ([інструкція](index.uk.md#enabling-developer-mode)) |
| **SD-карта** | Вставлена в принтер (потрібна для передачі файлів) |

!!! tip "Альтернатива -- Docker"
    Якщо ви віддаєте перевагу контейнерам, перегляньте [посібник зі встановлення Docker](docker.uk.md) -- це ще простіше!

---

## :material-download: Ручна інсталяція

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

    # Run
    uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
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

    # Run
    uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
    ```

Відкрийте [http://localhost:8000](http://localhost:8000) у браузері.

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
| `DATABASE_URL` | не задано (SQLite) | Postgres URL, наприклад `postgresql+asyncpg://user:pass@host:5432/bamdude`. Див. [Підтримка PostgreSQL](../features/postgresql.md). |

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
| Password | так | Мін 8 символів, має містити upper + lower + цифру + спецсимвол (наприклад `!@#$%^&*`). Макс 256 символів. Зберігається як bcrypt-хеш. |
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
    ExecStart=/home/YOUR_USERNAME/bamdude/venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
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
