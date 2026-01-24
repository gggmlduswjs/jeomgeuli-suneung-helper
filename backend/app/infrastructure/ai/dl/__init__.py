"""
Deep Learning Module (Level 2)

Level 2 DL 기능 (딥러닝 모델 도입):
- Document Layout Analyzer: LayoutLMv3 기반 문서 구조 이해
- Math Expression Recognizer: TrOCR 기반 수식 인식

사용 예시:
    # DLExtractionProcessor는 이 파일 내에 정의됨

    processor = DLExtractionProcessor(
        enable_layout_analysis=True,
        enable_math_recognition=True,
        use_gpu=False
    )

    # 페이지 처리
    enhanced_ocr_data = processor.process_page(page_image, ocr_data)
"""
from app.infrastructure.ai.dl.layout_analyzer import (
    DocumentLayoutAnalyzer,
    LayoutPrediction,
    analyze_document_layout
)
from app.infrastructure.ai.dl.math_recognizer import (
    MathExpressionRecognizer,
    MathPrediction,
    recognize_math_expression
)
from typing import List, Dict, Any, Optional
from PIL import Image


__all__ = [
    "DocumentLayoutAnalyzer",
    "LayoutPrediction",
    "MathExpressionRecognizer",
    "MathPrediction",
    "DLExtractionProcessor",
    "analyze_document_layout",
    "recognize_math_expression"
]


class DLExtractionProcessor:
    """
    Deep Learning Extraction Processor

    Extraction 단계에 DL 모델을 통합합니다:
    1. Layout Analysis: 문서 구조 자동 이해
    2. Math Recognition: 수식 영역 자동 인식 및 LaTeX 변환

    사용 예시:
        processor = DLExtractionProcessor()
        enhanced_ocr = processor.process_page(image, ocr_data)
    """

    def __init__(
        self,
        enable_layout_analysis: bool = True,
        enable_math_recognition: bool = True,
        layout_model: str = "microsoft/layoutlmv3-base",
        math_model: str = "microsoft/trocr-base-handwritten",
        use_gpu: bool = False
    ):
        """
        Args:
            enable_layout_analysis: 레이아웃 분석 활성화
            enable_math_recognition: 수식 인식 활성화
            layout_model: LayoutLM 모델 이름
            math_model: TrOCR 모델 이름
            use_gpu: GPU 사용 여부
        """
        self.enable_layout_analysis = enable_layout_analysis
        self.enable_math_recognition = enable_math_recognition
        self.use_gpu = use_gpu

        # Layout Analyzer
        self.layout_analyzer: Optional[DocumentLayoutAnalyzer] = None
        if enable_layout_analysis:
            try:
                self.layout_analyzer = DocumentLayoutAnalyzer(
                    model_name=layout_model,
                    use_gpu=use_gpu
                )
                print("[DLExtractionProcessor] Layout Analyzer loaded")
            except Exception as e:
                print(f"[DLExtractionProcessor] Failed to load Layout Analyzer: {e}")
                self.enable_layout_analysis = False

        # Math Recognizer
        self.math_recognizer: Optional[MathExpressionRecognizer] = None
        if enable_math_recognition:
            try:
                self.math_recognizer = MathExpressionRecognizer(
                    model_name=math_model,
                    use_gpu=use_gpu
                )
                print("[DLExtractionProcessor] Math Recognizer loaded")
            except Exception as e:
                print(f"[DLExtractionProcessor] Failed to load Math Recognizer: {e}")
                self.enable_math_recognition = False

    def process_page(
        self,
        page_image: Image.Image,
        ocr_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        페이지 처리 (DL 모델 적용)

        Args:
            page_image: 페이지 이미지
            ocr_data: 기존 OCR 결과

        Returns:
            Enhanced OCR 데이터 + DL 결과
        """
        result = {
            "ocr_data": ocr_data,
            "layout_analysis": None,
            "math_recognition": None
        }

        # Step 1: Layout Analysis
        if self.enable_layout_analysis and self.layout_analyzer:
            try:
                layout_result = self.layout_analyzer.analyze(page_image, ocr_data)
                if layout_result:
                    result["layout_analysis"] = {
                        "blocks": layout_result.blocks,
                        "tokens": layout_result.tokens,
                        "labels": layout_result.labels
                    }
                    print(f"[DLExtractionProcessor] Layout analysis: {len(layout_result.blocks)} blocks")
            except Exception as e:
                print(f"[DLExtractionProcessor] Layout analysis failed: {e}")

        # Step 2: Math Recognition
        if self.enable_math_recognition and self.math_recognizer:
            try:
                enhanced_ocr, math_predictions = self.math_recognizer.process_page_with_math(
                    page_image,
                    ocr_data,
                    replace_in_ocr=True
                )
                result["ocr_data"] = enhanced_ocr
                result["math_recognition"] = {
                    "count": len(math_predictions),
                    "predictions": [
                        {
                            "latex": p.latex,
                            "confidence": p.confidence
                        }
                        for p in math_predictions
                    ]
                }
                print(f"[DLExtractionProcessor] Math recognition: {len(math_predictions)} expressions")
            except Exception as e:
                print(f"[DLExtractionProcessor] Math recognition failed: {e}")

        return result

    def enrich_ocr_with_dl(
        self,
        page_image: Image.Image,
        ocr_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        OCR 데이터에 DL 결과 추가

        Args:
            page_image: 페이지 이미지
            ocr_data: OCR 결과

        Returns:
            Enriched OCR 데이터
        """
        result = self.process_page(page_image, ocr_data)

        enriched_ocr = result["ocr_data"]

        # Layout 정보 추가
        if result["layout_analysis"]:
            layout_blocks = result["layout_analysis"]["blocks"]
            # OCR 데이터에 block_type 추가 (bbox 매칭)
            for item in enriched_ocr:
                item_bbox = item.get("bbox")
                if not item_bbox:
                    continue

                # 가장 가까운 layout block 찾기
                best_block = None
                best_iou = 0.0

                for block in layout_blocks:
                    block_bbox = block.get("bbox")
                    if not block_bbox:
                        continue

                    iou = self._compute_iou(item_bbox, block_bbox)
                    if iou > best_iou:
                        best_iou = iou
                        best_block = block

                if best_block and best_iou > 0.3:  # IoU > 0.3이면 매칭
                    if "dl_metadata" not in item:
                        item["dl_metadata"] = {}
                    item["dl_metadata"]["layout_type"] = best_block["type"]
                    item["dl_metadata"]["layout_confidence"] = best_block["avg_score"]

        return enriched_ocr

    def _compute_iou(
        self,
        bbox1: List[int],
        bbox2: List[int]
    ) -> float:
        """
        IoU (Intersection over Union) 계산

        Args:
            bbox1, bbox2: [x0, y0, x1, y1]

        Returns:
            IoU 값 (0.0 ~ 1.0)
        """
        x0_1, y0_1, x1_1, y1_1 = bbox1
        x0_2, y0_2, x1_2, y1_2 = bbox2

        # Intersection
        x0_i = max(x0_1, x0_2)
        y0_i = max(y0_1, y0_2)
        x1_i = min(x1_1, x1_2)
        y1_i = min(y1_1, y1_2)

        if x1_i < x0_i or y1_i < y0_i:
            return 0.0

        intersection = (x1_i - x0_i) * (y1_i - y0_i)

        # Union
        area1 = (x1_1 - x0_1) * (y1_1 - y0_1)
        area2 = (x1_2 - x0_2) * (y1_2 - y0_2)
        union = area1 + area2 - intersection

        return intersection / union if union > 0 else 0.0
