# 빠른 시작 가이드 (Quick Start Guide)

지금까지 논의한 모든 기능을 빠르게 구현하기 위한 단계별 가이드입니다.

---

## 🚀 1단계: 환경 설정 (5분)

### 백엔드 설정

```bash
# 1. 가상환경 생성 및 활성화
cd api
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 의존성 설치
pip install -r requirements.txt
pip install -r requirements-ai.txt

# 3. 환경 변수 설정 (.env 파일 생성)
echo "OPENAI_API_KEY=sk-your-key-here" > .env
echo "DATABASE_URL=sqlite:///./data/db.sqlite3" >> .env
```

### 프론트엔드 설정

```bash
cd apps/web
npm install
```

---

## 🗄️ 2단계: 데이터베이스 마이그레이션 (1분)

```bash
cd api
python scripts/migrate_db.py
```

**확인 사항**:
- `data/db.sqlite3` 파일 생성 확인
- Lesson 테이블에 새 필드 추가 확인

---

## 🔧 3단계: 서버 실행 (1분)

### 백엔드 실행
```bash
cd api
uvicorn app.main:app --reload
```

**확인**: http://localhost:8000 접속 → `{"message": "점글이 MVP 2.0 API"}` 표시

### 프론트엔드 실행
```bash
cd apps/web
npm run dev
```

**확인**: http://localhost:5173 접속 → 앱 화면 표시

---

## 📝 4단계: 테스트 데이터 준비

### 관리자 작업 (백엔드)

#### 4.1 강의 대본 업로드
```bash
# API 호출 예시
curl -X POST "http://localhost:8000/api/v1/lessons/{lesson_id}/upload-script" \
  -F "hwp_file=@data/lecture_scripts/수능특강_문학_2026/1강.hwp"
```

#### 4.2 PDF에서 Unit 생성
```bash
# API 호출 예시
curl -X POST "http://localhost:8000/api/v1/lessons/{lesson_id}/units/from-pdf" \
  -F "pdf_file=@data/pdfs/2026 수능특강_ 문학.pdf"
```

---

## 🎯 5단계: 기능 테스트

### 테스트 시나리오 1: AI 강의 선생님

1. **레슨 선택**
   - 프론트엔드: `/lesson/{lesson_id}` 접속
   - AI 요약 자동 표시 확인

2. **Unit 선택**
   - Unit 클릭
   - AI 설명 자동 표시 확인
   - TTS 재생 확인

### 테스트 시나리오 2: 실시간 AI 학습 도우미

1. **질문 입력**
   - Unit 페이지에서 "AI에게 질문하기" 입력
   - 또는 음성으로 질문

2. **AI 답변 확인**
   - AI 답변 표시 확인
   - TTS 재생 확인
   - 점자 출력 확인 (디바이스 연결 시)

---

## 📊 구현 상태 체크

### ✅ 완료된 기능
- [x] 레슨 분할 서비스
- [x] PDF 구조 파서
- [x] PDF to Units 변환기
- [x] AI 강의 선생님 서비스
- [x] AI API 라우터
- [x] 프론트엔드 컴포넌트 (ConceptViewer, WorkViewer)
- [x] AI 설명 통합 (Unit 페이지)
- [x] AI 질문 입력 컴포넌트
- [x] AI 요약 통합 (Lesson 페이지)

### ⏳ 테스트 필요
- [ ] 실제 HWP 파일 업로드 테스트
- [ ] 실제 PDF 파일 업로드 테스트
- [ ] AI API 실제 호출 테스트
- [ ] TTS 재생 테스트
- [ ] 점자 출력 테스트

---

## 🐛 문제 해결

### 문제 1: AI API 호출 실패
**원인**: API 키 미설정
**해결**: `.env` 파일에 `OPENAI_API_KEY` 또는 `GEMINI_API_KEY` 설정

### 문제 2: DB 마이그레이션 실패
**원인**: 기존 DB 스키마와 충돌
**해결**: `data/db.sqlite3` 삭제 후 재생성

### 문제 3: PDF 업로드 실패
**원인**: 파일 크기 제한 초과
**해결**: `api/app/core/config.py`에서 `MAX_UPLOAD_SIZE` 조정

---

## 📚 다음 단계

1. **실제 데이터로 테스트**
   - HWP 파일 업로드
   - PDF 파일 업로드
   - AI 설명 확인

2. **UI/UX 개선**
   - 스타일링
   - 로딩 상태 개선
   - 에러 처리

3. **접근성 완성**
   - 점자 출력 연동
   - TTS 최적화

---

*작성일: 2024년 12월*
