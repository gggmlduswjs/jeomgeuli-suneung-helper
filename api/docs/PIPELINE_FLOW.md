# PDF 크롭 파이프라인 전체 흐름

## 📋 전체 파이프라인 개요

```
강의 대본 (TXT/HWP)
    ↓
[1단계] 자동 태깅 → [b0], [b1], [b2]... 블록 생성
    ↓
[2단계] TTS 최적화 (선택)
    ↓
[3단계] script.json 저장
    ↓
[4단계] PDF 처리
    ├─ 목차 파싱 (TOCParser)
    ├─ PDF 블록 추출 (PDFPlumberExtractor)
    ├─ 블록 매칭 (3가지 방법)
    │   ├─ ① 목차 기반 페이지 매핑
    │   ├─ ② 텍스트 매칭 (OCR)
    │   └─ ③ 키워드 매칭 (폴백)
    └─ PDF 영역 캡처 (PDFRegionCapturer)
    ↓
[5단계] blocks.json 저장
```

---

## 🔄 상세 단계별 설명

### **1단계: 강의 대본 태깅**

**입력**: 강의 대본 텍스트 파일
**출력**: 구조화된 섹션 리스트

```python
# 예시: 강의 대본
"""
[b0]
강의 시작 및 오리엔테이션
국어 영역 최선의 선택 최서희입니다...

[b1]
2강 개요 및 핵심 포인트
2강에서는 소설 두 작품을 만나볼 텐데...
"""

# → 파싱 결과
{
  "script_sections": [
    {
      "section_id": "b0",
      "title": "강의 시작 및 오리엔테이션",
      "content": "국어 영역 최선의 선택...",
      "keywords": ["국어", "수능특강", "문학"]
    },
    {
      "section_id": "b1",
      "title": "2강 개요 및 핵심 포인트",
      "content": "2강에서는 소설...",
      "keywords": ["소설", "개념 학습", "내용축"]
    }
  ]
}
```

**담당 모듈**: `AutoTagger` 또는 `_parse_tagged_script()`

---

### **2단계: PDF 처리 시작**

#### **2-1. 목차 파싱** (TOCParser)

**목적**: PDF에서 목차를 찾아 페이지 번호 매핑 생성

```python
# 목차에서 추출
{
  "parts": [
    {
      "part_name": "1부 교과서 개념 학습",
      "lessons": [
        {"lesson_number": 1, "title": "시의 표현과 형식", "page": 9},
        {"lesson_number": 2, "title": "시의 내용", "page": 12},  # ← 2강!
        ...
      ]
    }
  ]
}

# 페이지 매핑 생성
toc_page_map = {
  "2강": 12,
  "강2": 12,
  "2": 12
}
```

**담당 모듈**: `TOCParser.extract_toc_from_pdf()`

---

#### **2-2. PDF 블록 추출** (PDFPlumberExtractor)

**목적**: PDF의 모든 텍스트 블록을 좌표와 함께 추출

```python
# 추출 결과 예시
[
  {
    "type": "text",
    "page": 12,
    "bbox": [0, 100, 583.93, 200],
    "content": "2강 | 시의 내용\n매화 옛 등걸에..."
  },
  {
    "type": "text",
    "page": 12,
    "bbox": [0, 200, 583.93, 300],
    "content": "녹양이 천만사인들..."
  },
  ...
]
```

**담당 모듈**: `PDFPlumberExtractor.extract_blocks()`

**특징**:
- 줄 단위로 블록 추출
- 각 블록에 bbox 좌표 포함
- 문단 단위로 그룹화 가능 (`_group_pdf_blocks_by_paragraph()`)

---

#### **2-3. 블록 매칭** (3단계 전략)

**목적**: 강의 대본 섹션(b0, b1...)과 PDF 블록을 매칭

##### **① 목차 기반 페이지 타겟팅**

```python
# 섹션: "2강 개요 및 핵심 포인트"
lesson_match = re.search(r'(\d+)\s*강', section_title)  # → 2
target_page = toc_page_map.get("2강")  # → 12
```

**장점**: 정확한 페이지로 바로 이동

---

##### **② 텍스트 매칭** (OCR 기반) ⭐ **최신 추가**

**목적**: 섹션 제목/키워드로 정확한 영역 찾기

```python
# PDFRegionDetector 사용
detected = region_detector.detect_by_text_matching(
    pdf_path=pdf_path,
    page=12,  # 목차에서 찾은 페이지
    target_text="2강 개요",  # 섹션 제목
    context_lines=3
)

# 결과
{
  "bbox": [0, 50, 583, 150],  # 이미지 좌표계
  "matched_text": "2강 개요",
  "confidence": 0.8
}
```

**담당 모듈**: `PDFRegionDetector.detect_by_text_matching()`

**특징**:
- OCR로 텍스트 위치 정확히 찾기
- 주변 줄(context_lines) 포함하여 영역 계산
- 이미지 좌표계로 반환 (PDF 좌표계 변환 필요)

---

##### **③ 키워드 매칭** (폴백)

**목적**: 텍스트 매칭 실패 시 키워드 유사도로 매칭

```python
# 점수 계산
score = 0
for keyword in ["소설", "개념 학습", "내용축"]:
    if keyword in pdf_block_content:
        score += 2

# 텍스트 유사도
common_words = set(section_content.split()) & set(block_content.split())
score += len(common_words) * 0.1

# 목차 페이지 매칭 시 보너스
if target_page and pdf_block.page == target_page:
    score += 5.0
```

**담당 모듈**: `_match_script_to_pdf()`

**특징**:
- 여러 블록을 문단 단위로 그룹화
- 큰 bbox 생성 (여러 줄 포함)
- x0=x1=0 문제 자동 수정

---

#### **2-4. PDF 영역 캡처** (PDFRegionCapturer)

**목적**: 매칭된 bbox로 실제 이미지 크롭

```python
# 좌표 변환 과정
PDF 좌표계 (하단 기준) → 이미지 좌표계 (상단 기준)

# Y축 반전
pdf_y0 → img_y1
pdf_y1 → img_y0

# 크롭 실행
cropped_image = page_image.crop((x0, y0, x1, y1))
cropped_image.save("b1.png")
```

**담당 모듈**: `PDFRegionCapturer.capture_region()`

**특징**:
- Y축 좌표 자동 반전
- bbox 유효성 검사 및 자동 수정
- Poppler 자동 감지

---

## 🎯 매칭 전략 우선순위

```
1순위: 텍스트 매칭 (OCR)
   ↓ (실패 시)
2순위: 목차 기반 페이지 + 키워드 매칭
   ↓ (실패 시)
3순위: 키워드 매칭만
```

---

## 📊 최종 출력

### **script.json**
```json
{
  "lesson_id": "korean_lit_02",
  "script_sections": [
    {
      "section_id": "b0",
      "title": "강의 시작 및 오리엔테이션",
      "content": "..."
    }
  ]
}
```

### **blocks.json**
```json
{
  "blocks": [
    {
      "block_id": "b0",
      "title": "강의 시작 및 오리엔테이션",
      "image_path": "pdfs/captures/korean/lesson_02/b0.png",
      "pdf_reference": {
        "page": 8,
        "bbox": [0, 699.75, 583.93, 709.75]
      },
      "match_method": "text_detection"  // 또는 "keyword_matching"
    }
  ]
}
```

---

## 🔧 개선 사항 (최근 추가)

1. ✅ **Y축 좌표 변환 수정**: PDF 좌표계 ↔ 이미지 좌표계
2. ✅ **bbox 자동 수정**: x0=x1=0 문제 해결
3. ✅ **목차 기반 매칭**: 정확한 페이지 타겟팅
4. ✅ **텍스트 매칭**: OCR로 정확한 영역 찾기
5. ✅ **문단 단위 그룹화**: 여러 블록 합쳐서 큰 영역 생성

---

## 🚀 다음 개선 가능 사항

1. **문제 번호 기반 자동 감지**: `1.`, `2번` 패턴으로 문제 영역 자동 계산
2. **레이아웃 AI 통합**: LayoutLM 등으로 구조 분석
3. **YOLO 통합**: 문제 영역 직접 학습
