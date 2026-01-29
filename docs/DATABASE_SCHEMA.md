# 데이터베이스 스키마 문서

## 개요

본 프로젝트는 SQLAlchemy ORM을 사용하여 데이터베이스를 관리합니다. 개발 환경에서는 SQLite를 사용하며, 프로덕션 환경에서는 PostgreSQL을 사용할 수 있습니다.

## 데이터베이스 설정

- **ORM**: SQLAlchemy
- **개발 환경**: SQLite (`data/db.sqlite3`)
- **프로덕션 환경**: PostgreSQL (환경 변수 `DATABASE_URL`로 설정)
- **세션 관리**: `SessionLocal` (의존성 주입 패턴)

## 테이블 구조

### 1. books (교재)

교재 정보를 저장하는 테이블입니다.

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| `book_id` | String | PRIMARY KEY | 교재 고유 ID |
| `title` | String | NOT NULL | 교재 제목 |
| `subject` | Enum(Subject) | NOT NULL | 과목 (KOREAN, ENGLISH, MATH) |
| `year` | Integer | NULL | 출판 연도 |
| `parse_status` | Enum(ParseStatus) | DEFAULT PENDING | 파싱 상태 (PENDING, PROCESSING, DONE, FAILED) |
| `parse_progress` | Integer | DEFAULT 0 | 파싱 진행률 (0-100) |
| `current_page` | Integer | DEFAULT 0 | 현재 처리 중인 페이지 |
| `total_pages` | Integer | DEFAULT 0 | 전체 페이지 수 |
| `file_path` | String | NULL | PDF 파일 저장 경로 |
| `created_at` | DateTime | DEFAULT utcnow | 생성 일시 |
| `updated_at` | DateTime | DEFAULT utcnow | 수정 일시 |

**관계**:
- `lessons` (1:N) - 하나의 교재는 여러 강의를 가짐

**인덱스**: 없음

---

### 2. lessons (강의/단원)

교재 내의 강의(레슨) 정보를 저장하는 테이블입니다.

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| `lesson_id` | String | PRIMARY KEY | 강의 고유 ID |
| `book_id` | String | FOREIGN KEY, NOT NULL | 교재 ID (books.book_id 참조, CASCADE DELETE) |
| `index` | Integer | NOT NULL | 강의 순서 (1부터 시작) |
| `title` | String | NOT NULL | 강의 제목 |
| `lecture_script_text` | Text | NULL | 강의 대본 텍스트 (레슨 단위로 분할) |
| `estimated_time` | Integer | NULL | 예상 소요 시간 (분) |
| `key_points` | Text | NULL | 핵심 포인트 (JSON 배열: ["핵심1", "핵심2"]) |
| `has_question` | Boolean | DEFAULT FALSE | 문제 풀이 포함 여부 |
| `has_analysis` | Boolean | DEFAULT FALSE | 작품 분석 포함 여부 |
| `created_at` | DateTime | DEFAULT utcnow | 생성 일시 |

**관계**:
- `book` (N:1) - 하나의 교재에 속함
- `units` (1:N) - 하나의 강의는 여러 학습 단위를 가짐
- `syncpoints` (1:N) - 하나의 강의는 여러 동기화 지점을 가짐

**인덱스**: 없음

---

### 3. units (학습 단위)

강의 내의 학습 단위(개념, 본문, 문제 등) 정보를 저장하는 테이블입니다.

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| `unit_id` | String | PRIMARY KEY | 학습 단위 고유 ID |
| `lesson_id` | String | FOREIGN KEY, NOT NULL | 강의 ID (lessons.lesson_id 참조, CASCADE DELETE) |
| `type` | Enum(UnitType) | NOT NULL | 단위 타입 (CONCEPT_CORE, CONCEPT_FORM, CONCEPT_CONTENT, CONCEPT_SUMMARY, PASSAGE, QUESTION) |
| `title` | String | NOT NULL | 단위 제목 |
| `order` | Integer | NOT NULL | 단위 순서 |
| `content_text` | Text | NULL | 개념/지문 텍스트 |
| `braille_text` | Text | NULL | 점자 변환 결과 |
| `image_path` | String | NULL | 이미지 경로 (단일, 하위호환용) |
| `content_image_paths` | Text | NULL | 여러 이미지 경로 (JSON 배열) |
| `question_stem` | Text | NULL | 문제 지문 |
| `question_choices` | Text | NULL | 문제 선택지 (JSON 배열: ["① ...", "② ..."]) |
| `question_answer` | Integer | NULL | 정답 번호 |
| `ai_explanation` | Text | NULL | AI 튜터 설명 |
| `braille_keywords` | Text | NULL | 점자 키워드 (JSON 배열) |
| `created_at` | DateTime | DEFAULT utcnow | 생성 일시 |

**관계**:
- `lesson` (N:1) - 하나의 강의에 속함
- `answers` (1:N) - 하나의 단위는 여러 답안 기록을 가짐
- `review_items` (1:N) - 하나의 단위는 여러 복습 항목을 가짐

**인덱스**: 없음

**UnitType 열거형**:
- `CONCEPT_CORE`: 핵심 개념
- `CONCEPT_FORM`: 개념 형식
- `CONCEPT_CONTENT`: 개념 내용
- `CONCEPT_SUMMARY`: 단원 요약
- `PASSAGE`: 본문/지문
- `QUESTION`: 문제

---

### 4. syncpoints (동기화 지점)

강의 대본과 학습 단위를 동기화하기 위한 타임스탬프 정보를 저장하는 테이블입니다.

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| `syncpoint_id` | String | PRIMARY KEY | 동기화 지점 고유 ID |
| `lesson_id` | String | FOREIGN KEY, NOT NULL | 강의 ID (lessons.lesson_id 참조, CASCADE DELETE) |
| `timestamp_sec` | Float | NOT NULL | 타임스탬프 (초) |
| `hint_type` | String | NULL | 힌트 타입 ("개념", "예시", "문제", "정리") |
| `unit_id` | String | FOREIGN KEY, NULL | 학습 단위 ID (units.unit_id 참조, SET NULL) |
| `created_at` | DateTime | DEFAULT utcnow | 생성 일시 |

**관계**:
- `lesson` (N:1) - 하나의 강의에 속함
- `unit` (N:1) - 하나의 학습 단위와 연결 (선택적)
- `logs` (1:N) - 하나의 동기화 지점은 여러 로그를 가짐

**인덱스**: 없음

---

### 5. user_progress (사용자 진도)

사용자의 학습 진도를 추적하는 테이블입니다.

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| `id` | Integer | PRIMARY KEY, AUTO_INCREMENT | 레코드 고유 ID |
| `user_id` | String | NOT NULL, INDEX | 사용자 ID |
| `book_id` | String | FOREIGN KEY, NULL | 교재 ID (books.book_id 참조, SET NULL) |
| `lesson_id` | String | FOREIGN KEY, NULL | 강의 ID (lessons.lesson_id 참조, SET NULL) |
| `unit_id` | String | FOREIGN KEY, NULL | 학습 단위 ID (units.unit_id 참조, SET NULL) |
| `syncpoint_id` | String | FOREIGN KEY, NULL | 동기화 지점 ID (syncpoints.syncpoint_id 참조, SET NULL) |
| `updated_at` | DateTime | DEFAULT utcnow | 수정 일시 |

**관계**: 외래키만 존재, 관계 정의 없음

**인덱스**:
- `user_id` (INDEX)

---

### 6. answers (답안 기록)

사용자가 제출한 문제 답안을 저장하는 테이블입니다.

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| `answer_id` | String | PRIMARY KEY | 답안 고유 ID |
| `user_id` | String | NOT NULL, INDEX | 사용자 ID |
| `unit_id` | String | FOREIGN KEY, NOT NULL | 학습 단위 ID (units.unit_id 참조, CASCADE DELETE) |
| `selected` | Integer | NULL | 선택한 답안 번호 |
| `is_correct` | Boolean | NOT NULL | 정답 여부 |
| `created_at` | DateTime | DEFAULT utcnow | 생성 일시 |

**관계**:
- `unit` (N:1) - 하나의 학습 단위에 속함

**인덱스**:
- `user_id` (INDEX)

---

### 7. review_queue (복습 큐)

틀린 문제나 반복 학습이 필요한 항목을 관리하는 테이블입니다.

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| `id` | Integer | PRIMARY KEY, AUTO_INCREMENT | 레코드 고유 ID |
| `user_id` | String | NOT NULL, INDEX | 사용자 ID |
| `unit_id` | String | FOREIGN KEY, NOT NULL | 학습 단위 ID (units.unit_id 참조, CASCADE DELETE) |
| `lesson_id` | String | FOREIGN KEY, NULL | 강의 ID (lessons.lesson_id 참조, SET NULL) |
| `reason` | String | NULL | 복습 사유 ("WRONG", "WRONG_REPEATED") |
| `priority` | Integer | DEFAULT 0 | 우선순위 |
| `completed` | Boolean | DEFAULT FALSE | 완료 여부 |
| `created_at` | DateTime | DEFAULT utcnow | 생성 일시 |

**관계**:
- `unit` (N:1) - 하나의 학습 단위에 속함

**인덱스**:
- `user_id` (INDEX)

---

### 8. sync_logs (동기화 로그)

동기화 지점에서 발생한 사용자 이벤트를 기록하는 테이블입니다.

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| `id` | Integer | PRIMARY KEY, AUTO_INCREMENT | 로그 고유 ID |
| `user_id` | String | NOT NULL, INDEX | 사용자 ID |
| `lesson_id` | String | FOREIGN KEY, NULL | 강의 ID (lessons.lesson_id 참조, SET NULL) |
| `syncpoint_id` | String | FOREIGN KEY, NULL | 동기화 지점 ID (syncpoints.syncpoint_id 참조, SET NULL) |
| `event` | String | NULL | 이벤트 타입 ("BEEP_PLAYED", "JUMP_CLICKED", "SCROLLED", "IGNORED") |
| `created_at` | DateTime | DEFAULT utcnow | 생성 일시 |

**관계**:
- `syncpoint` (N:1) - 하나의 동기화 지점에 속함

**인덱스**:
- `user_id` (INDEX)

---

### 9. curricula (커리큘럼)

과목별 커리큘럼 정보를 저장하는 테이블입니다.

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| `curriculum_id` | String | PRIMARY KEY | 커리큘럼 고유 ID |
| `book_id` | String | FOREIGN KEY, NULL | 교재 ID (books.book_id 참조, SET NULL) |
| `subject` | Enum(Subject) | NOT NULL | 과목 (KOREAN, ENGLISH, MATH) |
| `title` | String | NOT NULL | 커리큘럼 제목 |
| `status` | Enum(CurriculumStatus) | DEFAULT PENDING | 생성 상태 (PENDING, GENERATING, DONE, FAILED) |
| `lesson_count` | Integer | DEFAULT 0 | 강의 수 |
| `created_at` | DateTime | DEFAULT utcnow | 생성 일시 |
| `updated_at` | DateTime | DEFAULT utcnow | 수정 일시 |

**관계**:
- `book` (N:1) - 하나의 교재와 연결 (선택적)
- `learning_units` (1:N) - 하나의 커리큘럼은 여러 학습 단위를 가짐

**인덱스**: 없음

**CurriculumStatus 열거형**:
- `PENDING`: 대기 중
- `GENERATING`: 생성 중
- `DONE`: 완료
- `FAILED`: 실패

---

### 10. learning_units (학습 단위 - 커리큘럼)

커리큘럼 내의 학습 단위 정보를 저장하는 테이블입니다. `units` 테이블과는 별개로 커리큘럼 전용 구조입니다.

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| `unit_id` | String | PRIMARY KEY | 학습 단위 고유 ID |
| `curriculum_id` | String | FOREIGN KEY, NOT NULL | 커리큘럼 ID (curricula.curriculum_id 참조, CASCADE DELETE) |
| `lesson_id` | String | FOREIGN KEY, NULL | 강의 ID (lessons.lesson_id 참조, SET NULL) |
| `section_type` | String | NOT NULL | 섹션 타입 (과목별 정의: "concept", "example", "strategy", "problem" 등) |
| `title` | String | NULL | 학습 단위 제목 |
| `content` | Text | NOT NULL | 전체 내용 텍스트 |
| `order` | Integer | NOT NULL | 순서 |
| `learning_objective` | Text | NULL | 학습 목표 |
| `key_content` | Text | NULL | 핵심 내용 |
| `learning_point` | Text | NULL | 학습 포인트 |
| `braille_pattern` | Text | NULL | 점자 3셀 패턴 (JSON: [1,2,3]) |
| `braille_text` | Text | NULL | 점자 변환 결과 |
| `tts_text` | Text | NULL | TTS용 요약 텍스트 |
| `break_points` | Text | NULL | 분할 지점 (JSON 배열) |
| `pdf_references` | Text | NULL | PDF 참조 정보 (JSON) |
| `subject_metadata` | Text | NULL | 과목별 확장 정보 (JSON) |
| `created_at` | DateTime | DEFAULT utcnow | 생성 일시 |

**관계**:
- `curriculum` (N:1) - 하나의 커리큘럼에 속함
- `lesson` (N:1) - 하나의 강의와 연결 (선택적)

**인덱스**: 없음

---

### 11. curriculum_templates (커리큘럼 템플릿)

과목별 커리큘럼 템플릿을 저장하는 테이블입니다.

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| `template_id` | String | PRIMARY KEY | 템플릿 고유 ID |
| `subject` | Enum(Subject) | NOT NULL, UNIQUE | 과목 (KOREAN, ENGLISH, MATH) |
| `structure` | Text | NOT NULL | 교재 구조 정의 (JSON) |
| `dependency_rules` | Text | NULL | 의존성 규칙 정의 (JSON) |
| `created_at` | DateTime | DEFAULT utcnow | 생성 일시 |
| `updated_at` | DateTime | DEFAULT utcnow | 수정 일시 |

**관계**: 없음

**인덱스**:
- `subject` (UNIQUE)

---

## 열거형 (Enums)

### ParseStatus
- `PENDING`: 파싱 대기 중
- `PROCESSING`: 파싱 진행 중
- `DONE`: 파싱 완료
- `FAILED`: 파싱 실패

### Subject
- `KOREAN`: 국어
- `ENGLISH`: 영어
- `MATH`: 수학

### UnitType
- `CONCEPT_CORE`: 핵심 개념
- `CONCEPT_FORM`: 개념 형식
- `CONCEPT_CONTENT`: 개념 내용
- `CONCEPT_SUMMARY`: 단원 요약
- `PASSAGE`: 본문/지문
- `QUESTION`: 문제

### CurriculumStatus
- `PENDING`: 대기 중
- `GENERATING`: 생성 중
- `DONE`: 완료
- `FAILED`: 실패

---

## 관계도 (ERD)

```
books (1) ──< (N) lessons
                │
                ├──< (N) units
                │     │
                │     ├──< (N) answers
                │     └──< (N) review_queue
                │
                └──< (N) syncpoints
                      │
                      └──< (N) sync_logs

books (1) ──< (N) curricula
                │
                └──< (N) learning_units

user_progress ──> books (선택적)
                ──> lessons (선택적)
                ──> units (선택적)
                ──> syncpoints (선택적)
```

---

## 외부 저장소

### JSON 파일 저장소

데이터베이스 외에도 다음 경로에 JSON 파일로 데이터가 저장됩니다:

- **강의 데이터**: `backend/data/{subject}/{book_id}/lectures/lecture_*.json`
- **템플릿 데이터**: `backend/data/templates/*.json`
- **이미지 데이터**: 
  - `backend/data/{subject}/{book_id}/concepts_images/`
  - `backend/data/{subject}/{book_id}/content_images/`
  - `backend/data/{subject}/{book_id}/problems_images/`

템플릿은 데이터베이스가 아닌 JSON 파일로 관리됩니다.

---

## 데이터베이스 초기화

데이터베이스는 다음 명령으로 초기화됩니다:

```python
from app.infrastructure.database.session import init_db
init_db()  # Base.metadata.create_all(bind=engine) 실행
```

---

## 주의사항

1. **CASCADE DELETE**: 
   - `lessons` 삭제 시 관련 `units`, `syncpoints` 자동 삭제
   - `units` 삭제 시 관련 `answers`, `review_queue` 자동 삭제
   - `syncpoints` 삭제 시 관련 `sync_logs` 자동 삭제

2. **SET NULL**:
   - `books` 삭제 시 `user_progress.book_id`는 NULL로 설정
   - `lessons` 삭제 시 관련 외래키는 NULL로 설정 (CASCADE가 아닌 경우)

3. **JSON 필드**:
   - `key_points`, `content_image_paths`, `question_choices`, `braille_keywords` 등은 JSON 문자열로 저장
   - 애플리케이션 레벨에서 JSON 파싱 필요

4. **인덱스**:
   - `user_id` 필드는 여러 테이블에서 인덱스로 설정되어 있음
   - 성능 최적화를 위해 추가 인덱스가 필요할 수 있음

---

## 마이그레이션

현재는 SQLAlchemy의 `Base.metadata.create_all()`을 사용하여 테이블을 생성합니다. 향후 Alembic 등을 사용한 마이그레이션 시스템 도입을 고려할 수 있습니다.
