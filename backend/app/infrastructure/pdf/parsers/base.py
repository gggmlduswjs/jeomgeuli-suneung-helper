"""
기본 파서 클래스
과목별 파서의 공통 기능 제공
"""
import re
from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from pathlib import Path
import logging

from app.infrastructure.pdf.types import OCRPageData, ParsingResult, SectionData, ParagraphData, JSONDict

logger = logging.getLogger(__name__)


class BaseParser(ABC):
    """과목별 파서의 기본 클래스"""

    @staticmethod
    def group_lines(
        ocr_data: OCRPageData,
        y_threshold: int = 10
    ) -> List[List[JSONDict]]:
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
    def join_line_text(line: List[JSONDict]) -> str:
        """
        줄의 단어들을 하나의 문자열로 결합

        Args:
            line: 단어 딕셔너리 리스트

        Returns:
            결합된 텍스트
        """
        return ' '.join(word['text'] for word in line)

    @staticmethod
    def get_line_bbox(line: List[JSONDict]) -> List[int]:
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

    @staticmethod
    def crop_section_images(
        pdf_path: Path,
        sections: List[SectionData],
        output_dir: Optional[Path] = None,
        book_id: Optional[str] = None
    ) -> List[SectionData]:
        """
        섹션별 이미지 크롭 및 저장

        Args:
            pdf_path: PDF 파일 경로
            sections: 섹션 리스트 (bbox 포함)
            output_dir: 이미지 저장 디렉토리 (None이면 자동 생성)
            book_id: 책 ID (저장 디렉토리 이름에 사용)

        Returns:
            이미지 경로가 추가된 섹션 리스트
        """
        if not pdf_path or not pdf_path.exists():
            logger.warning(f"[이미지 크롭] PDF 파일 없음: {pdf_path}")
            return sections

        if not sections:
            return sections

        try:
            from pdf2image import convert_from_path
            from PIL import Image
            from app.core.config import settings

            # 출력 디렉토리 설정
            if not output_dir:
                base_dir = Path("backend/data/parsing_results/images")
                if book_id:
                    output_dir = base_dir / book_id
                else:
                    output_dir = base_dir / "default"

            output_dir.mkdir(parents=True, exist_ok=True)

            # 페이지별로 섹션 그룹화
            sections_by_page: Dict[int, List[SectionData]] = {}
            for section in sections:
                page_num = section.get('page')
                if not page_num or not section.get('bbox'):
                    continue

                if page_num not in sections_by_page:
                    sections_by_page[page_num] = []
                sections_by_page[page_num].append(section)

            # 각 페이지 처리
            for page_num, page_sections in sections_by_page.items():
                try:
                    # PDF 페이지를 이미지로 변환
                    convert_kwargs = {
                        "dpi": 300,
                        "first_page": page_num,
                        "last_page": page_num,
                    }
                    if hasattr(settings, 'POPPLER_PATH') and settings.POPPLER_PATH:
                        convert_kwargs["poppler_path"] = settings.POPPLER_PATH

                    page_images = convert_from_path(str(pdf_path), **convert_kwargs)
                    if not page_images:
                        logger.warning(f"[이미지 크롭] 페이지 {page_num} 이미지 변환 실패")
                        continue

                    page_image = page_images[0]
                    img_width, img_height = page_image.size

                    # 해당 페이지의 모든 섹션 처리
                    for idx, section in enumerate(page_sections):
                        bbox = section.get('bbox')
                        if not bbox or len(bbox) != 4:
                            continue

                        section_type = section.get('type', 'unknown')

                        # bbox 좌표 검증 및 제한
                        x_min, y_min, x_max, y_max = bbox
                        left = max(0, min(int(x_min), img_width - 1))
                        top = max(0, min(int(y_min), img_height - 1))
                        right = max(left + 1, min(int(x_max), img_width))
                        bottom = max(top + 1, min(int(y_max), img_height))

                        # 영역 이미지 크롭
                        try:
                            region_image = page_image.crop((left, top, right, bottom))

                            # 파일명 생성: {type}_p{page}_{index}.png
                            filename = f"{section_type}_p{page_num:03d}_{idx:02d}.png"
                            image_path = output_dir / filename
                            region_image.save(image_path, 'PNG')

                            # 섹션에 이미지 경로 추가
                            section['image_path'] = str(image_path)

                            logger.info(
                                f"[이미지 크롭] {filename} 저장 "
                                f"({section_type}, 페이지 {page_num})"
                            )

                        except Exception as e:
                            logger.error(
                                f"[이미지 크롭] 영역 크롭 실패 "
                                f"(페이지 {page_num}, {section_type}): {e}"
                            )

                except Exception as e:
                    logger.error(f"[이미지 크롭] 페이지 {page_num} 처리 실패: {e}")

            return sections

        except ImportError as e:
            logger.warning(f"[이미지 크롭] 필수 라이브러리 없음: {e}")
            return sections
        except Exception as e:
            logger.error(f"[이미지 크롭] 실패: {e}", exc_info=True)
            return sections

    @abstractmethod
    def parse(self, ocr_data: List[OCRPageData]) -> ParsingResult:
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

    @abstractmethod
    def extract_sections(
        self,
        lecture_ocr_data: List[OCRPageData]
    ) -> List[SectionData]:
        """
        섹션 추출 (메인 개념 + 본문)
        
        모든 파서가 구현해야 하는 필수 메서드
        
        Args:
            lecture_ocr_data: 강의에 해당하는 OCR 데이터 리스트
            
        Returns:
            섹션 리스트 (각 섹션은 title, type, page, bbox 포함)
        """
        pass

    @abstractmethod
    def extract_content_paragraphs(
        self,
        lecture_ocr_data: List[OCRPageData],
        sections: List[SectionData]
    ) -> List[ParagraphData]:
        """
        섹션별 문단 추출
        
        모든 파서가 구현해야 하는 필수 메서드
        
        Args:
            lecture_ocr_data: 강의에 해당하는 OCR 데이터 리스트
            sections: 이미 추출된 섹션 리스트
            
        Returns:
            문단 리스트 (각 문단은 text, page, y_start, y_end, bbox 포함)
        """
        pass
