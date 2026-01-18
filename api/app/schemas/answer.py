"""
정답/오답 관련 Pydantic 스키마
"""
from pydantic import BaseModel
from typing import Optional


class AnswerCreate(BaseModel):
    user_id: str
    unit_id: str
    selected: int
    is_correct: bool


class AnswerResponse(BaseModel):
    answer_id: str
    saved: bool
