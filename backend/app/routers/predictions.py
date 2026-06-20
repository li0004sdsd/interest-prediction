from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.auth import get_current_user
from app.services.prediction_service import build_prediction_result

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("/me", response_model=schemas.PredictionResult)
def get_my_predictions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return build_prediction_result(current_user.id, db)
