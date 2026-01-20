"""
학습 단위 관련 라우터
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from pathlib import Path
import json

from app.db.session import get_db
from app.db.models import Unit, Lesson, UnitType
from app.schemas.unit import UnitResponse, UnitQuestion

# PDFToUnitsConverter (삭제된 모듈 대체용)
try:
    from app.services.pdf_to_units_converter import PDFToUnitsConverter
except ImportError:
    class PDFToUnitsConverter:
        def __init__(self, subject: str = "literature"):
            self.subject = subject
        
        def convert_pdf_to_units(self, pdf_path: Path, lesson_id: str) -> list:
            raise HTTPException(status_code=501, detail="PDF to Units 변환이 지원되지 않습니다.")

# LiteraturePDFExtractor (삭제된 모듈 대체용)
try:
    from app.services.pdf_extract.literature_extractor import LiteraturePDFExtractor
except ImportError:
    class LiteraturePDFExtractor:
        def __init__(self, subject: str = "literature"):
            self.subject = subject
        
        def extract(self, pdf_path: Path) -> dict:
            raise HTTPException(status_code=501, detail="문학 PDF 추출이 지원되지 않습니다.")

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


@router.post("/lessons/{lesson_id}/units/from-pdf")
async def create_units_from_pdf(
    lesson_id: str,
    pdf_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    PDF에서 Unit 생성 (관리자용)
    
    PDF 파일을 업로드하면 구조 파싱하여 Unit으로 변환
    """
    lesson = db.query(Lesson).filter(Lesson.lesson_id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="레슨을 찾을 수 없습니다.")
    
    # PDF 파일 임시 저장
    from app.core.config import settings
    upload_dir = settings.UPLOADS_DIR
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    pdf_path = upload_dir / pdf_file.filename
    with open(pdf_path, "wb") as f:
        content = await pdf_file.read()
        f.write(content)
    
    try:
        # PDF를 Unit으로 변환
        subject = lesson.book.subject.value.lower() if lesson.book else "literature"
        converter = PDFToUnitsConverter(subject=subject)
        units_data = converter.convert_pdf_to_units(pdf_path, lesson_id)
        
        # Unit 생성
        created_units = []
        for unit_data in units_data:
            unit = Unit(**unit_data)
            db.add(unit)
            created_units.append(unit)
        
        db.commit()
        
        # 응답 생성
        result = []
        for unit in created_units:
            unit_dict = {
                "unit_id": unit.unit_id,
                "lesson_id": unit.lesson_id,
                "type": unit.type,
                "title": unit.title,
                "order": unit.order,
                "content_text": unit.content_text,
                "braille_text": unit.braille_text,
            }
            
            if unit.type == UnitType.QUESTION and unit.question_stem:
                choices = json.loads(unit.question_choices) if unit.question_choices else []
                unit_dict["question"] = UnitQuestion(
                    stem=unit.question_stem,
                    choices=choices,
                    answer=unit.question_answer,
                )
            
            result.append(UnitResponse(**unit_dict))
        
        return {
            "message": f"{len(created_units)}개의 Unit이 생성되었습니다.",
            "units": result
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unit 생성 실패: {str(e)}")
    
    finally:
        # 임시 파일 삭제
        if pdf_path.exists():
            pdf_path.unlink()
