/**
 * Unit 페이지 AI 설명 관리 훅
 */
import { useState, useRef, useCallback } from 'react';
import { aiAPI } from '../services/ai';
import { literatureAPI } from '../services/literature';
import { createModuleLogger } from '../utils/logger';
import { markdownToPlainText } from '../utils/text/markdownToPlainText';

const logger = createModuleLogger('UnitAI');

export interface UseUnitAIReturn {
  aiExplanation: string | null;
  isAiLoading: boolean;
  loadAIExplanation: (unitId: string, unit?: { type: string; title: string; content_text?: string }) => Promise<void>;
  handleQuestion: (question: string, unitId: string, lessonId: string) => Promise<void>;
  reset: () => void;
}

/**
 * Unit AI 설명 관리 훅
 */
export function useUnitAI(
  onSpeak?: (text: string) => void,
  onSendBraille?: (text: string) => Promise<void>
): UseUnitAIReturn {
  const [aiExplanation, setAiExplanation] = useState<string | null>(null);
  const [isAiLoading, setIsAiLoading] = useState(false);
  
  const isLoadingExplanationRef = useRef(false);
  const hasSpokenExplanationRef = useRef<string | null>(null);
  const explanationLoadTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const loadAIExplanation = useCallback(async (unitId: string, unit?: { type: string; title: string; content_text?: string }) => {
    // 중복 호출 방지
    if (isLoadingExplanationRef.current) {
      logger.log('AI 설명 로드 중 - 중복 호출 방지');
      return;
    }
    
    // 이미 이 unitId에 대해 설명을 말했는지 확인
    if (hasSpokenExplanationRef.current === unitId) {
      logger.log('AI 설명 이미 재생됨 - 중복 방지');
      return;
    }
    
    // 기존 timeout 정리
    if (explanationLoadTimeoutRef.current) {
      clearTimeout(explanationLoadTimeoutRef.current);
      explanationLoadTimeoutRef.current = null;
    }
    
    setIsAiLoading(true);
    isLoadingExplanationRef.current = true;
    
    try {
      let explanation: string | null = null;
      
      // 문학/영어 Unit인 경우 과목별 문학 API 사용 (subject: literature | english)
      const subject = unitId.startsWith('english_') ? 'english' : unitId.startsWith('literature_') ? 'literature' : null;
      if (subject) {
        if (!unit) {
          logger.warn(`${subject} Unit인데 unit 정보가 없습니다.`);
          return;
        }
        const contentArray = unit.content_text?.split('\n').filter(line => line.trim()) || [];
        if (unit.type === 'CONCEPT_CORE') {
          const response = await literatureAPI.explainConcept(unit.title, contentArray, subject);
          explanation = response.ai_explanation;
        } else if (unit.type === 'PASSAGE') {
          const response = await literatureAPI.explainContent(unit.title, contentArray, subject);
          explanation = response.ai_explanation;
        } else if (unit.type === 'QUESTION') {
          logger.log('문제 설명은 아직 지원하지 않습니다.');
          explanation = null;
        }
      } else {
        // 일반 Unit인 경우 기존 AI API 사용
        const response = await aiAPI.teachUnit(unitId);
        explanation = response.explanation;
      }
      
      // 설명이 있으면 상태 업데이트
      if (explanation) {
        setAiExplanation(explanation);
        // TTS 재생은 한 번만 (hasSpokenExplanationRef로 보장)
        if (hasSpokenExplanationRef.current !== unitId) {
          hasSpokenExplanationRef.current = unitId;
          // 마크다운 특수기호 제거 후 TTS 재생
          onSpeak?.(markdownToPlainText(explanation));
          // 점자로도 출력 (에러가 나도 계속 진행)
          if (onSendBraille) {
            try {
              await onSendBraille(markdownToPlainText(explanation));
            } catch (err) {
              logger.error('점자 출력 실패:', err);
            }
          }
        }
      } else {
        // AI 설명이 없을 때는 TTS 재생하지 않음
        setAiExplanation(null);
      }
    } catch (err) {
      logger.error('AI 설명 로드 실패:', err);
      setAiExplanation(null);
    } finally {
      setIsAiLoading(false);
      isLoadingExplanationRef.current = false;
    }
  }, [onSpeak, onSendBraille]);

  const handleQuestion = useCallback(async (question: string, unitId: string, lessonId: string) => {
    setIsAiLoading(true);
    try {
      const response = await aiAPI.answerQuestion(question, unitId, lessonId);
      setAiExplanation(response.answer);
    } catch (err) {
      logger.error('AI 질문 답변 실패:', err);
    } finally {
      setIsAiLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setAiExplanation(null);
    hasSpokenExplanationRef.current = null;
    if (explanationLoadTimeoutRef.current) {
      clearTimeout(explanationLoadTimeoutRef.current);
      explanationLoadTimeoutRef.current = null;
    }
  }, []);

  return {
    aiExplanation,
    isAiLoading,
    loadAIExplanation,
    handleQuestion,
    reset,
  };
}

export default useUnitAI;
