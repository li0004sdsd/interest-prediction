from __future__ import annotations
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.auth import get_current_user

router = APIRouter(prefix="/behaviors", tags=["behaviors"])

VALID_ACTIONS = {"view", "click", "search", "add_to_cart", "purchase", "scroll"}
VALID_CATEGORIES = {
    "technology", "sports", "fashion", "food", "travel",
    "health", "finance", "entertainment", "education", "gaming",
}


@router.get("", response_model=List[schemas.BehaviorEventOut])
def list_behaviors(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.BehaviorEvent)
        .filter(models.BehaviorEvent.user_id == current_user.id)
        .order_by(models.BehaviorEvent.created_at.desc())
        .all()
    )


@router.post("", response_model=schemas.BehaviorEventOut, status_code=status.HTTP_201_CREATED)
def create_behavior(
    payload: schemas.BehaviorEventCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if payload.action.lower() not in VALID_ACTIONS:
        raise HTTPException(status_code=422, detail=f"action must be one of: {', '.join(sorted(VALID_ACTIONS))}")
    if payload.category.lower() not in VALID_CATEGORIES:
        raise HTTPException(status_code=422, detail=f"category must be one of: {', '.join(sorted(VALID_CATEGORIES))}")
    event = models.BehaviorEvent(
        user_id=current_user.id,
        category=payload.category.lower(),
        action=payload.action.lower(),
        weight=payload.weight,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_behavior(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    event = (
        db.query(models.BehaviorEvent)
        .filter(models.BehaviorEvent.id == event_id, models.BehaviorEvent.user_id == current_user.id)
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    db.delete(event)
    db.commit()
