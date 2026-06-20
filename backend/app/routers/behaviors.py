from __future__ import annotations
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
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


@router.get("", response_model=schemas.PaginatedResponse[schemas.BehaviorEventOut])
def list_behaviors(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return (max 100)"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # SQLAlchemy .offset().limit() 用法说明:
    # - .offset(skip): 跳过前 skip 条记录，对应 SQL 的 OFFSET 子句
    # - .limit(limit): 最多返回 limit 条记录，对应 SQL 的 LIMIT 子句
    # - 两者结合实现分页查询，避免一次性加载全部数据到内存
    # - 注意：OFFSET 较大时性能会下降，生产环境建议改用基于游标(cursor)的分页
    query = db.query(models.BehaviorEvent).filter(
        models.BehaviorEvent.user_id == current_user.id,
        models.BehaviorEvent.is_deleted == False,
    )
    total = query.count()
    items = (
        query
        .order_by(models.BehaviorEvent.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return schemas.PaginatedResponse(total=total, items=items)


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
        .filter(
            models.BehaviorEvent.id == event_id,
            models.BehaviorEvent.user_id == current_user.id,
            models.BehaviorEvent.is_deleted == False,
        )
        .with_for_update()
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    event.is_deleted = True
    db.commit()


@router.post("/batch", response_model=List[schemas.BehaviorEventOut], status_code=status.HTTP_201_CREATED)
def create_behaviors_batch(
    payloads: List[schemas.BehaviorEventCreate],
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    events = []
    try:
        for idx, payload in enumerate(payloads):
            action_lower = payload.action.lower()
            category_lower = payload.category.lower()
            if action_lower not in VALID_ACTIONS:
                raise HTTPException(
                    status_code=422,
                    detail=f"Item {idx}: action must be one of: {', '.join(sorted(VALID_ACTIONS))}"
                )
            if category_lower not in VALID_CATEGORIES:
                raise HTTPException(
                    status_code=422,
                    detail=f"Item {idx}: category must be one of: {', '.join(sorted(VALID_CATEGORIES))}"
                )
            events.append(models.BehaviorEvent(
                user_id=current_user.id,
                category=category_lower,
                action=action_lower,
                weight=payload.weight,
            ))

        db.add_all(events)
        db.commit()
        for event in events:
            db.refresh(event)
        return events
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise
