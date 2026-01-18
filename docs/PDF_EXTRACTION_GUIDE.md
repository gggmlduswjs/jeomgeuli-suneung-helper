# PDF 추출 및 파싱 완전 가이드

시각장애 수험생을 위한 수능 학습 시스템의 PDF 처리 파이프라인 사용 가이드입니다.

## 📋 목차

1. [개요](#개요)
2. [아키텍처 원칙](#아키텍처-원칙)
3. [시작하기](#시작하기)
4. [추출(Extract) 단계](#추출-extract-단계)
5. [파싱(Parse) 단계](#파싱-parse-단계)
6. [과목별 가이드](#과목별-가이드)
7. [AI/ML 기능 활용](#aiml-기능-활용)
8. [문제 해결](#문제-해결)
9. [API 사용법](#api-사용법)
10. [터미널 명령어 요약](#터미널-명령어-요약)
11. [테스트](#테스트)

---

## 개요

### 핵심 원칙

1. **추출과 파싱 분리**: PDF에서 데이터를 뽑아내는 것(extract)과 구조를 해석하는 것(parse)을 절대 섞지 않습니다.
2. **중간 결과 저장**: 각 단계의 결과를 JSON으로 저장하여 검증 및 재사용이 가능합니다.
3. **과목별 전략**: 수학, 문학, 영어는 각각 다른 구조를 가지므로 별도의 파서를 사용합니다.
4. **좌표 정보 보존**: 블록의 위치 정보(bbox)를 유지하여 레이아웃 분석이 가능합니다.

### 처리 흐름

```
PDF 파일
    ↓
[Extract 단계] → {book_id}_blocks.json
    ↓
[Parse 단계] → data/parsed/{subject}/{book_id}_parsed.json
    ↓
구조화된 콘텐츠 (DB 저장 또는 점자/음성 변환)
```

---

## 아키텍처 원칙

### 1. 추출과 파싱 분리

**왜 분리하나요?**

- **추출**: PDF 라이브러리 의존적 (pdfplumber, PyPDF2 등)
- **파싱**: 도메인 로직 (과목별 특성)
- 분리하면 테스트와 유지보수가 쉬움
- 각 단계를 독립적으로 최적화 가능

**예시:**

```python
# ❌ 나쁜 예: 추출과 파싱이 섞여있음
def process_pdf(pdf_path):
    text = extract_text(pdf_path)
    questions = parse_questions(text)  # 이미 구조 해석 시도
    return questions

# ✅ 좋은 예: 추출과 파싱 분리
def extract(pdf_path):
    blocks = extract_blocks(pdf_path)  # 구조 해석 없음
    return blocks

def parse(blocks, subject):
    parser = get_parser(subject)
    return parser.parse(blocks)  # 여기서 구조 해석
```

### 2. JSON 중간 산출물

**왜 JSON을 사용하나요?**

- 사람이 검증 가능 (디버깅 용이)
- 파이프라인 단계별 재실행 가능
- 다른 도구와 연동 용이
- 버전 관리 가능

### 3. 과목별 전략 패턴

**각 과목의 특성:**

| 과목 | 핵심 단위 | 파싱 포인트 | 점자 변환 |
|------|----------|------------|----------|
| 수학Ⅰ | 문제 + 수식 | 보기 묶기, 수식 이미지 | Nemeth 점자 |
| 문학 | 지문 + 문제 | 지문 경계, 문단 분리 | 문장 단위 |
| 영어 | 지문 + 문제 | 문장 분리, 빈칸 위치 | 문장 단위 |

---

## 시작하기

### 필수 요구사항

**Windows PowerShell:**
```powershell
# 기본 패키지 설치
cd api
pip install -r requirements.txt

# 필수 패키지:
# - pdfplumber: PDF 텍스트 추출
# - Pillow: 이미지 처리
# - pathlib: 파일 경로 관리 (Python 3.4+ 내장)
```

**Linux/Mac Bash:**
```bash
# 기본 패키지 설치
cd api
pip install -r requirements.txt
```

### 빠른 시작 (PowerShell)

```powershell
# 1. 프로젝트 디렉토리로 이동
cd C:\Users\user\Desktop\jeomgeuli-suneung-helper

# 2. API 디렉토리로 이동
cd api

# 3. 의존성 설치 (처음만)
pip install -r requirements.txt

# 4. PDF 파일 준비
# data/pdfs/ 폴더에 PDF 파일 복사/이동
New-Item -ItemType Directory -Force -Path data/pdfs

# 5. 테스트 실행
python tests/test_pdf_extract.py
```

### 디렉토리 구조

```
data/
├── pdfs/              # 원본 PDF 파일
├── extracted/         # 추출된 블록 JSON
│   └── {book_id}_blocks.json
└── parsed/            # 파싱된 구조 JSON
    ├── math/
    ├── korean/
    └── english/
```

### 기본 사용법

```python
from pathlib import Path
from app.services.pdf_parse.parse_pipeline import ParsePipeline

# 파이프라인 생성
pipeline = ParsePipeline()

# 전체 실행
result = pipeline.run(
    pdf_path=Path("data/pdfs/2026 수능특강 수학Ⅰ.pdf"),
    subject="MATH",
    book_id="math_2026",
    metadata={"year": 2026}
)

# 결과:
# - data/extracted/math_2026_blocks.json (추출 결과)
# - data/parsed/math/math_2026_parsed.json (파싱 결과)
```

---

## 추출(Extract) 단계

### 목적

PDF에서 좌표 기반 원본 블록을 추출합니다. **구조 해석은 하지 않습니다.**

### 사용 가능한 추출기

#### 1. PDFPlumberExtractor (기본)

**용도**: 일반적인 PDF 텍스트/이미지/테이블 추출

```python
from app.services.pdf_extract import PDFPlumberExtractor
from pathlib import Path

extractor = PDFPlumberExtractor(
    x_tolerance=3,  # 가로 방향 단어 간격 허용 범위
    y_tolerance=3,  # 세로 방향 단어 간격 허용 범위
)

pdf_path = Path("data/pdfs/math.pdf")
blocks = extractor.extract_blocks(pdf_path)

# blocks는 다음과 같은 구조:
# [
#   {
#     "type": "text",
#     "page": 1,
#     "bbox": [100, 200, 300, 250],
#     "content": "1. 다음 중 옳은 것은?",
#     "metadata": {"word_count": 5, "char_count": 12}
#   },
#   {
#     "type": "image",
#     "page": 1,
#     "bbox": [100, 300, 200, 400],
#     "content": None,  # 이미지는 별도 저장
#     "metadata": {"width": 100, "height": 100}
#   }
# ]
```

#### 2. LiteraturePDFExtractor (문학 전용)

**용도**: 문학 PDF에서 줄 단위 텍스트 추출

```python
from app.services.pdf_extract import LiteraturePDFExtractor

extractor = LiteraturePDFExtractor()
blocks = extractor.extract_blocks(pdf_path)

# blocks는 줄 단위로 분리된 텍스트:
# [
#   {
#     "type": "text",
#     "page": 1,
#     "text": "철령 이화에 설우난...",
#     "bbox": [100, 200, 300, 220],
#     "line_number": 1
#   }
# ]
```

#### 3. ImageExtractor (이미지 전용)

**용도**: PDF에서 이미지만 추출 (수식, 그래프 등)

```python
from app.services.pdf_extract import ImageExtractor

extractor = ImageExtractor(dpi=150)
blocks = extractor.extract_blocks(pdf_path)

# 이미지 블록만 추출
```

### 추출 결과 JSON 구조

```json
{
  "version": "1.0",
  "extractor": "PDFPlumberExtractor",
  "pages": {
    "1": [/* 페이지 1의 블록들 */],
    "2": [/* 페이지 2의 블록들 */]
  },
  "blocks": [
    {
      "type": "text" | "image" | "table",
      "page": 1,
      "bbox": [x0, y0, x1, y1],
      "content": "텍스트 또는 이미지 경로",
      "metadata": {
        "word_count": 10,
        "char_count": 20
      }
    }
  ]
}
```

### 추출 결과 저장

```python
# 추출 결과를 JSON으로 저장
extract_json = extractor.to_json(blocks, output_path=Path("output.json"))

# 또는 ParsePipeline 사용 시 자동 저장
pipeline = ParsePipeline()
extract_result = pipeline.extract(pdf_path, book_id="book_1")
# → data/extracted/book_1_blocks.json 자동 생성
```

---

## 파싱(Parse) 단계

### 목적

추출된 블록을 과목별 구조로 해석합니다.

### 과목별 파서

#### 1. MathParser (수학)

**특징:**
- 수식은 이미지로만 처리 (텍스트 변환 금지)
- 문제 → 보기 구조 명확
- 개념 설명 → 예제 → 유제 구성

```python
from app.services.subject_strategies.math import MathParser

parser = MathParser()
blocks = [...]  # 추출된 블록
result = parser.parse(blocks, metadata={"book_id": "math_2026"})

# result 구조:
# {
#   "subject": "math",
#   "units": [
#     {
#       "type": "concept",
#       "text": "지수의 정의",
#       "formulas": [/* 수식 이미지 */],
#       "page": 1
#     },
#     {
#       "type": "question",
#       "question_number": 1,
#       "body": "다음 중 옳은 것은?",
#       "choices": [
#         {"number": "①", "text": "x² + 2x + 1", "index": 0}
#       ],
#       "formula_images": [/* 수식 이미지 */],
#       "page": 1
#     }
#   ]
# }
```

#### 2. LiteratureParser (문학)

**특징:**
- 지문 = 문단 배열 (paragraph[])
- 지문 → 문제 참조 구조
- 문단 순서 보존

```python
from app.services.subject_strategies.literature import LiteratureParser

parser = LiteratureParser()
result = parser.parse(blocks, metadata={"book_id": "literature_2026"})

# result 구조:
# {
#   "subject": "literature",
#   "passages": [
#     {
#       "passage_id": "LIT-01",
#       "title": "황조가",
#       "paragraphs": [
#         {"index": 0, "text": "철령 이화에...", "char_count": 50}
#       ],
#       "full_text": "...",
#       "page": 1
#     }
#   ],
#   "questions": [
#     {
#       "question_id": "LIT-01-Q1",
#       "question_number": 1,
#       "question_text": "...",
#       "choices": [...]
#     }
#   ]
# }
```

#### 3. EnglishParser (영어)

**특징:**
- 지문 = 문장 배열 (sentence[])
- 빈칸 위치는 placeholder로 유지
- 문제 유형 자동 분류 (blank, ordering, insertion 등)

```python
from app.services.subject_strategies.english import EnglishParser

parser = EnglishParser()
result = parser.parse(blocks, metadata={"book_id": "english_2026"})

# result 구조:
# {
#   "subject": "english",
#   "passages": [
#     {
#       "passage_id": "ENG-01",
#       "sentences": [
#         {"index": 0, "text": "The quick brown...", "has_placeholder": false}
#       ],
#       "placeholders": [
#         {"position": 50, "length": 3, "type": "blank"}
#       ]
#     }
#   ],
#   "questions": [
#     {
#       "question_id": "ENG-01-Q1",
#       "type": "blank",
#       "question_text": "...",
#       "choices": [...]
#     }
#   ]
# }
```

### 파싱 결과 저장

```python
# ParsePipeline 사용 시 자동 저장
pipeline = ParsePipeline()
extract_result = pipeline.extract(pdf_path, book_id="book_1")
parse_result = pipeline.parse(
    extract_result=extract_result,
    subject="MATH",
    book_id="book_1"
)
# → data/parsed/math/book_1_parsed.json 자동 생성
```

---

## 과목별 가이드

### 수학Ⅰ

#### PDF 특징

- 개념 → 예제 → 유제 구조
- 수식은 이미지 또는 벡터 그래픽
- 보기는 ①②③④⑤ 패턴
- 문제 번호는 숫자 또는 "다음 중"으로 시작

#### 추출 전략

```python
# 1. PDFPlumberExtractor 사용
extractor = PDFPlumberExtractor()

# 2. 이미지 블록도 함께 추출
blocks = extractor.extract_blocks(pdf_path)

# 3. MathParser로 파싱
parser = MathParser()
result = parser.parse(blocks)
```

#### 주의사항

- 수식은 절대 텍스트로 변환하지 않음
- 수식 이미지는 `formula_images` 배열로 관리
- 보기는 y좌표 기준으로 정렬하여 묶음

### 문학

#### PDF 특징

- 지문은 연속된 텍스트 블록
- 문제는 지문 이후에 나옴
- 보기/문제/선택지가 명확히 구분됨

#### 추출 전략

```python
# 1. LiteraturePDFExtractor 사용 (줄 단위 추출)
extractor = LiteraturePDFExtractor()
blocks = extractor.extract_blocks(pdf_path)

# 2. LiteratureParser로 파싱
parser = LiteratureParser()
result = parser.parse(blocks)
```

#### 주의사항

- 지문과 문제를 절대 섞으면 안 됨
- 지문은 하나의 passage로 묶음
- 문제는 지문 ID를 참조

### 영어

#### PDF 특징

- 지문은 연속된 문장 블록
- 빈칸(___), 삽입 위치(①②③) 포함
- 문제 유형이 다양함 (blank, ordering, insertion 등)

#### 추출 전략

```python
# 1. PDFPlumberExtractor 사용
extractor = PDFPlumberExtractor()
blocks = extractor.extract_blocks(pdf_path)

# 2. EnglishParser로 파싱
parser = EnglishParser()
result = parser.parse(blocks)
```

#### 주의사항

- 빈칸(___), 삽입 위치는 반드시 유지
- 지문은 sentence 단위로 분리
- 문제 유형을 자동으로 분류

---

## AI/ML 기능 활용

### 1. Enhanced OCR

**용도**: 스캔본 PDF 처리

```python
from app.services.pdf_extract.enhanced_ocr import EnhancedOCR

ocr = EnhancedOCR(lang='kor+eng')

# PDF → 이미지 변환
from pdf2image import convert_from_path
images = convert_from_path(pdf_path, dpi=150)

# OCR 수행
result = ocr.extract_from_page_image(images[0], page_num=1)
# result: {"text": "...", "blocks": [...]}
```

**설정:**
- Tesseract 설치 필요 (Windows: https://github.com/UB-Mannheim/tesseract/wiki)
- `pip install pytesseract opencv-python`

### 2. AI 텍스트 후처리

**용도**: OCR 오류 수정, 텍스트 정리

```python
from app.services.pdf_extract.ai_text_postprocessor import get_text_postprocessor
from app.core.config import settings

# OpenAI API 키 필요
if settings.OPENAI_API_KEY:
    postprocessor = get_text_postprocessor(use_ai=True, model="gpt-4o-mini")
    
    # 텍스트 정리
    cleaned = postprocessor.clean_extracted_text(
        text="OCR로 추출한 텍스트 (오류 포함)",
        subject="korean"
    )
else:
    # 기본 후처리 (규칙 기반)
    postprocessor = get_text_postprocessor(use_ai=False)
    cleaned = postprocessor.clean_extracted_text(text, subject="korean")
```

**설정:**
- `.env` 파일에 `OPENAI_API_KEY=your-api-key` 추가
- `pip install openai langchain`

### 3. AI 구조 분류

**용도**: 블록 타입 자동 분류 (문제, 지문, 보기 등)

```python
from app.services.pdf_parse.ai_structure_classifier import AIStructureClassifier

classifier = AIStructureClassifier()

block_type = classifier.classify_block(block)
# "question" | "passage" | "choice" | "header" | "footer"
```

**설정:**
- `pip install transformers torch`

### 4. Math OCR

**용도**: 수식 이미지 → LaTeX 변환

```python
from app.services.pdf_extract.math_ocr import get_math_ocr

# MathPix 사용 (API 키 필요)
if settings.MATHPIX_APP_ID and settings.MATHPIX_APP_KEY:
    math_ocr = get_math_ocr(use_mathpix=True)
else:
    # 기본 OCR (PaddleOCR 등)
    math_ocr = get_math_ocr(use_mathpix=False)

latex = math_ocr.image_to_latex(image_path)
# LaTeX → Nemeth 점자 변환
braille = math_ocr.latex_to_braille(latex)
```

**설정:**
- MathPix: `.env`에 `MATHPIX_APP_ID`, `MATHPIX_APP_KEY` 추가
- PaddleOCR: `pip install paddleocr`

---

## 문제 해결

### PDF 파일을 찾을 수 없음

```
❌ PDF 파일을 찾을 수 없습니다: .../data/pdfs
```

**해결:**
1. `data/pdfs/` 폴더에 PDF 파일 배치
2. 파일 경로 확인:
   ```python
   from app.core.config import settings
   print(settings.PDFS_DIR)
   ```

### 추출 실패 (layout 파라미터 오류)

```
TypeError: WordExtractor.__init__() got an unexpected keyword argument 'layout'
```

**해결:**
- `pdfplumber` 버전 문제일 수 있음
- 코드에서 `layout` 파라미터 제거됨 (이미 수정됨)

### OCR 사용 불가

```
⚠️ Enhanced OCR을 사용할 수 없습니다.
```

**해결:**
1. Tesseract 설치 (Windows: https://github.com/UB-Mannheim/tesseract/wiki)
2. `pip install pytesseract opencv-python`

### AI 기능 사용 불가

```
⚠️ OPENAI_API_KEY가 설정되지 않았습니다.
```

**해결:**
1. `api/.env` 파일 생성
2. `OPENAI_API_KEY=your-api-key` 추가
3. 또는 환경변수로 설정:
   ```powershell
   $env:OPENAI_API_KEY="your-api-key"
   ```

### 파싱 결과가 비어있음

**가능한 원인:**
1. PDF 구조가 예상과 다름
2. 파서의 패턴 매칭 실패

**디버깅:**
```python
# 1. 추출 결과 확인
extract_result = pipeline.extract(pdf_path, book_id="test")
print(f"추출된 블록 수: {len(extract_result['blocks'])}")

# 2. 첫 번째 블록 확인
print(extract_result['blocks'][0])

# 3. 파서 로그 확인
parser = MathParser()
result = parser.parse(extract_result['blocks'], metadata={"book_id": "test"})
print(f"파싱된 단위 수: {len(result.get('units', []))}")
```

### uvicorn 서버 실행 오류 (ModuleNotFoundError: No module named 'app')

**오류 메시지:**
```
ModuleNotFoundError: No module named 'app'
```

**원인:**
1. `api` 디렉토리에서 실행하지 않음
2. Windows multiprocessing 문제

**해결 방법:**

**1. `api` 디렉토리에서 실행 (필수):**
```powershell
# 반드시 api 디렉토리에서 실행
cd api
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**2. Python 모듈로 실행 (권장):**
```powershell
cd api
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**3. PYTHONPATH 설정 (대안):**
```powershell
# api 디렉토리로 이동
cd api

# PYTHONPATH 설정
$env:PYTHONPATH = (Get-Location).Path

# 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**4. Windows multiprocessing 문제 해결:**
```powershell
# --reload 대신 단일 프로세스로 실행
cd api
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 또는 workers를 1로 제한
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --workers 1
```

**5. 현재 디렉토리 확인:**
```powershell
# 현재 디렉토리 확인
Get-Location

# app 디렉토리 존재 확인
Test-Path app

# app/main.py 존재 확인
Test-Path app\main.py

# 모든 것이 정상이면 api 디렉토리에서 실행
cd api
uvicorn app.main:app --reload
```

**6. 완전한 실행 스크립트 (PowerShell):**
```powershell
# run_server.ps1 파일 생성
# api/run_server.ps1

# API 디렉토리로 이동
Set-Location $PSScriptRoot

# 현재 디렉토리 확인
Write-Host "현재 디렉토리: $(Get-Location)"
Write-Host "app 디렉토리 존재: $(Test-Path app)"
Write-Host "app/main.py 존재: $(Test-Path app\main.py)"

# PYTHONPATH 설정
$env:PYTHONPATH = (Get-Location).Path

# 서버 실행
Write-Host "서버 시작 중..."
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**실행:**
```powershell
cd api
.\run_server.ps1
```

---

## API 사용법

### PDF 업로드 및 파싱

**PowerShell (curl 사용):**
```powershell
# POST /api/v1/books/upload
curl.exe -X POST http://localhost:8000/api/v1/books/upload `
  -F "file=@data/pdfs/math.pdf" `
  -F "title=2026 수능특강 수학Ⅰ" `
  -F "subject=MATH"
```

**Linux/Mac Bash:**
```bash
# POST /api/v1/books/upload
curl -X POST http://localhost:8000/api/v1/books/upload \
  -F "file=@data/pdfs/math.pdf" \
  -F "title=2026 수능특강 수학Ⅰ" \
  -F "subject=MATH"
```

### 구조화된 PDF 추출

**PowerShell:**
```powershell
# POST /api/v1/pdf/extract-structured
curl.exe -X POST http://localhost:8000/api/v1/pdf/extract-structured `
  -F "file=@data/pdfs/math.pdf"
```

**Linux/Mac Bash:**
```bash
# POST /api/v1/pdf/extract-structured
curl -X POST http://localhost:8000/api/v1/pdf/extract-structured \
  -F "file=@data/pdfs/math.pdf"
```

### FastAPI 서버 실행

**PowerShell:**
```powershell
# 백엔드 서버 시작
cd api
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 또는 Python으로 실행
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Linux/Mac Bash:**
```bash
# 백엔드 서버 시작
cd api
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Python 클라이언트

```python
import requests

# PDF 업로드
with open("data/pdfs/math.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/v1/books/upload",
        files={"file": f},
        data={
            "title": "2026 수능특강 수학Ⅰ",
            "subject": "MATH"
        }
    )

result = response.json()
book_id = result["book_id"]
```

---

## 터미널 명령어 요약

### Windows PowerShell 필수 명령어

#### 기본 작업

```powershell
# 프로젝트로 이동
cd C:\Users\user\Desktop\jeomgeuli-suneung-helper\api

# 의존성 설치
pip install -r requirements.txt

# PDF 파일 확인
Get-ChildItem data/pdfs/*.pdf

# 테스트 실행
python tests/test_pdf_extract.py
```

#### 파일 작업

```powershell
# PDF 파일 복사
Copy-Item "원본경로\파일.pdf" -Destination "data/pdfs\"

# 폴더 생성
New-Item -ItemType Directory -Force -Path data/pdfs

# 추출 결과 확인
Get-ChildItem data/extracted/*.json | Select-Object Name, Length, LastWriteTime

# 파싱 결과 확인
Get-ChildItem data/parsed/*/*.json | Select-Object Name, Length, LastWriteTime
```

#### 환경 설정

```powershell
# 환경 변수 설정 (세션용)
$env:OPENAI_API_KEY="your-api-key"

# .env 파일 생성
New-Item .env -ItemType File -Force
Add-Content .env "OPENAI_API_KEY=your-api-key"

# .env 파일 내용 확인
Get-Content .env
```

#### 서버 실행

**⚠️ 중요: 반드시 `api` 디렉토리에서 실행해야 합니다!**

```powershell
# 1. api 디렉토리로 이동 (필수!)
cd api

# 2. 현재 디렉토리 확인
Get-Location  # C:\Users\user\Desktop\jeomgeuli-suneung-helper\api 여야 함

# 3. app 디렉토리 존재 확인
Test-Path app  # True여야 함

# 4. 서버 실행 (방법 1: uvicorn 직접 실행)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 5. 서버 실행 (방법 2: Python 모듈로 실행 - 권장)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 6. Windows multiprocessing 문제가 있는 경우 (--reload 제거)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**잘못된 실행 (프로젝트 루트에서 실행):**
```powershell
# ❌ 이렇게 하면 안 됨!
cd C:\Users\user\Desktop\jeomgeuli-suneung-helper
uvicorn app.main:app --reload  # ModuleNotFoundError 발생!
```

**올바른 실행:**
```powershell
# ✅ 반드시 api 디렉토리에서 실행
cd C:\Users\user\Desktop\jeomgeuli-suneung-helper\api
uvicorn app.main:app --reload  # 정상 작동!
```

#### 디버깅

```powershell
# Python 경로 확인
python -c "import sys; print(sys.path)"

# 패키지 설치 확인
pip list | Select-String "pdfplumber|pillow"

# 설정 확인
python -c "from app.core.config import settings; print(settings.PDFS_DIR)"
```

### Linux/Mac Bash 명령어

```bash
# 기본 작업
cd api
pip install -r requirements.txt
ls data/pdfs/*.pdf
python tests/test_pdf_extract.py

# 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 환경 변수 설정
export OPENAI_API_KEY="your-api-key"

# .env 파일 생성
echo "OPENAI_API_KEY=your-api-key" > .env
```

---

## 테스트

### 전체 테스트 실행

**Windows PowerShell:**
```powershell
cd api
python tests/test_pdf_extract.py
```

**Linux/Mac Bash:**
```bash
cd api
python tests/test_pdf_extract.py
```

### 빠른 테스트 (PowerShell)

```powershell
# 1. API 디렉토리로 이동
cd api

# 2. 테스트 실행
python tests/test_pdf_extract.py

# 3. PDF 파일 확인
ls data/pdfs/*.pdf

# 4. 추출 결과 확인
ls data/extracted/*.json

# 5. 파싱 결과 확인
ls data/parsed/*/*.json
```

### 파일 준비 (PowerShell)

```powershell
# PDF 파일을 data/pdfs/ 폴더에 복사
Copy-Item "C:\Users\user\Downloads\2026 수능특강 수학Ⅰ.pdf" -Destination "data/pdfs/"

# 또는 이동
Move-Item "C:\Users\user\Downloads\2026 수능특강 수학Ⅰ.pdf" -Destination "data/pdfs/"

# PDF 파일 목록 확인
Get-ChildItem data/pdfs/*.pdf | Select-Object Name, Length, LastWriteTime
```

### 환경 설정 (PowerShell)

```powershell
# Python 가상환경 활성화 (선택적)
.\venv\Scripts\Activate.ps1

# 의존성 설치
pip install -r requirements.txt

# AI 기능 사용 시 추가 설치
pip install -r requirements-ai.txt

# 환경 변수 설정 (세션용)
$env:OPENAI_API_KEY="your-api-key-here"

# .env 파일 생성/편집
if (-not (Test-Path .env)) {
    New-Item .env -ItemType File
}
Add-Content .env "OPENAI_API_KEY=your-api-key-here"
```

### Python 인터프리터로 직접 실행

**PowerShell에서 Python 스크립트 실행:**
```powershell
# 프로젝트 루트에서
cd api
python -c "from app.services.pdf_extract import PDFPlumberExtractor; from pathlib import Path; extractor = PDFPlumberExtractor(); blocks = extractor.extract_blocks(Path('data/pdfs/math.pdf')); print(f'추출된 블록 수: {len(blocks)}')"
```

**Python REPL에서:**
```powershell
cd api
python

# Python REPL에서:
>>> from app.services.pdf_extract import PDFPlumberExtractor
>>> from pathlib import Path
>>> extractor = PDFPlumberExtractor()
>>> pdf_path = Path("data/pdfs/2026 수능특강 수학Ⅰ.pdf")
>>> blocks = extractor.extract_blocks(pdf_path)
>>> print(f"추출된 블록 수: {len(blocks)}")
>>> print(f"첫 블록: {blocks[0] if blocks else '없음'}")
```

### 개별 추출 테스트

```python
from app.services.pdf_extract import PDFPlumberExtractor
from pathlib import Path

extractor = PDFPlumberExtractor()
pdf_path = Path("data/pdfs/math.pdf")
blocks = extractor.extract_blocks(pdf_path)

print(f"추출된 블록 수: {len(blocks)}")
print(f"블록 타입: {[b['type'] for b in blocks[:5]]}")
```

### 파서 테스트

```python
from app.services.subject_strategies.math import MathParser

parser = MathParser()
blocks = [...]  # 추출된 블록
result = parser.parse(blocks, metadata={"book_id": "test"})

print(f"파싱된 단위 수: {len(result.get('units', []))}")
```

---

## 관련 문서

- [PDF_EXTRACTION_TEST.md](./PDF_EXTRACTION_TEST.md) - 테스트 가이드
- [PDF_PROCESSING_PIPELINE.md](./PDF_PROCESSING_PIPELINE.md) - 파이프라인 설계 문서
- [AI_ML_PDF_EXTRACTION.md](./AI_ML_PDF_EXTRACTION.md) - AI/ML 기능 상세 설명
- [MATH1_EXTRACTION_PROMPTS.md](./MATH1_EXTRACTION_PROMPTS.md) - 수학Ⅰ 추출 프롬프트
- [LITERATURE_EXTRACTION_PROMPTS.md](./LITERATURE_EXTRACTION_PROMPTS.md) - 문학 추출 프롬프트
- [ENGLISH_EXTRACTION_PROMPTS.md](./ENGLISH_EXTRACTION_PROMPTS.md) - 영어 추출 프롬프트

---

## 다음 단계

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

---

**작성일**: 2025-01-XX  
**최종 수정일**: 2025-01-XX
