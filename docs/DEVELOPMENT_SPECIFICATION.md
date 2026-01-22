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
| 백엔드 API | 메인 애플리케이션 | api/app/db | mongodb_models.py | MongoDB 모델 정의 (선택적 사용) |
| 백엔드 API | 메인 애플리케이션 | api/app/db | __init__.py | DB 패키지 초기화 파일 |

### 1.2 API 라우터

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 백엔드 API | API 라우터 | api/app/routers | health.py | 헬스 체크 API 엔드포인트 |
| 백엔드 API | API 라우터 | api/app/routers | subjects.py | 과목 목록 API (KOREAN, MATH, ENGLISH) |
| 백엔드 API | API 라우터 | api/app/routers | books.py | 교재 관리 API (PDF 업로드, 목록 조회, 과목별 필터링, 삭제) |
| 백엔드 API | API 라우터 | api/app/routers | lessons.py | 레슨 관리 API (레슨 목록, 상세 조회, question_count 계산) |
| 백엔드 API | API 라우터 | api/app/routers | units.py | 학습 단위 관리 API (단원 목록, 콘텐츠 조회, image_path, content_image_paths, ai_explanation, braille_keywords 지원) |
| 백엔드 API | API 라우터 | api/app/routers | progress.py | 학습 진행 상황 API (진행률 조회, 업데이트, 오늘 학습 이어하기) |
| 백엔드 API | API 라우터 | api/app/routers | answers.py | 답안 관리 API (답안 제출, 정답 확인) |
| 백엔드 API | API 라우터 | api/app/routers | curriculum.py | 커리큘럼 관리 API (관리자용 생성, 사용자용 조회, 레슨 목록, 특정 레슨 조회) |
| 백엔드 API | API 라우터 | api/app/routers | ai.py | AI 강의 교사 API (레슨 설명 생성, 문제 해설 생성, 문학 AI 기능 통합) |
| 백엔드 API | API 라우터 | api/app/routers | literature.py | 문학 학습 API (강의 목록, 문제 목록, 이미지, 본문 콘텐츠 조회) |
| 백엔드 API | API 라우터 | api/app/routers | literature_ai.py | [DEPRECATED] 문학 AI 설명 API (기능이 ai.py로 통합됨, 호환성 유지) |
| 백엔드 API | API 라우터 | api/app/routers | __init__.py | 라우터 패키지 초기화 파일 |

### 1.3 데이터 스키마

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 백엔드 API | 데이터 스키마 | api/app/schemas | answer.py | 답안 관련 Pydantic 스키마 정의 |
| 백엔드 API | 데이터 스키마 | api/app/schemas | book.py | 교재 관련 Pydantic 스키마 정의 |
| 백엔드 API | 데이터 스키마 | api/app/schemas | lesson.py | 레슨 관련 Pydantic 스키마 정의 (question_count 포함) |
| 백엔드 API | 데이터 스키마 | api/app/schemas | progress.py | 진행 상황 관련 Pydantic 스키마 정의 |
| 백엔드 API | 데이터 스키마 | api/app/schemas | unit.py | 단원 관련 Pydantic 스키마 정의 (image_path, content_image_paths, ai_explanation, braille_keywords 포함) |
| 백엔드 API | 데이터 스키마 | api/app/schemas | curriculum.py | 커리큘럼 관련 Pydantic 스키마 정의 |
| 백엔드 API | 데이터 스키마 | api/app/schemas | learning_unit_types.py | 학습 단위 타입 정의 |
| 백엔드 API | 데이터 스키마 | api/app/schemas | review.py | 복습 관련 Pydantic 스키마 정의 (라우터 삭제됨, 스키마만 유지) |
| 백엔드 API | 데이터 스키마 | api/app/schemas | syncpoint.py | 동기화 포인트 관련 Pydantic 스키마 정의 (라우터 삭제됨, 스키마만 유지) |
| 백엔드 API | 데이터 스키마 | api/app/schemas | __init__.py | 스키마 패키지 초기화 파일 |

### 1.4 핵심 서비스

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 백엔드 API | 핵심 서비스 | api/app/services | textbook_pipeline.py | 교재 파이프라인 서비스 (과목별 PDF 파싱: 문학, 수학Ⅰ, 영어) |
| 백엔드 API | 핵심 서비스 | api/app/services | __init__.py | 서비스 패키지 초기화 파일 |

### 1.5 PDF 추출 모듈

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 백엔드 API | PDF 추출 모듈 | api/app/extraction | base_extractor.py | PDF 추출기 베이스 클래스 (인터페이스) |
| 백엔드 API | PDF 추출 모듈 | api/app/extraction | extractors.py | PDF 추출기 구현 |
| 백엔드 API | PDF 추출 모듈 | api/app/extraction | pdfplumber_extractor.py | PDFPlumber 기반 텍스트 추출기 |
| 백엔드 API | PDF 추출 모듈 | api/app/extraction | ocr_extractor.py | OCR 기반 텍스트 추출기 |
| 백엔드 API | PDF 추출 모듈 | api/app/extraction | image_processor.py | PDF 이미지 처리 |
| 백엔드 API | PDF 추출 모듈 | api/app/extraction | text_normalizer.py | 텍스트 정규화 |
| 백엔드 API | PDF 추출 모듈 | api/app/extraction | utils.py | PDF 추출 유틸리티 함수 |
| 백엔드 API | PDF 추출 모듈 | api/app/extraction | exceptions.py | PDF 추출 예외 정의 |

### 1.6 파싱 모듈

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 백엔드 API | 파싱 모듈 | api/app/parsing | document_parser.py | 문서 파서 메인 클래스 |
| 백엔드 API | 파싱 모듈 | api/app/parsing | schemas.py | 파싱 스키마 정의 |
| 백엔드 API | 파싱 모듈 | api/app/parsing | parsing_rules.py | 파싱 규칙 정의 |
| 백엔드 API | 파싱 모듈 | api/app/parsing | utils.py | 파싱 유틸리티 함수 |
| 백엔드 API | 파싱 모듈 | api/app/parsing/strategies | base_strategy.py | 파싱 전략 베이스 클래스 |
| 백엔드 API | 파싱 모듈 | api/app/parsing/strategies | literature_strategy.py | 문학 과목 파싱 전략 |
| 백엔드 API | 파싱 모듈 | api/app/parsing/strategies | math1_strategy.py | 수학Ⅰ 과목 파싱 전략 |
| 백엔드 API | 파싱 모듈 | api/app/parsing/strategies | english_strategy.py | 영어 과목 파싱 전략 |
| 백엔드 API | 파싱 모듈 | api/app/parsing/strategies | __init__.py | 전략 패키지 초기화 파일 |
| 백엔드 API | 파싱 모듈 | api/app/parsing/block_parsers | concept_parser.py | 개념 블록 파서 |
| 백엔드 API | 파싱 모듈 | api/app/parsing/block_parsers | example_parser.py | 예제 블록 파서 |
| 백엔드 API | 파싱 모듈 | api/app/parsing/block_parsers | passage_parser.py | 지문 블록 파서 |
| 백엔드 API | 파싱 모듈 | api/app/parsing/block_parsers | question_parser.py | 문제 블록 파서 |
| 백엔드 API | 파싱 모듈 | api/app/parsing/classifiers | rule_classifier.py | 규칙 기반 블록 분류기 |
| 백엔드 API | 파싱 모듈 | api/app/parsing/classifiers | ml_classifier.py | ML 기반 블록 분류기 |

### 1.7 AI/ML 모듈

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 백엔드 API | AI/ML 모듈 | api/app/genai | explanation_generator.py | AI 설명 생성기 (개념, 작품, 문제 해설) |
| 백엔드 API | AI/ML 모듈 | api/app/genai | metadata_enricher.py | 메타데이터 보강기 |
| 백엔드 API | AI/ML 모듈 | api/app/genai | rag_recommender.py | RAG 기반 추천 시스템 |
| 백엔드 API | AI/ML 모듈 | api/app/genai | __init__.py | GenAI 패키지 초기화 파일 |
| 백엔드 API | AI/ML 모듈 | api/app/genai | README.md | GenAI 모듈 문서 (Level 3 LLM 기능) |
| 백엔드 API | AI/ML 모듈 | api/app/ml | block_classifier.py | ML 기반 블록 분류기 |
| 백엔드 API | AI/ML 모듈 | api/app/ml | deduplicator.py | 중복 제거기 |
| 백엔드 API | AI/ML 모듈 | api/app/ml | __init__.py | ML 패키지 초기화 파일 |
| 백엔드 API | AI/ML 모듈 | api/app/ml | README.md | ML 모듈 문서 (Level 1 ML 기능) |
| 백엔드 API | AI/ML 모듈 | api/app/dl | layout_analyzer.py | 딥러닝 기반 레이아웃 분석기 |
| 백엔드 API | AI/ML 모듈 | api/app/dl | math_recognizer.py | 수식 인식기 |
| 백엔드 API | AI/ML 모듈 | api/app/dl | __init__.py | DL 패키지 초기화 파일 |
| 백엔드 API | AI/ML 모듈 | api/app/dl | README.md | DL 모듈 문서 (Level 2 딥러닝 기능) |

### 1.8 어셈블리 모듈

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 백엔드 API | 어셈블리 모듈 | api/app/assembly | lecture_assembler.py | 강의 어셈블러 (JSON 데이터를 Unit으로 변환) |

### 1.9 유틸리티 및 기타

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 백엔드 API | 유틸리티 | api/app/utils | text_utils.py | 텍스트 처리 유틸리티 함수 |
| 백엔드 API | 유틸리티 | api/app/utils | data_file_handler.py | 데이터 파일 핸들러 (JSON 파일 읽기/쓰기) |
| 백엔드 API | 유틸리티 | api/app/utils | id_generator.py | ID 생성기 (unit_id, lesson_id 등) |
| 백엔드 API | 유틸리티 | api/app/utils | ml_content_similarity.py | ML 기반 콘텐츠 유사도 계산 |
| 백엔드 API | 유틸리티 | api/app/utils | __init__.py | 유틸리티 패키지 초기화 파일 |

### 1.10 스크립트 및 설정

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 백엔드 API | 스크립트 | api/scripts | create_units_from_lecture.py | lecture JSON 파일을 기반으로 Unit 생성 스크립트 |
| 백엔드 API | 스크립트 | api/scripts | add_image_path_column.py | Unit 테이블에 image_path 컬럼 추가 마이그레이션 스크립트 |
| 백엔드 API | 스크립트 | api/scripts | reparse_literature.py | 문학 교재 재파싱 스크립트 |
| 백엔드 API | 스크립트 | api/scripts | test_lecture_detection.py | 강의 감지 테스트 스크립트 |
| 백엔드 API | 스크립트 | api/scripts/admin | delete_book.py | 교재 삭제 관리 스크립트 |
| 백엔드 API | 스크립트 | api/scripts/admin | delete_curriculum.py | 커리큘럼 삭제 관리 스크립트 |
| 백엔드 API | 스크립트 | api/scripts/admin | cleanup_books.py | 교재 정리 스크립트 |
| 백엔드 API | 스크립트 | api/scripts/pipeline | run_textbook_pipeline.py | 교재 파이프라인 실행 스크립트 |
| 백엔드 API | 스크립트 | api/scripts/ml | build_training_dataset.py | 학습 데이터셋 구축 스크립트 |
| 백엔드 API | 스크립트 | api/scripts/examples | run_pipeline_example.py | 파이프라인 실행 예제 |
| 백엔드 API | 스크립트 | api/scripts/examples | test_ml_features.py | ML 기능 테스트 예제 |
| 백엔드 API | 스크립트 | api/scripts/examples | test_parser.py | 파서 테스트 예제 |
| 백엔드 API | 스크립트 | api/scripts/experiments | pdf_region_capturer.py | PDF 영역 캡처 실험 스크립트 |
| 백엔드 API | 스크립트 | api/scripts/experiments | pdf_region_detector.py | PDF 영역 감지 실험 스크립트 |
| 백엔드 API | 스크립트 | api/scripts | start_server.bat | Windows 서버 시작 스크립트 |
| 백엔드 API | 스크립트 | api/scripts | start_server.sh | Linux/Mac 서버 시작 스크립트 |
| 백엔드 API | 스크립트 | api/scripts | README.md | 스크립트 디렉토리 문서 (스크립트 사용 가이드) |
| 백엔드 API | 설정 | api | requirements.txt | Python 기본 의존성 목록 |
| 백엔드 API | 설정 | api | requirements-ai.txt | AI/ML 기능 의존성 목록 |

### 1.12 프로젝트 루트 스크립트

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 프로젝트 루트 | 유틸리티 스크립트 | . | check_all_books.py | 모든 교재 상태 확인 스크립트 |
| 프로젝트 루트 | 유틸리티 스크립트 | . | check_lesson01_db.py | 레슨 01 데이터베이스 확인 스크립트 |
| 프로젝트 루트 | 유틸리티 스크립트 | . | quick_check.py | 빠른 상태 확인 스크립트 |
| 프로젝트 루트 | 유틸리티 스크립트 | . | monitor_parsing.py | 파싱 모니터링 스크립트 |
| 프로젝트 루트 | 커리큘럼 생성 | . | create_literature_curriculum.py | 문학 커리큘럼 생성 스크립트 |
| 프로젝트 루트 | 커리큘럼 생성 | . | create_math1_curriculum.py | 수학Ⅰ 커리큘럼 생성 스크립트 |
| 프로젝트 루트 | 커리큘럼 생성 | . | create_english_curriculum.py | 영어 커리큘럼 생성 스크립트 |
| 프로젝트 루트 | 데이터 추출 | . | extract_lectures_from_images.py | 이미지에서 강의 추출 스크립트 |
| 프로젝트 루트 | 레슨 업데이트 | . | update_literature_lesson01.py | 문학 레슨 01 업데이트 스크립트 |
| 프로젝트 루트 | 레슨 업데이트 | . | update_literature_lesson01_v2.py | 문학 레슨 01 업데이트 스크립트 (v2) |
| 프로젝트 루트 | 검증 스크립트 | . | verify_curriculum.py | 커리큘럼 검증 스크립트 |
| 프로젝트 루트 | 검증 스크립트 | . | verify_math1.py | 수학Ⅰ 검증 스크립트 |
| 프로젝트 루트 | 테스트 스크립트 | . | test_lecture_extraction.py | 강의 추출 테스트 스크립트 |
| 프로젝트 루트 | 테스트 스크립트 | . | test_literature_lesson01_api.py | 문학 레슨 01 API 테스트 스크립트 |

### 1.11 보관된 파일 (Archived)

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 백엔드 API | 보관 파일 | api/archived | ai_text_postprocessor.py | LLM 기반 텍스트 후처리기 (OCR 오류 수정, 텍스트 정리, 구조 정규화) - 레거시 |
| 백엔드 API | 보관 파일 | api/archived | literature_extractor.py | 문학 PDF 전용 추출기 (텍스트 중심, 줄 단위 분리) - 레거시 |

---

## 2. 프론트엔드 웹 모듈

### 2.1 메인 애플리케이션

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 프론트엔드 웹 | 메인 애플리케이션 | apps/web/src | main.tsx | React 애플리케이션 진입점, ErrorBoundary 설정 |
| 프론트엔드 웹 | 메인 애플리케이션 | apps/web/src/app | App.tsx | 메인 App 컴포넌트 (라우터 설정, 전역 컴포넌트) |
| 프론트엔드 웹 | 메인 애플리케이션 | apps/web/src/app | routes.tsx | React Router 라우팅 설정 (MVP 3.0 Single-flow UI) |

### 2.2 주요 페이지 (MVP 3.0 - Single-flow UI)

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 프론트엔드 웹 | 주요 페이지 | apps/web/src/pages | Start.tsx | 시작 페이지 (학습 이어하기, 교재 선택) |
| 프론트엔드 웹 | 주요 페이지 | apps/web/src/pages | BookSelect.tsx | 교재 선택 페이지 (과목별 필터링, 삭제 기능) |
| 프론트엔드 웹 | 주요 페이지 | apps/web/src/pages | QuestionLearning.tsx | 문제 학습 페이지 (전체 유닛 순서대로 학습, 개념/본문/문제/요약 포함) |
| 프론트엔드 웹 | 주요 페이지 | apps/web/src/pages | QuestionList.tsx | 문제 목록 페이지 (레슨별 문제 목록) |
| 프론트엔드 웹 | 주요 페이지 | apps/web/src/pages | LearningSummary.tsx | 학습 종료 페이지 (오늘의 학습, 전체 진행률) |

### 2.3 레거시 페이지 (호환성 유지)

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 프론트엔드 웹 | 레거시 페이지 | apps/web/src/pages | Main.tsx | 메인 페이지 (문학 학습 바로가기, 과목 선택) |
| 프론트엔드 웹 | 레거시 페이지 | apps/web/src/pages | Book.tsx | 교재 목록 페이지 (과목별 필터링, 국어 선택 시 문학 강의 목록 표시) |
| 프론트엔드 웹 | 레거시 페이지 | apps/web/src/pages | Lesson.tsx | 레슨 페이지 (학습 화면) |
| 프론트엔드 웹 | 레거시 페이지 | apps/web/src/pages | Unit.tsx | 단원 페이지 |
| 프론트엔드 웹 | 레거시 페이지 | apps/web/src/pages | Question.tsx | 문제 풀이 페이지 |
| 프론트엔드 웹 | 레거시 페이지 | apps/web/src/pages | Textbook.tsx | 교재 관리 페이지 |
| 프론트엔드 웹 | 레거시 페이지 | apps/web/src/pages | Curriculum.tsx | 커리큘럼 목록 페이지 (조회만) |
| 프론트엔드 웹 | 레거시 페이지 | apps/web/src/pages | NotFound.tsx | 404 에러 페이지 |

### 2.4 재사용 컴포넌트

#### 2.4.1 점자 컴포넌트

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 프론트엔드 웹 | 점자 컴포넌트 | apps/web/src/components/braille | BrailleCell.tsx | 점자 셀 컴포넌트 (단일 셀) |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/braille | BrailleCells.tsx | 점자 셀 그룹 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/braille | BrailleGrid.tsx | 점자 그리드 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/braille | BrailleRow.tsx | 점자 행 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/braille | BrailleStrip.tsx | 점자 스트립 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/braille | ChunkNavigation.tsx | 점자 청크 네비게이션 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/braille | ArduinoButtonControl.tsx | Arduino 버튼 제어 컴포넌트 |

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
| 프론트엔드 웹 | UI 컴포넌트 | apps/web/src/components/ui | AppShellMobile.tsx | 모바일 앱 셸 컴포넌트 (헤더/푸터 옵션 지원) |

#### 2.4.4 시스템 컴포넌트

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 프론트엔드 웹 | 시스템 컴포넌트 | apps/web/src/components/system | DevHealth.tsx | 개발 헬스 체크 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/system | ErrorBoundary.tsx | 에러 바운더리 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/system | HealthCheck.tsx | 헬스 체크 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/system | PerformanceMonitor.tsx | 성능 모니터링 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/system | ToastA11y.tsx | 접근성 토스트 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/debug | VoiceRecognitionDebug.tsx | 음성 인식 디버그 컴포넌트 |

#### 2.4.5 AI 컴포넌트

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 프론트엔드 웹 | AI 컴포넌트 | apps/web/src/components/ai | AIExplanationCard.tsx | AI 설명 카드 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/ai | AIMetadataCard.tsx | AI 메타데이터 카드 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/ai | AIQuestionInput.tsx | AI 문제 입력 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/ai | ConceptExplanationCard.tsx | 개념 설명 카드 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/ai | SimilarContentCard.tsx | 유사 콘텐츠 카드 컴포넌트 |

#### 2.4.6 단원 컴포넌트

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 프론트엔드 웹 | 단원 컴포넌트 | apps/web/src/components/unit | UnitViewer.tsx | 단원 뷰어 컴포넌트 (CONCEPT_SUMMARY, QUESTION 등 타입별 표시) |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/unit | ConceptViewer.tsx | 개념 뷰어 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/unit | WorkViewer.tsx | 작품 뷰어 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/unit | UnitHeader.tsx | 단원 헤더 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/unit | UnitImage.tsx | 단원 이미지 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/unit | BrailleStatusPanel.tsx | 점자 상태 패널 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/unit | AIExplanationCard.tsx | AI 설명 카드 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/unit | constants.ts | 단원 관련 상수 정의 |

#### 2.4.7 문제 컴포넌트

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 프론트엔드 웹 | 문제 컴포넌트 | apps/web/src/components/question | QuestionDisplay.tsx | 문제 표시 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/question | AnswerInput.tsx | 답안 입력 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/question | AnswerResult.tsx | 답안 결과 표시 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/question | ChoiceComparison.tsx | 선택지 비교 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/question | WrongAnswerList.tsx | 오답 목록 컴포넌트 |

#### 2.4.8 기타 컴포넌트

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/home | BrailleDeviceCard.tsx | 홈 화면 점자 디바이스 카드 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/home | ContinueLearningCard.tsx | 홈 화면 학습 이어하기 카드 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/home | PDFManagementCard.tsx | 홈 화면 PDF 관리 카드 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/home | SubjectSelectCard.tsx | 홈 화면 과목 선택 카드 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/textbook | BookUpload.tsx | 책 업로드 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/textbook | PDFUpload.tsx | PDF 업로드 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/textbook | TextbookList.tsx | 교과서 목록 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/textbook | UnitContent.tsx | 단원 콘텐츠 표시 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/textbook | ProblemContent.tsx | 문제 콘텐츠 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/textbook | SimilarContentSection.tsx | 유사 콘텐츠 섹션 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/lesson | LessonList.tsx | 레슨 목록 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/curriculum | BlockTimestampList.tsx | 블록 타임스탬프 리스트 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/subject | SubjectDisplayAdapter.tsx | 과목별 표시 어댑터 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/layout | PageLayout.tsx | 페이지 레이아웃 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/layout | PageShell.tsx | 페이지 셸 컴포넌트 |

### 2.5 커스텀 훅

#### 2.5.1 핵심 훅

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 프론트엔드 웹 | 핵심 훅 | apps/web/src/hooks | useAutoBraille.ts | 자동 점자 출력 훅 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks | useAutoGuidance.ts | 자동 안내 훅 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks | useBrailleBLE.ts | BLE 점자 디바이스 훅 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks | useBrailleChunkReader.ts | 점자 청크 리더 훅 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks | useArduinoButtons.ts | Arduino 버튼 제어 훅 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks | useSTT.ts | 음성 인식(STT) 훅 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks | useTTS.ts | 음성 합성(TTS) 훅 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks | useVoiceCommands.ts | 음성 명령 훅 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks | usePageBase.ts | 페이지 기본 훅 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks | usePerformance.ts | 성능 모니터링 훅 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks | useAILearningAssistant.ts | AI 학습 어시스턴트 훅 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks | useAILectureTeacher.ts | AI 강의 교사 훅 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks | useUnitAIExplanation.ts | 단원 AI 설명 훅 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks | useUnitAudio.ts | 단원 오디오 훅 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks | useUnitBraille.ts | 단원 점자 훅 |

#### 2.5.2 API 훅

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 프론트엔드 웹 | API 훅 | apps/web/src/hooks/api | useProgress.ts | 진행 상황 API 훅 |

#### 2.5.3 점자 디바이스 훅

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 프론트엔드 웹 | 점자 디바이스 훅 | apps/web/src/hooks/braille | BrailleDeviceAdapter.ts | 점자 디바이스 어댑터 인터페이스 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks/braille | BrailleDeviceFactory.ts | 점자 디바이스 팩토리 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks/braille | GenericBLEAdapter.ts | 범용 BLE 어댑터 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks/braille | MockBrailleAdapter.ts | 모의 점자 디바이스 어댑터 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks/braille | OrbitReaderAdapter.ts | Orbit Reader 어댑터 |

#### 2.5.4 음성 명령 훅

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 프론트엔드 웹 | 음성 명령 훅 | apps/web/src/hooks/voice | commands.ts | 음성 명령 정의 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks/voice | matchers.ts | 음성 명령 매칭 로직 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks/voice | normalizers.ts | 음성 명령 정규화 |

### 2.6 서비스 레이어

#### 2.6.1 API 서비스

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 프론트엔드 웹 | API 서비스 | apps/web/src/services/api | index.ts | API 클라이언트 (Fetch 기반, 재시도 로직 포함) |
| 프론트엔드 웹 | 서비스 | apps/web/src/services/api | client.ts | API 클라이언트 설정 |

#### 2.6.2 도메인 서비스

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 프론트엔드 웹 | 도메인 서비스 | apps/web/src/services | lessons.ts | 레슨 서비스 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services | units.ts | 단원 서비스 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services | progress.ts | 진행 상황 서비스 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services | answers.ts | 답안 서비스 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services | curriculum.ts | 커리큘럼 서비스 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services | literature.ts | 문학 학습 서비스 (강의 목록, 문제 목록, 이미지, 본문 콘텐츠) |
| 프론트엔드 웹 | 서비스 | apps/web/src/services/books | index.ts | 교재 서비스 (교재 관리, 삭제 기능 포함) |
| 프론트엔드 웹 | 서비스 | apps/web/src/services/ai | index.ts | AI 서비스 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services/voice | index.ts | 음성 서비스 |

#### 2.6.3 학습 플로우 서비스

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 프론트엔드 웹 | 학습 플로우 서비스 | apps/web/src/services/learning | LearningFlow.ts | 학습 플로우 베이스 클래스 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services/learning | TextbookLearningFlow.ts | 교과서 학습 플로우 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services/learning | PassageLearningFlow.ts | 지문 학습 플로우 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services/learning | VocabLearningFlow.ts | 어휘 학습 플로우 |

#### 2.6.4 명령 패턴 서비스

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 프론트엔드 웹 | 명령 패턴 서비스 | apps/web/src/services | CommandService.ts | 명령 서비스 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services/commands | Command.ts | 명령 인터페이스 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services/commands | CommandInvoker.ts | 명령 실행자 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services/commands | ControlCommand.ts | 제어 명령 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services/commands | LearningCommand.ts | 학습 명령 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services/commands | NavigateCommand.ts | 네비게이션 명령 |

#### 2.6.5 기타 서비스

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 프론트엔드 웹 | 기타 서비스 | apps/web/src/services/passage | PassageService.ts | 지문 서비스 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services/question | QuestionService.ts | 문제 서비스 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services/textbook | TextbookService.ts | 교과서 서비스 |

### 2.7 상태 관리

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 프론트엔드 웹 | 상태 관리 | apps/web/src/store | bookStore.ts | 교재 상태 관리 (Zustand) |
| 프론트엔드 웹 | 상태 관리 | apps/web/src/store | lessonStore.ts | 레슨 상태 관리 |
| 프론트엔드 웹 | 상태 관리 | apps/web/src/store | progressStore.ts | 진행 상황 상태 관리 |
| 프론트엔드 웹 | 상태 관리 | apps/web/src/store | voice.ts | 음성 상태 관리 |
| 프론트엔드 웹 | 상태 관리 | apps/web/src/store | learnStore.ts | 학습 상태 관리 |
| 프론트엔드 웹 | 상태 관리 | apps/web/src/store | home.ts | 홈 상태 관리 |
| 프론트엔드 웹 | 상태 관리 | apps/web/src/store | keywords.ts | 키워드 상태 관리 |
| 프론트엔드 웹 | 상태 관리 | apps/web/src/store | examStore.ts | 시험 상태 관리 |
| 프론트엔드 웹 | 상태 관리 | apps/web/src/store | lessonSession.ts | 레슨 세션 상태 |
| 프론트엔드 웹 | 상태 관리 | apps/web/src/store | vocabStore.ts | 어휘 상태 관리 |

### 2.8 타입 정의

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 프론트엔드 웹 | 타입 정의 | apps/web/src/types | answer.ts | 답안 타입 정의 |
| 프론트엔드 웹 | 타입 정의 | apps/web/src/types | api.ts | API 타입 정의 |
| 프론트엔드 웹 | 타입 정의 | apps/web/src/types | book.ts | 교재 타입 정의 |
| 프론트엔드 웹 | 타입 정의 | apps/web/src/types | chat.ts | 채팅 타입 정의 |
| 프론트엔드 웹 | 타입 정의 | apps/web/src/types | errors.ts | 에러 타입 정의 |
| 프론트엔드 웹 | 타입 정의 | apps/web/src/types | global.d.ts | 전역 타입 정의 |
| 프론트엔드 웹 | 타입 정의 | apps/web/src/types | index.ts | 타입 인덱스 |
| 프론트엔드 웹 | 타입 정의 | apps/web/src/types | lesson.ts | 레슨 타입 정의 |
| 프론트엔드 웹 | 타입 정의 | apps/web/src/types | progress.ts | 진행 상황 타입 정의 |
| 프론트엔드 웹 | 타입 정의 | apps/web/src/types | unit.ts | 단원 타입 정의 (CONCEPT_SUMMARY, image_path, content_image_paths, ai_explanation, braille_keywords 포함) |
| 프론트엔드 웹 | 타입 정의 | apps/web/src/types | voice.ts | 음성 타입 정의 |
| 프론트엔드 웹 | 타입 정의 | apps/web/src/types | curriculum.ts | 커리큘럼 타입 정의 |
| 프론트엔드 웹 | 타입 정의 | apps/web/src/types | explore.ts | 탐색 타입 정의 |

### 2.9 유틸리티 및 기타

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 프론트엔드 웹 | 유틸리티 | apps/web/src/utils | contentExtractor.ts | 콘텐츠 추출기 |
| 프론트엔드 웹 | 유틸리티 | apps/web/src/utils | problemParser.ts | 문제 파서 |
| 프론트엔드 웹 | 유틸리티 | apps/web/src/utils/pdf | references.ts | PDF 참조 유틸리티 |
| 프론트엔드 웹 | 유틸리티 | apps/web/src/utils/text | metadata.ts | 텍스트 메타데이터 유틸리티 |
| 프론트엔드 웹 | 유틸리티 | apps/web/src/utils/text | sectionMatcher.ts | 섹션 매칭 유틸리티 |
| 프론트엔드 웹 | 유틸리티 | apps/web/src/utils/audio | notification.ts | 오디오 알림 유틸리티 |
| 프론트엔드 웹 | 전략 | apps/web/src/strategies | subjectLearning.ts | 과목별 학습 전략 |
| 프론트엔드 웹 | STT | apps/web/src/stt | GoogleStreamingProvider.ts | Google STT 스트리밍 프로바이더 |
| 프론트엔드 웹 | 설정 | apps/web/src/config | brailleDisplay.ts | 점자 디스플레이 설정 |
| 프론트엔드 웹 | 컨텍스트 | apps/web/src/contexts | KeyboardContext.tsx | 키보드 컨텍스트 |
| 프론트엔드 웹 | 스타일 | apps/web/src/styles | tokens.css | 디자인 토큰 CSS |
| 프론트엔드 웹 | 스타일 | apps/web/src/styles | util.css | 유틸리티 스타일 CSS |
| 프론트엔드 웹 | 스타일 | apps/web/src/styles | animations.css | 애니메이션 CSS |
| 프론트엔드 웹 | 스타일 | apps/web/src | index.css | 전역 스타일 CSS |
| 프론트엔드 웹 | 타입 정의 | apps/web/src | vite-env.d.ts | Vite 환경 타입 정의 |
| 프론트엔드 웹 | 설정 | apps/web | index.html | HTML 진입점 |
| 프론트엔드 웹 | 설정 | apps/web | vite.config.ts | Vite 빌드 설정 |
| 프론트엔드 웹 | 설정 | apps/web | tailwind.config.js | Tailwind CSS 설정 |
| 프론트엔드 웹 | 설정 | apps/web | postcss.config.js | PostCSS 설정 |
| 프론트엔드 웹 | 설정 | apps/web | playwright.config.ts | Playwright E2E 테스트 설정 |
| 프론트엔드 웹 | 스크립트 | apps/web/scripts | gen-icons.mjs | PWA 아이콘 생성 스크립트 |
| 프론트엔드 웹 | 문서 | apps/web | README.md | 프론트엔드 웹 애플리케이션 설명 문서 |
| 프론트엔드 웹 | 문서 | apps/web | FRONTEND_AI_UPDATE.md | 프론트엔드 AI 기능 업데이트 문서 |
| 프론트엔드 웹 | 문서 | apps/web | REFACTORING_STRATEGY.md | 프론트엔드 리팩토링 전략 문서 |
| 프론트엔드 웹 | 문서 | apps/web | REFACTORING_SUMMARY.md | 프론트엔드 리팩토링 요약 문서 |
| 프론트엔드 웹 | 문서 | apps/web | clear-cache.md | 캐시 정리 가이드 문서 |

---

## 3. 하드웨어 모듈

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 하드웨어 | 펌웨어 | arduino/braille_3cell | braille_3cell.ino | 3셀 점자 디스플레이 메인 스케치 (버튼 제어 포함) |
| 하드웨어 | 펌웨어 | arduino/braille_3cell | braille.cpp | 점자 구현 C++ 소스 |
| 하드웨어 | 펌웨어 | arduino/braille_3cell | braille.h | 점자 헤더 파일 |
| 하드웨어 | 펌웨어 | arduino/braille_3cell | BrailleConverter.cpp | 점자 변환기 C++ 소스 |
| 하드웨어 | 펌웨어 | arduino/braille_3cell | BrailleConverter.h | 점자 변환기 헤더 파일 |
| 하드웨어 | 펌웨어 | arduino/braille_3cell | BrailleMap.h | 점자 맵핑 헤더 파일 |
| 하드웨어 | 문서 | arduino | README.md | Arduino 프로젝트 설명 문서 |

---

## 4. Raspberry Pi 모듈

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| Raspberry Pi | 서버 | raspberrypi | ble_server.py | BLE 서버 스크립트 (점자 디바이스 통신) |
| Raspberry Pi | 문서 | raspberrypi | README.md | Raspberry Pi 프로젝트 설명 문서 |

---

## 5. 인프라 및 기타 모듈

### 5.1 데이터

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 데이터 | 데이터 디렉토리 문서 | api/data | README.md | 데이터 디렉토리 구조 및 사용 가이드 |
| 데이터 | 추출된 데이터 | api/data/literature | lectures/*.json | 강의 JSON 파일들 |
| 데이터 | 추출된 데이터 | api/data/literature | problems/*.json | 문제 JSON 파일들 |
| 데이터 | 추출된 데이터 | api/data/literature | content/*.json | 콘텐츠 JSON 파일들 |
| 데이터 | 추출된 데이터 | api/data/literature | concepts_images/*.png | 개념 이미지 파일들 |
| 데이터 | 추출된 데이터 | api/data/literature | content_images/*.png | 본문 이미지 파일들 |
| 데이터 | 추출된 데이터 | api/data/literature | problems_images/*.png | 문제 이미지 파일들 |
| 데이터 | 추출된 데이터 | api/data/literature | pages/*.png | 페이지 이미지 파일들 |
| 데이터 | 추출된 데이터 | api/data/literature | visualizations/*.png | 시각화 이미지 파일들 |
| 데이터 | 추출된 데이터 | api/data/english | *.png | 영어 교재 이미지 파일들 |
| 데이터 | 추출된 데이터 | api/data/math1 | *.png | 수학Ⅰ 교재 이미지 파일들 |
| 데이터 | ML 캐시 | api/data/ml_cache | *.pkl | ML 모델 캐시 파일들 (Sentence Transformers 임베딩 캐시) |
| 데이터 | PDF 파일 | data | *.pdf | 수능특강 PDF 파일들 |

### 5.2 문서

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 문서 | 프로젝트 문서 | docs | DEVELOPMENT_SPECIFICATION.md | 개발명세서 (본 문서) |
| 문서 | 프로젝트 문서 | docs | DATABASE_SCHEMA.md | 데이터베이스 스키마 문서 |
| 문서 | 프로젝트 문서 | docs | ARDUINO_BUTTON_INTEGRATION.md | Arduino 버튼 통합 문서 |
| 문서 | 프로젝트 문서 | docs | WBS.md | 작업 분해 구조 문서 |
| 문서 | 프로젝트 문서 | docs | SCREEN_SPECIFICATION.md | 화면 정의서 문서 |
| 문서 | 프로젝트 문서 | docs | SYSTEM_ARCHITECTURE.md | 시스템 아키텍처 문서 |
| 문서 | 프로젝트 문서 | docs | MENU_FLOW.md | 메뉴 흐름도 문서 |
| 문서 | 프로젝트 문서 | docs | README.md | 문서 디렉토리 README |
| 문서 | 프로젝트 문서 | README.md | 프로젝트 루트 README |
| 문서 | 프로젝트 문서 | README_REFACTORING.md | 리팩토링 README 문서 |
| 문서 | 프로젝트 문서 | REFACTORING_COMPLETE.md | 리팩토링 완료 문서 |
| 문서 | 프로젝트 문서 | CLEANUP_GUIDE.md | 데이터 폴더 정리 가이드 |
| 문서 | 프로젝트 문서 | LEVEL2_DL_SUMMARY.md | Level 2 딥러닝 기능 요약 문서 |
| 문서 | 프로젝트 문서 | LEVEL3_LLM_SUMMARY.md | Level 3 LLM 기능 요약 문서 |
| 문서 | 프로젝트 문서 | ML_FEATURES_SUMMARY.md | ML 기능 요약 문서 |
| 문서 | API 문서 | api/docs | LEARNING_UNIT_SCHEMA.md | 학습 단위(LearningUnit) 공통 스키마 문서 |
| 문서 | API 문서 | api/docs | LEARNING_UNIT_USAGE.md | 학습 단위 사용 가이드 문서 |
| 문서 | API 문서 | api/docs | PDF_ONLY_PIPELINE.md | PDF 전용 파이프라인 문서 |
| 문서 | API 문서 | api/docs | PIPELINE_FLOW.md | PDF 크롭 파이프라인 전체 흐름 문서 |
| 문서 | API 문서 | api/docs/refactoring | BACKEND_REFACTORING_STRATEGY.md | 백엔드 리팩토링 전략 문서 |
| 문서 | API 문서 | api/docs/refactoring | REFACTORING_PDF_EXTRACTION.md | PDF 추출 리팩토링 문서 |
| 문서 | API 문서 | api/docs/refactoring | REFACTORING_PROGRESS.md | 리팩토링 진행 상황 문서 |
| 문서 | API 문서 | api/docs/refactoring | REFACTORING_STRATEGY.md | 리팩토링 전략 문서 |
| 문서 | API 문서 | api/docs/refactoring | REFACTORING_SUMMARY.md | 리팩토링 요약 문서 |
| 문서 | API 보관 문서 | api/docs/archived | ai_lecture_generator.py | AI 강의 생성기 (레거시) |
| 문서 | API 보관 문서 | api/docs/archived | braille_convert.py | 점자 변환 스크립트 (레거시) |
| 문서 | API 보관 문서 | api/docs/archived | image_extractor.py | 이미지 추출 스크립트 (레거시) |
| 문서 | API 보관 문서 | api/docs/archived | math_ocr.py | 수학 OCR 스크립트 (레거시) |
| 문서 | API 보관 문서 | api/docs/archived | pdf_cropper.py | PDF 크롭 스크립트 (레거시) |
| 문서 | API 보관 문서 | api/docs/archived | toc_parser.py | 목차 파서 스크립트 (레거시) |
| 문서 | API 보관 문서 | api/docs/archived | tts_reader.py | TTS 리더 스크립트 (레거시) |

---

## 🔧 기능별 모듈 설명

### 1. PDF 처리 모듈

**목적**: PDF 파일에서 텍스트, 이미지, 구조를 추출하고 과목별로 파싱

**주요 구성요소**:
- **PDF 추출 계층** (`api/app/extraction/`)
  - `base_extractor.py`: 추출기 인터페이스 정의
  - `extractors.py`: PDF 추출기 구현
  - `pdfplumber_extractor.py`: PDFPlumber 기반 텍스트 추출
  - `ocr_extractor.py`: OCR 기반 텍스트 추출
  - `image_processor.py`: PDF 이미지 처리
  - `text_normalizer.py`: 텍스트 정규화
  - `utils.py`: PDF 추출 유틸리티 함수
  - `exceptions.py`: PDF 추출 예외 정의

- **파싱 계층** (`api/app/parsing/`)
  - `document_parser.py`: 문서 파서 메인 클래스
  - `strategies/`: 과목별 파싱 전략 (literature, math1, english)
  - `block_parsers/`: 블록별 파서 (concept, example, passage, question)
  - `classifiers/`: 블록 분류기 (rule, ml)

- **교재 파이프라인** (`api/app/services/textbook_pipeline.py`)
  - 과목별 PDF 파싱 전략 통합 (문학, 수학Ⅰ, 영어)
  - 문학: 강의/본문/문제 구조 파싱
  - 수학Ⅰ: 개념/예제/유제 구조 파싱
  - 영어: 단원/지문/문제 구조 파싱

**처리 흐름**: PDF 업로드 → 추출(Extract) → 과목별 파싱(textbook_pipeline) → 후처리(Post-process) → 구조화된 JSON

---

### 2. 점자 변환 모듈

**목적**: 한글 텍스트를 점자로 변환하여 점자 디바이스에 전송

**주요 구성요소**:
- **프론트엔드** (`apps/web/src/components/braille/`, `apps/web/src/hooks/braille/`)
  - 점자 시각화 컴포넌트 (BrailleCell, BrailleGrid 등)
  - 점자 디바이스 어댑터 (BLE 통신)
  - 점자 청크 관리 (말하는 단위 분할)
  - Arduino 버튼 제어

- **하드웨어** (`arduino/braille_3cell/`)
  - Arduino 기반 점자 디스플레이 펌웨어
  - 점자 패턴 제어
  - 버튼 입력 처리

**기능**: 텍스트 입력 → 점자 변환 → 디바이스 전송 → 시각화

---

### 3. 학습 관리 모듈

**목적**: 교재, 레슨, 단원, 학습 진행 상황 관리

**주요 구성요소**:
- **백엔드** (`api/app/routers/books.py`, `lessons.py`, `units.py`, `progress.py`)
  - 교재 업로드 및 파싱 상태 관리
  - 교재 삭제 기능
  - 레슨/단원 목록 및 콘텐츠 조회
  - 학습 진행률 추적 및 업데이트
  - Unit 타입: CONCEPT_CORE, CONCEPT_FORM, CONCEPT_CONTENT, CONCEPT_SUMMARY, PASSAGE, QUESTION
  - Unit 필드: image_path, content_image_paths, ai_explanation, braille_keywords

- **프론트엔드** (`apps/web/src/pages/`)
  - MVP 3.0 Single-flow UI: Start, BookSelect, QuestionLearning, QuestionList, LearningSummary
  - 레거시 페이지: Book, Lesson, Unit, Question, Textbook, Curriculum
  - 교재 관리 UI (업로드, 목록, 파싱 상태, 삭제)
  - 레슨/단원 뷰어
  - 학습 진행 상황 표시 (진행률 계산 개선)

**데이터 모델**: Book → Lesson → Unit → Content

---

### 4. AI/ML 모듈

**목적**: AI 기반 설명 생성, 메타데이터 보강, 콘텐츠 추천

**주요 구성요소**:
- **GenAI** (`api/app/genai/`)
  - `explanation_generator.py`: AI 설명 생성기 (개념, 작품, 문제 해설)
  - `metadata_enricher.py`: 메타데이터 보강기
  - `rag_recommender.py`: RAG 기반 추천 시스템

- **ML** (`api/app/ml/`)
  - `block_classifier.py`: ML 기반 블록 분류기
  - `deduplicator.py`: 중복 제거기

- **DL** (`api/app/dl/`)
  - `layout_analyzer.py`: 딥러닝 기반 레이아웃 분석기
  - `math_recognizer.py`: 수식 인식기

- **API** (`api/app/routers/ai.py`, `literature_ai.py`)
  - AI 강의 교사 API
  - 문학 AI 설명 API

---

### 5. 음성 처리 모듈

**목적**: 음성 인식(STT), 음성 합성(TTS), 오디오-텍스트 동기화

**주요 구성요소**:
- **STT (Speech-to-Text)** (`apps/web/src/hooks/useSTT.ts`, `apps/web/src/stt/GoogleStreamingProvider.ts`)
  - Google STT 스트리밍 프로바이더
  - 실시간 음성 인식
  - 음성 명령 처리

- **TTS (Text-to-Speech)** (`apps/web/src/hooks/useTTS.ts`)
  - Web Speech API 기반 음성 합성
  - 텍스트 읽기 기능

- **음성 명령** (`apps/web/src/hooks/useVoiceCommands.ts`, `apps/web/src/services/VoiceService.ts`)
  - 음성 명령 인식 및 실행
  - 명령 패턴 매칭
  - 명령 라우팅

**기능**: 음성 입력 → STT → 명령 인식 → 액션 실행

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
  - `useArduinoButtons.ts`: Arduino 버튼 제어 훅

- **BLE 서버** (`raspberrypi/ble_server.py`)
  - Raspberry Pi에서 실행되는 BLE 서버
  - 점자 디바이스와의 중계 서버

- **하드웨어 펌웨어** (`arduino/braille_3cell/`)
  - Arduino 기반 점자 디스플레이 펌웨어
  - 점자 패턴 제어
  - 버튼 입력 처리 (이전/다음/재생-일시정지)

**기능**: 텍스트 → 점자 변환 → BLE 전송 → 디바이스 표시

---

### 7. 문제 풀이 모듈

**목적**: 문제 표시, 답안 입력, 정답 확인, 오답 분석

**주요 구성요소**:
- **백엔드** (`api/app/routers/answers.py`)
  - 답안 제출 및 정답 확인
  - 오답 패턴 분석

- **프론트엔드** (`apps/web/src/pages/QuestionLearning.tsx`, `apps/web/src/components/question/`)
  - `QuestionDisplay.tsx`: 문제 표시
  - `AnswerInput.tsx`: 답안 입력
  - `AnswerResult.tsx`: 답안 결과 표시
  - `ChoiceComparison.tsx`: 선택지 비교
  - `WrongAnswerList.tsx`: 오답 목록
  - 문제 이미지 표시 지원
  - 실제 문제 데이터 연동 (JSON 파일에서 로드)

**기능**: 문제 표시 → 답안 입력 → 정답 확인 → 오답 분석

---

### 8. UI/UX 모듈

**목적**: 사용자 인터페이스 및 사용자 경험 제공

**주요 구성요소**:
- **MVP 3.0 Single-flow UI** (`apps/web/src/pages/`)
  - Start: 시작 페이지
  - BookSelect: 교재 선택
  - QuestionLearning: 문제 학습 (전체 유닛 순서대로)
  - QuestionList: 문제 목록
  - LearningSummary: 학습 종료 (진행률 계산 개선)

- **재사용 컴포넌트** (`apps/web/src/components/`)
  - 점자 컴포넌트 (BrailleCell, BrailleGrid 등)
  - 입력 컴포넌트 (VoiceButton, MicButton 등)
  - UI 컴포넌트 (AppShellMobile - 헤더/푸터 옵션 지원)
  - 시스템 컴포넌트 (ErrorBoundary, HealthCheck 등)
  - AI 컴포넌트 (AIExplanationCard, ConceptExplanationCard 등)
  - 단원 컴포넌트 (UnitViewer - CONCEPT_SUMMARY, QUESTION 등 타입별 표시)

- **레이아웃** (`apps/web/src/components/layout/`)
  - 페이지 레이아웃 관리
  - 모바일 반응형 디자인

**특징**: 접근성 우선 (스크린 리더, 키보드 네비게이션, 점자 디바이스 연동)

---

### 9. 상태 관리 모듈

**목적**: 애플리케이션 전역 상태 관리

**주요 구성요소**:
- **Zustand 스토어** (`apps/web/src/store/`)
  - `bookStore.ts`: 교재 상태
  - `lessonStore.ts`: 레슨 상태
  - `progressStore.ts`: 진행 상황
  - `voice.ts`: 음성 상태
  - `learnStore.ts`: 학습 상태
  - `home.ts`: 홈 상태
  - `keywords.ts`: 키워드 상태
  - `examStore.ts`: 시험 상태
  - `lessonSession.ts`: 레슨 세션 상태
  - `vocabStore.ts`: 어휘 상태

**기능**: 상태 저장 → 상태 업데이트 → 컴포넌트 반영

---

### 10. 서비스 레이어 모듈

**목적**: 비즈니스 로직 및 API 통신 관리

**주요 구성요소**:
- **API 클라이언트** (`apps/web/src/services/api/`)
  - `index.ts`: Fetch 기반 HTTP 클라이언트
  - `client.ts`: API 클라이언트 설정
  - 재시도 로직 포함
  - 에러 처리

- **도메인 서비스** (`apps/web/src/services/`)
  - `books.ts`, `lessons.ts`, `units.ts`, `curriculum.ts`: 학습 관련 서비스
  - `literature.ts`: 문학 학습 서비스
  - `answers.ts`: 문제 서비스
  - `ai/index.ts`: AI 서비스
  - `voice/index.ts`: 음성 서비스

- **학습 플로우** (`apps/web/src/services/learning/`)
  - `LearningFlow.ts`: 학습 플로우 베이스 클래스
  - `TextbookLearningFlow.ts`: 교과서 학습 플로우
  - `PassageLearningFlow.ts`: 지문 학습 플로우
  - `VocabLearningFlow.ts`: 어휘 학습 플로우

- **명령 패턴** (`apps/web/src/services/commands/`)
  - `Command.ts`: 명령 인터페이스
  - `CommandInvoker.ts`: 명령 실행자
  - `ControlCommand.ts`, `LearningCommand.ts`, `NavigateCommand.ts`: 구체적 명령

- **기타 서비스**
  - `passage/PassageService.ts`: 지문 서비스
  - `question/QuestionService.ts`: 문제 서비스
  - `textbook/TextbookService.ts`: 교과서 서비스

---

### 11. 하드웨어 모듈

**목적**: 점자 디스플레이 하드웨어 제어

**주요 구성요소**:
- **Arduino 펌웨어** (`arduino/braille_3cell/`)
  - 3셀 점자 디스플레이 제어
  - 점자 패턴 표시
  - BLE 통신
  - 버튼 입력 처리 (이전/다음/재생-일시정지)

---

### 12. 커리큘럼 관리 모듈

**목적**: 관리자가 AI/ML로 커리큘럼을 자동 생성하고, 사용자가 조회/학습

**역할 분리**:
- **관리자 (백엔드/인프라)**: EBS 수능특강 PDF 수신 → **AI/ML로 자동 분석** → 커리큘럼 생성 → DB 저장
  - **AI/ML 기술**: LLM (레슨 블록 생성), LangChain (파이프라인), CNN (PDF 구조 분석)
- **사용자 (프론트엔드)**: 이미 준비된 커리큘럼 조회 → 학습 시작 → 점자/음성 출력

**참고**: AI/ML 기능은 관리자용과 사용자용으로 분리됨. 자세한 내용은 `docs/AI_ML_ROLE_SEPARATION.md` 참고.

**주요 구성요소**:

#### 관리자용 (백엔드)
- **관리자용 API** (`api/app/routers/curriculum.py`)
  - `POST /api/v1/curriculum/generate`: 커리큘럼 생성 (관리자용, HWP + PDF 분석)
  - 백그라운드 처리로 자동 생성
  - 생성 완료 후 JSON 저장 (과목별 폴더)

#### 사용자용 (프론트엔드)
- **조회 API** (`api/app/routers/curriculum.py`)
  - `GET /api/v1/curriculum`: 커리큘럼 목록 조회 (과목별, 교재별 필터링)
  - `GET /api/v1/curriculum/{curriculum_id}`: 커리큘럼 상세 조회
  - `GET /api/v1/curriculum/{curriculum_id}/lessons`: 커리큘럼의 레슨 목록 조회
  - `GET /api/v1/curriculum/{curriculum_id}/lessons/{lesson_number}`: 특정 레슨 조회

- **프론트엔드** (`apps/web/src/pages/Curriculum.tsx`)
  - 커리큘럼 목록 화면 (조회만)
  - 커리큘럼 상세 화면 (조회만)

**작업 흐름**:
1. **관리자**: EBS PDF 수신 → HWP 분석 → 커리큘럼 생성 → DB 저장
2. **사용자**: 앱 열기 → 과목 선택 → 교재 선택 → 커리큘럼 선택 → 학습 시작

---

## 📊 모듈별 통계

### 백엔드 API
- 총 파일 수: 약 80개
- 주요 모듈: 라우터(11), 서비스(1), 스키마(9), PDF 추출(8), 파싱(10+), AI/ML(7), 어셈블리(1), 유틸리티(4), 스크립트(14+)

### 프론트엔드 웹
- 총 파일 수: 약 150개
- 주요 모듈: 페이지(13), 컴포넌트(50+), 훅(24), 서비스(20+), 상태 관리(11), 타입(13)

### 하드웨어
- 총 파일 수: 6개
- 주요 모듈: Arduino 펌웨어

### 문서
- 총 파일 수: 20개 이상
- 주요 문서: 개발명세서, DATABASE_SCHEMA, ARDUINO_BUTTON_INTEGRATION, WBS, 화면명세서, 시스템 아키텍처, 메뉴 흐름도, README

---

## 📝 최신화 이력

### 2025년 1월 (최신 업데이트)
- **MVP 3.0 Single-flow UI**: Start, BookSelect, QuestionLearning, QuestionList, LearningSummary 페이지 추가
- **진행률 계산 개선**: units에서 직접 문제 수 계산하여 500% 버그 수정
- **Unit 모델 확장**: image_path, content_image_paths, ai_explanation, braille_keywords 필드 추가
- **UnitType 확장**: CONCEPT_SUMMARY 타입 추가
- **교재 삭제 기능**: BookSelect 페이지에 삭제 기능 추가
- **문제 데이터 연동**: problem JSON 파일에서 실제 문제 데이터 로드
- **이미지 표시**: 문제 이미지 표시 기능 추가
- **Arduino 버튼 통합**: 3개 버튼으로 이전/다음/재생-일시정지 제어
- **파싱 모듈 구조화**: extraction/, parsing/, genai/, ml/, dl/ 디렉토리 분리
- **어셈블리 모듈**: lecture JSON을 Unit으로 변환하는 어셈블러 추가
- **스크립트 구조화**: admin/, pipeline/, ml/, examples/, experiments/ 디렉토리 분리

### 2025년 1월 (문학 학습 기능 추가)
- **문학 학습 페이지 추가**: `LiteratureLearning.tsx` - 개념/본문/문제 순서로 학습, AI 설명 생성
- **문학 API 라우터 추가**: `literature.py` (강의 목록, 문제 목록, 이미지, 본문 콘텐츠), `literature_ai.py` (AI 설명 생성)
- **과목별 파이프라인 통합**: `textbook_pipeline.py`에 문학/수학Ⅰ/영어 파싱 전략 통합
- **국어 선택 시 문학 강의 목록 표시**: `Book.tsx`에서 국어(KOREAN) 선택 시 문학 강의 목록 표시
- **핵심 키워드 섹션 추가**: 각 강의 마지막에 핵심 키워드 3개 점자 출력 기능

### 2025년 1월 (리팩토링)
- **프론트엔드 서비스 레이어 통합**: `api-client.ts` 생성, 공통 CRUD 패턴 추출
- **유틸리티 함수 통합**: `pdfReferences.ts`, `subjectMetadata.ts` 생성, 중복 코드 제거
- **CurriculumLesson.tsx 리팩토링**: 중복 파싱 로직 제거 (200+ 줄 감소)
- **코드 가독성 향상**: 유틸리티 함수로 의도 명확화

### 2024년 12월 (프로젝트 단순화)
- **프로젝트 단순화**: 불필요한 라우터 및 서비스 삭제
- **필수 라우터만 유지**: health, subjects, books, lessons, units, progress, answers, curriculum, ai, literature, literature_ai (총 11개)
- **핵심 서비스만 유지**: 교재 파이프라인, PDF 추출, 파싱, AI/ML
- **MENU_FLOW.md에 맞춘 API 구조 정리**: 단순화된 사용자 흐름 반영
- **문서 단순화**: 필수 문서만 유지
- **삭제된 기능**: 복습 시스템, 동기화 포인트, 레슨 블록 시스템, Chrome 확장 프로그램, 테스트 파일
- **역할 분리 명확화**: 관리자가 인프라 제공 (커리큘럼 생성), 사용자는 조회/학습만 수행

---

## 🗑️ 삭제된 기능 및 페이지

다음 기능들은 프로젝트 단순화 과정에서 삭제되었습니다:

### 삭제된 페이지 (프론트엔드)
- `Passage/Passage.tsx` - 지문 학습 페이지
- `GraphTable/GraphTable.tsx` - 그래프/표 뷰어
- `Vocab/Vocab.tsx` - 어휘 학습 페이지
- `BrailleSpeed/BrailleSpeed.tsx` - 점자 속도 훈련
- `ExamMode/ExamMode.tsx` - 시험 모드
- `ExamTimer/ExamTimer.tsx` - 시험 타이머
- `Explore.tsx` - 탐색 페이지
- `LearnIndex.tsx`, `LearnStep.tsx` - 학습 인덱스/스텝
- `FreeConvert.tsx` - 자유 변환
- `Quiz.tsx` - 퀴즈 페이지
- `exam/TextbookConverter.tsx`, `exam/TextCompress.tsx`, `exam/SentenceRepeat.tsx` - 시험 관련 페이지

### 삭제된 라우터 (백엔드)
- `review.py` - 복습 시스템 (Question으로 통합)
- `syncpoints.py` - 동기화 포인트
- `lecture_scripts.py` - 강의 대본 관리
- `lesson_blocks.py` - 레슨 블록 시스템
- `content.py` - 콘텐츠 관리 (통합됨)
- `pdf.py` - PDF 관리 (books.py로 통합)

### 삭제된 서비스 (백엔드)
- `review_logic.py` - 복습 로직
- `audio_sync.py` - 오디오 동기화 (나중에 구현 예정)
- `content_auto_generator.py` - 콘텐츠 자동 생성 (통합됨)
- `curriculum_generator.py`, `curriculum_template.py`, `pdf_script_matcher.py` - 커리큘럼 관련 (통합됨)
- `subject_strategies/` 디렉토리 - `textbook_pipeline.py`로 통합

### 삭제된 모듈
- Chrome 확장 프로그램 (`apps/extension/`)
- 테스트 파일 (`api/tests/`, `apps/web/src/__tests__/`)
- E2E 테스트 (`apps/web/e2e/`)

---

*작성일: 2024년*  
*마지막 업데이트: 2025년 1월*
