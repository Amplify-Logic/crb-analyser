"""
PDF Report Generator

Generates professional PDF reports using WeasyPrint.
"""

import io
import logging
from datetime import datetime
from typing import Dict, Any

from jinja2 import Template

from src.config.supabase_client import get_async_supabase

logger = logging.getLogger(__name__)

# HTML Template for PDF report
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

        .header .client-info {
            margin-top: 15px;
            font-size: 12px;
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

        .finding-priority {
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: bold;
        }

        .priority-high { background: #fee2e2; color: #dc2626; }
        .priority-medium { background: #fef3c7; color: #d97706; }
        .priority-low { background: #dcfce7; color: #16a34a; }

        .finding-description {
            color: #64748b;
            font-size: 11px;
        }

        .finding-impact {
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #e2e8f0;
            display: flex;
            justify-content: space-between;
        }

        .impact-item {
            text-align: center;
        }

        .impact-value {
            font-weight: bold;
            color: #16a34a;
        }

        .recommendation {
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
            page-break-inside: avoid;
        }

        .recommendation-title {
            font-weight: bold;
            font-size: 13px;
            color: #166534;
            margin-bottom: 8px;
        }

        .recommendation-details {
            display: flex;
            justify-content: space-between;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #bbf7d0;
        }

        .detail-item {
            text-align: center;
        }

        .detail-label {
            font-size: 9px;
            color: #666;
        }

        .detail-value {
            font-weight: bold;
            color: #166534;
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
        <div class="client-info">
            <strong>{{ client_name }}</strong><br>
            {{ client_industry }} | Generated {{ report_date }}
        </div>
    </div>

    <div class="score-card">
        <div class="score">{{ ai_readiness_score }}</div>
        <div class="score-label">AI Readiness Score (out of 100)</div>
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
            <div class="value">€{{ "{:,.0f}".format(total_savings) }}</div>
            <div class="label">Potential Annual Savings</div>
        </div>
    </div>

    <h2>Executive Summary</h2>
    <p>{{ executive_summary }}</p>

    <h2>Key Findings</h2>
    {% for finding in findings %}
    <div class="finding">
        <div class="finding-header">
            <span class="finding-title">{{ finding.title }}</span>
            <span class="finding-priority priority-{{ 'high' if finding.priority <= 2 else 'medium' if finding.priority <= 4 else 'low' }}">
                {{ 'High' if finding.priority <= 2 else 'Medium' if finding.priority <= 4 else 'Low' }} Priority
            </span>
        </div>
        <div class="finding-description">{{ finding.description }}</div>
        {% if finding.estimated_cost_saved or finding.estimated_hours_saved %}
        <div class="finding-impact">
            {% if finding.estimated_hours_saved %}
            <div class="impact-item">
                <div class="impact-value">{{ finding.estimated_hours_saved }} hrs/mo</div>
                <div>Time Saved</div>
            </div>
            {% endif %}
            {% if finding.estimated_cost_saved %}
            <div class="impact-item">
                <div class="impact-value">€{{ "{:,.0f}".format(finding.estimated_cost_saved) }}/yr</div>
                <div>Cost Saved</div>
            </div>
            {% endif %}
            {% if finding.confidence_level %}
            <div class="impact-item">
                <div class="impact-value">{{ finding.confidence_level }}%</div>
                <div>Confidence</div>
            </div>
            {% endif %}
        </div>
        {% endif %}
    </div>
    {% endfor %}

    <h2>Recommendations</h2>
    {% for rec in recommendations %}
    <div class="recommendation">
        <div class="recommendation-title">{{ rec.title }}</div>
        <div class="finding-description">{{ rec.description }}</div>
        <div class="recommendation-details">
            {% if rec.vendor_name %}
            <div class="detail-item">
                <div class="detail-label">Vendor</div>
                <div class="detail-value">{{ rec.vendor_name }}</div>
            </div>
            {% endif %}
            {% if rec.implementation_cost %}
            <div class="detail-item">
                <div class="detail-label">Setup Cost</div>
                <div class="detail-value">€{{ "{:,.0f}".format(rec.implementation_cost) }}</div>
            </div>
            {% endif %}
            {% if rec.monthly_cost %}
            <div class="detail-item">
                <div class="detail-label">Monthly Cost</div>
                <div class="detail-value">€{{ "{:,.0f}".format(rec.monthly_cost) }}/mo</div>
            </div>
            {% endif %}
            {% if rec.roi_percentage %}
            <div class="detail-item">
                <div class="detail-label">ROI</div>
                <div class="detail-value">{{ rec.roi_percentage }}%</div>
            </div>
            {% endif %}
            {% if rec.payback_months %}
            <div class="detail-item">
                <div class="detail-label">Payback</div>
                <div class="detail-value">{{ rec.payback_months }} months</div>
            </div>
            {% endif %}
        </div>
    </div>
    {% endfor %}

    <div class="disclaimer">
        <strong>Disclaimer:</strong> This report contains estimates based on the information provided in the intake questionnaire
        and industry benchmarks. Actual results may vary. Findings marked as "AI-estimated" are based on general industry
        patterns and should be validated with actual business data. All ROI calculations include stated assumptions.
    </div>

    <div class="footer">
        <p>Generated by CRB Analyser | {{ report_date }}</p>
        <p>© {{ year }} CRB Analyser. All rights reserved.</p>
    </div>
</body>
</html>
"""


async def generate_pdf_report(audit_id: str) -> io.BytesIO:
    """
    Generate a PDF report for an audit.

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
        "client_name": client.get("name", "Client"),
        "client_industry": client.get("industry", "").replace("_", " ").title(),
        "report_date": datetime.now().strftime("%B %d, %Y"),
        "year": datetime.now().year,
        "ai_readiness_score": audit.get("ai_readiness_score", 0),
        "total_findings": len(findings),
        "total_recommendations": len(recommendations),
        "total_savings": total_savings,
        "executive_summary": executive_summary.get(
            "ai_readiness_summary",
            "This report provides a comprehensive analysis of AI implementation opportunities "
            "based on your intake questionnaire responses and industry benchmarks."
        ),
        "findings": findings,
        "recommendations": recommendations,
    }

    # Render HTML
    template = Template(REPORT_TEMPLATE)
    html_content = template.render(**template_data)

    # Generate PDF
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
