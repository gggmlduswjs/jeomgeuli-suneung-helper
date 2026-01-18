"""
수능특강 문학 PDF 추출기

문학 PDF의 특징:
- 텍스트가 핵심 (이미지는 거의 없음)
- 줄 단위 구조가 중요
- 줄 순서(y좌표 기준)를 유지해야 함
"""
import logging
import pdfplumber
from pathlib import Path
from typing import List, Dict, Any
from .base_extractor import BaseExtractor
from .exceptions import (
    PDFExtractionError,
    PDFNotFoundError,
    PDFCorruptedError
)
from .utils import validate_pdf_path

logger = logging.getLogger(__name__)


class LiteraturePDFExtractor(BaseExtractor):
    """
    문학 PDF 전용 추출기
    
    수학과 달리:
    - 텍스트 중심 추출
    - 줄 단위로 분리
    - 이미지는 거의 무시
    """
    
    def __init__(self, layout: bool = True):
        """
        Args:
            layout: 레이아웃 정보 고려 여부
        """
        self.layout = layout
    
    def extract_blocks(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """
        문학 PDF에서 줄 단위로 텍스트 추출
        
        Returns:
            List[Dict]: 각 줄의 정보
                - type: "text"
                - page: 페이지 번호
                - text: 줄 텍스트
                - bbox: [x0, y0, x1, y1]
                - line_number: 줄 번호 (페이지 내)
        """
        # 경로 검증
        validate_pdf_path(pdf_path)
        
        lines = []
        logger.info(f"문학 PDF 추출 시작: {pdf_path}")
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                logger.debug(f"PDF 페이지 수: {total_pages}")
                
                for page_num, page in enumerate(pdf.pages, 1):
                    # 텍스트를 줄 단위로 추출
                    page_lines = self._extract_lines_from_page(page, page_num)
                    lines.extend(page_lines)
                    
                    if page_num % 10 == 0:
                        logger.debug(f"처리 중: {page_num}/{total_pages} 페이지")
        
        except FileNotFoundError as e:
            logger.error(f"PDF 파일을 찾을 수 없음: {pdf_path}", exc_info=True)
            raise PDFNotFoundError("PDF 파일을 찾을 수 없습니다", pdf_path=pdf_path) from e
        except pdfplumber.exceptions.PDFSyntaxError as e:
            logger.error(f"PDF 파일 손상: {pdf_path}", exc_info=True)
            raise PDFCorruptedError("PDF 파일이 손상되었습니다", pdf_path=pdf_path) from e
        except Exception as e:
            logger.error(f"문학 PDF 추출 중 예상치 못한 오류: {pdf_path}", exc_info=True)
            raise PDFExtractionError(f"문학 PDF 추출 실패: {e}", pdf_path=pdf_path) from e
        
        logger.info(f"문학 PDF 추출 완료: {len(lines)}줄 추출됨 (파일: {pdf_path.name})")
        return lines
    
    def _extract_lines_from_page(self, page, page_num: int) -> List[Dict[str, Any]]:
        """
        페이지에서 줄 단위로 텍스트 추출
        
        y좌표 기준으로 정렬하여 줄 순서 유지
        """
        # 단어 추출
        words = page.extract_words(
            x_tolerance=3,
            y_tolerance=3
        )
        
        if not words:
            return []
        
        # y좌표 기준으로 정렬
        sorted_words = sorted(words, key=lambda w: (w.get("top", 0), w.get("left", 0)))
        
        # 같은 줄(y 좌표)의 단어들을 묶기
        lines = []
        current_line = {
            "words": [],
            "y_center": None,
            "bbox": None,
        }
        
        y_threshold = 5  # 같은 줄 판단 기준 (픽셀)
        
        for word in sorted_words:
            y_center = word.get("top", 0) + word.get("height", 0) / 2
            x0 = word.get("left", 0)
            y0 = word.get("top", 0)
            x1 = word.get("right", 0)
            y1 = word.get("bottom", 0)
            
            # 첫 단어 또는 새로운 줄
            if (current_line["y_center"] is None or 
                abs(y_center - current_line["y_center"]) > y_threshold):
                
                # 이전 줄 저장
                if current_line["words"]:
                    line_dict = self._create_line_dict(current_line, page_num, len(lines))
                    lines.append(line_dict)
                
                # 새 줄 시작
                current_line = {
                    "words": [word],
                    "y_center": y_center,
                    "bbox": [x0, y0, x1, y1],
                }
            else:
                # 같은 줄에 추가
                current_line["words"].append(word)
                # bbox 확장
                bbox = current_line["bbox"]
                current_line["bbox"] = [
                    min(bbox[0], x0),
                    min(bbox[1], y0),
                    max(bbox[2], x1),
                    max(bbox[3], y1),
                ]
        
        # 마지막 줄 저장
        if current_line["words"]:
            line_dict = self._create_line_dict(current_line, page_num, len(lines))
            lines.append(line_dict)
        
        return lines
    
    def _create_line_dict(self, line_data: Dict, page_num: int, line_index: int) -> Dict[str, Any]:
        """줄 데이터를 딕셔너리로 변환"""
        words = line_data["words"]
        text = " ".join([w.get("text", "") for w in words])
        
        return {
            "type": "text",
            "page": page_num,
            "text": text,
            "bbox": line_data["bbox"],
            "line_number": line_index + 1,  # 1-based
            "metadata": {
                "word_count": len(words),
                "char_count": len(text),
            }
        }
    
    def extract_text(self, pdf_path: Path) -> str:
        """
        순수 텍스트만 추출 (레거시 호환)
        
        문학은 줄 단위 구조가 중요하므로 줄바꿈 유지
        """
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text(layout=self.layout)
                if page_text:
                    text += page_text + "\n"
        return text.strip()
