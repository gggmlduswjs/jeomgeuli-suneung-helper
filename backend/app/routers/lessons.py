"""
레슨 관련 라우터
"""
from fastapi import APIRouter, Depends, HTTPException, Body, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import json
import logging
from pathlib import Path

from app.infrastructure.database.session import get_db
from app.infrastructure.database.models import Lesson, Book, UnitType
from app.schemas.lesson import LessonCreate, LessonResponse
from app.core.exceptions import BookNotFoundException, LessonNotFoundException
# LectureLessonSplitter (삭제된 모듈 대체용)
try:
    from app.services.lecture_lesson_splitter import LectureLessonSplitter
except ImportError:
    # lecture_lesson_splitter 모듈이 없는 경우 stub 클래스 제공
    class LectureLessonSplitter:
        def __init__(self, subject: str = "literature"):
            self.subject = subject
        
        def split(self, text: str) -> list:
            raise HTTPException(status_code=501, detail="강의 레슨 분할이 지원되지 않습니다.")
        
        def split_into_lessons(self, text: str, lesson_titles: List[str]) -> list:
            raise HTTPException(status_code=501, detail="강의 레슨 분할이 지원되지 않습니다.")

from app.core.config import settings
from app.utils.id_generator import generate_lesson_id

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/lessons", response_model=LessonResponse, status_code=201)
async def create_lesson(
    data: LessonCreate,
    db: Session = Depends(get_db)
):
    """
    레슨 생성

    교재에 새로운 레슨을 추가합니다.

    Args:
        data: 레슨 생성 데이터 (book_id, index, title 포함)
        db: 데이터베이스 세션

    Returns:
        LessonResponse: 생성된 레슨 정보

    Raises:
        BookNotFoundException: 해당 교재를 찾을 수 없는 경우
    """
    book = db.query(Book).filter(Book.book_id == data.book_id).first()
    if not book:
        raise BookNotFoundException(data.book_id)
    
    # 의미있는 레슨 ID 생성
    lesson_id = generate_lesson_id(book.subject.value, data.index)
    lesson = Lesson(
        lesson_id=lesson_id,
        book_id=data.book_id,
        index=data.index,
        title=data.title,
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    
    return LessonResponse(
        lesson_id=lesson.lesson_id,
        book_id=lesson.book_id,
        index=lesson.index,
        title=lesson.title,
        lecture_script_text=lesson.lecture_script_text,
        estimated_time=lesson.estimated_time,
        key_points=json.loads(lesson.key_points) if lesson.key_points else [],
        has_question=lesson.has_question or False,
        has_analysis=lesson.has_analysis or False,
        unit_count=0,
        question_count=0,
        created_at=lesson.created_at,
    )


@router.get("/books/{book_id}/lessons", response_model=List[LessonResponse])
async def list_lessons(book_id: str, db: Session = Depends(get_db)):
    """
    교재의 레슨 목록 조회

    특정 교재에 속한 모든 레슨을 index 순으로 조회합니다.

    Args:
        book_id: 교재 ID
        db: 데이터베이스 세션

    Returns:
        List[LessonResponse]: 레슨 목록 (index 오름차순 정렬)

    Raises:
        BookNotFoundException: 해당 교재를 찾을 수 없는 경우
    """
    book = db.query(Book).filter(Book.book_id == book_id).first()
    if not book:
        raise BookNotFoundException(book_id)
    
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
            lecture_script_text=lesson.lecture_script_text,
            estimated_time=lesson.estimated_time,
            key_points=json.loads(lesson.key_points) if lesson.key_points else [],
            has_question=lesson.has_question or False,
            has_analysis=lesson.has_analysis or False,
            unit_count=unit_count,
            question_count=question_count,
            created_at=lesson.created_at,
        ))
    
    return result


@router.get("/lessons/{lesson_id}", response_model=LessonResponse)
async def get_lesson(lesson_id: str, db: Session = Depends(get_db)):
    """
    레슨 상세 조회

    레슨의 상세 정보를 조회합니다. 학습 단위 개수와 문제 개수를 포함합니다.

    Args:
        lesson_id: 레슨 ID
        db: 데이터베이스 세션

    Returns:
        LessonResponse: 레슨 상세 정보 (unit_count, question_count 포함)

    Raises:
        LessonNotFoundException: 해당 레슨을 찾을 수 없는 경우
    """
    lesson = db.query(Lesson).filter(Lesson.lesson_id == lesson_id).first()
    if not lesson:
        raise LessonNotFoundException(lesson_id)
    
    unit_count = len(lesson.units) if lesson.units else 0
    question_count = len([u for u in lesson.units if u.type == UnitType.QUESTION]) if lesson.units else 0
    
    return LessonResponse(
        lesson_id=lesson.lesson_id,
        book_id=lesson.book_id,
        index=lesson.index,
        title=lesson.title,
        lecture_script_text=lesson.lecture_script_text,
        estimated_time=lesson.estimated_time,
        key_points=json.loads(lesson.key_points) if lesson.key_points else [],
        has_question=lesson.has_question or False,
        has_analysis=lesson.has_analysis or False,
        unit_count=unit_count,
        question_count=question_count,
        created_at=lesson.created_at,
    )


@router.post("/lessons/{lesson_id}/split", response_model=List[LessonResponse])
async def split_lesson_script(
    lesson_id: str,
    lesson_titles: Optional[List[str]] = Body(None, embed=True),
    db: Session = Depends(get_db)
):
    """
    레슨의 강의 대본을 하위 레슨으로 분할
    
    Args:
        lesson_id: 원본 레슨 ID
        lesson_titles: 레슨 제목 리스트 (선택, 제공되면 사용)
        
    Returns:
        생성된 하위 레슨 목록
    """
    lesson = db.query(Lesson).filter(Lesson.lesson_id == lesson_id).first()
    if not lesson:
        raise LessonNotFoundException(lesson_id)

    if not lesson.lecture_script_text:
        raise HTTPException(status_code=400, detail="강의 대본이 없습니다.")
    
    # 레슨 분할
    subject = lesson.book.subject.value.lower() if lesson.book else 'literature'
    splitter = LectureLessonSplitter(subject=subject)
    sub_lessons = splitter.split_into_lessons(
        lesson.lecture_script_text,
        lesson_titles
    )
    
    # 하위 레슨 생성
    created_lessons = []
    for sub_lesson in sub_lessons:
        sub_lesson_id = f"lesson_{uuid.uuid4().hex[:12]}"
        
        new_lesson = Lesson(
            lesson_id=sub_lesson_id,
            book_id=lesson.book_id,
            index=sub_lesson['lesson_number'],
            title=sub_lesson['title'],
            lecture_script_text=sub_lesson['content'],
            estimated_time=sub_lesson['estimated_time'],
            key_points=json.dumps(sub_lesson['key_points'], ensure_ascii=False),
            has_question=sub_lesson.get('has_question', False),
            has_analysis=sub_lesson.get('has_analysis', False),
        )
        
        db.add(new_lesson)
        created_lessons.append(new_lesson)
    
    db.commit()
    
    return [
        LessonResponse(
            lesson_id=l.lesson_id,
            book_id=l.book_id,
            index=l.index,
            title=l.title,
            estimated_time=l.estimated_time,
            key_points=json.loads(l.key_points) if l.key_points else [],
            has_question=l.has_question,
            has_analysis=l.has_analysis,
            created_at=l.created_at,
        )
        for l in created_lessons
    ]


@router.get("/lessons/{lesson_id}/script")
async def get_lesson_script(lesson_id: str, db: Session = Depends(get_db)):
    """
    레슨의 강의 대본 조회 (AI 수업용)
    
    AI가 강의 대본을 프롬프트로 사용할 수 있도록 반환
    """
    lesson = db.query(Lesson).filter(Lesson.lesson_id == lesson_id).first()
    if not lesson:
        raise LessonNotFoundException(lesson_id)
    
    return {
        "lesson_id": lesson_id,
        "title": lesson.title,
        "script_text": lesson.lecture_script_text or "",
        "estimated_time": lesson.estimated_time,
        "key_points": json.loads(lesson.key_points) if lesson.key_points else [],
    }


@router.get("/lessons/{lesson_id}/summary")
async def get_lesson_summary(lesson_id: str, db: Session = Depends(get_db)):
    """
    레슨 내용 AI 요약 (사용자용)
    
    레슨 시작 전 AI가 핵심 내용을 요약
    """
    from app.services.ai_lecture_teacher import AILectureTeacher
    
    lesson = db.query(Lesson).filter(Lesson.lesson_id == lesson_id).first()
    if not lesson:
        raise LessonNotFoundException(lesson_id)
    
    # 레슨 내용 수집
    content_parts = []
    if lesson.title:
        content_parts.append(f"제목: {lesson.title}")
    if lesson.lecture_script_text:
        content_parts.append(f"강의 대본: {lesson.lecture_script_text[:1000]}")  # 처음 1000자만
    if lesson.key_points:
        key_points = json.loads(lesson.key_points)
        content_parts.append(f"핵심 포인트: {', '.join(key_points)}")
    
    content = "\n".join(content_parts)
    
    if not content:
        raise HTTPException(status_code=400, detail="요약할 내용이 없습니다.")
    
    # AI 요약
    try:
        subject = lesson.book.subject.value.lower() if lesson.book else 'literature'
        teacher = AILectureTeacher(
            lecture_script=lesson.lecture_script_text or "",
            subject=subject
        )
        
        # 요약 프롬프트
        summary_prompt = f"""다음 레슨 내용을 간단히 요약해주세요:

{content}

요약 시 다음을 포함해주세요:
- 이 레슨에서 배울 주요 내용
- 예상 소요 시간
- 핵심 포인트

친절하고 간결하게 요약해주세요."""
        
        summary = await teacher.answer_question(summary_prompt, content)
        
        return {
            "lesson_id": lesson_id,
            "summary": summary,
            "estimated_time": lesson.estimated_time
        }
    
    except ValueError as e:
        # API 키 관련 에러는 명확한 메시지 반환
        error_msg = str(e)
        raise HTTPException(
            status_code=500, 
            detail=f"AI 요약 생성 실패: {error_msg}"
        )
    except Exception as e:
        # 기타 에러는 일반 메시지
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"[Lesson Summary] 에러 상세: {error_detail}")
        raise HTTPException(
            status_code=500, 
            detail=f"AI 요약 생성 실패: {str(e)}"
        )
