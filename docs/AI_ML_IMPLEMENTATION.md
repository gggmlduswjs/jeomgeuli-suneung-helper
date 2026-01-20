# AI/ML 구현 현황 문서

## 📋 목차

1. [개요](#개요)
2. [구현된 AI/ML 기능](#구현된-aiml-기능)
3. [기술 스택](#기술-스택)
4. [API 엔드포인트](#api-엔드포인트)
5. [프론트엔드 통합](#프론트엔드-통합)
6. [사용 예시](#사용-예시)
7. [설정 및 의존성](#설정-및-의존성)

---

## 개요

이 프로젝트는 시각장애인을 위한 수능 학습 지원 시스템으로, **생성형 AI(LLM)**와 **전통적인 머신러닝** 기술을 활용하여 학습 콘텐츠를 자동 생성하고 사용자에게 맞춤형 학습 경험을 제공합니다.

### 핵심 원칙
- **교재 원문 중심**: AI는 교재 내용을 바탕으로 설명만 생성 (새로운 지식 추가 금지)
- **접근성 우선**: 점자 디바이스와 음성 출력을 통한 학습 지원
- **자동화**: PDF에서 학습 콘텐츠 자동 추출 및 구조화

---

## 구현된 AI/ML 기능

### 1. 생성형 AI (Generative AI) - LLM 기반

#### 1.1 OpenAI GPT-4o-mini 활용

##### 📚 개념 설명 생성
**위치**: `api/app/routers/literature_ai.py`  
**엔드포인트**: `POST /api/v1/literature/ai/explain-concept`

**기능**:
- 문학 개념을 학생이 이해하기 쉽게 정리
- 핵심 내용을 명확하게 설명
- 예시를 통한 이해도 향상
- 200자 이내 간결한 설명 생성

**사용 모델**: `gpt-4o-mini`  
**Temperature**: `0.7`

**예시 입력**:
```json
{
  "concept_title": "(1) 시적 표현의 개념",
  "concept_content": [
    "형상화 • 시 의 주제나 화자의 정서를 형상화하는 데 기여하는 일체의 언어적 표현을 가리킴.",
    "정서나 교훈, 삶의 이치 등과 같 • 비 유, 상징, 역설, 반어, 대구, 반복, 설의, 영탄, 도치, 열거, 점층, 우의, 풍자, 병렬 등"
  ],
  "subject": "literature"
}
```

##### 📖 본문(작품) 설명 생성
**엔드포인트**: `POST /api/v1/literature/ai/explain-content`

**기능**:
- 문학 작품 내용을 학생이 이해하기 쉽게 설명
- 작품의 핵심 내용과 특징을 간결하게 정리
- 300자 이내 설명 생성

##### ❓ 문제 설명 생성
**엔드포인트**: `POST /api/v1/literature/ai/explain-problem`

**기능**:
- 문제의 핵심을 명확하게 설명
- 각 선택지의 의미를 간단히 설명
- 200자 이내 설명 생성

#### 1.2 LangChain 기반 텍스트 후처리

**위치**: `api/app/services/pdf_extract/ai_text_postprocessor.py`  
**클래스**: `AITextPostProcessor`

**기능**:
- **OCR 오류 자동 수정**
  - 숫자와 문자 혼동 (0/O, 1/l/I, 5/S 등)
  - 문자 인접 오류 (rn → m, cl → d 등)
  - 공백 오류 (단어 분리/병합)
- **텍스트 정리 및 정규화**
  - 문장 구조 정리
  - 불필요한 줄바꿈, 공백 정규화
  - 수능특강 교재 형식 유지
- **청크 단위 처리**
  - 긴 텍스트를 자동으로 청크로 분할 (최대 3000자)
  - 문장/문단 경계 고려

**사용 모델**: `gpt-4o-mini` (기본값)  
**Temperature**: `0.0` (일관성 최우선)

### 2. PDF 파이프라인 AI 통합

**위치**: `api/app/services/textbook_pipeline.py`  
**메서드**: `_ai_postprocess_structured_data()`

**기능**:
- PDF에서 추출된 텍스트를 LLM으로 정제
- 강의 콘텐츠와 문제 텍스트 자동 정제
- 병렬 처리 지원 (성능 최적화)
- 선택적 사용 (사용자가 on/off 선택 가능)

**프로세스**:
1. OCR로 추출된 원본 텍스트
2. AI 후처리 옵션 활성화 시 LLM으로 정제
3. 정제된 텍스트를 JSON에 저장

**성능**:
- 병렬 처리로 29개 항목을 평균 0.13초/항목으로 처리
- 총 3.8초 소요 (29개 항목 기준)

### 3. AI 강의 선생님 (프론트엔드 통합)

#### 3.1 순차적 수업 진행
**위치**: `apps/web/src/hooks/useAILectureTeacher.ts`

**기능**:
- 강의 대본을 기반으로 순차적으로 수업 진행
- TTS로 자동 음성 출력
- 다음/이전 주제로 이동

**API**: `POST /api/v1/ai/teach/{lesson_id}` (mode: "sequential")

#### 3.2 대화형 질문-답변
**기능**:
- 사용자 질문에 AI가 강의 대본 기반으로 답변
- 실시간 학습 도우미

**API**: `POST /api/v1/ai/teach/{lesson_id}` (mode: "interactive")  
**프론트엔드 훅**: `useAILearningAssistant`

### 4. 음성 인식 (STT)

**위치**: `apps/web/src/hooks/useSTT.ts`  
**프로바이더**: 
- Google Streaming STT (우선)
- Web Speech API (fallback)

**기능**:
- 실시간 음성 명령 인식
- 음성 명령 처리 (네비게이션, 학습 제어 등)
- 전역 음성 인식 지원

### 5. 수식 OCR (선택적)

**위치**: `api/app/services/pdf_extract/math_ocr.py`  
**클래스**: `MathOCR`

**기능**:
- 수식 이미지 → LaTeX 변환
- Nemeth 점자 변환 파이프라인의 일부

**옵션**:
- **MathPix API** (상용, 높은 정확도)
- **PaddleOCR** (오픈소스, 무료)

---

## 기술 스택

### AI/ML 라이브러리

| 라이브러리 | 버전 | 용도 |
|-----------|------|------|
| **openai** | >= 1.0.0 | GPT-4o-mini API 클라이언트 |
| **langchain** | >= 0.1.0 | LLM 체인 구성 및 프롬프트 관리 |
| **pytorch** | >= 2.1.0 | 딥러닝 모델 (의존성) |
| **transformers** | >= 4.35.0 | Hugging Face 사전 학습 모델 |
| **paddleocr** | >= 2.7.0 | 수식 OCR (선택적) |

### 기타 AI 관련 도구

- **Tesseract OCR**: 텍스트 추출 (별도 설치 필요)
- **pdfplumber**: PDF 텍스트 레이어 추출
- **Google Speech-to-Text API**: 음성 인식

---

## API 엔드포인트

### 문학 AI 설명 API

#### 1. 개념 설명 생성
```
POST /api/v1/literature/ai/explain-concept

Request Body:
{
  "concept_title": "개념 제목",
  "concept_content": ["내용1", "내용2", ...],
  "subject": "literature"
}

Response:
{
  "concept_title": "개념 제목",
  "original_content": ["내용1", "내용2", ...],
  "ai_explanation": "AI가 생성한 설명",
  "subject": "literature"
}
```

#### 2. 본문 설명 생성
```
POST /api/v1/literature/ai/explain-content

Request Body:
{
  "content_title": "본문 제목",
  "content_text": ["작품 텍스트1", "작품 텍스트2", ...],
  "subject": "literature"
}

Response:
{
  "content_title": "본문 제목",
  "original_text": ["작품 텍스트1", ...],
  "ai_explanation": "AI가 생성한 설명",
  "subject": "literature"
}
```

#### 3. 문제 설명 생성
```
POST /api/v1/literature/ai/explain-problem

Request Body:
{
  "problem_id": "01",
  "question_text": "문제 질문",
  "choices": {"1": "선택지1", "2": "선택지2", ...},
  "passage": ["지문1", "지문2", ...],  // 선택
  "subject": "literature"
}

Response:
{
  "problem_id": "01",
  "question_text": "문제 질문",
  "choices": {"1": "선택지1", ...},
  "passage": ["지문1", ...],
  "ai_explanation": "AI가 생성한 설명",
  "subject": "literature"
}
```

### AI 강의 선생님 API

#### 1. 순차적 수업 시작
```
POST /api/v1/ai/teach/{lesson_id}?mode=sequential

Response:
{
  "lesson_id": "lesson_xxx",
  "response": "AI 수업 내용",
  "mode": "sequential"
}
```

#### 2. 대화형 질문-답변
```
POST /api/v1/ai/teach/{lesson_id}?mode=interactive

Request Body:
{
  "question": "사용자 질문"
}

Response:
{
  "lesson_id": "lesson_xxx",
  "response": "AI 답변",
  "mode": "interactive"
}
```

#### 3. Unit 설명
```
POST /api/v1/ai/teach/unit/{unit_id}

Response:
{
  "unit_id": "unit_xxx",
  "explanation": "AI 설명",
  "unit_type": "concept"
}
```

---

## 프론트엔드 통합

### React Hooks

#### 1. `useAILectureTeacher`
**위치**: `apps/web/src/hooks/useAILectureTeacher.ts`

**기능**:
- AI 강의 선생님 기능 통합
- 순차적 수업 진행
- 대화형 질문-답변
- TTS 자동 재생

**사용 예시**:
```typescript
const aiTeacher = useAILectureTeacher(lessonId);

// 수업 시작
await aiTeacher.startLesson();

// 질문하기
await aiTeacher.askQuestion("이 개념이 무엇인가요?");

// 다음 주제
await aiTeacher.nextTopic();
```

#### 2. `useAILearningAssistant`
**위치**: `apps/web/src/hooks/useAILearningAssistant.ts`

**기능**:
- 실시간 학습 도우미
- 사용자 질문에 AI 답변
- TTS 자동 재생

**사용 예시**:
```typescript
const { askQuestion, isAnswering } = useAILearningAssistant(unitId, lessonId);

// 질문하기
await askQuestion("이 문제의 핵심은 무엇인가요?");
```

#### 3. 문학 학습 페이지 AI 통합
**위치**: `apps/web/src/pages/LiteratureLearning.tsx`

**기능**:
- 개념 설명 AI 생성 (자동 + 수동 버튼)
- 본문 설명 AI 생성 (자동 + 수동 버튼)
- 문제 설명 AI 생성 (자동 + 수동 버튼)
- 자동 TTS 재생
- AI 설명 다시 생성 버튼
- AI 설명 다시 듣기 버튼

**섹션 타입 판별**:
- **개념 섹션**: 제목이 `(1)`, `(2)` 형식이고 작품이 없는 경우
- **본문 섹션**: 작가 이름 패턴(`- 작가명, 「작품명」`)이 포함된 경우 또는 나머지
- **문제 섹션**: 강의의 `problems` 배열에 포함된 문제

---

## 사용 예시

### 1. PDF 파이프라인에서 AI 후처리 사용

```bash
cd api
python scripts/run_textbook_pipeline.py

# 옵션 선택:
# AI 후처리 사용? (y/N): y  # ← AI 텍스트 정제 활성화
```

**결과**:
- OCR로 추출된 텍스트가 LLM으로 정제됨
- 오류 수정 및 형식 정규화
- 정제된 JSON 파일 저장

### 2. 프론트엔드에서 AI 설명 생성

```typescript
// 개념 설명 요청
const response = await literatureAPI.explainConcept(
  "시적 표현의 개념",
  ["형상화 • 시 의 주제나 화자의 정서를..."],
  "literature"
);

console.log(response.ai_explanation);
// 출력: "시적 표현은 시의 주제나 화자의 정서를 형상화하는 언어적 표현입니다..."
```

### 3. AI 강의 선생님 사용

```typescript
// Lesson 페이지에서
const aiTeacher = useAILectureTeacher(lessonId);

// 순차적 수업 시작
useEffect(() => {
  if (autoStartAI) {
    aiTeacher.startLesson();
  }
}, []);
```

---

## 설정 및 의존성

### 환경 변수

**`.env` 파일에 설정 필요**:
```env
OPENAI_API_KEY=sk-...
```

### 의존성 설치

```bash
# AI/ML 기능 의존성 설치
cd api
pip install -r requirements-ai.txt

# 또는 전체 의존성
pip install -r requirements.txt
```

### requirements-ai.txt 주요 패키지

```
openai>=1.0.0           # OpenAI API
langchain>=0.1.0        # LangChain
transformers>=4.35.0    # Hugging Face Transformers
torch>=2.1.0            # PyTorch
paddleocr>=2.7.0        # 수식 OCR (선택적)
```

---

## 성능 및 최적화

### 병렬 처리
- AI 후처리: 29개 항목을 병렬로 처리 (평균 0.13초/항목)
- PDF 파이프라인: 페이지별 병렬 OCR 처리

### 캐싱
- OCR 결과 캐싱 (재실행 시 속도 향상)
- 텍스트 후처리 결과 캐싱

### 비용 최적화
- `gpt-4o-mini` 사용 (GPT-4보다 저렴)
- Temperature 0.0~0.7로 일관성 유지
- 토큰 수 제한 (max_tokens: 300~400)
- 선택적 사용 (사용자가 on/off 선택 가능)

---

## 현재 구현 상태 요약

### ✅ 구현 완료

1. **생성형 AI (OpenAI GPT-4o-mini)**
   - ✅ 개념 설명 생성
   - ✅ 본문 설명 생성
   - ✅ 문제 설명 생성

2. **LangChain 기반 텍스트 후처리**
   - ✅ OCR 오류 자동 수정
   - ✅ 텍스트 정리 및 정규화
   - ✅ 청크 단위 처리

3. **PDF 파이프라인 AI 통합**
   - ✅ 선택적 AI 후처리
   - ✅ 병렬 처리 지원

4. **프론트엔드 AI 통합**
   - ✅ AI 강의 선생님 훅
   - ✅ 학습 도우미 훅
   - ✅ 문학 학습 페이지 AI 버튼

5. **음성 인식 (STT)**
   - ✅ Google Streaming STT
   - ✅ Web Speech API fallback

### ⚠️ 문서에는 언급되었으나 코드에서 미확인

다음 기능들은 문서(`SYSTEM_ARCHITECTURE.md`)에 언급되었으나 현재 코드베이스에서 구현을 확인하지 못했습니다:

- Whisper 기반 음성-텍스트 자동 동기화
- Sentence Transformers 기반 콘텐츠 임베딩
- KoBERT 기반 점자 변환 ML 모델
- 콘텐츠 기반 필터링 추천 시스템

이 기능들은 향후 구현 예정이거나 다른 브랜치에 있을 수 있습니다.

---

## 향후 개선 방향

### 단기 개선
- [ ] AI 설명 품질 향상 (프롬프트 최적화)
- [ ] 캐싱 전략 개선 (비용 절감)
- [ ] 오류 처리 강화

### 장기 개선
- [ ] 커스텀 LLM 모델 학습 (비용 절감)
- [ ] 로컬 LLM 지원 (Ollama 등)
- [ ] 멀티모달 AI (이미지 설명 생성)
- [ ] 개인화 추천 시스템

---

## 참고 문서

- [개발 사양서](./DEVELOPMENT_SPECIFICATION.md)
- [시스템 아키텍처](./SYSTEM_ARCHITECTURE.md)
- [AI/ML 역할 분리](./AI_ML_ROLE_SEPARATION.md)
- [AI 강의 선생님](./AI_LECTURE_TEACHER.md)

---

**마지막 업데이트**: 2024년
**문서 버전**: 1.0
