# ✅ PDF 업로드 준비 완료!

## 시스템 상태 확인 ✅

### 1. 서버 상태
- ✅ **Backend 서버**: 실행 중 (`http://localhost:8000`)
  - Health check: PASS
  - Database: Connected
- ✅ **Frontend 서버**: 실행 중 (`http://localhost:5174`)
  - Admin 페이지 접근 가능

### 2. 필수 도구 설치
- ✅ **Poppler**: `C:\poppler\Library\bin` (PDF → 이미지 변환)
- ✅ **Tesseract**: `C:\Program Files\Tesseract-OCR\tesseract.exe` (OCR)

### 3. 데이터베이스 상태
- ✅ **Books 테이블**: 비어있음 (0개)
- ✅ **이전 더미 데이터**: 완전 삭제됨

### 4. 파일 시스템 상태
- ✅ **literature 디렉토리**: 비어있음
- ✅ **uploads 디렉토리**: 준비됨

---

## PDF 업로드 가이드

### 1단계: 관리자 페이지 접속
```
브라우저에서 열기: http://localhost:5174/admin
```

### 2단계: PDF 파일 업로드
**"교재 업로드" 섹션에서:**

1. **파일 선택**
   - 파일: `2026_수능특강_문학.pdf` (또는 다른 문학 교재 PDF)

2. **기본 정보 입력**
   - **제목**: `2026 수능특강 문학`
   - **과목**: `KOREAN` (드롭다운에서 선택)
   - **연도**: `2026`

3. **AI 처리 옵션 선택** (권장 설정)

   **Level 1 - ML (기본, 빠름):**
   - ✅ **ML 중복 제거** (enable_ml_deduplication)
     - 중복된 블록 자동 제거
   - ✅ **ML 분류** (enable_ml_classification)
     - 블록 타입 자동 분류 (개념/본문/문제)

   **Level 2 - DL (고급, 느림):**
   - ✅ **Layout Analysis** (enable_layout_analysis)
     - YOLO 기반 레이아웃 분석 (더 정확한 구조 인식)
   - ❌ **Math Recognition** (enable_math_recognition)
     - 문학 교재에는 불필요 (수학 수식 인식용)

   **Level 3 - LLM (최고급, OpenAI API 필요):**
   - ❌ **Metadata Enrichment** (enable_llm_metadata)
     - OpenAI API Key 필요
   - ❌ **Explanations** (enable_llm_explanations)
     - OpenAI API Key 필요
   - ❌ **Recommendations** (enable_llm_recommendations)
     - OpenAI API Key 필요

4. **"업로드 및 파싱 시작" 버튼 클릭**

---

### 3단계: 파싱 진행 상황 모니터링

#### 관리자 페이지에서 실시간 확인
- **파싱 상태**: `PROCESSING` → `DONE`
- **진행률 바**: 0% → 100%
- **페이지 정보**: 현재 페이지 / 전체 페이지

#### Backend 콘솔 로그 확인
```bash
[books] ========================================
[books] [백그라운드] PDF 파이프라인 시작
[books] ========================================
[books] book_id: book_korean_2026_수능특강_문학_xxxxxx
[books] PDF 경로: data/uploads/book_korean_2026_수능특강_문학_xxxxxx.pdf
[Pipeline] 1. 텍스트 추출 시작
[Pipeline] OCR 사용: True
[Pipeline] 이미지 변환 완료: XXX개 페이지
[Pipeline] 2. 파서 선택 중...
[Pipeline] 3. 파싱 중...
[Pipeline] 4. 강의 콘텐츠 추출 중...
[Pipeline] 5. 개념 이미지 크롭 및 저장 중...
[Pipeline] 6. 본문 이미지 크롭 및 저장 중...
[Pipeline] 7. 문제 이미지 크롭 및 저장 중...
[books] ✅ 파싱 완료: DONE (100%)
```

#### 예상 소요 시간
- **OCR 고품질 모드** (300 DPI): 30-60분 (약 300페이지 기준)
- **pdfplumber 빠른 모드**: 5-10분 (OCR 비활성화 시)

---

### 4단계: 파싱 완료 후 검증

#### A. 데이터 파일 생성 확인
```bash
# Backend 서버 콘솔에서 실행
ls backend/data/literature/book_korean_2026_수능특강_문학_*/

# 예상 구조:
backend/data/literature/book_korean_2026_수능특강_문학_xxxxxx/
├── lectures/
│   ├── lectures.json           # 강의 목록 (80개)
│   ├── lecture_01.json         # 1강 상세
│   ├── lecture_02.json         # 2강 상세
│   └── ... (lecture_80.json까지)
├── concepts_images/            # 개념 이미지
│   ├── concept_p05_01.png
│   └── ...
├── content_images/             # 본문 이미지
│   ├── content_p09_01.png
│   └── ...
└── problems_images/            # 문제 이미지
    ├── problem_p250_01.png
    ├── problem_p250_01.json
    └── ...
```

#### B. API 응답 확인
```bash
# 1. 강의 목록 조회 (80개 강의 반환되어야 함)
curl http://localhost:8000/api/v1/literature/lectures

# 예상 응답:
[
  {"lecture_id": 1, "title": "1강 | 시의 표현과 형식"},
  {"lecture_id": 2, "title": "2강 | 화자와 청자"},
  ...
  {"lecture_id": 80, "title": "80강 | 종합 문제"}
]

# 2. 1강 상세 조회
curl http://localhost:8000/api/v1/literature/lectures/1

# 예상 응답:
{
  "lecture_id": 1,
  "title": "1강 | 시의 표현과 형식",
  "concepts": [
    {
      "title": "운율",
      "content": "시에서 규칙적으로 반복되는 소리의 흐름...",
      "page": 5
    }
  ],
  "works": [
    {
      "work_id": "work_01_01",
      "title": "해",
      "author": "박두진",
      "content": ["풀잎들이 가지를 벌려", "..."],
      "analysis": {
        "형식": "자유시, 7연으로 구성",
        "주제": "태양을 향한 끝없는 추구"
      }
    }
  ],
  "problems": [
    {
      "problem_id": "prob_01_01",
      "question_text": "윗글에 대한 설명으로 가장 적절한 것은?",
      "choices": {"1": "...", "2": "...", ...},
      "correct_answer": "1",
      "explanation": "..."
    }
  ]
}
```

#### C. 프론트엔드 확인
1. **시작 화면** (`http://localhost:5174/`)
   - ✅ "[2] 문학 📚" 버튼 활성화
   - ✅ "2026 수능특강 문학 · 80강" 표시

2. **강의 목록** (`http://localhost:5174/literature/lectures`)
   - ✅ 80개 강의가 표시됨
   - ✅ 각 강의 제목: "1강 | 시의 표현과 형식"
   - ✅ 진행률 바 (0%)

3. **강의 상세** (`http://localhost:5174/literature/lectures/1`)
   - ✅ 개념 섹션 (펼치기/접기 가능)
   - ✅ 작품 섹션 (작품명, 저자, 본문, 분석)
   - ✅ 문제 섹션 (5지선다, 정답 체크, 해설)
   - ✅ TTS 읽기 버튼 (모든 섹션)
   - ✅ 키보드 단축키 작동
     - 1-5: 답 선택
     - Enter: 정답 제출
     - Space: TTS 읽기
     - Esc: 뒤로가기

---

## 문제 해결 가이드

### 파싱 실패 시 (parse_status = FAILED)

#### 1. 콘솔 로그 확인
Backend 서버 콘솔에서 에러 메시지와 스택 트레이스를 확인하세요.

#### 2. 일반적인 문제와 해결 방법

**문제: PDF → 이미지 변환 실패**
```
Error: Unable to find pdftoppm
```
**해결**: Poppler가 설치되지 않았거나 경로가 잘못됨
- Poppler 설치 확인: `where pdftoppm`
- `backend/.env`에서 `POPPLER_PATH` 확인

**문제: OCR 실패**
```
Error: Tesseract not found
```
**해결**: Tesseract가 설치되지 않았거나 경로가 잘못됨
- Tesseract 설치 확인: `where tesseract`
- `backend/.env`에서 `TESSERACT_CMD` 확인

**문제: 메모리 부족**
```
MemoryError: Unable to allocate array
```
**해결**: 대용량 PDF 처리 시 메모리 부족
- 다른 프로그램 종료
- 배치 크기 줄이기 (코드 수정 필요)
- pdfplumber 모드 사용 (OCR 비활성화)

**문제: PDF 파일 손상**
```
Error: PDF file is damaged
```
**해결**: PDF 파일이 손상되었거나 암호화됨
- 다른 PDF 뷰어로 열기 시도
- PDF 복구 도구 사용
- 암호화된 경우 암호 해제 필요

#### 3. 재파싱 시도
관리자 페이지에서:
1. 문제가 된 교재 찾기
2. "재파싱" 버튼 클릭
3. AI 옵션 조정 (예: OCR 비활성화)
4. 다시 시도

---

## 현재 시스템 상태

### ✅ 모든 준비 완료
- ✅ Backend/Frontend 서버 실행 중
- ✅ DB 연결 정상
- ✅ Poppler/Tesseract 설치됨
- ✅ 더미 데이터 완전 삭제
- ✅ API 엔드포인트 동적 경로 적용
- ✅ 파싱 파이프라인 검증 완료

### ⏳ 다음 단계
1. **관리자 페이지 접속** → `http://localhost:5174/admin`
2. **PDF 업로드** → 기본 정보 입력 + AI 옵션 선택
3. **파싱 모니터링** → 진행률 확인 (30-60분 소요)
4. **결과 검증** → API + 프론트엔드 확인

---

## 테스트 체크리스트

파싱 완료 후 다음 항목들을 확인하세요:

### 데이터 생성 확인
- [ ] `backend/data/literature/{book_id}/lectures/` 디렉토리 생성됨
- [ ] `lectures.json` 파일에 80개 강의 목록 있음
- [ ] `lecture_01.json` ~ `lecture_80.json` 파일 생성됨
- [ ] `concepts_images/` 디렉토리에 이미지 파일 있음
- [ ] `content_images/` 디렉토리에 이미지 파일 있음
- [ ] `problems_images/` 디렉토리에 이미지 파일 있음

### API 확인
- [ ] `GET /api/v1/books` → 1개 교재 반환 (parse_status=DONE)
- [ ] `GET /api/v1/literature/lectures` → 80개 강의 반환
- [ ] `GET /api/v1/literature/lectures/1` → 1강 상세 반환 (개념/작품/문제)

### 프론트엔드 확인
- [ ] 시작 화면에서 "[2] 문학" 버튼 클릭 가능
- [ ] 강의 목록에 80개 강의 표시
- [ ] 1강 클릭 → 상세 페이지 표시
- [ ] 개념/작품/문제 섹션 모두 표시됨
- [ ] TTS 버튼 작동 (음성 읽기)
- [ ] 문제 풀이 가능 (5지선다, 정답 체크)
- [ ] 학습 진행률 추적 (완료 체크마크)

---

## 요약

**시스템이 완전히 준비되었습니다! 🚀**

- 서버: ✅ 실행 중
- 도구: ✅ Poppler + Tesseract 설치됨
- DB: ✅ 깨끗한 상태 (이전 데이터 삭제)
- 파일: ✅ literature 디렉토리 비어있음

**다음 단계:**
1. 관리자 페이지 접속 (`http://localhost:5174/admin`)
2. PDF 업로드 및 파싱 시작
3. 30-60분 대기 (진행률 모니터링)
4. 결과 검증 (API + 프론트엔드)

**파싱이 완료되면 시작 화면에서 "[2] 문학" 버튼을 눌러 80개 강의를 바로 확인할 수 있습니다!**
