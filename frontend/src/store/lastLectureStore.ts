/**
 * 마지막으로 본 강의 (문학/영어/수학) 저장
 * 홈 "진행 중인 학습" 표시용
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type LectureSubject = 'literature' | 'english' | 'math1';

export interface LastLecture {
  subject: LectureSubject;
  lectureId: number;
  lectureTitle: string;
  unitId: string | null;
  updatedAt: string;
}

interface LastLectureStore {
  lastLecture: LastLecture | null;
  setLastLecture: (payload: {
    subject: LectureSubject;
    lectureId: number;
    lectureTitle: string;
    unitId?: string | null;
  }) => void;
  clear: () => void;
}

export const useLastLectureStore = create<LastLectureStore>()(
  persist(
    (set) => ({
      lastLecture: null,
      setLastLecture: ({ subject, lectureId, lectureTitle, unitId = null }) =>
        set({
          lastLecture: {
            subject,
            lectureId,
            lectureTitle,
            unitId: unitId ?? null,
            updatedAt: new Date().toISOString(),
          },
        }),
      clear: () => set({ lastLecture: null }),
    }),
    { name: 'last-lecture-storage' }
  )
);
