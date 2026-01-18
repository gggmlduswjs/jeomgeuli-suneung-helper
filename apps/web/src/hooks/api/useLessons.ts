/**
 * 강 관련 훅
 */
import { useState, useCallback } from 'react';
import { lessonsAPI } from '../../services/lessons';
import type { Lesson } from '../../types/lesson';

export function useLessons(bookId?: string) {
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadLessons = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await lessonsAPI.list(id);
      setLessons(data);
      return data;
    } catch (err: any) {
      setError(err.message || '강 목록을 불러오는 중 오류가 발생했습니다.');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const getLesson = useCallback(async (lessonId: string) => {
    setLoading(true);
    setError(null);
    try {
      const lesson = await lessonsAPI.get(lessonId);
      return lesson;
    } catch (err: any) {
      setError(err.message || '강을 불러오는 중 오류가 발생했습니다.');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    lessons,
    loading,
    error,
    loadLessons,
    getLesson,
  };
}
