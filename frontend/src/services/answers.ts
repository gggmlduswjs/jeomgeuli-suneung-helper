/**
 * 정답/오답 API 서비스
 */
import { api } from './api';
import type { Answer, AnswerCreate } from '../types/answer';

export const answersAPI = {
  /**
   * 정답/오답 제출
   */
  async submit(data: AnswerCreate): Promise<Answer> {
    return api.post<Answer>('/answers', data);
  },
};
