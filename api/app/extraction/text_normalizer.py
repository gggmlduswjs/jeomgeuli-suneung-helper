"""
OCR 텍스트 정규화
OCR 오류를 복원하고 텍스트를 정규화
"""
import re
from typing import Dict, List


class OCRNormalizer:
    """OCR 오류 정규화 클래스"""

    # 문제 번호 오인식 패턴
    PROBLEM_NUMBER_FIXES: Dict[str, List[str]] = {
        '01': ['O1', '0l', 'Ol', '0I', 'OI'],
        '02': ['O2', 'OZ', '0Z'],
        '03': ['O3', '0з'],
        '04': ['O4'],
        '05': ['O5', '0S', 'OS'],
        '06': ['O6'],
        '07': ['O7'],
        '08': ['O8'],
        '09': ['O9'],
        '10': ['IO', 'I0', 'lO', 'l0'],
    }

    # 역방향 매핑 (오인식 → 정상)
    PROBLEM_NUMBER_REVERSE_MAP: Dict[str, str] = {}

    @classmethod
    def _init_reverse_map(cls):
        """역방향 매핑 초기화"""
        if not cls.PROBLEM_NUMBER_REVERSE_MAP:
            for correct, variants in cls.PROBLEM_NUMBER_FIXES.items():
                for variant in variants:
                    cls.PROBLEM_NUMBER_REVERSE_MAP[variant] = correct

    @classmethod
    def normalize_text(cls, text: str) -> str:
        """
        텍스트 전체 정규화

        Args:
            text: 원본 텍스트

        Returns:
            정규화된 텍스트
        """
        if not text:
            return text

        # 1. 작품 괄호 복원
        text = cls.normalize_work_brackets(text)

        # 2. 문제 번호 복원
        text = cls.normalize_problem_number(text)

        # 3. 공백 정규화
        text = cls.normalize_whitespace(text)

        return text

    @classmethod
    def normalize_work_brackets(cls, text: str) -> str:
        """
        작품 괄호 정규화
        「작품명」이 OCR에서 오인식되는 경우 복원

        예:
        - "r작품명」" → "「작품명」"
        - "「작품명l" → "「작품명」"
        - "[작품명]" → "「작품명」" (보수적으로 처리)
        """
        # 패턴 1: 왼쪽 괄호 오인식 (r, |, I, l → 「)
        text = re.sub(r'[r|Il]\s*([가-힣\s]+)\s*」', r'「\1」', text)

        # 패턴 2: 오른쪽 괄호 오인식 (l, I, | → 」)
        text = re.sub(r'「\s*([가-힣\s]+)\s*[lI|]', r'「\1」', text)

        # 패턴 3: 양쪽 괄호 모두 오인식
        text = re.sub(r'[r|Il]\s*([가-힣\s]+)\s*[lI|\]]', r'「\1」', text)

        # 패턴 4: 대괄호 → 꺾쇠 괄호 (보수적으로, 작품 패턴이 명확한 경우만)
        # "- 작가, [작품]" → "- 작가, 「작품」"
        text = re.sub(r'([-]\s*[가-힣\s]+,\s*)\[([가-힣\s]+)\]', r'\1「\2」', text)

        return text

    @classmethod
    def normalize_problem_number(cls, text: str) -> str:
        """
        문제 번호 정규화
        "O1" → "01", "0l" → "01" 등
        """
        cls._init_reverse_map()

        # 줄 시작 부분의 2자리 숫자 오인식 복원
        def replace_number(match):
            num_text = match.group(0)
            # 역방향 매핑에서 찾기
            if num_text in cls.PROBLEM_NUMBER_REVERSE_MAP:
                return cls.PROBLEM_NUMBER_REVERSE_MAP[num_text]
            return num_text

        # 패턴: 줄 시작의 2자리 문자 (숫자처럼 보이는)
        text = re.sub(r'^[O0Il][0-9lIZ]\b', replace_number, text, flags=re.MULTILINE)

        # 추가: "O" → "0", "l" → "1" (문맥에 따라)
        # 패턴: "O1" 형태를 "01"로
        text = re.sub(r'^O(\d)', r'0\1', text, flags=re.MULTILINE)
        text = re.sub(r'^(\d)l\b', r'\g<1>1', text, flags=re.MULTILINE)

        return text

    @classmethod
    def normalize_whitespace(cls, text: str) -> str:
        """
        공백 정규화
        - 연속된 공백을 하나로
        - 탭을 공백으로
        """
        # 탭 → 공백
        text = text.replace('\t', ' ')

        # 연속된 공백 → 하나의 공백
        text = re.sub(r' +', ' ', text)

        # 줄바꿈 주변의 불필요한 공백 제거
        text = re.sub(r' *\n *', '\n', text)

        # 전체 앞뒤 공백 제거
        text = text.strip()

        return text

    @classmethod
    def extract_problem_number(cls, text: str) -> str:
        """
        텍스트에서 문제 번호 추출

        Args:
            text: 입력 텍스트 (예: "01", "O1", "01. 다음")

        Returns:
            정규화된 문제 번호 (예: "01"), 없으면 빈 문자열
        """
        text = text.strip()

        # 먼저 정규화
        normalized = cls.normalize_problem_number(text)

        # 패턴 매칭: 2자리 숫자
        match = re.match(r'^(\d{2})', normalized)
        if match:
            return match.group(1)

        return ""

    @classmethod
    def extract_work_info(cls, text: str) -> Dict[str, str]:
        """
        작품 정보 추출
        "- 박두진, 「해」" → {"author": "박두진", "work": "해"}

        Args:
            text: 작품 표시 텍스트

        Returns:
            {"author": str, "work": str} 또는 빈 딕셔너리
        """
        # 먼저 괄호 정규화
        normalized = cls.normalize_work_brackets(text)

        # 패턴 1: "- 작가, 「작품」"
        pattern1 = r'[-]\s*([가-힣\s]+?)\s*[,·]\s*「([^」]+)」'
        match = re.search(pattern1, normalized)
        if match:
            return {
                "author": match.group(1).strip(),
                "work": match.group(2).strip()
            }

        # 패턴 2: "- 「작품」 - 작가"
        pattern2 = r'[-]\s*「([^」]+)」\s*[-]\s*([가-힣\s]+)'
        match = re.search(pattern2, normalized)
        if match:
            return {
                "work": match.group(1).strip(),
                "author": match.group(2).strip()
            }

        # 패턴 3: "① - 작가, 「작품」"
        pattern3 = r'[①-⑳]\s*[-]\s*([가-힣\s]+?)\s*[,·]\s*「([^」]+)」'
        match = re.search(pattern3, normalized)
        if match:
            return {
                "author": match.group(1).strip(),
                "work": match.group(2).strip()
            }

        return {}

    @classmethod
    def is_example_marker(cls, text: str) -> bool:
        """
        보기 마커인지 확인
        "< 보기 >", "「보기」", "[보기]" 등
        """
        text = text.strip()
        patterns = [
            r'<\s*보기\s*>',
            r'「\s*보기\s*」',
            r'\[\s*보기\s*\]',
            r'보기\s*:',
        ]

        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        return False
