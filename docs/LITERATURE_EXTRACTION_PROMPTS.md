# 수능특강 문학 PDF 추출·파싱 프롬프트 세트

이 문서는 **Cursor에 복붙해서 바로 사용할 수 있는 프롬프트**입니다.

---

## 🔴 수능특강 문학의 본질

### ❌ 수학과의 차이

| 항목 | 수학Ⅰ | 문학 |
|------|-------|------|
| 핵심 요소 | 수식 이미지 | 텍스트 |
| 주요 단위 | 문제 | 지문 |
| 추출 난이도 | 이미지 처리 | 텍스트 분리 |
| 파싱 포인트 | 보기 묶기 | 지문 경계 |
| 점자 핵심 | 수식 (Nemeth) | 문장 흐름 |

### ✅ 문학 고정 구조

```
[갈래 / 작가 / 작품명]
<지문>
────────────────
[문제 1]
[문제 2]
[문제 3]
```

또는

```
[보기]
<지문>
────────────────
[문제]
```

**핵심 원칙:** 지문과 문제를 절대 섞으면 안 됨

---

## 1️⃣ Cursor 시스템 프롬프트 (문학 전용)

**파일:** `.cursorrules` 또는 프로젝트 설정

```text
너는 수능특강 국어 문학 PDF를 파싱하는 엔지니어다.

문학 PDF의 특징:
- 지문은 연속된 텍스트 블록이다
- 문제는 지문 이후에 나온다
- 보기 / 문제 / 선택지가 명확히 구분된다
- 수식이나 그래프는 거의 없다

중요 원칙:
1. 지문은 하나의 passage로 묶는다
2. 문제 텍스트는 절대 지문에 섞지 않는다
3. 문제는 지문 ID를 참조한다
4. 추출 단계에서는 의미 해석을 하지 않는다
5. 줄 단위 구조를 유지한다
```

---

## 2️⃣ 문학 PDF 추출 전용 프롬프트

**파일:** `api/app/services/pdf_extract/literature_extractor.py`

### Cursor 프롬프트:

```text
수능특강 문학 PDF에서
페이지 단위로 텍스트를 줄 단위로 추출하는 코드를 작성해줘.

조건:
- pdfplumber 사용
- 텍스트는 줄 단위로 추출
- 줄 순서(y좌표 기준)를 유지
- 이미지 블록은 무시해도 된다 (문학은 텍스트 중심)
- 절대 문장 합치기나 줄 정리를 하지 않는다

출력 형식:
{
  "type": "text",
  "page": number,
  "text": string,
  "bbox": [x1, y1, x2, y2],
  "line_number": number
}

LiteraturePDFExtractor 클래스로 작성해줘.
```

**이 단계는 "글자 그대로 뜯어오기"** (교육 로직 ❌)

---

## 3️⃣ 문학 핵심 파서 프롬프트 (지문 분리)

**파일:** `api/app/services/subject_strategies/literature.py`

### Cursor 프롬프트:

```text
수능특강 문학 PDF 추출 결과를
지문(passage)과 문제(question)로 분리하는 파서를 작성해줘.

문학 규칙:
- 지문은 문제 번호가 나오기 전까지의 텍스트다
- 문제는 숫자 + 문장으로 시작한다
- "①②③④⑤"는 보기다
- 지문이 여러 페이지에 걸쳐 있을 수 있다
- 지문과 문제를 절대 섞지 않는다

출력 구조:
{
  "subject": "literature",
  "passages": [
    {
      "passage_id": "LIT-01-P01",
      "title": "작품명",
      "text": "...",
      "page_start": 1,
      "page_end": 1
    }
  ],
  "questions": [
    {
      "question_id": "LIT-01-Q01",
      "passage_id": "LIT-01-P01",
      "question_text": "...",
      "choices": []
    }
  ]
}

LiteratureParser 클래스로 구현해줘.
```

---

## 4️⃣ 문학 지문 시작 감지 프롬프트

**함수:** `is_literature_passage_line()`

### Cursor 프롬프트:

```text
문학 PDF에서 지문 시작을 감지하는 함수를 작성해줘.

지문 시작 신호:
- [작품명/갈래/작가] 패턴
- <보기> 또는 "보기" 텍스트
- 작품명(작가) 형식
- 작가: 이름 패턴

함수 시그니처:
def is_literature_passage_line(text: str) -> bool

정규식 기반으로 구현해줘.
```

---

## 5️⃣ 문학 문제 감지 프롬프트

**함수:** `is_literature_question_start()`

### Cursor 프롬프트:

```text
문학 문제 시작을 감지하는 함수를 작성해줘.

문제 시작 패턴:
- ^\d+\. (예: "1.")
- ^다음\s*중
- ^윗글을
- ^이\s*작품
- ^다음\s*[가-힣]*\s*으로\s*가장

함수 시그니처:
def is_literature_question_start(text: str) -> bool

첫 줄의 시작 부분만 확인해줘.
```

---

## 6️⃣ 문학 콘텐츠 최종 JSON 스키마 프롬프트

**파일:** `api/app/services/subject_strategies/literature_schema.py`

### Cursor 프롬프트:

```text
수능특강 문학 한 지문 단위를 표현하는 JSON 스키마를 정의해줘.

필수 필드:
- subject: "literature"
- passage_id: 지문 고유 ID (예: "LIT-01-P01")
- title: 작품명/제목
- text: 지문 전체 텍스트
- questions[]: 문제 배열
  - question_id: 문제 고유 ID (예: "LIT-01-Q01")
  - passage_id: 참조하는 지문 ID
  - question_text: 문제 본문
  - choices[]: 보기 배열

실제 예시 JSON을 포함해서 출력해줘.

Pydantic BaseModel로 스키마를 정의하고,
예시 JSON도 함께 제공해줘.
```

---

## 🔥 수학 vs 문학 구조 비교

### 핵심 차이점

| 항목 | 수학Ⅰ | 문학 |
|------|-------|------|
| **핵심 단위** | 문제 | 지문 |
| **추출 난이도** | 수식 이미지 | 텍스트 분리 |
| **파싱 포인트** | 보기 묶기 | 지문 경계 |
| **점자 핵심** | 수식 (Nemeth) | 문장 흐름 |
| **음성 출력** | 문제 중심 | 지문 먼저, 문제 나중 |

### 구조 비교

**수학Ⅰ:**
```json
{
  "items": [
    {"type": "concept", ...},
    {"type": "question", "formula_images": [...]}
  ]
}
```

**문학:**
```json
{
  "passages": [
    {"passage_id": "LIT-01-P01", "text": "..."}
  ],
  "questions": [
    {"question_id": "LIT-01-Q01", "passage_id": "LIT-01-P01", ...}
  ]
}
```

---

## 🚀 실제 사용 예시

### 전체 파이프라인 실행

```python
from pathlib import Path
from app.services.pdf_extract.literature_extractor import LiteraturePDFExtractor
from app.services.subject_strategies.literature import LiteratureParser

# Step 1: 추출 (줄 단위)
extractor = LiteraturePDFExtractor()
lines = extractor.extract_blocks(Path("literature.pdf"))

# Step 2: 파싱 (지문/문제 분리)
parser = LiteratureParser()
result = parser.parse(lines, metadata={"book_id": "bk_lit_2026"})
```

### 지문 시작 감지 테스트

```python
parser = LiteratureParser()

test_texts = [
    "[갈래: 시 | 작가: 신라]",
    "<보기>",
    "황조가(신라)",
    "작가: 김동인",
    "일반 텍스트",
]

for text in test_texts:
    is_passage = parser.is_literature_passage_line(text)
    print(f"{'✅ 지문' if is_passage else '❌ 아님'}: {text}")
```

---

## 📊 최종 JSON 구조

```json
{
  "version": "1.0",
  "subject": "literature",
  "passages": [
    {
      "passage_id": "LIT-01-P01",
      "title": "황조가",
      "text": "철령 이화 우는 수이건...",
      "page_start": 1,
      "page_end": 1
    }
  ],
  "questions": [
    {
      "question_id": "LIT-01-Q01",
      "passage_id": "LIT-01-P01",
      "question_text": "다음 시의 화자의 심정으로...",
      "choices": [
        {"number": "①", "text": "...", "index": 0}
      ]
    }
  ]
}
```

---

## 🎯 점글이 구조와의 연결

### 시각장애 수능 UX

1. **지문 먼저 읽기**
   - Passage 전체 텍스트를 점자/음성으로 제공
   - 사용자가 지문을 완전히 읽을 시간 제공

2. **문제 풀기**
   - 지문 읽기 완료 후 문제 시작
   - 한 문항씩 포커스
   - 보기는 음성으로 순차 재생

3. **구조의 장점**
   - `passage_id`로 지문과 문제 자동 연결
   - 여러 문제가 한 지문을 참조 가능
   - 페이지 범위 정보로 스킵 가능

---

## 🎯 다음 단계

1. **실제 PDF 1페이지 기준 분석**
   - "이 블록이 이 JSON으로 변환된다" 실사례

2. **문학 → 영어 독해 공통 파서 통합**
   - 둘 다 passage-based 구조
   - 공통 인터페이스 설계

3. **문학 음성 시험 모드 UX 설계**
   - 지문 먼저 TTS
   - 문제별 포커스
