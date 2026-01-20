# 수능특강 교재 파서 시스템

체계적인 3단계 파이프라인으로 PDF를 분석하여 강의 JSON을 생성합니다.

## 📋 목차

1. [개요](#개요)
2. [아키텍처](#아키텍처)
3. [설치](#설치)
4. [사용법](#사용법)
5. [파일 구조](#파일-구조)
6. [설계 원칙](#설계-원칙)

---

## 개요

### 3단계 파이프라인

```
┌─────────┐    ┌──────────────┐    ┌─────────────┐
│   PDF   │ →  │  Intermediate│ →  │  강의 JSON  │
│         │    │   Structure  │    │             │
└─────────┘    └──────────────┘    └─────────────┘
   OCR/PDF      물리적 파싱         논리적 변환
   텍스트 추출   (블록 분류)        (출력 조립)
```

### 장점

- **단일 책임 원칙**: 각 단계가 명확한 역할 수행
- **테스트 용이성**: 각 단계를 독립적으로 테스트
- **디버깅 효율성**: 중간 구조를 저장하여 육안 확인
- **유연성**: 출력 포맷 변경 시 변환 로직만 수정

---

## 아키텍처

### 모듈 구조

```
app/services/parsers/
├── __init__.py                 # 모듈 진입점
├── intermediate_schema.py      # 중간 구조 데이터 클래스
├── parsing_rules.py            # 파싱 규칙 설정
├── ocr_normalizer.py           # OCR 오류 정규화
├── base_parser.py              # 기본 파서 클래스
├── question_parser.py          # 문제 파서 (우선순위 1)
├── passage_parser.py           # 작품 파서 (우선순위 2)
├── concept_parser.py           # 개념 파서 (우선순위 3)
├── example_parser.py           # 보기 파서 (우선순위 4)
├── document_parser.py          # 메인 문서 파서
├── json_assembler.py           # 최종 JSON 변환기
└── example_usage.py            # 사용 예제
```

### 블록 타입

| 타입 | 설명 | 우선순위 | 예시 |
|------|------|----------|------|
| **question** | 문제 | 1 (최우선) | "01", "02" |
| **passage** | 작품 본문 | 2 | "- 박두진, 「해」" |
| **concept** | 개념 설명 | 3 | "(1) 시적 표현" |
| **example** | 보기 | 4 | "< 보기 >" |

### 중간 구조 (Intermediate Structure)

```python
IntermediateDocument
├── subject: str
├── pdf_path: str
├── pages: List[IntermediatePage]
│   ├── page_num: int
│   └── blocks: List[IntermediateBlock]
│       ├── block_id: str
│       ├── block_type: BlockType
│       ├── bbox: [x0, y0, x1, y1]
│       ├── raw_lines: List[Line]
│       └── metadata: BlockMetadata
└── lectures: List[LectureInfo]
```

---

## 설치

### 1. 의존성 설치

```bash
# 기본 (pdfplumber 사용)
pip install pdfplumber

# OCR 사용 시 추가
pip install pdf2image pytesseract Pillow
```

### 2. Tesseract 설치 (OCR 사용 시)

**Windows:**
```bash
# Chocolatey 사용
choco install tesseract

# 또는 수동 설치
# https://github.com/UB-Mannheim/tesseract/wiki
```

**macOS:**
```bash
brew install tesseract
brew install tesseract-lang  # 한국어 언어팩
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-kor
```

---

## 사용법

### 기본 사용 (pdfplumber)

```python
from pathlib import Path
from app.services.parsers import DocumentParser, JSONAssembler
from app.services.text_extractors import PdfplumberExtractor

# 1. 텍스트 추출
extractor = PdfplumberExtractor()
pdf_path = Path("data/literature/pdf/수능특강_문학.pdf")
all_ocr_data = extractor.extract(pdf_path)

# 2. 문서 파싱 (PDF → 중간 구조)
doc_parser = DocumentParser(subject="literature")
intermediate_doc = doc_parser.parse(
    all_ocr_data=all_ocr_data,
    pdf_path=str(pdf_path),
    ocr_method="pdfplumber"
)

# 3. 중간 구조 저장 (검증용)
doc_parser.save_intermediate(
    intermediate_doc,
    Path("data/literature/intermediate_doc.json")
)

# 4. 최종 JSON 생성 (중간 구조 → 강의 JSON)
assembler = JSONAssembler()
assembler.save_all(
    doc=intermediate_doc,
    lectures_dir=Path("data/literature/lectures"),
    problems_dir=Path("data/literature/problems")
)
```

### 고급 사용

#### 특정 강의만 JSON 생성

```python
# 중간 구조 로드
intermediate_doc = doc_parser.load_intermediate(
    Path("data/literature/intermediate_doc.json")
)

# 특정 강의 JSON 생성
assembler = JSONAssembler()
lecture_json = assembler.assemble_lecture_json(intermediate_doc, lecture_id=1)

print(lecture_json)
# {
#   "subject": "literature",
#   "lecture_id": 1,
#   "title": "강의 1",
#   "sections": [...],
#   "problems": ["01", "02", ...]
# }
```

#### OCR 사용 (스캔 PDF)

```python
from app.services.text_extractors import OCRExtractor

# OCR 추출기 초기화
extractor = OCRExtractor(dpi=180, lang='kor+eng')
all_ocr_data = extractor.extract(pdf_path)

# 이후 동일
doc_parser = DocumentParser(subject="literature")
intermediate_doc = doc_parser.parse(
    all_ocr_data=all_ocr_data,
    pdf_path=str(pdf_path),
    ocr_method="tesseract"
)
```

---

## 파일 구조

### 입력

```
data/literature/
└── pdf/
    └── 수능특강_문학.pdf
```

### 출력

```
data/literature/
├── intermediate_doc.json        # 중간 구조 (검증/디버깅용)
├── lectures/
│   ├── lectures.json            # 강의 목록
│   ├── lecture_01.json          # 강의 1
│   └── lecture_02.json          # 강의 2
└── problems/
    ├── problem_01.json          # 문제 1
    └── problem_02.json          # 문제 2
```

### 강의 JSON 포맷

```json
{
  "subject": "literature",
  "lecture_id": 1,
  "title": "시의 표현과 형식",
  "sections": [
    {
      "title": "(1) 형상화",
      "content": [
        "형상화는 시의 주제를 형상화하는 표현 기법입니다.",
        "..."
      ],
      "page": 8
    },
    {
      "title": "박두진 - 「해」",
      "content": [
        "태양을 연두빛으로 물들이는 해",
        "..."
      ],
      "page": 10
    }
  ],
  "problems": ["01", "02", "03"]
}
```

### 문제 JSON 포맷

```json
{
  "problem_id": "01",
  "page": 12,
  "content": [
    "다음 시의 표현 기법으로 적절한 것은?",
    "..."
  ],
  "has_example": true
}
```

---

## 설계 원칙

### 1. 파싱 우선순위

```
question (1) → passage (2) → concept (3) → example (4)
```

**이유:**
- **question**: 패턴이 가장 명확 (`^\d{2}$`)
- **passage**: 작품 표시가 고유 (`- 작가, 「작품」`)
- **concept**: 번호 패턴이 question과 유사하므로 나중에
- **example**: question 내부에 종속적

### 2. OCR 오류 정규화

```python
# 문제 번호 복원
"O1" → "01"
"0l" → "01"

# 작품 괄호 복원
"r작품명」" → "「작품명」"
"「작품명l" → "「작품명」"
```

### 3. 위치 기반 힌트

| 영역 | Y 위치 | 주요 타입 |
|------|--------|-----------|
| 상단 | 0.0 ~ 0.3 | concept |
| 중단 | 0.3 ~ 0.7 | passage |
| 하단 | 0.6 ~ 1.0 | question |

### 4. 폰트 크기 활용

```python
# 평균 대비 비율
제목 (lecture): 평균 * 1.3
개념 (concept): 평균 * 1.1
문제 번호 (question): 평균 * 1.2
```

---

## 예제 실행

```bash
# 프로젝트 루트에서
cd api

# 예제 스크립트 실행
python -m app.services.parsers.example_usage
```

**출력:**
```
============================================================
예제 1: pdfplumber를 사용한 파싱
============================================================

[단계 1] PDF 텍스트 추출 중...
   ✓ 150개 페이지 추출 완료

[단계 2] 문서 파싱 중...
   ✓ 파싱 완료:
     - 페이지: 150개
     - 블록: 450개
     - 강의: 30개

[단계 3] 중간 구조 저장 중...
   ✓ 저장 완료: data/literature/intermediate_doc.json

[단계 4] 최종 JSON 생성 중...
   ✓ 강의 JSON: data/literature/lectures/
   ✓ 문제 JSON: data/literature/problems/

============================================================
✅ 완료!
============================================================
```

---

## 문제 해결

### Q1. OCR 결과가 비어있음

**원인:** Tesseract가 설치되지 않았거나 한국어 언어팩 누락

**해결:**
```bash
# Windows
choco install tesseract

# macOS
brew install tesseract tesseract-lang

# Linux
sudo apt-get install tesseract-ocr tesseract-ocr-kor
```

### Q2. pdfplumber로 텍스트를 추출하지 못함

**원인:** 스캔된 PDF (텍스트 레이어 없음)

**해결:** OCR 모드 사용
```python
from app.services.text_extractors import OCRExtractor
extractor = OCRExtractor(dpi=180, lang='kor+eng')
```

### Q3. 파싱 결과가 부정확함

**원인:** OCR 오류 또는 패턴 미매칭

**해결:**
1. 중간 구조 JSON 확인: `data/literature/intermediate_doc.json`
2. 로그 레벨을 DEBUG로 변경:
   ```python
   logging.basicConfig(level=logging.DEBUG)
   ```
3. 파싱 규칙 조정: `app/services/parsers/parsing_rules.py`

---

## 기여

버그 리포트, 기능 제안, Pull Request를 환영합니다!

---

## 라이센스

MIT License
