# Create PRD Command

Generate a Product Requirements Document from the current conversation.

## Usage

After discussing a feature/product idea, run:
```
/create-prd [output-path]
```

Default output: `docs/plans/PRD-[feature-slug].md`

## Instructions

### 1. Extract from Conversation

Pull the following from our discussion:
- Core problem being solved
- Target users
- Key features discussed
- Constraints mentioned
- Success criteria

### 2. Generate PRD

Create a markdown document with this structure:

```markdown
# [Product/Feature Name] - PRD

## Mission
One sentence describing what this does and why it matters.

## Target Users
- Primary: [who]
- Secondary: [who]

## Problem Statement
What pain does this solve? Be specific.

## In Scope
- Feature 1
- Feature 2
- Feature 3

## Out of Scope (Explicit)
- What we're NOT building
- What's deferred to later

## User Stories

### Story 1: [Name]
**As a** [user type]
**I want to** [action]
**So that** [benefit]

**Acceptance Criteria:**
- [ ] Criterion 1
- [ ] Criterion 2

### Story 2: [Name]
...

## Architecture Overview

### Frontend
- Pages/components needed
- State management approach

### Backend
- API endpoints needed
- Data models
- External integrations

### Database
- Tables/schemas affected
- Migrations needed

## Technical Decisions
| Decision | Choice | Rationale |
|----------|--------|-----------|
| [Area] | [Choice] | [Why] |

## Dependencies
- External services
- Other features that must exist first

## Success Metrics
- How do we know this worked?
- Measurable outcomes

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| [Risk] | [H/M/L] | [How to address] |

## Open Questions
- [ ] Question 1
- [ ] Question 2
```

### 3. Validate with User

Present the PRD summary and ask:
- "Does this capture what we discussed?"
- "Any missing requirements?"
- "Should anything move to out-of-scope?"

### 4. Save and Next Steps

After approval:
1. Save to specified path
2. Suggest: "Next, use `/plan-feature` to break this into implementation tasks"

## PRD Quality Checklist

- [ ] Mission is one clear sentence
- [ ] In/Out of scope are explicit
- [ ] User stories have acceptance criteria
- [ ] Technical decisions have rationale
- [ ] No time estimates (focus on WHAT)
- [ ] Open questions are captured (not ignored)
