from __future__ import annotations
import json
import logging
import time
from sqlalchemy.orm import Session
from app import models, schemas
from app.services.predictor import compute_scores
from app.services.tagger import generate_tags

logger = logging.getLogger(__name__)


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

    t0 = time.perf_counter()
    scores_map = compute_scores(events)
    compute_scores_duration_ms = (time.perf_counter() - t0) * 1000

    sorted_scores = sorted(scores_map.items(), key=lambda x: x[1], reverse=True)
    category_scores = [
        schemas.CategoryScore(category=cat, score=score, rank=i + 1)
        for i, (cat, score) in enumerate(sorted_scores)
    ]

    t1 = time.perf_counter()
    tags = generate_tags(events)
    generate_tags_duration_ms = (time.perf_counter() - t1) * 1000

    logger.info(
        json.dumps(
            {
                "event": "prediction_compute",
                "user_id": user_id,
                "total_events": len(events),
                "compute_scores_duration_ms": round(compute_scores_duration_ms, 3),
                "generate_tags_duration_ms": round(generate_tags_duration_ms, 3),
                "total_duration_ms": round(
                    (compute_scores_duration_ms + generate_tags_duration_ms), 3
                ),
            }
        )
    )

    return schemas.PredictionResult(
        user_id=user_id,
        username=user.username if user else "",
        scores=category_scores,
        tags=tags,
        total_events=len(events),
    )
