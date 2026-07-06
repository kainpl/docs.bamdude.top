---
title: API Keys
description: Сервісні токени для headless-скриптів, інтеграцій і webhook-колбеків через BamDude REST API
---

# API Keys

API keys — спосіб дозволити нелюдському клієнту говорити з BamDude: Home Assistant, Node-RED, CI-скрипт, твій власний дашборд. Кожен ключ — довгий рандомний `bb_…` токен, який проходить ті ж permission-гейти, що й людська сесія: ключ, який може читати принтери, не може раптом запустити друк просто тому, що ввічливо попросив.

Auth завжди увімкнений (див. [Authentication](authentication.md)) — ключ це headless-еквівалент залогіненого юзера, не bypass.

---

## :material-shape: Формат токена

| Поле | Значення |
|---|---|
| **Префікс** | `bb_` (літерально) |
| **Тіло** | 32 рандомних байти, base64-url-encoded — 43 символи |
| **Повна довжина** | 46 символів |
| **At rest** | Хешований (`get_password_hash`); у відкритому вигляді зберігаються тільки префікс + ім'я |
| **Показується** | Один раз, у відповіді на створення. Загубив — ревокни і генеруй новий |

```
bb_VGhpc0lzVGhlVGVzdEtleVNvUGxlYXNlSWdub3JlMTIz
└┬┘ └─────────────────────────────────────────┘
prefix              random body
```

!!! warning "Один шанс показати"
    Повний токен повертається тільки у відповіді `POST /api/v1/api-keys/`. BamDude ніколи не зберігає його у відкритому вигляді — на сторінці списку немає кнопки "show key". Загубив — видали рядок і створи новий.

---

## :material-key-plus: Створення ключа

**Settings → API Keys → New API key.**

| Поле | Призначення |
|---|---|
| **Name** | Людський лейбл — називай ключі за consumer-ом (`Home Assistant Dashboard`, `Print-farm Grafana`, `n8n queue-poster`), щоб потім легко знаходити в списку |
| **Can queue** | Дозволити цьому ключу додавати завдання в чергу (`POST /queue`) |
| **Can control printer** | Дозволити команди start / pause / stop / cancel |
| **Can read status** | Дозволити live-стан принтера, списки архівів, статистику — read-поверхню |
| **Manage Library** | Опціонально. Завантаження / перейменування / переміщення / видалення файлів бібліотеки — **будь-якого власника**, не лише творця ключа — плюс нотатки й імпорт з MakerWorld (`can_manage_library`). Read-only доступ до бібліотеки лишається під **Can read status** |
| **Manage Inventory** | Опціонально. Створення / редагування / видалення котушок, записів каталогу й налаштувань прогнозу (`can_manage_inventory`). Read-only інвентар лишається під **Can read status** |
| **Use Bambu Cloud** | Опціонально. Коли ввімкнено, ключ резолвить per-user Bambu Cloud-токен юзера-творця для маршрутів `cloud:*` (slicer presets, MakerWorld imports). За замовчуванням вимкнено, щоб legacy-ключі не могли мовчки витрачати cloud-token власника. Відхиляється при збереженні на ownerless-ключах — див. примітку про значки нижче. |
| **Printer scope** | Опціонально. Залиш порожнім для "усіх принтерів", або обери конкретні printer ID, щоб звузити ключ. Дзвінки до інших принтерів повертатимуть 403 |
| **Expires at** | Опційний ISO timestamp. Після нього ключ відкидається, навіть якщо не ревокнутий |

Відповідь на створення містить поле `key` — **скопіюй його до закриття діалогу**. Подальші читання рядка показуватимуть тільки `bb_…` префікс.

!!! info "Значки Cloud / Legacy"
    Ключі, створені через UI, стампляться id юзера-творця, тож ключ з значком **Cloud** може витрачати Bambu Cloud-токен цього юзера. Pre-0.4.3 ключі, імпортовані зі старіших інсталяцій, ownerless і відображаються зі значком **Legacy** — їх не підняти до `Use Bambu Cloud` (тогл відхиляється при збереженні без owner-а). Перестворіть такі ключі під своїм юзер-аккаунтом, щоб увімкнути cloud spend.

!!! tip "Принцип найменших привілеїв"
    Не ткай усі прапорці підряд. HA-дашборд зазвичай потребує тільки `can_read_status`. Queue-poster зі слайсера потребує `can_queue` + `can_read_status` і *не* `can_control_printer`. Інтеграція-аплоадер тепер може отримати `can_manage_library` без `can_queue`. Окремі ключі на consumer-а роблять ротацію безболісною, а audit trail — читабельним.

---

## :material-send-lock: Як відправляти ключ

Обидві форми хедера приймаються — обери ту, що зручна твоєму клієнту.

```bash
# X-API-Key хедер (preferred для тулзів, які розрізняють "API key" і "Bearer token")
curl -H "X-API-Key: bb_..." http://localhost:8000/api/v1/printers/

# Authorization: Bearer — працює, бо сервер бачить bb_ префікс
# і йде по API-key-валідатору замість JWT-валідації.
curl -H "Authorization: Bearer bb_..." http://localhost:8000/api/v1/printers/
```

Обидва шляхи доходять до того самого коду. Префікс `bb_` на `Bearer` токені каже BamDude що це API key, не сесійний JWT, тож JWT-signature path пропускається — запускається key-hash порівняння.

---

## :material-shield-key: Permission модель

Два шари гейтять кожен API-keyed дзвінок:

1. **Required permission ендпоінта** перевіряється. API keys обходять *user* permission-чеки (бо не належать жодній групі), але…
2. **Прапорці самого ключа** — ось вони:
    - `can_queue` — потрібен для `POST /queue` і queue-mutation ендпоінтів (+ archive reprint, який енкʼюїть наявний архів)
    - `can_control_printer` — для start / pause / stop / cancel (+ smart-plug control)
    - `can_read_status` — для printer-state, archive, stats, monitoring (і read-only бібліотека / інвентар / settings-language)
    - `can_manage_library` — для library upload / rename / move / delete + notes + імпорт з MakerWorld. Ключ їде на **all-ownership** варіантах (`library:update_all` / `library:delete_all`): API-ключі не несуть per-row ідентичності власника, тож Manage-Library ключ може курувати **будь-який** файл незалежно від власника. Лише `library:purge` (hard-delete поза вікном trash) лишається admin-only
    - `can_manage_inventory` — для spool / catalog / forecast **writes** (read-only інвентар лишається під `can_read_status`)
    - `can_access_cloud` — для cloud-token-backed ендпоінтів (slicer presets, MakerWorld)
    - `can_update_energy_cost` — для `POST /settings/electricity-price` (вузько-обмежений Home-Assistant dynamic-tariff endpoint — див. [Energy → Tibber / Octopus / Dynamic Tariff Integration](energy.uk.md#tibber--octopus--dynamic-tariff-integration)). НЕ дає загальний `SETTINGS_UPDATE`.
3. **`printer_ids` scope** звужує printer-bound дзвінки. Ключ з `printer_ids = [3, 7]` поверне 403 на `/printers/5/status`, навіть якщо `can_read_status=true`.

!!! warning "Сувора ізоляція scope-ів"
    Ключ тепер дістає **тільки** ті ендпоінти, які покривають його видані scope-и. Усе поза ними — settings writes, user / group / API-key адміністрування, видалення ресурсів (принтери, архіви, проєкти), network discovery scan — відхиляється з `403`, навіть для валідного, увімкненого ключа. Раніше будь-який валідний ключ дотягувався майже до кожного ендпоінта (start/stop друку, reorder черги, reprint архівів, видалення чужих файлів бібліотеки, читання будь-якого ресурсу) *незалежно* від того, які прапорці scope на ньому стояли — upstream advisory **GHSA-r2qv-8222-hqg3** (CVSS 9.9 critical). Мапінг — allowlist: permission без scope-запису відхиляється за замовчуванням, тож новододаний admin-ендпоінт ніколи не буде мовчки доступний ключу.

!!! info "Успадкування на апгрейді"
    Два scope-и, додані цього циклу — `can_manage_library` і `can_manage_inventory` — на апгрейді бекфіляться зі значення `can_queue` (**Manage Queue**) кожного ключа. Queue-enabled ключ зберігає свій попередній upload + inventory-write workflow, а захардений read-only ключ (`can_queue = false`) не отримує нічого. Далі коригуй будь-який scope через `PATCH /api-keys/{id}`.

Permissions, що гейтять **управління** самими ключами (хто може list / create / revoke), — звичайні permission-и юзер-груп:

| Permission | Видається |
|---|---|
| `api_keys:read` | Адміністраторам |
| `api_keys:create` | Адміністраторам |
| `api_keys:update` | Адміністраторам |
| `api_keys:delete` | Адміністраторам |

Operators і Viewers за замовчуванням не керують ключами — видача сервіс-аккаунт-кредів це admin-task.

---

## :material-clock-outline: Lifecycle ключа

| Поле | Коли пишеться |
|---|---|
| `created_at` | На створенні |
| `last_used` | Оновлюється валідатором на кожному успішному запиті — корисно для пошуку забутих ключів |
| `expires_at` | Опціонально. Після — 401 навіть при `enabled=True` |
| `enabled` | Soft-disable перемикач. `PATCH /api-keys/{id}` з `enabled=false` ставить ключ на паузу без видалення |

Дзвінки з disabled, expired або невідомим ключем отримують `401 Unauthorized` з однорядковим "API key required / invalid" — без витоку інфи про причину.

---

## :material-server-network: Часті ендпоінти

| Endpoint | Method | Required flag |
|---|---|---|
| `/printers/` | GET | `can_read_status` |
| `/printers/{id}/status` | GET | `can_read_status` |
| `/printers/{id}/control/start` | POST | `can_control_printer` |
| `/printers/{id}/control/pause` | POST | `can_control_printer` |
| `/printers/{id}/control/stop` | POST | `can_control_printer` |
| `/queue/` | GET | `can_read_status` |
| `/queue/` | POST | `can_queue` |
| `/queue/{id}` | DELETE | `can_queue` |
| `/archives/` | GET | `can_read_status` |
| `/statistics` | GET | `can_read_status` |

Повна схема — `GET /openapi.json` — у `security`-блоці кожного route-а вказано, які кредентіали приймаються.

---

## :material-laptop: Приклади

### `curl`

```bash
# Прочитати стан принтера
curl -s -H "X-API-Key: bb_..." http://localhost:8000/api/v1/printers/3/status \
  | jq '.state, .progress'

# Додати library-файл до черги
curl -X POST http://localhost:8000/api/v1/queue/ \
  -H "X-API-Key: bb_..." \
  -H "Content-Type: application/json" \
  -d '{"printer_id": 3, "library_file_id": 142, "quantity": 1}'
```

### Python (`requests`)

```python
import os, requests

BASE = "http://bamdude.lan:8000/api/v1"
KEY = os.environ["BAMDUDE_API_KEY"]
HEADERS = {"X-API-Key": KEY}

# Знайти перший idle-принтер
for p in requests.get(f"{BASE}/printers/", headers=HEADERS).json():
    state = requests.get(f"{BASE}/printers/{p['id']}/status", headers=HEADERS).json()
    if state["state"] == "IDLE":
        print(f"{p['name']} idle, ready to dispatch")
        break
```

### Home Assistant `rest_command`

```yaml
rest_command:
  bamdude_pause_printer:
    url: "http://bamdude.lan:8000/api/v1/printers/{{ printer_id }}/control/pause"
    method: POST
    headers:
      X-API-Key: !secret bamdude_api_key
```

Тригер з будь-якої автоматизації: `service: rest_command.bamdude_pause_printer` з `data: {printer_id: 3}`.

### Node-RED

Кидай **HTTP request** node, став URL `http://bamdude.lan:8000/api/v1/printers/`, додай хедер `X-API-Key` зі своїм ключем, чейн **debug** або **switch**. Для багатьох ендпоінтів зберігай ключ один раз у глобальному context-варіаблі і інжекти через function node.

### Webhook колбеки (`X-API-Key` на приймачі)

Якщо ти відправляєш notification webhook (див. [Notifications](notifications.md)) на свій *власний* receiver і хочеш, щоб він автентифікувався назад у BamDude, та сама `X-API-Key` хедер-конвенція працює — твій receiver отримує BamDude-payload, потім робить callback у BamDude по контекст зі своїм API key. BamDude сам не підписує outgoing webhooks; захищай receiver IP allow-listом або проксі-шаром, який вимагає секретний хедер.

---

## :material-cancel: Ревокування

| Дія | Endpoint | Ефект |
|---|---|---|
| **Soft disable** | `PATCH /api-keys/{id}` з `enabled=false` | Ключ одразу повертає 401. Реверсибельно — постав `enabled=true` назад |
| **Hard delete** | `DELETE /api-keys/{id}` | Рядок зникає з БД. Не відновити — створюй новий |
| **Expire** | Постав `expires_at` у минулому | Валідатор трактує як expired, повертає 401 |

Після будь-якої з цих дій in-flight запити, які вже пройшли валідатор, дотрібнюються (валідатор працює раз на запит); *наступний* запит від цього ключа фейлиться. Глобального кешу чекати не треба.

!!! tip "Аудит до ротації"
    Перед видаленням заглянь у `last_used` на списку. Ключ, що рік не використовувався, безпечно видалити; ключ, що використовувався 30 секунд тому, має активного consumer-а, який зараз почне фейлитись. Координуй ротацію з restart-вікном consumer-а.

---

## :material-shield-check: Best practices

- **Назви ключі за consumer-ом.** `n8n-print-trigger` краще за `key1`. Майбутній ти, що грепає список о 2:00, скаже спасибі.
- **Один ключ — один consumer.** Простіша ротація, простіший revoke, окремий `last_used` каже хто ще ним користується.
- **Звужуй прапорці.** Read-only ключ — на одну футгану менше. Printer-scoped ключ не може mass-cancel-нути ферму.
- **Став `expires_at`** для коротких інтеграцій (CI, демо). Auto-expiry дешевше за "не забути ревокнути".
- **Не комітити ключі.** `.env`, secret managers, HA secrets, k8s `Secret` — будь-де, тільки не в repo.
- **Ротуй періодично.** Особливо коли контрибутор іде, або ноут пропадає. Створи новий → переключи consumer-а → видали старий.
- **Моніторь `last_used`.** Read-only ключ, який раптом тригерить о 3:00 з нової IP — корисний рання попередження.

---

## :material-help-circle: Troubleshooting

??? question "401 Unauthorized — `API key required`"
    Нема ні `X-API-Key`, ні `Authorization` хедера. Додай один з них. Якщо за проксі, що зрізає кастомні хедери — переключайсь на `Authorization: Bearer bb_…`.

??? question "401 Unauthorized — а ключ начебто правильний"
    Перевір `enabled` на рядку, потім `expires_at`. `PATCH` назад на `enabled=true` оживляє soft-disabled ключ. Expired ключ треба замінити — `expires_at` одностороння вулиця.

??? question "403 Forbidden на принтері, який мій"
    `printer_ids` scope ключа встановлений і не містить цього принтера. Або розширюй scope (`PATCH` з новим id-листом), або використовуй інший ключ.

??? question "403 Forbidden на `/queue` POST з `can_queue=true`"
    Деякі queue-мутації зачіпають бібліотеку; payload, що аплоадить файл, потребує окремого scope **Manage Library** (`can_manage_library`) — він не покривається `can_queue`.

??? question "403 Forbidden на записі library / inventory з queue-enabled ключем"
    Після суворої ізоляції scope-ів записи в бібліотеку потребують `can_manage_library`, а записи в інвентар — `can_manage_inventory`; вони більше не мають на увазі `can_queue`. На апгрейді їх бекфілнуло з `can_queue`, але ключ, зроблений read-only, або створений після розділення, потребує їх увімкнення явно. `PATCH /api-keys/{id}` зі scope-ом, потім ретрай.

??? question "Ключ працює на статусі, але не на `/control/start`"
    `can_control_printer` вимкнений. Увімкни через `PATCH`, потім ретрай — створювати новий ключ не треба.
