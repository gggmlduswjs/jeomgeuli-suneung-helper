# 학습 페이지 데이터 플로우

## 전체 플로우

```
1. PDF 업로드
   ↓
2. PDF 파싱 (sections 추출 + 이미지 크롭) ✅ 방금 구현
   ↓
3. LearningUnit 생성 (sections → LearningUnit)
   ↓
4. Unit 변환 (LearningUnit → Lesson + Unit)
   ↓
5. DB 저장
   ↓
6. 프론트엔드 API 호출
   ↓
7. 학습 페이지 표시
```

## 단계별 상세

### 1. PDF 파싱 (방금 구현 완료)

**위치**: `unified_parser.py`, `base.py`

**처리 내용**:
```python
# 섹션 추출
sections = extractor.extract(lecture_ocr_data)

# 각 섹션의 bbox로 이미지 크롭 (NEW!)
sections_with_images = crop_section_images(
    pdf_path=pdf_path,
    sections=sections,
    book_id=book_id
)
```

**결과 (SectionData)**:
```json
{
  "type": "concept",
  "title": "핵심 개념",
  "page": 9,
  "bbox": [100, 150, 500, 400],
  "text": "시의 표현 기법에는...",
  "image_path": "backend/data/parsing_results/images/book123/concept_p009_00.png"  // ← NEW!
}
```

### 2. LearningUnit 생성

**위치**: `books.py` (약 200-1000 라인)

**처리 내용**:
```python
# 섹션 → LearningUnit 변환
for section in sections:
    # 이미지 경로 저장
    pdf_ref = {
        "lecture_id": lecture_id,
        "page": section['page'],
        "image_filename": "concept_p009_00.png",  # 파일명만 추출
        "section_type": section['type']
    }

    learning_unit = LearningUnit(
        unit_id=unit_id,
        curriculum_id=curriculum_id,
        section_type=section['type'],  # concept, passage, problem
        title=section['title'],
        content=section['text'],
        order=order,
        pdf_references=json.dumps([pdf_ref])
    )
    db.add(learning_unit)
```

**LearningUnit 구조**:
```python
class LearningUnit:
    unit_id: str
    curriculum_id: str
    section_type: str  # concept, passage, problem
    title: str
    content: str  # 텍스트 내용
    order: int
    pdf_references: str  # JSON: [{"page": 9, "image_filename": "..."}]
```

### 3. Unit 변환

**위치**: `book_conversion.py`

**처리 내용**:
```python
def convert_learning_units_to_units(curriculum_id, book_id, db):
    # LearningUnit 조회
    learning_units = db.query(LearningUnit).filter(
        LearningUnit.curriculum_id == curriculum_id
    ).all()

    # Lesson별로 그룹화
    for lesson_number, lesson_units in lessons_dict.items():
        # Lesson 생성
        lesson = Lesson(
            lesson_id=lesson_id,
            book_id=book_id,
            title=f"{lesson_number}강",
            index=lesson_number
        )

        # 각 LearningUnit을 Unit으로 변환
        for lu in lesson_units:
            # pdf_references에서 이미지 경로 추출
            image_paths = []
            pdf_refs = json.loads(lu.pdf_references)
            for ref in pdf_refs:
                if ref.get('image_filename'):
                    # 경로 구성
                    img_path = f"/api/data/{subject}/{book_id}/{img_dir}/{ref['image_filename']}"
                    image_paths.append(img_path)

            # Unit 생성
            unit = Unit(
                unit_id=unit_id,
                lesson_id=lesson.lesson_id,
                type=unit_type,  # UnitType enum
                title=lu.title,
                content_text=lu.content,
                image_path=image_paths[0] if image_paths else None,  # 대표 이미지
                content_image_paths=json.dumps(image_paths) if len(image_paths) > 1 else None,  # 추가 이미지들
                order=unit_index
            )
            db.add(unit)
```

**Unit 구조**:
```python
class Unit:
    unit_id: str
    lesson_id: str
    type: UnitType  # CONCEPT, PASSAGE, PROBLEM
    title: str
    order: int
    content_text: str  # 텍스트 내용
    image_path: str  # 대표 이미지 경로 (단일)
    content_image_paths: str  # JSON: ["path1", "path2", ...]
    braille_text: str
    ai_explanation: str
    # 문제 타입인 경우
    question_stem: str
    question_choices: str  # JSON
    question_answer: int
```

### 4. 프론트엔드 API

**API 엔드포인트**: `GET /units/{unit_id}`

**위치**: `units.py`

**응답 구조**:
```json
{
  "unit_id": "u_abc123",
  "lesson_id": "l_def456",
  "type": "concept",
  "title": "핵심 개념",
  "order": 0,
  "content_text": "시의 표현 기법에는...",
  "image_path": "/api/data/literature/book123/concepts_images/concept_p009_00.png",
  "content_image_paths": [
    "/api/data/literature/book123/concepts_images/concept_p009_00.png",
    "/api/data/literature/book123/concepts_images/concept_p009_01.png"
  ],
  "braille_text": "⠎⠊⠮ ⠚⠕⠮⠑⠮...",
  "ai_explanation": "이 섹션에서는..."
}
```

### 5. 학습 페이지 표시

**프론트엔드 (예시)**:
```vue
<template>
  <div class="learning-page">
    <!-- 단원 제목 -->
    <h2>{{ unit.title }}</h2>

    <!-- 대표 이미지 -->
    <img
      v-if="unit.image_path"
      :src="unit.image_path"
      :alt="unit.title"
      class="main-image"
    />

    <!-- 추가 이미지들 -->
    <div v-if="unit.content_image_paths" class="additional-images">
      <img
        v-for="(path, idx) in unit.content_image_paths"
        :key="idx"
        :src="path"
        class="content-image"
      />
    </div>

    <!-- 텍스트 내용 -->
    <div class="content-text">
      {{ unit.content_text }}
    </div>

    <!-- 점자 텍스트 (시각장애인용) -->
    <div v-if="unit.braille_text" class="braille-text">
      {{ unit.braille_text }}
    </div>

    <!-- AI 설명 -->
    <div v-if="unit.ai_explanation" class="ai-explanation">
      <h3>AI 설명</h3>
      <p>{{ unit.ai_explanation }}</p>
    </div>

    <!-- 문제인 경우 -->
    <div v-if="unit.type === 'problem' && unit.question" class="question">
      <p class="question-stem">{{ unit.question.stem }}</p>
      <ul class="choices">
        <li v-for="(choice, idx) in unit.question.choices" :key="idx">
          {{ idx + 1 }}. {{ choice }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();
const unit = ref(null);

onMounted(async () => {
  const unitId = route.params.unitId;
  const response = await fetch(`/api/v1/units/${unitId}`);
  unit.value = await response.json();
});
</script>
```

## 현재 이슈 🚨

### 이미지 경로 불일치

**방금 구현한 섹션 이미지 크롭**:
```
backend/data/parsing_results/images/{book_id}/concept_p009_00.png
```

**book_conversion.py가 기대하는 경로**:
```
/api/data/{subject}/{book_id}/concepts_images/concept_p009_00.png
```

**해결 방법**:

#### 옵션 1: 이미지 저장 경로 변경 (권장)
섹션 이미지를 표준 경로에 저장하도록 수정:

```python
# base.py의 crop_section_images() 수정
def crop_section_images(...):
    # 출력 디렉토리 설정
    if not output_dir:
        # 과목별 디렉토리 구조 사용
        base_dir = Path(f"backend/data/{subject}/{book_id}")

        # 섹션 타입별 디렉토리
        if section_type == 'concept':
            output_dir = base_dir / "concepts_images"
        elif section_type == 'problem':
            output_dir = base_dir / "problems_images"
        else:
            output_dir = base_dir / "content_images"

    # 파일명 생성
    filename = f"{section_type}_p{page_num:03d}_{idx:02d}.png"
```

#### 옵션 2: book_conversion.py 수정
새 이미지 경로를 인식하도록 수정:

```python
# book_conversion.py에서 이미지 경로 추출 로직 수정
if ref.get('image_path'):
    # 파싱 단계에서 크롭한 이미지 경로 사용
    img_path = ref['image_path']
    # API 경로로 변환
    img_path = img_path.replace('backend/data/', '/api/data/')
    image_paths.append(img_path)
```

## 다음 작업

1. **이미지 경로 통합** (필수)
   - 섹션 이미지 저장 경로를 표준 경로로 변경
   - 또는 book_conversion.py에서 새 경로 인식

2. **섹션 이미지 → LearningUnit 연결** (필수)
   - books.py에서 section['image_path']를 pdf_references에 저장
   - book_conversion.py에서 이 경로를 Unit.image_path에 매핑

3. **이미지 제공 API** (선택)
   - `/api/v1/images/{path}` 엔드포인트 추가
   - 이미지 파일 다운로드 지원

4. **프론트엔드 통합** (마지막)
   - 학습 페이지 컴포넌트에서 이미지 표시
   - 이미지 로딩 상태 처리
   - 오류 처리

## 정리

현재까지 구현된 것:
- ✅ 섹션 이미지 자동 크롭 (파싱 단계)
- ✅ SectionData에 image_path 필드 추가
- ✅ 고품질 이미지 저장 (300 DPI PNG)

아직 필요한 것:
- ⏳ 이미지 경로 통합 (섹션 이미지 → Unit)
- ⏳ books.py에서 image_path를 pdf_references에 저장
- ⏳ 프론트엔드에서 이미지 표시

**다음 단계로 이미지 경로를 통합하면 학습 페이지에서 섹션 이미지를 바로 사용할 수 있게 됩니다!**
