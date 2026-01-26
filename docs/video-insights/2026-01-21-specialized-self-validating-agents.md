# Specialized Self-Validating Agents

> Source: YouTube video on Claude Code hooks in skills/subagents/commands
> Date extracted: 2026-01-21

## Core Insight

**Validation is now specializable at the prompt/skill/subagent level**, not just global hooks in settings.json.

The key breakthrough: Claude Code now supports hooks (`pre-tool-use`, `post-tool-use`, `stop`) inside of:
- Custom slash commands (prompts)
- Sub-agents
- Skills

This enables **deterministic validation** that runs automatically after AI operations.

---

## Why This Matters

| Before | After |
|--------|-------|
| Global hooks for everything | Specialized hooks per agent/skill |
| Trust LLM reasoning alone | Deterministic code validates LLM output |
| Catch errors at end | Catch and fix errors per-step |
| Manual review required | Self-correcting pipelines |
| One validation fits all | Task-specific validation |

### The Trust Equation

```
Validation → Trust → Time Saved
```

If your agents can validate their own work with deterministic code, you can trust them more, which means less manual review time.

---

## Key Patterns Extracted

### 1. Closed Loop Prompts

```
Agent runs → Validator checks → Issues found? → Agent fixes → Validator re-checks
```

The validator provides **specific, actionable feedback** that the agent can act on:
```
"Resolve this CSV error in [file_path]: [specific errors]"
```

### 2. One Agent, One Purpose

> "A focused agent with one purpose outperforms an unfocused agent with many purposes."

Specialized agents that do one thing extraordinarily well:
- CSV Edit Agent
- Report Generation Agent
- Vendor Research Agent

NOT: "General Purpose Agent that does everything"

### 3. Validators Directory Pattern

```
.claude/
├── hooks/
│   └── validators/
│       ├── csv_validator.py
│       ├── json_validator.py
│       ├── report_validator.py
│       └── vendor_validator.py
```

Each validator:
- Takes file path as input
- Outputs log file for observability
- Returns actionable error messages for agent to fix

### 4. Observable Logging

Every validator outputs its own log file:
```
logs/validators/
├── csv_single_validator.log
├── report_validator.log
└── vendor_validator.log
```

This provides proof that validations ran and what they found.

### 5. Agent Chaining with Specialized Validators

Top-level workflow orchestrates specialized sub-agents:
```
/review-finances
├── /categorize-csv (runs csv_validator)
├── /generative-ui (runs html_validator)
├── /merge-accounts (runs csv_validator)
└── /normalize-csv (runs csv_validator + global_validator)
```

Each sub-agent has its **own** specialized validator.

---

## Hook Configuration in Commands/Skills

### Command/Prompt Example

```yaml
---
name: csv-edit
description: Edit CSV files with validation
tools:
  - Glob
  - Read
  - Write
  - Edit
hooks:
  post_tool_use:
    - tools: [Edit, Write, Read]
      command: "uv run .claude/hooks/validators/csv_validator.py $CLAUDE_FILE_PATH"
---
```

### Sub-Agent Example

```yaml
---
name: csv-edit-agent
description: CSV editing agent with self-validation
allowed_tools:
  - Glob
  - Read
  - Write
  - Edit
hooks:
  post_tool_use:
    - tools: [Edit, Write]
      command: "uv run .claude/hooks/validators/csv_validator.py $CLAUDE_FILE_PATH"
  stop:
    - command: "uv run .claude/hooks/validators/validate_all_csvs.py"
---
```

### Key Variables Available

- `$CLAUDE_FILE_PATH` - Path to file that was read/edited/written
- `$CLAUDE_PROJECT_DIR` - Project root directory

---

## CRB Analyser Implementation Plan

### Current State

We already have:
- ✅ `MathValidatorSkill` - validates ROI calculations (great foundation!)
- ✅ `.claude/hooks/` directory with global hooks
- ✅ Skills system with `BaseSkill`, `SyncSkill`, `LLMSkill`
- ❌ No specialized hooks per command/skill
- ❌ No deterministic validators for report structure

### Proposed Implementation

#### Phase 1: Validators Directory

Create `.claude/hooks/validators/`:

```
.claude/hooks/validators/
├── report_json_validator.py   # Validates report JSON structure
├── finding_validator.py       # Validates individual findings
├── roi_validator.py           # Deterministic math check (calls MathValidatorSkill)
├── vendor_validator.py        # Validates vendor data completeness
└── quiz_response_validator.py # Validates quiz session data
```

#### Phase 2: Report Generation Validation

**Validator: `report_json_validator.py`**

Validates after report generation:
- JSON is valid
- Required sections present (exec_summary, findings, recommendations)
- All findings have required fields
- All vendors mentioned exist in our database
- No hallucinated statistics (all stats have sources)
- ROI calculations are mathematically correct

**Integration in `/execute` or report generation commands:**

```yaml
hooks:
  post_tool_use:
    - tools: [Write]
      match: "*.json"
      command: "python .claude/hooks/validators/report_json_validator.py $CLAUDE_FILE_PATH"
```

#### Phase 3: Vendor Data Validation

**Validator: `vendor_validator.py`**

Validates when adding/updating vendors:
- Required fields present (name, slug, pricing, features)
- Pricing is numeric and reasonable
- URLs are valid
- `verified_date` is recent (< 90 days)
- Industry tier assignments make sense

#### Phase 4: Command-Level Hooks

Add hooks to existing commands:

**`/execute` command:**
```yaml
hooks:
  stop:
    - command: "python .claude/hooks/validators/build_validator.py"
```

**`/plan-feature` command:**
```yaml
hooks:
  stop:
    - command: "python .claude/hooks/validators/plan_validator.py"
```

---

## Validator Template

```python
#!/usr/bin/env python3
"""
[Name] Validator

Validates [what it validates] for CRB Analyser.

Usage:
    python validator_name.py <file_path>

Returns:
    Exit 0 if valid
    Exit 1 if invalid (with actionable error message for agent)
"""

import sys
import json
from pathlib import Path
from datetime import datetime

LOG_FILE = Path(".claude/logs/validators/validator_name.log")

def log(message: str):
    """Log validation results."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat()
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def validate(file_path: str) -> tuple[bool, list[str]]:
    """
    Validate the file.

    Returns:
        (is_valid, list_of_issues)
    """
    issues = []

    # Validation logic here
    # ...

    return len(issues) == 0, issues

def main():
    if len(sys.argv) < 2:
        print("Usage: validator_name.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    is_valid, issues = validate(file_path)

    if is_valid:
        log(f"PASS: {file_path}")
        print(f"Validation passed for {file_path}")
        sys.exit(0)
    else:
        log(f"FAIL: {file_path} - {len(issues)} issues")
        # Format for agent to understand and fix
        print(f"Resolve these validation errors in {file_path}:")
        for issue in issues:
            print(f"  - {issue}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

---

## Key Quotes from Video

> "If you want your agents to accomplish loads of valuable work on your behalf, they must be able to validate their work."

> "A focused agent with one purpose outperforms an unfocused agent with many purposes."

> "We have edits from our agent that we know worked because we gave them the tools to validate their own work."

> "You don't work on your application anymore. You work on the agents that run your application."

> "Agents plus code beats agents."

---

## Anti-Patterns to Avoid

1. **Don't delegate learning** - Still understand what your agents do
2. **Don't skip reading docs** - Pasting docs into LLM without reading = vibe coding
3. **Don't use generalist agents** for specialized tasks
4. **Don't trust LLM reasoning alone** - Add deterministic validation
5. **Don't batch validations** - Validate per-step, not at end

---

## Implementation Priority

| Priority | Item | Impact |
|----------|------|--------|
| P0 | Report JSON validator | High - Core product quality |
| P0 | ROI math validator integration | High - Trust in numbers |
| P1 | Vendor data validator | Medium - Data quality |
| P1 | Command hooks for /execute | Medium - Development quality |
| P2 | Quiz response validator | Low - Input validation |

---

## Next Steps

1. Create `.claude/hooks/validators/` directory
2. Implement `report_json_validator.py`
3. Add hooks to report generation commands
4. Test with sample reports
5. Expand to other validators

---

## References

- Claude Code Hooks Documentation: https://docs.anthropic.com/en/docs/claude-code
- Existing `MathValidatorSkill`: `backend/src/skills/analysis/math_validator.py`
- Current hooks: `.claude/hooks/`
