# 프로젝트 폴더 구조

이 문서는 점글이 수능 헬퍼 프로젝트의 전체 폴더 구조를 설명합니다.

## 📁 전체 구조

```
jeomgeuli-suneung-helper/
├── apps/                    # 프론트엔드 애플리케이션
│   ├── extension/          # Chrome 확장 프로그램
│   └── web/                # 웹 애플리케이션
├── arduino/                # Arduino 펌웨어
├── raspberrypi/            # Raspberry Pi 관련 코드
├── api/                    # FastAPI 백엔드
├── data/                   # 데이터 저장소
│   ├── extracted/          # 추출된 데이터
│   ├── parsed/             # 파싱된 데이터
│   └── uploads/            # 업로드된 파일
└── infra/                  # 인프라 설정
    └── docker-compose.yml  # Docker Compose 설정
```

---

## 📱 apps/

### apps/extension/ - Chrome 확장 프로그램

점글이 학습 알림을 위한 Chrome 확장 프로그램입니다.

```
extension/
├── manifest.json           # 확장 프로그램 매니페스트
├── package.json            # 프로젝트 의존성 및 스크립트
└── src/
    ├── api.ts              # API 통신 모듈
    ├── background.ts       # 백그라운드 스크립트
    ├── contentScript.ts    # 콘텐츠 스크립트
    └── popup/              # 팝업 UI
        ├── popup.html      # 팝업 HTML
        └── Popup.tsx       # 팝업 React 컴포넌트
```

### apps/web/ - 웹 애플리케이션

React + TypeScript + Vite 기반의 메인 웹 애플리케이션입니다.

```
web/
├── index.html              # 진입점 HTML
├── package.json            # 프로젝트 의존성
├── package-lock.json       # 의존성 잠금 파일
├── tsconfig.json           # TypeScript 설정
├── tsconfig.node.json      # Node용 TypeScript 설정
├── vite.config.ts          # Vite 빌드 설정
├── tailwind.config.js      # Tailwind CSS 설정
├── postcss.config.js       # PostCSS 설정
├── playwright.config.ts    # Playwright E2E 테스트 설정
├── dev-dist/               # 개발 빌드 산출물
│   ├── registerSW.js       # Service Worker 등록
│   ├── sw.js               # Service Worker
│   └── workbox-*.js        # Workbox 라이브러리
├── scripts/
│   └── gen-icons.mjs       # 아이콘 생성 스크립트
├── e2e/                    # E2E 테스트
│   ├── accessibility.spec.ts
│   ├── explore.spec.ts
│   ├── home.spec.ts
│   └── voice-control.spec.ts
└── src/
    ├── main.tsx            # 애플리케이션 진입점
    ├── index.css           # 전역 스타일
    ├── vite-env.d.ts       # Vite 타입 정의
    │
    ├── app/                # 앱 설정
    │   ├── App.tsx         # 메인 App 컴포넌트
    │   └── routes.tsx      # 라우팅 설정
    │
    ├── pages/              # 페이지 컴포넌트 (52개 파일)
    │   ├── Home.tsx        # 홈 페이지
    │   ├── Main.tsx        # 메인 페이지
    │   ├── Explore.tsx     # 탐색 페이지
    │   ├── NotFound.tsx    # 404 페이지
    │   │
    │   ├── Home/           # 홈 관련 컴포넌트
    │   │   ├── components/
    │   │   │   ├── BrailleDeviceCard.tsx
    │   │   │   ├── ContinueLearningCard.tsx
    │   │   │   ├── PDFManagementCard.tsx
    │   │   │   └── SubjectSelectCard.tsx
    │   │
    │   ├── Learning/       # 학습 화면
    │   │   ├── LearningScreen.tsx
    │   │   └── components/
    │   │       ├── BrailleStatusPanel.tsx
    │   │       ├── CurrentContentPanel.tsx
    │   │       ├── DocumentTree.tsx
    │   │       └── GraphPreview.tsx
    │   │
    │   ├── Question/       # 문제 풀이
    │   │   ├── Question.tsx
    │   │   └── components/
    │   │       ├── AnswerInput.tsx
    │   │       ├── AnswerResult.tsx
    │   │       ├── ChoiceComparison.tsx
    │   │       ├── QuestionDisplay.tsx
    │   │       └── WrongAnswerList.tsx
    │   │
    │   ├── Passage/        # 지문 입력
    │   │   ├── Passage.tsx
    │   │   └── components/
    │   │       ├── PassageInput.tsx
    │   │       └── PassageStructure.tsx
    │   │
    │   ├── Textbook/       # 교과서 관리
    │   │   ├── Textbook.tsx
    │   │   └── components/
    │   │       ├── PDFUpload.tsx
    │   │       ├── TextbookList.tsx
    │   │       ├── UnitContent.tsx
    │   │       └── UnitList.tsx
    │   │
    │   ├── GraphTable/     # 그래프/표 변환
    │   │   ├── GraphTable.tsx
    │   │   └── components/
    │   │       ├── GraphDualView.tsx
    │   │       ├── GraphPatterns.tsx
    │   │       └── ImageUpload.tsx
    │   │
    │   ├── Explore/        # 탐색 기능
    │   │   └── hooks/
    │   │       ├── useExploreChat.ts
    │   │       ├── useExploreKeywords.ts
    │   │       └── useExploreNews.ts
    │   │
    │   ├── exam/           # 시험 모드 관련
    │   │   ├── SentenceRepeat.tsx
    │   │   ├── TextbookConverter.tsx
    │   │   └── TextCompress.tsx
    │   │
    │   ├── ExamMode/       # 시험 모드
    │   │   └── ExamMode.tsx
    │   │
    │   ├── ExamTimer/      # 시험 타이머
    │   │   └── ExamTimer.tsx
    │   │
    │   ├── BrailleSpeed/   # 점자 속도 연습
    │   │   └── BrailleSpeed.tsx
    │   │
    │   ├── Vocab/          # 어휘 학습
    │   │   ├── Vocab.tsx
    │   │   └── components/
    │   │       ├── SisaWords.tsx
    │   │       └── VocabCard.tsx
    │   │
    │   ├── Book.tsx        # 책 뷰어
    │   ├── Lesson.tsx      # 레슨 페이지
    │   ├── Unit.tsx        # 단원 페이지
    │   ├── Quiz.tsx        # 퀴즈 페이지
    │   ├── Review.tsx      # 복습 페이지
    │   ├── LearnIndex.tsx  # 학습 인덱스
    │   ├── LearnStep.tsx   # 학습 단계
    │   ├── TestStep.tsx    # 테스트 단계
    │   └── FreeConvert.tsx # 자유 변환
    │
    ├── components/         # 재사용 가능한 컴포넌트 (34개 파일)
    │   ├── braille/        # 점자 관련 컴포넌트
    │   │   ├── BrailleCell.tsx
    │   │   ├── BrailleCells.tsx
    │   │   ├── BrailleDot.tsx
    │   │   ├── BrailleGrid.tsx
    │   │   ├── BrailleOutputPanel.tsx
    │   │   ├── BraillePanel.tsx
    │   │   ├── BrailleRow.tsx
    │   │   ├── BrailleStrip.tsx
    │   │   └── ChunkNavigation.tsx
    │   │
    │   ├── input/          # 입력 관련 컴포넌트
    │   │   ├── ChatLikeInput.tsx
    │   │   ├── GlobalVoiceRecognition.tsx
    │   │   ├── MicButton.tsx
    │   │   ├── SpeechBar.tsx
    │   │   └── VoiceButton.tsx
    │   │
    │   ├── voice/          # 음성 관련 컴포넌트
    │   │   └── VoiceFirstDisplay.tsx
    │   │
    │   ├── ui/             # UI 컴포넌트
    │   │   ├── AnswerCard.tsx
    │   │   ├── AppShellMobile.tsx
    │   │   ├── BottomBar.tsx
    │   │   └── Card.tsx
    │   │
    │   ├── system/         # 시스템 컴포넌트
    │   │   ├── DevHealth.tsx
    │   │   ├── ErrorBoundary.tsx
    │   │   ├── HealthCheck.tsx
    │   │   ├── PerformanceMonitor.tsx
    │   │   └── ToastA11y.tsx
    │   │
    │   ├── settings/       # 설정 컴포넌트
    │   │   └── BrailleDisplaySettings.tsx
    │   │
    │   ├── subject/        # 과목 관련
    │   │   └── SubjectDisplayAdapter.tsx
    │   │
    │   ├── common/         # 공통 컴포넌트
    │   │   └── MemoizedList.tsx
    │   │
    │   ├── layout/         # 레이아웃 컴포넌트
    │   │   └── PageLayout.tsx
    │   │
    │   ├── debug/          # 디버그 컴포넌트
    │   │   └── VoiceRecognitionDebug.tsx
    │   │
    │   ├── textbook/       # 교과서 관련 컴포넌트
    │   │   └── BookUpload.tsx
    │   │
    │   ├── lesson/         # 레슨 관련 컴포넌트
    │   │   └── LessonList.tsx
    │   │
    │   ├── progress/      # 진도 관련 컴포넌트
    │   │   └── ProgressIndicator.tsx
    │   │
    │   ├── review/         # 복습 관련 컴포넌트
    │   │   └── ReviewQueue.tsx
    │   │
    │   └── unit/           # 단위 관련 컴포넌트
    │       └── UnitViewer.tsx
    │
    ├── hooks/              # 커스텀 훅 (28개 파일)
    │   ├── api/            # API 관련 훅
    │   │   ├── useAnswers.ts
    │   │   ├── useBooks.ts
    │   │   ├── useContinue.ts
    │   │   ├── useLessons.ts
    │   │   ├── useProgress.ts
    │   │   ├── useReview.ts
    │   │   ├── useSyncpoints.ts
    │   │   └── useUnits.ts
    │   │
    │   ├── braille/        # 점자 디바이스 관련 훅
    │   │   ├── __tests__/
    │   │   │   └── BrailleDeviceAdapter.test.ts
    │   │   ├── BrailleDeviceAdapter.ts
    │   │   ├── BrailleDeviceFactory.ts
    │   │   ├── GenericBLEAdapter.ts
    │   │   ├── MockBrailleAdapter.ts
    │   │   └── OrbitReaderAdapter.ts
    │   │
    │   ├── voice/          # 음성 명령 관련
    │   │   ├── commands.ts
    │   │   ├── matchers.ts
    │   │   └── normalizers.ts
    │   │
    │   ├── useBrailleBLE.ts          # BLE 점자 디바이스 훅
    │   ├── useBrailleChunkReader.ts  # 점자 청크 리더 훅
    │   ├── useBraillePlayback.ts     # 점자 재생 훅
    │   ├── useKeyboardNavigation.ts  # 키보드 네비게이션 훅
    │   ├── usePageBase.ts            # 페이지 기본 훅
    │   ├── usePerformance.ts         # 성능 모니터링 훅
    │   ├── usePointerGesture.ts      # 포인터 제스처 훅
    │   ├── useSTT.ts                 # 음성 인식 훅
    │   ├── useTTS.ts                 # 음성 합성 훅
    │   ├── useVoiceCommands.ts       # 음성 명령 훅
    │   └── useVoiceControl.ts        # 음성 제어 훅
    │
    ├── services/           # 서비스 레이어 (25개 파일)
    │   ├── __tests__/
    │   │   └── CommandService.test.ts
    │   ├── answers.ts      # 답안 서비스
    │   ├── api.ts          # API 클라이언트
    │   ├── books.ts        # 책 관리 서비스
    │   ├── CommandService.ts  # 명령 서비스
    │   ├── commands/     # 명령 패턴 구현
    │   │   ├── __tests__/
    │   │   │   └── CommandInvoker.test.ts
    │   │   ├── Command.ts
    │   │   ├── CommandInvoker.ts
    │   │   ├── ControlCommand.ts
    │   │   ├── LearningCommand.ts
    │   │   └── NavigateCommand.ts
    │   ├── learning/       # 학습 플로우 서비스
    │   │   ├── __tests__/
    │   │   │   └── LearningFlow.test.ts
    │   │   ├── LearningFlow.ts
    │   │   ├── PassageLearningFlow.ts
    │   │   ├── TextbookLearningFlow.ts
    │   │   └── VocabLearningFlow.ts
    │   ├── lessons.ts      # 레슨 서비스
    │   ├── passage/        # 지문 서비스
    │   │   └── PassageService.ts
    │   ├── progress.ts     # 진행 상황 서비스
    │   ├── question/       # 문제 서비스
    │   │   └── QuestionService.ts
    │   ├── review.ts       # 복습 서비스
    │   ├── syncpoints.ts  # 동기화 포인트 서비스
    │   ├── textbook/       # 교과서 서비스
    │   │   └── TextbookService.ts
    │   ├── units.ts        # 단원 서비스
    │   └── VoiceService.ts # 음성 서비스
    │
    ├── store/              # 상태 관리 (13개 파일)
    │   ├── __tests__/
    │   │   └── voice.test.ts
    │   ├── bookStore.ts    # 책 상태 관리
    │   ├── examStore.ts    # 시험 상태 관리
    │   ├── home.ts         # 홈 상태 관리
    │   ├── keywords.ts     # 키워드 상태 관리
    │   ├── learnStore.ts   # 학습 상태 관리
    │   ├── lessonSession.ts # 레슨 세션 상태
    │   ├── lessonStore.ts  # 레슨 상태 관리
    │   ├── progressStore.ts # 진행 상황 상태 관리
    │   ├── review.ts       # 복습 상태 관리 (ReviewItem)
    │   ├── reviewQueueStore.ts # 복습 큐 상태 관리 (ReviewQueueItem)
    │   ├── vocabStore.ts   # 어휘 상태 관리
    │   └── voice.ts        # 음성 상태 관리
    │
    ├── lib/                # 라이브러리 유틸리티 (16개 파일)
    │   ├── api/            # API 유틸리티
    │   │   ├── exam.ts     # 시험 API
    │   │   └── vocab.ts    # 어휘 API
    │   ├── api.ts          # API 클라이언트
    │   ├── braille.ts      # 점자 변환
    │   ├── brailleGrid.ts  # 점자 그리드
    │   ├── brailleMap.ts   # 점자 맵핑
    │   ├── braillePattern.ts # 점자 패턴
    │   ├── brailleSafe.ts  # 점자 안전 처리
    │   ├── http.ts         # HTTP 클라이언트
    │   ├── normalize.ts   # 텍스트 정규화
    │   ├── performance.ts  # 성능 유틸리티
    │   └── voice/          # 음성 관련 유틸리티
    │       ├── CircuitBreaker.ts
    │       ├── CommandRouter.ts
    │       ├── MicMode.ts
    │       ├── TranscriptProcessor.ts
    │       └── VoiceEventBus.ts
    │
    ├── types/              # TypeScript 타입 정의 (15개 파일)
    │   ├── __tests__/
    │   │   └── errors.test.ts
    │   ├── answer.ts       # 답안 타입
    │   ├── api.ts          # API 타입
    │   ├── book.ts         # 책 타입
    │   ├── chat.ts         # 채팅 타입
    │   ├── errors.ts       # 에러 타입
    │   ├── explore.ts      # 탐색 타입
    │   ├── global.d.ts     # 전역 타입 정의
    │   ├── index.ts        # 타입 인덱스
    │   ├── lesson.ts       # 레슨 타입
    │   ├── progress.ts     # 진행 상황 타입
    │   ├── review.ts       # 복습 타입
    │   ├── syncpoint.ts    # 동기화 포인트 타입
    │   ├── unit.ts         # 단원 타입
    │   └── voice.ts        # 음성 타입
    │
    ├── utils/              # 유틸리티 함수 (4개 파일)
    │   ├── __tests__/
    │   │   └── brailleChunk.test.ts
    │   ├── brailleChunk.ts      # 점자 청크 유틸리티
    │   ├── brailleChunkBuilder.ts # 점자 청크 빌더
    │   └── contentExtractor.ts  # 콘텐츠 추출기
    │
    ├── strategies/         # 전략 패턴 구현 (2개 파일)
    │   ├── __tests__/
    │   │   └── subjectLearning.test.ts
    │   └── subjectLearning.ts # 과목별 학습 전략
    │
    ├── stt/                # 음성 인식 관련 (1개 파일)
    │   └── GoogleStreamingProvider.ts # Google STT 프로바이더
    │
    ├── config/             # 설정 파일
    │   └── brailleDisplay.ts  # 점자 디스플레이 설정
    │
    ├── styles/             # 스타일 파일 (2개 CSS 파일)
    │   ├── tokens.css      # 디자인 토큰
    │   └── util.css        # 유틸리티 스타일
    │
    └── __tests__/          # 통합 테스트
        └── integration/
            └── api.test.ts # API 통합 테스트
```

---

## 🔧 arduino/

Arduino 기반 점자 디스플레이 펌웨어입니다.

```
arduino/
├── README.md               # Arduino 프로젝트 설명
│
├── braille_3cell/          # 3셀 점자 디스플레이 펌웨어
│   ├── braille_3cell.ino   # 메인 스케치 파일
│   ├── braille.cpp         # 점자 구현
│   ├── braille.h           # 점자 헤더
│   ├── BrailleConverter.cpp
│   ├── BrailleConverter.h
│   └── BrailleMap.h        # 점자 맵핑
│
├── braille_3cell_test/     # 3셀 점자 테스트
│   ├── integration_test/
│   │   └── integration_test.ino
│   └── test_braille_patterns/
│       └── test_braille_patterns.ino
│
└── braille_firmware/       # 점자 펌웨어
    └── braille_firmware.ino
```

---

## 🍓 raspberrypi/

Raspberry Pi에서 실행되는 BLE 서버입니다.

```
raspberrypi/
├── README.md               # Raspberry Pi 프로젝트 설명
└── ble_server.py           # BLE 서버 스크립트
```

---

## 🐍 api/ - FastAPI 백엔드

Python FastAPI 기반의 백엔드 API 서버입니다.

```
api/
├── Dockerfile              # Docker 이미지 빌드 설정
├── requirements.txt        # Python 의존성 (기본)
├── requirements-ai.txt     # AI/ML 기능 의존성 (선택적)
│
├── tests/                  # 테스트 파일
│   ├── __init__.py
│   ├── test_content_generator.py    # 콘텐츠 생성기 테스트
│   ├── test_english_parser.py       # 영어 파서 테스트
│   ├── test_hwp_extract.py          # HWP 추출 테스트
│   ├── test_literature_parser.py    # 문학 파서 테스트
│   ├── test_math1_parser.py         # 수학Ⅰ 파서 테스트
│   ├── test_pdf_api.py              # PDF API 테스트
│   └── test_pdf_extract.py          # PDF 추출 테스트
│
├── scripts/                # 유틸리티 스크립트
│   └── build_training_dataset.py    # 학습 데이터셋 빌드
│
├── datasets/               # 데이터셋 저장소
├── pdfs/                   # PDF 파일 저장소
├── lecture_scripts/        # 강의 대본 저장소
│
└── app/
    ├── __init__.py
    ├── main.py             # FastAPI 애플리케이션 진입점
    │
    ├── core/               # 핵심 설정 (2개 파일)
    │   ├── __init__.py
    │   └── config.py       # 애플리케이션 설정
    │
    ├── db/                 # 데이터베이스 관련 (3개 파일)
    │   ├── __init__.py
    │   ├── models.py       # 데이터베이스 모델
    │   └── session.py      # DB 세션 관리
    │
    ├── routers/            # API 라우터
    │   ├── __init__.py
    │   ├── answers.py      # 답안 관련 API
    │   ├── books.py        # 책 관련 API (PDF 업로드, 파싱)
    │   ├── health.py       # 헬스 체크 API
    │   ├── lessons.py      # 레슨 관련 API
    │   ├── pdf.py          # PDF 추출 API
    │   ├── progress.py     # 진행 상황 API
    │   ├── review.py       # 복습 관련 API
    │   ├── syncpoints.py   # 동기화 포인트 API
    │   └── units.py        # 단원 관련 API
    │
    ├── schemas/            # Pydantic 스키마 (8개 파일)
    │   ├── __init__.py
    │   ├── answer.py       # 답안 스키마
    │   ├── book.py         # 책 스키마
    │   ├── lesson.py       # 레슨 스키마
    │   ├── progress.py     # 진행 상황 스키마
    │   ├── review.py       # 복습 스키마
    │   ├── syncpoint.py    # 동기화 포인트 스키마
    │   └── unit.py         # 단원 스키마
    │
    ├── services/           # 비즈니스 로직
    │   ├── __init__.py
    │   │
    │   ├── audio_sync.py           # 오디오 동기화 서비스
    │   ├── braille_convert.py      # 점자 변환 서비스
    │   ├── content_auto_generator.py  # 콘텐츠 자동 생성
    │   ├── hwp_extract.py          # HWP 파일 추출
    │   ├── pdf_image_extract.py    # PDF 이미지 추출 (레거시)
    │   ├── pdf_extract.py          # PDF 추출 서비스 (레거시)
    │   ├── pdf_structure_extract.py # PDF 구조 추출 (레거시)
    │   ├── pdf_parse.py            # PDF 파싱 서비스 (레거시)
    │   ├── review_logic.py         # 복습 로직 서비스
    │   │
    │   ├── pdf_extract/            # PDF 추출 모듈 (새 아키텍처)
    │   │   ├── __init__.py
    │   │   ├── base_extractor.py   # 추출기 베이스 클래스
    │   │   ├── pdfplumber_extractor.py  # PDFPlumber 추출기
    │   │   ├── image_extractor.py  # 이미지 추출기
    │   │   ├── literature_extractor.py  # 문학 전용 추출기
    │   │   │
    │   │   ├── enhanced_ocr.py     # Enhanced OCR (AI)
    │   │   ├── ai_text_postprocessor.py  # AI 텍스트 후처리
    │   │   └── math_ocr.py         # 수식 OCR (AI)
    │   │
    │   ├── pdf_parse/              # PDF 파싱 모듈 (새 아키텍처)
    │   │   ├── __init__.py
    │   │   ├── base_parser.py      # 파서 베이스 클래스
    │   │   ├── parse_pipeline.py   # 파싱 파이프라인
    │   │   ├── json_schema.py      # JSON 스키마 정의
    │   │   └── ai_structure_classifier.py  # AI 구조 분류기
    │   │
    │   └── subject_strategies/     # 과목별 파싱 전략
    │       ├── __init__.py
    │       │
    │       ├── math.py             # 수학 파서 (일반)
    │       ├── math1.py            # 수학Ⅰ 파서 (전용)
    │       ├── math1_schema.py     # 수학Ⅰ JSON 스키마
    │       │
    │       ├── korean.py           # 국어 파서
    │       │
    │       ├── english.py          # 영어 파서
    │       ├── english_schema.py   # 영어 JSON 스키마
    │       │
    │       ├── literature.py       # 문학 파서
    │       └── literature_schema.py # 문학 JSON 스키마
    │
    └── utils/              # 유틸리티 함수 (2개 파일)
        ├── __init__.py
        └── text_utils.py   # 텍스트 유틸리티
```

---

## 📊 data/

데이터 저장소 디렉토리입니다.

```
data/
├── extracted/              # 추출된 데이터
├── parsed/                 # 파싱된 데이터
└── uploads/                # 업로드된 파일
```

---

## 🐳 infra/

인프라스트럭처 설정 파일입니다.

```
infra/
└── docker-compose.yml      # Docker Compose 설정
```

---

## 📝 주요 기술 스택

### 프론트엔드 (apps/web)
- **프레임워크**: React 18
- **언어**: TypeScript
- **빌드 도구**: Vite
- **스타일링**: Tailwind CSS
- **상태 관리**: Zustand
- **라우팅**: React Router
- **API 클라이언트**: Axios, React Query
- **테스트**: Vitest, Playwright

### 확장 프로그램 (apps/extension)
- **언어**: TypeScript
- **빌드 도구**: Vite

### 백엔드 (api)
- **프레임워크**: FastAPI
- **언어**: Python 3.12+
- **PDF 처리**: pdfplumber, pdf2image
- **OCR**: Tesseract OCR (pytesseract)
- **AI/ML**: OpenAI API, Transformers (선택적)
- **데이터베이스**: SQLAlchemy ORM

### 하드웨어
- **Arduino**: C++ (펌웨어)
- **Raspberry Pi**: Python (BLE 서버)

---

## 🔍 주요 기능 영역

1. **점자 디스플레이**: BLE를 통한 점자 디바이스 연동
2. **음성 인식/합성**: STT/TTS 기능
3. **학습 관리**: 교과서, 레슨, 단원 관리
4. **문제 풀이**: 문제 표시 및 답안 입력
5. **복습 시스템**: 학습 진행 상황 추적 및 복습
6. **그래프/표 변환**: 이미지를 점자로 변환
7. **시험 모드**: 시험 환경 시뮬레이션
8. **PDF 처리**: 
   - PDF 텍스트/이미지 추출
   - 과목별 구조 파싱 (수학Ⅰ, 영어, 문학)
   - AI 기반 OCR 및 텍스트 후처리
   - 수식 인식 및 LaTeX 변환
9. **HWP 처리**: 한글 파일 텍스트 추출

---

## 📚 API 서비스 아키텍처

### PDF 처리 파이프라인

```
PDF 파일 업로드
    ↓
[Extract 단계]
    ├── PDFPlumberExtractor      # 기본 텍스트 추출
    ├── EnhancedOCR              # OCR (스캔본 처리)
    └── LiteratureExtractor      # 과목별 전용 추출
    ↓
[Parse 단계]
    ├── AIStructureClassifier    # AI 기반 블록 분류
    └── SubjectStrategies        # 과목별 파싱 전략
        ├── Math1Parser          # 수학Ⅰ: 개념/예제/유제
        ├── EnglishParser        # 영어: 지문/문제 분리
        └── LiteratureParser     # 문학: 지문/문제 분리
    ↓
[Post-process 단계]
    ├── AITextPostProcessor      # AI 텍스트 정리
    └── MathOCR                  # 수식 → LaTeX 변환
    ↓
구조화된 JSON 출력
```

### 서비스 계층 구조

1. **추출 계층** (`pdf_extract/`)
   - `BaseExtractor`: 추출기 인터페이스
   - `PDFPlumberExtractor`: PDF 텍스트 추출
   - `EnhancedOCR`: OCR + 전처리
   - `MathOCR`: 수식 이미지 인식

2. **파싱 계층** (`pdf_parse/`, `subject_strategies/`)
   - `BaseParser`: 파서 인터페이스
   - `AIStructureClassifier`: AI 블록 분류
   - 과목별 파서: Math1, English, Literature

3. **후처리 계층**
   - `AITextPostProcessor`: LLM 기반 텍스트 정리
   - 점자 변환: `braille_convert.py`

### API 엔드포인트

- `POST /api/v1/books/upload`: PDF 업로드 및 파싱
- `POST /api/v1/books/{book_id}/reparse`: 재파싱
- `GET /api/v1/books/{book_id}/parse-status`: 파싱 상태 확인
- `POST /api/v1/pdf/extract`: PDF 텍스트 추출
- `GET /api/v1/health`: 헬스 체크

---

*마지막 업데이트: 2024년 12월*
