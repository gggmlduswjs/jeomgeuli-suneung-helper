"""
의미있는 ID 생성 유틸리티
UUID 대신 더 읽기 쉬운 ID를 생성합니다.
"""
import re
import uuid
from typing import Optional


def sanitize_for_id(text: str, max_length: int = 20) -> str:
    """텍스트를 ID에 사용 가능한 형식으로 변환"""
    if not text:
        return ""
    
    # 한글, 영문, 숫자만 남기고 나머지 제거
    text = re.sub(r'[^\w\s가-힣]', '', text)
    # 공백을 언더스코어로
    text = re.sub(r'\s+', '_', text)
    # 연속된 언더스코어를 하나로
    text = re.sub(r'_+', '_', text)
    # 앞뒤 언더스코어 제거
    text = text.strip('_')
    # 소문자로 변환 (한글은 그대로 유지)
    # 한글은 유니코드 범위가 다르므로 소문자 변환에서 제외
    text_lower = ""
    for char in text:
        if 'A' <= char <= 'Z':
            text_lower += char.lower()
        else:
            text_lower += char
    text = text_lower
    # 길이 제한
    if len(text) > max_length:
        text = text[:max_length].rstrip('_')
    
    return text


def generate_curriculum_id(subject: str, title: Optional[str] = None, year: Optional[int] = None) -> str:
    """커리큘럼 ID 생성
    
    형식: cur_{subject}_{year}_{short_title}_{uuid} 또는 cur_{subject}_{uuid}
    예: cur_korean_2026_수능특강_문학_a1b2c3
    """
    subject_lower = subject.lower()
    
    parts = ["cur", subject_lower]
    
    if year:
        parts.append(str(year))
    
    if title:
        # 제목에서 연도 제거 (중복 방지)
        title_clean = sanitize_for_id(title, max_length=20)
        # 연도 패턴 제거
        title_clean = re.sub(r'\d{4}', '', title_clean).strip('_')
        if title_clean:
            parts.append(title_clean)
    
    # 중복 방지를 위해 짧은 UUID 추가
    short_uuid = uuid.uuid4().hex[:6]
    parts.append(short_uuid)
    
    return "_".join(parts)


def generate_lesson_id(subject: str, lesson_number: int, book_id: Optional[str] = None) -> str:
    """레슨 ID 생성

    형식: lesson_{subject}_{lesson_number:02d} 또는 lesson_{book_id}_{lesson_number:02d}
    예: lesson_korean_01, lesson_book_korean_2026_abc123_01

    Args:
        subject: 과목
        lesson_number: 강의 번호
        book_id: 교재 ID (선택, 지정 시 교재별 고유 ID 생성)
    """
    subject_lower = subject.lower()

    # book_id가 제공되면 교재별 고유 ID 생성
    if book_id:
        # book_id의 마지막 6자 (UUID 부분) 추출
        book_suffix = book_id.split('_')[-1] if '_' in book_id else book_id[-6:]
        return f"lesson_{subject_lower}_{book_suffix}_{lesson_number:02d}"

    # 하위 호환성: book_id 없으면 기존 형식
    return f"lesson_{subject_lower}_{lesson_number:02d}"


def generate_unit_id(lesson_id: str, order: int) -> str:
    """학습 단위 ID 생성
    
    형식: unit_{lesson_id}_{order:03d}
    예: unit_lesson_korean_01_001
    """
    return f"unit_{lesson_id}_{order:03d}"


def generate_book_id(subject: str, title: Optional[str] = None, year: Optional[int] = None) -> str:
    """교재 ID 생성
    
    형식: book_{subject}_{year}_{short_title}_{uuid} 또는 book_{subject}_{uuid}
    예: book_korean_2026_수능특강_문학_a1b2c3
    """
    subject_lower = subject.lower()
    
    parts = ["book", subject_lower]
    
    if year:
        parts.append(str(year))
    
    if title:
        # 제목에서 연도 제거 (중복 방지)
        title_clean = sanitize_for_id(title, max_length=20)
        # 연도 패턴 제거
        title_clean = re.sub(r'\d{4}', '', title_clean).strip('_')
        if title_clean:
            parts.append(title_clean)
    
    # 중복 방지를 위해 짧은 UUID 추가
    short_uuid = uuid.uuid4().hex[:6]
    parts.append(short_uuid)
    
    return "_".join(parts)
