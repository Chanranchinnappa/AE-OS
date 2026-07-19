"""Site inventory — turns a local static-site directory into page records.

Feeds real page data (title, meta description, h1, word count, internal
links) to the CMO agents, replacing the synthetic dicts used before the
first venture property existed. Deterministic parsing, zero tokens
(11_TOKEN_OPTIMIZATION.md Rule 5).
"""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from typing import Any

_SKIP_TEXT_TAGS = {"script", "style", "nav", "footer"}


class _PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.meta_description = ""
        self.h1 = ""
        self.internal_links: list[str] = []
        self.words = 0
        self._stack: list[str] = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "meta" and attrs.get("name") == "description":
            self.meta_description = attrs.get("content", "")
        if tag == "a":
            href = attrs.get("href", "")
            # Internal = same-site: root-relative or document-relative links.
            # (Sites deployed under a subpath, e.g. GitHub Pages project
            # sites, must use relative links — see brightpaths.)
            if href and not href.startswith(
                    ("http://", "https://", "//", "#", "mailto:")):
                self.internal_links.append(href)
        self._stack.append(tag)

    def handle_endtag(self, tag):
        while self._stack and self._stack.pop() != tag:
            pass

    def handle_data(self, data):
        if "title" in self._stack:
            self.title += data.strip()
        elif "h1" in self._stack:
            self.h1 += data.strip()
        if not any(t in self._stack for t in _SKIP_TEXT_TAGS) \
                and "title" not in self._stack:
            self.words += len(data.split())


def _url_for(html_file: Path, root: Path) -> str:
    rel = html_file.relative_to(root).as_posix()
    if rel == "index.html":
        return "/"
    return "/" + (rel[:-len(".html")] if rel.endswith(".html") else rel)


def inventory(site_root: str | Path) -> list[dict[str, Any]]:
    """Parse every .html file under site_root into a page record."""
    root = Path(site_root)
    if not root.is_dir():
        raise FileNotFoundError(f"site root not found: {root}")
    pages = []
    for f in sorted(root.rglob("*.html")):
        p = _PageParser()
        p.feed(f.read_text(encoding="utf-8"))
        pages.append({
            "url": _url_for(f, root),
            "file": str(f),
            "title": p.title,
            "meta_description": p.meta_description,
            "h1": p.h1,
            "word_count": p.words,
            "internal_links": sorted(set(p.internal_links)),
        })
    return pages
