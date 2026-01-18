"""
콘텐츠 자동 생성 관련 라우터
"""
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.services.content_auto_generator import ContentAutoGenerator
from app.core.config import settings

router = APIRouter()


class ValidationRequest(BaseModel):
    """검증 요청 스키마"""
    content: str
    section_type: Optional[str] = None


class ValidationResponse(BaseModel):
    """검증 응답 스키마"""
    is_compliant: bool
    score: int
    issues: list
    improvements: list
    suggestions: list


@router.post("/content/validate", response_model=ValidationResponse)
async def validate_content(
    request: ValidationRequest,
    db: Session = Depends(get_db),
):
    """
    콘텐츠 검증
    
    매뉴얼 규칙 준수 여부 검증 및 품질 점수 계산
    """
    generator = ContentAutoGenerator()
    
    # 임시 섹션 생성
    sections = [{
        "type": request.section_type or "general",
        "content": request.content,
        "braille": "",
        "timestamp": None,
        "symbol": ""
    }]
    
    # 검증 수행
    validation = generator.validate_manual_compliance(sections)
    
    # 개선 제안 생성
    suggestions = generator._generate_improvement_suggestions(sections, validation)
    
    return ValidationResponse(
        is_compliant=validation["is_compliant"],
        score=validation["score"],
        issues=validation["issues"],
        improvements=validation.get("improvements", []),
        suggestions=suggestions
    )


@router.post("/content/generate")
async def generate_content(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    콘텐츠 자동 생성
    
    HWP 파일에서 구조화된 학습 자료 자동 생성
    """
    # 파일 검증
    if not file.filename or not (file.filename.endswith('.hwp') or file.filename.endswith('.HWP')):
        raise HTTPException(status_code=400, detail="한글 파일(.hwp)만 업로드 가능합니다.")
    
    if file.size and file.size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail=f"파일 크기는 {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB를 초과할 수 없습니다.")
    
    # 임시 파일 저장
    uploads_dir = Path(settings.UPLOADS_DIR)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    
    import uuid
    temp_file_path = uploads_dir / f"temp_{uuid.uuid4().hex[:12]}.hwp"
    
    try:
        with open(temp_file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # 콘텐츠 자동 생성
        generator = ContentAutoGenerator()
        result = generator.generate_with_auto_fix(temp_file_path)
        
        return {
            "sections": result["sections"],
            "validation": result["validation"],
            "suggestions": result.get("suggestions", []),
            "needs_review": result.get("needs_review", False)
        }
    
    finally:
        # 임시 파일 삭제
        if temp_file_path.exists():
            temp_file_path.unlink()
