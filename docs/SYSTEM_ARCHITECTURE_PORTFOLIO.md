# 점그리 수능 도우미 - 시스템 아키텍처 (포트폴리오 버전)

**작성일**: 2026년 1월 28일  
**버전**: 2.0.0  
**프로젝트**: 점그리 수능 도우미 (Jeomgeuli Suneung Helper)

---

## 1. 전체 시스템 아키텍처

```mermaid
graph TB
    subgraph UI["Frontend Layer<br/>React + TypeScript"]
        Pages[Pages<br/>Start, BookSelect, Learning, Admin]
        Components[Components<br/>braille, voice, unit, ai]
        Hooks[Custom Hooks<br/>useBrailleBLE, useTTS, useSTT]
        Services[Service Layer<br/>API Client, Subject Services]
        State[State Management<br/>Zustand Stores]
    end
    
    subgraph API["API Gateway Layer<br/>FastAPI Routers"]
        Routers[API Routers<br/>Books, Literature, English, Math1<br/>AI, Braille, Templates, Curriculum<br/>Lessons, Units, Progress, Answers<br/>Subjects, Health]
    end
    
    subgraph Services["Business Logic Layer<br/>Services"]
        BookSvc[Book Service<br/>PDF 업로드, 파싱 파이프라인]
        CurSvc[Curriculum Service<br/>커리큘럼 생성]
        TempSvc[Template Service<br/>템플릿 관리, AI 자동 생성]
        BrailleSvc[Korean Braille Service<br/>한글 → 점자 변환]
        ProgressSvc[Progress Tracker<br/>학습 진도 추적]
    end
    
    subgraph Infra["Infrastructure Layer"]
        subgraph PDF["PDF Processing"]
            Pipeline[Unified Pipeline<br/>PDF 추출, 파싱, 콘텐츠 추출]
            Parser[Hybrid Router<br/>Template/AI/Rule 기반 파싱]
            Extractors[Extractors<br/>Pdfplumber, OCR, PyMuPDF]
        end
        
        subgraph AI["AI Infrastructure"]
            GenAI[Generative AI<br/>StructureAnalyzer, StructureParser<br/>ExplanationGenerator, RAGRecommender]
            DL[Deep Learning<br/>LayoutAnalyzer, MathRecognizer]
        end
        
        DB[Database<br/>SQLAlchemy ORM]
    end
    
    subgraph Storage["Storage Layer"]
        FileSystem[File System<br/>JSON, Images]
        Database[(Database<br/>Books, Curriculums, Lessons)]
    end
    
    subgraph External["External Services"]
        OpenAPI[OpenAI API<br/>GPT-4o-mini]
        BrowserAPI[Browser APIs<br/>Web Speech, Web Bluetooth]
        Hardware[Hardware<br/>Orbit Reader 20]
    end
    
    Pages --> Components
    Components --> Hooks
    Hooks --> Services
    Services --> State
    
    UI -->|HTTP/REST API| API
    API --> Routers
    Routers --> Services
    Services --> Infra
    Infra --> Storage
    AI --> OpenAPI
    UI --> BrowserAPI
    BrowserAPI --> Hardware
```

---

## 2. 프론트엔드 아키텍처

```mermaid
graph TD
    subgraph Frontend["Frontend Architecture"]
        subgraph Presentation["Presentation Layer"]
            Start[Start Page]
            BookSelect[BookSelect Page]
            LearningSummary[Learning Summary]
            LiteratureLectures[Literature Lectures]
            EnglishLectures[English Lectures]
            Math1Lectures[Math1 Lectures]
            UnitSwipe[Unit Swipe 학습]
            Admin[Admin Page]
        end
        
        subgraph Components["Component Layer"]
            BrailleComp[Braille Components<br/>BrailleCell, BrailleGrid, ChunkNavigation]
            VoiceComp[Voice Components<br/>VoiceFirstDisplay, MicButton]
            UnitComp[Unit Components<br/>UnitViewer, ConceptViewer, WorkViewer]
            AIComp[AI Components<br/>AIQuestionInput, RAGRecommendationCard]
            AdminComp[Admin Components<br/>TemplateManager, TOCTemplateWizard]
        end
        
        subgraph Hooks["Custom Hooks Layer"]
            useBraille[useBrailleBLE<br/>점자 디스플레이 BLE 연동]
            useBrailleChunk[useBrailleChunkReader<br/>점자 청크 읽기]
            useTTS[useTTS<br/>음성 합성]
            useSTT[useSTT<br/>음성 인식]
            useUnit[useUnitData<br/>단원 데이터 관리]
            useUnitNav[useUnitNavigation<br/>단원 네비게이션]
            useVoice[useVoiceCommands<br/>음성 명령 처리]
            useAI[useAILearningAssistant<br/>AI 학습 도우미]
        end
        
        subgraph Service["Service Layer"]
            APIClient[API Client<br/>HTTP 요청/응답 처리]
            SubjectSvc[Subject Services<br/>literature, english, math1]
            AISvc[AI Service<br/>질의응답, 설명 생성]
            VoiceSvc[Voice Service<br/>WebSpeechSTT/TTS]
        end
        
        subgraph State["State Management"]
            BookStore[bookStore<br/>교재 및 강의 목록]
            ProgressStore[progressStore<br/>학습 진도]
            LessonStore[lessonStore<br/>현재 학습 중인 강의]
            LiteratureProgress[literatureProgressStore<br/>문학 진도]
            VoiceStore[voice.ts<br/>음성 인터페이스 상태]
            LearnStore[learnStore<br/>학습 상태]
        end
        
        subgraph Utils["Utility Layer"]
            BrailleUtils[Braille Utils<br/>Device Adapters]
            TextUtils[Text Utils<br/>markdownToPlainText, sectionMatcher]
            VoiceUtils[Voice Utils<br/>commands, matchers, normalizers]
        end
    end
    
    Presentation --> Components
    Components --> Hooks
    Hooks --> Service
    Service --> State
    Service --> Utils
```

---

## 3. 백엔드 아키텍처

```mermaid
graph TD
    subgraph Backend["Backend Architecture"]
        subgraph Router["Router Layer"]
            SubjectRouters[Subject Routers<br/>books, literature, english, math1, subjects]
            LearningRouters[Learning Routers<br/>lessons, units, curriculum, progress]
            FeatureRouters[Feature Routers<br/>ai, braille, templates, health]
        end
        
        subgraph Service["Service Layer"]
            BookService[Book Service<br/>upload_book, get_books, reparse_book<br/>process_pdf_background]
            CurService[Curriculum Service<br/>generate_curriculum, get_curriculum<br/>create_curriculum_from_pipeline]
            TempService[Template Service<br/>generate_template, update_template<br/>AI 기반 템플릿 생성]
            BrailleService[Korean Braille Service<br/>convert_to_braille]
            ProgressService[Progress Tracker<br/>track_progress, get_continue_learning]
            BookConversion[Book Conversion Service<br/>LearningUnit → Unit 변환]
        end
        
        subgraph Infra["Infrastructure Layer"]
            subgraph PDF["PDF Processing"]
                Pipeline[Unified Pipeline<br/>1. PDF 추출<br/>2. 파싱<br/>3. 강의 콘텐츠 추출<br/>4. 결과 저장]
                TemplateMgr[Template Manager<br/>템플릿 로드 및 매칭]
            end
            
            subgraph AI["AI Infrastructure"]
                GenAI[Generative AI<br/>StructureAnalyzer, StructureParser<br/>ExplanationGenerator, RAGRecommender]
                DL[Deep Learning<br/>LayoutAnalyzer, MathRecognizer]
            end
            
            DBInfra[Database Infrastructure<br/>SQLAlchemy ORM, Session 관리]
        end
    end
    
    Router --> Service
    Service --> Infra
    Infra --> Pipeline
    Infra --> GenAI
    Infra --> DBInfra
```

---

## 4. 데이터 흐름도

### 4.1 PDF 업로드 및 파싱 흐름

```mermaid
sequenceDiagram
    participant User as 사용자
    participant Frontend as Frontend<br/>(BookSelect.tsx)
    participant Router as Backend Router<br/>(books.py)
    participant Service as Book Service
    participant Pipeline as Unified Pipeline
    participant Storage as File System
    
    User->>Frontend: 1. PDF 업로드 요청
    Frontend->>Router: 2. POST /api/v1/books/upload
    Router->>Service: 3. upload_book()
    Service->>Service: 파일 저장
    Service->>Pipeline: 4. 파싱 파이프라인 시작 (백그라운드)
    
    Pipeline->>Pipeline: PDF 추출 (Extractors)
    Pipeline->>Pipeline: 템플릿 매칭 (TemplateManager)
    Pipeline->>Pipeline: 파싱 (HybridRouter)
    Pipeline->>Pipeline: 강의 콘텐츠 추출
    Pipeline->>Storage: 5. 결과 저장 (JSON, Images)
    
    Service-->>Router: 즉시 응답 (파싱 시작됨)
    Router-->>Frontend: 응답 반환
    Frontend-->>User: 업로드 완료
```

### 4.2 학습 데이터 조회 흐름

```mermaid
sequenceDiagram
    participant User as 사용자
    participant Frontend as Frontend<br/>(LiteratureLectures.tsx)
    participant Router as Backend Router<br/>(literature.py)
    participant Handler as Data File Handler
    participant Storage as File System
    
    User->>Frontend: 1. 강의 목록 조회 요청
    Frontend->>Router: 2. GET /api/v1/literature/lectures
    Router->>Handler: 3. 파일 시스템 조회
    Handler->>Storage: 4. lectures.json 읽기
    Storage-->>Handler: JSON 데이터
    Handler-->>Router: 파싱된 데이터
    Router-->>Frontend: 5. 응답 반환
    Frontend->>Frontend: 상태 관리 (bookStore)
    Frontend-->>User: 데이터 표시
```

### 4.3 AI 질의응답 흐름

```mermaid
sequenceDiagram
    participant User as 사용자
    participant Frontend as Frontend<br/>(AIQuestionInput.tsx)
    participant Router as Backend Router<br/>(ai.py)
    participant AIService as AI Infrastructure<br/>(explanation_generator.py)
    participant OpenAI as OpenAI API<br/>(GPT-4o-mini)
    
    User->>Frontend: 1. 질문 입력
    Frontend->>Frontend: 컨텍스트 수집 (현재 페이지 텍스트)
    Frontend->>Router: 2. POST /api/v1/ai/ask
    Router->>AIService: 3. AI Service 호출
    AIService->>AIService: 프롬프트 구성
    AIService->>OpenAI: 4. OpenAI API 호출
    OpenAI-->>AIService: 답변 생성
    AIService-->>Router: 응답 반환
    Router-->>Frontend: 5. 답변 전달
    Frontend->>Frontend: TTS로 음성 출력 (선택)
    Frontend-->>User: 답변 표시
```

### 4.4 점자 변환 및 디스플레이 출력 흐름

```mermaid
sequenceDiagram
    participant User as 사용자
    participant Frontend as Frontend<br/>(UnitSwipe.tsx)
    participant Router as Backend Router<br/>(braille.py)
    participant Service as Korean Braille Service
    participant BLE as Braille Device Adapter
    participant Device as Orbit Reader 20
    
    User->>Frontend: 1. 텍스트 선택 또는 페이지 로드
    Frontend->>Router: 2. POST /api/braille/convert
    Router->>Service: 3. 점자 변환 서비스 호출
    Service->>Service: 한글 텍스트 → 점자 셀 배열 변환
    Service->>Service: 표준 한글점자규정 적용
    Service-->>Router: 4. 점자 데이터 반환
    Router-->>Frontend: 점자 셀 배열
    Frontend->>Frontend: 청크 단위 분할 (useBrailleBLE)
    Frontend->>BLE: 5. BLE 디바이스로 전송
    BLE->>Device: 6. Web Bluetooth API 통신
    Device-->>User: 점자 출력
```

---

## 5. 주요 컴포넌트 상세

### 5.1 PDF 파싱 파이프라인

```mermaid
flowchart TD
    PDF[PDF 파일]
    
    PDF --> Extractor[Extractor 선택]
    
    Extractor --> Pdfplumber[Pdfplumber Extractor<br/>텍스트 추출, 좌표 정보]
    Extractor --> OCR[OCR Extractor<br/>이미지 OCR, 레이아웃 분석]
    Extractor --> PyMuPDF[PyMuPDF Extractor<br/>이미지 추출, PDF 렌더링]
    
    Pdfplumber --> Data[텍스트 및 이미지 데이터<br/>페이지별 텍스트 블록<br/>이미지 좌표 및 데이터]
    OCR --> Data
    PyMuPDF --> Data
    
    Data --> TemplateMgr[Template Manager<br/>과목별 템플릿 자동 매칭<br/>파싱 규칙 로드]
    
    TemplateMgr --> HybridRouter[Hybrid Router Parser]
    
    HybridRouter --> TemplateParsing[Template 기반 파싱<br/>정규식 패턴 매칭<br/>구조 규칙 적용]
    HybridRouter --> AIParsing[AI 기반 파싱<br/>StructureAnalyzer 구조 분석<br/>StructureParser 목차 파싱]
    HybridRouter --> RuleParsing[Rule 기반 파싱<br/>폰트 크기 분석<br/>레이아웃 분석]
    
    TemplateParsing --> LearningUnits[분류된 단원 LearningUnit<br/>concept 개념<br/>passage 본문<br/>problem 문제]
    AIParsing --> LearningUnits
    RuleParsing --> LearningUnits
    
    LearningUnits --> LectureExtractor[Lecture Contents Extractor<br/>강의별 단원 그룹핑<br/>페이지 범위 계산]
    
    LectureExtractor --> ResultSaver[ResultSaver<br/>lectures.json 강의 목록<br/>lecture_*.json 강의별 상세]
    LectureExtractor --> ImageSaver[ImageSaver<br/>concepts_images/*.png<br/>content_images/*.png<br/>problems_images/*.png]
```

### 5.2 AI 통합 구조

```mermaid
graph TB
    subgraph AIInfra["AI Infrastructure"]
        subgraph GenAI["Generative AI (genai/)"]
            StructureAnalyzer[StructureAnalyzer<br/>PDF 구조 분석<br/>섹션 식별<br/>레이아웃 이해]
            StructureParser[StructureParser<br/>목차 텍스트 파싱<br/>강의 정보 추출<br/>페이지 번호 매칭]
            ExplanationGenerator[ExplanationGenerator<br/>개념 설명 생성<br/>본문 해석 생성<br/>문제 해설 생성]
            MetadataEnricher[MetadataEnricher<br/>메타데이터 보강<br/>키워드 추출<br/>난이도 추정]
            RAGRecommender[RAGRecommender<br/>RAG 기반 학습 추천<br/>유사 콘텐츠 추천]
        end
        
        subgraph DL["Deep Learning (dl/)"]
            LayoutAnalyzer[LayoutAnalyzer<br/>레이아웃 분석 선택적<br/>YOLO 모델 활용 향후]
            MathRecognizer[MathRecognizer<br/>수식 인식 선택적<br/>LaTeX 변환]
        end
    end
    
    subgraph External["외부 AI 서비스"]
        OpenAI[OpenAI API<br/>GPT-4o-mini 주로 사용<br/>GPT-4 고품질 요청 시]
        Anthropic[Anthropic API<br/>Claude 선택적]
    end
    
    GenAI -->|API 호출| OpenAI
    GenAI -->|API 호출| Anthropic
    DL -->|선택적 사용| External
```

### 5.3 점자 변환 시스템

```mermaid
flowchart TD
    Input[한글 텍스트 입력]
    
    Input --> Preprocess[1. 텍스트 전처리<br/>공백 정규화<br/>특수문자 처리]
    
    Preprocess --> JamoSplit[2. 한글 자모 분리<br/>초성, 중성, 종성 분리<br/>유니코드 기반 자모 추출]
    
    JamoSplit --> BrailleMapping[3. 점자 셀 매핑<br/>표준 한글점자규정 적용<br/>초성/중성/종성 점자 매핑]
    
    BrailleMapping --> Abbreviation[4. 약자 처리<br/>약자 규칙 적용]
    
    Abbreviation --> NumberEnglish[5. 숫자/영문 처리<br/>숫자 점자 변환<br/>영문 점자 변환]
    
    NumberEnglish --> Output[점자 셀 배열 출력<br/>[1,0,0,0,0,0], [1,1,0,0,1,0], ...]
    
    Output --> Frontend[Frontend useBrailleBLE.ts<br/>점자 데이터 수신<br/>청크 단위 분할]
    
    Frontend --> Adapter[Braille Device Adapter]
    
    Adapter --> OrbitReader[OrbitReaderAdapter<br/>Orbit Reader 20 전용 프로토콜]
    Adapter --> GenericBLE[GenericBLEAdapter<br/>일반 BLE 점자 디스플레이 지원]
    
    OrbitReader --> Hardware[하드웨어 디바이스<br/>Orbit Reader 20<br/>점자 출력]
    GenericBLE --> Hardware
```

---

## 기술 스택 요약

### Frontend
- **프레임워크**: React 18.2.0 + TypeScript 5.3.3
- **빌드 도구**: Vite 5.0.8
- **스타일링**: Tailwind CSS 3.3.6
- **상태 관리**: Zustand 4.4.7
- **라우팅**: React Router 6.20.0
- **브라우저 API**: Web Speech API, Web Bluetooth API

### Backend
- **프레임워크**: FastAPI 0.104.1
- **언어**: Python 3.11
- **ORM**: SQLAlchemy 2.0.23
- **검증**: Pydantic 2.12.5
- **PDF 처리**: pdfplumber, PyMuPDF, OCR
- **AI**: OpenAI API, Anthropic API, LangChain

### Database
- **개발**: SQLite
- **프로덕션**: PostgreSQL (향후)

### 배포
- **플랫폼**: Render
- **Frontend**: Static Site Hosting
- **Backend**: Web Service

---

**문서 작성 완료**
