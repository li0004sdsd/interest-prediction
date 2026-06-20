from __future__ import annotations
from datetime import datetime
import pytest
from app.models import BehaviorEvent
from app.services.tagger import (
    generate_tags,
    TagThresholdConfig,
    HIGH_THRESHOLD,
    MEDIUM_THRESHOLD,
    LOW_THRESHOLD,
    _LOW_TIER_CEILING,
    _MEDIUM_TIER_CEILING,
)


def make_event(action: str, category: str, weight: float = 1.0) -> BehaviorEvent:
    return BehaviorEvent(
        id=1,
        user_id=1,
        action=action,
        category=category,
        weight=weight,
        created_at=datetime.utcnow(),
    )


class TestTagThresholdConfig:

    def test_default_thresholds_match_module_values(self):
        cfg = TagThresholdConfig()
        assert cfg.high == HIGH_THRESHOLD
        assert cfg.medium == MEDIUM_THRESHOLD
        assert cfg.low == LOW_THRESHOLD

    def test_custom_thresholds(self):
        cfg = TagThresholdConfig(high=80.0, medium=50.0, low=20.0)
        assert cfg.high == 80.0
        assert cfg.medium == 50.0
        assert cfg.low == 20.0

    def test_dataclass_is_frozen(self):
        cfg = TagThresholdConfig()
        with pytest.raises(Exception):
            cfg.high = 90.0


class TestGenerateTagsDefaultConfig:

    def test_high_interest_tag(self):
        events = [make_event("purchase", "technology", weight=10.0)]
        tags = generate_tags(events)
        assert len(tags) == 1
        assert tags[0].tag == "High Interest: technology"
        assert _MEDIUM_TIER_CEILING <= tags[0].confidence <= 1.0

    def test_medium_interest_tag(self):
        events = [
            make_event("purchase", "technology", weight=10.0),
            make_event("click", "sports", weight=20.0),
        ]
        cfg = TagThresholdConfig(high=95.0, medium=40.0, low=15.0)
        tags = generate_tags(events, config=cfg)
        medium_tag = next(t for t in tags if t.tag.startswith("Moderate"))
        assert medium_tag.tag == "Moderate Interest: sports"
        assert _LOW_TIER_CEILING <= medium_tag.confidence < _MEDIUM_TIER_CEILING

    def test_low_interest_tag(self):
        events = [
            make_event("purchase", "technology", weight=100.0),
            make_event("view", "sports", weight=10.0),
        ]
        cfg = TagThresholdConfig(high=95.0, medium=50.0, low=1.0)
        tags = generate_tags(events, config=cfg)
        low_tags = [t for t in tags if t.tag.startswith("Low")]
        assert len(low_tags) == 1
        assert low_tags[0].tag == "Low Interest: sports"
        assert 0.0 <= low_tags[0].confidence < _LOW_TIER_CEILING

    def test_tags_sorted_by_confidence_desc(self):
        events = [
            make_event("purchase", "technology", weight=10.0),
            make_event("scroll", "sports", weight=1.0),
        ]
        tags = generate_tags(events)
        confidences = [t.confidence for t in tags]
        assert confidences == sorted(confidences, reverse=True)

    def test_below_low_threshold_no_tags(self):
        events = [
            make_event("scroll", "technology", weight=1.0),
            make_event("purchase", "sports", weight=100.0),
        ]
        cfg = TagThresholdConfig(high=95.0, medium=80.0, low=70.0)
        tags = generate_tags(events, config=cfg)
        assert len(tags) == 1
        assert tags[0].tag.startswith("High")

    def test_empty_events_returns_empty_tags(self):
        tags = generate_tags([])
        assert tags == []


class TestGenerateTagsCustomConfig:

    def test_higher_high_threshold_moves_tag_to_medium(self):
        events = [
            make_event("purchase", "technology", weight=10.0),
            make_event("search", "sports", weight=20.0),
        ]
        cfg_default = TagThresholdConfig(high=70.0, medium=40.0, low=15.0)
        default_tags = generate_tags(events, config=cfg_default)
        default_tiers = {t.tag: t.tag.split(":")[0] for t in default_tags}
        cfg_strict = TagThresholdConfig(high=99.0, medium=40.0, low=15.0)
        strict_tags = generate_tags(events, config=cfg_strict)
        strict_tiers = {t.tag: t.tag.split(":")[0] for t in strict_tags}
        assert default_tiers != strict_tiers

    def test_lower_low_threshold_creates_more_tags(self):
        events = [
            make_event("scroll", "technology", weight=1.0),
            make_event("purchase", "sports", weight=10.0),
        ]
        cfg_strict = TagThresholdConfig(high=90.0, medium=70.0, low=60.0)
        strict_tags = generate_tags(events, config=cfg_strict)
        cfg_lenient = TagThresholdConfig(high=90.0, medium=50.0, low=5.0)
        lenient_tags = generate_tags(events, config=cfg_lenient)
        assert len(lenient_tags) >= len(strict_tags)

    def test_config_none_uses_defaults(self):
        events = [make_event("purchase", "technology", weight=10.0)]
        tags_none = generate_tags(events, config=None)
        tags_default = generate_tags(events)
        assert tags_none == tags_default


class TestGenerateTagsConfidenceNormalization:

    def test_all_confidences_in_zero_one_range(self):
        events = [
            make_event("purchase", "technology", weight=10.0),
            make_event("view", "sports", weight=1.0),
            make_event("scroll", "food", weight=1.0),
        ]
        for cfg in [
            TagThresholdConfig(),
            TagThresholdConfig(high=85.0, medium=50.0, low=20.0),
            TagThresholdConfig(high=95.0, medium=70.0, low=40.0),
        ]:
            tags = generate_tags(events, config=cfg)
            for tag in tags:
                assert 0.0 <= tag.confidence <= 1.0

    def test_high_tier_min_confidence(self):
        events = [make_event("view", "technology", weight=1.0)]
        cfg = TagThresholdConfig(high=70.0, medium=40.0, low=15.0)
        tags = generate_tags(events, config=cfg)
        if tags and tags[0].tag.startswith("High"):
            assert tags[0].confidence >= _MEDIUM_TIER_CEILING

    def test_medium_tier_confidence_bounds(self):
        events = [
            make_event("scroll", "technology", weight=1.0),
            make_event("view", "sports", weight=1.0),
        ]
        cfg = TagThresholdConfig(high=95.0, medium=40.0, low=15.0)
        tags = generate_tags(events, config=cfg)
        medium_tags = [t for t in tags if t.tag.startswith("Moderate")]
        for t in medium_tags:
            assert _LOW_TIER_CEILING <= t.confidence < _MEDIUM_TIER_CEILING

    def test_low_tier_max_confidence(self):
        events = [
            make_event("scroll", "technology", weight=1.0),
            make_event("purchase", "sports", weight=10.0),
        ]
        cfg = TagThresholdConfig(high=95.0, medium=70.0, low=15.0)
        tags = generate_tags(events, config=cfg)
        low_tags = [t for t in tags if t.tag.startswith("Low")]
        for t in low_tags:
            assert 0.0 <= t.confidence < _LOW_TIER_CEILING


class TestGenerateTagsBoundaryExtremeConfigs:

    def test_high_equals_100_extreme_config(self):
        cfg = TagThresholdConfig(high=100.0, medium=50.0, low=15.0)
        events = [make_event("view", "technology", weight=1.0)]
        tags = generate_tags(events, config=cfg)
        for tag in tags:
            assert 0.0 <= tag.confidence <= 1.0
        high_tag = next((t for t in tags if t.tag.startswith("High")), None)
        if high_tag is not None:
            assert high_tag.confidence == pytest.approx(1.0, abs=0.001)

    def test_high_equals_100_score_equals_100(self):
        cfg = TagThresholdConfig(high=100.0, medium=50.0, low=15.0)
        events = [make_event("purchase", "technology", weight=100.0)]
        tags = generate_tags(events, config=cfg)
        high_tag = next(t for t in tags if t.tag.startswith("High"))
        assert high_tag.confidence == pytest.approx(1.0, abs=0.001)

    def test_all_thresholds_equal_boundary(self):
        cfg = TagThresholdConfig(high=50.0, medium=50.0, low=50.0)
        events = [make_event("purchase", "technology", weight=10.0)]
        tags = generate_tags(events, config=cfg)
        for tag in tags:
            assert 0.0 <= tag.confidence <= 1.0

    def test_medium_equals_high_zero_range(self):
        cfg = TagThresholdConfig(high=70.0, medium=70.0, low=15.0)
        events = [make_event("view", "technology", weight=1.0)]
        tags = generate_tags(events, config=cfg)
        for tag in tags:
            assert 0.0 <= tag.confidence <= 1.0

    def test_low_equals_medium_zero_range(self):
        cfg = TagThresholdConfig(high=85.0, medium=40.0, low=40.0)
        events = [
            make_event("scroll", "technology", weight=1.0),
            make_event("purchase", "sports", weight=10.0),
        ]
        tags = generate_tags(events, config=cfg)
        for tag in tags:
            assert 0.0 <= tag.confidence <= 1.0

    def test_high_100_only_max_score_is_high(self):
        cfg = TagThresholdConfig(high=100.0, medium=40.0, low=15.0)
        events = [
            make_event("click", "technology", weight=1.0),
            make_event("purchase", "sports", weight=10.0),
        ]
        tags = generate_tags(events, config=cfg)
        high_tags = [t for t in tags if t.tag.startswith("High")]
        non_high_tags = [t for t in tags if not t.tag.startswith("High")]
        assert len(high_tags) == 1
        assert high_tags[0].confidence == pytest.approx(1.0, abs=0.001)
        for t in non_high_tags:
            assert t.confidence < 1.0

    def test_confidence_rounded_to_three_decimals(self):
        events = [make_event("view", "technology", weight=1.0)]
        tags = generate_tags(events)
        for tag in tags:
            assert isinstance(tag.confidence, float)
            assert round(tag.confidence, 3) == tag.confidence
