"""
강(단원) 관련 Pydantic 스키마
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LessonCreate(BaseModel):
    book_id: str
    index: int
    title: str


class LessonResponse(BaseModel):
    lesson_id: str
    book_id: str
    index: int
    title: str
    lecture_script_text: Optional[str] = None  # 강의 대본 텍스트 (AI 수업용)
    estimated_time: Optional[int] = None  # 예상 소요 시간 (분)
    key_points: Optional[list[str]] = []  # 핵심 포인트 리스트
    has_question: Optional[bool] = False  # 문제 풀이 포함 여부
    has_analysis: Optional[bool] = False  # 작품 분석 포함 여부
    unit_count: Optional[int] = 0
    question_count: Optional[int] = 0
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
