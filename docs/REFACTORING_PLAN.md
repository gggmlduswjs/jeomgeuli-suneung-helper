# Textbook Pipeline 리팩토링 계획

## 현재 문제점 요약

> ❌ "AI / OCR / 파싱 / 이미지 / 시각화"를 **한 파이프라인에서 동시에 완결**하려고 해서
> 👉 **디버깅 불가능 + 결과 불안정 상태**가 됨

**코드 품질 문제가 아니라 "책임 분리 실패" 문제**

---

## 우선순위 TOP 5 수정 완료 ✅

### ✅ 1. `_group_texts_by_line` threshold 수정
- **변경**: DPI 기반 동적 계산 (`int(self.dpi * 0.03)`)
- **효과**: 줄 그룹화 정확도 향상

### ✅ 2. START_PAGE 하드코딩 → config.json 이동
- **변경**: `START_PAGE = 8` → `self.config.get('start_content_page', 8)`
- **효과**: 과목별/판본별 유연성 확보

### ✅ 3. 이미지 추출 함수 책임 분리
- **변경**: `_extract_concept_content_and_problem_images()` → `_crop_concept_images()`, `_crop_content_images()`, `_crop_problem_images()`
- **효과**: 단일 책임 원칙 준수, 테스트 및 디버깅 용이

### ✅ 4. LLM 후처리 → 구조 파싱 이후로 이동
- **변경**: OCR → AI 후처리 → 구조 파싱 → 구조 파싱 → AI 후처리
- **효과**: bbox ↔ text 관계 안전성 확보

### ✅ 5. pdfplumber / OCR 완전 분리
- **변경**: `TextExtractor` 인터페이스, `PdfplumberExtractor`, `OCRExtractor` 클래스 생성
- **효과**: 좌표계 문제 해결, 각 추출기 독립적 관리

---

## 완료된 작업 요약

**현재 문제**:
```python
_extract_concept_content_and_problem_images()
```
이 함수가 하는 일:
- 개념 블록 탐지
- 본문 블록 탐지  
- 강의 단위 이미지
- 페이지 단위 이미지
- 문제 이미지
- 백업 방식까지 포함

**완료된 리팩토링**:
```python
# 블록 추출 (OCR 데이터 분석)
_extract_concept_blocks_from_ocr()      # 개념 블록만
_extract_content_blocks_from_ocr()      # 본문 블록만
_extract_problems()                     # 문제 블록만

# 이미지 크롭 (블록 정보 기반)
_crop_concept_images()                  # 개념 이미지만
_crop_content_images()                  # 본문 이미지만
_crop_problem_images()                  # 문제 이미지만
```

### ✅ 4. LLM 후처리 → 구조 파싱 이후로 이동

**완료된 변경**:
- 이전: OCR → AI 후처리 → 구조 파싱
- 현재: OCR → 구조 파싱 → JSON 완성 → (선택적) AI 후처리
- **효과**: bbox ↔ text 관계 안전성 확보

### ✅ 5. pdfplumber / OCR 완전 분리

**완료된 리팩토링**:
- `TextExtractor` 인터페이스 생성
- `PdfplumberExtractor` 클래스 (pdfplumber 전용)
- `OCRExtractor` 클래스 (OCR 전용)
- `TextbookPipeline`에서 선택적 사용
- **효과**: 좌표계 문제 해결, 각 추출기 독립적 관리

---

## 최종 리팩토링 구조 설계

### 목표: 4개 파일로 책임 분리

```
textbook_pipeline.py          # 메인 오케스트레이터
├── text_extractor.py        # OCR / pdfplumber 추출
├── structure_parser.py      # 규칙 기반 구조 파싱
└── image_cropper.py         # 이미지 크롭 및 시각화
```

### 파일별 책임

#### 1. `textbook_pipeline.py` (메인)
- 전체 파이프라인 오케스트레이션
- 설정 로드 및 전달
- 결과 통합 및 저장

#### 2. `text_extractor.py`
- OCR 처리 (`_ocr_pages_parallel`)
- pdfplumber 처리 (`_extract_with_pdfplumber`)
- 캐싱 관리
- **좌표계 통일** (OCR 좌표계로 통일)

#### 3. `structure_parser.py`
- 강의 추출 (`_extract_lectures`)
- 섹션 추출 (`_extract_sections`)
- 본문 추출 (`_extract_content_paragraphs`)
- 문제 추출 (`_extract_problems`)
- **LLM 후처리 제외** (구조 파싱만)

#### 4. `image_cropper.py`
- 개념 블록 추출 (`extract_concept_blocks`)
- 본문 블록 추출 (`extract_content_blocks`)
- 문제 블록 추출 (기존 `_extract_problems` 활용)
- 이미지 크롭 (`crop_*_images`)
- 시각화 (`_visualize_regions`)

---

## 단계별 마이그레이션 계획

### Phase 1: 즉시 적용 (완료 ✅)
- [x] `_group_texts_by_line` threshold 수정
- [x] START_PAGE → config 이동

### Phase 2: 함수 분리 (완료 ✅)
- [x] 이미지 추출 함수 책임 분리
- [x] LLM 후처리 순서 변경

### Phase 3: 파일 분리 (부분 완료 ✅)
- [x] `text_extractors.py` 생성 (pdfplumber / OCR 완전 분리)
- [ ] `structure_parser.py` 생성 (선택적)
- [ ] `image_cropper.py` 생성 (선택적)
- [x] `textbook_pipeline.py` 리팩토링 (추출기 통합)

### Phase 4: pdfplumber 분리 (완료 ✅)
- [x] `PdfplumberExtractor` 클래스 생성
- [x] `OCRExtractor` 클래스 생성
- [x] `TextExtractor` 인터페이스 정의
- [x] 좌표계 변환 완전 구현

---

## 예상 효과

### 디버깅 가능성
- 각 단계별 독립 테스트 가능
- 문제 발생 지점 명확히 추적

### 유지보수성
- 각 파일이 단일 책임
- 변경 영향 범위 최소화

### 확장성
- 새로운 추출 방식 추가 용이
- 과목별 파서 교체 가능

---

## 참고사항

- **점진적 마이그레이션**: 한 번에 다 바꾸지 말고 단계별로
- **기존 동작 보장**: 리팩토링 후에도 동일한 결과 생성
- **테스트 필수**: 각 단계별 검증 필요
