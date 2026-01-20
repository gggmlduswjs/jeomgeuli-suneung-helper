# Deep Learning Module (Level 2)

**Level 2 DL Features** - 딥러닝 모델 도입

이 모듈은 파이프라인의 **Extraction 단계**에서 실행되는 딥러닝 기능들을 제공합니다.

---

## 🎯 목적

채용 요건 증명:
- ✅ CNN/RNN/Transformer 구조 이해
- ✅ PyTorch, Hugging Face 활용
- ✅ 멀티모달 AI (Vision + Language)
- ✅ Image-to-Sequence 생성

---

## 📦 구현된 기능

### 1. **Document Layout Analyzer** (Level 2.1)

**파일**: `layout_analyzer.py`

**기능**:
- LayoutLMv3 기반 Visual Document Understanding
- 이미지 + 텍스트 + 레이아웃을 동시에 이해
- 블록 타입 자동 분류 (Title, Text, List, Table, Figure)
- Pre-trained 모델 inference (fine-tuning 선택적)

**파이프라인 단계**: **Extraction** (OCR 직후)

**AI 역량 증명**:
- **Transformer 구조 이해** (Vision + Language)
- Hugging Face Transformers 활용
- 멀티모달 모델 inference
- SOTA 모델 실무 적용

**사용 예시**:
```python
from app.dl import DocumentLayoutAnalyzer
from PIL import Image

analyzer = DocumentLayoutAnalyzer(
    model_name="microsoft/layoutlmv3-base",
    use_gpu=False
)

# 이미지 + OCR 결과
image = Image.open("page.png")
ocr_data = [{"text": "...", "bbox": [x0, y0, x1, y1]}, ...]

result = analyzer.analyze(image, ocr_data)
for block in result.blocks:
    print(f"{block['type']}: {block['text'][:50]}")
```

**모델 구조**:
```
LayoutLMv3 Architecture:
┌─────────────────────────────────────┐
│ Vision Transformer (ViT)            │  ← 이미지 특징 추출 (CNN)
├─────────────────────────────────────┤
│ Text Transformer (BERT)             │  ← 텍스트 인코딩
├─────────────────────────────────────┤
│ Layout Embeddings                   │  ← 위치 정보 (2D bbox)
├─────────────────────────────────────┤
│ Multimodal Fusion                   │  ← Vision + Text + Layout 통합
├─────────────────────────────────────┤
│ Token Classification Head           │  ← 블록 타입 예측
└─────────────────────────────────────┘
```

**이력서 어필 예시**:
> "LayoutLMv3를 교육 콘텐츠 도메인에 적용하여 블록 분류 자동화. Hugging Face Transformers로 멀티모달 문서 이해 파이프라인 구축. Vision Transformer + Text Encoder를 활용한 Document Understanding 경험"

---

### 2. **Math Expression Recognizer** (Level 2.2)

**파일**: `math_recognizer.py`

**기능**:
- TrOCR 기반 수식 이미지 → LaTeX 변환
- Vision Transformer (ViT) + Text Transformer Decoder
- Image-to-Sequence 생성
- 수식 영역 자동 탐지 및 일괄 처리

**파이프라인 단계**: **Extraction** (수식 영역 특화)

**AI 역량 증명**:
- **CNN 구조 이해** (이미지 특징 추출)
- **Transformer 시퀀스 생성** (Decoder)
- Encoder-Decoder 아키텍처
- 도메인 특화 모델 활용

**사용 예시**:
```python
from app.dl import MathExpressionRecognizer
from PIL import Image

recognizer = MathExpressionRecognizer(
    model_name="microsoft/trocr-base-handwritten",
    use_gpu=False
)

# 수식 이미지
math_image = Image.open("equation.png")

result = recognizer.recognize(math_image)
print(f"LaTeX: {result.latex}")
print(f"Confidence: {result.confidence:.3f}")
```

**모델 구조**:
```
TrOCR Architecture (Image-to-Sequence):
┌─────────────────────────────────────┐
│ Vision Transformer (ViT) Encoder    │  ← 이미지 → 특징 벡터 (CNN + Transformer)
│   - Patch Embedding                 │
│   - Multi-head Self-Attention       │
│   - Feed Forward                    │
└───────────┬─────────────────────────┘
            │ Encoder Output
┌───────────▼─────────────────────────┐
│ Text Transformer Decoder            │  ← 특징 벡터 → 텍스트 (AutoRegressive)
│   - Cross-Attention (to Encoder)    │
│   - Self-Attention                  │
│   - Token Generation (Beam Search)  │
└─────────────────────────────────────┘
```

**페이지 단위 처리**:
```python
# 페이지에서 수식 자동 탐지 + 인식
enhanced_ocr, math_predictions = recognizer.process_page_with_math(
    page_image,
    ocr_data,
    replace_in_ocr=True  # OCR 텍스트를 LaTeX로 교체
)

for pred in math_predictions:
    print(f"수식: {pred.latex}")
```

**이력서 어필 예시**:
> "TrOCR (Vision Transformer + Text Decoder)를 활용한 수식 인식 시스템 구축. CNN 기반 이미지 인코더와 Transformer 디코더를 결합한 Image-to-Sequence 모델 적용. 수학 콘텐츠 LaTeX 변환으로 교육 자료 디지털화 효율 개선"

---

## 🚀 통합 사용법

### DLExtractionProcessor (통합 파이프라인)

```python
from app.dl import DLExtractionProcessor
from PIL import Image

# Processor 생성
processor = DLExtractionProcessor(
    enable_layout_analysis=True,
    enable_math_recognition=True,
    use_gpu=False  # GPU 없으면 False
)

# 페이지 처리
page_image = Image.open("page.png")
ocr_data = [...]  # 기존 OCR 결과

result = processor.process_page(page_image, ocr_data)

# 결과
print(f"Layout blocks: {len(result['layout_analysis']['blocks'])}")
print(f"Math expressions: {result['math_recognition']['count']}")

# OCR 데이터 enrichment
enriched_ocr = processor.enrich_ocr_with_dl(page_image, ocr_data)
```

---

## 📊 출력 형식

### Layout Analysis 결과

```json
{
  "blocks": [
    {
      "type": "title",
      "text": "개념 설명",
      "bbox": [100, 50, 500, 100],
      "avg_score": 0.92,
      "tokens": ["개념", "설명"],
      "start_index": 0,
      "end_index": 1
    },
    {
      "type": "content",
      "text": "형상화는 시의 주제를...",
      "bbox": [100, 120, 500, 300],
      "avg_score": 0.87
    }
  ]
}
```

### Math Recognition 결과

```json
{
  "count": 3,
  "predictions": [
    {
      "latex": "x^2 + y^2 = r^2",
      "confidence": 0.95
    }
  ]
}
```

### Enriched OCR

```json
[
  {
    "text": "x^2 + y^2 = r^2",  // LaTeX로 교체됨
    "bbox": [200, 150, 300, 180],
    "is_math": true,
    "math_confidence": 0.95,
    "dl_metadata": {
      "layout_type": "content",
      "layout_confidence": 0.87
    }
  }
]
```

---

## 🔧 파이프라인 통합

### Extraction 단계에 통합

```python
# textbook_pipeline.py

from app.dl import DLExtractionProcessor

class TextbookPipeline:
    def __init__(self, ...):
        # ...
        self.dl_processor = DLExtractionProcessor(
            enable_layout_analysis=True,
            enable_math_recognition=True,
            use_gpu=False
        )

    def process_pdf(self, pdf_path):
        # 1. Extraction
        ocr_data = self.extractor.extract(pdf_path)

        # 2. DL Enhancement (NEW!)
        for page in ocr_data["pages"]:
            page_image = self._load_page_image(page["page_num"])
            enhanced = self.dl_processor.enrich_ocr_with_dl(
                page_image,
                page["text_blocks"]
            )
            page["text_blocks"] = enhanced

        # 3. Parsing
        parsed_data = self.parser.parse(ocr_data)

        # ...
```

---

## 📈 성능 최적화

### GPU 사용

```python
processor = DLExtractionProcessor(use_gpu=True)

# CUDA 확인
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"Device count: {torch.cuda.device_count()}")
```

### 배치 처리

```python
# 여러 수식 동시 처리
math_images = [...]
results = recognizer.recognize_batch(math_images, num_beams=4)
```

### 모델 캐싱

모델은 한 번만 로드되고 메모리에 유지됩니다 (싱글톤 패턴).

---

## 📦 의존성

```bash
# 필수
pip install transformers
pip install torch
pip install pillow

# GPU 가속 (선택)
pip install torch --index-url https://download.pytorch.org/whl/cu118

# LayoutLMv3 (선택)
pip install layoutparser
```

**모델 다운로드** (자동):
- LayoutLMv3: ~1GB (최초 1회)
- TrOCR: ~500MB (최초 1회)

---

## 🎓 AI 역량 증명 포인트

이 모듈을 통해 증명할 수 있는 역량:

1. **Transformer 구조 이해**:
   - Vision Transformer (ViT)
   - Text Transformer (BERT/GPT)
   - Multimodal Fusion

2. **CNN 이해**:
   - 이미지 특징 추출
   - Patch Embedding

3. **Encoder-Decoder 아키텍처**:
   - Image-to-Sequence
   - Beam Search 생성
   - Cross-Attention

4. **Hugging Face 생태계**:
   - Transformers 라이브러리
   - Pre-trained 모델 활용
   - Processor 및 Tokenizer

5. **멀티모달 AI**:
   - Vision + Language
   - Layout + Text 통합
   - 도메인 특화 적용

---

## 🧪 Fine-tuning 가이드 (선택사항)

### LayoutLMv3 Fine-tuning

교재 도메인에 특화하려면:

1. **데이터 준비**: 50-100 annotated pages
   - 이미지 + OCR + 블록 레이블
   - COCO 또는 PubLayNet 형식

2. **학습 스크립트**:
```python
from transformers import Trainer, TrainingArguments

model = LayoutLMv3ForTokenClassification.from_pretrained(
    "microsoft/layoutlmv3-base",
    num_labels=len(label_list)
)

training_args = TrainingArguments(
    output_dir="./layoutlm-finetuned",
    per_device_train_batch_size=2,
    num_train_epochs=10,
    learning_rate=5e-5
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset
)

trainer.train()
```

### TrOCR Fine-tuning (수식 특화)

1. **데이터 준비**: 수식 이미지 + LaTeX 쌍
2. **학습**: Seq2Seq 학습 파이프라인

---

## 📝 TODO (향후 개선)

- [ ] LayoutLMv3 fine-tuning 스크립트
- [ ] LaTeX 특화 TrOCR 모델 통합
- [ ] Semantic Segmentation (블록 경계 탐지)
- [ ] 정확도 평가 및 벤치마크

---

**작성일**: 2026-01-20
**버전**: 1.0.0
**Status**: ✅ 구현 완료
