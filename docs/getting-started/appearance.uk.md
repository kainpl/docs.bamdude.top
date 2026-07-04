---
title: Appearance
description: Тема Dark / Light / System, per-mode style, background і accent-колір — усе client-side і per-device
---

# Appearance

Вигляд BamDude повністю налаштовується per-device в **Settings → Appearance**. Кожен вибір зберігається у браузері (`localStorage`), тож кожен твій пристрій / браузер може виглядати по-різному — тема це display-налаштування, яке ніколи не пушиться на сервер і не шариться між користувачами.

---

## :material-theme-light-dark: Режим теми

Три режими, вибираються три-кнопковим селектором у **Settings → Appearance** (або цикляться кнопкою теми в сайдбарі, **Dark → Light → System**):

| Режим | Поведінка |
|---|---|
| **Dark** | Завжди темна. |
| **Light** | Завжди світла. |
| **System** | Слідує за light/dark-налаштуванням твоєї операційної системи і перемикається автоматично разом з ОС (через `prefers-color-scheme`). |

**System** резолвиться вживу в той режим, у якому зараз твоя ОС, і застосовує style / background / accent саме цього режиму (нижче). Перемкнув ОС між light і dark вночі — BamDude перемкнеться разом з нею, без reload.

---

## :material-palette-outline: Стилізація per-mode

Dark і Light тримають кожен **свій незалежний** style, background і accent — тож можеш, наприклад, гнати vibrant-темну тему вночі й просту світлу вдень, а **System** підхопить правильний набір автоматично.

| Налаштування | Опції Dark | Опції Light |
|---|---|---|
| **Style** | Classic · Glow · Vibrant | Classic · Glow · Vibrant |
| **Background** | Neutral · Warm · Cool · OLED · Slate · Forest | Neutral · Warm · Cool |
| **Accent** | Green · Teal · Blue · Orange · Purple · Red | Green · Teal · Blue · Orange · Purple · Red |

- **Style** керує загальним оформленням поверхонь (плаский *Classic*, м'який *Glow* чи насичений *Vibrant*).
- **Background** задає базовий відтінок канви — *OLED* це справжній чорний для економії на OLED-панелях; *Slate* / *Forest* — темніші тоновані варіанти.
- **Accent** перефарбовує кнопки, посилання, active-стани й підсвітки.

Твої dark- і light-вибори запам'ятовуються окремо й реаплаяться щоразу, коли цей режим стає активним (зокрема коли **System** перемикається між ними).

---

!!! note "Per-device, не per-account"
    Appearance живе у браузері, а не на твоєму BamDude-юзері. Вхід на новому пристрої стартує з дефолтів (Dark, Classic, Neutral, Green), поки не налаштуєш там. Очищення site data браузера скидає його.
