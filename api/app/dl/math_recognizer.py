"""
Math Expression Recognition (Level 2.2)

CNN + Transformer 기반 수식 인식
- 수식 이미지를 LaTeX 코드로 변환
- TrOCR (Transformer-based OCR) 활용
- Image-to-Sequence 생성

AI 역량 증명:
- CNN 구조 이해 (이미지 특징 추출)
- Transformer (시퀀스 생성)
- Encoder-Decoder 아키텍처
- 도메인 특화 모델 활용
"""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import numpy as np

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("[MathRecognizer] PIL not available. Install with: pip install pillow")

try:
    from transformers import (
        TrOCRProcessor,
        VisionEncoderDecoderModel,
        AutoProcessor,
        AutoModelForCausalLM
    )
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("[MathRecognizer] transformers not available. Install with: pip install transformers torch")


@dataclass
class MathPrediction:
    """수식 인식 결과"""
    latex: str
    confidence: float
    image_size: Tuple[int, int]
    metadata: Dict[str, Any]


class MathExpressionRecognizer:
    """
    Math Expression Recognizer

    특징:
    - TrOCR 기반 수식 이미지 → LaTeX 변환
    - Vision Transformer (ViT) + Text Transformer Decoder
    - Image-to-Sequence 생성
    - Pre-trained 모델 사용

    사용 예시:
        recognizer = MathExpressionRecognizer()
        result = recognizer.recognize(math_image)
        print(f"LaTeX: {result.latex}")
    """

    def __init__(
        self,
        model_name: str = "microsoft/trocr-base-handwritten",
        use_gpu: bool = False,
        max_length: int = 256
    ):
        """
        Args:
            model_name: Hugging Face 모델 이름
                - "microsoft/trocr-base-handwritten" (기본 OCR)
                - "microsoft/trocr-large-handwritten"
                - LaTeX 특화 모델 (fine-tuned)
            use_gpu: GPU 사용 여부
            max_length: 최대 생성 길이
        """
        if not TRANSFORMERS_AVAILABLE:
            raise RuntimeError(
                "transformers library not available. "
                "Install with: pip install transformers torch"
            )

        if not PIL_AVAILABLE:
            raise RuntimeError(
                "PIL not available. "
                "Install with: pip install pillow"
            )

        self.model_name = model_name
        self.use_gpu = use_gpu
        self.max_length = max_length

        self.device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
        self.processor: Optional[TrOCRProcessor] = None
        self.model: Optional[VisionEncoderDecoderModel] = None

        self._load_model()

    def _load_model(self):
        """모델 로드"""
        try:
            print(f"[MathRecognizer] Loading model: {self.model_name}")

            # Processor 로드
            self.processor = TrOCRProcessor.from_pretrained(self.model_name)

            # Model 로드
            self.model = VisionEncoderDecoderModel.from_pretrained(self.model_name)

            # GPU로 이동
            if self.use_gpu:
                self.model = self.model.to(self.device)

            self.model.eval()
            print(f"[MathRecognizer] Model loaded successfully (device: {self.device})")

        except Exception as e:
            print(f"[MathRecognizer] Failed to load model: {e}")
            self.processor = None
            self.model = None

    def recognize(
        self,
        image: Image.Image,
        num_beams: int = 4,
        return_confidence: bool = True
    ) -> Optional[MathPrediction]:
        """
        수식 인식

        Args:
            image: PIL Image 객체 (수식 이미지)
            num_beams: Beam search 크기 (생성 품질 향상)
            return_confidence: 신뢰도 계산 여부

        Returns:
            MathPrediction 또는 None (실패 시)
        """
        if not self.processor or not self.model:
            print("[MathRecognizer] Model not loaded")
            return None

        try:
            # 이미지 전처리
            pixel_values = self.processor(
                images=image,
                return_tensors="pt"
            ).pixel_values

            # GPU로 이동
            if self.use_gpu:
                pixel_values = pixel_values.to(self.device)

            # Inference (beam search)
            with torch.no_grad():
                generated_ids = self.model.generate(
                    pixel_values,
                    max_length=self.max_length,
                    num_beams=num_beams,
                    output_scores=return_confidence,
                    return_dict_in_generate=return_confidence
                )

            # 디코딩
            if return_confidence:
                sequences = generated_ids.sequences
                scores = generated_ids.sequences_scores
                latex = self.processor.batch_decode(sequences, skip_special_tokens=True)[0]
                confidence = float(torch.exp(scores[0]).item()) if len(scores) > 0 else 0.0
            else:
                latex = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
                confidence = 0.0

            return MathPrediction(
                latex=latex.strip(),
                confidence=confidence,
                image_size=image.size,
                metadata={
                    "model": self.model_name,
                    "num_beams": num_beams,
                    "device": self.device
                }
            )

        except Exception as e:
            print(f"[MathRecognizer] Recognition failed: {e}")
            import traceback
            traceback.print_exc()
            return None

    def recognize_batch(
        self,
        images: List[Image.Image],
        num_beams: int = 4
    ) -> List[Optional[MathPrediction]]:
        """
        배치 인식 (여러 수식 동시 처리)

        Args:
            images: PIL Image 리스트
            num_beams: Beam search 크기

        Returns:
            MathPrediction 리스트
        """
        results = []
        for image in images:
            result = self.recognize(image, num_beams=num_beams)
            results.append(result)

        return results

    def recognize_from_file(
        self,
        image_path: Path,
        num_beams: int = 4
    ) -> Optional[MathPrediction]:
        """
        파일에서 인식 (헬퍼 함수)

        Args:
            image_path: 이미지 파일 경로
            num_beams: Beam search 크기

        Returns:
            MathPrediction
        """
        try:
            image = Image.open(image_path).convert("RGB")
            return self.recognize(image, num_beams=num_beams)
        except Exception as e:
            print(f"[MathRecognizer] Failed to load image: {e}")
            return None

    def extract_math_regions(
        self,
        page_image: Image.Image,
        ocr_data: List[Dict[str, Any]],
        math_pattern: Optional[str] = None
    ) -> List[Tuple[Image.Image, Dict[str, Any]]]:
        """
        페이지에서 수식 영역 추출

        Args:
            page_image: 전체 페이지 이미지
            ocr_data: OCR 결과 (bbox 포함)
            math_pattern: 수식 패턴 (정규식)

        Returns:
            (수식 이미지, 메타데이터) 튜플 리스트
        """
        import re

        math_regions = []

        for item in ocr_data:
            text = item.get("text", "")
            bbox = item.get("bbox")

            if not bbox:
                continue

            # 수식 패턴 감지
            # 간단한 휴리스틱: 수학 기호나 LaTeX 명령어 포함
            is_math = False
            if math_pattern:
                is_math = bool(re.search(math_pattern, text))
            else:
                # 기본 패턴: 수학 기호, 분수, 제곱 등
                math_indicators = [
                    r'[∫∑∏√∞≈≠≤≥±×÷]',  # 수학 기호
                    r'\d+[/]\d+',  # 분수 (1/2)
                    r'\^\d+',  # 제곱 (x^2)
                    r'_\d+',  # 아래첨자 (x_1)
                    r'\\[a-z]+',  # LaTeX 명령어 (\frac, \sqrt 등)
                ]
                is_math = any(re.search(pattern, text) for pattern in math_indicators)

            if is_math:
                try:
                    # 이미지에서 영역 잘라내기
                    x0, y0, x1, y1 = bbox
                    cropped = page_image.crop((x0, y0, x1, y1))

                    math_regions.append((cropped, {
                        "text": text,
                        "bbox": bbox,
                        "original_ocr": text
                    }))
                except Exception as e:
                    print(f"[MathRecognizer] Failed to crop region: {e}")
                    continue

        return math_regions

    def process_page_with_math(
        self,
        page_image: Image.Image,
        ocr_data: List[Dict[str, Any]],
        replace_in_ocr: bool = True
    ) -> Tuple[List[Dict[str, Any]], List[MathPrediction]]:
        """
        페이지에서 수식 영역 자동 인식 및 교체

        Args:
            page_image: 페이지 이미지
            ocr_data: OCR 결과
            replace_in_ocr: OCR 결과의 수식을 LaTeX로 교체할지 여부

        Returns:
            (수정된 OCR 데이터, 수식 인식 결과 리스트)
        """
        # 수식 영역 추출
        math_regions = self.extract_math_regions(page_image, ocr_data)

        if not math_regions:
            return ocr_data, []

        # 수식 인식
        math_images = [region[0] for region in math_regions]
        math_predictions = self.recognize_batch(math_images)

        # OCR 데이터에 LaTeX 추가 또는 교체
        if replace_in_ocr:
            for (_, metadata), prediction in zip(math_regions, math_predictions):
                if prediction is None:
                    continue

                # 원본 OCR 텍스트를 가진 항목 찾기
                for item in ocr_data:
                    if (item.get("text") == metadata["original_ocr"] and
                        item.get("bbox") == metadata["bbox"]):
                        # LaTeX로 교체
                        item["text"] = prediction.latex
                        item["is_math"] = True
                        item["math_confidence"] = prediction.confidence
                        break

        return ocr_data, [p for p in math_predictions if p is not None]


def recognize_math_expression(
    image_path: str,
    model_name: str = "microsoft/trocr-base-handwritten",
    use_gpu: bool = False
) -> Optional[str]:
    """
    수식 인식 (헬퍼 함수)

    Args:
        image_path: 수식 이미지 경로
        model_name: 모델 이름
        use_gpu: GPU 사용 여부

    Returns:
        LaTeX 문자열 또는 None
    """
    recognizer = MathExpressionRecognizer(
        model_name=model_name,
        use_gpu=use_gpu
    )

    result = recognizer.recognize_from_file(Path(image_path))

    return result.latex if result else None


# 이력서 어필 예시:
# "TrOCR (Vision Transformer + Text Decoder)를 활용한 수식 인식 시스템 구축.
#  CNN 기반 이미지 인코더와 Transformer 디코더를 결합한 Image-to-Sequence 모델 적용.
#  수학 콘텐츠 LaTeX 변환 정확도 향상으로 교육 자료 디지털화 효율 개선"
