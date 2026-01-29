# 추가 리팩토링 제안서

**작성일**: 2026년 1월 26일  
**버전**: 1.0.0

---

## 발견된 추가 리팩토링 필요 사항

### 🔴 High Priority

#### 1. books.py 파일 분리 (2479줄)

**문제점**:
- `backend/app/routers/books.py`가 2479줄로 매우 큼
- 단일 책임 원칙 위반 (라우터, 비즈니스 로직, 데이터 변환 모두 포함)
- 유지보수 및 테스트 어려움

**제안 구조**:
```
backend/app/
├── routers/
│   └── books.py          # 라우터만 (약 200줄)
├── services/
│   ├── book_service.py   # 교재 CRUD 서비스
│   ├── curriculum_service.py  # 커리큘럼 생성 서비스
│   └── book_data_converter.py  # JSON → DB 변환 서비스
└── utils/
    └── book_helpers.py    # 헬퍼 함수들
```

**작업 내용**:
1. `_create_curriculum_from_pipeline` → `curriculum_service.py`로 이동
2. `_process_pdf_background` → `book_service.py`로 이동
3. JSON → DB 변환 로직 → `book_data_converter.py`로 이동
4. 헬퍼 함수들 → `book_helpers.py`로 이동
5. 라우터는 서비스 호출만 담당

**예상 작업 시간**: 6-8시간

---

#### 2. templates.py 파일 분리 (2376줄)

**문제점**:
- `backend/app/routers/templates.py`가 2376줄로 매우 큼
- 템플릿 생성, 편집, 테스트, TOC 파싱 등 여러 책임 포함

**제안 구조**:
```
backend/app/
├── routers/
│   └── templates.py      # 라우터만 (약 150줄)
├── services/
│   ├── template_service.py      # 템플릿 CRUD 서비스
│   ├── template_generator.py    # 템플릿 생성 서비스
│   └── toc_parser_service.py    # TOC 파싱 서비스
└── utils/
    └── template_helpers.py      # 템플릿 헬퍼 함수들
```

**작업 내용**:
1. `_generate_template_from_toc_via_openai` → `template_generator.py`
2. `_extract_lecture_lines_from_toc_directly` → `toc_parser_service.py`
3. `_extract_images_from_bbox_regions` → `template_helpers.py`
4. 템플릿 CRUD 로직 → `template_service.py`

**예상 작업 시간**: 4-6시간

---

### 🟡 Medium Priority

#### 3. print 문을 logger로 변경

**문제점**:
- `books.py`에 300개 이상의 `print()` 문 사용
- `book_conversion.py`에도 많은 `print()` 문
- 로깅 레벨 제어 불가, 프로덕션 환경에서 문제

**발견된 위치**:
- `backend/app/routers/books.py`: 약 300개
- `backend/app/services/book_conversion.py`: 약 20개

**제안**:
```python
# 변경 전
print(f"[books] 로드된 강의: {len(lectures)}개")

# 변경 후
logger.info(f"[books] 로드된 강의: {len(lectures)}개")
```

**작업 내용**:
1. 모든 `print()` 문을 `logger.info()`, `logger.warning()`, `logger.error()`로 변경
2. 로깅 레벨에 맞게 분류 (info, warning, error, debug)

**예상 작업 시간**: 2-3시간

---

#### 4. 중복 함수 제거 ✅ (완료)

**문제점**:
- `_map_section_type_to_unit_type` 함수가 `books.py`와 `book_conversion.py`에 중복
- `book_conversion.py`에 이미 `map_section_type_to_unit_type` 존재

**해결**:
- ✅ `books.py`의 중복 함수 제거 완료
- ✅ `book_conversion.py`의 함수를 import하여 사용

**상태**: ✅ 완료

---

### 🟢 Low Priority

#### 5. 타입 힌트 보완

**문제점**:
- 일부 함수에 타입 힌트 누락
- `dict = None` 같은 모호한 타입 힌트

**제안**:
```python
# 변경 전
def _process_pdf_background(book_id: str, pdf_path: Path, subject: str, ai_options: dict = None):

# 변경 후
from typing import Optional, Dict, Any
def _process_pdf_background(
    book_id: str, 
    pdf_path: Path, 
    subject: str, 
    ai_options: Optional[Dict[str, Any]] = None
):
```

**예상 작업 시간**: 1-2시간

---

#### 6. 에러 처리 일관성 개선

**문제점**:
- 일부 함수는 `HTTPException` 사용
- 일부 함수는 일반 `Exception` 사용
- 에러 메시지 형식 불일치

**제안**:
- 커스텀 예외 클래스 사용 (`app.core.exceptions`)
- 에러 메시지 형식 통일

**예상 작업 시간**: 2-3시간

---

## 우선순위별 작업 계획

### Phase 1: 긴급 (1주)
1. books.py 파일 분리
2. print 문을 logger로 변경

### Phase 2: 중요 (3일)
3. templates.py 파일 분리
4. ✅ 중복 함수 제거 (완료)

### Phase 3: 개선 (여유 있을 때)
5. 타입 힌트 보완
6. 에러 처리 일관성 개선

---

## 예상 효과

### 코드 품질 개선
- ✅ 큰 파일 분리로 가독성 향상
- ✅ 단일 책임 원칙 준수
- ✅ 테스트 용이성 향상

### 개발 효율성 향상
- ✅ 파일 크기 감소로 탐색 시간 단축
- ✅ 모듈화로 병렬 개발 가능
- ✅ 버그 수정 시 영향 범위 축소

---

**추가 리팩토링 제안서 작성 완료**
