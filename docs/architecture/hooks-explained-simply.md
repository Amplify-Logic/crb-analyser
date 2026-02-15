# Hooks in Claude Code - A Simple Explanation

## The Core Idea in One Sentence

**Hooks are automatic checkpoints that run code BEFORE or AFTER your AI does something.**

---

## Analogy: The Factory Assembly Line

Imagine a factory where robots (AI agents) build products:

```
Robot picks up part → Robot installs part → Robot moves to next step
```

**Without hooks:** You hope the robot did it right. You check at the end.

**With hooks:** After EVERY step, a quality inspector automatically checks the work:

```
Robot picks up part → [INSPECTOR CHECKS] → Robot installs part → [INSPECTOR CHECKS] → ...
```

If the inspector finds a problem, they tell the robot: "This is wrong. Fix it."

The robot fixes it, and the inspector checks again. Loop until correct.

---

## What Are Hooks Technically?

Hooks are shell scripts or Python scripts that run automatically when certain events happen.

### Three Types of Hooks

| Hook Type | When It Runs | Use Case |
|-----------|--------------|----------|
| **Pre-Tool-Use** | BEFORE the AI uses a tool | Block dangerous commands, validate inputs |
| **Post-Tool-Use** | AFTER the AI uses a tool | Validate output, check for errors |
| **Stop** | When the agent finishes | Run final checks, cleanup |

### Example: Post-Tool-Use Hook

```
AI writes a JSON file
    ↓
Hook runs: python validate_json.py "$FILE_PATH"
    ↓
Validation fails? → Returns error message to AI
    ↓
AI reads error: "Missing 'source' field on line 42"
    ↓
AI fixes the file
    ↓
Hook runs again automatically
    ↓
Validation passes → Continue
```

---

## Why "Specialized" Hooks Matter

### Before (Global Hooks)

You could only set hooks that run for EVERYTHING:

```json
// settings.json - runs for ALL file writes
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write",
      "command": "python validate.py"
    }]
  }
}
```

**Problem:** The same validator runs whether you're writing a report, a config file, or a README. One size doesn't fit all.

### After (Specialized Hooks)

Now you can put hooks INSIDE specific commands/skills:

```yaml
# csv-edit.md command
---
name: csv-edit
hooks:
  post_tool_use:
    - tools: [Write, Edit]
      command: "python csv_validator.py $FILE_PATH"
---
```

**This validator ONLY runs when the csv-edit command writes files.**

A different command can have a different validator:
- `csv-edit` → runs CSV validator
- `report-generate` → runs report validator
- `vendor-update` → runs vendor validator

---

## The Key Insight: Deterministic vs LLM Validation

### LLM Validation (What we had before)

```
AI generates report → AI checks its own work → "Looks good to me!"
```

**Problem:** The AI might not catch its own mistakes. It's like asking a student to grade their own test.

### Deterministic Validation (With hooks)

```
AI generates report → Python script checks math → "Error: 5 + 5 ≠ 11"
```

**The Python script doesn't care what the AI thinks.** It runs the actual formula and checks if the numbers match. This is deterministic - same input always gives same output.

---

## Real Example from the Video

The video shows a CSV editing agent:

```yaml
# csv-edit command
hooks:
  post_tool_use:
    - tools: [Edit, Write, Read]
      command: "python csv_validator.py $FILE_PATH"
```

**What happens:**

1. User asks: "Add 3 rows to expenses.csv"
2. AI reads the CSV file → **Hook runs, validates CSV is readable**
3. AI edits the CSV file → **Hook runs, validates CSV is still valid**
4. Hook finds error: "Row 5 has wrong number of columns"
5. AI sees error message, fixes the row
6. Hook runs again → **Passes!**
7. AI continues

**The AI automatically fixed its mistake because the hook told it exactly what was wrong.**

---

## Why This Matters for CRB Analyser

### What We Implemented

| Validator | What It Checks |
|-----------|----------------|
| `report_validator.py` | Report has all required sections |
| `roi_math_validator.py` | Math calculations are correct |
| `vendor_validator.py` | Vendor data is complete |
| `benchmark_source_validator.py` | All stats have sources |
| `playbook_validator.py` | Task dependencies make sense |
| `industry_data_validator.py` | Industry folders are complete |

### Two Layers

1. **Claude Code Hooks** - Run during development when I write files
2. **Backend Validation Service** - Runs during real report generation

---

## The Trust Equation

```
More Validation → More Trust → Less Manual Review → More Time Saved
```

If every report is validated by deterministic code:
- You KNOW the math is correct
- You KNOW all sections exist
- You KNOW sources are cited

You don't have to check these things manually anymore.

---

## Summary

| Concept | Simple Explanation |
|---------|-------------------|
| **Hook** | Code that runs automatically before/after AI actions |
| **Pre-Tool-Use** | Check before AI does something |
| **Post-Tool-Use** | Check after AI does something |
| **Stop** | Check when AI finishes |
| **Specialized** | Different validators for different tasks |
| **Deterministic** | Code-based checks, not AI opinion |
| **Closed Loop** | Error → AI fixes → Check again → Repeat until correct |

The big idea: **Don't trust the AI to check itself. Use code to verify.**
