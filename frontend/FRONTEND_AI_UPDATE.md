# Frontend AI Features Update

**Date**: 2026-01-20
**Branch**: `refactor/complete-pipeline-separation`

## 📋 Overview

프론트엔드에 Level 1 (ML), Level 2 (DL), Level 3 (LLM) AI 기능을 통합했습니다.

---

## 🎯 업데이트된 파일

### 1. 타입 정의 업데이트

**파일**: `src/types/book.ts`

**추가된 타입**:
```typescript
// AI 처리 옵션
interface AIProcessingOptions {
  // Level 1: ML
  enable_ml_deduplication?: boolean;
  enable_ml_classification?: boolean;

  // Level 2: DL
  enable_layout_analysis?: boolean;
  enable_math_recognition?: boolean;

  // Level 3: LLM
  enable_llm_metadata?: boolean;
  enable_llm_explanations?: boolean;
  enable_llm_recommendations?: boolean;
  openai_api_key?: string;
  education_level?: 'elementary' | 'middle' | 'high' | 'university';
}

// AI 처리 통계
interface AIProcessingStats {
  ml_deduplication_count?: number;
  ml_classification_count?: number;
  dl_layout_blocks?: number;
  dl_math_expressions?: number;
  llm_metadata_enriched?: number;
  llm_explanations_generated?: number;
  llm_recommendations_built?: boolean;
  llm_api_calls?: number;
  total_processing_time_ms?: number;
}

// LLM 메타데이터
interface LLMMetadata {
  tags: string[];
  keywords: string[];
  difficulty: string;
  learning_objectives: string[];
  subject_area: string;
  estimated_time_minutes: number;
  enrichment_confidence?: number;
}

// 개념 설명
interface ConceptExplanation {
  explanation: string;
  examples: string[];
  key_points: string[];
}

// 유사 콘텐츠
interface SimilarContent {
  text: string;
  metadata: Record<string, any>;
  score: number;
}
```

---

### 2. API 서비스 업데이트

**파일**: `src/services/api/client.ts`

**변경 사항**:
```typescript
// BookService.uploadPDF 메서드에 AI 옵션 추가
async uploadPDF(
  file: File,
  title: string,
  subject: Subject,
  year?: number,
  aiOptions?: AIProcessingOptions  // ← NEW!
): Promise<Book>
```

**FormData에 AI 옵션 추가**:
- `enable_ml_deduplication`
- `enable_ml_classification`
- `enable_layout_analysis`
- `enable_math_recognition`
- `enable_llm_metadata`
- `enable_llm_explanations`
- `enable_llm_recommendations`
- `openai_api_key`
- `education_level`

---

### 3. PDF 업로드 UI 업데이트

**파일**: `src/components/textbook/BookUpload.tsx`

**추가된 기능**:

#### 3.1 AI 옵션 선택 UI

```tsx
// AI 처리 옵션 토글
<button onClick={() => setShowAIOptions(!showAIOptions)}>
  🤖 AI 처리 옵션
</button>

{showAIOptions && (
  <div>
    {/* Level 1: ML (기본 활성화) */}
    - 중복 콘텐츠 제거 (체크박스)
    - 하이브리드 블록 분류 (체크박스)

    {/* Level 2: DL (선택적) */}
    - 문서 구조 분석 - LayoutLMv3 (체크박스)
    - 수식 인식 - TrOCR (체크박스)

    {/* Level 3: LLM (선택적, API 키 필요) */}
    - 메타데이터 자동 생성 (체크박스)
    - 개념 설명 자동 생성 (체크박스)
    - 유사 콘텐츠 추천 시스템 - RAG (체크박스)
    - OpenAI API 키 입력 (password field)
    - 교육 수준 선택 (select: 초등/중등/고등/대학)
  </div>
)}
```

#### 3.2 검증 로직

```typescript
// Level 3 (LLM) 활성화 시 API 키 필수 확인
const llmEnabled = aiOptions.enable_llm_metadata ||
                   aiOptions.enable_llm_explanations ||
                   aiOptions.enable_llm_recommendations;

if (llmEnabled && !aiOptions.openai_api_key?.trim()) {
  setError('Level 3 (LLM) 기능을 사용하려면 OpenAI API 키를 입력해주세요.');
  return;
}
```

---

### 4. AI 결과 표시 컴포넌트

#### 4.1 AIMetadataCard

**파일**: `src/components/ai/AIMetadataCard.tsx`

**기능**:
- LLM 메타데이터 표시
- 태그, 키워드, 난이도, 학습 목표, 예상 시간
- TTS 읽기 지원 (클릭 시 음성 출력)

**사용 예시**:
```tsx
import AIMetadataCard from './components/ai/AIMetadataCard';

<AIMetadataCard
  metadata={{
    tags: ['문학', '시', '수사법'],
    keywords: ['형상화', '이미지', '감각적 표현'],
    difficulty: '고급',
    learning_objectives: ['개념 이해', '작품 분석'],
    subject_area: '문학',
    estimated_time_minutes: 30,
    enrichment_confidence: 0.85
  }}
  onSpeak={(text) => console.log('Speak:', text)}
/>
```

**UI 구성**:
```
🤖 AI 메타데이터              신뢰도: 85%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏷️ 태그
  [문학] [시] [수사법]

🔑 핵심 키워드
  [형상화] [이미지] [감각적 표현] ...

📊 난이도: 고급
📚 과목 영역: 문학
⏱️ 예상 학습 시간: 30분

🎯 학습 목표
  • 형상화의 개념 이해
  • 작품 속 형상화 기법 분석
```

---

#### 4.2 ConceptExplanationCard

**파일**: `src/components/ai/ConceptExplanationCard.tsx`

**기능**:
- 개념 설명 표시 (수준별)
- 수준 전환 (초등/중등/고등/대학)
- 예시 및 핵심 포인트 표시
- TTS 읽기 지원

**사용 예시**:
```tsx
import ConceptExplanationCard from './components/ai/ConceptExplanationCard';

<ConceptExplanationCard
  concept="형상화"
  explanations={{
    high: {
      explanation: "형상화는 추상적인 개념을...",
      examples: ["시각적 형상화: ...", "청각적 형상화: ..."],
      key_points: ["추상 → 구체", "감각적 이미지", "공감 유도"]
    },
    middle: {
      explanation: "...",
      examples: [...],
      key_points: [...]
    }
  }}
  defaultLevel="high"
  onSpeak={(text) => console.log('Speak:', text)}
/>
```

**UI 구성**:
```
💡 개념 설명: 형상화              🔊 전체 읽기
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[초등] [중등] [고등] [대학]  ← 수준 선택

📝 설명
  형상화는 추상적인 개념이나 감정을
  구체적인 이미지로 표현하는 기법입니다...

📖 예시
  1. 시각적 형상화: '슬픔'을 '검은 구름'으로 표현
  2. 청각적 형상화: '고독'을 '적막한 발소리'로 표현

⭐ 핵심 포인트
  ▸ 추상 → 구체 변환
  ▸ 감각적 이미지 활용
  ▸ 독자의 공감 유도
```

---

#### 4.3 SimilarContentCard

**파일**: `src/components/ai/SimilarContentCard.tsx`

**기능**:
- 유사 콘텐츠 추천 목록 표시
- 유사도 점수 시각화
- 콘텐츠 미리보기 및 확장
- 메타데이터 표시
- TTS 읽기 지원

**사용 예시**:
```tsx
import SimilarContentCard from './components/ai/SimilarContentCard';

<SimilarContentCard
  title="🔍 유사 문제"
  recommendations={[
    {
      text: "다음 이차방정식을 푸시오: x^2 - 5x + 6 = 0",
      metadata: { type: 'problem', difficulty: '중급' },
      score: 0.92
    },
    {
      text: "이차방정식 x^2 + 2x - 3 = 0의 해를 구하시오.",
      metadata: { type: 'problem', difficulty: '초급' },
      score: 0.87
    }
  ]}
  onSpeak={(text) => console.log('Speak:', text)}
  onSelectContent={(content) => console.log('Selected:', content)}
/>
```

**UI 구성**:
```
🔍 유사 문제                    5개 추천
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────────────────────────┐
│ #1  매우 유사 (92.0%)        🔊 │
│ 다음 이차방정식을 푸시오...     │
│                                  │
│ ▼ 클릭하여 확장                 │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ #2  유사 (87.0%)             🔊 │
│ 이차방정식 x^2 + 2x - 3 = 0의   │
│ 해를 구하시오.                   │
└─────────────────────────────────┘
```

---

## 🔧 통합 예시

### PDF 업로드 후 AI 결과 표시

```tsx
// 예시 페이지: BookDetailPage.tsx
import AIMetadataCard from '../components/ai/AIMetadataCard';
import ConceptExplanationCard from '../components/ai/ConceptExplanationCard';
import SimilarContentCard from '../components/ai/SimilarContentCard';

function BookDetailPage({ book, lesson }) {
  return (
    <div className="space-y-4">
      {/* 기존 콘텐츠 */}
      <LessonContent lesson={lesson} />

      {/* AI 메타데이터 */}
      {lesson.llm_metadata && (
        <AIMetadataCard
          metadata={lesson.llm_metadata}
          onSpeak={handleSpeak}
        />
      )}

      {/* 개념 설명 */}
      {lesson.llm_explanation && (
        <ConceptExplanationCard
          concept={lesson.title}
          explanations={lesson.llm_explanation}
          onSpeak={handleSpeak}
        />
      )}

      {/* 유사 콘텐츠 */}
      {lesson.similar_contents && (
        <SimilarContentCard
          recommendations={lesson.similar_contents}
          onSpeak={handleSpeak}
          onSelectContent={handleNavigate}
        />
      )}
    </div>
  );
}
```

---

## 📊 데이터 흐름

```
┌──────────────────────────────────────┐
│ 1. User: PDF Upload + AI 옵션 선택   │
│    - BookUpload 컴포넌트              │
│    - Level 1/2/3 체크박스             │
│    - OpenAI API 키 입력 (Level 3)    │
└────────────┬─────────────────────────┘
             │
             │ FormData (file + options)
             ▼
┌──────────────────────────────────────┐
│ 2. Backend API: /books/upload        │
│    - PDF 추출 (Extraction)            │
│    - DL 처리 (Level 2)                │
│    - 파싱 (Parsing)                   │
│    - ML 후처리 (Level 1)              │
│    - LLM Enrichment (Level 3)         │
└────────────┬─────────────────────────┘
             │
             │ JSON Response
             ▼
┌──────────────────────────────────────┐
│ 3. Frontend: 결과 표시                │
│    - Book with AI data                │
│    - AIMetadataCard                   │
│    - ConceptExplanationCard           │
│    - SimilarContentCard               │
└──────────────────────────────────────┘
```

---

## 🎨 UI/UX 특징

### 1. **점진적 공개 (Progressive Disclosure)**
- AI 옵션은 기본적으로 숨겨져 있음
- 토글 버튼으로 필요시에만 확장
- 복잡성을 줄이고 사용성 향상

### 2. **시각적 피드백**
- Level별 색상 구분
- 유사도 점수 시각화 (매우 유사/유사/약간 유사)
- 신뢰도 퍼센트 표시

### 3. **접근성**
- TTS 지원 (모든 텍스트 클릭 가능)
- 키보드 네비게이션
- 명확한 레이블 및 설명

### 4. **비용 인식**
- Level 3 (LLM) 경고 메시지
- API 사용 비용 발생 알림
- API 키 필수 입력 검증

---

## 📝 사용 가이드

### PDF 업로드 시 AI 옵션 설정

1. **Level 1 (ML) - 기본 활성화**
   - 추가 설정 불필요
   - 중복 제거 및 블록 분류 자동 적용

2. **Level 2 (DL) - 선택적**
   - 문서 구조 분석: 복잡한 레이아웃일 때 권장
   - 수식 인식: 수학/과학 교재일 때 권장
   - 처리 시간 증가 (페이지당 ~2-3초)

3. **Level 3 (LLM) - 선택적**
   - ⚠️ OpenAI API 키 필수
   - ⚠️ API 비용 발생 (~$0.16/100개 콘텐츠)
   - 메타데이터: 자동 태깅 및 분류
   - 설명 생성: 개념 학습 지원
   - 추천 시스템: 유사 문제/개념 찾기

---

## 🚀 향후 개선 사항

- [ ] AI 처리 진행률 표시 (Progress Bar)
- [ ] AI 처리 실패 시 재시도 기능
- [ ] AI 결과 편집 기능 (사용자 수정 가능)
- [ ] AI 처리 통계 대시보드
- [ ] 배치 업로드 지원 (여러 PDF 동시 처리)
- [ ] AI 옵션 프리셋 저장 (자주 쓰는 설정)
- [ ] 다크 모드 지원
- [ ] 반응형 디자인 개선 (모바일)

---

## 🔗 관련 문서

- **Backend Level 1 ML**: `ML_FEATURES_SUMMARY.md`
- **Backend Level 2 DL**: `LEVEL2_DL_SUMMARY.md`
- **Backend Level 3 LLM**: `LEVEL3_LLM_SUMMARY.md`

---

**작성일**: 2026-01-20
**버전**: 1.0.0
**Status**: ✅ 구현 완료
