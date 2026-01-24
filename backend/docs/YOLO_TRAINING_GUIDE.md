# YOLO 모델 로컬 학습 가이드

이 문서는 데이터셋이 있을 때 로컬에서 YOLO 모델을 학습하는 방법을 설명합니다.

## 데이터셋 형식 확인

YOLO 학습을 위해서는 다음 형식의 데이터셋이 필요합니다:

```
yolo_dataset/
├── images/
│   ├── train/          # 학습 이미지
│   ├── val/            # 검증 이미지
│   └── test/           # 테스트 이미지 (선택)
└── labels/
    ├── train/          # 학습 라벨 (.txt 파일)
    ├── val/            # 검증 라벨
    └── test/           # 테스트 라벨
```

### 라벨 파일 형식

각 이미지마다 같은 이름의 `.txt` 파일이 필요합니다:

```
# 예: page_001.png → page_001.txt
0 0.5 0.3 0.8 0.6  # class_id center_x center_y width height (모두 0-1 정규화)
1 0.2 0.7 0.4 0.9
```

**형식**: `class_id center_x center_y width height`
- 모든 값은 0-1 사이로 정규화
- `center_x, center_y`: 바운딩 박스 중심 좌표
- `width, height`: 바운딩 박스 크기

**클래스 매핑**:
- `0`: header (헤더 영역)
- `1`: section (섹션 영역)
- `2`: passage (본문 영역)
- `3`: question (문제 영역)
- `4`: concept_box (개념박스 영역)
- `5`: sidebar (사이드바 영역)

## 데이터셋 준비 방법

### 방법 1: 기존 이미지에서 자동 생성 (부분 자동화)

```bash
cd api
python scripts/yolo/prepare_dataset.py
```

이 스크립트는:
1. `api/data/literature/pages/`에서 페이지 이미지 수집
2. `api/data/yolo_dataset/` 구조 생성
3. 이미지를 train/val/test로 분할
4. 빈 라벨 파일 생성 (수동 라벨링 필요)

### 방법 2: LabelImg로 수동 라벨링 (권장)

#### 1. LabelImg 설치

```bash
pip install labelImg
```

#### 2. LabelImg 실행

```bash
labelImg
```

#### 3. 라벨링 작업

1. **Open Dir**: `api/data/yolo_dataset/images/train/` 선택
2. **Change Save Dir**: `api/data/yolo_dataset/labels/train/` 선택
3. **YOLO 형식 선택**: 오른쪽 상단에서 "YOLO" 선택 (PascalVOC 아님)
4. **클래스 정의**: 
   - `header` (0)
   - `section` (1)
   - `passage` (2)
   - `question` (3)
   - `concept_box` (4)
   - `sidebar` (5)
5. **라벨링**: 각 이미지에서 영역을 드래그하여 라벨 지정
   - `W`: 박스 그리기
   - `D`: 다음 이미지
   - `A`: 이전 이미지

### 방법 3: Roboflow에서 Export

Roboflow에서 이미 라벨링한 데이터셋이 있다면:

1. Roboflow 프로젝트 열기
2. **Export** → **YOLOv8** 선택
3. 다운로드한 ZIP 파일 압축 해제
4. `api/data/yolo_dataset/`에 복사

## 데이터셋 설정 파일 생성

```bash
cd api
python scripts/yolo/prepare_dataset.py
```

또는 수동으로 `api/data/yolo_dataset/dataset.yaml` 생성:

```yaml
# dataset.yaml
path: C:/Users/user/Desktop/jeomgeuli-suneung-helper/api/data/yolo_dataset
train: images/train
val: images/val
test: images/test

# 클래스 정의
names:
  0: header
  1: section
  2: passage
  3: question
  4: concept_box
  5: sidebar

# 클래스 개수
nc: 6
```

## 모델 학습

### 1. 필수 패키지 설치

```bash
pip install ultralytics
```

### 2. 학습 실행

```bash
cd api
python scripts/yolo/train_yolo.py
```

### 3. 학습 옵션

```bash
# 작은 모델로 빠르게 학습 (테스트용)
python scripts/yolo/train_yolo.py --model-size n --epochs 50

# 중간 모델로 학습 (권장)
python scripts/yolo/train_yolo.py --model-size s --epochs 100

# 큰 모델로 정확도 향상
python scripts/yolo/train_yolo.py --model-size m --epochs 150

# GPU 사용 (NVIDIA GPU 있는 경우)
python scripts/yolo/train_yolo.py --model-size s --device cuda --batch-size 32
```

### 4. 학습 모니터링

학습 중 생성되는 파일:
- `runs/detect/literature_detector/weights/best.pt`: 최고 성능 모델
- `runs/detect/literature_detector/results.png`: 학습 곡선
- `runs/detect/literature_detector/confusion_matrix.png`: 혼동 행렬

학습 진행 상황은 터미널에서 실시간으로 확인할 수 있습니다.

## 모델 평가

```bash
cd api
python scripts/yolo/evaluate_yolo.py
```

또는 학습 스크립트에서 자동으로 평가가 실행됩니다.

## 학습된 모델 사용

### 로컬 모델 사용

```python
from app.dl.yolo_detector import YOLODetector

# 학습된 모델 로드
detector = YOLODetector(
    model_path="models/yolo_literature.pt",
    confidence_threshold=0.25
)

# 페이지 감지
results = detector.detect_page("data/literature/pages/page_001.png")

for det in results.detections:
    print(f"{det.class_name}: {det.confidence:.2%}")
```

### Roboflow API와 비교

로컬 모델의 장점:
- ✅ 오프라인 사용 가능
- ✅ 빠른 추론 속도 (네트워크 지연 없음)
- ✅ API 호출 비용 없음
- ✅ 데이터 프라이버시 보장

Roboflow API의 장점:
- ✅ 설정 간단 (모델 파일 불필요)
- ✅ 자동 스케일링
- ✅ 모델 업데이트 용이

## 데이터셋 품질 향상

### 1. 충분한 데이터

- **최소**: 클래스당 50-100개 이미지
- **권장**: 클래스당 200-500개 이미지
- **이상적**: 클래스당 1000개 이상

### 2. 데이터 분할

- **Train**: 70% (학습용)
- **Val**: 20% (검증용)
- **Test**: 10% (최종 평가용)

### 3. 데이터 증강

YOLOv8은 자동으로 데이터 증강을 수행합니다:
- 회전
- 크기 조정
- 밝기 조정
- Mosaic augmentation

### 4. 클래스 불균형 해결

클래스별 데이터가 불균형한 경우:
- 데이터 증강으로 부족한 클래스 보강
- 클래스 가중치 조정
- Focal Loss 사용

## 문제 해결

### 학습이 시작되지 않음

```
FileNotFoundError: 데이터셋 설정 파일을 찾을 수 없습니다
```

**해결**: `dataset.yaml` 파일이 올바른 경로에 있는지 확인

### 메모리 부족

```
RuntimeError: CUDA out of memory
```

**해결**: 
- `--batch-size` 줄이기 (예: 16 → 8)
- `--model-size` 줄이기 (예: m → s)
- `--image-size` 줄이기 (예: 640 → 416)

### 학습이 너무 느림

**해결**:
- GPU 사용 (`--device cuda`)
- 배치 크기 증가 (`--batch-size 32`)
- 모델 크기 줄이기 (`--model-size n`)

### 정확도가 낮음

**해결**:
- 더 많은 데이터 수집
- 라벨 품질 확인
- 학습 에포크 증가
- 더 큰 모델 사용 (`--model-size m` 또는 `l`)

## 다음 단계

1. **모델 최적화**: ONNX 또는 TensorRT로 변환
2. **파이프라인 통합**: PDF 파이프라인에 자동 감지 추가
3. **성능 평가**: 실제 데이터로 정확도 측정
4. **모델 업데이트**: 더 많은 데이터로 재학습

## 참고 자료

- [Ultralytics YOLOv8 문서](https://docs.ultralytics.com/)
- [YOLO 데이터셋 형식](https://docs.ultralytics.com/datasets/)
- [LabelImg GitHub](https://github.com/HumanSignal/labelImg)
