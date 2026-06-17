from __future__ import annotations
from datetime import datetime
from typing import List
from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str


class BehaviorEventCreate(BaseModel):
    category: str
    action: str
    weight: float = 1.0


class BehaviorEventOut(BaseModel):
    id: int
    category: str
    action: str
    weight: float
    created_at: datetime

    model_config = {"from_attributes": True}


class CategoryScore(BaseModel):
    category: str
    score: float
    rank: int


class InterestTag(BaseModel):
    tag: str
    confidence: float


class PredictionResult(BaseModel):
    user_id: int
    username: str
    scores: List[CategoryScore]
    tags: List[InterestTag]
    total_events: int
