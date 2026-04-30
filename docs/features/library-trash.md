---
title: Library & Archive Trash
description: Soft-delete with restore, scheduled retention, and reference-aware delete that won't drop bytes still pinned by an active archive
---

# Library & Archive Trash

BamDude keeps two independent **trash bins** so deletions never silently destroy data:

- **Library trash** — for files you uploaded or sliced into the library.
- **Archive trash** — for print archive rows the auto-purge sweep moves out of active history.

Both bins have the same shape: soft-delete on user-initiated delete, configurable restore window, scheduled retention sweeper, and a chain-of-custody guard that refuses to hard-delete library bytes still referenced by an active archive.

---

## :material-trash-can-outline: How soft-delete works

When you delete a library file or an archive (manually, or via auto-purge):

1. The row gets `deleted_at = now()` — it disappears from the main list and from dedup queries.
2. Bytes + thumbnails stay on disk untouched.
3. The trash page (admin section in Settings, plus dedicated `/files/trash` and `/archives/trash` routes) lists every soft-deleted row with a countdown to hard-delete.
4. **Restore** flips `deleted_at` back to `NULL` — the row reappears as if nothing happened.
5. **Hard-delete now** removes the row + bytes immediately (admin only).
6. After the configured retention window, a background sweeper hard-deletes anything that's been in the trash longer than the threshold.

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

## :material-cog-outline: Settings

**Settings → Printing** has two clearly separated sub-sections:

### File Manager (library trash)

| Setting | Default | What it controls |
|---------|---------|------------------|
| **Trash retention** | 30 days | How long a soft-deleted file sits in the bin before the sweeper hard-deletes it. Range 1–365 days. |
| **Auto-purge enabled** | off | Master toggle for the scheduled purge that moves old library files into the trash. |
| **Auto-purge age** | 90 days | Files idle (no recent print, no recent edit) longer than this become eligible for auto-purge. |
| **Include never-printed** | off | When on, never-printed files also count toward the auto-purge threshold. When off, only printed files get auto-purged — protects files you uploaded but haven't printed yet. |

### Archive Settings (archive trash)

| Setting | Default | What it controls |
|---------|---------|------------------|
| **Trash retention** | 30 days | Same as above, for archives. |
| **Auto-purge enabled** | off | Master toggle for archive auto-purge. |
| **Auto-purge age** | 365 days | Archives older than this become eligible. Reprinting an archive refreshes its age clock — frequently-reprinted archives never auto-purge. |

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
