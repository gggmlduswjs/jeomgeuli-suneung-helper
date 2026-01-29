"""
교재 관련 라우터
"""
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import sys
import logging
from pathlib import Path

from app.infrastructure.database.session import get_db
from app.infrastructure.database.models import Book, ParseStatus, Subject
from app.schemas.book import BookCreate, BookResponse, BookParseStatusResponse
from app.core.config import settings
from app.core.exceptions import (
    BookNotFoundException, InvalidFileFormatException,
    FileTooLargeException, InvalidSubjectException,
    ParsingFailedException, DatabaseOperationException
)
from app.utils.id_generator import generate_lesson_id, generate_book_id
from app.infrastructure.database.models import Lesson, Curriculum, LearningUnit, CurriculumStatus, Unit, UnitType
import json

# ML 기반 섹션 분류기는 curriculum_service로 이동됨


# 서비스 레이어에서 변환 함수 가져오기
from app.services.book_conversion import (
    subject_to_pipeline_subject as _subject_to_pipeline_subject,
    map_section_type_to_unit_type as _map_section_type_to_unit_type,
    convert_learning_units_to_units as _convert_learning_units_to_units
)
from app.services.curriculum_service import create_curriculum_from_pipeline
from app.services.book_service import process_pdf_background


def _map_section_type_to_unit_type(section_type: str) -> UnitType:
    """
    LearningUnit의 section_type (문자열)을 Unit의 UnitType (enum)으로 매핑

    Args:
        section_type: "concept", "content", "problem", "example", "strategy" 등

    Returns:
        UnitType enum value
    """
    mapping = {
        # 개념 타입
        "concept": UnitType.CONCEPT_CORE,
        "ot": UnitType.CONCEPT_CORE,  # 오리엔테이션도 핵심 개념으로
        "general": UnitType.CONCEPT_CORE,

        # 작품/본문 타입
        "content": UnitType.PASSAGE,
        "work": UnitType.PASSAGE,
        "passage": UnitType.PASSAGE,

        # 문제 타입
        "problem": UnitType.QUESTION,
        "question": UnitType.QUESTION,

        # 예시/전략은 개념으로 분류
        "example": UnitType.CONCEPT_FORM,
        "strategy": UnitType.CONCEPT_CONTENT,
    }

    return mapping.get(section_type.lower(), UnitType.CONCEPT_CORE)


# _convert_learning_units_to_units 함수는 서비스 레이어로 이동됨


def _create_curriculum_from_pipeline(
    book_id: Optional[str],
    subject_enum: Subject,
    pipeline_subject: str,
    title: str,
    db: Session
) -> str:
    """파이프라인 결과를 커리큘럼으로 변환 (서비스 레이어로 위임)"""
    return create_curriculum_from_pipeline(
        book_id=book_id,
        subject_enum=subject_enum,
        pipeline_subject=pipeline_subject,
        title=title,
        db=db
    )


def _process_pdf_background(book_id: str, pdf_path: Path, subject: str, ai_options: dict = None):
    """백그라운드에서 PDF 파이프라인 실행 (서비스 레이어로 위임)"""
    return process_pdf_background(book_id, pdf_path, subject, ai_options)


# LectureScriptParser (삭제된 모듈 대체용)
try:
    from app.services.lecture_script_parser import LectureScriptParser
except ImportError:
    # lecture_script_parser 모듈이 없는 경우 stub 클래스 제공
    class LectureScriptParser:
        def __init__(self, subject: str = "literature"):
            self.subject = subject
        
        def parse(self, text: str) -> dict:
            raise HTTPException(status_code=501, detail="강의 스크립트 파싱이 지원되지 않습니다.")

router = APIRouter()

logger = logging.getLogger(__name__)



@router.post("/books/upload", response_model=BookResponse, status_code=201)
async def upload_book(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    subject: str = Form(...),
    year: int = Form(None),
    # AI Processing Options (Level 1/2/3)
    enable_ml_deduplication: bool = Form(True),
    enable_ml_classification: bool = Form(True),
    enable_layout_analysis: bool = Form(False),
    enable_math_recognition: bool = Form(False),
    enable_llm_metadata: bool = Form(False),
    enable_llm_explanations: bool = Form(False),
    enable_llm_recommendations: bool = Form(False),
    openai_api_key: str = Form(None),
    education_level: str = Form("high"),
    db: Session = Depends(get_db),
):
    """
    PDF 업로드 + 교재 생성 + 파싱 시작

    PDF 파일을 업로드하고 자동으로 파싱 파이프라인을 실행하여
    학습 콘텐츠(개념, 지문, 문제)를 추출합니다.

    Args:
        background_tasks: 백그라운드 작업 관리자
        file: PDF 파일 (최대 크기: settings.MAX_UPLOAD_SIZE)
        title: 교재 제목
        subject: 과목 (KOREAN, MATH, ENGLISH)
        year: 출판 연도 (선택)
        enable_ml_deduplication: ML 기반 중복 제거 (Level 1)
        enable_ml_classification: ML 기반 블록 분류 (Level 1)
        enable_layout_analysis: 딥러닝 레이아웃 분석 (Level 2)
        enable_math_recognition: 수식 인식 (Level 2)
        enable_llm_metadata: LLM 메타데이터 생성 (Level 3)
        enable_llm_explanations: LLM 설명 생성 (Level 3)
        enable_llm_recommendations: LLM 추천 생성 (Level 3)
        openai_api_key: OpenAI API 키 (Level 3 기능 사용 시)
        education_level: 교육 수준 (high, middle, elementary)
        db: 데이터베이스 세션

    Returns:
        BookResponse: 생성된 교재 정보 (parse_status=PROCESSING)

    Raises:
        InvalidFileFormatException: PDF 파일이 아닌 경우
        FileTooLargeException: 파일 크기가 제한을 초과한 경우
        InvalidSubjectException: 유효하지 않은 과목인 경우
        DatabaseOperationException: 데이터베이스 저장 실패 시

    Note:
        - 파싱은 백그라운드에서 비동기로 실행됩니다
        - parse_status는 PENDING → PROCESSING → DONE/FAILED로 변경됩니다
        - Level 3 기능 사용 시 OpenAI API 키가 필요합니다
    """
    # 파일 검증
    if not file.filename.endswith('.pdf'):
        raise InvalidFileFormatException("PDF")

    if file.size and file.size > settings.MAX_UPLOAD_SIZE:
        raise FileTooLargeException(int(settings.MAX_UPLOAD_SIZE / 1024 / 1024))
    
    # 교재 ID 생성 (의미있는 ID)
    book_id = generate_book_id(subject, title, year)
    
    # Subject enum 변환
    try:
        subject_enum = Subject(subject)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"유효하지 않은 과목입니다: {subject}")
    
    # 같은 제목/과목/연도의 기존 교재 확인 및 정리
    try:
        # year가 None인 경우도 처리
        query = db.query(Book).filter(
            Book.title == title,
            Book.subject == subject_enum
        )
        if year is not None:
            query = query.filter(Book.year == year)
        else:
            query = query.filter(Book.year.is_(None))
        
        existing_books = query.all()
    except Exception as query_err:
        logger.error(f"[books] 기존 교재 조회 중 오류: {query_err}")
        import traceback
        logger.error(traceback.format_exc())
        existing_books = []  # 에러 발생 시 빈 리스트로 처리하고 계속 진행
    
    if existing_books:
        logger.warning(f"[books] ⚠️ 같은 교재가 {len(existing_books)}개 발견됨 (제목: {title}, 과목: {subject}, 연도: {year})")
        logger.debug(f"[books] 기존 교재 데이터 정리 중...")
        sys.stdout.flush()
        
        import shutil
        # settings는 이미 상단에서 import되어 있음
        pipeline_subject = _subject_to_pipeline_subject(subject_enum)
        
        # 기존 교재들의 데이터 디렉토리 및 DB 데이터 삭제
        for existing_book in existing_books:
            # 1. 교재별 데이터 디렉토리 삭제
            existing_book_data_dir = settings.API_DIR / "data" / pipeline_subject / existing_book.book_id
            if existing_book_data_dir.exists():
                try:
                    shutil.rmtree(existing_book_data_dir)
                    logger.debug(f"[books]   기존 교재 데이터 디렉토리 삭제: {existing_book.book_id}")
                except Exception as err:
                    logger.warning(f"[books]   기존 교재 데이터 디렉토리 삭제 실패 (계속 진행): {err}")
            
            # 2. 기존 교재의 PDF 파일 삭제
            if existing_book.file_path:
                existing_pdf_path = Path(existing_book.file_path)
                if existing_pdf_path.exists():
                    try:
                        existing_pdf_path.unlink()
                        logger.debug(f"[books]   기존 PDF 파일 삭제: {existing_pdf_path}")
                    except Exception as err:
                        logger.warning(f"[books]   기존 PDF 파일 삭제 실패 (계속 진행): {err}")
            
            # 3. DB에서 기존 교재 삭제 (관련 데이터 포함)
            try:
                # Curriculum 및 LearningUnit 삭제
                existing_curricula = db.query(Curriculum).filter(
                    Curriculum.book_id == existing_book.book_id
                ).all()
                for curriculum in existing_curricula:
                    learning_units = db.query(LearningUnit).filter(
                        LearningUnit.curriculum_id == curriculum.curriculum_id
                    ).all()
                    for lu in learning_units:
                        db.delete(lu)
                    db.delete(curriculum)
                
                # Lesson 및 Unit 삭제
                existing_lessons = db.query(Lesson).filter(
                    Lesson.book_id == existing_book.book_id
                ).all()
                for lesson in existing_lessons:
                    units = db.query(Unit).filter(Unit.lesson_id == lesson.lesson_id).all()
                    for unit in units:
                        db.delete(unit)
                    db.delete(lesson)
                
                # Book 삭제
                db.delete(existing_book)
                logger.debug(f"[books]   기존 교재 DB 데이터 삭제: {existing_book.book_id}")
            except Exception as err:
                logger.warning(f"[books]   기존 교재 DB 데이터 삭제 실패 (계속 진행): {err}")
        
        db.commit()
        logger.info(f"[books] 기존 교재 {len(existing_books)}개 정리 완료")
        sys.stdout.flush()
    
    # 파일 저장
    file_path = settings.UPLOADS_DIR / f"{book_id}.pdf"
    logger.debug(f"[books] ========================================")
    logger.info(f"[books] [업로드] 파일 업로드 시작")
    logger.debug(f"[books] ========================================")
    logger.debug(f"[books] 파일명: {file.filename}")
    logger.debug(f"[books] 파일 크기: {file.size} bytes")
    logger.debug(f"[books] 저장 경로: {file_path}")
    logger.debug(f"[books] 교재 ID: {book_id}")
    logger.debug(f"[books] 과목: {subject}")
    logger.debug(f"[books] 제목: {title}")
    sys.stdout.flush()
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    logger.info(f"[books] 파일 저장 완료: {file_path.exists()}, 크기: {file_path.stat().st_size if file_path.exists() else 0} bytes")
    sys.stdout.flush()
    
    # DB에 교재 생성
    book = Book(
        book_id=book_id,
        title=title,
        subject=subject_enum,  # 위에서 변환한 subject_enum 사용
        year=year,
        parse_status=ParseStatus.PROCESSING,
        file_path=str(file_path),
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    
    logger.info(f"[books] DB에 교재 생성 완료: {book_id}, 상태: {book.parse_status}")
    sys.stdout.flush()
    
    # 백그라운드에서 PDF 파이프라인 실행 (AI 옵션 전달)
    ai_options = {
        "enable_ml_deduplication": enable_ml_deduplication,
        "enable_ml_classification": enable_ml_classification,
        "enable_layout_analysis": enable_layout_analysis,
        "enable_math_recognition": enable_math_recognition,
        "enable_llm_metadata": enable_llm_metadata,
        "enable_llm_explanations": enable_llm_explanations,
        "enable_llm_recommendations": enable_llm_recommendations,
        "openai_api_key": openai_api_key,
        "education_level": education_level,
    }
    
    logger.info(f"[books] 백그라운드 작업 등록 시작...")
    logger.debug(f"[books] 파일 경로: {file_path}")
    logger.debug(f"[books] 파일 존재 여부: {file_path.exists()}")
    logger.debug(f"[books] 파일 경로 타입: {type(file_path)}")
    sys.stdout.flush()
    
    try:
        background_tasks.add_task(
            _process_pdf_background,
            book_id,
            file_path,
            subject,
            ai_options
        )
        logger.info(f"[books] ✅ 백그라운드 작업 등록 완료: {book_id}")
        logger.debug(f"[books] ========================================")
        sys.stdout.flush()
    except Exception as e:
        logger.warning(f"[books] ❌ 백그라운드 작업 등록 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
        raise
    
    return BookResponse(
        book_id=book.book_id,
        title=book.title,
        subject=book.subject,
        year=book.year,
        parse_status=book.parse_status,
        lesson_count=0,
    )


@router.get("/books", response_model=List[BookResponse])
async def list_books(
    subject: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    교재 목록 조회
    
    MENU_FLOW: 과목 선택 → 교재 목록에서 사용
    """
    query = db.query(Book)
    
    # 과목 필터링
    if subject:
        try:
            subject_enum = Subject(subject.upper())
            query = query.filter(Book.subject == subject_enum)
        except ValueError:
            raise InvalidSubjectException(subject)
    
    books = query.order_by(Book.created_at.desc()).all()
    
    # 중복 제거: 같은 제목과 연도의 교재는 가장 최근 것만 유지
    book_map = {}
    for book in books:
        key = (book.title, book.year)  # 제목과 연도로 중복 판단
        if key not in book_map or book.created_at > book_map[key].created_at:
            book_map[key] = book
    
    result = []
    for book in book_map.values():
        lesson_count = len(book.lessons) if book.lessons else 0
        result.append(BookResponse(
            book_id=book.book_id,
            title=book.title,
            subject=book.subject,
            year=book.year,
            parse_status=book.parse_status,
            lesson_count=lesson_count,
        ))
    
    # 최신순으로 정렬
    result.sort(key=lambda x: x.book_id, reverse=True)
    return result


@router.get("/books/{book_id}", response_model=BookResponse)
async def get_book(book_id: str, db: Session = Depends(get_db)):
    """
    교재 상세 조회

    특정 교재의 상세 정보를 조회합니다.

    Args:
        book_id: 교재 ID
        db: 데이터베이스 세션

    Returns:
        BookResponse: 교재 정보 (레슨 개수 포함)

    Raises:
        BookNotFoundException: 해당 교재를 찾을 수 없는 경우
    """
    book = db.query(Book).filter(Book.book_id == book_id).first()
    if not book:
        raise BookNotFoundException(book_id)
    
    lesson_count = len(book.lessons) if book.lessons else 0
    return BookResponse(
        book_id=book.book_id,
        title=book.title,
        subject=book.subject,
        year=book.year,
        parse_status=book.parse_status,
        lesson_count=lesson_count,
    )


@router.get("/books/{book_id}/parse-status", response_model=BookParseStatusResponse)
async def get_parse_status(book_id: str, db: Session = Depends(get_db)):
    """
    파싱 진행 상태 조회

    교재 파싱의 실시간 진행 상태를 조회합니다. (프론트엔드 폴링용)

    Args:
        book_id: 교재 ID
        db: 데이터베이스 세션

    Returns:
        BookParseStatusResponse: 파싱 상태 정보
            - status: PENDING, PROCESSING, DONE, FAILED
            - progress: 0-100 (진행률)
            - current_page: 현재 처리 중인 페이지
            - total_pages: 전체 페이지 수
            - message: 상태 메시지

    Raises:
        BookNotFoundException: 해당 교재를 찾을 수 없는 경우

    Note:
        프론트엔드에서 1-2초 간격으로 폴링하여 실시간 진행률 표시
    """
    book = db.query(Book).filter(Book.book_id == book_id).first()
    if not book:
        raise BookNotFoundException(book_id)
    
    # 파싱 진행률 계산 (실제 DB 값 사용)
    if book.parse_status == ParseStatus.DONE:
        progress = 100
    elif book.parse_status == ParseStatus.FAILED:
        progress = 0
    elif book.parse_status == ParseStatus.PROCESSING:
        # 실제 DB에 저장된 진행률 사용
        progress = book.parse_progress if book.parse_progress is not None else 0
    else:
        progress = 0
    
    return BookParseStatusResponse(
        book_id=book.book_id,
        status=book.parse_status,
        progress=progress,
        current_page=book.current_page if book.current_page is not None else 0,
        total_pages=book.total_pages if book.total_pages is not None else 0,
    )


@router.post("/books/{book_id}/reparse")
async def reparse_book(
    book_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """교재 재파싱"""
    book = db.query(Book).filter(Book.book_id == book_id).first()
    if not book:
        raise BookNotFoundException(book_id)

    # 파일 경로 확인
    file_path = Path(book.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"파일을 찾을 수 없습니다: {file_path}"
        )

    # PDF 파일인 경우 재파싱
    if file_path.suffix.lower() == '.pdf':
        try:
            logger.info(f"[books] 재파싱 시작: {book_id}")

            # 파싱 상태를 PROCESSING으로 업데이트
            book.parse_status = ParseStatus.PROCESSING
            db.commit()

            # 재파싱 전 기존 데이터 삭제 (교재별 JSON 파일, 이미지 등)
            pipeline_subject = _subject_to_pipeline_subject(book.subject)
            # 교재별 디렉토리: data/{subject}/{book_id}/
            book_data_dir = settings.API_DIR / "data" / pipeline_subject / book_id
            
            logger.info(f"[books] 재파싱 전 기존 데이터 삭제 시작 (교재별): {book_data_dir}")
            import shutil
            
            # 1. 캐시 삭제 (과목별)
            cache_dir = settings.DATA_DIR / pipeline_subject / "cache"
            if cache_dir.exists():
                try:
                    shutil.rmtree(cache_dir)
                    logger.info(f"[books] 캐시 삭제 완료: {cache_dir}")
                except Exception as cache_err:
                    logger.warning(f"[books] 캐시 삭제 실패 (계속 진행): {cache_err}")
            
            # 2. 교재별 JSON 파일 및 이미지 디렉토리 삭제
            if book_data_dir.exists():
                # 전체 교재 디렉토리 삭제 (교재별 완전 분리)
                try:
                    shutil.rmtree(book_data_dir)
                    logger.info(f"[books] 교재별 데이터 디렉토리 삭제 완료: {book_data_dir}")
                except Exception as err:
                    logger.warning(f"[books] 교재별 데이터 디렉토리 삭제 실패 (계속 진행): {err}")
            else:
                logger.debug(f"[books] 교재별 데이터 디렉토리가 없음: {book_data_dir}")
            
            logger.info(f"[books] 재파싱 전 기존 데이터 삭제 완료 (교재별)")

            # 기본 AI 옵션 (기본 ML 기능만 활성화)
            ai_options = {
                "enable_ml_deduplication": True,
                "enable_ml_classification": True,
                "enable_layout_analysis": False,
                "enable_math_recognition": False,
                "enable_llm_metadata": False,
                "enable_llm_explanations": False,
                "enable_llm_recommendations": False,
                "openai_api_key": None,
                "education_level": "high",
            }

            # 백그라운드에서 PDF 파이프라인 실행
            background_tasks.add_task(
                _process_pdf_background,
                book_id,
                file_path,
                book.subject.value,
                ai_options
            )

            logger.info(f"[books] 재파싱 백그라운드 작업 시작: {book_id}")

            return {
                "ok": True,
                "message": "재파싱이 시작되었습니다.",
                "status": book.parse_status.value if hasattr(book.parse_status, 'value') else str(book.parse_status)
            }
        except Exception as e:
            logger.warning(f"[books] 재파싱 실패: {e}")
            import traceback
            traceback.print_exc()

            # 파싱 실패 상태 업데이트
            book.parse_status = ParseStatus.FAILED
            db.commit()

            raise HTTPException(
                status_code=500,
                detail=f"재파싱 중 오류가 발생했습니다: {str(e)}"
            )
    else:
        raise HTTPException(
            status_code=400,
            detail="PDF 파일만 재파싱할 수 있습니다."
        )


@router.post("/books/{book_id}/sync-from-json")
async def sync_book_from_json(
    book_id: str,
    db: Session = Depends(get_db)
):
    """
    JSON 파일에서 DB로 동기화 (재파싱 없이)
    
    JSON 파일은 이미 생성되어 있지만 DB에 저장되지 않은 경우 사용
    기존 DB 데이터를 삭제하고 새로 저장합니다.
    """
    book = db.query(Book).filter(Book.book_id == book_id).first()
    if not book:
        raise BookNotFoundException(book_id)
    
    try:
        # 기존 데이터 삭제
        logger.info(f"[books] 기존 데이터 삭제 시작: {book_id}")
        
        # 1. 기존 커리큘럼 및 LearningUnit 삭제
        existing_curricula = db.query(Curriculum).filter(Curriculum.book_id == book_id).all()
        for curriculum in existing_curricula:
            # LearningUnit 삭제
            learning_units = db.query(LearningUnit).filter(
                LearningUnit.curriculum_id == curriculum.curriculum_id
            ).all()
            for lu in learning_units:
                db.delete(lu)
            db.delete(curriculum)
            logger.debug(f"[books]   Curriculum 삭제: {curriculum.curriculum_id} (LearningUnit {len(learning_units)}개)")
        
        # 2. 기존 Lesson 및 Unit 삭제
        existing_lessons = db.query(Lesson).filter(Lesson.book_id == book_id).all()
        for lesson in existing_lessons:
            # Unit 삭제
            units = db.query(Unit).filter(Unit.lesson_id == lesson.lesson_id).all()
            for unit in units:
                db.delete(unit)
            db.delete(lesson)
            logger.debug(f"[books]   Lesson 삭제: {lesson.lesson_id} (Unit {len(units)}개)")
        
        db.commit()
        logger.info(f"[books] 기존 데이터 삭제 완료: Curriculum {len(existing_curricula)}개, Lesson {len(existing_lessons)}개")
        
        # Subject enum 변환
        subject_enum = book.subject
        pipeline_subject = _subject_to_pipeline_subject(subject_enum)
        
        logger.info(f"[books] JSON → DB 동기화 시작: {book_id} (과목: {pipeline_subject})")
        
        # 커리큘럼 생성 (JSON 파일 읽기)
        curriculum_id = _create_curriculum_from_pipeline(
            book_id=book_id,
            subject_enum=subject_enum,
            pipeline_subject=pipeline_subject,
            title=book.title,
            db=db
        )
        
        logger.info(f"[books] JSON → DB 동기화 완료: {curriculum_id}")
        
        # Lesson 개수 확인
        lessons = db.query(Lesson).filter(Lesson.book_id == book_id).all()
        
        return {
            "ok": True,
            "message": f"동기화 완료: {len(lessons)}개 강의가 생성되었습니다.",
            "curriculum_id": curriculum_id,
            "lessons_count": len(lessons)
        }
    except Exception as e:
        logger.warning(f"[books] JSON → DB 동기화 실패: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"동기화 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/books/sync-all-from-json")
async def sync_all_books_from_json(
    subject: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    특정 과목의 모든 교재를 JSON에서 DB로 동기화
    
    Args:
        subject: 과목 (korean, math, english) - None이면 모든 과목
    """
    from app.core.config import settings
    
    # 과목별 매핑
    subject_mapping = {
        "korean": ("literature", Subject.KOREAN),
        "literature": ("literature", Subject.KOREAN),
        "math": ("math1", Subject.MATH),
        "english": ("english", Subject.ENGLISH),
    }
    
    results = []
    
    if subject:
        # 특정 과목만 동기화
        if subject.lower() not in subject_mapping:
            raise InvalidSubjectException(subject)
        
        pipeline_subject, subject_enum = subject_mapping[subject.lower()]
        books = db.query(Book).filter(Book.subject == subject_enum).all()
        
        for book in books:
            try:
                logger.info(f"[books] {book.book_id} 동기화 시작...")
                
                # 기존 데이터 삭제
                existing_curricula = db.query(Curriculum).filter(Curriculum.book_id == book.book_id).all()
                for curriculum in existing_curricula:
                    learning_units = db.query(LearningUnit).filter(
                        LearningUnit.curriculum_id == curriculum.curriculum_id
                    ).all()
                    for lu in learning_units:
                        db.delete(lu)
                    db.delete(curriculum)
                
                existing_lessons = db.query(Lesson).filter(Lesson.book_id == book.book_id).all()
                for lesson in existing_lessons:
                    units = db.query(Unit).filter(Unit.lesson_id == lesson.lesson_id).all()
                    for unit in units:
                        db.delete(unit)
                    db.delete(lesson)
                
                db.commit()
                
                # JSON → DB 동기화
                curriculum_id = _create_curriculum_from_pipeline(
                    book_id=book.book_id,
                    subject_enum=subject_enum,
                    pipeline_subject=pipeline_subject,
                    title=book.title,
                    db=db
                )
                
                lesson_count = db.query(Lesson).filter(Lesson.book_id == book.book_id).count()
                results.append({
                    "book_id": book.book_id,
                    "title": book.title,
                    "curriculum_id": curriculum_id,
                    "lessons_count": lesson_count,
                    "status": "success"
                })
                logger.info(f"[books] ✅ {book.book_id} 동기화 완료: {lesson_count}개 Lesson")
            except Exception as e:
                logger.warning(f"[books] ❌ {book.book_id} 동기화 실패: {e}")
                results.append({
                    "book_id": book.book_id,
                    "title": book.title,
                    "status": "failed",
                    "error": str(e)
                })
    else:
        # 모든 과목 동기화
        for subj_key, (pipeline_subject, subject_enum) in subject_mapping.items():
            books = db.query(Book).filter(Book.subject == subject_enum).all()
            for book in books:
                try:
                    logger.info(f"[books] {book.book_id} ({pipeline_subject}) 동기화 시작...")
                    
                    # 기존 데이터 삭제
                    existing_curricula = db.query(Curriculum).filter(Curriculum.book_id == book.book_id).all()
                    for curriculum in existing_curricula:
                        learning_units = db.query(LearningUnit).filter(
                            LearningUnit.curriculum_id == curriculum.curriculum_id
                        ).all()
                        for lu in learning_units:
                            db.delete(lu)
                        db.delete(curriculum)
                    
                    existing_lessons = db.query(Lesson).filter(Lesson.book_id == book.book_id).all()
                    for lesson in existing_lessons:
                        units = db.query(Unit).filter(Unit.lesson_id == lesson.lesson_id).all()
                        for unit in units:
                            db.delete(unit)
                        db.delete(lesson)
                    
                    db.commit()
                    
                    # JSON → DB 동기화
                    curriculum_id = _create_curriculum_from_pipeline(
                        book_id=book.book_id,
                        subject_enum=subject_enum,
                        pipeline_subject=pipeline_subject,
                        title=book.title,
                        db=db
                    )
                    
                    lesson_count = db.query(Lesson).filter(Lesson.book_id == book.book_id).count()
                    results.append({
                        "book_id": book.book_id,
                        "title": book.title,
                        "subject": pipeline_subject,
                        "curriculum_id": curriculum_id,
                        "lessons_count": lesson_count,
                        "status": "success"
                    })
                    logger.info(f"[books] ✅ {book.book_id} 동기화 완료: {lesson_count}개 Lesson")
                except Exception as e:
                    logger.warning(f"[books] ❌ {book.book_id} 동기화 실패: {e}")
                    results.append({
                        "book_id": book.book_id,
                        "title": book.title,
                        "subject": pipeline_subject,
                        "status": "failed",
                        "error": str(e)
                    })
    
    success_count = sum(1 for r in results if r.get("status") == "success")
    total_lessons = sum(r.get("lessons_count", 0) for r in results if r.get("status") == "success")
    
    return {
        "ok": True,
        "message": f"{success_count}개 교재 동기화 완료 (총 {total_lessons}개 Lesson)",
        "results": results
    }



@router.delete("/books/{book_id}")
async def delete_book(
    book_id: str,
    db: Session = Depends(get_db)
):
    """
    교재 삭제
    
    교재와 관련된 모든 데이터(레슨, 유닛, 커리큘럼, 학습 단위 등)를 함께 삭제합니다.
    """
    book = db.query(Book).filter(Book.book_id == book_id).first()
    if not book:
        raise BookNotFoundException(book_id)
    
    try:
        # 1. 관련 Lesson 및 Unit 명시적으로 삭제
        lessons = db.query(Lesson).filter(Lesson.book_id == book_id).all()
        lesson_count = len(lessons)
        unit_count = 0
        
        # Lesson 삭제 전에 orphaned units 확인 (join이 작동하도록)
        orphaned_units = db.query(Unit).join(Lesson).filter(Lesson.book_id == book_id).all()
        if orphaned_units:
            logger.warning(f"[books] 경고: {len(orphaned_units)}개 orphaned unit 발견, 삭제 중...")
            for unit in orphaned_units:
                db.delete(unit)
            unit_count += len(orphaned_units)
        
        # Unit과 관련된 Answer, ReviewQueue 등을 먼저 삭제 (Unit 삭제 전에)
        from app.infrastructure.database.models import Answer, ReviewQueue
        for lesson in lessons:
            lesson_units = db.query(Unit).filter(Unit.lesson_id == lesson.lesson_id).all()
            for unit in lesson_units:
                # Answer 삭제
                answers = db.query(Answer).filter(Answer.unit_id == unit.unit_id).all()
                for answer in answers:
                    db.delete(answer)
                # ReviewQueue 삭제
                review_items = db.query(ReviewQueue).filter(ReviewQueue.unit_id == unit.unit_id).all()
                for review_item in review_items:
                    db.delete(review_item)
        
        # 모든 Unit을 삭제
        for lesson in lessons:
            units = db.query(Unit).filter(Unit.lesson_id == lesson.lesson_id).all()
            unit_count += len(units)
            for unit in units:
                db.delete(unit)
        
        # 그 다음 모든 Lesson 삭제
        for lesson in lessons:
            db.delete(lesson)
            logger.debug(f"[books] Lesson 삭제: {lesson.lesson_id}")
        
        logger.info(f"[books] Lesson 및 Unit 삭제 완료: Lesson {lesson_count}개, Unit {unit_count}개")
        
        # 2. 관련 Curriculum 및 LearningUnit 명시적으로 삭제
        curricula = db.query(Curriculum).filter(Curriculum.book_id == book_id).all()
        curriculum_count = len(curricula)
        learning_unit_count = 0
        
        for curriculum in curricula:
            # LearningUnit 삭제
            learning_units = db.query(LearningUnit).filter(
                LearningUnit.curriculum_id == curriculum.curriculum_id
            ).all()
            learning_unit_count += len(learning_units)
            for lu in learning_units:
                db.delete(lu)
            # Curriculum 삭제
            db.delete(curriculum)
            logger.debug(f"[books] Curriculum 삭제: {curriculum.curriculum_id} (LearningUnit {len(learning_units)}개)")
        
        logger.info(f"[books] Curriculum 및 LearningUnit 삭제 완료: Curriculum {curriculum_count}개, LearningUnit {learning_unit_count}개")
        
        # 3. UserProgress에서 book_id를 NULL로 설정 (진행 상황 초기화)
        from app.infrastructure.database.models import UserProgress
        progress_records = db.query(UserProgress).filter(UserProgress.book_id == book_id).all()
        for progress in progress_records:
            progress.book_id = None
            progress.lesson_id = None
            progress.unit_id = None
            progress.syncpoint_id = None
        logger.debug(f"[books] UserProgress 초기화: {len(progress_records)}개 레코드")
        
        # 4. PDF 파일 삭제 (file_path가 있는 경우)
        if book.file_path:
            try:
                pdf_path = Path(book.file_path)
                if pdf_path.exists():
                    pdf_path.unlink()
                    logger.debug(f"[books] PDF 파일 삭제: {pdf_path}")
            except Exception as e:
                logger.warning(f"[books] 경고: PDF 파일 삭제 실패: {e}")
        
        # 5. 데이터 디렉토리 삭제 (backend/data/{subject}/{book_id}/ 폴더)
        try:
            import shutil
            subject_str = _subject_to_pipeline_subject(book.subject)
            # 교재별 디렉토리: data/{subject}/{book_id}/
            book_data_dir = settings.API_DIR / "data" / subject_str / book_id
            if book_data_dir.exists():
                shutil.rmtree(book_data_dir)
                logger.debug(f"[books] 데이터 디렉토리 삭제: {book_data_dir}")
            else:
                logger.debug(f"[books] 데이터 디렉토리 없음 (건너뜀): {book_data_dir}")
        except Exception as e:
            logger.warning(f"[books] 경고: 데이터 디렉토리 삭제 실패 (계속 진행): {e}")
        
        # 6. Book 삭제
        db.delete(book)
        db.commit()
        
        logger.info(f"[books] 교재 삭제 완료: {book_id}")
        logger.debug(f"[books]   - Lesson: {lesson_count}개, Unit: {unit_count}개")
        logger.debug(f"[books]   - Curriculum: {curriculum_count}개, LearningUnit: {learning_unit_count}개")
        logger.debug(f"[books]   - UserProgress: {len(progress_records)}개 초기화")
        
        logger.info(f"[books] 교재 삭제 완료: {book_id} (Curriculum {len(curricula)}개, Progress {len(progress_records)}개 정리, 데이터 디렉토리 삭제)")
        return {"ok": True, "message": "교재가 삭제되었습니다."}
    except Exception as e:
        db.rollback()
        logger.warning(f"[books] 교재 삭제 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"교재 삭제 실패: {str(e)}")


@router.post("/books/{book_id}/create-curriculum-from-data")
async def create_curriculum_from_existing_data(
    book_id: str,
    db: Session = Depends(get_db),
):
    """
    기존 파이프라인 데이터로부터 커리큘럼 생성
    
    이미 backend/data/{subject}/lectures/ 폴더에 데이터가 있는 경우,
    이를 기반으로 커리큘럼을 생성합니다.
    """
    book = db.query(Book).filter(Book.book_id == book_id).first()
    if not book:
        raise BookNotFoundException(book_id)
    
    # 이미 커리큘럼이 있는지 확인하고 삭제
    try:
        existing_curriculum = db.query(Curriculum).filter(Curriculum.book_id == book_id).first()
        if existing_curriculum:
            # 기존 커리큘럼의 학습 단위 삭제
            existing_units = db.query(LearningUnit).filter(
                LearningUnit.curriculum_id == existing_curriculum.curriculum_id
            ).all()
            for unit in existing_units:
                db.delete(unit)
            # 기존 커리큘럼 삭제
            db.delete(existing_curriculum)
            db.commit()
            logger.debug(f"[books] 기존 커리큘럼 삭제: {existing_curriculum.curriculum_id} (학습 단위 {len(existing_units)}개)")
    except Exception as e:
        logger.warning(f"[books] 경고: 기존 커리큘럼 삭제 중 오류: {e}")
        db.rollback()
    
    # Subject enum 변환
    subject_enum = book.subject
    pipeline_subject = _subject_to_pipeline_subject(subject_enum)
    
    try:
        # 파이프라인 데이터로부터 커리큘럼 생성
        curriculum_id = _create_curriculum_from_pipeline(
            book_id=book_id,
            subject_enum=subject_enum,
            pipeline_subject=pipeline_subject,
            title=book.title,
            db=db
        )
        
        if curriculum_id:
            return {
                "ok": True,
                "message": "커리큘럼이 성공적으로 생성되었습니다.",
                "curriculum_id": curriculum_id
            }
        else:
            return {
                "ok": False,
                "message": "커리큘럼 생성에 실패했습니다. 파이프라인 데이터를 확인하세요."
            }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"커리큘럼 생성 중 오류가 발생했습니다: {str(e)}"
        )
