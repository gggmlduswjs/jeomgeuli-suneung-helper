/**
 * 교재 상태 관리 Store
 */
import { create } from 'zustand';
import type { Book } from '../types/book';

interface BookState {
  books: Book[];
  selectedBook: Book | null;
  setBooks: (books: Book[]) => void;
  setBook: (book: Book | null) => void;
  addBook: (book: Book) => void;
  updateBook: (bookId: string, updates: Partial<Book>) => void;
  clearBooks: () => void;
}

export const useBookStore = create<BookState>((set) => ({
  books: [],
  selectedBook: null,
  setBooks: (books) => set({ books }),
  setBook: (book) => set({ selectedBook: book }),
  addBook: (book) => set((state) => ({ books: [book, ...state.books] })),
  updateBook: (bookId, updates) =>
    set((state) => ({
      books: state.books.map((b) => (b.book_id === bookId ? { ...b, ...updates } : b)),
      selectedBook:
        state.selectedBook?.book_id === bookId
          ? { ...state.selectedBook, ...updates }
          : state.selectedBook,
    })),
  clearBooks: () => set({ books: [], selectedBook: null }),
}));
