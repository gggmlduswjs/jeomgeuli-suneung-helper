# PDF 파이프라인 스크립트

## 개요

이 스크립트는 **개발 및 테스트용**입니다. 실제 운영 환경에서는 API 엔드포인트를 사용하세요.

## 실제 운영 환경 (API 사용)

### PDF 업로드 및 자동 파싱

```bash
# API 엔드포인트 사용
POST /api/books/upload

# 요청 형식 (multipart/form-data)
- file: PDF 파일
- title: 교재 제목
- subject: 과목 (KOREAN, MATH, ENGLISH)
- year: 연도 (선택)
```

**예시 (curl)**:
```bash
curl -X POST "http://localhost:8000/api/books/upload" \
  -F "file=@2026_수능특강_문학.pdf" \
  -F "title=2026 수능특강 문학" \
  -F "subject=KOREAN" \
  -F "year=2026"
```

**프론트엔드 사용**:
```typescript
const formData = new FormData();
formData.append('file', pdfFile);
formData.append('title', '2026 수능특강 문학');
formData.append('subject', 'KOREAN');
formData.append('year', '2026');

const response = await fetch('/api/books/upload', {
  method: 'POST',
  body: formData
});
```

### 파싱 상태 확인

```bash
GET /api/books/{book_id}/parse-status
```

**응답**:
```json
{
  "book_id": "book_literature_2026수능특강문학_2026",
  "status": "PROCESSING",
  "progress": 50
}
```

### 재파싱

```bash
POST /api/books/{book_id}/reparse
```

## 개발/테스트용 스크립트

### 사용 시나리오

1. **로컬 개발 환경에서 빠른 테스트**
   - API 서버 없이 파이프라인만 테스트
   - 디버깅 및 로그 확인

2. **성능 측정**
   - 처리 시간 측정
   - 메모리 사용량 확인

3. **파이프라인 로직 검증**
   - 새로운 파서 로직 테스트
   - 템플릿 매칭 테스트

### 실행 방법

```bash
python backend/scripts/pipeline/run_textbook_pipeline.py
```

### 스크립트 vs API 차이점

| 항목 | 스크립트 | API |
|-----|---------|-----|
| **용도** | 개발/테스트 | 실제 운영 |
| **DB 저장** | ❌ JSON만 저장 | ✅ DB + JSON 저장 |
| **백그라운드 처리** | ❌ 동기 처리 | ✅ 비동기 처리 |
| **진행률 추적** | ❌ | ✅ 실시간 진행률 |
| **에러 처리** | 콘솔 출력 | ✅ DB 상태 업데이트 |
| **프론트엔드 연동** | ❌ | ✅ 자동 연동 |

## API 엔드포인트 목록

### 교재 관리

- `POST /api/books/upload` - PDF 업로드 및 자동 파싱
- `GET /api/books` - 교재 목록 조회
- `GET /api/books/{book_id}` - 교재 상세
- `GET /api/books/{book_id}/parse-status` - 파싱 상태 확인
- `POST /api/books/{book_id}/reparse` - 재파싱
- `POST /api/books/{book_id}/sync-from-json` - JSON → DB 동기화

### 커리큘럼 관리

- `POST /api/curriculum/generate` - 커리큘럼 자동 생성
- `GET /api/curriculum` - 커리큘럼 목록
- `GET /api/curriculum/{curriculum_id}` - 커리큘럼 상세

## 권장 워크플로우

### 개발 단계
1. 스크립트로 빠르게 테스트
2. 로그 확인 및 디버깅
3. 코드 수정 및 재테스트

### 운영 단계
1. 프론트엔드에서 PDF 업로드
2. API가 백그라운드에서 처리
3. 프론트엔드에서 진행률 폴링
4. 완료 후 자동으로 DB에 저장

## 참고

- 실제 운영에서는 항상 API를 사용하세요
- 스크립트는 개발/디버깅용으로만 사용
- API는 `books.py`의 `_process_pdf_background` 함수에서 동일한 `UnifiedPipeline` 사용
