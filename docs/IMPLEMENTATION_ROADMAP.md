# 구현 로드맵 (Implementation Roadmap)

지금까지 논의한 모든 기능을 구현하기 위한 단계별 가이드입니다.

---

## 📋 구현 범위 요약

### ✅ 이미 구현 완료
1. 레슨 분할 서비스 (`lecture_lesson_splitter.py`)
2. PDF 구조 파서 (`pdf_structure_parser.py`)
3. PDF to Units 변환기 (`pdf_to_units_converter.py`)
4. AI 강의 선생님 서비스 (`ai_lecture_teacher.py`)
5. AI API 라우터 (`ai.py`)
6. 프론트엔드 컴포넌트 (ConceptViewer, WorkViewer, UnitViewer)
7. 프론트엔드 AI 서비스 (`ai.ts`)
8. Unit 페이지에 AI 설명 통합

### ⏳ 구현 필요
1. PDF 구조 파싱 실제 연동
2. Unit 생성 및 DB 저장
3. AI 강의 선생님 실제 동작
4. 실시간 AI 학습 도우미
5. AI 학습 내용 요약
6. 점자 출력 연동
7. TTS 연동

---

## 🎯 구현 단계별 계획

### Phase 1: 기초 인프라 (1주)

#### 1.1 데이터베이스 마이그레이션
```bash
# Lesson 모델에 추가된 필드 반영
- lecture_script_text
- estimated_time
- key_points
- has_question
- has_analysis
```

**작업**:
- [ ] `api/app/db/models.py` 확인 (이미 추가됨)
- [ ] 마이그레이션 스크립트 생성
- [ ] DB 마이그레이션 실행

**파일**:
- `api/app/db/models.py` (확인)
- `api/scripts/migrate_db.py` (새로 생성)

---

#### 1.2 PDF 구조 파싱 연동
**목적**: PDF에서 개념/작품/문제를 실제로 추출하여 Unit으로 변환

**작업**:
- [ ] `pdf_structure_parser.py` 테스트 및 개선
- [ ] `pdf_to_units_converter.py` 실제 PDF 파일로 테스트
- [ ] Unit 생성 API 엔드포인트 추가

**파일**:
- `api/app/services/pdf_structure_parser.py` (개선)
- `api/app/services/pdf_to_units_converter.py` (테스트)
- `api/app/routers/units.py` (새 엔드포인트 추가)

**API 엔드포인트**:
```python
@router.post("/lessons/{lesson_id}/units/from-pdf")
async def create_units_from_pdf(
    lesson_id: str,
    pdf_path: str,
    db: Session = Depends(get_db)
):
    """PDF에서 Unit 생성"""
```

---

#### 1.3 강의 대본 저장
**목적**: HWP 파일에서 강의 대본 추출하여 Lesson에 저장

**작업**:
- [ ] HWP 파일 업로드 API
- [ ] 강의 대본 추출 및 저장
- [ ] 레슨 분할 API 테스트

**파일**:
- `api/app/routers/lessons.py` (HWP 업로드 엔드포인트 추가)
- `api/app/services/hwp_extract.py` (확인)

**API 엔드포인트**:
```python
@router.post("/lessons/{lesson_id}/upload-script")
async def upload_lecture_script(
    lesson_id: str,
    hwp_file: UploadFile,
    db: Session = Depends(get_db)
):
    """강의 대본 HWP 업로드 및 저장"""
```

---

### Phase 2: AI 기능 구현 (1주)

#### 2.1 AI 강의 선생님 실제 동작
**목적**: OpenAI/Gemini API 연동하여 실제로 동작하게

**작업**:
- [ ] API 키 설정 (환경 변수)
- [ ] `ai_lecture_teacher.py` 실제 API 호출 테스트
- [ ] 에러 처리 및 재시도 로직
- [ ] 토큰 제한 관리

**파일**:
- `api/app/services/ai_lecture_teacher.py` (개선)
- `api/app/core/config.py` (API 키 설정)
- `.env` (환경 변수)

**환경 변수**:
```bash
OPENAI_API_KEY=sk-...
# 또는
GEMINI_API_KEY=...
```

---

#### 2.2 실시간 AI 학습 도우미
**목적**: 사용자가 음성으로 질문하면 AI가 답변

**작업**:
- [ ] 프론트엔드: 음성 질문 입력 UI
- [ ] 프론트엔드: AI 답변 표시 UI
- [ ] 백엔드: 질문 답변 API 개선
- [ ] TTS 연동

**파일**:
- `apps/web/src/hooks/useAILearningAssistant.ts` (새로 생성)
- `apps/web/src/components/ai/AIQuestionInput.tsx` (새로 생성)
- `apps/web/src/components/ai/AIAnswerDisplay.tsx` (새로 생성)
- `api/app/routers/ai.py` (개선)

**API 엔드포인트**:
```python
@router.post("/ai/answer")
async def ai_answer_question(
    question: str,
    unit_id: Optional[str] = None,
    lesson_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """실시간 AI 질문 답변"""
```

---

#### 2.3 AI 학습 내용 요약
**목적**: 레슨 시작 전 AI가 핵심 내용 요약

**작업**:
- [ ] 백엔드: 레슨 요약 API
- [ ] 프론트엔드: 레슨 시작 시 자동 요약
- [ ] TTS로 요약 재생

**파일**:
- `api/app/routers/lessons.py` (요약 엔드포인트 추가)
- `api/app/services/ai_lecture_teacher.py` (요약 메서드 추가)
- `apps/web/src/pages/Lesson.tsx` (요약 통합)

**API 엔드포인트**:
```python
@router.get("/lessons/{lesson_id}/summary")
async def get_lesson_summary(
    lesson_id: str,
    db: Session = Depends(get_db)
):
    """레슨 내용 AI 요약"""
```

---

### Phase 3: UI/UX 완성 (1주)

#### 3.1 PDF 내용 표시
**목적**: 개념/작품/문제를 UI에 표시

**작업**:
- [ ] ConceptViewer 스타일링
- [ ] WorkViewer 스타일링
- [ ] QuestionViewer 개선
- [ ] 반응형 디자인

**파일**:
- `apps/web/src/components/unit/ConceptViewer.tsx` (스타일링)
- `apps/web/src/components/unit/WorkViewer.tsx` (스타일링)
- `apps/web/src/components/unit/UnitViewer.tsx` (개선)

---

#### 3.2 AI 설명 UI
**목적**: AI 설명을 보기 좋게 표시

**작업**:
- [ ] AI 설명 카드 디자인
- [ ] 로딩 상태 표시
- [ ] 에러 처리 UI
- [ ] "다시 듣기" 버튼

**파일**:
- `apps/web/src/components/ai/AIExplanationCard.tsx` (새로 생성)
- `apps/web/src/pages/Unit.tsx` (UI 개선)

---

#### 3.3 음성 질문 UI
**목적**: 사용자가 쉽게 질문할 수 있게

**작업**:
- [ ] 음성 질문 버튼
- [ ] 질문 입력 UI
- [ ] AI 답변 표시 UI

**파일**:
- `apps/web/src/components/ai/AIQuestionInput.tsx` (새로 생성)
- `apps/web/src/components/ai/AIAnswerDisplay.tsx` (새로 생성)

---

### Phase 4: 접근성 기능 (1주)

#### 4.1 TTS 연동
**목적**: AI 설명을 음성으로 재생

**작업**:
- [ ] AI 설명 자동 TTS 재생
- [ ] "다시 듣기" 기능
- [ ] TTS 속도 조절

**파일**:
- `apps/web/src/pages/Unit.tsx` (TTS 통합)
- `apps/web/src/hooks/useTTS.ts` (확인)

---

#### 4.2 점자 출력 연동
**목적**: AI 설명을 점자로 출력

**작업**:
- [ ] AI 설명 텍스트 → 점자 변환
- [ ] 점자 디바이스 전송
- [ ] 점자 청크 관리

**파일**:
- `apps/web/src/services/braille/aiBrailleConverter.ts` (새로 생성)
- `apps/web/src/hooks/useBrailleBLE.ts` (확인)
- `apps/web/src/pages/Unit.tsx` (점자 출력 통합)

---

### Phase 5: 통합 테스트 (3일)

#### 5.1 전체 플로우 테스트
**작업**:
- [ ] 관리자: HWP 업로드 → 강의 대본 저장
- [ ] 관리자: PDF 업로드 → Unit 생성
- [ ] 사용자: 레슨 선택 → AI 설명 듣기
- [ ] 사용자: 질문 → AI 답변
- [ ] 점자 출력 테스트
- [ ] TTS 테스트

---

#### 5.2 에러 처리
**작업**:
- [ ] API 에러 처리
- [ ] 네트워크 에러 처리
- [ ] AI API 실패 시 fallback

---

## 📊 우선순위 매트릭스

### 🔥 최우선 (MVP)
1. **AI 강의 선생님 기본 동작** (Phase 2.1)
   - 구현 시간: 2일
   - 임팩트: ⭐⭐⭐⭐⭐

2. **실시간 AI 학습 도우미** (Phase 2.2)
   - 구현 시간: 3일
   - 임팩트: ⭐⭐⭐⭐⭐

3. **AI 학습 내용 요약** (Phase 2.3)
   - 구현 시간: 1일
   - 임팩트: ⭐⭐⭐⭐

### ⚡ 높은 우선순위
4. **PDF 구조 파싱 연동** (Phase 1.2)
   - 구현 시간: 2일
   - 임팩트: ⭐⭐⭐⭐

5. **강의 대본 저장** (Phase 1.3)
   - 구현 시간: 1일
   - 임팩트: ⭐⭐⭐⭐

6. **TTS 연동** (Phase 4.1)
   - 구현 시간: 1일
   - 임팩트: ⭐⭐⭐⭐

### 📋 중간 우선순위
7. **UI/UX 완성** (Phase 3)
   - 구현 시간: 3일
   - 임팩트: ⭐⭐⭐

8. **점자 출력 연동** (Phase 4.2)
   - 구현 시간: 2일
   - 임팩트: ⭐⭐⭐

---

## 🛠️ 구현 체크리스트

### 백엔드
- [ ] DB 마이그레이션 (Lesson 모델 필드 추가)
- [ ] HWP 업로드 API
- [ ] PDF 구조 파싱 API
- [ ] Unit 생성 API (PDF 기반)
- [ ] AI 강의 선생님 API (OpenAI/Gemini 연동)
- [ ] AI 질문 답변 API
- [ ] AI 레슨 요약 API
- [ ] 에러 처리 및 로깅

### 프론트엔드
- [ ] ConceptViewer 컴포넌트
- [ ] WorkViewer 컴포넌트
- [ ] UnitViewer 개선
- [ ] AI 설명 카드 컴포넌트
- [ ] AI 질문 입력 컴포넌트
- [ ] AI 답변 표시 컴포넌트
- [ ] TTS 연동
- [ ] 점자 출력 연동
- [ ] 로딩 상태 표시
- [ ] 에러 처리 UI

### 통합
- [ ] 전체 플로우 테스트
- [ ] 성능 최적화
- [ ] 접근성 검증

---

## 📝 구현 가이드

### 1. 환경 설정

**백엔드**:
```bash
cd api
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-ai.txt
```

**환경 변수** (`.env`):
```bash
OPENAI_API_KEY=sk-...
# 또는
GEMINI_API_KEY=...
DATABASE_URL=sqlite:///./data/db.sqlite3
```

**프론트엔드**:
```bash
cd apps/web
npm install
```

---

### 2. DB 마이그레이션

```python
# api/scripts/migrate_db.py
from app.db.session import SessionLocal, engine
from app.db.models import Base, Lesson

def migrate():
    # Lesson 모델에 새 필드 추가 확인
    Base.metadata.create_all(bind=engine)
    print("마이그레이션 완료")

if __name__ == "__main__":
    migrate()
```

---

### 3. AI API 연동

**OpenAI 사용 시**:
```python
# api/app/services/ai_lecture_teacher.py
import os
import openai

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
```

**Gemini 사용 시**:
```python
# api/app/services/ai_lecture_teacher.py
import os
from google import generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-pro")
```

---

### 4. 테스트 시나리오

**시나리오 1: 강의 대본 업로드**
```
1. 관리자가 HWP 파일 업로드
2. 강의 대본 추출
3. Lesson에 저장
4. 레슨 분할 (선택)
```

**시나리오 2: PDF에서 Unit 생성**
```
1. 관리자가 PDF 업로드
2. PDF 구조 파싱 (개념/작품/문제)
3. Unit 생성
4. DB 저장
```

**시나리오 3: 사용자 학습**
```
1. 사용자가 레슨 선택
2. AI가 레슨 요약 제공
3. Unit 표시 (개념/작품/문제)
4. AI가 각 Unit 설명
5. 사용자가 질문 → AI 답변
6. TTS 재생 + 점자 출력
```

---

## 🎯 최종 목표

### MVP 완성 기준
1. ✅ 관리자가 HWP 업로드 → 강의 대본 저장
2. ✅ 관리자가 PDF 업로드 → Unit 생성
3. ✅ 사용자가 레슨 선택 → AI 설명 듣기
4. ✅ 사용자가 질문 → AI 답변
5. ✅ TTS 재생
6. ✅ 점자 출력 (선택)

### 완성도 체크
- [ ] 백엔드 API 모두 동작
- [ ] 프론트엔드 UI 모두 표시
- [ ] AI 기능 실제 동작
- [ ] TTS 재생 확인
- [ ] 점자 출력 확인
- [ ] 에러 처리 완료

---

## 💡 구현 팁

### 1. 점진적 구현
- 먼저 기본 기능부터 (AI 설명)
- 그 다음 고급 기능 (질문 답변)
- 마지막으로 UI/UX 개선

### 2. 테스트 우선
- 각 기능마다 테스트 작성
- 실제 데이터로 테스트
- 에러 케이스 처리

### 3. 성능 고려
- AI API 호출 최적화 (토큰 제한)
- 캐싱 활용
- 로딩 상태 표시

---

## 📚 참고 문서

- `docs/AI_LECTURE_TEACHER.md`: AI 강의 선생님 설계
- `docs/PDF_CONTENT_STRUCTURE.md`: PDF 구조화 설계
- `docs/AI_ML_USER_EXPERIENCE.md`: 사용자 경험 설계
- `docs/LECTURE_LESSON_STRUCTURE.md`: 레슨 구조 설계

---

*작성일: 2024년 12월*
