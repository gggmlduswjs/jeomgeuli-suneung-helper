# 데이터베이스 스키마 문서

## 개요

점글이 수능 헬퍼 프로젝트의 데이터베이스 스키마 문서입니다.
SQLite 데이터베이스를 사용하며, SQLAlchemy ORM으로 관리됩니다.

**데이터베이스 파일**: `data/db.sqlite3`

---

## ERD (Entity Relationship Diagram)

```
┌─────────────────┐
│     books       │
├─────────────────┤
│ book_id (PK)    │
│ title           │
│ subject         │
│ year            │
│ parse_status    │
│ file_path       │
│ created_at      │
│ updated_at      │
└────────┬────────┘
         │ 1
         │
         │ N
┌────────▼────────┐
│    lessons      │
├─────────────────┤
│ lesson_id (PK)  │
│ book_id (FK)    │──┐
│ index           │  │
│ title           │  │
│ lecture_script  │  │
│ estimated_time  │  │
│ key_points      │  │
│ has_question    │  │
│ has_analysis    │  │
│ created_at      │  │
└────────┬────────┘  │
         │ 1          │
         │            │
         │ N          │
┌────────▼────────┐   │
│     units       │   │
├─────────────────┤   │
│ unit_id (PK)    │   │
│ lesson_id (FK)  │───┘
│ type            │
│ title           │
│ order           │
│ content_text    │
│ braille_text    │
│ question_stem   │
│ question_choices│
│ question_answer │
│ created_at      │
└────────┬────────┘
         │ 1
         │
         │ N
┌────────▼────────┐
│    answers      │
├─────────────────┤
│ answer_id (PK) │
│ user_id        │
│ unit_id (FK)   │──┐
│ selected       │  │
│ is_correct     │  │
│ created_at    │  │
└────────────────┘  │
                    │
┌─────────────────┐ │
│ review_queue    │ │
├─────────────────┤ │
│ id (PK)         │ │
│ user_id        │ │
│ unit_id (FK)   │─┘
│ lesson_id (FK) │
│ reason         │
│ priority       │
│ completed      │
│ created_at    │
└────────────────┘

┌─────────────────┐
│  user_progress  │
├─────────────────┤
│ id (PK)         │
│ user_id        │
│ book_id (FK)   │──┐
│ lesson_id (FK) │──┤
│ unit_id (FK)   │──┤
│ syncpoint_id   │──┤
│ updated_at     │  │
└────────────────┘  │
                    │
┌─────────────────┐ │
│  syncpoints     │ │
├─────────────────┤ │
│ syncpoint_id(PK)│ │
│ lesson_id (FK)  │─┼─┐
│ timestamp_sec   │ │ │
│ hint_type       │ │ │
│ unit_id (FK)    │─┼─┼─┐
│ created_at      │ │ │ │
└─────────────────┘ │ │ │
                    │ │ │
┌─────────────────┐ │ │ │
│   sync_logs     │ │ │ │
├─────────────────┤ │ │ │
│ id (PK)         │ │ │ │
│ user_id        │ │ │ │
│ lesson_id (FK) │─┘ │ │
│ syncpoint_id   │───┘ │
│ event          │     │
│ created_at    │     │
└────────────────┘     │
                        │
┌─────────────────┐     │
│  curricula      │     │
├─────────────────┤     │
│ curriculum_id   │     │
│ book_id (FK)    │─────┘
│ subject         │
│ title           │
│ status          │
│ lesson_count    │
│ created_at      │
│ updated_at      │
└────────┬────────┘
         │ 1
         │
         │ N
┌────────▼──────────────┐
│   learning_units      │
├───────────────────────┤
│ unit_id (PK)         │
│ curriculum_id (FK)   │──┐
│ lesson_id (FK)       │──┼──┐
│ section_type         │  │  │
│ title                │  │  │
│ content              │  │  │
│ order                │  │  │
│ learning_objective   │  │  │
│ key_content          │  │  │
│ learning_point       │  │  │
│ braille_pattern      │  │  │
│ braille_text         │  │  │
│ tts_text             │  │  │
│ break_points         │  │  │
│ pdf_references       │  │  │
│ subject_metadata     │  │  │
│ created_at           │  │  │
└──────────────────────┘  │  │
                          │  │
┌─────────────────────────┘  │
│  curriculum_templates       │
├─────────────────────────────┤
│ template_id (PK)            │
│ subject (UNIQUE)            │
│ structure                  │
│ dependency_rules            │
│ created_at                 │
│ updated_at                 │
└────────────────────────────┘
```

---

## 테이블 상세

### 1. books (교재)

**용도**: 교재 메타데이터 저장

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| book_id | String | PK | 교재 고유 ID |
| title | String | NOT NULL | 교재 제목 |
| subject | Enum(Subject) | NOT NULL | 과목 (KOREAN, ENGLISH, MATH) |
| year | Integer | NULL | 출판 연도 |
| parse_status | Enum(ParseStatus) | DEFAULT PENDING | 파싱 상태 |
| file_path | String | NULL | PDF 파일 경로 |
| created_at | DateTime | DEFAULT now | 생성 시간 |
| updated_at | DateTime | DEFAULT now | 수정 시간 |

**관계**:
- `lessons` (1:N) - 하나의 교재에 여러 레슨
- `curricula` (1:N) - 하나의 교재에 여러 커리큘럼

---

### 2. lessons (레슨/강)

**용도**: 교재 내 강의 단위 정보

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| lesson_id | String | PK | 레슨 고유 ID |
| book_id | String | FK, NOT NULL | 교재 ID (CASCADE 삭제) |
| index | Integer | NOT NULL | 레슨 순서 |
| title | String | NOT NULL | 레슨 제목 |
| lecture_script_text | Text | NULL | 강의 대본 텍스트 |
| estimated_time | Integer | NULL | 예상 소요 시간 (분) |
| key_points | Text | NULL | 핵심 포인트 (JSON) |
| has_question | Boolean | DEFAULT false | 문제 포함 여부 |
| has_analysis | Boolean | DEFAULT false | 작품 분석 포함 여부 |
| created_at | DateTime | DEFAULT now | 생성 시간 |

**관계**:
- `book` (N:1) - 하나의 교재에 속함
- `units` (1:N) - 하나의 레슨에 여러 단위
- `syncpoints` (1:N) - 하나의 레슨에 여러 동기화 포인트

---

### 3. units (학습 단위)

**용도**: 레슨 내 학습 단위 (개념, 지문, 문제 등)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| unit_id | String | PK | 단위 고유 ID |
| lesson_id | String | FK, NOT NULL | 레슨 ID (CASCADE 삭제) |
| type | Enum(UnitType) | NOT NULL | 단위 타입 |
| title | String | NOT NULL | 단위 제목 |
| order | Integer | NOT NULL | 순서 |
| content_text | Text | NULL | 개념/지문 텍스트 |
| braille_text | Text | NULL | 점자 변환 결과 |
| question_stem | Text | NULL | 문제 지문 |
| question_choices | Text | NULL | 선택지 (JSON) |
| question_answer | Integer | NULL | 정답 번호 |
| created_at | DateTime | DEFAULT now | 생성 시간 |

**UnitType 종류**:
- `CONCEPT_CORE`: 핵심 개념
- `CONCEPT_FORM`: 개념 형식
- `CONCEPT_CONTENT`: 개념 내용
- `PASSAGE`: 지문
- `QUESTION`: 문제

**관계**:
- `lesson` (N:1) - 하나의 레슨에 속함
- `answers` (1:N) - 하나의 단위에 여러 답안
- `review_items` (1:N) - 하나의 단위에 여러 복습 항목

---

### 4. user_progress (사용자 진행 상황)

**용도**: 사용자의 현재 학습 위치 추적

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | Integer | PK, AUTO | 자동 증가 ID |
| user_id | String | NOT NULL, INDEX | 사용자 ID |
| book_id | String | FK, NULL | 현재 교재 (SET NULL 삭제) |
| lesson_id | String | FK, NULL | 현재 레슨 (SET NULL 삭제) |
| unit_id | String | FK, NULL | 현재 단위 (SET NULL 삭제) |
| syncpoint_id | String | FK, NULL | 동기화 포인트 (SET NULL 삭제) |
| updated_at | DateTime | DEFAULT now | 수정 시간 |

**특징**:
- 사용자당 하나의 레코드만 존재 (user_id로 조회)
- Foreign Key는 모두 SET NULL (부모 삭제 시 NULL로 설정)

---

### 5. answers (답안)

**용도**: 사용자가 제출한 답안 기록

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| answer_id | String | PK | 답안 고유 ID |
| user_id | String | NOT NULL, INDEX | 사용자 ID |
| unit_id | String | FK, NOT NULL | 단위 ID (CASCADE 삭제) |
| selected | Integer | NULL | 선택한 답안 번호 |
| is_correct | Boolean | NOT NULL | 정답 여부 |
| created_at | DateTime | DEFAULT now | 제출 시간 |

**관계**:
- `unit` (N:1) - 하나의 단위에 여러 답안

---

### 6. review_queue (복습 큐)

**용도**: 틀린 문제를 복습 큐에 추가

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | Integer | PK, AUTO | 자동 증가 ID |
| user_id | String | NOT NULL | 사용자 ID |
| unit_id | String | FK, NOT NULL | 단위 ID (CASCADE 삭제) |
| lesson_id | String | FK, NULL | 레슨 ID (SET NULL 삭제) |
| reason | String | NULL | 복습 사유 |
| priority | Integer | DEFAULT 0 | 우선순위 |
| completed | Boolean | DEFAULT false | 완료 여부 |
| created_at | DateTime | DEFAULT now | 추가 시간 |

---

### 7. syncpoints (동기화 포인트)

**용도**: 강의 오디오와 학습 단위 동기화

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| syncpoint_id | String | PK | 동기화 포인트 ID |
| lesson_id | String | FK, NOT NULL | 레슨 ID (CASCADE 삭제) |
| timestamp_sec | Float | NOT NULL | 오디오 타임스탬프 (초) |
| hint_type | String | NULL | 힌트 타입 |
| unit_id | String | FK, NULL | 단위 ID (SET NULL 삭제) |
| created_at | DateTime | DEFAULT now | 생성 시간 |

---

### 8. sync_logs (동기화 로그)

**용도**: 사용자의 동기화 포인트 상호작용 기록

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | Integer | PK, AUTO | 자동 증가 ID |
| user_id | String | NOT NULL | 사용자 ID |
| lesson_id | String | FK, NULL | 레슨 ID (SET NULL 삭제) |
| syncpoint_id | String | FK, NULL | 동기화 포인트 ID (SET NULL 삭제) |
| event | String | NULL | 이벤트 타입 |
| created_at | DateTime | DEFAULT now | 발생 시간 |

---

### 9. curricula (커리큘럼)

**용도**: 교재별 커리큘럼 정보

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| curriculum_id | String | PK | 커리큘럼 고유 ID |
| book_id | String | FK, NULL | 교재 ID (SET NULL 삭제) |
| subject | Enum(Subject) | NOT NULL | 과목 |
| title | String | NOT NULL | 커리큘럼 제목 |
| status | Enum(CurriculumStatus) | DEFAULT PENDING | 생성 상태 |
| lesson_count | Integer | DEFAULT 0 | 레슨 수 |
| created_at | DateTime | DEFAULT now | 생성 시간 |
| updated_at | DateTime | DEFAULT now | 수정 시간 |

**CurriculumStatus 종류**:
- `PENDING`: 대기 중
- `GENERATING`: 생성 중
- `DONE`: 완료
- `FAILED`: 실패

---

### 10. learning_units (학습 단위 - 커리큘럼용)

**용도**: 커리큘럼 내 학습 단위 (과목별 구조화된 콘텐츠)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| unit_id | String | PK | 학습 단위 ID |
| curriculum_id | String | FK, NOT NULL | 커리큘럼 ID (CASCADE 삭제) |
| lesson_id | String | FK, NULL | 레슨 ID (SET NULL 삭제) |
| section_type | String | NOT NULL | 섹션 타입 |
| title | String | NULL | 제목 |
| content | Text | NOT NULL | 전체 내용 |
| order | Integer | NOT NULL | 순서 |
| learning_objective | Text | NULL | 학습 목표 |
| key_content | Text | NULL | 핵심 내용 |
| learning_point | Text | NULL | 학습 포인트 |
| braille_pattern | Text | NULL | 점자 패턴 (JSON) |
| braille_text | Text | NULL | 점자 변환 결과 |
| tts_text | Text | NULL | TTS용 요약 |
| break_points | Text | NULL | 분할 지점 (JSON) |
| pdf_references | Text | NULL | PDF 참조 (JSON) |
| subject_metadata | Text | NULL | 과목별 메타데이터 (JSON) |
| created_at | DateTime | DEFAULT now | 생성 시간 |

---

### 11. curriculum_templates (커리큘럼 템플릿)

**용도**: 과목별 커리큘럼 구조 템플릿

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| template_id | String | PK | 템플릿 ID |
| subject | Enum(Subject) | NOT NULL, UNIQUE | 과목 |
| structure | Text | NOT NULL | 구조 정의 (JSON) |
| dependency_rules | Text | NULL | 의존성 규칙 (JSON) |
| created_at | DateTime | DEFAULT now | 생성 시간 |
| updated_at | DateTime | DEFAULT now | 수정 시간 |

---

## 관계 요약

### 계층 구조
```
Book (1) ──< (N) Lesson (1) ──< (N) Unit (1) ──< (N) Answer
                                                      └──< (N) ReviewQueue
```

### 참조 관계
- `UserProgress` → `Book`, `Lesson`, `Unit`, `Syncpoint` (모두 선택적)
- `Syncpoint` → `Lesson`, `Unit` (선택적)
- `SyncLog` → `Lesson`, `Syncpoint` (선택적)
- `Curriculum` → `Book` (선택적)
- `LearningUnit` → `Curriculum`, `Lesson` (선택적)

---

## 삭제 정책 (CASCADE)

### CASCADE 삭제 (부모 삭제 시 자식도 삭제)
- `Book` 삭제 → `Lesson` 삭제 → `Unit` 삭제 → `Answer`, `ReviewQueue` 삭제
- `Curriculum` 삭제 → `LearningUnit` 삭제
- `Lesson` 삭제 → `Syncpoint` 삭제 → `SyncLog` 삭제

### SET NULL 삭제 (부모 삭제 시 NULL로 설정)
- `Book` 삭제 → `UserProgress.book_id = NULL`
- `Lesson` 삭제 → `UserProgress.lesson_id = NULL`, `LearningUnit.lesson_id = NULL`
- `Unit` 삭제 → `UserProgress.unit_id = NULL`, `Syncpoint.unit_id = NULL`
- `Syncpoint` 삭제 → `UserProgress.syncpoint_id = NULL`, `SyncLog.syncpoint_id = NULL`

---

## 인덱스

### 자동 인덱스
- Primary Key: 모든 테이블의 PK
- Foreign Key: 모든 FK (SQLite 자동 생성)

### 명시적 인덱스
- `user_progress.user_id` - 사용자별 진행 상황 조회
- `answers.user_id` - 사용자별 답안 조회

---

## 데이터 타입

### Enum 타입

**Subject**:
- `KOREAN`: 국어
- `ENGLISH`: 영어
- `MATH`: 수학

**ParseStatus**:
- `PENDING`: 대기 중
- `PROCESSING`: 처리 중
- `DONE`: 완료
- `FAILED`: 실패

**UnitType**:
- `CONCEPT_CORE`: 핵심 개념
- `CONCEPT_FORM`: 개념 형식
- `CONCEPT_CONTENT`: 개념 내용
- `PASSAGE`: 지문
- `QUESTION`: 문제

**CurriculumStatus**:
- `PENDING`: 대기 중
- `GENERATING`: 생성 중
- `DONE`: 완료
- `FAILED`: 실패

---

## JSON 필드

다음 필드는 JSON 문자열로 저장됩니다:

- `lessons.key_points`: `["핵심1", "핵심2"]`
- `units.question_choices`: `["① ...", "② ..."]`
- `learning_units.braille_pattern`: `[1,2,3]`
- `learning_units.break_points`: `["자, 그다음에...", "먼저..."]`
- `learning_units.pdf_references`: `[{"type": "problem", "number": 1}, ...]`
- `learning_units.subject_metadata`: 과목별 특화 정보
- `curriculum_templates.structure`: 교재 구조 정의
- `curriculum_templates.dependency_rules`: 의존성 규칙

---

## 데이터베이스 초기화

```python
from app.db.session import init_db

# 모든 테이블 생성
init_db()
```

**위치**: `api/app/db/session.py`

---

## 마이그레이션

현재는 SQLAlchemy의 `Base.metadata.create_all()`을 사용하여 자동으로 테이블을 생성합니다.

향후 Alembic을 사용한 마이그레이션 시스템 도입을 고려할 수 있습니다.

---

## 데이터베이스 파일 위치

- **개발 환경**: `data/db.sqlite3` (프로젝트 루트)
- **경로 설정**: `api/app/core/config.py`의 `DATABASE_URL`

---

## 주의사항

1. **SQLite 제한사항**:
   - 동시 쓰기 제한 (WAL 모드 사용 권장)
   - 외래 키 제약조건은 기본적으로 비활성화 (활성화하려면 설정 필요)

2. **트랜잭션**:
   - 모든 변경사항은 `db.commit()`으로 커밋해야 저장됨
   - 에러 발생 시 `db.rollback()`으로 롤백 가능

3. **CASCADE 삭제**:
   - Book 삭제 시 관련된 모든 Lesson, Unit, Answer가 자동 삭제됨
   - 주의해서 사용해야 함
