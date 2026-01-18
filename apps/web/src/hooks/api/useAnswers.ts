/**
 * 정답/오답 관련 훅
 */
import { useState, useCallback } from 'react';
import { answersAPI } from '../../services/answers';
import type { Answer, AnswerCreate } from '../../types/answer';

export function useAnswers() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submitAnswer = useCallback(async (data: AnswerCreate) => {
    setLoading(true);
    setError(null);
    try {
      const result = await answersAPI.submit(data);
      return result;
    } catch (err: any) {
      setError(err.message || '답안 제출 중 오류가 발생했습니다.');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    loading,
    error,
    submitAnswer,
  };
}
