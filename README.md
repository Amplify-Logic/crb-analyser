# CRB Analyser

AI-powered Cost/Risk/Benefit Analysis for Business

## Overview

CRB Analyser delivers consultant-quality business audits at 1/10th the cost. We analyze your business operations and provide:

- AI implementation opportunities ranked by ROI
- Process automation recommendations
- Real vendor pricing comparisons
- Transparent ROI calculations
- Professional PDF reports

## Target Market

Mid-market professional services (20-200 employees):
- Marketing/Creative Agencies
- Legal Firms
- Accounting Firms
- Recruitment Agencies

## Tech Stack

- **Backend:** FastAPI + Python 3.12
- **Frontend:** React + Vite + TypeScript
- **Database:** Supabase (PostgreSQL)
- **AI:** Anthropic Claude API
- **Payments:** Stripe

## Getting Started

See `SETUP_PROMPT.md` for complete setup instructions.

### Quick Start

```bash
# Backend (port 8383)
cd backend && uvicorn src.main:app --reload --port 8383

# Frontend (port 5174)
cd frontend && npm run dev
```

## Documentation

- `CLAUDE.md` - Development guide and patterns
- `PRD.md` - Product requirements
- `BOOTSTRAP.md` - Technical specification
- `SETUP_PROMPT.md` - Full setup instructions

## License

Proprietary - Amplify Logic
