---
title: Підтримувані принтери
description: Інформація про сумісність моделей принтерів Bambu Lab
---

# Підтримувані принтери

BamDude підтримує наведені нижче 3D-принтери Bambu Lab за наявності Developer Mode.

---

## :material-check-circle: Підтримувані моделі

| Модель | Серія | Камера | AMS |
|--------|-------|:------:|:---:|
| **X1** | X1 | :material-check: | :material-check: |
| **X1 Carbon** | X1 | :material-check: | :material-check: |
| **X1E** | X1 | :material-check: | :material-check: |
| **H2D** | H2 | :material-check: | :material-check: |
| **H2D Pro** | H2 | :material-check: | :material-check: |
| **H2C** | H2 | :material-check: | :material-check: |
| **H2S** | H2 | :material-check: | :material-check: |
| **P1P** | P1 | Додатково | :material-check: |
| **P1S** | P1 | :material-check: | :material-check: |
| **P2S** | P2 | :material-check: | :material-check: |
| **X2D** | X2 | :material-check: | :material-check: |
| **A1** | A1 | :material-check: | AMS Lite |
| **A1 Mini** | A1 | :material-check: | AMS Lite |
| **A2L** | A2 | :material-check:[^a2l] | :material-check:[^a2l] |

У BambuStudio `v02.08.04.57` також зʼявився опис моделі **N8**. BamDude
розпізнає її назву та код у дзеркалі каталогу, але підключення, друк і лазерні
функції N8 ще не перевірені. Тому її поки немає в таблиці підтримуваних моделей
і переліку функцій.

---

## :material-printer-3d: Особливості за серіями

### Серія X1

- Активний обігрів камери на X1E; X1 і X1 Carbon мають сенсор камери, але не активний нагрівач
- До 4 блоків AMS
- Підтримка RTSP-відео; частота кадрів залежить від принтера й підключення

### Серія H2

- H2D / H2D Pro: подвійне сопло зі статусом лівого/правого сопла
- H2C: стійка для 6 сопел (tool changer)
- Обігрів камери

### Серія P1

- P1P потребує додаткової камери
- До 4 блоків AMS
- Камера з низькою частотою кадрів

### Серія A1

- A1 та A1 mini: підтримка AMS Lite, зокрема налаштування слотів, призначення філаменту та його резервування, коли воно ввімкнене на принтері
- Обидві моделі також підтримують зовнішню котушку. A1 mini — основна ціль для [режиму заміни](../features/swap-mode.uk.md); swap mode не означає відсутність підтримки AMS у моделі
- Камера з низькою частотою кадрів

### Серія X2

- X2D: подвійне сопло зі статусом лівого/правого сопла
- Ethernet-порт + RTSP-камера (порт 322)
- Клас обслуговування Steel Rods

### Серія A2

- A2L: одне FDM-сопло — друга голова це інтегрований різак/плоттер, а не сопло
- Лише Wi-Fi (без Ethernet), низькочастотна chamber-image камера на порту 6000
- Клас обслуговування Linear Rails

---

## :material-table-check: Матриця можливостей BamDude { #bamdude-capability-matrix }

Таблиця показує, які функції BamDude вмикаються per-серія. Незаповнені
клітинки — або залізо не публікує дані, або біт протоколу не верифіковано,
або клас моделі не застосовний — BamDude не показує фейкового стану в таких
випадках.

| Можливість | X1 | P1P | P1S | P2S / X2D | A1 | A1 Mini | A2L | H2D / H2D Pro | H2C | H2S |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| Камера (вбудована) | :material-check: | додатково | :material-check: | :material-check: | :material-check: | :material-check: | :material-check:[^a2l] | :material-check: | :material-check: | :material-check: |
| RTSP-відеопотік | :material-check: | — | — | :material-check: | — | — | — | :material-check: | :material-check: | :material-check: |
| Ethernet-порт [^network] | лише X1E | — | — | лише X2D | — | — | — | :material-check: | :material-check: | :material-check: |
| Активний обігрів камери | лише X1E | — | — | лише X2D | — | — | — | :material-check: | :material-check: | :material-check: |
| Сенсор дверей (MQTT) [^door] | :material-check: | n/a [^opentop] | — | :material-check:[^door] | n/a [^opentop] | n/a [^opentop] | — | — [^bit23] | — [^bit23] | — [^bit23] |
| Подвійне сопло (L/R) | — | — | — | лише X2D | — | — | — | :material-check: | :material-check: | — |
| 6-слотовий tool changer | — | — | — | — | — | — | — | — | :material-check: | — |
| Чотирислотовий AMS [^ams] | до 4 | до 4 | до 4 | до 4 | див. примітку | див. примітку | :material-check:[^a2l] | до 4 | до 4 | до 4 |
| AMS Lite | — | — | — | — | :material-check: | :material-check: | — | — | — | — |
| Зовнішня котушка | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: |
| AMS-HT (single-slot 128–135) | — | — | — | — | — | — | — | :material-check: | :material-check: | :material-check: |
| Сповіщення про вологість / температуру AMS [^ams] | :material-check: | :material-check: | :material-check: | :material-check: | — із Lite | — із Lite | :material-check: | :material-check: | :material-check: | :material-check: |
| Обслуговування — Carbon Rods | :material-check: | :material-check: | :material-check: | — | — | — | — | — | — | — |
| Обслуговування — Steel Rods | — | — | — | :material-check: | — | — | — | — | — | — |
| Обслуговування — Linear Rails | — | — | — | — | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: |
| Swap mode (виштовхування) [^swap] | — | — | — | — | :material-check: | :material-check: | — | — | — | — |
| Vibration-cali skip патчер | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: |
| Skip-objects посеред друку | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: |

[^door]: BamDude читає `home_flag` біт 23 для X1 та `stat` біт 23 для X2D/P2S. X2D перевірено на залізі; для P2S використовується те саме трактування, поки що як припущення. P1S не має сенсора дверей. Див. `backend/app/utils/printer_models.py::door_sensor_field`.

[^opentop]: Open-frame принтери фізично не мають дверей — нічого
сенсорити.

[^bit23]: Апаратний сенсор і придатний MQTT-звіт — різні можливості. BamDude не показує бейдж дверей для цих моделей, доки правильне поле телеметрії не перевірено.

[^ams]: Підтримка AMS не означає наявності всіх його функцій. AMS Lite на **A1 та A1 mini** підтримує подачу філаменту й керування слотами, зокрема RFID-ідентифікацію котушок Bambu, але не надає показників вологості чи активного сушіння. Інші варіанти AMS та доступні команди залежать від підключеного обладнання, адаптера й прошивки; див. [налаштування AMS](../features/ams.uk.md). Вологість, температура й керування сушінням потребують відповідної можливості, яку повідомляє пристрій.

[^network]: LAN-режим не означає наявності Ethernet. У документах виробника для [X1/X1C](https://cdn1.bambulab.com/documentation/quick-start-2024-01-17/Quick-Start-X1%26X1C_en.pdf), [P1S](https://cdn1.bambulab.com/documentation/quick-start-2024-01-17/Quick-Start-P1S_en.pdf) та [P2S](https://csm.bblcdn.com/hub/2ddc44d3a72443ba914efe0f963fbbc5.pdf) зазначено бездротове підключення; [X1E](https://cdn1.bambulab.com/x1e/spec/Bambu%20Lab%20X1E%20Technical%20Specification.pdf) має Ethernet.

[^swap]: Swap mode офіційно підтримується на серії A1. Інші моделі можуть
опт-ін через власні swap-mode G-code макроси, але фабричних профілів для
них не постачається.

[^a2l]: A2L — це нова **single-extruder** модель: її друга голова це
інтегрований різак/плоттер, **а не** друге сопло. Вона **лише Wi-Fi** (без
Ethernet-порту), віддає **низькочастотну chamber-image камеру** на порту 6000
(без RTSP / 30 FPS) і належить до класу обслуговування **Linear Rails**.
Підтримка AMS виведена з firmware-можливості "print-while-drying" (яка
потребує heated AMS); тонші деталі AMS ще звіряються на реальному залізі.

---

## :material-connection: Вимоги до підключення

Для всіх принтерів потрібно:

- **Developer Mode** увімкнений (надає доступ через LAN)
- **SD-карта** встановлена (для передачі файлів)
- **Та сама мережа**, що й сервер BamDude

| Порт | Протокол | Призначення |
|------|----------|-------------|
| 8883 | MQTT/TLS | Зв'язок з принтером |
| 990 | FTPS | Передача файлів |

> Початково базується на документації [Bambuddy](https://github.com/maziggy/bambuddy).
