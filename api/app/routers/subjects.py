"""
과목 관련 라우터
"""
from fastapi import APIRouter
from typing import List
from pydantic import BaseModel
from app.db.models import Subject

router = APIRouter()


class SubjectResponse(BaseModel):
    """과목 응답 스키마"""
    value: str
    label: str
    description: str

    class Config:
        from_attributes = True


@router.get("/subjects", response_model=List[SubjectResponse])
async def list_subjects():
    """
    과목 목록 조회
    
    MENU_FLOW: 홈 화면 → 과목 선택에서 사용
    """
    subjects = [
        SubjectResponse(
            value="KOREAN",
            label="국어",
            description="수능특강 국어 (문학 포함)"
        ),
        SubjectResponse(
            value="MATH",
            label="수학",
            description="수능특강 수학Ⅰ"
        ),
        SubjectResponse(
            value="ENGLISH",
            label="영어",
            description="수능특강 영어"
        ),
    ]
    return subjects
