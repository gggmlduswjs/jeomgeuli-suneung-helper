"""
PDF 이미지 추출기
"""
from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image
import io
import base64

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

from .base_extractor import BaseExtractor


class ImageExtractor(BaseExtractor):
    """
    PDF에서 이미지(수식, 그래프 등)를 추출하는 클래스
    """
    
    def __init__(self, dpi: int = 150, output_dir: Optional[Path] = None):
        """
        Args:
            dpi: 이미지 해상도
            output_dir: 이미지 저장 디렉토리
        """
        self.dpi = dpi
        self.output_dir = output_dir
    
    def extract_blocks(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """
        PDF에서 이미지 블록만 추출
        """
        blocks = []
        
        if not PDF2IMAGE_AVAILABLE:
            raise ImportError("pdf2image가 설치되지 않았습니다. pip install pdf2image")
        
        try:
            images = convert_from_path(pdf_path, dpi=self.dpi)
            
            for page_num, page_image in enumerate(images, 1):
                # 페이지 전체를 이미지 블록으로 추가
                blocks.append({
                    "type": "image",
                    "page": page_num,
                    "bbox": [0, 0, page_image.width, page_image.height],
                    "content": self._save_image(page_image, pdf_path.stem, page_num),
                    "metadata": {
                        "width": page_image.width,
                        "height": page_image.height,
                        "dpi": self.dpi,
                        "format": "png",
                    }
                })
        
        except Exception as e:
            raise Exception(f"이미지 추출 실패: {e}")
        
        return blocks
    
    def _save_image(self, image: Image.Image, pdf_name: str, page_num: int) -> str:
        """이미지를 저장하고 경로 반환"""
        if self.output_dir:
            output_path = self.output_dir / f"{pdf_name}_page_{page_num}.png"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(output_path, "PNG")
            return str(output_path)
        else:
            # Base64 인코딩으로 반환
            img_bytes = io.BytesIO()
            image.save(img_bytes, format="PNG")
            img_base64 = base64.b64encode(img_bytes.getvalue()).decode()
            return f"data:image/png;base64,{img_base64}"
    
    def extract_text(self, pdf_path: Path) -> str:
        """텍스트 추출 없음"""
        return ""
