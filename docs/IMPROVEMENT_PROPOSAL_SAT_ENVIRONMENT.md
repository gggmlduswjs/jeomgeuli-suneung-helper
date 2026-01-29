# 실제 수능 환경 반영 개선 제안서

**작성일**: 2026년 1월 26일  
**목적**: 시각장애인 수험생의 실제 수능 시험 환경을 반영한 기능 개선

---

## 📋 개요

현재 프로젝트는 학습 지원 플랫폼으로 잘 구축되어 있으나, 실제 수능 시험 환경과의 차이점이 있습니다. 
실제 수능 시험 방식을 분석하여 개선이 필요한 기능을 정리했습니다.

---

## 🔍 현재 프로젝트 상태 분석

### ✅ 이미 구현된 기능
- 점자 변환 및 디스플레이 연동 (Orbit Reader 20)
- 음성 인터페이스 (STT/TTS)
- AI 학습 도우미
- 학습 진도 추적
- PDF 파싱 및 구조화

### ❌ 부족한 기능 (실제 수능 환경 대비)
1. **텍스트 찾기 기능 (Ctrl+F)** - 국어 영역 필수
2. **수식 계산 도구** - 수학 영역 필수 (한소네 대체)
3. **촉각 그래프/도형 표현** - 수학/탐구 영역
4. **제2외국어 TTS 옵션** - 제2외국어 영역
5. **실제 수능 환경 시뮬레이션 모드**
6. **답안 작성 및 제출 기능**

---

## 🎯 개선 제안 상세

### 1. 텍스트 찾기 기능 강화 (국어 영역 핵심) ⭐⭐⭐

**현재 문제점**:
- 국어 영역에서 "귀로 듣는 독해"가 주력이지만, 특정 단어/구문을 찾기 위해 Ctrl+F가 필수
- 2026학년도 수능 이슈: 괄호 문자 (가) → 특수문자 ㈎ 변경으로 검색 실패

**개선 방안**:

#### 1.1 고급 검색 기능 구현
```typescript
// frontend/src/components/textbook/TextSearch.tsx
interface TextSearchProps {
  content: string;
  onSearch: (query: string, options: SearchOptions) => void;
}

interface SearchOptions {
  caseSensitive: boolean;
  wholeWord: boolean;
  regex: boolean;
  specialChars: boolean; // 특수문자 변형 처리
}
```

**기능 요구사항**:
- ✅ 일반 텍스트 검색 (Ctrl+F)
- ✅ 정규식 검색 지원
- ✅ 특수문자 변형 처리 (가) ↔ ㈎ 자동 매칭
- ✅ 검색 결과 하이라이트 및 음성 안내
- ✅ 점자 디스플레이에 검색 결과 위치 표시
- ✅ 검색 결과 개수 및 현재 위치 안내

#### 1.2 음성 명령 통합
```typescript
// 음성 명령 예시
"찾기 [단어]" → 텍스트 검색 실행
"다음 결과" → 다음 검색 결과로 이동
"이전 결과" → 이전 검색 결과로 이동
"검색 취소" → 검색 종료
```

#### 1.3 점자 디스플레이 연동
- 검색된 단어 위치를 점자 디스플레이에 표시
- 검색 결과 주변 컨텍스트 제공

**우선순위**: ⭐⭐⭐ (최우선)

---

### 2. 수식 계산 도구 (수학 영역 핵심) ⭐⭐⭐

**현재 문제점**:
- 수학 영역에서 복잡한 수식 계산이 필요하나, 계산 도구가 없음
- 실제 수능에서는 "한소네" 점자정보단말기 사용

**개선 방안**:

#### 2. 점자 수식 입력기 구현
```typescript
// frontend/src/components/math/BrailleMathCalculator.tsx
interface BrailleMathCalculatorProps {
  onCalculate: (expression: string) => string;
  brailleMode: boolean; // 점자 입력 모드
}

// 기능:
// - 점자 키보드로 수식 입력
// - LaTeX 수식 표기 지원
// - 계산 결과 음성/점자 출력
// - 계산 히스토리 저장
```

**기능 요구사항**:
- ✅ 점자 키보드 입력 지원
- ✅ 수식 파싱 및 계산 (math.js 또는 similar)
- ✅ LaTeX 수식 렌더링 (음성 설명)
- ✅ 계산 과정 단계별 음성 안내
- ✅ 계산 히스토리 관리
- ✅ 점자 디스플레이에 수식 및 결과 표시

#### 2.2 수식 음성 설명
```typescript
// 예시: "이차방정식 x제곱 더하기 2x 빼기 3은 0"
// → "x² + 2x - 3 = 0"
// → 계산 결과: "x는 1 또는 -3"
```

**우선순위**: ⭐⭐⭐ (최우선)

---

### 3. 촉각 그래프/도형 표현 개선 (수학/탐구 영역) ⭐⭐

**현재 문제점**:
- 그래프, 도표, 지도가 시각적 이미지로만 제공
- 점자 문제지의 촉각 그래프를 시뮬레이션할 수 없음

**개선 방안**:

#### 3.1 그래프 데이터 구조화
```typescript
// backend/app/schemas/graph.ts
interface TactileGraph {
  type: 'line' | 'bar' | 'pie' | 'scatter' | 'map';
  data: GraphDataPoint[];
  description: string; // 음성 설명용
  brailleDescription: string; // 점자 설명용
}

interface GraphDataPoint {
  x: number;
  y: number;
  label: string;
  brailleLabel: string;
}
```

#### 3.2 음성 그래프 설명
```typescript
// 그래프를 음성으로 설명
// 예: "이 그래프는 2020년부터 2024년까지의 온도 변화를 보여줍니다.
//     2020년 온도는 15도, 2021년은 18도, 2022년은 20도..."
```

#### 3.3 점자 그래프 표현
- 그래프 데이터를 점자로 표현 (ASCII art 스타일)
- 점자 디스플레이에 단계별 정보 제공
- 촉각 그래프 시뮬레이션 (텍스트 기반)

**우선순위**: ⭐⭐ (중요)

---

### 4. 제2외국어 TTS 옵션 추가 ⭐⭐

**현재 문제점**:
- 제2외국어 영역은 실제 수능에서 TTS가 제공되지 않음
- 하지만 학습 단계에서는 TTS가 도움이 될 수 있음

**개선 방안**:

#### 4.1 TTS 옵션 설정
```typescript
// frontend/src/components/settings/TTSOptions.tsx
interface TTSOptions {
  enabled: boolean;
  languages: {
    korean: boolean;
    english: boolean;
    chinese: boolean;
    japanese: boolean;
    // ... 기타 제2외국어
  };
  examMode: boolean; // 수능 모드에서는 제2외국어 TTS 비활성화
}
```

#### 4.2 학습 모드 vs 시험 모드
- **학습 모드**: 모든 언어 TTS 활성화
- **시험 모드**: 제2외국어 TTS 비활성화 (실제 수능 환경 반영)

**우선순위**: ⭐⭐ (중요)

---

### 5. 실제 수능 환경 시뮬레이션 모드 ⭐⭐⭐

**현재 문제점**:
- 실제 수능 시험 환경과 차이가 있어 적응이 어려움
- 시험 시간 제한, 도구 제한 등이 반영되지 않음

**개선 방안**:

#### 5.1 시험 모드 구현
```typescript
// frontend/src/components/exam/ExamMode.tsx
interface ExamModeConfig {
  subject: 'korean' | 'math' | 'english' | 'social' | 'science' | 'second_language';
  timeLimit: number; // 일반 수험생 시간의 1.7배
  tools: {
    brailleDisplay: boolean;
    tts: boolean;
    calculator: boolean; // 수학/과학만
    search: boolean; // 국어/영어만
  };
  answerFormat: 'braille' | 'file' | 'assistant'; // 답안 작성 방식
}
```

#### 5.2 시험 환경 설정
- **국어**: 점자 문제지 + TTS + 검색 기능
- **수학**: 점자 문제지 + 계산기 + 촉각 그래프
- **영어**: 점자 문제지 + TTS + 검색 기능
- **탐구**: 점자 문제지 + TTS + 계산기 + 촉각 자료
- **제2외국어**: 점자 문제지만 (TTS 없음)

#### 5.3 시간 관리 기능
```typescript
// 시험 시간 타이머
// - 일반 수험생 시간의 1.7배 자동 계산
// - 주기적 시간 안내 (음성)
// - 남은 시간 점자 디스플레이 표시
```

**우선순위**: ⭐⭐⭐ (최우선)

---

### 6. 답안 작성 및 제출 기능 ⭐⭐

**현재 문제점**:
- 답안 작성 기능이 없음
- 실제 수능에서는 점자 답안지, 파일 제출 등 다양한 방식 사용

**개선 방안**:

#### 6.1 답안 작성 인터페이스
```typescript
// frontend/src/components/exam/AnswerSheet.tsx
interface AnswerSheet {
  questionNumber: number;
  answer: string | number;
  answerType: 'multiple_choice' | 'short_answer' | 'essay';
  brailleAnswer: string; // 점자 답안
}
```

#### 6.2 답안 작성 방식
- **점자 답안지 모드**: 점자로 답안 입력
- **파일 제출 모드**: 텍스트 파일로 답안 저장
- **대필 모드**: 일반 답안지 형식 (시각 확인용)

#### 6.3 답안 검토 기능
- 작성한 답안 음성 재생
- 점자 디스플레이에 답안 표시
- 답안 수정 기능

**우선순위**: ⭐⭐ (중요)

---

## 📊 우선순위 정리

### Phase 1 (최우선) - 실제 수능 환경 핵심 기능
1. **텍스트 찾기 기능 강화** (국어 영역 필수)
2. **수식 계산 도구** (수학 영역 필수)
3. **실제 수능 환경 시뮬레이션 모드** (전체 영역)

### Phase 2 (중요) - 학습 효과 향상
4. **촉각 그래프/도형 표현 개선** (수학/탐구)
5. **제2외국어 TTS 옵션** (학습 지원)
6. **답안 작성 및 제출 기능** (실전 연습)

---

## 🛠️ 구현 가이드

### 1. 텍스트 찾기 기능 구현

**Frontend 컴포넌트**:
```typescript
// frontend/src/components/textbook/TextSearch.tsx
export const TextSearch: React.FC<TextSearchProps> = ({ content, onSearch }) => {
  // 검색 UI 구현
  // 특수문자 변형 처리
  // 검색 결과 하이라이트
  // 음성 안내
};
```

**Backend API**:
```python
# backend/app/routers/search.py
@router.post("/search/text")
async def search_text(
    content: str,
    query: str,
    options: SearchOptions
) -> SearchResult:
    # 특수문자 변형 처리
    # 정규식 검색
    # 결과 반환
```

### 2. 수식 계산 도구 구현

**Frontend 컴포넌트**:
```typescript
// frontend/src/components/math/BrailleMathCalculator.tsx
import { evaluate } from 'mathjs';

export const BrailleMathCalculator: React.FC = () => {
  // 점자 키보드 입력
  // 수식 파싱
  // 계산 실행
  // 결과 음성/점자 출력
};
```

**점자 수식 입력**:
- 점자 키보드 매핑
- LaTeX 변환
- 음성 피드백

### 3. 시험 모드 구현

**상태 관리**:
```typescript
// frontend/src/store/examStore.ts
interface ExamState {
  mode: 'learning' | 'exam';
  subject: SubjectType;
  timeRemaining: number;
  tools: ExamTools;
  answers: Answer[];
}
```

---

## 📝 추가 고려사항

### 1. 2026학년도 수능 이슈 대응
- 괄호 문자 변형 (가) ↔ ㈎ 자동 처리
- 다양한 특수문자 포맷 지원
- 검색 기능 강화

### 2. 접근성 강화
- 키보드 단축키 지원 (Ctrl+F 등)
- 스크린 리더 호환성
- 점자 디스플레이 최적화

### 3. 사용자 피드백 수집
- 실제 시각장애인 수험생 테스트
- 사용성 개선
- 기능 추가 요청 반영

---

## 🎯 기대 효과

1. **실제 수능 환경 적응**: 시뮬레이션 모드를 통해 실제 시험에 익숙해짐
2. **학습 효율 향상**: 찾기 기능, 계산 도구 등으로 학습 시간 단축
3. **자신감 향상**: 실제 시험 환경과 유사한 연습으로 불안감 감소
4. **접근성 개선**: 다양한 도구와 옵션으로 개인별 맞춤 학습 가능

---

## 📚 참고 자료

- 한국교육과정평가원: 시각장애인 수능 시험 안내
- 2026학년도 수능 특수문자 이슈 관련 자료
- 점자정보단말기(한소네) 사용법

---

**작성자**: AI Assistant  
**검토 필요**: 실제 시각장애인 수험생 사용자 테스트 필수
