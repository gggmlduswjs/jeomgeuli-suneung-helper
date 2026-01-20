"""
AI 강의 선생님 API
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Optional
import json

from app.db.session import get_db
from app.db.models import Lesson, Unit, UnitType

# AILectureTeacher (삭제된 모듈 대체용)
try:
    from app.services.ai_lecture_teacher import AILectureTeacher
except ImportError:
    class AILectureTeacher:
        def __init__(self, lecture_script: str = "", subject: str = "literature"):
            self.lecture_script = lecture_script
            self.subject = subject
        
        async def teach_unit(self, unit_content: str, unit_type: str) -> str:
            raise HTTPException(status_code=501, detail="AI 강의가 지원되지 않습니다.")
        
        async def answer_question(self, question: str, unit_content: str = "") -> str:
            raise HTTPException(status_code=501, detail="AI 질문 답변이 지원되지 않습니다.")
        
        async def teach_sequentially(self) -> dict:
            raise HTTPException(status_code=501, detail="AI 순차 수업이 지원되지 않습니다.")
        
        async def get_next_topic(self, current_position: int = 0) -> dict:
            raise HTTPException(status_code=501, detail="AI 다음 주제가 지원되지 않습니다.")

router = APIRouter()


@router.post("/ai/teach/unit/{unit_id}")
async def ai_teach_unit(
    unit_id: str,
    db: Session = Depends(get_db)
):
    """
    Unit 내용을 AI가 강의 대본 기반으로 설명

    Args:
        unit_id: Unit ID

    Returns:
        AI 설명 텍스트
    """
    unit = db.query(Unit).filter(Unit.unit_id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="학습 단위를 찾을 수 없습니다.")

    # 1순위: Unit에 저장된 AI 설명 사용
    if unit.ai_explanation:
        return {
            "unit_id": unit_id,
            "explanation": unit.ai_explanation,
            "unit_type": unit.type.value,
            "source": "stored"
        }

    # 2순위: 레슨의 강의 대본 기반 LLM 호출
    lesson = db.query(Lesson).filter(Lesson.lesson_id == unit.lesson_id).first()
    if not lesson or not hasattr(lesson, 'lecture_script_text') or not lesson.lecture_script_text:
        # 강의 대본도 없으면 기본 설명 반환
        return {
            "unit_id": unit_id,
            "explanation": "이 문제에 대한 상세한 설명이 준비되지 않았습니다.",
            "unit_type": unit.type.value,
            "source": "default"
        }

    # AI 강의 선생님 초기화
    subject = lesson.book.subject.value.lower() if lesson.book else 'literature'
    teacher = AILectureTeacher(
        lecture_script=lesson.lecture_script_text,
        subject=subject
    )

    # Unit 타입에 따라 설명
    unit_content = unit.content_text or unit.question_stem or ''

    try:
        explanation = await teacher.teach_unit(
            unit_content=unit_content,
            unit_type=unit.type.value,
            unit_title=unit.title
        )

        return {
            "unit_id": unit_id,
            "explanation": explanation,
            "unit_type": unit.type.value,
            "source": "llm"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 설명 생성 실패: {str(e)}")


@router.post("/ai/answer")
async def ai_answer_question(
    question: str = Body(..., embed=True),
    unit_id: Optional[str] = Body(None, embed=True),
    lesson_id: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db)
):
    """
    사용자 질문에 AI가 강의 대본 기반으로 답변
    
    Args:
        question: 사용자 질문
        unit_id: 현재 Unit ID (선택)
        lesson_id: 현재 Lesson ID (선택)
        
    Returns:
        AI 답변 텍스트
    """
    # 강의 대본 가져오기
    lecture_script = ""
    subject = "literature"
    
    if unit_id:
        unit = db.query(Unit).filter(Unit.unit_id == unit_id).first()
        if unit:
            lesson = db.query(Lesson).filter(Lesson.lesson_id == unit.lesson_id).first()
            if lesson and lesson.lecture_script_text:
                lecture_script = lesson.lecture_script_text
                subject = lesson.book.subject.value.lower() if lesson.book else 'literature'
    elif lesson_id:
        lesson = db.query(Lesson).filter(Lesson.lesson_id == lesson_id).first()
        if lesson and lesson.lecture_script_text:
            lecture_script = lesson.lecture_script_text
            subject = lesson.book.subject.value.lower() if lesson.book else 'literature'
    
    if not lecture_script:
        raise HTTPException(status_code=400, detail="강의 대본을 찾을 수 없습니다.")
    
    # AI 강의 선생님 초기화
    teacher = AILectureTeacher(
        lecture_script=lecture_script,
        subject=subject
    )
    
    # Unit 내용 가져오기 (있는 경우)
    unit_content = None
    if unit_id:
        unit = db.query(Unit).filter(Unit.unit_id == unit_id).first()
        if unit:
            unit_content = unit.content_text or unit.question_stem
    
    try:
        answer = await teacher.answer_question(
            question=question,
            unit_content=unit_content
        )
        
        return {
            "question": question,
            "answer": answer
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 답변 생성 실패: {str(e)}")


@router.post("/ai/teach/{lesson_id}")
async def ai_teach_lesson(
    lesson_id: str,
    mode: str = "sequential",  # "sequential" or "interactive"
    question: Optional[str] = Body(None, embed=True),  # 대화형 모드일 때
    db: Session = Depends(get_db)
):
    """
    AI가 강의 대본을 기반으로 수업 진행
    
    Args:
        lesson_id: 레슨 ID
        mode: "sequential" (순차적) 또는 "interactive" (대화형)
        question: 대화형 모드일 때 사용자 질문
        
    Returns:
        AI 수업 응답
    """
    lesson = db.query(Lesson).filter(Lesson.lesson_id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="레슨을 찾을 수 없습니다.")
    
    if not lesson.lecture_script_text:
        raise HTTPException(status_code=400, detail="강의 대본이 없습니다.")
    
    # AI 강의 선생님 초기화
    subject = lesson.book.subject.value.lower() if lesson.book else 'literature'
    teacher = AILectureTeacher(
        lecture_script=lesson.lecture_script_text,
        subject=subject
    )
    
    try:
        if mode == "sequential":
            # 순차적 수업 진행
            response = await teacher.teach_sequentially()
        else:
            # 대화형 수업 (질문 기반)
            if not question:
                raise HTTPException(status_code=400, detail="질문이 필요합니다.")
            response = await teacher.answer_question(question)
        
        return {
            "lesson_id": lesson_id,
            "response": response,
            "mode": mode
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 수업 진행 실패: {str(e)}")


@router.post("/ai/teach/{lesson_id}/next")
async def ai_get_next_topic(
    lesson_id: str,
    position: int = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """
    강의 대본에서 다음 주제 가져오기
    
    Args:
        lesson_id: 레슨 ID
        position: 현재 위치 (청크 인덱스)
        
    Returns:
        다음 주제 설명
    """
    lesson = db.query(Lesson).filter(Lesson.lesson_id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="레슨을 찾을 수 없습니다.")
    
    if not lesson.lecture_script_text:
        raise HTTPException(status_code=400, detail="강의 대본이 없습니다.")
    
    # AI 강의 선생님 초기화
    subject = lesson.book.subject.value.lower() if lesson.book else 'literature'
    teacher = AILectureTeacher(
        lecture_script=lesson.lecture_script_text,
        subject=subject
    )
    
    try:
        response = await teacher.get_next_topic(current_position=position)
        
        return {
            "lesson_id": lesson_id,
            "position": position,
            "response": response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"다음 주제 가져오기 실패: {str(e)}")
