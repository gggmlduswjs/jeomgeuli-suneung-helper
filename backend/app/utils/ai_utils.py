"""
AI 관련 공통 유틸리티 함수
OpenAI 클라이언트 및 ML 서비스 팩토리 함수
"""
import os
from typing import Optional, Callable, Any
from fastapi import HTTPException

# OpenAI API 사용
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# ML 기반 유사도 계산 서비스 (선택적)
try:
    from app.utils.ml_content_similarity import (
        get_similarity_service as _get_similarity_service,
        get_keyword_extractor as _get_keyword_extractor
    )
    ML_AVAILABLE = True
except (ImportError, Exception):
    ML_AVAILABLE = False
    _get_similarity_service = None
    _get_keyword_extractor = None


def get_openai_client() -> openai.OpenAI:
    """
    OpenAI 클라이언트 생성
    
    Returns:
        OpenAI 클라이언트 인스턴스
        
    Raises:
        HTTPException: OPENAI_API_KEY가 설정되지 않은 경우
    """
    if not OPENAI_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="OpenAI가 설치되지 않았습니다. pip install openai를 실행하세요."
        )
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY가 설정되지 않았습니다."
        )
    
    return openai.OpenAI(api_key=api_key)


def get_similarity_service() -> Optional[Any]:
    """
    ML 기반 유사도 계산 서비스 가져오기
    
    Returns:
        유사도 서비스 인스턴스 또는 None (ML이 사용 불가능한 경우)
    """
    if not ML_AVAILABLE or _get_similarity_service is None:
        return None
    try:
        return _get_similarity_service()
    except Exception:
        return None


def get_keyword_extractor() -> Optional[Any]:
    """
    키워드 추출 서비스 가져오기
    
    Returns:
        키워드 추출 서비스 인스턴스 또는 None (ML이 사용 불가능한 경우)
    """
    if not ML_AVAILABLE or _get_keyword_extractor is None:
        return None
    try:
        return _get_keyword_extractor()
    except Exception:
        return None


def check_openai_available() -> bool:
    """OpenAI 사용 가능 여부 확인"""
    return OPENAI_AVAILABLE and bool(os.getenv("OPENAI_API_KEY"))


def check_ml_available() -> bool:
    """ML 서비스 사용 가능 여부 확인"""
    return ML_AVAILABLE
