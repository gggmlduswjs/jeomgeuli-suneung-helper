# 파싱 상태 연동 완료

## ✅ 수정 사항

### 1. 백엔드 API 수정

**파일:** `backend/app/routers/books.py`

**변경 전:**
```python
elif book.parse_status == ParseStatus.PROCESSING:
    progress = 50  # 하드코딩된 50%
```

**변경 후:**
```python
elif book.parse_status == ParseStatus.PROCESSING:
    progress = book.parse_progress if book.parse_progress is not None else 0

return BookParseStatusResponse(
    book_id=book.book_id,
    status=book.parse_status,
    progress=progress,
    current_page=book.current_page if book.current_page is not None else 0,
    total_pages=book.total_pages if book.total_pages is not None else 0,
)
```

**결과:**
- ✅ 실제 DB에 저장된 진행률 반환
- ✅ 현재 페이지 및 전체 페이지 수 반환
- ✅ 실시간 진행 상황 확인 가능

### 2. 프론트엔드 진행률 표시

**파일:** `frontend/src/pages/Admin.tsx`

**추가된 기능:**
1. **진행률 상태 관리**
   ```typescript
   const [parseProgress, setParseProgress] = useState<Record<string, { 
     progress: number; 
     current_page?: number; 
     total_pages?: number 
   }>>({});
   ```

2. **자동 폴링**
   - 파싱 중인 교재가 있으면 자동으로 10초마다 상태 확인
   - 진행률 자동 업데이트

3. **UI 표시**
   - 교재 카드에 진행률 표시: `38% (171/456페이지)`
   - Toast 메시지에 진행률 포함

## 📊 연동 흐름

### 1. 파싱 시작
```
관리자 페이지 → "재파싱" 버튼 클릭
  ↓
백엔드: book.parse_status = PROCESSING
  ↓
백그라운드 작업 시작
  ↓
진행률 업데이트: 5% → 10% → 20% → ...
```

### 2. 실시간 모니터링
```
프론트엔드: 10초마다 GET /api/v1/books/{id}/parse-status
  ↓
백엔드: DB에서 실제 진행률 조회
  ↓
응답: { progress: 38, current_page: 171, total_pages: 456 }
  ↓
프론트엔드: UI 업데이트
```

### 3. 완료
```
백엔드: book.parse_status = DONE, parse_progress = 100
  ↓
프론트엔드: 폴링 중지, 목록 새로고침
  ↓
UI: "완료" 상태 표시
```

## 🎯 사용자 경험

### 관리자 페이지에서 확인 가능한 정보

1. **교재 카드**
   - 상태: 파싱 중 / 완료 / 실패
   - 진행률: 38%
   - 페이지 정보: (171/456페이지)

2. **Toast 메시지**
   - "재파싱 진행 중... 38% (171/456페이지)"
   - 30초마다 업데이트 (너무 자주 표시하지 않음)

3. **자동 업데이트**
   - 페이지 새로고침 없이 자동으로 진행률 업데이트
   - 완료 시 자동으로 목록 새로고침

## 🔍 확인 방법

### 1. 관리자 페이지
- `http://localhost:3000/admin`
- 파싱 중인 교재에 진행률 표시 확인

### 2. API 직접 확인
```bash
curl http://localhost:8000/api/v1/books/{book_id}/parse-status
```

**응답 예시:**
```json
{
  "book_id": "book_korean_2026_수능특강_문학_296749",
  "status": "PROCESSING",
  "progress": 38,
  "current_page": 171,
  "total_pages": 456
}
```

### 3. 스크립트로 확인
```bash
cd backend
python scripts/check_parsing_status.py {book_id}
```

## ✅ 완료된 기능

- ✅ 백엔드: 실제 진행률 반환
- ✅ 프론트엔드: 진행률 상태 관리
- ✅ 자동 폴링: 파싱 중인 교재 자동 모니터링
- ✅ UI 표시: 진행률 및 페이지 정보 표시
- ✅ Toast 알림: 진행 상황 알림

## 🎉 결과

이제 관리자 페이지에서 **실시간으로 파싱 진행 상황을 확인**할 수 있습니다!

- 진행률이 실시간으로 업데이트됨
- 페이지 정보 표시
- 완료 시 자동 알림
