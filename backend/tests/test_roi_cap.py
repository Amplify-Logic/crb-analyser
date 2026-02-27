"""Tests for ROI capping logic in report generation."""

import pytest


def apply_confidence_adjustment(rec: dict, adj: dict) -> dict:
    """
    Simulate the confidence adjustment logic from report_service.py.

    This is extracted to test in isolation.
    """
    CONFIDENCE_FACTORS = {"high": 1.0, "medium": 0.85, "low": 0.70}
    ROI_CAP = 500

    if "roi_percentage" in rec and adj["adjusted"] != adj["original"]:
        original_roi = rec.get("roi_percentage", 0)
        factor = (
            CONFIDENCE_FACTORS.get(adj["adjusted"], 0.85)
            / CONFIDENCE_FACTORS.get(adj["original"], 0.85)
        )
        rec["roi_percentage_original"] = original_roi
        rec["roi_percentage"] = round(original_roi * factor, 1)

        # Re-apply cap after confidence adjustment
        if rec["roi_percentage"] > ROI_CAP:
            rec["roi_percentage"] = ROI_CAP
            rec["roi_capped"] = True

    return rec


class TestROICapping:
    def test_cap_not_exceeded_after_confidence_upgrade(self):
        """Confidence upgrade should NOT push ROI above 500% cap."""
        rec = {"roi_percentage": 500, "roi_capped": True}
        adj = {"original": "medium", "adjusted": "high", "reason": "test"}
        result = apply_confidence_adjustment(rec, adj)
        assert result["roi_percentage"] <= 500

    def test_confidence_downgrade_reduces_roi(self):
        """Confidence downgrade should reduce ROI below cap."""
        rec = {"roi_percentage": 500, "roi_capped": True}
        adj = {"original": "medium", "adjusted": "low", "reason": "test"}
        result = apply_confidence_adjustment(rec, adj)
        # low/medium = 0.70/0.85 = 0.823 → 500 * 0.823 = 411.8
        assert result["roi_percentage"] < 500
        assert result["roi_percentage"] == pytest.approx(411.8, abs=1)

    def test_uncapped_roi_stays_correct(self):
        """ROI below cap should adjust normally."""
        rec = {"roi_percentage": 200}
        adj = {"original": "medium", "adjusted": "high", "reason": "test"}
        result = apply_confidence_adjustment(rec, adj)
        # high/medium = 1.0/0.85 = 1.176 → 200 * 1.176 = 235.3
        assert result["roi_percentage"] == pytest.approx(235.3, abs=1)

    def test_original_preserved_before_adjustment(self):
        """roi_percentage_original should store the pre-adjustment value."""
        rec = {"roi_percentage": 300}
        adj = {"original": "medium", "adjusted": "high", "reason": "test"}
        result = apply_confidence_adjustment(rec, adj)
        assert result["roi_percentage_original"] == 300
