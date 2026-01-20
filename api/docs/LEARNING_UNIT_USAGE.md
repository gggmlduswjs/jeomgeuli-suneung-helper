# 학습 단위(LearningUnit) 사용 가이드

## 📋 개요

모든 과목(국어/수학/영어)에서 **공통 구조**를 사용하면서 **과목별 특성**을 반영하는 학습 단위 시스템입니다.

---

## ✅ 완료된 작업

1. ✅ **LearningUnit 모델 확장**
   - 점자/음성 필드 추가 (`braille_pattern`, `braille_text`, `tts_text`)
   - 공통 구조 필드 추가 (`learning_objective`, `key_content`, `learning_point`)
   - 과목별 확장 필드 추가 (`metadata` JSON)

2. ✅ **공통 스키마 정의**
   - 모든 과목이 동일한 필드 구조 사용
   - `api/app/schemas/learning_unit_types.py`에 과목별 타입 정의

3. ✅ **자동 분해 스크립트**
   - `api/scripts/create_learning_units.py`: 범용 학습 단위 생성 스크립트

4. ✅ **예시 구조 파일**
   - `api/data/unit_structures/math_1_unit_structure.json`: 수학 1강 구조
   - `api/data/unit_structures/english_1_unit_structure.json`: 영어 1강 구조

---

## 🚀 사용 방법

### 1. 구조 JSON 파일 준비

과목별 학습 단위 구조를 JSON 파일로 작성합니다.

**예시: `math_1_unit_structure.json`**

```json
[
  {
    "title": "Unit 1. 수학Ⅰ 전체 맵 이해",
    "section_type": "orientation",
    "keywords": ["수학Ⅰ", "전체", "맵"],
    "learning_objective": "수학Ⅰ 전체 흐름을 큰 지도로 이해한다",
    "key_content": "수학Ⅰ 교과서 3과 구조",
    "learning_point": "수학Ⅰ = 함수 중심 과목"
  },
  ...
]
```

### 2. 스크립트 실행

```bash
cd C:\Users\user\Desktop\jeomgeuli-suneung-helper\api

# 구조만 사용 (강의 대본 없음)
python scripts/create_learning_units.py lesson_xxx data/unit_structures/math_1_unit_structure.json

# 구조 + 강의 대본 (키워드 기반 분할)
python scripts/create_learning_units.py lesson_xxx data/unit_structures/math_1_unit_structure.json data/lecture_scripts/math_1.txt
```

### 3. 결과 확인

스크립트가 자동으로:
- ✅ 커리큘럼 생성/업데이트
- ✅ 학습 단위 생성 (공통 필드 자동 추출)
- ✅ 점자 패턴 생성
- ✅ TTS 텍스트 생성
- ✅ DB 저장

---

## 📚 과목별 section_type

### 국어 (KoreanSectionType)

```python
from app.schemas.learning_unit_types import KoreanSectionType

# 사용 가능한 타입
KoreanSectionType.ORIENTATION          # "orientation"
KoreanSectionType.CONCEPT_EXPRESSION   # "concept_expression"
KoreanSectionType.CONCEPT_FORM         # "concept_form"
KoreanSectionType.CONCEPT_CONTENT      # "concept_content"
KoreanSectionType.WORK_ANALYSIS        # "work_analysis"
KoreanSectionType.PROBLEM_SOLVING      # "problem_solving"
KoreanSectionType.SUMMARY              # "summary"
```

### 수학 (MathSectionType)

```python
from app.schemas.learning_unit_types import MathSectionType

# 사용 가능한 타입
MathSectionType.ORIENTATION            # "orientation"
MathSectionType.CONCEPT_DEFINITION     # "concept_definition"
MathSectionType.CONCEPT_APPLICATION    # "concept_application"
MathSectionType.GRAPH_INTERPRETATION   # "graph_interpretation"
MathSectionType.EQUATION_SOLVING       # "equation_solving"
MathSectionType.EXAMPLE                # "example"
MathSectionType.PROBLEM                # "problem"
MathSectionType.SUMMARY                # "summary"
```

### 영어 (EnglishSectionType)

```python
from app.schemas.learning_unit_types import EnglishSectionType

# 사용 가능한 타입
EnglishSectionType.ORIENTATION         # "orientation"
EnglishSectionType.STRATEGY            # "strategy"
EnglishSectionType.SIGNAL_EXPRESSION   # "signal_expression"
EnglishSectionType.LOGIC_CODE          # "logic_code"
EnglishSectionType.GATEWAY_PROBLEM     # "gateway_problem"
EnglishSectionType.PRACTICE_PROBLEM    # "practice_problem"
EnglishSectionType.VARIATION           # "variation"
EnglishSectionType.SUMMARY             # "summary"
```

---

## 🎯 점자 3셀 패턴

점자 3셀은 **내용 전달이 아닌 상태 전환 신호**로 사용합니다.

### 패턴 생성 규칙

```python
# section_type 기반 자동 생성
{
    "orientation": [1, 0, 0],
    "concept": [2, 0, 0],
    "example": [3, 0, 0],
    "problem": [4, 0, 0],
    "summary": [5, 0, 0],
}
```

### 사용 예시

```json
{
    "braille_pattern": "[1,2,3]",
    "braille_text": "⠼⠁ ⠛⠁⠝⠛ ⠊⠉⠓⠑"
}
```

---

## 📦 과목별 metadata 예시

### 국어

```json
{
    "metadata": {
        "work_title": "박두진의 '해'",
        "expression_type": "상징",
        "form_type": "자유시",
        "content_theme": "평화와 공존"
    }
}
```

### 수학

```json
{
    "metadata": {
        "concept": "거듭제곱근",
        "formula": "xⁿ = a",
        "graph_type": "n차 함수",
        "key_condition": "n의 짝·홀"
    }
}
```

### 영어

```json
{
    "metadata": {
        "question_type": "글의 목적",
        "signal_words": ["let me know", "I would like"],
        "logic_code": "전환",
        "problem_number": 18
    }
}
```

---

## 🔄 전체 워크플로우

```
1. 강의 대본 준비
   ↓
2. 학습 단위 구조 JSON 작성
   ↓
3. create_learning_units.py 실행
   ↓
4. 자동 생성:
   - 공통 필드 추출 (학습 목표, 핵심 내용, 학습 포인트)
   - 점자 패턴 생성
   - TTS 텍스트 생성
   - DB 저장
   ↓
5. 프론트엔드에서 사용
   - 점자 디스플레이 출력
   - TTS 재생
   - 학습 진행 추적
```

---

## 💡 장점

1. **공통 구조**: 모든 과목이 동일한 필드 구조 사용
2. **과목별 확장**: `section_type` + `metadata`로 특화
3. **점자/TTS 통합**: 앱에서 바로 사용 가능
4. **AI 자동 분해**: 구조화된 데이터로 프롬프트 작성 용이
5. **유지보수 용이**: 공통 로직은 한 곳에서 관리

---

## 📝 다음 단계

1. **AI 기반 필드 추출 개선**
   - 현재는 휴리스틱 기반
   - OpenAI API로 `learning_objective`, `key_content`, `learning_point` 자동 추출

2. **점자 변환 개선**
   - 현재는 간단한 패턴 매핑
   - 실제 점자 변환 라이브러리 연동

3. **TTS 텍스트 최적화**
   - 현재는 첫 200자
   - 과목별 전략에 맞는 요약 생성

4. **프론트엔드 연동**
   - `LearningUnit` 데이터를 앱에서 표시
   - 점자 디스플레이 출력
   - TTS 재생
