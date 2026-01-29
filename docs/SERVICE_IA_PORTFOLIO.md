# 서비스 IA(Information Architecture) - 포트폴리오 버전

> 점그리 수능 도우미 서비스 정보 구조 및 사용자 플로우

**작성일**: 2026년 1월 28일  
**버전**: 2.0.0

---

## 1. 전체 네비게이션 흐름

```mermaid
flowchart TD
    A["홈 (/)<br/>앱 진입점"] --> B{진입 경로}
    B -->|교재| C["/books<br/>교재 선택"]
    B -->|강의| D["/lectures/:bookId<br/>강의 목록"]
    B -->|단원| E["/unit/:unitId<br/>단원 학습"]
    B -->|과목별| G{과목}
    B -->|관리| H["/admin<br/>관리자"]
    G -->|문학| I["/literature/lectures"]
    G -->|영어| J["/english/lectures"]
    G -->|수학1| K["/math1/lectures"]
    C --> D
    D --> E
    I --> L["/literature/lectures/:lectureId<br/>강의 상세"]
    J --> M["/english/lectures/:lectureId"]
    K --> N["/math1/lectures/:lectureId"]
    L --> E
    M --> E
    N --> E
    E -->|학습 완료| F["/summary<br/>학습 요약"]
    E -->|Q키 강제 종료| F
```

---

## 2. 학습 사용자 플로우

```mermaid
flowchart LR
    A["/books<br/>교재 목록"] --> B{교재 선택}
    B --> C["/lectures/:bookId<br/>강의 목록"]
    C --> D{강의 선택}
    D --> E["/unit/:unitId<br/>단원 학습"]
    E --> F[카드 스와이프<br/>다음/이전]
    E --> G[점자 출력]
    E --> H[TTS 음성]
    E --> I[AI 질의]
    E --> J[RAG 추천]
    E --> K[정답 확인]
    F --> E
    E -->|학습 완료| L["/summary<br/>학습 요약"]
    E -->|Q키 강제 종료| L
```

---

## 3. 단원 학습 화면 액션 플로우

```mermaid
flowchart TD
    A["/unit/:unitId<br/>단원 데이터 조회"] --> B{단원 타입}
    B -->|개념| C[개념 UI 렌더링]
    B -->|본문| D[본문 UI 렌더링]
    B -->|문제| E[문제 UI 렌더링]
    C --> F[카드 표시]
    D --> F
    E --> F
    F --> G{사용자 액션}
    G -->|스와이프| H[다음/이전 단원]
    G -->|점자| I[텍스트 → 점자 변환<br/>→ BLE 전송]
    G -->|TTS| J[텍스트 → TTS API<br/>→ 음성 출력]
    G -->|AI 질의| K[질문 입력 → API<br/>→ 답변 표시]
    G -->|RAG 추천| M[현재 텍스트 → Vector DB<br/>→ 유사 콘텐츠 표시]
    G -->|정답 확인| L[답안 입력 → 채점<br/>→ 결과 표시]
    G -->|Ctrl+F| N[검색어 입력<br/>→ 결과 하이라이트]
    G -->|특수문자| O["(가) ↔ ㈎<br/>자동 매칭"]
    G -->|수식 계산| P[수식 입력<br/>→ 계산 → 결과]
    G -->|음성 명령| Q[음성 입력<br/>→ 명령 인식 → 액션]
    G -->|학습 완료| R["/summary 이동"]
    G -->|Q키| R
    H --> A
```

---

## 4. 주요 페이지별 기능 플로우

### 4.1 홈 화면 (/)

```mermaid
flowchart TD
    A["홈 화면 (/)"] --> B[최근 강의 표시<br/>이어서 학습하기]
    A --> C[교재 선택 버튼<br/>→ /books]
    A --> D[과목별 바로가기<br/>문학/영어/수학1]
    A --> E[관리자 페이지 버튼<br/>→ /admin]
```

### 4.2 교재 선택 (/books)

```mermaid
flowchart LR
    A["/books<br/>진입"] --> B[API 호출<br/>교재 목록]
    B --> C[목록 렌더링]
    C --> D{사용자 액션}
    D -->|과목 필터| E[문학/영어/수학1<br/>필터링]
    E --> C
    D -->|교재 클릭| F["/lectures/:bookId<br/>강의 목록 이동"]
    D -->|업로드<br/>관리자| G[PDF 선택 → 업로드<br/>→ 파싱 시작]
```

### 4.3 강의 목록 (/lectures/:bookId)

```mermaid
flowchart TD
    A["/lectures/:bookId"] --> B[API 호출<br/>강의 목록]
    B --> C[강의 목록 렌더링]
    C --> D[학습 진도 표시]
    C --> E{강의 선택}
    E --> F["/unit/:unitId<br/>첫 번째 단원으로 이동]
```

### 4.4 단원 학습 (/unit/:unitId)

```mermaid
flowchart TD
    A["/unit/:unitId"] --> B[단원 데이터 조회]
    B --> C{단원 타입}
    C -->|CONCEPT| D[개념 UI]
    C -->|PASSAGE| E[본문 UI]
    C -->|QUESTION| F[문제 UI]
    D --> G[카드 스와이프 UI]
    E --> G
    F --> G
    G --> H[점자 출력]
    G --> I[TTS 음성]
    G --> J[AI 질의응답]
    G --> K[RAG 추천]
    G --> L[정답 확인]
    G --> M[텍스트 검색 Ctrl+F]
    G --> N[특수문자 변형]
    G --> O[수식 계산기]
    G --> P[음성 명령]
```

### 4.5 학습 요약 (/summary)

```mermaid
flowchart TD
    A["/summary<br/>학습 완료 후"] --> B[세션 통계 표시<br/>문제 수, 정답률, 시간]
    A --> C[전체 진도 표시<br/>퍼센트]
    A --> D[다음 강의로 이동]
    A --> E[홈으로 이동]
```

### 4.6 과목별 강의 진입 플로우

```mermaid
flowchart LR
    A{과목 선택} -->|문학| B["/literature/lectures"]
    A -->|영어| C["/english/lectures"]
    A -->|수학1| D["/math1/lectures"]
    B --> E[강의 목록 조회]
    C --> E
    D --> E
    E --> F[강의 클릭]
    F --> G["/.../lectures/:lectureId<br/>강의 상세"]
    G --> H{항목 클릭}
    H -->|개념/본문/문제| I["/unit/:unitId<br/>단원 학습"]
    H -->|AI 설명<br/>문학만| J[개념/본문/문제<br/>AI 설명 생성]
```

### 4.7 관리자 페이지 (/admin)

```mermaid
flowchart TD
    A["/admin<br/>관리자"] --> B{작업 유형}
    B -->|템플릿| C[템플릿 관리]
    B -->|교재 파싱| D[교재 업로드]
    C --> C1[목록 조회]
    C --> C2[AI 마법사<br/>생성]
    C --> C3[편집/삭제/테스트]
    D --> D1[PDF 업로드]
    D1 --> D2[과목/제목/연도<br/>정보 입력]
    D2 --> D3[템플릿 선택]
    D3 --> D4[파싱 시작]
    D4 --> D5[상태 API<br/>진행률 표시]
    D5 --> D6{결과}
    D6 -->|완료| D7[결과 검증]
    D6 -->|실패| D8[재실행]
    D7 --> D9{수정 필요?}
    D9 -->|예| D10[결과 수동 수정]
    D9 -->|아니오| D11[완료]
    D10 --> D11
```

---

## 5. AI 서비스 플로우

### 5.1 AI 질의응답 플로우

```mermaid
sequenceDiagram
    participant User as 사용자
    participant Frontend as Frontend<br/>(UnitSwipe.tsx)
    participant Router as Backend Router<br/>(ai.py)
    participant AIService as AI Service<br/>(explanation_generator.py)
    participant OpenAI as OpenAI API<br/>(GPT-4o-mini)
    
    User->>Frontend: 질문 입력
    Frontend->>Frontend: 컨텍스트 수집<br/>(현재 페이지 텍스트)
    Frontend->>Router: POST /api/v1/ai/ask
    Router->>AIService: 질문 + 컨텍스트 전달
    AIService->>AIService: 프롬프트 구성<br/>(Chain-of-Thought)
    AIService->>OpenAI: API 호출
    OpenAI-->>AIService: 답변 생성
    AIService-->>Router: 답변 반환
    Router-->>Frontend: 응답 전달
    Frontend->>Frontend: TTS로 음성 출력 (선택)
    Frontend-->>User: 답변 표시
```

### 5.2 RAG 추천 플로우

```mermaid
sequenceDiagram
    participant User as 사용자
    participant Frontend as Frontend<br/>(RAGRecommendationCard.tsx)
    participant Router as Backend Router<br/>(ai.py)
    participant RAGService as RAG Recommender<br/>(rag_recommender.py)
    participant VectorDB as Vector Database
    
    User->>Frontend: 현재 단원 텍스트
    Frontend->>Router: POST /api/v1/ai/recommend
    Router->>RAGService: 추천 요청<br/>(query, content_type)
    RAGService->>VectorDB: 유사 콘텐츠 검색<br/>(top_k=5)
    VectorDB-->>RAGService: 유사 콘텐츠 리스트
    RAGService->>RAGService: 점수 필터링<br/>(min_score=0.3)
    RAGService-->>Router: 추천 결과
    Router-->>Frontend: 추천 리스트
    Frontend-->>User: 유사 개념/문제/본문 표시
```

### 5.3 RAG 시스템 초기화 플로우

```mermaid
sequenceDiagram
    participant Admin as 관리자
    participant Frontend as Frontend<br/>(Admin.tsx)
    participant Router as Backend Router<br/>(ai.py)
    participant RAGService as RAG Recommender
    participant DB as Database
    
    Admin->>Frontend: 강의 선택
    Frontend->>Router: POST /api/v1/ai/recommend/initialize<br/>(lesson_id)
    Router->>DB: 강의 및 단원 조회
    DB-->>Router: Lesson + Units 데이터
    Router->>Router: 타입별 분류<br/>(concepts, problems, passages)
    Router->>RAGService: Vector DB에 추가
    RAGService->>RAGService: 임베딩 생성
    RAGService->>RAGService: Vector DB 저장
    RAGService-->>Router: 초기화 완료
    Router-->>Frontend: 성공 응답
    Frontend-->>Admin: 초기화 완료 메시지
```

---

## 6. 점자 변환 및 출력 플로우

```mermaid
sequenceDiagram
    participant User as 사용자
    participant Frontend as Frontend<br/>(UnitSwipe.tsx)
    participant Router as Backend Router<br/>(braille.py)
    participant Service as Korean Braille Service
    participant BLE as Braille Device Adapter
    participant Device as Orbit Reader 20
    
    User->>Frontend: 텍스트 선택 또는 페이지 로드
    Frontend->>Router: POST /api/braille/convert
    Router->>Service: 한글 텍스트 전달
    Service->>Service: 1. 텍스트 전처리
    Service->>Service: 2. 한글 자모 분리<br/>(초성, 중성, 종성)
    Service->>Service: 3. 점자 셀 매핑<br/>(표준 한글점자규정)
    Service->>Service: 4. 약자 처리
    Service->>Service: 5. 숫자/영문 처리
    Service-->>Router: 점자 셀 배열<br/>[1,0,0,0,0,0], ...
    Router-->>Frontend: 점자 데이터
    Frontend->>Frontend: 청크 단위 분할<br/>(useBrailleChunkReader)
    Frontend->>BLE: BLE 디바이스로 전송
    BLE->>Device: Web Bluetooth API 통신
    Device-->>User: 점자 출력
```

---

## 7. IA 구조 요약 (계층도)

```mermaid
flowchart TD
    ROOT["홈 (/)"] --> BOOKS["교재 선택<br/>/books"]
    ROOT --> LEC["강의 목록<br/>/lectures/:bookId"]
    ROOT --> UNIT["단원 학습<br/>/unit/:unitId"]
    ROOT --> SUBJ{과목별}
    ROOT --> ADMIN["관리자<br/>/admin"]
    
    BOOKS --> B1[목록 조회]
    BOOKS --> B2[과목 필터]
    BOOKS --> B3[교재 선택]
    BOOKS --> B4[업로드]
    
    LEC --> L1[목록 조회]
    LEC --> L2[강의 선택]
    LEC --> L3[진도 표시]
    
    UNIT --> U1[내용 표시]
    UNIT --> U2[카드 스와이프]
    UNIT --> U3[점자/TTS/AI/RAG/정답]
    UNIT --> U4[Ctrl+F·특수문자·수식·음성명령]
    UNIT -->|학습 완료<br/>또는 Q키| SUM["학습 요약<br/>/summary"]
    
    SUM --> S1[세션 통계]
    SUM --> S2[전체/과목별 진도]
    SUM --> S3[다음 강의/홈 이동]
    
    SUBJ --> LIT["문학<br/>/literature/lectures"]
    SUBJ --> ENG["영어<br/>/english/lectures"]
    SUBJ --> M1["수학1<br/>/math1/lectures"]
    
    LIT --> LITD["강의 상세<br/>:lectureId"]
    ENG --> ENGD["강의 상세<br/>:lectureId"]
    M1 --> M1D["강의 상세<br/>:lectureId"]
    
    LITD --> UNIT
    ENGD --> UNIT
    M1D --> UNIT
    
    ADMIN --> AD1[템플릿: 목록/생성/편집/삭제/테스트]
    ADMIN --> AD2[파싱: 업로드·정보·템플릿·시작/상태/검증/재실행/수정]
```

---

## 8. 주요 기능 매트릭스

| 페이지 | 경로 | 주요 기능 |
|--------|------|----------|
| 홈 | `/` | 최근 강의 표시, 교재 선택, 과목별 바로가기, 관리자 |
| 교재 선택 | `/books` | 교재 목록, 과목 필터, 교재 선택, 업로드 |
| 강의 목록 | `/lectures/:bookId` | 강의 목록, 강의 선택, 진도 표시 |
| 단원 학습 | `/unit/:unitId` | 카드 스와이프, 점자/TTS, AI 질의, RAG 추천, 정답 확인, 검색, 수식 계산 |
| 학습 요약 | `/summary` | 세션 통계, 진도 표시, 다음 강의 이동 |
| 문학 강의 | `/literature/lectures` | 강의 목록, 강의 상세, AI 설명 |
| 영어 강의 | `/english/lectures` | 강의 목록, 강의 상세 |
| 수학1 강의 | `/math1/lectures` | 강의 목록, 강의 상세 |
| 관리자 | `/admin` | 템플릿 관리, 교재 업로드/파싱 |

---

## 9. API 엔드포인트 요약

### 9.1 교재 관련
- `POST /api/v1/books/upload` - PDF 업로드
- `GET /api/v1/books` - 교재 목록
- `GET /api/v1/books/{book_id}` - 교재 상세
- `GET /api/v1/books/{book_id}/parse-status` - 파싱 상태

### 9.2 강의 관련
- `GET /api/v1/literature/lectures` - 문학 강의 목록
- `GET /api/v1/literature/lectures/{lecture_id}` - 문학 강의 상세
- `GET /api/v1/english/lectures` - 영어 강의 목록
- `GET /api/v1/math1/lectures` - 수학1 강의 목록

### 9.3 단원 관련
- `GET /api/v1/lessons/{lesson_id}/units` - 단원 목록
- `GET /api/v1/units/{unit_id}` - 단원 상세

### 9.4 AI 관련
- `POST /api/v1/ai/ask` - AI 질의응답
- `POST /api/v1/ai/recommend` - RAG 추천
- `POST /api/v1/ai/recommend/initialize` - RAG 시스템 초기화

### 9.5 점자 관련
- `POST /api/braille/convert` - 한글 → 점자 변환 (prefix: /api)

### 9.6 학습 진도 관련
- `POST /api/v1/progress` - 진도 기록
- `GET /api/v1/progress/continue` - 이어서 학습하기

### 9.7 관리자 관련
- `GET /api/v1/templates` - 템플릿 목록
- `POST /api/v1/templates/generate-from-toc` - AI 템플릿 생성
- `POST /api/v1/templates/{subject}/{name}/test` - 템플릿 테스트

---

**문서 작성 완료**
