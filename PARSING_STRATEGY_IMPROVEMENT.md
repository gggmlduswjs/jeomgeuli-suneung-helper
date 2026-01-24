# 파싱 전략 개선 제안

## 현재 문제점

### 1. 템플릿 매칭 실패 원인
- **샘플링 제한**: 첫 5페이지, 각 페이지 50개 텍스트만 사용
- **높은 임계값**: 0.85 신뢰도를 넘기 어려움
- **목차 활용 부족**: 목차 페이지를 제대로 활용하지 못함
- **정적 샘플링**: 교재마다 구조가 다른데 항상 같은 방식으로 샘플링

### 2. 목차 기반 파싱의 한계
- 목차 텍스트를 수동으로 입력해야 함
- 목차 페이지 위치를 모르면 활용 불가

## 개선 전략

### 전략 1: 적응형 샘플링 (Adaptive Sampling)

**현재 (정적)**:
```python
# 항상 첫 5페이지만
sample_pages = ocr_data[:5]
```

**개선안 (적응형)**:
```python
# 1단계: 목차 페이지 자동 탐지
toc_pages = detect_toc_pages(ocr_data)  # 2-15페이지 범위에서 목차 탐지

# 2단계: 목차 + 본문 시작 부분 샘플링
if toc_pages:
    # 목차 전체 + 본문 시작 3페이지
    sample_pages = toc_pages + content_start_pages[:3]
else:
    # 폴백: 분산 샘플링 (첫 5페이지 + 중간 2페이지 + 마지막 1페이지)
    sample_pages = pages[:5] + pages[len(pages)//2:len(pages)//2+2] + pages[-1:]

# 3단계: 페이지당 더 많은 텍스트 사용
page_text = ' '.join(str(t) for t in texts[:200])  # 50 → 200
```

**구현 위치**: `hybrid_router.py:_try_template_matching()`

### 전략 2: 목차 페이지 자동 탐지

**목차 페이지 특징**:
- "목차", "차례", "CONTENTS", "INDEX" 등의 키워드
- 강의 번호 패턴 밀집 (1강, 2강, ... 또는 01, 02, ...)
- 페이지 번호 패턴 밀집
- 보통 2-15페이지 사이에 위치

**알고리즘**:
```python
def detect_toc_pages(ocr_data, start_page=2, end_page=15):
    """목차 페이지 자동 탐지"""
    toc_indicators = []

    for page in ocr_data[start_page-1:end_page]:
        score = 0
        texts = page.get('text', [])
        page_text = ' '.join(texts)

        # 1. 키워드 체크 (가중치: 30)
        if re.search(r'(목차|차례|CONTENTS|INDEX)', page_text, re.I):
            score += 30

        # 2. 강의 번호 패턴 밀도 (가중치: 40)
        lecture_patterns = [r'\d+강', r'제\s*\d+\s*장', r'CHAPTER\s+\d+']
        lecture_matches = sum(len(re.findall(p, page_text, re.I)) for p in lecture_patterns)
        if lecture_matches >= 5:  # 5개 이상의 강의 번호
            score += 40
        elif lecture_matches >= 3:
            score += 20

        # 3. 페이지 번호 패턴 (가중치: 20)
        page_num_pattern = r'\s+\d{1,3}\s*$'  # 줄 끝에 페이지 번호
        page_num_matches = len(re.findall(page_num_pattern, page_text, re.M))
        if page_num_matches >= 5:
            score += 20
        elif page_num_matches >= 3:
            score += 10

        # 4. 텍스트 밀도 체크 (목차는 텍스트가 많음)
        if len(texts) > 50:
            score += 10

        toc_indicators.append((page.get('page_num'), score))

    # 임계값 60 이상인 페이지들을 목차로 판단
    toc_pages = [page_num for page_num, score in toc_indicators if score >= 60]
    return toc_pages
```

**구현 위치**: 새 파일 `backend/app/infrastructure/pdf/parsers/toc_detector.py`

### 전략 3: 목차 텍스트 자동 추출 및 템플릿 생성

**현재**: 사용자가 수동으로 목차 텍스트 입력
**개선**: PDF 업로드 시 자동으로 목차 추출 및 템플릿 생성 제안

**워크플로우**:
```
1. PDF 업로드
   ↓
2. 목차 페이지 자동 탐지
   ↓
3. 목차 텍스트 자동 추출
   ↓
4. 강의 라인 예시 자동 추출 (패턴 분석)
   ↓
5. "템플릿 자동 생성하시겠습니까?" 제안
   ↓
6. 사용자 확인 → OpenAI로 템플릿 생성
```

**API 엔드포인트 추가**:
```python
@router.post("/templates/auto-generate")
async def auto_generate_template_from_pdf(
    pdf_file: UploadFile = File(...),
    subject: str = Form(...),
    name: str = Form(...),
    auto_detect_toc: bool = Form(default=True),
    toc_start_page: Optional[int] = Form(default=None),
    toc_end_page: Optional[int] = Form(default=None)
):
    """PDF에서 목차를 자동 추출하여 템플릿 생성"""
    # 1. OCR 추출
    # 2. 목차 페이지 탐지
    # 3. 목차 텍스트 추출
    # 4. 강의 라인 예시 자동 추출
    # 5. OpenAI로 템플릿 생성
    # 6. 검증 및 미리보기 반환
```

### 전략 4: 다단계 신뢰도 전략 (Tiered Confidence)

**현재**: 0.85 단일 임계값
**개선**: 3단계 임계값 시스템

```python
class ConfidenceTier:
    HIGH = 0.85      # 높은 신뢰도 - 바로 사용
    MEDIUM = 0.70    # 중간 신뢰도 - 사용자 확인 후 사용
    LOW = 0.50       # 낮은 신뢰도 - AI 파싱 또는 폴백
```

**매칭 결과 처리**:
```python
if confidence >= 0.85:
    # 즉시 사용
    return template, "HIGH_CONFIDENCE"
elif confidence >= 0.70:
    # 사용자에게 확인 요청
    return template, "MEDIUM_CONFIDENCE", {
        "message": "템플릿 매칭 신뢰도가 중간입니다. 사용하시겠습니까?",
        "matched_patterns": matched_patterns,
        "missing_patterns": missing_patterns
    }
else:
    # AI 파싱 또는 폴백
    return None, "LOW_CONFIDENCE"
```

### 전략 5: 패턴 학습 기반 매칭 개선

**현재**: 정규식 패턴 직접 매칭
**개선**: 텍스트 임베딩 + 패턴 매칭 하이브리드

```python
def _calculate_confidence_enhanced(pdf_text, template):
    """개선된 신뢰도 계산 (패턴 + 의미적 유사도)"""

    # 1. 기존 패턴 매칭 (60%)
    pattern_score = _calculate_pattern_score(pdf_text, template)

    # 2. 의미적 유사도 (40%)
    # 템플릿의 sample_texts와 PDF 텍스트의 코사인 유사도
    semantic_score = 0.0
    if template.sample_texts:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        vectorizer = TfidfVectorizer()
        corpus = template.sample_texts + [pdf_text]
        tfidf_matrix = vectorizer.fit_transform(corpus)

        # PDF와 템플릿 샘플들의 평균 유사도
        similarities = cosine_similarity(tfidf_matrix[-1:], tfidf_matrix[:-1])
        semantic_score = similarities.mean()

    # 가중 평균
    final_score = pattern_score * 0.6 + semantic_score * 0.4
    return final_score
```

### 전략 6: 점진적 폴백 전략

**현재**: 템플릿 → AI → 폴백
**개선**: 더 세밀한 단계별 폴백

```
1. 정확한 템플릿 매칭 (신뢰도 >= 0.85)
   ↓ 실패
2. 유사 템플릿 사용 (신뢰도 >= 0.70) + 사용자 확인
   ↓ 실패
3. 같은 과목의 최신 템플릿 강제 사용 (region_hints 활용)
   ↓ 실패
4. AI 파싱 (OpenAI API 사용)
   ↓ 실패
5. 목차 자동 탐지 + 휴리스틱 파싱
   ↓ 실패
6. 기본 config.json 폴백
```

### 전략 7: 시작 페이지 지능형 탐지

**문제**: 교재마다 본문 시작 페이지가 다름
**해결**: 자동 탐지 알고리즘

```python
def detect_content_start_page(ocr_data, toc_end_page=None):
    """본문 시작 페이지 자동 탐지"""

    start_search = toc_end_page + 1 if toc_end_page else 8

    for page in ocr_data[start_search:start_search+10]:
        page_num = page.get('page_num')
        texts = page.get('text', [])
        page_text = ' '.join(texts)

        # 본문 시작 지표
        indicators = 0

        # 1. "1강", "제1장" 등의 첫 강의 표시
        if re.search(r'(1강|제\s*1\s*장|CHAPTER\s+1|UNIT\s+1)', page_text, re.I):
            indicators += 3

        # 2. 본문 특유의 패턴 (문제, 개념 설명 등)
        if re.search(r'(문제|개념|학습목표|핵심정리)', page_text):
            indicators += 2

        # 3. 충분한 텍스트 밀도
        if len(texts) > 100:
            indicators += 1

        if indicators >= 4:
            return page_num

    # 기본값 반환
    return toc_end_page + 1 if toc_end_page else 8
```

## 구현 우선순위

### Phase 1: 즉시 개선 가능 (1-2일)
1. **적응형 샘플링** - 샘플 텍스트 개수 50→200으로 증가
2. **다단계 신뢰도** - 0.85 → 0.85/0.70/0.50 3단계 시스템
3. **목차 페이지 탐지** - 간단한 휴리스틱 알고리즘

### Phase 2: 중요 기능 추가 (3-5일)
4. **목차 자동 추출 API** - `/templates/auto-generate` 엔드포인트
5. **시작 페이지 자동 탐지** - 본문 시작 위치 지능형 탐지
6. **개선된 매칭 알고리즘** - 의미적 유사도 추가

### Phase 3: 고급 기능 (1주)
7. **패턴 학습 시스템** - 사용자 피드백 기반 패턴 개선
8. **템플릿 자동 업데이트** - 파싱 결과 기반 템플릿 개선

## 기대 효과

### 매칭 성공률 개선
- **현재**: ~40% (임계값 0.85 이상)
- **Phase 1 후**: ~65% (적응형 샘플링 + 다단계 신뢰도)
- **Phase 2 후**: ~85% (목차 자동 추출 + 시작 페이지 탐지)

### 사용자 경험 개선
- **수동 입력 감소**: 목차 텍스트, 시작 페이지 자동 탐지
- **투명성 향상**: 중간 신뢰도일 때 사용자에게 확인 요청
- **신규 교재 지원**: 템플릿 없어도 AI 파싱 + 휴리스틱으로 처리

### 유지보수 개선
- **디버깅 용이**: 각 단계별 신뢰도 로깅
- **패턴 개선**: 매칭 실패 케이스 분석 가능
- **확장성**: 새로운 파싱 전략 쉽게 추가

## 코드 수정 위치

### 주요 파일
1. `backend/app/infrastructure/pdf/parsers/hybrid_router.py`
   - `_try_template_matching()` - 적응형 샘플링 적용

2. `backend/app/infrastructure/pdf/parsers/template_manager.py`
   - `_calculate_confidence()` - 다단계 신뢰도 적용
   - `match_template()` - 반환 타입 확장 (신뢰도 등급 포함)

3. `backend/app/routers/templates.py`
   - `/templates/auto-generate` - 새 엔드포인트 추가

4. `backend/app/infrastructure/pdf/parsers/toc_detector.py` (신규)
   - 목차 페이지 탐지 로직
   - 시작 페이지 탐지 로직

### 설정 파일
5. `backend/app/core/config.py`
   - 새로운 임계값 설정 추가
   ```python
   TEMPLATE_CONFIDENCE_HIGH: float = 0.85
   TEMPLATE_CONFIDENCE_MEDIUM: float = 0.70
   TEMPLATE_CONFIDENCE_LOW: float = 0.50
   ```

## 예시: 개선된 워크플로우

### 시나리오: 새로운 EBS 수능특강 문학 2026 업로드

**현재**:
```
1. PDF 업로드
2. 템플릿 매칭 실패 (신뢰도 0.75)
3. AI 파싱 시도 (60초 소요)
4. 사용자는 왜 느린지 모름
```

**개선 후**:
```
1. PDF 업로드
2. 목차 페이지 자동 탐지 (2-7페이지)
3. 목차 텍스트 자동 추출
4. 시스템: "목차에서 32개 강의를 발견했습니다.
           템플릿을 자동 생성하시겠습니까?"
5. 사용자: "예" 클릭
6. OpenAI로 템플릿 생성 (15초)
7. 미리보기 표시
8. 사용자: "저장" 클릭
9. 다음 업로드부터는 즉시 매칭 성공 (2초)
```

## 참고: 현재 시스템 메트릭

### 템플릿 매칭 신뢰도 계산 (template_manager.py:212-280)
```python
# 가중치
lecture_patterns: 40%  # 강의 제목 패턴
problem_pattern: 30%   # 문제 번호 패턴
concept_patterns: 20%  # 개념/섹션 패턴
base_confidence: 10%   # 템플릿 기본 신뢰도
```

### 샘플링 현황 (hybrid_router.py:247-258)
```python
sample_pages = ocr_data[:5]  # 첫 5페이지만
page_text = ' '.join(str(t) for t in texts[:50])  # 각 페이지 50개만
```

## 결론

제안하신 "목차 페이지에서 텍스트 뽑아서 자동 생성"과 "시작 페이지 입력" 기능은 매우 효과적인 개선 방안입니다.

**핵심 개선점**:
1. ✅ 목차 자동 탐지 및 추출 - 사용자 편의성 대폭 향상
2. ✅ 적응형 샘플링 - 매칭 성공률 향상
3. ✅ 다단계 신뢰도 - 투명성 및 유연성 향상
4. ✅ 시작 페이지 자동 탐지 - 정확도 향상

이러한 개선사항들을 단계적으로 구현하면 템플릿 매칭 성공률을 40%에서 85%까지 높일 수 있을 것으로 예상됩니다.
