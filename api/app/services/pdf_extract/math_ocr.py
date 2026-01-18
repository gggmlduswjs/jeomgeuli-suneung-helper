"""
Math OCR: 수식 이미지 인식 및 LaTeX 변환

수식 이미지 → LaTeX → Nemeth 점자 변환 파이프라인
"""
from PIL import Image
from typing import Dict, Any, Optional
import base64
import io

try:
    import mathpix
    MATHPIX_AVAILABLE = True
except ImportError:
    MATHPIX_AVAILABLE = False

try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False


class MathOCR:
    """
    수식 이미지 → LaTeX 변환기
    
    옵션:
    1. MathPix API (상용, 높은 정확도)
    2. PaddleOCR (오픈소스, 무료)
    """
    
    def __init__(self, use_mathpix: bool = False, mathpix_app_id: Optional[str] = None, mathpix_app_key: Optional[str] = None):
        """
        Args:
            use_mathpix: MathPix API 사용 여부
            mathpix_app_id: MathPix App ID
            mathpix_app_key: MathPix App Key
        """
        self.use_mathpix = use_mathpix
        
        if use_mathpix:
            if not MATHPIX_AVAILABLE:
                raise ImportError("mathpix가 설치되지 않았습니다. pip install mathpix-python")
            if not mathpix_app_id or not mathpix_app_key:
                raise ValueError("MathPix를 사용하려면 app_id와 app_key가 필요합니다.")
            self.mathpix_client = mathpix.Client(app_id=mathpix_app_id, app_key=mathpix_app_key)
        elif PADDLEOCR_AVAILABLE:
            # PaddleOCR 사용 (무료, 수식 인식 전용 모델 필요)
            self.paddle_ocr = PaddleOCR(use_angle_cls=True, lang='korean', use_gpu=False)
            print("⚠️ PaddleOCR 사용 중 (수식 인식 정확도는 MathPix보다 낮을 수 있음)")
        else:
            print("⚠️ 수식 OCR 라이브러리가 없습니다. 기본 이미지 정보만 반환합니다.")
            self.mathpix_client = None
            self.paddle_ocr = None
    
    def image_to_base64(self, image: Image.Image) -> str:
        """PIL Image → Base64 인코딩"""
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str
    
    def image_to_latex(self, image: Image.Image) -> str:
        """
        수식 이미지 → LaTeX 코드
        
        Args:
            image: PIL Image (수식 이미지)
        
        Returns:
            LaTeX 코드 (예: "x = \\frac{-b \\pm \\sqrt{b^2-4ac}}{2a}")
        """
        if self.use_mathpix and self.mathpix_client:
            return self._mathpix_to_latex(image)
        elif self.paddle_ocr:
            return self._paddleocr_to_latex(image)
        else:
            # Fallback: 이미지 정보만 반환
            return f"[수식 이미지: {image.size[0]}x{image.size[1]}px]"
    
    def _mathpix_to_latex(self, image: Image.Image) -> str:
        """MathPix API로 LaTeX 변환"""
        try:
            img_base64 = self.image_to_base64(image)
            
            # MathPix API 호출
            result = self.mathpix_client.latex({
                "src": f"data:image/png;base64,{img_base64}",
                "formats": ["latex_styled"]
            })
            
            # LaTeX 코드 추출
            latex = result.get("latex_styled") or result.get("latex", "")
            return latex
        except Exception as e:
            raise Exception(f"MathPix API 호출 실패: {e}")
    
    def _paddleocr_to_latex(self, image: Image.Image) -> str:
        """PaddleOCR로 수식 인식 (간단한 수식만 가능)"""
        try:
            # PIL Image → numpy array
            import numpy as np
            img_array = np.array(image.convert('RGB'))
            
            # OCR 수행
            result = self.paddle_ocr.ocr(img_array, cls=True)
            
            if result and result[0]:
                # 텍스트 추출 및 LaTeX로 변환 시도
                texts = [line[1][0] for line in result[0]]
                # 간단한 수식 패턴 매칭 (실제로는 더 복잡한 변환이 필요)
                combined = " ".join(texts)
                return self._text_to_latex_approximation(combined)
            else:
                return "[수식 인식 실패]"
        except Exception as e:
            raise Exception(f"PaddleOCR 실패: {e}")
    
    def _text_to_latex_approximation(self, text: str) -> str:
        """텍스트를 LaTeX로 근사 변환 (간단한 패턴)"""
        # 간단한 수식 패턴 변환 예시
        # 실제로는 더 정교한 변환이 필요
        replacements = {
            "×": "\\times",
            "÷": "\\div",
            "√": "\\sqrt",
            "²": "^2",
            "³": "^3",
        }
        
        latex = text
        for old, new in replacements.items():
            latex = latex.replace(old, new)
        
        return latex
    
    def latex_to_braille(self, latex: str) -> str:
        """
        LaTeX → Nemeth 점자 코드 (수학 점자)
        
        참고: Nemeth 점자 변환은 별도 구현 필요
        """
        # TODO: Nemeth 점자 변환 로직 구현
        # 참고: Nemeth 점자 규칙
        # - 숫자: 특수 점자 패턴
        # - 연산자: +, -, ×, ÷ 등
        # - 분수: 특수 점자 표기
        # - 근호: √ 표기
        
        return f"[Nemeth 점자 변환 예정: {latex}]"
    
    def extract_formula_from_pdf_block(self, image_block: Dict[str, Any]) -> Dict[str, Any]:
        """
        PDF 블록에서 수식 정보 추출
        
        Args:
            image_block: 이미지 블록 (bbox, image_path 등 포함)
        
        Returns:
            Dict with keys: latex, braille, metadata
        """
        # 이미지 로드 (image_path 또는 직접 이미지)
        image_path = image_block.get("image_path")
        if image_path:
            image = Image.open(image_path)
        else:
            # 이미지 데이터가 직접 있는 경우
            image_data = image_block.get("image_data")
            if image_data:
                image = Image.open(io.BytesIO(image_data))
            else:
                raise ValueError("이미지 경로 또는 데이터가 없습니다.")
        
        # LaTeX 변환
        latex = self.image_to_latex(image)
        
        # Nemeth 점자 변환
        braille = self.latex_to_braille(latex)
        
        return {
            "formula_id": image_block.get("formula_id", f"formula_{id(self)}"),
            "latex": latex,
            "braille": braille,
            "bbox": image_block.get("bbox", []),
            "page": image_block.get("page", 1),
            "metadata": {
                "image_size": image.size,
                "ocr_method": "mathpix" if self.use_mathpix else "paddleocr" if self.paddle_ocr else "none",
                **image_block.get("metadata", {})
            }
        }


# Fallback: 수식 OCR 없이 사용
class BasicMathOCR:
    """기본 수식 OCR (이미지 정보만 반환)"""
    
    @staticmethod
    def image_to_latex(image: Image.Image) -> str:
        """이미지 정보만 반환"""
        return f"[수식 이미지: {image.size[0]}x{image.size[1]}px]"
    
    @staticmethod
    def latex_to_braille(latex: str) -> str:
        """Nemeth 점자 변환 (미구현)"""
        return f"[Nemeth 점자 변환 예정: {latex}]"


def get_math_ocr(use_mathpix: bool = False, **kwargs) -> Any:
    """
    수식 OCR 인스턴스 반환
    
    Args:
        use_mathpix: MathPix 사용 여부
        **kwargs: MathOCR 생성자 인자
    
    Returns:
        MathOCR 또는 BasicMathOCR 인스턴스
    """
    if use_mathpix or PADDLEOCR_AVAILABLE:
        try:
            return MathOCR(use_mathpix=use_mathpix, **kwargs)
        except (ImportError, Exception) as e:
            print(f"⚠️ 수식 OCR 사용 불가, 기본 OCR 사용: {e}")
            return BasicMathOCR()
    else:
        return BasicMathOCR()
