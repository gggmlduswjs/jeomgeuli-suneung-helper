"""
강(단원) 관련 Pydantic 스키마
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LessonResponse(BaseModel):
    lesson_id: str
    book_id: str
    index: int
    title: str
    unit_count: Optional[int] = 0
    question_count: Optional[int] = 0
    
    class Config:
        from_attributes = True
