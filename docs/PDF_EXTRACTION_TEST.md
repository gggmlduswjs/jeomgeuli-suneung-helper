# PDF 추출 테스트 가이드

새 아키텍처 기반 PDF 추출 기능 테스트 방법입니다.

## 🚀 빠른 시작

### 1. 기본 PDF 추출 테스트

```bash
cd api
python tests/test_pdf_extract.py
```

### 2. 필요한 파일 준비

PDF 파일을 `data/pdfs/` 폴더에 배치:
```
data/
└── pdfs/
    ├── 2026 수능특강 수학Ⅰ.pdf
    ├── 2026 수능특강 영어.pdf
    └── 2026 수능특강 문학.pdf
```

## 📋 테스트 항목

### ✅ 필수 테스트

1. **기본 PDF 추출** (PDFPlumber)
   - 텍스트 블록 추출
   - 이미지 블록 추출
   - 테이블 블록 추출

2. **문학 PDF 추출** (LiteraturePDFExtractor)
   - 줄 단위 텍스트 추출
   - 레이아웃 정보 보존

### 🔍 선택적 테스트

3. **Enhanced OCR**
   - 스캔본 PDF 처리
   - OCR + 전처리
   - Tesseract 필요

4. **AI 텍스트 후처리**
   - OCR 오류 수정
   - 텍스트 정리
   - OpenAI API 키 필요

## 🛠️ 설정 방법

### Enhanced OCR 사용

```bash
# Tesseract 설치 (Windows)
# https://github.com/UB-Mannheim/tesseract/wiki 에서 다운로드

# 패키지 설치
pip install pytesseract opencv-python
```

### AI 텍스트 후처리 사용

```bash
# 패키지 설치
pip install -r requirements-ai.txt

# 또는 개별 설치
pip install openai langchain

# .env 파일에 API 키 설정
# OPENAI_API_KEY=your-api-key
```

## 📊 테스트 결과 예시

```
🚀 PDF 추출 테스트 시작

============================================================
📄 기본 PDF 추출 테스트 (PDFPlumber)
============================================================

📖 PDF 파일: 2026 수능특강 수학Ⅰ.pdf
📊 파일 크기: 15.23 MB

🔄 PDF 추출 중...
✅ 추출 완료!

📊 추출 결과:
   - 총 블록 수: 1234개
   - 블록 타입별 통계:
     • text: 1100개
     • image: 120개
     • table: 14개

📝 처음 5개 블록 샘플:
   1. [text] 01 지수 ...
   2. [text] 개념 ...
   3. [image] ...
   4. [text] 예제 1 ...
   5. [text] 다음 중 ...

============================================================
📚 문학 PDF 추출 테스트
============================================================
...

============================================================
📊 테스트 결과 요약
============================================================
   basic         : ✅ 통과
   literature    : ✅ 통과
   ocr           : ⏭️  스킵 (선택적)
   ai            : ⏭️  스킵 (선택적)

✅ 필수 테스트 모두 통과!
```

## 🔧 문제 해결

### PDF 파일을 찾을 수 없음

```
❌ PDF 파일을 찾을 수 없습니다: .../data/pdfs
   data/pdfs/ 폴더에 PDF 파일을 넣어주세요.
```

**해결:**
- `data/pdfs/` 폴더에 PDF 파일을 배치
- 파일 경로 확인: `python -c "from app.core.config import settings; print(settings.PDFS_DIR)"`

### Enhanced OCR 사용 불가

```
⚠️ Enhanced OCR을 사용할 수 없습니다.
   pip install pytesseract opencv-python
```

**해결:**
```bash
pip install pytesseract opencv-python
# Tesseract 설치 필요 (Windows: https://github.com/UB-Mannheim/tesseract/wiki)
```

### AI 후처리 사용 불가

```
⚠️ OPENAI_API_KEY가 설정되지 않았습니다.
   .env 파일에 OPENAI_API_KEY를 설정하세요.
```

**해결:**
1. `api/.env` 파일 생성
2. `OPENAI_API_KEY=your-api-key` 추가
3. 또는 환경변수로 설정: `$env:OPENAI_API_KEY="your-api-key"`

## 📝 개별 테스트 실행

### 기본 추출만 테스트

```python
from app.services.pdf_extract import PDFPlumberExtractor
from pathlib import Path

extractor = PDFPlumberExtractor()
pdf_path = Path("data/pdfs/2026 수능특강 수학Ⅰ.pdf")
blocks = extractor.extract_blocks(pdf_path)

print(f"추출된 블록 수: {len(blocks)}개")
```

### 문학 추출만 테스트

```python
from app.services.pdf_extract import LiteraturePDFExtractor
from pathlib import Path

extractor = LiteraturePDFExtractor()
pdf_path = Path("data/pdfs/2026 수능특강 문학.pdf")
lines = extractor.extract_blocks(pdf_path)

print(f"추출된 줄 수: {len(lines)}줄")
```

## 🔗 관련 문서

- [AI_ML_PDF_EXTRACTION.md](./AI_ML_PDF_EXTRACTION.md) - AI/ML 기능 상세 설명
- [MATH1_EXTRACTION_PROMPTS.md](./MATH1_EXTRACTION_PROMPTS.md) - 수학Ⅰ 추출 가이드
- [LITERATURE_EXTRACTION_PROMPTS.md](./LITERATURE_EXTRACTION_PROMPTS.md) - 문학 추출 가이드
- [ENGLISH_EXTRACTION_PROMPTS.md](./ENGLISH_EXTRACTION_PROMPTS.md) - 영어 추출 가이드
