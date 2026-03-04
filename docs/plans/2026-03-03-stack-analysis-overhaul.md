# Stack Analysis Overhaul — Execution Plan

**Date:** 2026-03-03
**Goal:** Make the Stack Analysis tab show real data instead of hardcoded/fabricated content
**Kickoff:** `/execute docs/plans/2026-03-03-stack-analysis-overhaul.md`

---

## Context for Executor

The Stack Analysis tab in the report viewer shows a 3-column architecture diagram (YOUR TOOLS → AI BRAIN → AUTOMATIONS) plus a cost comparison. Currently all content is either empty, hardcoded, or fabricated.

**Test report:** Naif ecommerce report
- Report ID: `fbc46137-5904-4df8-ada9-e8ccdeb3e7aa`
- Quiz session: `be8754c1-c738-48cd-9fa6-1d38de691e5f`
- Status already set to `released`
- View at: `http://localhost:5175/report/fbc46137-5904-4df8-ada9-e8ccdeb3e7aa` (need backend on 8383, frontend on 5175)

**Start servers:**
```bash
cd backend && python -m uvicorn src.main:app --host 0.0.0.0 --port 8383 &
cd frontend && pnpm dev &
```

---

## Data Available (already in report JSON)

The report JSON at `backend/reports/ecommerce/20260303_211814_naif.json` contains everything we need:

### 1. Existing tools — from `automation_summary.stack_assessment.tools`
```json
[
  {"name": "shopify", "slug": "shopify", "api_score": 3},
  {"name": "klaviyo", "slug": "klaviyo", "api_score": 3},
  {"name": "google-analytics", "slug": "google-analytics", "api_score": 3}
]
```
Also available in `quiz_answers["current_tools"]` = `["shopify", "klaviyo", "google-analytics"]`

### 2. Recommendations with 3-tier options
Each recommendation has `options.connect_and_automate` and `options.targeted_upgrade` with:
- `tools_used` / `tools` — actual tool names
- `monthly_cost` / `cost_range` — actual costs (string format, needs parsing)
- `matched_vendor` — vendor from our DB with pricing

### 3. Findings with real descriptions
Each finding has `title`, `description`, `category`, `value_saved`, etc.

---

## Task 1: Fix existing_tools population

**File:** `backend/src/services/architecture_generator.py`
**Method:** `generate_architecture()` lines 180-209

### Problem
`quiz_answers["current_tools"]` = `["shopify", "klaviyo", "google-analytics"]` but `TOOL_DATABASE` has key `"google_analytics"` (underscore). The `_match_tool()` method fails on hyphenated slugs.

### Fix

**1a.** Add a `SLUG_ALIASES` dict above `TOOL_DATABASE` (around line 105):

```python
SLUG_ALIASES = {
    "google-analytics": "google_analytics",
    "ga4": "google_analytics",
    "google analytics": "google_analytics",
    "woocommerce": "woocommerce",
    "ship-station": "shipstation",
    "send-cloud": "sendcloud",
}
```

**1b.** Add missing ecommerce tools to `TOOL_DATABASE` (after line 151):

```python
# Ecommerce
"shopify": {"name": "Shopify", "category": "existing", "monthly_cost": 36, "icon": "shopping-cart"},
"klaviyo": {"name": "Klaviyo", "category": "existing", "monthly_cost": 45, "icon": "mail"},
"gorgias": {"name": "Gorgias", "category": "existing", "monthly_cost": 60, "icon": "message"},
"tidio": {"name": "Tidio", "category": "existing", "monthly_cost": 29, "icon": "message"},
"shipstation": {"name": "ShipStation", "category": "existing", "monthly_cost": 30, "icon": "truck"},
"sendcloud": {"name": "Sendcloud", "category": "existing", "monthly_cost": 25, "icon": "truck"},
"woocommerce": {"name": "WooCommerce", "category": "existing", "monthly_cost": 0, "icon": "shopping-cart"},
"inventory_planner": {"name": "Inventory Planner", "category": "existing", "monthly_cost": 100, "icon": "package"},
"triple_whale": {"name": "Triple Whale", "category": "existing", "monthly_cost": 100, "icon": "bar-chart"},
```

**1c.** Update `_match_tool()` to normalize slugs:

```python
def _match_tool(self, tool_key: str) -> Optional[Dict[str, Any]]:
    tool_key = tool_key.lower().strip()
    # Check aliases first
    normalized = SLUG_ALIASES.get(tool_key, tool_key.replace("-", "_"))
    if normalized in TOOL_DATABASE:
        return TOOL_DATABASE[normalized]
    # Fuzzy fallback
    for key, info in TOOL_DATABASE.items():
        if key in tool_key or tool_key in info["name"].lower():
            return info
    return None
```

**1d.** Add second data source — pass `existing_stack` into `generate_architecture()`. Change method signature:

```python
def generate_architecture(
    self,
    recommendations: List[Dict[str, Any]],
    quiz_answers: Dict[str, Any],
    existing_stack: Optional[List[Dict[str, Any]]] = None,
) -> SystemArchitecture:
```

Then after existing_tools_raw processing (around line 190), add fallback:

```python
# Fallback: use existing_stack data if current_tools matching fails
if not existing_tools and existing_stack:
    for i, stack_tool in enumerate(existing_stack[:6]):
        slug = stack_tool.get("slug", stack_tool.get("name", ""))
        tool_info = self._match_tool(slug)
        api_score = stack_tool.get("api_score", 0)
        tool_name = tool_info["name"] if tool_info else slug.replace("-", " ").title()
        existing_tools.append(ToolNode(
            id=f"existing-{i}",
            name=tool_name,
            category="existing",
            icon=tool_info.get("icon") if tool_info else None,
            monthly_cost=0,
            crb=NodeCRB(
                cost="Already owned",
                risk="Low" if api_score >= 3 else "Medium — limited API",
                risk_level="low" if api_score >= 3 else "medium",
                benefit=f"API score {api_score}/5 — {'strong' if api_score >= 3 else 'limited'} integration potential",
                powers=[],
            ),
            position=Position(x=0, y=i * 100, column="existing"),
            is_existing=True,
        ))
```

**1e.** Update the caller in `report_service.py` (line ~3990):

```python
arch_gen = ArchitectureGenerator()
architecture = arch_gen.generate_architecture(
    recommendations=recommendations,
    quiz_answers=self.context.get("answers", {}),
    existing_stack=self.context.get("existing_stack", []),
)
```

### Verify
After this task, `system_architecture.existing_tools` should contain 3 items for the Naif report (Shopify, Klaviyo, Google Analytics).

---

## Task 2: Make AI layer dynamic

**File:** `backend/src/services/architecture_generator.py`
**Method:** `generate_architecture()` lines 212-243

### Problem
AI layer is hardcoded to Claude Sonnet 4.5 + Make.com regardless of recommendations.

### Fix

Replace the hardcoded block (lines 212-243) with dynamic extraction:

```python
# Build AI layer from what recommendations actually use
ai_tools_seen = {}  # deduplicate
for rec in recommendations:
    connect = rec.get("options", {}).get("connect_and_automate", {})
    for tool_name in connect.get("tools_used", []):
        tool_lower = tool_name.lower()
        # Categorize
        if "claude" in tool_lower:
            if "claude" not in ai_tools_seen:
                # Determine which Claude model
                model_name = "Claude Sonnet 4.5"
                monthly = 50
                if "haiku" in tool_lower:
                    model_name = "Claude Haiku 4.5"
                    monthly = 20
                elif "opus" in tool_lower:
                    model_name = "Claude Opus 4.5"
                    monthly = 150
                ai_tools_seen["claude"] = {
                    "name": model_name, "category": "ai_brain",
                    "monthly_cost": monthly, "icon": "brain",
                    "powers": []
                }
        elif "make" in tool_lower:
            if "make" not in ai_tools_seen:
                ai_tools_seen["make"] = {
                    "name": "Make.com", "category": "automation",
                    "monthly_cost": 20, "icon": "zap",
                    "powers": []
                }
        elif "supabase" in tool_lower:
            if "supabase" not in ai_tools_seen:
                ai_tools_seen["supabase"] = {
                    "name": "Supabase", "category": "database",
                    "monthly_cost": 0, "icon": "database",
                    "powers": []
                }
        elif "railway" in tool_lower or "vercel" in tool_lower:
            key = "hosting"
            if key not in ai_tools_seen:
                ai_tools_seen[key] = {
                    "name": tool_name, "category": "hosting",
                    "monthly_cost": 5 if "railway" in tool_lower else 0,
                    "icon": "cloud",
                    "powers": []
                }

    # Track which recs each AI tool powers
    rec_title = rec.get("title", "")[:40]
    for key in ai_tools_seen:
        if key in ["claude", "make"]:  # These power most automations
            if rec_title not in ai_tools_seen[key]["powers"]:
                ai_tools_seen[key]["powers"].append(rec_title)

# Fallback if nothing extracted
if not ai_tools_seen:
    ai_tools_seen["claude"] = {
        "name": "Claude Sonnet 4.5", "category": "ai_brain",
        "monthly_cost": 50, "icon": "brain", "powers": []
    }
    ai_tools_seen["make"] = {
        "name": "Make.com", "category": "automation",
        "monthly_cost": 20, "icon": "zap", "powers": []
    }

ai_layer = []
for i, (key, tool_data) in enumerate(ai_tools_seen.items()):
    ai_layer.append(ToolNode(
        id=f"ai-{key}",
        name=tool_data["name"],
        category=tool_data["category"],
        icon=tool_data.get("icon"),
        monthly_cost=tool_data["monthly_cost"],
        crb=NodeCRB(
            cost=f"~€{tool_data['monthly_cost']}/mo" if tool_data["monthly_cost"] > 0 else "Free tier",
            risk="API dependency" if tool_data["category"] == "ai_brain" else "Low",
            risk_level="low",
            benefit=f"Powers {len(tool_data['powers'])} automations",
            powers=tool_data["powers"][:5],
        ),
        position=Position(x=200, y=i * 100, column="ai_layer"),
    ))
```

### Verify
AI layer should show the actual tools from recommendations (likely Claude Haiku + Make.com + Supabase + Railway for Naif).

---

## Task 3: Generate real automations from findings

**File:** `backend/src/services/architecture_generator.py`
**Method:** `generate_architecture()` lines 246-256

### Problem
Automation names truncated to 30 chars. Triggers are fake ("When automate occurs").

### Fix

Replace lines 246-256:

```python
# Build automations from recommendations with real data
automations = []
for i, rec in enumerate(recommendations[:6]):
    title = rec.get("title", "Automation")

    # Extract real trigger from finding context
    connect = rec.get("options", {}).get("connect_and_automate", {})
    approach = connect.get("approach", "")

    # Derive trigger from the finding's category/context
    trigger = _derive_trigger(title, rec)
    action = approach[:80] if approach else rec.get("description", "Automated action")[:80]

    # Get tools from the selected/connect option
    tools = connect.get("tools_used", ["claude"])
    tool_keys = [t.lower().split()[0] for t in tools[:3]]

    automations.append(AutomationNode(
        id=f"auto-{i}",
        name=title,  # Full title — frontend handles overflow
        trigger=trigger,
        action=action,
        tools_used=tool_keys,
        output_type="action",
    ))
```

Add a helper function above the class:

```python
def _derive_trigger(title: str, rec: Dict[str, Any]) -> str:
    """Derive a meaningful trigger from recommendation title and data."""
    title_lower = title.lower()

    if "order" in title_lower and ("rout" in title_lower or "track" in title_lower):
        return "New order placed in Shopify"
    if "cart" in title_lower and ("abandon" in title_lower or "recovery" in title_lower):
        return "Cart abandoned for 1+ hours"
    if "email" in title_lower or "klaviyo" in title_lower or "dormant" in title_lower:
        return "Subscriber inactive for 90+ days"
    if "support" in title_lower or "chatbot" in title_lower or "inquir" in title_lower:
        return "Customer support ticket received"
    if "inventory" in title_lower or "forecast" in title_lower or "restock" in title_lower:
        return "Stock level drops below threshold"
    if "product" in title_lower and ("description" in title_lower or "content" in title_lower):
        return "New product added to catalog"
    if "review" in title_lower:
        return "New product review posted"
    if "return" in title_lower:
        return "Return request submitted"
    if "segment" in title_lower or "personali" in title_lower:
        return "Customer behavior data updated"
    if "conversion" in title_lower or "analytics" in title_lower or "data" in title_lower:
        return "Weekly data sync triggered"
    if "recommend" in title_lower or "aov" in title_lower or "cross-sell" in title_lower:
        return "Customer views product page"
    if "fulfillment" in title_lower or "shipping" in title_lower:
        return "Order ready for fulfillment"

    # Generic but better than "When X occurs"
    return "Triggered by schedule or event"
```

### Verify
Automations should show full titles and real triggers like "Cart abandoned for 1+ hours".

---

## Task 4: Build real cost comparison

**File:** `backend/src/services/architecture_generator.py`
**Method:** `_calculate_costs()` lines 299-354

### Problem
SaaS costs fall through to fake "Multiple SaaS tools €400". DIY costs are always the same 4 items.

### Fix

Replace entire `_calculate_costs()` method:

```python
def _calculate_costs(
    self,
    recommendations: List[Dict[str, Any]],
    ai_layer: List[ToolNode],
) -> CostComparison:
    """Calculate SaaS vs DIY cost comparison from actual recommendation data."""

    # === DIY ROUTE: from connect_and_automate options ===
    diy_items_seen = {}
    total_build_hours = 0

    for node in ai_layer:
        if node.name not in diy_items_seen:
            diy_items_seen[node.name] = node.monthly_cost

    for rec in recommendations:
        connect = rec.get("options", {}).get("connect_and_automate", {})
        build_time = connect.get("build_time", "")
        # Parse build hours from strings like "8-12 hours" or "2-3 weeks"
        hours = _parse_build_hours(build_time)
        total_build_hours += hours

    diy_items = [
        CostItem(name=name, monthly_cost=cost, category="diy")
        for name, cost in diy_items_seen.items()
    ]
    diy_total = sum(item.monthly_cost for item in diy_items)

    # Build cost = total hours × €50/hr (freelancer rate)
    build_cost = max(total_build_hours * 50, 500)  # Minimum €500

    # === SAAS ROUTE: from targeted_upgrade options ===
    saas_items_seen = {}

    for rec in recommendations[:6]:
        tu = rec.get("options", {}).get("targeted_upgrade", {})
        tools = tu.get("tools", [])
        cost_range = tu.get("cost_range", "")

        # Try to get costs from matched_vendor
        matched = tu.get("matched_vendor", {})
        vendor_cost = matched.get("monthly_cost")

        for tool_name in tools:
            if tool_name and tool_name not in saas_items_seen and "no matching" not in tool_name.lower():
                # Parse cost from cost_range string or use vendor cost
                tool_cost = _parse_cost_from_range(cost_range, tool_name)
                if not tool_cost and vendor_cost:
                    tool_cost = float(vendor_cost)
                if not tool_cost:
                    tool_cost = 50  # Conservative estimate
                saas_items_seen[tool_name] = tool_cost

    saas_items = [
        CostItem(name=name, monthly_cost=cost, category="saas")
        for name, cost in saas_items_seen.items()
    ]
    saas_total = sum(item.monthly_cost for item in saas_items)

    # Ensure we have at least something
    if not saas_items:
        saas_total = diy_total * 3  # Rough 3x multiplier
        saas_items = [CostItem(name="Estimated SaaS equivalent", monthly_cost=saas_total, category="saas")]

    monthly_savings = saas_total - diy_total
    savings_pct = (monthly_savings / saas_total * 100) if saas_total > 0 else 0
    breakeven = build_cost / monthly_savings if monthly_savings > 0 else 999

    return CostComparison(
        saas_route=CostBreakdown(items=saas_items, total_monthly=saas_total),
        diy_route=CostBreakdown(items=diy_items, total_monthly=diy_total, total_one_time=build_cost),
        monthly_savings=monthly_savings,
        savings_percentage=savings_pct,
        build_cost=build_cost,
        breakeven_months=round(breakeven, 1),
    )
```

Add helper functions above the class:

```python
def _parse_build_hours(build_time: str) -> float:
    """Parse build hours from strings like '8-12 hours' or '2-3 weeks'."""
    if not build_time:
        return 8  # Default
    build_time = build_time.lower()
    import re
    numbers = re.findall(r'(\d+(?:\.\d+)?)', build_time)
    if not numbers:
        return 8
    # Take the average of found numbers
    avg = sum(float(n) for n in numbers) / len(numbers)
    if "week" in build_time:
        return avg * 20  # 20 hours per week
    if "day" in build_time:
        return avg * 4  # 4 hours per day
    return avg  # Assume hours


def _parse_cost_from_range(cost_range: str, tool_name: str) -> Optional[float]:
    """Parse a monthly cost from a cost_range string for a specific tool."""
    if not cost_range:
        return None
    import re
    # Look for patterns like "ToolName EUR 100" or "ToolName €100"
    tool_lower = tool_name.lower()
    cost_lower = cost_range.lower()

    # Try to find the tool name near a price
    patterns = [
        rf'{re.escape(tool_lower)}[^€\d]*[€EUR]*\s*(\d+)',
        rf'(\d+)[^€\d]*{re.escape(tool_lower)}',
    ]
    for pattern in patterns:
        match = re.search(pattern, cost_lower)
        if match:
            return float(match.group(1))

    # Fallback: first number in the string
    match = re.search(r'[€EUR]\s*(\d+)', cost_range)
    if match:
        return float(match.group(1))

    return None
```

### Verify
SaaS route should list real tools (ShipStation, Klaviyo, Gorgias, etc.) with actual pricing. DIY route should show tools extracted from connect options.

---

## Task 5: Frontend — handle long names and show tools

**File:** `frontend/src/components/report/StackTab.tsx`

### 5a. Existing tools should show API score badge

In the existing tools `.map()` (around line 170), add after "Already owned":

```tsx
{tool.crb?.risk_level && (
  <span className={`text-xs px-2 py-0.5 rounded-full ml-8 ${
    tool.crb.risk_level === 'low' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
  }`}>
    {tool.crb.benefit?.includes('API score') ? tool.crb.benefit.split('—')[0].trim() : 'Connected'}
  </span>
)}
```

### 5b. Automation names — no truncation, use CSS

Change the automations card (around line 230) to handle long names:

```tsx
<p className="font-medium text-green-900 text-sm line-clamp-2">{auto.name}</p>
```

Add `line-clamp-2` utility — already available via Tailwind.

### 5c. Show more than 4 automations

Change `automations.slice(0, 4)` on line 225 to `automations.slice(0, 6)` and add a "show all" toggle if more exist.

### 5d. SaaS cost breakdown — remove "Multiple SaaS tools" fallback display

The backend fix handles this, but add a guard in the frontend: if `saas_route.items` has only 1 item named "Multiple SaaS tools" or "Estimated SaaS equivalent", show a note instead of pretending.

---

## Task 6: Wire existing_stack into architecture call

**File:** `backend/src/services/report_service.py` line ~3990

### Current
```python
arch_gen = ArchitectureGenerator()
architecture = arch_gen.generate_architecture(
    recommendations=recommendations,
    quiz_answers=self.context.get("answers", {}),
)
```

### Change to
```python
arch_gen = ArchitectureGenerator()
architecture = arch_gen.generate_architecture(
    recommendations=recommendations,
    quiz_answers=self.context.get("answers", {}),
    existing_stack=self.context.get("existing_stack", []),
)
```

---

## Execution Order

1. **Task 1** — Fix existing_tools (backend) — highest impact, makes YOUR TOOLS column work
2. **Task 6** — Wire existing_stack — one-line change, unlocks Task 1's fallback
3. **Task 2** — Dynamic AI layer (backend) — makes AI BRAIN column real
4. **Task 3** — Real automations (backend) — makes AUTOMATIONS column real
5. **Task 4** — Real cost comparison (backend) — makes Cost Comparison real
6. **Task 5** — Frontend polish — visual improvements

**After each task:** Restart backend, refresh the report page, verify the change visually.

---

## Validation Checklist

After all tasks, the Naif report Stack Analysis should show:

- [ ] YOUR TOOLS: Shopify, Klaviyo, Google Analytics (3 items with API score badges)
- [ ] AI BRAIN: Claude Haiku (most recs use Haiku), Make.com, Supabase, Railway (extracted from recs)
- [ ] AUTOMATIONS: 5-6 items with real titles and triggers like "Cart abandoned for 1+ hours"
- [ ] SaaS Cost: Lists real tools (ShipStation, Inventory Planner, Triple Whale, Gorgias, Klaviyo) with actual pricing
- [ ] DIY Cost: Shows actual AI layer tools with their costs
- [ ] Build Cost: Calculated from recommendation build_time fields, not hardcoded €2,400
- [ ] No "Multiple SaaS tools" fallback anywhere
- [ ] No truncated garbage in automation names

## Generate fresh report to test end-to-end

```bash
cd backend && python generate_and_review.py --industry ecommerce --dev-mode
```

Then view at `http://localhost:5175/report/{new-id}` — Stack Analysis tab.
