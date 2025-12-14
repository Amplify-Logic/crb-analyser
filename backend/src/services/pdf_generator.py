"""
PDF Report Generator

Generates professional PDF reports using WeasyPrint.
Supports both audit-based and quiz-based reports with the two pillars methodology.
"""

import io
import logging
from datetime import datetime
from typing import Dict, Any

from jinja2 import Template

from src.config.supabase_client import get_async_supabase

logger = logging.getLogger(__name__)

# HTML Template for PDF report (Updated for Two Pillars methodology)
REPORT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @page {
            size: A4;
            margin: 2cm;
            @bottom-center {
                content: "Page " counter(page) " of " counter(pages);
                font-size: 10px;
                color: #666;
            }
        }

        body {
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-size: 11px;
            line-height: 1.6;
            color: #333;
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #6366f1;
        }

        .header h1 {
            color: #6366f1;
            font-size: 28px;
            margin: 0 0 10px 0;
        }

        .header .subtitle {
            color: #666;
            font-size: 14px;
        }

        .header .meta {
            margin-top: 15px;
            font-size: 12px;
            color: #666;
        }

        .score-card {
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: white;
            padding: 25px;
            border-radius: 12px;
            text-align: center;
            margin: 20px 0;
        }

        .score-card .score {
            font-size: 48px;
            font-weight: bold;
        }

        .score-card .score-label {
            font-size: 14px;
            opacity: 0.9;
        }

        .two-pillars {
            display: flex;
            justify-content: space-around;
            margin: 20px 0;
        }

        .pillar {
            text-align: center;
            padding: 20px;
            background: #f8fafc;
            border-radius: 8px;
            flex: 1;
            margin: 0 10px;
        }

        .pillar .pillar-score {
            font-size: 32px;
            font-weight: bold;
            color: #6366f1;
        }

        .pillar .pillar-label {
            font-size: 12px;
            color: #666;
        }

        .metrics-grid {
            display: flex;
            justify-content: space-around;
            margin: 20px 0;
        }

        .metric-box {
            text-align: center;
            padding: 15px;
            background: #f8fafc;
            border-radius: 8px;
            flex: 1;
            margin: 0 10px;
        }

        .metric-box .value {
            font-size: 24px;
            font-weight: bold;
            color: #6366f1;
        }

        .metric-box .label {
            font-size: 11px;
            color: #666;
        }

        .value-summary {
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }

        .value-summary h3 {
            color: #166534;
            margin: 0 0 15px 0;
        }

        .value-row {
            display: flex;
            justify-content: space-between;
            margin: 8px 0;
            padding: 5px 0;
            border-bottom: 1px solid #bbf7d0;
        }

        .value-row:last-child {
            border-bottom: none;
            font-weight: bold;
        }

        h2 {
            color: #6366f1;
            font-size: 18px;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 8px;
            margin-top: 30px;
        }

        h3 {
            color: #334155;
            font-size: 14px;
            margin-top: 20px;
        }

        .finding {
            background: #fff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
            page-break-inside: avoid;
        }

        .finding-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }

        .finding-title {
            font-weight: bold;
            font-size: 13px;
            color: #1e293b;
        }

        .score-badge {
            display: flex;
            gap: 10px;
        }

        .score-pill {
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: bold;
        }

        .score-customer { background: #dbeafe; color: #1d4ed8; }
        .score-business { background: #dcfce7; color: #16a34a; }

        .confidence-badge {
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 10px;
        }

        .confidence-high { background: #dcfce7; color: #16a34a; }
        .confidence-medium { background: #fef3c7; color: #d97706; }
        .confidence-low { background: #f1f5f9; color: #64748b; }

        .finding-description {
            color: #64748b;
            font-size: 11px;
        }

        .finding-value {
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #e2e8f0;
            display: flex;
            justify-content: space-between;
        }

        .value-item {
            text-align: center;
        }

        .value-amount {
            font-weight: bold;
            color: #16a34a;
        }

        .recommendation {
            background: #fff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
            page-break-inside: avoid;
        }

        .recommendation-title {
            font-weight: bold;
            font-size: 14px;
            color: #1e293b;
            margin-bottom: 8px;
        }

        .three-options {
            display: flex;
            gap: 10px;
            margin: 15px 0;
        }

        .option-card {
            flex: 1;
            padding: 12px;
            border-radius: 6px;
            font-size: 10px;
        }

        .option-a { background: #eff6ff; border: 1px solid #bfdbfe; }
        .option-b { background: #f0fdf4; border: 1px solid #bbf7d0; }
        .option-c { background: #fdf4ff; border: 1px solid #e9d5ff; }

        .option-name {
            font-weight: bold;
            font-size: 11px;
            margin-bottom: 5px;
        }

        .option-price {
            font-size: 12px;
            font-weight: bold;
            color: #6366f1;
        }

        .crb-table {
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
            font-size: 10px;
        }

        .crb-table th, .crb-table td {
            border: 1px solid #e2e8f0;
            padding: 6px;
            text-align: center;
        }

        .crb-table th {
            background: #f8fafc;
            color: #334155;
            font-weight: bold;
        }

        .crb-table .row-label {
            text-align: left;
            font-weight: bold;
            background: #f8fafc;
        }

        .roi-box {
            background: #6366f1;
            color: white;
            padding: 10px 15px;
            border-radius: 6px;
            display: inline-block;
            margin: 10px 0;
        }

        .roadmap-phase {
            background: #f8fafc;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
        }

        .roadmap-phase h4 {
            color: #6366f1;
            margin: 0 0 10px 0;
        }

        .roadmap-item {
            margin: 8px 0;
            padding-left: 15px;
            border-left: 2px solid #6366f1;
        }

        .not-recommended {
            background: #fef2f2;
            border: 1px solid #fecaca;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
        }

        .not-recommended h3 {
            color: #dc2626;
            margin: 0 0 10px 0;
        }

        .not-rec-item {
            margin: 8px 0;
            padding: 8px;
            background: white;
            border-radius: 4px;
        }

        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e2e8f0;
            text-align: center;
            font-size: 10px;
            color: #666;
        }

        .disclaimer {
            background: #f8fafc;
            padding: 15px;
            border-radius: 8px;
            font-size: 10px;
            color: #64748b;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>CRB Analysis Report</h1>
        <div class="subtitle">Cost / Risk / Benefit Analysis for AI Implementation</div>
        <div class="meta">
            Generated {{ report_date }} | {{ tier_name }}
        </div>
    </div>

    <div class="score-card">
        <div class="score">{{ ai_readiness_score }}</div>
        <div class="score-label">AI Readiness Score (out of 100)</div>
    </div>

    <div class="two-pillars">
        <div class="pillar">
            <div class="pillar-score">{{ customer_value_score }}/10</div>
            <div class="pillar-label">Customer Value Score</div>
        </div>
        <div class="pillar">
            <div class="pillar-score">{{ business_health_score }}/10</div>
            <div class="pillar-label">Business Health Score</div>
        </div>
    </div>

    <div class="metrics-grid">
        <div class="metric-box">
            <div class="value">{{ total_findings }}</div>
            <div class="label">Findings</div>
        </div>
        <div class="metric-box">
            <div class="value">{{ total_recommendations }}</div>
            <div class="label">Recommendations</div>
        </div>
        <div class="metric-box">
            <div class="value">€{{ "{:,.0f}".format(value_potential_min) }} - €{{ "{:,.0f}".format(value_potential_max) }}</div>
            <div class="label">3-Year Value Potential</div>
        </div>
    </div>

    {% if key_insight %}
    <div style="background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 15px; margin: 20px 0;">
        <strong>Key Insight:</strong> {{ key_insight }}
    </div>
    {% endif %}

    <div class="value-summary">
        <h3>Value Summary (3-Year Projection)</h3>
        <div class="value-row">
            <span>Value SAVED (Efficiency)</span>
            <span>€{{ "{:,.0f}".format(value_saved_min) }} - €{{ "{:,.0f}".format(value_saved_max) }}</span>
        </div>
        <div class="value-row">
            <span>Value CREATED (Growth)</span>
            <span>€{{ "{:,.0f}".format(value_created_min) }} - €{{ "{:,.0f}".format(value_created_max) }}</span>
        </div>
        <div class="value-row">
            <span>TOTAL POTENTIAL VALUE</span>
            <span>€{{ "{:,.0f}".format(total_value_min) }} - €{{ "{:,.0f}".format(total_value_max) }}</span>
        </div>
    </div>

    <h2>Key Findings</h2>
    {% for finding in findings %}
    <div class="finding">
        <div class="finding-header">
            <span class="finding-title">{{ finding.title }}</span>
            <div class="score-badge">
                <span class="score-pill score-customer">CV: {{ finding.customer_value_score or '?' }}</span>
                <span class="score-pill score-business">BH: {{ finding.business_health_score or '?' }}</span>
                <span class="confidence-badge confidence-{{ finding.confidence or 'medium' }}">
                    {{ (finding.confidence or 'medium')|title }}
                </span>
            </div>
        </div>
        <div class="finding-description">{{ finding.description }}</div>
        {% if finding.value_saved or finding.value_created %}
        <div class="finding-value">
            {% if finding.value_saved and finding.value_saved.annual_savings %}
            <div class="value-item">
                <div class="value-amount">€{{ "{:,.0f}".format(finding.value_saved.annual_savings) }}/yr</div>
                <div>Value Saved</div>
            </div>
            {% endif %}
            {% if finding.value_created and finding.value_created.potential_revenue %}
            <div class="value-item">
                <div class="value-amount">€{{ "{:,.0f}".format(finding.value_created.potential_revenue) }}</div>
                <div>Value Created</div>
            </div>
            {% endif %}
            <div class="value-item">
                <div>{{ finding.time_horizon|title }}</div>
                <div>Time Horizon</div>
            </div>
        </div>
        {% endif %}
    </div>
    {% endfor %}

    <h2>Recommendations</h2>
    {% for rec in recommendations %}
    <div class="recommendation">
        <div class="recommendation-title">{{ rec.title }}</div>
        <div class="finding-description">{{ rec.description }}</div>

        {% if rec.options %}
        <div class="three-options">
            {% if rec.options.off_the_shelf %}
            <div class="option-card option-a">
                <div class="option-name">Option A: Off-the-Shelf</div>
                <div>{{ rec.options.off_the_shelf.name }}</div>
                <div class="option-price">€{{ rec.options.off_the_shelf.monthly_cost }}/mo</div>
            </div>
            {% endif %}
            {% if rec.options.best_in_class %}
            <div class="option-card option-b">
                <div class="option-name">Option B: Best-in-Class</div>
                <div>{{ rec.options.best_in_class.name }}</div>
                <div class="option-price">€{{ rec.options.best_in_class.monthly_cost }}/mo</div>
            </div>
            {% endif %}
            {% if rec.options.custom_solution %}
            <div class="option-card option-c">
                <div class="option-name">Option C: Custom AI</div>
                <div>{{ rec.options.custom_solution.approach[:50] }}...</div>
                <div class="option-price">€{{ rec.options.custom_solution.estimated_cost.min }}-{{ rec.options.custom_solution.estimated_cost.max }}</div>
            </div>
            {% endif %}
        </div>
        {% endif %}

        {% if rec.crb_analysis %}
        <table class="crb-table">
            <tr>
                <th></th>
                <th>Short Term</th>
                <th>Mid Term</th>
                <th>Long Term</th>
            </tr>
            {% if rec.crb_analysis.cost %}
            <tr>
                <td class="row-label">Cost</td>
                <td>€{{ "{:,.0f}".format((rec.crb_analysis.cost.short_term.software or 0) + (rec.crb_analysis.cost.short_term.implementation or 0)) }}</td>
                <td>€{{ "{:,.0f}".format((rec.crb_analysis.cost.mid_term.software or 0) + (rec.crb_analysis.cost.mid_term.maintenance or 0)) }}</td>
                <td>€{{ "{:,.0f}".format((rec.crb_analysis.cost.long_term.software or 0) + (rec.crb_analysis.cost.long_term.upgrades or 0)) }}</td>
            </tr>
            {% endif %}
            {% if rec.crb_analysis.benefit %}
            <tr>
                <td class="row-label">Benefit</td>
                <td>€{{ "{:,.0f}".format((rec.crb_analysis.benefit.short_term.value_saved or 0) + (rec.crb_analysis.benefit.short_term.value_created or 0)) }}</td>
                <td>€{{ "{:,.0f}".format((rec.crb_analysis.benefit.mid_term.value_saved or 0) + (rec.crb_analysis.benefit.mid_term.value_created or 0)) }}</td>
                <td>€{{ "{:,.0f}".format((rec.crb_analysis.benefit.long_term.value_saved or 0) + (rec.crb_analysis.benefit.long_term.value_created or 0)) }}</td>
            </tr>
            {% endif %}
        </table>
        {% endif %}

        {% if rec.roi_percentage or rec.payback_months %}
        <div class="roi-box">
            {% if rec.roi_percentage %}ROI: {{ rec.roi_percentage }}%{% endif %}
            {% if rec.payback_months %} | Payback: {{ rec.payback_months }} months{% endif %}
        </div>
        {% endif %}

        {% if rec.our_recommendation %}
        <div style="margin-top: 10px; padding: 10px; background: #dcfce7; border-radius: 6px;">
            <strong>Our Recommendation:</strong> {{ rec.our_recommendation }} - {{ rec.recommendation_rationale }}
        </div>
        {% endif %}
    </div>
    {% endfor %}

    {% if not_recommended %}
    <div class="not-recommended">
        <h3>Not Recommended</h3>
        {% for item in not_recommended %}
        <div class="not-rec-item">
            <strong>{{ item.title }}</strong>: {{ item.reason }}
        </div>
        {% endfor %}
    </div>
    {% endif %}

    {% if roadmap %}
    <h2>Implementation Roadmap</h2>

    {% if roadmap.short_term %}
    <div class="roadmap-phase">
        <h4>Phase 1: Quick Wins (0-6 months)</h4>
        {% for item in roadmap.short_term %}
        <div class="roadmap-item">
            <strong>{{ item.title }}</strong><br>
            {{ item.description }}<br>
            <small>Timeline: {{ item.timeline }} | Expected: {{ item.expected_outcome }}</small>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    {% if roadmap.mid_term %}
    <div class="roadmap-phase">
        <h4>Phase 2: Foundation (6-18 months)</h4>
        {% for item in roadmap.mid_term %}
        <div class="roadmap-item">
            <strong>{{ item.title }}</strong><br>
            {{ item.description }}<br>
            <small>Timeline: {{ item.timeline }} | Expected: {{ item.expected_outcome }}</small>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    {% if roadmap.long_term %}
    <div class="roadmap-phase">
        <h4>Phase 3: Transformation (18+ months)</h4>
        {% for item in roadmap.long_term %}
        <div class="roadmap-item">
            <strong>{{ item.title }}</strong><br>
            {{ item.description }}<br>
            <small>Timeline: {{ item.timeline }} | Expected: {{ item.expected_outcome }}</small>
        </div>
        {% endfor %}
    </div>
    {% endif %}
    {% endif %}

    <div class="disclaimer">
        <strong>Disclaimer:</strong> This report contains estimates based on the information provided
        and industry benchmarks. Actual results may vary. All ROI calculations include stated assumptions.
        Recommendations scoring 6+ on BOTH Customer Value AND Business Health dimensions have been included.
        {% if methodology_notes and methodology_notes.assumptions %}
        <br><br><strong>Assumptions:</strong> {{ methodology_notes.assumptions | join('; ') }}
        {% endif %}
    </div>

    <div class="footer">
        <p>Generated by CRB Analyser | {{ report_date }}</p>
        <p>&copy; {{ year }} CRB Analyser. All rights reserved.</p>
    </div>
</body>
</html>
"""


async def generate_pdf_report(audit_id: str) -> io.BytesIO:
    """
    Generate a PDF report for an audit (legacy format).

    Returns a BytesIO buffer containing the PDF.
    """
    supabase = await get_async_supabase()

    # Get audit data
    audit_result = await supabase.table("audits").select(
        "*, clients(name, industry, company_size)"
    ).eq("id", audit_id).single().execute()

    if not audit_result.data:
        raise ValueError(f"Audit not found: {audit_id}")

    audit = audit_result.data
    client = audit.get("clients", {})

    # Get findings
    findings_result = await supabase.table("findings").select("*").eq(
        "audit_id", audit_id
    ).order("priority").execute()

    # Get recommendations
    recs_result = await supabase.table("recommendations").select("*").eq(
        "audit_id", audit_id
    ).order("priority").execute()

    # Get report summary
    report_result = await supabase.table("reports").select("*").eq(
        "audit_id", audit_id
    ).limit(1).execute()

    report = report_result.data[0] if report_result.data else {}
    executive_summary = report.get("executive_summary", {})

    # Prepare template data
    findings = findings_result.data or []
    recommendations = recs_result.data or []

    total_savings = sum(f.get("estimated_cost_saved", 0) or 0 for f in findings)

    template_data = {
        "tier_name": audit.get("tier", "Professional"),
        "report_date": datetime.now().strftime("%B %d, %Y"),
        "year": datetime.now().year,
        "ai_readiness_score": audit.get("ai_readiness_score", 0),
        "customer_value_score": executive_summary.get("customer_value_score", 5),
        "business_health_score": executive_summary.get("business_health_score", 5),
        "total_findings": len(findings),
        "total_recommendations": len(recommendations),
        "value_potential_min": total_savings * 0.8,
        "value_potential_max": total_savings * 1.2,
        "key_insight": executive_summary.get("key_insight", ""),
        "value_saved_min": total_savings * 0.8,
        "value_saved_max": total_savings,
        "value_created_min": 0,
        "value_created_max": total_savings * 0.3,
        "total_value_min": total_savings * 0.8,
        "total_value_max": total_savings * 1.5,
        "findings": findings,
        "recommendations": recommendations,
        "not_recommended": executive_summary.get("not_recommended", []),
        "roadmap": report.get("roadmap", {}),
        "methodology_notes": report.get("methodology_notes", {}),
    }

    return await _render_pdf(template_data)


async def generate_pdf_from_report_data(report: Dict[str, Any]) -> io.BytesIO:
    """
    Generate a PDF from report data (new quiz-based format).

    Args:
        report: Full report data dict from reports table

    Returns a BytesIO buffer containing the PDF.
    """
    executive_summary = report.get("executive_summary", {})
    value_summary = report.get("value_summary", {})
    findings = report.get("findings", [])
    recommendations = report.get("recommendations", [])
    roadmap = report.get("roadmap", {})
    methodology_notes = report.get("methodology_notes", {})

    # Calculate totals
    value_saved = value_summary.get("value_saved", {}).get("subtotal", {})
    value_created = value_summary.get("value_created", {}).get("subtotal", {})
    total_value = value_summary.get("total", {})

    tier_names = {
        "quick": "Quick Report",
        "full": "Full Analysis",
    }

    template_data = {
        "tier_name": tier_names.get(report.get("tier"), report.get("tier", "Report")),
        "report_date": datetime.now().strftime("%B %d, %Y"),
        "year": datetime.now().year,
        "ai_readiness_score": executive_summary.get("ai_readiness_score", 0),
        "customer_value_score": executive_summary.get("customer_value_score", 5),
        "business_health_score": executive_summary.get("business_health_score", 5),
        "total_findings": len(findings),
        "total_recommendations": len(recommendations),
        "value_potential_min": executive_summary.get("total_value_potential", {}).get("min", 0),
        "value_potential_max": executive_summary.get("total_value_potential", {}).get("max", 0),
        "key_insight": executive_summary.get("key_insight", ""),
        "value_saved_min": value_saved.get("min", 0),
        "value_saved_max": value_saved.get("max", 0),
        "value_created_min": value_created.get("min", 0),
        "value_created_max": value_created.get("max", 0),
        "total_value_min": total_value.get("min", 0),
        "total_value_max": total_value.get("max", 0),
        "findings": findings,
        "recommendations": recommendations,
        "not_recommended": executive_summary.get("not_recommended", []),
        "roadmap": roadmap,
        "methodology_notes": methodology_notes,
    }

    return await _render_pdf(template_data)


async def _render_pdf(template_data: Dict[str, Any]) -> io.BytesIO:
    """
    Render template data to PDF.

    Returns a BytesIO buffer.
    """
    template = Template(REPORT_TEMPLATE)
    html_content = template.render(**template_data)

    try:
        from weasyprint import HTML
        pdf_buffer = io.BytesIO()
        HTML(string=html_content).write_pdf(pdf_buffer)
        pdf_buffer.seek(0)
        return pdf_buffer
    except ImportError:
        logger.warning("WeasyPrint not available, returning HTML as fallback")
        # Fallback: return HTML as text (for development without WeasyPrint)
        html_buffer = io.BytesIO(html_content.encode('utf-8'))
        html_buffer.seek(0)
        return html_buffer
