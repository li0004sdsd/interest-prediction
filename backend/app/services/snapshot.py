from __future__ import annotations
import logging
from sqlalchemy.orm import Session
from app import models
from app.services.predictor import compute_scores

logger = logging.getLogger(__name__)


def take_interest_snapshot(db: Session) -> int:
    users = db.query(models.User).all()
    success_count = 0
    for user in users:
        try:
            events = (
                db.query(models.BehaviorEvent)
                .filter(
                    models.BehaviorEvent.user_id == user.id,
                    models.BehaviorEvent.is_deleted == False,
                )
                .all()
            )
            scores = compute_scores(events)
            snapshot = models.InterestSnapshot(
                user_id=user.id,
                scores_json=scores,
            )
            db.add(snapshot)
            db.commit()
            success_count += 1
        except Exception as e:
            db.rollback()
            logger.error(
                "Failed to take interest snapshot for user %d: %s",
                user.id,
                str(e),
                exc_info=True,
            )
    logger.info(
        "Interest snapshot task completed: %d/%d users succeeded",
        success_count,
        len(users),
    )
    return success_count
