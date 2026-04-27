---
title: AI-детекція фейлів Obico
description: Опційна ML-детекція фейлів друку з відповідями notify / pause / pause-and-power-off
---

# AI-детекція фейлів Obico

BamDude має опційну інтеграцію з [Obico](https://www.obico.io/) — ML-сервісом, що дивиться на кадри з камери під час друку і ловить spaghetti / фейли до того, як це вилізе боком. Інтеграція **вимкнена за замовчуванням**. Коли увімкнена — поллить кадри камери, віддає в Obico ML-endpoint, згладжує результат у часі, і при стійкому фейлі або нотіфаїть, або паузить друк, або паузить + вимикає принтер через розумну розетку.

## :material-shield-check: Коли це корисно

Obico найбільше виграє на unattended нічних прогонах і автоматизації ферми. Ловить:

- Відрив / spaghetti на перших ~20 шарах
- Mid-print blob-of-death від невдалої retraction чи layer-shift
- Заклеювання столу на multi-spool друках

Це **не** заміна моніторингу першого шару чи нотифікацій HMS — ті ловлять інші типи фейлів швидше.

## :material-cog: Налаштування

1. Підніми Obico ML-сервер сам (або використай публічний — див. документацію Obico).
2. Відкрий **Settings → Integrations → Obico AI**.
3. Постав галочку **Enable Obico failure detection**.
4. Заповни:

    | Налаштування | Примітки |
    |---|---|
    | **ML API URL** | Повний URL, який Obico публікує для класифікації (наприклад `https://obico.example.com/api/v1/octo/`). |
    | **Sensitivity** | `low` / `medium` / `high`. Контролює поріг, на якому окремий кадр класифікується як "warning" чи "failure". |
    | **Action on sustained failure** | `notify`, `pause` або `pause_and_off`. Деталі нижче. |
    | **Poll interval** | Секунди між захопленням кадрів (5–120). Менше = швидша реакція, більше bandwidth + витрат на ML. |
    | **Enabled printers** | Per-printer toggle list. Лиши все увімкненим або обмеж конкретними принтерами (наприклад тільки нічний unattended). |

5. **Save**. Obico-цикл стартує одразу для будь-якого принтера в `RUNNING` стані.

## :material-radar: Як працює детекція

Цикл поллить кожен увімкнений друкуючий принтер з заданим інтервалом:

1. **Capture** — BamDude бере кадр з локальної камери принтера (без участі Bambu Cloud).
2. **Stash** — JPEG іде в in-process кеш під 32-байтним random nonce з TTL 30 секунд.
3. **Hand off** — BamDude відправляє Obico ML API URL, що вказує назад на `/api/v1/obico/cached-frame/{nonce}`. Obico-сервер фетчить цей URL і запускає класифікатор. (Тому й `APP_URL` важливий — він має бути reachable з Obico-хоста.)
4. **Score smoothing** — сирі скори проганяються через exponentially-weighted moving average **плюс** dual rolling mean. Один "warning"-кадр нічого не тригерить; стійкі скори вище failure-порогу — тригерять.
5. **Action** — коли згладжений скор переходить failure-поріг:

    | Action | Що відбувається |
    |---|---|
    | `notify` | Спрацьовує сповіщення через стандартний канал `printer_error` (Telegram зі знімком, email тощо), позначене `error_type='ai_failure_detection'`. Окремої події `obico_failure` немає — Obico-алерти їдуть тими ж провайдерами і quiet-hours, як і будь-яка printer-помилка. |
    | `pause` | Шле pause MQTT-команду на принтер. Сповіщення провайдера все одно йде. |
    | `pause_and_off` | Паузить принтер **і** після короткої затримки вимикає прив'язану розумну розетку, щоб принтер встиг чисто записати end-state. Це для unattended overnight, коли краще вирубити живлення, ніж марнувати пластик. |

## :material-key-variant: Чому cached-frame URL у whitelist?

`/api/v1/obico/cached-frame/{nonce}` — один з небагатьох ендпоінтів, що **обходить** always-on auth gate — Obico ML-сервер не може відправити bearer-токен для одноразового GET. 32-байтний nonce + 30-секундний TTL — це поверхня безпеки; без nonce — 404. Шлях звільнений тільки в `auth_middleware` whitelist.

Через це Obico URL має бути reachable з ML-хоста. Якщо ти за reverse proxy — переконайся, що `/api/v1/obico/cached-frame/` не блокується додатковим auth-шаром у nginx.

## :material-tune: Tuning чутливості

Стартуй на `medium`. Якщо Obico кричить "failure" на кожен retraction-blob — впади на `low`. Якщо пропускає очевидні детачі — підніми на `high`. Smoothing означає, що окремий кадр-outlier action не тригерне — потрібна стійка confidence над порогом.

Точні пороги — у `backend/app/services/obico_smoothing.py`; за замовчуванням консервативні (щоб не false-trip-нути на reference-датасеті Obico).

## :material-eye: Що бачить Obico

Detection panel під **Settings → Integrations → Obico AI** показує останнє рішення на принтер (згладжений скор, класифікація, остання action), плюс live-мініатюру кадру, який Obico щойно подивився. Корисно для тюнингу sensitivity, не чекаючи реального фейлу.

## :material-power-off: Fail-safe поведінка

Якщо API Obico недосяжне або повертає non-2xx:

- Помилка логується на `WARNING`, не `ERROR` (без спам-stack-trace-ів).
- Detection loop продовжує — transient outage не вимикає детекцію назавжди.
- Жодна несправжня "failure"-action не фірить з пропущеної класифікації.

Якщо `obico_enabled` вимикають посеред друку — цикл зупиняється на наступній ітерації; друк триває без перерви.
