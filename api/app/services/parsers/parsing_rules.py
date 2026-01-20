"""
파싱 규칙 설정
타입별 시작/종료 신호, 우선순위 등
"""
import re
from typing import Dict, List, Tuple, Any


class ParsingRules:
    """파싱 규칙 상수"""

    # Y좌표 임계값
    Y_THRESHOLD_SAME_LINE = 10  # 같은 줄 판단
    Y_THRESHOLD_PARAGRAPH = 25  # 같은 문단 판단

    # 폰트 크기 비율
    FONT_RATIO_TITLE = 1.3  # 강의 제목
    FONT_RATIO_CONCEPT = 1.1  # 개념 제목
    FONT_RATIO_QUESTION = 1.2  # 문제 번호

    # 페이지 영역 구분
    PAGE_REGIONS = {
        "top": (0.0, 0.3),  # 상단 (개념)
        "middle": (0.3, 0.7),  # 중단 (작품)
        "bottom": (0.6, 1.0)  # 하단 (문제)
    }

    # 타입별 파싱 규칙
    RULES: Dict[str, Dict[str, Any]] = {
        "concept": {
            "priority": 3,
            "start_signals": {
                "patterns": [
                    r'^\(\d+\)\s+[가-힣]{2,}',  # "(1) 시적 표현"
                    r'^[①-⑳]\s*[가-힣]{2,}',  # "① 형상화"
                    r'^\d+[\.\)]\s+[가-힣]{2,}',  # "1. 개념 설명"
                    r'^핵심',  # "핵심"
                    r'^학습.*?목표',  # "학습 목표"
                    r'^중요.*?개념',  # "중요 개념"
                ],
                "position_y_ratio": (0.0, 0.4),
                "font_size_min_ratio": 1.0,
            },
            "end_signals": {
                "patterns": [
                    r'^\d{2}$',  # 문제 번호
                    r'[-]\s*[가-힣\s]+,?\s*「',  # 작품 시작
                ],
                "position_y_ratio": (0.5, 1.0),
                "blank_lines": 3,
            },
            "negative_signals": [
                r'^\d{2}$',  # 문제 번호
                r'「[^」]+」',  # 작품 괄호
            ],
        },
        "passage": {
            "priority": 2,
            "start_signals": {
                "patterns": [
                    r'[-]\s*[가-힣\s]+(,|·)\s*「[^」]+」',  # "- 박두진, 「해」"
                    r'[-]\s*「[^」]+」\s*[-]\s*[가-힣\s]+',  # "- 「해」 - 박두진"
                    r'[①-⑳]\s*[-]\s*[가-힣\s]+,\s*「[^」]+」',  # "① - 작가, 「작품」"
                    # OCR 오류 대응 패턴
                    r'[-]\s*[가-힣\s]+(,|·)\s*[r\[|]\s*[^」\]]+\s*[」\]]',  # 괄호 오인식
                ],
                "position_y_ratio": (0.2, 0.8),
            },
            "end_signals": {
                "patterns": [
                    r'^\d{2}$',  # 문제 번호
                    r'[-]\s*[가-힣\s]+,?\s*「',  # 다음 작품
                ],
                "blank_lines": 3,
                "font_size_increase": True,  # 폰트가 갑자기 커지면
            },
            "negative_signals": [
                r'^\d{2}$',  # 문제 번호
                r'^\(\d+\)',  # 개념 번호
            ],
        },
        "question": {
            "priority": 1,  # 최우선
            "start_signals": {
                "patterns": [
                    r'^\d{2}$',  # "01", "02" (단독 줄)
                    r'^\d{2}\s*[\.\)\s]',  # "01.", "01)", "01 "
                    r'^문제\s*\d+',  # "문제 1"
                    r'^\d+\s*번',  # "1번"
                    # OCR 오류 대응
                    r'^[O0][1-9lI]$',  # "O1", "0l"
                    r'^[O0][2-9Z]$',  # "O2", "OZ"
                ],
                "position_y_ratio": (0.6, 1.0),
                "font_size_min_ratio": 1.2,
            },
            "end_signals": {
                "patterns": [
                    r'^\d{2}$',  # 다음 문제
                ],
                "page_end": True,
            },
            "negative_signals": [
                r'^\(\d+\)',  # 개념 번호
                r'「[^」]+」',  # 작품 표시
            ],
        },
        "example": {
            "priority": 4,
            "start_signals": {
                "patterns": [
                    r'<\s*보기\s*>',  # "< 보기 >"
                    r'「\s*보기\s*」',  # "「 보기 」"
                    r'^\[보기\]',  # "[보기]"
                    r'^보기\s*:',  # "보기:"
                ],
            },
            "end_signals": {
                "patterns": [
                    r'^[①-⑤]',  # 선택지
                    r'^\d+\.',  # 번호 선택지
                ],
            },
            "parent": "question",  # question 내부에 종속
        },
    }

    @classmethod
    def get_rule(cls, block_type: str) -> Dict[str, Any]:
        """특정 타입의 규칙 가져오기"""
        return cls.RULES.get(block_type, {})

    @classmethod
    def get_start_patterns(cls, block_type: str) -> List[str]:
        """시작 패턴 가져오기"""
        rule = cls.get_rule(block_type)
        return rule.get("start_signals", {}).get("patterns", [])

    @classmethod
    def get_end_patterns(cls, block_type: str) -> List[str]:
        """종료 패턴 가져오기"""
        rule = cls.get_rule(block_type)
        return rule.get("end_signals", {}).get("patterns", [])

    @classmethod
    def get_negative_patterns(cls, block_type: str) -> List[str]:
        """부정 패턴 가져오기"""
        rule = cls.get_rule(block_type)
        return rule.get("negative_signals", [])

    @classmethod
    def get_position_range(cls, block_type: str, signal_type: str = "start") -> Tuple[float, float]:
        """위치 범위 가져오기"""
        rule = cls.get_rule(block_type)
        signals = rule.get(f"{signal_type}_signals", {})
        return signals.get("position_y_ratio", (0.0, 1.0))

    @classmethod
    def get_priority(cls, block_type: str) -> int:
        """우선순위 가져오기 (낮을수록 우선)"""
        rule = cls.get_rule(block_type)
        return rule.get("priority", 99)

    @classmethod
    def get_sorted_types_by_priority(cls) -> List[str]:
        """우선순위 순서로 타입 목록 반환"""
        types = list(cls.RULES.keys())
        return sorted(types, key=lambda t: cls.get_priority(t))


# 추가 유틸리티 함수
def matches_any_pattern(text: str, patterns: List[str]) -> bool:
    """텍스트가 패턴 중 하나와 매칭되는지 확인"""
    if not text or not patterns:
        return False

    normalized_text = re.sub(r'\s+', ' ', text.strip())

    for pattern in patterns:
        try:
            if re.match(pattern, text) or re.match(pattern, normalized_text):
                return True
            # 부분 매칭도 시도 (패턴이 텍스트 시작 부분과 일치)
            match = re.search(pattern, text) or re.search(pattern, normalized_text)
            if match and match.start() == 0:
                return True
        except re.error:
            continue
    return False


def is_in_position_range(y_position: float, y_range: Tuple[float, float]) -> bool:
    """y 위치가 범위 내에 있는지 확인"""
    return y_range[0] <= y_position <= y_range[1]
