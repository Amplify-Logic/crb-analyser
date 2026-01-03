# CRB Analyser

AI-powered Cost/Risk/Benefit Analysis for passion-driven service businesses.

## What We Do

We deliver consultant-quality business audits at 1/10th the cost:
- AI implementation opportunities ranked by ROI
- Process automation recommendations
- Real vendor pricing comparisons
- Transparent ROI calculations with confidence scoring
- Professional PDF reports

## Target Market

Passion-driven service businesses ($500K-$20M revenue):
- **Primary:** Professional Services, Home Services, Dental
- **Secondary:** Recruiting, Coaching, Veterinary
- **Markets:** Netherlands, Germany, UK, Ireland

## Quick Start

```bash
# Backend (port 8383)
cd backend && source venv/bin/activate && uvicorn src.main:app --reload --port 8383

# Frontend (port 5174)
cd frontend && npm run dev

# Redis (required)
brew services start redis
```

## Documentation

### Core (read these first)
| Doc | Purpose |
|-----|---------|
| [CLAUDE.md](./CLAUDE.md) | **Development guide** - How to code |
| [PRODUCT.md](./PRODUCT.md) | **Domain model** - What it does |
| [STRATEGY.md](./STRATEGY.md) | **Business context** - Why we build |

### Reference
| Doc | Purpose |
|-----|---------|
| [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) | System architecture deep-dive |
| [SETUP_PROMPT.md](./SETUP_PROMPT.md) | Full setup instructions |
| [PRD.md](./PRD.md) | Original product requirements |

### Session Continuity
| Doc | Purpose |
|-----|---------|
| [docs/handoffs/](./docs/handoffs/) | Handoff documents between sessions |
| [docs/plans/](./docs/plans/) | Implementation plans |

## Tech Stack

| Layer | Tech |
|-------|------|
| Backend | FastAPI + Python 3.12 |
| Frontend | React 18 + Vite + TypeScript |
| Database | Supabase (PostgreSQL + RLS) |
| Cache | Redis |
| AI | Anthropic Claude API |
| Payments | Stripe |
| Deploy | Railway |

## Project Structure

```
crb-analyser/
├── backend/
│   ├── src/
│   │   ├── agents/         # CRB analysis agent
│   │   ├── config/         # Settings, model routing
│   │   ├── expertise/      # Self-improving system (our moat)
│   │   ├── knowledge/      # Industry data (our moat)
│   │   ├── routes/         # API endpoints
│   │   ├── services/       # Business logic
│   │   ├── skills/         # Agent capabilities
│   │   └── tools/          # Agent tools
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── contexts/
│   │   ├── pages/
│   │   └── services/
├── docs/                   # Extended documentation
└── *.md                    # Core docs
```

## License

Proprietary - Amplify Logic
