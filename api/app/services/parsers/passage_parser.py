"""
작품 본문(Passage) 블록 파서
우선순위: 2
"""
from typing import List, Dict, Any, Tuple

from .base_parser import BaseParser
from .intermediate_schema import BlockType, BlockMetadata
from .parsing_rules import ParsingRules


class PassageParser(BaseParser):
    """작품 본문 파서"""

    def __init__(self):
        super().__init__(BlockType.PASSAGE)

    def can_start_block(
        self,
        lines: List[Dict[str, Any]],
        line_idx: int,
        page_height: float,
        avg_font_size: float
    ) -> Tuple[bool, float]:
        """
        작품 블록 시작 확인

        조건:
        1. 작품 표시 패턴 매칭 ("- 작가, 「작품」")
        2. 페이지 중단 영역
        3. 부정 패턴 없음
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

        # 2. 작품 표시 패턴 매칭 (가장 중요)
        if self._matches_start_patterns(text):
            confidence += 0.6

            # 작가/작품명 추출 시도
            work_info = self.normalizer.extract_work_info(text)
            if work_info:
                confidence += 0.2
        else:
            return False, 0.0

        # 3. 위치 확인 (페이지 중단)
        y_position = line.get('top', 0) / page_height if page_height > 0 else 0.0
        if self._is_in_start_position(y_position):
            confidence += 0.1

        # 4. 작품 괄호 「」 존재 확인
        if '「' in text and '」' in text:
            confidence += 0.1

        return confidence >= 0.6, confidence

    def find_block_end(
        self,
        lines: List[Dict[str, Any]],
        start_idx: int,
        page_height: float,
        avg_font_size: float
    ) -> int:
        """
        작품 블록 종료 지점 찾기

        종료 조건:
        1. 다음 작품 시작
        2. 문제 번호 감지
        3. 연속 빈 줄 (3줄 이상)
        4. 폰트 크기가 갑자기 증가 (다음 섹션 제목)
        """
        end_idx = start_idx
        blank_count = 0
        prev_font_size = lines[start_idx].get('height', 0)

        for i in range(start_idx + 1, len(lines)):
            line = lines[i]
            text = self._get_line_text(line)
            font_size = line.get('height', 0)

            # 빈 줄 카운트
            if not text:
                blank_count += 1
                # 연속 3줄 이상 빈 줄이면 종료
                if blank_count >= 3:
                    break
                end_idx = i
                continue
            else:
                blank_count = 0

            # 다음 작품 시작 감지
            if self._matches_start_patterns(text):
                break

            # 문제 번호 감지
            question_patterns = ParsingRules.get_start_patterns('question')
            from .parsing_rules import matches_any_pattern
            if matches_any_pattern(text, question_patterns):
                break

            # 폰트 크기 갑자기 증가 (다음 섹션)
            if prev_font_size > 0 and font_size > prev_font_size * 1.3:
                break

            end_idx = i
            prev_font_size = font_size

        return end_idx

    def extract_metadata(
        self,
        lines: List[Dict[str, Any]],
        start_idx: int,
        end_idx: int
    ) -> BlockMetadata:
        """
        작품 메타데이터 추출

        추출 항목:
        - author: 작가명
        - work_title: 작품명
        - passage_id: 작품 ID (페이지_작품명)
        """
        metadata = BlockMetadata()

        if start_idx < len(lines):
            first_line = lines[start_idx]
            first_text = self._get_line_text(first_line)

            # 작가/작품 정보 추출
            work_info = self.normalizer.extract_work_info(first_text)
            if work_info:
                metadata.author = work_info.get('author', '')
                metadata.work_title = work_info.get('work', '')
                metadata.signals_matched.append(f"work_pattern:author+work")

                # passage_id 생성
                page_num = lines[start_idx].get('page', 0)
                metadata.passage_id = f"p{page_num}_{metadata.work_title[:10]}"

                metadata.confidence = 0.9
            else:
                metadata.confidence = 0.5

            # 제목 설정
            if metadata.author and metadata.work_title:
                metadata.title = f"{metadata.author} - 「{metadata.work_title}」"
            else:
                metadata.title = first_text[:50]

        return metadata
