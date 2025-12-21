"""
Pytest configuration and fixtures for CRB Analyser tests.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any


@pytest.fixture
def mock_quiz_data() -> Dict[str, Any]:
    """Sample quiz session data for testing."""
    return {
        "id": "test-quiz-123",
        "email": "test@example.com",
        "industry": "tech-companies",
        "answers": {
            "company_name": "Test Corp",
            "industry": "tech-companies",
            "company_size": "10-50",
            "annual_revenue": "500000-1000000",
            "main_challenges": ["manual_processes", "slow_support", "data_silos"],
            "current_tools": ["Google Workspace", "Slack", "Notion"],
            "tech_comfort": "high",
            "budget_range": "5000-10000",
            "timeline": "3-6 months",
            "pain_point_description": "We spend 40+ hours per week on repetitive customer support tasks.",
            "growth_goals": "Double revenue in 12 months while keeping team size stable.",
        },
        "results": {
            "ai_readiness_score": 72,
            "industry": "tech-companies",
        },
        "status": "completed",
    }


@pytest.fixture
def mock_findings() -> list:
    """Sample findings for testing."""
    return [
        {
            "id": "finding-001",
            "title": "Customer Support Automation Opportunity",
            "description": "40+ hours weekly on repetitive support tasks",
            "category": "efficiency",
            "customer_value_score": 8,
            "business_health_score": 7,
            "current_state": "Manual email responses",
            "value_saved": {
                "hours_per_week": 20,
                "hourly_rate": 50,
                "annual_savings": 52000
            },
            "confidence": "high",
            "sources": ["Quiz Q5: '40+ hours per week on repetitive tasks'"],
            "time_horizon": "short",
            "is_not_recommended": False,
        },
        {
            "id": "finding-002",
            "title": "Data Entry Automation",
            "description": "Manual data entry across systems",
            "category": "efficiency",
            "customer_value_score": 6,
            "business_health_score": 8,
            "confidence": "medium",
            "sources": ["Industry pattern: Tech companies average 15hrs/week on data entry"],
            "time_horizon": "mid",
            "is_not_recommended": False,
        },
        {
            "id": "finding-003",
            "title": "Content Generation",
            "description": "Marketing content creation bottleneck",
            "category": "growth",
            "customer_value_score": 7,
            "business_health_score": 6,
            "confidence": "medium",
            "sources": ["Quiz: Growth goals mention content scaling"],
            "time_horizon": "mid",
            "is_not_recommended": False,
        },
        {
            "id": "finding-not-001",
            "title": "Full AI Customer Replacement",
            "description": "Replacing all human support with AI",
            "category": "customer_experience",
            "customer_value_score": 3,
            "business_health_score": 4,
            "confidence": "high",
            "sources": ["Studies show 40% satisfaction drop"],
            "time_horizon": "short",
            "is_not_recommended": True,
            "why_not": "Customer satisfaction drops significantly",
            "what_instead": "Use AI-assisted human support",
        },
        {
            "id": "finding-not-002",
            "title": "Custom LLM Training",
            "description": "Training custom language models",
            "category": "efficiency",
            "customer_value_score": 4,
            "business_health_score": 3,
            "confidence": "high",
            "sources": ["Cost analysis shows negative ROI at current scale"],
            "time_horizon": "long",
            "is_not_recommended": True,
            "why_not": "Scale doesn't justify investment",
            "what_instead": "Use API-based models",
        },
        {
            "id": "finding-not-003",
            "title": "Autonomous Sales Bot",
            "description": "Fully autonomous sales process",
            "category": "growth",
            "customer_value_score": 2,
            "business_health_score": 5,
            "confidence": "medium",
            "sources": ["B2B sales require human relationship building"],
            "time_horizon": "long",
            "is_not_recommended": True,
            "why_not": "B2B requires human touch",
            "what_instead": "AI-assisted lead qualification",
        },
    ]


@pytest.fixture
def mock_recommendations() -> list:
    """Sample recommendations for testing."""
    return [
        {
            "id": "rec-001",
            "finding_id": "finding-001",
            "title": "AI Customer Support Assistant",
            "description": "Implement AI-powered support triage",
            "priority": "high",
            "why_it_matters": {
                "customer_value": "Faster response times",
                "business_health": "Reduce support costs by 40%"
            },
            "options": {
                "off_the_shelf": {
                    "name": "Intercom Fin",
                    "vendor": "Intercom",
                    "monthly_cost": 99,
                    "implementation_weeks": 2,
                    "implementation_cost": 500,
                    "pros": ["Quick setup", "No code"],
                    "cons": ["Monthly cost", "Limited customization"]
                },
                "best_in_class": {
                    "name": "Zendesk AI",
                    "vendor": "Zendesk",
                    "monthly_cost": 199,
                    "implementation_weeks": 4,
                    "implementation_cost": 2000,
                    "pros": ["Enterprise features"],
                    "cons": ["Higher cost"]
                },
                "custom_solution": {
                    "approach": "Build RAG-based support bot",
                    "estimated_cost": {"min": 5000, "max": 10000},
                    "monthly_running_cost": 50,
                    "implementation_weeks": 6,
                    "pros": ["Perfect fit", "Competitive advantage"],
                    "cons": ["Development time"],
                    "build_tools": ["Claude API", "Cursor", "Vercel"],
                    "model_recommendation": "Claude Sonnet 4",
                    "skills_required": ["Python", "API integration"],
                    "dev_hours_estimate": "60-100 hours"
                }
            },
            "our_recommendation": "custom_solution",
            "recommendation_rationale": "Tech team can execute, high ROI justifies investment",
            "roi_percentage": 350,
            "payback_months": 4,
            "assumptions": ["50 EUR hourly rate", "20 hours saved weekly"]
        }
    ]


@pytest.fixture
def mock_report_data(mock_quiz_data, mock_findings, mock_recommendations) -> Dict[str, Any]:
    """Complete mock report data for validation testing."""
    return {
        "id": "report-test-123",
        "quiz_session_id": mock_quiz_data["id"],
        "tier": "quick",
        "status": "completed",
        "executive_summary": {
            "ai_readiness_score": 72,
            "customer_value_score": 7,
            "business_health_score": 7,
            "key_insight": "Strong AI adoption potential with clear quick wins",
            "total_value_potential": {"min": 50000, "max": 100000, "projection_years": 3},
            "top_opportunities": [
                {"title": "Support Automation", "value_potential": "€20K-40K", "time_horizon": "short"}
            ],
            "not_recommended": [
                {"title": "Full AI Replacement", "reason": "Customer satisfaction risk"}
            ],
            "recommended_investment": {"year_1_min": 5000, "year_1_max": 15000},
            "verdict": {
                "recommendation": "proceed",
                "headline": "Go For It",
                "subheadline": "Strong fundamentals",
                "reasoning": ["High readiness score", "Clear ROI"],
                "confidence": "high",
                "color": "green"
            }
        },
        "findings": mock_findings,
        "recommendations": mock_recommendations,
        "roadmap": {
            "short_term": [{"title": "Support Bot", "timeline": "Week 1-4"}],
            "mid_term": [{"title": "Data Integration", "timeline": "Month 3-6"}],
            "long_term": []
        },
        "value_summary": {
            "value_saved": {"hours_per_week": 20, "annual_savings": 52000},
            "value_created": {"potential_revenue": 20000},
            "total": {"min": 50000, "max": 100000}
        },
        "methodology_notes": {
            "data_sources": ["Quiz responses"],
            "assumptions": ["50 EUR hourly rate"],
            "limitations": ["Self-reported data"]
        }
    }


@pytest.fixture
def mock_supabase():
    """Mock Supabase client."""
    mock = AsyncMock()
    mock.table.return_value.select.return_value.eq.return_value.single.return_value.execute = AsyncMock()
    mock.table.return_value.insert.return_value.execute = AsyncMock()
    mock.table.return_value.update.return_value.eq.return_value.execute = AsyncMock()
    return mock


@pytest.fixture
def mock_anthropic_response():
    """Mock Anthropic API response."""
    response = MagicMock()
    response.content = [MagicMock(text='{"test": "response"}')]
    response.usage = MagicMock(input_tokens=100, output_tokens=50)
    return response
