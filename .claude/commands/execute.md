# Execute Command

Execute a structured plan with minimal context overhead.

## Usage

```
/execute docs/plans/[plan-file].md
```

## IMPORTANT: Superpowers Integration

This command wraps **superpowers:execute-plan** with CRB-specific context.

### Execution Flow

1. **Read the plan file** - This is your single source of truth
2. **Load reference docs** if specified in the plan's "CRB Context" section
3. **Use superpowers:execute-plan** for the actual execution:
   ```
   /superpowers:execute-plan
   ```

### Superpowers Skills to Use During Execution

| When | Use This Skill |
|------|----------------|
| Writing any code | `superpowers:test-driven-development` (TDD) |
| Writing tests | `superpowers:testing-anti-patterns` |
| Encountering a bug | `superpowers:systematic-debugging` |
| Before claiming "done" | `superpowers:verification-before-completion` |
| After completing a major step | `superpowers:requesting-code-review` |

## Context Reset

This command is designed to run AFTER a context reset. The plan file is your single source of truth. This keeps context light for better reasoning.

**Do NOT read CLAUDE.md, PRODUCT.md** unless the plan explicitly requires it.

## Execution Rules

- **Stay focused** - Only do what the plan says
- **No scope creep** - Don't add improvements not in the plan
- **TDD always** - Write test first, watch it fail, then implement
- **Verify each step** - Use verification-before-completion skill
- **Stop on blockers** - Report issues instead of improvising

## If Something Goes Wrong

1. Use **superpowers:systematic-debugging** to find root cause
2. Use **superpowers:root-cause-tracing** for deep issues
3. Note exactly what failed and which task/step
4. Report to user with specifics
5. Do NOT attempt fixes outside the plan scope

## After Completion

1. Run **superpowers:verification-before-completion**
2. Summarize:
   - Tasks completed
   - Tests passing
   - Any issues encountered
3. Remind user to run `/evolve` if any bugs were fixed
