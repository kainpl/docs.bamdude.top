---
title: AI-детекція фейлів Obico
description: Опційна ML-детекція фейлів друку з відповідями notify / pause / pause-and-power-off
---

# AI-детекція фейлів Obico

BamDude має опційну інтеграцію з **self-hosted** [Obico](https://github.com/TheSpaghettiDetective/obico-server) `ml_api` — ML-сервісом, що дивиться на кадри з камери під час друку і ловить spaghetti / фейли до того, як це вилізе боком. Інтеграція **вимкнена за замовчуванням**. Коли увімкнена — поллить кадри камери, віддає в Obico ML-endpoint, згладжує результат у часі, і при стійкому фейлі або нотіфаїть, або паузить друк, або паузить + вимикає принтер через розумну розетку.

!!! info "Тільки self-hosted — без cloud, без obico.io"
    BamDude ходить до **твого власного** Obico `ml_api` через HTTP у локальній мережі. Жодного коннекту до obico.io, жодної реєстрації принтера в Obico web app, жодного WebSocket, жодних кадрів кудись за межі LAN. Кадри живуть у 30-секундному in-process кеші; єдиний зовнішній отримувач snapshot URL — ML-контейнер, який ти контролюєш.

## :material-shield-check: Коли це корисно

Obico найбільше виграє на unattended нічних прогонах і автоматизації ферми. Ловить:

- Відрив / spaghetti на перших ~20 шарах
- Mid-print blob-of-death від невдалої retraction чи layer-shift
- Заклеювання столу на multi-spool друках

Це **не** заміна моніторингу першого шару чи нотифікацій HMS — ті ловлять інші типи фейлів швидше.

## :material-server: Self-host Obico ML API

Тобі потрібен лише `ml_api` контейнер зі стека Obico. Web app, Django site і реєстрація принтера **не потрібні** — BamDude не говорить Obico printer-protocol-ом, тільки сирим classification HTTP-endpoint-ом.

### 1. Клонуй Obico server

```bash
git clone -b release https://github.com/TheSpaghettiDetective/obico-server.git
cd obico-server
```

### 2. Виставь порт 3333

Відредагуй `docker-compose.yml` і додай `ports` мапінг на сервісі `ml_api`:

```yaml
ml_api:
  ports:
    - "3333:3333"
```

### 3. Запусти лише `ml_api`

```bash
docker compose up -d ml_api
```

Перший старт скачує YOLO-модель (~100 MB) і алокує приблизно 4 GB RAM у runtime. Плануй capacity відповідно, якщо хостиш на маленькому сервері.

### 4. Перевір

```bash
curl http://<obico-host>:3333/hc/
# → "ok"
```

Якщо `/hc/` повертає `ok` — ML API готовий до BamDude.

---

## :material-cog: Налаштування

1. Підніми Obico ML-сервер за кроками вище.
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

!!! warning "External URL має бути виставлений"
    **Settings → Network → External URL** — це URL, який ML-контейнер використовуватиме для фетчу кешованого кадру. Obico-контейнер сам ходить за `/<external-url>/api/v1/obico/cached-frame/{nonce}`; URL має резолвитись зсередини network namespace того контейнера, не з твого браузера. Зазвичай це LAN IP BamDude-хоста. Без нього BamDude не стартує цикл — побачиш `external_url not set — ML API cannot reach snapshot endpoint`.

### Sensitivity Low / Medium / High

| Рівень | Ефект |
|---|---|
| **Low** | Вищий confidence threshold; менше false positives, але повільніше алертить і може пропустити тонкі ранні фейли. |
| **Medium** | Оригінальні пороги Obico — рекомендована стартова точка. |
| **High** | Нижчий поріг; алертить раніше, більше false positives на retraction-blob-ах / тінях / camera glare. |

## :material-radar: Як працює детекція

Цикл поллить кожен увімкнений друкуючий принтер з заданим інтервалом:

1. **Capture** — BamDude бере кадр з локальної камери принтера (без участі Bambu Cloud).
2. **Stash** — JPEG іде в in-process кеш під 32-байтним random nonce з TTL 30 секунд.
3. **Hand off** — BamDude відправляє Obico ML API URL, що вказує назад на `/api/v1/obico/cached-frame/{nonce}`. Obico-сервер фетчить цей URL і запускає класифікатор. (Тому й `APP_URL` важливий — він має бути reachable з Obico-хоста.)
4. **Score smoothing** — сирі скори проганяються через exponentially-weighted moving average **плюс** dual rolling mean. Один "warning"-кадр нічого не тригерить; стійкі скори вище failure-порогу — тригерять.

    Конкретно: **30-frame warmup** на старті кожного друку — це "не вір нічому" (~5 хвилин при default 10-секундному poll-інтервалі); після warmup сирі скори годуються в EWM з `alpha = 2/13` для short-window smoothing (~5 хв еквівалент) плюс long rolling-mean baseline (~20 годин при 10 с/кадр) — для попередження false-positive-ів від поступового environmental drift-у. Це той самий підхід, що використовує власний детектор Obico upstream.
5. **Action** — коли згладжений скор переходить failure-поріг:

    | Action | Що відбувається |
    |---|---|
    | `notify` | Спрацьовує окрема подія **AI Failure Detection** — самостійний **opt-in** тригер (вимкнений за замовчуванням) з власним шаблоном, виділений з `printer_error`, щоб можна було отримувати AI-алерти, не отримуючи пейдж на кожен HMS hardware-код. Алерт несе принтер, назву завдання, confidence-скор і вжиту дію. Підписуйся на неї окремо: кожен провайдер має власний тумблер **AI Failure Detection**, а Telegram додає відповідний per-chat notify-пункт. |
    | `pause` | Шле pause MQTT-команду на принтер. Сповіщення провайдера все одно йде. |
    | `pause_and_off` | Паузить принтер **і** після короткої затримки вимикає прив'язану розумну розетку, щоб принтер встиг чисто записати end-state. Це для unattended overnight, коли краще вирубити живлення, ніж марнувати пластик. |

## :material-key-variant: Чому cached-frame URL у whitelist?

`/api/v1/obico/cached-frame/{nonce}` — один з небагатьох ендпоінтів, що **обходить** always-on auth gate — Obico ML-сервер не може відправити bearer-токен для одноразового GET. 32-байтний nonce + 30-секундний TTL — це поверхня безпеки; без nonce — 404. Шлях звільнений тільки в `auth_middleware` whitelist.

Через це Obico URL має бути reachable з ML-хоста. Якщо ти за reverse proxy — переконайся, що `/api/v1/obico/cached-frame/` не блокується додатковим auth-шаром у nginx.

## :material-tune: Tuning чутливості

Стартуй на `medium`. Якщо Obico кричить "failure" на кожен retraction-blob — впади на `low`. Якщо пропускає очевидні детачі — підніми на `high`. Smoothing означає, що окремий кадр-outlier action не тригерне — потрібна стійка confidence над порогом.

Точні пороги — у `backend/app/services/obico_smoothing.py`; за замовчуванням консервативні (щоб не false-trip-нути на reference-датасеті Obico).

## :material-eye: Що бачить Obico

Detection panel під **Settings → Integrations → Obico AI** розбита на Status card і стрічку Recent detections:

**Status card**

- Прапор background-сервісу running (зелений / червоний).
- Активні значення порогу після sensitivity-scaling (щоб sanity-чекнути, що Low / Medium / High реально підкрутили цифри).
- На кожен поточно-друкуючий моніторений принтер:
    - Жива класифікація — `safe` / `warning` / `failure`
    - Згладжений скор (post-EWM число, що порівнюється з порогом)
    - Скільки кадрів побачено в цьому друці (видно warmup-countdown)

**Recent detections** — хронологічний список останніх подій з timestamp, принтером, класифікацією, скором і мініатюрою кадру, що пересік поріг. Корисно для тюнингу sensitivity без чекання реального фейлу.

---

## :material-alert-circle: Вимоги і підводні камені

- **Двостороння reachability.** BamDude має дістати ML API на `http://<obico-host>:3333/p/`, **і** ML-контейнер має дістати BamDude на `<external-url>/api/v1/obico/cached-frame/{nonce}`. Якщо вони в одній Docker-мережі — використовуй hostname BamDude-контейнера; на різних хостах — LAN IP. `localhost` працює лише коли обидва на одному хості.
- **External URL обов'язковий.** Без **Settings → Network → External URL** BamDude нема чого віддати ML API; цикл відмовляється стартувати.
- **Public URL caveat при reverse-proxy auth.** Cached-frame route обходить always-on auth gate BamDude (ML-контейнер не може віддати bearer для одноразового GET), тож переконайся що твій nginx / Caddy / Traefik не накладає **свій** auth-шар на `/api/v1/obico/cached-frame/`. Власна security-поверхня route — 32-байтний випадковий nonce + 30-секундний TTL — без nonce 404.
- **Calibration-друки скіпаються.** Detection loop крутиться лише поки друк у `RUNNING` стані, тож calibration / first-layer фаза не класифікується — Bambu-калібрації створюють надто багато форм, що ще не є реальними фейлами.
- **Перші 30 кадрів ігноруються.** Навіть всередині `RUNNING`, 30-frame warmup означає, що перші ~5 хвилин кожного друку навмисно тихі — даємо EWM stabilise до того, як щось тригерити.
- **Single-fire на друк.** Раз action спрацювала, наступні failure-скори в тому ж друці не ре-тригеряться. Це навмисно — не хочемо п'ять "pause"-команд одна на одну, коли spaghetti monster уже очевидний. Action state ресетиться на наступному `print_started`.
- **Камера має бути доступною.** Detection loop фетчить кадри з локальної камери принтера так само, як головний UI BamDude. Якщо camera-сторінка в UI не показує стрім — Obico теж нічого не отримає.
- **Disk / RAM.** ~4 GB RAM на Obico-хості. CPU масштабується кількістю моніторених принтерів × частотою polling-у. 5-секундний інтервал на 8 принтерів — приблизно 1.6 кадрів/сек, на більшості заліза без проблем.

---

## :material-help-circle: Усунення несправностей

**`external_url not set — ML API cannot reach snapshot endpoint`**
: Відкрий **Settings → Network** і виставь External URL на hostname або IP, що дістається зсередини Obico-контейнера. Перевір `curl`-ом цього URL з shell-а в Obico-контейнері.

**Test button повертає помилку**
: ML API недосяжне з BamDude. Перевір `docker compose ps ml_api` і спробуй `curl http://<obico-host>:3333/hc/` з BamDude-хоста. Якщо `/hc/` працює а Test ні — двічі перевір, що поле URL вживає ту ж схему (`http://` vs `https://`) і порт.

**Сервіс крутиться але детекцій нема**
: Нема новин — добрі новини. Записи лягають в історію лише коли класифікація виходить з `safe` або action фірить. Якщо реально думаєш, що Obico пропустив справжній фейл — перевір Status card, що друк поллиться, і піднімай sensitivity.

**False positives на нормальних друках**
: Опусти sensitivity High → Medium → Low. Також перевір кут камери — якщо в кадрі забагато non-print background (котушки філаменту, AMS, кіт оператора), модель має більше шансів побачити "spaghetti" в випадкових формах.

**Пропущені очевидні фейли**
: Підніми sensitivity. Пам'ятай 30-frame warmup на старті — перші ~5 хв навмисно тихі. Перевір, що камера справді показує build plate (а не лише toolhead).

**`/api/v1/obico/cached-frame/` повертає 401 / 403**
: Твій reverse proxy енфорсить власний auth-шар поверх BamDude. Виріж виняток для цього шляху; BamDude сам whitelist-ить його з always-on gate.

---

## :material-license: Ліцензія і attribution

ML-модель і алгоритми детекції Obico ліцензовані під **AGPL-3.0** — той самий ліценз, що й BamDude, тож derivative-work зобов'язання вирівняні. BamDude **не** вендорить і не лінкує жодного Obico-коду; він лише викликає ML API через HTTP. Container-image живе в реєстрі Obico; тягни його з upstream-репо `obico-server`, не з `ghcr.io/kainpl/bamdude`.

## :material-power-off: Fail-safe поведінка

Якщо API Obico недосяжне або повертає non-2xx:

- Помилка логується на `WARNING`, не `ERROR` (без спам-stack-trace-ів).
- Detection loop продовжує — transient outage не вимикає детекцію назавжди.
- Жодна несправжня "failure"-action не фірить з пропущеної класифікації.

Якщо `obico_enabled` вимикають посеред друку — цикл зупиняється на наступній ітерації; друк триває без перерви.
