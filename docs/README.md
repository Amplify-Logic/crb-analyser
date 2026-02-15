# Documentation Index

> For the primary development guide, see [CLAUDE.md](../CLAUDE.md) at project root.
> For task-specific reference, see [.claude/reference/](../.claude/reference/).

---

## Directory Structure

| Directory | Purpose | Contents |
|-----------|---------|----------|
| [architecture/](./architecture/) | Technical deep-dives | System architecture, observability, skills strategy, workflow guide |
| [marketing/](./marketing/) | Business & GTM | Go-to-market strategy, outreach plans, target industries |
| [plans/](./plans/) | Implementation plans | Feature design and implementation specs (dated `YYYY-MM-DD-slug.md`) |
| [handoffs/](./handoffs/) | Session continuity | Context handoff docs between development sessions |
| [audits/](./audits/) | Quality audits | Report quality, quiz, prompt, and benchmark audits |
| [prompts/](./prompts/) | Ad-hoc audit prompts | Prompts for system validation and quality checks |
| [video-insights/](./video-insights/) | Video content analysis | Transcripts and extracted insights from video sources |
| [reports/](./reports/) | Generated reports | Sample and analysis report outputs |
| [research/](./research/) | Research notes | Vendor and market research |
| [archive/](./archive/) | Historical docs | Deprecated/superseded documents |

## Key Files

| File | Purpose |
|------|---------|
| [evolution-log.md](./evolution-log.md) | System improvement tracking (updated via `/evolve`) |

## Architecture Files

| File | Topic |
|------|-------|
| [ARCHITECTURE.md](./architecture/ARCHITECTURE.md) | Three-layer system architecture |
| [OBSERVABILITY.md](./architecture/OBSERVABILITY.md) | Logging, monitoring, alerting |
| [SKILLS_STRATEGY.md](./architecture/SKILLS_STRATEGY.md) | Skills system design strategy |
| [SKILLS_INTEGRATION_MAP.md](./architecture/SKILLS_INTEGRATION_MAP.md) | How skills integrate across the system |
| [WORKFLOW-GUIDE.md](./architecture/WORKFLOW-GUIDE.md) | User workflow documentation |
| [hooks-explained-simply.md](./architecture/hooks-explained-simply.md) | Claude Code hooks explained |

## Marketing Files

| File | Topic |
|------|-------|
| [GTM_STRATEGY.md](./marketing/GTM_STRATEGY.md) | Go-to-market strategy |
| [COLD_OUTREACH_PLAN.md](./marketing/COLD_OUTREACH_PLAN.md) | Cold outreach playbook |
| [EMAIL_NURTURE_PLAN.md](./marketing/EMAIL_NURTURE_PLAN.md) | Email nurture sequences |
| [TARGET_INDUSTRIES.md](./marketing/TARGET_INDUSTRIES.md) | Industry selection and priorities |

## Conventions

- **Plans**: Named `YYYY-MM-DD-feature-slug.md`. Old plans archived to `plans/archive/`.
- **Handoffs**: Named `YYYY-MM-DD-topic.md`. Created at end of development sessions.
- **Audits**: Named `YYYY-MM-DD-audit-type.md`. Quality checks on specific systems.
