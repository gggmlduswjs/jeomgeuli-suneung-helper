"""
학습 단위 관련 Pydantic 스키마
"""
from pydantic import BaseModel
from typing import Optional, List
from app.infrastructure.database.models import UnitType


class UnitQuestion(BaseModel):
    stem: str
    choices: List[str]  # ["① ...", "② ...", ...]
    answer: Optional[int] = None


class UnitResponse(BaseModel):
    unit_id: str
    lesson_id: str
    type: UnitType
    title: str
    order: int
    content_text: Optional[str] = None
    braille_text: Optional[str] = None
    image_path: Optional[str] = None  # 단일 이미지 경로 (하위호환)
    content_image_paths: Optional[List[str]] = None  # 여러 이미지 경로
    ai_explanation: Optional[str] = None  # AI 튜터 설명
    braille_keywords: Optional[List[str]] = None  # 점자 키워드
    question: Optional[UnitQuestion] = None

    class Config:
        from_attributes = True
        
    @classmethod
    def from_orm_with_question(cls, unit):
        """문제 타입인 경우 question 필드 구성"""
        data = {
            "unit_id": unit.unit_id,
            "lesson_id": unit.lesson_id,
            "type": unit.type,
            "title": unit.title,
            "order": unit.order,
            "content_text": unit.content_text,
            "braille_text": unit.braille_text,
        }
        
        if unit.type == UnitType.QUESTION and unit.question_stem:
            import json
            choices = json.loads(unit.question_choices) if unit.question_choices else []
            data["question"] = UnitQuestion(
                stem=unit.question_stem,
                choices=choices,
                answer=unit.question_answer,
            )
        
        return cls(**data)
