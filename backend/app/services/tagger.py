from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
from app.services.predictor import compute_scores
from app.models import BehaviorEvent
from app.schemas import InterestTag

HIGH_THRESHOLD = 70.0
MEDIUM_THRESHOLD = 40.0
LOW_THRESHOLD = 15.0


@dataclass(frozen=True)
class TagThresholdConfig:
    high: float = HIGH_THRESHOLD
    medium: float = MEDIUM_THRESHOLD
    low: float = LOW_THRESHOLD


_DEFAULT_CONFIG = TagThresholdConfig()

_LOW_TIER_CEILING = 1.0 / 3.0
_MEDIUM_TIER_CEILING = 2.0 / 3.0


def _normalize_confidence(score: float, tier_low: float, tier_high: float, conf_low: float, conf_high: float) -> float:
    if tier_high == tier_low:
        return conf_high
    ratio = (score - tier_low) / (tier_high - tier_low)
    ratio = max(0.0, min(1.0, ratio))
    return conf_low + ratio * (conf_high - conf_low)


def generate_tags(events: List[BehaviorEvent], config: Optional[TagThresholdConfig] = None) -> List[InterestTag]:
    cfg = config if config is not None else _DEFAULT_CONFIG
    scores = compute_scores(events)
    tags: List[InterestTag] = []
    for category, score in scores.items():
        if score >= cfg.high:
            confidence = _normalize_confidence(score, cfg.high, 100.0, _MEDIUM_TIER_CEILING, 1.0)
            tags.append(InterestTag(tag=f"High Interest: {category}", confidence=round(confidence, 3)))
        elif score >= cfg.medium:
            confidence = _normalize_confidence(score, cfg.medium, cfg.high, _LOW_TIER_CEILING, _MEDIUM_TIER_CEILING)
            tags.append(InterestTag(tag=f"Moderate Interest: {category}", confidence=round(confidence, 3)))
        elif score >= cfg.low:
            confidence = _normalize_confidence(score, cfg.low, cfg.medium, 0.0, _LOW_TIER_CEILING)
            tags.append(InterestTag(tag=f"Low Interest: {category}", confidence=round(confidence, 3)))
    tags.sort(key=lambda t: t.confidence, reverse=True)
    return tags
