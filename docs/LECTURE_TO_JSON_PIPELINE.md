# 강의 대본 → 구조화된 JSON 파이프라인

## 개요

EBS 수능특강 강의 대본을 학습 시스템에서 바로 사용 가능한 구조화된 JSON 형식으로 변환하는 파이프라인입니다.

## 출력 형식

```json
{
  "subject": "korean | math | english",
  "lessonId": "subject_nn",
  "title": "레슨 제목",
  "order": number,
  "sections": [
    {
      "sectionId": "subject_nn_mm",
      "title": "섹션 제목",
      "units": [
        {
          "unitId": "subject_nn_mm_uX",
          "type": "intro | concept | definition | example | notation | problem_intro | summary | outro",
          "content": "학습 내용 텍스트"
        }
      ]
    }
  ]
}
```

## Unit Type 정의

- `intro`: 레슨 도입, 학습 방향 제시
- `concept`: 개념 설명
- `definition`: 수학·용어 정의
- `example`: 예시 설명
- `notation`: 기호, 표현 정리
- `problem_intro`: 문제 풀이로 넘어가기 전 설명
- `summary`: 정리
- `outro`: 다음 강의 예고

## 사용 방법

### 1. 단일 파일 처리

```python
from pathlib import Path
from app.services.lecture_to_json_pipeline import LectureToJSONPipeline

# 파이프라인 생성
pipeline = LectureToJSONPipeline(subject='literature')

# 파일 처리
json_data = pipeline.process_lecture_file(
    Path('data/lecture_scripts/수능특강_문학_2026/1강.hwp')
)

# JSON 저장
import json
with open('output.json', 'w', encoding='utf-8') as f:
    json.dump(json_data, f, ensure_ascii=False, indent=2)
```

### 2. 텍스트 직접 처리

```python
script_text = """
여러분, 안녕하세요? 국어 영역 최선의 선택 최서희입니다...
"""

pipeline = LectureToJSONPipeline(subject='literature')
json_data = pipeline.process_lecture_text(script_text, lesson_number=1)
```

### 3. 디렉토리 일괄 처리 (CLI)

```bash
# 문학 강의 대본 처리
python api/scripts/process_lecture_scripts.py \
  --subject literature \
  --input data/lecture_scripts/수능특강_문학_2026 \
  --output data/parsed/literature

# 수학Ⅰ 강의 대본 처리
python api/scripts/process_lecture_scripts.py \
  --subject math1 \
  --input data/lecture_scripts/수능특강_수1_2026 \
  --output data/parsed/math1
```

## 처리 과정

1. **파일 읽기**: HWP 또는 TXT 파일에서 텍스트 추출
2. **강의 번호 추출**: 파일명 또는 내용에서 강의 번호 추출
3. **강의 대본 파싱**: 섹션별로 분류 (OT, 개념, 예제, 정리 등)
4. **문학 과목 구조화**: 인트로, 본문, 문제 1, 문제 2 형식으로 구조화
5. **학습 단위 생성**: TTS 읽기 적합한 길이로 분할
6. **내용 정제**: 
   - 불필요한 강사 멘트 제거
   - 구어체를 문어체로 변환
   - 반복/강조 표현 정리
7. **JSON 구조 생성**: 목표 형식에 맞게 변환

## 내용 정제 규칙

다음 패턴들이 자동으로 제거/변환됩니다:

- 제거: "여러분,", "알겠지?", "맞죠?", "자,", "그래서요" 등
- 변환: "~거든요" → "~입니다", "~해요" → "~합니다"
- 정리: 불필요한 공백, 반복 표현

## 출력 예시

### 문학 강의

```json
{
  "subject": "korean",
  "lessonId": "korean_01",
  "title": "1강 시의 표현과 형식",
  "order": 1,
  "sections": [
    {
      "sectionId": "korean_01_00",
      "title": "인트로",
      "units": [
        {
          "unitId": "korean_01_00_u1",
          "type": "intro",
          "content": "2026 수능특강 최서희의 문학 1강이 시작되었습니다..."
        }
      ]
    },
    {
      "sectionId": "korean_01_01",
      "title": "본문",
      "units": [
        {
          "unitId": "korean_01_01_u1",
          "type": "concept",
          "content": "형상화는 정서나 교훈, 삶의 이치 등과 같이 분명한 형체로 나타나 있지 않은 것을 구체적이고 실감나게 그려내는 것입니다..."
        }
      ]
    },
    {
      "sectionId": "korean_01_02",
      "title": "문제 1",
      "units": [
        {
          "unitId": "korean_01_02_u1",
          "type": "problem_intro",
          "content": "1번 문제를 살펴보겠습니다..."
        }
      ]
    }
  ]
}
```

### 수학Ⅰ 강의

```json
{
  "subject": "math",
  "lessonId": "math_01",
  "title": "1강 지수와 로그",
  "order": 1,
  "sections": [
    {
      "sectionId": "math_01_00",
      "title": "오리엔테이션",
      "units": [
        {
          "unitId": "math_01_00_u1",
          "type": "intro",
          "content": "수학Ⅰ 전체 구조는 함수 중심입니다..."
        }
      ]
    },
    {
      "sectionId": "math_01_01",
      "title": "개념",
      "units": [
        {
          "unitId": "math_01_01_u1",
          "type": "definition",
          "content": "a의 n제곱근은 x^n = a를 만족하는 x입니다..."
        }
      ]
    }
  ]
}
```

## 주의사항

- 강의 내용의 의미는 유지됩니다
- 문제 푸는 사고 흐름은 보존됩니다
- 시각장애인 학습에 적합하도록 단계적이고 명시적으로 구성됩니다
- 문장 간 인과 관계가 분명하게 유지됩니다
