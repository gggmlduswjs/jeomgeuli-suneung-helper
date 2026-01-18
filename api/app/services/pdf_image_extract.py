"""
PDF 이미지 캡처 서비스
문제/본문 영역을 이미지로 추출
"""
try:
    from pdf2image import convert_from_path
except ImportError:
    convert_from_path = None

from PIL import Image
import io
import base64
from pathlib import Path
from typing import List, Dict, Tuple, Optional


class PDFImageExtractor:
    def __init__(self, dpi: int = 150):
        self.dpi = dpi  # 이미지 해상도
        
    def extract_question_images(
        self, 
        pdf_path: Path, 
        question_positions: List[Dict]
    ) -> List[Dict]:
        """문제 영역을 이미지로 추출"""
        images = []
        
        try:
            for q_pos in question_positions:
                page_num = q_pos.get("page", 1)
                bbox = q_pos.get("bbox")  # (x0, y0, x1, y1)
                
                # PDF 페이지를 이미지로 변환
                try:
                    if convert_from_path:
                        # pdf2image 사용
                        images_list = convert_from_path(
                            pdf_path,
                            first_page=page_num,
                            last_page=page_num,
                            dpi=self.dpi
                        )
                        if images_list:
                            page_image = images_list[0]
                        else:
                            continue
                    else:
                        # pdfplumber fallback (제한적 지원)
                        import pdfplumber
                        with pdfplumber.open(pdf_path) as pdf:
                            if page_num > len(pdf.pages):
                                continue
                            page = pdf.pages[page_num - 1]
                            page_image_obj = page.to_image(resolution=self.dpi)
                            page_image = page_image_obj.original
                    
                    # 영역 자르기
                    if bbox:
                        cropped = page_image.crop(bbox)
                    else:
                        # bbox가 없으면 전체 페이지 또는 자동 감지
                        cropped = self._auto_crop_question(page_image, q_pos)
                    
                    # 이미지를 base64로 인코딩
                    img_bytes = io.BytesIO()
                    cropped.save(img_bytes, format='PNG')
                    img_base64 = base64.b64encode(img_bytes.getvalue()).decode()
                    
                    images.append({
                        "question_number": q_pos.get("number"),
                        "image": f"data:image/png;base64,{img_base64}",
                        "page": page_num,
                        "bbox": bbox
                    })
                except Exception as e:
                    print(f"[pdf_image_extract] Error extracting question image: {e}")
                    continue
        except Exception as e:
            print(f"[pdf_image_extract] Error processing PDF: {e}")
        
        return images
    
    def extract_passage_images(
        self,
        pdf_path: Path,
        passage_positions: List[Dict]
    ) -> List[Dict]:
        """본문 영역을 이미지로 추출"""
        images = []
        
        try:
            for p_pos in passage_positions:
                page_num = p_pos.get("page", 1)
                bbox = p_pos.get("bbox")
                
                try:
                    if convert_from_path:
                        # pdf2image 사용
                        images_list = convert_from_path(
                            pdf_path,
                            first_page=page_num,
                            last_page=page_num,
                            dpi=self.dpi
                        )
                        if images_list:
                            page_image = images_list[0]
                        else:
                            continue
                    else:
                        # pdfplumber fallback
                        import pdfplumber
                        with pdfplumber.open(pdf_path) as pdf:
                            if page_num > len(pdf.pages):
                                continue
                            page = pdf.pages[page_num - 1]
                            page_image_obj = page.to_image(resolution=self.dpi)
                            page_image = page_image_obj.original
                    
                    if bbox:
                        cropped = page_image.crop(bbox)
                    else:
                        cropped = self._auto_crop_passage(page_image, p_pos)
                    
                    img_bytes = io.BytesIO()
                    cropped.save(img_bytes, format='PNG')
                    img_base64 = base64.b64encode(img_bytes.getvalue()).decode()
                    
                    images.append({
                        "passage_title": p_pos.get("title"),
                        "image": f"data:image/png;base64,{img_base64}",
                        "page": page_num,
                        "bbox": bbox
                    })
                except Exception as e:
                    print(f"[pdf_image_extract] Error extracting passage image: {e}")
                    continue
        except Exception as e:
            print(f"[pdf_image_extract] Error processing PDF: {e}")
        
        return images
    
    def _auto_crop_question(self, page_image: Image.Image, question_pos: Dict) -> Image.Image:
        """문제 영역 자동 감지 및 자르기"""
        # OCR 또는 레이아웃 분석으로 문제 영역 감지
        # 또는 텍스트 위치 기반으로 영역 추정
        # 현재는 전체 페이지 반환 (향후 ML 모델로 개선)
        return page_image
    
    def _auto_crop_passage(self, page_image: Image.Image, passage_pos: Dict) -> Image.Image:
        """본문 영역 자동 감지 및 자르기"""
        # 현재는 전체 페이지 반환 (향후 ML 모델로 개선)
        return page_image
