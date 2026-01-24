# YOLO Header 식별 구조 분석

## 현재 식별 구조

### 1. YOLO 감지 단계
```
456개 페이지 이미지
  ↓
페이지별 순차 처리 (Roboflow API)
  ↓
각 페이지에서 header 클래스 감지
  ↓
Confidence threshold: 0.15 (낮춤)
  ↓
감지 결과: 22개 header
```

### 2. Header → Lecture 변환
```
YOLO 감지 결과
  ↓
_classify_detections()
  - header 클래스 → lectures 리스트
  - lecture_id 순차 증가 (1, 2, 3, ...)
  ↓
convert_yolo_detections_to_units()
  - 각 header → lecture 변환
  - header 텍스트 추출 (OCR)
  - 같은 페이지의 units 수집
  ↓
최종: 22개 Lecture 생성
```

## 문제점 분석

### 디버깅 결과
- **감지된 header**: 22개
- **필요한 header**: 73개
- **감지율**: 30% (22/73)

### Confidence 분포
- **평균 confidence**: 0.246
- **0.25 미만**: 17개 (77%)
- **0.25 이상**: 5개 (23%)
- **0.5 이상**: 2개 (9%)

### 페이지별 분포
```
페이지   2: 2개 header
페이지   4: 1개 header
페이지   5: 1개 header
페이지   6: 1개 header
페이지   8: 1개 header
페이지  14: 1개 header
페이지  28: 2개 header
페이지  31: 1개 header
페이지  40: 1개 header
페이지 115: 1개 header
페이지 190: 1개 header
페이지 303: 1개 header
페이지 330: 1개 header
페이지 331: 1개 header
페이지 362: 1개 header
페이지 397: 1개 header
페이지 405: 1개 header
페이지 417: 1개 header
페이지 455: 2개 header
```

**문제**: 456페이지 중 19페이지만 header 감지됨

## 원인 분석

### 1. YOLO 모델 정확도 부족
- Header를 감지하지 못하는 페이지가 많음
- Confidence가 낮은 감지가 많음 (0.15-0.25)

### 2. Header가 없는 페이지
- 일부 페이지에는 실제로 header가 없을 수 있음
- 문제 페이지, 해설 페이지 등

### 3. Header 형식 다양성
- "1강 | 시의 표현과 형식" 형식
- "작품으로 이해하기 4" 형식
- 다양한 레이아웃으로 인해 감지 어려움

## 현재 구조의 한계

### YOLO만 사용하는 경우
```
YOLO 감지 → Header → Lecture
  ↓
22개만 감지 (73개 필요)
  ↓
51개 강의 누락
```

### OCR/파싱 사용하는 경우
```
OCR → 텍스트 추출 → 패턴 매칭 → Lecture
  ↓
73개 모두 감지 가능
  ↓
정확도는 낮을 수 있음
```

## 개선 방안

### 1. YOLO + OCR 결합 (권장)
```
YOLO로 감지된 header (22개)
  +
OCR/파싱으로 추가 header 찾기 (51개)
  ↓
73개 모두 감지
```

### 2. YOLO 모델 재학습
- 더 많은 header 데이터로 학습
- 다양한 header 형식 포함
- Confidence 향상

### 3. Confidence threshold 조정
- 현재: 0.15
- 더 낮추면: 더 많은 감지 (False positive 증가)
- 더 높이면: 더 적은 감지 (False negative 증가)

### 4. OCR/파싱 우선, YOLO 보조
```
OCR/파싱으로 모든 header 찾기
  ↓
YOLO로 검증 및 보완
  ↓
최종 73개 header 확정
```

## 권장 구조

### 하이브리드 방식
```
1. OCR/파싱으로 모든 header 후보 찾기 (73개)
2. YOLO로 검증 및 추가 header 찾기
3. 두 결과 병합하여 최종 결정
```

이렇게 하면:
- ✅ 73개 모두 감지 가능
- ✅ YOLO의 정확도 활용
- ✅ OCR/파싱의 완전성 활용
