"""
강의 대본 파싱 API 엔드포인트
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from pathlib import Path
import tempfile
import os

from app.services.lecture_script_parser import (
    LectureScriptParser,
    parse_lecture_script_file,
    parse_lecture_script_text,
)

router = APIRouter(prefix="/api/lecture-scripts", tags=["lecture-scripts"])


class ParseScriptRequest(BaseModel):
    """대본 파싱 요청"""
    script_text: str
    subject: str = "math1"


class ParseScriptResponse(BaseModel):
    """대본 파싱 응답"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/parse", response_model=ParseScriptResponse)
async def parse_script_text(request: ParseScriptRequest):
    """
    강의 대본 텍스트 파싱
    
    Args:
        request: 파싱 요청 (script_text, subject)
        
    Returns:
        파싱된 구조화 데이터
    """
    try:
        parser = LectureScriptParser(subject=request.subject)
        result = parser.parse(request.script_text)
        
        return ParseScriptResponse(
            success=True,
            data=result,
        )
    except Exception as e:
        return ParseScriptResponse(
            success=False,
            error=str(e),
        )


@router.post("/parse/file", response_model=ParseScriptResponse)
async def parse_script_file(
    file: UploadFile = File(...),
    subject: str = "math1",
):
    """
    강의 대본 파일 업로드 및 파싱
    
    지원 형식:
    - .txt (텍스트 파일)
    - .hwp, .hwpx (한글 파일)
    
    Args:
        file: 업로드된 대본 파일
        subject: 과목명 (기본값: math1)
        
    Returns:
        파싱된 구조화 데이터
    """
    try:
        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=Path(file.filename).suffix if file.filename else ".txt"
        ) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = Path(tmp_file.name)
        
        try:
            # 파일 파싱
            result = parse_lecture_script_file(tmp_path, subject=subject)
            
            return ParseScriptResponse(
                success=True,
                data=result,
            )
        finally:
            # 임시 파일 삭제
            if tmp_path.exists():
                os.unlink(tmp_path)
                
    except Exception as e:
        return ParseScriptResponse(
            success=False,
            error=str(e),
        )


@router.get("/parse/path")
async def parse_script_from_path(
    file_path: str,
    subject: str = "math1",
):
    """
    파일 경로로 강의 대본 파싱
    
    Args:
        file_path: 대본 파일 경로 (상대 경로 또는 절대 경로)
        subject: 과목명 (기본값: math1)
        
    Returns:
        파싱된 구조화 데이터
    """
    try:
        path = Path(file_path)
        
        # 상대 경로인 경우 프로젝트 루트 기준으로 변환
        if not path.is_absolute():
            # data/lecture_scripts 디렉토리에서 찾기
            project_root = Path(__file__).parent.parent.parent.parent
            path = project_root / "data" / "lecture_scripts" / path
        
        if not path.exists():
            raise HTTPException(status_code=404, detail=f"파일을 찾을 수 없습니다: {path}")
        
        result = parse_lecture_script_file(path, subject=subject)
        
        return ParseScriptResponse(
            success=True,
            data=result,
        )
    except Exception as e:
        return ParseScriptResponse(
            success=False,
            error=str(e),
        )
