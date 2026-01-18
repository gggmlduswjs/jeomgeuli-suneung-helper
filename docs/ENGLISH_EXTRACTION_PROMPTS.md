# 수능특강 영어 PDF 추출·파싱 프롬프트 세트

이 문서는 **Cursor에 복붙해서 바로 사용할 수 있는 프롬프트**입니다.

---

## ✅ 0️⃣ Cursor 시스템 프롬프트 (맨 위 고정)

**파일:** `.cursorrules` 또는 프로젝트 설정

```text
너는 수능특강 영어 PDF를 분석하는 시니어 백엔드 엔지니어다.

이 시스템의 목적은:
- PDF를 단순히 읽는 것이 아니라
- 시각장애 수험생을 위한 교육 콘텐츠로 구조화하는 것이다

출력 결과는 반드시 다음을 만족해야 한다:
1. 지문(passage)과 문제(question)를 명확히 분리
2. 문제 유형(type)을 자동 분류
3. 시험 모드 / 음성 모드 / 점자 모드에서 바로 사용 가능
4. 중간 결과는 사람이 검증 가능한 JSON 형태

절대 하지 말 것:
- 지문과 문제를 하나의 텍스트로 합치기
- 빈칸, 삽입 위치를 제거하기
- 문장을 임의로 합치거나 분리하기
```

---

## ✅ 1️⃣ 영어 과목 전용 파서 생성 프롬프트 (핵심)

**파일:** `api/app/services/subject_strategies/english.py`

### Cursor 프롬프트:

```text
수능특강 영어 PDF 추출 결과(JSON)를
교육용 콘텐츠 구조로 변환하는 영어 전용 파서를 작성해줘.

입력 데이터 형식:
{
  "page": number,
  "lines": [
    { "text": string, "bbox": [x1, y1, x2, y2] }
  ]
}

수능특강 영어의 특징:
- 지문(passage)은 연속된 문장 블록이다
- 문제는 지문 이후에 나온다
- 문제 유형은 다음 중 하나다:
  - 빈칸 추론 (___)
  - 순서 배열 (A, B, C)
  - 문장 삽입 (① 위치)
  - 주제 / 요지
- 보기는 ①②③④⑤ 형태다

파싱 규칙:
1. 지문은 sentence 배열로 분리한다
2. 문제는 passage_id를 참조한다
3. 빈칸은 반드시 ___ placeholder로 유지한다
4. 문제 유형(type)을 자동으로 분류한다
5. 보기(choice)는 순서 보존

출력 JSON 형식:
{
  "subject": "english",
  "passage": {
    "id": "ENG-01",
    "sentences": [ "...", "..." ]
  },
  "questions": [
    {
      "id": "ENG-01-Q1",
      "type": "blank | ordering | insertion | main_idea",
      "question": "...",
      "choices": [ { "label": "①", "text": "..." } ]
    }
  ]
}

EnglishParser 클래스로 작성해줘.
```

**이 프롬프트 하나로 `english_parser.py`가 나와야 정상**

---

## ✅ 2️⃣ 문제 유형 자동 분류 로직 프롬프트

**함수:** `detect_english_question_type()`

### Cursor 프롬프트:

```text
수능특강 영어 문제 유형을 자동 분류하는 함수를 작성해줘.

분류 규칙:
- 빈칸 추론:
  - 지문 또는 문제에 ___ 포함
- 순서 배열:
  - (A), (B), (C) 또는 문장 나열 언급
- 문장 삽입:
  - 삽입 위치 ①②③④⑤ 언급
- 주제/요지:
  - main idea, topic, title 등
- 그 외는 general

함수 시그니처:
def detect_english_question_type(text: str) -> str

반환값:
"blank" | "ordering" | "insertion" | "main_idea" | "detail" | "general"

정규식 기반으로 구현해줘.
```

---

## ✅ 3️⃣ 지문(sentence) 분리 프롬프트

**함수:** `split_english_sentences()`

### Cursor 프롬프트:

```text
영어 지문을 sentence 단위로 분리하는 로직을 작성해줘.

조건:
- 마침표(.), 물음표(?) 기준
- 약어(Mr., etc.)는 분리하지 않는다
  - Mr., Mrs., Ms., Dr., Prof.
  - etc., e.g., i.e., vs., U.S.
  - Inc., Ltd., Co., St., Ave.
- 빈칸 ___ 은 문장 내부에 유지한다

함수 시그니처:
def split_english_sentences(passage_text: str) -> List[str]

반환값:
List[str]: 문장 리스트 (순수 텍스트)

예시:
입력: "Mr. Smith went to the U.S. He said hello."
출력: ["Mr. Smith went to the U.S.", "He said hello."]
```

---

## ✅ 4️⃣ 영어 보기(choice) 묶기 프롬프트

**함수:** `group_english_choices()`

### Cursor 프롬프트:

```text
수능특강 영어 문제의 보기를 묶는 로직을 작성해줘.

조건:
- 보기 기호는 반드시 ①②③④⑤ 유지
- 보기 순서는 변경하지 않는다
- 다른 문제의 보기와 섞이지 않게 한다

함수 시그니처:
def group_english_choices(lines: List[Dict[str, Any]]) -> List[Dict[str, Any]]

입력:
- lines: 줄 리스트 (text 필드 포함)

반환값:
List[Dict] where Dict has:
  - label: str (①, ② 등)
  - text: str
  - index: int (0-based)
  - char_count: int (optional)
  - word_count: int (optional)
```

---

## ✅ 5️⃣ 영어 과목 최종 콘텐츠 JSON 스키마 프롬프트

**파일:** `api/app/services/subject_strategies/english_schema.py`

### Cursor 프롬프트:

```text
수능특강 영어 한 지문 단위를
시험 모드 / 음성 모드 / 점자 모드에서 공통 사용 가능한
최종 JSON 스키마로 정의해줘.

필수 필드:
- subject: "english"
- passage_id: 지문 고유 ID (예: "ENG-01-P01")
- sentences[]: 문장 배열
- questions[]: 문제 배열
  - question_id: 문제 고유 ID (예: "ENG-01-Q01")
  - type: 문제 유형 (blank, ordering, insertion 등)
  - question: 문제 본문
  - choices[]: 보기 배열

실제 예시 JSON을 포함해서 출력해줘.

Pydantic BaseModel로 스키마를 정의하고,
예시 JSON도 함께 제공해줘.
```

---

## 🔥 이 프롬프트 세트가 "완성본"인 이유

### ✅ 영어 문제 유형 분기까지 포함

```python
# 자동 분류
question_type = parser.detect_english_question_type(question_text)
# "blank" | "ordering" | "insertion" | "main_idea" | "general"
```

### ✅ 빈칸 / 삽입 / 순서 → 시험 UX 그대로 반영

```json
{
  "question_type": "blank",
  "question": "다음 빈칸에 들어갈 말은?",
  "passage": {
    "sentences": [
      "Some sentences may contain ___ that need to be filled in."
    ],
    "placeholders": [
      {"position": 168, "type": "blank", "context": "contain ___ that"}
    ]
  }
}
```

### ✅ 영어 → 음성 출력 시 sentence 단위 읽기 가능

```python
# sentence 단위로 TTS
for sentence in passage["sentences"]:
    tts.speak(sentence)
```

### ✅ 점자 → 문장 단위 스트립 분리 가능

```python
# 각 sentence를 점자 스트립으로 변환
for sentence in passage["sentences"]:
    braille_strip = convert_to_braille(sentence)
```

---

## 🚀 실제 사용 예시

### 전체 파이프라인 실행

```python
from pathlib import Path
from app.services.subject_strategies.english import EnglishParser
from app.services.pdf_extract.literature_extractor import LiteraturePDFExtractor

# Step 1: 추출 (줄 단위)
extractor = LiteraturePDFExtractor()  # 문학과 동일 (텍스트 중심)
lines = extractor.extract_blocks(Path("english.pdf"))

# Step 2: 파싱 (지문/문제 분리 + 문장 단위 분리)
parser = EnglishParser()
result = parser.parse(lines, metadata={"book_id": "bk_eng_2026"})
```

### 문제 유형 자동 분류 테스트

```python
parser = EnglishParser()

test_questions = [
    "다음 빈칸에 들어갈 말은?",
    "다음 문장들의 순서를 배열하면?",
    "다음 문장이 들어갈 위치는?",
    "이 글의 주제는?",
    "일반 문제",
]

for q in test_questions:
    q_type = parser.detect_english_question_type(q)
    print(f"{q_type}: {q}")
```

### 문장 분리 테스트

```python
parser = EnglishParser()

text = "Mr. Smith went to the U.S. He said hello. Dr. Lee is a Prof. at Harvard."
sentences = parser.split_english_sentences(text)

for sent in sentences:
    print(f"- {sent}")
# 출력:
# - Mr. Smith went to the U.S.
# - He said hello.
# - Dr. Lee is a Prof. at Harvard.
```

---

## 📊 최종 JSON 구조

```json
{
  "version": "1.0",
  "subject": "english",
  "passages": [
    {
      "passage_id": "ENG-01-P01",
      "sentences": [
        "The quick brown fox jumps over the lazy dog.",
        "Some sentences may contain ___ that need to be filled in."
      ],
      "placeholders": [
        {"position": 168, "type": "blank", "context": "contain ___ that"}
      ]
    }
  ],
  "questions": [
    {
      "question_id": "ENG-01-Q01",
      "question_type": "blank",
      "passage_id": "ENG-01-P01",
      "question": "다음 빈칸에 들어갈 말로 가장 적절한 것은?",
      "choices": [
        {"label": "①", "text": "words", "index": 0}
      ]
    }
  ]
}
```

---

## 🎯 점글이 구조와의 연결

### 시각장애 수능 영어 UX

1. **지문 먼저 읽기**
   - Sentence 단위로 TTS 제공
   - 빈칸(___)은 "빈칸" 또는 건너뛰기
   - 사용자가 지문 완전히 읽을 시간 제공

2. **문제 풀기**
   - 문제 유형별 맞춤 UX
   - **빈칸 추론**: 보기 순서대로 재생
   - **순서 배열**: 문장 재배열 인터페이스
   - **삽입**: 위치 선택 인터페이스

3. **구조의 장점**
   - `passage_id`로 지문과 문제 자동 연결
   - `question_type`으로 맞춤 UX 제공
   - `sentences[]`로 문장 단위 처리 가능

---

## 🎯 다음 단계

1. **실제 PDF 1페이지 기준 분석**
   - "이 블록이 이 JSON으로 변환된다" 실사례

2. **영어 듣기(청취) 문항까지 확장 설계**
   - 듣기 지문 구조 추가

3. **영어 → 국어/문학 공통 추상 파서 통합**
   - 둘 다 passage-based 구조
   - 공통 인터페이스 설계
