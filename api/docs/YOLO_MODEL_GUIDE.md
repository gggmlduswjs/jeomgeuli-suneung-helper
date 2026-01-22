# YOLO 모델 학습 및 통합 가이드

이 문서는 수능특강 교재 PDF 페이지에서 문제, 개념, 본문 영역을 자동으로 감지하는 YOLO 모델을 만드는 방법을 설명합니다.

## 목차

1. [개요](#개요)
2. [환경 설정](#환경-설정)
3. [데이터셋 준비](#데이터셋-준비)
4. [모델 학습](#모델-학습)
5. [모델 평가](#모델-평가)
6. [모델 통합](#모델-통합)
7. [성능 최적화](#성능-최적화)

## 개요

### YOLO 모델의 목적

- **문제 영역 감지**: PDF 페이지에서 문제가 있는 영역을 자동으로 찾기
- **개념 영역 감지**: 개념 설명이 있는 영역 감지
- **본문 영역 감지**: 작품 본문이 있는 영역 감지
- **제목/헤더 감지**: 섹션 제목 감지
- **이미지/그림 감지**: 삽화, 그래프 등 이미지 영역 감지

### 사용 모델

- **YOLOv8** (권장): Ultralytics의 최신 버전, 사용하기 쉬움
- **YOLOv5**: 대안 옵션

## 환경 설정

### 1. 필수 패키지 설치

```bash
# YOLOv8 (권장)
pip install ultralytics

# 또는 YOLOv5
pip install torch torchvision
# YOLOv5는 GitHub에서 설치
git clone https://github.com/ultralytics/yolov5
cd yolov5
pip install -r requirements.txt
```

### 2. 프로젝트 구조 생성

```
api/
├── models/
│   └── yolo_literature.pt          # 학습된 모델 (학습 후 생성)
├── data/
│   └── yolo_dataset/
│       ├── images/
│       │   ├── train/              # 학습 이미지
│       │   ├── val/                # 검증 이미지
│       │   └── test/                # 테스트 이미지
│       └── labels/
│           ├── train/              # YOLO 형식 라벨 (.txt)
│           ├── val/
│           └── test/
├── scripts/
│   └── yolo/
│       ├── prepare_dataset.py      # 데이터셋 준비 스크립트
│       ├── train_yolo.py            # 모델 학습 스크립트
│       ├── evaluate_yolo.py         # 모델 평가 스크립트
│       └── label_images.py          # 이미지 라벨링 도구
└── app/
    └── dl/
        └── yolo_detector.py        # YOLO 감지기 모듈 (이미 생성됨)
```

## 데이터셋 준비

### 1. 이미지 수집

프로젝트에 이미 있는 이미지들을 활용:

```bash
# literature 페이지 이미지 사용
api/data/literature/pages/*.png
```

### 2. 라벨링 도구 선택

#### 옵션 1: LabelImg (GUI 도구, 권장)

```bash
# 설치
pip install labelImg

# 실행
labelImg
```

**사용 방법:**
1. `Open Dir`로 `api/data/yolo_dataset/images/train/` 선택
2. `Change Save Dir`로 `api/data/yolo_dataset/labels/train/` 선택
3. `YOLO` 형식 선택 (PascalVOC가 아닌)
4. 각 이미지에서 영역을 드래그하여 라벨링:
   - `problem`: 문제 영역
   - `concept`: 개념 설명 영역
   - `content`: 본문/작품 영역
   - `title`: 제목/헤더 영역
   - `figure`: 이미지/그림 영역

#### 옵션 2: Roboflow (온라인, 협업 가능)

1. [Roboflow](https://roboflow.com) 가입
2. 프로젝트 생성
3. 이미지 업로드 및 라벨링
4. YOLO 형식으로 export

#### 옵션 3: 자동 라벨링 (기존 데이터 활용)

기존에 추출된 `concepts_images`, `problems_images`, `content_images`를 활용하여 자동으로 라벨 생성:

```python
# scripts/yolo/prepare_dataset.py 예시
```

### 3. YOLO 라벨 형식

각 이미지마다 `.txt` 파일이 필요합니다:

```
# 예: page_001.txt
0 0.5 0.3 0.8 0.6  # class_id center_x center_y width height (모두 0-1 정규화)
1 0.2 0.7 0.4 0.9
```

**클래스 매핑:**
- `0`: problem
- `1`: concept
- `2`: content
- `3`: title
- `4`: figure

### 4. 데이터셋 분할

```python
# scripts/yolo/prepare_dataset.py
import shutil
from pathlib import Path
import random

def split_dataset(source_dir, train_ratio=0.7, val_ratio=0.2, test_ratio=0.1):
    """데이터셋을 train/val/test로 분할"""
    images = list(Path(source_dir).glob("*.png"))
    random.shuffle(images)
    
    n = len(images)
    train_end = int(n * train_ratio)
    val_end = train_end + int(n * val_ratio)
    
    # 분할 및 복사
    # ...
```

## 모델 학습

### 1. 기본 학습 스크립트

```python
# scripts/yolo/train_yolo.py
from ultralytics import YOLO
from pathlib import Path

def train_yolo_model():
    """YOLOv8 모델 학습"""
    
    # 사전 학습된 모델 로드 (YOLOv8n = nano, 작고 빠름)
    model = YOLO('yolov8n.pt')  # 또는 yolov8s.pt, yolov8m.pt, yolov8l.pt, yolov8x.pt
    
    # 데이터셋 설정 파일 경로
    dataset_yaml = Path(__file__).parent.parent.parent / "data" / "yolo_dataset" / "dataset.yaml"
    
    # 학습 시작
    results = model.train(
        data=str(dataset_yaml),           # 데이터셋 설정 파일
        epochs=100,                        # 학습 에포크
        imgsz=640,                        # 이미지 크기
        batch=16,                          # 배치 크기 (GPU 메모리에 따라 조정)
        name='literature_detector',        # 실험 이름
        device='cuda',                     # 'cpu' or 'cuda'
        patience=20,                       # Early stopping patience
        save=True,                         # 체크포인트 저장
        plots=True,                        # 학습 그래프 생성
    )
    
    # 최종 모델 저장
    best_model_path = Path("runs/detect/literature_detector/weights/best.pt")
    target_path = Path(__file__).parent.parent.parent / "models" / "yolo_literature.pt"
    shutil.copy(best_model_path, target_path)
    print(f"모델 저장 완료: {target_path}")

if __name__ == "__main__":
    train_yolo_model()
```

### 2. 데이터셋 설정 파일

```yaml
# data/yolo_dataset/dataset.yaml
path: api/data/yolo_dataset  # 데이터셋 루트 경로
train: images/train          # 학습 이미지 경로 (path 기준 상대 경로)
val: images/val              # 검증 이미지 경로
test: images/test            # 테스트 이미지 경로 (선택)

# 클래스 정의
names:
  0: problem
  1: concept
  2: content
  3: title
  4: figure

# 클래스 개수
nc: 5
```

### 3. 학습 실행

```bash
cd api
python scripts/yolo/train_yolo.py
```

### 4. 학습 모니터링

학습 중 생성되는 파일:
- `runs/detect/literature_detector/weights/best.pt`: 최고 성능 모델
- `runs/detect/literature_detector/results.png`: 학습 곡선
- `runs/detect/literature_detector/confusion_matrix.png`: 혼동 행렬

## 모델 평가

```python
# scripts/yolo/evaluate_yolo.py
from ultralytics import YOLO
from pathlib import Path

def evaluate_model():
    """모델 성능 평가"""
    model_path = Path(__file__).parent.parent.parent / "models" / "yolo_literature.pt"
    model = YOLO(str(model_path))
    
    # 검증 데이터셋으로 평가
    results = model.val(
        data="data/yolo_dataset/dataset.yaml",
        imgsz=640,
        conf=0.25,
        iou=0.45
    )
    
    print(f"mAP50: {results.box.map50}")
    print(f"mAP50-95: {results.box.map}")

if __name__ == "__main__":
    evaluate_model()
```

## 모델 통합

### 1. 파이프라인에 통합

```python
# api/app/services/textbook_pipeline.py 수정 예시
from app.dl.yolo_detector import YOLODetector

def extract_with_yolo(page_image_path: str):
    """YOLO를 사용한 영역 감지"""
    detector = YOLODetector(
        model_path="models/yolo_literature.pt",
        confidence_threshold=0.25
    )
    
    results = detector.detect_page(page_image_path)
    
    # 감지된 영역별로 처리
    for det in results.detections:
        if det.class_name == "problem":
            # 문제 영역 처리
            pass
        elif det.class_name == "concept":
            # 개념 영역 처리
            pass
        # ...
```

### 2. API 엔드포인트 추가

```python
# api/app/routers/books.py에 추가
@router.post("/books/{book_id}/detect-regions")
async def detect_regions_with_yolo(
    book_id: str,
    page_number: int,
    db: Session = Depends(get_db)
):
    """YOLO를 사용한 페이지 영역 감지"""
    from app.dl.yolo_detector import YOLODetector
    
    # 페이지 이미지 경로 찾기
    page_image = f"data/literature/pages/page_{page_number:03d}.png"
    
    detector = YOLODetector()
    results = detector.detect_page(page_image)
    
    return {
        "page": page_number,
        "detections": [
            {
                "class": det.class_name,
                "confidence": det.confidence,
                "bbox": det.bbox
            }
            for det in results.detections
        ]
    }
```

## 성능 최적화

### 1. 모델 크기 선택

- **YOLOv8n (nano)**: 가장 빠름, 정확도 낮음 (모바일/엣지)
- **YOLOv8s (small)**: 균형잡힌 선택 (권장)
- **YOLOv8m (medium)**: 더 정확하지만 느림
- **YOLOv8l/x (large/xlarge)**: 최고 정확도, 느림

### 2. 추론 최적화

```python
# ONNX 변환 (더 빠른 추론)
from ultralytics import YOLO

model = YOLO("models/yolo_literature.pt")
model.export(format="onnx")  # ONNX 형식으로 변환

# TensorRT 변환 (NVIDIA GPU 최적화)
model.export(format="engine", device=0)
```

### 3. 배치 처리

여러 페이지를 한 번에 처리:

```python
detector = YOLODetector()
image_paths = ["page_001.png", "page_002.png", ...]
results = detector.detect_batch(image_paths, batch_size=8)
```

## 다음 단계

1. **데이터 증강**: 회전, 크기 조정, 밝기 조정 등으로 데이터셋 확장
2. **전이 학습**: 사전 학습된 모델을 기반으로 fine-tuning
3. **앙상블**: 여러 모델의 결과를 결합하여 정확도 향상
4. **실시간 추론**: GPU 가속 및 모델 최적화로 실시간 처리

## 참고 자료

- [Ultralytics YOLOv8 문서](https://docs.ultralytics.com/)
- [YOLOv5 GitHub](https://github.com/ultralytics/yolov5)
- [LabelImg GitHub](https://github.com/HumanSignal/labelImg)
