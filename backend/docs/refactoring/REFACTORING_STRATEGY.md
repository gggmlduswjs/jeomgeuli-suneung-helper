# 레거시 프로젝트 리팩토링 전략

## [1] 현재 구조가 망가지는 이유 요약

### 1.1 레거시 + 목적 변경의 전형적 문제점

#### A. **단일 거대 파일 (God Object)**
- `textbook_pipeline.py` (4240줄): 모든 책임이 한 파일에 집중
  - OCR 추출 로직
  - 파싱 로직 (강의, 개념, 작품, 문제)
  - JSON 조립 로직
  - 이미지 처리 로직
  - 캐싱 로직
  - 성능 통계
- **문제**: 변경 시 부작용 예측 불가, 테스트 불가능, 코드 재사용 불가

#### B. **책임 혼재 (Mixed Responsibilities)**
- `textbook_pipeline.py`가 동시에:
  - **Extraction**: PDF → OCR 데이터
  - **Parsing**: OCR 데이터 → 중간 구조
  - **Assembly**: 중간 구조 → 최종 JSON
- **문제**: 각 단계의 독립적 개선/테스트 불가

#### C. **기존 코드 위에 덧붙이기 (Accretion)**
- 원래 다른 목적의 코드베이스에 수능특강 파싱 기능을 추가
- 기존 파일을 수정하지 않고 새 메서드만 추가
- 결과: `_extract_lectures_literature()`, `_extract_lectures_math1()` 등 과목별 분기 로직 산재
- **문제**: 과목 추가 시 파일이 계속 커짐, 중복 코드 증가

#### D. **실험 코드와 프로덕션 코드 혼재**
- `scripts/experiments/`: 실험용 코드
- `scripts/examples/`: 예제 코드
- `api/archived/`: 사용 안 하는 코드
- **문제**: 어떤 코드가 실제로 사용되는지 불명확

#### E. **폴더 구조와 실제 사용 불일치**
- `api/app/extraction/`, `api/app/parsing/`, `api/app/assembly/` 폴더는 존재하지만
- `textbook_pipeline.py`가 이들을 제대로 활용하지 않음
- `text_extractors.py`가 `extraction/` 폴더 밖에 있음
- **문제**: 폴더 구조가 실제 의존성을 반영하지 않음

#### F. **중간 구조 설계는 있으나 미활용**
- `parsing/schemas.py`에 `IntermediateDocument` 등 중간 구조 정의
- `parsing/document_parser.py`에 파서 구현
- 하지만 `textbook_pipeline.py`는 이를 사용하지 않고 직접 JSON 생성
- **문제**: 중간 구조의 이점(검증, 재사용, 테스트)을 못 살림

---

## [2] 레거시 프로젝트 정리 전략 (단계별)

### Phase 1: Freeze (동결)
**목표**: 현재 동작하는 코드를 보존

1. **현재 동작 확인**
   - `scripts/run_textbook_pipeline.py` 실행하여 정상 동작 확인
   - 생성되는 JSON 파일 검증
   - 테스트 케이스 기록 (입력 PDF, 예상 출력)

2. **Git 브랜치 생성**
   ```bash
   git checkout -b refactor/pipeline-separation
   ```

3. **현재 상태 문서화**
   - `textbook_pipeline.py`의 주요 메서드 목록 작성
   - 각 메서드의 책임 정리

### Phase 2: 분류 (Categorize)
**목표**: 코드를 역할별로 분류

1. **메서드 분류표 작성**
   - Extraction 관련: `_extract_with_pdfplumber()`, `_ocr_page_worker()` 등
   - Parsing 관련: `_extract_lectures()`, `_extract_concept_blocks_from_ocr()` 등
   - Assembly 관련: JSON 생성 로직
   - Utility: `_preprocess_image()`, `_group_texts_by_line()` 등

2. **의존성 맵 작성**
   - 어떤 메서드가 어떤 메서드를 호출하는지
   - 공유되는 유틸리티 함수 식별

### Phase 3: 이동 (Extract & Move)
**목표**: 코드를 적절한 모듈로 이동

1. **Extraction 레이어 정리**
   - `textbook_pipeline.py`의 OCR/추출 로직 → `extraction/` 폴더
   - `text_extractors.py` → `extraction/extractors.py`로 통합 또는 이동

2. **Parsing 레이어 정리**
   - `textbook_pipeline.py`의 파싱 로직 → `parsing/` 폴더
   - 기존 `parsing/document_parser.py`와 통합

3. **Assembly 레이어 정리**
   - JSON 조립 로직 → `assembly/` 폴더
   - 기존 `assembly/lecture_assembler.py` 활용

### Phase 4: 정리 (Refactor)
**목표**: 각 레이어 내부 정리

1. **인터페이스 정의**
   - 각 레이어의 입력/출력 명확히 정의
   - 중간 구조 스키마 활용

2. **중복 제거**
   - 과목별 분기 로직을 전략 패턴으로 변경
   - 공통 로직 추출

3. **의존성 역전**
   - `TextbookPipeline`이 각 레이어를 조합하는 역할만 수행
   - 각 레이어는 독립적으로 테스트 가능하도록

### Phase 5: 삭제 판단 (Prune)
**목표**: 사용하지 않는 코드 제거

1. **사용 여부 확인**
   - `archived/` 폴더: 참조 여부 확인 후 삭제 또는 보관
   - `scripts/experiments/`: 실험 완료된 코드는 보관용으로 이동

2. **임시 코드 제거**
   - 주석 처리된 코드
   - 디버깅용 print 문 정리

---

## [3] 파일 유형별 처리 방침

### ✅ 유지해야 할 파일 유형

#### A. **Core Pipeline 파일**
- `api/app/services/textbook_pipeline.py`
  - **역할 변경**: 파이프라인 오케스트레이터로 축소
  - Extraction → Parsing → Assembly 순서만 관리
  - 각 레이어의 결과를 연결하는 역할만

#### B. **스키마/타입 정의**
- `api/app/parsing/schemas.py` (중간 구조)
- `api/app/schemas/` (API 스키마)
- **역할**: 유지, 확장 가능하도록 설계

#### C. **실행 스크립트**
- `api/scripts/run_textbook_pipeline.py`
- **역할**: 유지, 내부 구현 변경에 맞춰 수정

### 🔄 역할을 바꿔야 할 파일 유형

#### A. **textbook_pipeline.py**
- **현재**: 모든 로직 포함 (4240줄)
- **변경 후**: 파이프라인 오케스트레이터 (200줄 이하)
  ```python
  class TextbookPipeline:
      def __init__(self, ...):
          self.extractor = TextExtractor(...)
          self.parser = DocumentParser(...)
          self.assembler = LectureAssembler(...)
      
      def process_pdf(self, pdf_path):
          # 1. Extract
          ocr_data = self.extractor.extract(pdf_path)
          # 2. Parse
          intermediate = self.parser.parse(ocr_data)
          # 3. Assemble
          lectures = self.assembler.assemble_all(intermediate)
          return lectures
  ```

#### B. **extraction/ 폴더**
- **현재**: 일부 구현만 있음
- **변경 후**: 모든 추출 로직 집중
  - `textbook_pipeline.py`의 OCR 로직 이동
  - `text_extractors.py` 통합

#### C. **parsing/ 폴더**
- **현재**: `document_parser.py`가 있으나 미활용
- **변경 후**: 모든 파싱 로직 집중
  - `textbook_pipeline.py`의 `_extract_lectures()`, `_extract_concept_blocks()` 등 이동
  - 과목별 파서는 전략 패턴으로 분리

#### D. **assembly/ 폴더**
- **현재**: `lecture_assembler.py`가 있으나 미활용
- **변경 후**: 모든 JSON 조립 로직 집중
  - `textbook_pipeline.py`의 JSON 생성 로직 이동

### ✂️ 분리해야 할 파일 유형

#### A. **과목별 분기 로직**
- `_extract_lectures_literature()`, `_extract_lectures_math1()` 등
- **분리 방법**: 전략 패턴
  ```
  parsing/
    strategies/
      literature_parser.py
      math1_parser.py
      english_parser.py
      base_parser.py
  ```

#### B. **유틸리티 함수**
- `_group_texts_by_line()`, `_preprocess_image()` 등
- **분리 방법**: 공통 유틸리티 모듈
  ```
  parsing/utils.py  # 파싱 관련 유틸
  extraction/utils.py  # 추출 관련 유틸
  ```

#### C. **이미지 처리 로직**
- `_process_and_save_image()`, `_preprocess_image()` 등
- **분리 방법**: 별도 모듈
  ```
  extraction/image_processor.py
  ```

### 🗑️ 과감히 제거 후보로 둘 파일 유형

#### A. **archived/ 폴더**
- 사용하지 않는 레거시 코드
- **처리**: 참조 여부 확인 후 삭제 또는 `docs/archived/`로 이동

#### B. **실험 코드**
- `scripts/experiments/` 내 완료된 실험
- **처리**: `docs/experiments/`로 이동 또는 삭제

#### C. **중복된 추출기**
- `text_extractors.py`와 `extraction/extractors.py` 중복
- **처리**: 하나로 통합

#### D. **임시 스크립트**
- `api/test_parser.py` (git status에서 삭제됨)
- **처리**: 삭제

---

## [4] 목표 폴더 구조 + 파일 이동 가이드

### 최종 목표 구조

```
api/
├── app/
│   ├── services/
│   │   └── textbook_pipeline.py          # [축소] 파이프라인 오케스트레이터만
│   │
│   ├── extraction/                        # [확장] 모든 추출 로직
│   │   ├── __init__.py
│   │   ├── base_extractor.py             # [유지]
│   │   ├── extractors.py                 # [통합] text_extractors.py 내용 통합
│   │   ├── ocr_extractor.py              # [유지]
│   │   ├── pdfplumber_extractor.py       # [이동] textbook_pipeline.py에서
│   │   ├── text_normalizer.py            # [유지]
│   │   ├── image_processor.py            # [신규] 이미지 전처리 로직
│   │   ├── exceptions.py                 # [유지]
│   │   └── utils.py                      # [유지]
│   │
│   ├── parsing/                           # [확장] 모든 파싱 로직
│   │   ├── __init__.py
│   │   ├── document_parser.py            # [확장] textbook_pipeline.py 파싱 로직 통합
│   │   ├── schemas.py                    # [유지]
│   │   ├── parsing_rules.py              # [유지]
│   │   │
│   │   ├── block_parsers/                 # [유지]
│   │   │   ├── concept_parser.py
│   │   │   ├── passage_parser.py
│   │   │   ├── question_parser.py
│   │   │   └── example_parser.py
│   │   │
│   │   ├── classifiers/                  # [유지]
│   │   │   ├── rule_classifier.py
│   │   │   └── ml_classifier.py
│   │   │
│   │   ├── strategies/                   # [신규] 과목별 파싱 전략
│   │   │   ├── __init__.py
│   │   │   ├── base_strategy.py
│   │   │   ├── literature_strategy.py   # [이동] _extract_lectures_literature()
│   │   │   ├── math1_strategy.py        # [이동] _extract_lectures_math1()
│   │   │   └── english_strategy.py       # [이동] _extract_lectures_english()
│   │   │
│   │   └── utils.py                      # [신규] _group_texts_by_line() 등
│   │
│   ├── assembly/                          # [확장] 모든 조립 로직
│   │   ├── __init__.py
│   │   ├── lecture_assembler.py          # [확장] textbook_pipeline.py JSON 생성 로직 통합
│   │   └── json_builder.py               # [신규] JSON 구조 생성 유틸
│   │
│   └── utils/                             # [유지]
│       ├── data_file_handler.py
│       ├── ml_content_similarity.py
│       └── ...
│
├── scripts/
│   ├── run_textbook_pipeline.py          # [수정] 새로운 구조에 맞게
│   ├── examples/                          # [유지]
│   │   └── run_pipeline_example.py
│   └── experiments/                      # [정리] 완료된 실험은 docs/로 이동
│
└── archived/                              # [정리] 참조 없으면 삭제
```

### 파일 이동 매핑

#### Extraction 레이어

| 현재 위치 | 이동 위치 | 작업 |
|---------|---------|------|
| `textbook_pipeline.py::_extract_with_pdfplumber()` | `extraction/pdfplumber_extractor.py` | 이동 |
| `textbook_pipeline.py::_ocr_page_worker()` | `extraction/ocr_extractor.py` | 이동 |
| `textbook_pipeline.py::_preprocess_image()` | `extraction/image_processor.py` | 이동 |
| `textbook_pipeline.py::_process_and_save_image()` | `extraction/image_processor.py` | 이동 |
| `services/text_extractors.py` | `extraction/extractors.py` | 통합/이동 |

#### Parsing 레이어

| 현재 위치 | 이동 위치 | 작업 |
|---------|---------|------|
| `textbook_pipeline.py::_extract_lectures()` | `parsing/document_parser.py` | 통합 |
| `textbook_pipeline.py::_extract_lectures_literature()` | `parsing/strategies/literature_strategy.py` | 이동 |
| `textbook_pipeline.py::_extract_lectures_math1()` | `parsing/strategies/math1_strategy.py` | 이동 |
| `textbook_pipeline.py::_extract_lectures_english()` | `parsing/strategies/english_strategy.py` | 이동 |
| `textbook_pipeline.py::_extract_concept_blocks_from_ocr()` | `parsing/block_parsers/concept_parser.py` | 통합 |
| `textbook_pipeline.py::_extract_content_blocks_from_ocr()` | `parsing/block_parsers/passage_parser.py` | 통합 |
| `textbook_pipeline.py::_extract_problems_literature()` | `parsing/strategies/literature_strategy.py` | 이동 |
| `textbook_pipeline.py::_group_texts_by_line()` | `parsing/utils.py` | 이동 |

#### Assembly 레이어

| 현재 위치 | 이동 위치 | 작업 |
|---------|---------|------|
| `textbook_pipeline.py::process_pdf()` 내 JSON 생성 로직 | `assembly/lecture_assembler.py` | 이동 |
| `textbook_pipeline.py::_extract_lecture_contents()` | `assembly/lecture_assembler.py` | 이동 |

#### Pipeline 오케스트레이터

| 현재 위치 | 변경 후 | 작업 |
|---------|---------|------|
| `textbook_pipeline.py` (4240줄) | `textbook_pipeline.py` (200줄 이하) | 축소 |

---

## [5] 지금 바로 실행 가능한 정리 체크리스트

### 1단계: 안전장치 마련 (10분)

- [ ] **현재 동작 확인**
  ```bash
  cd api
  python scripts/run_textbook_pipeline.py
  # 정상 동작 확인, 생성된 JSON 파일 검증
  ```

- [ ] **Git 브랜치 생성**
  ```bash
  git checkout -b refactor/pipeline-separation
  git add .
  git commit -m "chore: 리팩토링 전 브랜치 생성"
  ```

- [ ] **현재 상태 백업**
  - `textbook_pipeline.py`의 주요 메서드 목록을 `REFACTORING_NOTES.md`에 기록

### 2단계: Extraction 레이어 분리 (30분)

- [ ] **이미지 처리 모듈 생성**
  ```bash
  # api/app/extraction/image_processor.py 생성
  ```
  - `_preprocess_image()`, `_process_and_save_image()` 이동

- [ ] **pdfplumber 추출기 분리**
  ```bash
  # api/app/extraction/pdfplumber_extractor.py 생성 (또는 extractors.py에 통합)
  ```
  - `_extract_with_pdfplumber()` 이동

- [ ] **text_extractors.py 통합**
  - `services/text_extractors.py` 내용을 `extraction/extractors.py`에 통합
  - 또는 `extraction/` 폴더로 이동

- [ ] **textbook_pipeline.py에서 import 변경**
  ```python
  # 기존
  from app.services.text_extractors import ...
  
  # 변경 후
  from app.extraction.extractors import ...
  ```

### 3단계: Parsing 레이어 정리 (40분)

- [ ] **과목별 전략 폴더 생성**
  ```bash
  mkdir -p api/app/parsing/strategies
  touch api/app/parsing/strategies/__init__.py
  ```

- [ ] **과목별 전략 파일 생성**
  - `parsing/strategies/base_strategy.py` (추상 클래스)
  - `parsing/strategies/literature_strategy.py` (`_extract_lectures_literature()` 이동)
  - `parsing/strategies/math1_strategy.py` (`_extract_lectures_math1()` 이동)
  - `parsing/strategies/english_strategy.py` (`_extract_lectures_english()` 이동)

- [ ] **유틸리티 함수 이동**
  - `_group_texts_by_line()` → `parsing/utils.py`

- [ ] **document_parser.py 확장**
  - `textbook_pipeline.py`의 파싱 로직을 `document_parser.py`에 통합
  - 전략 패턴으로 과목별 분기 처리

### 4단계: Assembly 레이어 정리 (20분)

- [ ] **lecture_assembler.py 확장**
  - `textbook_pipeline.py`의 JSON 생성 로직 이동
  - `_extract_lecture_contents()` 등 이동

- [ ] **json_builder.py 생성** (선택)
  - JSON 구조 생성 유틸리티 함수들

### 5단계: Pipeline 오케스트레이터 축소 (20분)

- [ ] **textbook_pipeline.py 리팩토링**
  - 모든 로직을 각 레이어로 이동
  - `process_pdf()` 메서드만 남기고 각 레이어 호출로 변경
  ```python
  def process_pdf(self, pdf_path):
      # 1. Extract
      ocr_data = self.extractor.extract(pdf_path)
      # 2. Parse
      intermediate = self.parser.parse(ocr_data, pdf_path)
      # 3. Assemble
      lectures = self.assembler.assemble_all(intermediate)
      return {"lectures": lectures, ...}
  ```

- [ ] **의존성 주입 구조로 변경**
  - 각 레이어를 생성자에서 주입받도록

### 6단계: 정리 및 검증 (20분)

- [ ] **임시 주석 제거**
  - 디버깅용 print 문 정리
  - 주석 처리된 코드 삭제

- [ ] **import 정리**
  - 사용하지 않는 import 제거
  - 순환 참조 확인

- [ ] **동작 검증**
  ```bash
  python scripts/run_textbook_pipeline.py
  # 생성된 JSON 파일이 이전과 동일한지 확인
  ```

- [ ] **Git 커밋**
  ```bash
  git add .
  git commit -m "refactor: 파이프라인을 Extraction/Parsing/Assembly로 분리"
  ```

### 7단계: 정리 (선택, 나중에)

- [ ] **archived/ 폴더 정리**
  - 참조 여부 확인 (`grep -r "archived" api/`)
  - 사용 안 하면 삭제 또는 `docs/archived/`로 이동

- [ ] **실험 코드 정리**
  - `scripts/experiments/` 내 완료된 실험은 `docs/experiments/`로 이동

---

## 추가 고려사항

### 테스트 전략
- 각 레이어를 독립적으로 테스트 가능하도록
- Mock 객체로 의존성 분리

### 성능 최적화
- 각 레이어에서 캐싱 전략 적용
- 병렬 처리 로직은 Extraction 레이어에 집중

### 확장성
- 새로운 과목 추가 시: `parsing/strategies/`에 새 전략만 추가
- 새로운 출력 형식 추가 시: `assembly/`에 새 assembler 추가

---

## 예상 소요 시간

- **1-2시간**: 핵심 구조 분리 (체크리스트 1-5단계)
- **추가 1시간**: 정리 및 검증 (6-7단계)

**총 예상 시간: 2-3시간**
