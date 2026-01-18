# 수능특강 수학Ⅰ PDF 추출·파싱 프롬프트 세트

이 문서는 **Cursor에 복붙해서 바로 사용할 수 있는 프롬프트**입니다.

---

## 🎯 전제: 수능특강 수학Ⅰ의 고정 구조

수학Ⅰ은 다른 과목과 달리 **형식이 거의 고정**되어 있습니다.

### 📘 수능특강 수학Ⅰ 한 단원 공통 패턴

```
01 지수
 ├─ 개념
 │   ├─ 정의 문장
 │   ├─ 성질 (●, ▶, (1)(2))
 │   └─ 대표 수식
 ├─ 예제
 │   ├─ 문제
 │   └─ 풀이
 └─ 유제
     ├─ 문제
     └─ 보기 (①~⑤)
```

---

## 1️⃣ Cursor 시스템 프롬프트 (필수)

**파일:** `.cursorrules` 또는 프로젝트 설정

```text
너는 수능특강 수학Ⅰ PDF를 분석하는 백엔드 엔지니어다.

이 PDF는 다음 특징을 가진다:
- 개념 / 예제 / 유제로 구성된다
- 수식은 텍스트가 아닌 이미지 또는 벡터다
- 문제 번호, 보기 기호(①②③④⑤), 수식은 반드시 분리해야 한다
- 결과는 점자 변환 및 음성 시험 모드에 사용된다

중요 규칙:
1. PDF 추출 단계에서는 의미 해석을 하지 않는다
2. 구조 해석 단계에서만 수학Ⅰ 규칙을 적용한다
3. 중간 결과는 JSON으로 저장한다
4. 수식은 절대 텍스트로 변환하지 않고 이미지로 유지한다
```

---

## 2️⃣ 수학Ⅰ PDF 추출 전용 프롬프트

**파일:** `api/app/services/pdf_extract/math1_extractor.py`

### Cursor 프롬프트:

```text
수능특강 수학Ⅰ PDF에서
페이지 단위로 모든 요소를 추출하는 코드를 작성해줘.

조건:
- pdfplumber를 사용한다
- 텍스트 블록은 좌표(bbox)와 raw 텍스트를 유지한다
- 수식, 그래프, 표는 이미지로 추출한다
- 절대 문장 합치기나 줄 정리를 하지 않는다
- 추출 단계에서는 의미 해석을 하지 않는다

출력 형식:
{
  "page": number,
  "blocks": [
    {
      "type": "text" | "image",
      "bbox": [x1, y1, x2, y2],
      "raw": string | null,
      "image_path": string | null
    }
  ]
}

Math1PDFExtractor 클래스로 작성해줘.
```

**이 단계 결과는 "PDF 원본의 디지털 복사본"임** (교육 로직 ❌)

---

## 3️⃣ 수학Ⅰ 구조 파싱 핵심 프롬프트 (가장 중요)

**파일:** `api/app/services/subject_strategies/math1.py`

### Cursor 프롬프트:

```text
수능특강 수학Ⅰ PDF 추출 결과(JSON)를
교육 콘텐츠 구조로 변환하는 파서를 작성해줘.

수학Ⅰ 고유 규칙:
- "개념", "예제", "유제"는 섹션이다
- 문제는 숫자 또는 "다음 중"으로 시작한다
- 보기는 ①②③④⑤ 패턴이다
- 수식은 image 블록 중 중앙 정렬 + 특정 크기 비율을 가진다

변환 규칙:
1. 개념 → concept 객체
2. 예제/유제 → question 객체
3. 보기는 choices 배열로 묶는다
4. 수식은 formula_images 배열로 관리한다

출력 JSON 예:
{
  "subject": "math1",
  "section": "concept" | "example" | "exercise",
  "items": [
    {
      "type": "concept",
      "text": "...",
      "formulas": []
    },
    {
      "type": "question",
      "id": "M1-01-03",
      "body": "",
      "choices": [],
      "formula_images": []
    }
  ]
}

Math1Parser 클래스로 구현해줘.
```

---

## 4️⃣ 수학Ⅰ 문제 감지 로직 전용 프롬프트

**함수:** `is_math1_question_start()`

### Cursor 프롬프트:

```text
수학Ⅰ PDF에서 문제 시작을 감지하는 함수를 작성해줘.

조건:
- 다음 패턴을 문제 시작으로 본다
  - ^\d+\. (예: "1.")
  - ^예제\s*\d+
  - ^유제\s*\d+
  - ^다음\s+중

함수 시그니처:
def is_math1_question_start(text: str) -> bool

정규식 기반으로 구현하고, 각 줄의 시작 부분만 확인해줘.
```

---

## 5️⃣ 보기(①②③④⑤) 묶기 프롬프트

**함수:** `group_math1_choices()`

### Cursor 프롬프트:

```text
수학Ⅰ 문제에서 보기(①②③④⑤)를
하나의 choices 배열로 묶는 로직을 작성해줘.

조건:
- 보기 기호는 반드시 유지한다
- y좌표 기준으로 정렬한다
- 다른 문제의 보기와 섞이지 않도록 한다
- ①②③④⑤ 패턴과 (1), (2) 패턴 모두 지원한다

함수 시그니처:
def group_math1_choices(blocks: List[Dict[str, Any]]) -> List[Choice]

반환 타입:
List[Dict] where Dict has:
  - number: str (①, ② 등)
  - text: str
  - index: int (0-based)
  - bbox: List[float]
  - page: int
```

---

## 6️⃣ 최종 수학Ⅰ 콘텐츠 JSON 스키마 프롬프트

**파일:** `api/app/services/subject_strategies/math1_schema.py`

### Cursor 프롬프트:

```text
수능특강 수학Ⅰ 한 문제를
점자·음성·시험 모드에서 공통으로 사용할 JSON 스키마를 정의해줘.

필수 필드:
- subject: "math1"
- chapter: 단원 번호 (예: "01", "02")
- section: "concept" | "example" | "exercise"
- question_id: 고유 ID (예: "M1-01-EX-01")
- body: 문제 본문
- choices: 보기 배열
- formula_images: 수식 이미지 배열
- difficulty: 난이도 (optional)

실제 예시 JSON을 포함해서 출력해줘.

Pydantic BaseModel로 스키마를 정의하고,
예시 JSON도 함께 제공해줘.
```

---

## 🔥 실제 사용 예시

### 전체 파이프라인 실행

```python
from pathlib import Path
from app.services.pdf_parse.parse_pipeline import ParsePipeline

pipeline = ParsePipeline()

result = pipeline.run(
    pdf_path=Path("data/pdfs/2026 수능특강 수학Ⅰ.pdf"),
    subject="MATH",  # 또는 "MATH1"로 확장
    book_id="bk_math1_2026",
    metadata={"year": 2026, "chapter": "01"}
)
```

### 수학Ⅰ 전용 파서 사용

```python
from app.services.subject_strategies.math1 import Math1Parser
from app.services.pdf_extract.pdfplumber_extractor import PDFPlumberExtractor

# 추출
extractor = PDFPlumberExtractor()
blocks_json = extractor.extract_blocks(Path("math1.pdf"))

# 파싱
parser = Math1Parser()
result = parser.parse(blocks_json["blocks"], metadata={"book_id": "bk_1"})
```

---

## 📊 최종 JSON 구조

```json
{
  "version": "1.0",
  "subject": "math1",
  "chapter": "01",
  "items": [
    {
      "type": "concept",
      "section": "concept",
      "text": "지수의 정의...",
      "formulas": []
    },
    {
      "type": "question",
      "question_id": "M1-01-EX-01",
      "section": "example",
      "body": "다음 중 옳은 것은?",
      "choices": [
        {"number": "①", "text": "...", "index": 0}
      ],
      "formula_images": [
        {"formula_id": "formula_1", "image_path": "..."}
      ]
    }
  ]
}
```

---

## 🎯 다음 단계

1. **실제 PDF 1페이지 기준 분석**
   - "이 블록이 이 JSON으로 변환된다" 실사례

2. **수학 수식 → Nemeth 점자 변환**
   - `formula_images` → 점자 변환 서비스 연동

3. **수학Ⅱ / 미적분으로 확장**
   - Math1Parser를 기반으로 확장
