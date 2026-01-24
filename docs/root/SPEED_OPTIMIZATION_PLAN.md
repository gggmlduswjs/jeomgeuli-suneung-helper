# 문학 파이프라인 속도 최적화 계획

## 현재 상태
- **처리 시간**: 40분 (300페이지 기준)
- **품질**: 매우 낮음 (CID 폰트 문제로 텍스트 깨짐)
- **병목 구간**: OCR (순차 처리)

## 최적화 전략

### Phase 1: 속도 최적화 (20분 → 5분)

#### 1.1 병렬 OCR 처리 (가장 효과적)
**예상 효과**: 40분 → 8분 (5배 속도 향상)
```python
# asyncio + ThreadPoolExecutor 사용
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def process_page_parallel(page_images):
    with ThreadPoolExecutor(max_workers=8) as executor:
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(executor, ocr_single_page, img)
            for img in page_images
        ]
        return await asyncio.gather(*tasks)
```

**구현 위치**: `backend/app/infrastructure/pdf/extractors/ocr_extractor.py`

#### 1.2 이미지 캐싱
**예상 효과**: 8분 → 6분 (중복 변환 제거)
```python
# 페이지 이미지를 메모리에 캐싱
self._page_image_cache = {}  # {page_num: PIL.Image}

# 한 번만 변환, 여러 번 재사용
if page_num not in self._page_image_cache:
    self._page_image_cache[page_num] = convert_from_path(...)
```

**구현 위치**: `backend/app/infrastructure/pdf/pipeline.py`

#### 1.3 배치 처리
**예상 효과**: 6분 → 5분 (초기화 오버헤드 감소)
```python
# 50페이지씩 배치로 처리
batch_size = 50
for i in range(0, len(pages), batch_size):
    batch = pages[i:i+batch_size]
    process_batch(batch)
```

### Phase 2: AI 파싱 활성화 (품질 개선)

#### 2.1 GPT-4를 이용한 텍스트 복구
**시간 증가**: +3분 (병렬 처리 시)
**품질 향상**: ★★★★★

```python
# 깨진 텍스트를 GPT-4가 복구
# "날 밤 이 싫어" → "날밤이 싫어"
# "2강|Alo]내용" → "2강 시의 내용"

from app.infrastructure.ai.genai.text_corrector import TextCorrector

corrector = TextCorrector()
corrected_texts = await corrector.batch_correct(ocr_texts)
```

**구현 방법**:
1. OCR 결과를 50개씩 배치로 묶음
2. GPT-4에 한 번에 전송 (배치 API)
3. 병렬 처리로 여러 배치 동시 실행

#### 2.2 섹션 추출 AI 개선
```python
# ImprovedSectionExtractor의 AI 모드 활성화
extractor = ImprovedSectionExtractor(
    enable_ai=True,
    api_key=settings.OPENAI_API_KEY
)
```

### Phase 3: 캐싱 시스템 (API 속도)

#### 3.1 Redis 캐싱
```python
# API 응답을 Redis에 캐싱
@cache(ttl=3600)  # 1시간 캐싱
async def get_lecture(lecture_id: int):
    ...
```

#### 3.2 메모리 캐싱
```python
# FastAPI에 LRU 캐시 추가
from functools import lru_cache

@lru_cache(maxsize=100)
def load_lecture_json(path: Path):
    with open(path) as f:
        return json.load(f)
```

## 최종 목표

### 성능
- **처리 시간**: 40분 → **8분** (AI 파싱 포함)
- **API 응답**: 500ms → **50ms** (캐싱)

### 품질
- **텍스트 정확도**: 30% → **95%**
- **섹션 추출**: 불완전 → **완전**
- **강의 구조**: 부분 → **완전**

## 구현 순서

1. ✅ **Week 1**: 병렬 OCR 처리 (가장 큰 효과)
2. ✅ **Week 1**: 이미지 캐싱
3. ✅ **Week 2**: AI 텍스트 복구
4. ✅ **Week 2**: API 캐싱
5. ✅ **Week 3**: 배치 처리 최적화
