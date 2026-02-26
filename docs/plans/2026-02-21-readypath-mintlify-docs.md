# ReadyPath Mintlify Docs — Handoff Document

> **Status**: Docs scaffolded, locally verified, ready for deployment
> **Date**: 2026-02-21
> **Location**: `docs/mintlify/`

---

## What's Done

### Docs Structure (20 pages, 3 tabs)

All pages created with AI-discoverable frontmatter (title, description, keywords):

```
docs/mintlify/
├── docs.json                           # Config: theme, nav, SEO, OpenAPI
├── openapi.json                        # Exported from FastAPI (182 endpoints)
├── favicon.svg                         # Placeholder "R" icon
├── logo/light.svg                      # Placeholder ReadyPath logo (light)
├── logo/dark.svg                       # Placeholder ReadyPath logo (dark)
│
├── introduction.mdx                    # Product landing page
├── quickstart.mdx                      # Get started in 4 steps
├── how-it-works.mdx                    # 5-phase AI pipeline explained
│
├── framework/                          # CRB Framework tab
│   ├── overview.mdx                    # Framework intro, NET score, tiers
│   ├── costs.mdx                       # 6 cost dimensions
│   ├── risks.mdx                       # 4 risk categories
│   ├── benefits.mdx                    # 4 benefit categories
│   ├── scoring.mdx                     # AI Readiness Score, NET Score
│   ├── three-options.mdx               # Off-the-Shelf / Best-in-Class / Custom
│   └── value-calculation.mdx           # Value Saved + Value Created formulas
│
├── guides/                             # User guides
│   ├── quiz-flow.mdx                   # Adaptive quiz explained
│   ├── workshop.mdx                    # 90-minute workshop guide
│   ├── reading-your-report.mdx         # How to interpret your report
│   └── connect-vs-replace.mdx          # Integration vs migration guidance
│
├── industries/                         # Industry-specific pages
│   ├── professional-services.mdx       # Law, accounting, consulting
│   ├── dental-practices.mdx            # Dental technology decisions
│   └── ecommerce.mdx                   # E-commerce platform decisions
│
├── api-reference/                      # API Reference tab
│   ├── overview.mdx                    # Base URL, response format, SDKs
│   ├── authentication.mdx              # API keys, JWT auth
│   ├── quiz.mdx                        # Quiz session endpoints
│   ├── reports.mdx                     # Report generation endpoints
│   └── vendors.mdx                     # Vendor search/compare endpoints
│
└── snippets/
    └── crb-formula.mdx                 # Reusable NET Score formula
```

### Naming Convention

- **ReadyPath** = product name (used everywhere the product is referenced)
- **CRB** = framework/methodology only (CRB analysis, CRB framework, CRB report)
- **readypath.ai** = domain (quiz links, API base URL, dashboard)
- Zero instances of "CRB Analyser" remain in docs

### OpenAPI Spec

- Exported from FastAPI: `docs/mintlify/openapi.json` (182 endpoints)
- Title updated to "ReadyPath API"
- Wired into `docs.json` via `"api": { "openapi": "openapi.json" }`
- Mintlify will auto-generate interactive API playground from this

### Local Verification

All 20 pages return HTTP 200 via `mint dev` on localhost:3000.

---

## What's Left To Do

### 1. Create GitHub Repo for Docs

The docs can live in:
- **Option A**: Separate `amplify-logic/docs` repo (cleaner, Mintlify's recommendation)
- **Option B**: Subdirectory in the main repo (simpler, one repo to manage)

**If separate repo:**
```bash
cd docs/mintlify
git init
git add .
git commit -m "feat: initial ReadyPath documentation site"
gh repo create amplify-logic/docs --public --source=. --push
```

**If subdirectory**: Just commit `docs/mintlify/` to the main repo. Configure Mintlify to use `docs/mintlify` as the content directory.

### 2. Connect Mintlify Dashboard

1. Go to [dashboard.mintlify.com](https://dashboard.mintlify.com)
2. Sign up / sign in
3. Connect the GitHub repo containing the docs
4. Set the content directory (if using subdirectory: `docs/mintlify`)
5. Mintlify will auto-deploy on every push

### 3. Set Custom Domain

In Mintlify dashboard → Settings → Custom Domain:
- Set `docs.readypath.ai`
- Add CNAME record in your DNS: `docs.readypath.ai → cname.mintlify.com`
- Wait for SSL provisioning (usually < 5 minutes)

### 4. Replace Placeholder Logos

Current logos are simple SVG text placeholders. Replace with real brand assets:
- `docs/mintlify/logo/light.svg` — for light mode
- `docs/mintlify/logo/dark.svg` — for dark mode
- `docs/mintlify/favicon.svg` — browser tab icon

Recommended: SVG format, max 160x40px for logos, 32x32px for favicon.

### 5. Review OpenAPI Spec for Public Exposure

The exported `openapi.json` contains **all 182 endpoints** including admin routes. Before deploying:

**Filter to public endpoints only:**
- `/api/quiz/*` — quiz session management
- `/api/reports/*` — report retrieval
- `/api/vendors/*` — vendor search
- `/api/auth/*` — authentication
- `/api/health` — health check

**Remove internal/admin endpoints:**
- `/api/admin/*` — admin dashboard routes
- `/api/admin/knowledge/*` — knowledge base management
- `/api/admin/insights/*` — insight management
- Any other internal routes

You can either:
- Manually edit `openapi.json` to remove admin paths
- Create a script to filter paths (recommended for re-exports)
- Add `--exclude` patterns if FastAPI supports it

### 6. Verify AI Discoverability (Post-Deploy)

After deploying to production:

```bash
# Check llms.txt is generated
curl https://docs.readypath.ai/llms.txt

# Check llms-full.txt is generated
curl https://docs.readypath.ai/llms-full.txt

# Check content negotiation works (Markdown for AI agents)
curl -H "Accept: text/markdown" https://docs.readypath.ai/introduction

# Check sitemap
curl https://docs.readypath.ai/sitemap.xml
```

All four should return content. The `llms.txt` and `llms-full.txt` are auto-generated by Mintlify from your page frontmatter.

### 7. Optional Enhancements

**Analytics** — Add to `docs.json`:
```json
"integrations": {
  "posthog": { "apiKey": "phc_xxx" }
}
```

**Search customisation:**
```json
"search": {
  "prompt": "Search ReadyPath docs..."
}
```

**Changelog page** — Add a `changelog/` section for product updates.

**Blog integration** — If readypath.ai has a blog, link it in the navbar.

---

## Quick Reference

| Item | Value |
|------|-------|
| Docs location | `docs/mintlify/` |
| Config file | `docs/mintlify/docs.json` |
| OpenAPI spec | `docs/mintlify/openapi.json` (182 endpoints, needs filtering) |
| Local preview | `cd docs/mintlify && mint dev` → localhost:3000 |
| CLI install | `npm i -g mint` |
| Target domain | `docs.readypath.ai` |
| Product name | ReadyPath (never "CRB Analyser") |
| Framework name | CRB (Cost-Risk-Benefit) |
