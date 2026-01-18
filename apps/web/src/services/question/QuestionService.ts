/**
 * 문제 관련 서비스
 * 문제 및 답안 제출 관련 비즈니스 로직
 */
import { examAPI, type Question, type AnswerResult } from '../../lib/api/exam';

export class QuestionService {
  /**
   * 문제 조회
   */
  static async loadQuestion(questionId: number): Promise<Question | null> {
    try {
      return await examAPI.getQuestion(questionId);
    } catch (error) {
      console.error('[QuestionService] loadQuestion error:', error);
      throw error;
    }
  }
  
  /**
   * 답안 제출
   */
  static async submitAnswer(
    questionId: number, 
    answer: number, 
    responseTime?: number
  ): Promise<AnswerResult | null> {
    try {
      return await examAPI.submitAnswer(questionId, answer, responseTime);
    } catch (error) {
      console.error('[QuestionService] submitAnswer error:', error);
      throw error;
    }
  }
}

