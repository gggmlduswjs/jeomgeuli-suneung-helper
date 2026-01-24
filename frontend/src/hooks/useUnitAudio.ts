/**
 * Unit 음성 안내 훅
 */
import { useEffect, useRef } from 'react';
import { extractKeywords } from '../utils/contentExtractor';
import { AUDIO_INTRO_DELAY, CONTENT_PREVIEW_LENGTH, CONTENT_FALLBACK_LENGTH, KEYWORD_EXTRACT_COUNT } from '../components/unit/constants';
import type { Unit } from '../types/api';
import type { SubjectStrategy } from '../strategies/subjectLearning';

interface UseUnitAudioOptions {
  unit: Unit | null;
  strategy: SubjectStrategy;
  readingMode: 'braille-only' | 'audio-first' | 'mixed';
  brailleStatus: 'pending' | 'converting' | 'completed' | 'failed';
  onSpeak: (text: string) => void;
  skipIfAIExplanation?: boolean; // AI 설명이 있으면 기본 내용 읽기 건너뛰기
  aiExplanation?: string | null; // AI 설명 상태
  loadingAI?: boolean; // AI 로딩 중 여부
}

export function useUnitAudio({
  unit,
  strategy,
  readingMode,
  brailleStatus,
  onSpeak,
  skipIfAIExplanation = false,
  aiExplanation = null,
  loadingAI = false,
}: UseUnitAudioOptions) {
  // 이전 unit ID를 추적하여 무한 루프 방지
  const lastUnitIdRef = useRef<string | number | null>(null);
  const hasSpokenRef = useRef(false);

  useEffect(() => {
    if (!unit) return;

    // 단원 ID를 사용하여 변경 감지 (unit.id가 필수)
    const currentUnitId = unit.id || 'unknown';
    const unitChanged = lastUnitIdRef.current !== currentUnitId;
    
    if (unitChanged) {
      console.log('[useUnitAudio] 단원 변경 감지:', { 
        previous: lastUnitIdRef.current, 
        current: currentUnitId,
        title: unit.title 
      });
      lastUnitIdRef.current = currentUnitId;
      hasSpokenRef.current = false; // 새 단원이므로 읽기 플래그 리셋
    } else {
      // 같은 단원이면 이미 읽었는지 확인
      if (hasSpokenRef.current) {
        console.log('[useUnitAudio] 이미 읽은 단원이므로 건너뜀', { unitId: currentUnitId });
        return;
      }
    }

    // 점자 모드: 최소한의 안내만
    if (readingMode === 'braille-only') {
      if (brailleStatus === 'pending') {
        onSpeak('점자 변환 중입니다.');
        hasSpokenRef.current = true;
      } else if (brailleStatus === 'completed') {
        onSpeak('점자로 읽어보세요.');
        hasSpokenRef.current = true;
      }
      return;
    }

    // 음성 모드: 내용 읽기
    if (!strategy.displayContent.useAudio) return;

    // AI 설명이 자동으로 읽히는 경우 아무것도 읽지 않음 (AI 설명만 읽음)
    if (skipIfAIExplanation) {
      // AI 설명이 이미 생성된 경우에만 건너뛰기 (로딩 중이면 대기)
      if (aiExplanation) {
        // AI 설명이 이미 생성되어 있으면 아무것도 읽지 않음
        // AI 설명이 자동으로 읽히므로 제목이나 내용을 읽을 필요 없음
        console.log('[useUnitAudio] AI 설명이 있으므로 건너뜀');
        hasSpokenRef.current = true;
        return;
      }
      // AI 설명이 로딩 중이면 잠시 대기 (AI 설명이 생성되면 자동으로 읽힘)
      if (loadingAI) {
        console.log('[useUnitAudio] AI 설명 로딩 중이므로 대기');
        return; // hasSpokenRef는 설정하지 않음 (AI 설명이 생성되면 읽을 수 있도록)
      }
    }

    // AI 설명이 없을 때만 제목과 내용 읽기
    const intro = `${unit.title}입니다.`;
    onSpeak(intro);
    hasSpokenRef.current = true;

    if (!unit.content) return;

    // 내용이 있으면 읽기
    const contentText = strategy.displayContent.extractKey
      ? (() => {
          const keywords = extractKeywords(unit.content, KEYWORD_EXTRACT_COUNT);
          return keywords.length > 0
            ? `핵심 키워드: ${keywords.join(', ')}`
            : unit.content.substring(0, CONTENT_FALLBACK_LENGTH);
        })()
      : unit.content.length > CONTENT_PREVIEW_LENGTH
      ? unit.content.substring(0, CONTENT_PREVIEW_LENGTH) + '...'
      : unit.content;

    setTimeout(() => onSpeak(contentText), AUDIO_INTRO_DELAY);
  }, [unit?.id, unit?.title, onSpeak, strategy.displayContent.useAudio, readingMode, brailleStatus, skipIfAIExplanation, aiExplanation, loadingAI]); // unit?.content 제거하여 불필요한 재실행 방지
}
