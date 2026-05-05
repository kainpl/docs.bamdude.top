---
title: Full-Text Search
description: SQLite FTS5 (or PostgreSQL tsvector) search across archive print names, filenames, tags, notes, designer, and filament type — with prefix wildcards, exclusion, phrase matching, and a one-click index rebuild
---

# Full-Text Search

BamDude indexes a fixed set of archive metadata fields into a full-text search structure: SQLite installs get an FTS5 virtual table (`archive_fts`), PostgreSQL installs get a `tsvector` column with a GIN index. Both back the same `GET /api/v1/archives/search?q=...` endpoint. Search is wired up automatically by migration `m001`; no manual setup is needed.

## :material-magnify: What it indexes

The index covers six columns of `print_archives`:

| Field | What goes in |
|---|---|
| `print_name` | The print name from the 3MF or the user-edited override. |
| `filename` | The original 3MF filename. |
| `tags` | User-applied tags (comma-separated string). |
| `notes` | Free-form notes attached to the archive. |
| `designer` | Author / designer string from the 3MF metadata. |
| `filament_type` | The material code (PLA, PETG, ABS, …). |

That's it for the searchable surface. AMS colour names, printer name, project name, plate-level metadata, and library files are **not** in the index — see [Limits](#limits) below.

!!! note "Two backends, one endpoint"
    On SQLite the search runs `archive_fts MATCH :term`. On PostgreSQL it runs `search_vector @@ to_tsquery('simple', :term)` with `ts_rank` ordering. The route auto-detects the dialect via `is_postgres()`. If FTS itself fails (corrupt index, a malformed query that the parser rejects), the route silently falls back to a slower `LIKE` scan over the same columns, so search never goes 500 — just slower.

## :material-keyboard: Triggering search

The search box lives in the Archives toolbar. The frontend keeps the URL query in sync, so search results are shareable / bookmarkable.

There is no global `/` keyboard shortcut for archive search yet — the `/` shortcut is wired to the spool-list search box on the [Inventory](inventory.md) page only. Use the click-and-type pattern on the Archives page header.

## :material-format-text: Syntax

The route's behaviour depends on which database backend you're on, but both have the same observable feel for the common cases:

| Pattern | What it does | Backend notes |
|---|---|---|
| `vase` | Plain word match. | SQLite auto-appends `*`, so it's equivalent to `vase*`. PostgreSQL tokenises into `vase:*`. Either way, prefix matching is the default. |
| `vase*` | Explicit prefix. Matches `vase`, `vasely`, `vases`. | SQLite: handled natively. PostgreSQL: tokenised the same as `vase`. |
| `"calibration cube"` | Phrase match. Both words must appear adjacent and in order. | FTS5 supports phrase queries directly. |
| `vase OR cup` | Either word. | FTS5 supports `OR`; PostgreSQL `tsquery` treats space as `&` so use it sparingly on PG installs. |
| `phone -case` | Exclude word. Matches archives mentioning `phone` but not `case`. | FTS5 native. |

!!! tip "Keep queries simple on PostgreSQL"
    On PG the route splits your query on whitespace and joins with `&` (AND), then appends `:*` to each word for prefix matching (e.g. `vase calibration` → `vase:* & calibration:*`). Boolean `OR` and exclusion (`-`) are not pre-translated to `tsquery` syntax — they'll match literally as part of a word. If a query falls back to LIKE you'll get partial-substring matching across all six columns instead, which is more permissive but slower.

## :material-sort: Ranking and result shape

| Backend | Ranking |
|---|---|
| SQLite (FTS5) | `ORDER BY rank` — FTS5's built-in BM25-style ranking. |
| PostgreSQL | `ORDER BY ts_rank(search_vector, query) DESC`. Per-field weights: `print_name` = A, `filename` = B, `tags` = B, `designer` = C, `filament_type` = C, `notes` = D. So a hit on the print name outranks a hit on the notes. |

Trashed archives (`deleted_at IS NOT NULL`) are filtered out **after** the FTS lookup. That means trashed rows still occupy slots in the `LIMIT 50` window; if your query returns zero results but you're sure something matches, restore from [Library Trash](library-trash.md) (or its archive equivalent — same `deleted_at` column on archives).

## :material-filter: Combining with filters

Beyond the free-form `q`, the search endpoint accepts:

| Param | Purpose |
|---|---|
| `printer_id` | Restrict to one printer. |
| `project_id` | Restrict to one project. |
| `status` | `completed` / `failed` / `printing`. |
| `limit` | Default 50, max enforced upstream. |
| `offset` | Pagination. |

Filter chips on the Archives page also feed the regular `GET /api/v1/archives/?search=...` listing endpoint, which uses the same FTS path internally.

## :material-cog-refresh: Manual index rebuild

The triggers that maintain `archive_fts` (SQLite) and the BEFORE INSERT/UPDATE trigger (PostgreSQL) keep the index in sync automatically — every insert, update, and delete on `print_archives` propagates. You should rarely need to rebuild.

When to rebuild:

- After a failed schema migration that touched `print_archives`.
- After importing archives via direct SQL (skipping the ORM means triggers may not fire reliably depending on driver).
- If a search clearly returns wrong results that don't reflect the current row state.

How to rebuild:

```
POST /api/v1/archives/search/rebuild-index
```

Permission: `archives:update_all`. Returns `{"message": "Search index rebuilt with N entries"}`.

On SQLite this clears `archive_fts` and re-INSERTs every row from `print_archives`. On PostgreSQL it does `UPDATE print_archives SET print_name = print_name`, which fires the BEFORE INSERT/UPDATE trigger on every row and rebuilds `search_vector` in place.

!!! warning "Locks the archives table briefly"
    On a 100k-archive install a rebuild takes a few seconds and holds a lock on `print_archives`. Don't rebuild during a printing burst.

## :material-alert-outline: Limits

| What's NOT searchable | Why |
|---|---|
| Library files | The library uses a separate ORM-level filter, no FTS index. Library list endpoints accept a `search` param but it's a `LIKE` over filename/folder. |
| Projects | Same — listed via project list endpoint, no full-text index. |
| Settings, users, permissions | Not indexed — by design, to keep secrets out of FTS dumps. |
| AMS colour names | Colours live in the `color_catalog` table and are joined at render time; they're not denormalised onto `print_archives`. |
| Printer names | Same reason — printer name is a join, not a column on `print_archives`. Filter by `printer_id` instead. |
| Plate-level metadata | Stored as JSON inside `print_archives.extra_data`; FTS5/tsvector don't index nested JSON. |

If you need to filter on something that isn't in the FTS index, combine the search with the `printer_id` / `project_id` / `status` query params, or use the regular Archives list endpoint with its filter chips.

## :material-shield-key: Permissions

| Action | Permission |
|---|---|
| Search archives | `archives:read` |
| Rebuild index | `archives:update_all` |

## :material-api: API reference

```
GET /api/v1/archives/search?q=benchy
GET /api/v1/archives/search?q=benchy&printer_id=2&status=completed
POST /api/v1/archives/search/rebuild-index
```

The list endpoint (`GET /api/v1/archives/?search=...`) accepts the same `search` term and runs through the same FTS path internally, so any syntax that works on `/search` also works on the listing.
