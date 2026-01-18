# PDF 처리 파이프라인 설계 문서

## 📋 개요

시각장애 수험생을 위한 수능 학습 시스템의 PDF 처리 파이프라인입니다.

**핵심 원칙:**
1. PDF **추출(extract)**과 **구조 해석(parse)**을 절대 섞지 않는다
2. 중간 산출물(JSON)은 사람이 검증 가능해야 한다
3. 과목별 특성을 코드 구조로 분리한다
4. 수식, 보기, 지문, 문제 번호는 모두 별도 객체로 관리한다

## 📁 폴더 구조

```
api/app/services/
├── pdf_extract/              # PDF 추출 (구조 해석 없음)
│   ├── __init__.py
│   ├── base_extractor.py     # 추출기 기본 인터페이스
│   ├── pdfplumber_extractor.py  # PDFPlumber 기반 추출기
│   └── image_extractor.py    # 이미지 추출기
│
├── pdf_parse/                # 구조 해석
│   ├── __init__.py
│   ├── base_parser.py        # 파서 기본 인터페이스
│   ├── parse_pipeline.py     # 전체 파이프라인
│   └── json_schema.py        # JSON 스키마 정의
│
└── subject_strategies/       # 과목별 파싱 전략
    ├── __init__.py
    ├── math.py               # 수학 파서
    ├── korean.py             # 국어 파서
    └── english.py            # 영어 파서
```

## 🔄 처리 단계

### Step 1: Extract (추출)

**목적:** PDF에서 좌표 기반 원본 블록 추출

**입력:** PDF 파일
**출력:** `{book_id}_blocks.json`

```json
{
  "version": "1.0",
  "extractor": "PDFPlumberExtractor",
  "pages": {
    "1": [...]
  },
  "blocks": [
    {
      "type": "text",
      "page": 1,
      "bbox": [100, 200, 300, 250],
      "content": "1. 다음 중 옳은 것은?",
      "metadata": {"word_count": 5}
    },
    {
      "type": "image",
      "page": 1,
      "bbox": [100, 300, 200, 400],
      "content": "data/formulas/formula_1.png",
      "metadata": {"width": 100, "height": 100}
    }
  ]
}
```

**특징:**
- 구조 해석 없음 (단순 블록 추출)
- 좌표 정보 유지
- 이미지는 별도 저장

### Step 2: Parse (구조 해석)

**목적:** 추출된 블록을 과목별로 구조화

**입력:** `{book_id}_blocks.json`
**출력:** `data/parsed/{subject}/{book_id}_parsed.json`

**과목별 차이점:**

#### 수학 (MathParser)
- 수식은 **이미지로만** 처리 (텍스트 변환 금지)
- 문제 → 보기 구조 명확
- 개념 설명 → 예제 → 유제 구성

```json
{
  "subject": "math",
  "units": [
    {
      "type": "question",
      "question_number": 1,
      "question_stem": "다음 중 옳은 것은?",
      "choices": [
        {"number": "①", "text": "x² + 2x + 1", "index": 0}
      ],
      "formula_images": [
        {"image_path": "formula_1.png", "bbox": [...], "page": 1}
      ]
    }
  ]
}
```

#### 국어 (KoreanParser)
- 지문 = **문단 배열** (paragraph[])
- 지문 → 문제 참조 구조
- 문학의 경우 화자/상황/정서 메타데이터

```json
{
  "subject": "korean",
  "units": [
    {
      "type": "passage",
      "passage_id": "passage_1",
      "title": "황조가",
      "paragraphs": [
        {"index": 0, "text": "철령 이화...", "char_count": 13}
      ],
      "full_text": "..."
    },
    {
      "type": "question",
      "question_number": 1,
      "passage_id": "passage_1",
      "question_stem": "...",
      "choices": [...]
    }
  ]
}
```

#### 영어 (EnglishParser)
- 지문 = **문장 배열** (sentence[])
- 빈칸 위치는 placeholder로 유지
- 문제 유형 자동 분류 (blank, ordering, insertion 등)

```json
{
  "subject": "english",
  "units": [
    {
      "type": "passage",
      "passage_id": "passage_1",
      "sentences": [
        {"index": 0, "text": "The quick brown fox...", "has_placeholder": false}
      ],
      "placeholders": [
        {"position": 50, "length": 3, "type": "blank"}
      ]
    },
    {
      "type": "question",
      "question_type": "blank",
      "question_stem": "...",
      "choices": [...]
    }
  ]
}
```

### Step 3: Save (저장)

**목적:** 파싱 결과를 데이터베이스에 저장 (선택적)

**향후 구현 예정**

## 🚀 사용 방법

### 기본 사용

```python
from pathlib import Path
from app.services.pdf_parse.parse_pipeline import ParsePipeline

# 파이프라인 생성
pipeline = ParsePipeline()

# 전체 실행
result = pipeline.run(
    pdf_path=Path("data/pdfs/math_2026.pdf"),
    subject="MATH",
    book_id="bk_math_2026",
    metadata={"year": 2026}
)

# 결과:
# - data/extracted/bk_math_2026_blocks.json (추출 결과)
# - data/parsed/math/bk_math_2026_parsed.json (파싱 결과)
```

### 단계별 실행

```python
# Step 1: 추출만
extract_result = pipeline.extract(
    pdf_path=Path("data/pdfs/math_2026.pdf"),
    book_id="bk_math_2026"
)

# Step 2: 파싱만 (추출 결과 사용)
parse_result = pipeline.parse(
    extract_result=extract_result,
    subject="MATH",
    book_id="bk_math_2026"
)
```

### 과목별 파서 직접 사용

```python
from app.services.subject_strategies.math import MathParser
from app.services.pdf_extract.pdfplumber_extractor import PDFPlumberExtractor

# 추출
extractor = PDFPlumberExtractor()
blocks = extractor.extract_blocks(Path("math.pdf"))

# 파싱
parser = MathParser()
result = parser.parse(blocks, metadata={"book_id": "bk_1"})
```

## 📊 JSON 스키마

### 최종 결과 스키마

모든 과목에서 공통으로 사용하는 구조:

```typescript
interface StructuredContent {
  version: string;
  subject: "math" | "korean" | "english";
  book_id?: string;
  title?: string;
  pages: { [pageNum: string]: PageStructure };
  units: ContentUnit[];
  statistics: {
    total_units: number;
    questions: number;
    // 과목별 추가 통계
  };
  metadata: Record<string, any>;
}

interface ContentUnit {
  unit_id: string;
  type: "question" | "passage" | "concept";
  subject: "math" | "korean" | "english";
  
  // 과목별 필드
  question?: Question;
  passage?: Passage;
  concept?: Concept;
  
  page: number;
  metadata: Record<string, any>;
}
```

## 🔑 핵심 설계 원칙

### 1. 추출과 파싱 분리

**왜?**
- 추출은 PDF 라이브러리 의존적 (pdfplumber, PyPDF2 등)
- 파싱은 도메인 로직 (과목별 특성)
- 분리하면 테스트와 유지보수가 쉬움

### 2. JSON 중간 산출물

**왜?**
- 사람이 검증 가능 (디버깅 용이)
- 파이프라인 단계별 재실행 가능
- 다른 도구와 연동 용이

### 3. 과목별 전략 패턴

**왜?**
- 수학: 수식 이미지 중요
- 국어: 문단 구조 중요
- 영어: 문장 단위 중요
- 각각 다른 로직 필요

### 4. 수식은 이미지로만

**왜?**
- LaTeX 변환은 복잡하고 오류 많음
- 이미지는 100% 정확
- 점자 변환/음성 출력 시 별도 처리 필요

## 📝 다음 단계

1. **점자 변환 연동**
   - `ContentUnit` → 점자 변환 서비스
   - 수식 이미지는 "수식 이미지" 안내

2. **음성 출력 연동**
   - 문단/문장 단위로 TTS 처리
   - 수식 이미지는 "수식" 또는 건너뛰기

3. **시험 모드 연동**
   - 문제 단위로 추출
   - 답안 제출 후 채점

4. **DB 저장 구현**
   - `Lesson`, `Unit` 모델 변환
   - 기존 데이터와 통합
