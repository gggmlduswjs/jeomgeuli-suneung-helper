/**
 * Unit 페이지 데이터 로딩 및 관리 훅
 */
import { useState, useRef, useCallback } from 'react';
import { unitsAPI, lessonsAPI, booksAPI } from '../services/api/client';
import { progressAPI } from '../services/progress';
import type { Unit } from '../types/unit';
import type { Lesson } from '../types/lesson';
import type { Book } from '../types/book';
import { createModuleLogger } from '../utils/logger';
import { DEFAULT_USER_ID } from '../constants';

const logger = createModuleLogger('UnitData');

export interface UseUnitDataReturn {
  unit: Unit | null;
  lesson: Lesson | null;
  book: Book | null;
  allUnits: Unit[];
  loading: boolean;
  error: string | null;
  loadUnit: (id: string) => Promise<void>;
  reset: () => void;
}

/**
 * Unit 데이터 로딩 및 관리 훅
 */
export function useUnitData(): UseUnitDataReturn {
  const [unit, setUnit] = useState<Unit | null>(null);
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [book, setBook] = useState<Book | null>(null);
  const [allUnits, setAllUnits] = useState<Unit[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const isLoadingRef = useRef(false);
  const loadedUnitIdRef = useRef<string | null>(null);

  const loadUnit = useCallback(async (id: string) => {
    // 중복 호출 방지
    if (isLoadingRef.current || loadedUnitIdRef.current === id) {
      return;
    }

    isLoadingRef.current = true;
    loadedUnitIdRef.current = id;
    setLoading(true);
    setError(null);
    
    try {
      // Load unit
      const data = await unitsAPI.get(id);
      
      // Load lesson (unit의 lesson_id 검증)
      let lessonData: Lesson;
      try {
        lessonData = await lessonsAPI.get(data.lesson_id);
      } catch (err: unknown) {
        logger.error('Lesson 로드 실패:', err);
        const errorMsg = `학습 단위의 강(레슨)을 찾을 수 없습니다. (lesson_id: ${data.lesson_id})`;
        setError(errorMsg);
        setLoading(false);
        isLoadingRef.current = false;
        return;
      }
      
      // Load book (lesson의 book_id 검증)
      let bookData: Book;
      try {
        bookData = await booksAPI.get(lessonData.book_id);
      } catch (err: unknown) {
        logger.error('Book 로드 실패:', err);
        const errorMsg = `강의 교재를 찾을 수 없습니다. (book_id: ${lessonData.book_id})`;
        setError(errorMsg);
        setLoading(false);
        isLoadingRef.current = false;
        return;
      }
      
      // 데이터 일관성 검증: unit이 올바른 lesson에 속하는지 확인
      if (data.lesson_id !== lessonData.lesson_id) {
        logger.warn('데이터 불일치:', {
          unit_lesson_id: data.lesson_id,
          lesson_lesson_id: lessonData.lesson_id
        });
        const errorMsg = '학습 단위 데이터가 올바르지 않습니다. 데이터를 다시 동기화해주세요.';
        setError(errorMsg);
        setLoading(false);
        isLoadingRef.current = false;
        return;
      }
      
      setUnit(data);
      setLesson(lessonData);
      setBook(bookData);
      
      // Load all units in lesson (for navigation)
      const units = await unitsAPI.listByLesson(data.lesson_id);
      setAllUnits(units);
      
      // 진도 저장
      await progressAPI.save({
        user_id: DEFAULT_USER_ID,
        unit_id: id,
        lesson_id: data.lesson_id,
        book_id: lessonData.book_id,
      });
    } catch (err) {
      logger.error('학습 단위 로드 실패:', err);
      const errorMsg = '학습 단위를 불러오는 중 오류가 발생했습니다.';
      setError(errorMsg);
    } finally {
      setLoading(false);
      isLoadingRef.current = false;
    }
  }, []);

  const reset = useCallback(() => {
    setUnit(null);
    setLesson(null);
    setBook(null);
    setAllUnits([]);
    setError(null);
    loadedUnitIdRef.current = null;
  }, []);

  return {
    unit,
    lesson,
    book,
    allUnits,
    loading,
    error,
    loadUnit,
    reset,
  };
}

export default useUnitData;
