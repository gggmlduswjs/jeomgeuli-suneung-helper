"""
학습 단위 관련 라우터
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import json

from app.db.session import get_db
from app.db.models import Unit, Lesson, UnitType
from app.schemas.unit import UnitResponse, UnitQuestion

router = APIRouter()


@router.get("/lessons/{lesson_id}/units", response_model=List[UnitResponse])
async def list_units(lesson_id: str, db: Session = Depends(get_db)):
    """학습 단위 목록 (순서 보장)"""
    # 강 존재 확인
    lesson = db.query(Lesson).filter(Lesson.lesson_id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="강을 찾을 수 없습니다.")
    
    units = db.query(Unit).filter(Unit.lesson_id == lesson_id).order_by(Unit.order).all()
    
    result = []
    for unit in units:
        unit_data = {
            "unit_id": unit.unit_id,
            "lesson_id": unit.lesson_id,
            "type": unit.type,
            "title": unit.title,
            "order": unit.order,
            "content_text": unit.content_text,
            "braille_text": unit.braille_text,
        }
        
        # 문제 타입인 경우 question 필드 추가
        if unit.type == UnitType.QUESTION and unit.question_stem:
            choices = json.loads(unit.question_choices) if unit.question_choices else []
            unit_data["question"] = UnitQuestion(
                stem=unit.question_stem,
                choices=choices,
                answer=unit.question_answer,
            )
        
        result.append(UnitResponse(**unit_data))
    
    return result


@router.get("/units/{unit_id}", response_model=UnitResponse)
async def get_unit(unit_id: str, db: Session = Depends(get_db)):
    """학습 단위 상세"""
    unit = db.query(Unit).filter(Unit.unit_id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="학습 단위를 찾을 수 없습니다.")
    
    unit_data = {
        "unit_id": unit.unit_id,
        "lesson_id": unit.lesson_id,
        "type": unit.type,
        "title": unit.title,
        "order": unit.order,
        "content_text": unit.content_text,
        "braille_text": unit.braille_text,
    }
    
    # 문제 타입인 경우 question 필드 추가
    if unit.type == UnitType.QUESTION and unit.question_stem:
        choices = json.loads(unit.question_choices) if unit.question_choices else []
        unit_data["question"] = UnitQuestion(
            stem=unit.question_stem,
            choices=choices,
            answer=unit.question_answer,
        )
    
    return UnitResponse(**unit_data)
