# Report Generation Skills

## Overview

These skills handle the generation of CRB report components. They provide consistent output formatting and can use expertise data for industry-calibrated insights.

## Available Skills

### exec_summary.py - Executive Summary Generation

**When to use:** At the start of report generation, after quiz/interview data is collected.

**What it does:**
- Generates compelling executive summary with key metrics
- Scores AI readiness, customer value, business health
- Identifies top opportunities and what NOT to do
- Uses expertise to calibrate scores to industry norms

**Input:** SkillContext with:
- `quiz_answers`: Raw quiz responses
- `industry`: Industry slug
- `expertise` (optional): IndustryExpertise for calibration

**Output:** Executive summary dict matching report schema

### three_options.py - Three Options Formatting

**When to use:** When generating recommendations.

**What it does:**
- Formats recommendations in consistent Three Options structure
- Ensures off-the-shelf, best-in-class, and custom options
- Calculates ROI with confidence adjustment

### verdict.py - Verdict Generation

**When to use:** After findings and recommendations are generated.

**What it does:**
- Generates honest Go/Caution/Wait/No recommendation
- Provides reasoning and next steps
- Uses expertise to calibrate expectations

## Design Principles

1. **Consistent Output**: Every skill produces the same schema
2. **Expertise Aware**: Skills use expertise when available
3. **Fallback Gracefully**: Works without expertise, just less calibrated
4. **Honest Assessments**: Never oversell, include "not recommended" items
