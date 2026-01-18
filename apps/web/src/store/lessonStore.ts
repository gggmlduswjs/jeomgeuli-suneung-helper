/**
 * 강 상태 관리 Store
 */
import { create } from 'zustand';
import type { Lesson } from '../types/lesson';

interface LessonState {
  lessons: Lesson[];
  selectedLesson: Lesson | null;
  setLessons: (lessons: Lesson[]) => void;
  setLesson: (lesson: Lesson | null) => void;
}

export const useLessonStore = create<LessonState>((set) => ({
  lessons: [],
  selectedLesson: null,
  setLessons: (lessons) => set({ lessons }),
  setLesson: (lesson) => set({ selectedLesson: lesson }),
}));
