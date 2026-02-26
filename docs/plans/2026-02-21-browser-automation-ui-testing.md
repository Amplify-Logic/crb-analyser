# Browser Automation & Agentic UI Testing — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add browser automation capabilities (Playwright) to CRB Analyser for three purposes: (1) agentic UI testing of critical user flows, (2) enhanced site analysis for richer report input data, (3) enhanced vendor research for JS-heavy vendor sites. Built as a 5-phase layered architecture: Skills → Agents → Commands → Task Runner.

**Architecture:** Follows the 4-layer pattern (capability → scale → orchestration → reusability). Python Playwright skills in `backend/src/skills/browser/` for production use (site analysis, vendor research). Claude Code skills/commands for development use (UI testing, report validation). Both share the same Playwright foundation.

**Tech Stack:** Python 3.12, Playwright (async), existing FastAPI backend, existing skills registry, Claude Code commands

**Design source:** Brainstorming session 2026-02-21 (Dan's 4-layer agentic browser architecture adapted for CRB)

**CRB Context — load these references during implementation:**
- `.claude/reference/skills.md` — skill patterns
- `.claude/reference/api-development.md` — error handling
- `.claude/reference/testing.md` — test patterns

---

## Phase 1: Playwright Foundation (Skill Layer)

> **Risk: zero** — additive only, no existing code changes

### Task 1: Install Playwright and Create Browser Skill

**Files:**
- Create: `backend/src/skills/browser/__init__.py`
- Create: `backend/src/skills/browser/playwright_browser.py`
- Create: `backend/tests/skills/browser/__init__.py`
- Create: `backend/tests/skills/browser/test_playwright_browser.py`
- Modify: `backend/requirements.txt` (add `playwright`)

**Step 1: Install Playwright**

```bash
cd backend && source venv/bin/activate
pip install playwright
playwright install chromium
pip freeze | grep playwright >> requirements.txt
```

Verify installation:
```bash
cd backend && python -c "from playwright.async_api import async_playwright; print('Playwright installed')"
```

**Step 2: Write the failing test**

Create `backend/tests/skills/browser/__init__.py` (empty).

Create `backend/tests/skills/browser/test_playwright_browser.py`:

```python
"""Tests for Playwright browser skill."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.skills.browser.playwright_browser import PlaywrightBrowserSkill
from src.skills.base import SkillContext


class TestPlaywrightBrowserSkill:
    """Test the Playwright browser skill."""

    def test_skill_metadata(self):
        """Skill has correct metadata."""
        skill = PlaywrightBrowserSkill()
        assert skill.name == "playwright-browser"
        assert skill.requires_llm is False

    @pytest.mark.asyncio
    async def test_navigate_and_screenshot(self):
        """Navigate to URL and take screenshot."""
        skill = PlaywrightBrowserSkill()
        context = SkillContext(
            industry="ecommerce",
            metadata={
                "action": "navigate_and_screenshot",
                "url": "https://example.com",
                "screenshot_path": "/tmp/test_screenshot.png",
            }
        )

        # Mock playwright
        mock_page = AsyncMock()
        mock_page.title = AsyncMock(return_value="Example Domain")
        mock_page.url = "https://example.com"
        mock_page.content = AsyncMock(return_value="<html><body>Hello</body></html>")

        with patch.object(skill, '_get_page', return_value=mock_page):
            result = await skill.run(context)

        assert result.success is True
        assert result.data["title"] == "Example Domain"
        mock_page.goto.assert_called_once_with("https://example.com", wait_until="networkidle")
        mock_page.screenshot.assert_called_once()

    @pytest.mark.asyncio
    async def test_scrape_with_js_rendering(self):
        """Scrape page with full JS rendering."""
        skill = PlaywrightBrowserSkill()
        context = SkillContext(
            industry="ecommerce",
            metadata={
                "action": "scrape",
                "url": "https://example.com",
            }
        )

        mock_page = AsyncMock()
        mock_page.title = AsyncMock(return_value="JS Store")
        mock_page.url = "https://example.com"
        mock_page.content = AsyncMock(return_value="""
            <html><head><title>JS Store</title></head>
            <body>
                <h1>Welcome</h1>
                <script src="https://cdn.shopify.com/theme.js"></script>
                <script src="https://static.klaviyo.com/onsite/js/klaviyo.js"></script>
            </body></html>
        """)

        with patch.object(skill, '_get_page', return_value=mock_page):
            result = await skill.run(context)

        assert result.success is True
        assert "shopify" in result.data.get("visible_tech", [])
        assert "klaviyo" in result.data.get("visible_tech", [])

    @pytest.mark.asyncio
    async def test_handles_timeout_gracefully(self):
        """Timeout returns failure, not exception."""
        skill = PlaywrightBrowserSkill()
        context = SkillContext(
            industry="ecommerce",
            metadata={
                "action": "navigate_and_screenshot",
                "url": "https://slow-site.example.com",
                "screenshot_path": "/tmp/test.png",
            }
        )

        mock_page = AsyncMock()
        mock_page.goto = AsyncMock(side_effect=TimeoutError("Navigation timeout"))

        with patch.object(skill, '_get_page', return_value=mock_page):
            result = await skill.run(context)

        assert result.success is False

    @pytest.mark.asyncio
    async def test_parallel_sessions(self):
        """Multiple sessions can run with different names."""
        skill = PlaywrightBrowserSkill()
        # Verify session naming works
        assert skill._session_name("user-flow-1") == "user-flow-1"
        assert skill._session_name("vendor-research") == "vendor-research"
```

Run to verify failure:
```bash
cd backend && python -m pytest tests/skills/browser/test_playwright_browser.py -v
```

Expected: `ModuleNotFoundError: No module named 'src.skills.browser'`

**Step 3: Implement the Playwright browser skill**

Create `backend/src/skills/browser/__init__.py`:

```python
"""Browser automation skills using Playwright."""
from .playwright_browser import PlaywrightBrowserSkill

__all__ = ["PlaywrightBrowserSkill"]
```

Create `backend/src/skills/browser/playwright_browser.py`:

```python
"""
Playwright Browser Skill

Provides browser automation capabilities for:
- JS-rendered page scraping (enhanced site analysis)
- Screenshot capture (UI testing, report validation)
- Navigation and interaction (vendor research, form filling)

Uses Playwright async API with headless Chromium by default.
Supports parallel named sessions for concurrent browser work.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.skills.base import BaseSkill, SkillContext, SkillError

logger = logging.getLogger(__name__)

# Reuse tech fingerprints from CLI scraper for consistency
TECH_FINGERPRINTS = {
    "shopify": ["cdn.shopify.com", "Shopify.theme", "shopify-section", "myshopify.com"],
    "woocommerce": ["woocommerce", "wc-blocks", "wp-content"],
    "bigcommerce": ["bigcommerce.com", "stencil-utils"],
    "magento": ["magento", "mage-init"],
    "klaviyo": ["klaviyo.com", "klOnsite", "static.klaviyo.com"],
    "mailchimp": ["mailchimp.com", "mc-embedded"],
    "gorgias": ["gorgias.chat", "gorgias-chat"],
    "tidio": ["tidio.co", "tidioChatCode"],
    "zendesk": ["zendesk.com", "zdassets"],
    "klarna": ["klarna.com", "klarna-placement"],
    "afterpay": ["afterpay.com", "afterpay-placement"],
    "hotjar": ["hotjar.com", "hj-"],
    "google_analytics": ["google-analytics.com", "gtag", "googletagmanager"],
    "meta_pixel": ["facebook.net/tr", "fbevents.js"],
    "intercom": ["intercom.io", "intercomcdn.com"],
    "drift": ["drift.com", "driftt.com"],
    "hubspot": ["hubspot.com", "hs-scripts.com", "hs-analytics"],
    "segment": ["segment.com", "cdn.segment.com"],
    "stripe": ["stripe.com", "js.stripe.com"],
    "paypal": ["paypal.com", "paypalobjects.com"],
    "recharge": ["rechargepayments.com", "rechargecdn.com"],
    "yotpo": ["yotpo.com", "staticw2.yotpo.com"],
    "judge_me": ["judge.me"],
    "loox": ["loox.io"],
    "privy": ["privy.com"],
    "smile_io": ["smile.io"],
}


class PlaywrightBrowserSkill(BaseSkill[Dict[str, Any]]):
    """
    Browser automation skill using Playwright.

    Actions (passed via context.metadata["action"]):
    - "scrape": Navigate and extract page data with JS rendering
    - "navigate_and_screenshot": Navigate, screenshot, return page info
    - "extract_tech": Navigate and detect technologies
    - "multi_page_scrape": Scrape multiple pages from same domain

    Config (via context.metadata):
    - "url": Target URL (required)
    - "screenshot_path": Where to save screenshot (optional)
    - "session_name": Named session for parallel execution (optional)
    - "headless": Run headless (default: True)
    - "timeout_ms": Navigation timeout in ms (default: 30000)
    - "wait_for": CSS selector to wait for before extraction (optional)
    """

    name = "playwright-browser"
    description = "Browser automation with Playwright for JS-rendered scraping and screenshots"
    version = "1.0.0"
    requires_llm = False

    # Track active browser instances by session name
    _browsers: Dict[str, Any] = {}

    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        """Execute browser action based on context.metadata."""
        action = context.metadata.get("action", "scrape")
        url = context.metadata.get("url")

        if not url:
            raise SkillError(self.name, "Missing 'url' in metadata", recoverable=False)

        page = await self._get_page(context)

        try:
            if action == "scrape":
                return await self._action_scrape(page, context)
            elif action == "navigate_and_screenshot":
                return await self._action_navigate_screenshot(page, context)
            elif action == "extract_tech":
                return await self._action_extract_tech(page, context)
            elif action == "multi_page_scrape":
                return await self._action_multi_page(page, context)
            else:
                raise SkillError(self.name, f"Unknown action: {action}", recoverable=False)
        finally:
            # Close page but keep browser for session reuse
            if not context.metadata.get("keep_page", False):
                await page.close()

    async def _get_page(self, context: SkillContext) -> Any:
        """Get or create a browser page for this session."""
        from playwright.async_api import async_playwright

        session = context.metadata.get("session_name", "default")
        headless = context.metadata.get("headless", True)

        if session not in self._browsers:
            pw = await async_playwright().start()
            browser = await pw.chromium.launch(headless=headless)
            self._browsers[session] = {"pw": pw, "browser": browser}

        browser = self._browsers[session]["browser"]
        browser_context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        return await browser_context.new_page()

    def _session_name(self, name: str) -> str:
        """Return session name for parallel execution tracking."""
        return name

    async def _action_scrape(self, page: Any, context: SkillContext) -> Dict[str, Any]:
        """Navigate to URL and extract page data with JS rendering."""
        url = context.metadata["url"]
        timeout = context.metadata.get("timeout_ms", 30000)
        wait_for = context.metadata.get("wait_for")

        await page.goto(url, wait_until="networkidle", timeout=timeout)

        if wait_for:
            await page.wait_for_selector(wait_for, timeout=timeout)

        title = await page.title()
        html = await page.content()
        current_url = page.url

        # Extract structured data
        visible_tech = self._detect_tech(html)
        headings = await self._extract_headings(page)
        description = await self._extract_description(page)
        links = await self._extract_links(page)

        # Optional screenshot
        screenshot_path = context.metadata.get("screenshot_path")
        if screenshot_path:
            Path(screenshot_path).parent.mkdir(parents=True, exist_ok=True)
            await page.screenshot(path=screenshot_path, full_page=True)

        return {
            "url": current_url,
            "title": title,
            "description": description,
            "headings": headings,
            "visible_tech": visible_tech,
            "link_count": len(links),
            "screenshot_path": screenshot_path,
        }

    async def _action_navigate_screenshot(self, page: Any, context: SkillContext) -> Dict[str, Any]:
        """Navigate and take screenshot."""
        url = context.metadata["url"]
        screenshot_path = context.metadata.get("screenshot_path", "/tmp/crb_screenshot.png")
        timeout = context.metadata.get("timeout_ms", 30000)

        await page.goto(url, wait_until="networkidle", timeout=timeout)

        title = await page.title()

        Path(screenshot_path).parent.mkdir(parents=True, exist_ok=True)
        await page.screenshot(path=screenshot_path, full_page=True)

        return {
            "url": page.url,
            "title": title,
            "screenshot_path": screenshot_path,
        }

    async def _action_extract_tech(self, page: Any, context: SkillContext) -> Dict[str, Any]:
        """Navigate and detect all technologies."""
        url = context.metadata["url"]
        timeout = context.metadata.get("timeout_ms", 30000)

        await page.goto(url, wait_until="networkidle", timeout=timeout)

        html = await page.content()
        visible_tech = self._detect_tech(html)

        # Also check for technologies loaded via network requests
        # (Playwright can intercept these in future enhancement)

        return {
            "url": page.url,
            "title": await page.title(),
            "visible_tech": visible_tech,
            "tech_count": len(visible_tech),
        }

    async def _action_multi_page(self, page: Any, context: SkillContext) -> Dict[str, Any]:
        """Scrape multiple pages from the same domain."""
        urls = context.metadata.get("urls", [context.metadata["url"]])
        timeout = context.metadata.get("timeout_ms", 30000)
        results = []

        for url in urls:
            try:
                await page.goto(url, wait_until="networkidle", timeout=timeout)
                title = await page.title()
                html = await page.content()
                results.append({
                    "url": page.url,
                    "title": title,
                    "visible_tech": self._detect_tech(html),
                    "success": True,
                })
            except Exception as e:
                results.append({
                    "url": url,
                    "error": str(e),
                    "success": False,
                })

        # Merge all detected tech
        all_tech = set()
        for r in results:
            all_tech.update(r.get("visible_tech", []))

        return {
            "pages": results,
            "all_visible_tech": sorted(all_tech),
            "pages_scraped": sum(1 for r in results if r["success"]),
            "pages_failed": sum(1 for r in results if not r["success"]),
        }

    def _detect_tech(self, html: str) -> List[str]:
        """Detect technologies from rendered page source."""
        html_lower = html.lower()
        detected = []
        for tech, fingerprints in TECH_FINGERPRINTS.items():
            for fp in fingerprints:
                if fp.lower() in html_lower:
                    detected.append(tech)
                    break
        return detected

    async def _extract_headings(self, page: Any) -> List[str]:
        """Extract h1 and h2 headings from page."""
        headings = await page.eval_on_selector_all(
            "h1, h2",
            "els => els.slice(0, 10).map(el => el.textContent.trim()).filter(t => t.length > 0)"
        )
        return headings

    async def _extract_description(self, page: Any) -> str:
        """Extract meta description from page."""
        desc = await page.evaluate("""() => {
            const meta = document.querySelector('meta[name="description"]');
            if (meta) return meta.content;
            const og = document.querySelector('meta[property="og:description"]');
            if (og) return og.content;
            const p = document.querySelector('p');
            return p ? p.textContent.trim().substring(0, 300) : '';
        }""")
        return desc or ""

    async def _extract_links(self, page: Any) -> List[str]:
        """Extract all links from page."""
        return await page.eval_on_selector_all(
            "a[href]",
            "els => els.map(el => el.href).filter(h => h.startsWith('http'))"
        )

    async def cleanup(self) -> None:
        """Close all browser instances."""
        for session_name, session in self._browsers.items():
            try:
                await session["browser"].close()
                await session["pw"].stop()
            except Exception as e:
                logger.warning(f"Failed to close browser session {session_name}: {e}")
        self._browsers.clear()
```

**Step 4: Run tests to verify they pass**

```bash
cd backend && python -m pytest tests/skills/browser/test_playwright_browser.py -v
```

Expected: All 5 tests PASS.

**Step 5: Verify skill auto-discovery**

```bash
cd backend && python -c "
from src.skills.registry import get_registry
reg = get_registry()
browser_skills = [n for n in reg.list_names() if 'browser' in n or 'playwright' in n]
print(f'Browser skills found: {browser_skills}')
assert len(browser_skills) > 0, 'PlaywrightBrowserSkill not auto-discovered'
print('Auto-discovery working')
"
```

**Step 6: Commit**

```bash
git add backend/src/skills/browser/ backend/tests/skills/browser/ backend/requirements.txt
git commit -m "feat: add Playwright browser skill with JS-rendered scraping and screenshots"
```

---

## Phase 2: Agentic UI Testing (Agent + Command Layer)

> **Risk: low** — testing infrastructure only, doesn't touch production code

### Task 2: Create User Story Format and Critical Flow Stories

**Files:**
- Create: `tests/ui/stories/quiz-flow.yaml`
- Create: `tests/ui/stories/report-viewer.yaml`
- Create: `tests/ui/stories/checkout.yaml`
- Create: `tests/ui/stories/admin-dashboard.yaml`
- Create: `tests/ui/stories/landing-page.yaml`
- Create: `tests/ui/screenshots/.gitkeep`

**Step 1: Create the stories directory structure**

```bash
mkdir -p tests/ui/stories tests/ui/screenshots
```

**Step 2: Create user story files**

User stories use a simple YAML format that agents parse into steps.

Create `tests/ui/stories/quiz-flow.yaml`:

```yaml
name: Quiz Flow - Complete Journey
description: Test the main conversion path from landing to quiz completion
url: http://localhost:5174/quiz
priority: critical

steps:
  - name: Load quiz page
    action: navigate
    expect: Quiz page loads with first question visible

  - name: Answer industry question
    action: click option containing "E-commerce" or first available option
    expect: Next question appears, progress bar advances

  - name: Answer company size question
    action: click option for company size
    expect: Next question appears

  - name: Complete remaining questions
    action: answer all remaining questions by clicking first available option
    expect: Each question advances to next, progress increases

  - name: View results
    action: wait for results/score page
    expect: AI readiness score displayed, teaser report preview visible

  - name: CTA visible
    action: check for purchase/checkout button
    expect: Call-to-action button is visible and clickable
```

Create `tests/ui/stories/report-viewer.yaml`:

```yaml
name: Report Viewer - Rendering
description: Verify report renders all sections correctly
url: http://localhost:5174/report/{report_id}
priority: critical
requires:
  report_id: "a valid report ID from the database"

steps:
  - name: Load report page
    action: navigate to report URL
    expect: Report loads without errors, executive summary visible

  - name: Check executive summary
    action: scroll to executive summary section
    expect: AI readiness score, key metrics, and summary text visible

  - name: Check findings section
    action: scroll to findings/recommendations
    expect: At least 3 findings displayed with CRB options

  - name: Check charts
    action: look for chart/visualization elements
    expect: At least one chart or data visualization renders

  - name: Check navigation
    action: click table of contents or section links
    expect: Page scrolls to correct section

  - name: Responsive check
    action: resize viewport to 375px width (mobile)
    expect: Content reflows properly, no horizontal scroll
```

Create `tests/ui/stories/checkout.yaml`:

```yaml
name: Checkout Flow
description: Test payment flow UI (not actual payment)
url: http://localhost:5174/checkout/{session_id}
priority: critical
requires:
  session_id: "a completed quiz session ID"

steps:
  - name: Load checkout page
    action: navigate to checkout URL
    expect: Price displayed (EUR 147), order summary visible

  - name: Verify pricing
    action: check displayed price
    expect: EUR 147 shown, no other hidden fees

  - name: Check Stripe elements
    action: look for Stripe payment form
    expect: Card input fields visible (Stripe Elements loaded)
```

Create `tests/ui/stories/admin-dashboard.yaml`:

```yaml
name: Admin Dashboard
description: Test admin pages load and display data
url: http://localhost:5174/admin
priority: high
requires:
  auth: "admin user session"

steps:
  - name: Load admin dashboard
    action: navigate to admin URL
    expect: Dashboard loads with stats/metrics

  - name: Check vendor admin
    action: navigate to vendor management
    expect: Vendor list loads, search/filter available

  - name: Check knowledge base admin
    action: navigate to knowledge base
    expect: Knowledge categories listed, entries viewable
```

Create `tests/ui/stories/landing-page.yaml`:

```yaml
name: Landing Page
description: Test landing page loads and CTA works
url: http://localhost:5174/
priority: high

steps:
  - name: Load landing page
    action: navigate to root URL
    expect: Page loads, hero section visible

  - name: Check CTA button
    action: find main call-to-action button
    expect: "Start Quiz" or similar CTA button visible

  - name: Click CTA
    action: click the primary CTA button
    expect: Navigates to /quiz page

  - name: Check mobile nav
    action: resize to 375px width
    expect: Hamburger menu visible, content reflows
```

**Step 3: Commit**

```bash
git add tests/ui/
git commit -m "feat: add user story definitions for critical UI flows"
```

---

### Task 3: Create Claude Code UI Testing Command

**Files:**
- Create: `.claude/commands/ui-test.md`

**Step 1: Create the UI test orchestration command**

Create `.claude/commands/ui-test.md`:

```markdown
# UI Test Command

Run agentic UI testing against user stories using Playwright.

## Usage

```
/ui-test                    # Run all stories
/ui-test quiz-flow          # Run specific story
/ui-test --headed           # Run with visible browser
```

## Prerequisites

- Frontend running: `cd frontend && npm run dev` (port 5174)
- Backend running: `cd backend && uvicorn src.main:app --port 8383`
- Playwright installed: `cd backend && playwright install chromium`

## Workflow

### 1. Discover Stories

Read all YAML files in `tests/ui/stories/`. Each file is one user story with steps.

### 2. Setup

Create output directory for this run:
```
tests/ui/screenshots/YYYY-MM-DD-HHmmss/
```

### 3. Spawn Parallel Agents

For each story file, spawn a sub-agent using the Task tool with these instructions:

```
You are a UI testing agent. Use the Playwright CLI (npx playwright) or the
PlaywrightBrowserSkill to test a user story.

STORY: {paste the full YAML content}

WORKFLOW:
1. Read the story steps carefully
2. For each step:
   a. Execute the action described
   b. Take a screenshot: tests/ui/screenshots/{run_dir}/{story_name}-step-{N}.png
   c. Validate the expected outcome
   d. Record PASS or FAIL with reasoning
3. After all steps, close the browser

IMPORTANT:
- Use headless mode unless --headed was specified
- Take a screenshot BEFORE and AFTER each action
- If a step fails, continue with remaining steps (don't abort)
- Return a structured result with pass/fail for each step

OUTPUT FORMAT:
{
  "story": "story-name",
  "passed": true/false,
  "steps": [
    {"name": "step name", "status": "pass|fail", "screenshot": "path", "notes": "..."}
  ],
  "duration_seconds": N
}
```

### 4. Collect Results

After all agents complete, aggregate results:

```
UI Test Summary — YYYY-MM-DD HH:mm
═══════════════════════════════════

  ✓ quiz-flow          5/5 steps passed    12.3s
  ✓ landing-page       4/4 steps passed     6.1s
  ✗ report-viewer      4/6 steps passed     8.7s
      Step 4 FAIL: Chart did not render (screenshot: ...)
      Step 6 FAIL: Horizontal scroll detected on mobile
  ✓ admin-dashboard    3/3 steps passed     5.2s

Total: 3/4 stories passed, 16/18 steps passed
Screenshots: tests/ui/screenshots/2026-02-21-143022/
```

### 5. Cleanup

Close all browser instances.

## Adding New Stories

Create a new YAML file in `tests/ui/stories/` following this format:

```yaml
name: Story Name
description: What this tests
url: http://localhost:5174/path
priority: critical|high|medium
requires:           # optional
  key: "description of prerequisite"

steps:
  - name: Step description
    action: what to do
    expect: what should happen
```

Stories are auto-discovered — no registration needed.
```

**Step 2: Commit**

```bash
git add .claude/commands/ui-test.md
git commit -m "feat: add /ui-test command for agentic UI testing"
```

---

### Task 4: Add UI Test Target to Makefile

**Files:**
- Modify: `Makefile`

**Step 1: Add ui-test and ui-test-headed targets**

Add after the existing `test-frontend` target:

```makefile
ui-test:
	@echo "Run: /ui-test in Claude Code to execute agentic UI tests"
	@echo "Or manually: cd backend && python -m pytest tests/ui/ -v"

ui-test-headed:
	@echo "Run: /ui-test --headed in Claude Code"
```

**Step 2: Commit**

```bash
git add Makefile
git commit -m "feat: add ui-test targets to Makefile"
```

---

## Phase 3: Enhanced Site Analysis (Production Skill)

> **Risk: low** — extends existing scraper, falls back to httpx for simple sites

### Task 5: Create Enhanced Scraper That Uses Playwright

**Files:**
- Create: `backend/src/skills/browser/enhanced_scraper.py`
- Create: `backend/tests/skills/browser/test_enhanced_scraper.py`

**Step 1: Write failing test**

Create `backend/tests/skills/browser/test_enhanced_scraper.py`:

```python
"""Tests for enhanced scraper skill (Playwright-powered)."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.skills.browser.enhanced_scraper import EnhancedScraperSkill
from src.skills.base import SkillContext


class TestEnhancedScraperSkill:
    """Test the enhanced Playwright-based scraper."""

    def test_skill_metadata(self):
        """Skill has correct metadata."""
        skill = EnhancedScraperSkill()
        assert skill.name == "enhanced-scraper"

    @pytest.mark.asyncio
    async def test_scrapes_js_rendered_content(self):
        """Detects tech from JS-rendered pages that httpx would miss."""
        skill = EnhancedScraperSkill()
        context = SkillContext(
            industry="ecommerce",
            metadata={"url": "https://js-store.example.com"}
        )

        mock_page = AsyncMock()
        mock_page.title = AsyncMock(return_value="JS Fashion Store")
        mock_page.url = "https://js-store.example.com"
        mock_page.content = AsyncMock(return_value="""
            <html>
            <head><title>JS Fashion Store</title>
            <meta name="description" content="Premium fashion"></head>
            <body>
                <h1>Welcome to JS Fashion Store</h1>
                <script src="https://cdn.shopify.com/theme.js"></script>
                <script src="https://static.klaviyo.com/onsite/js/klaviyo.js"></script>
                <script src="https://widget.intercom.io/widget/abc"></script>
                <div data-recharge-checkout="true"></div>
            </body></html>
        """)
        mock_page.eval_on_selector_all = AsyncMock(return_value=["Welcome to JS Fashion Store"])
        mock_page.evaluate = AsyncMock(return_value="Premium fashion")
        mock_page.close = AsyncMock()

        mock_browser_skill = AsyncMock()
        with patch.object(skill, '_get_browser_skill') as mock_get:
            mock_get.return_value._get_page = AsyncMock(return_value=mock_page)
            with patch.object(skill, '_scrape_with_playwright', return_value={
                "url": "https://js-store.example.com",
                "title": "JS Fashion Store",
                "description": "Premium fashion",
                "headings": ["Welcome to JS Fashion Store"],
                "visible_tech": ["shopify", "klaviyo", "intercom", "recharge"],
                "link_count": 42,
            }):
                result = await skill.run(context)

        assert result.success is True
        assert "shopify" in result.data["visible_tech"]
        assert "klaviyo" in result.data["visible_tech"]
        assert len(result.data["visible_tech"]) >= 2

    @pytest.mark.asyncio
    async def test_falls_back_to_httpx_on_playwright_failure(self):
        """Falls back to httpx scraper if Playwright fails."""
        skill = EnhancedScraperSkill()
        context = SkillContext(
            industry="ecommerce",
            metadata={"url": "https://simple-site.example.com"}
        )

        with patch.object(skill, '_scrape_with_playwright', side_effect=Exception("Playwright failed")):
            with patch('src.skills.browser.enhanced_scraper.scrape_ecommerce_site', return_value={
                "success": True,
                "title": "Simple Site",
                "description": "A simple store",
                "headings": ["Welcome"],
                "visible_tech": ["shopify"],
                "url": "https://simple-site.example.com",
            }) as mock_httpx:
                result = await skill.run(context)

        assert result.success is True
        assert result.data["scrape_method"] == "httpx_fallback"
        mock_httpx.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_scrape_method_in_result(self):
        """Result includes which method was used (playwright vs httpx)."""
        skill = EnhancedScraperSkill()
        context = SkillContext(
            industry="ecommerce",
            metadata={"url": "https://store.example.com"}
        )

        with patch.object(skill, '_scrape_with_playwright', return_value={
            "url": "https://store.example.com",
            "title": "Store",
            "description": "",
            "headings": [],
            "visible_tech": ["shopify"],
            "link_count": 10,
        }):
            result = await skill.run(context)

        assert result.success is True
        assert result.data["scrape_method"] == "playwright"
```

Run to verify failure:
```bash
cd backend && python -m pytest tests/skills/browser/test_enhanced_scraper.py -v
```

**Step 2: Implement the enhanced scraper skill**

Create `backend/src/skills/browser/enhanced_scraper.py`:

```python
"""
Enhanced Scraper Skill

Scrapes e-commerce sites using Playwright for full JS rendering.
Falls back to httpx if Playwright fails (graceful degradation).

This produces richer input data for CRB reports than the httpx-only scraper:
- Detects client-side-only technologies (Intercom widgets, Recharge, etc.)
- Captures dynamically loaded content
- Takes visual screenshots for report context
"""

import logging
from typing import Any, Dict, Optional

from src.skills.base import BaseSkill, SkillContext, SkillError
from src.cli.scraper import scrape_ecommerce_site  # httpx fallback

logger = logging.getLogger(__name__)


class EnhancedScraperSkill(BaseSkill[Dict[str, Any]]):
    """
    Enhanced site scraper with Playwright + httpx fallback.

    Input (via context.metadata):
    - "url": Target URL (required)
    - "screenshot_path": Save screenshot (optional)
    - "timeout_ms": Timeout in ms (default: 30000)

    Output:
    {
        "url": str,
        "title": str,
        "description": str,
        "headings": list[str],
        "visible_tech": list[str],
        "link_count": int,
        "scrape_method": "playwright" | "httpx_fallback",
        "screenshot_path": str | None,
    }
    """

    name = "enhanced-scraper"
    description = "Scrape e-commerce sites with JS rendering and httpx fallback"
    version = "1.0.0"
    requires_llm = False

    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        """Scrape with Playwright, falling back to httpx."""
        url = context.metadata.get("url")
        if not url:
            raise SkillError(self.name, "Missing 'url' in metadata", recoverable=False)

        # Try Playwright first
        try:
            result = await self._scrape_with_playwright(context)
            result["scrape_method"] = "playwright"
            return result
        except Exception as e:
            logger.warning(f"Playwright scrape failed for {url}, falling back to httpx: {e}")

        # Fallback to httpx
        httpx_result = await scrape_ecommerce_site(url)
        if httpx_result.get("success"):
            return {
                "url": httpx_result.get("url", url),
                "title": httpx_result.get("title", ""),
                "description": httpx_result.get("description", ""),
                "headings": httpx_result.get("headings", []),
                "visible_tech": httpx_result.get("visible_tech", []),
                "link_count": 0,
                "scrape_method": "httpx_fallback",
                "screenshot_path": None,
            }

        raise SkillError(
            self.name,
            f"Both Playwright and httpx failed for {url}: {httpx_result.get('error', 'unknown')}",
            recoverable=True,
        )

    async def _scrape_with_playwright(self, context: SkillContext) -> Dict[str, Any]:
        """Scrape using the PlaywrightBrowserSkill."""
        from src.skills.browser.playwright_browser import PlaywrightBrowserSkill

        browser_skill = PlaywrightBrowserSkill()
        scrape_context = SkillContext(
            industry=context.industry,
            metadata={
                "action": "scrape",
                "url": context.metadata["url"],
                "screenshot_path": context.metadata.get("screenshot_path"),
                "timeout_ms": context.metadata.get("timeout_ms", 30000),
            }
        )

        result = await browser_skill.run(scrape_context)
        if not result.success:
            raise Exception(f"PlaywrightBrowserSkill failed: {result.warnings}")

        return result.data

    def _get_browser_skill(self):
        """Get browser skill instance (for testing/mocking)."""
        from src.skills.browser.playwright_browser import PlaywrightBrowserSkill
        return PlaywrightBrowserSkill()
```

Update `backend/src/skills/browser/__init__.py`:

```python
"""Browser automation skills using Playwright."""
from .playwright_browser import PlaywrightBrowserSkill
from .enhanced_scraper import EnhancedScraperSkill

__all__ = ["PlaywrightBrowserSkill", "EnhancedScraperSkill"]
```

**Step 3: Run tests**

```bash
cd backend && python -m pytest tests/skills/browser/ -v
```

Expected: All tests pass.

**Step 4: Commit**

```bash
git add backend/src/skills/browser/ backend/tests/skills/browser/
git commit -m "feat: add enhanced scraper skill with Playwright + httpx fallback"
```

---

### Task 6: Integrate Enhanced Scraper into CLI Pipeline

**Files:**
- Modify: `backend/src/cli/generate_report.py`

**Step 1: Read the current generate_report.py**

Read `backend/src/cli/generate_report.py` to understand the current scraping integration point.

**Step 2: Add --playwright flag to CLI**

Add a `--playwright` flag to the argument parser that switches from the httpx scraper to the enhanced scraper. This is opt-in so existing behavior doesn't change.

In the argparse section, add:
```python
parser.add_argument("--playwright", action="store_true",
                    help="Use Playwright for JS-rendered scraping (more thorough but slower)")
```

In the `generate_single_report` function, modify the scraping step:

```python
# Step 1: Scrape website (optional)
scraped_data = None
if scrape and seed.get("website"):
    print("  Scraping website...", end="", flush=True)
    if use_playwright:
        from src.skills.browser.enhanced_scraper import EnhancedScraperSkill
        from src.skills.base import SkillContext
        scraper = EnhancedScraperSkill()
        scrape_context = SkillContext(
            industry="ecommerce",
            metadata={"url": seed["website"]}
        )
        result = await scraper.run(scrape_context)
        if result.success:
            scraped_data = result.data
            tech = scraped_data.get("visible_tech", [])
            method = scraped_data.get("scrape_method", "unknown")
            print(f" done via {method} ({len(tech)} technologies detected)")
        else:
            print(f" failed, using seed data only")
            scraped_data = None
    else:
        scraped_data = await scrape_ecommerce_site(seed["website"])
        if scraped_data.get("success"):
            tech = scraped_data.get("visible_tech", [])
            print(f" done ({len(tech)} technologies detected)")
        else:
            print(f" failed ({scraped_data.get('error', 'unknown')}), using seed data only")
            scraped_data = None
```

Pass `use_playwright=args.playwright` through the call chain.

**Step 3: Verify**

```bash
cd backend && python -m src.cli.generate_report --help
```

Expected: `--playwright` flag visible in help.

**Step 4: Commit**

```bash
git add backend/src/cli/generate_report.py
git commit -m "feat: add --playwright flag to CLI for enhanced JS-rendered scraping"
```

---

## Phase 4: Enhanced Vendor Research (Agent Layer)

> **Risk: medium** — touches existing research pipeline, needs careful integration

### Task 7: Create Vendor Site Scraper Skill

**Files:**
- Create: `backend/src/skills/browser/vendor_scraper.py`
- Create: `backend/tests/skills/browser/test_vendor_scraper.py`

**Step 1: Read existing vendor research patterns**

Read `backend/src/agents/research/sources/vendor_site.py` to understand the current `scrape_vendor_pricing` function. Read `backend/src/agents/research/discover.py` to understand how vendors are discovered.

**Step 2: Write failing test**

Create `backend/tests/skills/browser/test_vendor_scraper.py`:

```python
"""Tests for vendor site scraper skill."""
import pytest
from unittest.mock import AsyncMock, patch

from src.skills.browser.vendor_scraper import VendorSiteScraperSkill
from src.skills.base import SkillContext


class TestVendorSiteScraperSkill:
    """Test Playwright-based vendor site scraping."""

    def test_skill_metadata(self):
        skill = VendorSiteScraperSkill()
        assert skill.name == "vendor-site-scraper"
        assert skill.requires_llm is True  # Uses Claude to extract pricing

    @pytest.mark.asyncio
    async def test_extracts_pricing_from_js_page(self):
        """Extracts pricing tiers from JS-rendered pricing page."""
        skill = VendorSiteScraperSkill()
        context = SkillContext(
            industry="ecommerce",
            metadata={
                "vendor_url": "https://vendor.example.com",
                "vendor_name": "TestVendor",
                "category": "customer_service",
            }
        )

        mock_page_content = """
        <html><body>
            <h1>Pricing</h1>
            <div class="plan">
                <h3>Starter</h3><span class="price">$29/mo</span>
            </div>
            <div class="plan">
                <h3>Pro</h3><span class="price">$79/mo</span>
            </div>
            <div class="plan">
                <h3>Enterprise</h3><span class="price">Custom</span>
            </div>
        </body></html>
        """

        with patch.object(skill, '_navigate_to_pricing', return_value=mock_page_content):
            with patch.object(skill, 'call_llm_json', return_value={
                "tiers": [
                    {"name": "Starter", "price_monthly": 29, "currency": "USD"},
                    {"name": "Pro", "price_monthly": 79, "currency": "USD"},
                    {"name": "Enterprise", "price_monthly": None, "currency": "USD", "custom": True},
                ],
                "has_free_tier": False,
                "pricing_model": "per_seat",
            }):
                result = await skill.run(context)

        assert result.success is True
        assert len(result.data["tiers"]) == 3
        assert result.data["tiers"][0]["price_monthly"] == 29

    @pytest.mark.asyncio
    async def test_finds_pricing_page_from_homepage(self):
        """Navigates from homepage to pricing page."""
        skill = VendorSiteScraperSkill()
        # Verify the pricing URL patterns
        assert skill._guess_pricing_urls("https://vendor.com") == [
            "https://vendor.com/pricing",
            "https://vendor.com/pricing/",
            "https://vendor.com/plans",
            "https://vendor.com/plans/",
        ]
```

**Step 3: Implement vendor scraper skill**

Create `backend/src/skills/browser/vendor_scraper.py` that:
- Takes a vendor URL and category
- Navigates to the vendor's pricing page (tries `/pricing`, `/plans`, etc.)
- Extracts the rendered HTML
- Uses Claude (Haiku) to extract structured pricing data
- Returns tiers, features, pricing model

This is an `LLMSkill` since it uses Claude for extraction.

**Step 4: Run tests, commit**

```bash
cd backend && python -m pytest tests/skills/browser/test_vendor_scraper.py -v
git add backend/src/skills/browser/vendor_scraper.py backend/tests/skills/browser/
git commit -m "feat: add vendor site scraper skill with Playwright pricing extraction"
```

---

### Task 8: Wire Vendor Scraper into Research Agent

**Files:**
- Modify: `backend/src/agents/research/sources/vendor_site.py`

**Step 1: Read the current vendor_site.py**

Read to understand the current `scrape_vendor_pricing` function.

**Step 2: Add Playwright-enhanced scraping option**

Add an optional parameter to `scrape_vendor_pricing` that uses the `VendorSiteScraperSkill` when available. Fall back to existing httpx approach when Playwright is not available or fails.

The key change: after the existing httpx scraping attempt, if it failed to find pricing data, try the Playwright skill as a second attempt.

**Step 3: Run existing vendor research tests**

```bash
cd backend && python -m pytest tests/ -k "vendor" -v
```

Verify no existing tests break.

**Step 4: Commit**

```bash
git add backend/src/agents/research/sources/vendor_site.py
git commit -m "feat: enhance vendor pricing scraper with Playwright fallback"
```

---

## Phase 5: Orchestration Layer (Commands + Task Runner)

> **Risk: medium** — architectural change, but components are battle-tested by now

### Task 9: Create Research Command

**Files:**
- Create: `.claude/commands/research-vendor.md`

**Step 1: Create vendor research command**

Create `.claude/commands/research-vendor.md` that:
- Takes a vendor category and optional industry
- Spawns the research agent with Playwright-enhanced scraping
- Reports discovered vendors with pricing data
- Saves results to a structured output

**Step 2: Commit**

```bash
git add .claude/commands/research-vendor.md
git commit -m "feat: add /research-vendor command for Playwright-enhanced vendor discovery"
```

---

### Task 10: Expand Makefile into Full Task Runner

**Files:**
- Modify: `Makefile`

**Step 1: Add comprehensive targets**

Add these targets to the Makefile:

```makefile
# Browser automation
playwright-install:
	cd backend && playwright install chromium

# UI testing
ui-test:
	@echo "Starting agentic UI tests..."
	@echo "Use /ui-test in Claude Code for full agentic testing"
	@echo "Or: cd backend && python -m pytest tests/ui/ -v"

# Enhanced report generation
generate-report-playwright:
	cd backend && python -m src.cli.generate_report --playwright $(ARGS)

# Vendor research
research-vendor:
	@echo "Use /research-vendor in Claude Code"
	@echo "Category: $(CATEGORY), Industry: $(INDUSTRY)"

# Full test suite (including UI)
test-all: test ui-test
```

**Step 2: Commit**

```bash
git add Makefile
git commit -m "feat: expand Makefile with browser automation and UI testing targets"
```

---

### Task 11: Update CLAUDE.md with Browser Capabilities

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Add browser section to CLAUDE.md**

Add a "Browser Automation" section documenting:
- Available browser skills (playwright-browser, enhanced-scraper, vendor-site-scraper)
- The `/ui-test` command and how to add stories
- The `--playwright` CLI flag
- Makefile targets

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add browser automation section to CLAUDE.md"
```

---

## Summary

| Phase | Task | Description | New Files | Risk |
|-------|------|-------------|-----------|------|
| 1 | 1 | Playwright browser skill | 4 py + 1 test | Zero |
| 2 | 2 | User story definitions | 5 yaml + 1 gitkeep | Zero |
| 2 | 3 | `/ui-test` command | 1 md | Zero |
| 2 | 4 | Makefile UI targets | Modify 1 | Zero |
| 3 | 5 | Enhanced scraper skill | 2 py + 1 test | Low |
| 3 | 6 | CLI Playwright integration | Modify 1 py | Low |
| 4 | 7 | Vendor site scraper skill | 2 py + 1 test | Medium |
| 4 | 8 | Research agent integration | Modify 1 py | Medium |
| 5 | 9 | Research command | 1 md | Low |
| 5 | 10 | Full task runner | Modify 1 | Low |
| 5 | 11 | Documentation | Modify 1 | Zero |

**Total:** ~800 lines new code, ~15 new files, 3 modified files, 0 breaking changes to existing code.

**Each phase is independently deployable.** Phase 1 alone gives you browser capabilities. Phase 2 gives you UI testing. You can stop after any phase and still have a working, useful system.

## CRB Context
- Affected user journey stage: All (Quiz, Payment, Report, Dashboard — via UI testing)
- Industries impacted: All (enhanced scraping benefits all reports)
- Reference docs to load during execution: `.claude/reference/skills.md`, `.claude/reference/testing.md`

## Rollback Plan
If anything fails, revert by:
- Phase 1: `pip uninstall playwright` + delete `backend/src/skills/browser/`
- Phase 2: Delete `tests/ui/` + `.claude/commands/ui-test.md`
- Phase 3-4: Revert modified files (scraper fallback ensures no breakage)
- Phase 5: Revert Makefile + CLAUDE.md changes
