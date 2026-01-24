"""
진도 관련 Pydantic 스키마
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ProgressCreate(BaseModel):
    user_id: str
    book_id: Optional[str] = None
    lesson_id: Optional[str] = None
    unit_id: Optional[str] = None
    syncpoint_id: Optional[str] = None


class ProgressResponse(BaseModel):
    user_id: str
    book_id: Optional[str] = None
    lesson_id: Optional[str] = None
    unit_id: Optional[str] = None
    syncpoint_id: Optional[str] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
