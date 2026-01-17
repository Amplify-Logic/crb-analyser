# Automation & Build-vs-Buy Gap Analysis
*Generated: 2026-01-14*

## Executive Summary

Your CRB system has **strong AI automation knowledge** in the knowledge base but **significant gaps in how it's surfaced to users**. The three main issues:

1. **Missing automation platform coverage** (17 of 24 key platforms not in vendor DB)
2. **No "hire agency" option** in recommendations (only SaaS or full DIY)
3. **Quiz doesn't capture implementation capability** (can't tailor recommendations)

---

## Part 1: What's Working Well

### Knowledge Base: Excellent

You have comprehensive AI automation content:

| File | Content Quality |
|------|-----------------|
| `ai_automation_reality_q4_2025.json` | **Exceptional** - real research data, failure rates, cost reality |
| `diy_resources.json` | **Excellent** - AI providers, dev tools, stacks, learning times |
| `patterns/ai_implementation_playbook.json` | **Good** - implementation guidance |

**Key insight from your data:** "95% of enterprise AI pilots fail to deliver ROI" - this is gold for helping clients set realistic expectations.

### Core iPaaS Coverage: Good

| Platform | In DB | Has Pricing | API Score |
|----------|-------|-------------|-----------|
| Make | ✅ | ✅ | 5 |
| n8n | ✅ | ✅ | 5 |
| Zapier | ✅ | ✅ | 5 |
| Tray.io | ✅ | ✅ | 5 |
| Workato | ✅ | ✅ | 5 |
| Supabase | ✅ | ✅ | 5 |
| Notion | ✅ | ✅ | 4 |

### Three Options Pattern: Exists

The `three_options.py` skill does generate:
- Off-the-shelf (SaaS)
- Best-in-class (Premium SaaS)
- Custom solution (DIY with AI tools)

It mentions Cursor, Claude API, Supabase in custom solutions.

---

## Part 2: Critical Gaps

### Gap 1: Missing Automation Platforms (17/24)

| Category | Missing Platforms |
|----------|-------------------|
| **AI Agent Platforms** | Lindy, Relevance AI, Beam AI |
| **Scraping/Data Tools** | Apify, Firecrawl, Browserbase |
| **Low-Code Builders** | Retool, Bubble, Glide, Softr |
| **Backend Services** | Firebase, Airtable |
| **AI Dev Tools** | Cursor, Claude Code, v0.dev, bolt.new, Replit |

**Impact:** Reports can't recommend these tools for automation workflows.

### Gap 2: No "Hire Agency" Implementation Path

Current options:
1. Buy SaaS (off-the-shelf)
2. Buy Premium SaaS (best-in-class)
3. DIY Custom Build

**Missing options:**
- **Hire automation agency** (€2K-20K projects)
- **Hire freelancer** (€50-150/hr)
- **Use Make/n8n to connect existing tools** (no-code middle ground)

**Impact:** Users who can't DIY and can't afford premium SaaS have no path forward.

### Gap 3: Quiz Doesn't Capture Implementation Capability

The quiz captures:
- ✅ Budget range
- ✅ AI/automation experience (some industries)
- ❌ **Technical capability of team**
- ❌ **Implementation urgency**
- ❌ **DIY vs outsource preference**
- ❌ **Developer on staff?**

**Impact:** Can't tailor recommendations to user's ability to execute.

### Gap 4: Reports Don't Explain HOW to Automate

Reports recommend WHAT (software) but not:
- ❌ How to connect existing tools with Make/n8n
- ❌ Specific automation workflows for their industry
- ❌ Step-by-step implementation guides
- ❌ "Here's what this would look like" examples

### Gap 5: Implementation Costs Are Generic

The `diy_resources.json` has learning time estimates:
```json
"chatbot": {"learning_time": "1-2 weeks"},
"customer_support": {"learning_time": "3-4 weeks"}
```

But missing:
- ❌ Agency project costs (€2K-20K typical)
- ❌ Freelancer hourly rates (€50-150/hr)
- ❌ Maintenance burden estimates
- ❌ Hidden costs (API overages, hosting)

---

## Part 3: What Users Need to See

### For Each Finding, Show:

```
┌─────────────────────────────────────────────────────────────────────┐
│ IMPLEMENTATION OPTIONS                                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ 🛒 BUY SOFTWARE                                                     │
│    Calendly Pro: €12/mo, 1 week setup                              │
│    Best for: Quick win, no technical work                          │
│                                                                     │
│ 🔗 CONNECT YOUR TOOLS (No-Code Automation)                          │
│    Use Make/n8n to connect Calendar + CRM + Email                  │
│    Cost: €29/mo (Make) + 4 hrs setup                               │
│    Workflow: New booking → Add to CRM → Send confirmation          │
│    Best for: Custom needs, some technical comfort                  │
│                                                                     │
│ 🏗️ BUILD CUSTOM                                                     │
│    AI-powered scheduling with Claude + Supabase                    │
│    Cost: €5K-15K build, €50-200/mo running                         │
│    Time: 2-4 weeks with developer                                  │
│    Best for: Unique requirements, competitive advantage            │
│                                                                     │
│ 👥 HIRE EXPERT                                                      │
│    Automation agency: €3K-8K for this project                      │
│    Freelancer: €1.5K-3K (30-60 hrs @ €50-100/hr)                  │
│    Best for: Fast results, no internal capability                  │
│                                                                     │
│ ⭐ OUR RECOMMENDATION: Connect Your Tools                           │
│    Why: You have HubSpot already. Make can connect it to           │
│    Calendly in 2 hours. No switching software, keeps your data.   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Decision Framework to Show Users:

```
Do you have a developer on staff?
├─ YES → Consider Build Custom (if unique needs)
│        Otherwise → Connect Your Tools with Make/n8n
│
└─ NO → Do you need results in <2 weeks?
        ├─ YES → Hire Expert OR Buy Software
        │
        └─ NO → Are you willing to learn?
                ├─ YES → Connect Your Tools (20-40 hrs learning)
                └─ NO → Hire Expert OR Buy Software
```

---

## Part 4: Improvement Recommendations

### Priority 1: Add "Implementation Path Advisor" Skill

Create new skill: `backend/src/skills/analysis/implementation_path.py`

```python
class ImplementationPathSkill(LLMSkill):
    """
    For each finding, recommend FOUR implementation paths:
    1. Buy SaaS - fastest, least control
    2. Connect Tools - Make/n8n automation, no-code
    3. Build Custom - full control, needs developer
    4. Hire Expert - fastest custom, highest cost

    Decision based on:
    - Technical capability (quiz answer)
    - Budget
    - Timeline urgency
    - Existing tool stack
    """
```

### Priority 2: Add Quiz Questions for Capability

Add to all industry question sets:

```json
{
  "id": "implementation_capability",
  "question": "When implementing new tools, who typically handles the setup?",
  "input_type": "select",
  "options": [
    {"value": "self_tech", "label": "I/we do it ourselves - we're technical"},
    {"value": "self_learn", "label": "I/we figure it out with tutorials"},
    {"value": "hire_help", "label": "We hire someone to set it up"},
    {"value": "vendor_help", "label": "We rely on vendor support/onboarding"}
  ],
  "target_categories": ["implementation_fit"],
  "priority": 1
},
{
  "id": "implementation_urgency",
  "question": "How quickly do you need this problem solved?",
  "input_type": "select",
  "options": [
    {"value": "asap", "label": "ASAP - it's costing us money daily"},
    {"value": "month", "label": "Within a month"},
    {"value": "quarter", "label": "This quarter"},
    {"value": "when_ready", "label": "When we find the right solution"}
  ],
  "target_categories": ["buying_signals", "implementation_fit"],
  "priority": 2
},
{
  "id": "developer_on_staff",
  "question": "Do you have a developer or technical person on staff?",
  "input_type": "select",
  "options": [
    {"value": "yes_full", "label": "Yes, full-time developer(s)"},
    {"value": "yes_part", "label": "Yes, part-time or contractor"},
    {"value": "tech_savvy", "label": "No developer, but someone tech-savvy"},
    {"value": "no", "label": "No technical staff"}
  ],
  "target_categories": ["implementation_fit"],
  "priority": 2
}
```

### Priority 3: Add Missing Automation Platforms to Vendor DB

Add these vendors with full data:

**AI Agent Platforms:**
- Lindy (lindy.ai) - AI agents for SMBs
- Relevance AI - No-code AI agents
- Beam AI - AI agents for customer service

**Low-Code Builders:**
- Retool - Internal tool builder
- Bubble - No-code web apps
- Glide - Mobile apps from spreadsheets
- Softr - Web apps from Airtable

**Scraping/Data:**
- Apify - Web scraping platform
- Firecrawl - AI-powered web scraping

**AI Dev Tools:**
- Cursor - AI-native IDE (€20/mo)
- Replit - Browser-based IDE with AI

### Priority 4: Add Agency/Freelancer Cost Data

Create new knowledge file: `backend/src/knowledge/implementation_costs.json`

```json
{
  "agency_costs": {
    "automation_project": {
      "simple": {"min": 2000, "max": 5000, "description": "Connect 2-3 tools with Make/Zapier"},
      "medium": {"min": 5000, "max": 15000, "description": "Custom workflow with AI integration"},
      "complex": {"min": 15000, "max": 50000, "description": "Full custom solution with multiple integrations"}
    },
    "ongoing_support": {"hourly": {"min": 75, "max": 150}, "monthly_retainer": {"min": 500, "max": 2000}}
  },
  "freelancer_costs": {
    "automation_specialist": {"hourly": {"min": 50, "max": 100}},
    "ai_developer": {"hourly": {"min": 100, "max": 200}},
    "no_code_builder": {"hourly": {"min": 40, "max": 80}}
  },
  "diy_time_estimates": {
    "learn_make_zapier": {"hours": 20, "description": "Basic competency"},
    "learn_n8n": {"hours": 30, "description": "Self-hosted, more complex"},
    "build_simple_automation": {"hours": 8, "description": "After learning platform"},
    "build_ai_integration": {"hours": 40, "description": "Claude API + existing tools"}
  },
  "hidden_costs": {
    "api_overages": "Plan for 2x expected usage in first 3 months",
    "maintenance": "10-20% of build cost annually",
    "hosting": "€20-100/month for custom solutions"
  }
}
```

### Priority 5: Enhance Three Options with Connect Tools Path

Update `three_options.py` to generate FOUR options:

1. **Buy SaaS** (current off_the_shelf)
2. **Connect Tools** (NEW - automation workflow)
3. **Build Custom** (current custom_solution)
4. **Hire Expert** (NEW - agency/freelancer path)

Add to prompt:
```
Option B: CONNECT YOUR TOOLS (No-Code Automation)
- Use Make, n8n, or Zapier to connect existing tools
- No switching software, keep your data
- Best for: Custom workflows without coding

Option D: HIRE EXPERT
- Automation agency or freelancer builds for you
- Cost: €2K-20K depending on complexity
- Best for: Fast results, no internal capability
```

---

## Part 5: Specific Automation Workflow Examples

Add to knowledge base per industry:

### Dental Practice Automations

```json
{
  "industry": "dental",
  "automations": [
    {
      "name": "Appointment Reminder Workflow",
      "trigger": "24 hours before appointment",
      "tools": ["Open Dental", "Make", "Twilio"],
      "steps": [
        "Get tomorrow's appointments from Open Dental",
        "For each appointment, send SMS via Twilio",
        "Log confirmation status back to Open Dental"
      ],
      "build_time": "2-4 hours",
      "monthly_cost": "€29 (Make) + €0.05/SMS"
    },
    {
      "name": "Review Request Automation",
      "trigger": "After appointment marked complete",
      "tools": ["Open Dental", "n8n", "Podium or BirdEye"],
      "steps": [
        "Watch for completed appointments",
        "Wait 2 hours",
        "Send review request via SMS/email",
        "Track responses"
      ],
      "build_time": "3-5 hours",
      "expected_result": "30-50% increase in Google reviews"
    }
  ]
}
```

### Recruiting Agency Automations

```json
{
  "industry": "recruiting",
  "automations": [
    {
      "name": "Candidate Outreach Sequence",
      "trigger": "New candidate added to ATS",
      "tools": ["Bullhorn", "Make", "Claude API", "Email"],
      "steps": [
        "New candidate in Bullhorn triggers webhook",
        "Claude generates personalized outreach based on profile",
        "Send via email with tracking",
        "Log engagement back to ATS"
      ],
      "build_time": "6-10 hours",
      "monthly_cost": "€49 (Make) + ~€30 (Claude API)",
      "expected_result": "2-3x response rates vs templates"
    }
  ]
}
```

---

## Part 6: Action Plan

### Week 1: Foundation
- [ ] Add 3 quiz questions for implementation capability
- [ ] Create `implementation_costs.json` knowledge file
- [ ] Add top 5 missing automation platforms to vendor DB

### Week 2: Report Enhancement
- [ ] Create `implementation_path.py` skill
- [ ] Update `three_options.py` to use 4 options
- [ ] Add automation workflow examples for dental, recruiting

### Week 3: Knowledge Expansion
- [ ] Add remaining automation platforms to vendor DB
- [ ] Create automation workflow templates per industry
- [ ] Add agency/freelancer recommendation logic

### Week 4: Testing & Refinement
- [ ] Generate test reports with new implementation paths
- [ ] Validate cost estimates are realistic
- [ ] User testing for clarity

---

## Verification Commands

After implementing, run:

```bash
# Check automation platforms coverage
cd backend && python -c "
from src.services.vendor_service import VendorService
import asyncio

async def check():
    vs = VendorService()
    platforms = ['make', 'n8n', 'zapier', 'lindy', 'apify', 'retool', 'cursor']
    for p in platforms:
        v = await vs.get_vendor(p)
        print(f'{p}: {\"✓\" if v else \"❌\"}')"

# Check quiz captures capability
grep -r "implementation_capability\|developer_on_staff" backend/src/knowledge/industry_questions/

# Check implementation paths in reports
# Generate test report and verify 4 options appear
```

---

## Summary

| Area | Current State | Target State |
|------|---------------|--------------|
| Automation platforms | 7/24 (29%) | 20/24 (83%) |
| Implementation paths | 3 (SaaS only) | 4 (SaaS, Connect, Build, Hire) |
| Capability assessment | None | 3 quiz questions |
| Automation workflows | None | 5+ per industry |
| Agency/freelancer costs | None | Full cost data |
| Decision framework | Implicit | Explicit tree |

**Bottom line:** The knowledge exists but isn't being surfaced. Users need to see:
1. **What** they can do (automation options)
2. **How** to do it (step-by-step)
3. **Who** should do it (based on their capability)
4. **What it costs** (realistic, including hire option)
