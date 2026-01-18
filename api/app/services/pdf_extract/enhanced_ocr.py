"""
Enhanced OCR: 전처리 + Tesseract OCR

OCR 정확도 향상을 위한 이미지 전처리 및 텍스트 추출
"""
import pytesseract
from PIL import Image
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
import io

try:
    import pdf2image
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False


class EnhancedOCR:
    """
    전처리 + OCR을 통한 텍스트 추출
    
    특징:
    - 이미지 전처리 (이진화, 노이즈 제거, 기울기 보정)
    - OCR (Tesseract)
    - 레이아웃 정보 보존 (bbox)
    """
    
    def __init__(self, lang: str = 'kor+eng', dpi: int = 300):
        """
        Args:
            lang: Tesseract 언어 코드 ('kor+eng', 'kor', 'eng' 등)
            dpi: PDF → 이미지 변환 해상도
        """
        self.lang = lang
        self.dpi = dpi
        
        # Windows에서 Tesseract 경로 자동 감지 시도
        try:
            # 기본 경로들 확인
            default_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            ]
            for path in default_paths:
                if Path(path).exists():
                    pytesseract.pytesseract.tesseract_cmd = path
                    break
        except Exception:
            pass  # 환경변수에서 찾기 시도
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        OCR 정확도 향상을 위한 이미지 전처리
        
        전처리 단계:
        1. Grayscale 변환
        2. 이진화 (Otsu thresholding)
        3. 노이즈 제거 (morphological operations)
        4. 스캔 기울기 보정 (deskew)
        
        Returns:
            전처리된 PIL Image
        """
        # PIL Image → numpy array
        img_array = np.array(image.convert('L'))  # Grayscale
        
        # 1. 이진화 (Otsu thresholding)
        _, binary = cv2.threshold(img_array, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 2. 노이즈 제거 (morphological operations)
        # 작은 노이즈 제거
        kernel = np.ones((2, 2), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
        
        # 3. 스캔 기울기 보정 (간단한 버전)
        # Hough Transform으로 선 검출 후 각도 계산
        try:
            # Canny 엣지 검출
            edges = cv2.Canny(cleaned, 50, 150, apertureSize=3)
            lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)
            
            if lines is not None:
                # 가장 긴 선의 각도 계산
                angles = []
                for rho, theta in lines[:10]:  # 상위 10개 선만
                    angle = np.degrees(theta) - 90
                    if -45 < angle < 45:  # 기울기 범위 제한
                        angles.append(angle)
                
                if angles:
                    # 중앙값 각도
                    angle = np.median(angles)
                    # 이미지 회전
                    center = (cleaned.shape[1] // 2, cleaned.shape[0] // 2)
                    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
                    cleaned = cv2.warpAffine(cleaned, rotation_matrix, 
                                            (cleaned.shape[1], cleaned.shape[0]),
                                            flags=cv2.INTER_CUBIC,
                                            borderMode=cv2.BORDER_REPLICATE)
        except Exception:
            # 기울기 보정 실패 시 원본 사용
            pass
        
        # numpy array → PIL Image
        return Image.fromarray(cleaned)
    
    def extract_text_with_ocr(self, image: Image.Image) -> str:
        """
        전처리된 이미지에서 OCR 수행 (순수 텍스트)
        
        Args:
            image: PIL Image
        
        Returns:
            추출된 텍스트
        """
        try:
            preprocessed = self.preprocess_image(image)
            text = pytesseract.image_to_string(preprocessed, lang=self.lang)
            return text.strip()
        except Exception as e:
            raise Exception(f"OCR 실패: {e}")
    
    def extract_with_layout(self, image: Image.Image) -> List[Dict[str, Any]]:
        """
        OCR + 레이아웃 정보 (bbox, confidence)
        
        Args:
            image: PIL Image
        
        Returns:
            List[Dict] with keys: text, bbox, confidence, page, word_index
        """
        try:
            preprocessed = self.preprocess_image(image)
            
            # OCR with layout info
            data = pytesseract.image_to_data(
                preprocessed, 
                lang=self.lang, 
                output_type=pytesseract.Output.DICT
            )
            
            blocks = []
            for i, text in enumerate(data['text']):
                if text.strip() and data['conf'][i] > 0:
                    blocks.append({
                        "text": text.strip(),
                        "bbox": [
                            data['left'][i],
                            data['top'][i],
                            data['left'][i] + data['width'][i],
                            data['top'][i] + data['height'][i]
                        ],
                        "confidence": float(data['conf'][i]) / 100.0,  # 0-100 → 0-1
                        "word_index": data['word_num'][i],
                        "line_index": data['line_num'][i],
                        "block_index": data['block_num'][i],
                    })
            
            return blocks
        except Exception as e:
            raise Exception(f"OCR with layout 실패: {e}")
    
    def extract_from_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """
        PDF 파일에서 OCR로 텍스트 추출
        
        Args:
            pdf_path: PDF 파일 경로
        
        Returns:
            Dict with keys: text, blocks, pages
        """
        if not PDF2IMAGE_AVAILABLE:
            raise ImportError("pdf2image가 설치되지 않았습니다. pip install pdf2image")
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
        
        # PDF → 이미지 변환
        images = pdf2image.convert_from_path(pdf_path, dpi=self.dpi)
        
        all_text = []
        all_blocks = []
        
        for page_num, page_image in enumerate(images, 1):
            # OCR 수행
            page_text = self.extract_text_with_ocr(page_image)
            page_blocks = self.extract_with_layout(page_image)
            
            # 페이지 정보 추가
            for block in page_blocks:
                block["page"] = page_num
            
            all_text.append(page_text)
            all_blocks.extend(page_blocks)
        
        return {
            "text": "\n\n".join(all_text),
            "blocks": all_blocks,
            "pages": len(images),
            "total_blocks": len(all_blocks),
        }
    
    def extract_from_page_image(self, page_image: Image.Image, page_num: int = 1) -> Dict[str, Any]:
        """
        단일 페이지 이미지에서 OCR 수행
        
        Args:
            page_image: PIL Image
            page_num: 페이지 번호
        
        Returns:
            Dict with keys: text, blocks, page
        """
        text = self.extract_text_with_ocr(page_image)
        blocks = self.extract_with_layout(page_image)
        
        # 페이지 정보 추가
        for block in blocks:
            block["page"] = page_num
        
        return {
            "text": text,
            "blocks": blocks,
            "page": page_num,
            "total_blocks": len(blocks),
        }


def test_enhanced_ocr():
    """Enhanced OCR 테스트"""
    ocr = EnhancedOCR(lang='kor+eng')
    
    # 테스트 이미지 경로 (실제 경로로 변경)
    test_image_path = Path("../data/test_images/test_scan.jpg")
    
    if test_image_path.exists():
        image = Image.open(test_image_path)
        result = ocr.extract_from_page_image(image)
        
        print(f"✅ OCR 완료")
        print(f"📊 추출된 블록 수: {result['total_blocks']}")
        print(f"📝 텍스트 샘플 (처음 200자):")
        print(result['text'][:200])
    else:
        print(f"❌ 테스트 이미지를 찾을 수 없습니다: {test_image_path}")


if __name__ == "__main__":
    test_enhanced_ocr()
