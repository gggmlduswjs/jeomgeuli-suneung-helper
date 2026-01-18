"""
PDFPlumber 기반 PDF 추출기
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


class PDFPlumberExtractor(BaseExtractor):
    """
    PDFPlumber를 사용한 텍스트/이미지 블록 추출기
    """
    
    def __init__(self, x_tolerance: int = 3, y_tolerance: int = 3, layout: bool = True):
        """
        Args:
            x_tolerance: 가로 방향 단어 간격 허용 범위
            y_tolerance: 세로 방향 단어 간격 허용 범위
            layout: 레이아웃 정보 고려 여부
        """
        self.x_tolerance = x_tolerance
        self.y_tolerance = y_tolerance
        self.layout = layout
    
    def extract_blocks(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """
        PDF에서 모든 블록 추출 (텍스트, 이미지, 테이블)
        """
        # 경로 검증
        validate_pdf_path(pdf_path)
        
        blocks = []
        logger.info(f"PDF 추출 시작: {pdf_path}")
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                logger.debug(f"PDF 페이지 수: {total_pages}")
                
                for page_num, page in enumerate(pdf.pages, 1):
                    # 텍스트 블록 추출
                    words = page.extract_words(
                        x_tolerance=self.x_tolerance,
                        y_tolerance=self.y_tolerance
                    )
                    
                    if words:
                        # 단어들을 문장/문단 단위로 그룹화
                        text_blocks = self._group_words_to_blocks(words, page_num)
                        blocks.extend(text_blocks)
                    
                    # 이미지 추출
                    images = page.images
                    for img in images:
                        blocks.append({
                            "type": "image",
                            "page": page_num,
                            "bbox": img.get("bbox", [0, 0, 0, 0]),
                            "content": None,  # 이미지는 별도 저장 필요
                            "metadata": {
                                "width": img.get("width", 0),
                                "height": img.get("height", 0),
                                "name": img.get("name", ""),
                            }
                        })
                    
                    # 테이블 추출
                    tables = page.extract_tables()
                    for table_idx, table in enumerate(tables):
                        blocks.append({
                            "type": "table",
                            "page": page_num,
                            "bbox": page.bbox,
                            "content": table,
                            "metadata": {
                                "table_index": table_idx,
                                "rows": len(table),
                                "cols": len(table[0]) if table else 0,
                            }
                        })
        
        except FileNotFoundError as e:
            logger.error(f"PDF 파일을 찾을 수 없음: {pdf_path}", exc_info=True)
            raise PDFNotFoundError("PDF 파일을 찾을 수 없습니다", pdf_path=pdf_path) from e
        except pdfplumber.exceptions.PDFSyntaxError as e:
            logger.error(f"PDF 파일 손상: {pdf_path}", exc_info=True)
            raise PDFCorruptedError("PDF 파일이 손상되었습니다", pdf_path=pdf_path) from e
        except Exception as e:
            logger.error(f"PDF 추출 중 예상치 못한 오류: {pdf_path}", exc_info=True)
            raise PDFExtractionError(f"PDF 추출 실패: {e}", pdf_path=pdf_path) from e
        
        logger.info(f"PDF 추출 완료: {len(blocks)}개 블록 추출됨 (파일: {pdf_path.name})")
        return blocks
    
    def _group_words_to_blocks(self, words: List[Dict], page_num: int) -> List[Dict[str, Any]]:
        """
        단어 리스트를 블록으로 그룹화
        
        간단한 구현: 같은 줄(y 좌표)의 단어들을 하나의 블록으로
        """
        if not words:
            return []
        
        # y 좌표 기준으로 정렬
        sorted_words = sorted(words, key=lambda w: (w.get("top", 0), w.get("left", 0)))
        
        blocks = []
        current_block = {
            "words": [],
            "bbox": None,
            "y_center": None,
        }
        
        y_threshold = 5  # 같은 줄 판단 기준 (픽셀)
        
        for word in sorted_words:
            y_center = word.get("top", 0) + word.get("height", 0) / 2
            x0 = word.get("left", 0)
            y0 = word.get("top", 0)
            x1 = word.get("right", 0)
            y1 = word.get("bottom", 0)
            
            # 첫 단어 또는 새로운 줄
            if (current_block["y_center"] is None or 
                abs(y_center - current_block["y_center"]) > y_threshold):
                
                # 이전 블록 저장
                if current_block["words"]:
                    blocks.append(self._create_text_block(current_block, page_num))
                
                # 새 블록 시작
                current_block = {
                    "words": [word],
                    "bbox": [x0, y0, x1, y1],
                    "y_center": y_center,
                }
            else:
                # 같은 줄에 추가
                current_block["words"].append(word)
                # bbox 확장
                bbox = current_block["bbox"]
                current_block["bbox"] = [
                    min(bbox[0], x0),
                    min(bbox[1], y0),
                    max(bbox[2], x1),
                    max(bbox[3], y1),
                ]
        
        # 마지막 블록 저장
        if current_block["words"]:
            blocks.append(self._create_text_block(current_block, page_num))
        
        return blocks
    
    def _create_text_block(self, block_data: Dict, page_num: int) -> Dict[str, Any]:
        """단어 리스트로부터 텍스트 블록 생성"""
        words = block_data["words"]
        text = " ".join([w.get("text", "") for w in words])
        
        return {
            "type": "text",
            "page": page_num,
            "bbox": block_data["bbox"],
            "content": text,
            "metadata": {
                "word_count": len(words),
                "char_count": len(text),
            }
        }
    
    def extract_text(self, pdf_path: Path) -> str:
        """
        순수 텍스트만 추출 (레거시 호환)
        """
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text(
                    layout=self.layout,
                    x_tolerance=self.x_tolerance,
                    y_tolerance=self.y_tolerance
                )
                if page_text:
                    text += page_text + "\n\n"
        return text.strip()
