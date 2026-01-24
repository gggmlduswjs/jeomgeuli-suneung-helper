"""
레이아웃 감지 (LayoutParser 또는 YOLO)
PDF 페이지의 구조를 자동으로 파악
"""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import cv2
import numpy as np

logger = logging.getLogger(__name__)


class LayoutBlock:
    """레이아웃 블록 (박스 + 타입)"""

    def __init__(self, bbox: List[int], block_type: str, confidence: float = 1.0):
        self.bbox = bbox  # [x1, y1, x2, y2]
        self.type = block_type  # concept, work, question, title, image, etc.
        self.confidence = confidence
        self.text = None
        self.image_path = None

    @property
    def x1(self): return self.bbox[0]

    @property
    def y1(self): return self.bbox[1]

    @property
    def x2(self): return self.bbox[2]

    @property
    def y2(self): return self.bbox[3]

    @property
    def width(self): return self.x2 - self.x1

    @property
    def height(self): return self.y2 - self.y1

    def crop_image(self, image: np.ndarray) -> np.ndarray:
        """이미지에서 이 박스 영역 잘라내기"""
        return image[self.y1:self.y2, self.x1:self.x2]


class LayoutDetector:
    """레이아웃 감지기 (LayoutParser 기반)"""

    def __init__(self, model_type: str = "layoutparser"):
        """
        Args:
            model_type: "layoutparser" | "yolo" | "none"
        """
        self.model_type = model_type
        self.model = None

        if model_type == "layoutparser":
            self._init_layoutparser()
        elif model_type == "yolo":
            self._init_yolo()

    def _init_layoutparser(self):
        """LayoutParser 모델 초기화"""
        try:
            import layoutparser as lp

            # PubLayNet: 논문/교재 레이아웃 (사전학습)
            self.model = lp.Detectron2LayoutModel(
                config_path='lp://PubLayNet/faster_rcnn_R_50_FPN_3x/config',
                label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"}
            )
            logger.info("[LayoutDetector] LayoutParser 모델 로드 성공")
        except Exception as e:
            logger.error(f"[LayoutDetector] LayoutParser 로드 실패: {e}")
            logger.info("[LayoutDetector] pip install layoutparser detectron2 필요")
            self.model_type = "none"

    def _init_yolo(self):
        """YOLO 모델 초기화 (Custom)"""
        try:
            from ultralytics import YOLO

            model_path = Path(__file__).parent / "models" / "suneung_layout.pt"
            if model_path.exists():
                self.model = YOLO(str(model_path))
                logger.info(f"[LayoutDetector] YOLO 모델 로드: {model_path}")
            else:
                logger.warning(f"[LayoutDetector] YOLO 모델 없음: {model_path}")
                self.model_type = "none"
        except Exception as e:
            logger.error(f"[LayoutDetector] YOLO 로드 실패: {e}")
            self.model_type = "none"

    def detect(self, image: np.ndarray, page_num: int = 0) -> List[LayoutBlock]:
        """
        페이지 이미지에서 레이아웃 블록 감지

        Args:
            image: 페이지 이미지 (numpy array)
            page_num: 페이지 번호

        Returns:
            레이아웃 블록 리스트
        """
        if self.model_type == "none" or self.model is None:
            # Fallback: 전체 페이지를 하나의 텍스트 블록으로
            h, w = image.shape[:2]
            return [LayoutBlock([0, 0, w, h], "text", 1.0)]

        if self.model_type == "layoutparser":
            return self._detect_layoutparser(image, page_num)
        elif self.model_type == "yolo":
            return self._detect_yolo(image, page_num)

        return []

    def _detect_layoutparser(self, image: np.ndarray, page_num: int) -> List[LayoutBlock]:
        """LayoutParser로 감지"""
        import layoutparser as lp

        layout = self.model.detect(image)
        blocks = []

        for block in layout:
            # LayoutParser 좌표 → 정수 bbox
            bbox = [
                int(block.block.x_1),
                int(block.block.y_1),
                int(block.block.x_2),
                int(block.block.y_2)
            ]

            # 타입 매핑
            block_type = self._map_layoutparser_type(block.type)

            blocks.append(LayoutBlock(
                bbox=bbox,
                block_type=block_type,
                confidence=block.score
            ))

        logger.info(f"[LayoutDetector] Page {page_num}: {len(blocks)}개 블록 감지")
        return blocks

    def _detect_yolo(self, image: np.ndarray, page_num: int) -> List[LayoutBlock]:
        """YOLO로 감지"""
        results = self.model(image, verbose=False)
        blocks = []

        for result in results:
            boxes = result.boxes
            for box in boxes:
                xyxy = box.xyxy[0].cpu().numpy()  # [x1, y1, x2, y2]
                cls = int(box.cls[0])
                conf = float(box.conf[0])

                # 클래스 이름
                class_name = result.names[cls]

                blocks.append(LayoutBlock(
                    bbox=[int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])],
                    block_type=class_name,
                    confidence=conf
                ))

        logger.info(f"[LayoutDetector] Page {page_num}: {len(blocks)}개 블록 감지")
        return blocks

    def _map_layoutparser_type(self, lp_type: str) -> str:
        """LayoutParser 타입 → 우리 타입"""
        mapping = {
            "Text": "text",
            "Title": "title",
            "List": "text",
            "Table": "table",
            "Figure": "image"
        }
        return mapping.get(lp_type, "text")

    def extract_blocks_with_ocr(
        self,
        image: np.ndarray,
        blocks: List[LayoutBlock],
        ocr_func
    ) -> List[LayoutBlock]:
        """
        각 블록에 OCR 적용

        Args:
            image: 페이지 이미지
            blocks: 레이아웃 블록 리스트
            ocr_func: OCR 함수 (image → text)

        Returns:
            텍스트가 채워진 블록 리스트
        """
        for block in blocks:
            if block.type in ['text', 'title']:
                # 블록 영역만 OCR
                cropped = block.crop_image(image)
                block.text = ocr_func(cropped)

        return blocks


def detect_lecture_structure_with_layout(
    pages: List[np.ndarray],
    lecture_mapping: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    레이아웃 감지 기반 강의 구조 파악

    Args:
        pages: 페이지 이미지 리스트
        lecture_mapping: 강의 매핑 (있으면 우선 사용)

    Returns:
        강의 구조
    """
    detector = LayoutDetector(model_type="layoutparser")

    all_blocks = []

    for page_num, page_img in enumerate(pages):
        blocks = detector.detect(page_img, page_num)
        all_blocks.extend(blocks)

    # 강의 경계 감지
    # Title 블록이 나오면 새 강의 시작으로 간주
    lectures = []
    current_lecture = None

    for block in all_blocks:
        if block.type == "title" and block.height > 30:  # 큰 제목
            # 새 강의 시작
            if current_lecture:
                lectures.append(current_lecture)

            current_lecture = {
                "title": block.text,
                "blocks": []
            }

        if current_lecture:
            current_lecture["blocks"].append(block)

    if current_lecture:
        lectures.append(current_lecture)

    return {
        "lectures": lectures,
        "total_blocks": len(all_blocks)
    }
