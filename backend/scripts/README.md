# Backend Scripts

백엔드 개발 및 유지보수를 위한 스크립트 모음

## 스크립트 목록

### 1. 템플릿 초기화
**파일**: `init_templates.py`

기존 `config.json` 파일들을 템플릿으로 변환합니다.

```bash
python backend/scripts/init_templates.py
```

**기능**:
- `data/literature/config.json` → `data/templates/literature_ebs_수능특강_literature_2026.json`
- `data/math1/config.json` → `data/templates/math1_ebs_수능특강_math1_2026.json`
- `data/english/config.json` → `data/templates/english_ebs_수능특강_english_2026.json`

**효과**:
- 하이브리드 라우터가 자동으로 템플릿 매칭
- 기존 교재 처리 시간: 2-5초 (템플릿 사용)

---

### 2. PDF 파이프라인 테스트 (개발용)
**파일**: `pipeline/run_textbook_pipeline.py`

⚠️ **개발/테스트용 스크립트입니다. 실제 운영에서는 API를 사용하세요.**

```bash
python backend/scripts/pipeline/run_textbook_pipeline.py
```

**용도**:
- 파이프라인 로직 테스트
- 디버깅 및 성능 측정
- 로컬 개발 환경에서 빠른 테스트

**실제 운영**: `POST /api/books/upload` 사용

자세한 내용은 `pipeline/README.md` 참고

---

## API 사용 가이드

### PDF 업로드 (실제 운영)

```bash
# curl 예시
curl -X POST "http://localhost:8000/api/books/upload" \
  -F "file=@2026_수능특강_문학.pdf" \
  -F "title=2026 수능특강 문학" \
  -F "subject=KOREAN" \
  -F "year=2026"
```

**프론트엔드 예시**:
```typescript
const formData = new FormData();
formData.append('file', pdfFile);
formData.append('title', '2026 수능특강 문학');
formData.append('subject', 'KOREAN');

const response = await fetch('/api/books/upload', {
  method: 'POST',
  body: formData
});

const book = await response.json();
// book.parse_status: "PROCESSING"
// 백그라운드에서 자동으로 파싱 시작
```

### 파싱 상태 확인

```typescript
// 폴링으로 진행률 확인
const checkStatus = async (bookId: string) => {
  const response = await fetch(`/api/books/${bookId}/parse-status`);
  const status = await response.json();
  
  if (status.status === 'DONE') {
    console.log('파싱 완료!');
  } else if (status.status === 'PROCESSING') {
    console.log(`진행률: ${status.progress}%`);
    setTimeout(() => checkStatus(bookId), 2000); // 2초 후 재확인
  }
};
```

---

## 워크플로우

### 개발 단계
1. 스크립트로 빠르게 테스트 (`run_textbook_pipeline.py`)
2. 로그 확인 및 디버깅
3. 코드 수정 및 재테스트

### 운영 단계
1. 프론트엔드에서 PDF 업로드 (`POST /api/books/upload`)
2. API가 백그라운드에서 처리
3. 프론트엔드에서 진행률 폴링 (`GET /api/books/{book_id}/parse-status`)
4. 완료 후 자동으로 DB에 저장

---

## 참고

- 모든 스크립트는 `backend/` 디렉토리에서 실행해야 합니다
- API 엔드포인트는 `app/routers/books.py`에 정의되어 있습니다
- 실제 파이프라인 로직은 `app/infrastructure/pdf/pipeline.py`에 있습니다
