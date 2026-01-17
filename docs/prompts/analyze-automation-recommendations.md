# Automation & Build-vs-Buy Analysis Prompt

## Purpose
Audit how well the CRB system explains automation platforms, AI tools, and provides realistic cost/effort guidance for different implementation paths.

---

## Analysis Areas

### 1. Automation Platform Coverage

**Question:** Does the system recommend and explain workflow automation platforms?

Check for coverage of:
- **iPaaS (Integration Platforms):** Make, n8n, Zapier, Tray.io, Workato
- **AI Agent Platforms:** Lindy, Relevance AI, Beam AI, AgentGPT
- **Scraping/Data Tools:** Apify, Firecrawl, Browserbase, ScrapingBee
- **AI APIs:** OpenAI, Anthropic Claude, Google Gemini
- **Low-Code Builders:** Retool, Bubble, Glide, Softr
- **Database/Backend:** Supabase, Firebase, Airtable, Notion

For each platform category:
- Is it in the vendor database?
- Are use cases explained?
- Is pricing accurate?
- Are integration capabilities documented?

### 2. AI & Automation Explanation Quality

**Question:** Does the system explain WHAT, WHY, and HOW for automation tools?

Check if reports include:
- **What it does:** Clear explanation of capabilities
- **Why it matters:** Business value, time savings, cost reduction
- **How to implement:** Step-by-step or at least high-level approach
- **Real examples:** Specific automations possible for their industry
- **Limitations:** What it can't do, when it's overkill

### 3. Build vs Buy vs Hire Framework

**Question:** Does the system help users decide between:

| Option | Description | When Appropriate |
|--------|-------------|------------------|
| **Buy SaaS** | Purchase existing software | Standard needs, no customization required |
| **Build with No-Code** | Use Make/n8n/Zapier | Custom workflows, moderate complexity |
| **Build with AI Tools** | Cursor, Claude Code, v0 | Technical team, unique requirements |
| **Hire Agency** | Outsource to experts | Complex needs, no internal capability |
| **Hire Developer** | Full-time or contract | Ongoing needs, strategic capability |

For each finding, does the report consider:
- Team's technical capability?
- Time-to-value requirements?
- Budget constraints?
- Ongoing maintenance needs?
- Customization requirements?

### 4. Cost Realism

**Question:** Are implementation costs realistic?

Check for:
- **Agency costs:** Typically €2,000-20,000+ for automation projects
- **Freelancer costs:** €50-150/hour for automation specialists
- **Learning curve:** 20-100+ hours to become proficient
- **Platform costs:** Monthly fees for Make/n8n/Zapier
- **Hidden costs:** Maintenance, updates, API fees, overages

### 5. Capability Assessment

**Question:** Does the system assess the client's ability to implement?

Should capture:
- Do they have technical staff?
- What's their comfort with no-code tools?
- Have they used automation before?
- What's their timeline urgency?
- What's their budget for implementation?

---

## Verification Steps

### Step 1: Check Vendor Database for Automation Platforms

```python
# Check if automation platforms exist in vendor database
automation_platforms = [
    'make', 'n8n', 'zapier', 'lindy', 'relevance-ai',
    'apify', 'firecrawl', 'retool', 'bubble', 'supabase',
    'cursor', 'airtable', 'notion'
]
```

### Step 2: Check Knowledge Base for Automation Guidance

Search for:
- Automation workflow examples
- Integration patterns
- Build vs buy guidance
- Agency cost benchmarks
- DIY learning resources

### Step 3: Check Report Generation Skills

Look at:
- `three_options.py` - Does it include automation/DIY options?
- `finding_generation.py` - Does it explain HOW to solve, not just WHAT?
- `verdict.py` - Does it consider implementation capability?

### Step 4: Check Quiz/Interview Questions

Does the intake capture:
- Technical capability of team?
- Previous automation experience?
- Budget for implementation vs ongoing?
- Timeline urgency?
- Preference for DIY vs outsource?

---

## Expected Gaps to Find

1. **Automation platforms underrepresented** in vendor database
2. **Reports recommend software but not automation workflows**
3. **No build-vs-buy framework** in recommendations
4. **Implementation costs are generic**, not realistic
5. **Quiz doesn't capture** technical capability or preferences
6. **Three options** are always software tiers, not implementation approaches

---

## Improvement Recommendations (Expected)

### If automation platforms missing:
- Add Make, n8n, Zapier, Lindy to vendor database
- Create "automation" category with detailed use cases
- Add API openness scores for integration potential

### If build-vs-buy missing:
- Add new skill: `implementation_path_advisor.py`
- Capture technical capability in quiz
- Generate implementation path recommendation per finding

### If costs unrealistic:
- Research actual agency rates by region
- Add "implementation cost" field to findings
- Include DIY time estimates

### If explanation quality low:
- Enhance finding templates with HOW section
- Add automation workflow examples to knowledge base
- Include step-by-step implementation guides

---

## Run This Analysis

Execute the following to audit current state:

```bash
# 1. Check vendor database for automation platforms
# 2. Search knowledge base for automation guidance
# 3. Review report generation for implementation advice
# 4. Check quiz for capability assessment questions
# 5. Generate sample report and evaluate automation coverage
```
