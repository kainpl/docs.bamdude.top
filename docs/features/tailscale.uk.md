---
title: Інтеграція з Tailscale (приватний tailnet)
description: Анонсуй віртуальні принтери в свій Tailnet з авто-оновленими сертами Let's Encrypt і tailnet-FQDN SSDP, щоб віддалені слайсери діставались BamDude без VPN-гімнастики
---

# Інтеграція з Tailscale

BamDude може анонсувати [віртуальні принтери](virtual-printer.md) у приватну мережу [Tailscale](https://tailscale.com/) замість LAN (або разом з нею). Кожен VP отримує справжній серт Let's Encrypt прив'язаний до свого `*.tailnet-name.ts.net` FQDN, SSDP-анонс використовує цей FQDN, і віддалені слайсери — Bambu Studio / OrcaSlicer на телефоні чи лептопі десь на тайнеті — знаходять VP так само, як знайшли б у локальній мережі. Без port-forward, без додаткового VPN-клієнта, без ручної жонгляційки сертами.

Це **opt-in per VP**: існуючі сетапи продовжують анонсуватись на LAN за замовчуванням, а tailnet-флоу вмикається лише на тих VP, де ти явно його тригернеш.

---

## :material-lan-disconnect: Коли це треба

Альтернатива з коробки — [VP `proxy` mode](virtual-printer.md#proxy) — теж працює для віддаленого друку, але ганяє кожен байт через власний BamDude TCP-релей. Wire-level mesh Tailscale швидший (peer-to-peer коли можна, DERP-relayed коли ні), zero-config зі сторони слайсера, і слайсер думає, що говорить зі звичайним Bambu-принтером.

| Сценарій | Рекомендований шлях |
|---|---|
| Слайсити на лептопі в одному LAN з BamDude | Звичайний VP, Tailscale не треба. |
| Слайсити на лептопі / телефоні *off-network* (кав'ярня, відрядження) | Tailscale на VP. |
| Слайсити з CI / GitHub Actions runner | VP `proxy` mode (Tailscale на VM — overkill). |
| Multi-tenant cloud → BamDude bridge | VP `proxy` mode + твій існуючий TLS. |

Tailscale світиться особливо коли **машина, де крутиться слайсер, уже на Tailscale**, і ти хочеш, щоб вона "просто бачила" принтер.

---

## :material-package-variant: Передумови

1. **Демон Tailscale на хості BamDude.** Native-інстал: встанови [tailscaled](https://tailscale.com/kb/1031/install-linux) і `tailscale up`. Docker-інстал потребує **двох** bind-mount'ів (BamDude image не містить ні того, ні іншого — див. Caveats нижче):

    ```yaml
    services:
      bamdude:
        volumes:
          - /var/run/tailscale/tailscaled.sock:/var/run/tailscale/tailscaled.sock
          - /usr/bin/tailscale:/usr/bin/tailscale:ro
    ```

    Сокет дозволяє BamDude говорити з демоном хоста; бінарник — це CLI-клієнт, на який BamDude shell-out'ить (`shutil.which("tailscale")` повертає `None` без нього, і інтеграція сама вимикається). Daemon живе на хості, BamDude лише читає його.
2. **MagicDNS + HTTPS-сертифікати ввімкнені** на твоєму tailnet'і — обидві опції на [Tailscale admin DNS page](https://login.tailscale.com/admin/dns). Без них немає `*.ts.net` FQDN, проти якого BamDude буде випустити серт.
3. **Віртуальний принтер.** Tailscale тогглиться *per VP*; потрібен принаймні один VP, щоб увімкнути.

---

## :material-cog-outline: Увімкнення на VP

**Settings → Virtual Printer → редагувати VP** — внизу є тоглер:

| Поле | Default | Що робить |
|---|---|---|
| **Tailscale enabled** | off | Коли on — BamDude викликає `tailscale cert <vp-name>.<tailnet>.ts.net` на старті, atomic-swap результуючий серт перед тим, як FTPS / MQTT TLS-listener'и запустяться, і використовує tailnet FQDN як SSDP `Location:` URL. |
| **Tailscale FQDN** | auto | Read-only display резолв'нутого FQDN. Авто-визначається з `tailscale status` хоста + ім'я VP; перевизначай тільки якщо у тебе кілька VP на одній машині, які потребують явних імен. |

Тоглер per-VP, бо деякі сетапи хочуть VP-A на LAN (цех) і VP-B на tailnet (віддалений слайсер інженерної команди) **одночасно** — глобальний тумблер цього не зробив би.

---

## :material-certificate: Життєвий цикл сертів

- **Перша емісія** — на старті VP з увімкненим Tailscale, BamDude shell-out'ить `tailscale cert <fqdn>` (що звертається через Tailscale-broker до Let's Encrypt) і пише результуючий `.crt + .key` поряд із існуючою self-signed парою.
- **Atomic swap** — FTPS + MQTT TLS-listener'и рестартуються з новим сертом ДО того, як SSDP-анонс випуститься, тож слайсер, що пінг'є FQDN, ніколи не бачить self-signed fallback.
- **Daily renewal** — фонова петля 24h викликає `tailscale cert` знову задовго до експірації. Self-cancelling на shutdown'і, щоб петля не пережила asyncio event loop.
- **Failure mode** — якщо `tailscale cert` повертає помилку (daemon offline, FQDN typo, rate limit) — BamDude логує і фолбекає до існуючого self-signed серта. VP продовжує працювати; віддалені слайсери бачать cert error, доки не пофіксиш upstream і не повториш.

---

## :material-lan-connect: SSDP-анонс

Стандартний VP SSDP анонсує LAN-IP хоста, що недоступний з tailnet'а. З увімкненим Tailscale SSDP `Location:` URL вказує на tailnet FQDN — Bambu Studio / OrcaSlicer на будь-якому tailnet-девайсі бачать VP точно так, ніби це справжній принтер у тій же мережі.

LAN-анонс теж відбувається — локальні слайсери підхоплюють LAN-IP, віддалені слайсери (доступні лише через tailnet) — tailnet FQDN. Вони не конкурують.

---

## :material-shield-key: Дозволи і безпека

- **Жодних нових BamDude-permissions.** Tailscale-конфіг — частина існуючого `virtual_printer:update` permission gate.
- **Жодного Tailscale auth surface всередині BamDude.** Авторизація (хто на тайнеті) — справа Tailscale. BamDude читає daemon, не імітує його.
- **Той самий VP access code** все ще потрібен слайсеру для авторизації на VP. Tailscale приносить мережу до принтера; access code досі гейтить принтер.

---

## :material-alert-circle-outline: Підводні камені

!!! info "Docker-варіант відкладено"
    Docker-image спеціально не несе `tailscaled`. Причини: tailscaled хоче raw netlink + state directory + auth-флоу, що погано лягають у stateless-контейнери. Runtime-шлях — "хост має tailscaled → монтуй його сокет у контейнер BamDude" — це і lower-blast-radius і поважає твою існуючу Tailscale-конфігурацію.

- **`tailscaled` має бути на хості (або примонтований із sidecar) — BamDude не може його підняти.** Це навмисний поділ: auth + state model Tailscale — host-concern.
- **Лише приватні tailnet'и** — публічного інтернет-анонсу VP через це немає. Це by design (для цього є `proxy` mode).
- **Cert renewal потребує доступ до daemon у час виконання** — якщо tailscaled на хості ляже, daily-renewal почне фейлити за 30+ днів до експірації серта; стеж за алертами.

---

## :material-bug-outline: Усунення проблем

Якщо при старті VP відбувається фолбек на самопідписаний серт — причина в логах BamDude на рівні WARNING. Зіставляй повідомлення з фіксом:

| Повідомлення в логу | Причина | Фікс |
|---|---|---|
| `tailscale binary not found` | CLI не у `PATH`. Bare-metal: не встановлено. Docker: бінарник не примонтований. | Bare-metal: встанови [tailscaled](https://tailscale.com/kb/1031/install-linux). Docker: додай `- /usr/bin/tailscale:/usr/bin/tailscale:ro` (на додачу до сокет-маунту). |
| `Running in Docker but /var/run/tailscale/tailscaled.sock is not mounted` | Одноразова підказка на старті, коли бінарник є, але сокета — нема. | Додай `- /var/run/tailscale/tailscaled.sock:/var/run/tailscale/tailscaled.sock` у `volumes:`. |
| `Tailscale not connected (no DNSName)` | Daemon піднятий, але хост не залогінений у tailnet. | `tailscale up` на хості, авторизація. |
| `https cert ... disabled` / `not enabled tailnet` / `cert ... not enabled` | Toggle HTTPS Certificates вимкнений в admin-консолі. | Увімкни MagicDNS + HTTPS Certificates на [login.tailscale.com/admin/dns](https://login.tailscale.com/admin/dns). У корпоративному / шкільному tailnet'і може знадобитися admin, щоб це перемкнути. |
| `Tailscale cert files at ... are not readable by this process` | Bare-metal-інстал, де `tailscale cert` запустився під root, і файли лишилися root-owned. | `sudo chown $(whoami):$(whoami) <data>/certs/<vp_id>/*` — у логу буде точний шлях і команда. |
| `tailscale cert failed (exit N): ...` | Будь-що інше від CLI (rate-limit, неправильний FQDN, daemon у мить рестарту). | Читай stderr у тому ж рядку логу; rate-limit'и самі вирішуються за годину, проблеми з FQDN означають що ім'я VP має символи, які Tailscale не приймає. |

У будь-якому випадку VP продовжує працювати на самопідписаному серті — виправ root cause, після чого або рестарни VP, або дочекайся наступного 24h renewal-проходу.

---

## :material-link-variant: Дивись також

- [Virtual Printer](virtual-printer.md) — VP-режими, які отримують вигоду.
- [Reverse proxy & HTTPS](../getting-started/reverse-proxy.md) — для самого UI BamDude'у, не для VP.
