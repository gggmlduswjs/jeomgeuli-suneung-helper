"""
YOLO 기반 문서 영역 감지기 (Level 2.2)

YOLOv8/YOLOv5 및 Roboflow API를 사용한 PDF 페이지 영역 자동 감지

YOLO 클래스 매핑:
- header: 페이지 최상단 제목 -> 강의 제목 (Lesson)
- section: 중간 제목 (예: "1 시적 표현") -> 개념 제목 (Unit: concept, subtype: title)
- concept_box: 굵은 테두리 큰 박스 -> 개념 내용 (Unit: concept, subtype: content)
- sidebar: 왼쪽 세로 보조 설명 -> 세부 개념 (Unit: concept_detail)
- passage: 작품 전문 전체 -> 본문 (Unit: passage)
- question: 문제 전체 (선지 포함) -> 문제 (Unit: question)

Lesson 구성 규칙:
- Lesson 제목은 header 목록으로 구성
- 각 Lesson 안의 Unit은 페이지 단위로 구성
- 페이지 내 순서: 개념(section, concept_box, sidebar) → 본문(passage) → 문제(question)

AI 역량 증명:
- Object Detection 모델 학습 및 배포
- Custom Dataset 생성 및 라벨링
- Transfer Learning 활용
- 모델 최적화 및 추론 최적화
- Cloud-based 모델 API 통합
"""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import base64
import requests
import os

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("[YOLODetector] PIL not available. Install with: pip install pillow")

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("[YOLODetector] ultralytics not available. Install with: pip install ultralytics")
    # YOLOv5 대체 옵션
    try:
        import torch
        YOLO5_AVAILABLE = True
    except ImportError:
        YOLO5_AVAILABLE = False


@dataclass
class DetectionResult:
    """YOLO 감지 결과"""
    bbox: List[float]  # [x1, y1, x2, y2] normalized (0-1)
    confidence: float
    class_id: int
    class_name: str  # "problem", "concept", "content", "title", "figure"


@dataclass
class PageDetection:
    """페이지 전체 감지 결과"""
    page_path: str
    detections: List[DetectionResult]
    image_width: int
    image_height: int


class YOLODetector:
    """
    YOLO 기반 문서 영역 감지기
    
    사용 예시:
        detector = YOLODetector(model_path="models/yolo_literature.pt")
        results = detector.detect_page("data/literature/pages/page_001.png")
        for det in results.detections:
            print(f"{det.class_name}: {det.confidence:.2f} at {det.bbox}")
    """
    
    # 클래스 매핑 (YOLO 모델 학습 시 사용)
    # 업데이트된 클래스 정의 (6개 클래스)
    CLASS_NAMES = {
        0: "header",       # 페이지 최상단 제목 -> 강의 제목 (Lesson)
        1: "section",      # 중간 제목 (예: "1 시적 표현") -> 개념 제목 (Unit: concept, subtype: title)
        2: "passage",      # 작품 전문 전체 -> 본문 (Unit: passage)
        3: "question",     # 문제 전체 (선지 포함) -> 문제 (Unit: question)
        4: "concept_box",  # 굵은 테두리 큰 박스 -> 개념 내용 (Unit: concept, subtype: content)
        5: "sidebar",     # 왼쪽 세로 보조 설명 -> 세부 개념 (Unit: concept_detail)
    }
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        confidence_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        device: str = "cpu"  # "cpu" or "cuda"
    ):
        """
        YOLO 감지기 초기화
        
        Args:
            model_path: 학습된 YOLO 모델 경로 (.pt 파일)
            confidence_threshold: 신뢰도 임계값 (0-1)
            iou_threshold: NMS IoU 임계값
            device: 사용할 디바이스 ("cpu" or "cuda")
        """
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.device = device
        self.model = None
        
        if not YOLO_AVAILABLE:
            raise ImportError(
                "ultralytics가 설치되지 않았습니다. "
                "설치: pip install ultralytics"
            )
        
        if model_path:
            self.load_model(model_path)
        else:
            # 기본 모델 경로 시도
            default_path = Path(__file__).parent.parent.parent / "models" / "yolo_literature.pt"
            if default_path.exists():
                self.load_model(str(default_path))
            else:
                print("[YOLODetector] 경고: 모델 파일이 없습니다. 학습이 필요합니다.")
    
    def load_model(self, model_path: str):
        """YOLO 모델 로드"""
        if not Path(model_path).exists():
            raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {model_path}")
        
        try:
            self.model = YOLO(model_path)
            print(f"[YOLODetector] 모델 로드 완료: {model_path}")
        except Exception as e:
            raise RuntimeError(f"모델 로드 실패: {e}")
    
    def detect_page(
        self,
        image_path: str,
        return_image: bool = False
    ) -> PageDetection:
        """
        페이지 이미지에서 영역 감지
        
        Args:
            image_path: 이미지 파일 경로
            return_image: 결과 이미지도 반환할지 여부
            
        Returns:
            PageDetection 객체
        """
        if not self.model:
            raise RuntimeError("모델이 로드되지 않았습니다. load_model()을 먼저 호출하세요.")
        
        if not PIL_AVAILABLE:
            raise ImportError("PIL이 필요합니다. pip install pillow")
        
        # 이미지 로드
        image = Image.open(image_path)
        image_width, image_height = image.size
        
        # YOLO 추론
        results = self.model.predict(
            source=image_path,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            device=self.device,
            verbose=False
        )
        
        # 결과 파싱
        detections = []
        if results and len(results) > 0:
            result = results[0]  # 첫 번째 결과
            
            # 박스 좌표 (xyxy 형식, 픽셀 단위)
            boxes = result.boxes.xyxy.cpu().numpy() if hasattr(result.boxes, 'xyxy') else []
            confidences = result.boxes.conf.cpu().numpy() if hasattr(result.boxes, 'conf') else []
            class_ids = result.boxes.cls.cpu().numpy().astype(int) if hasattr(result.boxes, 'cls') else []
            
            for i in range(len(boxes)):
                x1, y1, x2, y2 = boxes[i]
                confidence = float(confidences[i])
                class_id = int(class_ids[i])
                
                # 정규화된 좌표로 변환 (0-1)
                bbox_normalized = [
                    float(x1 / image_width),
                    float(y1 / image_height),
                    float(x2 / image_width),
                    float(y2 / image_height)
                ]
                
                # 클래스 이름
                class_name = self.CLASS_NAMES.get(class_id, f"class_{class_id}")
                
                detections.append(DetectionResult(
                    bbox=bbox_normalized,
                    confidence=confidence,
                    class_id=class_id,
                    class_name=class_name
                ))
        
        return PageDetection(
            page_path=image_path,
            detections=detections,
            image_width=image_width,
            image_height=image_height
        )
    
    def detect_batch(
        self,
        image_paths: List[str],
        batch_size: int = 8
    ) -> List[PageDetection]:
        """
        여러 이미지를 배치로 처리
        
        Args:
            image_paths: 이미지 파일 경로 리스트
            batch_size: 배치 크기
            
        Returns:
            PageDetection 리스트
        """
        results = []
        for i in range(0, len(image_paths), batch_size):
            batch = image_paths[i:i + batch_size]
            batch_results = self.model.predict(
                source=batch,
                conf=self.confidence_threshold,
                iou=self.iou_threshold,
                device=self.device,
                verbose=False
            )
            
            # 각 결과를 PageDetection으로 변환
            for j, result in enumerate(batch_results):
                image_path = batch[j]
                image = Image.open(image_path)
                image_width, image_height = image.size
                
                detections = []
                if hasattr(result, 'boxes'):
                    boxes = result.boxes.xyxy.cpu().numpy() if hasattr(result.boxes, 'xyxy') else []
                    confidences = result.boxes.conf.cpu().numpy() if hasattr(result.boxes, 'conf') else []
                    class_ids = result.boxes.cls.cpu().numpy().astype(int) if hasattr(result.boxes, 'cls') else []
                    
                    for k in range(len(boxes)):
                        x1, y1, x2, y2 = boxes[k]
                        bbox_normalized = [
                            float(x1 / image_width),
                            float(y1 / image_height),
                            float(x2 / image_width),
                            float(y2 / image_height)
                        ]
                        class_name = self.CLASS_NAMES.get(int(class_ids[k]), f"class_{class_ids[k]}")
                        detections.append(DetectionResult(
                            bbox=bbox_normalized,
                            confidence=float(confidences[k]),
                            class_id=int(class_ids[k]),
                            class_name=class_name
                        ))
                
                results.append(PageDetection(
                    page_path=image_path,
                    detections=detections,
                    image_width=image_width,
                    image_height=image_height
                ))
        
        return results
    
    def visualize_detections(
        self,
        image_path: str,
        output_path: Optional[str] = None,
        show_labels: bool = True
    ) -> Image.Image:
        """
        감지 결과를 시각화
        
        Args:
            image_path: 원본 이미지 경로
            output_path: 저장할 경로 (None이면 반환만)
            show_labels: 라벨 표시 여부
            
        Returns:
            시각화된 이미지
        """
        if not self.model:
            raise RuntimeError("모델이 로드되지 않았습니다.")
        
        # YOLO의 내장 시각화 기능 사용
        results = self.model.predict(
            source=image_path,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            device=self.device,
            save=False,
            show=False
        )
        
        if results and len(results) > 0:
            # 결과 이미지 가져오기
            annotated_image = results[0].plot()
            annotated_pil = Image.fromarray(annotated_image)
            
            if output_path:
                annotated_pil.save(output_path)
                print(f"[YOLODetector] 시각화 결과 저장: {output_path}")
            
            return annotated_pil
        
        return Image.open(image_path)


def get_detector(
    model_path: Optional[str] = None,
    confidence_threshold: float = 0.25
) -> YOLODetector:
    """
    YOLO 감지기 인스턴스 생성 (팩토리 함수)
    
    Args:
        model_path: 모델 경로 (None이면 기본 경로 시도)
        confidence_threshold: 신뢰도 임계값
        
    Returns:
        YOLODetector 인스턴스
    """
    return YOLODetector(
        model_path=model_path,
        confidence_threshold=confidence_threshold
    )


# ============================================================================
# Roboflow API 기반 감지기
# ============================================================================

class RoboflowDetector:
    """
    Roboflow API를 사용한 YOLO 감지기
    
    사용 예시:
        detector = RoboflowDetector(
            workspace_id="-wshlq",
            project_id="2",
            api_key="ohDbNa6uGc3Aozm81aci"
        )
        results = detector.detect_page("data/literature/pages/page_001.png")
    """
    
    # 클래스 매핑 (Roboflow 모델의 클래스 이름)
    # 업데이트된 클래스 정의 (6개 클래스)
    # 매핑: header -> Lesson, section/concept_box/sidebar -> concept, passage -> 본문, question -> 문제
    CLASS_NAMES = {
        "header": 0,       # 페이지 최상단 제목 -> 강의 제목 (Lesson)
        "section": 1,       # 중간 제목 -> 개념 제목 (Unit: concept, subtype: title)
        "passage": 2,      # 작품 전문 전체 -> 본문 (Unit: passage)
        "question": 3,     # 문제 전체 (선지 포함) -> 문제 (Unit: question)
        "concept_box": 4,  # 굵은 테두리 큰 박스 -> 개념 내용 (Unit: concept, subtype: content)
        "sidebar": 5,      # 왼쪽 세로 보조 설명 -> 세부 개념 (Unit: concept_detail)
    }
    
    def __init__(
        self,
        workspace_id: str = "-wshlq",
        project_id: str = "2",
        api_key: Optional[str] = None,
        confidence_threshold: float = 0.25,
        overlap_threshold: float = 30.0
    ):
        """
        Roboflow 감지기 초기화
        
        Args:
            workspace_id: Roboflow 워크스페이스 ID
            project_id: 프로젝트 ID
            api_key: Roboflow API 키 (None이면 환경변수에서 로드)
            confidence_threshold: 신뢰도 임계값 (0-100)
            overlap_threshold: NMS IoU 임계값 (0-100)
        """
        self.workspace_id = workspace_id
        self.project_id = project_id
        self.api_key = api_key or os.getenv("ROBOFLOW_API_KEY")
        self.confidence_threshold = confidence_threshold
        self.overlap_threshold = overlap_threshold
        
        if not self.api_key:
            raise ValueError(
                "Roboflow API 키가 필요합니다. "
                "환경변수 ROBOFLOW_API_KEY를 설정하거나 api_key 파라미터를 제공하세요."
            )
        
        # API 엔드포인트 URL
        self.api_url = f"https://detect.roboflow.com/{workspace_id}/{project_id}"
        
        print(f"[RoboflowDetector] 초기화 완료: workspace={workspace_id}, project={project_id}")
    
    def _image_to_base64(self, image_path: str) -> str:
        """이미지를 base64로 인코딩"""
        if not PIL_AVAILABLE:
            raise ImportError("PIL이 필요합니다. pip install pillow")
        
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    
    def _image_pil_to_base64(self, image: Image.Image) -> str:
        """PIL Image를 base64로 인코딩"""
        import io
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
    
    def detect_page(
        self,
        image_path: str,
        return_image: bool = False
    ) -> PageDetection:
        """
        페이지 이미지에서 영역 감지 (Roboflow API 사용)
        
        Args:
            image_path: 이미지 파일 경로
            return_image: 결과 이미지도 반환할지 여부 (Roboflow는 지원 안 함)
            
        Returns:
            PageDetection 객체
        """
        if not PIL_AVAILABLE:
            raise ImportError("PIL이 필요합니다. pip install pillow")
        
        # 이미지 로드 및 크기 확인
        image = Image.open(image_path)
        image_width, image_height = image.size
        
        # base64 인코딩
        image_base64 = self._image_to_base64(image_path)
        
        # API 요청
        # Roboflow API: base64 문자열을 직접 body로 전송
        params = {
            "api_key": self.api_key,
            "confidence": int(self.confidence_threshold * 100),  # 0-100 범위
            "overlap": int(self.overlap_threshold)  # 0-100 범위
        }
        
        try:
            # Raw base64 문자열을 body로 전송 (curl -d @- 형식과 동일)
            response = requests.post(
                self.api_url,
                data=image_base64.encode('utf-8'),  # bytes로 변환
                params=params,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Roboflow API 요청 실패: {e}")
        except ValueError as e:
            raise RuntimeError(f"Roboflow API 응답 파싱 실패: {e}")
        
        # 결과 파싱
        detections = []
        
        if "predictions" in result:
            for pred in result["predictions"]:
                # Roboflow 응답 형식: {"x": center_x, "y": center_y, "width": w, "height": h, "confidence": conf, "class": class_name}
                center_x = pred.get("x", 0)
                center_y = pred.get("y", 0)
                width = pred.get("width", 0)
                height = pred.get("height", 0)
                confidence = pred.get("confidence", 0.0)
                class_name = pred.get("class", "")
                
                # center_x, center_y, width, height는 픽셀 단위
                # YOLO 형식 (정규화된 bbox)으로 변환: [x1, y1, x2, y2]
                x1 = (center_x - width / 2) / image_width
                y1 = (center_y - height / 2) / image_height
                x2 = (center_x + width / 2) / image_width
                y2 = (center_y + height / 2) / image_height
                
                # 클래스 ID 매핑
                class_id = self.CLASS_NAMES.get(class_name.lower(), -1)
                
                detections.append(DetectionResult(
                    bbox=[x1, y1, x2, y2],
                    confidence=confidence,
                    class_id=class_id,
                    class_name=class_name
                ))
        
        return PageDetection(
            page_path=image_path,
            detections=detections,
            image_width=image_width,
            image_height=image_height
        )
    
    def detect_image(
        self,
        image: Image.Image
    ) -> PageDetection:
        """
        PIL Image에서 영역 감지
        
        Args:
            image: PIL Image 객체
            
        Returns:
            PageDetection 객체
        """
        image_width, image_height = image.size
        
        # base64 인코딩
        image_base64 = self._image_pil_to_base64(image)
        
        # API 요청
        params = {
            "api_key": self.api_key,
            "confidence": int(self.confidence_threshold * 100),
            "overlap": int(self.overlap_threshold)
        }
        
        try:
            # Raw base64 문자열을 body로 전송
            response = requests.post(
                self.api_url,
                data=image_base64.encode('utf-8'),  # bytes로 변환
                params=params,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Roboflow API 요청 실패: {e}")
        except ValueError as e:
            raise RuntimeError(f"Roboflow API 응답 파싱 실패: {e}")
        
        # 결과 파싱
        detections = []
        
        if "predictions" in result:
            for pred in result["predictions"]:
                center_x = pred.get("x", 0)
                center_y = pred.get("y", 0)
                width = pred.get("width", 0)
                height = pred.get("height", 0)
                confidence = pred.get("confidence", 0.0)
                class_name = pred.get("class", "")
                
                x1 = (center_x - width / 2) / image_width
                y1 = (center_y - height / 2) / image_height
                x2 = (center_x + width / 2) / image_width
                y2 = (center_y + height / 2) / image_height
                
                class_id = self.CLASS_NAMES.get(class_name.lower(), -1)
                
                detections.append(DetectionResult(
                    bbox=[x1, y1, x2, y2],
                    confidence=confidence,
                    class_id=class_id,
                    class_name=class_name
                ))
        
        return PageDetection(
            page_path="<in-memory>",
            detections=detections,
            image_width=image_width,
            image_height=image_height
        )


def get_roboflow_detector(
    workspace_id: str = "-wshlq",
    project_id: str = "2",
    api_key: Optional[str] = None,
    confidence_threshold: float = 0.25
) -> RoboflowDetector:
    """
    Roboflow 감지기 인스턴스 생성 (팩토리 함수)
    
    Args:
        workspace_id: Roboflow 워크스페이스 ID
        project_id: 프로젝트 ID
        api_key: API 키 (None이면 환경변수에서 로드)
        confidence_threshold: 신뢰도 임계값
        
    Returns:
        RoboflowDetector 인스턴스
    """
    return RoboflowDetector(
        workspace_id=workspace_id,
        project_id=project_id,
        api_key=api_key,
        confidence_threshold=confidence_threshold
    )
