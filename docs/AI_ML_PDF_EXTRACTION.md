# AI/ML PDF 추출 기능 구현 가이드

이 문서는 점글이 수능 헬퍼 프로젝트의 PDF 추출 파이프라인에 AI/ML 기술을 적용한 구현 가이드입니다.

## 📋 목차

1. [개요](#개요)
2. [구현된 기능](#구현된-기능)
3. [사용 방법](#사용-방법)
4. [적용 위치 및 통합](#적용-위치-및-통합)
5. [향후 계획](#향후-계획)
6. [참고 자료](#참고-자료)

---

## 개요

### 현재 PDF 추출 파이프라인의 한계

기존 PDF 추출 시스템은 다음과 같은 한계가 있습니다:

1. **텍스트 추출 오류**
   - 스캔본 PDF 처리 불가
   - OCR 오류 수정 없음
   - 이미지 기반 텍스트 추출 미흡

2. **구조 인식의 한계**
   - 정규식 기반 규칙 파싱만 사용
   - 문제/지문/보기 분류가 패턴 매칭에 의존
   - 복잡한 레이아웃 처리 어려움

3. **수식 처리 부족**
   - 수식 이미지 감지가 bbox 기반 휴리스틱
   - 수식 → LaTeX 변환 없음
   - 점자 변환(Nemeth) 연결 부재

### AI/ML 적용 목표

다음 영역에서 AI/ML 기술을 적용하여 추출 정확도와 자동화 수준을 향상시킵니다:

1. **OCR 품질 향상** → Enhanced OCR
2. **텍스트 후처리** → AI Text Postprocessor
3. **구조 자동 분류** → AI Structure Classifier
4. **수식 인식** → Math OCR (향후)
5. **레이아웃 분석** → Layout Analysis (향후)

---

## 구현된 기능

### 1. Enhanced OCR (`api/app/services/pdf_extract/enhanced_ocr.py`)

**기능:**
- 이미지 전처리 (이진화, 노이즈 제거, 기울기 보정)
- Tesseract OCR 통합
- 레이아웃 정보 보존 (bbox, confidence)

**사용 예시:**
```python
from app.services.pdf_extract.enhanced_ocr import EnhancedOCR
from pathlib import Path

# OCR 인스턴스 생성
ocr = EnhancedOCR(lang='kor+eng', dpi=300)

# PDF에서 텍스트 추출
pdf_path = Path("data/pdfs/2026 수능특강 수학Ⅰ.pdf")
result = ocr.extract_from_pdf(pdf_path)

print(f"추출된 텍스트 길이: {len(result['text'])} 문자")
print(f"블록 수: {result['total_blocks']}개")

# 단일 페이지 이미지에서 추출
from PIL import Image
page_image = Image.open("page1.png")
page_result = ocr.extract_from_page_image(page_image, page_num=1)
```

**주요 메서드:**
- `preprocess_image(image)`: 이미지 전처리
- `extract_text_with_ocr(image)`: 순수 텍스트 추출
- `extract_with_layout(image)`: 레이아웃 정보 포함 추출
- `extract_from_pdf(pdf_path)`: PDF 전체 추출

---

### 2. AI Text Postprocessor (`api/app/services/pdf_extract/ai_text_postprocessor.py`)

**기능:**
- LLM(GPT-4) 기반 텍스트 정리
- OCR 오류 자동 수정
- 문장 구조 정규화
- 한글/영어 혼합 텍스트 처리

**사용 예시:**
```python
from app.services.pdf_extract.ai_text_postprocessor import AITextPostProcessor

# AI 후처리기 생성
postprocessor = AITextPostProcessor(model="gpt-4o-mini", temperature=0.0)

# 텍스트 정리
raw_text = "다 음 문 제를 읽고 답하시오..."  # OCR 오류 포함
cleaned = postprocessor.clean_extracted_text(raw_text, subject="korean")

# OCR 오류 수정
error_text = "1. 다음 중 0 (영)이 아닌 것은?"
fixed = postprocessor.fix_ocr_errors(error_text, context="수학 문제")

# Fallback: AI 없이 사용 (기본 정리만)
from app.services.pdf_extract.ai_text_postprocessor import BasicTextPostProcessor
basic = BasicTextPostProcessor()
cleaned = basic.clean_extracted_text(raw_text)
```

**주요 메서드:**
- `clean_extracted_text(raw_text, subject)`: 텍스트 정리
- `fix_ocr_errors(text, context)`: OCR 오류 수정

**설정:**
- `model`: OpenAI 모델명 (기본: "gpt-4o-mini")
- `temperature`: 생성 온도 (기본: 0.0)
- `use_langchain`: LangChain 사용 여부 (기본: True)

---

### 3. AI Structure Classifier (`api/app/services/pdf_parse/ai_structure_classifier.py`)

**기능:**
- BERT 기반 블록 타입 분류
- 문제/지문/보기/헤더/푸터 자동 인식
- 규칙 기반 Fallback 제공

**사용 예시:**
```python
from app.services.pdf_parse.ai_structure_classifier import AIStructureClassifier

# 구조 분류기 생성
classifier = AIStructureClassifier(model_name="skt/kobert-base-v1")

# 단일 블록 분류
text = "1. 다음 중 옳은 것은?"
result = classifier.classify_block(text, context="수학 문제")

print(f"타입: {result['type']}")  # "question"
print(f"신뢰도: {result['confidence']:.2f}")  # 0.85

# 배치 분류
blocks = [
    {"text": "The quick brown fox...", "context": "지문"},
    {"text": "1. 다음 중...", "context": "문제"},
    {"text": "① 첫 번째 보기", "context": "보기"},
]
classified = classifier.classify_batch(blocks)

# Fallback: 규칙 기반만 사용
from app.services.pdf_parse.ai_structure_classifier import get_structure_classifier
rule_based = get_structure_classifier(use_ai=False)
result = rule_based.classify_block(text)
```

**주요 메서드:**
- `classify_block(text, context, metadata)`: 단일 블록 분류
- `classify_batch(blocks)`: 배치 분류

**분류 타입:**
- `passage`: 지문
- `question`: 문제
- `choice`: 보기
- `header`: 헤더/제목
- `footer`: 푸터/페이지 번호
- `other`: 기타

**참고:**
- Fine-tuned 모델이 필요합니다 (향후 구현)
- 현재는 규칙 기반 Fallback 제공

---

## 사용 방법

### 환경 설정

#### 1. 필요한 패키지 설치

**기본 기능 (Enhanced OCR):**
```bash
# requirements.txt에 이미 포함됨
pip install -r requirements.txt
```

**AI 기능 (선택적):**
```bash
# AI 기능 전체 설치
pip install -r requirements-ai.txt

# 또는 개별 설치
# Enhanced OCR (기본)
pip install pytesseract opencv-python

# AI Text Postprocessor
pip install openai langchain

# AI Structure Classifier
pip install transformers torch

# Math OCR (PaddleOCR, 오픈소스)
pip install paddleocr

# Math OCR (MathPix, 상용, 선택적)
pip install mathpix-python
```

#### 2. Tesseract 설치 (Windows)

1. [Tesseract 설치 프로그램](https://github.com/UB-Mannheim/tesseract/wiki) 다운로드
2. 설치 경로: `C:\Program Files\Tesseract-OCR\tesseract.exe`
3. 한글 언어 팩 포함 설치

#### 3. OpenAI API 키 설정

```bash
# 환경변수 설정
export OPENAI_API_KEY="your-api-key"

# 또는 .env 파일
OPENAI_API_KEY=your-api-key
```

### 통합 예시

#### PDF 추출 파이프라인에 통합

```python
# api/app/services/pdf_extract.py 수정 예시
from app.services.pdf_extract.enhanced_ocr import EnhancedOCR
from app.services.pdf_extract.ai_text_postprocessor import get_text_postprocessor
from app.services.pdf_parse.ai_structure_classifier import get_structure_classifier

def extract_text_from_pdf(pdf_path: Path, use_ai: bool = True) -> Optional[str]:
    """PDF 텍스트 추출 (AI 보강)"""
    # 1. 기본 추출 시도 (pdfplumber)
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = "\n\n".join([page.extract_text() for page in pdf.pages])
            if text and len(text) > 100:
                # 기본 추출 성공
                pass
            else:
                # 텍스트 부족 → OCR 사용
                raise ValueError("텍스트 부족, OCR 시도")
    except Exception:
        # OCR Fallback
        ocr = EnhancedOCR(lang='kor+eng')
        result = ocr.extract_from_pdf(pdf_path)
        text = result['text']
    
    # 2. AI 후처리 (선택적)
    if use_ai:
        postprocessor = get_text_postprocessor(use_ai=True)
        text = postprocessor.clean_extracted_text(text)
    
    return text
```

#### 구조 분류기 통합

```python
# api/app/services/subject_strategies/english.py 수정 예시
from app.services.pdf_parse.ai_structure_classifier import get_structure_classifier

class EnglishParser(BaseParser):
    def __init__(self):
        super().__init__()
        # AI 구조 분류기 추가
        self.classifier = get_structure_classifier(use_ai=True)
    
    def detect_content_type(self, block: Dict[str, Any]) -> str:
        """AI 보강된 콘텐츠 타입 감지"""
        text = block.get("content", "")
        
        # AI 분류 결과 활용
        ai_result = self.classifier.classify_block(text)
        ai_type = ai_result["type"]
        ai_confidence = ai_result["confidence"]
        
        # 기존 규칙 기반 감지
        rule_type = self._detect_with_rules(text)
        
        # AI 신뢰도가 높으면 AI 결과 우선 사용
        if ai_confidence > 0.8:
            type_map = {
                "passage": "passage",
                "question": "question",
                "choice": "choice",
            }
            return type_map.get(ai_type, rule_type)
        
        return rule_type
```

---

## 적용 위치 및 통합

### Phase 1: 즉시 적용 가능 ✅

#### 1. Enhanced OCR 통합

**파일:** `api/app/services/pdf_extract/pdfplumber_extractor.py`

```python
class PDFPlumberExtractor(BaseExtractor):
    def __init__(self, use_ocr_fallback: bool = True):
        self.use_ocr_fallback = use_ocr_fallback
        if use_ocr_fallback:
            from app.services.pdf_extract.enhanced_ocr import EnhancedOCR
            self.ocr = EnhancedOCR(lang='kor+eng')
    
    def extract_blocks(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """기존 로직 + OCR Fallback"""
        try:
            # 기존 pdfplumber 추출 시도
            blocks = self._extract_with_pdfplumber(pdf_path)
            
            # 텍스트 부족 시 OCR Fallback
            if self.use_ocr_fallback and self._is_text_insufficient(blocks):
                ocr_blocks = self._extract_with_ocr(pdf_path)
                return self._merge_blocks(blocks, ocr_blocks)
            
            return blocks
        except Exception as e:
            if self.use_ocr_fallback:
                return self._extract_with_ocr(pdf_path)
            raise
```

#### 2. AI Text Postprocessor 통합

**파일:** `api/app/services/pdf_extract.py`

```python
def extract_text_from_pdf(pdf_path: Path, use_ai_postprocess: bool = False) -> Optional[str]:
    """기존 함수 + AI 후처리 옵션"""
    # 기존 추출 로직
    text = _extract_with_pdfplumber(pdf_path)
    
    # AI 후처리 (선택적)
    if use_ai_postprocess and text:
        from app.services.pdf_extract.ai_text_postprocessor import get_text_postprocessor
        postprocessor = get_text_postprocessor(use_ai=True)
        text = postprocessor.clean_extracted_text(text)
    
    return text
```

#### 3. AI Structure Classifier 통합

**파일:** `api/app/services/subject_strategies/english.py`, `math1.py`, `literature.py`

```python
# 각 Parser 클래스에 통합
class EnglishParser(BaseParser):
    def __init__(self):
        super().__init__()
        from app.services.pdf_parse.ai_structure_classifier import get_structure_classifier
        self.classifier = get_structure_classifier(use_ai=True)
    
    def detect_content_type(self, block: Dict[str, Any]) -> str:
        """AI + 규칙 하이브리드"""
        ai_result = self.classifier.classify_block(block.get("content", ""))
        rule_result = self._detect_with_rules(block)
        
        # AI 신뢰도가 높으면 AI 결과 사용
        if ai_result["confidence"] > 0.8:
            return self._map_ai_type(ai_result["type"])
        return rule_result
```

### Phase 2: 중기 계획

#### 1. 수식 인식 (Math OCR)

**구현 파일:** `api/app/services/pdf_extract/math_ocr.py` (향후)

```python
class MathOCR:
    """수식 이미지 → LaTeX 변환"""
    
    def __init__(self):
        # MathPix API 또는 PaddleOCR
        pass
    
    def image_to_latex(self, image: Image.Image) -> str:
        """수식 이미지 → LaTeX"""
        pass
    
    def latex_to_braille(self, latex: str) -> str:
        """LaTeX → Nemeth 점자"""
        pass
```

**통합 위치:**
- `api/app/services/subject_strategies/math1.py`
- `Math1Parser._is_formula_image()` → 실제 수식 인식으로 개선

#### 2. 레이아웃 분석 (LayoutLM)

**구현 파일:** `api/app/services/pdf_extract/ai_layout_analyzer.py` (향후)

```python
class AILayoutAnalyzer:
    """Vision 기반 레이아웃 분석"""
    
    def analyze_page_layout(self, page_image: Image.Image) -> List[Dict]:
        """텍스트/이미지/테이블 블록 자동 감지"""
        pass
```

**통합 위치:**
- `api/app/services/pdf_extract/pdfplumber_extractor.py`
- `PDFPlumberExtractor._group_words_to_blocks()` → AI 레이아웃 분석 결과 활용

---

## 향후 계획

### Phase 1: 즉시 적용 가능 ✅ (완료)

- [x] Enhanced OCR 구현
- [x] AI Text Postprocessor 구현
- [x] AI Structure Classifier 기본 구조 구현

### Phase 2: 중기 계획 (1-2개월)

- [ ] 수식 인식 (MathPix / PaddleOCR)
- [ ] AI Structure Classifier Fine-tuning
- [ ] 테스트 및 성능 평가

### Phase 3: 장기 계획 (3-6개월)

- [ ] 레이아웃 분석 (LayoutLM)
- [ ] 테이블 구조 추출 (TableNet)
- [ ] 다국어 처리 개선 (XLM-RoBERTa)

---

## 테스트

### Enhanced OCR 테스트

```python
# api/test_enhanced_ocr.py
from app.services.pdf_extract.enhanced_ocr import EnhancedOCR
from pathlib import Path

def test_ocr():
    ocr = EnhancedOCR(lang='kor+eng')
    pdf_path = Path("../data/pdfs/2026 수능특강 수학Ⅰ.pdf")
    result = ocr.extract_from_pdf(pdf_path)
    print(f"추출 성공: {result['total_blocks']}개 블록")
```

### AI Text Postprocessor 테스트

```python
# api/test_ai_postprocessor.py
from app.services.pdf_extract.ai_text_postprocessor import AITextPostProcessor

def test_postprocessor():
    postprocessor = AITextPostProcessor(model="gpt-4o-mini")
    raw_text = "다 음 문 제를 읽고..."
    cleaned = postprocessor.clean_extracted_text(raw_text)
    print(f"정리 완료: {len(cleaned)} 문자")
```

### AI Structure Classifier 테스트

```python
# api/test_ai_classifier.py
from app.services.pdf_parse.ai_structure_classifier import AIStructureClassifier

def test_classifier():
    classifier = AIStructureClassifier()
    test_blocks = [
        "The quick brown fox jumps over the lazy dog.",
        "1. 다음 중 옳은 것은?",
        "① 첫 번째 보기",
    ]
    for text in test_blocks:
        result = classifier.classify_block(text)
        print(f"{text[:30]}... → {result['type']} ({result['confidence']:.2f})")
```

---

## 참고 자료

### 라이브러리 문서

- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [OpenAI API](https://platform.openai.com/docs)
- [LangChain](https://python.langchain.com/)
- [Transformers (Hugging Face)](https://huggingface.co/docs/transformers)

### 관련 문서

- [AI_ML_IMPLEMENTATION_PROPOSAL.md](./AI_ML_IMPLEMENTATION_PROPOSAL.md) - 전체 AI/ML 제안서
- [PDF_PROCESSING_PIPELINE.md](./PDF_PROCESSING_PIPELINE.md) - PDF 처리 파이프라인 개요

### 모델 Fine-tuning 가이드 (향후)

1. **AI Structure Classifier Fine-tuning**
   - 데이터셋: 수능특강 PDF 블록 + 라벨
   - 모델: KoBERT 또는 다국어 BERT
   - 목표: 문제/지문/보기 분류 정확도 90% 이상

2. **레이아웃 분석 모델 학습**
   - 데이터셋: PDF 페이지 이미지 + 레이아웃 라벨
   - 모델: LayoutLMv3 또는 DETR
   - 목표: 블록 타입 자동 감지 정확도 95% 이상

---

## 문제 해결

### Tesseract 설치 오류

**Windows:**
```python
# 자동 경로 감지 실패 시 수동 설정
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### OpenAI API 키 오류

```python
# 환경변수 확인
import os
print(os.getenv("OPENAI_API_KEY"))

# 또는 코드에서 직접 설정 (비권장, 보안 주의)
import openai
openai.api_key = "your-api-key"
```

### Transformers 모델 다운로드 오류

```bash
# Hugging Face 토큰 설정 (필요 시)
export HF_TOKEN="your-huggingface-token"
```

---

## 요약

이 문서는 PDF 추출 파이프라인에 AI/ML 기술을 적용하는 방법을 정리했습니다.

**완료된 기능:**
1. ✅ Enhanced OCR (전처리 + Tesseract)
2. ✅ AI Text Postprocessor (GPT-4)
3. ✅ AI Structure Classifier (BERT 기반, 규칙 Fallback)

**다음 단계:**
1. 실제 PDF로 테스트 및 성능 평가
2. Fine-tuned 모델 학습 (AI Structure Classifier)
3. 수식 인식 모듈 구현 (Math OCR)

각 기능은 **Fallback 메커니즘**을 제공하므로, AI 모델이 없어도 기본 기능은 동작합니다.
