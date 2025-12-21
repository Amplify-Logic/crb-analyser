"""
Chart Generation Service

Generates charts for PDF reports using matplotlib.
All charts are returned as base64-encoded PNG images.
"""

import io
import base64
import logging
from typing import List, Dict, Optional

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Wedge
import numpy as np

logger = logging.getLogger(__name__)

# Color palette matching CRB brand
COLORS = {
    "primary": "#6366f1",      # Indigo
    "secondary": "#8b5cf6",    # Purple
    "success": "#22c55e",      # Green
    "warning": "#f59e0b",      # Amber
    "danger": "#ef4444",       # Red
    "gray": "#64748b",         # Slate
    "light_gray": "#f1f5f9",   # Slate 100
    "customer_value": "#3b82f6",   # Blue
    "business_health": "#8b5cf6",  # Purple
}


def fig_to_base64(fig) -> str:
    """Convert matplotlib figure to base64 PNG string."""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    buf.seek(0)
    base64_str = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return base64_str


def create_gauge_chart(score: int, title: str = "AI Readiness Score") -> str:
    """
    Create a semi-circular gauge chart for AI readiness score.

    Args:
        score: Score value (0-100)
        title: Chart title

    Returns:
        Base64-encoded PNG image
    """
    try:
        fig, ax = plt.subplots(figsize=(4, 2.5), subplot_kw={'aspect': 'equal'})

        # Color ranges for the gauge
        colors = [COLORS["danger"], COLORS["warning"], COLORS["success"]]
        ranges = [(0, 40), (40, 70), (70, 100)]

        # Draw the gauge background arcs
        for (start_val, end_val), color in zip(ranges, colors):
            start_angle = 180 - (start_val / 100 * 180)
            end_angle = 180 - (end_val / 100 * 180)
            wedge = Wedge(
                center=(0.5, 0),
                r=0.4,
                theta1=end_angle,
                theta2=start_angle,
                width=0.15,
                facecolor=color,
                alpha=0.3
            )
            ax.add_patch(wedge)

        # Draw the score indicator
        score_angle = 180 - (score / 100 * 180)

        # Determine score color
        if score < 40:
            score_color = COLORS["danger"]
        elif score < 70:
            score_color = COLORS["warning"]
        else:
            score_color = COLORS["success"]

        # Draw active portion
        active_wedge = Wedge(
            center=(0.5, 0),
            r=0.4,
            theta1=score_angle,
            theta2=180,
            width=0.15,
            facecolor=score_color
        )
        ax.add_patch(active_wedge)

        # Draw needle
        needle_length = 0.3
        needle_x = 0.5 + needle_length * np.cos(np.radians(score_angle))
        needle_y = needle_length * np.sin(np.radians(score_angle))
        ax.annotate(
            '',
            xy=(needle_x, needle_y),
            xytext=(0.5, 0),
            arrowprops=dict(arrowstyle='->', color=COLORS["gray"], lw=2)
        )

        # Center circle
        center_circle = plt.Circle((0.5, 0), 0.05, color=COLORS["gray"])
        ax.add_patch(center_circle)

        # Score text
        ax.text(0.5, -0.15, str(score), fontsize=28, fontweight='bold',
                ha='center', va='top', color=score_color)
        ax.text(0.5, -0.32, 'out of 100', fontsize=10, ha='center',
                va='top', color=COLORS["gray"])

        # Title
        ax.text(0.5, 0.55, title, fontsize=12, fontweight='bold',
                ha='center', va='bottom', color=COLORS["gray"])

        ax.set_xlim(0, 1)
        ax.set_ylim(-0.4, 0.6)
        ax.axis('off')

        return fig_to_base64(fig)

    except Exception as e:
        logger.error(f"Failed to create gauge chart: {e}")
        return ""


def create_two_pillars_chart(
    customer_value: int,
    business_health: int,
) -> str:
    """
    Create horizontal bar chart for the Two Pillars scores.

    Args:
        customer_value: Customer Value score (1-10)
        business_health: Business Health score (1-10)

    Returns:
        Base64-encoded PNG image
    """
    try:
        fig, ax = plt.subplots(figsize=(6, 2))

        categories = ['Customer Value', 'Business Health']
        scores = [customer_value, business_health]
        colors = [COLORS["customer_value"], COLORS["business_health"]]

        # Create horizontal bars
        y_pos = np.arange(len(categories))
        bars = ax.barh(y_pos, scores, color=colors, height=0.5, alpha=0.8)

        # Background bars (max = 10)
        ax.barh(y_pos, [10, 10], color=COLORS["light_gray"], height=0.5, zorder=0)

        ax.set_xlim(0, 10)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(categories, fontsize=11, fontweight='bold')
        ax.set_xlabel('Score (1-10)', fontsize=10, color=COLORS["gray"])

        # Add score labels
        for bar, score in zip(bars, scores):
            ax.text(
                score + 0.2, bar.get_y() + bar.get_height() / 2,
                f'{score}/10',
                va='center', fontsize=12, fontweight='bold',
                color=COLORS["gray"]
            )

        # Remove spines
        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)
        ax.spines['bottom'].set_color(COLORS["light_gray"])
        ax.spines['left'].set_color(COLORS["light_gray"])

        plt.tight_layout()
        return fig_to_base64(fig)

    except Exception as e:
        logger.error(f"Failed to create two pillars chart: {e}")
        return ""


def create_value_timeline_chart(
    value_summary: Dict,
) -> str:
    """
    Create a line chart showing value projection over time.

    Args:
        value_summary: Dict with year1, year2, year3 values

    Returns:
        Base64-encoded PNG image
    """
    try:
        fig, ax = plt.subplots(figsize=(6, 3))

        # Extract values
        year1 = value_summary.get("year1", {})
        year2 = value_summary.get("year2", {})
        year3 = value_summary.get("year3", {})

        years = ['Year 1', 'Year 2', 'Year 3']

        # Get min/max values for range
        min_values = [
            year1.get("min", 0),
            year2.get("min", 0),
            year3.get("min", 0),
        ]
        max_values = [
            year1.get("max", 0),
            year2.get("max", 0),
            year3.get("max", 0),
        ]
        avg_values = [(min_val + max_val) / 2 for min_val, max_val in zip(min_values, max_values)]

        x = np.arange(len(years))

        # Plot range as filled area
        ax.fill_between(x, min_values, max_values, alpha=0.2, color=COLORS["primary"])

        # Plot average line
        ax.plot(x, avg_values, color=COLORS["primary"], linewidth=2, marker='o', markersize=8)

        # Add value labels
        for i, (min_val, max_val) in enumerate(zip(min_values, max_values)):
            ax.annotate(
                f'€{min_val/1000:.0f}k - €{max_val/1000:.0f}k',
                xy=(i, max_val),
                xytext=(0, 10),
                textcoords='offset points',
                ha='center',
                fontsize=9,
                color=COLORS["gray"]
            )

        ax.set_xticks(x)
        ax.set_xticklabels(years, fontsize=11)
        ax.set_ylabel('Value (€)', fontsize=10, color=COLORS["gray"])

        # Format y-axis
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'€{x/1000:.0f}k'))

        # Remove spines
        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)

        ax.set_title('3-Year Value Projection', fontsize=12, fontweight='bold',
                     color=COLORS["gray"], pad=20)

        plt.tight_layout()
        return fig_to_base64(fig)

    except Exception as e:
        logger.error(f"Failed to create value timeline chart: {e}")
        return ""


def create_roi_comparison_chart(
    recommendations: List[Dict],
    max_items: int = 5,
) -> str:
    """
    Create a bar chart comparing ROI across recommendations.

    Args:
        recommendations: List of recommendation dicts with roi_percentage
        max_items: Maximum number of items to show

    Returns:
        Base64-encoded PNG image
    """
    try:
        # Filter and sort by ROI
        valid_recs = [r for r in recommendations if r.get("roi_percentage")]
        sorted_recs = sorted(valid_recs, key=lambda x: x.get("roi_percentage", 0), reverse=True)[:max_items]

        if not sorted_recs:
            return ""

        fig, ax = plt.subplots(figsize=(6, max(2.5, len(sorted_recs) * 0.6)))

        # Extract data
        titles = [r.get("title", "")[:30] + "..." if len(r.get("title", "")) > 30 else r.get("title", "") for r in sorted_recs]
        rois = [r.get("roi_percentage", 0) for r in sorted_recs]

        # Color based on ROI value
        colors = []
        for roi in rois:
            if roi >= 200:
                colors.append(COLORS["success"])
            elif roi >= 100:
                colors.append(COLORS["primary"])
            else:
                colors.append(COLORS["warning"])

        y_pos = np.arange(len(titles))
        bars = ax.barh(y_pos, rois, color=colors, height=0.6, alpha=0.8)

        ax.set_yticks(y_pos)
        ax.set_yticklabels(titles, fontsize=9)
        ax.set_xlabel('ROI (%)', fontsize=10, color=COLORS["gray"])

        # Add ROI labels
        for bar, roi in zip(bars, rois):
            ax.text(
                roi + 5, bar.get_y() + bar.get_height() / 2,
                f'{roi}%',
                va='center', fontsize=10, fontweight='bold',
                color=COLORS["gray"]
            )

        # Remove spines
        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)

        ax.set_title('ROI by Recommendation', fontsize=12, fontweight='bold',
                     color=COLORS["gray"], pad=10)

        plt.tight_layout()
        return fig_to_base64(fig)

    except Exception as e:
        logger.error(f"Failed to create ROI comparison chart: {e}")
        return ""


def create_findings_breakdown_chart(
    findings: List[Dict],
) -> str:
    """
    Create a pie chart showing findings by priority.

    Args:
        findings: List of finding dicts with priority field

    Returns:
        Base64-encoded PNG image
    """
    try:
        # Count by priority
        priority_counts = {"high": 0, "medium": 0, "low": 0}
        for finding in findings:
            priority = finding.get("priority", "medium").lower()
            if priority in priority_counts:
                priority_counts[priority] += 1

        # Filter out zero values
        labels = []
        sizes = []
        colors = []
        priority_colors = {
            "high": COLORS["danger"],
            "medium": COLORS["warning"],
            "low": COLORS["success"],
        }

        for priority, count in priority_counts.items():
            if count > 0:
                labels.append(f'{priority.title()} ({count})')
                sizes.append(count)
                colors.append(priority_colors[priority])

        if not sizes:
            return ""

        fig, ax = plt.subplots(figsize=(4, 3))

        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            colors=colors,
            autopct='%1.0f%%',
            startangle=90,
            pctdistance=0.75,
        )

        # Style
        for autotext in autotexts:
            autotext.set_fontsize(10)
            autotext.set_fontweight('bold')

        ax.set_title('Findings by Priority', fontsize=12, fontweight='bold',
                     color=COLORS["gray"], pad=10)

        plt.tight_layout()
        return fig_to_base64(fig)

    except Exception as e:
        logger.error(f"Failed to create findings breakdown chart: {e}")
        return ""


async def generate_all_charts(report: Dict) -> Dict[str, str]:
    """
    Generate all charts for a report.

    Args:
        report: Full report data

    Returns:
        Dict mapping chart names to base64 PNG strings
    """
    charts = {}

    executive_summary = report.get("executive_summary", {})
    value_summary = report.get("value_summary", {})
    findings = report.get("findings", [])
    recommendations = report.get("recommendations", [])

    # AI Readiness Gauge
    ai_readiness = executive_summary.get("ai_readiness_score", 0)
    if ai_readiness:
        charts["readiness_gauge"] = create_gauge_chart(ai_readiness)

    # Two Pillars
    cv_score = executive_summary.get("customer_value_score", 0)
    bh_score = executive_summary.get("business_health_score", 0)
    if cv_score or bh_score:
        charts["two_pillars"] = create_two_pillars_chart(cv_score, bh_score)

    # Value Timeline
    if value_summary:
        charts["value_timeline"] = create_value_timeline_chart(value_summary)

    # ROI Comparison
    if recommendations:
        charts["roi_comparison"] = create_roi_comparison_chart(recommendations)

    # Findings Breakdown
    if findings:
        charts["findings_breakdown"] = create_findings_breakdown_chart(findings)

    return charts
