"""
개념(Concept) 블록 파서
우선순위: 3
"""
from typing import List, Dict, Any, Tuple
import re

from .base_parser import BaseParser
from .intermediate_schema import BlockType, BlockMetadata
from .parsing_rules import ParsingRules


class ConceptParser(BaseParser):
    """개념 블록 파서"""

    def __init__(self):
        super().__init__(BlockType.CONCEPT)

    def can_start_block(
        self,
        lines: List[Dict[str, Any]],
        line_idx: int,
        page_height: float,
        avg_font_size: float
    ) -> Tuple[bool, float]:
        """
        개념 블록 시작 확인

        조건:
        1. 개념 번호 패턴 매칭 ("(1)", "①" 등)
        2. 페이지 상단 영역
        3. 중간 이상 폰트 크기
        4. 부정 패턴 없음
        """
        if line_idx >= len(lines):
            return False, 0.0

        line = lines[line_idx]
        text = self._get_line_text(line)

        if not text:
            return False, 0.0

        confidence = 0.0

        # 1. 부정 패턴 체크
        if self._matches_negative_patterns(text):
            return False, 0.0

        # 2. 시작 패턴 매칭
        if self._matches_start_patterns(text):
            confidence += 0.5

            # 개념 번호 추출
            concept_num = self._extract_concept_number(text)
            if concept_num:
                confidence += 0.1
        else:
            return False, 0.0

        # 3. 위치 확인 (페이지 상단)
        y_position = line.get('top', 0) / page_height if page_height > 0 else 0.0
        if self._is_in_start_position(y_position):
            confidence += 0.2
        else:
            # 너무 하단이면 감소
            if y_position > 0.6:
                confidence -= 0.2

        # 4. 폰트 크기 확인
        font_size = line.get('height', 0)
        if avg_font_size > 0:
            font_ratio = font_size / avg_font_size
            if font_ratio >= ParsingRules.FONT_RATIO_CONCEPT:
                confidence += 0.1

        # 5. 한글 제목 포함 여부
        if re.search(r'[가-힣]{2,}', text):
            confidence += 0.1

        return confidence >= 0.5, confidence

    def find_block_end(
        self,
        lines: List[Dict[str, Any]],
        start_idx: int,
        page_height: float,
        avg_font_size: float
    ) -> int:
        """
        개념 블록 종료 지점 찾기

        종료 조건:
        1. 다음 개념 시작
        2. 작품 시작
        3. 문제 시작
        4. 연속 빈 줄
        """
        end_idx = start_idx
        blank_count = 0

        for i in range(start_idx + 1, len(lines)):
            line = lines[i]
            text = self._get_line_text(line)
            y_position = line.get('top', 0) / page_height if page_height > 0 else 0.0

            # 빈 줄 카운트
            if not text:
                blank_count += 1
                if blank_count >= 3:
                    break
                end_idx = i
                continue
            else:
                blank_count = 0

            # 다음 개념 시작
            if self._matches_start_patterns(text):
                break

            # 작품 시작
            passage_patterns = ParsingRules.get_start_patterns('passage')
            from .parsing_rules import matches_any_pattern
            if matches_any_pattern(text, passage_patterns):
                break

            # 문제 시작
            question_patterns = ParsingRules.get_start_patterns('question')
            if matches_any_pattern(text, question_patterns):
                break

            # 페이지 중단 이후로 내려가면 종료 (개념은 주로 상단)
            if y_position > 0.5:
                # 단, 개념 내용이 길 수 있으므로 조심스럽게
                # 작품 패턴이나 문제 패턴이 나오기 전까지는 포함
                pass

            end_idx = i

        return end_idx

    def extract_metadata(
        self,
        lines: List[Dict[str, Any]],
        start_idx: int,
        end_idx: int
    ) -> BlockMetadata:
        """
        개념 메타데이터 추출

        추출 항목:
        - concept_id: 개념 ID
        - title: 개념 제목
        """
        metadata = BlockMetadata()

        if start_idx < len(lines):
            first_line = lines[start_idx]
            first_text = self._get_line_text(first_line)

            # 개념 번호 추출
            concept_num = self._extract_concept_number(first_text)
            if concept_num:
                metadata.concept_id = concept_num
                metadata.signals_matched.append(f"concept_number:{concept_num}")

            # 제목 추출 (번호 제거)
            title = re.sub(r'^\(\d+\)\s*', '', first_text)
            title = re.sub(r'^[①-⑳]\s*', '', title)
            title = re.sub(r'^\d+[\.\)]\s*', '', title)
            metadata.title = title.strip()[:100]

            metadata.confidence = 0.8

        return metadata

    def _extract_concept_number(self, text: str) -> str:
        """
        개념 번호 추출
        "(1)", "①", "1." 등
        """
        # 패턴 1: (1), (2)
        match = re.match(r'^\((\d+)\)', text)
        if match:
            return f"({match.group(1)})"

        # 패턴 2: ①, ②
        match = re.match(r'^([①-⑳])', text)
        if match:
            return match.group(1)

        # 패턴 3: 1., 2.
        match = re.match(r'^(\d+)[\.\)]', text)
        if match:
            return match.group(1)

        return ""
