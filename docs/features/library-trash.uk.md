---
title: Корзини бібліотеки і архіву
description: Soft-delete з відновленням, scheduled retention і reference-aware видалення, що не дасть стерти байти, на які ще посилається активний архів
---

# Корзини бібліотеки і архіву

BamDude має дві незалежні **корзини**, щоб видалення ніколи мовчки не знищувало дані:

- **Корзина бібліотеки** — для файлів, які ти завантажив або сляйснув у бібліотеку. Має opt-in **авто-purge**, що переносить idle-файли в корзину по 24г drift-розкладу.
- **Корзина архіву** — для рядків архіву, які ти (або "Empty trash" sweeps) явно видалив. З 0.4.2 manual-only — більше немає щоденного auto-purge, що переносив старі archive-рядки сюди.

Обидві корзини одного крою: soft-delete на ручне видалення, конфігурований restore-window, scheduled-retention sweeper що hard-delete'ить усе після вікна, і chain-of-custody guard, що відмовляється hard-delete'ити байти бібліотеки, якщо на них ще посилається активний архів.

!!! note "Чому archive auto-purge видалили в 0.4.2"
    Upstream-портований archive auto-purge запускався щодня і переносив будь-який archive-рядок старший за поріг у корзину. У BamDude post-b1 це виявилося і **редундантним** (per-design [3MF Auto-Cleanup](archiving.uk.md#material-broom-avtochistka-3mf-041-drift-rezhim-u-042) вже звільняє диск для холодних дизайнів, зберігаючи історію), і **шкідливим** (per-row aging означало, що модель, яку друкують щотижня два роки, втрачала найраніші ~70 archive-рядків поодинці, навіть коли дизайн ще hot — мовчки знищуючи print-історію, заради якої BamDude і існує). Ручний flow delete → trash → restore → empty-trash лишається інтактним для явного видалення рядків; зник лише щоденний auto-purge sweep.

---

## :material-trash-can-outline: Як працює soft-delete

Коли ти видаляєш файл бібліотеки чи архів (вручну або через auto-purge):

1. У ряду виставляється `deleted_at = now()` — він пропадає з основного списку і дедуп-запитів.
2. Байти + мініатюри лишаються на диску.
3. Сторінка корзини (admin-секція в Settings + окремі маршрути `/files/trash` і `/archives/trash`) показує кожен рядок з countdown'ом до hard-delete.
4. **Restore** — повертає `deleted_at = NULL`, рядок з'являється знову, мов і не видаляли.
5. **Hard-delete now** — стирає рядок + байти миттєво (admin only).
6. Після retention-вікна фоновий sweeper hard-delete'ить усе, що проіснувало в корзині довше за поріг.

---

## :material-shield-alert: Reference-aware hard-delete

На файли бібліотеки можуть посилатися рядки архіву (кожен друк файлу породжує архів). Якщо hard-delete'нути байти бібліотеки, на які ще посилається активний (non-trashed) архів — ламається **chain-of-custody**: реприни з того архіву не матимуть що відсилати.

BamDude таке відмовляє з `409 Conflict` і структурованою payload'ою:

```json
{
  "code": "library_file_pinned_by_archives",
  "active_references": 3,
  "message": "..."
}
```

UI показує: `Pinned by 3 active archives — delete those first or trash them too`. Bulk-операція **Empty trash** пропускає pinned-файли і повідомляє кількість окремо, тож зрозуміло, чому деякі не видалились.

Sweeper корзини бібліотеки застосовує той же гейт у час retention: рядок, що вже за вікном, лишається pinned і чекає наступного тіку, якщо архіви на нього ще посилаються. Як тільки ті архіви теж потраплять у корзину — файл стає eligible на наступному тіку.

---

## :material-cog-outline: Налаштування

**Settings → Printing** має дві чітко розділені суб-секції:

### File Manager (корзина бібліотеки)

| Опція | За замовчуванням | Що контролює |
|-------|------------------|--------------|
| **Trash retention** | 30 днів | Скільки soft-deleted файл сидить у корзині перед hard-delete sweeper'ом. Діапазон 1–365. |
| **Auto-purge enabled** | off | Master-тоглер для scheduled-purge, який переносить старі файли в корзину. |
| **Auto-purge age** | 90 днів | Файли idle (без свіжого друку, без свіжого редагування) довше за це стають кандидатами на auto-purge. |
| **Include never-printed** | off | Якщо on — never-printed-файли теж рахуються до threshold'у. Якщо off — auto-purge зачіпає лише друковані файли (захищає те, що ти залив, але ще не друкував). |

### Archive Settings (корзина архіву)

| Опція | За замовчуванням | Що контролює |
|-------|------------------|--------------|
| **Trash retention** | 30 днів | Те саме, для архівів. |
| **Auto-purge enabled** | off | Master-тоглер для archive auto-purge. |
| **Auto-purge age** | 365 днів | Архіви старші за це стають кандидатами. Реприн архіву обновляє його age clock — часто-репринтні архіви ніколи не auto-purge'аються. |

---

## :material-shield-key: Дозволи

| Permission | Що дозволяє |
|------------|--------------|
| `library:delete_own` / `library:delete_all` | Soft-delete (move to trash). Той самий permission, що гейтує звичайну delete-кнопку — *якщо можеш видалити, можеш і відновити*. |
| `archives:delete_own` / `archives:delete_all` | Те саме, для архівів. |
| `library:purge` | Тригерити admin-purge + змінювати налаштування корзини бібліотеки. |
| `archives:purge` | Тригерити admin-purge + змінювати налаштування корзини архіву. |

Manual hard-delete зі сторінки корзини теж потребує відповідного `library:purge` / `archives:purge`.

---

## :material-keyboard-return: Restore / Empty / Hard-delete

Обидві сторінки корзини підтримують:

- **Restore** — повернути `deleted_at = NULL`. Рядок з'являється у списку.
- **Hard-delete now** — admin-only. Стирає рядок + байти миттєво, обходить retention.
- **Empty trash** — bulk hard-delete усього, що вже eligible. Пропускає pinned (бібліотека) і повідомляє `{deleted, skipped_pinned}`, щоб UI пояснив розрив.
- **Multi-select** — bulk Restore і bulk Hard-delete на обраних рядках.

---

## :material-database-search: Дедуп ігнорує trashed-рядки

Кожен дедуп-запит у BamDude — перевірка при upload'і, бейдж "X duplicates" у списку, панель "Find similar" в file-detail, anchor `find_existing_archive` в archive-chain — фільтрує trashed-рядки. Trashed-сибл ніколи не treat'иться як source-of-truth: видалення файлу з корзини раптом не роздуває counter'и інших файлів; повторний upload trashed-файлу імпортується чисто, замість silently link'нутись на приречений рядок.

---

## :material-folder-cog-outline: Зовнішні папки оминають корзину

Зовнішні папки бібліотеки (mounted NAS-шари, USB-диски) **не йдуть через корзину** — їхні байти живуть поза контролем BamDude, тож відновлювати нічого. Видалення external-запису просто стирає DB-рядок + мініатюру; сам файл на mount'і не зачіпається.

Bulk-операція **Empty trash** і per-row **Hard-delete now** ніколи не торкаються external-папок.

---

## :material-link-variant: Дивись також

- [File Manager](file-manager.md) — де живе кнопка Trash + кнопка Purge old.
- [Print Archiving](archiving.md) — керування корзиною архіву поряд із заголовком архіву.
- [Authentication](authentication.md) — як `library:purge` / `archives:purge` прив'язані до дефолтних груп.
