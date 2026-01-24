# 이미지 크롭 기능 상태

## ✅ 구현 상태

이미지 크롭 기능이 **완전히 구현되어 있습니다!**

### 구현된 기능

1. **개념 이미지 크롭** (`_save_concept_images`)
   - 섹션 타입: `concept`
   - 파일명: `concept_p{page:02d}_{idx:02d}.png`
   - 저장 위치: `data/{subject}/{book_id}/concepts_images/`

2. **본문 이미지 크롭** (`_save_content_images`)
   - 섹션 타입: `content`, `passage`
   - 파일명: `content_p{page:02d}_{idx:02d}.png`
   - 저장 위치: `data/{subject}/{book_id}/content_images/`

3. **문제 이미지 크롭** (`_save_problem_images`)
   - 문제 타입: 모든 문제
   - 파일명: `problem_p{page:02d}_{problem_id}.png`
   - 저장 위치: `data/{subject}/{book_id}/problems_images/`

### 크롭 로직

```python
# 1. bbox 좌표 추출
left, top, right, bottom = bbox[:4]

# 2. 이미지 크기 제한 (안전성)
img_width, img_height = page_image.size
left = max(0, min(int(left), img_width - 1))
top = max(0, min(int(top), img_height - 1))
right = max(left + 1, min(int(right), img_width))
bottom = max(top + 1, min(int(bottom), img_height))

# 3. PIL Image.crop() 사용
cropped_image = page_image.crop((left, top, right, bottom))

# 4. PNG로 저장
cropped_image.save(output_path, 'PNG')
```

## ⚠️ 활성화 조건

이미지 크롭이 실행되려면 **3가지 조건**이 모두 충족되어야 합니다:

### 조건 1: OCR 추출기 사용 ✅
```python
if isinstance(self.extractor, OCRExtractor):
    # 이미지 저장 실행
```

**현재 상태:**
- `PdfplumberExtractor` 사용 중 → ❌ 이미지 저장 안 됨
- `OCRExtractor` 사용 시 → ✅ 이미지 저장 됨

### 조건 2: 섹션이 있어야 함 ⚠️
```python
sections = lecture_content.get('sections', [])
for section in sections:
    if section.get('type') == 'concept':
        # 개념 이미지 저장
```

**현재 상태:**
- 레거시 데이터: `sections: []` → ❌ 저장할 섹션 없음
- 교재별 데이터: 다른 형식 사용 → ❌ `sections` 필드 없음

### 조건 3: bbox 정보 필요 ⚠️
```python
bbox = section.get('bbox', [])
if not bbox or len(bbox) < 4:
    logger.warning("bbox가 유효하지 않음")
    continue
```

**현재 상태:**
- 섹션에 `bbox` 정보가 있어야 함
- OCR 데이터에서 bbox 추출 필요

## 🔧 이미지 크롭 활성화 방법

### 방법 1: OCR 추출기 사용 (추천)

**관리자 페이지에서 업로드 시:**
- 현재는 기본적으로 `PdfplumberExtractor` 사용
- OCR 추출기로 변경하려면 파이프라인 수정 필요

**또는 API 호출 시:**
```python
# use_ocr=True로 설정
pipeline = UnifiedPipeline(
    subject="literature",
    use_ocr=True,  # ← OCR 추출기 사용
    ...
)
```

### 방법 2: PdfplumberExtractor에도 이미지 저장 추가

`pipeline.py` 수정:
```python
# 현재 (line 265)
if isinstance(self.extractor, OCRExtractor):
    # 이미지 저장

# 수정 후
if isinstance(self.extractor, OCRExtractor) or isinstance(self.extractor, PdfplumberExtractor):
    # 이미지 저장 (PdfplumberExtractor도 지원)
```

**단, 문제점:**
- `PdfplumberExtractor`는 bbox 정보를 제공하지 않을 수 있음
- OCR 데이터가 없으면 페이지 이미지 변환이 필요

## 📊 현재 동작 흐름

### OCR 추출기 사용 시
1. PDF → OCR 추출 → 텍스트 + bbox 정보
2. 파싱 → 섹션 추출 (bbox 포함)
3. 섹션별 이미지 크롭 → 저장 ✅

### PdfplumberExtractor 사용 시
1. PDF → 텍스트 추출 (bbox 없음)
2. 파싱 → 섹션 추출
3. 이미지 저장 건너뜀 ❌

## 🧪 테스트 방법

### 1. OCR 추출기로 재파싱
```python
# pipeline.py에서 use_ocr=True로 설정 후 재파싱
pipeline = UnifiedPipeline(
    subject="literature",
    use_ocr=True,  # OCR 활성화
    ...
)
```

### 2. 결과 확인
```bash
# 이미지 폴더 확인
ls backend/data/literature/{book_id}/concepts_images/
ls backend/data/literature/{book_id}/content_images/
ls backend/data/literature/{book_id}/problems_images/
```

## 결론

**이미지 크롭 기능은 완전히 구현되어 있습니다!** ✅

하지만 현재는:
- ❌ `PdfplumberExtractor` 사용 중 → 이미지 저장 안 됨
- ❌ 섹션이 비어있음 → 저장할 이미지 없음

**활성화하려면:**
1. OCR 추출기 사용 (`use_ocr=True`)
2. 섹션이 채워져 있어야 함 (개선된 섹션 추출기 적용)
3. bbox 정보가 있어야 함 (OCR에서 제공)

**다음 단계:**
1. 관리자 페이지에서 재파싱 (OCR 추출기 사용)
2. 섹션이 채워진 후 이미지 자동 저장 확인
