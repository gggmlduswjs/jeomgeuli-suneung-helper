# JSON → DB 동기화 문제 해결 가이드

## 🔍 문제 상황

`lecture_01.json` 파일은 생성되었지만 프론트엔드 화면에 표시되지 않는 경우:

1. **JSON 파일은 존재**: `api/data/literature/lectures/lecture_01.json` ✅
2. **DB에 저장 안됨**: `Lesson` 테이블에 데이터 없음 ❌
3. **프론트엔드 조회 실패**: `GET /books/{book_id}/lessons` → 빈 배열 반환

## 🔄 데이터 흐름

```
PDF 파싱 완료
  ↓
lecture_01.json 생성 (JSON 파일)
  ↓
_create_curriculum_from_pipeline() 실행
  ├─ lecture_01.json 읽기
  ├─ LearningUnit 생성
  └─ _convert_learning_units_to_units() 실행
      ├─ Lesson 생성
      └─ Unit 생성
  ↓
DB에 저장 완료
  ↓
프론트엔드에서 조회 가능
```

## 🛠️ 해결 방법

### 방법 1: 재파싱 (권장)

**API 엔드포인트**: `POST /api/books/{book_id}/reparse`

```bash
# curl 예시
curl -X POST "http://localhost:8000/api/books/{book_id}/reparse"
```

또는 프론트엔드에서:
```typescript
await booksAPI.reparse(bookId);
```

**동작**:
1. PDF 파일 재파싱
2. JSON 파일 재생성
3. `_create_curriculum_from_pipeline()` 자동 실행
4. DB에 저장

### 방법 2: 수동 커리큘럼 생성 (JSON만 있는 경우)

JSON 파일은 있지만 DB에 저장되지 않은 경우, 수동으로 커리큘럼을 생성할 수 있습니다.

**스크립트 생성 필요**: `api/scripts/sync_json_to_db.py`

```python
# 예시 스크립트
from app.routers.books import _create_curriculum_from_pipeline
from app.db.session import SessionLocal
from app.db.models import Subject

book_id = "your_book_id"
subject = Subject.KOREAN
pipeline_subject = "literature"
title = "교재 제목"

db = SessionLocal()
try:
    curriculum_id = _create_curriculum_from_pipeline(
        book_id=book_id,
        subject_enum=subject,
        pipeline_subject=pipeline_subject,
        title=title,
        db=db
    )
    print(f"커리큘럼 생성 완료: {curriculum_id}")
finally:
    db.close()
```

### 방법 3: 직접 DB 확인

**DB 쿼리로 확인**:
```python
# Lesson이 있는지 확인
lessons = db.query(Lesson).filter(Lesson.book_id == book_id).all()
print(f"Lesson 개수: {len(lessons)}")

# LearningUnit이 있는지 확인
learning_units = db.query(LearningUnit).filter(
    LearningUnit.curriculum_id == curriculum_id
).all()
print(f"LearningUnit 개수: {len(learning_units)}")
```

## 🔍 문제 진단 체크리스트

1. **JSON 파일 존재 확인**
   ```bash
   ls api/data/literature/lectures/lecture_*.json
   ```

2. **파이프라인 로그 확인**
   - `_create_curriculum_from_pipeline` 실행 여부
   - `_convert_learning_units_to_units` 실행 여부
   - 에러 메시지 확인

3. **DB 데이터 확인**
   ```sql
   SELECT * FROM lessons WHERE book_id = 'your_book_id';
   SELECT * FROM units WHERE lesson_id IN (SELECT lesson_id FROM lessons WHERE book_id = 'your_book_id');
   ```

4. **커리큘럼 확인**
   ```sql
   SELECT * FROM curriculum WHERE book_id = 'your_book_id';
   ```

## 🚨 일반적인 원인

1. **파이프라인 실패 후 커리큘럼 생성 스킵**
   - `_process_pdf_background`에서 예외 발생
   - `_create_curriculum_from_pipeline` 실행 안됨

2. **JSON 파일 형식 오류**
   - `lecture_id` 누락
   - `sections` 배열이 비어있음
   - JSON 파싱 실패

3. **파일 경로 불일치**
   - `lectures_dir` 경로가 잘못됨
   - 파일명 패턴 불일치 (`lecture_01.json` vs `lecture_1.json`)

4. **DB 커밋 실패**
   - 트랜잭션 롤백
   - 제약 조건 위반

## 💡 빠른 해결책

**가장 간단한 방법**: 재파싱 API 호출

```typescript
// 프론트엔드에서
const handleReparse = async () => {
  try {
    await booksAPI.reparse(bookId);
    // 파싱 완료 대기 후 새로고침
    setTimeout(() => {
      loadLessons(bookId);
    }, 5000);
  } catch (error) {
    console.error('재파싱 실패:', error);
  }
};
```
