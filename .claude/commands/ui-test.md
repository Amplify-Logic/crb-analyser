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
