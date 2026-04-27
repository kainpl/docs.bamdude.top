---
title: Підтримувані принтери
description: Інформація про сумісність моделей принтерів Bambu Lab
---

# Підтримувані принтери

BamDude підтримує всі 3D-принтери Bambu Lab з можливістю Developer Mode.

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
| **A1** | A1 | :material-check: | AMS Lite |
| **A1 Mini** | A1 | :material-check: | :material-close: |

---

## :material-printer-3d: Особливості за серіями

### Серія X1

- Обігрів камери
- До 4 блоків AMS
- Повна підтримка камери (до 30 FPS)

### Серія H2

- H2D / H2D Pro: подвійне сопло зі статусом лівого/правого сопла
- H2C: стійка для 6 сопел (tool changer)
- Обігрів камери

### Серія P1

- P1P потребує додаткової камери
- До 4 блоків AMS
- Камера обмежена ~5 FPS

### Серія A1

- A1: підтримка AMS Lite
- A1 Mini: лише зовнішня котушка, основна ціль для [режиму заміни](../features/swap-mode.md)
- Камера обмежена ~5 FPS

---

## :material-table-check: Матриця можливостей BamDude { #bamdude-capability-matrix }

Таблиця показує, які функції BamDude вмикаються per-серія. Незаповнені
клітинки — або залізо не публікує дані, або біт протоколу не верифіковано,
або клас моделі не застосовний — BamDude не показує фейкового стану в таких
випадках.

| Можливість | X1 | P1P | P1S | P2S / X2D | A1 | A1 Mini | H2D / H2D Pro | H2C | H2S |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| Камера (вбудована) | :material-check: | додатково | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: |
| 30 FPS-стрім | :material-check: | — | — | — | — | — | :material-check: | :material-check: | :material-check: |
| Ethernet-порт | лише X1C/X1E | — | :material-check: | :material-check: | — | — | :material-check: | :material-check: | :material-check: |
| Обігрів камери | :material-check: | — | пасивна | :material-check: | — | — | :material-check: | :material-check: | :material-check: |
| Сенсор дверей (MQTT) [^door] | :material-check: | n/a [^opentop] | — [^bit23] | — [^bit23] | n/a [^opentop] | n/a [^opentop] | — [^bit23] | — [^bit23] | — [^bit23] |
| Подвійне сопло (L/R) | — | — | — | — | — | — | :material-check: | — | — |
| 6-слотовий tool changer | — | — | — | — | — | — | — | :material-check: | — |
| AMS Pro (4-слотовий) | до 4 | до 4 | до 4 | до 4 | — | — | до 4 | до 4 | до 4 |
| AMS Lite | — | — | — | — | :material-check: | — | — | — | — |
| Зовнішня котушка | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | лише вона | :material-check: | :material-check: | :material-check: |
| AMS-HT (single-slot 128–135) | — | — | — | — | — | — | :material-check: | :material-check: | :material-check: |
| AMS humidity / temperature alerts | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: [^lite] | — | :material-check: | :material-check: | :material-check: |
| Обслуговування — Carbon Rods | :material-check: | :material-check: | :material-check: | — | — | — | — | — | — |
| Обслуговування — Steel Rods | — | — | — | :material-check: | — | — | — | — | — |
| Обслуговування — Linear Rails | — | — | — | — | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: |
| Swap mode (виштовхування) [^swap] | — | — | — | — | :material-check: | :material-check: | — | — | — |
| Vibration-cali skip патчер | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: |
| Skip-objects посеред друку | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: | :material-check: |

[^door]: Стан дверей парситься з `home_flag` біт 23 у MQTT. Лише X1-сімейство
прошивки реверс-енджинірно публікує надійне значення; не позначені у
списку enclosed-моделі публікують біт як завжди-нуль на спостережуваних
прошивках, тому BamDude відмовляється показувати оманливий бейдж "Двері
зачинені". Див. `backend/app/utils/printer_models.py::DOOR_SENSOR_MODELS`.

[^opentop]: Open-frame принтери фізично не мають дверей — нічого
сенсорити.

[^bit23]: Enclosed-модель, у якої `home_flag` біт 23 не підтверджено
flip-ається. Буде ввімкнено, як тільки звіримо на реальному принтері; не
запитуйте на спекуляції.

[^lite]: AMS Lite звітує humidity, але не AMS-HT sub-стрім.

[^swap]: Swap mode офіційно підтримується на серії A1. Інші моделі можуть
опт-ін через власні swap-mode G-code макроси, але фабричних профілів для
них не постачається.

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
