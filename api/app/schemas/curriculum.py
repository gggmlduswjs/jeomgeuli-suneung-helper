"""
커리큘럼 관련 Pydantic 스키마
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.db.models import Subject, CurriculumStatus


class LearningUnitCreate(BaseModel):
    """학습 단위 생성 스키마"""
    section_type: str = Field(..., description="섹션 타입 (ot, concept, example 등)")
    content: str = Field(..., description="학습 단위 내용")
    order: int = Field(..., description="순서")
    break_points: Optional[str] = Field(None, description="분할 지점 (JSON)")
    pdf_references: Optional[str] = Field(None, description="PDF 참조 정보 (JSON)")


class LearningUnitResponse(BaseModel):
    """학습 단위 응답 스키마"""
    unit_id: str
    curriculum_id: str
    lesson_id: Optional[str] = None
    section_type: str
    content: str
    order: int
    break_points: Optional[str] = None
    pdf_references: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class LessonInfo(BaseModel):
    """레슨 정보 스키마"""
    lesson_number: int
    title: str
    learning_units: List[Dict[str, Any]]
    sections: List[Dict[str, Any]]
    pdf_references: List[Dict[str, Any]]
    dependencies: List[int]
    estimated_time: int


class LearningPathItem(BaseModel):
    """학습 경로 항목 스키마"""
    lesson: int
    order: int
    title: str


class ConnectionInfo(BaseModel):
    """레슨 간 연결 정보 스키마"""
    from_lesson: int
    to_lesson: int
    type: str
    keywords: List[str]


class CurriculumCreate(BaseModel):
    """커리큘럼 생성 스키마"""
    subject: Subject = Field(..., description="과목")
    title: str = Field(..., description="커리큘럼 제목")
    book_id: Optional[str] = Field(None, description="교재 ID (선택)")


class CurriculumResponse(BaseModel):
    """커리큘럼 응답 스키마"""
    curriculum_id: str
    book_id: Optional[str] = None
    subject: Subject
    title: str
    status: CurriculumStatus
    lesson_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CurriculumDetailResponse(BaseModel):
    """커리큘럼 상세 응답 스키마"""
    curriculum_id: str
    book_id: Optional[str] = None
    subject: Subject
    title: str
    status: CurriculumStatus
    lesson_count: int
    lessons: List[LessonInfo]
    learning_path: List[LearningPathItem]
    connections: List[ConnectionInfo]
    total_lessons: int
    total_units: int
    created_at: datetime
    updated_at: datetime


class CurriculumUpdate(BaseModel):
    """커리큘럼 수정 스키마"""
    title: Optional[str] = None
    lessons: Optional[List[LessonInfo]] = None
    learning_path: Optional[List[LearningPathItem]] = None


class CurriculumGenerateRequest(BaseModel):
    """커리큘럼 생성 요청 스키마"""
    subject: Subject = Field(..., description="과목")
    title: str = Field(..., description="커리큘럼 제목")
    book_id: Optional[str] = Field(None, description="교재 ID (선택)")
