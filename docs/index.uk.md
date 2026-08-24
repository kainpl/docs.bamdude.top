---
title: Головна
description: BamDude - Самостійно розгорнута система керування фермою 3D-друку для принтерів Bambu Lab
hide:
  - navigation
  - toc
---

<style>
.md-typeset h1 { display: none; }
</style>

<div class="hero" markdown>

<div markdown>

# Ваша ферма.<br>Ваші дані.<br>Ваш контроль.

**BamDude** -- це самостійно розгорнута система керування фермою 3D-друку для принтерів Bambu Lab. Відстежуйте свій парк принтерів у реальному часі, керуйте чергою та плануйте друк, автоматизуйте робочі процеси за допомогою макросів та контролюйте все через Telegram-бот.

Hard fork проєкту [Bambuddy](https://github.com/maziggy/bambuddy) з індивідуальними чергами для кожного принтера, swap mode, поетапним запуском, Telegram-ботом, макросами, історією обслуговування та багато іншого.

<div class="stats-row" markdown>
  <span class="stat-badge" markdown>:material-printer-3d: Мультипринтер</span>
  <span class="stat-badge" markdown>:material-cloud-off-outline: Працює офлайн</span>
  <span class="stat-badge" markdown>:material-open-source-initiative: Відкритий код</span>
</div>

[Почати :material-arrow-right:](getting-started/index.uk.md){ .btn .btn-primary }
[GitHub :material-github:](https://github.com/kainpl/bamdude){ .btn .btn-secondary }

</div>

</div>

---

## :material-help-circle-outline: Чому BamDude

BamDude — це **фарм-менеджер**, а не пасивний бекенд, який просто слухає ваш слайсер. Класичний флоу «нарізав → друкуй → BamDude запише що зможе» нормально працює на 1-2 принтерах, але починає сипатись тільки-но точна історія і реальний облік котушок стають важливими.

Фарм-перший флоу перевертає це: **слайсер → BamDude → принтери.** Тиснеш Print у слайсері, роутиш його у віртуальний принтер BamDude у режимі File Manager, далі в BamDude обираєш скільки принтерів і скільки копій. BamDude роздає файл по принтерах, виконує своп-макроси, стежить за прогресом, пише історію і списує кожен грам пластика — на всю ферму з одного місця.

[Повна версія :material-arrow-right:](why.uk.md){ .md-button }

---

## :rocket: Швидкий старт

<div class="quick-start" markdown>

[:material-download: **Встановлення**<br><small>Запустіть за кілька хвилин</small>](getting-started/installation.uk.md)

[:material-docker: **Docker**<br><small>Розгортання однією командою</small>](getting-started/docker.uk.md)

[:material-printer-3d: **Додати принтер**<br><small>Підключіть свій перший принтер</small>](getting-started/first-printer.uk.md)

[:material-arrow-up-circle: **Оновлення**<br><small>Міграція з Bambuddy</small>](getting-started/upgrading.uk.md)

</div>

---

## :sparkles: Можливості

<div class="feature-grid" markdown>

<div class="feature-card" markdown>
### :material-monitor-dashboard: [Моніторинг у реальному часі](features/monitoring.uk.md)
Статус принтерів у реальному часі через WebSocket, потокове відео з камери MJPEG, відстеження помилок HMS та моніторинг вологості й температури AMS.
</div>

<div class="feature-card" markdown>
### :material-clock-outline: [Індивідуальні черги для принтерів](features/print-queue.uk.md)
Незалежні черги друку для кожного принтера з перетягуванням, планованим друком, поетапним запуском та swap mode для A1 Mini з підміною платформ.
</div>

<div class="feature-card" markdown>
### :material-archive: [Архів друку](features/archiving.uk.md)
Автоматичне архівування 3MF з витягуванням метаданих, 3D-попереднім переглядом моделей, виявленням дублікатів та повнотекстовим пошуком.
</div>

<div class="feature-card" markdown>
### :material-robot: [Telegram-бот](features/telegram-bot.uk.md)
Повне керування принтером з Telegram з вбудованими меню, авторизацією кількох чатів, рольовими дозволами та інтерактивними сповіщеннями.
</div>

<div class="feature-card" markdown>
### :material-code-braces: [Макроси](features/macros.uk.md)
G-code макроси, що активуються подіями друку (старт, завершення, пауза). Вбудований редактор з налаштуванням для кожного принтера та моделі.
</div>

<div class="feature-card" markdown>
### :material-bell-ring: [Сповіщення](features/notifications.uk.md)
Багатопровайдерні сповіщення через Telegram, Discord, Email, Pushover, ntfy, CallMeBot (WhatsApp), Home Assistant та власні webhook. Тихі години й щоденний digest на кожен провайдер окремо.
</div>

<div class="feature-card" markdown>
### :material-cog-transfer: [Server-side нарізання](features/slicer-api.uk.md)
OrcaSlicer + BambuStudio sidecar-контейнери, вибір слайсера на кожен запит із live-індикаторами доступності, override типу столу, inline-вибір плити для мульти-плейт-файлів, owner-фільтр на пресетах.
</div>

<div class="feature-card" markdown>
### :material-folder-multiple: [File Manager + бібліотека](features/file-manager.uk.md)
Бібліотека 3MF / G-code / STL / STEP із композитними тегами-чіпами (format / readiness / modifiers / provenance), чіп-фільтром, per-plate-галереєю, 3D-/G-code-в'ювером з вайрфреймом друкарського об'єму. Page-level drag-and-drop у File Manager + на картках черг принтерів + у панелі Auto-Queue.
</div>

<div class="feature-card" markdown>
### :material-source-branch: [Авточерга ферми](features/auto-queue.uk.md)
Один пул роботи на всю ферму: завдання йдуть на будь-який принтер, у якому заряджено відповідний філамент, з рознесеними стартами, воротами очистки столу й фолбеками на принтер.
</div>

<div class="feature-card" markdown>
### :material-power-plug: [Zigbee без хаба](features/smart-plugs.uk.md)
BamDude сам керує радіо через USB чи Ethernet — розетки й датчики температури/вологості підключаються в мережу, якою володіє він. Без Home Assistant, без Zigbee2MQTT, без брокера, який треба тримати живим.
</div>

<div class="feature-card" markdown>
### :material-lightning-bolt: [Енергія і вартість друку](features/energy.uk.md)
Ват-години прив'язані до архіву кожного друку, з погодинними знімками під діапазонними цифрами і динамічним тарифом, якщо ваш постачальник його публікує.
</div>

<div class="feature-card" markdown>
### :material-palette-swatch: [Філамент і котушки](features/inventory.uk.md)
Інвентар котушок з обліком витрат, визначенням кольору за спільним каталогом, друкованими етикетками та двосторонньою синхронізацією зі [Spoolman](features/spoolman.uk.md).
</div>

<div class="feature-card" markdown>
### :material-tune: [Калібрування](features/filament-calibration.uk.md)
Прогони flow-rate і pressure-advance разом із K-профілями, які вони дають, плюс калібрування пристрою — рівень столу, вібрації, шум моторів, зміщення сопла — обмежене тим, що конкретна модель справді вміє.
</div>

<div class="feature-card" markdown>
### :material-wrench-clock: [Обслуговування](features/maintenance.uk.md)
Інтервали сервісу на кожен принтер у годинах друку: те, що прострочено, видно на картці принтера й позначається виконаним із вебу або з бота.
</div>

<div class="feature-card" markdown>
### :material-printer-eye: [Віртуальний принтер](features/virtual-printer.uk.md)
Надсилайте зі слайсера на принтер, якого немає: файл потрапляє в бібліотеку як щось, що можна переглянути, позначити тегом і надрукувати пізніше, а не в архів.
</div>

<div class="feature-card" markdown>
### :material-shield-account: [Автентифікація](features/authentication.uk.md)
Завжди увімкнена. Групи прав на користувача, TOTP і email-2FA, OIDC single sign-on та API-ключі з обмеженою областю для всього, що не браузер.
</div>

</div>

[Усі можливості :material-arrow-right:](features/index.uk.md){ .md-button }

---

## :printer: Підтримувані принтери

| Серія | Моделі |
|-------|--------|
| **X1 Series** | X1, X1 Carbon, X1E |
| **H2 Series** | H2D, H2D Pro, H2C, H2S |
| **P1 Series** | P1P, P1S |
| **P2 Series** | P2S |
| **X2 Series** | X2D |
| **A2 Series** | A2L |
| **A1 Series** | A1, A1 Mini |

---

## :wrench: Технічний стек

<div class="feature-grid" markdown>

<div class="feature-card" markdown>
### Backend
:material-language-python: Python
:material-api: FastAPI
:material-database: SQLAlchemy + SQLite
</div>

<div class="feature-card" markdown>
### Frontend
:material-react: React
:material-language-typescript: TypeScript
:material-tailwind: Tailwind CSS
</div>

<div class="feature-card" markdown>
### Комунікація
:material-transit-connection-variant: MQTT over TLS
:material-folder-network: FTPS
:material-web: WebSocket
</div>

</div>

---

## :material-heart: Звідки це взялося

BamDude виріс із волонтерського цеху. Автор проєкту — волонтер [**ДрукАрмії**](https://drukarmy.org.ua/ua/about-us),
найбільшої волонтерської ініціативи 3D-друку для фронту: друкує сам і веде напрямок FPV як старший куратор.

Партії, дедлайни й ферма, яку треба тримати в русі цілодобово, не влазять у жоден готовий інструмент — тому
кожна фіча тут спершу відпрацювала на реальному замовленні. Звідти ж українська локалізація.

[:material-account-plus: Долучитись до ДрукАрмії](https://app.drukarmy.org.ua/inv/ujnv7w8i){ .md-button }

## :material-handshake: Партнери

<div class="grid cards" markdown>

-   ![ДрукАрмія](assets/partners/drukarmy.png){ width="64" style="background:#fff;border-radius:12px;padding:6px;float:right;margin-left:12px" }

    **[ДрукАрмія](https://drukarmy.org.ua/ua)**

    ---

    Найбільша волонтерська 3D-друк спільнота України, що друкує для фронту. BamDude народився саме в цій майстерні — і якщо у тебе є принтер, для нього тут знайдеться корисна робота.

    [:material-account-plus: Долучитись до ДрукАрмії](https://app.drukarmy.org.ua/inv/ujnv7w8i)

-   ![Дракони Оборони](assets/partners/dragons.png){ width="64" style="border-radius:12px;float:right;margin-left:12px" }

    **[Дракони Оборони](https://dragons.in.ua/)**

    ---

    Волонтерська 3D-друк ініціатива: цілодобова ферма, що друкує пластикове спорядження для Сил оборони, з повністю прозорими фінансами — все публічно й рахується автоматично.

    [:material-open-in-new: dragons.in.ua](https://dragons.in.ua/)

-   ![AdditHub](assets/partners/addithub.png){ width="64" style="background:#fff;border-radius:12px;padding:6px;float:right;margin-left:12px" }

    **[AdditHub](https://addithub.com/)**

    ---

    Маркетплейс 3D-друку №1 в Україні: публікуєш замовлення — перевірені виконавці дають сліпі ставки. FDM, SLA і SLS друк, 3D-моделювання та постобробка.

    [:material-open-in-new: addithub.com](https://addithub.com/)

</div>

## :material-hand-heart: Підтримати проєкт

BamDude безкоштовний і таким лишиться — AGPL-3.0, без платних тарифів і без pro-версії. Найцінніша
підтримка — баг-репорт, PR із перекладом або зірка на GitHub. Якщо хочеться закинути:

| | |
|---|---|
| **Банка monobank** | [send.monobank.ua/jar/2vREyf3SrF](https://send.monobank.ua/jar/2vREyf3SrF) |
| **PayPal** | `pushkar.valeriy@gmail.com` |
| **USDT (TRC20)** | `TWe1MaXz7mpDZZqDkY7Az7NdZ6s9H5fvMF` |

---

<div style="text-align: center; margin-top: 3rem;" markdown>
<span style="opacity: 0.6;">Створено з :heart: для спільноти 3D-друку</span>
</div>
