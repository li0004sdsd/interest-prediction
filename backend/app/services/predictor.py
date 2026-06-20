from __future__ import annotations
import logging
from collections import defaultdict
from typing import Dict, List
from app.models import BehaviorEvent

logger = logging.getLogger(__name__)

ACTION_MULTIPLIERS: Dict[str, float] = {
    "purchase": 5.0,
    "add_to_cart": 3.0,
    "search": 2.0,
    "click": 1.5,
    "view": 1.0,
    "scroll": 0.5,
}


def compute_scores(events: List[BehaviorEvent]) -> Dict[str, float]:
    raw: Dict[str, float] = defaultdict(float)
    for event in events:
        action_lower = event.action.lower()
        multiplier = ACTION_MULTIPLIERS.get(action_lower)
        if multiplier is None:
            logger.warning(
                "Unknown action type '%s' encountered in behavior event (category: '%s', weight: %s), "
                "falling back to default multiplier 1.0. Valid actions are: %s",
                event.action, event.category, event.weight,
                ", ".join(sorted(ACTION_MULTIPLIERS.keys()))
            )
            multiplier = 1.0
        raw[event.category] += event.weight * multiplier
    if not raw:
        return {}
    max_score = max(raw.values())
    if max_score == 0:
        # Edge case: all events have zero weight, so every category scores 0.
        # Normalization is impossible (division by zero), so return explicit zeros
        # instead of failing silently. Callers should handle this by either
        # filtering zero-weight events or checking for uniform zero scores.
        return {k: 0.0 for k in raw}
    return {k: round(v / max_score * 100, 2) for k, v in raw.items()}
