"""
텍스트 유틸리티
기존 backend/utils/encode_hangul.py의 일부 기능 통합
"""
import unicodedata
from typing import List


def normalize_text(text: str) -> str:
    """텍스트 정규화 (NFC)"""
    return unicodedata.normalize("NFC", text or "")


def extract_keywords(text: str, max_keywords: int = 3) -> List[str]:
    """
    텍스트에서 키워드 추출 (간단한 구현)
    
    Args:
        text: 텍스트
        max_keywords: 최대 키워드 수
    
    Returns:
        키워드 리스트
    """
    # 간단한 구현: 공백으로 분리하고 길이 2 이상인 단어 추출
    words = text.split()
    keywords = [w for w in words if len(w) >= 2][:max_keywords]
    return keywords
