# 커리큘럼 JSON 구조 및 학습 흐름

## 저장 위치

과목별로 폴더가 생성되어 저장됩니다:

```
data/
  └── curricula/
      ├── korean/          # 국어/문학 커리큘럼
      │   └── cur_xxx.json
      ├── math1/           # 수학1 커리큘럼
      │   └── cur_xxx.json
      └── english/          # 영어 커리큘럼
          └── cur_xxx.json
```

## JSON 구조

### 1. 기본 정보

```json
{
  "curriculum_id": "cur_xxx",
  "subject": "korean",
  "total_lessons": 44,
  "total_units": 427,
  "created_at": "2026-01-16T...",
  "lessons": [...],
  "learning_path": [...],
  "connections": [...],
  "learning_flow": {...}
}
```

### 2. 레슨 구조 (lessons)

각 레슨은 HWP 파일 하나에 해당합니다:

```json
{
  "lesson_number": 1,
  "title": "1강 [교과서_개념] 1, 2",
  "sections": [
    {
      "type": "ot",
      "content": "...",
      "paragraphs": [...]
    }
  ],
  "pdf_references": [
    {
      "type": "problem",
      "number": 1,
      "section": "concept"
    }
  ],
  "dependencies": [],
  "estimated_time": 25,
  "learning_units": [...]
}
```

### 3. 학습 단위 구조 (learning_units)

각 레슨 안의 학습 단위는 강의대본을 분석해서 생성됩니다:

```json
{
  "unit_index": 0,
  "section_type": "ot",
  "content": "여러분, 안녕하세요? 국어 영역 최선의 선택 최서희입니다...",
  "key_points": [
    "핵심 포인트 1",
    "핵심 포인트 2"
  ],
  "pdf_references": [
    {
      "type": "problem",
      "number": 1
    }
  ],
  "break_points": [
    {
      "section_type": "ot",
      "paragraph_index": 0,
      "text": "자, 그다음에...",
      "transition_type": "transition"
    }
  ]
}
```

### 4. 학습 경로 (learning_path)

레슨들의 학습 순서:

```json
[
  {
    "lesson": 0,
    "order": 1,
    "title": "0강 ot"
  },
  {
    "lesson": 1,
    "order": 2,
    "title": "1강 [교과서_개념] 1, 2"
  }
]
```

### 5. 레슨 간 연결 (connections)

레슨 간의 유기적 연결 관계:

```json
[
  {
    "from_lesson": 0,
    "to_lesson": 1,
    "type": "sequential",
    "keywords": ["교과서", "개념"]
  }
]
```

### 6. 학습 흐름 (learning_flow)

전체 학습 흐름 정보:

```json
{
  "overview": {
    "total_lessons": 44,
    "total_units": 427,
    "estimated_total_time": 2135
  },
  "sequence": [
    {
      "order": 1,
      "lesson_number": 0,
      "title": "0강 ot",
      "units": [
        {
          "unit_index": 0,
          "section_type": "ot",
          "content_preview": "여러분, 안녕하세요? 국어 영역 최선의 선택...",
          "key_points": [...],
          "pdf_references": [...]
        }
      ]
    }
  ],
  "lesson_details": {
    "0": {
      "title": "0강 ot",
      "estimated_time": 25,
      "unit_count": 5,
      "sections": [...],
      "dependencies": []
    }
  }
}
```

## 학습 흐름 예시

### 문학 커리큘럼 (44강)

1. **0강 (오리엔테이션)**
   - 학습 단위: 5개
   - 흐름: OT → 교과서 내용 → 정리

2. **1강 (교과서 개념 1, 2)**
   - 학습 단위: 5개
   - 흐름: OT → 교과서 내용 → 교과서 내용 → 정리 → 정리

3. **2강 (교과서 개념 3, 4)**
   - 학습 단위: 10개
   - 흐름: OT → OT → OT → 개념 → 정리 → 정리 → 정리 → 정리 → 교과서 내용 → 교과서 내용

...

## 학습 단위 타입

- `ot`: 오리엔테이션
- `textbook_content`: 교과서/본문 내용
- `summary`: 정리/요약
- `concept`: 개념 설명
- `problem`: 문제
- `example`: 예제
- `exercise`: 연습

## 사용 방법

1. **커리큘럼 생성**: HWP 파일 업로드 → JSON 자동 생성
2. **데이터 확인**: `data/curricula/{과목}/{curriculum_id}.json` 파일 확인
3. **학습 흐름 활용**: `learning_flow.sequence`를 통해 학습 순서 확인
