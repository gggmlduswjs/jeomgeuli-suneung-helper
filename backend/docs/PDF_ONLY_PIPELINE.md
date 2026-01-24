# PDF 중심 파이프라인 (PDF Only Pipeline)

## 🎯 핵심 아이디어

**강의 대본 없이 PDF만으로 블록 자동 생성**

```
PDF 파일
  ↓
[1단계] 목차 파싱 → 강/섹션 구조 파악
  ↓
[2단계] PDF 구조 분석
  ├─ 문제 번호 감지 (1., 2번, ①② 등)
  ├─ 제목 감지 (2강 |, >>> 고전 시가 등)
  └─ 레이아웃 분석
  ↓
[3단계] 블록 자동 생성
  ├─ 목차 기반: 각 강/섹션 → 블록
  ├─ 문제 기반: 문제 번호 → 블록
  └─ 제목 기반: 큰 제목 → 블록
  ↓
[4단계] PDF 영역 캡처
  ↓
[5단계] blocks.json 저장
```

---

## 📊 비교: 현재 방식 vs PDF 중심 방식

### 현재 방식 (강의 대본 의존)

```
강의 대본 → 태깅 → 매칭 → 크롭
```

**문제점:**
- ❌ 강의 대본 필수
- ❌ 복잡한 매칭 과정
- ❌ 매칭 실패 가능성
- ❌ 오버헤드 큼

### PDF 중심 방식 (제안)

```
PDF → 구조 분석 → 블록 생성 → 크롭
```

**장점:**
- ✅ PDF만 있으면 됨
- ✅ 직접적이고 간단
- ✅ PDF 구조를 정확히 반영
- ✅ 빠르고 효율적

---

## 🔄 상세 프로세스

### **1단계: 목차 파싱**

```python
# 목차에서 추출
{
  "parts": [
    {
      "lessons": [
        {"lesson_number": 2, "title": "시의 내용", "page": 12}
      ]
    }
  ]
}

# → 블록 생성
{
  "block_id": "b0",
  "title": "2강 | 시의 내용",
  "page": 12,
  "bbox": None  # 페이지 전체 또는 자동 계산
}
```

---

### **2단계: PDF 구조 분석**

#### **2-1. 문제 번호 감지**

```python
# OCR로 문제 번호 찾기
question_regions = detector.detect_question_regions(
    pdf_path=pdf_path,
    page=12
)

# 결과
[
  {
    "question_number": 1,
    "bbox": [0, 100, 583, 300],
    "page": 12
  },
  {
    "question_number": 2,
    "bbox": [0, 300, 583, 500],
    "page": 12
  }
]
```

#### **2-2. 제목 감지**

```python
# 제목 패턴
- "2강 | 시의 내용"
- ">>> 고전 시가"
- "1부 교과서 개념 학습"

# → 블록 생성
{
  "block_id": "b1",
  "title": "2강 | 시의 내용",
  "page": 12,
  "bbox": [제목 위치]
}
```

---

### **3단계: 블록 자동 생성**

**전략 조합:**

1. **목차 기반** (우선)
   - 각 강/섹션을 블록으로
   - 정확한 페이지 번호

2. **문제 번호 기반**
   - OCR로 문제 영역 자동 감지
   - 정확한 bbox 계산

3. **제목 기반** (보완)
   - 큰 제목을 블록으로
   - 구조 파악

---

### **4단계: PDF 영역 캡처**

```python
# bbox가 있으면 그대로 사용
# bbox가 없으면 페이지 전체 또는 자동 계산

for block in blocks:
    if block['bbox']:
        # 정확한 영역 크롭
        crop(block['bbox'])
    else:
        # 페이지 전체 또는 다음 블록까지
        crop_page_section(block['page'])
```

---

## 💡 구현 예시

### **사용법**

```python
from app.services.pdf_only_pipeline import PDFOnlyPipeline

pipeline = PDFOnlyPipeline(use_ocr=True)

result = pipeline.process_pdf(
    pdf_path=Path("2026 수능특강 문학.pdf"),
    subject="korean",
    lesson_number=2  # None이면 목차에서 자동 추출
)

# 결과
{
  "blocks_json": {
    "blocks": [
      {
        "block_id": "b0",
        "title": "2강 | 시의 내용",
        "page": 12,
        "image_path": "pdfs/captures/korean/lesson_02/b0.png"
      }
    ]
  },
  "captured_images": {...}
}
```

---

## 🎯 장점 요약

1. **단순함**: PDF만 있으면 자동 생성
2. **정확성**: PDF 구조를 직접 반영
3. **효율성**: 불필요한 매칭 과정 제거
4. **확장성**: 문제 번호, 제목 등 규칙 추가 용이

---

## 🔧 다음 개선 사항

1. **문제 영역 자동 계산**: 문제 번호 → 다음 문제까지 자동 영역 계산
2. **지문/보기 구분**: 레이아웃 분석으로 지문과 보기 분리
3. **다중 전략 조합**: 목차 + 문제 번호 + 제목을 조합하여 더 정확한 블록 생성
