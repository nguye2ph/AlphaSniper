"""Fetch and extract article body content from URLs."""

from dataclasses import dataclass

import httpx
import structlog
from bs4 import BeautifulSoup

logger = structlog.get_logger()

USER_AGENT = "Mozilla/5.0 (compatible; AlphaSniper/1.0)"


@dataclass
class ContentResult:
    body: str
    image_url: str | None = None
    author: str | None = None


async def fetch_article_content(url: str) -> ContentResult | None:
    """Fetch URL and extract article body. Returns None on failure."""
    if not url or not url.startswith("http"):
        return None
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": USER_AGENT})
            if resp.status_code != 200:
                logger.debug("scrape_non_200", url=url[:80], status=resp.status_code)
                return None
            return _parse_html(resp.text)
    except Exception as e:
        logger.debug("scrape_error", url=url[:80], error=str(e)[:60])
        return None


def _parse_html(html: str) -> ContentResult:
    """Extract body text, image, author from HTML."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove noise elements
    for tag in soup.find_all(["nav", "footer", "header", "script", "style", "aside"]):
        tag.decompose()

    body = _extract_body(soup)
    image_url = _extract_image(soup)
    author = _extract_author(soup)

    return ContentResult(body=body, image_url=image_url, author=author)


def _extract_body(soup: BeautifulSoup) -> str:
    """Extract main article text, try <article> then <main> then <body>."""
    for selector in ["article", "main", "[role='main']", ".article-body", ".post-content"]:
        el = soup.select_one(selector)
        if el:
            text = el.get_text(separator=" ", strip=True)
            if len(text) > 100:
                return text[:5000]
    # Fallback to body
    text = soup.get_text(separator=" ", strip=True)
    return text[:5000] if text else ""


def _extract_image(soup: BeautifulSoup) -> str | None:
    """Extract main image from og:image meta or first article img."""
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        return og["content"]
    img = soup.find("img", src=True)
    if img and img["src"].startswith("http"):
        return img["src"]
    return None


def _extract_author(soup: BeautifulSoup) -> str | None:
    """Extract author from meta tag or common selectors."""
    meta = soup.find("meta", attrs={"name": "author"})
    if meta and meta.get("content"):
        return meta["content"][:255]
    for sel in [".author", "[rel='author']", ".byline"]:
        el = soup.select_one(sel)
        if el:
            return el.get_text(strip=True)[:255]
    return None
