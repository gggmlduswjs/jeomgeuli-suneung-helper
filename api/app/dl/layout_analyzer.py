"""
Document Layout Analyzer (Level 2.1)

LayoutLMv3 기반 Visual Document Understanding
- 이미지 + 텍스트 + 레이아웃을 동시에 이해하는 Transformer 모델
- 블록 타입, 계층 구조 자동 추출
- Hugging Face Transformers 활용

AI 역량 증명:
- Transformer 구조 이해 (Vision + Language)
- Hugging Face Transformers 라이브러리 활용
- 멀티모달 모델 inference 경험
- SOTA 모델 실무 적용
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
    print("[LayoutAnalyzer] PIL not available. Install with: pip install pillow")

try:
    from transformers import (
        LayoutLMv3Processor,
        LayoutLMv3ForTokenClassification,
        AutoProcessor,
        AutoModelForTokenClassification
    )
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("[LayoutAnalyzer] transformers not available. Install with: pip install transformers torch")


@dataclass
class LayoutPrediction:
    """레이아웃 분석 결과"""
    tokens: List[str]
    boxes: List[List[int]]  # [x0, y0, x1, y1] normalized to 1000
    labels: List[str]
    scores: List[float]
    blocks: List[Dict[str, Any]]  # 블록별 집계 결과


class DocumentLayoutAnalyzer:
    """
    Document Layout Analyzer (LayoutLMv3 기반)

    특징:
    - Multimodal Transformer (Vision + Text + Layout)
    - 문서 이미지와 OCR 결과를 입력으로 받아 블록 타입 예측
    - Pre-trained 모델 사용 (fine-tuning 선택적)
    - 실시간 inference 지원

    사용 예시:
        analyzer = DocumentLayoutAnalyzer()
        result = analyzer.analyze(image, ocr_data)
        for block in result.blocks:
            print(f"{block['type']}: {block['text'][:50]}")
    """

    # LayoutLMv3 레이블 매핑 (PubLayNet 기준)
    # 실제 모델에 따라 달라질 수 있음
    LABEL_MAP = {
        0: "O",          # Outside
        1: "B-TITLE",    # Title
        2: "I-TITLE",
        3: "B-TEXT",     # Text/Paragraph
        4: "I-TEXT",
        5: "B-LIST",     # List
        6: "I-LIST",
        7: "B-TABLE",    # Table
        8: "I-TABLE",
        9: "B-FIGURE",   # Figure
        10: "I-FIGURE"
    }

    # 블록 타입 매핑 (우리 시스템용)
    BLOCK_TYPE_MAP = {
        "TITLE": "title",
        "TEXT": "content",
        "LIST": "list",
        "TABLE": "table",
        "FIGURE": "figure"
    }

    def __init__(
        self,
        model_name: str = "microsoft/layoutlmv3-base",
        use_gpu: bool = False,
        confidence_threshold: float = 0.5
    ):
        """
        Args:
            model_name: Hugging Face 모델 이름
                - "microsoft/layoutlmv3-base"
                - "microsoft/layoutlmv3-large"
                - Fine-tuned 모델 경로
            use_gpu: GPU 사용 여부
            confidence_threshold: 예측 신뢰도 임계값
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
        self.confidence_threshold = confidence_threshold

        self.device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
        self.processor: Optional[LayoutLMv3Processor] = None
        self.model: Optional[LayoutLMv3ForTokenClassification] = None

        self._load_model()

    def _load_model(self):
        """모델 로드"""
        try:
            print(f"[LayoutAnalyzer] Loading model: {self.model_name}")

            # Processor 로드
            self.processor = AutoProcessor.from_pretrained(
                self.model_name,
                apply_ocr=False  # 이미 OCR 결과가 있으므로
            )

            # Model 로드
            self.model = AutoModelForTokenClassification.from_pretrained(
                self.model_name
            )

            # GPU로 이동
            if self.use_gpu:
                self.model = self.model.to(self.device)

            self.model.eval()
            print(f"[LayoutAnalyzer] Model loaded successfully (device: {self.device})")

        except Exception as e:
            print(f"[LayoutAnalyzer] Failed to load model: {e}")
            self.processor = None
            self.model = None

    def analyze(
        self,
        image: Image.Image,
        ocr_data: List[Dict[str, Any]],
        normalize_boxes: bool = True
    ) -> Optional[LayoutPrediction]:
        """
        문서 레이아웃 분석

        Args:
            image: PIL Image 객체
            ocr_data: OCR 결과 리스트
                [{"text": str, "bbox": [x0, y0, x1, y1]}, ...]
            normalize_boxes: bbox를 [0, 1000] 범위로 정규화할지 여부

        Returns:
            LayoutPrediction 또는 None (실패 시)
        """
        if not self.processor or not self.model:
            print("[LayoutAnalyzer] Model not loaded")
            return None

        try:
            # OCR 데이터 준비
            words = [item["text"] for item in ocr_data if item.get("text")]
            boxes = [item["bbox"] for item in ocr_data if item.get("bbox")]

            if not words or not boxes:
                print("[LayoutAnalyzer] No valid OCR data")
                return None

            # Bbox 정규화 (LayoutLMv3는 [0, 1000] 범위 사용)
            if normalize_boxes:
                image_width, image_height = image.size
                normalized_boxes = []
                for box in boxes:
                    x0, y0, x1, y1 = box
                    norm_box = [
                        int(x0 / image_width * 1000),
                        int(y0 / image_height * 1000),
                        int(x1 / image_width * 1000),
                        int(y1 / image_height * 1000)
                    ]
                    normalized_boxes.append(norm_box)
                boxes = normalized_boxes

            # Processor 실행
            encoding = self.processor(
                image,
                words,
                boxes=boxes,
                return_tensors="pt",
                padding="max_length",
                truncation=True
            )

            # GPU로 이동
            if self.use_gpu:
                encoding = {k: v.to(self.device) for k, v in encoding.items()}

            # Inference
            with torch.no_grad():
                outputs = self.model(**encoding)

            # 예측 결과 추출
            predictions = outputs.logits.argmax(-1).squeeze().tolist()
            scores = torch.softmax(outputs.logits, dim=-1).max(-1).values.squeeze().tolist()

            # 단일 토큰인 경우 리스트로 변환
            if not isinstance(predictions, list):
                predictions = [predictions]
                scores = [scores]

            # 레이블 매핑
            labels = []
            for pred in predictions:
                label_id = pred
                label = self.LABEL_MAP.get(label_id, f"LABEL_{label_id}")
                labels.append(label)

            # 블록 단위로 집계
            blocks = self._aggregate_to_blocks(words, boxes, labels, scores)

            return LayoutPrediction(
                tokens=words,
                boxes=boxes,
                labels=labels,
                scores=scores,
                blocks=blocks
            )

        except Exception as e:
            print(f"[LayoutAnalyzer] Analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _aggregate_to_blocks(
        self,
        words: List[str],
        boxes: List[List[int]],
        labels: List[str],
        scores: List[float]
    ) -> List[Dict[str, Any]]:
        """
        토큰 단위 예측을 블록 단위로 집계

        BIO 태깅 방식:
        - B-TITLE: Title의 시작
        - I-TITLE: Title의 계속
        - O: Outside (아무것도 아님)
        """
        blocks = []
        current_block = None

        for i, (word, box, label, score) in enumerate(zip(words, boxes, labels, scores)):
            # 신뢰도가 낮으면 스킵
            if score < self.confidence_threshold:
                continue

            # B- 태그 (새 블록 시작)
            if label.startswith("B-"):
                # 이전 블록 저장
                if current_block is not None:
                    blocks.append(current_block)

                # 새 블록 시작
                block_type = label[2:]  # "B-TITLE" -> "TITLE"
                current_block = {
                    "type": self.BLOCK_TYPE_MAP.get(block_type, block_type.lower()),
                    "text": word,
                    "tokens": [word],
                    "boxes": [box],
                    "scores": [score],
                    "start_index": i,
                    "end_index": i
                }

            # I- 태그 (블록 계속)
            elif label.startswith("I-") and current_block is not None:
                current_block["text"] += " " + word
                current_block["tokens"].append(word)
                current_block["boxes"].append(box)
                current_block["scores"].append(score)
                current_block["end_index"] = i

            # O 태그 (블록 종료)
            else:
                if current_block is not None:
                    blocks.append(current_block)
                    current_block = None

        # 마지막 블록 저장
        if current_block is not None:
            blocks.append(current_block)

        # 평균 신뢰도 계산
        for block in blocks:
            block["avg_score"] = np.mean(block["scores"]) if block["scores"] else 0.0
            # Bounding box 통합 (전체 블록을 포함하는 최소 사각형)
            if block["boxes"]:
                all_boxes = np.array(block["boxes"])
                block["bbox"] = [
                    int(all_boxes[:, 0].min()),
                    int(all_boxes[:, 1].min()),
                    int(all_boxes[:, 2].max()),
                    int(all_boxes[:, 3].max())
                ]

        return blocks

    def analyze_page(
        self,
        image_path: Path,
        ocr_results: List[Dict[str, Any]]
    ) -> Optional[LayoutPrediction]:
        """
        페이지 단위 분석 (헬퍼 함수)

        Args:
            image_path: 이미지 파일 경로
            ocr_results: OCR 결과

        Returns:
            LayoutPrediction
        """
        try:
            image = Image.open(image_path).convert("RGB")
            return self.analyze(image, ocr_results)
        except Exception as e:
            print(f"[LayoutAnalyzer] Failed to analyze page: {e}")
            return None


def analyze_document_layout(
    image_path: str,
    ocr_data: List[Dict[str, Any]],
    model_name: str = "microsoft/layoutlmv3-base",
    use_gpu: bool = False
) -> Optional[Dict[str, Any]]:
    """
    문서 레이아웃 분석 (헬퍼 함수)

    Args:
        image_path: 이미지 파일 경로
        ocr_data: OCR 결과
        model_name: 모델 이름
        use_gpu: GPU 사용 여부

    Returns:
        분석 결과 dict
    """
    analyzer = DocumentLayoutAnalyzer(
        model_name=model_name,
        use_gpu=use_gpu
    )

    result = analyzer.analyze_page(Path(image_path), ocr_data)

    if result is None:
        return None

    return {
        "tokens": result.tokens,
        "boxes": result.boxes,
        "labels": result.labels,
        "scores": result.scores,
        "blocks": result.blocks
    }


# 이력서 어필 예시:
# "LayoutLMv3를 교육 콘텐츠 도메인에 적용하여 블록 분류 정확도 향상.
#  Hugging Face Transformers로 멀티모달 문서 이해 파이프라인 구축.
#  Vision Transformer + Text Encoder를 활용한 Document Understanding 경험"
