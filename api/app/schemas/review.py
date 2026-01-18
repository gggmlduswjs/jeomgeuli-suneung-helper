"""
복습 관련 Pydantic 스키마
"""
from pydantic import BaseModel
from typing import Optional


class ReviewQueueItem(BaseModel):
    unit_id: str
    lesson_id: Optional[str]
    reason: str  # "WRONG", "WRONG_REPEATED"
    priority: int


class ReviewComplete(BaseModel):
    user_id: str
    unit_id: str
