from __future__ import annotations
from sqlalchemy.orm import Session
from app import models, schemas
from app.services.predictor import compute_scores
from app.services.tagger import generate_tags


def build_prediction_result(user_id: int, db: Session) -> schemas.PredictionResult:
    user = db.query(models.User).filter(models.User.id == user_id).first()
    events = (
        db.query(models.BehaviorEvent)
        .filter(
            models.BehaviorEvent.user_id == user_id,
            models.BehaviorEvent.is_deleted == False,
        )
        .all()
    )
    scores_map = compute_scores(events)
    sorted_scores = sorted(scores_map.items(), key=lambda x: x[1], reverse=True)
    category_scores = [
        schemas.CategoryScore(category=cat, score=score, rank=i + 1)
        for i, (cat, score) in enumerate(sorted_scores)
    ]
    tags = generate_tags(events)
    return schemas.PredictionResult(
        user_id=user_id,
        username=user.username if user else "",
        scores=category_scores,
        tags=tags,
        total_events=len(events),
    )
