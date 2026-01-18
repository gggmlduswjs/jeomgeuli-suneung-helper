/**
 * 교재 API 서비스
 */
import { api } from './api';
import type { Book, BookCreate, BookParseStatus, Subject } from '../types/book';

export const booksAPI = {
  /**
   * PDF 업로드 및 교재 생성
   */
  async upload(
    file: File,
    title: string,
    subject: Subject,
    year?: number
  ): Promise<Book> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    formData.append('subject', subject);
    if (year) {
      formData.append('year', year.toString());
    }
    
    return api.postFormData<Book>('/books/upload', formData);
  },

  /**
   * 교재 목록 조회
   */
  async list(): Promise<Book[]> {
    return api.get<Book[]>('/books');
  },

  /**
   * 교재 상세 조회
   */
  async get(bookId: string): Promise<Book> {
    return api.get<Book>(`/books/${bookId}`);
  },

  /**
   * 파싱 상태 조회
   */
  async getParseStatus(bookId: string): Promise<BookParseStatus> {
    return api.get<BookParseStatus>(`/books/${bookId}/parse-status`);
  },

  /**
   * 교재 재파싱
   */
  async reparse(bookId: string): Promise<{ ok: boolean; message: string; status: string }> {
    return api.post<{ ok: boolean; message: string; status: string }>(`/books/${bookId}/reparse`);
  },

  /**
   * HWP 파일 업로드 및 교재 생성
   */
  async uploadHWP(
    file: File,
    title: string,
    subject: Subject,
    year?: number
  ): Promise<Book> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    formData.append('subject', subject);
    if (year) {
      formData.append('year', year.toString());
    }
    
    return api.postFormData<Book>('/books/upload-hwp', formData);
  },
};
