/**
 * Unit AI 설명 로드 훅
 */
import { useState, useCallback, useEffect, useRef } from 'react';
import { literatureAPI } from '../services/literature';
import type { Unit } from '../types/api';

interface UseUnitAIExplanationOptions {
  unit: Unit | null;
  sectionType: string;
  autoLoad?: boolean;
  onSpeak?: (text: string) => void;
  autoSpeak?: boolean; // AI 설명 생성 시 자동으로 TTS 재생 여부
  readingMode?: 'braille-only' | 'audio-first' | 'mixed'; // 읽기 모드
  onTTSComplete?: () => void; // TTS 재생 완료 시 콜백
  allSections?: unknown[]; // keywords 섹션 요약 생성을 위한 전체 섹션 데이터
}

export function useUnitAIExplanation({
  unit,
  sectionType,
  autoLoad = true,
  onSpeak,
  autoSpeak = true, // 기본값: 자동 재생 활성화
  readingMode = 'mixed', // 기본값: 혼합 모드
  onTTSComplete, // TTS 재생 완료 시 콜백
  allSections = [], // keywords 섹션 요약 생성을 위한 전체 섹션 데이터
}: UseUnitAIExplanationOptions) {
  const [aiExplanation, setAiExplanation] = useState<string | null>(null);
  const [loadingAI, setLoadingAI] = useState(false);
  const onSpeakRef = useRef(onSpeak);
  const autoSpeakRef = useRef(autoSpeak);
  const onTTSCompleteRef = useRef(onTTSComplete);
  const isLoadingRef = useRef(false); // 로딩 중 플래그
  const lastUnitIdRef = useRef<string | number | null>(null); // 이전 unit ID
  const hasSpokenRef = useRef(false); // 이미 읽었는지 플래그
  const readingModeRef = useRef(readingMode); // 읽기 모드 ref

  // onSpeak, autoSpeak, readingMode, onTTSComplete ref 업데이트
  useEffect(() => {
    onSpeakRef.current = onSpeak;
    autoSpeakRef.current = autoSpeak;
    readingModeRef.current = readingMode;
    onTTSCompleteRef.current = onTTSComplete;
  }, [onSpeak, autoSpeak, readingMode, onTTSComplete]);

  const loadAIExplanation = useCallback(async () => {
    if (!unit) {
      // unit이 없으면 상태 초기화
      setAiExplanation(null);
      setLoadingAI(false);
      return;
    }
    
    // keywords 섹션은 content가 없어도 진행 (전체 단원 요약용)
    // 다른 섹션은 content가 필수
    if (sectionType !== 'keywords' && !unit.content) {
      setAiExplanation(null);
      setLoadingAI(false);
      return;
    }

    // 단원 ID와 섹션 타입을 함께 사용하여 확인
    const currentUnitId = unit.id || 'unknown';
    const currentSectionKey = `${currentUnitId}_${sectionType}`;
    const lastSectionKey = lastUnitIdRef.current ? `${lastUnitIdRef.current}_${sectionType}` : null;
    
    // 섹션이 변경되지 않았고 이미 로딩 중이면 건너뜀
    if (isLoadingRef.current && currentSectionKey === lastSectionKey) {
      if (import.meta.env.DEV) console.log('[useUnitAIExplanation] 이미 로딩 중이므로 건너뜀', { sectionKey: currentSectionKey });
      return;
    }

    // 섹션이 변경되었거나 AI 설명이 없으면 새로 로드
    // 이전 섹션의 데이터를 완전히 제거하기 위해 즉시 초기화
    if (import.meta.env.DEV) console.log('[useUnitAIExplanation] AI 설명 로드 시작 (즉시):', {
      unitId: currentUnitId,
      sectionType,
      lastUnitId: lastUnitIdRef.current,
      isLoading: isLoadingRef.current,
      title: unit.title
    });

    // 즉시 이전 데이터 초기화
    setAiExplanation(null); // 이전 설명 즉시 초기화
    hasSpokenRef.current = false; // 읽기 플래그 리셋
    isLoadingRef.current = true;
    setLoadingAI(true);

    try {
      let explanation = '';
      
      // keywords 섹션은 전체 단원 요약을 생성
      if (sectionType === 'keywords') {
        // keywords 섹션: 이전 섹션들의 내용을 모두 모아서 요약 생성
        let allContentText: string[] = [];
        
        if (allSections && allSections.length > 0) {
          // 이전 섹션들의 내용을 모두 모음 (문제 제외)
          allContentText = allSections
            .filter((s): s is { section_type: string; content: string } =>
              typeof s === 'object' && s !== null &&
              'section_type' in s && 'content' in s &&
              s.section_type !== 'problem' && !!s.content && String(s.content).trim() !== ''
            )
            .map(s => String(s.content).trim());
        }
        
        // content가 있으면 추가
        if (unit.content && unit.content.trim()) {
          allContentText.push(unit.content.trim());
        }
        
        // 내용이 없으면 제목만 사용
        if (allContentText.length === 0) {
          allContentText = [unit.title || '단원 요약'];
        }
        
        if (import.meta.env.DEV) console.log('[useUnitAIExplanation] keywords 섹션 - 단원 요약 생성 요청:', { 
          title: unit.title,
          sectionsCount: allSections?.length || 0,
          contentLength: allContentText.length
        });
        
        const result = await literatureAPI.explainContent(
          `${unit.title || '단원'} 전체 내용 요약`,
          allContentText.length > 0 ? allContentText : ['이 단원의 핵심 내용을 간단하고 명확하게 요약해주세요.'],
          'literature'
        );
        explanation = result.ai_explanation;
      } else {
        // 일반 섹션: 기존 로직 사용
        const contentArray = unit.content.split('\n').filter(line => line.trim());

        if (import.meta.env.DEV) console.log('[useUnitAIExplanation] AI 설명 요청:', { 
          sectionType, 
          title: unit.title, 
          contentLength: contentArray.length 
        });

        // sectionType에 따라 적절한 API 호출
        if (sectionType === 'concept') {
          const result = await literatureAPI.explainConcept(
            unit.title || '',
            contentArray,
            'literature'
          );
          explanation = result.ai_explanation;
        } else if (sectionType === 'content' || sectionType === 'example' || sectionType === 'general') {
          // 'general'도 content로 처리
          const result = await literatureAPI.explainContent(
            unit.title || '',
            contentArray,
            'literature'
          );
          explanation = result.ai_explanation;
        } else {
          // 기본적으로 content로 처리
          const result = await literatureAPI.explainContent(
            unit.title || '',
            contentArray,
            'literature'
          );
          explanation = result.ai_explanation;
        }
      }

      if (explanation) {
        setAiExplanation(explanation);
        if (import.meta.env.DEV) console.log('🤖 [AI 설명 생성됨]', { title: unit.title, length: explanation.length });
        
        // AI 설명 생성 시 자동으로 TTS 재생
        // 점자 모드가 아닐 때만 TTS 재생, 이미 읽지 않았을 때만
        if (
          readingModeRef.current !== 'braille-only' && 
          autoSpeakRef.current && 
          onSpeakRef.current &&
          !hasSpokenRef.current
        ) {
          hasSpokenRef.current = true;
          
          // AI 설명만 읽기
          setTimeout(() => {
            if (onSpeakRef.current) {
              onSpeakRef.current(explanation);
              // TTS 완료 콜백은 onSpeak이 단순 함수이므로 직접 호출
              if (onTTSCompleteRef.current) {
                // TTS 재생 시간을 추정하여 콜백 호출 (대략 계산)
                const estimatedDuration = explanation.length * 100; // 문자당 100ms 가정
                setTimeout(() => {
                  if (import.meta.env.DEV) console.log('[useUnitAIExplanation] AI 설명 TTS 완료 추정 - 다음 섹션으로 이동');
                  onTTSCompleteRef.current?.();
                }, estimatedDuration);
              }
            }
          }, 300);
        }
      }
    } catch (err) {
      console.error('AI 설명 로드 실패:', err);
    } finally {
      setLoadingAI(false);
      isLoadingRef.current = false;
    }
  }, [unit?.id, unit?.title, sectionType, allSections]); // allSections 추가하여 keywords 섹션에서 섹션 변경 시 재로드

  // 단원이 변경될 때 AI 설명 자동 로드 (즉시 시작)
  useEffect(() => {
    if (!autoLoad || !unit) return;
    
    // keywords 섹션은 단원 전체를 요약하므로 content가 없어도 진행
    // 다른 섹션은 content가 필수
    if (sectionType !== 'keywords' && !unit.content) {
      return;
    }

    // 단원 ID와 섹션 타입을 함께 사용하여 변경 감지
    const currentUnitId = unit.id || 'unknown';
    const currentSectionKey = `${currentUnitId}_${sectionType}`;
    const previousSectionKey = lastUnitIdRef.current ? `${lastUnitIdRef.current}_${sectionType}` : null;
    const sectionChanged = previousSectionKey !== currentSectionKey;
    
    // 섹션이 변경되었을 때만 로드 (단원 ID와 섹션 타입 모두 고려)
    if (sectionChanged) {
      if (import.meta.env.DEV) console.log('[useUnitAIExplanation] 섹션 변경 감지 - 즉시 AI 설명 로드 시작:', { 
        previous: lastUnitIdRef.current, 
        current: currentUnitId,
        title: unit.title,
        sectionType,
        sectionChanged
      });
      
      // 상태 초기화 (순서 중요!)
      lastUnitIdRef.current = currentUnitId; // 먼저 ID 업데이트
      hasSpokenRef.current = false; // 새 섹션이므로 읽기 플래그 리셋
      isLoadingRef.current = false; // 로딩 플래그도 리셋
      setAiExplanation(null); // 이전 AI 설명 즉시 초기화 (상태 업데이트)
      
      // 즉시 AI 설명 로드 시작 (딜레이 없음)
      loadAIExplanation();
    } else {
      // 같은 섹션이면 건너뜀 (이미 로드됨)
      if (import.meta.env.DEV) console.log('[useUnitAIExplanation] 같은 섹션이므로 AI 설명 로드 건너뜀', { 
        unitId: currentUnitId,
        sectionType,
        isLoading: isLoadingRef.current
      });
    }
  }, [unit?.id, unit?.title, sectionType, autoLoad, loadAIExplanation, allSections]); // allSections 추가하여 keywords 섹션에서 섹션 변경 시 재로드

  return {
    aiExplanation,
    loadingAI,
    loadAIExplanation,
    setAiExplanation,
  };
}
