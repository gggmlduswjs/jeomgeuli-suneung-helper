# 아키텍처 요약

## 핵심 원칙

**관리자가 인프라 제공, 사용자는 학습만**

## 역할 분리

### 관리자 (백엔드/인프라)
```
EBS 수능특강 발행
    ↓
PDF 파일 수신
    ↓
PDF 파싱 (textbook_pipeline.py)
    - extraction/: PDF 추출 (텍스트, 이미지, OCR)
    - parsing/: 과목별 파싱 전략 (문학, 수학Ⅰ, 영어)
    - genai/: AI 설명 생성
    - ml/: ML 기반 분류 및 중복 제거
    - dl/: 딥러닝 기반 레이아웃 분석 및 수식 인식
    ↓
lecture JSON 생성 (api/data/literature/lectures/)
    ↓
Unit 생성 (create_units_from_lecture.py)
    - assembly/: lecture JSON을 Unit으로 변환
    - 이미지 경로 연동 (concepts_images, content_images, problems_images)
    - 문제 데이터 연동 (problem JSON 파일)
    ↓
DB 저장 (SQLite)
    ↓
사용자에게 즉시 제공
```

### 사용자 (프론트엔드)
```
앱 열기 (Start.tsx)
    ↓
교재 선택 (BookSelect.tsx)
    - 과목별 필터링
    - 교재 삭제 기능
    ↓
학습 시작 (QuestionLearning.tsx)
    - 전체 유닛 순서대로 학습
    - 개념 → 본문 → 문제 → 요약
    - 이미지 표시
    - AI 설명 표시
    - 점자 키워드 표시
    ↓
문제 목록 (QuestionList.tsx)
    ↓
학습 종료 (LearningSummary.tsx)
    - 오늘의 학습 통계
    - 전체 진행률 (units에서 직접 계산)
```

## 주요 흐름

### 1. 관리자 작업 (백엔드)

#### PDF 파싱 및 Unit 생성
- PDF 업로드 → `textbook_pipeline.py` 실행
- **Extraction 계층**: PDF에서 텍스트, 이미지 추출
- **Parsing 계층**: 과목별 전략으로 구조 파싱
  - 문학: 강의/본문/문제 구조
  - 수학Ⅰ: 개념/예제/유제 구조
  - 영어: 단원/지문/문제 구조
- **AI/ML 계층**: 설명 생성, 메타데이터 보강, 블록 분류
- JSON 파일 저장: `api/data/literature/lectures/`, `problems/`, `content/`
- 이미지 저장: `concepts_images/`, `content_images/`, `problems_images/`
- Unit 생성: `create_units_from_lecture.py` 실행
  - lecture JSON → Unit 변환
  - 이미지 경로 연동
  - 문제 데이터 연동
- DB 저장: SQLite (Book, Lesson, Unit)

#### 데이터 구조
- **Unit 타입**: CONCEPT_CORE, CONCEPT_FORM, CONCEPT_CONTENT, CONCEPT_SUMMARY, PASSAGE, QUESTION
- **Unit 필드**: 
  - `image_path`: 단일 이미지 경로 (하위호환)
  - `content_image_paths`: 여러 이미지 경로 (JSON 배열)
  - `ai_explanation`: AI 튜터 설명
  - `braille_keywords`: 점자 키워드 (JSON 배열)

### 2. 사용자 작업 (프론트엔드)

#### MVP 3.0 Single-flow UI
- **Start.tsx**: 시작 페이지
  - 학습 이어하기
  - 교재 선택으로 이동
- **BookSelect.tsx**: 교재 선택
  - 과목별 필터링
  - 교재 삭제 기능 (키보드 'D' 또는 버튼)
- **QuestionLearning.tsx**: 문제 학습
  - 전체 유닛 순서대로 학습 (개념/본문/문제/요약)
  - 유닛 타입별 표시 (UnitViewer)
  - 이미지 표시
  - AI 설명 표시
  - 점자 키워드 표시 (CONCEPT_SUMMARY)
  - Arduino 버튼 제어 (이전/다음/재생-일시정지)
- **QuestionList.tsx**: 문제 목록
  - 레슨별 문제 목록
  - 진행률 표시
- **LearningSummary.tsx**: 학습 종료
  - 오늘의 학습 통계
  - 전체 진행률 (units에서 직접 계산하여 500% 버그 수정)

## API 구조

### 관리자용 (생성)
- `POST /api/v1/books/upload`: PDF 업로드 및 파싱
- `POST /api/v1/curriculum/generate`: 커리큘럼 생성 (HWP + PDF 분석)
- `POST /api/v1/lessons/{lesson_id}/units/from-pdf`: PDF에서 Unit 생성

### 사용자용 (조회)
- `GET /api/v1/books`: 교재 목록 (과목별 필터링)
- `DELETE /api/v1/books/{book_id}`: 교재 삭제
- `GET /api/v1/lessons/{lesson_id}`: 레슨 상세 (question_count 포함)
- `GET /api/v1/lessons/{lesson_id}/units`: Unit 목록 (image_path, content_image_paths, ai_explanation, braille_keywords 포함)
- `GET /api/v1/units/{unit_id}`: Unit 상세
- `GET /api/v1/progress/continue`: 학습 이어하기
- `POST /api/v1/answers`: 답안 제출
- `GET /api/v1/curriculum`: 커리큘럼 목록
- `GET /api/v1/curriculum/{curriculum_id}`: 커리큘럼 상세
- `GET /api/v1/literature/lectures`: 문학 강의 목록
- `GET /api/v1/literature/lectures/{lecture_id}`: 문학 강의 상세
- `POST /api/v1/literature-ai/explain-concept`: 개념 설명 생성
- `POST /api/v1/literature-ai/explain-content`: 작품 설명 생성
- `POST /api/v1/literature-ai/explain-problem`: 문제 해설 생성

## 프론트엔드 페이지

### MVP 3.0 Single-flow UI (메인)
- `Start.tsx`: 시작 페이지 (학습 이어하기, 교재 선택)
- `BookSelect.tsx`: 교재 선택 (과목별 필터링, 삭제)
- `QuestionLearning.tsx`: 문제 학습 (전체 유닛 순서대로)
- `QuestionList.tsx`: 문제 목록
- `LearningSummary.tsx`: 학습 종료 (진행률 계산 개선)

### 레거시 페이지 (호환성 유지)
- `Main.tsx`: 메인 페이지 (과목 선택, 문학 학습 바로가기)
- `Book.tsx`: 교재 목록 (국어 선택 시 문학 강의 목록 표시)
- `Lesson.tsx`: 레슨 페이지
- `Unit.tsx`: 단원 페이지
- `Question.tsx`: 문제 풀이 페이지
- `Textbook.tsx`: 교재 관리 페이지
- `Curriculum.tsx`: 커리큘럼 목록 (조회만)
- `NotFound.tsx`: 404 에러 페이지

## 백엔드 모듈 구조

### 계층 구조
```
api/app/
├── routers/          # API 엔드포인트 (11개)
│   ├── health.py
│   ├── subjects.py
│   ├── books.py      # 교재 관리 (업로드, 목록, 삭제)
│   ├── lessons.py    # 레슨 관리 (question_count 계산)
│   ├── units.py      # Unit 관리 (이미지, AI 설명, 점자 키워드)
│   ├── progress.py
│   ├── answers.py
│   ├── curriculum.py
│   ├── ai.py
│   ├── literature.py
│   └── literature_ai.py
├── extraction/       # PDF 추출 계층
│   ├── base_extractor.py
│   ├── extractors.py
│   ├── pdfplumber_extractor.py
│   ├── ocr_extractor.py
│   ├── image_processor.py
│   └── text_normalizer.py
├── parsing/          # 파싱 계층
│   ├── document_parser.py
│   ├── strategies/   # 과목별 파싱 전략
│   │   ├── literature_strategy.py
│   │   ├── math1_strategy.py
│   │   └── english_strategy.py
│   ├── block_parsers/  # 블록별 파서
│   └── classifiers/    # 블록 분류기
├── genai/            # AI 설명 생성
│   ├── explanation_generator.py
│   ├── metadata_enricher.py
│   └── rag_recommender.py
├── ml/               # ML 기반 분류 및 중복 제거
│   ├── block_classifier.py
│   └── deduplicator.py
├── dl/               # 딥러닝 기반 분석
│   ├── layout_analyzer.py
│   └── math_recognizer.py
├── assembly/         # 어셈블리 (JSON → Unit)
│   └── lecture_assembler.py
├── services/         # 핵심 서비스
│   └── textbook_pipeline.py  # 교재 파이프라인
└── utils/            # 유틸리티
    ├── data_file_handler.py
    ├── id_generator.py
    └── ml_content_similarity.py
```

## 데이터 흐름

### 1. PDF 파싱 및 Unit 생성
```
PDF 업로드
    ↓
[Extraction] → extraction/
    - 텍스트 추출 (pdfplumber, OCR)
    - 이미지 추출
    - 텍스트 정규화
    ↓
[Parsing] → parsing/
    - 과목별 전략 선택 (literature/math1/english)
    - 블록 분류 (rule/ml classifier)
    - 블록 파싱 (concept/example/passage/question)
    ↓
[JSON 저장] → api/data/literature/
    - lectures/lecture_XX.json
    - problems/problem_pXX_YY.json
    - content/content_pXX_YY.json
    - concepts_images/*.png
    - content_images/*.png
    - problems_images/*.png
    ↓
[Unit 생성] → create_units_from_lecture.py
    - lecture JSON 로드
    - problem JSON 로드 (문제 데이터 연동)
    - content JSON 로드 (본문 데이터 연동)
    - 이미지 경로 연동
    - Unit 생성 (DB 저장)
```

### 2. 학습 흐름
```
사용자: Start.tsx
    ↓
교재 선택: BookSelect.tsx
    ↓
학습 시작: QuestionLearning.tsx
    - units API 호출 → Unit 목록 조회
    - 전체 유닛 순서대로 표시
    - UnitViewer: 타입별 표시
      - CONCEPT_SUMMARY: 요약 + 점자 키워드
      - QUESTION: 문제 지문 + 선택지 + 이미지
      - CONCEPT_CONTENT: 개념 내용 + 이미지
      - PASSAGE: 본문 + 이미지
    - Arduino 버튼: 이전/다음/재생-일시정지
    ↓
답안 제출: answers API
    ↓
학습 종료: LearningSummary.tsx
    - units API 호출 → 실제 문제 수 계산
    - 진행률 계산: (완료된 문제 수 / 전체 문제 수) * 100
```

## 핵심 가치

1. **즉시 학습 가능**: 관리자가 미리 준비 → 사용자는 바로 학습
2. **단순한 구조**: 사용자는 조회/학습만, 복잡한 생성 로직은 백엔드
3. **명확한 책임**: 관리자 = 데이터 준비, 사용자 = 학습
4. **접근성 우선**: 점자 디바이스, 음성, 키보드 네비게이션 지원
5. **확장 가능한 구조**: 과목별 파싱 전략, AI/ML 모듈 분리

## 기술 스택

### 백엔드
- **프레임워크**: FastAPI
- **데이터베이스**: SQLite (메타데이터)
- **PDF 처리**: pdfplumber, OCR
- **AI/ML**: OpenAI API, LangChain, Sentence Transformers
- **파싱**: 규칙 기반 + ML 기반 분류

### 프론트엔드
- **프레임워크**: React 18+ + TypeScript
- **빌드 도구**: Vite
- **상태 관리**: Zustand
- **점자 디바이스**: Web Bluetooth API
- **음성**: Web Speech API (STT, TTS)
- **스타일**: Tailwind CSS

### 하드웨어
- **Arduino**: 3셀 점자 디스플레이 + 버튼 제어
- **BLE**: 점자 디바이스 통신
- **Raspberry Pi**: BLE 서버 (선택적)

---

*작성일: 2024년 12월*  
*마지막 업데이트: 2025년 1월*
