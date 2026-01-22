# Roboflow YOLO 모델 통합 가이드

이 문서는 Roboflow에서 학습한 YOLO 모델을 프로젝트에 통합하는 방법을 설명합니다.

## 개요

Roboflow는 클라우드 기반 객체 감지 모델 학습 및 배포 플랫폼입니다. 학습한 모델을 API를 통해 사용할 수 있습니다.

## API 정보

- **Workspace ID**: `-wshlq`
- **Project ID**: `2`
- **API Key**: `ohDbNa6uGc3Aozm81aci` (환경변수로 관리 권장)
- **API Endpoint**: `https://detect.roboflow.com/-wshlq/2`

## 환경 설정

### 1. API 키 설정

`.env` 파일에 API 키 추가:

```bash
# api/.env
ROBOFLOW_API_KEY=ohDbNa6uGc3Aozm81aci
ROBOFLOW_WORKSPACE_ID=-wshlq
ROBOFLOW_PROJECT_ID=2
```

### 2. 패키지 설치

```bash
pip install requests pillow
```

## 사용 방법

### 기본 사용

```python
from app.dl.yolo_detector import RoboflowDetector

# 감지기 생성
detector = RoboflowDetector(
    workspace_id="-wshlq",
    project_id="2",
    api_key="ohDbNa6uGc3Aozm81aci",  # 또는 환경변수에서 자동 로드
    confidence_threshold=0.25
)

# 페이지 이미지 감지
results = detector.detect_page("data/literature/pages/page_001.png")

# 결과 확인
for det in results.detections:
    print(f"{det.class_name}: {det.confidence:.2f} at {det.bbox}")
```

### 환경변수 사용

```python
from app.dl.yolo_detector import get_roboflow_detector

# 환경변수에서 자동으로 로드
detector = get_roboflow_detector(
    confidence_threshold=0.25
)

results = detector.detect_page("data/literature/pages/page_001.png")
```

### PIL Image 직접 사용

```python
from PIL import Image
from app.dl.yolo_detector import RoboflowDetector

detector = RoboflowDetector()

# 이미지 로드
image = Image.open("page_001.png")

# 감지
results = detector.detect_image(image)
```

## API 응답 형식

Roboflow API는 다음과 같은 형식으로 응답합니다:

```json
{
  "predictions": [
    {
      "x": 500,           // 중심 X 좌표 (픽셀)
      "y": 300,           // 중심 Y 좌표 (픽셀)
      "width": 400,       // 너비 (픽셀)
      "height": 200,      // 높이 (픽셀)
      "confidence": 0.95, // 신뢰도 (0-1)
      "class": "problem"  // 클래스 이름
    }
  ]
}
```

## 클래스 매핑

- `problem`: 문제 영역
- `concept`: 개념 설명 영역
- `content`: 본문/작품 영역
- `title`: 제목/헤더 영역
- `figure`: 이미지/그림 영역

## 파이프라인 통합

### 1. PDF 파이프라인에 통합

```python
# api/app/services/textbook_pipeline.py
from app.dl.yolo_detector import RoboflowDetector

def extract_with_roboflow(page_image_path: str):
    """Roboflow를 사용한 영역 감지"""
    detector = RoboflowDetector()
    results = detector.detect_page(page_image_path)
    
    # 감지된 영역별로 처리
    for det in results.detections:
        if det.class_name == "problem":
            # 문제 영역 처리
            bbox_pixels = [
                int(det.bbox[0] * results.image_width),
                int(det.bbox[1] * results.image_height),
                int(det.bbox[2] * results.image_width),
                int(det.bbox[3] * results.image_height)
            ]
            # 이미지 크롭 및 저장
            # ...
```

### 2. API 엔드포인트 추가

```python
# api/app/routers/books.py
@router.post("/books/{book_id}/detect-regions")
async def detect_regions_with_roboflow(
    book_id: str,
    page_number: int,
    db: Session = Depends(get_db)
):
    """Roboflow를 사용한 페이지 영역 감지"""
    from app.dl.yolo_detector import RoboflowDetector
    
    # 페이지 이미지 경로 찾기
    page_image = f"data/literature/pages/page_{page_number:03d}.png"
    
    detector = RoboflowDetector()
    results = detector.detect_page(page_image)
    
    return {
        "page": page_number,
        "detections": [
            {
                "class": det.class_name,
                "confidence": det.confidence,
                "bbox": det.bbox,
                "bbox_pixels": [
                    int(det.bbox[0] * results.image_width),
                    int(det.bbox[1] * results.image_height),
                    int(det.bbox[2] * results.image_width),
                    int(det.bbox[3] * results.image_height)
                ]
            }
            for det in results.detections
        ]
    }
```

## 성능 최적화

### 1. 배치 처리

Roboflow API는 단일 이미지씩 처리하므로, 여러 이미지를 순차적으로 처리:

```python
detector = RoboflowDetector()
image_paths = ["page_001.png", "page_002.png", ...]

results_list = []
for image_path in image_paths:
    results = detector.detect_page(image_path)
    results_list.append(results)
```

### 2. 캐싱

같은 이미지를 여러 번 감지하지 않도록 캐싱:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_detect(image_path: str):
    detector = RoboflowDetector()
    return detector.detect_page(image_path)
```

### 3. 비동기 처리

여러 이미지를 병렬로 처리:

```python
import asyncio
import aiohttp

async def detect_async(image_path: str):
    detector = RoboflowDetector()
    return detector.detect_page(image_path)

# 여러 이미지 병렬 처리
results = await asyncio.gather(*[
    detect_async(path) for path in image_paths
])
```

## 로컬 모델과 비교

| 특징 | Roboflow API | 로컬 YOLO |
|------|-------------|-----------|
| 설정 | 간단 (API 키만) | 복잡 (모델 파일 필요) |
| 속도 | 네트워크 지연 | 빠름 (로컬) |
| 비용 | API 호출당 과금 | 무료 (로컬) |
| 확장성 | 자동 스케일링 | 서버 리소스 제한 |
| 오프라인 | 불가능 | 가능 |

## 문제 해결

### API 키 오류

```
ValueError: Roboflow API 키가 필요합니다.
```

**해결**: `.env` 파일에 `ROBOFLOW_API_KEY` 설정

### 네트워크 오류

```
RuntimeError: Roboflow API 요청 실패: ...
```

**해결**: 
- 인터넷 연결 확인
- API 키 유효성 확인
- 타임아웃 증가 (기본 30초)

### 응답 파싱 오류

```
RuntimeError: Roboflow API 응답 파싱 실패: ...
```

**해결**: Roboflow 대시보드에서 모델 상태 확인

## 다음 단계

1. **모델 성능 평가**: 테스트 이미지로 정확도 확인
2. **파이프라인 통합**: PDF 파이프라인에 자동 감지 추가
3. **후처리**: 감지된 영역을 기반으로 이미지 크롭 및 저장
4. **로컬 모델 전환**: 필요시 로컬 YOLO 모델로 마이그레이션
