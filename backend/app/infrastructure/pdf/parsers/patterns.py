"""
통합 패턴 라이브러리
과목별 파싱에 사용되는 패턴 정의
"""
import re
from typing import List


class PatternLibrary:
    """중앙 집중화된 패턴 라이브러리"""

    # ==================== 블록 타입 키워드 ====================

    CONCEPT_KEYWORDS = r'개념|concept|정의|설명|이론|원리'
    QUESTION_KEYWORDS = r'문제|다음.*?고른|정답|선택지|<보기>|물음|질문'
    EXAMPLE_KEYWORDS = r'예시|example|예를|사례|예:'

    # 작품 패턴 (예: "- 작가명, 「작품명」")
    WORK_PATTERN = r'[-]\s*[가-힣\s]+,?\s*「[가-힣\s]+」'

    # ==================== 강의 제목 패턴 ====================
    # (from parsing/strategies/literature_strategy.py)

    LECTURE_TITLE_PATTERNS = [
        r'^\d+강',                              # "1강 |", "2강" 등
        r'작품으로\s*이해하기\s*\d+',             # "작품으로 이해하기 4"
        r'^\d{2}\s+[가-힣]+',                   # "01 고전 시가", "02 현대시" 등
        r'^\d{2}[가-힣]+',                      # "01고전시가" (공백 없이)
    ]

    # ==================== 문제 번호 패턴 ====================

    PROBLEM_NUMBER_PATTERN = r'^\d{2}$'  # "01", "02", ...

    # ==================== 구조 패턴 ====================

    BULLET_PATTERN = r'[-•∙◦▪]'
    NUMBER_PATTERN = r'\d+'

    # ==================== 헬퍼 메서드 ====================

    @classmethod
    def matches_lecture_title(cls, text: str) -> bool:
        """
        텍스트가 강의 제목 패턴과 일치하는지 확인

        Args:
            text: 검사할 텍스트

        Returns:
            패턴 매치 여부
        """
        return any(re.search(pattern, text) for pattern in cls.LECTURE_TITLE_PATTERNS)

    @classmethod
    def is_valid_lecture_title(cls, text: str) -> bool:
        """
        강의 제목 유효성 검증 (패턴 매칭 + 추가 검증)

        Args:
            text: 검사할 텍스트

        Returns:
            유효한 강의 제목 여부
        """
        # 기본 패턴 매칭
        if not cls.matches_lecture_title(text):
            return False

        # 추가 검증 (길이, 형식 체크)
        if len(text) > 50 or len(text) < 2:
            return False

        # 숫자로 시작하고 한글 포함 확인
        if not re.match(r'^\d+', text):
            return False

        if not re.search(r'[가-힣]', text):
            return False

        return True

    @classmethod
    def matches_problem_number(cls, text: str) -> bool:
        """
        문제 번호 패턴 일치 확인

        Args:
            text: 검사할 텍스트

        Returns:
            문제 번호 패턴 일치 여부
        """
        return bool(re.match(cls.PROBLEM_NUMBER_PATTERN, text.strip()))

    @classmethod
    def has_concept_keywords(cls, text: str) -> bool:
        """개념 키워드 포함 여부"""
        return bool(re.search(cls.CONCEPT_KEYWORDS, text, re.IGNORECASE))

    @classmethod
    def has_question_keywords(cls, text: str) -> bool:
        """문제 키워드 포함 여부"""
        return bool(re.search(cls.QUESTION_KEYWORDS, text, re.IGNORECASE))

    @classmethod
    def has_example_keywords(cls, text: str) -> bool:
        """예시 키워드 포함 여부"""
        return bool(re.search(cls.EXAMPLE_KEYWORDS, text, re.IGNORECASE))

    @classmethod
    def has_work_pattern(cls, text: str) -> bool:
        """작품 패턴 포함 여부"""
        return bool(re.search(cls.WORK_PATTERN, text))

    @classmethod
    def has_bullets(cls, text: str) -> bool:
        """불릿 포인트 포함 여부"""
        return bool(re.search(cls.BULLET_PATTERN, text))

    @classmethod
    def has_numbers(cls, text: str) -> bool:
        """숫자 포함 여부"""
        return bool(re.search(cls.NUMBER_PATTERN, text))
