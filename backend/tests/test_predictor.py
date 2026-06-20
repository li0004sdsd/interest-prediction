from __future__ import annotations
import logging
from datetime import datetime
from unittest.mock import patch
import pytest
from app.models import BehaviorEvent
from app.services.predictor import compute_scores, ACTION_MULTIPLIERS


def make_event(action: str, category: str, weight: float = 1.0) -> BehaviorEvent:
    return BehaviorEvent(
        id=1,
        user_id=1,
        action=action,
        category=category,
        weight=weight,
        created_at=datetime.utcnow(),
    )


class TestComputeScoresUnknownAction:

    def test_unknown_action_logs_warning(self, caplog):
        caplog.set_level(logging.WARNING, logger="app.services.predictor")
        events = [make_event("unknown_action", "technology")]
        result = compute_scores(events)
        assert "technology" in result
        assert result["technology"] == 100.0
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "WARNING"
        assert "unknown_action" in caplog.records[0].message
        assert "technology" in caplog.records[0].message

    def test_unknown_action_uses_default_multiplier_1_0(self):
        events = [
            make_event("unknown_action", "technology", weight=2.0),
            make_event("view", "sports", weight=2.0),
        ]
        result = compute_scores(events)
        assert result["technology"] == 100.0
        assert result["sports"] == 100.0

    def test_mixed_known_and_unknown_actions(self, caplog):
        caplog.set_level(logging.WARNING, logger="app.services.predictor")
        events = [
            make_event("purchase", "technology", weight=1.0),
            make_event("invalid_action", "sports", weight=1.0),
            make_event("click", "fashion", weight=1.0),
            make_event("another_bad_action", "food", weight=1.0),
        ]
        result = compute_scores(events)
        assert len(caplog.records) == 2
        assert "invalid_action" in caplog.records[0].message
        assert "another_bad_action" in caplog.records[1].message
        tech_score = 1.0 * ACTION_MULTIPLIERS["purchase"]
        sports_score = 1.0 * 1.0
        fashion_score = 1.0 * ACTION_MULTIPLIERS["click"]
        food_score = 1.0 * 1.0
        max_raw = max(tech_score, sports_score, fashion_score, food_score)
        assert result["technology"] == pytest.approx(tech_score / max_raw * 100, abs=0.01)

    def test_unknown_action_case_insensitive(self, caplog):
        caplog.set_level(logging.WARNING, logger="app.services.predictor")
        events = [make_event("UNKNOWN", "technology")]
        compute_scores(events)
        assert len(caplog.records) == 1
        assert "UNKNOWN" in caplog.records[0].message


class TestComputeScoresZeroWeightEdgeCase:

    def test_all_zero_weights_returns_all_zero_scores(self):
        events = [
            make_event("view", "technology", weight=0.0),
            make_event("click", "sports", weight=0.0),
            make_event("purchase", "fashion", weight=0.0),
        ]
        result = compute_scores(events)
        assert len(result) == 3
        assert result["technology"] == 0.0
        assert result["sports"] == 0.0
        assert result["fashion"] == 0.0
        assert all(v == 0.0 for v in result.values())

    def test_single_event_zero_weight(self):
        events = [make_event("view", "technology", weight=0.0)]
        result = compute_scores(events)
        assert result == {"technology": 0.0}

    def test_some_zero_weights_not_all(self):
        events = [
            make_event("view", "technology", weight=0.0),
            make_event("click", "sports", weight=2.0),
        ]
        result = compute_scores(events)
        assert result["technology"] == 0.0
        assert result["sports"] == 100.0

    def test_all_zero_weights_multiple_categories_same_score(self):
        events = [
            make_event("purchase", "technology", weight=0.0),
            make_event("add_to_cart", "sports", weight=0.0),
        ]
        result = compute_scores(events)
        assert result["technology"] == 0.0
        assert result["sports"] == 0.0

    def test_empty_events_returns_empty_dict(self):
        result = compute_scores([])
        assert result == {}


class TestComputeScoresNormalBehavior:

    def test_normal_scores_proportional(self):
        events = [
            make_event("purchase", "technology", weight=1.0),
            make_event("view", "sports", weight=2.0),
        ]
        tech_raw = 1.0 * ACTION_MULTIPLIERS["purchase"]
        sports_raw = 2.0 * ACTION_MULTIPLIERS["view"]
        max_raw = max(tech_raw, sports_raw)
        result = compute_scores(events)
        assert result["technology"] == pytest.approx(tech_raw / max_raw * 100, abs=0.01)
        assert result["sports"] == pytest.approx(sports_raw / max_raw * 100, abs=0.01)

    def test_action_case_insensitive(self):
        events = [
            make_event("PURCHASE", "technology", weight=1.0),
            make_event("View", "sports", weight=1.0),
        ]
        result_lower = compute_scores([make_event("purchase", "technology"), make_event("view", "sports")])
        result_upper = compute_scores(events)
        assert result_lower == result_upper

    def test_scores_rounded_to_two_decimals(self):
        events = [
            make_event("view", "technology", weight=3.0),
            make_event("view", "sports", weight=7.0),
        ]
        result = compute_scores(events)
        for v in result.values():
            assert isinstance(v, float)
            assert round(v, 2) == v
