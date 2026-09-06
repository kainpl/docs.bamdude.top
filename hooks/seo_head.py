"""Open Graph, Twitter card and JSON-LD for every docs page.

Material emits no `og:*` at all unless its `social` plugin is on, and that
plugin wants cairosvg plus a system cairo on the deploy runner and renders
one card per page per build. The docs share one static card per language
instead (`docs/assets/og-<lang>.png`, 1200×630, rendered by the landing's
`npm run og:docs`); the page-level facts ride in the tags.

JSON-LD is one `@graph` per page: the Organization and WebSite under the
same `@id`s the landing uses (so Google merges the two sites' records), a
`TechArticle` for the page with `dateModified` from git (set by
hooks/sitemap_lastmod.py, which runs earlier in the page pipeline), and a
`BreadcrumbList` from the nav path. Sections are not pages: a crumb is
emitted only where the section has an index page to link, because every
crumb but the last needs a URL to be valid.

Runs after mkdocs-static-i18n (priority 50) so `config.theme.language` is
the language being built. Only facts the code can vouch for go in — no
ratings, no versions, no profiles that do not exist.
"""

LANDING = "https://bamdude.top"
REPO = "https://github.com/kainpl/bamdude"
DOCKER_HUB = "https://hub.docker.com/r/kainpl/bamdude"
OG_LOCALES = {"en": "en_US", "uk": "uk_UA"}
HOME_NAMES = {"en": "Home", "uk": "Головна"}


def _breadcrumbs(page, lang, site_url):
    home = f"{site_url}/uk/" if lang == "uk" else f"{site_url}/"
    crumbs = [{"name": HOME_NAMES.get(lang, "Home"), "url": home}]
    for section in reversed(page.ancestors):
        index = next((c for c in section.children if c.is_page and c.is_index), None)
        if index is not None and index.canonical_url:
            crumbs.append({"name": section.title, "url": index.canonical_url})
    crumbs.append({"name": page.title, "url": page.canonical_url})
    return crumbs


def on_page_context(context, page, config, nav):
    site_url = (config.site_url or "").rstrip("/")
    if not site_url or not page.canonical_url:
        return context
    lang = config.theme.get("language") or "en"
    if lang not in OG_LOCALES:
        lang = "en"
    is_home = page.canonical_url.rstrip("/") in (site_url, f"{site_url}/uk")
    title = config.site_name if is_home else f"{page.title} - {config.site_name}"
    description = page.meta.get("description") or config.site_description or ""
    image = f"{site_url}/assets/og-{lang}.png"
    modified = page.meta.get("git_lastmod")
    org_id = f"{LANDING}/#organization"
    website_id = f"{site_url}/#website"
    crumbs = [] if is_home else _breadcrumbs(page, lang, site_url)
    breadcrumb_id = f"{page.canonical_url}#breadcrumb"

    article = {
        "@type": "TechArticle",
        "@id": page.canonical_url,
        "url": page.canonical_url,
        "headline": page.title,
        "description": description,
        "inLanguage": lang,
        "isPartOf": {"@id": website_id},
        "about": {"@id": f"{LANDING}/#software"},
        "author": {"@id": org_id},
        "publisher": {"@id": org_id},
        "image": image,
    }
    if modified:
        article["dateModified"] = modified
    if len(crumbs) > 1:
        article["breadcrumb"] = {"@id": breadcrumb_id}

    graph = [
        {
            "@type": "Organization",
            "@id": org_id,
            "name": "BamDude",
            "url": f"{LANDING}/",
            "logo": {
                "@type": "ImageObject",
                "url": f"{LANDING}/brand/png/icon-tile-512.png",
                "width": 512,
                "height": 512,
            },
            "sameAs": [REPO, DOCKER_HUB],
        },
        {
            "@type": "WebSite",
            "@id": website_id,
            "name": config.site_name,
            "url": f"{site_url}/",
            "inLanguage": ["en", "uk"],
            "publisher": {"@id": org_id},
        },
        article,
    ]
    if len(crumbs) > 1:
        graph.append(
            {
                "@type": "BreadcrumbList",
                "@id": breadcrumb_id,
                "itemListElement": [
                    {"@type": "ListItem", "position": n, "name": c["name"], "item": c["url"]}
                    for n, c in enumerate(crumbs, start=1)
                ],
            }
        )

    context["seo"] = {
        "title": title,
        "description": description,
        "url": page.canonical_url,
        "image": image,
        "image_alt": title,
        "og_locale": OG_LOCALES[lang],
        "og_locale_alt": OG_LOCALES["en" if lang == "uk" else "uk"],
        "modified": modified,
    }
    context["seo_jsonld"] = {"@context": "https://schema.org", "@graph": graph}
    return context
