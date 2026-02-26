---
model: opus
description: Parallel user story validation — discovers YAML stories, fans out bowser-qa-agents, aggregates results
argument-hint: [headed] [filename-filter] [vision]
---

# Purpose

Discover user stories from YAML files, fan out parallel `bowser-qa-agent` instances to validate each story, then aggregate and report pass/fail results with screenshots.

## Variables

HEADED: detected from $ARGUMENTS (default: "false" — set to "true" or "headed" for visible browser windows)
VISION: detected from $ARGUMENTS — if the keyword "vision" appears anywhere in the arguments, enable vision mode (screenshots returned as image responses in the agent's context for richer validation; higher token cost). Default: false.
FILENAME_FILTER: remaining non-keyword arguments after removing "headed" and "vision" (if present)
STORIES_DIR: "tests/ui/stories"
STORIES_GLOB: "tests/ui/stories/*.yaml"
AGENT_TIMEOUT: 300000
SCREENSHOTS_BASE: "screenshots/bowser-qa"
RUN_DIR: "{SCREENSHOTS_BASE}/{YYYYMMDD_HHMMSS}_{short-uuid}" (generated once at start of run)

## Codebase Structure

```
tests/ui/
└── stories/
    ├── quiz-flow.yaml         # Quiz completion journey
    ├── report-viewer.yaml     # Report rendering
    ├── checkout.yaml          # Payment flow UI
    ├── admin-dashboard.yaml   # Admin pages
    ├── landing-page.yaml      # Landing + CTA
    └── *.yaml                 # Additional story files
screenshots/
└── bowser-qa/
    └── 20260221_143022_a1b2c3/        # Run directory (datetime + short uuid)
        ├── quiz-flow/                  # Source file stem
        │   └── quiz-flow-complete-journey/   # Slugified story name
        ├── landing-page/
        │   └── landing-page-hero-and-cta/
        └── another-file/
            └── story-name/
```

## Instructions

- Spawn one `bowser-qa-agent` per story via the Task tool
- Launch ALL agents in a single message so they run in parallel
- Be absolutely sure you clearly prompt each agent to have one specific task so all tasks get covered and you get results for every story
- If FILENAME_FILTER is provided and non-empty, only run stories from files whose name contains that substring
- If a YAML file fails to parse, log a warning and skip it — do not abort the entire run
- If no stories are found after discovery, report that and stop
- Be resilient: if an agent times out or crashes, mark that story as FAIL and include whatever output was available

## Workflow

### Phase 1: Discover

1. Use the Glob tool to find all files matching `STORIES_GLOB`
2. If `FILENAME_FILTER` is provided and non-empty, filter the file list to only include files whose name contains that substring
3. Read each YAML file and parse the `stories` array
4. If a file fails to parse, log a warning and skip it
5. Build a flat list of all stories across all files, tracking which source file each story came from
6. If no stories are found, report that and stop
7. Generate `RUN_DIR` using Bash:
   ```bash
   RUN_DIR="screenshots/bowser-qa/$(date +%Y%m%d_%H%M%S)_$(uuidgen | tr '[:upper:]' '[:lower:]' | head -c 6)"
   ```
   Example result: `screenshots/bowser-qa/20260221_143022_a1b2c3`
8. For each story, build its `SCREENSHOT_PATH` by combining three parts:
   - `RUN_DIR` (from step 7)
   - Source file stem (filename without `.yaml` extension, e.g. `quiz-flow.yaml` → `quiz-flow`)
   - Slugified story name (lowercase, replace spaces with hyphens, e.g. `"Quiz Flow - Complete Journey"` → `quiz-flow-complete-journey`)

   Concatenate: `SCREENSHOT_PATH = "{RUN_DIR}/{file-stem}/{slugified-name}/"`

   Example: `screenshots/bowser-qa/20260221_143022_a1b2c3/quiz-flow/quiz-flow-complete-journey/`

### Phase 2: Spawn

9. For each story, spawn a `bowser-qa-agent` via the Task tool. Launch ALL agents in a single message so they run in parallel.
10. For each Task call, use `subagent_type: "general-purpose"` and this prompt (note: pass the pre-computed `SCREENSHOT_PATH` for this story):

```
You are a bowser-qa-agent. Read and follow the agent instructions at .claude/agents/bowser-qa-agent.md exactly.

Execute this user story and report results:

**Story:** {story.name}
**URL:** {story.url}
**Headed:** {HEADED}
**Vision:** {VISION}

**Workflow:**
{story.workflow}

Instructions:
- Follow the playwright-bowser skill at .claude/skills/playwright-bowser/SKILL.md
- Follow each step in the workflow sequentially
- Take a screenshot after each significant step
- Save ALL screenshots to: {SCREENSHOT_PATH}
- Report each step as PASS or FAIL with a brief explanation
- At the end, provide a summary: total steps, passed, failed
- Use this exact format for your final summary line:
  RESULT: {PASS|FAIL} | Steps: {passed}/{total}
```

### Phase 3: Collect

11. Wait for all agent results to arrive
12. Parse each agent's report to extract:
    - Overall result: PASS or FAIL (look for the `RESULT:` line; if not found, check for indicators of success/failure)
    - Steps completed vs total (from the `Steps: X/Y` portion)
    - The full agent report text
13. Track which stories passed and which failed

### Phase 4: Report

14. Verify all browser sessions are closed:
    ```bash
    playwright-cli list
    ```
    If any sessions remain, close them:
    ```bash
    playwright-cli close-all
    ```
15. Now follow the `Report` section to present results

## Report

Present the aggregated results in this format:

```
# UI Test Summary

**Run:** {current date and time}
**Stories:** {total} total | {passed} passed | {failed} failed
**Status:** ALL PASSED | PARTIAL FAILURE | ALL FAILED

## Results

| #   | Story        | Source File | Status | Steps            |
| --- | ------------ | ----------- | ------ | ---------------- |
| 1   | {story name} | {filename}  | PASS   | {passed}/{total} |
| 2   | {story name} | {filename}  | FAIL   | {passed}/{total} |

## Failures

(Only include this section if there are failures)

### Story: {failed story name}
**Source:** {filename}
**Agent Report:**
{full agent report for this story}

---

(Repeat for each failed story)

## Screenshots
All screenshots saved to: `{RUN_DIR}/`
```

Use ALL PASSED for status only when every story passed. Use PARTIAL FAILURE when some passed and some failed. Use ALL FAILED when none passed.
