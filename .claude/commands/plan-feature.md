# Plan Feature Command

Create a structured implementation plan for a feature. This plan will be used with `/execute` after a context reset.

## Usage

```
/plan-feature [feature description]
```

## IMPORTANT: Superpowers Integration

This command builds on superpowers skills. Follow this order:

### Step 1: Brainstorm First (Mandatory)

Before creating any plan, use the **superpowers:brainstorming** skill:
```
/superpowers:brainstorm
```

This refines the idea through Socratic questioning before jumping to implementation.

**Skip brainstorming ONLY if:**
- The feature is purely mechanical (rename, move, delete)
- User explicitly says "skip brainstorming, I know exactly what I want"

### Step 2: Create the Plan

After brainstorming is complete, use **superpowers:write-plan** to create the detailed implementation plan:
```
/superpowers:write-plan
```

This creates comprehensive implementation plans with exact file paths and verification steps.

## Project-Specific Additions

After running the superpowers skills, ensure the plan includes:

### CRB-Specific Checks
- [ ] Does this affect the quiz flow? (main conversion path)
- [ ] Does this touch report generation? (load report-quality.md reference)
- [ ] Does this involve vendors? (load vendor-management.md reference)
- [ ] What's the impact on existing pricing tiers?

### Output Location
Save to: `docs/plans/[YYYY-MM-DD]-[feature-slug].md`

### Plan Template Additions
Add these CRB-specific sections to the superpowers plan output:

```markdown
## CRB Context
- Affected user journey stage: [Quiz / Payment / Report / Dashboard]
- Industries impacted: [all / specific ones]
- Reference docs to load during execution: [list]

## Rollback Plan
If this fails, revert by: [specific instructions]
```

## After Plan Approval

Tell the user:
> "Plan saved to `docs/plans/[filename].md`.
> To execute: Start a new conversation, then run `/execute docs/plans/[filename].md`"

This ensures a context reset between planning and execution.
