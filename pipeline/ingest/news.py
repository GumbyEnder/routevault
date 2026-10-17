"""AI/tech news ingest. Politics-filtered RSS → SQLite."""

from __future__ import annotations

import hashlib
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

USER_AGENT = "RouteVault/1.0 (https://routevault-production.up.railway.app)"

FEEDS: list[tuple[str, str]] = [
    ("Hacker News AI", "https://hnrss.org/newest?q=AI+OR+LLM+OR+OpenAI+OR+Anthropic"),
    ("The Verge AI", "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
    ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
    ("Simon Willison", "https://simonwillison.net/atom/everything/"),
    ("Hugging Face", "https://huggingface.co/blog/feed.xml"),
    ("Google AI", "https://blog.google/technology/ai/rss/"),
    ("Ars Technica", "https://feeds.arstechnica.com/arstechnica/index"),
    ("MIT Tech Review", "https://www.technologyreview.com/topic/artificial-intelligence/feed"),
    ("OpenAI", "https://openai.com/news/rss.xml"),
]

POLITICS_RE = re.compile(
    r"\b("
    r"election|elections|electoral|president|presidential|congress|congressional|"
    r"senator|senate race|democrat|democratic party|republican party|\bgop\b|"
    r"impeach|primaries|campaign trail|white house|capitol hill|"
    r"supreme court justice|trump\b|biden\b|kamala|maga\b|"
    r"netanyahu|hamas|gaza|ukraine war|nato troops|geopolitics"
    r")\b",
    re.I,
)

TAG_RE = re.compile(r"<[^>]+>")
ATOM = {"atom": "http://www.w3.org/2005/Atom"}


def news_id(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()


def strip_html(text: str) -> str:
    text = TAG_RE.sub(" ", unescape(text or ""))
    return re.sub(r"\s+", " ", text).strip()


def is_politics(title: str, summary: str) -> bool:
    blob = f"{title} {summary}"
    return bool(POLITICS_RE.search(blob))


def _text(el: ET.Element | None) -> str:
    if el is None:
        return ""
    if el.text and el.text.strip():
        return el.text.strip()
    return strip_html("".join(el.itertext()))


def _child(el: ET.Element, *names: str) -> ET.Element | None:
    for name in names:
        found = el.find(name)
        if found is not None:
            return found
        found = el.find(name, ATOM)
        if found is not None:
            return found
    return None


def parse_published(raw: str) -> str | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        dt = parsedate_to_datetime(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError, OverflowError):
        pass
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except ValueError:
        return raw


def parse_feed(xml_bytes: bytes, source: str) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_bytes)
    items: list[dict[str, Any]] = []
    rss_items = root.findall(".//item")
    atom_entries = root.findall("atom:entry", ATOM) or root.findall(
        "{http://www.w3.org/2005/Atom}entry"
    )
    nodes = rss_items or atom_entries
    for node in nodes:
        title = _text(_child(node, "title", "atom:title"))
        link_el = _child(node, "link", "atom:link")
        link = ""
        if link_el is not None:
            link = (link_el.get("href") or _text(link_el)).strip()
        if not link:
            guid = _child(node, "guid", "id", "atom:id")
            link = _text(guid)
        summary = _text(
            _child(node, "description", "summary", "atom:summary", "content", "atom:content")
        )
        published = parse_published(
            _text(_child(node, "pubDate", "published", "updated", "atom:published", "atom:updated"))
        )
        if not title or not link:
            continue
        summary = strip_html(summary)[:2000]
        if is_politics(title, summary):
            continue
        items.append(
            {
                "id": news_id(link),
                "url": link,
                "title": strip_html(title)[:500],
                "source": source,
                "published_at": published,
                "summary": summary,
            }
        )
    return items


def fetch_feed(url: str, timeout: int = 25) -> bytes:
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml"})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read()


def collect_news(feeds: list[tuple[str, str]] | None = None) -> dict[str, Any]:
    feeds = feeds or FEEDS
    kept: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    seen: set[str] = set()
    for source, url in feeds:
        try:
            raw = fetch_feed(url)
            for item in parse_feed(raw, source):
                if item["id"] in seen:
                    continue
                seen.add(item["id"])
                kept.append(item)
        except (HTTPError, URLError, ET.ParseError, TimeoutError, OSError) as exc:
            errors.append({"source": source, "url": url, "error": str(exc)})
    kept.sort(key=lambda r: r.get("published_at") or "", reverse=True)
    return {
        "items": kept,
        "errors": errors,
        "feeds": len(feeds),
        "kept": len(kept),
    }
