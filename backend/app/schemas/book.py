"""
교재 관련 Pydantic 스키마
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.infrastructure.database.models import ParseStatus, Subject


class BookCreate(BaseModel):
    title: str
    subject: Subject
    year: Optional[int] = None


class BookResponse(BaseModel):
    book_id: str
    title: str
    subject: Subject
    year: Optional[int]
    parse_status: ParseStatus
    lesson_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


class BookParseStatusResponse(BaseModel):
    book_id: str
    status: ParseStatus
    progress: int  # 0-100
    current_page: Optional[int] = 0
    total_pages: Optional[int] = 0
    message: Optional[str] = None