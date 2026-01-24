/**
 * 문학 학습 진도 관리 스토어
 * 로컬 스토리지를 사용하여 진도 저장
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface ProblemResult {
  selected: string;
  correct: boolean;
  timestamp: string;
}

interface LiteratureProgress {
  lastLectureId: number | null;
  completedLectures: number[];
  problemResults: Record<string, ProblemResult>;
  totalStudyTime: number; // seconds
  lastAccessTime: string;
  totalLectures: number; // 전체 강의 수 (동적)
}

interface LiteratureProgressStore {
  progress: LiteratureProgress;

  // 전체 강의 수 설정
  setTotalLectures: (total: number) => void;

  // 마지막 강의 업데이트
  setLastLecture: (lectureId: number) => void;

  // 강의 완료 표시
  completeLecture: (lectureId: number) => void;

  // 강의 완료 여부 확인
  isLectureCompleted: (lectureId: number) => boolean;

  // 문제 결과 저장
  saveProblemResult: (problemId: string, selected: string, correct: boolean) => void;

  // 문제 결과 가져오기
  getProblemResult: (problemId: string) => ProblemResult | null;

  // 학습 시간 추가
  addStudyTime: (seconds: number) => void;

  // 진도율 계산
  getProgressPercentage: () => number;

  // 완료한 문제 개수
  getCompletedProblemsCount: () => number;

  // 정답률 계산
  getAccuracy: () => number;

  // 진도 초기화
  reset: () => void;
}

const initialProgress: LiteratureProgress = {
  lastLectureId: null,
  completedLectures: [],
  problemResults: {},
  totalStudyTime: 0,
  lastAccessTime: new Date().toISOString(),
  totalLectures: 0, // 초기값 0, API 로드 후 설정됨
};

export const useLiteratureProgressStore = create<LiteratureProgressStore>()(
  persist(
    (set, get) => ({
      progress: initialProgress,

      setTotalLectures: (total: number) => {
        set((state) => ({
          progress: {
            ...state.progress,
            totalLectures: total,
          },
        }));
      },

      setLastLecture: (lectureId: number) => {
        set((state) => ({
          progress: {
            ...state.progress,
            lastLectureId: lectureId,
            lastAccessTime: new Date().toISOString(),
          },
        }));
      },

      completeLecture: (lectureId: number) => {
        set((state) => {
          const completedLectures = state.progress.completedLectures;
          if (!completedLectures.includes(lectureId)) {
            return {
              progress: {
                ...state.progress,
                completedLectures: [...completedLectures, lectureId].sort((a, b) => a - b),
                lastAccessTime: new Date().toISOString(),
              },
            };
          }
          return state;
        });
      },

      isLectureCompleted: (lectureId: number) => {
        return get().progress.completedLectures.includes(lectureId);
      },

      saveProblemResult: (problemId: string, selected: string, correct: boolean) => {
        set((state) => ({
          progress: {
            ...state.progress,
            problemResults: {
              ...state.progress.problemResults,
              [problemId]: {
                selected,
                correct,
                timestamp: new Date().toISOString(),
              },
            },
            lastAccessTime: new Date().toISOString(),
          },
        }));
      },

      getProblemResult: (problemId: string) => {
        return get().progress.problemResults[problemId] || null;
      },

      addStudyTime: (seconds: number) => {
        set((state) => ({
          progress: {
            ...state.progress,
            totalStudyTime: state.progress.totalStudyTime + seconds,
            lastAccessTime: new Date().toISOString(),
          },
        }));
      },

      getProgressPercentage: () => {
        const totalLectures = get().progress.totalLectures;
        const completed = get().progress.completedLectures.length;
        if (totalLectures === 0) return 0;
        return Math.round((completed / totalLectures) * 100);
      },

      getCompletedProblemsCount: () => {
        return Object.keys(get().progress.problemResults).length;
      },

      getAccuracy: () => {
        const results = Object.values(get().progress.problemResults);
        if (results.length === 0) return 0;

        const correctCount = results.filter((r) => r.correct).length;
        return Math.round((correctCount / results.length) * 100);
      },

      reset: () => {
        set({ progress: initialProgress });
      },
    }),
    {
      name: 'literature-progress-storage',
    }
  )
);
