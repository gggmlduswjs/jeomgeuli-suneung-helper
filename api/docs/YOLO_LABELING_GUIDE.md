# YOLO 모델 라벨링 가이드

YOLO 모델 학습을 위한 클래스 정의 및 라벨링 규칙입니다.

## 클래스 정의 (6개)

### 1. header (페이지 최상단 제목)
- **설명**: 페이지 최상단에 있는 강의 제목
- **예시**: "1강 | 시의 표현과 형식", "2강 | 산문의 이해"
- **매핑**: → **Lesson 제목**
- **라벨링 규칙**:
  - 페이지 상단 20% 이내에 위치
  - 큰 폰트 크기
  - "N강" 형식 포함
  - 단원/유형/번호/코너 이름 포함

### 2. section (중간 제목)
- **설명**: 개념 섹션의 제목 (예: "1 시적 표현", "2 운율")
- **예시**: "1 시적 표현", "2 운율", "3 상징"
- **매핑**: → **Unit: concept (subtype: title)** - 개념 제목
- **라벨링 규칙**:
  - 숫자로 시작하는 중간 제목
  - 개념을 소개하는 제목
  - 본문보다 작지만 일반 텍스트보다 큰 폰트

### 3. concept_box (개념 내용)
- **설명**: 굵은 테두리가 있는 큰 박스 안의 개념 설명
- **예시**: 개념 설명 박스, 풀이 전략 박스
- **매핑**: → **Unit: concept (subtype: content)** - 개념 내용
- **라벨링 규칙**:
  - 굵은 테두리 (2px 이상)
  - 박스 형태의 영역
  - 개념 설명, 풀이 전략, 핵심 정리 등 포함

### 4. sidebar (세부 개념)
- **설명**: 왼쪽 세로로 배치된 보조 설명
- **예시**: 단어 뜻, 주석, 참고 정보
- **매핑**: → **Unit: concept_detail** - 세부 개념
- **라벨링 규칙**:
  - 페이지 왼쪽 또는 오른쪽에 세로로 배치
  - 작은 폰트
  - 보조 정보, 주석, 단어 뜻 등

### 5. passage (본문)
- **설명**: 작품 전문 전체 (시, 산문 등)
- **예시**: 시 전문, 산문 전문
- **매핑**: → **Unit: passage** - 본문
- **라벨링 규칙**:
  - 작품 전문이 포함된 영역
  - 여러 줄로 구성
  - 시적 표현, 운율 등 포함 가능

### 6. question (문제)
- **설명**: 문제 전체 (질문 + 선지 포함)
- **예시**: 문제 번호, 질문, ① ② ③ ④ ⑤ 선지
- **매핑**: → **Unit: question** - 문제
- **라벨링 규칙**:
  - 문제 번호 포함 (예: "01", "02")
  - 질문 문장
  - 선택지 (①, ②, ③, ④, ⑤) 포함

## Lesson 구성 규칙

### Lesson 생성
- **Lesson 제목**: `header` 목록으로 구성
- 각 `header`가 하나의 `Lesson`이 됩니다

### Unit 구성 (페이지 단위)
각 Lesson 안의 Unit은 **페이지 단위**로 구성됩니다:

1. **같은 페이지의 모든 영역 수집**
   - `section` (개념 제목)
   - `concept_box` (개념 내용)
   - `sidebar` (세부 개념)
   - `passage` (본문)
   - `question` (문제)

2. **정렬 순서**
   - **우선순위**: 개념 → 본문 → 문제
     - 개념: `section`, `concept_box`, `sidebar` (priority: 1)
     - 본문: `passage` (priority: 2)
     - 문제: `question` (priority: 3)
   - **y좌표**: 같은 우선순위 내에서는 위에서 아래로 (y1 기준)

3. **최종 순서**
   ```
   개념 (section, concept_box, sidebar) 
     ↓
   본문 (passage)
     ↓
   문제 (question)
   ```

## 라벨링 예시

### 페이지 구조 예시

```
┌─────────────────────────────────────┐
│ 1강 | 시의 표현과 형식              │ ← header
├─────────────────────────────────────┤
│                                     │
│ ┌─────────────────────────────┐    │
│ │ 1 시적 표현                 │    │ ← section (개념 제목)
│ │                             │    │
│ │ 시적 표현은...              │    │ ← concept_box (개념 내용)
│ └─────────────────────────────┘    │
│                                     │
│ ┌─────────────────────────────┐    │
│ │ 해야 솟아라                 │    │ ← passage (본문)
│ │ 해야 솟아라                 │    │
│ │ ...                         │    │
│ │ - 박두진, 「해」            │    │
│ └─────────────────────────────┘    │
│                                     │
│ 01 다음 시의 표현 기법은?           │ ← question (문제)
│ ① ...                               │
│ ② ...                               │
│                                     │
└─────────────────────────────────────┘
```

### Unit 순서 예시

같은 페이지에 다음 영역들이 감지된 경우:

1. `section` (y1=200) - "1 시적 표현"
2. `concept_box` (y1=300) - 개념 설명 박스
3. `passage` (y1=500) - 작품 전문
4. `question` (y1=1000) - 문제

**최종 Unit 순서:**
1. Unit (concept, title): "1 시적 표현" (y1=200)
2. Unit (concept, content): 개념 설명 (y1=300)
3. Unit (passage): 본문 (y1=500)
4. Unit (question): 문제 (y1=1000)

## 데이터셋 준비

### 디렉토리 구조
```
dataset/
├── train/
│   ├── images/
│   └── labels/
├── val/
│   ├── images/
│   └── labels/
└── test/
    ├── images/
    └── labels/
```

### YOLO 형식 라벨 파일
각 이미지에 대해 `.txt` 파일 생성:

```
class_id center_x center_y width height
```

예시:
```
0 0.5 0.1 0.8 0.05    # header
1 0.5 0.2 0.6 0.03    # section
4 0.5 0.3 0.7 0.15    # concept_box
2 0.5 0.5 0.8 0.25    # passage
3 0.5 0.8 0.9 0.15   # question
```

### data.yaml
```yaml
path: /path/to/dataset
train: train/images
val: val/images
test: test/images

nc: 6
names:
  0: header
  1: section
  2: passage
  3: question
  4: concept_box
  5: sidebar
```

## 참고

- **라벨링 도구**: LabelImg, Roboflow
- **검증 스크립트**: `api/scripts/yolo/check_dataset.py`
- **학습 스크립트**: `api/scripts/yolo/train_yolo.py`
- **사용 가이드**: `api/docs/YOLO_USAGE_GUIDE.md`
