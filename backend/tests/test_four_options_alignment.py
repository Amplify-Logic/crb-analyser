"""Tests for four_options / AIOS recommendation alignment."""


def align_four_options_with_recommendation(rec: dict) -> dict:
    """
    Ensure four_options scores don't contradict our_recommendation.

    When four_options ranks a different option highest, add a note explaining
    why the AIOS recommendation overrides it.
    """
    four_options = rec.get("four_options", {})
    our_rec = rec.get("our_recommendation", "")
    if not four_options or not our_rec:
        return rec

    scores = four_options.get("scores", [])
    fo_recommended = four_options.get("recommended", "")

    # Map AIOS types to four_options types
    aios_to_four = {
        "connect_and_automate": "connect",
        "enhance_with_ai": "build",
        "targeted_upgrade": "buy",
    }
    equivalent_four = aios_to_four.get(our_rec, "")

    if fo_recommended and equivalent_four and fo_recommended != equivalent_four:
        four_options["recommendation_override"] = {
            "four_options_ranked": fo_recommended,
            "aios_recommendation": our_rec,
            "note": (
                f"The AIOS analysis recommends '{our_rec}' based on this company's "
                f"specific readiness profile. The four-options scoring ranked '{fo_recommended}' "
                f"higher on generic fit criteria."
            ),
        }
        # Update is_recommended flags
        for score in scores:
            if isinstance(score, dict):
                opt_val = score.get("option", "")
                score["is_recommended"] = (opt_val == equivalent_four)

    rec["four_options"] = four_options
    return rec


class TestFourOptionsAlignment:
    def test_override_note_when_disagreement(self):
        """When four_options and AIOS disagree, add override note."""
        rec = {
            "our_recommendation": "connect_and_automate",
            "four_options": {
                "recommended": "buy",
                "scores": [
                    {"option": "buy", "score": 97, "is_recommended": True},
                    {"option": "connect", "score": 85, "is_recommended": False},
                ],
            },
        }
        result = align_four_options_with_recommendation(rec)
        assert "recommendation_override" in result["four_options"]
        override = result["four_options"]["recommendation_override"]
        assert override["four_options_ranked"] == "buy"
        assert override["aios_recommendation"] == "connect_and_automate"

    def test_no_override_when_agreement(self):
        """When four_options and AIOS agree, no override note needed."""
        rec = {
            "our_recommendation": "targeted_upgrade",
            "four_options": {
                "recommended": "buy",
                "scores": [
                    {"option": "buy", "score": 97, "is_recommended": True},
                ],
            },
        }
        result = align_four_options_with_recommendation(rec)
        assert "recommendation_override" not in result["four_options"]

    def test_is_recommended_updated(self):
        """is_recommended should match the AIOS recommendation."""
        rec = {
            "our_recommendation": "connect_and_automate",
            "four_options": {
                "recommended": "buy",
                "scores": [
                    {"option": "buy", "score": 97, "is_recommended": True},
                    {"option": "connect", "score": 85, "is_recommended": False},
                ],
            },
        }
        result = align_four_options_with_recommendation(rec)
        scores = result["four_options"]["scores"]
        buy_score = next(s for s in scores if s["option"] == "buy")
        connect_score = next(s for s in scores if s["option"] == "connect")
        assert buy_score["is_recommended"] is False
        assert connect_score["is_recommended"] is True
