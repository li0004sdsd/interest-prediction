from __future__ import annotations
from typing import List
from app.services.predictor import compute_scores
from app.models import BehaviorEvent
from app.schemas import InterestTag

HIGH_THRESHOLD = 70.0
MEDIUM_THRESHOLD = 40.0
LOW_THRESHOLD = 15.0


def generate_tags(events: List[BehaviorEvent]) -> List[InterestTag]:
    scores = compute_scores(events)
    tags: List[InterestTag] = []
    for category, score in scores.items():
        if score >= HIGH_THRESHOLD:
            confidence = round(score / 100, 3)
            tags.append(InterestTag(tag=f"High Interest: {category}", confidence=confidence))
        elif score >= MEDIUM_THRESHOLD:
            confidence = round(score / 100, 3)
            tags.append(InterestTag(tag=f"Moderate Interest: {category}", confidence=confidence))
        elif score >= LOW_THRESHOLD:
            confidence = round(score / 100, 3)
            tags.append(InterestTag(tag=f"Low Interest: {category}", confidence=confidence))
    tags.sort(key=lambda t: t.confidence, reverse=True)
    return tags
