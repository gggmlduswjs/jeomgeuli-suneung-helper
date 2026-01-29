# 점그리 수능 도우미 API 명세서

**작성일**: 2026년 1월 26일  
**버전**: 2.1.0 (리팩토링 반영)  
**Base URL**: `http://localhost:8000` (개발), `https://api.example.com` (프로덕션)  
**최종 수정**: 2026년 1월 26일 (라우터/서비스 레이어 분리 반영)

---

## 목차

1. [개요](#1-개요)
2. [인증](#2-인증)
3. [공통 응답 형식](#3-공통-응답-형식)
4. [학습 관련 API](#4-학습-관련-api)
5. [AI 관련 API](#5-ai-관련-api)
6. [점자 관련 API](#6-점자-관련-api)
7. [관리자 관련 API](#7-관리자-관련-api)
8. [에러 코드](#8-에러-코드)
9. [백엔드 아키텍처](#9-백엔드-아키텍처-리팩토링-반영)
10. [데이터 형식](#10-데이터-형식)
11. [Rate Limiting](#11-rate-limiting)
12. [API 버전 관리](#12-api-버전-관리)

---

## 1. 개요

### 1.1 API 기본 정보
- **프로토콜**: HTTP/HTTPS
- **데이터 형식**: JSON
- **문자 인코딩**: UTF-8
- **API 버전**: v1

### 1.2 Base URL
```
개발 환경: http://localhost:8000
프로덕션 환경: https://api.example.com
```

### 1.3 Swagger UI
```
http://localhost:8000/docs
```

---

## 2. 인증

현재 버전에서는 인증이 필요하지 않습니다. (향후 구현 예정)

---

## 3. 공통 응답 형식

### 3.1 성공 응답
```json
{
  "data": { ... },
  "message": "성공 메시지"
}
```

### 3.2 에러 응답
```json
{
  "detail": "에러 메시지",
  "error_code": "ERROR_CODE"
}
```

---

## 4. 학습 관련 API

### 4.1 교재 목록 조회

**엔드포인트**: `GET /api/v1/books`

**설명**: 등록된 교재 목록을 조회합니다.

**요청 파라미터**: 없음

**응답**:
```json
[
  {
    "id": "book_123",
    "title": "EBS 수능특강 문학",
    "subject": "literature",
    "year": 2026,
    "parse_status": "completed",
    "created_at": "2026-01-01T00:00:00Z"
  }
]
```

**응답 필드**:
- `id` (string): 교재 ID
- `title` (string): 교재명
- `subject` (string): 과목 (literature, english, math1)
- `year` (integer): 연도
- `parse_status` (string): 파싱 상태 (pending, parsing, completed, failed)
- `created_at` (string): 생성일시 (ISO 8601)

---

### 4.2 강의 목록 조회

**엔드포인트**: `GET /api/v1/lectures`

**설명**: 강의 목록을 조회합니다.

**쿼리 파라미터**:
- `subject` (string, 선택): 과목 필터 (literature, english, math1)
- `book_id` (string, 선택): 교재 ID 필터

**응답**:
```json
[
  {
    "lecture_id": 1,
    "title": "1강 | 고전 시가",
    "page_start": 9,
    "page_end": 15,
    "book_id": "book_123"
  }
]
```

**응답 필드**:
- `lecture_id` (integer): 강의 ID
- `title` (string): 강의 제목
- `page_start` (integer): 시작 페이지
- `page_end` (integer): 종료 페이지
- `book_id` (string): 교재 ID

---

### 4.3 단원 상세 조회

**엔드포인트**: `GET /api/v1/units/{unit_id}`

**설명**: 단원 상세 정보를 조회합니다.

**경로 파라미터**:
- `unit_id` (string, 필수): 단원 ID

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

**응답 필드**:
- `id` (string): 단원 ID
- `type` (string): 단원 타입 (concept, passage, problem)
- `content` (string): 단원 내용
- `page_num` (integer): 페이지 번호
- `order` (integer): 순서
- `images` (array[string]): 이미지 URL 목록
- `lesson_id` (string): 강의 ID

---

### 4.4 문학 강의 목록 조회

**엔드포인트**: `GET /api/v1/literature/lectures`

**설명**: 문학 강의 목록을 조회합니다.

**응답**:
```json
[
  {
    "lecture_id": 1,
    "title": "1강 | 고전 시가"
  }
]
```

---

### 4.5 문학 강의 상세 조회

**엔드포인트**: `GET /api/v1/literature/lectures/{lecture_id}`

**설명**: 문학 강의 상세 정보를 조회합니다.

**경로 파라미터**:
- `lecture_id` (integer, 필수): 강의 ID

**응답**:
```json
{
  "lecture_id": 1,
  "title": "1강 | 고전 시가",
  "concepts": [
    {
      "id": "concept_123",
      "title": "고전 시가의 이해",
      "content": "...",
      "page_num": 10
    }
  ],
  "passages": [
    {
      "id": "passage_123",
      "title": "작품 제목",
      "content": "...",
      "page_num": 11
    }
  ],
  "problems": [
    {
      "id": "problem_123",
      "content": "문제 내용...",
      "page_num": 12
    }
  ]
}
```

---

### 4.6 문학 문제 목록 조회

**엔드포인트**: `GET /api/v1/literature/problems`

**설명**: 문학 문제 목록을 조회합니다.

**응답**:
```json
[
  {
    "id": "problem_p12_01",
    "content": "문제 내용...",
    "page_num": 12,
    "images": ["problem_p12_01.png"]
  }
]
```

---

### 4.7 문학 문제 상세 조회

**엔드포인트**: `GET /api/v1/literature/problems/{problem_id}`

**설명**: 문학 문제 상세 정보를 조회합니다.

**경로 파라미터**:
- `problem_id` (string, 필수): 문제 ID

**응답**:
```json
{
  "id": "problem_p12_01",
  "content": "문제 내용...",
  "page_num": 12,
  "images": ["problem_p12_01.png"],
  "options": ["①", "②", "③", "④", "⑤"],
  "answer": "①"
}
```

---

## 5. AI 관련 API

### 5.1 AI 질의응답

**엔드포인트**: `POST /api/v1/ai/ask`

**설명**: AI 튜터에게 질문하고 답변을 받습니다.

**요청 본문**:
```json
{
  "question": "이 개념을 설명해주세요",
  "context": "현재 학습 중인 페이지 텍스트 (선택)",
  "page_num": 10
}
```

**요청 필드**:
- `question` (string, 필수): 질문 내용
- `context` (string, 선택): 컨텍스트 텍스트
- `page_num` (integer, 선택): 페이지 번호

**응답**:
```json
{
  "answer": "이 개념은 다음과 같이 설명할 수 있습니다...",
  "confidence": 0.9
}
```

**응답 필드**:
- `answer` (string): AI 답변
- `confidence` (float): 신뢰도 (0.0 ~ 1.0)

**에러 응답**:
- `500`: AI 응답 생성 실패

---

### 5.2 개념 설명 생성

**엔드포인트**: `POST /api/v1/literature/explain-concept`

**설명**: 문학 개념에 대한 상세 설명을 생성합니다.

**요청 본문**:
```json
{
  "concept_id": "concept_123",
  "lecture_id": 1
}
```

**응답**:
```json
{
  "explanation": "이 개념은 다음과 같이 이해할 수 있습니다...",
  "examples": ["예시 1", "예시 2"],
  "key_points": ["핵심 포인트 1", "핵심 포인트 2"]
}
```

---

### 5.3 본문 설명 생성

**엔드포인트**: `POST /api/v1/literature/explain-content`

**설명**: 문학 본문(작품)에 대한 상세 설명을 생성합니다.

**요청 본문**:
```json
{
  "content_id": "content_123",
  "lecture_id": 1
}
```

**응답**:
```json
{
  "explanation": "이 작품은 다음과 같은 특징을 가지고 있습니다...",
  "theme": "주제",
  "literary_devices": ["수사법 1", "수사법 2"]
}
```

---

### 5.4 문제 설명 생성

**엔드포인트**: `POST /api/v1/literature/explain-problem`

**설명**: 문학 문제에 대한 상세 설명 및 해설을 생성합니다.

**요청 본문**:
```json
{
  "problem_id": "problem_123",
  "lecture_id": 1
}
```

**응답**:
```json
{
  "explanation": "이 문제는 다음과 같이 해결할 수 있습니다...",
  "answer": "①",
  "reasoning": "정답인 이유는...",
  "distractor_analysis": {
    "②": "이 선택지는...",
    "③": "이 선택지는..."
  }
}
```

---

## 6. 점자 관련 API

### 6.1 텍스트를 점자로 변환

**엔드포인트**: `POST /api/braille/convert`

**설명**: 한글 텍스트를 표준 한글점자규정에 따라 점자 셀 배열로 변환합니다.

**요청 본문**:
```json
{
  "text": "안녕하세요"
}
```

**요청 필드**:
- `text` (string, 필수): 변환할 텍스트

**응답**:
```json
{
  "cells": [
    [1, 0, 0, 0, 0, 0],  // 안 (초성 ㅇ, 중성 ㅏ, 종성 ㄴ)
    [1, 1, 0, 0, 1, 0],  // 녕 (초성 ㄴ, 중성 ㅕ, 종성 ㅇ)
    [0, 0, 0, 0, 0, 0],  // 하 (초성 ㅎ, 중성 ㅏ)
    [1, 0, 1, 0, 0, 0],  // 세 (초성 ㅅ, 중성 ㅔ)
    [1, 1, 0, 0, 0, 0]   // 요 (초성 ㅇ, 중성 ㅛ)
  ]
}
```

**응답 필드**:
- `cells` (array[array[integer]]): 점자 셀 배열
  - 각 셀은 6개 점의 배열 [점1, 점2, 점3, 점4, 점5, 점6]
  - 점이 올라오면 1, 내려가면 0

**에러 응답**:
- `500`: 점자 변환 실패

---

## 7. 관리자 관련 API

### 7.1 템플릿 생성

**엔드포인트**: `POST /api/v1/templates/generate`

**설명**: AI를 활용하여 파싱 템플릿을 자동 생성합니다.

**요청 본문**:
```json
{
  "subject": "literature",
  "name": "ebs_수능특강_literature_2026",
  "version": "2026",
  "description": "EBS 수능특강 문학 2026 템플릿",
  "year": 2026,
  "book_name": "EBS 수능특강 문학",
  "toc_text": "목차 텍스트 원문...",
  "toc_lecture_line_examples": [
    "1강 | 고전 시가 009",
    "2강 | 고전 산문 012"
  ],
  "toc_nonlecture_line_examples": [
    "목차",
    "제1부 고전 문학"
  ],
  "expected_lecture_count": 20,
  "save": true,
  "model_name": "gpt-4o-mini",
  "confidence": 0.85
}
```

**요청 필드**:
- `subject` (string, 필수): 과목 (literature, english, math1)
- `name` (string, 필수): 템플릿 이름
- `version` (string, 선택): 템플릿 버전
- `description` (string, 선택): 템플릿 설명
- `year` (integer, 선택): 교재 연도
- `book_name` (string, 선택): 교재 이름
- `toc_text` (string, 필수): 목차 텍스트 원문
- `toc_lecture_line_examples` (array[string], 선택): 강의 줄 예시
- `toc_nonlecture_line_examples` (array[string], 선택): 비강의 줄 예시
- `expected_lecture_count` (integer, 선택): 기대 강의 개수
- `save` (boolean, 선택): 생성 후 저장 여부
- `model_name` (string, 선택): 사용할 AI 모델
- `confidence` (float, 선택): 템플릿 신뢰도

**응답**:
```json
{
  "template_id": "template_123",
  "name": "ebs_수능특강_literature_2026",
  "subject": "literature",
  "version": "2026",
  "confidence": 0.85,
  "lectures": [
    {
      "lecture_id": 1,
      "title": "1강 | 고전 시가",
      "page": 9
    }
  ],
  "toc_lecture_patterns": [
    "^(\\d+)강\\s*\\|\\s*(.+?)\\s+(\\d{3})$"
  ]
}
```

---

### 7.2 교재 업로드 및 파싱

**엔드포인트**: `POST /api/v1/books/upload`

**설명**: PDF 교재를 업로드하고 파싱을 시작합니다.

**요청 형식**: `multipart/form-data`

**요청 필드**:
- `file` (file, 필수): PDF 파일
- `subject` (string, 필수): 과목 (literature, english, math1)
- `template_id` (string, 선택): 사용할 템플릿 ID
- `title` (string, 선택): 교재 제목

**응답**:
```json
{
  "book_id": "book_123",
  "status": "parsing",
  "message": "파싱이 시작되었습니다.",
  "estimated_time": 600
}
```

**응답 필드**:
- `book_id` (string): 교재 ID
- `status` (string): 파싱 상태 (parsing, completed, failed)
- `message` (string): 상태 메시지
- `estimated_time` (integer): 예상 소요 시간 (초)

---

### 7.3 템플릿 목록 조회

**엔드포인트**: `GET /api/v1/templates`

**설명**: 등록된 템플릿 목록을 조회합니다.

**쿼리 파라미터**:
- `subject` (string, 선택): 과목 필터

**응답**:
```json
[
  {
    "id": "template_123",
    "name": "ebs_수능특강_literature_2026",
    "subject": "literature",
    "version": "2026",
    "confidence": 0.85,
    "created_at": "2026-01-01T00:00:00Z"
  }
]
```

---

### 7.4 템플릿 상세 조회

**엔드포인트**: `GET /api/v1/templates/{template_id}`

**설명**: 템플릿 상세 정보를 조회합니다.

**경로 파라미터**:
- `template_id` (string, 필수): 템플릿 ID

**응답**:
```json
{
  "id": "template_123",
  "name": "ebs_수능특강_literature_2026",
  "subject": "literature",
  "version": "2026",
  "config": {
    "toc_lecture_patterns": ["^(\\d+)강\\s*\\|\\s*(.+?)\\s+(\\d{3})$"],
    "section_patterns": { ... },
    "problem_patterns": { ... }
  },
  "created_at": "2026-01-01T00:00:00Z"
}
```

---

## 8. 에러 코드

---

## 9. 백엔드 아키텍처 (리팩토링 반영)

### 9.1 레이어 구조

```
Router Layer (app.routers)
    ↓
Service Layer (app.services)
    ↓
Infrastructure Layer (app.infrastructure)
```

### 9.2 주요 라우터 파일

- `books.py`: 교재 관리 API (업로드, 목록 조회, 파싱 상태 등)
- `curriculum.py`: 커리큘럼 관리 API
- `templates.py`: 템플릿 관리 API
- `lessons.py`: 강의 관리 API
- `units.py`: 단원 관리 API
- `literature.py`: 문학 교재 데이터 API
- `english.py`: 영어 교재 데이터 API
- `math1.py`: 수학1 교재 데이터 API
- `ai.py`: AI 질의응답 API
- `braille.py`: 점자 변환 API

### 9.3 주요 서비스 파일

- `book_service.py`: 교재 처리 서비스 (PDF 파이프라인 실행, 백그라운드 작업)
- `curriculum_service.py`: 커리큘럼 생성 서비스 (파이프라인 결과를 커리큘럼으로 변환)
- `template_service.py`: 템플릿 관리 서비스 (템플릿 생성, 수정, 삭제 등의 비즈니스 로직)
- `book_conversion.py`: 교재 데이터 변환 서비스 (LearningUnit → Unit 변환)
- `korean_braille.py`: 한글 점자 변환 서비스
- `progress_tracker.py`: 학습 진도 추적 서비스

### 9.4 리팩토링 원칙

- **Router Layer**: HTTP 요청/응답 처리만 담당, 비즈니스 로직은 서비스로 위임
- **Service Layer**: 비즈니스 로직, 데이터 처리, 파이프라인 실행 담당
- **로깅**: 모든 `print` 문을 `logger`로 변경하여 표준화

---

### 9.1 레이어 구조

```
Router Layer (app.routers)
    ↓
Service Layer (app.services)
    ↓
Infrastructure Layer (app.infrastructure)
```

### 9.2 주요 라우터 파일

- `books.py`: 교재 관리 API (업로드, 목록 조회, 파싱 상태 등)
- `curriculum.py`: 커리큘럼 관리 API
- `templates.py`: 템플릿 관리 API
- `lessons.py`: 강의 관리 API
- `units.py`: 단원 관리 API
- `literature.py`: 문학 교재 데이터 API
- `english.py`: 영어 교재 데이터 API
- `math1.py`: 수학1 교재 데이터 API
- `ai.py`: AI 질의응답 API
- `braille.py`: 점자 변환 API

### 9.3 주요 서비스 파일

- `book_service.py`: 교재 처리 서비스 (PDF 파이프라인 실행, 백그라운드 작업)
- `curriculum_service.py`: 커리큘럼 생성 서비스 (파이프라인 결과를 커리큘럼으로 변환)
- `template_service.py`: 템플릿 관리 서비스 (템플릿 생성, 수정, 삭제 등의 비즈니스 로직)
- `book_conversion.py`: 교재 데이터 변환 서비스 (LearningUnit → Unit 변환)
- `korean_braille.py`: 한글 점자 변환 서비스
- `progress_tracker.py`: 학습 진도 추적 서비스

### 9.4 리팩토링 원칙

- **Router Layer**: HTTP 요청/응답 처리만 담당, 비즈니스 로직은 서비스로 위임
- **Service Layer**: 비즈니스 로직, 데이터 처리, 파이프라인 실행 담당
- **로깅**: 모든 `print` 문을 `logger`로 변경하여 표준화

---

## 10. 데이터 형식

### 10.1 날짜/시간
ISO 8601 형식 사용: `2026-01-26T10:30:00Z`

### 10.2 이미지 URL
```
/api/data/{subject}/{book_id}/{type}_images/{filename}
```

예시:
```
/api/data/literature/book_123/concepts_images/concept_p10_01.png
```

---

## 11. Rate Limiting

현재 버전에서는 Rate Limiting이 적용되지 않습니다. (향후 구현 예정)

---

## 12. API 버전 관리

현재 API 버전은 v1입니다. 향후 버전 변경 시 URL에 버전을 명시합니다:
- `/api/v1/...` (현재)
- `/api/v2/...` (향후)

---

**API 명세서 작성 완료**
