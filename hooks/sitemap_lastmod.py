"""Give every sitemap entry a `<lastmod>` from git instead of the build clock.

MkDocs' `page.update_date` is the build date, so every deploy stamped all
146 URLs with "today". Google reads exactly one field of a sitemap entry —
`<lastmod>` (`<changefreq>` and `<priority>` are documented as ignored) —
and checks it against what changed on recrawl; a site whose lastmod is
always "now" loses that signal. One `git log --name-only` over `docs/` at
config time yields the last commit per source file (first sighting wins,
the log is newest-first); each page then carries it as `meta.git_lastmod`
for `overrides/sitemap.xml` to print. A docs page is one .md file, so
"sources of the page" is exact here, unlike the landing.

A shallow checkout has one commit and would date every file to HEAD, so
nothing is recorded then and the template writes no `<lastmod>` at all —
omitted beats wrong. Both workflows check out with fetch-depth 0 so that
branch is never taken there.
"""

import subprocess
from pathlib import Path

_dates: dict[Path, str] = {}


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def on_config(config):
    _dates.clear()
    try:
        if _git("rev-parse", "--is-shallow-repository").strip() == "true":
            return config
        root = Path(_git("rev-parse", "--show-toplevel").strip()).resolve()
        log = _git("log", "--format=__%cI", "--name-only", "--", "docs")
    except (subprocess.CalledProcessError, FileNotFoundError):
        return config
    current = None
    for line in log.splitlines():
        if line.startswith("__"):
            current = line[2:]
        elif line and current:
            _dates.setdefault((root / line).resolve(), current)
    return config


def on_page_markdown(markdown, page, config, files):
    if _dates and page.file.abs_src_path:
        stamp = _dates.get(Path(page.file.abs_src_path).resolve())
        if stamp:
            page.meta["git_lastmod"] = stamp
    return markdown
