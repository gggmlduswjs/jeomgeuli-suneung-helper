"""
기본 파서 클래스
과목별 파서의 공통 기능 제공
"""
import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class BaseParser(ABC):
    """과목별 파서의 기본 클래스"""

    @staticmethod
    def group_lines(
        ocr_data: Dict[str, Any],
        y_threshold: int = 10
    ) -> List[List[Dict[str, Any]]]:
        """
        OCR 데이터를 줄 단위로 그룹화

        Args:
            ocr_data: OCR 결과 딕셔너리 (text, top, left, width, height 리스트 포함)
            y_threshold: 같은 줄 판단 y좌표 임계값 (픽셀)

        Returns:
            줄별 단어 리스트 (각 줄은 단어 딕셔너리 리스트)
        """
        texts = ocr_data.get('text', [])
        tops = ocr_data.get('top', [])
        lefts = ocr_data.get('left', [])
        widths = ocr_data.get('width', [])
        heights = ocr_data.get('height', [])

        if not texts or not tops:
            return []

        # 단어 정보 수집
        words = []
        for i in range(len(texts)):
            text = texts[i].strip() if i < len(texts) else ""
            if not text:
                continue

            word = {
                'text': text,
                'top': tops[i] if i < len(tops) else 0,
                'left': lefts[i] if i < len(lefts) else 0,
                'width': widths[i] if i < len(widths) else 0,
                'height': heights[i] if i < len(heights) else 0,
                'index': i
            }
            words.append(word)

        if not words:
            return []

        # y좌표 기준으로 정렬
        words.sort(key=lambda w: (w['top'], w['left']))

        # 같은 줄로 그룹화
        lines = []
        current_line = [words[0]]
        current_y = words[0]['top']

        for word in words[1:]:
            # 같은 줄인지 확인
            if abs(word['top'] - current_y) <= y_threshold:
                current_line.append(word)
            else:
                # 새 줄 시작
                if current_line:
                    current_line.sort(key=lambda w: w['left'])
                    lines.append(current_line)
                current_line = [word]
                current_y = word['top']

        # 마지막 줄 추가
        if current_line:
            current_line.sort(key=lambda w: w['left'])
            lines.append(current_line)

        return lines

    @staticmethod
    def join_line_text(line: List[Dict[str, Any]]) -> str:
        """
        줄의 단어들을 하나의 문자열로 결합

        Args:
            line: 단어 딕셔너리 리스트

        Returns:
            결합된 텍스트
        """
        return ' '.join(word['text'] for word in line)

    @staticmethod
    def get_line_bbox(line: List[Dict[str, Any]]) -> List[int]:
        """
        줄의 bounding box 계산

        Args:
            line: 단어 딕셔너리 리스트

        Returns:
            [left, top, right, bottom]
        """
        if not line:
            return [0, 0, 0, 0]

        first_word = line[0]
        last_word = line[-1]

        left = first_word['left']
        top = first_word['top']
        right = last_word['left'] + last_word['width']
        bottom = max(w['top'] + w['height'] for w in line)

        return [left, top, right, bottom]

    @staticmethod
    def matches_patterns(text: str, patterns: List[str]) -> bool:
        """
        텍스트가 패턴 중 하나와 매칭되는지 확인

        Args:
            text: 검사할 텍스트
            patterns: 정규식 패턴 리스트

        Returns:
            매칭 여부
        """
        if not text or len(text.strip()) < 2:
            return False

        # 텍스트 정규화
        normalized_text = re.sub(r'\s+', ' ', text.strip())

        for pattern in patterns:
            try:
                if re.match(pattern, text) or re.match(pattern, normalized_text):
                    return True
                # 부분 매칭 (패턴이 텍스트 시작 부분과 일치)
                match = re.search(pattern, text) or re.search(pattern, normalized_text)
                if match and match.start() == 0:
                    return True
            except re.error:
                continue

        return False

    @abstractmethod
    def parse(self, ocr_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        OCR 데이터를 파싱하여 구조화된 데이터 반환

        Args:
            ocr_data: 페이지별 OCR 결과 리스트

        Returns:
            {
                'lectures': [...],
                'problems': [...],
                'metadata': {...}
            }
        """
        pass
