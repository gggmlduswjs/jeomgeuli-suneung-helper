# 리팩토링 진행 상황

## 완료된 작업

### ✅ Extraction 레이어 분리
1. **이미지 처리 모듈 생성** (`api/app/extraction/image_processor.py`)
   - `_preprocess_image()` → `ImageProcessor.preprocess_image()`
   - `_process_and_save_image()` → `ImageProcessor.process_and_save_image()`

2. **Import 수정**
   - `from app.services.text_extractors` → `from app.extraction.extractors`
   - `PdfplumberExtractor`, `OCRExtractor`는 이미 `extraction/extractors.py`에 구현되어 있음

3. **textbook_pipeline.py 수정**
   - 이미지 처리 메서드가 `ImageProcessor`를 사용하도록 변경

### ✅ Parsing 레이어 정리 (진행 중)
1. **유틸리티 함수 생성** (`api/app/parsing/utils.py`)
   - `group_texts_by_line()` - y좌표 기준 줄 그룹화
   - `matches_patterns()` - 패턴 매칭

2. **전략 패턴 기본 구조 생성**
   - `api/app/parsing/strategies/__init__.py`
   - `api/app/parsing/strategies/base_strategy.py` - 기본 추상 클래스

3. **textbook_pipeline.py 수정**
   - `_group_texts_by_line()` → `group_texts_by_line()` 사용
   - `_matches_patterns()` → `matches_patterns()` 사용
   - 레거시 호환성을 위해 래퍼 메서드 유지

## 진행 중인 작업

### 🔄 Parsing 레이어 완성
- [ ] 과목별 전략 클래스 생성
  - `LiteratureParsingStrategy` (`_extract_lectures_literature()` 이동)
  - `Math1ParsingStrategy` (`_extract_lectures_math1()` 이동)
  - `EnglishParsingStrategy` (`_extract_lectures_english()` 이동)

### 🔄 Assembly 레이어 정리
- [ ] `lecture_assembler.py` 확장
  - JSON 생성 로직 이동
  - `_extract_lecture_contents()` 이동

### 🔄 Pipeline 오케스트레이터 축소
- [ ] `textbook_pipeline.py` 축소 (200줄 이하 목표)
  - 각 레이어를 조합하는 역할만 수행
  - 의존성 주입 구조로 변경

## 다음 단계

1. **과목별 전략 클래스 생성** (우선순위: 높음)
   - `_extract_lectures_literature()` 등의 메서드를 전략 클래스로 이동
   - `textbook_pipeline.py`에서 전략 패턴 사용

2. **Assembly 레이어 정리** (우선순위: 중간)
   - JSON 조립 로직을 `assembly/lecture_assembler.py`로 이동

3. **최종 정리** (우선순위: 낮음)
   - 사용하지 않는 메서드 제거
   - Import 정리
   - 동작 검증

## 주의사항

- 현재 `textbook_pipeline.py`는 여전히 4000줄 이상
- 점진적 리팩토링이 필요 (한 번에 모든 것을 변경하지 않음)
- 각 단계마다 동작 검증 필요
