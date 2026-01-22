# PDF 업로드 전체 로직 흐름

## 📋 개요

PDF 업로드 시 자동으로 파싱하여 학습 데이터를 생성하는 전체 프로세스입니다.

## 🔄 전체 플로우

```
[프론트엔드]                    [백엔드 API]                    [백그라운드 작업]
     │                              │                                │
     ├─ 1. PDF 파일 선택            │                                │
     │   (BookUpload.tsx)           │                                │
     │                              │                                │
     ├─ 2. booksAPI.upload() 호출  │                                │
     │   POST /books/upload         │                                │
     │                              │                                │
     │                              ├─ 3. 파일 검증 및 저장          │
     │                              │   (uploads/{book_id}.pdf)      │
     │                              │                                │
     │                              ├─ 4. DB에 Book 생성             │
     │                              │   parse_status = PROCESSING    │
     │                              │                                │
     │                              ├─ 5. 즉시 응답 반환             │
     │                              │   (201 Created)                │
     │                              │                                │
     │                              └─ 6. 백그라운드 작업 등록        │
     │                                 (BackgroundTasks)              │
     │                                                               │
     │                                                               ├─ 7. _process_pdf_background() 실행
     │                                                               │
     │                                                               ├─ 8. TextbookPipeline 초기화
     │                                                               │   - UnifiedPipeline 사용 시도
     │                                                               │   - 실패 시 레거시 방식
     │                                                               │
     │                                                               ├─ 9. pipeline.process_pdf() 실행
     │                                                               │
     │                                                               │   [UnifiedPipeline 사용 시]
     │                                                               │   ├─ 9-1. 텍스트 추출
     │                                                               │   │   (pdfplumber 또는 OCR)
     │                                                               │   │
     │                                                               │   ├─ 9-2. 파싱
     │                                                               │   │   (강의, 문제 추출)
     │                                                               │   │
     │                                                               │   ├─ 9-3. 강의 콘텐츠 추출
     │                                                               │   │   (섹션, 본문)
     │                                                               │   │
     │                                                               │   ├─ 9-4. JSON 저장
     │                                                               │   │   (lectures.json, lecture_XX.json)
     │                                                               │   │
     │                                                               │   └─ 9-5. 결과 반환
     │                                                               │
     │                                                               │   [레거시 방식 사용 시]
     │                                                               │   ├─ 9-1. YOLO 감지 (선택적)
     │                                                               │   ├─ 9-2. 텍스트 추출
     │                                                               │   ├─ 9-3. 강의 추출
     │                                                               │   ├─ 9-4. 강의 콘텐츠 추출
     │                                                               │   ├─ 9-5. 문제 추출
     │                                                               │   ├─ 9-6. 이미지 크롭
     │                                                               │   └─ 9-7. JSON 저장
     │                                                               │
     │                                                               ├─ 10. _create_curriculum_from_pipeline()
     │                                                               │   - lecture_XX.json 읽기
     │                                                               │   - LearningUnit 생성
     │                                                               │   - Lesson + Unit 변환
     │                                                               │
     │                                                               └─ 11. DB 업데이트
     │                                                                   parse_status = DONE
     │
     ├─ 12. 파싱 상태 폴링           │                                │
     │   (getParseStatus)           │                                │
     │   PROCESSING → DONE           │                                │
     │                              │                                │
     └─ 13. 결과 표시                │                                │
        (Book.tsx)                  │                                │
```

## 📝 상세 단계 설명

### 1. 프론트엔드: PDF 업로드

**파일**: `apps/web/src/components/textbook/BookUpload.tsx`

```typescript
// 사용자가 PDF 파일 선택
const book = await booksAPI.upload(
  file,           // PDF 파일
  title,          // 교재 제목
  subject,        // 과목 (KOREAN, MATH, ENGLISH)
  year,           // 연도
  aiOptions       // AI 처리 옵션
);
```

**API 호출**: `POST /api/books/upload`

### 2. 백엔드: 파일 저장 및 DB 생성

**파일**: `api/app/routers/books.py` - `upload_book()`

```python
# 1. 파일 검증
if not file.filename.endswith('.pdf'):
    raise HTTPException(400, "PDF 파일만 업로드 가능")

# 2. 파일 저장
file_path = settings.UPLOADS_DIR / f"{book_id}.pdf"
with open(file_path, "wb") as f:
    f.write(await file.read())

# 3. DB에 Book 생성
book = Book(
    book_id=book_id,
    title=title,
    subject=Subject(subject),
    parse_status=ParseStatus.PROCESSING,  # ⚠️ 파싱 중 상태
    file_path=str(file_path),
)
db.add(book)
db.commit()

# 4. 즉시 응답 반환 (파싱은 백그라운드에서)
return BookResponse(...)
```

### 3. 백그라운드 작업: PDF 파싱

**파일**: `api/app/routers/books.py` - `_process_pdf_background()`

```python
# 1. TextbookPipeline 초기화
pipeline = TextbookPipeline(
    subject=pipeline_subject,
    dpi=150,
    use_parallel=True,
    use_pdfplumber=True,
    use_yolo=ai_options.get('enable_yolo_detection', False),
    ...
)

# 2. 파이프라인 실행
result = pipeline.process_pdf(pdf_path)
```

### 4. 파이프라인 실행 (UnifiedPipeline 우선)

**파일**: `api/app/services/textbook_pipeline.py` - `process_pdf()`

#### 4-1. UnifiedPipeline 사용 시 (새로운 방식)

```python
if self.use_unified_pipeline and self.unified_pipeline:
    result = self.unified_pipeline.process(pdf_path)
    # 반환: {lectures, problems, lecture_contents}
```

**UnifiedPipeline 내부**:
1. **텍스트 추출**: `extractor.extract(pdf_path)`
   - pdfplumber 또는 OCR 사용
2. **파싱**: `parser.parse(ocr_data)`
   - 강의 목록 추출
   - 문제 목록 추출
3. **강의 콘텐츠 추출**: `lecture_extractor.extract()`
   - 각 강의의 섹션 추출
   - 본문 추출
4. **JSON 저장**: `result_saver.save()`
   - `lectures.json`: 강의 목록
   - `lecture_XX.json`: 각 강의 상세 내용

#### 4-2. 레거시 방식 (UnifiedPipeline 실패 시)

```python
# 1. YOLO 감지 (선택적)
if self.use_yolo:
    yolo_detection_results = self._run_yolo_detection(...)

# 2. 텍스트 추출
all_ocr_data = self._ocr_with_cache(page_images, pdf_path)

# 3. 강의 추출
lectures = self._extract_lectures(all_ocr_data)

# 4. 강의 콘텐츠 추출
lecture_contents = self._extract_lecture_contents(all_ocr_data, lectures)

# 5. 문제 추출
problems = self._extract_problems(all_ocr_data)

# 6. 이미지 크롭
self._extract_concept_content_and_problem_images(...)

# 7. JSON 저장
self._save_results(lectures, lecture_contents, problems)
```

### 5. 커리큘럼 생성

**파일**: `api/app/routers/books.py` - `_create_curriculum_from_pipeline()`

```python
# 1. lecture_XX.json 파일 읽기
lecture_files = sorted(lectures_dir.glob("lecture_*.json"))

# 2. 각 강의를 LearningUnit으로 변환
for lecture_file in lecture_files:
    lecture_data = json.load(lecture_file)
    sections = lecture_data.get("sections", [])
    
    # 각 섹션을 LearningUnit으로 변환
    for section in sections:
        learning_unit = LearningUnit(
            unit_id=f"lu_{uuid.uuid4().hex[:12]}",
            curriculum_id=curriculum_id,
            section_type=section.get("type", "concept"),
            title=section.get("title", ""),
            content=content_text,
            ...
        )
        db.add(learning_unit)

# 3. LearningUnit → Lesson + Unit 변환
_convert_learning_units_to_units(curriculum_id, book_id, db)
```

### 6. DB 업데이트

```python
# 파싱 완료 상태로 업데이트
book.parse_status = ParseStatus.DONE
db.commit()
```

### 7. 프론트엔드: 상태 확인

**파일**: `apps/web/src/pages/Book.tsx`

```typescript
// 파싱 상태 폴링
const interval = setInterval(async () => {
  const status = await booksAPI.getParseStatus(bookId);
  if (status.status === 'DONE') {
    clearInterval(interval);
    await loadBook(bookId);  // 교재 정보 새로고침
    await loadLessons(bookId);  // 강의 목록 새로고침
  }
}, 2000);  // 2초마다 확인
```

## 📂 생성되는 파일들

### JSON 파일
- `api/data/{subject}/lectures/lectures.json`: 강의 목록
- `api/data/{subject}/lectures/lecture_01.json`: 1강 상세 내용
- `api/data/{subject}/lectures/lecture_02.json`: 2강 상세 내용
- ...

### 이미지 파일 (레거시 방식만)
- `api/data/{subject}/concepts_images/concept_p08_01.png`: 개념 이미지
- `api/data/{subject}/content_images/content_p09_01.png`: 본문 이미지
- `api/data/{subject}/problems_images/problem_p10_01.png`: 문제 이미지
- `api/data/{subject}/pages/page_001.png`: 페이지 이미지

### DB 레코드
- `Book`: 교재 정보
- `Curriculum`: 커리큘럼 정보
- `Lesson`: 강의 정보 (lecture_XX.json → Lesson)
- `Unit`: 학습 단위 (sections → Unit)

## 🔍 현재 상태 (UnifiedPipeline 전환 중)

### ✅ UnifiedPipeline 사용 시
- 텍스트 추출: `processing/extractors/`
- 파싱: `processing/parsers/`
- 강의 콘텐츠 추출: `processing/lecture_contents_extractor.py`
- JSON 저장: `processing/result_saver.py`

### ⚠️ 레거시 방식 (UnifiedPipeline 실패 시)
- 모든 로직이 `textbook_pipeline.py`에 있음
- YOLO 통합, 이미지 크롭 등 추가 기능 포함

## 🎯 다음 단계

1. **UnifiedPipeline 완전 전환**: 모든 기능을 `processing/` 모듈로 이동
2. **이미지 추출 통합**: `processing/image_extractors/` 모듈 추가
3. **YOLO 통합**: `processing/detectors/` 모듈 추가
4. **레거시 코드 제거**: `textbook_pipeline.py` 삭제
