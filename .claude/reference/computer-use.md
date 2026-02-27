# Computer Use & Claude Cowork Reference

> Load this when working on browser automation, research pipelines, or when a task would benefit from desktop-level automation.

---

## When to Suggest Cowork

During a Claude Code session, if you encounter a task that requires **visual browser interaction, human-like navigation, or desktop app control**, suggest the user run it in Claude Cowork instead.

### Tasks Better Suited for Cowork

| Task | Why Cowork | Suggested Prompt |
|------|-----------|-----------------|
| **Vendor pricing research** | Sites with CAPTCHAs, dynamic pricing, login walls | "Open [vendor].com/pricing and extract all tier names, prices, and feature lists into a JSON file" |
| **Competitor positioning analysis** | Need to read landing pages, understand messaging | "Visit these 10 competitor websites and create a comparison matrix of their positioning, pricing, and target audience" |
| **Client stack verification** | Browse client's public tools, check integrations | "Go to [client-site].com and identify all visible software tools, integrations, and tech stack indicators" |
| **Ad-hoc market research** | Browse industry reports, extract data points | "Search for [industry] AI adoption benchmarks from 2025-2026 and compile findings into a spreadsheet" |
| **Report QA walkthrough** | Open report as a reader, check formatting and flow | "Open this report PDF and review it as if you're a business owner seeing it for the first time. Flag anything confusing" |
| **Meta Ad Library research** | Browse ad libraries, extract creative strategies | "Search Meta Ad Library for [industry] businesses and document the top 10 ad strategies being used" |
| **G2/Capterra review scraping** | Navigate review sites with JS-heavy UIs | "Go to G2.com and extract the top 5 reviews for [vendor], including ratings and key themes" |

### How to Suggest It

When you identify a Cowork-suitable task, output something like:

```
This would be faster in Claude Cowork. Run this:

> "Go to [URL], extract [specific data], and save it to [file path]"

Cowork will handle the browser navigation, CAPTCHAs, and dynamic content
that our Playwright scripts can't easily manage.
```

### When NOT to Suggest Cowork

- **Programmatic scraping** that our Playwright skills already handle well
- **API-based data fetching** — use the API directly
- **Tasks that need to run in CI/CD** — Cowork requires a desktop
- **High-volume automated scraping** — use our existing scraper pipeline
- **Anything requiring Claude Code tools** (file editing, git, tests) — stay in CC

---

## Current Browser Automation Stack (Use First)

Before suggesting Cowork, check if our existing tools can handle it:

| Tool | Best For | Location |
|------|----------|----------|
| `PlaywrightBrowserSkill` | JS-rendered page scraping, tech detection, screenshots | `backend/src/skills/browser/playwright_browser.py` |
| `EnhancedScraperSkill` | Site scraping with Playwright → httpx fallback | `backend/src/skills/browser/enhanced_scraper.py` |
| `VendorSiteScraperSkill` | Vendor pricing extraction (Playwright + Claude) | `backend/src/skills/browser/vendor_scraper.py` |
| `playwright-cli` (Bowser) | UI testing, QA validation, screenshots | `.claude/skills/playwright-bowser/SKILL.md` |
| CLI scraper | Quick httpx-based site profiling | `backend/src/cli/scraper.py` |

**Decision tree:**

```
Can our Playwright skills handle it?
    YES → Use existing skills
    NO → Is it a one-off research task?
        YES → Suggest Cowork
        NO → Is it a repeatable pipeline task?
            YES → Consider Computer Use API integration
            NO → Suggest Cowork
```

---

## Computer Use API (Future Integration)

The Computer Use API allows programmatic desktop control via Claude's API. Currently in beta.

### Integration Opportunities

| Use Case | Priority | Value |
|----------|----------|-------|
| Autonomous vendor research pipeline | HIGH | Fresh pricing data without manual scraping scripts |
| Client tech stack verification | MEDIUM | Verify self-reported stack from public sources |
| Automated report QA | MEDIUM | AI reads report as user, flags issues |
| Industry benchmark gathering | LOW | Supplement knowledge base with fresh data |

### API Details

- Beta header required: `computer-use-2025-11-24`
- Available on Claude Opus 4.6, Sonnet 4.6, Opus 4.5
- Provides screenshot capture + mouse/keyboard control
- Runs in isolated VM for safety
- See: [Computer Use API Docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool)

### When to Build vs Use Cowork

| Factor | Build with API | Use Cowork |
|--------|---------------|------------|
| Runs in production pipeline | Yes | No |
| One-off research task | No | Yes |
| Needs to scale to 100+ sites | Yes | No |
| Needs human oversight | No | Yes |
| Requires logged-in sessions | No | Yes (has your sessions) |
| Must work in CI/CD | Yes | No |

---

## Claude Code ↔ Cowork Bridge (Upcoming)

There is no programmatic bridge between Claude Code and Cowork yet. [Feature request is open](https://github.com/anthropics/claude-code/issues/25791).

**When it ships, we should:**
1. Add a Claude Code command that delegates tasks to Cowork
2. Build a research pipeline that uses Cowork for sites our Playwright can't handle
3. Use Cowork for report QA as a post-generation step

**Until then:** Claude Code outputs clear Cowork instructions for the user to copy-paste into the Cowork interface.

---

## Setup

```bash
# Python skills (production scraping)
pip install playwright && playwright install chromium
# Or: make playwright-install

# Bowser QA (UI testing via CLI)
pnpm add -g @playwright/cli@latest && playwright-cli install
# Or: make playwright-cli-install
```

---

## Bowser QA (UI Testing)

Uses the [Bowser pattern](https://github.com/anthropics/bowser): Skill -> Agent -> Command -> Makefile.

| Component | File | Purpose |
|-----------|------|---------|
| Skill | `.claude/skills/playwright-bowser/SKILL.md` | `playwright-cli` usage reference |
| QA Agent | `.claude/agents/bowser-qa-agent.md` | Executes stories with PASS/FAIL reporting |
| Command | `.claude/commands/ui-test.md` | Orchestrates parallel QA agent runs |

**Workflow:** `/ui-test` discovers YAML stories in `tests/ui/stories/*.yaml`, spawns one QA agent per story in parallel, each agent uses `playwright-cli` to execute steps with screenshots, results are aggregated into a summary table.

Screenshots are saved to `screenshots/bowser-qa/<run_id>/` (gitignored).

### Commands

| Command | Purpose |
|---------|---------|
| `/ui-test` | Run Bowser QA agents against user stories |
| `/ui-test landing-page` | Run a specific story |
| `/research-vendor` | Discover and scrape vendor pricing |

### CLI Flag

```bash
# Use Playwright for JS-rendered scraping in report generation
cd backend && python -m src.cli.generate_report --playwright --url https://example.com
# Or: make generate-report-playwright ARGS="--url https://example.com"
```

### Makefile Targets

```bash
make playwright-install          # Install Chromium (Python skills)
make playwright-cli-install      # Install playwright-cli (Bowser QA)
make ui-test                     # Run UI tests via Bowser QA
make generate-report-playwright  # Generate report with Playwright scraping
make test-all                    # Full test suite including UI
```
