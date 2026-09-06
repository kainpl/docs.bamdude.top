"""Make every `<link rel="alternate" hreflang>` a fully-qualified URL.

mkdocs-static-i18n fills `config.extra.alternate` per page in its
`on_page_context` (priority 50) with site-relative paths such as
`uk/features/notifications/`; Material then renders them through MkDocs'
`url` filter, which turns a relative path into a page-relative one
(`../../uk/features/notifications/`). Google reads hreflang only from
fully-qualified URLs, so as built the annotations said nothing.

The `url` filter passes anything with a scheme through untouched, so this
hook — which runs after the plugin because the default priority is 0 and
higher runs first — prefixes `site_url`. The plugin deep-copies its list on
every page, so mutating in place cannot leak across pages. The language
switcher renders from the same list and simply gains absolute links.

⚠ The per-page list is an *attribute* (`config.extra.alternate = …`), not
the `"alternate"` key: `extra` is a MkDocs Config, whose attribute
assignment does not touch its keys, and Jinja resolves `config.extra.alternate`
attribute-first. The key still holds the site-root pair from `on_config`.
Rewriting the key changes nothing on screen (measured 2026-09-06), so this
reads the attribute and falls back to the key only when it is absent.
"""

from urllib.parse import urlsplit


def on_page_context(context, page, config, nav):
    site_url = (config.site_url or "").rstrip("/")
    if not site_url:
        return context
    alternates = getattr(config.extra, "alternate", None)
    if alternates is None:
        alternates = config.extra.get("alternate")
    for alt in alternates or []:
        link = alt.get("link", "")
        if urlsplit(link).scheme:
            continue
        if link in (".", "./"):
            link = ""
        alt["link"] = f"{site_url}/{link.lstrip('/')}"
    return context
