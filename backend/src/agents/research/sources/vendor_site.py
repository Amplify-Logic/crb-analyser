"""
Vendor website scraper using Crawl4AI + Claude extraction.

Quality Improvements:
1. Smarter page rendering - wait for elements, scroll, multiple URL patterns
2. Better content extraction - CSS selectors, noise filtering
3. Multi-stage LLM extraction - identify, extract, validate with confidence
4. Multi-source enrichment - G2/Capterra cross-reference
"""

import asyncio
import json
import re
import structlog
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse, urljoin

from anthropic import Anthropic

from ..schemas import ExtractedPricing, PricingTier

logger = structlog.get_logger()


# =============================================================================
# Configuration
# =============================================================================

class ScraperConfig:
    """Scraper configuration constants."""
    # Retry settings
    MAX_RETRIES = 3
    BASE_DELAY_SECONDS = 1.0
    MAX_DELAY_SECONDS = 10.0

    # JS rendering delays (escalating)
    JS_DELAYS = [3.0, 5.0, 8.0]

    # Rate limiting
    MAX_CONCURRENT_REQUESTS = 3
    MIN_DELAY_BETWEEN_REQUESTS = 1.0

    # Content thresholds
    MIN_CONTENT_LENGTH = 200
    MIN_PRICING_CONTENT_LENGTH = 500  # After filtering
    MAX_CONTENT_FOR_LLM = 20000

    # Timeouts
    CRAWL_TIMEOUT_SECONDS = 45

    # Pricing URL patterns to try
    PRICING_URL_PATTERNS = [
        "/pricing",
        "/plans",
        "/pricing-plans",
        "/prices",
        "/plans-pricing",
        "/subscription",
    ]


# Global semaphore for rate limiting
_request_semaphore: Optional[asyncio.Semaphore] = None
_domain_last_request: dict[str, float] = {}


def _get_semaphore() -> asyncio.Semaphore:
    """Get or create the global request semaphore."""
    global _request_semaphore
    if _request_semaphore is None:
        _request_semaphore = asyncio.Semaphore(ScraperConfig.MAX_CONCURRENT_REQUESTS)
    return _request_semaphore


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class ExtractionResult:
    """Result of multi-stage extraction."""
    success: bool
    data: Optional[dict] = None
    confidence: float = 0.0
    extraction_notes: Optional[str] = None
    error: Optional[str] = None


@dataclass
class PageContent:
    """Processed page content ready for extraction."""
    url: str
    raw_markdown: str
    filtered_content: str
    pricing_sections: list[str]
    has_pricing_indicators: bool
    content_quality_score: float


# =============================================================================
# Error Types
# =============================================================================

class ScrapeError(Exception):
    """Base class for scraping errors."""
    def __init__(self, message: str, retryable: bool = False):
        super().__init__(message)
        self.retryable = retryable


class CrawlError(ScrapeError):
    """Error during page crawling."""
    pass


class ContentError(ScrapeError):
    """Error with page content (empty, blocked, etc)."""
    pass


class ExtractionError(ScrapeError):
    """Error extracting data from content."""
    pass


class RateLimitError(ScrapeError):
    """Rate limited by target site."""
    def __init__(self, message: str):
        super().__init__(message, retryable=True)


# =============================================================================
# Rate Limiting
# =============================================================================

async def _wait_for_rate_limit(url: str) -> None:
    """Wait for rate limit before making request to domain."""
    domain = urlparse(url).netloc
    now = asyncio.get_event_loop().time()

    if domain in _domain_last_request:
        elapsed = now - _domain_last_request[domain]
        if elapsed < ScraperConfig.MIN_DELAY_BETWEEN_REQUESTS:
            wait_time = ScraperConfig.MIN_DELAY_BETWEEN_REQUESTS - elapsed
            logger.debug("rate_limit_wait", domain=domain, wait_seconds=wait_time)
            await asyncio.sleep(wait_time)

    _domain_last_request[domain] = asyncio.get_event_loop().time()


# =============================================================================
# URL Discovery
# =============================================================================

def _get_pricing_urls(base_url: str) -> list[str]:
    """Generate list of potential pricing URLs to try."""
    parsed = urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"

    urls = []

    # If URL already looks like a pricing page, use it first
    if any(p in base_url.lower() for p in ["pricing", "plans", "price"]):
        urls.append(base_url)

    # Add common pricing URL patterns
    for pattern in ScraperConfig.PRICING_URL_PATTERNS:
        url = urljoin(base, pattern)
        if url not in urls:
            urls.append(url)

    # Add the base URL as fallback
    if base_url not in urls:
        urls.append(base_url)

    return urls


# =============================================================================
# Content Filtering (Improvement #2)
# =============================================================================

# Patterns that indicate pricing content
PRICING_INDICATORS = [
    r'\$\d+',  # Dollar amounts
    r'€\d+',   # Euro amounts
    r'£\d+',   # Pound amounts
    r'/month',
    r'/mo\b',
    r'/year',
    r'/yr\b',
    r'per month',
    r'per user',
    r'per seat',
    r'billed annually',
    r'billed monthly',
    r'free trial',
    r'free tier',
    r'enterprise',
    r'professional',
    r'starter',
    r'basic plan',
    r'premium',
    r'contact sales',
    r'get started',
    r'try free',
]

# Patterns to filter out (noise)
NOISE_PATTERNS = [
    r'cookie\s*(policy|consent|settings)',
    r'privacy\s*policy',
    r'terms\s*(of\s*service|and\s*conditions)',
    r'©\s*\d{4}',
    r'all\s*rights\s*reserved',
    r'follow\s*us\s*on',
    r'subscribe\s*to\s*(our\s*)?(newsletter|updates)',
    r'(facebook|twitter|linkedin|instagram|youtube)',
    r'navigation|menu|header|footer',
    r'sign\s*in|log\s*in|sign\s*up',
    r'already\s*have\s*an?\s*account',
]


def _extract_pricing_sections(markdown: str) -> list[str]:
    """Extract sections that likely contain pricing information."""
    sections = []

    # Split by headers
    header_pattern = r'^#{1,3}\s+(.+)$'
    lines = markdown.split('\n')

    current_section = []
    current_header = ""
    in_pricing_section = False

    pricing_headers = ['pricing', 'plans', 'price', 'subscription', 'billing', 'cost', 'tier']

    for line in lines:
        header_match = re.match(header_pattern, line, re.MULTILINE)

        if header_match:
            # Save previous section if it was pricing-related
            if in_pricing_section and current_section:
                sections.append('\n'.join(current_section))

            current_header = header_match.group(1).lower()
            current_section = [line]
            in_pricing_section = any(h in current_header for h in pricing_headers)
        else:
            current_section.append(line)

            # Check if line has pricing indicators
            if any(re.search(p, line, re.IGNORECASE) for p in PRICING_INDICATORS[:6]):
                in_pricing_section = True

    # Don't forget the last section
    if in_pricing_section and current_section:
        sections.append('\n'.join(current_section))

    return sections


def _filter_noise(markdown: str) -> str:
    """Remove noise content that doesn't contain pricing info."""
    lines = markdown.split('\n')
    filtered_lines = []

    for line in lines:
        # Skip lines that match noise patterns
        is_noise = any(re.search(p, line, re.IGNORECASE) for p in NOISE_PATTERNS)
        if is_noise and not any(re.search(p, line, re.IGNORECASE) for p in PRICING_INDICATORS):
            continue

        # Skip very short lines that don't have pricing info
        if len(line.strip()) < 10 and not any(re.search(p, line, re.IGNORECASE) for p in PRICING_INDICATORS[:6]):
            continue

        filtered_lines.append(line)

    return '\n'.join(filtered_lines)


def _extract_tables(markdown: str) -> list[str]:
    """Extract markdown tables which often contain pricing."""
    tables = []
    lines = markdown.split('\n')

    current_table = []
    in_table = False

    for line in lines:
        # Detect table rows (contain |)
        if '|' in line and line.strip().startswith('|'):
            in_table = True
            current_table.append(line)
        elif in_table:
            if line.strip() == '' or not '|' in line:
                if current_table:
                    tables.append('\n'.join(current_table))
                current_table = []
                in_table = False

    if current_table:
        tables.append('\n'.join(current_table))

    return tables


def _calculate_content_quality(markdown: str) -> float:
    """Calculate a quality score for the content (0-1)."""
    if not markdown:
        return 0.0

    score = 0.0

    # Check for pricing indicators
    indicator_count = sum(
        1 for p in PRICING_INDICATORS
        if re.search(p, markdown, re.IGNORECASE)
    )
    score += min(indicator_count / 10, 0.4)  # Max 0.4 from indicators

    # Check for price patterns (actual numbers)
    price_pattern = r'[\$€£]\s*\d+(?:[.,]\d{2})?'
    prices = re.findall(price_pattern, markdown)
    score += min(len(prices) / 5, 0.3)  # Max 0.3 from prices

    # Check for tables
    if '|' in markdown and '---' in markdown:
        score += 0.15

    # Check for tier/plan names
    tier_names = ['free', 'starter', 'basic', 'pro', 'professional', 'enterprise', 'business', 'team', 'growth']
    tier_count = sum(1 for t in tier_names if t in markdown.lower())
    score += min(tier_count / 4, 0.15)

    return min(score, 1.0)


def _process_page_content(url: str, markdown: str) -> PageContent:
    """Process raw markdown into structured content for extraction."""
    # Filter noise
    filtered = _filter_noise(markdown)

    # Extract pricing sections
    sections = _extract_pricing_sections(markdown)

    # Also extract tables
    tables = _extract_tables(markdown)
    if tables:
        sections.extend(tables)

    # Check for pricing indicators
    has_indicators = any(
        re.search(p, markdown, re.IGNORECASE)
        for p in PRICING_INDICATORS
    )

    # Calculate quality score
    quality = _calculate_content_quality(markdown)

    return PageContent(
        url=url,
        raw_markdown=markdown,
        filtered_content=filtered,
        pricing_sections=sections,
        has_pricing_indicators=has_indicators,
        content_quality_score=quality,
    )


# =============================================================================
# Smart Page Rendering (Improvement #1)
# =============================================================================

async def _crawl_with_smart_rendering(
    url: str,
    vendor_name: str,
    js_delay: float,
) -> tuple[bool, str, str]:
    """
    Crawl page with smart rendering strategies.

    Returns: (success, markdown, error_message)
    """
    try:
        from crawl4ai import AsyncWebCrawler
    except ImportError:
        return False, "", "crawl4ai not installed"

    # JavaScript to scroll and wait for dynamic content
    js_code = """
    // Scroll to load lazy content
    async function scrollPage() {
        await new Promise(resolve => {
            let totalHeight = 0;
            const distance = 300;
            const timer = setInterval(() => {
                window.scrollBy(0, distance);
                totalHeight += distance;
                if (totalHeight >= document.body.scrollHeight) {
                    clearInterval(timer);
                    window.scrollTo(0, 0);
                    resolve();
                }
            }, 100);
        });
    }
    await scrollPage();

    // Wait for pricing elements to load
    await new Promise(resolve => setTimeout(resolve, 1000));
    """

    # CSS selectors to wait for (common pricing page elements)
    wait_selectors = [
        "[class*='pricing']",
        "[class*='price']",
        "[class*='plan']",
        "[class*='tier']",
        "[data-pricing]",
        ".pricing-table",
        ".pricing-card",
    ]

    try:
        async with AsyncWebCrawler(
            headless=True,
            verbose=False,
        ) as crawler:
            result = await asyncio.wait_for(
                crawler.arun(
                    url=url,
                    cache_mode="bypass",
                    delay_before_return_html=js_delay,
                    js_code=js_code,
                    # Note: Removed wait_for as it can cause timeouts on some sites
                ),
                timeout=ScraperConfig.CRAWL_TIMEOUT_SECONDS,
            )

            if not result.success:
                return False, "", result.error_message or "Crawl failed"

            markdown = result.markdown or ""
            return True, markdown, ""

    except asyncio.TimeoutError:
        return False, "", f"Timeout after {ScraperConfig.CRAWL_TIMEOUT_SECONDS}s"
    except Exception as e:
        # Handle playwright-specific errors gracefully
        error_str = str(e)
        if "TargetClosedError" in error_str or "Target page" in error_str:
            return False, "", "Browser closed unexpectedly - retrying"
        return False, "", error_str


# =============================================================================
# Multi-Stage LLM Extraction (Improvement #3)
# =============================================================================

def _stage1_identify_pricing(content: PageContent, vendor_name: str) -> dict:
    """Stage 1: Identify if pricing info exists and assess quality."""
    client = Anthropic()

    # Use the best content we have
    if content.pricing_sections:
        text = "\n\n---\n\n".join(content.pricing_sections[:3])
    else:
        text = content.filtered_content

    if len(text) > 8000:
        text = text[:8000]

    prompt = f"""Analyze this content from {vendor_name}'s website and determine if it contains pricing information.

<content>
{text}
</content>

Return a JSON object:
{{
    "has_pricing": true/false,
    "pricing_type": "public|contact_sales|freemium|none",
    "confidence": 0.0-1.0,
    "tier_names_found": ["list", "of", "tier", "names"],
    "currencies_found": ["USD", "EUR", etc],
    "price_range": {{"min": number_or_null, "max": number_or_null}},
    "notes": "brief description of what pricing info was found"
}}

Return ONLY valid JSON."""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )

        content_text = response.content[0].text.strip()
        content_text = _clean_json_response(content_text)
        return json.loads(content_text)

    except Exception as e:
        logger.warning("stage1_failed", vendor=vendor_name, error=str(e))
        return {"has_pricing": content.has_pricing_indicators, "confidence": 0.3}


def _stage2_extract_details(content: PageContent, vendor_name: str, stage1_result: dict) -> dict:
    """Stage 2: Extract detailed pricing information."""
    client = Anthropic()

    # Build context from stage 1
    context = ""
    if stage1_result.get("tier_names_found"):
        context += f"Expected tiers: {', '.join(stage1_result['tier_names_found'])}\n"
    if stage1_result.get("currencies_found"):
        context += f"Currency: {stage1_result['currencies_found'][0]}\n"

    # Use best available content
    if content.pricing_sections:
        text = "\n\n---\n\n".join(content.pricing_sections)
    else:
        text = content.filtered_content

    if len(text) > ScraperConfig.MAX_CONTENT_FOR_LLM:
        text = text[:ScraperConfig.MAX_CONTENT_FOR_LLM]

    prompt = f"""Extract detailed pricing information for {vendor_name}.

{context}

<page_content>
{text}
</page_content>

Extract ALL pricing tiers you can find. Look for:
- Pricing tables or cards
- Plan names with associated prices
- Feature lists per tier
- Annual vs monthly pricing differences

Return a JSON object with this structure:
{{
    "vendor_name": "string",
    "pricing_model": "subscription|usage|one-time|freemium",
    "currency": "USD|EUR|GBP",
    "free_tier": true/false/null,
    "free_trial_days": number or null,
    "starting_price": lowest_monthly_price_as_number_or_null,
    "tiers": [
        {{
            "name": "tier name",
            "price": monthly_price_as_number_or_null,
            "price_annual": annual_monthly_equivalent_or_null,
            "billing": "monthly|annual|one-time",
            "features": ["feature1", "feature2", "feature3"],
            "limits": "e.g., '5 users', '1000 contacts'"
        }}
    ],
    "enterprise_available": true/false/null,
    "notes": "important notes about pricing, limitations, etc"
}}

Rules:
- Extract EVERY tier you find, even if price is unclear
- For annual prices shown, calculate monthly equivalent (divide by 12)
- If price says "Contact Sales", set price to null but include the tier
- starting_price = lowest non-zero monthly price
- Include up to 5 key features per tier
- Return ONLY valid JSON"""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2500,
            messages=[{"role": "user", "content": prompt}],
        )

        content_text = response.content[0].text.strip()
        content_text = _clean_json_response(content_text)
        return json.loads(content_text)

    except Exception as e:
        logger.warning("stage2_failed", vendor=vendor_name, error=str(e))
        return {"error": str(e)}


def _stage3_validate_and_score(extracted: dict, vendor_name: str, content: PageContent) -> ExtractionResult:
    """Stage 3: Validate extracted data and calculate confidence score."""
    if "error" in extracted:
        return ExtractionResult(
            success=False,
            error=extracted["error"],
            confidence=0.0,
        )

    # Validate and build result
    try:
        validated = _validate_pricing_data(extracted, vendor_name)
        if "error" in validated:
            return ExtractionResult(
                success=False,
                error=validated["error"],
                confidence=0.0,
            )

        # Calculate confidence score
        confidence = _calculate_extraction_confidence(validated, content)

        # Build notes about extraction quality
        notes = []
        tiers = validated.get("tiers", [])
        if not tiers:
            notes.append("No pricing tiers found")
        elif len(tiers) == 1:
            notes.append("Only 1 tier found")
        else:
            notes.append(f"Found {len(tiers)} tiers")

        if validated.get("starting_price"):
            notes.append(f"Starting at ${validated['starting_price']}")

        if confidence < 0.5:
            notes.append("Low confidence - may need manual review")

        return ExtractionResult(
            success=True,
            data=validated,
            confidence=confidence,
            extraction_notes="; ".join(notes),
        )

    except Exception as e:
        return ExtractionResult(
            success=False,
            error=str(e),
            confidence=0.0,
        )


def _calculate_extraction_confidence(data: dict, content: PageContent) -> float:
    """Calculate confidence score for extraction (0-1)."""
    score = 0.0

    # Base score from content quality
    score += content.content_quality_score * 0.3

    # Tiers found
    tiers = data.get("tiers", [])
    if len(tiers) >= 3:
        score += 0.25
    elif len(tiers) >= 1:
        score += 0.15

    # Prices found
    prices_with_values = [t for t in tiers if t.get("price") is not None]
    if prices_with_values:
        score += 0.2

    # Starting price found
    if data.get("starting_price"):
        score += 0.1

    # Features found
    tiers_with_features = [t for t in tiers if t.get("features")]
    if tiers_with_features:
        score += 0.1

    # Currency specified
    if data.get("currency"):
        score += 0.05

    return min(score, 1.0)


def _clean_json_response(text: str) -> str:
    """Clean JSON response from LLM, handling code blocks."""
    if text.startswith("```"):
        lines = text.split("\n")
        json_lines = []
        in_block = False
        for line in lines:
            if line.startswith("```"):
                if in_block:
                    break
                in_block = True
                continue
            if in_block:
                json_lines.append(line)
        text = "\n".join(json_lines).strip()
    return text


# =============================================================================
# Core Scraping Function
# =============================================================================

async def scrape_vendor_pricing(
    url: str,
    vendor_name: str,
    max_retries: int = ScraperConfig.MAX_RETRIES,
) -> dict:
    """
    Scrape pricing page with quality-focused extraction.

    Features:
    - Tries multiple pricing URL patterns
    - Smart JS rendering with scrolling
    - Content filtering and section extraction
    - Multi-stage LLM extraction with confidence scoring

    Returns:
        dict with keys:
        - success: bool
        - data: ExtractedPricing (if success)
        - confidence: float (0-1)
        - error: str (if failed)
        - error_type: str
        - attempts: int
        - urls_tried: list[str]
    """
    # Generate URLs to try
    urls_to_try = _get_pricing_urls(url)

    best_result = None
    best_confidence = 0.0
    all_errors = []
    attempts = 0

    semaphore = _get_semaphore()

    for try_url in urls_to_try[:3]:  # Try up to 3 URLs
        for attempt in range(max_retries):
            attempts += 1
            js_delay = ScraperConfig.JS_DELAYS[min(attempt, len(ScraperConfig.JS_DELAYS) - 1)]

            async with semaphore:
                await _wait_for_rate_limit(try_url)

                logger.info(
                    "scraping_vendor_pricing",
                    vendor=vendor_name,
                    url=try_url,
                    js_delay=js_delay,
                    attempt=attempt + 1,
                )

                # Crawl with smart rendering
                success, markdown, error = await _crawl_with_smart_rendering(
                    try_url, vendor_name, js_delay
                )

                if not success:
                    all_errors.append(f"{try_url}: {error}")

                    # Check if retryable
                    if "timeout" in error.lower() or "rate" in error.lower():
                        await asyncio.sleep(ScraperConfig.BASE_DELAY_SECONDS * (2 ** attempt))
                        continue
                    else:
                        break  # Non-retryable, try next URL

                logger.info(
                    "page_crawled",
                    vendor=vendor_name,
                    markdown_length=len(markdown),
                )

                # Process content
                content = _process_page_content(try_url, markdown)

                if not content.has_pricing_indicators and content.content_quality_score < 0.2:
                    all_errors.append(f"{try_url}: No pricing content detected")
                    break  # Try next URL

                # Multi-stage extraction
                stage1 = _stage1_identify_pricing(content, vendor_name)

                if not stage1.get("has_pricing") and stage1.get("confidence", 0) < 0.3:
                    all_errors.append(f"{try_url}: Stage 1 - no pricing found")
                    break  # Try next URL

                stage2 = _stage2_extract_details(content, vendor_name, stage1)
                result = _stage3_validate_and_score(stage2, vendor_name, content)

                if result.success and result.confidence > best_confidence:
                    best_result = result
                    best_confidence = result.confidence

                    # If we got a good result, stop trying
                    if best_confidence >= 0.7:
                        break

                # Successful extraction, move on
                break

        # If we got a good result, stop trying more URLs
        if best_result and best_confidence >= 0.7:
            break

    # Return best result or error
    if best_result and best_result.success:
        return {
            "success": True,
            "data": best_result.data,
            "confidence": best_result.confidence,
            "extraction_notes": best_result.extraction_notes,
            "attempts": attempts,
            "urls_tried": urls_to_try[:3],
        }
    else:
        return {
            "success": False,
            "error": "; ".join(all_errors) if all_errors else "Unknown error",
            "error_type": "extraction",
            "attempts": attempts,
            "urls_tried": urls_to_try[:3],
        }


# =============================================================================
# Validation
# =============================================================================

def _validate_pricing_data(data: dict, vendor_name: str) -> dict:
    """Validate and normalize extracted pricing data."""
    try:
        # Build tiers list
        tiers = []
        for tier_data in data.get("tiers", []):
            if not isinstance(tier_data, dict):
                continue
            tier = PricingTier(
                name=tier_data.get("name", "Unknown"),
                price=_safe_float(tier_data.get("price")),
                price_annual=_safe_float(tier_data.get("price_annual")),
                billing=tier_data.get("billing"),
                features=tier_data.get("features", [])[:5],
            )
            tiers.append(tier)

        # Calculate starting_price if not provided
        starting_price = _safe_float(data.get("starting_price"))
        if starting_price is None and tiers:
            prices = [t.price for t in tiers if t.price and t.price > 0]
            if prices:
                starting_price = min(prices)

        pricing = ExtractedPricing(
            vendor_name=data.get("vendor_name") or vendor_name,
            pricing_model=data.get("pricing_model"),
            currency=data.get("currency") or "USD",
            free_tier=data.get("free_tier"),
            free_trial_days=_safe_int(data.get("free_trial_days")),
            tiers=tiers,
            enterprise_available=data.get("enterprise_available"),
            starting_price=starting_price,
            notes=data.get("notes"),
        )

        return pricing.model_dump()

    except Exception as e:
        logger.warning("validation_failed", vendor=vendor_name, error=str(e))
        return {"error": f"Validation failed: {e}"}


def _safe_float(value) -> Optional[float]:
    """Safely convert to float."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _safe_int(value) -> Optional[int]:
    """Safely convert to int."""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


# =============================================================================
# Multi-Source Enrichment (Improvement #4)
# =============================================================================

async def enrich_with_g2_data(vendor_name: str, vendor_slug: str) -> Optional[dict]:
    """
    Fetch additional data from G2 for cross-reference.

    Returns ratings, review counts, and verified pricing if available.
    """
    try:
        from crawl4ai import AsyncWebCrawler
    except ImportError:
        return None

    g2_url = f"https://www.g2.com/products/{vendor_slug}/pricing"

    try:
        async with AsyncWebCrawler(headless=True, verbose=False) as crawler:
            result = await asyncio.wait_for(
                crawler.arun(url=g2_url, cache_mode="bypass", delay_before_return_html=2.0),
                timeout=20,
            )

            if not result.success:
                return None

            markdown = result.markdown or ""
            if len(markdown) < 100:
                return None

            # Extract G2-specific data
            client = Anthropic()
            prompt = f"""Extract G2 review data for {vendor_name} from this page.

<content>
{markdown[:10000]}
</content>

Return JSON:
{{
    "g2_rating": number (0-5) or null,
    "review_count": number or null,
    "g2_pricing_info": "summary of pricing shown on G2" or null,
    "category_rank": number or null,
    "satisfaction_score": number (0-100) or null
}}

Return ONLY valid JSON."""

            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}],
            )

            content = _clean_json_response(response.content[0].text.strip())
            return json.loads(content)

    except Exception as e:
        logger.debug("g2_enrichment_failed", vendor=vendor_name, error=str(e))
        return None


async def scrape_vendor_pricing_enriched(
    url: str,
    vendor_name: str,
    vendor_slug: Optional[str] = None,
) -> dict:
    """
    Scrape pricing with multi-source enrichment.

    Combines website scraping with G2 data for higher confidence.
    """
    # First, scrape the vendor's website
    result = await scrape_vendor_pricing(url, vendor_name)

    # If we got a result, try to enrich with G2 data
    if result.get("success") and vendor_slug:
        g2_data = await enrich_with_g2_data(vendor_name, vendor_slug)

        if g2_data:
            result["g2_data"] = g2_data

            # Boost confidence if G2 data confirms pricing
            if g2_data.get("g2_pricing_info"):
                result["confidence"] = min(result.get("confidence", 0) + 0.1, 1.0)
                result["extraction_notes"] = (
                    result.get("extraction_notes", "") + "; G2 data available"
                )

    return result


# =============================================================================
# Batch Scraping
# =============================================================================

async def scrape_multiple_vendors(
    vendors: list[dict],
    enrich: bool = False,
) -> list[dict]:
    """
    Scrape pricing for multiple vendors.

    Args:
        vendors: List of dicts with 'slug', 'name', 'pricing_url' keys
        enrich: If True, also fetch G2 data for enrichment

    Returns:
        List of results with vendor_slug and scrape result
    """
    results = []

    for vendor in vendors:
        slug = vendor.get("slug", "unknown")
        name = vendor.get("name", slug)
        url = vendor.get("pricing_url") or vendor.get("website")

        if not url:
            results.append({
                "vendor_slug": slug,
                "success": False,
                "error": "No URL provided",
                "error_type": "input",
            })
            continue

        if enrich:
            result = await scrape_vendor_pricing_enriched(url, name, slug)
        else:
            result = await scrape_vendor_pricing(url, name)

        result["vendor_slug"] = slug
        results.append(result)

    return results
