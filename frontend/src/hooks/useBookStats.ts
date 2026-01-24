/**
 * 교재 통계 계산 커스텀 hook
 */
import { useMemo } from 'react';
import type { Book } from '../types/book';

interface BookStats {
  total: number;
  done: number;
  processing: number;
  failed: number;
  pending: number;
  totalLessons: number;
}

export function useBookStats(books: Book[]): BookStats {
  return useMemo(() => ({
    total: books.length,
    done: books.filter(b => b.parse_status === 'DONE').length,
    processing: books.filter(b => b.parse_status === 'PROCESSING').length,
    failed: books.filter(b => b.parse_status === 'FAILED').length,
    pending: books.filter(b => b.parse_status === 'PENDING').length,
    totalLessons: books.reduce((sum, b) => sum + (b.lesson_count || 0), 0),
  }), [books]);
}
