# Lesson 생성 가이드

Lesson이 어떻게 생성되는지 설명합니다.

## Lesson 생성 흐름

### 전체 프로세스

```
PDF 업로드
  ↓
파이프라인 실행 (textbook_pipeline.py)
  ↓
JSON 파일 생성
  ├─ lectures.json (강의 목록)
  └─ lecture_XX.json (각 강의 상세)
  ↓
커리큘럼 생성 (_create_curriculum_from_pipeline)
  ↓
Lesson 생성 (각 lecture → Lesson)
  ↓
Unit 생성 (각 section → Unit)
  ↓
DB 저장
```

## Lesson 생성 과정

### 1. 파이프라인 결과 → JSON 파일

**파일 위치:**
- `api/data/{subject}/lectures/lectures.json`
- `api/data/{subject}/lectures/lecture_XX.json`

**lectures.json 구조:**
```json
[
  {
    "lecture_id": 1,
    "title": "1강 | 시의 표현과 형식"
  },
  {
    "lecture_id": 2,
    "title": "2강 | 산문의 이해"
  }
]
```

**lecture_XX.json 구조:**
```json
{
  "subject": "literature",
  "lecture_id": 1,
  "title": "1강 | 시의 표현과 형식 >>> 고전 시가",
  "sections": [
    {
      "title": "개념: section",
      "content": ["..."],
      "page": 11,
      "type": "concept"
    },
    {
      "title": "본문",
      "content": ["..."],
      "page": 12,
      "type": "passage"
    }
  ],
  "problems": ["01", "02"]
}
```

### 2. 커리큘럼 생성 (`_create_curriculum_from_pipeline`)

**위치:** `api/app/routers/books.py`

**프로세스:**
1. `lectures.json` 파일 읽기
2. 각 lecture에 대해:
   - `lecture_XX.json` 파일 읽기
   - 강의 제목 검증 ("N강" 형식)
   - Lesson 생성
   - Sections를 Unit으로 변환

### 3. Lesson 생성 코드

```python
def _create_curriculum_from_pipeline(...):
    # lectures.json 읽기
    with open(lectures_json, "r", encoding="utf-8") as f:
        lectures = json.load(f)
    
    # 각 강의(lecture)를 레슨(lesson)으로 변환
    for lecture in lectures:
        lecture_id = lecture.get("lecture_id", 0)
        lecture_number = lecture.get("lecture_number", lecture_id)
        
        # 강의 상세 파일 읽기
        lecture_file = lectures_dir / f"lecture_{lecture_id:02d}.json"
        with open(lecture_file, "r", encoding="utf-8") as f:
            lecture_data = json.load(f)
        
        # 레슨 제목 추출
        lecture_title = lecture_data.get("title", f"{lecture_number}강")
        
        # 강의 제목 검증 ("N강" 형식)
        if subject_enum in [Subject.KOREAN, Subject.MATH]:
            lecture_title_match = re.search(r'^(\d+)강', lecture_title)
            if not lecture_title_match:
                continue  # 건너뜀
        
        # Lesson ID 생성
        lesson_db_id = generate_lesson_id(pipeline_subject, lecture_number)
        
        # Lesson 생성
        lesson = Lesson(
            lesson_id=lesson_db_id,
            book_id=book_id,
            index=lecture_number,
            title=lecture_title,
        )
        db.add(lesson)
        db.flush()
```

### 4. Lesson ID 생성

**함수:** `generate_lesson_id(subject: str, lesson_number: int)`

**형식:**
- 문학: `lesson_literature_{lesson_number:02d}`
- 수학: `lesson_math1_{lesson_number:02d}`
- 영어: `lesson_english_{lesson_number:02d}`

**예시:**
- `lesson_literature_01` (1강)
- `lesson_literature_02` (2강)

### 5. Unit 생성 (Sections → Units)

각 section이 Unit으로 변환됩니다:

```python
for idx, section in enumerate(sections):
    # section_type 결정
    section_type = section.get("type", "general")
    
    # UnitType 매핑
    unit_type = _map_section_type_to_unit_type(section_type)
    
    # Unit 생성
    unit = Unit(
        unit_id=unit_id,
        lesson_id=lesson_id,
        type=unit_type,
        title=section.get("title", ""),
        order=idx,
        content_text=section.get("content", ""),
        # ...
    )
    db.add(unit)
```

## YOLO 기반 Lesson 생성

### YOLO 감지 → Lecture 변환

```python
# YOLO 감지 결과
yolo_detection_results = {
    'lectures': [
        {
            'lecture_id': 1,
            'title': '1강',
            'page': 8,
            'bbox': [...],
            'units': [...]  # YOLO로 감지된 units
        }
    ]
}

# Lecture → Lesson 변환
for lecture in yolo_lectures:
    lesson = Lesson(
        lesson_id=generate_lesson_id(subject, lecture['lecture_id']),
        book_id=book_id,
        index=lecture['lecture_id'],
        title=lecture['title'],
    )
```

### Units 변환

YOLO로 감지된 units가 sections로 변환되어 Unit이 됩니다:

```python
# YOLO units → sections 변환
sections = []
for unit in lecture['units']:
    section = {
        'title': unit.get('text', ''),
        'type': unit.get('type', 'general'),
        'page': unit.get('page', 0),
        'bbox': unit.get('bbox', [])
    }
    sections.append(section)

# sections → Units 변환
for section in sections:
    unit = Unit(...)
```

## Lesson 모델 구조

```python
class Lesson(Base):
    lesson_id: str          # PK, "lesson_literature_01"
    book_id: str            # FK, Book 참조
    index: int              # 강의 번호 (1, 2, 3, ...)
    title: str              # 강의 제목 ("1강 | 시의 표현과 형식")
    lecture_script_text: Text  # 강의 대본 (선택)
    estimated_time: int    # 예상 소요 시간 (분)
    key_points: Text        # JSON: ["핵심1", "핵심2"]
    has_question: bool      # 문제 포함 여부
    has_analysis: bool      # 작품 분석 포함 여부
    created_at: DateTime
```

## 데이터 흐름

### 일반 파이프라인

```
PDF → 파이프라인
  ↓
lectures.json 생성
  ↓
lecture_XX.json 생성 (sections 포함)
  ↓
_create_curriculum_from_pipeline()
  ↓
각 lecture → Lesson 생성
  ↓
각 section → Unit 생성
```

### YOLO 파이프라인

```
PDF → 이미지 변환
  ↓
YOLO 감지 (header, section, concept_box, ...)
  ↓
header → lecture 변환
  ↓
lecture에 units 포함
  ↓
lecture → Lesson 생성
  ↓
units → sections → Units 변환
```

## Lesson 생성 위치

### 1. PDF 업로드 시 (자동)

**엔드포인트:** `POST /api/v1/books/upload`

**프로세스:**
1. PDF 업로드
2. 백그라운드에서 파이프라인 실행
3. `_process_pdf_background()` 호출
4. `_create_curriculum_from_pipeline()` 호출
5. Lesson 자동 생성

### 2. 수동 생성

**엔드포인트:** `POST /api/v1/lessons`

```python
lesson = Lesson(
    lesson_id=generate_lesson_id(subject, index),
    book_id=book_id,
    index=index,
    title=title,
)
```

## Lesson과 Unit의 관계

```
Book
  └─ Lesson (1강)
      ├─ Unit (concept) - 개념 제목
      ├─ Unit (concept) - 개념 내용
      ├─ Unit (passage) - 본문
      └─ Unit (question) - 문제
```

**관계:**
- `Lesson.units`: One-to-Many (Lesson → Units)
- `Unit.lesson_id`: Foreign Key (Unit → Lesson)

## 검증 로직

### 강의 제목 검증

```python
# "N강" 형식 검증
lecture_title_match = re.search(r'^(\d+)강', lecture_title)
if not lecture_title_match:
    continue  # 건너뜀

# 문제 지문 필터링
if re.match(r'^\d{2,}\s+[가-힣]{5,}', lecture_title) and not re.search(r'^\d+강', lecture_title):
    continue  # 건너뜀

# 문제 번호 필터링
if re.match(r'^\d{2,}\s+[가-힣]{1,4}', lecture_title) and not re.search(r'^\d+강', lecture_title):
    continue  # 건너뜀
```

### 섹션 검증

```python
sections = lecture_data.get("sections", [])
problems = lecture_data.get("problems", [])

if not sections and not problems:
    continue  # 건너뜀
```

## YOLO 기반 Lesson 생성 (새로운 방식)

### YOLO Header → Lesson

```python
# YOLO 감지 결과
header_detection = {
    'class_name': 'header',
    'bbox': [x1, y1, x2, y2],
    'confidence': 0.95
}

# Header 텍스트 추출 (OCR)
header_text = extract_text_from_bbox(ocr_data, bbox)

# Lecture 생성
lecture = {
    'lecture_id': 1,
    'title': header_text,  # "1강 | 시의 표현과 형식"
    'page': 8,
    'units': [...]  # 같은 페이지의 다른 영역들
}

# Lesson 생성
lesson = Lesson(
    lesson_id=generate_lesson_id('literature', 1),
    book_id=book_id,
    index=1,
    title=header_text,
)
```

### Units → Sections → Units 변환

```python
# YOLO units
units = [
    {'type': 'concept', 'subtype': 'title', ...},
    {'type': 'concept', 'subtype': 'content', ...},
    {'type': 'passage', ...},
    {'type': 'question', ...}
]

# → sections 변환
sections = [
    {'title': '개념: section', 'type': 'concept', ...},
    {'title': '개념 내용', 'type': 'concept', ...},
    {'title': '본문', 'type': 'passage', ...}
]

# → Units 변환
for section in sections:
    unit = Unit(
        type=UnitType.CONCEPT_CORE,  # section_type → UnitType 매핑
        title=section['title'],
        ...
    )
```

## 참고

- **Lesson ID 형식**: `lesson_{subject}_{number:02d}`
- **Lesson 생성 위치**: `_create_curriculum_from_pipeline()` (books.py)
- **Unit 생성 위치**: 같은 함수 내에서 sections를 순회하며 생성
- **YOLO 우선**: YOLO 결과가 있으면 자동으로 Lesson 생성
