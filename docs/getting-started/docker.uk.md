---
title: Інсталяція Docker
description: Розгорніть BamDude за допомогою Docker однією командою
---

# Інсталяція Docker

Docker -- найпростіший спосіб запустити BamDude. Одна команда -- і готово.

---

## :rocket: Швидкий старт

=== ":material-download: Готовий образ"

    ```bash
    mkdir bamdude && cd bamdude
    curl -O https://raw.githubusercontent.com/kainpl/bamdude/main/docker-compose.yml
    docker compose up -d
    ```

=== ":material-source-branch: Збірка з вихідного коду"

    ```bash
    git clone https://github.com/kainpl/bamdude.git
    cd bamdude
    docker compose up -d --build
    ```

Відкрийте [http://localhost:8000](http://localhost:8000) у браузері.

---

## :material-cog: Конфігурація

### docker-compose.yml (host mode — Linux, рекомендовано)

```yaml
services:
  bamdude:
    image: ghcr.io/kainpl/bamdude:latest
    build: .
    container_name: bamdude
    # Прибирає warnings про permissions volumes: ставимо в UID/GID хоста,
    # який володіє /var/lib/docker/volumes (зазвичай 1000:1000 на Debian / Ubuntu).
    # Дізнатись: id -u && id -g
    user: "${PUID:-1000}:${PGID:-1000}"
    # Дозволяє bind на привілейовані порти (322 RTSP, 990 FTPS) як non-root.
    cap_add:
      - NET_BIND_SERVICE
    # Тільки Linux — Docker Desktop на macOS / Windows host-mode не підтримує.
    # Там закоментуй цей рядок і використай bridge-mode-блок нижче.
    network_mode: host
    volumes:
      - bamdude_data:/app/data
      - bamdude_logs:/app/logs
      # Поділ virtual-printer сертів з паралельною натив-інсталяцією, якщо є.
      - ./virtual_printer:/app/data/virtual_printer
    environment:
      - TZ=${TZ:-Europe/Kyiv}
      - PORT=${PORT:-8000}
    restart: unless-stopped

volumes:
  bamdude_data:
  bamdude_logs:
```

### docker-compose.yml (bridge mode — macOS / Windows / strict networking) {#bridge-mode}

Docker Desktop на macOS / Windows не підтримує `network_mode: host`, та й деякі hardened-Linux setups його уникають. У bridge-режимі треба замапити кожен порт, з яким говорить принтер, і кожен порт, який слухає віртуальний принтер. Авто-discovery фізичних принтерів вмирає — додавай по IP вручну з UI.

```yaml
services:
  bamdude:
    image: ghcr.io/kainpl/bamdude:latest
    container_name: bamdude
    user: "${PUID:-1000}:${PGID:-1000}"
    cap_add:
      - NET_BIND_SERVICE
    ports:
      - "${PORT:-8000}:8000"            # Web UI + REST + WebSocket
      - "322:322"                        # Virtual-printer RTSP camera proxy
      - "990:990"                        # Virtual-printer FTPS control
      - "3000:3000"                      # Virtual-printer bind/detect
      - "3002:3002"                      # Virtual-printer bind/detect alt
      - "6000:6000"                      # Virtual-printer file tunnel
      - "8883:8883"                      # Virtual-printer MQTT
      - "2024-2026:2024-2026"            # Virtual-printer A1 / P1S range
      - "50000-50100:50000-50100"        # Virtual-printer FTP PASV data
    volumes:
      - bamdude_data:/app/data
      - bamdude_logs:/app/logs
    environment:
      - TZ=${TZ:-Europe/Kyiv}
      - PORT=${PORT:-8000}
      # Обов'язково для FTP PASV за NAT — постав LAN-IP Docker-хоста.
      # Слайсеру це треба, щоб відкрити data-з'єднання.
      - VIRTUAL_PRINTER_PASV_ADDRESS=${VIRTUAL_PRINTER_PASV_ADDRESS:-}
    restart: unless-stopped

volumes:
  bamdude_data:
  bamdude_logs:
```

### Змінні середовища

| Змінна | За замовчуванням | Опис |
|--------|------------------|------|
| `TZ` | `UTC` | Ваш часовий пояс (наприклад, `America/New_York`) |
| `PORT` | `8000` | Порт, на якому працює BamDude |
| `DEBUG` | `false` | Увімкнення логування налагодження |
| `LOG_LEVEL` | `INFO` | Рівень логування: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_TO_FILE` | `true` | Запис логів у `/app/logs/bamdude.log` |
| `DATABASE_URL` | не задано (SQLite) | URL PostgreSQL, наприклад `postgresql+asyncpg://user:pass@host:5432/bamdude` |
| `TRUSTED_PROXY_IPS` | порожньо | Розділені комою IP реверс-проксі, що довіряються для `X-Forwarded-For` (встановлюйте, коли BamDude стоїть за nginx / Caddy / Traefik) |
| `AUTH_REFRESH_COOKIE_SECURE` | не задано (auto) | Примусово встановити прапорець `Secure` для refresh-cookie. За замовчуванням -- автовизначення зі схеми запиту. |
| `MFA_ENCRYPTION_KEY` | не задано | URL-safe base64 Fernet-ключ для at-rest шифрування TOTP / OIDC секретів. |
| `APP_URL` | `http://localhost:5173` | Публічний базовий URL — використовується в password-reset / MFA листах, OIDC callback-ах і Obico cached-frame URL. Налаштування `external_url` в Settings → System перебиває цю змінну. |
| `JWT_SECRET_KEY` | автогенерація, зберігається | Не змінюйте на запущеній інсталяції -- це анулює всі видані токени. |
| `PUID` / `PGID` | `1000` / `1000` | UID / GID, від якого працює контейнер. Виставляй у відповідність власника mounted volumes, щоб уникнути permission-помилок. |
| `VIRTUAL_PRINTER_PASV_ADDRESS` | не задано | Перевизначити FTP-PASV IP, який анонсує віртуальний принтер. Обов'язково в **bridge mode** (LAN-IP Docker-хоста); у host-mode лиши порожнім. |
| `USE_SYSTEM_TRUST_STORE` | не задано (off) | Opt-in. Постав будь-яке непорожнє значення (напр. `true`), щоб контейнер довіряв самопідписаним сертифікатам, змонтованим у `/usr/local/share/ca-certificates`. Див. [Довіра до самопідписаного сертифіката](#trusting-a-self-signed-certificate) нижче. |

Повний перелік, включно з опціональними інтеграціями, див. у [Інсталяція > Змінні середовища](installation.uk.md#змінні-середовища).

### Довіра до самопідписаного сертифіката { #trusting-a-self-signed-certificate }

Деякі інтеграції живуть на HTTPS-ендпоінтах із **самопідписаними сертифікатами** — найчастіше це локальний Home Assistant, але те саме стосується OIDC-провайдерів чи будь-якого HTTPS-клієнта, з яким говорить BamDude. Замість того, щоб вимикати TLS-перевірку (це ослабило б кожне з'єднання), BamDude може додати твій власний сертифікат(и) у trust store контейнера.

1. Змонтуй host-директорію зі своїми `.crt`-файлами у `/usr/local/share/ca-certificates`
2. Постав `USE_SYSTEM_TRUST_STORE=true`

На старті контейнера entrypoint виконує `update-ca-certificates --fresh` і експортує `SSL_CERT_DIR=/etc/ssl/certs`, тож увесь Python-стек (інтеграція Home Assistant, OIDC, будь-який HTTPS-клієнт) надалі довіряє сертифікату.

```yaml
services:
  bamdude:
    image: ghcr.io/kainpl/bamdude:latest
    container_name: bamdude
    network_mode: host
    volumes:
      - bamdude_data:/app/data
      - bamdude_logs:/app/logs
      # Поклади свій самопідписаний .crt у цю host-директорію.
      - /path/to/certs:/usr/local/share/ca-certificates
    environment:
      - TZ=${TZ:-Europe/Kyiv}
      - USE_SYSTEM_TRUST_STORE=true
    restart: unless-stopped

volumes:
  bamdude_data:
  bamdude_logs:
```

!!! warning "Падає голосно при невірній конфігурації"
    Прапорець **вимкнений за замовчуванням**. Якщо ти його виставив, але **не** змонтував жодного `.crt`-файлу, контейнер виходить з помилкою замість тихого старту — інакше порожній mount виглядав би так, ніби прапорець нічого не зробив. Також потрібен **root**-контейнер: якщо ти задав non-root `user:` / `PUID`/`PGID`, entrypoint не зможе писати в системний trust store і вийде з помилкою. Запускай оновлення trust store від root (це default) — entrypoint усе одно скине привілеї після цього для самого застосунку.

---

## :material-database: Збереження даних

Стандартний compose-файл монтує два named-volumes плюс один host-bound subdir:

| Mount | Тип | Що зберігає |
|---|---|---|
| `bamdude_data:/app/data` | named volume | `bamdude.db` (SQLite), `archive/` (3MF + мініатюри), `library/` (file manager), `certs/` (TLS-матеріал per-VP), uploads, бекапи |
| `bamdude_logs:/app/logs` | named volume | `bamdude.log` -- ротовані логи застосунку |
| `./virtual_printer:/app/data/virtual_printer` | bind-mount | Сертифікати слайсера per-VP (поділ з паралельною native-інсталяцією, якщо є) |

Docker Compose v2 додає до named-volumes префікс **імені проєкту** (basename директорії, де лежить compose-файл), тому реальний том на диску -- наприклад `bamdude_bamdude_data`, а не `bamdude_data`. Перерахуй усі через `docker volume ls`.

!!! tip "Резервне копіювання"
    Щоб зробити бекап, скопіюй вміст volumes (або скористайся вбудованою функцією [Резервне копіювання та відновлення](../features/backup.md) у **Settings → Backup**, яка пакує все в один zip). Application-level бекап -- кращий варіант: він зберігає метадані ключа шифрування і стан scheduled-бекапів, які сирий `tar` тома не захоплює.

!!! warning "Перейменування compose-папки = нові порожні volumes"
    Якщо оновлюєшся, перейменувавши `~/bamdude` у `~/bamdude-old` і розпакувавши свіжий checkout на старе місце, Docker Compose створить **свіжий, порожній** `bamdude_bamdude_data`, а реальні дані залишаться в старому `bamdude-old_bamdude_data`. Це найпоширеніша причина "новий контейнер запустився порожнім після оновлення". Див. [Оновлення та міграція → Персистентність даних](upgrading.uk.md#9-data-persistence-new-container-started-empty) -- там розписані всі сценарії і їх фікси (namespacing named-volumes, дрейф bind-mount шляхів, дані лише в container-layer, невідповідність PUID/PGID, випадковий `down -v`, namespacing у GUI-менеджерах).

---

## :material-update: Оновлення

=== ":material-download: Готовий образ"

    ```bash
    docker compose pull && docker compose up -d
    ```

=== ":material-source-branch: Зібраний з вихідного коду"

    ```bash
    cd bamdude && git pull && docker compose build --pull && docker compose up -d
    ```

---

## :material-server: Розширені налаштування

### Зворотний проксі (Nginx)

```nginx
server {
    listen 443 ssl http2;
    server_name bamdude.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

!!! warning "Підтримка WebSocket"
    Переконайтеся, що ваш зворотний проксі підтримує з'єднання WebSocket -- це необхідно для оновлень стану принтера в реальному часі.

### Мережевий режим Host

Мережевий режим host **обов'язковий** для виявлення принтерів та потокового відео з камери на Linux:

```yaml
services:
  bamdude:
    network_mode: host
```

!!! note "macOS / Windows"
    Docker Desktop на macOS / Windows потребує перенаправлення портів замість host-режиму. Скопіюй [bridge-mode compose-блок вище](#bridge-mode) — мапінгу тільки `ports: ["8000:8000"]` достатньо для веб-UI, але це ламає виявлення принтерів, віртуальний принтер і FTP-завантаження архівів. Фізичні принтери додавай по IP вручну з UI.

!!! warning "DEBUG=true на першому boot великої інсталяції"
    `DEBUG=true` змушує BamDude перезапускати останню міграцію на кожному старті. Якщо в тебе тисячі архівів — це означає прохід по всім 3MF на диску перед тим, як API підніметься. Вимикай DEBUG після того, як міграція встояла.

---

## :material-help-circle: Вирішення проблем

### Контейнер не запускається

```bash
docker compose logs bamdude
```

### Не вдається підключитися до принтера

```bash
docker compose exec bamdude ping YOUR_PRINTER_IP
```

Якщо використовуєте bridge-режим мережі, спробуйте `network_mode: host`.

---

## :checkered_flag: Наступні кроки

<div class="quick-start" markdown>

[:material-printer-3d: **Додайте принтер**<br><small>Підключіть свій перший принтер</small>](first-printer.uk.md)

[:material-arrow-up-circle: **Оновлення**<br><small>Безпечне оновлення та відкат</small>](upgrading.uk.md)

[:material-help-circle: **Вирішення проблем**<br><small>Виникли проблеми?</small>](../reference/troubleshooting.uk.md)

</div>

> Початково базується на документації [Bambuddy](https://github.com/maziggy/bambuddy).
