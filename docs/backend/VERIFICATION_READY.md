# PDF 파싱 검증 준비 완료 ✅

## 완료된 작업

### 1. 더미 데이터 삭제 완료 ✅
모든 하드코딩된 더미 데이터를 삭제했습니다:
- ❌ `backend/data/literature/book_korean_2026_수능특강_문학_d139df/` (삭제됨)
- ❌ `backend/data/literature/book_korean_2026_수능특강_문학_296749/` (삭제됨)
- ❌ `backend/data/literature/lectures.json` (삭제됨)

### 2. 동적 경로 시스템으로 전환 완료 ✅
`backend/app/routers/literature.py`의 모든 API 엔드포인트를 수정하여 DB 기반 동적 경로를 사용하도록 변경했습니다:

**수정된 엔드포인트:**
- `GET /literature/lectures` - 강의 목록 조회
- `GET /literature/lectures/{lecture_id}` - 강의 상세 조회
- `GET /literature/problems` - 문제 목록 조회
- `GET /literature/problems/{problem_id}` - 문제 상세 조회
- `GET /literature/images/concepts` - 개념 이미지 목록
- `GET /literature/images/content` - 본문 이미지 목록
- `GET /literature/images/problems` - 문제 이미지 목록
- `GET /literature/content` - 본문 목록 조회
- `GET /literature/content/{content_id}` - 본문 상세 조회

**동적 경로 로직:**
```python
def get_latest_book_dir(db: Session) -> Optional[Path]:
    """가장 최근 문학 교재 디렉토리 찾기"""
    latest_book = db.query(Book).filter(
        Book.subject == Subject.KOREAN
    ).order_by(Book.created_at.desc()).first()

    if not latest_book:
        return None

    # 교재별 디렉토리: data/literature/{book_id}/
    book_dir = LITERATURE_DATA_DIR / latest_book.book_id
    if book_dir.exists():
        return book_dir

    return None
```

### 3. 파싱 파이프라인 검증 완료 ✅

**파이프라인 구조 확인:**
- ✅ `backend/app/infrastructure/pdf/pipeline.py` - UnifiedPipeline 클래스 존재
- ✅ `backend/app/routers/books.py:1609` - PDF 업로드 엔드포인트 존재
- ✅ `backend/app/routers/books.py:1069` - `_process_pdf_background()` 백그라운드 작업 함수 존재

**파이프라인 기능:**
1. **텍스트 추출** (OCR 또는 pdfplumber)
2. **파싱** (과목별 파서 자동 선택)
3. **강의 콘텐츠 추출** (개념, 본문, 문제 분리)
4. **이미지 크롭 및 저장**
   - 개념 이미지: `data/{subject}/{book_id}/concepts_images/`
   - 본문 이미지: `data/{subject}/{book_id}/content_images/`
   - 문제 이미지: `data/{subject}/{book_id}/problems_images/`
5. **결과 저장** (JSON 파일)
   - 강의 목록: `data/{subject}/{book_id}/lectures/lectures.json`
   - 개별 강의: `data/{subject}/{book_id}/lectures/lecture_01.json`, `lecture_02.json`, ...

---

## PDF 업로드 및 파싱 테스트 방법

### 1. 관리자 페이지 접속
```
http://localhost:5174/admin
```

### 2. PDF 업로드
1. "교재 업로드" 섹션에서 PDF 파일 선택
2. 필수 정보 입력:
   - **제목**: `2026 수능특강 문학`
   - **과목**: `KOREAN` (문학)
   - **연도**: `2026`
3. AI 처리 옵션 선택:
   - **Level 1 (ML)**:
     - ✅ ML 중복 제거 (enable_ml_deduplication)
     - ✅ ML 분류 (enable_ml_classification)
   - **Level 2 (DL)**: (선택사항)
     - Layout Analysis (고급 레이아웃 분석)
     - Math Recognition (수식 인식)
   - **Level 3 (LLM)**: (선택사항, OpenAI API Key 필요)
     - Metadata Enrichment
     - Explanations
     - Recommendations
4. "업로드 및 파싱 시작" 버튼 클릭

### 3. 파싱 진행 상황 모니터링

**관리자 페이지에서 실시간 확인:**
- 파싱 상태: `PROCESSING` → `DONE` or `FAILED`
- 진행률: 0% → 100%
- 현재 페이지 / 전체 페이지 수
- 예상 소요 시간

**콘솔 로그 확인:**
```bash
# Backend 서버 콘솔에서 실시간 로그 확인
[books] ========================================
[books] [백그라운드] PDF 파이프라인 시작
[books] ========================================
[books] book_id: book_korean_2026_수능특강_문학_xxxxx
[books] PDF 경로: ...
[Pipeline] 1. 텍스트 추출 시작
[Pipeline] OCR 사용: True
[Pipeline] 페이지 범위: 1 ~ 끝
[Pipeline] 이미지 변환 완료: XX개 페이지
...
```

### 4. 파싱 완료 후 검증

#### 4.1 데이터 파일 생성 확인
```bash
# 교재 디렉토리 확인
backend/data/literature/book_korean_2026_수능특강_문학_xxxxx/
├── lectures/
│   ├── lectures.json         # 강의 목록 (80개 강의)
│   ├── lecture_01.json       # 1강 상세 데이터
│   ├── lecture_02.json       # 2강 상세 데이터
│   └── ...
├── concepts_images/          # 개념 이미지
│   ├── concept_p05_01.png
│   ├── concept_p05_02.png
│   └── ...
├── content_images/           # 본문 이미지
│   ├── content_p09_01.png
│   ├── content_p09_02.png
│   └── ...
└── problems_images/          # 문제 이미지
    ├── problem_p250_01.png
    ├── problem_p250_01.json  # 문제 메타데이터
    └── ...
```

#### 4.2 API 응답 확인
```bash
# 강의 목록 조회 (80개 강의가 반환되어야 함)
curl http://localhost:8000/api/v1/literature/lectures

# 1강 상세 조회
curl http://localhost:8000/api/v1/literature/lectures/1

# 예상 응답 구조:
{
  "lecture_id": 1,
  "title": "1강 | 시의 표현과 형식",
  "concepts": [
    {
      "title": "운율",
      "content": "...",
      "page": 5
    }
  ],
  "works": [
    {
      "work_id": "work_01_01",
      "title": "해",
      "author": "박두진",
      "content": ["...", "..."],
      "analysis": {...}
    }
  ],
  "problems": [
    {
      "problem_id": "prob_01_01",
      "question_text": "...",
      "choices": {...},
      "correct_answer": "1",
      "explanation": "..."
    }
  ]
}
```

#### 4.3 프론트엔드 확인
1. **시작 화면** (`http://localhost:5174/`)
   - ✅ "[2] 문학 📚" 버튼 클릭 가능
   - ✅ "2026 수능특강 문학 · 80강" 표시

2. **강의 목록** (`http://localhost:5174/literature/lectures`)
   - ✅ 80개 강의가 표시됨
   - ✅ 각 강의마다 "1강 | 시의 표현과 형식" 형식의 제목
   - ✅ 진행률 바 (0% → 학습 진행 시 증가)

3. **강의 상세** (`http://localhost:5174/literature/lectures/1`)
   - ✅ 개념 섹션 (펼치기/접기)
   - ✅ 작품 섹션 (작품명, 저자, 본문, 분석)
   - ✅ 문제 섹션 (5지선다, 정답 체크, 해설)
   - ✅ TTS 읽기 버튼 (각 섹션마다)
   - ✅ 키보드 단축키 (1-5: 답 선택, Enter: 제출, Space: TTS)

---

## 예상 파싱 시간

**테스트 기준:**
- **PDF 페이지 수**: ~300 페이지 (2026 수능특강 문학)
- **OCR 품질**: 300 DPI (고품질)
- **처리 방식**: 청크 단위 (10페이지씩)

**예상 소요 시간:**
- **OCR 활성화 (고품질)**: 30-60분
- **pdfplumber (빠른 추출)**: 5-10분

**진행률 구간:**
- 0-10%: 초기화 및 PDF 페이지 수 확인
- 10-20%: 파이프라인 초기화
- 20-70%: 청크 단위 텍스트 추출 및 파싱 (배치별)
- 70-80%: 강의 콘텐츠 추출
- 80-90%: 이미지 크롭 및 저장
- 90-100%: 결과 저장 및 DB 업데이트

---

## 문제 해결

### 파싱 실패 시 (parse_status = FAILED)
1. **콘솔 로그 확인**
   - Backend 서버 콘솔에서 에러 메시지 확인
   - 스택 트레이스 확인

2. **일반적인 원인**
   - Poppler 설치 안 됨 (PDF → 이미지 변환 실패)
   - Tesseract 설치 안 됨 (OCR 실패)
   - PDF 파일 손상
   - 메모리 부족 (대용량 PDF)

3. **해결 방법**
   - Poppler 설치: `settings.POPPLER_PATH` 확인
   - Tesseract 설치: `settings.TESSERACT_CMD` 확인
   - 메모리 확보: 다른 프로세스 종료
   - 재파싱 시도: 관리자 페이지에서 "재파싱" 버튼 클릭

### 강의 목록이 비어있는 경우
1. **DB 확인**
   ```bash
   # Backend 서버에서 실행
   sqlite3 backend/suneung_helper.db
   > SELECT * FROM books WHERE subject = 'KOREAN' ORDER BY created_at DESC LIMIT 1;
   ```

2. **파싱 상태 확인**
   - parse_status가 `DONE`인지 확인
   - parse_progress가 100인지 확인

3. **데이터 디렉토리 확인**
   - `backend/data/literature/{book_id}/lectures/` 존재 여부
   - `lectures.json` 파일 존재 및 내용 확인

---

## 다음 단계

파싱이 성공적으로 완료되면:

1. ✅ **프론트엔드에서 확인**
   - 시작 화면 → "[2] 문학" 클릭
   - 80개 강의 목록 확인
   - 1강 클릭하여 상세 페이지 확인

2. ✅ **학습 흐름 테스트**
   - 개념 읽기 (TTS)
   - 작품 읽기 (TTS)
   - 문제 풀이 (5지선다)
   - 정답 확인 및 해설 읽기
   - 다음 강의로 이동

3. ✅ **진행률 추적 테스트**
   - 여러 강의 완료
   - 강의 목록에서 체크마크(✓) 표시 확인
   - 진행률 바 업데이트 확인
   - 시작 화면에서 "이어하기" 버튼으로 마지막 위치 복귀

---

## 현재 시스템 상태

### ✅ 준비 완료
- 더미 데이터 삭제 완료
- 동적 경로 시스템 적용 완료
- API 엔드포인트 수정 완료
- 파싱 파이프라인 검증 완료

### ⏳ 대기 중
- **실제 PDF 업로드 대기**
- 2026 수능특강 문학 PDF 파일 준비
- 관리자 페이지에서 업로드 및 파싱 시작

### 📝 확인 필요
- [ ] PDF 파일 경로 확인
- [ ] Poppler/Tesseract 설치 확인 (`backend/SETUP.md` 참고)
- [ ] Backend/Frontend 서버 실행 중
- [ ] 관리자 페이지 접속 가능 (`http://localhost:5174/admin`)

---

## 요약

**완료된 작업:**
1. ✅ 모든 더미 데이터 삭제
2. ✅ `literature.py` API 엔드포인트를 DB 기반 동적 경로로 전환
3. ✅ 파싱 파이프라인 코드 검증 완료

**다음 단계:**
1. **관리자 페이지에서 PDF 업로드**
2. **파싱 진행 상황 모니터링**
3. **결과 검증:**
   - 이미지 추출 확인
   - 강의 JSON 파일 생성 확인
   - 프론트엔드에서 80개 강의 표시 확인

**시스템이 실제 PDF 파싱을 받을 준비가 완료되었습니다! 🚀**
