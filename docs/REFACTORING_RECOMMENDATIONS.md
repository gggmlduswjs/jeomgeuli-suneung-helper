# 점그리 수능 도우미 리팩토링 제안서

**작성일**: 2026년 1월 26일  
**버전**: 1.0.0  
**작성자**: 개발팀

---

## 목차

1. [개요](#1-개요)
2. [우선순위별 리팩토링 항목](#2-우선순위별-리팩토링-항목)
3. [상세 리팩토링 계획](#3-상세-리팩토링-계획)
4. [마이그레이션 전략](#4-마이그레이션-전략)

---

## 1. 개요

본 문서는 점그리 수능 도우미 프로젝트의 코드 구조를 분석하여 발견된 리팩토링 필요 사항을 정리한 문서입니다.

### 1.1 분석 범위
- Backend 코드 구조
- Frontend 코드 구조
- 아키텍처 일관성
- 코드 중복
- 레거시 코드

### 1.2 발견된 주요 이슈
1. **PDF 파서 구조 중복** (High Priority)
2. **라우터 구조 불일치** (Medium Priority)
3. **Frontend 레거시 코드** (Medium Priority)
4. **TODO/FIXME 미해결** (Low Priority)

---

## 2. 우선순위별 리팩토링 항목

### 🔴 High Priority (즉시 처리 권장)

#### 2.1 PDF 파서 구조 중복 제거

**문제점**:
- `backend/app/infrastructure/pdf/parsers/`와 `backend/app/infrastructure/pdf/full_parsing/parsers/`에 동일한 파일들이 중복되어 있음
- 약 30개 이상의 파서 파일이 두 위치에 중복 존재
- `pipeline.py`, `result_saver.py`, `postprocessors/` 등도 중복

**영향**:
- 코드 유지보수 어려움
- 버그 수정 시 두 곳 모두 수정 필요
- 혼란스러운 import 경로

**제안**:
```
현재 구조:
backend/app/infrastructure/pdf/
├── parsers/              # ❌ 중복
│   ├── literature.py
│   ├── english.py
│   └── ...
├── full_parsing/
│   ├── parsers/          # ❌ 중복
│   │   ├── literature.py
│   │   ├── english.py
│   │   └── ...
│   └── pipeline.py
└── pipeline.py           # ❌ 중복

제안 구조:
backend/app/infrastructure/pdf/
├── parsers/              # ✅ 단일 위치
│   ├── literature.py
│   ├── english.py
│   └── ...
├── pipeline.py           # ✅ 단일 파일
├── postprocessors/       # ✅ 단일 위치
└── extractors/           # ✅ 기존 유지
```

**작업 내용**:
1. `full_parsing/parsers/`의 파일들을 `parsers/`로 통합
2. `full_parsing/pipeline.py`를 `pipeline.py`로 통합
3. 모든 import 경로 수정
4. 테스트 및 검증

**예상 작업 시간**: 4-6시간

---

### 🟡 Medium Priority (단기간 내 처리 권장)

#### 2.2 라우터 구조 통일

**문제점**:
- 일부 라우터는 `app/routers/`에 위치
- 일부 라우터는 `app/api/v1/`에 위치
- 구조적 일관성 부족

**현재 구조**:
```
app/routers/          # 10개 파일
├── books.py
├── literature.py
├── english.py
└── ...

app/api/v1/           # 4개 디렉토리
├── health/
├── subjects/
├── answers/
└── progress/
```

**제안**:
```
옵션 1: 모두 app/routers/로 통합 (권장)
app/routers/
├── books.py
├── literature.py
├── health.py
├── subjects.py
├── answers.py
└── progress.py

옵션 2: 모두 app/api/v1/로 통합
app/api/v1/
├── books/
├── literature/
├── health/
└── ...
```

**작업 내용**:
1. 라우터 위치 통일 결정
2. 파일 이동 및 import 경로 수정
3. `main.py`의 라우터 등록 코드 수정
4. 테스트 및 검증

**예상 작업 시간**: 2-3시간

---

#### 2.3 Frontend 레거시 라우트 정리

**문제점**:
- `frontend/src/app/routes.tsx`에 많은 주석 처리된 레거시 코드 존재
- 사용하지 않는 라우트 정의가 남아있음
- 코드 가독성 저하

**현재 상태**:
```typescript
// 삭제된 페이지들 (주석 처리)
// const Passage = lazy(() => import('../pages/Passage/Passage'));
// const GraphTable = lazy(() => import('../pages/GraphTable/GraphTable'));
// ... (10개 이상의 주석 처리된 코드)
```

**제안**:
1. 주석 처리된 레거시 코드 완전 제거
2. 사용하지 않는 라우트 정의 제거
3. 라우트 구조 문서화

**작업 내용**:
1. 주석 처리된 코드 제거
2. 실제 사용 중인 라우트만 유지
3. 라우트 구조 문서화

**예상 작업 시간**: 1-2시간

---

### 🟢 Low Priority (여유 있을 때 처리)

#### 2.4 TODO/FIXME 해결

**발견된 TODO/FIXME**:

**Backend**:
- `backend/app/api/v1/answers/routes.py:38`: 오답인 경우 복습 큐에 추가 (나중에 구현)

**Frontend**:
- `frontend/src/pages/LearningSummary.tsx:63`: 실제 세션 통계 계산 필요
- `frontend/src/pages/LearningSummary.tsx:70`: 실제 완료한 문제 수 조회 필요
- `frontend/src/components/input/GlobalVoiceRecognition.tsx:110`: VoiceEventBus에 emitMicMode 메서드 추가 필요
- `frontend/src/components/home/BrailleDeviceCard.tsx:89`: batteryLevel 기능 추가 시 활성화

**작업 내용**:
1. 각 TODO/FIXME의 우선순위 결정
2. 구현 또는 제거 결정
3. 구현 시 코드 작성, 제거 시 주석 삭제

**예상 작업 시간**: 2-4시간 (구현 범위에 따라 다름)

---

## 3. 상세 리팩토링 계획

### 3.1 PDF 파서 구조 통합 상세 계획

#### 3.1.1 현재 상태 분석

**중복 파일 목록**:
- `parsers/literature.py` ↔ `full_parsing/parsers/literature.py`
- `parsers/english.py` ↔ `full_parsing/parsers/english.py`
- `parsers/math1.py` ↔ `full_parsing/parsers/math1.py`
- `parsers/template.py` ↔ `full_parsing/parsers/template.py`
- `parsers/ai_parser.py` ↔ `full_parsing/parsers/ai_parser.py`
- `parsers/hybrid_router.py` ↔ `full_parsing/parsers/hybrid_router.py`
- ... (총 30개 이상)

**중복 유틸리티**:
- `pipeline.py` ↔ `full_parsing/pipeline.py`
- `result_saver.py` ↔ `full_parsing/result_saver.py`
- `postprocessors/` ↔ `full_parsing/postprocessors/`
- `image_saver.py` ↔ `full_parsing/image_saver.py`
- `lecture_contents_extractor.py` ↔ `full_parsing/lecture_contents_extractor.py`
- `page_range_calculator.py` ↔ `full_parsing/page_range_calculator.py`

#### 3.1.2 통합 전략

**단계 1: 파일 비교 및 최신 버전 확인**
```bash
# 각 중복 파일의 최신 수정 시간 확인
# 더 최신 버전을 기준으로 통합
```

**단계 2: Import 경로 수정**
```python
# 변경 전
from app.infrastructure.pdf.full_parsing.parsers.literature import LiteratureParser

# 변경 후
from app.infrastructure.pdf.parsers.literature import LiteratureParser
```

**단계 3: 테스트 및 검증**
- 기존 테스트 실행
- PDF 파싱 기능 수동 테스트
- 모든 라우터에서 파서 사용 확인

#### 3.1.3 예상 영향 범위

**수정 필요한 파일**:
- `backend/app/routers/books.py`
- `backend/app/routers/templates.py`
- `backend/app/infrastructure/pdf/pipeline.py` (통합 후)
- 기타 파서를 import하는 모든 파일

---

### 3.2 라우터 구조 통일 상세 계획

#### 3.2.1 옵션 비교

**옵션 1: `app/routers/`로 통합 (권장)**
- ✅ 더 간단한 구조
- ✅ 기존 대부분의 라우터가 이미 여기에 위치
- ✅ FastAPI의 일반적인 패턴

**옵션 2: `app/api/v1/`로 통합**
- ✅ API 버전 관리 명확
- ❌ 더 복잡한 디렉토리 구조
- ❌ 기존 코드 대부분 수정 필요

#### 3.2.2 통합 작업 순서

1. **health, subjects, answers, progress 라우터를 `app/routers/`로 이동**
2. **파일명 변경** (필요시):
   - `health/routes.py` → `health.py`
   - `subjects/routes.py` → `subjects.py`
   - `answers/routes.py` → `answers.py`
   - `progress/routes.py` → `progress.py`
3. **`main.py` 수정**:
   ```python
   # 변경 전
   from app.api.v1.health import routes as health
   app.include_router(health.router, prefix="/api/v1", tags=["health"])
   
   # 변경 후
   from app.routers import health
   app.include_router(health.router, prefix="/api/v1", tags=["health"])
   ```
4. **`app/api/v1/` 디렉토리 제거**

---

## 4. 마이그레이션 전략

### 4.1 단계별 마이그레이션

#### Phase 1: PDF 파서 구조 통합 (1주)
- [ ] 파일 비교 및 최신 버전 확인
- [ ] `full_parsing/parsers/` → `parsers/` 통합
- [ ] `full_parsing/pipeline.py` → `pipeline.py` 통합
- [ ] 모든 import 경로 수정
- [ ] 테스트 및 검증
- [ ] `full_parsing/` 디렉토리 제거

#### Phase 2: 라우터 구조 통일 (3일)
- [ ] 라우터 통합 방식 결정
- [ ] 라우터 파일 이동
- [ ] `main.py` 수정
- [ ] 테스트 및 검증
- [ ] 레거시 디렉토리 제거

#### Phase 3: Frontend 레거시 코드 정리 (1일)
- [ ] 주석 처리된 코드 제거
- [ ] 사용하지 않는 라우트 제거
- [ ] 라우트 구조 문서화

#### Phase 4: TODO/FIXME 해결 (1주)
- [ ] 각 TODO/FIXME 우선순위 결정
- [ ] 구현 또는 제거 결정
- [ ] 코드 수정 또는 주석 삭제

### 4.2 리스크 관리

**리스크 1: PDF 파서 통합 시 기능 손실**
- **대응**: 통합 전 모든 파서 파일의 차이점 확인
- **대응**: 통합 후 전체 파싱 파이프라인 테스트

**리스크 2: 라우터 통합 시 API 경로 변경**
- **대응**: API 경로는 유지 (prefix 동일)
- **대응**: Frontend API 호출 경로 확인

**리스크 3: 레거시 코드 제거 시 의존성 문제**
- **대응**: 제거 전 의존성 검사
- **대응**: 단계적 제거 및 테스트

### 4.3 롤백 계획

각 Phase는 독립적으로 롤백 가능하도록:
1. Git 브랜치로 작업
2. 각 Phase 완료 후 커밋
3. 문제 발생 시 해당 Phase만 롤백

---

## 5. 예상 효과

### 5.1 코드 품질 개선
- ✅ 중복 코드 제거로 유지보수성 향상
- ✅ 구조 일관성으로 가독성 향상
- ✅ 레거시 코드 제거로 복잡도 감소

### 5.2 개발 효율성 향상
- ✅ 명확한 파일 위치로 개발 속도 향상
- ✅ 일관된 구조로 신규 개발자 온보딩 용이
- ✅ 버그 수정 시 단일 위치만 수정

### 5.3 기술 부채 감소
- ✅ 중복 코드 제거
- ✅ TODO/FIXME 해결
- ✅ 레거시 코드 정리

---

## 6. 참고 사항

### 6.1 리팩토링 원칙
1. **기능 변경 없음**: 리팩토링은 코드 구조만 변경, 기능은 동일하게 유지
2. **단계적 진행**: 한 번에 모든 것을 변경하지 않고 단계적으로 진행
3. **테스트 필수**: 각 단계마다 테스트 및 검증 수행
4. **문서 업데이트**: 구조 변경 시 관련 문서도 함께 업데이트

### 6.2 관련 문서
- [개발명세서](./DEVELOPMENT_SPEC.md)
- [모듈별 파일 구조](./MODULE_FILE_STRUCTURE.md)

---

**리팩토링 제안서 작성 완료**
