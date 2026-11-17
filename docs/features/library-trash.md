---
title: Library & Archive Trash
description: Soft-delete with restore, scheduled retention, and reference-aware delete that won't drop bytes still pinned by an active archive
---

# Library & Archive Trash

BamDude keeps two independent **trash bins** so deletions never silently destroy data:

- **Library trash** — for files you uploaded or sliced into the library. Has an opt-in **auto-purge** that moves idle files into the bin on a 24h drift schedule.
- **Archive trash** — for archive rows you (or "Empty trash" sweeps) explicitly delete. Manual-only — no auto-purge moves old archive rows here.

Both bins have the same shape: soft-delete on user-initiated delete, configurable restore window, scheduled retention sweeper that hard-deletes anything past the window, and a chain-of-custody guard that refuses to hard-delete library bytes still referenced by an active archive.

!!! note "Why archive rows are not auto-purged"
    A daily sweep that moved every archive row older than a threshold into the trash would be both **redundant** (the per-design [3MF Auto-Cleanup](archiving.md#3mf-auto-cleanup-041-drift-mode-in-042) already reclaims the disk for cold designs while preserving history) and **harmful** (per-row aging means a model printed weekly for two years would lose its earliest ~70 archive rows individually, even though the design is still hot — silently destroying the print history BamDude exists to preserve). The manual delete → trash → restore → empty-trash flow covers explicit row deletes.

---

## :material-trash-can-outline: How soft-delete works

When you delete a library file or an archive (manually, or via auto-purge):

1. The row gets `deleted_at = now()` — it disappears from the main list and from dedup queries.
2. Bytes + thumbnails stay on disk untouched. A library file also keeps its notes and its [photos](file-manager.md#file-photos); while the file is in the trash they cannot be read or changed, and a restore brings them back with it.
3. The trash page (admin section in Settings, plus dedicated `/files/trash` and `/archives/trash` routes) lists every soft-deleted row with a countdown to hard-delete.
4. **Restore** flips `deleted_at` back to `NULL` — the row reappears as if nothing happened.
5. **Hard-delete now** removes the row + bytes immediately (admin only).
6. After the configured retention window, a background sweeper hard-deletes anything that's been in the trash longer than the threshold.

A hard delete of a library file — by hand, by **Empty trash** or by the sweeper — removes its notes and photos with it.

**Deleting a folder** sends the files BamDude stores in it, subfolders included, to the trash; the folder itself has no trash and is gone. External files are the exception, as everywhere: their library entry is removed without the trash, and the original on the disk stays. Files already in the trash — binned before, or in the same multi-select delete — stay there with their original delete time, so their retention does not restart. Restored files land at the library root, since their folder no longer exists.

---

## :material-shield-alert: Reference-aware hard-delete

Library files can be referenced by archive rows (every print of a file gets an archive). If you hard-delete library bytes that are still pinned by an active (non-trashed) archive, you break **chain-of-custody** — reprints from that archive would have nothing to send.

BamDude refuses such deletes with a `409 Conflict` and a structured payload:

```json
{
  "code": "library_file_pinned_by_archives",
  "active_references": 3,
  "message": "..."
}
```

The UI surfaces it as `Pinned by 3 active archives — delete those first or trash them too`. The bulk **Empty trash** action skips pinned files and reports the count separately so you see why some entries remain.

The library trash sweeper applies the same gate at retention time: a row past its retention window stays pinned and waits for the next tick if archives still reference it. Once those archives are also trashed, the file becomes eligible for hard-delete on the following sweeper tick.

---

## :material-shield-check: Archives retained by print work

Archive **Empty trash** deletes each removable archive and reports both the deleted count and the retained count, with reasons. An active print, running or finishing job, owed table swap, **Clear plate / Repeat** gate, or current printer-queue item can keep an archive and its files. A retained archive does not stop the rest of the bin from being emptied. Deleting that archive individually returns `409 archive_retained` with the reasons.

Resolve the named work through the printer queue or print recovery, then retry. Retention cleanup follows the same rule. If another operator restores an archive while cleanup is waiting, cleanup leaves that restored archive and its video files intact.

---

## :material-cog-outline: Settings

**Settings → Printing → File Manager** has two stacked sub-blocks (auto-purge first, trash retention at the bottom — same order as Archive Settings):

### Library auto-purge

The expanded controls collapse out of view when the toggle is off; flip it on to reveal them.

| Setting | Default | What it controls |
|---------|---------|------------------|
| **Auto-purge enabled** | off | Master toggle for the drift-mode purge that moves idle library files into the trash. Gates the 15-min auto-tick only — manual `/library/purge` always works. |
| **Auto-purge age** | 90 days | Files idle (no recent print, no recent edit) longer than this become eligible for auto-purge. |
| **Include never-printed** | off | When on, never-printed files also count toward the auto-purge threshold. When off, only printed files get auto-purged — protects files you uploaded but haven't printed yet. |
| **Last / Next run cards** | — | Same shared `<LastNextRunCards>` component used by [archive 3MF cleanup](archiving.md#3mf-auto-cleanup-041-drift-mode-in-042). Shows "moved 5 file(s) to trash, 4 hours ago" + "in ~20 hours". After a server restart the in-memory `moved` count is lost; the card reads "count was lost on restart — see logs" instead of `0` (the persistent `library_auto_purge_last_run` timestamp survives, only the count goes). |

### Library trash retention

| Setting | Default | What it controls |
|---------|---------|------------------|
| **Trash retention** | 30 days | How long a soft-deleted file sits in the bin before the sweeper hard-deletes it. Range 1–365 days. The retention sweeper runs every 15 min. |

### Archive trash retention

Archives have no auto-purge (see the note at the top of this page), only the trash retention sweeper:

| Setting | Default | What it controls |
|---------|---------|------------------|
| **Trash retention** | 30 days | How long a soft-deleted archive sits in the bin before the sweeper hard-deletes it. Range 1–365 days. The sweeper still runs every 15 min. |

### Schedule shape (both bins)

| Mechanism | Cadence | Resets |
|-----------|---------|--------|
| Library auto-purge | 15 min tick → run when `now - last_run >= 24 h` | Auto-tick + manual `/library/purge` both stamp `library_auto_purge_last_run` |
| Archive 3MF cleanup | 15 min tick → run when `now - last_run >= 24 h` | Auto-tick + manual `/archives/cleanup/run` both stamp `archive_3mf_cleanup_last_run` |
| Trash retention sweeper (both) | 15 min tick → hard-delete anything past the configured window | n/a |

**First-fire delay (auto-purge / cleanup):** the loop sleeps 15 min **before** the first evaluation, so enabling the toggle now means the first auto-run lands ~15 min later (no last-run exists yet, so the 24h gate doesn't apply on the first tick). Click "Run now" to fire instantly — the manual run stamps the same `last_run` timestamp and starts the 24h drift cycle.

---

## :material-shield-key: Permissions

| Permission | Grants |
|------------|--------|
| `library:delete_own` / `library:delete_all` | Soft-delete (move to trash). Same permission already gates the regular delete button — *if you can delete, you can recover*. |
| `archives:delete_own` / `archives:delete_all` | Same, for archives. |
| `library:purge` | Trigger admin purge + change library trash settings. |
| `archives:purge` | Trigger admin purge + change archive trash settings. |

Manual hard-delete from the trash page also requires the matching `library:purge` / `archives:purge`.

---

## :material-keyboard-return: Restore / Empty / Hard-delete

Both trash pages support:

- **Restore** — flip `deleted_at` back to `NULL`. Row reappears in the main list.
- **Hard-delete now** — admin-only. Removes the row + bytes immediately, bypasses the retention window.
- **Empty trash** — bulk hard-delete every eligible row. Skips pinned files (library) and reports `{deleted, skipped_pinned}` so the UI can explain the gap.
- **Multi-select** — bulk Restore and bulk Hard-delete on selected rows.

!!! warning "Restoring a library file asks before it recreates a duplicate"
    Every other path refuses to store the same file twice, so taking one back out of the trash is the one way left to end up with two identical files. Restore checks first, and speaks up **only when the file really is byte-identical to one you already have** — the dialog names the file that is already there and you decide.

    Restoring several at once asks **once**, listing exactly which of them are duplicates, and offers to restore only the rest. A file with nothing matching it restores without a question.

    It asks; it does not refuse. A duplicate can be deliberate — two MakerWorld profiles can produce byte-identical 3MFs — and the person restoring is the one who put the file there.

!!! danger "An installation that ran a version older than 0.5.4 may hold leaked archive files"
    In those versions the archive trash and its retention sweeper removed the database rows while leaving every 3MF, preview, timelapse and photo on disk. Those files are still there, and BamDude will not go and delete them unasked. `scripts/prune_orphan_archive_files.py` lists what is no longer referenced and removes it only with `--apply`.

---

## :material-database-search: Dedup ignores trashed rows

Every dedup query in BamDude — library upload check, "X duplicates" badge in the file list, the file-detail "Find similar" panel, archive `find_existing_archive` chain anchor — filters out trashed rows. A trashed sibling is never treated as the source of truth: deleting a file from the bin doesn't suddenly inflate other files' duplicate counters; uploading a fresh copy of a trashed file imports cleanly instead of being silently linked back to the doomed row.

---

## :material-folder-cog-outline: External folders bypass the trash

External library folders (mounted NAS shares, USB drives) **don't go through the trash** — their bytes live outside BamDude's control, so there's nothing to restore. Deleting an external entry just drops the DB row + thumbnail; the underlying file on the mount is untouched.

The bulk **Empty trash** action and per-row **Hard-delete now** never touch external folders.

---

## :material-link-variant: Related

- [File Manager](file-manager.md) — where the Trash button + Purge old button live.
- [Print Archiving](archiving.md) — archive trash management lives next to the archives header.
- [Authentication](authentication.md) — how `library:purge` / `archives:purge` are wired to default groups.
