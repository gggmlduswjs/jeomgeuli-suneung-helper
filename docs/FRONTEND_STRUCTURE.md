# 프론트엔드 구조 정리

## 컴포넌트 구조

### 중복 컴포넌트
- `components/ai/AIExplanationCard.tsx` - 간단한 버전 (Unit.tsx에서 사용)
- `components/unit/AIExplanationCard.tsx` - 복잡한 버전 (UnitContent.tsx에서 사용)
  - **권장**: `unit/AIExplanationCard.tsx`를 사용하고 `ai/AIExplanationCard.tsx`는 제거 또는 통합

### 주요 컴포넌트 폴더
- `components/textbook/` - 교재 관련 (UnitContent, ProblemContent, TextbookList)
- `components/unit/` - 학습 단위 관련 (AIExplanationCard, UnitHeader, UnitImage)
- `components/question/` - 문제 관련 (QuestionDisplay, AnswerInput, AnswerResult)
- `components/braille/` - 점자 관련 (BrailleCell, BrailleRow, ChunkNavigation)
- `components/input/` - 입력 관련 (ChatLikeInput, SpeechBar, VoiceButton)
- `components/home/` - 홈 화면 카드들
- `components/system/` - 시스템 컴포넌트 (ErrorBoundary, HealthCheck)

## TTS (Text-to-Speech) 구조

### TTS 훅
- `hooks/useTTS.ts` - 기본 TTS 훅 (Web Speech API)
- `hooks/useUnitAudio.ts` - 단원별 음성 안내 훅

### TTS 사용 흐름
1. `Textbook.tsx`에서 `useTTS()`로 `speak` 함수 생성
2. `speak` 함수를 `UnitContent`의 `onSpeak` prop으로 전달
3. `UnitContent`에서 `useUnitAudio` 훅이 자동으로 음성 안내

### TTS 문제 해결
- `readingMode`가 `'braille-only'`일 때는 최소한의 안내만
- `readingMode`가 `'audio-first'` 또는 `'mixed'`일 때는 내용 읽기
- 기본값이 `'braille-only'`이므로 TTS가 안 나올 수 있음 → URL 파라미터나 설정에서 모드 변경 필요

## 학습단위 생성 기준

자세한 내용은 `docs/LEARNING_UNIT_CREATION_RULES.md` 참조

### 요약
1. **섹션 기반**: JSON의 각 섹션이 이미지 단위로 학습단위 생성
2. **문제 기반**: JSON의 각 문제가 이미지 단위로 학습단위 생성
3. **작품 분리**: 섹션에 작품이 있으면 별도 `content` 타입으로 분리
4. **빈 섹션 필터링**: 내용이 없으면 생성하지 않음

## 리팩토링 권장 사항

1. **중복 컴포넌트 통합**
   - `ai/AIExplanationCard`와 `unit/AIExplanationCard` 통합

2. **TTS 로직 단순화**
   - `useUnitAudio`를 더 단순하게 만들기
   - `readingMode` 기본값을 `'mixed'`로 변경 고려

3. **폴더 구조 정리**
   - 사용되지 않는 컴포넌트 제거
   - 관련 컴포넌트 그룹화
