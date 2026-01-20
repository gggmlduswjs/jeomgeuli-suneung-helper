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
| 백엔드 API | API 라우터 | api/app/routers | subjects.py | 과목 목록 API (KOREAN, MATH, ENGLISH) |
| 백엔드 API | API 라우터 | api/app/routers | books.py | 교재 관리 API (PDF 업로드, 목록 조회, 과목별 필터링) |
| 백엔드 API | API 라우터 | api/app/routers | lessons.py | 레슨 관리 API (레슨 목록, 상세 조회) |
| 백엔드 API | API 라우터 | api/app/routers | units.py | 학습 단위 관리 API (단원 목록, 콘텐츠 조회) |
| 백엔드 API | API 라우터 | api/app/routers | progress.py | 학습 진행 상황 API (진행률 조회, 업데이트, 오늘 학습 이어하기) |
| 백엔드 API | API 라우터 | api/app/routers | answers.py | 답안 관리 API (답안 제출, 정답 확인) |
| 백엔드 API | API 라우터 | api/app/routers | curriculum.py | 커리큘럼 관리 API (관리자용 생성, 사용자용 조회, 레슨 목록, 특정 레슨 조회) |
| 백엔드 API | API 라우터 | api/app/routers | ai.py | AI 강의 교사 API (레슨 설명 생성, 문제 해설 생성) |
| 백엔드 API | API 라우터 | api/app/routers | literature.py | 문학 학습 API (강의 목록, 문제 목록, 이미지, 본문 콘텐츠 조회) |
| 백엔드 API | API 라우터 | api/app/routers | literature_ai.py | 문학 AI 설명 API (개념 설명, 작품 설명, 문제 해설 생성) |
| 백엔드 API | API 라우터 | api/app/routers | __init__.py | 라우터 패키지 초기화 파일 |

### 1.3 데이터 스키마

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 백엔드 API | 데이터 스키마 | api/app/schemas | answer.py | 답안 관련 Pydantic 스키마 정의 |
| 백엔드 API | 데이터 스키마 | api/app/schemas | book.py | 교재 관련 Pydantic 스키마 정의 |
| 백엔드 API | 데이터 스키마 | api/app/schemas | lesson.py | 레슨 관련 Pydantic 스키마 정의 |
| 백엔드 API | 데이터 스키마 | api/app/schemas | progress.py | 진행 상황 관련 Pydantic 스키마 정의 |
| 백엔드 API | 데이터 스키마 | api/app/schemas | unit.py | 단원 관련 Pydantic 스키마 정의 |
| 백엔드 API | 데이터 스키마 | api/app/schemas | curriculum.py | 커리큘럼 관련 Pydantic 스키마 정의 |
| 백엔드 API | 데이터 스키마 | api/app/schemas | review.py | 복습 관련 Pydantic 스키마 정의 (라우터 삭제됨, 스키마만 유지) |
| 백엔드 API | 데이터 스키마 | api/app/schemas | syncpoint.py | 동기화 포인트 관련 Pydantic 스키마 정의 (라우터 삭제됨, 스키마만 유지) |
| 백엔드 API | 데이터 스키마 | api/app/schemas | __init__.py | 스키마 패키지 초기화 파일 |

### 1.4 핵심 서비스

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 백엔드 API | 핵심 서비스 | api/app/services | braille_convert.py | 한글 텍스트를 점자로 변환하는 규칙 기반 변환 서비스 |
| 백엔드 API | 핵심 서비스 | api/app/services | ai_lecture_generator.py | AI 강의 교사 서비스 (레슨 설명, 문제 해설 생성) |
| 백엔드 API | 핵심 서비스 | api/app/services | textbook_pipeline.py | 교재 파이프라인 서비스 (과목별 PDF 파싱: 문학, 수학Ⅰ, 영어) |
| 백엔드 API | 핵심 서비스 | api/app/services | data_file_handler.py | 데이터 파일 핸들러 (JSON 파일 읽기/쓰기) |
| 백엔드 API | 핵심 서비스 | api/app/services | tts_reader.py | TTS 읽기 서비스 |
| 백엔드 API | 핵심 서비스 | api/app/services | toc_parser.py | 목차 파서 서비스 |
| 백엔드 API | 핵심 서비스 | api/app/services | text_extractors.py | 텍스트 추출기 서비스 |
| 백엔드 API | 핵심 서비스 | api/app/services | pdf_region_capturer.py | PDF 영역 캡처 서비스 |
| 백엔드 API | 핵심 서비스 | api/app/services | pdf_region_detector.py | PDF 영역 감지 서비스 |
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
| 백엔드 API | PDF 추출 모듈 | api/app/services/pdf_extract | pdf_cropper.py | PDF 영역 자르기 서비스 |
| 백엔드 API | PDF 추출 모듈 | api/app/services/pdf_extract | utils.py | PDF 추출 유틸리티 함수 |
| 백엔드 API | PDF 추출 모듈 | api/app/services/pdf_extract | exceptions.py | PDF 추출 예외 정의 |
| 백엔드 API | PDF 추출 모듈 | api/app/services/pdf_extract | __init__.py | PDF 추출 패키지 초기화 파일 |

### 1.6 과목별 파이프라인 전략

**참고**: 과목별 파싱 전략은 `textbook_pipeline.py`에 통합되어 있습니다. 각 과목(문학, 수학Ⅰ, 영어)별로 다른 파싱 로직을 사용합니다.

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 백엔드 API | 과목별 파이프라인 | api/app/services | textbook_pipeline.py | 교재 파이프라인 (과목별 PDF 파싱 전략 통합) |
| | | | | - 문학: 강의/본문/문제 구조 파싱 |
| | | | | - 수학Ⅰ: 개념/예제/유제 구조 파싱 |
| | | | | - 영어: 단원/지문/문제 구조 파싱 |

### 1.8 유틸리티 및 기타

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 백엔드 API | 유틸리티 | api/app/utils | text_utils.py | 텍스트 처리 유틸리티 함수 |
| 백엔드 API | 유틸리티 | api/app/utils | __init__.py | 유틸리티 패키지 초기화 파일 |

### 1.9 스크립트 및 설정

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
| 프론트엔드 웹 | 주요 페이지 | apps/web/src/pages | Home.tsx | 홈 페이지 (과목 선택, 학습 이어하기) |
| 프론트엔드 웹 | 주요 페이지 | apps/web/src/pages | Main.tsx | 메인 페이지 (문학 학습 바로가기, 과목 선택) |
| 프론트엔드 웹 | 주요 페이지 | apps/web/src/pages | NotFound.tsx | 404 에러 페이지 |
| 프론트엔드 웹 | 주요 페이지 | apps/web/src/pages | Book.tsx | 교재 목록 페이지 (과목별 필터링, 국어 선택 시 문학 강의 목록 표시) |
| 프론트엔드 웹 | 주요 페이지 | apps/web/src/pages | Lesson.tsx | 레슨 페이지 (학습 화면) |
| 프론트엔드 웹 | 주요 페이지 | apps/web/src/pages | Unit.tsx | 단원 페이지 |
| 프론트엔드 웹 | 주요 페이지 | apps/web/src/pages | Question.tsx | 문제 풀이 페이지 |
| 프론트엔드 웹 | 주요 페이지 | apps/web/src/pages | Textbook.tsx | 교재 관리 페이지 |
| 프론트엔드 웹 | 주요 페이지 | apps/web/src/pages | LiteratureLearning.tsx | 문학 학습 페이지 (강의 목록, 개념/본문/문제 학습, AI 설명) |
| 프론트엔드 웹 | 주요 페이지 | apps/web/src/pages/Curriculum | Curriculum.tsx | 커리큘럼 목록 페이지 (조회만) |
| 프론트엔드 웹 | 주요 페이지 | apps/web/src/pages/Curriculum | CurriculumDetail.tsx | 커리큘럼 상세 페이지 (조회만) |
| 프론트엔드 웹 | 주요 페이지 | apps/web/src/pages/Curriculum | CurriculumLesson.tsx | 커리큘럼 레슨 페이지 |
| 프론트엔드 웹 | 주요 페이지 | apps/web/src/pages/Learning | LearningScreen.tsx | 학습 화면 메인 컴포넌트 |

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
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Textbook | TextbookList.tsx | 교과서 목록 컴포넌트 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Textbook | PDFUpload.tsx | PDF 업로드 컴포넌트 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Textbook | UnitList.tsx | 단원 목록 컴포넌트 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Textbook | UnitContent.tsx | 단원 콘텐츠 표시 컴포넌트 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Textbook | HWPUpload.tsx | HWP 업로드 컴포넌트 |
| 프론트엔드 웹 | 페이지 컴포넌트 | apps/web/src/pages/Textbook | PDFStructuredViewer.tsx | PDF 구조화 뷰어 컴포넌트 |
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
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/unit | UnitViewer.tsx | 단원 뷰어 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/unit | ConceptViewer.tsx | 개념 뷰어 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/unit | WorkViewer.tsx | 작품 뷰어 컴포넌트 |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/pdf | QuestionViewer.tsx | 문제 뷰어 컴포넌트 (PDF 구조화) |
| 프론트엔드 웹 | 컴포넌트 | apps/web/src/components/curriculum | BlockTimestampList.tsx | 블록 타임스탬프 리스트 컴포넌트 |
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
| 프론트엔드 웹 | 훅 | apps/web/src/hooks | useCurriculum.ts | 커리큘럼 조회 훅 (조회만, 생성은 관리자가 백엔드에서 처리) |
#### 2.5.2 API 훅

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 프론트엔드 웹 | API 훅 | apps/web/src/hooks/api | useAnswers.ts | 답안 API 훅 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks/api | useBooks.ts | 교재 API 훅 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks/api | useContinue.ts | 학습 이어하기 API 훅 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks/api | useLessons.ts | 레슨 API 훅 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks/api | useProgress.ts | 진행 상황 API 훅 |
| 프론트엔드 웹 | 훅 | apps/web/src/hooks/api | useUnits.ts | 단원 API 훅 |
| 프론트엔드 웹 | API 훅 | apps/web/src/hooks/api | useCurriculum.ts | 커리큘럼 API 훅 |
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
| 프론트엔드 웹 | 서비스 | apps/web/src/services | units.ts | 단원 서비스 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services | curriculum.ts | 커리큘럼 서비스 |
| 프론트엔드 웹 | 서비스 | apps/web/src/services | literature.ts | 문학 학습 서비스 (강의 목록, 문제 목록, 이미지, 본문 콘텐츠) |
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
| 프론트엔드 웹 | 상태 관리 | apps/web/src/store | voice.ts | 음성 상태 관리 |
| 프론트엔드 웹 | 상태 관리 | apps/web/src/store | curriculumStore.ts | 커리큘럼 상태 관리 |
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
| 프론트엔드 웹 | 타입 정의 | apps/web/src/types | unit.ts | 단원 타입 정의 |
| 프론트엔드 웹 | 타입 정의 | apps/web/src/types | voice.ts | 음성 타입 정의 |
| 프론트엔드 웹 | 타입 정의 | apps/web/src/types | curriculum.ts | 커리큘럼 타입 정의 |
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
| 프론트엔드 웹 | 설정 | apps/web | index.html | HTML 진입점 |
| 프론트엔드 웹 | 설정 | apps/web | vite.config.ts | Vite 빌드 설정 |
| 프론트엔드 웹 | 설정 | apps/web | tailwind.config.js | Tailwind CSS 설정 |
| 프론트엔드 웹 | 설정 | apps/web | postcss.config.js | PostCSS 설정 |
| 프론트엔드 웹 | 스크립트 | apps/web/scripts | gen-icons.mjs | 아이콘 생성 스크립트 |
---

## 3. 하드웨어 모듈

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
| 데이터 | 추출된 데이터 | data/extracted | *.txt | 추출된 PDF 텍스트 파일들 |
| 데이터 | 강의 대본 | data/lecture_scripts | *.hwp, *.hwpx | 한글 파일 강의 대본들 |
| 데이터 | PDF 파일 | data/pdfs | *.pdf | 수능특강 PDF 파일들 |
| 데이터 | 업로드 파일 | data/uploads | *.pdf | 업로드된 PDF 파일들 |

### 5.2 문서

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| 문서 | 프로젝트 문서 | docs | DEVELOPMENT_SPECIFICATION.md | 개발명세서 |
| 문서 | 프로젝트 문서 | docs | WBS.md | 작업 분해 구조 문서 |
| 문서 | 프로젝트 문서 | docs | SCREEN_SPECIFICATION.md | 화면 정의서 문서 |
| 문서 | 프로젝트 문서 | docs | SYSTEM_ARCHITECTURE.md | 시스템 아키텍처 문서 |
| 문서 | 프로젝트 문서 | docs | MENU_FLOW.md | 메뉴 흐름도 문서 |
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
  - `pdf_cropper.py`: PDF 영역 자르기

- **교재 파이프라인** (`api/app/services/textbook_pipeline.py`)
  - 과목별 PDF 파싱 전략 통합 (문학, 수학Ⅰ, 영어)
  - 문학: 강의/본문/문제 구조 파싱
  - 수학Ⅰ: 개념/예제/유제 구조 파싱
  - 영어: 단원/지문/문제 구조 파싱

- **기타 PDF 관련 서비스**
  - `pdf_region_capturer.py`: PDF 영역 캡처
  - `pdf_region_detector.py`: PDF 영역 감지
  - `text_extractors.py`: 텍스트 추출기
  - `toc_parser.py`: 목차 파서

**처리 흐름**: PDF 업로드 → 추출(Extract) → 과목별 파싱(textbook_pipeline) → 후처리(Post-process) → 구조화된 JSON

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

**참고**: ML 기반 오디오 동기화는 나중에 구현 예정

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

### 7. 문제 풀이 모듈

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

**기능**: 문제 표시 → 답안 입력 → 정답 확인 → 오답 분석

---

### 8. UI/UX 모듈

**목적**: 사용자 인터페이스 및 사용자 경험 제공

**주요 구성요소**:
- **페이지 컴포넌트** (`apps/web/src/pages/`)
  - 홈, 학습, 문제, 교재 관리 등 주요 페이지
  - 문학 학습, 커리큘럼 등 과목별 학습 페이지

- **재사용 컴포넌트** (`apps/web/src/components/`)
  - 점자 컴포넌트 (BrailleCell, BrailleGrid 등)
  - 입력 컴포넌트 (VoiceButton, MicButton 등)
  - UI 컴포넌트 (Card, BottomBar 등)
  - 시스템 컴포넌트 (ErrorBoundary, HealthCheck 등)
  - AI 컴포넌트 (AIExplanationCard, AIAnswerDisplay 등)

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
  - `curriculumStore.ts`: 커리큘럼 상태
  - `learnStore.ts`: 학습 상태
  - `home.ts`: 홈 상태
  - `keywords.ts`: 키워드 상태
  - `examStore.ts`: 시험 상태

**기능**: 상태 저장 → 상태 업데이트 → 컴포넌트 반영

---

### 10. 서비스 레이어 모듈

**목적**: 비즈니스 로직 및 API 통신 관리

**주요 구성요소**:
- **API 클라이언트** (`apps/web/src/services/api.ts`)
  - Fetch 기반 HTTP 클라이언트
  - 재시도 로직 포함
  - 에러 처리

- **도메인 서비스** (`apps/web/src/services/`)
  - `books.ts`, `lessons.ts`, `units.ts`, `curriculum.ts`: 학습 관련 서비스
  - `literature.ts`: 문학 학습 서비스
  - `answers.ts`: 문제 서비스
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

- **테스트** (`arduino/braille_3cell_test/`)
  - 통합 테스트
  - 점자 패턴 테스트

---

### 14. 커리큘럼 관리 모듈

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
  - **참고**: HWP 처리, 강의 대본 파싱 등은 `curriculum.py` 내부에서 처리되거나 stub 함수로 처리됨

#### 사용자용 (프론트엔드)
- **조회 API** (`api/app/routers/curriculum.py`)
  - `GET /api/v1/curriculum`: 커리큘럼 목록 조회 (과목별, 교재별 필터링)
  - `GET /api/v1/curriculum/{curriculum_id}`: 커리큘럼 상세 조회
  - `GET /api/v1/curriculum/{curriculum_id}/lessons`: 커리큘럼의 레슨 목록 조회
  - `GET /api/v1/curriculum/{curriculum_id}/lessons/{lesson_number}`: 특정 레슨 조회

- **프론트엔드** (`apps/web/src/pages/Curriculum/`)
  - 커리큘럼 목록 화면 (조회만)
  - 커리큘럼 상세 화면 (조회만)
  - 커리큘럼 레슨 화면

**작업 흐름**:
1. **관리자**: EBS PDF 수신 → HWP 분석 → 커리큘럼 생성 → DB 저장
2. **사용자**: 앱 열기 → 과목 선택 → 교재 선택 → 커리큘럼 선택 → 학습 시작

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
- 총 파일 수: 약 60개 (단순화 후)
- 주요 모듈: 라우터(11), 서비스(10+), 스키마(9), PDF 모듈(10), 데이터 핸들러

### 프론트엔드 웹
- 총 파일 수: 약 130개 (단순화 후)
- 주요 모듈: 페이지(13), 컴포넌트(35+), 훅(28), 서비스(15+), 상태 관리(10)

### 하드웨어
- 총 파일 수: 8개
- 주요 모듈: Arduino 펌웨어, 테스트 스케치

### 문서
- 총 파일 수: 6개 (단순화 후)
- 주요 문서: 개발명세서, WBS, 화면명세서, 시스템 아키텍처, 메뉴 흐름도, README

---

## 📝 최신화 이력

### 2024년 12월 (최신)
- **프로젝트 단순화**: 불필요한 라우터 및 서비스 삭제
- **필수 라우터만 유지**: health, subjects, books, lessons, units, progress, answers, curriculum, ai (총 9개)
- **핵심 서비스만 유지**: 커리큘럼 생성, HWP 추출, 강의 대본 파서, 점자 변환, PDF-강의대본 매칭, AI 강의 교사
- **MENU_FLOW.md에 맞춘 API 구조 정리**: 단순화된 사용자 흐름 반영
- **문서 단순화**: 필수 문서만 유지 (개발명세서, WBS, 화면명세서, 시스템 아키텍처, 메뉴 흐름도, README)
- **삭제된 기능**: 복습 시스템, 동기화 포인트, 레슨 블록 시스템, AI/ML 고급 기능, Chrome 확장 프로그램, 테스트 파일, 사용자용 커리큘럼 생성 UI (나중에 구현 예정)
- **역할 분리 명확화**: 관리자가 인프라 제공 (커리큘럼 생성), 사용자는 조회/학습만 수행

### 2025년 1월 (리팩토링)
- **프론트엔드 서비스 레이어 통합**: `api-client.ts` 생성, 공통 CRUD 패턴 추출
- **유틸리티 함수 통합**: `pdfReferences.ts`, `subjectMetadata.ts` 생성, 중복 코드 제거
- **CurriculumLesson.tsx 리팩토링**: 중복 파싱 로직 제거 (200+ 줄 감소)
- **코드 가독성 향상**: 유틸리티 함수로 의도 명확화

### 2025년 1월 (문학 학습 기능 추가)
- **문학 학습 페이지 추가**: `LiteratureLearning.tsx` - 개념/본문/문제 순서로 학습, AI 설명 생성
- **문학 API 라우터 추가**: `literature.py` (강의 목록, 문제 목록, 이미지, 본문 콘텐츠), `literature_ai.py` (AI 설명 생성)
- **과목별 파이프라인 통합**: `textbook_pipeline.py`에 문학/수학Ⅰ/영어 파싱 전략 통합
- **국어 선택 시 문학 강의 목록 표시**: `Book.tsx`에서 국어(KOREAN) 선택 시 문학 강의 목록 표시
- **핵심 키워드 섹션 추가**: 각 강의 마지막에 핵심 키워드 3개 점자 출력 기능

---

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
