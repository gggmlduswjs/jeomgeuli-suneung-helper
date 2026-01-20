"""
보기(Example) 블록 파서
우선순위: 4 (최하위)
"""
from typing import List, Dict, Any, Tuple

from .base_parser import BaseParser
from .intermediate_schema import BlockType, BlockMetadata
from .parsing_rules import ParsingRules


class ExampleParser(BaseParser):
    """보기 블록 파서"""

    def __init__(self):
        super().__init__(BlockType.EXAMPLE)

    def can_start_block(
        self,
        lines: List[Dict[str, Any]],
        line_idx: int,
        page_height: float,
        avg_font_size: float
    ) -> Tuple[bool, float]:
        """
        보기 블록 시작 확인

        조건:
        1. "< 보기 >", "「보기」" 패턴
        2. question 블록 내부에 위치
        """
        if line_idx >= len(lines):
            return False, 0.0

        line = lines[line_idx]
        text = self._get_line_text(line)

        if not text:
            return False, 0.0

        confidence = 0.0

        # 1. 보기 패턴 매칭
        if self._matches_start_patterns(text):
            confidence += 0.7

            # 정확한 보기 마커인지 확인
            if self.normalizer.is_example_marker(text):
                confidence += 0.2
        else:
            return False, 0.0

        # 2. 위치 (주로 페이지 하단 - 문제 내부)
        y_position = line.get('top', 0) / page_height if page_height > 0 else 0.0
        if y_position > 0.5:
            confidence += 0.1

        return confidence >= 0.7, confidence

    def find_block_end(
        self,
        lines: List[Dict[str, Any]],
        start_idx: int,
        page_height: float,
        avg_font_size: float
    ) -> int:
        """
        보기 블록 종료 지점 찾기

        종료 조건:
        1. 선택지 시작 ("①", "②" 등)
        2. 다음 문제 시작
        """
        end_idx = start_idx

        for i in range(start_idx + 1, len(lines)):
            line = lines[i]
            text = self._get_line_text(line)

            if not text:
                end_idx = i
                continue

            # 선택지 시작 패턴
            if self._matches_end_patterns(text):
                break

            # 다음 문제 시작
            question_patterns = ParsingRules.get_start_patterns('question')
            from .parsing_rules import matches_any_pattern
            if matches_any_pattern(text, question_patterns):
                break

            end_idx = i

        return end_idx

    def extract_metadata(
        self,
        lines: List[Dict[str, Any]],
        start_idx: int,
        end_idx: int
    ) -> BlockMetadata:
        """
        보기 메타데이터 추출
        """
        metadata = BlockMetadata()
        metadata.title = "보기"
        metadata.confidence = 0.9
        metadata.signals_matched.append("example_marker")

        return metadata
