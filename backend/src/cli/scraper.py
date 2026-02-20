"""
Lightweight E-Commerce Site Scraper

Scrapes a single URL to extract company profile data for report generation.
Simplified version of the full pre-research agent scraper.
"""

import logging
from typing import Any, Dict, List

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Known tech fingerprints in page source
TECH_FINGERPRINTS = {
    "shopify": ["cdn.shopify.com", "Shopify.theme", "shopify-section"],
    "woocommerce": ["woocommerce", "wc-blocks", "wp-content"],
    "bigcommerce": ["bigcommerce.com", "stencil-utils"],
    "magento": ["magento", "mage-init"],
    "klaviyo": ["klaviyo.com", "klOnsite"],
    "mailchimp": ["mailchimp.com", "mc-embedded"],
    "gorgias": ["gorgias.chat", "gorgias-chat"],
    "tidio": ["tidio.co", "tidioChatCode"],
    "zendesk": ["zendesk.com", "zdassets"],
    "klarna": ["klarna.com", "klarna-placement"],
    "afterpay": ["afterpay.com", "afterpay-placement"],
    "hotjar": ["hotjar.com", "hj-"],
    "google_analytics": ["google-analytics.com", "gtag", "googletagmanager"],
    "meta_pixel": ["facebook.net/tr", "fbevents.js"],
}


async def scrape_ecommerce_site(url: str, timeout: int = 15) -> Dict[str, Any]:
    """
    Scrape an e-commerce site for company profile data.

    Args:
        url: The website URL to scrape
        timeout: Request timeout in seconds

    Returns:
        Dict with: success, title, description, visible_tech, headings, error
    """
    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; CRB-Analyser/1.0)"}
        ) as client:
            response = await client.get(url)

        if response.status_code != 200:
            return {"success": False, "error": f"HTTP {response.status_code}"}

        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        # Extract metadata
        title = _get_title(soup)
        description = _get_description(soup)
        headings = _get_headings(soup)
        visible_tech = _detect_tech(html)

        return {
            "success": True,
            "title": title,
            "description": description,
            "headings": headings,
            "visible_tech": visible_tech,
            "url": url,
        }

    except Exception as e:
        logger.warning(f"Failed to scrape {url}: {e}")
        return {"success": False, "error": str(e)}


def _get_title(soup: BeautifulSoup) -> str:
    """Extract page title."""
    tag = soup.find("title")
    return tag.get_text(strip=True) if tag else ""


def _get_description(soup: BeautifulSoup) -> str:
    """Extract meta description or OG description."""
    # Try meta description
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        return meta["content"].strip()

    # Try Open Graph
    og = soup.find("meta", attrs={"property": "og:description"})
    if og and og.get("content"):
        return og["content"].strip()

    # Fallback: first substantial paragraph
    for p in soup.find_all("p"):
        text = p.get_text(strip=True)
        if len(text) > 50:
            return text[:300]

    return ""


def _get_headings(soup: BeautifulSoup) -> List[str]:
    """Extract h1 and h2 headings."""
    headings = []
    for tag in soup.find_all(["h1", "h2"], limit=10):
        text = tag.get_text(strip=True)
        if text:
            headings.append(text)
    return headings


def _detect_tech(html: str) -> List[str]:
    """Detect technologies from page source."""
    html_lower = html.lower()
    detected = []
    for tech, fingerprints in TECH_FINGERPRINTS.items():
        for fp in fingerprints:
            if fp.lower() in html_lower:
                detected.append(tech)
                break
    return detected
