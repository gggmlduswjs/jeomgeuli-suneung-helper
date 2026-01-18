"""
PDF 구조화 추출 및 이미지 캡처 라우터
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pathlib import Path
import tempfile
import os

from app.db.session import get_db
from app.db.models import Book
from app.core.config import settings
from app.services.pdf_structure_extract import PDFStructureExtractor
from app.services.pdf_image_extract import PDFImageExtractor
from app.services.braille_convert import text_to_braille

router = APIRouter()


def save_temp_file(file: UploadFile) -> Path:
    """업로드된 파일을 임시로 저장"""
    temp_dir = settings.UPLOADS_DIR / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # 임시 파일 경로 생성
    suffix = Path(file.filename).suffix if file.filename else ".pdf"
    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        dir=temp_dir,
        suffix=suffix
    )
    
    # 파일 내용 저장
    content = file.file.read()
    temp_file.write(content)
    temp_file.close()
    
    return Path(temp_file.name)


@router.post("/pdf/extract-structured")
async def extract_structured_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """PDF에서 구조화된 콘텐츠 추출"""
    try:
        extractor = PDFStructureExtractor()
        
        # 임시 파일 저장
        temp_path = save_temp_file(file)
        
        try:
            # 구조화된 콘텐츠 추출
            structured_content = extractor.extract_structured_content(temp_path)
            
            # 점자 변환
            for question in structured_content["questions"]:
                question["stem_braille"] = text_to_braille(question["stem"])
                for choice in question["choices"]:
                    choice["text_braille"] = text_to_braille(choice["text"])
            
            for passage in structured_content["passages"]:
                passage["content_braille"] = text_to_braille(passage["content"])
            
            return structured_content
        finally:
            # 임시 파일 삭제
            if temp_path.exists():
                os.unlink(temp_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF 추출 실패: {str(e)}")


@router.post("/pdf/extract-images")
async def extract_pdf_images(
    file: UploadFile = File(...),
    extract_type: str = "both",  # "questions", "passages", "both"
    db: Session = Depends(get_db),
):
    """PDF에서 문제/본문 이미지 추출"""
    try:
        extractor = PDFImageExtractor()
        structure_extractor = PDFStructureExtractor()
        
        # 임시 파일 저장
        temp_path = save_temp_file(file)
        
        try:
            # 구조화된 콘텐츠 추출 (위치 정보 포함)
            structured = structure_extractor.extract_structured_content(temp_path)
            
            images = []
            
            if extract_type in ["questions", "both"]:
                question_images = extractor.extract_question_images(
                    temp_path,
                    structured["questions"]
                )
                images.extend(question_images)
            
            if extract_type in ["passages", "both"]:
                passage_images = extractor.extract_passage_images(
                    temp_path,
                    structured["passages"]
                )
                images.extend(passage_images)
            
            return {
                "images": images,
                "total_count": len(images)
            }
        finally:
            # 임시 파일 삭제
            if temp_path.exists():
                os.unlink(temp_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이미지 추출 실패: {str(e)}")


@router.get("/books/{book_id}/structured-content")
async def get_structured_content(
    book_id: str,
    lesson_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """구조화된 PDF 콘텐츠 조회"""
    book = db.query(Book).filter(Book.book_id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    pdf_path = Path(book.file_path)
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found")
    
    # 구조화된 콘텐츠 추출
    extractor = PDFStructureExtractor()
    structured = extractor.extract_structured_content(pdf_path)
    
    # 이미지 추출
    image_extractor = PDFImageExtractor()
    
    # 문제 이미지 추가
    question_images = image_extractor.extract_question_images(
        pdf_path,
        structured["questions"]
    )
    # 이미지를 questions에 병합
    for q_img in question_images:
        for q in structured["questions"]:
            if q.get("number") == q_img.get("question_number") and q.get("page") == q_img.get("page"):
                q["image"] = q_img["image"]
                break
    
    # 본문 이미지 추가
    passage_images = image_extractor.extract_passage_images(
        pdf_path,
        structured["passages"]
    )
    # 이미지를 passages에 병합
    for p_img in passage_images:
        for p in structured["passages"]:
            if p.get("title") == p_img.get("passage_title") and p.get("page") == p_img.get("page"):
                p["image"] = p_img["image"]
                break
    
    # 점자 변환
    for question in structured["questions"]:
        question["stem_braille"] = text_to_braille(question["stem"])
        for choice in question["choices"]:
            choice["text_braille"] = text_to_braille(choice["text"])
    
    for passage in structured["passages"]:
        passage["content_braille"] = text_to_braille(passage["content"])
    
    # 특정 강의만 필터링 (향후 구현)
    if lesson_id:
        # lesson_id에 해당하는 문제/본문만 필터링
        pass
    
    return structured
