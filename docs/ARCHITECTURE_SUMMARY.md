# 아키텍처 요약

## 핵심 원칙

**관리자가 인프라 제공, 사용자는 학습만**

## 역할 분리

### 관리자 (백엔드/인프라)
```
EBS 수능특강 발행
    ↓
PDF 파일 수신
    ↓
커리큘럼 생성 (HWP 분석 또는 JSON 직접 업로드)
    ↓
DB 저장
    ↓
사용자에게 즉시 제공
```

### 사용자 (프론트엔드)
```
앱 열기
    ↓
과목 선택
    ↓
교재 목록 (이미 준비됨)
    ↓
커리큘럼 목록 (이미 준비됨)
    ↓
1강 클릭 → 즉시 학습 시작
```

## 주요 흐름

### 1. 관리자 작업 (백엔드)
- EBS에서 PDF 수신
- HWP 파일 분석 또는 완성된 커리큘럼 JSON 업로드
- 자동 커리큘럼 생성 (백그라운드)
- DB 저장 및 JSON 파일 저장

### 2. 사용자 작업 (프론트엔드)
- 커리큘럼 목록 조회
- 커리큘럼 상세 조회
- 레슨 목록 조회
- 레슨 상세 조회
- 학습 시작

## API 구조

### 관리자용 (생성)
- `POST /api/v1/curriculum/generate`: 커리큘럼 생성 (HWP + PDF 분석)

### 사용자용 (조회)
- `GET /api/v1/curriculum`: 커리큘럼 목록
- `GET /api/v1/curriculum/{curriculum_id}`: 커리큘럼 상세
- `GET /api/v1/curriculum/{curriculum_id}/lessons`: 레슨 목록
- `GET /api/v1/curriculum/{curriculum_id}/lessons/{lesson_number}`: 레슨 상세

## 프론트엔드 페이지

### 필수 페이지
- `Home.tsx`: 홈 (과목 선택, 학습 이어하기)
- `Book.tsx`: 교재 목록
- `Curriculum.tsx`: 커리큘럼 목록 (조회만)
- `CurriculumDetail.tsx`: 커리큘럼 상세 (조회만)
- `Lesson.tsx`: 레슨 페이지 (학습 화면)
- `Question.tsx`: 문제 풀이

### 삭제된 페이지
- `CurriculumCreate.tsx`: 사용자가 생성할 필요 없음 (관리자가 처리)

## 핵심 가치

1. **즉시 학습 가능**: 관리자가 미리 준비 → 사용자는 바로 학습
2. **단순한 구조**: 사용자는 조회/학습만, 복잡한 생성 로직은 백엔드
3. **명확한 책임**: 관리자 = 데이터 준비, 사용자 = 학습

---

*작성일: 2024년 12월*
