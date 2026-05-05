---
title: External Links
description: Admin-defined custom sidebar links to external tools — wikis, helpdesks, dashboards, or anything else, with Lucide icons or uploaded custom images
---

# External Links

External Links let an admin add custom items to the BamDude sidebar that point at anywhere outside the app — your team wiki, a helpdesk ticket form, a Grafana dashboard, an OctoPrint instance, the Bambu Studio download page. Links are stored in BamDude's database, render below the built-in nav, and ship as part of the standard backup/restore cycle.

## :material-link: What it is

A small admin-managed table of `(name, url, icon, open_in_new_tab, sort_order)` rows. Anyone with `external_links:read` permission sees the rendered links in the sidebar; only users with `external_links:create` / `external_links:update` / `external_links:delete` can manage them. URLs are validated to start with `http://` or `https://` (other schemes like `mailto:` or `ssh://` are rejected by the backend validator).

There is **no per-group visibility** in BamDude's external_links model — every authenticated user with `external_links:read` sees the same list. If you need group-scoped links, use a dashboard tool with its own auth and link to it.

## :material-plus-circle: Adding a link

**Settings → External Links → Add Link** opens the form:

| Field | Notes |
|---|---|
| **Name** | 1–50 chars. Shown next to the icon in the sidebar. |
| **URL** | 1–500 chars. Must start with `http://` or `https://`. |
| **Icon** | Either pick a [Lucide](https://lucide.dev/icons/) icon by name from the icon picker, or upload a custom image. |
| **Open in new tab** | When `true`, the link opens with `target="_blank"` so BamDude stays in the current tab. Leave off for in-app navigation (only useful if the URL is on the same origin as BamDude). |

New links are appended at the bottom of the list (`sort_order` is auto-set to `max(existing) + 1`).

!!! tip "Lucide vs Material icon names"
    The upstream Bambuddy wiki referred to mkdocs-material icon names — BamDude actually uses [Lucide](https://lucide.dev/icons/) icon names (because the frontend imports `lucide-react`). If you don't see your icon, check the Lucide catalog, not Material Design Icons.

### Custom image icons

If a Lucide icon doesn't fit (e.g. you want a vendor logo), click **Upload custom icon** in the modal:

| Restriction | Value |
|---|---|
| Allowed extensions | `.png`, `.jpg`, `.jpeg`, `.gif`, `.svg`, `.webp`, `.ico` |
| Max file size | 1 MB |
| Storage | `<base_dir>/icons/<uuid>.<ext>` on disk |
| Served by | `GET /api/v1/external-links/{id}/icon` (unauthenticated, so `<img>` tags can load it without an Authorization header) |

Switching back from a custom icon to a Lucide preset deletes the uploaded file from disk on save.

## :material-sidebar: Sidebar position and behaviour

External links render **below the built-in BamDude nav** (Dashboard, Printers, Library, Archives, Inventory, etc.) in a separate section. There is no toggle to hide them per user — if a link is in the table, every authenticated user with `external_links:read` sees it.

| Behaviour | What happens |
|---|---|
| `open_in_new_tab = true` | Click opens the URL in a new tab (`target="_blank"`, `rel="noopener noreferrer"`). Useful for external tools you want side-by-side with BamDude. |
| `open_in_new_tab = false` | Click navigates the current tab. Only do this for URLs on the same origin (otherwise the SPA loses its state). |
| Custom icon set | The uploaded image is rendered. The `icon` field is ignored. |
| No custom icon | The Lucide icon named in `icon` is rendered. Defaults to `link` if unset. |

## :material-sort: Reordering

Drag-and-drop in **Settings → External Links** to change the order. The frontend sends a `PUT /api/v1/external-links/reorder` with the new ID list; the backend assigns `sort_order = index` to each. The new order takes effect on the next page load.

## :material-pencil: Editing and deleting

| Action | Endpoint | Permission |
|---|---|---|
| Edit fields (name / URL / icon / new-tab toggle) | `PATCH /api/v1/external-links/{id}` | `external_links:update` |
| Delete a link | `DELETE /api/v1/external-links/{id}` | `external_links:delete` |
| Replace custom icon | `POST /api/v1/external-links/{id}/icon` (multipart) | `external_links:update` |
| Remove custom icon | `DELETE /api/v1/external-links/{id}/icon` | `external_links:update` |

Deleting a link with a custom icon also removes the underlying file from `<base_dir>/icons/`.

## :material-lightbulb: Examples

### Internal wiki

| Field | Value |
|---|---|
| Name | `Team Wiki` |
| URL | `https://wiki.lan/3d-printing` |
| Icon | `book-open` |
| Open in new tab | yes |

### Ticket system / helpdesk

| Field | Value |
|---|---|
| Name | `Print Request` |
| URL | `https://helpdesk.example.com/forms/print-request` |
| Icon | `ticket` |
| Open in new tab | yes |

### Grafana / monitoring dashboard

| Field | Value |
|---|---|
| Name | `Farm Metrics` |
| URL | `https://grafana.lan/d/printers` |
| Icon | `chart-line` |
| Open in new tab | yes |

For BamDude's own metrics endpoint, see [Prometheus](prometheus.md).

### OctoPrint / Mainsail (mixed farm)

| Field | Value |
|---|---|
| Name | `Voron 2.4` |
| URL | `http://192.168.1.50` |
| Icon | `printer` |
| Open in new tab | yes |

## :material-backup-restore: Backup and restore

External links are part of the standard BamDude database, so they ride along with every backup. See [Backup](backup.md) for the full backup/restore protocol.

!!! warning "Custom icons are NOT in the backup"
    Database rows are backed up; the underlying files in `<base_dir>/icons/` are not part of the SQLite/PostgreSQL dump. If you restore a backup onto a fresh host without copying the `icons/` folder across, the rows survive but the `<img>` tags 404 and the sidebar falls back to the Lucide preset named in `icon`. Copy the `icons/` directory yourself when migrating hosts.

## :material-shield-key: Permissions

| Permission | Default groups |
|---|---|
| `external_links:read` | Administrators, Operators, Viewers |
| `external_links:create` | Administrators, Operators |
| `external_links:update` | Administrators, Operators |
| `external_links:delete` | Administrators, Operators |

`update` covers reordering, editing, and icon upload/delete (there is no separate `external_links:edit` — the permission name is `external_links:update`).

## :material-api: API reference

All endpoints live under `/api/v1/external-links` and require the matching permission unless noted.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/external-links/` | List all links, ordered by `sort_order` then `id`. |
| `POST` | `/external-links/` | Create a link. Body: `{name, url, icon, open_in_new_tab}`. |
| `GET` | `/external-links/{id}` | Fetch one link. |
| `PATCH` | `/external-links/{id}` | Update one or more fields. |
| `DELETE` | `/external-links/{id}` | Delete a link (and its custom icon file, if any). |
| `PUT` | `/external-links/reorder` | Body: `{ids: [...]}`. Reassigns `sort_order` based on list position. |
| `POST` | `/external-links/{id}/icon` | Multipart upload of a custom icon. |
| `DELETE` | `/external-links/{id}/icon` | Remove the custom icon and revert to the Lucide preset. |
| `GET` | `/external-links/{id}/icon` | Returns the icon file. **Unauthenticated** by design — `<img>` tags can't send bearer tokens. |
