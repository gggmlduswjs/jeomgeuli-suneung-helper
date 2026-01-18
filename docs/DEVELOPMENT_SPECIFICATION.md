# 개발명세서 (Development Specification)

점글이 수능 헬퍼 프로젝트의 전체 파일 구조 및 기능 명세서입니다.

## 📋 파일 목록

> **엑셀 사용 가이드**: 아래 표들을 엑셀로 복사할 때, 각 섹션의 표를 선택하여 복사-붙여넣기 하면 자동으로 엑셀 표 형식으로 변환됩니다. 각 모듈별로 필터링하여 사용하세요.

---

## 1. 백엔드 API 모듈

### 1.1 메인 애플리케이션

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 백엔드 API | 메인 애플리케이션 | api/app | main.py | FastAPI 메인 애플리케이션 진입점, 라우터 등록 및 CORS 설정 |
| 백엔드 API | 메인 애플리케이션 | api/app | __init__.py | 앱 패키지 초기화 파일 |
| 백엔드 API | 메인 애플리케이션 | api/app/core | config.py | 애플리케이션 설정 관리 (환경변수, 데이터베이스 연결 등) |
| 백엔드 API | 메인 애플리케이션 | api/app/core | __init__.py | 코어 패키지 초기화 파일 |
| 백엔드 API | 메인 애플리케이션 | api/app/db | models.py | SQLAlchemy 데이터베이스 모델 정의 (Book, Lesson, Unit, Progress 등) |
| 백엔드 API | 메인 애플리케이션 | api/app/db | session.py | 데이터베이스 세션 관리 및 초기화 |
| 백엔드 API | 메인 애플리케이션 | api/app/db | __init__.py | DB 패키지 초기화 파일 |

### 1.2 API 라우터

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 백엔드 API | API 라우터 | api/app/routers | health.py | 헬스 체크 API 엔드포인트 |
| 백엔드 API | API 라우터 | api/app/routers | books.py | 교재 관리 API (PDF 업로드, 목록 조회, 파싱 상태 확인) |
| 백엔드 API | API 라우터 | api/app/routers | lessons.py | 레슨 관리 API (레슨 목록, 상세 조회) |
| 백엔드 API | API 라우터 | api/app/routers | units.py | 단원 관리 API (단원 목록, 콘텐츠 조회) |
| 백엔드 API | API 라우터 | api/app/routers | progress.py | 학습 진행 상황 API (진행률 조회, 업데이트) |
| 백엔드 API | API 라우터 | api/app/routers | answers.py | 답안 관리 API (답안 제출, 정답 확인) |
| 백엔드 API | API 라우터 | api/app/routers | review.py | 복습 관리 API (복습 큐 조회, 복습 항목 관리) |
| 백엔드 API | API 라우터 | api/app/routers | syncpoints.py | 동기화 포인트 API (오디오-텍스트 동기화 포인트 관리) |
| 백엔드 API | API 라우터 | api/app/routers | pdf.py | PDF 처리 API (PDF 추출, 파싱) |
| 백엔드 API | API 라우터 | api/app/routers | lecture_scripts.py | 강의 대본 파싱 API (HWP 파일 파싱, 구조 추출) |
| 백엔드 API | API 라우터 | api/app/routers | curriculum.py | 커리큘럼 자동 생성 API (커리큘럼 생성, 조회, 수정) |
| 백엔드 API | API 라우터 | api/app/routers | recommendations.py | 추천 시스템 API (다음 레슨 추천, 복습 추천) |
| 백엔드 API | API 라우터 | api/app/routers | __init__.py | 라우터 패키지 초기화 파일 |

### 1.3 데이터 스키마

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 백엔드 API | 데이터 스키마 | api/app/schemas | answer.py | 답안 관련 Pydantic 스키마 정의 |
| 백엔드 API | 데이터 스키마 | api/app/schemas | book.py | 교재 관련 Pydantic 스키마 정의 |
| 백엔드 API | 데이터 스키마 | api/app/schemas | lesson.py | 레슨 관련 Pydantic 스키마 정의 |
| 백엔드 API | 데이터 스키마 | api/app/schemas | progress.py | 진행 상황 관련 Pydantic 스키마 정의 |
| 백엔드 API | 데이터 스키마 | api/app/schemas | review.py | 복습 관련 Pydantic 스키마 정의 |
| 백엔드 API | 데이터 스키마 | api/app/schemas | syncpoint.py | 동기화 포인트 관련 Pydantic 스키마 정의 |
| 백엔드 API | 데이터 스키마 | api/app/schemas | unit.py | 단원 관련 Pydantic 스키마 정의 |
| 백엔드 API | 데이터 스키마 | api/app/schemas | curriculum.py | 커리큘럼 관련 Pydantic 스키마 정의 |
| 백엔드 API | 데이터 스키마 | api/app/schemas | recommendation.py | 추천 시스템 관련 Pydantic 스키마 정의 |
| 백엔드 API | 데이터 스키마 | api/app/schemas | __init__.py | 스키마 패키지 초기화 파일 |

### 1.4 핵심 서비스

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 백엔드 API | 핵심 서비스 | api/app/services | braille_convert.py | 한글 텍스트를 점자로 변환하는 규칙 기반 변환 서비스 |
| 백엔드 API | 핵심 서비스 | api/app/services | audio_sync.py | 오디오-텍스트 동기화 서비스 (STT 기반 매칭) |
| 백엔드 API | 핵심 서비스 | api/app/services | content_auto_generator.py | 콘텐츠 자동 생성 서비스 (매뉴얼 규칙 자동 적용) |
| 백엔드 API | 핵심 서비스 | api/app/services | hwp_extract.py | 한글 파일(HWP) 텍스트 추출 서비스 |
| 백엔드 API | 핵심 서비스 | api/app/services | lecture_script_parser.py | 강의 대본 파서 (섹션 분류, 핵심 포인트 추출) |
| 백엔드 API | 핵심 서비스 | api/app/services | pdf_extract.py | PDF 추출 서비스 (레거시) |
| 백엔드 API | 핵심 서비스 | api/app/services | pdf_image_extract.py | PDF 이미지 추출 서비스 (레거시) |
| 백엔드 API | 핵심 서비스 | api/app/services | pdf_structure_extract.py | PDF 구조 추출 서비스 (레거시) |
| 백엔드 API | 핵심 서비스 | api/app/services | pdf_parse.py | PDF 파싱 서비스 (레거시) |
| 백엔드 API | 핵심 서비스 | api/app/services | review_logic.py | 복습 로직 서비스 (복습 큐 관리, 복습 스케줄링) |
| 백엔드 API | 핵심 서비스 | api/app/services | curriculum_generator.py | 커리큘럼 자동 생성 서비스 (강의대본 분석, 학습 단위 생성) |
| 백엔드 API | 핵심 서비스 | api/app/services | curriculum_template.py | 커리큘럼 템플릿 서비스 (교재별 템플릿 정의, 의존성 규칙) |
| 백엔드 API | 핵심 서비스 | api/app/services | pdf_script_matcher.py | PDF-강의대본 매칭 서비스 (참조 정보 매칭, 신뢰도 계산) |
| 백엔드 API | 핵심 서비스 | api/app/services | __init__.py | 서비스 패키지 초기화 파일 |

### 1.5 PDF 추출 모듈

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 백엔드 API | PDF 추출 모듈 | api/app/services/pdf_extract | base_extractor.py | PDF 추출기 베이스 클래스 (인터페이스) |
| 백엔드 API | PDF 추출 모듈 | api/app/services/pdf_extract | pdfplumber_extractor.py | PDFPlumber 기반 텍스트 추출기 |
| 백엔드 API | PDF 추출 모듈 | api/app/services/pdf_extract | image_extractor.py | PDF 이미지 추출기 |
| 백엔드 API | PDF 추출 모듈 | api/app/services/pdf_extract | literature_extractor.py | 문학 과목 전용 추출기 |
| 백엔드 API | PDF 추출 모듈 | api/app/services/pdf_extract | enhanced_ocr.py | 향상된 OCR 서비스 (AI 기반 텍스트 인식) |
| 백엔드 API | PDF 추출 모듈 | api/app/services/pdf_extract | ai_text_postprocessor.py | AI 기반 텍스트 후처리 서비스 |
| 백엔드 API | PDF 추출 모듈 | api/app/services/pdf_extract | math_ocr.py | 수식 OCR 서비스 (수식 이미지 → LaTeX 변환) |
| 백엔드 API | PDF 추출 모듈 | api/app/services/pdf_extract | utils.py | PDF 추출 유틸리티 함수 |
| 백엔드 API | PDF 추출 모듈 | api/app/services/pdf_extract | exceptions.py | PDF 추출 예외 정의 |
| 백엔드 API | PDF 추출 모듈 | api/app/services/pdf_extract | __init__.py | PDF 추출 패키지 초기화 파일 |

### 1.6 PDF 파싱 모듈

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 백엔드 API | PDF 파싱 모듈 | api/app/services/pdf_parse | base_parser.py | PDF 파서 베이스 클래스 (인터페이스) |
| 백엔드 API | PDF 파싱 모듈 | api/app/services/pdf_parse | parse_pipeline.py | PDF 파싱 파이프라인 (추출 → 파싱 → 후처리) |
| 백엔드 API | PDF 파싱 모듈 | api/app/services/pdf_parse | json_schema.py | 파싱 결과 JSON 스키마 정의 |
| 백엔드 API | PDF 파싱 모듈 | api/app/services/pdf_parse | ai_structure_classifier.py | AI 기반 블록 구조 분류기 |
| 백엔드 API | PDF 파싱 모듈 | api/app/services/pdf_parse | __init__.py | PDF 파싱 패키지 초기화 파일 |

### 1.7 과목별 파싱 전략

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 백엔드 API | 과목별 파싱 전략 | api/app/services/subject_strategies | math.py | 수학 과목 일반 파서 |
| 백엔드 API | 과목별 파싱 전략 | api/app/services/subject_strategies | math1.py | 수학Ⅰ 전용 파서 (개념/예제/유제 구조 파싱) |
| 백엔드 API | 과목별 파싱 전략 | api/app/services/subject_strategies | math1_schema.py | 수학Ⅰ JSON 스키마 정의 |
| 백엔드 API | 과목별 파싱 전략 | api/app/services/subject_strategies | english.py | 영어 파서 (지문/문제 분리) |
| 백엔드 API | 과목별 파싱 전략 | api/app/services/subject_strategies | english_schema.py | 영어 JSON 스키마 정의 |
| 백엔드 API | 과목별 파싱 전략 | api/app/services/subject_strategies | literature.py | 문학 파서 (지문/문제 분리) |
| 백엔드 API | 과목별 파싱 전략 | api/app/services/subject_strategies | literature_schema.py | 문학 JSON 스키마 정의 |
| 백엔드 API | 과목별 파싱 전략 | api/app/services/subject_strategies | korean.py | 국어 파서 |
| 백엔드 API | 과목별 파싱 전략 | api/app/services/subject_strategies | __init__.py | 과목별 전략 패키지 초기화 파일 |
| 백엔드 API | AI/ML 서비스 | api/app/services | audio_sync_ml.py | ML 기반 오디오-텍스트 동기화 서비스 (Whisper + Sentence Transformers) |
| 백엔드 API | AI/ML 서비스 | api/app/services | braille_ml.py | ML 기반 점자 변환 서비스 (KoBERT 기반 Seq2Seq 모델) |
| 백엔드 API | AI/ML 서비스 | api/app/services | content_generator.py | 생성형 AI 콘텐츠 생성 서비스 (LangChain + GPT-4/Claude) |
| 백엔드 API | AI/ML 서비스 | api/app/services | content_auto_generator_ml.py | AI 기반 제작 프로세스 자동화 서비스 (LangChain 기반) |
| 백엔드 API | AI/ML 서비스 | api/app/services | recommendation_engine.py | 학습자 맞춤형 추천 엔진 (콘텐츠 기반 필터링, Sentence Transformers) |
| 백엔드 API | AI/ML 서비스 | api/app/services | user_behavior_profiler.py | 사용자 행동 프로파일링 서비스 (학습 패턴 분석, 약점 주제 식별) |
| 백엔드 API | AI/ML 서비스 | api/app/services | pdf_structure_classifier.py | Vision Transformer 기반 PDF 구조 분류 서비스 (LayoutLMv3) |

### 1.8 유틸리티 및 기타

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 백엔드 API | 유틸리티 | api/app/utils | text_utils.py | 텍스트 처리 유틸리티 함수 |
| 백엔드 API | 유틸리티 | api/app/utils | __init__.py | 유틸리티 패키지 초기화 파일 |

### 1.9 테스트

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 백엔드 API | 테스트 | api/tests | test_content_generator.py | 콘텐츠 생성기 테스트 |
| 백엔드 API | 테스트 | api/tests | test_english_lecture_script.py | 영어 강의 대본 파서 테스트 |
| 백엔드 API | 테스트 | api/tests | test_helpers.py | 테스트 헬퍼 함수 |
| 백엔드 API | 테스트 | api/tests | test_hwp_extract.py | HWP 추출 테스트 |
| 백엔드 API | 테스트 | api/tests | test_lecture_script_full.py | 강의 대본 파서 전체 테스트 |
| 백엔드 API | 테스트 | api/tests | test_lecture_script_parser.py | 강의 대본 파서 단위 테스트 |
| 백엔드 API | 테스트 | api/tests | test_parsers.py | PDF 파서 테스트 |
| 백엔드 API | 테스트 | api/tests | test_pdf_api.py | PDF API 엔드포인트 테스트 |
| 백엔드 API | 테스트 | api/tests | test_pdf_extract.py | PDF 추출 테스트 |
| 백엔드 API | 테스트 | api/tests | __init__.py | 테스트 패키지 초기화 파일 |
| 백엔드 API | 테스트 | api/tests | README.md | 테스트 가이드 문서 |

### 1.10 스크립트 및 설정

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 백엔드 API | 스크립트 | api/scripts | build_training_dataset.py | 학습 데이터셋 구축 스크립트 |
| 백엔드 API | 설정 | api | Dockerfile | Docker 이미지 빌드 설정 |
| 백엔드 API | 설정 | api | requirements.txt | Python 기본 의존성 목록 |
| 백엔드 API | 설정 | api | requirements-ai.txt | AI/ML 기능 의존성 목록 |
| 백엔드 API | 문서 | api | REFACTORING_PDF_EXTRACTION.md | PDF 추출 리팩토링 문서 |

---

## 2. 프론트엔드 웹 모듈

### 2.1 메인 애플리케이션

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 프론트엔드 웹 | 메인 애플리케이션 | apps/web/src | main.tsx | React 애플리케이션 진입점, ErrorBoundary 설정 |
| 프론트엔드 웹 | 메인 애플리케이션 | apps/web/src/app | App.tsx | 메인 App 컴포넌트 |
| 프론트엔드 웹 | 메인 애플리케이션 | apps/web/src/app | routes.tsx | React Router 라우팅 설정 |

### 2.2 주요 페이지

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 프론트엔드 웹 | 주요 페이지 | apps/web/src/pages | Home.tsx | 홈 페이지 (메인 대시보드) |
| 프론트엔드 웹 | 주요 페이지 | apps/web/src/pages | Main.tsx | 메인 페이지 |
| 프론트엔드 웹 | 주요 페이지 | apps/web/src/pages | Explore.tsx | 탐색 페이지 (키워드, 뉴스, 채팅) |
| 프론트엔드 웹 | 주요 페이지 | apps/web/src/pages | NotFound.tsx | 404 에러 페이지 |
| 프론트엔드 웹 | 주요 페이지 | apps/web/src/pages | Book.tsx | 책 뷰어 페이지 |
| 프론트엔드 웹 | 주요 페이지 | apps/web/src/pages | Lesson.tsx | 레슨 페이지 |
| 프론트엔드 웹 | 주요 페이지 | apps/web/src/pages | Unit.tsx | 단원 페이지 |
| 프론트엔드 웹 | 주요 페이지 | apps/web/src/pages | Quiz.tsx | 퀴즈 페이지 |
| 프론트엔드 웹 | 주요 페이지 | apps/web/src/pages | Review.tsx | 복습 페이지 |
| 프론트엔드 웹 | 주요 페이지 | apps/web/src/pages | LearnIndex.tsx | 학습 인덱스 페이지 |
| 프론트엔드 웹 | 주요 페이지 | apps/web/src/pages | LearnStep.tsx | 학습 단계 페이지 |
| 프론트엔드 웹 | 주요 페이지 | apps/web/src/pages | TestStep.tsx | 테스트 단계 페이지 |
| 프론트엔드 웹 | 주요 페이지 | apps/web/src/pages | FreeConvert.tsx | 자유 변환 페이지 |
| 프론트엔드 웹 | 주요 페이지 | apps/web/src/pages | Curriculum.tsx | 커리큘럼 관리 페이지 (제작자용) |
| 프론트엔드 웹 | 주요 페이지 | apps/web/src/pages | CurriculumDetail.tsx | 커리큘럼 상세 페이지 |
| 프론트엔드 웹 | 주요 페이지 | apps/web/src/pages | CurriculumCreate.tsx | 커리큘럼 생성 페이지 |

### 2.3 페이지 컴포넌트

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Home | BrailleDeviceCard.tsx | 홈 화면 점자 디바이스 카드 컴포넌트 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Home | ContinueLearningCard.tsx | 홈 화면 학습 이어하기 카드 컴포넌트 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Home | PDFManagementCard.tsx | 홈 화면 PDF 관리 카드 컴포넌트 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Home | SubjectSelectCard.tsx | 홈 화면 과목 선택 카드 컴포넌트 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Learning | LearningScreen.tsx | 학습 화면 메인 컴포넌트 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Learning | BrailleStatusPanel.tsx | 학습 화면 점자 상태 패널 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Learning | CurrentContentPanel.tsx | 학습 화면 현재 콘텐츠 패널 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Learning | DocumentTree.tsx | 학습 화면 문서 트리 뷰 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Learning | GraphPreview.tsx | 학습 화면 그래프 미리보기 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Question | Question.tsx | 문제 풀이 페이지 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Question | QuestionDisplay.tsx | 문제 표시 컴포넌트 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Question | AnswerInput.tsx | 답안 입력 컴포넌트 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Question | AnswerResult.tsx | 답안 결과 표시 컴포넌트 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Question | ChoiceComparison.tsx | 선택지 비교 컴포넌트 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Question | WrongAnswerList.tsx | 오답 목록 컴포넌트 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Passage | Passage.tsx | 지문 입력 페이지 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Passage | PassageInput.tsx | 지문 입력 컴포넌트 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Passage | PassageStructure.tsx | 지문 구조 표시 컴포넌트 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Textbook | Textbook.tsx | 교과서 관리 페이지 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Textbook | TextbookList.tsx | 교과서 목록 컴포넌트 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Textbook | PDFUpload.tsx | PDF 업로드 컴포넌트 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Textbook | UnitList.tsx | 단원 목록 컴포넌트 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Textbook | UnitContent.tsx | 단원 콘텐츠 표시 컴포넌트 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Textbook | PDFStructuredViewer.tsx | PDF 구조화 뷰어 컴포넌트 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/GraphTable | GraphTable.tsx | 그래프/표 변환 페이지 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/GraphTable | GraphDualView.tsx | 그래프 이중 뷰 컴포넌트 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/GraphTable | GraphPatterns.tsx | 그래프 패턴 표시 컴포넌트 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/GraphTable | ImageUpload.tsx | 이미지 업로드 컴포넌트 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Explore | useExploreChat.ts | 탐색 채팅 훅 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Explore | useExploreKeywords.ts | 탐색 키워드 훅 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Explore | useExploreNews.ts | 탐색 뉴스 훅 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/exam | SentenceRepeat.tsx | 문장 반복 페이지 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/exam | TextbookConverter.tsx | 교과서 변환 페이지 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/exam | TextCompress.tsx | 텍스트 압축 페이지 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/ExamMode | ExamMode.tsx | 시험 모드 페이지 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/ExamTimer | ExamTimer.tsx | 시험 타이머 페이지 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/BrailleSpeed | BrailleSpeed.tsx | 점자 속도 연습 페이지 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Vocab | Vocab.tsx | 어휘 학습 페이지 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Vocab | VocabCard.tsx | 어휘 카드 컴포넌트 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Vocab | SisaWords.tsx | 시사 어휘 컴포넌트 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Curriculum | CurriculumList.tsx | 커리큘럼 목록 컴포넌트 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Curriculum | CurriculumDetailView.tsx | 커리큘럼 상세 뷰 컴포넌트 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Curriculum | LearningPathVisualization.tsx | 학습 경로 시각화 컴포넌트 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Curriculum | LessonConnectionView.tsx | 레슨 간 연결 표시 컴포넌트 |
### 2.4 재사용 컴포넌트

#### 2.4.1 점자 컴포넌트

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 프론트엔드 웹 | 점자 컴포넌트 | apps/web/src/components/braille | BrailleCell.tsx | 점자 셀 컴포넌트 (단일 셀) |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/braille | BrailleCells.tsx | 점자 셀 그룹 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/braille | BrailleDot.tsx | 점자 점 컴포넌트 (단일 점) |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/braille | BrailleGrid.tsx | 점자 그리드 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/braille | BrailleOutputPanel.tsx | 점자 출력 패널 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/braille | BraillePanel.tsx | 점자 패널 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/braille | BrailleRow.tsx | 점자 행 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/braille | BrailleStrip.tsx | 점자 스트립 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/braille | ChunkNavigation.tsx | 점자 청크 네비게이션 컴포넌트 |
#### 2.4.2 입력 컴포넌트

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 프론트엔드 웹 | 입력 컴포넌트 | apps/web/src/components/input | ChatLikeInput.tsx | 채팅 스타일 입력 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/input | GlobalVoiceRecognition.tsx | 전역 음성 인식 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/input | MicButton.tsx | 마이크 버튼 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/input | SpeechBar.tsx | 음성 입력 바 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/input | VoiceButton.tsx | 음성 버튼 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/voice | VoiceFirstDisplay.tsx | 음성 우선 표시 컴포넌트 |
#### 2.4.3 UI 컴포넌트

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 프론트엔드 웹 | UI 컴포넌트 | apps/web/src/components/ui | AnswerCard.tsx | 답안 카드 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/ui | AppShellMobile.tsx | 모바일 앱 셸 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/ui | BottomBar.tsx | 하단 바 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/ui | Card.tsx | 카드 컴포넌트 (공통) |
#### 2.4.4 시스템 컴포넌트

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 프론트엔드 웹 | 시스템 컴포넌트 | apps/web/src/components/system | DevHealth.tsx | 개발 헬스 체크 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/system | ErrorBoundary.tsx | 에러 바운더리 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/system | HealthCheck.tsx | 헬스 체크 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/system | PerformanceMonitor.tsx | 성능 모니터링 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/system | ToastA11y.tsx | 접근성 토스트 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/settings | BrailleDisplaySettings.tsx | 점자 디스플레이 설정 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/subject | SubjectDisplayAdapter.tsx | 과목별 표시 어댑터 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/common | MemoizedList.tsx | 메모이제이션된 리스트 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/layout | PageLayout.tsx | 페이지 레이아웃 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/debug | VoiceRecognitionDebug.tsx | 음성 인식 디버그 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/textbook | BookUpload.tsx | 책 업로드 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/lesson | LessonList.tsx | 레슨 목록 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/progress | ProgressIndicator.tsx | 진행 상황 표시기 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/review | ReviewQueue.tsx | 복습 큐 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/unit | UnitViewer.tsx | 단원 뷰어 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/pdf | QuestionViewer.tsx | 문제 뷰어 컴포넌트 (PDF 구조화) |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/pdf | PassageViewer.tsx | 지문 뷰어 컴포넌트 (PDF 구조화) |
### 2.5 커스텀 훅

#### 2.5.1 핵심 훅

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 프론트엔드 웹 | 핵심 훅 | apps/web/src/hooks | useAudioSync.ts | 오디오 동기화 훅 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks | useBrailleBLE.ts | BLE 점자 디바이스 훅 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks | useBrailleChunkReader.ts | 점자 청크 리더 훅 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks | useBraillePlayback.ts | 점자 재생 훅 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks | useKeyboardNavigation.ts | 키보드 네비게이션 훅 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks | usePageBase.ts | 페이지 기본 훅 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks | usePerformance.ts | 성능 모니터링 훅 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks | usePointerGesture.ts | 포인터 제스처 훅 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks | useSTT.ts | 음성 인식(STT) 훅 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks | useTTS.ts | 음성 합성(TTS) 훅 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks | useVoiceCommands.ts | 음성 명령 훅 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks | useVoiceControl.ts | 음성 제어 훅 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks | useAudioSyncML.ts | ML 기반 오디오 동기화 훅 (Whisper + Sentence Transformers) |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks | useRecommendations.ts | 추천 시스템 훅 (다음 레슨, 복습 추천) |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks | useCurriculum.ts | 커리큘럼 관리 훅 (생성, 조회, 수정) |
#### 2.5.2 API 훅

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 프론트엔드 웹 | API 훅 | apps/web/src/hooks/api | useAnswers.ts | 답안 API 훅 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks/api | useBooks.ts | 교재 API 훅 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks/api | useContinue.ts | 학습 이어하기 API 훅 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks/api | useLessons.ts | 레슨 API 훅 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks/api | useProgress.ts | 진행 상황 API 훅 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks/api | useReview.ts | 복습 API 훅 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks/api | useSyncpoints.ts | 동기화 포인트 API 훅 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks/api | useUnits.ts | 단원 API 훅 |
| 프론트엔드 웹 | API 훅 | apps/web/src/hooks/api | useCurriculum.ts | 커리큘럼 API 훅 |
| 프론트엔드 웹 | API 훅 | apps/web/src/hooks/api | useRecommendations.ts | 추천 시스템 API 훅 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks/braille | BrailleDeviceAdapter.ts | 점자 디바이스 어댑터 인터페이스 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks/braille | BrailleDeviceFactory.ts | 점자 디바이스 팩토리 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks/braille | GenericBLEAdapter.ts | 범용 BLE 어댑터 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks/braille | MockBrailleAdapter.ts | 모의 점자 디바이스 어댑터 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks/braille | OrbitReaderAdapter.ts | Orbit Reader 어댑터 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks/voice | commands.ts | 음성 명령 정의 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks/voice | matchers.ts | 음성 명령 매칭 로직 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks/voice | normalizers.ts | 음성 명령 정규화 |
### 2.6 서비스 레이어

#### 2.6.1 핵심 서비스

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 프론트엔드 웹 | 핵심 서비스 | apps/web/src/services | api.ts | API 클라이언트 (Axios 기반) |
| 프론트엔드 웹 | 서비스 | apps/web/src/services | answers.ts | 답안 서비스 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services | books.ts | 교재 관리 서비스 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services | lessons.ts | 레슨 서비스 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services | progress.ts | 진행 상황 서비스 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services | review.ts | 복습 서비스 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services | syncpoints.ts | 동기화 포인트 서비스 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services | units.ts | 단원 서비스 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services | curriculum.ts | 커리큘럼 서비스 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services | recommendations.ts | 추천 시스템 서비스 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services | VoiceService.ts | 음성 서비스 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services | CommandService.ts | 명령 서비스 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services/commands | Command.ts | 명령 인터페이스 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services/commands | CommandInvoker.ts | 명령 실행자 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services/commands | ControlCommand.ts | 제어 명령 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services/commands | LearningCommand.ts | 학습 명령 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services/commands | NavigateCommand.ts | 네비게이션 명령 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services/learning | LearningFlow.ts | 학습 플로우 베이스 클래스 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services/learning | PassageLearningFlow.ts | 지문 학습 플로우 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services/learning | TextbookLearningFlow.ts | 교과서 학습 플로우 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services/learning | VocabLearningFlow.ts | 어휘 학습 플로우 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services/passage | PassageService.ts | 지문 서비스 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services/question | QuestionService.ts | 문제 서비스 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services/textbook | TextbookService.ts | 교과서 서비스 |
### 2.7 상태 관리

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 프론트엔드 웹 | 상태 관리 | apps/web/src/store | bookStore.ts | 교재 상태 관리 (Zustand) |
| 프론트엔드 웹 | 상태 관리 | apps/web/src/store | examStore.ts | 시험 상태 관리 |
| 프론트엔드 웹 | 상태 관리 | apps/web/src/store | home.ts | 홈 상태 관리 |
| 프론트엔드 웹 | 상태 관리 | apps/web/src/store | keywords.ts | 키워드 상태 관리 |
| 프론트엔드 웹 | 상태 관리 | apps/web/src/store | learnStore.ts | 학습 상태 관리 |
| 프론트엔드 웹 | 상태 관리 | apps/web/src/store | lessonSession.ts | 레슨 세션 상태 |
| 프론트엔드 웹 | 상태 관리 | apps/web/src/store | lessonStore.ts | 레슨 상태 관리 |
| 프론트엔드 웹 | 상태 관리 | apps/web/src/store | progressStore.ts | 진행 상황 상태 관리 |
| 프론트엔드 웹 | 상태 관리 | apps/web/src/store | review.ts | 복습 상태 관리 (ReviewItem) |
| 프론트엔드 웹 | 상태 관리 | apps/web/src/store | reviewQueueStore.ts | 복습 큐 상태 관리 (ReviewQueueItem) |
| 프론트엔드 웹 | 상태 관리 | apps/web/src/store | vocabStore.ts | 어휘 상태 관리 |
| 프론트엔드 웹 | 상태 관리 | apps/web/src/store | voice.ts | 음성 상태 관리 |
| 프론트엔드 웹 | 상태 관리 | apps/web/src/store | curriculumStore.ts | 커리큘럼 상태 관리 |
| 프론트엔드 웹 | 상태 관리 | apps/web/src/store | recommendationStore.ts | 추천 시스템 상태 관리 |
### 2.8 타입 정의

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 프론트엔드 웹 | 타입 정의 | apps/web/src/types | answer.ts | 답안 타입 정의 |
| 프론트엔드 웹 | 타입 정의 | apps/web/src/types | api.ts | API 타입 정의 |
| 프론트엔드 웹 | 타입 정의 | apps/web/src/types | book.ts | 교재 타입 정의 |
| 프론트엔드 웹 | 타입 정의 | apps/web/src/types | chat.ts | 채팅 타입 정의 |
| 프론트엔드 웹 | 타입 정의 | apps/web/src/types | errors.ts | 에러 타입 정의 |
| 프론트엔드 웹 | 타입 정의 | apps/web/src/types | explore.ts | 탐색 타입 정의 |
| 프론트엔드 웹 | 타입 정의 | apps/web/src/types | global.d.ts | 전역 타입 정의 |
| 프론트엔드 웹 | 타입 정의 | apps/web/src/types | index.ts | 타입 인덱스 |
| 프론트엔드 웹 | 타입 정의 | apps/web/src/types | lesson.ts | 레슨 타입 정의 |
| 프론트엔드 웹 | 타입 정의 | apps/web/src/types | progress.ts | 진행 상황 타입 정의 |
| 프론트엔드 웹 | 타입 정의 | apps/web/src/types | review.ts | 복습 타입 정의 |
| 프론트엔드 웹 | 타입 정의 | apps/web/src/types | syncpoint.ts | 동기화 포인트 타입 정의 |
| 프론트엔드 웹 | 타입 정의 | apps/web/src/types | unit.ts | 단원 타입 정의 |
| 프론트엔드 웹 | 타입 정의 | apps/web/src/types | voice.ts | 음성 타입 정의 |
| 프론트엔드 웹 | 타입 정의 | apps/web/src/types | curriculum.ts | 커리큘럼 타입 정의 |
| 프론트엔드 웹 | 타입 정의 | apps/web/src/types | recommendation.ts | 추천 시스템 타입 정의 |
### 2.9 유틸리티 및 기타

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 프론트엔드 웹 | 유틸리티 | apps/web/src/utils | brailleChunk.ts | 점자 청크 유틸리티 |
| 프론트엔드 웹 | 유틸리티 | apps/web/src/utils | brailleChunkBuilder.ts | 점자 청크 빌더 |
| 프론트엔드 웹 | 유틸리티 | apps/web/src/utils | contentExtractor.ts | 콘텐츠 추출기 |
| 프론트엔드 웹 | 전략 | apps/web/src/strategies | subjectLearning.ts | 과목별 학습 전략 |
| 프론트엔드 웹 | STT | apps/web/src/stt | GoogleStreamingProvider.ts | Google STT 스트리밍 프로바이더 |
| 프론트엔드 웹 | 설정 | apps/web/src/config | brailleDisplay.ts | 점자 디스플레이 설정 |
| 프론트엔드 웹 | 스타일 | apps/web/src/styles | tokens.css | 디자인 토큰 CSS |
| 프론트엔드 웹 | 스타일 | apps/web/src/styles | util.css | 유틸리티 스타일 CSS |
| 프론트엔드 웹 | 스타일 | apps/web/src | index.css | 전역 스타일 CSS |
| 프론트엔드 웹 | 테스트 | apps/web/src/__tests__ | api.test.ts | API 통합 테스트 |
| 프론트엔드 웹 | 설정 | apps/web | index.html | HTML 진입점 |
| 프론트엔드 웹 | 설정 | apps/web | vite.config.ts | Vite 빌드 설정 |
| 프론트엔드 웹 | 설정 | apps/web | tailwind.config.js | Tailwind CSS 설정 |
| 프론트엔드 웹 | 설정 | apps/web | postcss.config.js | PostCSS 설정 |
| 프론트엔드 웹 | 설정 | apps/web | playwright.config.ts | Playwright E2E 테스트 설정 |
| 프론트엔드 웹 | E2E 테스트 | apps/web/e2e | accessibility.spec.ts | 접근성 E2E 테스트 |
| 프론트엔드 웹 | E2E 테스트 | apps/web/e2e | explore.spec.ts | 탐색 E2E 테스트 |
| 프론트엔드 웹 | E2E 테스트 | apps/web/e2e | home.spec.ts | 홈 E2E 테스트 |
| 프론트엔드 웹 | E2E 테스트 | apps/web/e2e | voice-control.spec.ts | 음성 제어 E2E 테스트 |
| 프론트엔드 웹 | 빌드 산출물 | apps/web/dev-dist | registerSW.js | Service Worker 등록 스크립트 |
| 프론트엔드 웹 | 빌드 산출물 | apps/web/dev-dist | sw.js | Service Worker 스크립트 |
| 프론트엔드 웹 | 빌드 산출물 | apps/web/dev-dist | workbox-5682fe79.js | Workbox 라이브러리 |
| 프론트엔드 웹 | 스크립트 | apps/web/scripts | gen-icons.mjs | 아이콘 생성 스크립트 |
---

## 3. 확장 프로그램 모듈

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 확장 프로그램 | 메인 | apps/extension/src | background.ts | Chrome 확장 프로그램 백그라운드 스크립트 |
| 확장 프로그램 | 메인 | apps/extension/src | contentScript.ts | Chrome 확장 프로그램 콘텐츠 스크립트 |
| 확장 프로그램 | 메인 | apps/extension/src | api.ts | Chrome 확장 프로그램 API 통신 모듈 |
| 확장 프로그램 | UI | apps/extension/src/popup | Popup.tsx | Chrome 확장 프로그램 팝업 React 컴포넌트 |
| 확장 프로그램 | UI | apps/extension/src/popup | popup.html | Chrome 확장 프로그램 팝업 HTML |
---

## 4. 하드웨어 모듈

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 하드웨어 | 펌웨어 | arduino/braille_3cell | braille_3cell.ino | 3셀 점자 디스플레이 메인 스케치 |
| 하드웨어 | 펌웨어 | arduino/braille_3cell | braille.cpp | 점자 구현 C++ 소스 |
| 하드웨어 | 펌웨어 | arduino/braille_3cell | braille.h | 점자 헤더 파일 |
| 하드웨어 | 펌웨어 | arduino/braille_3cell | BrailleConverter.cpp | 점자 변환기 C++ 소스 |
| 하드웨어 | 펌웨어 | arduino/braille_3cell | BrailleConverter.h | 점자 변환기 헤더 파일 |
| 하드웨어 | 펌웨어 | arduino/braille_3cell | BrailleMap.h | 점자 맵핑 헤더 파일 |
| 하드웨어 | 테스트 | arduino/braille_3cell_test/integration_test | integration_test.ino | 통합 테스트 스케치 |
| 하드웨어 | 테스트 | arduino/braille_3cell_test/test_braille_patterns | test_braille_patterns.ino | 점자 패턴 테스트 스케치 |
| 하드웨어 | 펌웨어 | arduino/braille_firmware | braille_firmware.ino | 점자 펌웨어 메인 스케치 |
| 하드웨어 | 문서 | arduino | README.md | Arduino 프로젝트 설명 문서 |
---

## 5. Raspberry Pi 모듈

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| Raspberry Pi | 서버 | raspberrypi | ble_server.py | BLE 서버 스크립트 (점자 디바이스 통신) |
| Raspberry Pi | 문서 | raspberrypi | README.md | Raspberry Pi 프로젝트 설명 문서 |
---

## 6. 인프라 및 기타 모듈

### 6.1 인프라

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 인프라 | 설정 | infra | docker-compose.yml | Docker Compose 설정 파일 |

### 6.2 스크립트

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 스크립트 | 유틸리티 | scripts | create_data_folders.py | 데이터 폴더 생성 스크립트 |

### 6.3 데이터

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 데이터 | 추출된 데이터 | data/extracted | *.txt | 추출된 PDF 텍스트 파일들 |
| 데이터 | 강의 대본 | data/lecture_scripts | *.hwp, *.hwpx | 한글 파일 강의 대본들 |
| 데이터 | PDF 파일 | data/pdfs | *.pdf | 수능특강 PDF 파일들 |
| 데이터 | 업로드 파일 | data/uploads | *.pdf | 업로드된 PDF 파일들 |

### 6.4 문서

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 문서 | 프로젝트 문서 | docs | WBS.md | 작업 분해 구조 문서 |
| 문서 | 프로젝트 문서 | docs | PROJECT_STRUCTURE.md | 프로젝트 구조 문서 |
| 문서 | 프로젝트 문서 | docs | DEVELOPMENT_ROADMAP.md | 개발 로드맵 문서 |
| 문서 | 프로젝트 문서 | docs | AI_ML_IMPLEMENTATION_PROPOSAL.md | AI/ML 구현 제안서 |
| 문서 | 프로젝트 문서 | docs | AI_ML_PDF_EXTRACTION.md | AI/ML PDF 추출 문서 |
| 문서 | 프로젝트 문서 | docs | PDF_EXTRACTION_GUIDE.md | PDF 추출 가이드 |
| 문서 | 프로젝트 문서 | docs | PDF_PROCESSING_PIPELINE.md | PDF 처리 파이프라인 문서 |
| 문서 | 프로젝트 문서 | docs | MATH1_EXTRACTION_PROMPTS.md | 수학Ⅰ 추출 프롬프트 |
| 문서 | 프로젝트 문서 | docs | LITERATURE_EXTRACTION_PROMPTS.md | 문학 추출 프롬프트 |
| 문서 | 프로젝트 문서 | docs | ENGLISH_EXTRACTION_PROMPTS.md | 영어 추출 프롬프트 |
| 문서 | 프로젝트 문서 | docs | TEST_COMMANDS.md | 테스트 명령어 문서 |
| 문서 | 프로젝트 문서 | docs | TESTING_GUIDE.md | 테스트 가이드 문서 |
| 문서 | 프로젝트 문서 | docs | CURRICULUM_AUTO_GENERATION.md | 커리큘럼 자동 생성 시스템 문서 |
| 문서 | 프로젝트 문서 | docs | AI_ML_IMPLEMENTATION_IDEAS.md | AI/ML 기능 구현 아이디어 가이드 |
| 문서 | 프로젝트 문서 | docs | MENU_FLOW.md | 메뉴 흐름도 문서 |
| 문서 | 프로젝트 문서 | docs | SCREEN_SPECIFICATION.md | 화면 정의서 문서 |
| 문서 | 프로젝트 문서 | docs | README.md | 문서 디렉토리 README |
| 문서 | 프로젝트 문서 | README.md | 프로젝트 루트 README |

## 🔧 기능별 모듈 설명

### 1. PDF 처리 모듈

**목적**: PDF 파일에서 텍스트, 이미지, 구조를 추출하고 과목별로 파싱

**주요 구성요소**:
- **PDF 추출 계층** (`api/app/services/pdf_extract/`)
  - `base_extractor.py`: 추출기 인터페이스 정의
  - `pdfplumber_extractor.py`: PDFPlumber 기반 텍스트 추출
  - `image_extractor.py`: PDF 내 이미지 추출
  - `literature_extractor.py`: 문학 과목 전용 추출기
  - `enhanced_ocr.py`: AI 기반 OCR (스캔본 처리)
  - `math_ocr.py`: 수식 이미지 → LaTeX 변환
  - `ai_text_postprocessor.py`: AI 기반 텍스트 후처리

- **PDF 파싱 계층** (`api/app/services/pdf_parse/`)
  - `base_parser.py`: 파서 인터페이스 정의
  - `parse_pipeline.py`: 전체 파싱 파이프라인 관리
  - `json_schema.py`: 파싱 결과 JSON 스키마 정의
  - `ai_structure_classifier.py`: AI 기반 블록 구조 분류

- **과목별 파싱 전략** (`api/app/services/subject_strategies/`)
  - `math1.py`: 수학Ⅰ 파서 (개념/예제/유제 구조 파싱)
  - `english.py`: 영어 파서 (지문/문제 분리)
  - `literature.py`: 문학 파서 (지문/문제 분리)
  - `korean.py`: 국어 파서

**처리 흐름**: PDF 업로드 → 추출(Extract) → 파싱(Parse) → 후처리(Post-process) → 구조화된 JSON

---

### 2. 점자 변환 모듈

**목적**: 한글 텍스트를 점자로 변환하여 점자 디바이스에 전송

**주요 구성요소**:
- **백엔드** (`api/app/services/braille_convert.py`)
  - 규칙 기반 한글→점자 변환
  - 약자 처리
  - 점자 규칙 적용

- **프론트엔드** (`apps/web/src/components/braille/`, `apps/web/src/hooks/braille/`)
  - 점자 시각화 컴포넌트 (BrailleCell, BrailleGrid 등)
  - 점자 디바이스 어댑터 (BLE 통신)
  - 점자 청크 관리 (말하는 단위 분할)

**기능**: 텍스트 입력 → 점자 변환 → 디바이스 전송 → 시각화

---

### 3. 학습 관리 모듈

**목적**: 교재, 레슨, 단원, 학습 진행 상황 관리

**주요 구성요소**:
- **백엔드** (`api/app/routers/books.py`, `lessons.py`, `units.py`, `progress.py`)
  - 교재 업로드 및 파싱 상태 관리
  - 레슨/단원 목록 및 콘텐츠 조회
  - 학습 진행률 추적 및 업데이트

- **프론트엔드** (`apps/web/src/pages/Textbook/`, `Lesson.tsx`, `Unit.tsx`)
  - 교재 관리 UI (업로드, 목록, 파싱 상태)
  - 레슨/단원 뷰어
  - 학습 진행 상황 표시

**데이터 모델**: Book → Lesson → Unit → Content

---

### 4. 복습 시스템 모듈

**목적**: 학습한 내용을 효율적으로 복습할 수 있도록 스케줄링 및 큐 관리

**주요 구성요소**:
- **백엔드** (`api/app/services/review_logic.py`, `api/app/routers/review.py`)
  - 복습 큐 관리 (ReviewQueue)
  - 복습 스케줄링 알고리즘
  - 복습 항목 생성 및 업데이트

- **프론트엔드** (`apps/web/src/pages/Review.tsx`, `apps/web/src/store/review*.ts`)
  - 복습 큐 UI
  - 복습 항목 표시 및 관리
  - 복습 진행 상황 추적

**기능**: 오답 추적 → 복습 큐 추가 → 스케줄링 → 복습 제공

---

### 5. 음성 처리 모듈

**목적**: 음성 인식(STT), 음성 합성(TTS), 오디오-텍스트 동기화

**주요 구성요소**:
- **STT (Speech-to-Text)** (`apps/web/src/hooks/useSTT.ts`, `apps/web/src/stt/GoogleStreamingProvider.ts`)
  - Google STT 스트리밍 프로바이더
  - 실시간 음성 인식
  - 음성 명령 처리

- **ML 기반 STT** (`api/app/services/audio_sync_ml.py`)
  - Whisper 모델 통합 (한국어 최적화)
  - 실시간 오디오 청크 처리
  - Sentence Transformers 기반 텍스트 임베딩
  - 코사인 유사도 기반 매칭
  - 신뢰도 계산

- **TTS (Text-to-Speech)** (`apps/web/src/hooks/useTTS.ts`)
  - Web Speech API 기반 음성 합성
  - 텍스트 읽기 기능

- **오디오 동기화** (`api/app/services/audio_sync.py`, `apps/web/src/hooks/useAudioSync.ts`)
  - 강의 오디오와 텍스트 자동 동기화
  - STT 기반 매칭 알고리즘
  - 실시간 동기화 상태 관리

- **ML 기반 오디오 동기화** (`apps/web/src/hooks/useAudioSyncML.ts`)
  - Whisper + Sentence Transformers 통합
  - 실시간 스트리밍 처리
  - 자동 하이라이트

- **음성 명령** (`apps/web/src/hooks/useVoiceCommands.ts`, `apps/web/src/services/VoiceService.ts`)
  - 음성 명령 인식 및 실행
  - 명령 패턴 매칭
  - 명령 라우팅

**기능**: 음성 입력 → STT → 명령 인식 → 액션 실행 / 오디오 재생 → ML 동기화 → 텍스트 하이라이트

---

### 6. 점자 디바이스 연동 모듈

**목적**: BLE를 통한 점자 디바이스와의 통신 및 제어

**주요 구성요소**:
- **프론트엔드** (`apps/web/src/hooks/braille/`)
  - `BrailleDeviceAdapter.ts`: 점자 디바이스 어댑터 인터페이스
  - `BrailleDeviceFactory.ts`: 디바이스 팩토리 (다양한 디바이스 지원)
  - `GenericBLEAdapter.ts`: 범용 BLE 어댑터
  - `OrbitReaderAdapter.ts`: Orbit Reader 전용 어댑터
  - `MockBrailleAdapter.ts`: 테스트용 모의 어댑터

- **BLE 서버** (`raspberrypi/ble_server.py`)
  - Raspberry Pi에서 실행되는 BLE 서버
  - 점자 디바이스와의 중계 서버

- **하드웨어 펌웨어** (`arduino/braille_3cell/`)
  - Arduino 기반 점자 디스플레이 펌웨어
  - 점자 패턴 제어

**기능**: 텍스트 → 점자 변환 → BLE 전송 → 디바이스 표시

---

### 7. 콘텐츠 자동 생성 모듈

**목적**: 제작 시간 단축을 위한 콘텐츠 자동 생성 및 검증

**주요 구성요소**:
- **자동 생성** (`api/app/services/content_auto_generator.py`)
  - 매뉴얼 규칙 자동 적용
  - 기호 사용 규칙 자동 검증 및 수정
  - 정보 순서 자동 최적화
  - 텍스트 길이 자동 조절 (말하는 단위)

- **AI 기반 자동 생성** (`api/app/services/content_auto_generator_ml.py`)
  - LangChain 기반 제작 프로세스 자동화
  - 매뉴얼 규칙 자동 적용 (LLM 활용)
  - 말하는 단위 자동 분할 (문맥 고려)
  - 정보 순서 최적화
  - 품질 점수 자동 계산

- **생성형 AI 콘텐츠** (`api/app/services/content_generator.py`)
  - LangChain + GPT-4/Claude 기반
  - 문제 해설 자동 생성
  - 핵심 포인트 요약
  - 강의 대본 초안 생성

- **강의 대본 파서** (`api/app/services/lecture_script_parser.py`)
  - HWP 파일에서 강의 대본 추출
  - 섹션 분류 (OT, Overview, Concept 등)
  - 핵심 포인트 추출
  - 수학 표현식 추출

- **HWP 처리** (`api/app/services/hwp_extract.py`)
  - 한글 파일 텍스트 추출
  - 파일명에서 강의 정보 추출

**기능**: HWP 업로드 → 텍스트 추출 → 구조 파싱 → 자동 생성 → 검증

---

### 8. 문제 풀이 모듈

**목적**: 문제 표시, 답안 입력, 정답 확인, 오답 분석

**주요 구성요소**:
- **백엔드** (`api/app/routers/answers.py`)
  - 답안 제출 및 정답 확인
  - 오답 패턴 분석

- **프론트엔드** (`apps/web/src/pages/Question/`)
  - `QuestionDisplay.tsx`: 문제 표시
  - `AnswerInput.tsx`: 답안 입력
  - `AnswerResult.tsx`: 답안 결과 표시
  - `ChoiceComparison.tsx`: 선택지 비교
  - `WrongAnswerList.tsx`: 오답 목록

**기능**: 문제 표시 → 답안 입력 → 정답 확인 → 오답 분석 → 복습 큐 추가

---

### 9. UI/UX 모듈

**목적**: 사용자 인터페이스 및 사용자 경험 제공

**주요 구성요소**:
- **페이지 컴포넌트** (`apps/web/src/pages/`)
  - 홈, 학습, 문제, 복습, 탐색 등 주요 페이지
  - 시험 모드, 점자 속도 연습, 어휘 학습 등 특수 페이지

- **재사용 컴포넌트** (`apps/web/src/components/`)
  - 점자 컴포넌트 (BrailleCell, BrailleGrid 등)
  - 입력 컴포넌트 (VoiceButton, MicButton 등)
  - UI 컴포넌트 (Card, BottomBar 등)
  - 시스템 컴포넌트 (ErrorBoundary, HealthCheck 등)

- **레이아웃** (`apps/web/src/components/layout/`)
  - 페이지 레이아웃 관리
  - 모바일 반응형 디자인

**특징**: 접근성 우선 (스크린 리더, 키보드 네비게이션, 점자 디바이스 연동)

---

### 10. 상태 관리 모듈

**목적**: 애플리케이션 전역 상태 관리

**주요 구성요소**:
- **Zustand 스토어** (`apps/web/src/store/`)
  - `bookStore.ts`: 교재 상태
  - `lessonStore.ts`: 레슨 상태
  - `progressStore.ts`: 진행 상황
  - `review*.ts`: 복습 상태
  - `voice.ts`: 음성 상태
  - `examStore.ts`: 시험 상태
  - `vocabStore.ts`: 어휘 상태

**기능**: 상태 저장 → 상태 업데이트 → 컴포넌트 반영

---

### 11. 서비스 레이어 모듈

**목적**: 비즈니스 로직 및 API 통신 관리

**주요 구성요소**:
- **API 클라이언트** (`apps/web/src/services/api.ts`)
  - Axios 기반 HTTP 클라이언트
  - 요청/응답 인터셉터

- **도메인 서비스** (`apps/web/src/services/`)
  - `books.ts`, `lessons.ts`, `units.ts`: 학습 관련 서비스
  - `answers.ts`, `review.ts`: 문제/복습 서비스
  - `VoiceService.ts`: 음성 서비스
  - `CommandService.ts`: 명령 서비스

- **학습 플로우** (`apps/web/src/services/learning/`)
  - `LearningFlow.ts`: 학습 플로우 베이스 클래스
  - `TextbookLearningFlow.ts`: 교과서 학습 플로우
  - `PassageLearningFlow.ts`: 지문 학습 플로우
  - `VocabLearningFlow.ts`: 어휘 학습 플로우

- **명령 패턴** (`apps/web/src/services/commands/`)
  - `Command.ts`: 명령 인터페이스
  - `CommandInvoker.ts`: 명령 실행자
  - `ControlCommand.ts`, `LearningCommand.ts`, `NavigateCommand.ts`: 구체적 명령

---

### 12. 확장 프로그램 모듈

**목적**: Chrome 확장 프로그램을 통한 학습 알림 및 동기화

**주요 구성요소**:
- **백그라운드 스크립트** (`apps/extension/src/background.ts`)
  - 확장 프로그램 생명주기 관리
  - 알림 스케줄링

- **콘텐츠 스크립트** (`apps/extension/src/contentScript.ts`)
  - 웹 페이지와의 상호작용
  - 동기화 포인트 로깅

- **팝업 UI** (`apps/extension/src/popup/`)
  - 확장 프로그램 팝업 인터페이스
  - 학습 알림 설정

---

### 13. 하드웨어 모듈

**목적**: 점자 디스플레이 하드웨어 제어

**주요 구성요소**:
- **Arduino 펌웨어** (`arduino/braille_3cell/`)
  - 3셀 점자 디스플레이 제어
  - 점자 패턴 표시
  - BLE 통신

- **테스트** (`arduino/braille_3cell_test/`)
  - 통합 테스트
  - 점자 패턴 테스트

---

### 14. 커리큘럼 자동 생성 모듈

**목적**: 강의대본(HWP) 분석을 통한 커리큘럼 자동 생성

**주요 구성요소**:
- **커리큘럼 생성기** (`api/app/services/curriculum_generator.py`)
  - 강의대본 분석 (분할 지점 파악, PDF 참조 정보 추출)
  - 학습 단위 생성
  - 의존성 분석

- **커리큘럼 템플릿** (`api/app/services/curriculum_template.py`)
  - 교재별 템플릿 정의 (문학/수1/영어)
  - 의존성 규칙 정의
  - 학습 경로 자동 생성

- **PDF-강의대본 매칭** (`api/app/services/pdf_script_matcher.py`)
  - 참조 정보 매칭
  - 신뢰도 계산
  - 레슨 간 유기적 연결

- **백엔드 API** (`api/app/routers/curriculum.py`)
  - `POST /api/v1/curriculum/generate`: 커리큘럼 생성
  - `GET /api/v1/curriculum/{curriculum_id}`: 커리큘럼 조회
  - `PATCH /api/v1/curriculum/{curriculum_id}`: 커리큘럼 수정
  - 커리큘럼 생성 완료 후 임시 파일 자동 삭제

- **프론트엔드** (`apps/web/src/pages/Curriculum/`)
  - 커리큘럼 목록 화면
  - 커리큘럼 생성 화면
  - 커리큘럼 상세 화면
  - 학습 경로 시각화
  - 레슨 간 연결 표시

**기능**: HWP 업로드 → 강의대본 분석 → 학습 단위 생성 → 커리큘럼 자동 생성 → 학습 경로 생성 → JSON 저장 (과목별 폴더)

---

### 18. 레슨 블록 시스템 모듈

**목적**: 강의대본을 레슨 블록 단위로 구조화하여 시각장애 학습자에게 최적화된 학습 경험 제공

**주요 구성요소**:
- **레슨 블록 분해기** (`api/app/services/lesson_block_decomposer.py`)
  - 규칙 기반 레슨 블록 분해
  - 과목별 패턴 매칭
  - 블록 타입 자동 분류

- **LangChain Flow** (`api/app/services/langchain_lesson_flow.py`)
  - LLM 기반 레슨 블록 자동 생성
  - 전처리 → LLM 분해 → JSON 파싱 → Pydantic 검증 → MongoDB 저장
  - 규칙 기반 폴백 지원

- **AI 프롬프트** (`api/app/services/ai_block_decomposer.py`)
  - 레슨 블록 분해 전용 프롬프트 정의
  - 과목별 특화 프롬프트

- **MongoDB 모델** (`api/app/db/mongodb_models.py`)
  - Lesson, LessonBlock Pydantic 모델
  - 블록 타입별 Content 모델
  - UI 동작 규칙 정의

- **JSON 변환기** (`api/app/services/json_to_mongodb_converter.py`)
  - 기존 JSON 커리큘럼 데이터를 MongoDB 형식으로 변환

- **백엔드 API** (`api/app/routers/lesson_blocks.py`)
  - `POST /api/v1/lesson-blocks/generate`: 레슨 블록 생성 (AI/규칙 기반)
  - `POST /api/v1/lesson-blocks/generate-batch`: 일괄 생성
  - `GET /api/v1/lesson-blocks/validate/{lesson_id}`: 레슨 블록 검증

**핵심 설계 원칙**:
- **점자는 신호등**: 3셀 점자로 현재 학습 상태만 표시
- **5가지 필수 요소**: 학습 목적, 점자 신호, 음성 범위, 사용자 인지, UI 동작 규칙
- **Document DB**: MongoDB로 레슨 단위 완결된 문서 저장

**기능**: 강의대본 입력 → 레슨 블록 분해 (AI/규칙) → MongoDB 저장 → UI 전달

---

### 15. 추천 시스템 모듈

**목적**: 학습자 맞춤형 추천 제공

**주요 구성요소**:
- **추천 엔진** (`api/app/services/recommendation_engine.py`)
  - PersonalizedRecommender 클래스
  - 콘텐츠 기반 필터링 (Sentence Transformers)
  - 사용자 프로파일링
  - 오답 패턴 기반 복습 추천
  - 간격 반복 학습 알고리즘

- **사용자 행동 프로파일러** (`api/app/services/user_behavior_profiler.py`)
  - 학습 패턴 분석
  - 약점 주제 식별
  - 선호도 벡터 계산
  - 학습 시간대 분석

- **백엔드 API** (`api/app/routers/recommendations.py`)
  - `GET /api/v1/recommendations/next-lesson`: 다음 레슨 추천
  - `GET /api/v1/recommendations/review`: 복습 추천

- **프론트엔드** (`apps/web/src/hooks/useRecommendations.ts`)
  - 추천 시스템 훅
  - "오늘 학습 이어하기" 화면에 추천 표시
  - 단원 목록에 추천 순서 표시

**기능**: 사용자 행동 분석 → 프로파일 생성 → 콘텐츠 기반 필터링 → 추천 생성

---

### 16. AI/ML 모듈

**목적**: 머신러닝 및 딥러닝 기반 기능 제공

**주요 구성요소**:
- **ML 기반 점자 변환** (`api/app/services/braille_ml.py`)
  - KoBERT 기반 Seq2Seq 모델
  - 문맥 인식 점자 변환
  - 동음이의어 처리 개선
  - 규칙 기반과 병행 (Fallback)

- **Vision Transformer** (`api/app/services/pdf_structure_classifier.py`)
  - LayoutLMv3 기반 PDF 구조 분류
  - 이미지 + 텍스트 멀티모달 분석
  - 블록 구조 자동 분류

- **생성형 AI** (`api/app/services/content_generator.py`)
  - LangChain + GPT-4/Claude
  - 문제 해설 자동 생성
  - 핵심 포인트 요약
  - 강의 대본 초안 생성

- **AI 기반 제작 자동화** (`api/app/services/content_auto_generator_ml.py`)
  - LangChain 기반 자동화
  - 매뉴얼 규칙 자동 적용
  - 품질 점수 자동 계산

- **LangChain 기반 레슨 블록 생성** (`api/app/services/langchain_lesson_flow.py`)
  - GPT-4o-mini 기반 레슨 블록 자동 분해
  - Pydantic 스키마 검증
  - MongoDB 자동 저장

**기술 스택**: PyTorch, Transformers (Hugging Face), LangChain, OpenAI GPT-4, Whisper, Sentence Transformers, MongoDB

---

### 17. 인프라 모듈

**목적**: 배포 및 운영 환경 설정

**주요 구성요소**:
- **Docker** (`api/Dockerfile`, `infra/docker-compose.yml`)
  - 컨테이너 이미지 빌드
  - 서비스 오케스트레이션

- **설정 파일** (`api/requirements.txt`, `api/requirements-ai.txt`, `apps/web/vite.config.ts` 등)
  - 의존성 관리
  - AI/ML 의존성 분리
  - 빌드 설정

---

## 📊 모듈별 통계

### 백엔드 API
- 총 파일 수: 약 76개
- 주요 모듈: 라우터(11), 서비스(35), 스키마(8), 테스트(9)

### 프론트엔드 웹
- 총 파일 수: 약 200개
- 주요 모듈: 페이지(50+), 컴포넌트(36), 훅(29), 서비스(25), 상태 관리(13)

### 확장 프로그램
- 총 파일 수: 5개
- 주요 모듈: 백그라운드 스크립트, 콘텐츠 스크립트, 팝업 UI

### 하드웨어
- 총 파일 수: 8개
- 주요 모듈: Arduino 펌웨어, 테스트 스케치

### 문서
- 총 파일 수: 22개
- 주요 문서: 개발 가이드, API 문서, 테스트 가이드

---

*작성일: 2024년*
*마지막 업데이트: 2024년*
