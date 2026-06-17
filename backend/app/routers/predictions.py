from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.auth import get_current_user
from app.services.predictor import compute_scores
from app.services.tagger import generate_tags

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("/me", response_model=schemas.PredictionResult)
def get_my_predictions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    events = (
        db.query(models.BehaviorEvent)
        .filter(models.BehaviorEvent.user_id == current_user.id)
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
        user_id=current_user.id,
        username=current_user.username,
        scores=category_scores,
        tags=tags,
        total_events=len(events),
    )
