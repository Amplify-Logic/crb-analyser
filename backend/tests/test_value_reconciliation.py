"""Tests for executive summary / value summary reconciliation."""

import pytest


def reconcile_totals(executive_summary: dict, value_summary: dict) -> dict:
    """
    Overwrite exec summary total_value_potential with value_summary actuals.

    This ensures the two sections of the report show consistent numbers.
    """
    if value_summary and value_summary.get("total"):
        vs_total = value_summary["total"]
        if vs_total.get("min", 0) > 0 or vs_total.get("max", 0) > 0:
            executive_summary["total_value_potential"] = {
                "min": vs_total["min"],
                "max": vs_total["max"],
                "projection_years": value_summary.get("projection_years", 3),
                "reconciled": True,
                "note": "Derived from detailed finding-level calculations",
            }
    return executive_summary


class TestValueReconciliation:
    def test_exec_summary_uses_value_summary_totals(self):
        """Exec summary total_value_potential must match value_summary.total."""
        exec_summary = {
            "total_value_potential": {"min": 85000, "max": 195000, "projection_years": 3},
        }
        value_summary = {
            "total": {"min": 264042, "max": 416475},
            "projection_years": 3,
        }
        result = reconcile_totals(exec_summary, value_summary)
        assert result["total_value_potential"]["min"] == 264042
        assert result["total_value_potential"]["max"] == 416475
        assert result["total_value_potential"]["reconciled"] is True

    def test_no_overwrite_when_value_summary_empty(self):
        """Don't overwrite if value_summary has no data."""
        exec_summary = {
            "total_value_potential": {"min": 85000, "max": 195000, "projection_years": 3},
        }
        value_summary = {"total": {"min": 0, "max": 0}}
        result = reconcile_totals(exec_summary, value_summary)
        assert result["total_value_potential"]["min"] == 85000  # unchanged

    def test_projection_years_preserved(self):
        """Projection years should come from value_summary."""
        exec_summary = {
            "total_value_potential": {"min": 10000, "max": 50000, "projection_years": 1},
        }
        value_summary = {
            "total": {"min": 100000, "max": 200000},
            "projection_years": 3,
        }
        result = reconcile_totals(exec_summary, value_summary)
        assert result["total_value_potential"]["projection_years"] == 3
