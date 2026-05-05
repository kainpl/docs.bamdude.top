---
title: Keyboard shortcuts
description: Every keyboard shortcut wired into the BamDude UI — verified against the codebase, no aspirational fluff
---

# Keyboard shortcuts

BamDude has a deliberately small keyboard surface. The shortcuts below are the ones actually wired into the React app — the in-app shortcuts modal (open with `?`) lists the same set.

!!! tip "Open this list inside the app"
    Press ++question++ (i.e. ++shift+slash++) anywhere in BamDude to pop the same shortcuts modal that mirrors this page. Press ++esc++ or click outside to close.

---

## :material-keyboard: Global navigation

These work from any page. They fire only when no input field is focused (typing `1` in a search box still types `1` — the global handler skips inputs, textareas, and content-editable elements).

| Shortcut | Action |
|:--------:|--------|
| ++1++ | Jump to the 1st sidebar item |
| ++2++ | Jump to the 2nd sidebar item |
| ++3++ | Jump to the 3rd sidebar item |
| ++4++ | Jump to the 4th sidebar item |
| ++5++ | Jump to the 5th sidebar item |
| ++6++ | Jump to the 6th sidebar item |
| ++7++ | Jump to the 7th sidebar item |
| ++8++ | Jump to the 8th sidebar item |
| ++9++ | Jump to the 9th sidebar item |
| ++question++ | Show the keyboard-shortcuts modal |
| ++esc++ | Close the shortcuts modal (when open) |

The number keys map to the **current order of your sidebar**, including any external links you've added. So `1` is whatever sits at the top — for default installs that's Printers, but if you've reordered the sidebar or pinned external links to the top, the numbers follow that order.

!!! note "External-link items"
    If a number maps to an external link, the action depends on the link's `open_in_new_tab` flag — either a new tab opens, or BamDude navigates to the embedded `/external/<id>` viewer.

---

## :material-archive: Archives page

The Archives page adds two extra shortcuts on top of global navigation.

| Shortcut | Action |
|:--------:|--------|
| ++slash++ | Focus the search box |
| ++esc++ | Clear selection (in selection mode) / blur the search input |

That's it for archive-specific shortcuts — there's no arrow-key card-grid navigation, no ++del++-to-delete hotkey, no spacebar-to-toggle-select. Selection is done with click + shift-click + ctrl/cmd-click. Right-click (or long-press on mobile) opens the context menu for delete, edit, and other per-card actions.

---

## :material-package-variant: K-Profiles page

Selection-mode shortcuts on the K-Profiles tab inside the Cloud Profiles page.

| Shortcut | Action |
|:--------:|--------|
| ++r++ | Refresh profile list |
| ++n++ | Open the New profile modal |
| ++esc++ | Exit selection mode |

These fire only when no modal is open and no input is focused.

---

## :material-image-multiple: Photo gallery & lightbox modals

Inside the photo gallery modal and the Makerworld lightbox preview:

| Shortcut | Action |
|:--------:|--------|
| ++arrow-left++ | Previous image |
| ++arrow-right++ | Next image |
| ++esc++ | Close the lightbox |

---

## :material-application-cog: Modals & dialogs

Almost every modal in BamDude (~50 of them) wires the same baseline:

| Shortcut | Action |
|:--------:|--------|
| ++esc++ | Close the modal (or cancel, when there's a destructive in-flight action like a Purge) |
| ++enter++ | Submit when focus is in an input that's wired for it (e.g. inline rename, tag-add, search input) |

Confirmation modals (Purge Old Files, Purge Archives, Confirm dialogs) deliberately ignore ++esc++ while a request is in flight so you can't cancel mid-purge.

---

## :material-form-textbox: Form navigation

Standard browser behaviour — no BamDude-specific overrides:

| Shortcut | Action |
|:--------:|--------|
| ++tab++ | Next form field |
| ++shift+tab++ | Previous form field |
| ++enter++ | Submit (in single-line inputs and inline editors) |
| ++esc++ | Cancel inline edit / blur input |

---

## :material-mouse: Mouse + keyboard combos

Used across selectable lists (archives, library, queue, profiles):

| Combination | Action |
|:-----------:|--------|
| ++ctrl++ + click *(or ++cmd++ + click on macOS)* | Toggle selection of one item |
| ++shift++ + click | Range select between two items |
| Right-click | Open context menu (long-press on touch devices) |

---

## :material-magnify: Search syntax

The Archives search is a full-text search over the print archive. Once you've focused it with ++slash++, you can use plain words plus the standard FTS5 operators (quoted phrases, `OR`, `-` for negation). For full guidance on what fields are searchable and how filters combine see [Archive history](../features/archiving.md).

---

## :material-cog: Customization

Keyboard shortcuts are **not** user-customizable. The bindings above are hard-coded in the React layer; if you want a different layout, that's a frontend change rather than a settings toggle.

---

## :material-human: Accessibility

Every shortcut has an equivalent UI button or menu item — sidebar items have visible nav links, the shortcuts modal has a footer "Press Esc or click outside to close" hint, and search inputs are reachable through normal Tab navigation. You can run BamDude with the keyboard alone or with a screen reader without memorizing any shortcut from this page.

---

## :material-information: What this page is **not**

If you came here looking for shortcuts that exist in other tools — Ctrl+K command palettes, vim-style `g g` / `g a` jumps, queue-row `j`/`k` navigation, ++del++-to-delete in archives, ++f2++-to-rename in the file manager — those aren't wired in BamDude today. The number-key sidebar nav + ++slash++ + ++question++ is the entire global surface, and that's by design: a small surface that's stable across releases beats a long table that drifts out of sync with the code.

If a missing shortcut would genuinely speed up your workflow, that's fair feedback for a feature request.
