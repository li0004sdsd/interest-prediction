from __future__ import annotations
from collections import defaultdict
from typing import Dict, List
from app.models import BehaviorEvent

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
        multiplier = ACTION_MULTIPLIERS.get(event.action.lower(), 1.0)
        raw[event.category] += event.weight * multiplier
    if not raw:
        return {}
    max_score = max(raw.values())
    if max_score == 0:
        return {k: 0.0 for k in raw}
    return {k: round(v / max_score * 100, 2) for k, v in raw.items()}
