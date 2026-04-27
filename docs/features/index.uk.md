---
title: Можливості
description: Ознайомтеся з усіма можливостями BamDude
---

# Можливості

BamDude має безліч функцій для керування вашою фермою 3D-друку. Ознайомтеся з ними нижче.

---

## :material-printer-3d: Принтери та моніторинг

<div class="feature-grid" markdown>

<div class="feature-card" markdown>
### [:material-monitor-dashboard: Моніторинг у реальному часі](monitoring.uk.md)
Статус принтерів у реальному часі, температури, прогрес друку та відстеження помилок HMS через WebSocket.
</div>

<div class="feature-card" markdown>
### [:material-camera: Потокове відео з камери](camera.uk.md)
MJPEG потокове відео та знімки з вбудованої камери принтера.
</div>

<div class="feature-card" markdown>
### [:material-water-percent: AMS та вологість](ams.uk.md)
Моніторинг слотів AMS, рівнів вологості та температури. Віддалена сушка та налаштовувані пресети.
</div>

</div>

---

## :material-clock-outline: Черга друку

<div class="feature-grid" markdown>

<div class="feature-card" markdown>
### [:material-printer-3d-nozzle: Індивідуальні черги](print-queue.uk.md)
Незалежна черга для кожного принтера з перетягуванням, кількістю в партії, запланованим запуском та призначенням за моделлю.
</div>

<div class="feature-card" markdown>
### [:material-timer-sand: Поетапний запуск](staggered-start.md)
Поетапний запуск серійних друків для уникнення піків споживання від одночасного нагрівання столів.
</div>

<div class="feature-card" markdown>
### [:material-swap-horizontal: Swap Mode](swap-mode.md)
Підтримка підміни платформ A1 Mini з swap-файлами, макросами та автоматичним очищенням платформи.
</div>

</div>

---

## :material-archive: Архів друку

<div class="feature-grid" markdown>

<div class="feature-card" markdown>
### [:material-archive-outline: Архівування друку](archiving.md)
Автоматичне архівування 3MF з витягуванням метаданих, 3D-попереднім переглядом та виявленням дублікатів.
</div>

<div class="feature-card" markdown>
### [:material-folder: Файловий менеджер](file-manager.md)
Перегляд, завантаження та керування локальною бібліотекою файлів друку. Друк напряму або додавання до черги.
</div>

</div>

---

## :material-robot: Автоматизація

<div class="feature-grid" markdown>

<div class="feature-card" markdown>
### [:material-power-plug: Розумні розетки](smart-plugs.md)
Інтеграція з Tasmota, Home Assistant, REST/Webhook та MQTT для автоматичного ввімкнення/вимкнення та моніторингу енергоспоживання.
</div>

<div class="feature-card" markdown>
### [:material-printer-3d: Віртуальний принтер](virtual-printer.md)
Емуляція принтера Bambu у вашій мережі для надсилання друків безпосередньо зі слайсера.
</div>

<div class="feature-card" markdown>
### [:material-code-braces: Макроси](macros.md)
G-code макроси, що активуються подіями друку, з вбудованим редактором.
</div>

<div class="feature-card" markdown>
### [:material-bell-ring: Сповіщення](notifications.uk.md)
Вісім каналів доставки — Telegram, Discord, Email, Pushover, ntfy, CallMeBot (WhatsApp), Home Assistant, власні webhook. Тихі години, щоденний digest і шаблони — кожному провайдеру свої.
</div>

<div class="feature-card" markdown>
### [:material-robot-confused: AI-детекція фейлів Obico](obico.uk.md)
Опційна ML-детекція фейлів друку. Чутливість і список увімкнених принтерів конфігуруються; при стійкому фейлі — нотифай, пауза або пауза + вимкнення розетки.
</div>

</div>

---

## :material-send: Telegram-бот

<div class="feature-grid" markdown>

<div class="feature-card" markdown>
### [:material-robot: Налаштування бота](telegram-bot.md)
Повне керування принтером з Telegram через вбудовані меню, друк з бібліотеки та інтерактивні сповіщення.
</div>

<div class="feature-card" markdown>
### [:material-shield-lock: Авторизація кількох чатів](telegram-auth.md)
Авторизація для кожного чату з ролями, дозволами, режимами реєстрації та маршрутизацією сповіщень.
</div>

</div>

---

## :material-wrench: Обслуговування та налаштування

<div class="feature-grid" markdown>

<div class="feature-card" markdown>
### [:material-tools: Трекер обслуговування](maintenance.md)
Планування та відстеження завдань обслуговування з нагадуваннями за інтервалом та детальною історією.
</div>

<div class="feature-card" markdown>
### [:material-lock: Автентифікація](authentication.uk.md)
Завжди-увімкнена автентифікація з рольовим контролем доступу, 80+ гранульованими дозволами, MFA (TOTP / email OTP / backup-коди), OIDC SSO та LDAP.
</div>

<div class="feature-card" markdown>
### [:material-backup-restore: Резервне копіювання та відновлення](backup.md)
Повне резервне копіювання та відновлення бази даних для захисту даних.
</div>

</div>

---

## :material-folder-multiple: Бібліотека, інвентар і проєкти

<div class="feature-grid" markdown>

<div class="feature-card" markdown>
### [:material-package-variant: Інвентар котушок](inventory.uk.md)
Вбудований облік пластику: ціна / lot / дата покупки, призначення слотів AMS на принтер, авто-облік витрати на друк, каталог кольорів з урахуванням виробника.
</div>

<div class="feature-card" markdown>
### [:material-folder-multiple: Проєкти та print plan](projects.uk.md)
Групуй друки в проєкти зі впорядкованим print plan. Stepper копій на файл, live-обчислення пластику/часу/ціни, експорт ZIP / JSON.
</div>

<div class="feature-card" markdown>
### [:material-tune-variant: K-профілі](kprofiles.uk.md)
Print-профілі на принтер з обмеженнями для двосопельних, імпорт/експорт та інтеграція з Git-бекапом.
</div>

<div class="feature-card" markdown>
### [:material-chart-bar: Статистика і енергія](stats.uk.md)
Сумарна стата друку, облік енергії на друк з розетки, фермові підсумки за період, розбивка на принтер.
</div>

</div>

---

## :material-puzzle: Інтеграції

<div class="feature-grid" markdown>

<div class="feature-card" markdown>
### [:material-spool: Spoolman](spoolman.uk.md)
Двостороння синхронізація інвентарю філаменту зі Spoolman.
</div>

<div class="feature-card" markdown>
### [:material-wifi: MQTT Publishing](mqtt.uk.md)
Публікація стану принтерів до зовнішніх MQTT-брокерів для Home Assistant та Node-RED.
</div>

<div class="feature-card" markdown>
### [:material-chart-line: Prometheus Metrics](prometheus.uk.md)
Експорт телеметрії принтерів для дашбордів Grafana та систем моніторингу.
</div>

</div>
