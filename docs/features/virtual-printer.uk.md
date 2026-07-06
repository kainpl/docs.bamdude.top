---
title: Віртуальний принтер
description: Емуляція принтера Bambu для надсилання друків зі слайсера — review, per-printer queue, auto-queue або proxy
---

# Віртуальний принтер

Віртуальний принтер (VP) робить так, що BamDude з'являється у вашій LAN як один або кілька принтерів Bambu Lab. "Send to Printer" з Bambu Studio / OrcaSlicer лягає на VP так само, як він лягав би на справжній принтер — через захищений TLS (MQTT + FTPS) з access-кодом принтера. Далі BamDude роутить аплоад згідно з режимом VP.

---

## :material-printer-3d: Огляд

Кожен VP:

- Анонсує себе через **SSDP** з реальним кодом моделі Bambu (X1C / P1S / A1 Mini / H2D / …), щоб слайсери виявляли його автоматично.
- Запускає **власні FTPS + MQTT + SSDP сервери**. За замовчуванням слухає на `0.0.0.0` (усі інтерфейси хоста); якщо потрібно кілька VP одночасно — даєте кожному свій `bind_ip`, щоб вони не конфліктували за порти.
- Несе **access-код**, як справжній принтер — слайсери питають його при першому використанні і кешують потім.
- Має **серійний номер** і **код моделі**, що збігаються з реальним форматом Bambu, — тож compatibility checks слайсера проходять.

---

## :material-swap-horizontal: Режими {#modes}

VP працює в **рівно одному режимі**. Режим задається per-VP і валідується сервером — будь-що інше відхиляється з HTTP 400.

| Режим | Що відбувається з аплоадами | Use case |
|-------|----------------------------|----------|
| **`file_manager`** (дефолт) | Аплоад лягає в `/pending-uploads` як **review-item**. З review-модалки оператор може диспатчити на реальний принтер, масово заархівувати (без друку) або відхилити. | Multi-user / multi-machine inbox, де кожен аплоад проходить sanity-check перед друком — також правильний режим, якщо ви хочете лише **архівувати** без друку (через bulk-archive у review-модалці). |
| **`print_queue`** | Аплоад архівується **і** ставиться в чергу на **конкретний** цільовий принтер. З `auto_dispatch=true` queue item стартує одразу; з `auto_dispatch=false` чекає на explicit Start-клік. | Аплоади з цього VP завжди їдуть на ту саму машину. |
| **`auto_queue`** | Аплоад архівується і кидається в **[авто-чергу](auto-queue.md)** — без фіксованого таргету. Планувальник сам обирає будь-який придатний вільний принтер (за моделлю + філаментом + кольором). Per-VP перемикач **Force colour match** включає матчинг per-slot `(type, colour, weight)` замість слабшого type-only набору — так job "Жовтий PLA" не піде на принтер з лише "Чорним PLA". | Hands-off load-balancing на ферму з кількох принтерів. |
| **`proxy`** | TLS-сесія слайсера TCP-проксується на реальний `target_printer_id` — BamDude лише публічний endpoint. | Віддалений друк — слайсер достукується до BamDude через LAN/VPN, BamDude достукується до принтера. |

!!! info "Окремого режиму ‘тільки архівувати’ немає"
    Раніше ця сторінка згадувала режим `immediate`, який нібито автоматично створює archive-рядок без черги і бібліотеки. **Такого режиму в коді не було ніколи** — документація брехала. Mode-енум у коді — це рівно чотири варіанти вище (див. `backend/app/models/virtual_printer.py` та валідатор у `backend/app/api/routes/virtual_printers.py`). Щоб отримати "тільки архівувати", використовуйте `file_manager` + bulk-archive у review-модалці — це створить рядок у `print_archives` і навіть не зачепить принтер.

---

## :material-broadcast: Дзеркалення живого стану в non-proxy режимах

Коли non-proxy VP (`file_manager` / `print_queue` / `auto_queue`) налаштований з **target-принтером**, слайсер, який говорить з VP, бачить **реальний живий стан принтера** — не заморожену idle-заглушку. Детект слотів AMS, FTS-роутинг, ідентифікація типу сопла, k-profiles на філамент і жива камера працюють так, ніби слайсер говорить безпосередньо з принтером. Ви зберігаєте чергу / архів / диспетчеризацію BamDude і отримуєте slicer-as-remote-ергономіку у тому ж VP.

Як це працює (важливе для оператора):

- BamDude вже тримає per-printer MQTT-підписку — другої сесії на принтері не відкриваємо, бюджет in-flight повідомлень фірмварі не страждає.
- VP кешує останні `push_status` і `info.get_version` від принтера й віддає слайсеру майже байт-у-байт ідентичну копію реального push'а. Перевизначаємо лише upload-state-поля, якими керує BamDude (`gcode_state`, `gcode_file`, `prepare_percent`, `subtask_name`).
- Slicer-команди (AMS load / unload, xcam, `extrusion_cali_get` для k-profile, …) форвардяться на реальний принтер. `project_file` / `gcode_file` все одно завершуються локально — файл лежить у BamDude.
- Камера — raw TCP passthrough на `<bind_ip>:322` → `printer:322` (той самий підхід, що в proxy-режимі).

!!! warning "Однаковий access code на VP і target-принтері"
    BambuStudio автентифікує RTSPS access-кодом зі свого профілю слайсера — VP і його target мають мати **однаковий access code**, інакше кнопка камери впаде з "LAN connection failed". MQTT і FTPS працюють обома способами. Виставте через **Settings → Virtual Printer → Edit** і **Settings → Printers → Edit**.

!!! info "Proxy-режим це не зачепило"
    Proxy-режим тримає власні RTSP / FTP / MQTT проксі і роутить усе end-to-end на TCP-рівні — кешу немає чого дзеркалити. Поведінка вище — opt-in для трьох non-proxy режимів.

---

## :material-cog: Налаштування

**Налаштування → Virtual Printer → Add Virtual Printer**:

| Поле | Примітки |
|------|----------|
| Name | Display-лейбл (наприклад, `Studio inbox`). |
| Model | SSDP model code — оберіть модель принтера, яку VP має імперсонувати, щоб compatibility checks слайсера проходили. |
| Bind IP | Опціональне. Залиште порожнім — VP слухатиме `0.0.0.0` (усі інтерфейси хоста), цього досить для одного VP на стандартних портах. Виділений IP потрібен лише коли запускаєте **кілька VP одночасно**, щоб у кожного був свій FTPS / MQTT / SSDP-listener. На Linux найпростіший шлях додати IP — virtual interface (alias) на хості. |
| Access code | 8-символьний код, яким автентифікується слайсер. |
| Mode | Один з чотирьох вище. |
| Auto-dispatch | Активний у режимах `print_queue` і `auto_queue` — див. нижче. |
| Target printer | Тільки для режиму `print_queue` (конкретний таргет) і `proxy`. Прихований коли вибрано `auto_queue` або `file_manager`. |

Слайсери виявляють новий VP через SSDP автоматично за хвилину-дві. Якщо discovery не спрацював, додайте вручну за IP + access-кодом.

---

## :material-ethernet: Потрібні порти

!!! tip "Зазвичай ручного налаштування не треба"
    Контейнер / нативна інсталяція відкриває потрібні порти автоматично — таблиця нижче для довідки: фаєрвол, Docker NAT, мульти-NIC, proxy mode.

Кожен VP використовує ці порти на своєму bind IP:

| Сервіс | Порт | Протокол | Призначення |
|--------|------|----------|-------------|
| Bind / detect | 3000, 3002 | TCP | Хендшейк "Add Printer" слайсера — потрібен у всіх режимах |
| SSDP | 2021 | UDP | Авто-discovery в LAN (не працює через VPN / Docker bridge / remote) |
| MQTT | 8883 | TCP/TLS | Контроль + статус принтера |
| File transfer tunnel | 6000 | TCP/TLS | Verify-job + завантаження файлу (proxy mode + камера A1/P1) |
| RTSP camera | 322 | TCP/TLS | Стрім камери X1 / H2 / P2 — proxy mode **і** не-proxy режими, коли заданий target printer (через цей порт йде live-камера слайсера) |
| FTPS | 990 | TCP/TLS | Контроль FTP |
| FTP PASV data | 10-портовий слайс на VP у межах `50000–50999` | TCP | Пасивний канал даних FTP — кожен non-proxy VP має свій слайс (VP 1 → `50000–50009`, VP 2 → `50010–50019`, …); proxy-режим натомість форвардить діапазон таргет-принтера |
| Slicer proprietary | 2024–2026 | TCP/TLS | Протокол слайсер ↔ принтер для A1 / P1S (proxy mode) |

!!! note "Чому два bind-порти"
    Різні версії Bambu Studio і OrcaSlicer використовують різні порти для bind-хендшейку. BamDude слухає **обидва — 3000 і 3002** — щоб будь-який слайсер сконектився.

!!! note "Привілейований порт 990"
    990 — привілейований (<1024). Процесу потрібен `CAP_NET_BIND_SERVICE` або root, щоб його забіндити. Готовий Docker-образ і systemd unit вже мають цю capability — нічого додаткового робити не треба.

!!! note "Пасивні FTP-порти нарізаються на кожен VP"
    Кожен **non-proxy** VP отримує власний **10-портовий слайс** пасивних даних, виділений із його database id: VP 1 → `50000–50009`, VP 2 → `50010–50019` і так далі (слот вертається після 100 VP, тож будь-який слайс лишається в межах `50000–50999`). Це замінило старий плаский пул `50000–50100` — під дефолтним userland-проксі Docker'а той широкий діапазон породжував ~2000 host-процесів (~3.5 GB host RAM). Відкривай лише ті слайси, які твої VP реально використовують, і додавай по 10 портів на кожен наступний VP. Точний слайс запущеного VP видно в його стартовому лозі `FTP passive data port range: <min>-<max>`. **Proxy-режим** — виняток: він форвардить *повний* пасивний діапазон таргет-принтера (приблизно `50000–50100`).

---

## :material-printer-3d-nozzle: Додаємо VP у слайсер

### Авто-discovery (та сама LAN)

1. VP **увімкнений** (Settings → Virtual Printer → toggle on, статус `Running`).
2. У Bambu Studio / OrcaSlicer відкрий **Device** → **Refresh** (або зачекай — він поллить).
3. VP зʼявляється у списку пристроїв як модель, яку ти обрав. Вибери, встав access code — все.

### Ручне додавання (VPN / Docker bridge / remote / інша підмережа)

SSDP — link-local: бродкасти не виходять за роутер, через VPN tun, ні через Docker bridge. Тоді:

1. **Device → Add Printer → Add printer manually** (або "Bind with access code" — залежить від білда слайсера).
2. **IP**: досяжний IP хоста BamDude (або per-VP bind IP, якщо ти його задав).
3. **Access code**: 8-символьний код з картки VP.

!!! warning "Bind-порти повинні бути досяжні"
    Хендшейк іде на 3000 або 3002 — машина зі слайсером має могти TCP-конектитись на цей порт хоста BamDude. Фаєрвол, port forwarding, Docker `ports:` — будь-що з цього може ламати.

---

## :material-send: Відправка прінтів — Send vs Print

!!! warning "Тиснемо **Send**, а не **Print**"
    - **Send** → шле 3MF в BamDude, далі по режиму VP (review / queue / auto-queue / archive). **Правильно.**
    - **Print** → каже слайсеру стартанути друк негайно на справжньому принтері. VP — не принтер, тому або таймаут, або помилка.

У Bambu Studio / OrcaSlicer кнопка **Send** стоїть біля **Print** (або під випадайкою на кнопці Print — залежить від версії слайсера). Що буде далі — залежить від [режиму VP](#modes).

Для VP у режимі `proxy` тиснемо **Print** як завжди — proxy режим прозорий, він форвардить на справжній принтер.

!!! note "Multi-plate 'Send all plates'"
    Коли використовуєш **Send all plates** слайсера на multi-plate 3MF у VP режиму черги, BamDude ставить у чергу **по одному айтему на плейт** у порядку плейтів — а не один айтем на весь файл — тож планувальник виконує кожен плейт як окремий джоб. Одноплейтний **Send** лишається одним айтемом.

---

## :material-certificate: Встановлення сертифікату

VP піднімає MQTT + FTPS + RTSP за самопідписаним CA, який BamDude генерує під час першого вмикання VP. **Bambu Studio і OrcaSlicer його з коробки не довіряють** — у них захардкожений список CA Bambu, і (на macOS / Windows) системний trust store ігнорується. Треба додати CA BamDude у файл `printer.cer`, який лежить у слайсера (на Linux — варіант ще через системний CA store, якщо твій білд його поважає).

!!! info "Коли треба повторити"
    - Перший раз (на кожній новій інсталяції)
    - Перенесли BamDude на новий хост (кожна інсталяція генерить свій унікальний CA — крім випадку, коли ти переніс директорію `certs/`)
    - Слайсер оновився і затер `printer.cer` (часто на Windows / macOS)

### Крок 1 — Знаходимо CA BamDude

CA лежить у `<DATA_DIR>/virtual_printer/certs/bbl_ca.crt`.

=== "Native"
    ```bash
    # за замовчуванням DATA_DIR — це ./data поряд з інсталяцією
    cat data/virtual_printer/certs/bbl_ca.crt
    ```

=== "Docker"
    ```bash
    docker cp bamdude:/app/data/virtual_printer/certs/bbl_ca.crt ./bamdude-ca.crt
    ```

!!! note "CA генерується ліниво"
    `bbl_ca.crt` зʼявляється тільки після того, як ти **увімкнув** VP перший раз. Якщо файлу нема — створи + увімкни VP в UI, потім ще раз cp.

### Крок 2 — Дописуємо CA у `printer.cer` слайсера

`printer.cer` — PEM-бандл CA, яким слайсер довіряє для підключень до принтерів. Відкрий, **допиши** CA BamDude в самому кінці (після останнього `-----END CERTIFICATE-----`), збережи, потім **повністю перезапусти** слайсер (Cmd+Q на macOS — закрити вікно недостатньо; Task Manager → End Task на Windows).

!!! tip "Дописуємо, не замінюємо"
    Дописуючи, ти зберігаєш довіру до справжніх принтерів Bambu Lab. Заміна файлу ламає Bambu Cloud / прямий MQTT до фізичного заліза.

**Де живе `printer.cer`:**

=== "macOS"
    - Bambu Studio: `/Applications/BambuStudio.app/Contents/Resources/cert/printer.cer`
    - OrcaSlicer: `/Applications/OrcaSlicer.app/Contents/Resources/cert/printer.cer`

=== "Windows"
    - Bambu Studio: `C:\Program Files\Bambu Studio\resources\cert\printer.cer`
    - OrcaSlicer: `C:\Program Files\OrcaSlicer\resources\cert\printer.cer`

=== "Linux — `.deb` / `.rpm`"
    Нативні пакети лінкуються з системним OpenSSL і підхоплюють системний CA bundle, коли в `~/.config/BambuStudio/BambuStudio.conf` стоїть `tls_cert_store_accepted: yes` (default після першого запуску). Тоді ставимо CA системно:

    Debian / Ubuntu / Mint / Raspberry Pi OS:

    ```bash
    sudo cp bbl_ca.crt /usr/local/share/ca-certificates/bamdude-ca.crt   # розширення ОБОВʼЯЗКОВО .crt
    sudo update-ca-certificates
    ```

    Fedora / RHEL / openSUSE:

    ```bash
    sudo cp bbl_ca.crt /etc/pki/ca-trust/source/anchors/bamdude-ca.crt
    sudo update-ca-trust
    ```

    Arch:

    ```bash
    sudo trust anchor --store bbl_ca.crt
    ```

    Потім **повністю** перезапусти слайсер.

    !!! warning "Поширена помилка"
        Кинути файл у `/etc/ssl/certs/` і запустити `update-ca-certificates` — no-op. Інструмент бере тільки файли з `/usr/local/share/ca-certificates/` із розширенням `.crt`.

    Якщо системний store не береться — фолбек у пряме редагування (вони root-owned, тож `sudo`):

    - Bambu Studio: `/usr/share/Bambu Studio/resources/cert/printer.cer`
    - OrcaSlicer: `/usr/share/OrcaSlicer/resources/cert/printer.cer`

    Прямі правки скидаються при кожному оновленні пакета.

=== "Linux — AppImage"
    Системний CA store ненадійний для AppImage-білдів (вони мають свій мережевий стек). Розпаковуй, редагуй вшитий `printer.cer`, запускай з розпакованого дерева:

    ```bash
    ./Bambu_Studio_linux_*.AppImage --appimage-extract
    # редагуй squashfs-root/usr/share/Bambu Studio/resources/cert/printer.cer
    ./squashfs-root/AppRun
    ```

    Повторювати щоразу при оновленні AppImage.

### Персистентність CA

CA генерується один раз і живе через рестарти BamDude. **Тримай `<DATA_DIR>/virtual_printer/certs/` у бекапі** — без нього після наступного рестарту кожен слайсер доведеться переімпортувати на новий CA.

Якщо перемикаєшся між Docker і native і хочеш один CA на обидва — share-уй директорію через bind-mount:

```yaml
volumes:
  - ./virtual_printer:/app/data/virtual_printer
```

### Кілька хостів BamDude

Кожна інсталяція генерує свій CA. Два чисті варіанти:

**Поділити CA (рекомендовано для ферм)**

```bash
scp -r host1:/path/to/data/virtual_printer/certs/ host2:/path/to/data/virtual_printer/
# рестарт bamdude на host2
```

Усі хости тепер з одним CA — один сертифікат у слайсері покриває всіх.

**Або: переімпорт на хост**

При перемиканні слайсера на інший хост BamDude — видали старий блок CA з `printer.cer`, додай новий, повністю перезапусти слайсер.

!!! warning "Один CA BamDude за раз"
    Запхати кілька CA BamDude у `printer.cer` криптографічно ОК, але це робить дуже легко вказати слайсер на "не той" хост випадково. Чисти старі.

---

## :material-ip-network: Виділені bind IP (кілька VP)

Кожен VP, що сидить на стандартних портах, потребує власного IP — слухачі FTPS / MQTT / SSDP не можуть ділити порт між VP на одній адресі. Один VP на `0.0.0.0` — основного IP хоста достатньо; для двох і більше VP даємо кожному свій bind IP через interface-аліаси (додаткові IP на тому ж NIC).

Приклад розкладу:

| | IP |
|---|---|
| BamDude UI | `192.168.1.100` (основний хоста) |
| VP 1 | `192.168.1.101` |
| VP 2 | `192.168.1.102` |
| VP 3 | `192.168.1.103` |

!!! warning "Бери вільні IP"
    Адреси **поза DHCP-діапазоном**, або зарезервовані на роутері. Перевіряй `ping 192.168.1.101` перед додаванням — якщо хтось відповідає, бери інший.

### Додаємо аліаси інтерфейсу

=== "Linux (native або Docker host mode)"

    Знайди імʼя інтерфейсу:

    ```bash
    ip -br addr show
    # eth0  UP  192.168.1.100/24
    ```

    Додай аліаси (тимчасові — після ребута зникнуть):

    ```bash
    sudo ip addr add 192.168.1.101/24 dev eth0
    sudo ip addr add 192.168.1.102/24 dev eth0
    sudo ip addr add 192.168.1.103/24 dev eth0
    ```

    **Робимо постійно:**

    === "Netplan (Ubuntu 18.04+, Debian 12+)"

        У `/etc/netplan/*.yaml`:

        ```yaml
        network:
          version: 2
          ethernets:
            eth0:
              dhcp4: true
              addresses:
                - 192.168.1.101/24
                - 192.168.1.102/24
                - 192.168.1.103/24
        ```

        `sudo netplan apply`.

    === "/etc/network/interfaces (Debian, Raspberry Pi OS)"

        ```
        auto eth0:1
        iface eth0:1 inet static
            address 192.168.1.101
            netmask 255.255.255.0

        auto eth0:2
        iface eth0:2 inet static
            address 192.168.1.102
            netmask 255.255.255.0
        ```

        `sudo ifup eth0:1 eth0:2`.

    === "NetworkManager (Fedora, RHEL, Arch)"

        ```bash
        sudo nmcli con mod "Wired connection 1" +ipv4.addresses "192.168.1.101/24"
        sudo nmcli con mod "Wired connection 1" +ipv4.addresses "192.168.1.102/24"
        sudo nmcli con up "Wired connection 1"
        ```

        Імʼя зʼєднання — `nmcli con show`.

=== "Unraid"

    SSH або веб-термінал:

    ```bash
    ip addr add 192.168.1.101/24 dev eth0
    ip addr add 192.168.1.102/24 dev eth0
    ```

    Постійно — у `/boot/config/go`:

    ```bash
    echo "ip addr add 192.168.1.101/24 dev eth0" >> /boot/config/go
    echo "ip addr add 192.168.1.102/24 dev eth0" >> /boot/config/go
    ```

=== "Synology NAS"

    SSH:

    ```bash
    sudo ip addr add 192.168.1.101/24 dev eth0
    sudo ip addr add 192.168.1.102/24 dev eth0
    ```

    Постійно — Control Panel → **Task Scheduler** → Triggered Task → User-defined script, тригер **Boot-up**, користувач **root**, ті ж рядки `ip addr add …`.

=== "TrueNAS SCALE"

    Network → Interfaces → Edit → додай **Aliases** (`192.168.1.101/24`, …) → Save → Apply. Постійно автоматично.

=== "Proxmox LXC"

    **Усередині контейнера** — постав `iproute2`, далі Linux-інструкції вище (netplan або `/etc/network/interfaces`).

    **З Proxmox-хоста** — `/etc/pve/lxc/<CTID>.conf`:

    ```
    net0: name=eth0,bridge=vmbr0,ip=192.168.1.100/24,gw=192.168.1.1
    net1: name=eth1,bridge=vmbr0,ip=192.168.1.101/24
    net2: name=eth2,bridge=vmbr0,ip=192.168.1.102/24
    ```

    Або `pct set <CTID> -net1 name=eth1,bridge=vmbr0,ip=192.168.1.101/24`. Перезапустити контейнер після.

=== "Docker Desktop (macOS / Windows)"

    !!! warning "Тільки один VP"
        Docker Desktop крутить все у Linux VM і не дає додавати в неї interface-аліаси, які потім досяжні з контейнера. У bridge-режимі лімит — **один VP** на хост. Для багатьох VP — Linux (native або VM з host networking).

!!! tip "Docker host mode"
    З `network_mode: host` додавай аліаси на **Docker-хості**, не в контейнері — host mode зашейрить всі IP хоста в контейнер автоматично.

---

## :material-list-box: SSDP-коди моделей

VP видає себе за реальну модель Bambu, щоб слайсерська перевірка сумісності пройшла. Бери модель, що збігається з пресетом слайсера.

| SSDP-код | Назва | Префікс серійника |
|---|---|---|
| `BL-P001` | X1C *(default)* | 00M |
| `BL-P002` | X1 | 00M |
| `C13` | X1E | 03W |
| `N6` | X2D | 20P9 |
| `N9` | A2L | 26A19 |
| `C11` | P1P | 01S |
| `C12` | P1S | 01P |
| `N7` | P2S | 22E |
| `N2S` | A1 | 039 |
| `N1` | A1 Mini | 030 |
| `O1D` | H2D | 094 |
| `O1E` / `O2D` | H2D Pro *(експериментально — коди переписані з довідника моделей, ще не підтверджені на живому H2D Pro)* | 094 |
| `O1C` / `O1C2` | H2C *(O1C2 = dual-nozzle)* | 094 |
| `O1S` | H2S | 094 |

!!! note "Зміна моделі рестартить VP"
    Зміна моделі регенерить серійник і рестартить слухачі. Слайсер побачить новий принтер — швидше за все доведеться додавати наново (кеш паринга у слайсера зашитий по серійнику).

---

## :material-network-strength-4: Network Interface Override

Коли в хоста кілька NIC (Tailscale, кілька LAN-бриджів, Docker overlay, dual-homed routing), авто-detect IP BamDude може потрапити не на ту інтерфейсу — слайсери з потрібного сегмента не дотягуються, та й IP, який лягає в SAN сертифікату, не пройде перевірку.

**Settings → Virtual Printer → Network Interface Override** — обираємо, який інтерфейс BamDude:

- анонсує в **SSDP**-discovery
- зашиває в SAN **TLS-сертифікату**

Працює у **всіх режимах** (server modes + proxy SSDP relay). Бери інтерфейс, з якого слайсер реально дотягується до BamDude.

---

## :material-shield-check: Tailscale

Tailscale — рекомендований шлях для **віддаленого доступу слайсера**: слайсер досягає VP через приватну WireGuard-мережу звідки завгодно, без port forwarding і без публічного експорту.

Тогл Tailscale на картці VP показує IP / MagicDNS-host у tailnet — це і вставляєш у слайсер. CA однаково треба імпортувати в слайсер (Tailscale не змінює довіру до сертифікатів).

Повний setup (native + Docker + LXC), prerequisites і troubleshooting — у виділеному гайді:

[:material-arrow-right: **Tailscale-інтеграція**](tailscale.uk.md){ .md-button }

---

## :material-server-network: Платформенне налаштування

Відкрий [порти зі списку вище](#потрібні-порти) у фаєрволі.

=== "Linux native"

    Порту 990 потрібен `CAP_NET_BIND_SERVICE`. Готовий systemd unit вже містить:

    ```ini
    AmbientCapabilities=CAP_NET_BIND_SERVICE
    ```

    Для ручного запуску — capability на бінарь Python:

    ```bash
    sudo setcap cap_net_bind_service=+ep $(readlink -f $(which python3))
    ```

    UFW:

    ```bash
    sudo ufw allow 3000/tcp
    sudo ufw allow 3002/tcp
    sudo ufw allow 2021/udp
    sudo ufw allow 8883/tcp
    sudo ufw allow 990/tcp
    sudo ufw allow 6000/tcp
    sudo ufw allow 322/tcp
    sudo ufw allow 2024:2026/tcp
    sudo ufw allow 50000:50009/tcp   # пасивний слайс одного VP; додай по 10 портів на кожен наступний VP (…:50019, …:50029, …)
    ```

    firewalld:

    ```bash
    sudo firewall-cmd --permanent --add-port=3000/tcp
    sudo firewall-cmd --permanent --add-port=3002/tcp
    sudo firewall-cmd --permanent --add-port=2021/udp
    sudo firewall-cmd --permanent --add-port=8883/tcp
    sudo firewall-cmd --permanent --add-port=990/tcp
    sudo firewall-cmd --permanent --add-port=6000/tcp
    sudo firewall-cmd --permanent --add-port=322/tcp
    sudo firewall-cmd --permanent --add-port=2024-2026/tcp
    sudo firewall-cmd --permanent --add-port=50000-50009/tcp   # пасивний слайс одного VP; +10 портів на кожен наступний VP
    sudo firewall-cmd --reload
    ```

=== "Docker (Linux, host mode)"

    Host networking обовʼязкове для SSDP-discovery. Стандартний compose:

    ```yaml
    services:
      bamdude:
        image: ghcr.io/kainpl/bamdude:latest
        container_name: bamdude
        network_mode: host          # потрібно для SSDP
        cap_add:
          - NET_BIND_SERVICE        # потрібно для порту 990
        volumes:
          - bamdude_data:/app/data
          - bamdude_logs:/app/logs
        environment:
          - TZ=Europe/Kyiv
        restart: unless-stopped
    ```

    Маппінг портів не треба — host mode біндить прямо в інтерфейси хоста. UFW / firewalld-правила застосовуй на хості (як у вкладці Linux native).

=== "Docker Desktop (macOS / Windows)"

    !!! warning "Обмежена підтримка"
        `network_mode: host` на Docker Desktop недоступний — SSDP **не працюватиме**, додавай VP вручну за IP. Bridge-режим обмежує **одним VP** (interface-аліаси у VM не зробити).

    Bridge-mode compose:

    ```yaml
    services:
      bamdude:
        image: ghcr.io/kainpl/bamdude:latest
        container_name: bamdude
        cap_add:
          - NET_BIND_SERVICE
        ports:
          - "${PORT:-8000}:8000"
          - "3000:3000"
          - "3002:3002"
          - "990:990"
          - "6000:6000"
          - "8883:8883"
          - "322:322"
          - "2024-2026:2024-2026"
          - "50000-50029:50000-50029"   # FTP passive data — покриває 3 VP (по 10 портів на слайс); розшир до 50000-500N9 для N+1 VP, або 50000-50100 для proxy-режиму
        volumes:
          - bamdude_data:/app/data
          - bamdude_logs:/app/logs
        environment:
          - TZ=Europe/Kyiv
          - VIRTUAL_PRINTER_PASV_ADDRESS=192.168.1.100  # LAN IP Docker-хоста
        restart: unless-stopped
    ```

    `VIRTUAL_PRINTER_PASV_ADDRESS` у bridge-режимі **обовʼязковий** — без нього FTP PASV анонсує внутрішній IP контейнера і канал даних ламається у середині хендшейку.

=== "Unraid / Synology / TrueNAS SCALE"

    У налаштуваннях контейнера ставимо **Host Network**. FTP-сервер біндиться напряму на 990 — додаткової конфігурації не треба, окрім увімкнення VP в UI.

=== "Proxmox LXC"

    Спецконфігурації не треба — FTP-сервер біндиться напряму на 990. BamDude крутиться як root **або** з `CAP_NET_BIND_SERVICE` на бінарі Python (див. вкладку Linux native).

---

## :material-form-select: UI вибору режиму

Діалог Add / Edit показує чотири режими як **три великі кнопки** + sub-toggle — бо `print_queue` і `auto_queue` це по суті два варіанти одного й того самого (диспатч у чергу, з фіксованим таргетом vs без):

```
┌──────────────────────────────────────────────────────────┐
│  Mode                                                    │
│  ┌─────────────┬───────────────┬──────────────────────┐  │
│  │   Queue     │  File Manager │    ⇄  Proxy          │  │
│  └─────────────┴───────────────┴──────────────────────┘  │
│                                                          │
│  Коли вибрано Queue:                                     │
│    [ ] Auto-select printer  ← тогл                       │
│        on  → mode = auto_queue                           │
│        off → mode = print_queue + поле Target Printer    │
│                                                          │
│  Auto-dispatch                          [ ]              │
└──────────────────────────────────────────────────────────┘
```

Коли **Queue → Auto-select printer = on** — VP у режимі `auto_queue`, дропдаун Target Printer зникає (будь-який принтер відповідної моделі підбере). Коли **Auto-select = off** — режим `print_queue` і дропдаун Target Printer, на який завжди йдуть аплоади.

`file_manager` і `proxy` — це окремі повноширокі кнопки.

### Звʼязка Model ↔ Target Printer

У режимі `print_queue` діалог звʼязує Model і Target Printer, щоб не вийшло несумісної пари:

- Вибираєш **Target Printer** — Model автоматично заповнюється з моделі того принтера.
- Вибираєш **Model** — список Target Printer фільтрується за цією моделлю. Якщо раніше вибраний таргет не підходить новій моделі — діалог чистить його.
- В полі Target Printer є явна **кнопка очистки (×)**, якщо хочеш скинути вибір без зміни моделі.

---

## :material-shield-alert: Правила валідації

Backend (`POST /virtual-printers/`, `PUT /virtual-printers/{id}`) енфорсить:

| Правило | Помилка |
|---------|---------|
| `mode='print_queue'` + `auto_dispatch=true` + немає `target_printer_id` (і не перемикаєшся в auto-select) | **400** — *"Auto-dispatch in Queue mode requires a Target Printer. Pick a target, enable Auto-select printer, or turn Auto-dispatch off."* |
| `mode='proxy'` без `target_printer_id` | **400** — *"Proxy mode requires a Target Printer."* |
| Будь-яке інше значення `mode` | **400** — *"Invalid mode."* |

Маршрут `PUT` перевіряє **остаточний** стан після застосування body — не можна обійти правило, чистячи поля по одному. Якщо треба прибрати існуючий таргет — шли `clear_target_printer: true` (кнопка × в діалозі це й робить).

Frontend дзеркалить це жовтим попередженням, що відключає тогл Auto-dispatch, коли комбінація небезпечна — обмеження видно ще до сабміту.

---

## :material-clipboard-check: Review-модалка (режим file_manager)

У режимі `file_manager` кожен завантажений 3MF лягає в **review queue** на `/pending-uploads`. З review-модалки оператор:

1. Відкриває аплоад, бачить розпарсений metadata + мініатюру.
2. Обирає цільовий реальний принтер.
3. Перевіряє AMS slot mapping, вибір плити і будь-які per-print опції.
4. Натискає **Send to Printer** — 3MF диспатчиться через стандартний background-dispatch pipeline (FTP-аплоад, swap macros, archive linkage).

Review-батчі також можна **архівувати масово** (без друку, просто заскладувати metadata) або **відхилити** (видаляє аплоад). Корисно, коли кілька юзерів / машин слайсять у один і той же VP, і ви хочете sanity-check, перш ніж це справді доб'ється до принтера.

API: `GET /api/v1/pending-uploads/`, `POST /api/v1/pending-uploads/{id}/archive`, `POST /api/v1/pending-uploads/archive-all`.

---

## :material-flash: Auto-dispatch (режими черги) {#auto-dispatch}

VP у будь-якому режимі черги (`print_queue` чи `auto_queue`) підкоряється флагу `auto_dispatch`:

| `auto_dispatch` | `print_queue` | `auto_queue` |
|-----------------|---------------|--------------|
| **true** | Аплоад зі слайсера → архівується → ставиться в чергу → диспатчиться одразу. | Аплоад зі слайсера → архівується → кидається в [авто-чергу](auto-queue.md) → наступний 30-секундний тік призначає елемент придатному вільному принтеру. |
| **false** | Аплоад зі слайсера → архівується → стає в чергу як `pending`, чекає на explicit Start-клік у queue UI. | Аплоад зі слайсера → архівується → router-рядок створюється з `manual_start=true`, тож планувальник його ігнорує, поки не звільниш через панель авто-черги. |

!!! tip "Тільки trusted upstream"
    Auto-dispatch прибирає human gate. Використовуйте його, коли upstream-джерело — це ви самі або trusted-автоматизація (slicer plugin, CI job, MakerWorld webhook). Для shared / multi-tenant аплоадів краще режим `file_manager` + review-модалка.

---

## :material-code-tags: Per-VP G-code injection {#gcode-injection}

Обидва VP режиму черги (`print_queue` і `auto_queue`) мають на картці VP тоглер **G-code injection**. Увімкни його — і кожен джоб, який цей VP ставить у чергу, помічається так, що диспетчер вплітає per-model **start / end сніпети** в gcode при диспатчі — той самий рушій [G-code injection](gcode-injection.md), що й per-item тоглер черги, лише застосований автоматично до slicer-silent аплоадів цього VP.

- **Вимкнено за замовчуванням**, і **no-op, доки** для цільової моделі принтера реально не існують start / end сніпети.
- **Перемикання рестартить VP** (лісенери переініціалізуються), тож слайсер може коротко побачити, як принтер зникає і з'являється.

Використовуй, коли VP завжди годує одну модель, якій потрібна фіксована преамбула chamber-heat-soak / purge / swap-mode, щоб не пам'ятати про per-item тоглер на кожному send.

---

## :material-tune-variant: Системні дефолтні print-опції (slicer-silent диспатчі) {#system-default-print-options}

Коли слайсер шле друк на VP у режимі черги, він зазвичай несе per-job тогли print-опцій — **bed levelling**, **flow calibration**, **layer inspection** і **timelapse**. Деякі білди слайсерів і headless / скриптові шляхи аплоаду ці флаги **не передають**. Раніше queue item з відсутнім флагом одразу падав на built-in column-дефолт моделі принтера.

Тепер queue item резолвить кожен із цих чотирьох флагів за таким пріоритетом:

| Пріоритет | Джерело | Коли застосовується |
|---|---|---|
| 1 (найвищий) | **Значення зі слайсера** | Слайсер передав явний вибір для флага. Завжди виграє. |
| 2 | **Per-model системний дефолт** | Слайсер флаг **не** передав **і** для цієї моделі принтера налаштований системний дефолт. |
| 3 (фолбек) | **Built-in column-дефолт** | Ні те, ні інше — захардкожений дефолт моделі. |

!!! info "Лише заповнює прогалини — ніколи не перевизначає слайсер"
    Флаг, який слайсер **передає**, завжди виграє. Системний дефолт існує лише щоб заповнити тогли, які мовчазний слайсер лишив порожніми; він ніколи не перевизначає явний вибір у слайсері.

### Налаштування системного дефолту

Системні дефолти живуть поряд із per-user saved-профілями у **Settings → Print → Saved Print Profiles**. Таблиця профілів тепер пропонує псевдо-користувача **"System (slicer fallback)"** на додачу до реальних користувачів:

1. Відкрий діалог **Add / Edit** профілю.
2. Обери **System (slicer fallback)** як користувача.
3. Вибери **модель принтера**, до якої застосовуються дефолти.
4. Вистав чотири тогли і збережи.

Системний дефолт — **щонайбільше один на модель принтера**: вибір тієї ж моделі ще раз редагує існуючий, а не створює дубль.

!!! note "`use_ams` не є системним дефолтом"
    `use_ams` — **не** один із тоглів saved-профілю, тож його навмисно виключено із системного дефолту. Використання AMS лишається **slicer-sent-or-column-default** — виставляй його у слайсері (або покладайся на built-in дефолт моделі), не тут.

!!! tip "Приклад — завжди timelapse на флоті P1S"
    Щоб форсити timelapse на кожному slicer-silent диспатчі до твоїх принтерів P1S — навіть із білда слайсера, що не передає флаг — додай профіль **System (slicer fallback)** для моделі **P1S** з увімкненим timelapse. Кожен queue item, що лягає на P1S без явного вибору timelapse, тепер його успадковує.

---

## :material-router-network: Режим auto_queue {#auto_queue}

`auto_queue` — це природна спарка ВП з [авто-чергою](auto-queue.md). На отриманні аплоада ВП:

1. Архівує 3MF (повна per-plate metadata, мініатюри, source-hash chain).
2. Викликає `extract_auto_queue_requirements` на заархівованому файлі — витягує:
    - `target_model` (з `sliced_for_model` у 3MF)
    - `required_filament_types` (з `slice_info.config`)
    - `plate_id`, якщо слайсер вказав конкретний плейт
3. Створює `AutoQueueItem` з `manual_start = !auto_dispatch`.
4. Повертає FTPS-успіх слайсеру — той самий UX, що й справжній принтер, який прийняв файл.

Далі підхоплює маршрутизатор: 30-секундний тік, пошук придатного принтера, AMS-мапінг на момент призначення. Повний потік маршрутизації — у [доку про авто-чергу](auto-queue.md).

У режимі `auto_queue` поля Target Printer не існує — це й сенс. Діалог приховує його і чистить значення, якщо лишилося після переключення режиму.

---

## :material-file-edit-outline: Джерело імені архіву

За замовчуванням 3MF, заархівований через VP, бере display-name з `print_name` з project-метадаt — це зазвичай людськочитабельне "Calibration Cube v3", набране оператором у Bambu Studio. Деякі workflow'и віддадуть перевагу **upload-filename** замість того — наприклад, batch-система, що називає кожен upload `2026-04-30_jobid-1234.gcode.3mf` і хоче зберегти ці ідентифікатори як є.

**Settings → Virtual Printer → Archive name source**:

| Значення | Ефект |
|---|---|
| `metadata` (default) | Брати 3MF-метадані `print_name`. Падає на filename, якщо метадані відсутні. |
| `filename` | Брати stem upload-filename'а. Падає на метадані, якщо filename порожній / generic. |

Тоглер install-wide, застосовується до кожного VP крім `proxy`-mode (proxy-uploads BamDude'ом не архівуються — flow архіву реального принтера бере на себе).

---

## :material-network-outline: PASV Address (NAT / Docker bridge)

FTPS використовує команду PASV — сервер каже клієнту, на який IP передзвонити для data-каналу. Коли BamDude працює в Docker bridge мережі (або за будь-яким NAT), PASV-відповідь інакше анонсувала б **внутрішній IP контейнера** — слайсери в LAN не зможуть до нього достукатися, і data-канал зафейлиться посеред handshake-у.

Поставте env-змінну `VIRTUAL_PRINTER_PASV_ADDRESS` на **externally-reachable IP** (LAN-адресу хоста — більшість слайсерів тут не резолвлять hostnames):

```bash
VIRTUAL_PRINTER_PASV_ADDRESS=192.168.1.100
```

FTPS-сервер стартує, логує `FTP PASV address override: 192.168.1.100`, і відтепер кожна PASV-відповідь використовує цю адресу. Не має ефекту, коли BamDude крутиться на host-мережі — там не задавайте.

---

## :material-help-circle: Troubleshooting

### Слайсер не знаходить VP (auto-discovery)

1. **VP увімкнено і запущено?** Бейдж на картці VP має бути `Running` — якщо `Error`, відкривай картку і читай причину.
2. **Той самий LAN-сегмент?** SSDP — link-local: не пройде через VPN tun, Docker bridge, маршрутизовані підмережі. Додавай вручну за IP.
3. **Bind-порти досяжні?** З машини зі слайсером:
   ```bash
   nc -zv BAMDUDE_IP 3000
   nc -zv BAMDUDE_IP 3002
   ```
4. **Фаєрвол**: 3000/tcp, 3002/tcp, 2021/udp мають бути відкриті між слайсером і BamDude.
5. **Кілька NIC?** [Network Interface Override](#network-interface-override) — пін SSDP на потрібний інтерфейс.

### "Failed to connect" / TLS error -1 / cert untrusted

Слайсер не довіряє CA BamDude. По черзі:

1. **CA дописаний у `printer.cer`?**
   ```bash
   grep -c "BEGIN CERTIFICATE" "/path/to/slicer/resources/cert/printer.cer"
   ```
   Stock = 1. Після append = 2 (або більше при мульти-host).
2. **Той CA?** Якщо переніс BamDude на новий хост — CA інший. Звіряй fingerprint:
   ```bash
   # Native
   openssl x509 -in data/virtual_printer/certs/bbl_ca.crt -noout -fingerprint -sha1

   # Docker
   docker exec bamdude openssl x509 -in /app/data/virtual_printer/certs/bbl_ca.crt -noout -fingerprint -sha1
   ```
   Рядок `SHA1 Fingerprint=…` має бути серед сертифікатів у `printer.cer`.
3. **Слайсер повністю перезапущений?** Cmd+Q на macOS, End Task на Windows. Закрити вікно недостатньо — `printer.cer` не перечитується.
4. **Linux AppImage / Flatpak**: `printer.cer` всередині бандла read-only. Або розпаковуй AppImage і редагуй вшитий cert, або ставимо CA в системний trust store + перевіряємо `tls_cert_store_accepted: yes` у `~/.config/BambuStudio/BambuStudio.conf`.
5. **Останній варіант — регенерація**:
   ```bash
   rm -rf /path/to/data/virtual_printer/certs/
   # disable + re-enable VP в UI для регенерації
   ```
   Потім переімпортуй новий CA у кожен слайсер.

### "Wrong printer model"

Модель пресета слайсера і [SSDP-код VP](#ssdp-коди-моделей) не збігаються. Постав однакову модель з обох боків — перевірка сумісності читає саме SSDP-код VP.

### Authentication failed

- Access code — рівно **8 символів**, ні більше, ні менше.
- Слайсер кешує access code per discovered printer; якщо ти змінив його у BamDude — видали і додай принтер у слайсері знову.

### Не той IP в SSDP / TLS SAN не співпадає

Хост з кількома NIC (Tailscale, Docker bridges, dual LAN) — авто-detect взяв не той інтерфейс:

1. **Settings → Virtual Printer**
2. **Network Interface Override** → інтерфейс, з якого слайсер реально дотягується до BamDude
3. VP перезапуститься; SSDP і SAN сертифіката оновляться

### FTP error / connection reset

1. **Права** на `<DATA_DIR>/virtual_printer/` — має бути writeable юзером, від якого крутиться BamDude.
2. **Порт 990 вже занятий?** `sudo ss -tlnp | grep :990` — вимкни конфліктуючий FTP.
3. **`CAP_NET_BIND_SERVICE` нема** — див. [Linux native вище](#платформенне-налаштування).
4. **Bridge-режим Docker** — `VIRTUAL_PRINTER_PASV_ADDRESS` обовʼязковий; без нього PASV анонсує внутрішній IP контейнера, і канал даних рветься.

### Слайсер каже "The printer is busy with another print job"

Слайсер відмовляється надсилати, бо бачить VP як «у процесі друку». Це стан *preparing* — VP переходить у нього щойно ти починаєш send, і знімає його коли аплоад завершується.

- **Виправлено у 0.4.5.** До 0.4.5 обірваний чи невдалий аплоад (або файл, що прийшов не як `.3mf`) міг лишити VP застряглим у *preparing* аж до рестарту BamDude — і кожен наступний send бачив його зайнятим. Тепер VP завжди повертається в готовність коли аплоад завершується — успіх чи помилка, будь-який тип файлу — і репортує *preparing* лише поки аплоад справді триває. Якщо ловиш це на **0.4.5+** — має зникнути саме протягом одного статус-циклу.
- **Воркераунд на старіших білдах**: перемкни VP off→on (або пере-збережи його конфіг), щоб скинути стан; рестарт BamDude робить те саме.
- Стосується всіх non-proxy режимів (Файловий менеджер, Черга, Авто-черга) і обох слайсерів — Bambu Studio та OrcaSlicer.

### Proxy mode: принтер offline у слайсері

- Target принтер у BamDude онлайн? На сторінці Printers картка має показувати `Online`.
- Принтер у **LAN Mode** (Developer Mode у Bambu Handy)? Proxy режим вимагає LAN mode — у Cloud Mode проксована MQTT-сесія відхиляється.
- Перемкни proxy off + on, щоб форснути reconnect.

### Proxy mode: попап "Connect using IP and access code" при Print

1. **Порт 6000 досяжний?** Bambu Studio через нього шле тунель файлу.
   ```bash
   nc -zv BAMDUDE_IP 6000
   ```
2. **Фаєрвол**: 6000/tcp між слайсером і BamDude.
3. **Різні VLAN / підмережі** — глянь у логах BamDude `IP rewrite active`. Крок MQTT IP-rewrite перепаковує LAN-IP принтера у MQTT-payload на IP BamDude, щоб слайсер ішов у proxy, а не напряму.

### Proxy mode: камера не вантажиться

- **X1 / H2 / P2**: RTSP на 322 — відкрити між слайсером і BamDude.
- **A1 / P1**: камера їде через 6000 (спільно з file transfer).

### Proxy mode: розривається посеред передачі

Великі 3MF на повільному uplink. Або підняти VPN (Tailscale / WireGuard), щоб канал даних ішов одним стабільним тунелем, або заливати 3MF локально, а далі диспатчити Print Queue.

---

## :material-shield-account: Технічні деталі

### Безпека по протоколу

- **Bind** (3000, 3002): нешифрований TCP — передає тільки ідентифікацію принтера, без чутливих даних. У proxy режимі BamDude відповідає від імені VP і не форвардить bind на принтер.
- **MQTT control** (8883): TLS 1.2, термінується в BamDude. Proxy режим переписує IP принтера всередині MQTT-payloads, щоб слайсер не міг обійти проксі.
- **File transfer tunnel** (6000): end-to-end TLS, прозоре проксі.
- **RTSP camera** (322): end-to-end TLS, прозоре проксі.
- **A1 / P1S proprietary** (2024–2026): end-to-end TLS, прозоре проксі.
- **FTPS control** (990): end-to-end TLS, прозоре проксі.
- **FTP data** (10-портовий слайс на VP від `50000`; proxy-режим форвардить діапазон таргет-принтера): у proxy режимі — прозоре проксі; реальне шифрування залежить від домовленості слайсера/принтера. Bambu Studio шле дані каналом **у відкритому вигляді** навіть коли узгоджує `PROT P`. VPN — якщо тобі треба конфіденційність каналу даних.
- Усі зʼєднання вимагають 8-символьний access code — слайсер автентифікується на кожному TLS-handshake.
- CA живе у `<DATA_DIR>/virtual_printer/certs/`; per-VP device certs у `<DATA_DIR>/virtual_printer/certs/{id}/` регенеруються при зміні серійника.

### Обмеження

- Кільком VP потрібен **окремий bind IP кожному** — interface-аліаси за таблицею вище.
- **SSDP працює тільки на одній LAN / маршрутизованих підмережах**. VPN tun mode і Docker bridge — додавати вручну за IP.
- Слайсер повинен довіряти самопідписаному CA BamDude — див. [Встановлення сертифікату](#встановлення-сертифікату).
- **FTP data channel нешифрований** з боку слайсера — VPN, якщо хочеш повне шифрування.
- **Docker Desktop на macOS / Windows = тільки один VP** (interface-аліаси у VM не зробити).

---

## :material-rocket: Use cases

- **Multi-user farm inbox** — `file_manager` + review-модалка дозволяє кільком людям слайсити у той же VP, не наступаючи одне одному на ноги.
- **Архівування друку без друку** — `file_manager` + дія **bulk-archive** у review-модалці перетворює slice → send на постійний запис (мініатюри, metadata, source 3MF) без коміту до друку.
- **Збирання бібліотеки** — той самий `file_manager`: архівуйте аплоади з review-модалки, щоб прикріплювати їх до проєктів, batch-друкувати або шарити з командою до першого білда.
- **Hands-off на одну машину** — `print_queue` з фіксованим Target Printer + `auto_dispatch=true` — це найближче до "Cloud Print, але локально" для одного принтера.
- **Ручний gate на черзі** — `print_queue` + `auto_dispatch=false` ставить аплоад у чергу, але чекає на explicit Start-клік перед тим, як диспетчер його забере.
- **Load-balancing на фермі** — `auto_queue` + `auto_dispatch=true` — це killer-флоу для багатопринтерної ферми: слайсер не знає, який принтер виконуватиме друк, маршрутизатор обирає на момент диспатчу.
- **Віддалений друк** — режим `proxy` пробрасує remote-слайсера TLS-сесію прямо в реальний принтер, з сертифікатом BamDude як публічним обличчям.

---

## :material-lightbulb: Поради

!!! tip "Один VP на workflow"
    Ніщо не заважає крутити кілька VP одночасно на різних IP — один на production auto-dispatch, один на review, один на архівування. Вони шарять той самий backend, тож усі дані залишаються уніфікованими.

!!! tip "Slicer auth caching"
    Bambu Studio / OrcaSlicer кешують access-код per discovered принтер. Поверніть VP access-код — і слайсери знову спитають, без ручної очистки кешу.

> Початково базується на документації [Bambuddy](https://github.com/maziggy/bambuddy).
