"""
Research Scraper Tools

Tools for scraping company information from reliable sources.
"""

import asyncio
import logging
import re
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse, urljoin

import httpx
from bs4 import BeautifulSoup

from src.config.settings import settings

logger = logging.getLogger(__name__)

# User agent for web scraping
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


async def scrape_website(url: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Scrape a company website for key information.

    Extracts: about page, services, team info, contact details.
    """
    result = {
        "url": url,
        "success": False,
        "pages_scraped": [],
        "data": {},
        "error": None,
    }

    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT}
        ) as client:
            # Scrape main page
            homepage = await _scrape_page(client, url)
            if homepage:
                result["pages_scraped"].append(url)
                result["data"]["homepage"] = homepage

            # Find and scrape key pages
            key_pages = ["about", "services", "products", "team", "contact", "pricing"]
            links = homepage.get("links", []) if homepage else []

            for page_type in key_pages:
                page_url = _find_page_url(url, links, page_type)
                if page_url and page_url not in result["pages_scraped"]:
                    page_data = await _scrape_page(client, page_url)
                    if page_data:
                        result["pages_scraped"].append(page_url)
                        result["data"][page_type] = page_data

            result["success"] = True

    except Exception as e:
        logger.error(f"Website scrape error for {url}: {e}")
        result["error"] = str(e)

    return result


async def _scrape_page(client: httpx.AsyncClient, url: str) -> Optional[Dict[str, Any]]:
    """Scrape a single page."""
    try:
        response = await client.get(url)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        # Extract data
        return {
            "url": str(response.url),
            "title": soup.title.string if soup.title else None,
            "meta_description": _get_meta(soup, "description"),
            "meta_keywords": _get_meta(soup, "keywords"),
            "headings": _get_headings(soup),
            "paragraphs": _get_paragraphs(soup),
            "links": _get_links(soup, url),
            "emails": _extract_emails(response.text),
            "phone_numbers": _extract_phones(response.text),
            "social_links": _get_social_links(soup),
        }

    except Exception as e:
        logger.error(f"Page scrape error for {url}: {e}")
        return None


def _get_meta(soup: BeautifulSoup, name: str) -> Optional[str]:
    """Get meta tag content."""
    tag = soup.find("meta", attrs={"name": name})
    if tag:
        return tag.get("content")
    return None


def _get_headings(soup: BeautifulSoup) -> List[str]:
    """Extract all headings."""
    headings = []
    for tag in ["h1", "h2", "h3"]:
        for h in soup.find_all(tag):
            text = h.get_text(strip=True)
            if text and len(text) > 3:
                headings.append(text)
    return headings[:20]  # Limit


def _get_paragraphs(soup: BeautifulSoup) -> List[str]:
    """Extract meaningful paragraphs."""
    paragraphs = []
    for p in soup.find_all("p"):
        text = p.get_text(strip=True)
        if text and len(text) > 50:  # Only meaningful paragraphs
            paragraphs.append(text)
    return paragraphs[:15]  # Limit


def _get_links(soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
    """Extract internal links."""
    links = []
    base_domain = urlparse(base_url).netloc

    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True)

        # Make absolute
        if href.startswith("/"):
            href = urljoin(base_url, href)

        # Only internal links
        if base_domain in href:
            links.append({"url": href, "text": text})

    return links[:50]  # Limit


def _get_social_links(soup: BeautifulSoup) -> Dict[str, str]:
    """Extract social media links."""
    social = {}
    patterns = {
        "linkedin": r"linkedin\.com/company/([^/\"'\s]+)",
        "twitter": r"twitter\.com/([^/\"'\s]+)",
        "facebook": r"facebook\.com/([^/\"'\s]+)",
        "instagram": r"instagram\.com/([^/\"'\s]+)",
        "youtube": r"youtube\.com/(channel|c|user)/([^/\"'\s]+)",
    }

    html = str(soup)
    for platform, pattern in patterns.items():
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            social[platform] = match.group(0)

    return social


def _extract_emails(text: str) -> List[str]:
    """Extract email addresses."""
    pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    emails = list(set(re.findall(pattern, text)))
    # Filter out common non-company emails
    filtered = [e for e in emails if not any(x in e.lower() for x in ["example", "email", "test"])]
    return filtered[:5]


def _extract_phones(text: str) -> List[str]:
    """Extract phone numbers."""
    patterns = [
        r"\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}",
        r"\(\d{2,4}\)\s?\d{3,4}[-.\s]?\d{3,4}",
    ]
    phones = []
    for pattern in patterns:
        phones.extend(re.findall(pattern, text))
    return list(set(phones))[:3]


def _find_page_url(base_url: str, links: List[Dict], page_type: str) -> Optional[str]:
    """Find URL for a specific page type."""
    keywords = {
        "about": ["about", "over-ons", "about-us", "who-we-are", "our-story"],
        "services": ["services", "diensten", "what-we-do", "solutions"],
        "products": ["products", "producten", "offerings", "platform"],
        "team": ["team", "people", "leadership", "about-us"],
        "contact": ["contact", "get-in-touch", "reach-us"],
        "pricing": ["pricing", "plans", "packages"],
    }

    search_terms = keywords.get(page_type, [page_type])

    for link in links:
        url_lower = link["url"].lower()
        text_lower = link.get("text", "").lower()

        for term in search_terms:
            if term in url_lower or term in text_lower:
                return link["url"]

    return None


async def search_web(
    query: str,
    num_results: int = 10,
) -> Dict[str, Any]:
    """
    Search the web for company information.

    Uses Brave Search API or Tavily if available.
    """
    result = {
        "query": query,
        "success": False,
        "results": [],
        "error": None,
    }

    # Try Brave Search first
    if settings.BRAVE_SEARCH_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    "https://api.search.brave.com/res/v1/web/search",
                    params={"q": query, "count": num_results},
                    headers={
                        "Accept": "application/json",
                        "X-Subscription-Token": settings.BRAVE_SEARCH_API_KEY,
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    for item in data.get("web", {}).get("results", []):
                        result["results"].append({
                            "title": item.get("title"),
                            "url": item.get("url"),
                            "description": item.get("description"),
                            "source": "brave",
                        })
                    result["success"] = True
                    return result

        except Exception as e:
            logger.error(f"Brave search error: {e}")

    # Try Tavily as fallback
    if settings.TAVILY_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": settings.TAVILY_API_KEY,
                        "query": query,
                        "max_results": num_results,
                        "include_answer": False,
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    for item in data.get("results", []):
                        result["results"].append({
                            "title": item.get("title"),
                            "url": item.get("url"),
                            "description": item.get("content", "")[:500],
                            "source": "tavily",
                        })
                    result["success"] = True
                    return result

        except Exception as e:
            logger.error(f"Tavily search error: {e}")

    result["error"] = "No search API available"
    return result


async def search_linkedin_company(company_name: str) -> Dict[str, Any]:
    """
    Search for company LinkedIn profile info.

    Note: We search for LinkedIn results, not scrape directly (ToS compliance).
    """
    query = f"site:linkedin.com/company {company_name}"
    search_results = await search_web(query, num_results=5)

    result = {
        "company_name": company_name,
        "success": False,
        "linkedin_url": None,
        "data": {},
    }

    if search_results["success"] and search_results["results"]:
        for item in search_results["results"]:
            if "linkedin.com/company" in item.get("url", ""):
                result["linkedin_url"] = item["url"]
                result["data"]["description"] = item.get("description")
                result["success"] = True
                break

    return result


async def search_crunchbase(company_name: str) -> Dict[str, Any]:
    """
    Search for company Crunchbase profile.
    """
    query = f"site:crunchbase.com/organization {company_name}"
    search_results = await search_web(query, num_results=5)

    result = {
        "company_name": company_name,
        "success": False,
        "crunchbase_url": None,
        "data": {},
    }

    if search_results["success"] and search_results["results"]:
        for item in search_results["results"]:
            if "crunchbase.com/organization" in item.get("url", ""):
                result["crunchbase_url"] = item["url"]
                result["data"]["description"] = item.get("description")
                result["success"] = True
                break

    return result


async def search_company_news(company_name: str, limit: int = 5) -> Dict[str, Any]:
    """
    Search for recent news about a company.
    """
    query = f"{company_name} company news"
    search_results = await search_web(query, num_results=limit * 2)

    result = {
        "company_name": company_name,
        "success": False,
        "articles": [],
    }

    if search_results["success"]:
        # Filter out non-news results
        news_domains = ["news", "techcrunch", "forbes", "bloomberg", "reuters", "bbc", "cnbc"]

        for item in search_results["results"]:
            url = item.get("url", "").lower()
            if any(domain in url for domain in news_domains):
                result["articles"].append(item)

            if len(result["articles"]) >= limit:
                break

        result["success"] = len(result["articles"]) > 0

    return result


async def search_job_postings(company_name: str) -> Dict[str, Any]:
    """
    Search for company job postings to infer tech stack and team growth.
    """
    query = f"{company_name} careers jobs"
    search_results = await search_web(query, num_results=10)

    result = {
        "company_name": company_name,
        "success": False,
        "job_urls": [],
        "inferred_tech": [],
        "hiring_roles": [],
    }

    if search_results["success"]:
        job_domains = ["careers", "jobs", "greenhouse", "lever", "workable", "linkedin.com/jobs"]

        for item in search_results["results"]:
            url = item.get("url", "").lower()
            desc = item.get("description", "").lower()

            if any(domain in url for domain in job_domains):
                result["job_urls"].append(item["url"])

            # Infer tech from descriptions
            tech_keywords = [
                "python", "javascript", "typescript", "react", "node",
                "aws", "gcp", "azure", "kubernetes", "docker",
                "salesforce", "hubspot", "zendesk", "jira",
                "postgresql", "mongodb", "redis",
            ]

            for tech in tech_keywords:
                if tech in desc and tech not in result["inferred_tech"]:
                    result["inferred_tech"].append(tech)

            # Extract job titles
            title = item.get("title", "")
            if any(role in title.lower() for role in ["engineer", "developer", "manager", "designer", "analyst"]):
                result["hiring_roles"].append(title)

        result["success"] = True

    return result


# Tool definitions for the agent
RESEARCH_SCRAPER_TOOLS = [
    {
        "name": "scrape_company_website",
        "description": "Scrape a company's website to extract information about their business, products, services, and team. Returns structured data from homepage and key pages.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The company website URL to scrape",
                },
            },
            "required": ["url"],
        },
    },
    {
        "name": "search_web",
        "description": "Search the web for information about a company. Use this to find news, profiles, and other public information.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query",
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return (default 10)",
                    "default": 10,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_linkedin_company",
        "description": "Search for a company's LinkedIn profile to get company size, industry, and description.",
        "input_schema": {
            "type": "object",
            "properties": {
                "company_name": {
                    "type": "string",
                    "description": "The company name to search for",
                },
            },
            "required": ["company_name"],
        },
    },
    {
        "name": "search_crunchbase",
        "description": "Search for a company's Crunchbase profile to get funding, investors, and company info.",
        "input_schema": {
            "type": "object",
            "properties": {
                "company_name": {
                    "type": "string",
                    "description": "The company name to search for",
                },
            },
            "required": ["company_name"],
        },
    },
    {
        "name": "search_company_news",
        "description": "Search for recent news articles about a company.",
        "input_schema": {
            "type": "object",
            "properties": {
                "company_name": {
                    "type": "string",
                    "description": "The company name to search for",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of articles (default 5)",
                    "default": 5,
                },
            },
            "required": ["company_name"],
        },
    },
    {
        "name": "search_job_postings",
        "description": "Search for company job postings to infer their tech stack and which teams are growing.",
        "input_schema": {
            "type": "object",
            "properties": {
                "company_name": {
                    "type": "string",
                    "description": "The company name to search for",
                },
            },
            "required": ["company_name"],
        },
    },
]


async def execute_research_tool(tool_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a research scraper tool."""
    tools = {
        "scrape_company_website": lambda: scrape_website(inputs.get("url")),
        "search_web": lambda: search_web(inputs.get("query"), inputs.get("num_results", 10)),
        "search_linkedin_company": lambda: search_linkedin_company(inputs.get("company_name")),
        "search_crunchbase": lambda: search_crunchbase(inputs.get("company_name")),
        "search_company_news": lambda: search_company_news(inputs.get("company_name"), inputs.get("limit", 5)),
        "search_job_postings": lambda: search_job_postings(inputs.get("company_name")),
    }

    if tool_name in tools:
        return await tools[tool_name]()
    else:
        return {"error": f"Unknown tool: {tool_name}"}
