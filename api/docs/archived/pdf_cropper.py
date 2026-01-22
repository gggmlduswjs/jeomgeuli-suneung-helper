"""
PDF 크롭/추출 유틸리티
특정 페이지 범위나 영역을 추출
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pdfplumber
from PyPDF2 import PdfReader, PdfWriter

logger = logging.getLogger(__name__)


class PDFCropper:
    """
    PDF에서 특정 페이지 범위나 영역을 추출하는 클래스
    """
    
    def __init__(self):
        pass
    
    def extract_page_range(
        self,
        pdf_path: Path,
        start_page: int,
        end_page: Optional[int] = None,
        output_path: Optional[Path] = None
    ) -> Path:
        """
        PDF에서 특정 페이지 범위를 추출하여 새 PDF 파일 생성
        
        Args:
            pdf_path: 원본 PDF 파일 경로
            start_page: 시작 페이지 (1-based)
            end_page: 끝 페이지 (1-based, None이면 start_page만)
            output_path: 출력 파일 경로 (None이면 자동 생성)
        
        Returns:
            생성된 PDF 파일 경로
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
        
        if end_page is None:
            end_page = start_page
        
        if start_page < 1:
            raise ValueError("시작 페이지는 1 이상이어야 합니다.")
        
        # 출력 경로 자동 생성
        if output_path is None:
            output_dir = pdf_path.parent / "cropped"
            output_dir.mkdir(exist_ok=True)
            stem = pdf_path.stem
            output_path = output_dir / f"{stem}_pages_{start_page}-{end_page}.pdf"
        
        try:
            reader = PdfReader(str(pdf_path))
            total_pages = len(reader.pages)
            
            if start_page > total_pages:
                raise ValueError(f"시작 페이지({start_page})가 총 페이지 수({total_pages})보다 큽니다.")
            
            if end_page > total_pages:
                logger.warning(f"끝 페이지({end_page})가 총 페이지 수({total_pages})보다 큽니다. {total_pages}로 조정합니다.")
                end_page = total_pages
            
            writer = PdfWriter()
            
            # 페이지 범위 추출 (0-based 인덱스)
            for page_num in range(start_page - 1, end_page):
                writer.add_page(reader.pages[page_num])
            
            # 파일 저장
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            
            logger.info(f"페이지 범위 추출 완료: {start_page}-{end_page} → {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"페이지 범위 추출 실패: {e}", exc_info=True)
            raise
    
    def extract_blocks_from_page_range(
        self,
        pdf_path: Path,
        start_page: int,
        end_page: Optional[int] = None,
        bbox: Optional[Tuple[float, float, float, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        PDF에서 특정 페이지 범위의 블록만 추출 (텍스트/이미지)
        
        Args:
            pdf_path: PDF 파일 경로
            start_page: 시작 페이지 (1-based)
            end_page: 끝 페이지 (1-based, None이면 start_page만)
            bbox: 영역 지정 [x0, y0, x1, y1] (None이면 전체 페이지)
        
        Returns:
            추출된 블록 리스트
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
        
        if end_page is None:
            end_page = start_page
        
        blocks = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                
                if start_page > total_pages:
                    raise ValueError(f"시작 페이지({start_page})가 총 페이지 수({total_pages})보다 큽니다.")
                
                if end_page > total_pages:
                    end_page = total_pages
                
                for page_num in range(start_page - 1, end_page):  # 0-based
                    page = pdf.pages[page_num]
                    
                    # 영역 지정이 있으면 해당 영역만 추출
                    if bbox:
                        cropped_page = page.crop(bbox)
                        page_blocks = self._extract_blocks_from_page(cropped_page, page_num + 1)
                    else:
                        page_blocks = self._extract_blocks_from_page(page, page_num + 1)
                    
                    blocks.extend(page_blocks)
            
            logger.info(f"블록 추출 완료: {len(blocks)}개 블록 (페이지 {start_page}-{end_page})")
            return blocks
            
        except Exception as e:
            logger.error(f"블록 추출 실패: {e}", exc_info=True)
            raise
    
    def _extract_blocks_from_page(self, page, page_num: int) -> List[Dict[str, Any]]:
        """페이지에서 블록 추출"""
        blocks = []
        
        # 텍스트 추출
        words = page.extract_words()
        if words:
            # 단어들을 문장 단위로 그룹화
            text_blocks = self._group_words_to_blocks(words, page_num)
            blocks.extend(text_blocks)
        
        # 이미지 추출
        images = page.images
        for img in images:
            blocks.append({
                "type": "image",
                "page": page_num,
                "bbox": img.get("bbox", [0, 0, 0, 0]),
                "content": None,
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
        
        return blocks
    
    def _group_words_to_blocks(self, words: List[Dict], page_num: int) -> List[Dict[str, Any]]:
        """단어 리스트를 블록으로 그룹화"""
        if not words:
            return []
        
        sorted_words = sorted(words, key=lambda w: (w.get("top", 0), w.get("left", 0)))
        
        blocks = []
        current_block = {
            "words": [],
            "bbox": None,
            "y_center": None,
        }
        
        y_threshold = 5
        
        for word in sorted_words:
            y_center = word.get("top", 0) + word.get("height", 0) / 2
            x0 = word.get("left", 0)
            y0 = word.get("top", 0)
            x1 = word.get("right", 0)
            y1 = word.get("bottom", 0)
            
            if (current_block["y_center"] is None or 
                abs(y_center - current_block["y_center"]) > y_threshold):
                
                if current_block["words"]:
                    blocks.append(self._create_text_block(current_block, page_num))
                
                current_block = {
                    "words": [word],
                    "bbox": [x0, y0, x1, y1],
                    "y_center": y_center,
                }
            else:
                current_block["words"].append(word)
                bbox = current_block["bbox"]
                current_block["bbox"] = [
                    min(bbox[0], x0),
                    min(bbox[1], y0),
                    max(bbox[2], x1),
                    max(bbox[3], y1),
                ]
        
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


def crop_pdf_pages(
    pdf_path: Path,
    start_page: int,
    end_page: Optional[int] = None,
    output_path: Optional[Path] = None
) -> Path:
    """
    편의 함수: PDF에서 페이지 범위 추출
    
    Args:
        pdf_path: 원본 PDF 파일 경로
        start_page: 시작 페이지 (1-based)
        end_page: 끝 페이지 (1-based, None이면 start_page만)
        output_path: 출력 파일 경로
    
    Returns:
        생성된 PDF 파일 경로
    """
    cropper = PDFCropper()
    return cropper.extract_page_range(pdf_path, start_page, end_page, output_path)


def extract_pdf_blocks_from_range(
    pdf_path: Path,
    start_page: int,
    end_page: Optional[int] = None,
    bbox: Optional[Tuple[float, float, float, float]] = None
) -> List[Dict[str, Any]]:
    """
    편의 함수: PDF에서 페이지 범위의 블록 추출
    
    Args:
        pdf_path: PDF 파일 경로
        start_page: 시작 페이지 (1-based)
        end_page: 끝 페이지 (1-based, None이면 start_page만)
        bbox: 영역 지정 [x0, y0, x1, y1] (None이면 전체 페이지)
    
    Returns:
        추출된 블록 리스트
    """
    cropper = PDFCropper()
    return cropper.extract_blocks_from_page_range(pdf_path, start_page, end_page, bbox)
