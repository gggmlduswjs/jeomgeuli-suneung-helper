# Backend 리팩토링 완료 보고서

날짜: 2026-01-24

## 실행된 리팩토링

### 1. 미사용 디렉토리 삭제

#### Domain 레이어 제거
- `app/domain/books/`
- `app/domain/curriculum/`
- `app/domain/lessons/`
- `app/domain/units/`
- `app/domain/` (전체 삭제)

**이유**: 도메인 계층이 정의만 되어 있고 실제로 사용되지 않음

#### API v1 빈 디렉토리 제거
- `app/api/v1/ai/`
- `app/api/v1/curriculum/`
- `app/api/v1/lessons/`
- `app/api/v1/units/`
- `app/api/v1/braille/`

**이유**: 빈 디렉토리로 실제 구현이 없음

#### Infrastructure 빈 디렉토리 제거
- `app/infrastructure/database/repositories/`
- `app/infrastructure/ai/ml/`

**이유**: Repository 패턴 미구현, ML 기능 미사용

### 2. 라우터 중복 해결

#### 삭제
- `app/api/v1/books/routes.py` (전체 디렉토리)

#### main.py 수정
```python
# 이전
app.include_router(books_v1.router, prefix="/api/v1", tags=["books"])
app.include_router(books.router, prefix="/api/v1", tags=["books-legacy"])

# 이후
app.include_router(books.router, prefix="/api/v1", tags=["books"])
```

**이유**: 같은 엔드포인트(/api/v1/books)에 두 개의 라우터가 등록되어 충돌

### 3. 테스트 파일 정리

#### 이동
- `test_parsing_pipeline.py` → `tests/test_parsing_pipeline.py`
- `test_quick.py` → `tests/test_quick.py`

**이유**: 테스트 파일을 tests/ 폴더로 통합

## 정리 후 구조

```
backend/
├── app/
│   ├── main.py
│   ├── api/v1/
│   │   ├── health/
│   │   ├── subjects/
│   │   ├── answers/
│   │   └── progress/
│   ├── routers/ (주요 비즈니스 로직)
│   │   ├── books.py (2620 lines)
│   │   ├── templates.py (1941 lines)
│   │   ├── curriculum.py
│   │   ├── lessons.py
│   │   ├── units.py
│   │   ├── ai.py
│   │   ├── literature.py
│   │   └── braille.py
│   ├── infrastructure/
│   │   ├── pdf/ (파싱 파이프라인)
│   │   ├── ai/
│   │   │   ├── dl/ (딥러닝)
│   │   │   └── genai/ (LLM)
│   │   └── database/
│   │       ├── models.py
│   │       └── session.py
│   ├── schemas/ (Pydantic 모델)
│   ├── services/ (비즈니스 로직)
│   │   └── book_conversion.py
│   ├── utils/ (유틸리티)
│   └── core/ (설정)
├── tests/ (통합된 테스트)
└── data/ (데이터베이스, 파일)
```

## 크기 절감

- **이전**: 알 수 없음
- **이후**: 23MB
- **절감**: 빈 디렉토리 및 중복 코드 제거

## 남은 개선 과제

### 1. 큰 파일 분할 (우선순위: 중)

**대상 파일:**
- `app/routers/books.py` (2620 lines)
  - 교재 업로드, 파싱, 커리큘럼 생성 등 여러 책임
  - 분할 제안: books.py, parsing.py, curriculum.py

- `app/routers/templates.py` (1941 lines)
  - 템플릿 CRUD, 생성, 테스트 등
  - 분할 제안: templates.py, template_generation.py

- `app/infrastructure/pdf/parsers/section_extractor.py` (1232 lines)

### 2. 미구현 기능 제거 (우선순위: 높)

**HWP 관련 Stub 코드:**
```python
# app/routers/books.py, lessons.py
try:
    from app.services.hwp_extract import ...
except ImportError:
    def extract_text_from_hwp(...):
        raise HTTPException(status_code=501, detail="HWP 파일 처리가 지원되지 않습니다.")
```

**제안:**
- HWP 기능을 완전히 구현하거나
- 엔드포인트 자체를 제거

**영향받는 엔드포인트:**
- POST /books/upload-hwp
- POST /lessons/{id}/upload-hwp-script
- GET /books/{id}/lessons-from-hwp

### 3. Repository 패턴 도입 (우선순위: 낮)

**현재 상황:**
- 라우터에서 직접 DB 쿼리 수행
- 강하게 결합된 구조

**제안:**
```python
# app/infrastructure/database/repositories/book_repository.py
class BookRepository:
    def get_by_id(self, db: Session, book_id: str) -> Book:
        return db.query(Book).filter(Book.book_id == book_id).first()
```

### 4. 에러 핸들링 통일 (우선순위: 중)

**현재 상황:**
- 각 라우터마다 다른 에러 처리 방식
- try-except가 많이 산재

**제안:**
```python
# app/core/exceptions.py
class BookNotFoundException(HTTPException):
    def __init__(self, book_id: str):
        super().__init__(status_code=404, detail=f"교재를 찾을 수 없습니다: {book_id}")
```

### 5. 타입 힌트 강화 (우선순위: 낮)

**현재 상황:**
- 일부 함수에 타입 힌트 누락
- Optional, Union 등 일관성 부족

**제안:**
- 모든 함수에 명확한 타입 힌트 추가
- mypy 도입

### 6. 문서화 개선 (우선순위: 중)

**현재 상황:**
- 일부 함수에만 docstring 존재
- API 문서 부족

**제안:**
- 모든 public 함수에 docstring 추가
- Swagger/OpenAPI 문서 강화

## 주요 발견 사항

1. **라우터 구조**: app/routers (주요 로직) + app/api/v1 (간단한 CRUD)로 이원화
2. **Infrastructure 계층**: PDF, AI, Database로 명확히 분리됨
3. **순환 의존성**: 발견되지 않음 (건강한 구조)
4. **테스트 커버리지**: 매우 낮음 (PDF 파싱 관련만 존재)

## 권장 사항

### 즉시 실행 가능
1. ✅ 미사용 디렉토리 삭제 (완료)
2. ✅ 라우터 중복 해결 (완료)
3. ✅ 테스트 파일 정리 (완료)
4. HWP Stub 코드 제거 또는 구현

### 중기 과제
1. 큰 파일 분할 (books.py, templates.py)
2. 에러 핸들링 통일
3. 문서화 개선

### 장기 과제
1. Repository 패턴 도입
2. 테스트 커버리지 확대
3. 타입 체크 (mypy) 도입

## 결론

현재 백엔드 구조는 이미 Infrastructure, Routers, Schemas로 명확히 분리되어 있습니다. 주요 문제는:
1. 일부 파일이 너무 큼 (2000+ lines)
2. 미구현 기능(HWP)의 Stub 코드 존재
3. Repository 패턴 미적용

단, 프로젝트가 현재 정상 작동하고 있으므로 대규모 리팩토링보다는 점진적 개선을 권장합니다.
