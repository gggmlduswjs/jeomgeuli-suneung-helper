# RAG 기반 추천 시스템 구현 완료

> **구현일**: 2026-01-27  
> **상태**: ✅ 완료

---

## 구현된 기능

### ✅ 백엔드 API

1. **`POST /api/v1/ai/recommend`** - RAG 기반 유사 콘텐츠 추천
   - 파일: `backend/app/routers/ai.py`
   - 기능: 쿼리 텍스트로 유사한 개념/문제/본문 검색
   - 파라미터:
     - `query`: 검색 쿼리
     - `unit_id`: 현재 단원 ID (선택)
     - `lesson_id`: 현재 강의 ID (선택)
     - `content_type`: "concept" | "problem" | "passage" | "all"
     - `top_k`: 추천 개수 (기본 5)
     - `min_score`: 최소 유사도 점수 (기본 0.3)

2. **`POST /api/v1/ai/recommend/initialize`** - RAG 시스템 초기화
   - 파일: `backend/app/routers/ai.py`
   - 기능: 특정 강의의 모든 단원을 Vector DB에 추가
   - 파라미터:
     - `lesson_id`: 초기화할 강의 ID

### ✅ 프론트엔드 컴포넌트

1. **`RAGRecommendationCard.tsx`** - 추천 카드 컴포넌트
   - 파일: `frontend/src/components/ai/RAGRecommendationCard.tsx`
   - 기능:
     - 접기/펼치기 UI
     - 로딩 상태 표시
     - 추천 결과 리스트 (타입별 색상 구분)
     - 유사도 점수 표시
     - 클릭 시 TTS 음성 안내
     - 추천 항목 선택 콜백

2. **API 서비스 추가**
   - 파일: `frontend/src/services/ai/index.ts`
   - 메서드:
     - `getRecommendations()` - 추천 요청
     - `initializeRAG()` - RAG 초기화

### ✅ UI 통합

1. **ConceptViewer** - 개념 뷰어에 추천 카드 추가
   - 파일: `frontend/src/components/unit/ConceptViewer.tsx`
   - 위치: 개념 내용 하단
   - 타입: `contentType="concept"`

2. **WorkViewer** - 본문 뷰어에 추천 카드 추가
   - 파일: `frontend/src/components/unit/WorkViewer.tsx`
   - 위치: 본문 내용 하단
   - 타입: `contentType="passage"`

3. **UnitViewer** - 문제 뷰어에 추천 카드 추가
   - 파일: `frontend/src/components/unit/UnitViewer.tsx`
   - 위치: 문제 내용 하단
   - 타입: `contentType="problem"`

---

## 사용 방법

### 1. RAG 시스템 초기화 (선택사항)

강의의 단원들을 Vector DB에 추가하려면:

```typescript
// 프론트엔드에서
await aiAPI.initializeRAG(lessonId);
```

또는 API 직접 호출:

```bash
POST /api/v1/ai/recommend/initialize
{
  "lesson_id": "lesson_001"
}
```

### 2. 추천 요청

```typescript
// 프론트엔드에서
const response = await aiAPI.getRecommendations({
  query: "이차방정식",
  lesson_id: "lesson_001",
  content_type: "all",
  top_k: 5,
  min_score: 0.3
});
```

### 3. UI에서 자동 사용

- 개념 단원 학습 시 → 유사 개념 추천 자동 표시
- 본문 단원 학습 시 → 유사 본문 추천 자동 표시
- 문제 단원 학습 시 → 유사 문제 추천 자동 표시

---

## 데이터 흐름

```
1. 사용자가 단원 학습 중
   ↓
2. UnitViewer/ConceptViewer/WorkViewer 렌더링
   ↓
3. RAGRecommendationCard 컴포넌트 마운트
   ↓
4. 사용자가 "유사 콘텐츠 추천" 카드 클릭 (펼치기)
   ↓
5. 현재 단원 텍스트로 추천 API 호출
   POST /api/v1/ai/recommend
   {
     query: "현재 단원 텍스트...",
     unit_id: "...",
     lesson_id: "...",
     content_type: "concept|problem|passage"
   }
   ↓
6. 백엔드: GenAIProcessor.rag_recommender.search()
   ↓
7. Vector DB에서 유사도 검색 (FAISS/Chroma)
   ↓
8. 추천 결과 반환
   ↓
9. 프론트엔드: 추천 리스트 표시
   ↓
10. 사용자가 추천 항목 클릭
    ↓
11. onSelect 콜백 실행 (네비게이션 또는 TTS)
```

---

## 주의사항

### Vector DB 초기화

- **자동 초기화 없음**: 현재는 수동으로 `/ai/recommend/initialize` 호출 필요
- **메모리 기반**: 서버 재시작 시 Vector DB 초기화됨
- **영구 저장**: 필요시 `vector_db_path` 지정하여 디스크에 저장 가능

### 성능

- **첫 검색 느림**: Vector DB가 비어있으면 빈 결과 반환
- **초기화 시간**: 강의당 수십~수백 개 단원 시 초기화에 시간 소요
- **메모리 사용**: FAISS는 메모리 기반, 대량 데이터 시 주의

### 에러 처리

- Vector DB가 없으면 빈 결과 반환 (에러 아님)
- RAG 초기화 실패 시 HTTP 500 에러
- 프론트엔드에서 에러 메시지 표시

---

## 다음 단계 (선택사항)

1. **자동 초기화**: 강의 상세 조회 시 자동으로 RAG 초기화
2. **네비게이션**: 추천 항목 클릭 시 해당 단원으로 이동
3. **Vector DB 영구 저장**: 디스크에 저장하여 서버 재시작 후에도 유지
4. **배치 초기화**: 모든 강의를 한 번에 초기화하는 스크립트
5. **캐싱**: 추천 결과 캐싱으로 성능 향상

---

## 테스트 방법

### 1. 백엔드 API 테스트

```bash
# RAG 초기화
curl -X POST http://localhost:8000/api/v1/ai/recommend/initialize \
  -H "Content-Type: application/json" \
  -d '{"lesson_id": "lesson_001"}'

# 추천 요청
curl -X POST http://localhost:8000/api/v1/ai/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "query": "이차방정식",
    "lesson_id": "lesson_001",
    "content_type": "all",
    "top_k": 5
  }'
```

### 2. 프론트엔드 테스트

1. 단원 학습 페이지 접속
2. "유사 콘텐츠 추천" 카드 클릭
3. 추천 결과 확인
4. 추천 항목 클릭하여 동작 확인

---

## 파일 변경 사항

### 백엔드
- ✅ `backend/app/routers/ai.py` - RAG 추천 API 추가

### 프론트엔드
- ✅ `frontend/src/services/ai/index.ts` - API 서비스 추가
- ✅ `frontend/src/components/ai/RAGRecommendationCard.tsx` - 새 컴포넌트
- ✅ `frontend/src/components/unit/ConceptViewer.tsx` - 추천 카드 통합
- ✅ `frontend/src/components/unit/WorkViewer.tsx` - 추천 카드 통합
- ✅ `frontend/src/components/unit/UnitViewer.tsx` - 추천 카드 통합

---

*구현 완료: 2026-01-27*
