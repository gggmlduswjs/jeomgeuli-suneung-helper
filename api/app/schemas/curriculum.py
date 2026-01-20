"""
커리큘럼 관련 Pydantic 스키마
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.db.models import Subject, CurriculumStatus


class LearningUnitCreate(BaseModel):
    """학습 단위 생성 스키마 (공통 구조)"""
    section_type: str = Field(..., description="섹션 타입 (과목별 정의)")
    title: Optional[str] = Field(None, description="학습 단위 제목")
    content: str = Field(..., description="학습 단위 전체 내용")
    order: int = Field(..., description="순서")
    
    # 공통 구조 필드
    learning_objective: Optional[str] = Field(None, description="학습 목표")
    key_content: Optional[str] = Field(None, description="핵심 내용")
    learning_point: Optional[str] = Field(None, description="학습 포인트")
    
    # 점자/음성 지원
    braille_pattern: Optional[str] = Field(None, description="점자 3셀 패턴 (JSON: [1,2,3])")
    braille_text: Optional[str] = Field(None, description="점자 변환 결과")
    tts_text: Optional[str] = Field(None, description="TTS용 요약 텍스트")
    
    # 분할 및 참조
    break_points: Optional[str] = Field(None, description="분할 지점 (JSON)")
    pdf_references: Optional[str] = Field(None, description="PDF 참조 정보 (JSON)")
    
    # 과목별 확장
    subject_metadata: Optional[str] = Field(None, description="과목별 확장 정보 (JSON)")


class LearningUnitResponse(BaseModel):
    """학습 단위 응답 스키마 (공통 구조)"""
    unit_id: str
    curriculum_id: str
    lesson_id: Optional[str] = None
    section_type: str
    title: Optional[str] = None
    content: str
    order: int
    
    # 공통 구조 필드
    learning_objective: Optional[str] = None
    key_content: Optional[str] = None
    learning_point: Optional[str] = None
    
    # 점자/음성 지원
    braille_pattern: Optional[str] = None
    braille_text: Optional[str] = None
    tts_text: Optional[str] = None
    
    # 분할 및 참조
    break_points: Optional[str] = None
    pdf_references: Optional[str] = None
    
    # 과목별 확장
    subject_metadata: Optional[str] = None
    
    created_at: datetime
    
    class Config:
        from_attributes = True


class LessonInfo(BaseModel):
    """레슨 정보 스키마"""
    lesson_number: int
    title: str
    subject: Optional[Subject] = None  # 과목 정보 (이미지 경로 구성용)
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
