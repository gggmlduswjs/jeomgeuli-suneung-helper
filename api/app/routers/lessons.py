"""
강(단원) 관련 라우터
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.db.models import Lesson, Book, Unit, UnitType
from app.schemas.lesson import LessonResponse

router = APIRouter()


@router.get("/books/{book_id}/lessons", response_model=List[LessonResponse])
async def list_lessons(book_id: str, db: Session = Depends(get_db)):
    """강 목록"""
    # 교재 존재 확인
    book = db.query(Book).filter(Book.book_id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="교재를 찾을 수 없습니다.")
    
    lessons = db.query(Lesson).filter(Lesson.book_id == book_id).order_by(Lesson.index).all()
    
    result = []
    for lesson in lessons:
        unit_count = len(lesson.units) if lesson.units else 0
        question_count = len([u for u in lesson.units if u.type == UnitType.QUESTION]) if lesson.units else 0
        
        result.append(LessonResponse(
            lesson_id=lesson.lesson_id,
            book_id=lesson.book_id,
            index=lesson.index,
            title=lesson.title,
            unit_count=unit_count,
            question_count=question_count,
        ))
    
    return result


@router.get("/lessons/{lesson_id}", response_model=LessonResponse)
async def get_lesson(lesson_id: str, db: Session = Depends(get_db)):
    """강 상세"""
    lesson = db.query(Lesson).filter(Lesson.lesson_id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="강을 찾을 수 없습니다.")
    
    unit_count = len(lesson.units) if lesson.units else 0
    question_count = len([u for u in lesson.units if u.type == UnitType.QUESTION]) if lesson.units else 0
    
    return LessonResponse(
        lesson_id=lesson.lesson_id,
        book_id=lesson.book_id,
        index=lesson.index,
        title=lesson.title,
        unit_count=unit_count,
        question_count=question_count,
    )
