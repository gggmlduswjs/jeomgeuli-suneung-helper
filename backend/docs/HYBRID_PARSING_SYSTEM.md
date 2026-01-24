# 하이브리드 파싱 시스템 문서

## 개요

하이브리드 파싱 시스템은 EBS 교재 PDF를 자동으로 파싱하기 위한 시스템입니다. 템플릿 매칭(빠른 경로)과 AI 분석(정확한 경로)을 신뢰도 기반으로 자동 선택하여 관리자 개입을 최소화합니다.

## 아키텍처

```
PDF 업로드
    ↓
OCR/텍스트 추출
    ↓
HybridRouter
    ├─ 템플릿 매칭 시도 (2-5초)
    │   ├─ 성공 (신뢰도 ≥ 85%) → 템플릿 파서 사용
    │   └─ 실패 → 다음 단계
    ├─ AI 파싱 시도 (60-120초)
    │   ├─ 성공 → AI 파서 사용
    │   └─ 실패 → 폴백
    └─ 폴백 → config.json 기반 파서
```

## 주요 컴포넌트

### 1. TemplateManager
**위치**: `backend/app/infrastructure/pdf/parsers/template_manager.py`

**기능**:
- 템플릿 로드/저장
- PDF 텍스트와 템플릿 매칭
- 신뢰도 계산

**사용 예시**:
```python
from app.infrastructure.pdf.parsers.template_manager import TemplateManager

manager = TemplateManager()
result = manager.match_template(
    pdf_text="1강 시의 표현과 형식\n01\n02",
    subject="literature",
    threshold=0.85
)

if result:
    template, confidence = result
    print(f"매칭된 템플릿: {template.name}, 신뢰도: {confidence}")
```

### 2. HybridRouter
**위치**: `backend/app/infrastructure/pdf/parsers/hybrid_router.py`

**기능**:
- 템플릿 매칭 → AI 파싱 → 폴백 순서로 파서 선택
- 성능 메트릭 수집
- 캐싱 지원

**사용 예시**:
```python
from app.infrastructure.pdf.parsers.hybrid_router import HybridRouter

router = HybridRouter(template_threshold=0.85)
parser, strategy, metadata = router.select_parser(
    subject="literature",
    ocr_data=ocr_data,
    book_id="book_123"
)

print(f"사용된 전략: {strategy}")
print(f"처리 시간: {metadata['processing_time']:.2f}초")
```

### 3. StructureAnalyzer
**위치**: `backend/app/infrastructure/ai/genai/structure_analyzer.py`

**기능**:
- LLM을 사용한 PDF 구조 자동 분석
- 파싱 규칙 생성

**사용 예시**:
```python
from app.infrastructure.ai.genai.structure_analyzer import StructureAnalyzer

analyzer = StructureAnalyzer(api_key="sk-...")
structure = analyzer.analyze_from_ocr_data(
    ocr_data=ocr_data,
    subject="literature"
)

print(f"강의 패턴: {structure.lecture_title_patterns}")
print(f"문제 패턴: {structure.problem_number_pattern}")
```

### 4. AIParser
**위치**: `backend/app/infrastructure/pdf/parsers/ai_parser.py`

**기능**:
- LLM 구조 분석 → 규칙 생성 → 파싱 실행

## 성능 목표

| 지표 | 목표 | 측정 방법 |
|-----|------|----------|
| 기존 교재 처리 시간 | 2-5초 | 템플릿 매칭 성공 시 |
| 신규 교재 처리 시간 | 60-120초 | AI 파싱 사용 시 |
| 파싱 정확도 | 89-95% | 강의/문제 추출 정확도 |
| 관리자 개입 | 10% | 수동 config.json 작성 비율 |
| 템플릿 매칭률 | 80%+ | 기존 교재 중 템플릿 매칭 성공률 |

## 사용 방법

### 1. 기존 config.json을 템플릿으로 변환

```bash
cd backend
python scripts/convert_config_to_template.py --all --version 2026
```

### 2. 템플릿 수동 생성

```python
from app.infrastructure.pdf.parsers.template import ParsingTemplate
from app.infrastructure.pdf.parsers.template_manager import TemplateManager

template = ParsingTemplate(
    name="ebs_수능특강_문학_2026",
    subject="literature",
    version="2026",
    patterns={
        "lecture_title_patterns": [r'^\d+강\s+[가-힣]+'],
        "problem_number_pattern": r'^\d{2}$'
    },
    config={
        "toc_end_page": 7,
        "start_content_page": 8
    },
    confidence=0.85
)

manager = TemplateManager()
manager.add_template(template)
```

### 3. 파이프라인 사용 (자동)

UnifiedPipeline이 자동으로 HybridRouter를 사용합니다:

```python
from app.infrastructure.pdf.pipeline import UnifiedPipeline

pipeline = UnifiedPipeline(
    subject="literature",
    use_ocr=True,
    book_id="book_123"
)

result = pipeline.process(pdf_path)
# 자동으로 템플릿 매칭 → AI 파싱 → 폴백 순서로 시도
```

## 성능 모니터링

HybridRouter의 메트릭 확인:

```python
router = HybridRouter()
metrics = router.get_metrics()

print(f"템플릿 매칭률: {metrics['template_match_rate']:.2%}")
print(f"AI 파싱 사용률: {metrics['ai_parsing_rate']:.2%}")
print(f"폴백 사용률: {metrics['fallback_rate']:.2%}")
print(f"평균 처리 시간 (템플릿): {metrics['template_avg_time']:.2f}초")
print(f"평균 처리 시간 (AI): {metrics['ai_avg_time']:.2f}초")
```

## 캐싱

템플릿 매칭 결과와 AI 파싱 결과는 교재 ID 기반으로 캐싱됩니다:

- **템플릿 매칭 캐시**: 동일 교재 재파싱 시 즉시 매칭
- **AI 파서 캐시**: 동일 교재 재파싱 시 AI 분석 결과 재사용

캐시 초기화:
```python
router.clear_cache()
```

## 문제 해결

### 템플릿이 매칭되지 않음
1. 템플릿이 `backend/data/templates/`에 있는지 확인
2. 템플릿의 패턴이 PDF 텍스트와 일치하는지 확인
3. 신뢰도 임계값을 낮춰보기 (기본값: 0.85)

### AI 파싱이 작동하지 않음
1. OpenAI API 키가 설정되어 있는지 확인
2. `enable_ai_parsing=True`로 설정되어 있는지 확인
3. LLM 모델이 사용 가능한지 확인

### 성능이 느림
1. 템플릿 매칭률 확인 (낮으면 템플릿 추가)
2. 캐싱 활성화 확인
3. AI 파싱은 신규 교재에만 사용되도록 설정

## 향후 개선 사항

1. **템플릿 자동 학습**: AI 파싱 결과를 템플릿으로 자동 저장
2. **분산 캐싱**: Redis 등을 사용한 분산 캐시
3. **실시간 모니터링**: 대시보드에서 실시간 메트릭 확인
4. **A/B 테스팅**: 여러 파싱 전략 비교
