"""`llms.txt` and `llms-full.txt` for AI tools, from the English nav.

`llms.txt` (https://llmstxt.org) is a Markdown index a language model can
read in one request: the site's name, a short summary, then one link per page
with the page's own front-matter `description`, grouped by the nav's
sections. `llms-full.txt` carries the Markdown source of every English page in
the same order, so a tool that wants the whole manual makes one request
instead of a hundred.

Only the English build writes them; the Ukrainian pages are the same pages
under /uk/, and `llms.txt` says so once. mkdocs-static-i18n builds the other
languages from inside its own `on_post_build` (priority 50), on the same
config object, so this hook's `on_post_build` runs first (priority 100),
while `config` still describes the English build. The nav is kept from the
English `on_nav`; by `on_post_build` every page in it has been read, so its
title, meta and Markdown are filled in.
"""

from pathlib import Path

from mkdocs.plugins import event_priority
from mkdocs.structure.nav import Link, Section
from mkdocs.structure.pages import Page

LANDING = "https://bamdude.top"
REPO = "https://github.com/kainpl/bamdude"

_english_nav = None


def _language(config):
    return config.theme.get("language") or "en"


def on_nav(nav, config, files):
    global _english_nav
    if _language(config) == "en":
        _english_nav = nav
    return nav


def _walk(items, path, groups):
    """Collect `(section path, [entries])` in nav order: a run of pages, then each subsection."""
    run = []
    for item in items:
        if isinstance(item, Section):
            if run:
                groups.append((path, run))
                run = []
            _walk(item.children, [*path, item.title], groups)
        elif isinstance(item, (Page, Link)):
            run.append(item)
    if run:
        groups.append((path, run))


def _url(item):
    return item.canonical_url if isinstance(item, Page) else item.url


def _summary(config):
    site = config.site_url.rstrip("/")
    return (
        f"# {config.site_name}\n\n"
        "> The documentation of BamDude, a self-hosted print archive and farm-management system for "
        "Bambu Lab 3D printers: installation, every feature, the settings reference and the API.\n\n"
        "BamDude talks to Bambu Lab printers over the local network and needs no Bambu Cloud account. "
        f"The product site is {LANDING} (its own summary: {LANDING}/llms.txt); the source code is {REPO}. "
        f"Every page below also exists in Ukrainian under {site}/uk/. "
        f"The Markdown text of every English page, in this order, is in {site}/llms-full.txt.\n"
    )


@event_priority(100)
def on_post_build(config):
    if _language(config) != "en" or _english_nav is None:
        return
    groups = []
    _walk(_english_nav.items, [], groups)

    index = [_summary(config)]
    full = [_summary(config)]
    loose_runs = 0
    for path, entries in groups:
        if path:
            heading = " › ".join(path)
        else:  # top-level pages: the run before the first section, then any after it
            heading = "Overview" if loose_runs == 0 else "More"
            loose_runs += 1
        index.append(f"\n## {heading}\n\n")
        for item in entries:
            description = (item.meta.get("description") or "").strip() if isinstance(item, Page) else ""
            line = f"- [{item.title}]({_url(item)})"
            index.append(f"{line}: {description}\n" if description else f"{line}\n")
            if isinstance(item, Page) and item.markdown:
                full.append(f"\n---\n\n# {item.title}\n\nSource: {_url(item)}\n\n{item.markdown.strip()}\n")

    site_dir = Path(config.site_dir)
    (site_dir / "llms.txt").write_text("".join(index), encoding="utf-8", newline="\n")
    (site_dir / "llms-full.txt").write_text("".join(full), encoding="utf-8", newline="\n")
