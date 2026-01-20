"""
문제(Question) 블록 파서
우선순위: 1 (최우선)
"""
from typing import List, Dict, Any, Tuple

from .base_parser import BaseParser
from .intermediate_schema import BlockType, BlockMetadata
from .parsing_rules import ParsingRules


class QuestionParser(BaseParser):
    """문제 블록 파서"""

    def __init__(self):
        super().__init__(BlockType.QUESTION)

    def can_start_block(
        self,
        lines: List[Dict[str, Any]],
        line_idx: int,
        page_height: float,
        avg_font_size: float
    ) -> Tuple[bool, float]:
        """
        문제 블록 시작 확인

        조건:
        1. 문제 번호 패턴 매칭 ("01", "02" 등)
        2. 페이지 하단 영역 (y > 0.6)
        3. 큰 폰트 크기 (평균 * 1.2 이상)
        4. 부정 패턴 없음
        """
        if line_idx >= len(lines):
            return False, 0.0

        line = lines[line_idx]
        text = self._get_line_text(line)

        if not text:
            return False, 0.0

        # 신뢰도 점수
        confidence = 0.0

        # 1. 부정 패턴 체크 (먼저 확인)
        if self._matches_negative_patterns(text):
            return False, 0.0

        # 2. 시작 패턴 매칭 (가장 중요)
        if self._matches_start_patterns(text):
            confidence += 0.5

            # 문제 번호 추출 시도
            problem_num = self.normalizer.extract_problem_number(text)
            if problem_num:
                confidence += 0.2
        else:
            return False, 0.0

        # 3. 위치 확인 (페이지 하단)
        y_position = line.get('top', 0) / page_height if page_height > 0 else 0.0
        if self._is_in_start_position(y_position):
            confidence += 0.2
        else:
            # 위치가 너무 상단이면 신뢰도 감소
            if y_position < 0.4:
                confidence -= 0.3

        # 4. 폰트 크기 확인
        font_size = line.get('height', 0)
        if avg_font_size > 0:
            font_ratio = font_size / avg_font_size
            if font_ratio >= ParsingRules.FONT_RATIO_QUESTION:
                confidence += 0.1

        # 최종 신뢰도가 임계값 이상이면 시작 가능
        return confidence >= 0.6, confidence

    def find_block_end(
        self,
        lines: List[Dict[str, Any]],
        start_idx: int,
        page_height: float,
        avg_font_size: float
    ) -> int:
        """
        문제 블록 종료 지점 찾기

        종료 조건:
        1. 다음 문제 번호 감지
        2. 페이지 끝
        3. 다음 concept/passage 시작 (드물지만)
        """
        end_idx = start_idx

        for i in range(start_idx + 1, len(lines)):
            line = lines[i]
            text = self._get_line_text(line)

            # 빈 줄은 스킵 (문제 내용에 포함)
            if not text:
                end_idx = i
                continue

            # 다음 문제 번호 감지 (종료)
            if self._matches_start_patterns(text):
                # 추가 검증: 정말 문제 번호인지
                problem_num = self.normalizer.extract_problem_number(text)
                if problem_num:
                    break

            # 다음 블록 시작 패턴 감지 (개념, 작품)
            concept_patterns = ParsingRules.get_start_patterns('concept')
            passage_patterns = ParsingRules.get_start_patterns('passage')

            from .parsing_rules import matches_any_pattern
            if (matches_any_pattern(text, concept_patterns) or
                matches_any_pattern(text, passage_patterns)):
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
        문제 메타데이터 추출

        추출 항목:
        - question_id: 문제 번호 ("01", "02" 등)
        - title: 문제의 첫 줄 (질문 내용)
        """
        metadata = BlockMetadata()

        if start_idx < len(lines):
            first_line = lines[start_idx]
            first_text = self._get_line_text(first_line)

            # 문제 번호 추출
            question_id = self.normalizer.extract_problem_number(first_text)
            if question_id:
                metadata.question_id = question_id
                metadata.signals_matched.append(f"question_number:{question_id}")

            # 문제 제목 (첫 줄 또는 두 번째 줄)
            if start_idx + 1 < len(lines):
                title_line = lines[start_idx + 1]
                title_text = self._get_line_text(title_line)
                if title_text:
                    # 너무 길면 앞부분만
                    metadata.title = title_text[:100]
            else:
                metadata.title = first_text

            metadata.confidence = 0.9

        return metadata
