# 학습 단위(LearningUnit) 공통 스키마

## 📋 개요

모든 과목(국어/수학/영어)에서 공통으로 사용하는 학습 단위 구조입니다.
과목별 특성은 `section_type`과 `metadata` 필드로 확장합니다.

---

## 🔹 공통 필드 구조

### 필수 필드

```python
{
    "unit_id": "string (PK)",
    "curriculum_id": "string (FK)",
    "lesson_id": "string (FK, optional)",
    "section_type": "string",  # 과목별 타입
    "content": "string",  # 전체 내용 텍스트
    "order": "integer"  # 순서
}
```

### 공통 구조 필드 (과목 공통)

```python
{
    "title": "string (optional)",  # 예: "Unit 1. 수학Ⅰ 전체 맵 이해"
    "learning_objective": "string (optional)",  # 학습 목표
    "key_content": "string (optional)",  # 핵심 내용
    "learning_point": "string (optional)"  # 학습 포인트
}
```

### 점자/음성 지원 필드

```python
{
    "braille_pattern": "string (JSON, optional)",  # [1,2,3] - 점자 3셀 패턴
    "braille_text": "string (optional)",  # 점자 변환 결과 (전체)
    "tts_text": "string (optional)"  # TTS용 요약 텍스트
}
```

### 분할 및 참조 필드

```python
{
    "break_points": "string (JSON, optional)",  # ["자, 그다음에...", "먼저..."]
    "pdf_references": "string (JSON, optional)",  # [{"type": "problem", "number": 1}]
    "metadata": "string (JSON, optional)"  # 과목별 확장 정보
}
```

---

## 📚 과목별 section_type

### 국어 (KoreanSectionType)

- `orientation`: 강의 오리엔테이션
- `concept_expression`: 시의 표현 개념
- `concept_form`: 시의 형식 개념
- `concept_content`: 시의 내용 개념
- `work_analysis`: 작품 분석
- `problem_solving`: 문제 풀이
- `summary`: 정리

### 수학 (MathSectionType)

- `orientation`: 강의 오리엔테이션
- `concept_definition`: 개념 정의
- `concept_application`: 개념 적용
- `graph_interpretation`: 그래프 해석
- `equation_solving`: 방정식 풀이
- `example`: 예제
- `problem`: 문제
- `summary`: 정리

### 영어 (EnglishSectionType)

- `orientation`: 강의 오리엔테이션
- `strategy`: 전략 설명
- `signal_expression`: 핵심 표현(시그널)
- `logic_code`: 논리 코드
- `gateway_problem`: Gateway 문제
- `practice_problem`: 실전 문제
- `variation`: 변형 출제
- `summary`: 정리

---

## 🎯 점자 3셀 패턴 (braille_pattern)

점자 3셀은 **내용 전달이 아닌 상태 전환 신호**로 사용합니다.

### 예시

```json
{
    "braille_pattern": "[1,2,3]",  // 셀 1,2,3에 점자 패턴
    "braille_text": "⠼⠁ ⠛⠁⠝⠛ ⠊⠉⠓⠑"  // 전체 점자 텍스트
}
```

### 과목별 점자 전략

- **국어**: 문장 단위, 작품 제목/핵심 표현
- **수학**: 수식 단위, 개념 키워드
- **영어**: 단어 단위, 시그널 표현

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

## 🔄 사용 흐름

1. **강의 대본 입력** → `split_lesson_script.py`
2. **과목별 구조 분석** → `section_type` 자동 할당
3. **공통 필드 추출** → `learning_objective`, `key_content`, `learning_point`
4. **점자 변환** → `braille_pattern`, `braille_text`
5. **TTS 생성** → `tts_text`
6. **DB 저장** → `LearningUnit` 생성

---

## ✅ 장점

1. **공통 구조**: 모든 과목이 동일한 필드 구조 사용
2. **과목별 확장**: `section_type` + `metadata`로 특화
3. **점자/TTS 통합**: 앱에서 바로 사용 가능
4. **AI 자동 분해**: 구조화된 데이터로 프롬프트 작성 용이
