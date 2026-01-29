/**
 * 실시간 AI 학습 도우미 훅
 * 사용자가 음성으로 질문하면 AI가 답변
 */
import { useState } from 'react';
import { aiAPI } from '../services/ai';
import useTTS from './useTTS';
import { markdownToPlainText } from '../utils/text/markdownToPlainText';

export function useAILearningAssistant(unitId?: string, lessonId?: string) {
  const { speak } = useTTS();
  const [isAnswering, setIsAnswering] = useState(false);
  const [lastAnswer, setLastAnswer] = useState<string | null>(null);

  const askQuestion = async (question: string) => {
    if (!question.trim()) {
      return;
    }

    setIsAnswering(true);
    try {
      const response = await aiAPI.answerQuestion(question, unitId, lessonId);
      
      setLastAnswer(response.answer);
      
      // TTS로 답변 재생 (마크다운 특수기호 제거)
      speak(markdownToPlainText(response.answer));
      
      return response.answer;
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      console.error('[AI Learning Assistant] 질문 실패:', errorMessage);
      const errorMsg = '죄송합니다. 답변을 생성하는 중 오류가 발생했습니다.';
      speak(errorMsg);
      throw error;
    } finally {
      setIsAnswering(false);
    }
  };

  return {
    askQuestion,
    isAnswering,
    lastAnswer,
  };
}
