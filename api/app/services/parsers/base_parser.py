"""
기본 파서 클래스
모든 타입별 파서의 부모 클래스
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod

from .intermediate_schema import (
    IntermediateBlock,
    BlockType,
    Line,
    Word,
    BlockMetadata,
    BlockStatus
)
from .parsing_rules import ParsingRules, matches_any_pattern, is_in_position_range
from .ocr_normalizer import OCRNormalizer


class BaseParser(ABC):
    """기본 파서 추상 클래스"""

    def __init__(self, block_type: BlockType):
        """
        Args:
            block_type: 이 파서가 처리하는 블록 타입
        """
        self.block_type = block_type
        self.rules = ParsingRules.get_rule(block_type.value)
        self.normalizer = OCRNormalizer()

    @abstractmethod
    def can_start_block(
        self,
        lines: List[Dict[str, Any]],
        line_idx: int,
        page_height: float,
        avg_font_size: float
    ) -> Tuple[bool, float]:
        """
        현재 위치에서 블록을 시작할 수 있는지 확인

        Args:
            lines: 페이지의 모든 줄
            line_idx: 현재 줄 인덱스
            page_height: 페이지 높이
            avg_font_size: 평균 폰트 크기

        Returns:
            (시작 가능 여부, 신뢰도)
        """
        pass

    @abstractmethod
    def find_block_end(
        self,
        lines: List[Dict[str, Any]],
        start_idx: int,
        page_height: float,
        avg_font_size: float
    ) -> int:
        """
        블록의 종료 지점 찾기

        Args:
            lines: 페이지의 모든 줄
            start_idx: 블록 시작 줄 인덱스
            page_height: 페이지 높이
            avg_font_size: 평균 폰트 크기

        Returns:
            블록 종료 줄 인덱스 (포함)
        """
        pass

    @abstractmethod
    def extract_metadata(
        self,
        lines: List[Dict[str, Any]],
        start_idx: int,
        end_idx: int
    ) -> BlockMetadata:
        """
        블록 메타데이터 추출

        Args:
            lines: 페이지의 모든 줄
            start_idx: 블록 시작 줄 인덱스
            end_idx: 블록 종료 줄 인덱스

        Returns:
            BlockMetadata 객체
        """
        pass

    def parse_block(
        self,
        page_num: int,
        block_id: str,
        lines: List[Dict[str, Any]],
        start_idx: int,
        end_idx: int,
        page_height: float,
        avg_font_size: float
    ) -> IntermediateBlock:
        """
        블록 파싱 (공통 로직)

        Args:
            page_num: 페이지 번호
            block_id: 블록 ID
            lines: 페이지의 모든 줄
            start_idx: 블록 시작 줄 인덱스
            end_idx: 블록 종료 줄 인덱스
            page_height: 페이지 높이
            avg_font_size: 평균 폰트 크기

        Returns:
            IntermediateBlock 객체
        """
        # 블록 줄들 추출
        block_lines = lines[start_idx:end_idx + 1]

        # bbox 계산
        bbox = self._calculate_bbox(block_lines)

        # y 위치 계산 (페이지 내 상대 위치)
        y_position = bbox[1] / page_height if page_height > 0 else 0.0

        # 폰트 크기 평균 계산
        font_size_avg = self._calculate_avg_font_size(block_lines)

        # Line 객체 생성
        raw_lines = []
        for i, line_data in enumerate(block_lines):
            line_text = line_data.get('text', '')
            # OCR 정규화
            normalized_text = self.normalizer.normalize_text(line_text)

            words = []
            for word_data in line_data.get('words', []):
                word = Word(
                    text=word_data.get('text', ''),
                    bbox=[
                        word_data.get('left', 0),
                        word_data.get('top', 0),
                        word_data.get('left', 0) + word_data.get('width', 0),
                        word_data.get('top', 0) + word_data.get('height', 0)
                    ],
                    confidence=word_data.get('confidence', 1.0)
                )
                words.append(word)

            line = Line(
                line_num=i + 1,
                text=normalized_text,
                words=words
            )
            raw_lines.append(line)

        # 메타데이터 추출
        metadata = self.extract_metadata(lines, start_idx, end_idx)

        # 블록 생성
        block = IntermediateBlock(
            block_id=block_id,
            block_type=self.block_type,
            page=page_num,
            bbox=bbox,
            y_position=y_position,
            font_size_avg=font_size_avg,
            raw_lines=raw_lines,
            metadata=metadata,
            status=BlockStatus(parsed=True, verified=False, has_errors=False)
        )

        return block

    def _calculate_bbox(self, lines: List[Dict[str, Any]]) -> List[int]:
        """줄들의 전체 bbox 계산"""
        if not lines:
            return [0, 0, 0, 0]

        x0 = min(line.get('left', 0) for line in lines)
        y0 = min(line.get('top', 0) for line in lines)
        x1 = max(line.get('left', 0) + line.get('width', 0) for line in lines)
        y1 = max(line.get('top', 0) + line.get('height', 0) for line in lines)

        return [x0, y0, x1, y1]

    def _calculate_avg_font_size(self, lines: List[Dict[str, Any]]) -> float:
        """평균 폰트 크기 계산"""
        if not lines:
            return 0.0

        heights = [line.get('height', 0) for line in lines if line.get('height', 0) > 0]
        if not heights:
            return 0.0

        return sum(heights) / len(heights)

    def _matches_start_patterns(self, text: str) -> bool:
        """시작 패턴 매칭"""
        patterns = ParsingRules.get_start_patterns(self.block_type.value)
        return matches_any_pattern(text, patterns)

    def _matches_end_patterns(self, text: str) -> bool:
        """종료 패턴 매칭"""
        patterns = ParsingRules.get_end_patterns(self.block_type.value)
        return matches_any_pattern(text, patterns)

    def _matches_negative_patterns(self, text: str) -> bool:
        """부정 패턴 매칭 (이 패턴과 매칭되면 이 타입이 아님)"""
        patterns = ParsingRules.get_negative_patterns(self.block_type.value)
        return matches_any_pattern(text, patterns)

    def _is_in_start_position(self, y_position: float) -> bool:
        """시작 위치 범위 내에 있는지"""
        y_range = ParsingRules.get_position_range(self.block_type.value, "start")
        return is_in_position_range(y_position, y_range)

    def _is_in_end_position(self, y_position: float) -> bool:
        """종료 위치 범위 내에 있는지"""
        y_range = ParsingRules.get_position_range(self.block_type.value, "end")
        return is_in_position_range(y_position, y_range)

    def _get_line_text(self, line: Dict[str, Any]) -> str:
        """줄 텍스트 가져오기 (정규화)"""
        text = line.get('text', '')
        return self.normalizer.normalize_text(text)

    def _count_blank_lines(self, lines: List[Dict[str, Any]], start_idx: int) -> int:
        """연속된 빈 줄 개수 세기"""
        count = 0
        for i in range(start_idx, len(lines)):
            text = self._get_line_text(lines[i])
            if not text or text.isspace():
                count += 1
            else:
                break
        return count
