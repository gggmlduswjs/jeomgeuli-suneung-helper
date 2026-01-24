/**
 * AI 강의 선생님 훅
 * 강의 대본 기반 순차적/대화형 수업 진행
 */
import { useState } from 'react';
import { aiAPI } from '../services/ai';
import useTTS from './useTTS';

export function useAILectureTeacher(lessonId: string) {
  const { speak } = useTTS();
  const [isTeaching, setIsTeaching] = useState(false);
  const [currentTopic, setCurrentTopic] = useState<string | null>(null);
  const [position, setPosition] = useState(0);

  /**
   * 순차적 수업 시작
   */
  const startLesson = async () => {
    setIsTeaching(true);
    try {
      // 순차적 수업 시작
      const response = await aiAPI.teachLesson(lessonId, 'sequential');
      setCurrentTopic(response.response);
      // TTS로 재생
      speak(response.response);
    } catch (error) {
      console.error('[AI Lecture] 수업 시작 실패:', error);
      speak('죄송합니다. 수업을 시작하는 중 오류가 발생했습니다.');
    } finally {
      setIsTeaching(false);
    }
  };

  /**
   * 사용자 질문에 답변 (대화형 모드)
   */
  const askQuestion = async (question: string) => {
    try {
      // 대화형 모드로 질문
      const response = await aiAPI.teachLesson(lessonId, 'interactive', question);
      // TTS로 재생
      speak(response.response);
      return response.response;
    } catch (error) {
      console.error('[AI Lecture] 질문 실패:', error);
      speak('죄송합니다. 답변을 생성하는 중 오류가 발생했습니다.');
      throw error;
    }
  };

  /**
   * 다음 주제로 이동
   */
  const nextTopic = async () => {
    const nextPosition = position + 1;
    setPosition(nextPosition);
    try {
      const response = await aiAPI.getNextTopic(lessonId, nextPosition);
      setCurrentTopic(response.response);
      speak(response.response);
    } catch (error) {
      console.error('[AI Lecture] 다음 주제 실패:', error);
      speak('다음 주제를 가져오는 중 오류가 발생했습니다.');
    }
  };

  /**
   * 이전 주제로 이동
   */
  const prevTopic = async () => {
    if (position > 0) {
      const prevPosition = position - 1;
      setPosition(prevPosition);
      try {
        const response = await aiAPI.getNextTopic(lessonId, prevPosition);
        setCurrentTopic(response.response);
        speak(response.response);
      } catch (error) {
        console.error('[AI Lecture] 이전 주제 실패:', error);
        speak('이전 주제를 가져오는 중 오류가 발생했습니다.');
      }
    }
  };

  return {
    startLesson,
    askQuestion,
    nextTopic,
    prevTopic,
    isTeaching,
    currentTopic,
    position,
  };
}
