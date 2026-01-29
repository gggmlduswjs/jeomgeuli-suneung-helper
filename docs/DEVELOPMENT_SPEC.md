# 점그리 수능 도우미 개발명세서

**작성일**: 2026년 1월 26일  
**버전**: 2.0.0  
**작성자**: 개발팀

---

## 목차

1. [개요](#1-개요)
2. [시스템 요구사항](#2-시스템-요구사항)
3. [기술 스택 및 아키텍처](#3-기술-스택-및-아키텍처)
4. [모듈별 개발 명세](#4-모듈별-개발-명세)
5. [데이터베이스 설계](#5-데이터베이스-설계)
6. [API 명세](#6-api-명세)
7. [보안 및 성능](#7-보안-및-성능)
8. [테스트 계획](#8-테스트-계획)

---

## 1. 개요

### 1.1 프로젝트 목적
시각장애 수험생의 학습권 실질적 보장을 위해 AI 기반 자동화 시스템을 통해 교재 점역 및 변환 과정을 혁신하고, 독립적 학습 환경을 구축

### 1.2 개발 범위
- Backend API 서버 개발
- Frontend 웹 애플리케이션 개발
- PDF 파싱 엔진 개발
- 점자 변환 시스템 개발
- AI 통합 및 학습 도우미 개발
- 하드웨어 연동 (BLE 점자 디스플레이)

### 1.3 개발 환경
- **OS**: Windows 10/11, Linux (배포 환경)
- **Python**: 3.11+
- **Node.js**: 18+
- **데이터베이스**: SQLite (개발), PostgreSQL (프로덕션)

---

## 2. 시스템 요구사항

### 2.1 기능 요구사항

#### FR-01: PDF 자동 파싱 시스템
- **FR-01-01**: PDF 교재 업로드 및 저장
- **FR-01-02**: 템플릿 기반 자동 구조 분석
- **FR-01-03**: AI 기반 목차 분석 및 강의 목록 추출
- **FR-01-04**: 개념, 본문, 문제 자동 분류
- **FR-01-05**: 이미지 자동 추출 및 저장
- **FR-01-06**: 파싱 결과 검증 및 후처리

#### FR-02: 점자 변환 시스템
- **FR-02-01**: 한글 텍스트를 표준 한글점자규정에 따라 변환
- **FR-02-02**: 초성, 중성, 종성 분리 및 점자 셀 매핑
- **FR-02-03**: 약자 및 문장 부호 처리
- **FR-02-04**: 숫자, 영문, 특수문자 변환

#### FR-03: 점자 디스플레이 연동
- **FR-03-01**: Web Bluetooth API를 통한 BLE 디바이스 연결
- **FR-03-02**: Orbit Reader 20 하드웨어 지원
- **FR-03-03**: 실시간 점자 출력
- **FR-03-04**: 청크 기반 긴 텍스트 처리

#### FR-04: AI 학습 도우미
- **FR-04-01**: 실시간 질의응답 (OpenAI GPT-4o-mini)
- **FR-04-02**: 컨텍스트 기반 맞춤형 답변
- **FR-04-03**: 개념, 본문, 문제에 대한 상세 설명 생성
- **FR-04-04**: 교육적 프롬프트 최적화

#### FR-05: 음성 인터페이스
- **FR-05-01**: Web Speech API 기반 음성 인식 (STT)
- **FR-05-02**: Web Speech API 기반 음성 합성 (TTS)
- **FR-05-03**: 음성 명령 시스템
- **FR-05-04**: 학습 콘텐츠 음성 읽기

#### FR-06: 학습 관리 시스템
- **FR-06-01**: 교재 및 강의 목록 관리
- **FR-06-02**: 학습 진도 자동 추적
- **FR-06-03**: 카드 스와이프 기반 학습 UI
- **FR-06-04**: 이어서 학습하기 기능

#### FR-07: 관리자 기능
- **FR-07-01**: AI 기반 템플릿 생성 마법사
- **FR-07-02**: 교재 업로드 및 파싱 관리
- **FR-07-03**: 템플릿 관리 및 편집
- **FR-07-04**: 파싱 결과 검증 및 수정

### 2.2 비기능 요구사항

#### NFR-01: 성능
- PDF 파싱 시간: 10분 이내 (300페이지 기준)
- API 응답 시간: 평균 200ms 이내
- 페이지 로딩 시간: 2초 이내

#### NFR-02: 접근성
- WCAG 2.1 AA 수준 준수
- 키보드 네비게이션 지원
- 스크린 리더 호환

#### NFR-03: 호환성
- Chrome, Edge 브라우저 지원
- 반응형 디자인 (모바일, 태블릿, 데스크톱)

#### NFR-04: 확장성
- 다양한 교재 유형 지원 가능한 구조
- 다양한 과목 지원 가능한 구조
- 다양한 점자 디스플레이 하드웨어 지원 가능한 구조

---

## 3. 기술 스택 및 아키텍처

### 3.1 기술 스택

#### Backend
- **프레임워크**: FastAPI 0.104.1
- **언어**: Python 3.11
- **ORM**: SQLAlchemy 2.0.23
- **검증**: Pydantic 2.12.5
- **PDF 처리**: pdfplumber 0.10.3, PyPDF2 3.0.1
- **AI/ML**: OpenAI API, Anthropic Claude, LangChain 1.2.7

#### Frontend
- **프레임워크**: React 18.2.0
- **언어**: TypeScript 5.3.3
- **빌드 도구**: Vite 5.0.8
- **스타일링**: Tailwind CSS 3.3.6
- **상태 관리**: Zustand 4.4.7
- **라우팅**: React Router 6.20.0

### 3.2 시스템 아키텍처

#### 레이어드 아키텍처

```
┌─────────────────────────────────────────┐
│         Presentation Layer              │
│         (Frontend - React)              │
└────────────────┬────────────────────────┘
                  │ HTTP/REST API
┌─────────────────▼───────────────────────┐
│         Application Layer                │
│         (Backend - FastAPI)             │
│  ┌──────────┐  ┌──────────┐            │
│  │ Routers  │  │ Services │            │
│  └──────────┘  └──────────┘            │
└────────────────┬────────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Infrastructure Layer            │
│  ┌──────────┐  ┌──────────┐            │
│  │   PDF    │  │    AI    │            │
│  │  Parser  │  │  Engine  │            │
│  └──────────┘  └──────────┘            │
└────────────────┬────────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Data Layer                      │
│  ┌──────────┐  ┌──────────┐            │
│  │ Database │  │   File   │            │
│  │          │  │  System  │            │
│  └──────────┘  └──────────┘            │
└─────────────────────────────────────────┘
```

---

## 4. 모듈별 개발 명세

### 4.1 모듈별 파일 구조

모듈별 파일 구조는 별도 문서로 정리되어 있습니다.

**참조 문서**: [모듈별 파일 구조](./MODULE_FILE_STRUCTURE.md)

본 문서에서는 각 모듈의 책임과 주요 기능에 대해 설명합니다.

### 4.2 Backend 모듈

#### 4.2.1 라우터 모듈 (`app/routers/`)

**책임**: RESTful API 엔드포인트 정의 및 요청/응답 처리

**주요 파일**:
- `ai.py`: AI 질의응답 API
- `books.py`: 교재 관리 API
- `braille.py`: 점자 변환 API
- `literature.py`: 문학 교재 데이터 API
- `english.py`: 영어 교재 데이터 API
- `math1.py`: 수학1 교재 데이터 API
- `templates.py`: 템플릿 관리 API
- `units.py`: 단원 관리 API

**개발 규칙**:
- 모든 엔드포인트는 Pydantic 모델로 요청/응답 검증
- 에러는 HTTPException으로 처리
- 로깅은 `logging` 모듈 사용

#### 4.2.2 서비스 모듈 (`app/services/`)

**책임**: 비즈니스 로직 구현

**주요 파일**:
- `korean_braille.py`: 한글 점자 변환 서비스
- `book_conversion.py`: 교재 데이터 변환 서비스
- `progress_tracker.py`: 학습 진도 추적 서비스

#### 4.2.3 인프라 모듈 (`app/infrastructure/`)

**책임**: 외부 시스템 통합 및 인프라 관리

**주요 모듈**:
- `pdf/`: PDF 파싱 파이프라인
  - `full_parsing/`: 전체 파싱 파이프라인
  - `parsers/`: 파서 구현
  - `postprocessors/`: 후처리 로직
- `ai/`: AI 통합
  - `genai/`: 생성형 AI 통합 (OpenAI, Anthropic)
  - `dl/`: 딥러닝 모델 (선택적)
- `database/`: 데이터베이스 세션 관리

#### 4.2.4 유틸리티 모듈 (`app/utils/`)

**책임**: 공통 유틸리티 함수

**주요 파일**:
- `ai_utils.py`: AI API 클라이언트 관리
- `env_loader.py`: 환경 변수 로드
- `id_generator.py`: ID 생성
- `pdf_tools.py`: PDF 처리 유틸리티

### 4.3 Frontend 모듈

#### 4.3.1 페이지 컴포넌트 (`src/pages/`)

**주요 페이지**:
- `Start.tsx`: 시작 페이지
- `BookSelect.tsx`: 교재 선택 페이지
- `UnitSwipe.tsx`: 단원 학습 페이지 (카드 스와이프)
- `Admin.tsx`: 관리자 페이지
- `LiteratureLectures.tsx`: 문학 강의 목록
- `LiteratureLectureDetail.tsx`: 문학 강의 상세
- `EnglishLectures.tsx`: 영어 강의 목록
- `EnglishLectureDetail.tsx`: 영어 강의 상세
- `Math1Lectures.tsx`: 수학1 강의 목록
- `Math1LectureDetail.tsx`: 수학1 강의 상세

#### 4.3.2 컴포넌트 (`src/components/`)

**주요 컴포넌트**:
- `braille/`: 점자 관련 컴포넌트
- `voice/`: 음성 인터페이스 컴포넌트
- `unit/`: 학습 단위 컴포넌트
- `admin/`: 관리자 컴포넌트
- `ai/`: AI 관련 컴포넌트

#### 4.3.3 커스텀 Hooks (`src/hooks/`)

**주요 Hooks**:
- `useBrailleBLE.ts`: 점자 디스플레이 BLE 연동
- `useAILearningAssistant.ts`: AI 학습 도우미
- `useTTS.ts`: 음성 합성
- `useSTT.ts`: 음성 인식
- `useUnitData.ts`: 단원 데이터 관리

#### 4.3.4 서비스 (`src/services/`)

**주요 서비스**:
- `api/client.ts`: API 클라이언트
- `ai/index.ts`: AI 서비스
- `voice/index.ts`: 음성 서비스

#### 4.3.5 상태 관리 (`src/store/`)

**주요 스토어**:
- `bookStore.ts`: 교재 및 강의 목록
- `progressStore.ts`: 학습 진도
- `lessonStore.ts`: 현재 학습 중인 강의
- `voice.ts`: 음성 인터페이스 상태

---

## 5. 데이터베이스 설계

### 5.1 데이터 모델

#### Book (교재)
```python
class Book:
    id: str (PK)
    title: str
    subject: Subject (enum)
    year: int
    parse_status: ParseStatus (enum)
    created_at: datetime
    updated_at: datetime
```

#### Curriculum (커리큘럼)
```python
class Curriculum:
    id: str (PK)
    book_id: str (FK)
    status: CurriculumStatus (enum)
    created_at: datetime
```

#### Lesson (강의)
```python
class Lesson:
    id: str (PK)
    curriculum_id: str (FK)
    lecture_id: int
    title: str
    page_start: int
    page_end: int
    order: int
```

#### Unit (단원)
```python
class Unit:
    id: str (PK)
    lesson_id: str (FK)
    type: UnitType (enum)
    content: str
    page_num: int
    order: int
```

#### Template (템플릿)
```python
class Template:
    id: str (PK)
    name: str
    subject: str
    version: str
    config: dict (JSON)
    created_at: datetime
```

### 5.2 데이터 저장 방식

#### 구조화된 데이터
- **형식**: JSON 파일
- **위치**: `backend/data/{subject}/{book_id}/`
- **파일 구조**:
  ```
  data/
  ├── literature/
  │   └── {book_id}/
  │       ├── lectures/
  │       │   ├── lectures.json
  │       │   └── lecture_01.json
  │       ├── concepts_images/
  │       ├── content_images/
  │       └── problems_images/
  └── english/
      └── {book_id}/
  ```

#### 이미지 데이터
- **형식**: PNG 파일
- **위치**: `backend/data/{subject}/{book_id}/{type}_images/`
- **명명 규칙**: `{type}_p{page}_{id}.png`

#### 템플릿 데이터
- **형식**: JSON 파일
- **위치**: `backend/data/templates/`
- **명명 규칙**: `{subject}_{name}_{version}.json`

---

## 6. API 명세

### 6.1 학습 관련 API

#### GET /api/v1/books
**설명**: 교재 목록 조회

**응답**:
```json
[
  {
    "id": "book_123",
    "title": "EBS 수능특강 문학",
    "subject": "literature",
    "year": 2026,
    "parse_status": "completed"
  }
]
```

#### GET /api/v1/lectures
**설명**: 강의 목록 조회

**쿼리 파라미터**:
- `subject`: 과목 (literature, english, math1)
- `book_id`: 교재 ID (선택)

**응답**:
```json
[
  {
    "lecture_id": 1,
    "title": "1강 | 고전 시가"
  }
]
```

#### GET /api/v1/units/{unit_id}
**설명**: 단원 상세 정보 조회

**응답**:
```json
{
  "id": "unit_123",
  "type": "concept",
  "content": "개념 내용 텍스트...",
  "page_num": 10,
  "order": 1,
  "images": [
    "/api/data/literature/book_123/concepts_images/concept_p10_01.png"
  ],
  "lesson_id": "lesson_123"
}
```

---

## 7. 보안 및 성능

### 7.1 보안

#### API 키 관리
- 환경 변수를 통한 안전한 관리
- `.env` 파일은 Git에 커밋하지 않음
- 프로덕션 환경에서는 환경 변수로 설정

#### 입력 검증
- Pydantic을 통한 모든 요청 데이터 검증
- 파일 업로드 크기 제한 (예: 100MB)
- 파일 형식 검증 (PDF만 허용)

#### CORS 설정
- 허용된 도메인만 접근 가능
- 개발 환경: `http://localhost:5173`
- 프로덕션 환경: 실제 도메인

### 7.2 성능 최적화

#### 비동기 처리
- FastAPI 비동기 엔드포인트 활용
- PDF 파싱은 Background Tasks로 처리
- AI API 호출은 비동기로 처리

#### 스트리밍 처리
- 대용량 PDF 페이지별 처리
- 메모리 효율적인 이미지 처리
- 진행 상황 추적 및 재시작 기능

#### 캐싱 전략
- 파싱 결과 캐싱 (향후 구현)
- AI 응답 캐싱 (향후 구현)
- 정적 파일 CDN 배포 (향후 구현)

---

## 8. 테스트 계획

### 8.1 단위 테스트
- 각 모듈별 단위 테스트 작성
- 핵심 비즈니스 로직 테스트
- 유틸리티 함수 테스트

### 8.2 통합 테스트
- API 엔드포인트 통합 테스트
- PDF 파싱 파이프라인 테스트
- 점자 변환 시스템 테스트

### 8.3 E2E 테스트
- 주요 사용자 시나리오 테스트
- Playwright를 활용한 브라우저 자동화 테스트

---

## 9. 배포 및 운영

### 9.1 배포 환경
- **플랫폼**: Render
- **Backend**: Python 3.11 환경
- **Frontend**: Node.js 18+ 환경

### 9.2 환경 변수
```env
# Backend
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=sqlite:///./data.db

# Frontend
VITE_API_BASE_URL=https://api.example.com
```

### 9.3 모니터링
- 로깅: Python `logging` 모듈
- 에러 추적: (향후 구현)
- 성능 모니터링: (향후 구현)

---

**개발명세서 작성 완료**

---

## 5. 데이터베이스 설계

### 5.1 데이터 모델

#### Book (교재)
```python
class Book:
    id: str (PK)
    title: str
    subject: Subject (enum)
    year: int
    parse_status: ParseStatus (enum)
    created_at: datetime
    updated_at: datetime
```

#### Curriculum (커리큘럼)
```python
class Curriculum:
    id: str (PK)
    book_id: str (FK)
    status: CurriculumStatus (enum)
    created_at: datetime
```

#### Lesson (강의)
```python
class Lesson:
    id: str (PK)
    curriculum_id: str (FK)
    lecture_id: int
    title: str
    page_start: int
    page_end: int
    order: int
```

#### Unit (단원)
```python
class Unit:
    id: str (PK)
    lesson_id: str (FK)
    type: UnitType (enum)
    content: str
    page_num: int
    order: int
```

#### Template (템플릿)
```python
class Template:
    id: str (PK)
    name: str
    subject: str
    version: str
    config: dict (JSON)
    created_at: datetime
```

### 5.2 데이터 저장 방식

#### 구조화된 데이터
- **형식**: JSON 파일
- **위치**: `backend/data/{subject}/{book_id}/`
- **파일 구조**:
  ```
  data/
  ├── literature/
  │   └── {book_id}/
  │       ├── lectures/
  │       │   ├── lectures.json
  │       │   └── lecture_01.json
  │       ├── concepts_images/
  │       ├── content_images/
  │       └── problems_images/
  └── english/
      └── {book_id}/
  ```

#### 이미지 데이터
- **형식**: PNG 파일
- **위치**: `backend/data/{subject}/{book_id}/{type}_images/`
- **명명 규칙**: `{type}_p{page}_{id}.png`

#### 템플릿 데이터
- **형식**: JSON 파일
- **위치**: `backend/data/templates/`
- **명명 규칙**: `{subject}_{name}_{version}.json`

---

## 6. API 명세

### 6.1 학습 관련 API

#### GET /api/v1/books
**설명**: 교재 목록 조회

**응답**:
```json
[
  {
    "id": "book_123",
    "title": "EBS 수능특강 문학",
    "subject": "literature",
    "year": 2026,
    "parse_status": "completed"
  }
]
```

#### GET /api/v1/lectures
**설명**: 강의 목록 조회

**쿼리 파라미터**:
- `subject`: 과목 (literature, english, math1)
- `book_id`: 교재 ID (선택)

**응답**:
```json
[
  {
    "lecture_id": 1,
    "title": "1강 | 고전 시가"
  }
]
```

#### GET /api/v1/units/{unit_id}
**설명**: 단원 상세 정보 조회

**응답**:
```json
{
  "id": "unit_123",
  "type": "concept",
  "content": "개념 내용...",
  "page_num": 10,
  "images": ["concept_p10_01.png"]
}
```

### 6.2 AI 관련 API

#### POST /api/v1/ai/ask
**설명**: AI 질의응답

**요청**:
```json
{
  "question": "이 개념을 설명해주세요",
  "context": "현재 학습 중인 페이지 텍스트",
  "page_num": 10
}
```

**응답**:
```json
{
  "answer": "AI 답변 내용...",
  "confidence": 0.9
}
```

#### POST /api/v1/literature/explain-concept
**설명**: 개념 설명 생성

**요청**:
```json
{
  "concept_id": "concept_123",
  "lecture_id": 1
}
```

**응답**:
```json
{
  "explanation": "상세한 개념 설명...",
  "examples": ["예시 1", "예시 2"]
}
```

### 6.3 점자 관련 API

#### POST /api/braille/convert
**설명**: 텍스트를 점자로 변환

**요청**:
```json
{
  "text": "안녕하세요"
}
```

**응답**:
```json
{
  "cells": [
    [1, 0, 0, 0, 0, 0],  // 안
    [1, 1, 0, 0, 1, 0],  // 녕
    [0, 0, 0, 0, 0, 0],  // 하
    [1, 0, 1, 0, 0, 0],  // 세
    [1, 1, 0, 0, 0, 0]   // 요
  ]
}
```

### 6.4 관리자 관련 API

#### POST /api/v1/templates/generate
**설명**: 템플릿 생성

**요청**:
```json
{
  "subject": "literature",
  "name": "ebs_수능특강_literature_2026",
  "toc_text": "목차 텍스트...",
  "toc_lecture_line_examples": ["1강 | 고전 시가 009", "2강 | 고전 산문 012"],
  "save": true
}
```

**응답**:
```json
{
  "template_id": "template_123",
  "name": "ebs_수능특강_literature_2026",
  "confidence": 0.85,
  "lectures": [
    {"lecture_id": 1, "title": "1강 | 고전 시가", "page": 9}
  ]
}
```

#### POST /api/v1/books/upload
**설명**: 교재 업로드 및 파싱

**요청**:
- `file`: PDF 파일 (multipart/form-data)
- `subject`: 과목
- `template_id`: 템플릿 ID (선택)

**응답**:
```json
{
  "book_id": "book_123",
  "status": "parsing",
  "message": "파싱이 시작되었습니다."
}
```

---

## 7. 보안 및 성능

### 7.1 보안

#### API 키 관리
- 환경 변수를 통한 안전한 관리
- `.env` 파일은 Git에 커밋하지 않음
- 프로덕션 환경에서는 환경 변수로 설정

#### 입력 검증
- Pydantic을 통한 모든 요청 데이터 검증
- 파일 업로드 크기 제한 (예: 100MB)
- 파일 형식 검증 (PDF만 허용)

#### CORS 설정
- 허용된 도메인만 접근 가능
- 개발 환경: `http://localhost:5173`
- 프로덕션 환경: 실제 도메인

### 7.2 성능 최적화

#### 비동기 처리
- FastAPI 비동기 엔드포인트 활용
- PDF 파싱은 Background Tasks로 처리
- AI API 호출은 비동기로 처리

#### 스트리밍 처리
- 대용량 PDF 페이지별 처리
- 메모리 효율적인 이미지 처리
- 진행 상황 추적 및 재시작 기능

#### 캐싱 전략
- 파싱 결과 캐싱 (향후 구현)
- AI 응답 캐싱 (향후 구현)
- 정적 파일 CDN 배포 (향후 구현)

---

## 8. 테스트 계획

### 8.1 단위 테스트
- 각 모듈별 단위 테스트 작성
- 핵심 비즈니스 로직 테스트
- 유틸리티 함수 테스트

### 8.2 통합 테스트
- API 엔드포인트 통합 테스트
- PDF 파싱 파이프라인 테스트
- 점자 변환 시스템 테스트

### 8.3 E2E 테스트
- 주요 사용자 시나리오 테스트
- Playwright를 활용한 브라우저 자동화 테스트

---

## 9. 배포 및 운영

### 9.1 배포 환경
- **플랫폼**: Render
- **Backend**: Python 3.11 환경
- **Frontend**: Node.js 18+ 환경

### 9.2 환경 변수
```env
# Backend
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=sqlite:///./data.db

# Frontend
VITE_API_BASE_URL=https://api.example.com
```

### 9.3 모니터링
- 로깅: Python `logging` 모듈
- 에러 추적: (향후 구현)
- 성능 모니터링: (향후 구현)

---

**개발명세서 작성 완료**
