"""
교재 관련 라우터
"""
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
from pathlib import Path

from app.db.session import get_db
from app.db.models import Book, ParseStatus, Subject
from app.schemas.book import BookCreate, BookResponse, BookParseStatusResponse
from app.core.config import settings
# pdf_parse.py 파일에서 직접 import (레거시 함수)
# pdf_parse 디렉토리와 pdf_parse.py 파일이 같은 레벨에 있어서
# 직접 파일 모듈을 import해야 함
import importlib.util
from pathlib import Path
pdf_parse_file = Path(__file__).parent.parent / "services" / "pdf_parse.py"
spec = importlib.util.spec_from_file_location("pdf_parse_module", pdf_parse_file)
pdf_parse_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pdf_parse_module)
parse_lessons_and_units = pdf_parse_module.parse_lessons_and_units
from app.services.hwp_extract import (
    extract_text_from_hwp,
    extract_lesson_info_from_filename,
    extract_structure_from_hwp
)

router = APIRouter()


@router.post("/books/upload", response_model=BookResponse, status_code=201)
async def upload_book(
    file: UploadFile = File(...),
    title: str = Form(...),
    subject: str = Form(...),
    year: int = Form(None),
    db: Session = Depends(get_db),
):
    """
    PDF 업로드 + 교재 생성 + 파싱 시작
    """
    # 파일 검증
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="PDF 파일만 업로드 가능합니다.")
    
    if file.size and file.size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail=f"파일 크기는 {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB를 초과할 수 없습니다.")
    
    # 교재 ID 생성
    book_id = f"bk_{uuid.uuid4().hex[:12]}"
    
    # 파일 저장
    file_path = settings.UPLOADS_DIR / f"{book_id}.pdf"
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # DB에 교재 생성
    book = Book(
        book_id=book_id,
        title=title,
        subject=Subject(subject),
        year=year,
        parse_status=ParseStatus.PENDING,
        file_path=str(file_path),
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    
    # 파싱 작업 시작 (동기 처리, 나중에 비동기로 변경 가능)
    # 백그라운드에서 파싱 시작 (비동기 처리 필요 시 workers 사용)
    try:
        parse_lessons_and_units(book_id, db)
    except Exception as e:
        print(f"[books] Error parsing PDF: {e}")
        book.parse_status = ParseStatus.FAILED
        db.commit()
    
    return BookResponse(
        book_id=book.book_id,
        title=book.title,
        subject=book.subject,
        year=book.year,
        parse_status=book.parse_status,
        lesson_count=0,
    )


@router.get("/books", response_model=List[BookResponse])
async def list_books(db: Session = Depends(get_db)):
    """교재 목록"""
    books = db.query(Book).order_by(Book.created_at.desc()).all()
    result = []
    for book in books:
        lesson_count = len(book.lessons) if book.lessons else 0
        result.append(BookResponse(
            book_id=book.book_id,
            title=book.title,
            subject=book.subject,
            year=book.year,
            parse_status=book.parse_status,
            lesson_count=lesson_count,
        ))
    return result


@router.get("/books/{book_id}", response_model=BookResponse)
async def get_book(book_id: str, db: Session = Depends(get_db)):
    """교재 상세"""
    book = db.query(Book).filter(Book.book_id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="교재를 찾을 수 없습니다.")
    
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
    """파싱 진행 상태 (프론트 폴링용)"""
    book = db.query(Book).filter(Book.book_id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="교재를 찾을 수 없습니다.")
    
    # TODO: 실제 파싱 진행률 계산 (현재는 상태만 반환)
    progress = 100 if book.parse_status == ParseStatus.DONE else 0
    
    return BookParseStatusResponse(
        book_id=book.book_id,
        status=book.parse_status,
        progress=progress,
    )


@router.post("/books/{book_id}/reparse")
async def reparse_book(book_id: str, db: Session = Depends(get_db)):
    """교재 재파싱"""
    book = db.query(Book).filter(Book.book_id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="교재를 찾을 수 없습니다.")
    
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
            # 기존 강의 삭제 (선택적)
            # for lesson in book.lessons:
            #     db.delete(lesson)
            # db.commit()
            
            # 재파싱 시작
            success = parse_lessons_and_units(book_id, db)
            
            # 최신 상태 가져오기
            db.refresh(book)
            
            if success:
                return {
                    "ok": True,
                    "message": "재파싱이 완료되었습니다.",
                    "status": book.parse_status.value if hasattr(book.parse_status, 'value') else str(book.parse_status)
                }
            else:
                return {
                    "ok": False,
                    "message": "재파싱에 실패했습니다.",
                    "status": book.parse_status.value if hasattr(book.parse_status, 'value') else str(book.parse_status)
                }
        except Exception as e:
            print(f"[books] 재파싱 실패: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail=f"재파싱 중 오류가 발생했습니다: {str(e)}"
            )
    else:
        raise HTTPException(
            status_code=400,
            detail="PDF 파일만 재파싱할 수 있습니다."
        )


@router.post("/books/upload-hwp", response_model=BookResponse, status_code=201)
async def upload_hwp_book(
    file: UploadFile = File(...),
    title: str = Form(...),
    subject: str = Form(...),
    year: int = Form(None),
    db: Session = Depends(get_db),
):
    """
    한글 파일 업로드 및 파싱
    
    - 파일명에서 강의 정보 추출
    - 텍스트 추출 및 구조화
    - 데이터베이스에 저장
    """
    # 파일 검증
    if not file.filename or not (file.filename.endswith('.hwp') or file.filename.endswith('.HWP')):
        raise HTTPException(status_code=400, detail="한글 파일(.hwp)만 업로드 가능합니다.")
    
    if file.size and file.size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail=f"파일 크기는 {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB를 초과할 수 없습니다.")
    
    # 교재 ID 생성
    book_id = f"bk_{uuid.uuid4().hex[:12]}"
    
    # 파일 저장
    file_path = settings.UPLOADS_DIR / f"{book_id}.hwp"
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # 파일명에서 강의 정보 추출
    lesson_info = extract_lesson_info_from_filename(file.filename)
    
    # 텍스트 추출 및 구조 파싱
    text = extract_text_from_hwp(file_path)
    structure = extract_structure_from_hwp(file_path) if text else {}
    
    # DB에 교재 생성
    book = Book(
        book_id=book_id,
        title=title,
        subject=Subject(subject),
        year=year,
        parse_status=ParseStatus.DONE if text else ParseStatus.FAILED,
        file_path=str(file_path),
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    
    # TODO: 구조화된 데이터를 Lesson/Unit으로 변환하여 저장
    
    return BookResponse(
        book_id=book.book_id,
        title=book.title,
        subject=book.subject,
        year=book.year,
        parse_status=book.parse_status,
        lesson_count=len(structure.get("problems", [])),
    )


@router.get("/books/{book_id}/lessons-from-hwp")
async def get_lessons_from_hwp(book_id: str, db: Session = Depends(get_db)):
    """한글 파일에서 추출한 강의 목록 조회"""
    book = db.query(Book).filter(Book.book_id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="교재를 찾을 수 없습니다.")
    
    pdf_path = Path(book.file_path)
    if not pdf_path.exists() or not pdf_path.suffix.lower() == '.hwp':
        raise HTTPException(status_code=404, detail="한글 파일을 찾을 수 없습니다.")
    
    # 구조 추출
    structure = extract_structure_from_hwp(pdf_path)
    lesson_info = extract_lesson_info_from_filename(pdf_path.name)
    
    return {
        "book_id": book_id,
        "lesson_info": lesson_info,
        "structure": structure
    }
