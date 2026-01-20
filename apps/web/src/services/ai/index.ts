/**
 * AI 서비스
 * AI 강의 선생님 API 호출
 */
import { api } from '../api';

export const aiAPI = {
  /**
   * Unit 내용을 AI가 설명
   */
  async teachUnit(unitId: string) {
    return api.post<{
      unit_id: string;
      explanation: string;
      unit_type: string;
    }>(`/ai/teach/unit/${unitId}`);
  },

  /**
   * 사용자 질문에 AI가 답변
   */
  async answerQuestion(
    question: string,
    unitId?: string,
    lessonId?: string
  ) {
    return api.post<{
      question: string;
      answer: string;
    }>('/ai/answer', {
      question,
      unit_id: unitId,
      lesson_id: lessonId,
    });
  },

  /**
   * AI가 강의 대본 기반으로 수업 진행
   */
  async teachLesson(
    lessonId: string,
    mode: 'sequential' | 'interactive',
    question?: string
  ) {
    const body: any = { mode };
    if (question) {
      body.question = question;
    }
    return api.post<{
      lesson_id: string;
      response: string;
      mode: string;
    }>(`/ai/teach/${lessonId}`, body);
  },

  /**
   * 강의 대본에서 다음 주제 가져오기
   */
  async getNextTopic(lessonId: string, position: number) {
    return api.post<{
      lesson_id: string;
      position: number;
      response: string;
    }>(`/ai/teach/${lessonId}/next`, { position });
  },
};
