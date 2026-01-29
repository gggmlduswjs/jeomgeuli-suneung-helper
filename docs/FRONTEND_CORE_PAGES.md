# 프론트엔드 핵심 페이지 6개

## 개요

점그리 수능 도우미의 핵심 사용자 플로우를 구성하는 6개의 주요 페이지입니다.

---

## 1. 시작 화면 (Start)

**경로**: `/`  
**파일**: `frontend/src/pages/Start.tsx`  
**화면 ID**: SC-01

### 기능
- 앱 진입점
- 이어서 학습하기 (Resume) / 새로 시작하기 (New Start) 선택
- 마지막 학습 위치 자동 복원
- 환영 메시지 및 주요 기능 안내

### 주요 특징
- Single-flow accessibility-first UI
- 키보드 네비게이션 지원
- 음성 안내 (TTS)
- 학습 진도 자동 로드

---

## 2. 교재 선택 (BookSelect)

**경로**: `/books`  
**파일**: `frontend/src/pages/BookSelect.tsx`  
**화면 ID**: SC-02

### 기능
- 교재 목록 표시
- 교재 선택 및 강의 목록으로 이동
- 교재별 파싱 상태 확인
- 키보드로 교재 선택 (숫자 키)

### 주요 특징
- 번호가 매겨진 교재 목록
- 키보드 네비게이션 (방향키, 숫자 키)
- 음성 안내
- 파싱 진행 상태 실시간 표시

---

## 3. 강의 목록 (BookLectures)

**경로**: `/lectures/:bookId`  
**파일**: `frontend/src/pages/BookLectures.tsx`  
**화면 ID**: SC-03

### 기능
- 선택한 교재의 강의(레슨) 목록 표시
- 강의 선택 및 학습 시작
- 강의별 진도 표시
- 강의 정보 (제목, 예상 시간, 핵심 포인트)

### 주요 특징
- 강의 목록 카드 형태
- 진도 표시 (완료/진행 중/미시작)
- 키보드 네비게이션
- 강의 상세 정보 표시

---

## 4. 단원 학습 (Unit)

**경로**: `/unit/:unitId`  
**파일**: `frontend/src/pages/Unit.tsx` (또는 `UnitSwipe.tsx`)  
**화면 ID**: SC-04

### 기능
- **핵심 학습 화면** - 개념/본문/문제 통합 뷰어
- 단원 콘텐츠 표시 (텍스트, 이미지, 점자)
- 문제 풀이 및 답안 제출
- AI 학습 도우미 (질문/답변)
- 점자 디스플레이 연동
- 음성 명령 지원

### 주요 특징
- **카드 스와이프 기반 학습** (UnitSwipe)
- 개념 뷰어 (ConceptViewer)
- 문제 입력 및 결과 표시
- AI 설명 자동 생성
- 점자 키워드 패널
- 검색 기능 (Ctrl+F)
- 이전/다음 단원 네비게이션

### 하위 컴포넌트
- `UnitViewer`: 단원 콘텐츠 표시
- `ConceptViewer`: 개념 콘텐츠 및 이미지
- `AnswerInput`: 답안 입력
- `AnswerResultComponent`: 답안 결과
- `AIQuestionInput`: AI 질문 입력
- `AIExplanationCard`: AI 설명 카드
- `BrailleKeywordsPanel`: 점자 키워드 패널

---

## 5. 관리자 페이지 (Admin)

**경로**: `/admin`  
**파일**: `frontend/src/pages/Admin.tsx`  
**화면 ID**: SC-11

### 기능
- **교재 관리 탭**
  - 교재 목록 및 상태 모니터링
  - 교재 업로드
  - 교재별 액션 (재파싱, 삭제, JSON 동기화)
  - 파싱 진행률 실시간 표시
  - 통계 (전체 교재, 완료, 진행 중, 실패)

- **템플릿 관리 탭**
  - 템플릿 목록 (과목별 필터링)
  - 템플릿 생성 (목차 기반)
  - 템플릿 편집/복사/삭제
  - 템플릿 테스트

### 주요 특징
- 탭 기반 네비게이션 (교재 관리 / 템플릿 관리)
- 실시간 파싱 상태 모니터링
- 템플릿 통합 관리
- 교재 업로드 및 파싱 제어

---

## 6. 학습 요약 (LearningSummary)

**경로**: `/summary`  
**파일**: `frontend/src/pages/LearningSummary.tsx`  
**화면 ID**: SC-12

### 기능
- 학습 진도 요약
- 완료한 강의/단원 표시
- 학습 통계
- 이어서 학습하기 링크

### 주요 특징
- 진도 시각화
- 학습 이력 요약
- 빠른 재개 기능

---

## 페이지 간 플로우

```
시작 화면 (/)
    ↓
교재 선택 (/books)
    ↓
강의 목록 (/lectures/:bookId)
    ↓
단원 학습 (/unit/:unitId)
    ↓
학습 요약 (/summary) [선택적]
```

**관리자 플로우**:
```
관리자 페이지 (/admin)
    ├─→ 교재 관리
    │   ├─→ 교재 업로드
    │   └─→ 교재 목록 관리
    └─→ 템플릿 관리
        ├─→ 템플릿 생성
        └─→ 템플릿 편집
```

---

## 공통 기능

모든 핵심 페이지에서 공통으로 지원하는 기능:

1. **접근성**
   - 키보드 네비게이션
   - 스크린 리더 지원
   - 음성 안내 (TTS)

2. **음성 명령**
   - 전역 음성 인식 (화면 길게 눌러 활성화)
   - 음성 명령 처리

3. **점자 디스플레이**
   - BLE 연결
   - 점자 텍스트 전송

4. **반응형 디자인**
   - 모바일 최적화
   - 태블릿/데스크톱 지원

---

## 기술 스택

- **프레임워크**: React + TypeScript
- **라우팅**: React Router (lazy loading)
- **스타일링**: Tailwind CSS
- **상태 관리**: Zustand
- **UI 컴포넌트**: 커스텀 컴포넌트 (AppShellMobile)

---

## 파일 구조

```
frontend/src/pages/
├── Start.tsx              # 1. 시작 화면
├── BookSelect.tsx         # 2. 교재 선택
├── BookLectures.tsx       # 3. 강의 목록
├── Unit.tsx               # 4. 단원 학습 (메인)
├── UnitSwipe.tsx          # 4. 단원 학습 (스와이프 버전)
├── Admin.tsx              # 5. 관리자 페이지
└── LearningSummary.tsx    # 6. 학습 요약
```
