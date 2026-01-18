/**
 * 교재 관련 훅
 */
import { useState, useCallback } from 'react';
import { booksAPI } from '../../services/books';
import type { Book, BookCreate, BookParseStatus, Subject } from '../../types/book';

export function useBooks() {
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadBooks = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await booksAPI.list();
      setBooks(data);
      return data;
    } catch (err: any) {
      setError(err.message || '교재 목록을 불러오는 중 오류가 발생했습니다.');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const uploadBook = useCallback(async (
    file: File,
    title: string,
    subject: Subject,
    year?: number
  ) => {
    setLoading(true);
    setError(null);
    try {
      const book = await booksAPI.upload(file, title, subject, year);
      setBooks(prev => [book, ...prev]);
      return book;
    } catch (err: any) {
      setError(err.message || '교재 업로드 중 오류가 발생했습니다.');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const getBook = useCallback(async (bookId: string) => {
    setLoading(true);
    setError(null);
    try {
      const book = await booksAPI.get(bookId);
      return book;
    } catch (err: any) {
      setError(err.message || '교재를 불러오는 중 오류가 발생했습니다.');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const getParseStatus = useCallback(async (bookId: string) => {
    try {
      const status = await booksAPI.getParseStatus(bookId);
      return status;
    } catch (err: any) {
      console.error('[useBooks] 파싱 상태 조회 실패:', err);
      throw err;
    }
  }, []);

  return {
    books,
    loading,
    error,
    loadBooks,
    uploadBook,
    getBook,
    getParseStatus,
  };
}
