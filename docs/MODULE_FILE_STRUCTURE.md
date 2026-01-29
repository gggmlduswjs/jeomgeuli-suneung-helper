# 점그리 수능 도우미 모듈별 파일 구조

**작성일**: 2026년 1월 26일  
**버전**: 2.1.0 (리팩토링 반영)  
**작성자**: 개발팀  
**최종 수정**: 2026년 1월 26일 (라우터/서비스 레이어 분리 반영)

---

## 목차

1. [개요](#1-개요)
2. [Backend 모듈 파일 구조](#2-backend-모듈-파일-구조)
3. [Frontend 모듈 파일 구조](#3-frontend-모듈-파일-구조)

---

## 1. 개요

본 문서는 점그리 수능 도우미 프로젝트의 모듈별 파일 구조를 정리한 문서입니다. 각 모듈의 분류, 경로, 파일명, 설명을 표 형태로 제공합니다.

---

## 2. Backend 모듈 파일 구조

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| Common | config | app.core | config.py | 애플리케이션 설정 관리 (환경 변수, 데이터베이스 설정 등) |
| Common | exception | app.core | exceptions.py | 커스텀 예외 클래스 정의 |
| Common | schema | app.schemas | book.py | 교재 관련 Pydantic 스키마 |
| Common | schema | app.schemas | curriculum.py | 커리큘럼 관련 Pydantic 스키마 |
| Common | schema | app.schemas | lesson.py | 강의 관련 Pydantic 스키마 |
| Common | schema | app.schemas | unit.py | 단원 관련 Pydantic 스키마 |
| Common | schema | app.schemas | progress.py | 학습 진도 관련 Pydantic 스키마 |
| Common | schema | app.schemas | answer.py | 답안 관련 Pydantic 스키마 |
| Common | utils | app.utils | ai_utils.py | AI API 클라이언트 관리 (OpenAI, Anthropic) |
| Common | utils | app.utils | env_loader.py | 환경 변수 로드 유틸리티 |
| Common | utils | app.utils | id_generator.py | ID 생성 유틸리티 |
| Common | utils | app.utils | pdf_tools.py | PDF 처리 유틸리티 |
| Common | utils | app.utils | text_utils.py | 텍스트 처리 유틸리티 |
| Common | utils | app.utils | data_file_handler.py | 데이터 파일 핸들러 |
| Books | router | app.routers | books.py | 교재 관리 API (업로드, 목록 조회, 파싱 상태 등) |
| Books | service | app.services | book_service.py | 교재 처리 서비스 (PDF 파이프라인 실행, 백그라운드 작업) |
| Books | service | app.services | book_conversion.py | 교재 데이터 변환 서비스 (LearningUnit → Unit 변환) |
| AI | router | app.routers | ai.py | AI 질의응답 API |
| AI | infrastructure | app.infrastructure.ai.genai | structure_parser.py | PDF 구조 분석 AI 파서 |
| AI | infrastructure | app.infrastructure.ai.genai | structure_analyzer.py | PDF 구조 분석기 |
| AI | infrastructure | app.infrastructure.ai.genai | explanation_generator.py | AI 설명 생성기 |
| AI | infrastructure | app.infrastructure.ai.genai | metadata_enricher.py | 메타데이터 보강기 |
| AI | infrastructure | app.infrastructure.ai.genai | rag_recommender.py | RAG 기반 추천 시스템 |
| Braille | router | app.routers | braille.py | 점자 변환 API |
| Braille | service | app.services | korean_braille.py | 한글 점자 변환 서비스 (표준 한글점자규정) |
| Literature | router | app.routers | literature.py | 문학 교재 데이터 API (강의 목록, 상세, 문제 등) |
| English | router | app.routers | english.py | 영어 교재 데이터 API (강의 목록, 상세, 문제 등) |
| Math1 | router | app.routers | math1.py | 수학1 교재 데이터 API (강의 목록, 상세, 문제 등) |
| Templates | router | app.routers | templates.py | 템플릿 관리 API (생성, 조회, 편집, 삭제 등) |
| Templates | service | app.services | template_service.py | 템플릿 관리 서비스 (템플릿 생성, 수정, 삭제 등의 비즈니스 로직) |
| Units | router | app.routers | units.py | 단원 관리 API |
| Lessons | router | app.routers | lessons.py | 강의 관리 API |
| Curriculum | router | app.routers | curriculum.py | 커리큘럼 관리 API |
| Curriculum | service | app.services | curriculum_service.py | 커리큘럼 생성 서비스 (파이프라인 결과를 커리큘럼으로 변환) |
| PDF | infrastructure | app.infrastructure.pdf | pipeline.py | PDF 파싱 파이프라인 |
| PDF | infrastructure | app.infrastructure.pdf.full_parsing | pipeline.py | 전체 파싱 파이프라인 |
| PDF | infrastructure | app.infrastructure.pdf.full_parsing.parsers | literature.py | 문학 교재 파서 |
| PDF | infrastructure | app.infrastructure.pdf.full_parsing.parsers | english.py | 영어 교재 파서 |
| PDF | infrastructure | app.infrastructure.pdf.full_parsing.parsers | math1.py | 수학1 교재 파서 |
| PDF | infrastructure | app.infrastructure.pdf.full_parsing.parsers | template.py | 템플릿 기반 파서 |
| PDF | infrastructure | app.infrastructure.pdf.full_parsing.parsers | ai_parser.py | AI 기반 파서 |
| PDF | infrastructure | app.infrastructure.pdf.full_parsing.parsers | hybrid_router.py | 하이브리드 파싱 라우터 |
| PDF | infrastructure | app.infrastructure.pdf.full_parsing.parsers | section_extractor.py | 섹션 추출기 |
| PDF | infrastructure | app.infrastructure.pdf.full_parsing.parsers | template_manager.py | 템플릿 관리자 |
| PDF | infrastructure | app.infrastructure.pdf.full_parsing.parsers | pattern_matching.py | 패턴 매칭 유틸리티 |
| PDF | infrastructure | app.infrastructure.pdf.full_parsing.parsers | text_preprocessor.py | 텍스트 전처리기 |
| PDF | infrastructure | app.infrastructure.pdf.full_parsing.parsers | text_block_classifier.py | 텍스트 블록 분류기 |
| PDF | infrastructure | app.infrastructure.pdf.full_parsing.parsers | region_classifier.py | 영역 분류기 |
| PDF | infrastructure | app.infrastructure.pdf.full_parsing.parsers | font_classifier.py | 폰트 분류기 |
| PDF | infrastructure | app.infrastructure.pdf.full_parsing.parsers | layout_validator.py | 레이아웃 검증기 |
| PDF | infrastructure | app.infrastructure.pdf.full_parsing.parsers | lecture_title_validator.py | 강의 제목 검증기 |
| PDF | infrastructure | app.infrastructure.pdf.full_parsing.parsers | lecture_boundary_validator.py | 강의 경계 검증기 |
| PDF | infrastructure | app.infrastructure.pdf.full_parsing.parsers | section_spacing_validator.py | 섹션 간격 검증기 |
| PDF | infrastructure | app.infrastructure.pdf.full_parsing.parsers | problem_pattern_matcher.py | 문제 패턴 매칭기 |
| PDF | infrastructure | app.infrastructure.pdf.full_parsing.parsers | rule_generator.py | 규칙 생성기 |
| PDF | infrastructure | app.infrastructure.pdf.full_parsing.parsers | base.py | 파서 베이스 클래스 |
| PDF | infrastructure | app.infrastructure.pdf.full_parsing.parsers | config_manager.py | 설정 관리자 |
| PDF | infrastructure | app.infrastructure.pdf.full_parsing.parsers | extraction_config.py | 추출 설정 |
| PDF | infrastructure | app.infrastructure.pdf.full_parsing.parsers | extraction_strategies.py | 추출 전략 |
| PDF | infrastructure | app.infrastructure.pdf.full_parsing.parsers | extraction_types.py | 추출 타입 정의 |
| PDF | infrastructure | app.infrastructure.pdf.full_parsing.parsers | patterns.py | 패턴 정의 |
| PDF | infrastructure | app.infrastructure.pdf.full_parsing.parsers | unified_parser.py | 통합 파서 |
| PDF | infrastructure | app.infrastructure.pdf.full_parsing.postprocessors | classifier.py | 콘텐츠 분류 후처리기 |
| PDF | infrastructure | app.infrastructure.pdf.full_parsing.postprocessors | deduplicator.py | 중복 제거 후처리기 |
| PDF | infrastructure | app.infrastructure.pdf.full_parsing | image_saver.py | 이미지 저장 유틸리티 |
| PDF | infrastructure | app.infrastructure.pdf.full_parsing | result_saver.py | 파싱 결과 저장 유틸리티 |
| PDF | infrastructure | app.infrastructure.pdf.full_parsing | lecture_contents_extractor.py | 강의 콘텐츠 추출기 |
| PDF | infrastructure | app.infrastructure.pdf.full_parsing | page_range_calculator.py | 페이지 범위 계산기 |
| PDF | infrastructure | app.infrastructure.pdf.full_parsing | extractor_factory.py | 추출기 팩토리 |
| PDF | infrastructure | app.infrastructure.pdf | constants.py | PDF 처리 상수 |
| PDF | infrastructure | app.infrastructure.pdf | exceptions.py | PDF 처리 예외 |
| PDF | infrastructure | app.infrastructure.pdf | types.py | PDF 처리 타입 정의 |
| PDF | infrastructure | app.infrastructure.pdf | image_cache.py | 이미지 캐시 |
| PDF | infrastructure | app.infrastructure.pdf | image_saver.py | 이미지 저장 유틸리티 |
| PDF | infrastructure | app.infrastructure.pdf | logging_config.py | 로깅 설정 |
| Database | infrastructure | app.infrastructure.database | models.py | SQLAlchemy 데이터 모델 정의 |
| Database | infrastructure | app.infrastructure.database | session.py | 데이터베이스 세션 관리 |
| Progress | router | app.api.v1.progress | routes.py | 학습 진도 API |
| Progress | service | app.services | progress_tracker.py | 학습 진도 추적 서비스 |
| Answers | router | app.api.v1.answers | routes.py | 답안 API |
| Health | router | app.api.v1.health | routes.py | 헬스 체크 API |
| Subjects | router | app.api.v1.subjects | routes.py | 과목 관리 API |

---

## 3. Frontend 모듈 파일 구조

| 모듈 | 분류 | 경로 | 파일이름 | 설명 |
|------|------|------|----------|------|
| Common | config | src.config | brailleDisplay.ts | 점자 디스플레이 설정 |
| Common | constants | src.constants | index.ts | 공통 상수 정의 |
| Common | types | src.types | api.ts | API 타입 정의 |
| Common | types | src.types | book.ts | 교재 타입 정의 |
| Common | types | src.types | unit.ts | 단원 타입 정의 |
| Common | types | src.types | lesson.ts | 강의 타입 정의 |
| Common | types | src.types | curriculum.ts | 커리큘럼 타입 정의 |
| Common | types | src.types | progress.ts | 학습 진도 타입 정의 |
| Common | types | src.types | answer.ts | 답안 타입 정의 |
| Common | types | src.types | voice.ts | 음성 인터페이스 타입 정의 |
| Common | types | src.types | errors.ts | 에러 타입 정의 |
| Common | types | src.types | bluetooth.d.ts | 블루투스 타입 정의 |
| Common | types | src.types | global.d.ts | 전역 타입 정의 |
| Common | types | src.types | string-similarity.d.ts | 문자열 유사도 타입 정의 |
| Common | utils | src.utils | logger.ts | 로깅 유틸리티 |
| Common | utils | src.utils | unitHelpers.ts | 단원 관련 헬퍼 함수 |
| Common | utils | src.utils | contentExtractor.ts | 콘텐츠 추출 유틸리티 |
| Common | utils | src.utils | literatureUnitConverter.ts | 문학 단원 변환 유틸리티 |
| Common | utils | src.utils | problemParser.ts | 문제 파싱 유틸리티 |
| Common | utils | src.utils.text | metadata.ts | 텍스트 메타데이터 유틸리티 |
| Common | utils | src.utils.text | sectionMatcher.ts | 섹션 매칭 유틸리티 |
| Common | context | src.contexts | KeyboardContext.tsx | 키보드 단축키 컨텍스트 |
| Common | store | src.store | bookStore.ts | 교재 및 강의 목록 상태 관리 |
| Common | store | src.store | progressStore.ts | 학습 진도 상태 관리 |
| Common | store | src.store | lessonStore.ts | 현재 학습 중인 강의 상태 관리 |
| Common | store | src.store | learnStore.ts | 학습 상태 관리 |
| Common | store | src.store | literatureProgressStore.ts | 문학 학습 진도 상태 관리 |
| Common | store | src.store | lastLectureStore.ts | 마지막 학습 강의 상태 관리 |
| Common | store | src.store | voice.ts | 음성 인터페이스 상태 관리 |
| Common | styles | src.styles | tokens.css | 디자인 토큰 (컬러, 간격 등) |
| Common | styles | src.styles | animations.css | 애니메이션 스타일 |
| Common | styles | src.styles | util.css | 유틸리티 CSS 클래스 |
| App | router | src.app | routes.tsx | 라우트 정의 |
| App | component | src.app | App.tsx | 메인 앱 컴포넌트 |
| Start | page | src.pages | Start.tsx | 시작 화면 (이어서 학습하기, 새로 시작하기) |
| BookSelect | page | src.pages | BookSelect.tsx | 교재 선택 페이지 |
| BookSelect | component | src.components.bookselect | BookListItem.tsx | 교재 목록 아이템 컴포넌트 |
| BookLectures | page | src.pages | BookLectures.tsx | 강의 목록 페이지 |
| Book | component | src.components.book | BookInfo.tsx | 교재 정보 컴포넌트 |
| Book | component | src.components.book | LessonList.tsx | 강의 목록 컴포넌트 |
| UnitSwipe | page | src.pages | UnitSwipe.tsx | 단원 학습 페이지 (카드 스와이프) |
| Unit | page | src.pages | Unit.tsx | 단원 학습 페이지 (레거시) |
| Unit | component | src.components.unit | UnitViewer.tsx | 단원 뷰어 컴포넌트 |
| Unit | component | src.components.unit | UnitCardSwiper.tsx | 단원 카드 스와이퍼 컴포넌트 |
| Unit | component | src.components.unit | UnitHeader.tsx | 단원 헤더 컴포넌트 |
| Unit | component | src.components.unit | UnitImage.tsx | 단원 이미지 컴포넌트 |
| Unit | component | src.components.unit | ConceptViewer.tsx | 개념 뷰어 컴포넌트 |
| Unit | component | src.components.unit | WorkViewer.tsx | 작품 뷰어 컴포넌트 |
| Unit | component | src.components.unit | AIExplanationCard.tsx | AI 설명 카드 컴포넌트 |
| Unit | component | src.components.unit | BrailleStatusPanel.tsx | 점자 상태 패널 컴포넌트 |
| Unit | component | src.components.unit | UnitListSidebar.tsx | 단원 목록 사이드바 컴포넌트 |
| Unit | component | src.components.unit | constants.ts | 단원 관련 상수 |
| Unit | hook | src.hooks | useUnitData.ts | 단원 데이터 관리 Hook |
| Unit | hook | src.hooks | useUnitNavigation.ts | 단원 네비게이션 Hook |
| Unit | hook | src.hooks | useUnitBraille.ts | 단원 점자 변환 Hook |
| Unit | hook | src.hooks | useUnitAI.ts | 단원 AI 질의응답 Hook |
| Unit | hook | src.hooks | useUnitAIExplanation.ts | 단원 AI 설명 Hook |
| Literature | page | src.pages | LiteratureLectures.tsx | 문학 강의 목록 페이지 |
| Literature | page | src.pages | LiteratureLectureDetail.tsx | 문학 강의 상세 페이지 |
| Literature | hook | src.hooks | useLiteratureUnitData.ts | 문학 단원 데이터 Hook |
| Literature | service | src.services | literature.ts | 문학 교재 API 서비스 |
| English | page | src.pages | EnglishLectures.tsx | 영어 강의 목록 페이지 |
| English | page | src.pages | EnglishLectureDetail.tsx | 영어 강의 상세 페이지 |
| English | hook | src.hooks | useEnglishUnitData.ts | 영어 단원 데이터 Hook |
| English | service | src.services | english.ts | 영어 교재 API 서비스 |
| Math1 | page | src.pages | Math1Lectures.tsx | 수학1 강의 목록 페이지 |
| Math1 | page | src.pages | Math1LectureDetail.tsx | 수학1 강의 상세 페이지 |
| Math1 | service | src.services | math1.ts | 수학1 교재 API 서비스 |
| Admin | page | src.pages | Admin.tsx | 관리자 페이지 |
| Admin | component | src.components.admin | TOCTemplateWizard.tsx | 목차 템플릿 생성 마법사 |
| Admin | component | src.components.admin | TemplateManager.tsx | 템플릿 관리 컴포넌트 |
| Admin | component | src.components.admin | TemplateEditor.tsx | 템플릿 편집 컴포넌트 |
| Admin | component | src.components.admin | TemplateTestPanel.tsx | 템플릿 테스트 패널 |
| Admin | component | src.components.admin | TemplateAdvancedConfig.tsx | 템플릿 고급 설정 컴포넌트 |
| Admin | component | src.components.admin | TemplatePatternEditor.tsx | 템플릿 패턴 편집 컴포넌트 |
| Admin | component | src.components.admin | PDFBboxMarker.tsx | PDF 바운딩 박스 마커 컴포넌트 |
| Admin | component | src.components.textbook | BookUploadWithTemplate.tsx | 템플릿 기반 교재 업로드 |
| Admin | component | src.components.textbook | BookUpload.tsx | 교재 업로드 컴포넌트 |
| Admin | component | src.components.textbook | SimpleBookUpload.tsx | 간단한 교재 업로드 컴포넌트 |
| Admin | component | src.components.textbook | PDFUpload.tsx | PDF 업로드 컴포넌트 |
| Admin | component | src.components.textbook.steps | FileUploadStep.tsx | 파일 업로드 단계 컴포넌트 |
| Admin | component | src.components.textbook.steps | TemplateSelectStep.tsx | 템플릿 선택 단계 컴포넌트 |
| Admin | component | src.components.textbook.steps | TOCInputStep.tsx | 목차 입력 단계 컴포넌트 |
| Admin | component | src.components.textbook.steps | SurveyStep.tsx | 설문 단계 컴포넌트 |
| Braille | component | src.components.braille | BrailleCell.tsx | 점자 셀 컴포넌트 |
| Braille | component | src.components.braille | BrailleCells.tsx | 점자 셀 배열 컴포넌트 |
| Braille | component | src.components.braille | BrailleGrid.tsx | 점자 그리드 컴포넌트 |
| Braille | component | src.components.braille | BrailleStrip.tsx | 점자 스트립 컴포넌트 |
| Braille | component | src.components.braille | BrailleRow.tsx | 점자 행 컴포넌트 |
| Braille | component | src.components.braille | BrailleKeywordsPanel.tsx | 점자 키워드 패널 컴포넌트 |
| Braille | component | src.components.braille | ChunkNavigation.tsx | 청크 네비게이션 컴포넌트 |
| Braille | component | src.components.braille | ArduinoButtonControl.tsx | 아두이노 버튼 제어 컴포넌트 |
| Braille | hook | src.hooks | useBrailleBLE.ts | 점자 디스플레이 BLE 연동 Hook |
| Braille | hook | src.hooks | useBrailleChunkReader.ts | 점자 청크 리더 Hook |
| Braille | hook | src.hooks | useArduinoButtons.ts | 아두이노 버튼 Hook |
| Braille | utils | src.utils.braille | OrbitReaderAdapter.ts | Orbit Reader 20 어댑터 |
| Braille | utils | src.utils.braille | GenericBLEAdapter.ts | 일반 BLE 어댑터 |
| Braille | utils | src.utils.braille | MockBrailleAdapter.ts | 모의 점자 어댑터 |
| Braille | utils | src.utils.braille | BrailleDeviceAdapter.ts | 점자 디바이스 어댑터 인터페이스 |
| Voice | component | src.components.input | SpeechBar.tsx | 음성 입력 바 컴포넌트 |
| Voice | component | src.components.input | MicButton.tsx | 마이크 버튼 컴포넌트 |
| Voice | component | src.components.input | VoiceMicAnimation.tsx | 음성 마이크 애니메이션 |
| Voice | component | src.components.input | GlobalVoiceRecognition.tsx | 전역 음성 인식 컴포넌트 |
| Voice | component | src.components.voice | VoiceFirstDisplay.tsx | 음성 우선 표시 컴포넌트 |
| Voice | hook | src.hooks | useTTS.ts | 음성 합성 (TTS) Hook |
| Voice | hook | src.hooks | useSTT.ts | 음성 인식 (STT) Hook |
| Voice | hook | src.hooks | useVoiceCommands.ts | 음성 명령 Hook |
| Voice | hook | src.hooks | useAutoGuidance.ts | 자동 안내 Hook |
| Voice | service | src.services.voice | index.ts | 음성 서비스 |
| Voice | service | src.services.voice.providers | WebSpeechTTSProvider.ts | Web Speech API TTS 제공자 |
| Voice | service | src.services.voice.providers | WebSpeechSTTProvider.ts | Web Speech API STT 제공자 |
| Voice | service | src.services.voice | types.ts | 음성 서비스 타입 정의 |
| Voice | utils | src.utils.voice | commands.ts | 음성 명령 정의 |
| Voice | utils | src.utils.voice | matchers.ts | 음성 명령 매칭 유틸리티 |
| Voice | utils | src.utils.voice | normalizers.ts | 음성 텍스트 정규화 유틸리티 |
| AI | component | src.components.ai | AIQuestionInput.tsx | AI 질문 입력 컴포넌트 |
| AI | hook | src.hooks | useAILearningAssistant.ts | AI 학습 도우미 Hook |
| AI | hook | src.hooks | useAILectureTeacher.ts | AI 강의 선생님 Hook |
| AI | hook | src.hooks | useUnitAI.ts | 단원 AI Hook |
| AI | hook | src.hooks | useUnitAIExplanation.ts | 단원 AI 설명 Hook |
| AI | hook | src.hooks | useExtractKeywords.ts | 키워드 추출 Hook |
| AI | service | src.services.ai | index.ts | AI 서비스 |
| Question | component | src.components.question | AnswerInput.tsx | 답안 입력 컴포넌트 |
| Question | component | src.components.question | AnswerResult.tsx | 답안 결과 컴포넌트 |
| Question | service | src.services | answers.ts | 답안 API 서비스 |
| API | service | src.services.api | client.ts | API 클라이언트 (axios 기반) |
| API | service | src.services.api | index.ts | API 서비스 인덱스 |
| Templates | service | src.services | templates.ts | 템플릿 API 서비스 |
| Progress | service | src.services | progress.ts | 학습 진도 API 서비스 |
| System | component | src.components.system | ToastA11y.tsx | 접근성 토스트 컴포넌트 |
| System | component | src.components.system | ErrorBoundary.tsx | 에러 바운더리 컴포넌트 |
| System | component | src.components.system | HealthCheck.tsx | 헬스 체크 컴포넌트 |
| System | component | src.components.system | DevHealth.tsx | 개발 헬스 체크 컴포넌트 |
| System | component | src.components.system | PerformanceMonitor.tsx | 성능 모니터 컴포넌트 |
| System | component | src.components.ui | AppShellMobile.tsx | 모바일 앱 셸 컴포넌트 |
| System | hook | src.hooks | useToast.ts | 토스트 Hook |
| System | hook | src.hooks | usePerformance.ts | 성능 모니터링 Hook |
| Home | component | src.components.home | SubjectSelectCard.tsx | 과목 선택 카드 컴포넌트 |
| Home | component | src.components.home | ContinueLearningCard.tsx | 이어서 학습하기 카드 |
| Home | component | src.components.home | BrailleDeviceCard.tsx | 점자 디바이스 카드 |
| Home | component | src.components.home | PDFManagementCard.tsx | PDF 관리 카드 |
| Home | page | src.pages | Main.tsx | 메인 페이지 |
| Lesson | page | src.pages | Lesson.tsx | 강의 페이지 |
| Lesson | component | src.components.lesson | LessonList.tsx | 강의 목록 컴포넌트 |
| Curriculum | page | src.pages | Curriculum.tsx | 커리큘럼 페이지 |
| LearningSummary | page | src.pages | LearningSummary.tsx | 학습 요약 페이지 |
| Book | page | src.pages | Book.tsx | 교재 페이지 (레거시) |
| Routing | component | src.components.routing | LearnRedirect.tsx | 학습 리다이렉트 컴포넌트 |
| Debug | component | src.components.debug | VoiceRecognitionDebug.tsx | 음성 인식 디버그 컴포넌트 |
| Textbook | component | src.components.textbook | ProblemContent.tsx | 문제 콘텐츠 컴포넌트 |
| Textbook | component | src.components.textbook | SimilarContentSection.tsx | 유사 콘텐츠 섹션 컴포넌트 |
| Hook | hook | src.hooks | useBookStats.ts | 교재 통계 Hook |
| Hook | hook | src.hooks | useLearnMenuHandler.ts | 학습 메뉴 핸들러 Hook |
| Hook | hook | src.hooks | usePageBase.ts | 페이지 베이스 Hook |
| Hook | hook | src.hooks | useParseMonitoring.ts | 파싱 모니터링 Hook |
| Hook | hook | src.hooks | useTOCAutoExtract.ts | 목차 자동 추출 Hook |
| Service | service | src.services | CommandService.ts | 명령 서비스 |
| STT | service | src.stt | GoogleStreamingProvider.ts | Google 스트리밍 STT 제공자 |
| Strategy | strategy | src.strategies | subjectLearning.ts | 과목별 학습 전략 |

---

## 4. 파일 구조 통계

### 4.1 Backend 파일 통계

- **총 파일 수**: 약 85개
- **라우터**: 14개
- **서비스**: 6개 (book_service.py, book_conversion.py, curriculum_service.py, template_service.py, korean_braille.py, progress_tracker.py)
- **인프라**: 약 60개
- **스키마**: 7개
- **유틸리티**: 6개

### 4.2 Frontend 파일 통계

- **총 파일 수**: 약 120개
- **페이지**: 17개
- **컴포넌트**: 약 60개
- **Hooks**: 25개
- **서비스**: 10개
- **스토어**: 7개
- **타입**: 10개
- **유틸리티**: 8개

---

## 5. 모듈별 의존성

### 5.1 Backend 모듈 의존성

```
Common (config, utils, schemas)
    ↓
Routers (API 엔드포인트)
    ↓
Services (비즈니스 로직)
    ↓
PDF Infrastructure, Database Infrastructure
```

**리팩토링 구조**:
- **Routers**: API 엔드포인트만 담당 (HTTP 요청/응답 처리)
- **Services**: 비즈니스 로직 담당 (데이터 처리, 변환, 파이프라인 실행 등)
- 주요 서비스 파일:
  - `book_service.py`: PDF 파이프라인 실행 및 교재 처리
  - `curriculum_service.py`: 커리큘럼 생성 및 변환
  - `template_service.py`: 템플릿 관리 비즈니스 로직
  - `book_conversion.py`: 데이터 변환 유틸리티

### 5.2 Frontend 모듈 의존성

```
Common (types, utils, store, styles)
    ↓
App (router)
    ↓
Pages → Components → Hooks → Services
```

---

**모듈별 파일 구조 문서 작성 완료**
