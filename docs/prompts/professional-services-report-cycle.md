# Professional Services Report Generation & Quality Cycle

## Context

We just completed vendor research for professional-services — 18 new vendors discovered and added to Supabase across 6 categories (CRM, project management, automation, scheduling, finance, AI assistants). We also fixed 4 bugs in the report generation pipeline (CostEstimate null coercion, playbook logger, vendor KB format handling, review data extraction). Time to generate a test report and iterate on quality.

## Step 1: Generate the report

```bash
cd backend && source venv/bin/activate
python generate_and_review.py --industry professional-services --dev-mode
```

Wait for it to complete. Save the output — it includes:
- Report ID (for Supabase lookup)
- Quality analysis (findings count, recommendations count, distribution)
- Saved JSON file path in `reports/professional-services/`

## Step 2: Analyze the output

Read the saved report JSON and the terminal output. Check for:

### Hard failures (fix immediately)
- [ ] Any Python exceptions or tracebacks
- [ ] `year_one_total` validation errors (should be fixed)
- [ ] Logger keyword argument errors (should be fixed)
- [ ] 0 findings or 0 recommendations (should be fixed)
- [ ] Vendor count = 0 for professional-services (should be fixed)

### Quality issues (assess severity)
- [ ] Are recommendations diverse? (mix of connect_and_automate, enhance_with_ai, targeted_upgrade — NOT all the same type)
- [ ] Does each recommendation have 4 options (buy/connect/build/hire) with cost estimates > 0?
- [ ] Are vendor names in recommendations real KB vendors (not "No matching vendor" or hallucinated)?
- [ ] Is the executive summary coherent and specific to the company profile?
- [ ] Are NET scores reasonable (not all identical, range between -5 and +15)?
- [ ] Does the playbook have realistic timelines and task breakdowns?

### Data quality (log for future improvement)
- [ ] How many recommendations reference discovered vendors vs existing KB vendors?
- [ ] Are pricing tiers from scraped data appearing in cost estimates?
- [ ] Is the industry context (professional services pain points) reflected in findings?

## Step 3: Fix and re-run

For each issue found:

1. **Identify the source** — is it in report_service.py, a skill, the knowledge base, or the seed data?
2. **Fix the root cause** — don't patch symptoms
3. **Re-run** the same command to verify the fix
4. **Compare** the before/after quality scores

Key files for fixes:
- `backend/src/services/report_service.py` — main report orchestrator (3,500+ lines, use offset/limit)
- `backend/src/skills/report-generation/four_options.py` — buy/connect/build/hire generation
- `backend/src/skills/report-generation/three_options.py` — alternative 3-option format
- `backend/src/knowledge/professional-services/` — industry KB (vendors, opportunities, benchmarks)
- `backend/src/knowledge/__init__.py` — KB loading (get_vendor_recommendations, line 650+)
- `backend/src/services/playbook_generator.py` — implementation playbook generation
- `backend/src/cli/seeds/professional-services.json` — seed company profiles

## Step 4: Validation checklist

After fixes, run again and confirm ALL pass:

```
QUALITY GATES:
[ ] Findings count >= 5
[ ] Recommendations count >= 3
[ ] Recommendation types: at least 2 different types present
[ ] Every recommendation has cost.year_one_total > 0 for at least buy + connect options
[ ] No "No matching vendor" in buy options (should have real vendor names)
[ ] Executive summary > 200 characters and mentions the company name
[ ] NET scores have variance (std dev > 1.0)
[ ] Playbook generated without errors
[ ] Quality review score >= 6/10
[ ] No Python exceptions in output
```

## Tips

- Use `--dev-mode` to route through Claude CLI (Max subscription) instead of API credits
- Use `--quick` for faster iteration with Sonnet (lower quality but 3x faster)
- Use `--seed-name "Company Name"` to test a specific seed profile
- Reports save to `backend/reports/professional-services/<timestamp>_<company>.json`
- The quality review at the end uses `review_service.py` to score the report 1-10
- If vendor matching seems wrong, check `backend/src/knowledge/professional-services/vendors.json` — it uses `categories` dict format (not `vendor_categories` list)
