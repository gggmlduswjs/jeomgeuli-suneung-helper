# Step 1: 코드 분석 결과

## 현재 구조

### 하이브리드 파싱 시스템
- **HybridRouter** (`backend/app/infrastructure/pdf/parsers/hybrid_router.py`):
  - 템플릿 매칭 → AI 파싱 → 폴백 자동 선택
  - 신뢰도 기반 라우팅 (threshold: 0.85)
  - 성능 메트릭 수집 및 캐싱

- **TemplateManager** (`backend/app/infrastructure/pdf/parsers/template_manager.py`):
  - 템플릿 로드/저장/매칭
  - 신뢰도 계산 (강의 제목 40%, 문제 번호 30%, 개념/섹션 20%, 기본 신뢰도 10%)
  - 캐싱 지원 (book_id별)

- **StructureAnalyzer** (`backend/app/infrastructure/ai/genai/structure_analyzer.py`):
  - LLM 기반 PDF 구조 분석
  - 자동 정규식 패턴 생성
  - Pydantic 모델로 구조화

### 통합 파이프라인
- **UnifiedPipeline** (`backend/app/infrastructure/pdf/pipeline.py`):
  - OCR/PDF 추출 → 하이브리드 라우터 → 파싱 → 콘텐츠 추출 → 저장
  - 교재별 데이터 분리 (`book_id` 기반)
  - 백그라운드 비동기 처리

- **LectureContentsExtractor** (`backend/app/infrastructure/pdf/lecture_contents_extractor.py`):
  - 강의별 섹션 및 본문 추출
  - 섹션별 content 매칭
  - 강의 시작 페이지 탐색 (개선됨)

### 파서 구조
- **BaseParser** (`backend/app/infrastructure/pdf/parsers/base.py`):
  - 공통 기능: `group_lines()`, `join_line_text()`, `get_line_bbox()`, `matches_patterns()`
  - 추상 메서드: `parse()`, `extract_sections()`, `extract_content_paragraphs()`

- **LiteratureParser** (`backend/app/infrastructure/pdf/parsers/literature.py`):
  - 강의 추출: TOC + 컨텐츠 페이지
  - 문제 추출: 문제 번호 패턴 매칭
  - 섹션 추출: 패턴 매칭만 사용 (하드코딩된 정규식)

## 문제점 분석

### 1. 섹션 추출 정확도 문제 (우선순위 높음)

**현재 구현:**
```python
def extract_sections(self, lecture_ocr_data):
    # 패턴 매칭만 사용
    main_concept_match = re.match(r'^(\d+)\s*[\.]\s*([가-힣\s]{2,20})$', cleaned_line)
    # 또는
    elif self.matches_patterns(cleaned_line, content_patterns):
```

**문제점:**
1. **단일 전략 의존**: 패턴 매칭만 사용, 실패 시 빈 배열 반환
2. **하드코딩된 패턴**: 교재 형식이 다르면 매칭 실패
3. **OCR 오류 처리 부족**: `(cid:\d+)` 제거만 하고 다른 오류 처리 없음
4. **폴백 메커니즘 없음**: 패턴 매칭 실패 시 섹션을 찾지 못함
5. **AI 파싱 미활용**: `HybridRouter`는 파서 선택에만 사용, 섹션 추출에는 미사용

**영향:**
- `lecture_01.json`의 `sections`가 빈 배열로 저장됨
- 섹션별 content 매칭 실패
- 사용자가 섹션별 학습 불가

### 2. OCR 전처리 부족

**현재:**
- `(cid:\d+)` 문자만 제거
- 텍스트 정규화 최소

**개선 필요:**
- 공백 정규화
- 특수 문자 처리
- 폰트 인코딩 문제 해결

### 3. 에러 처리

**현재:**
- try-except로 감싸고 빈 배열 반환
- 에러 로깅만 하고 복구 시도 없음

**개선 필요:**
- 단계별 폴백 메커니즘
- 에러 복구 시도
- 상세한 디버깅 정보

## 개선 포인트

### 1. 다중 전략 섹션 추출 (우선순위 높음)

**현재:**
```
패턴 매칭 → 실패 → 빈 배열 반환
```

**개선 후:**
```
패턴 매칭 (빠름, 정확도 70-80%)
    ↓ 실패
AI 분석 (느림, 정확도 85-95%)
    ↓ 실패
휴리스틱 폴백 (안정성, 정확도 50-70%)
    ↓ 최소한 빈 배열보다는 나음
```

**구현 방안:**
1. `ImprovedSectionExtractor` 클래스 생성
2. 다중 전략 구현 (패턴 → AI → 휴리스틱)
3. 신뢰도 기반 선택
4. 결과 병합 및 검증

### 2. OCR 전처리 강화

**개선 사항:**
- 공백 정규화 (`\s+` → ` `)
- 특수 문자 정리
- 폰트 인코딩 문제 해결
- 텍스트 품질 점수 계산

### 3. 에러 복구 메커니즘

**개선 사항:**
- 단계별 폴백
- 부분 성공 허용
- 상세한 에러 로깅
- 디버깅 정보 제공

## 성능 병목 지점

### 현재 성능
- 템플릿 매칭: 2-5초 ✅
- AI 파싱: 60-120초 ⚠️
- 섹션 추출: 1-3초 (하지만 정확도 낮음) ⚠️

### 최적화 여지
- 섹션 추출에 AI 사용 시 비용 증가
- 캐싱 전략 개선
- 배치 처리

## 아키텍처 개선 포인트

### 1. 섹션 추출기 분리
- 현재: `LiteratureParser.extract_sections()`에 하드코딩
- 개선: `ImprovedSectionExtractor` 독립 클래스
- 장점: 재사용성, 테스트 용이성, 확장성

### 2. 전략 패턴 적용
- 각 전략을 별도 클래스로 분리
- 전략 선택 로직 분리
- 장점: 유지보수성, 확장성

### 3. 에러 처리 표준화
- 공통 에러 처리 클래스
- 에러 복구 전략 정의
- 장점: 일관성, 디버깅 용이성
