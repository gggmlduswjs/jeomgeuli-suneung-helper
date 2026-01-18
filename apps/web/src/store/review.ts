// src/store/useReviewStore.ts
import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

export interface ReviewItem {
  id: string;
  type: "char" | "word" | "sent" | "free";
  korean: string;
  braille: string;
  description: string;
  timestamp: number;
  correct: boolean;
}

interface ReviewState {
  items: ReviewItem[];
  addReviewItem: (item: Omit<ReviewItem, "id" | "timestamp">) => void;
  clearReviewItems: () => void;
  removeReviewItem: (id: string) => void;
  getIncorrectItems: () => ReviewItem[];
}

const MAX_ITEMS = 500;

// 안전한 ID 생성기
const genId = () => {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `review_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
};

// 동일 항목 정의(타입+korean+braille가 같으면 같은 항목으로 간주)
const sameKey = (a: Omit<ReviewItem, "id" | "timestamp">, b: ReviewItem) =>
  a.type === b.type &&
  a.korean.trim() === b.korean.trim() &&
  a.braille.trim() === b.braille.trim();

export const useReviewStore = create<ReviewState>()(
  persist(
    (set, get) => ({
      items: [],

      addReviewItem: (item) =>
        set((state) => {
          const incoming = {
            ...item,
            korean: item.korean.trim(),
            braille: item.braille.trim(),
            description: item.description?.trim() ?? "",
          };

          // 1) 중복이면 최신으로 교체(정답 여부/설명 갱신)
          let next = state.items.slice();
          const dupIdx = next.findIndex((x) => sameKey(incoming, x));
          const record: ReviewItem = {
            ...incoming,
            id: dupIdx >= 0 ? next[dupIdx].id : genId(),
            timestamp: Date.now(),
          };

          if (dupIdx >= 0) {
            next[dupIdx] = record;
          } else {
            next.push(record);
          }

          // 2) 타임스탬프 내림차순 정렬(최근 먼저)
          next.sort((a, b) => b.timestamp - a.timestamp);

          // 3) 개수 제한
          if (next.length > MAX_ITEMS) next = next.slice(0, MAX_ITEMS);

          return { items: next };
        }),

      clearReviewItems: () => set({ items: [] }),

      removeReviewItem: (id) =>
        set((state) => ({
          items: state.items.filter((item) => item.id !== id),
        })),

      getIncorrectItems: () => {
        const { items } = get();
        // 오래된 것부터 하도록 오름차순 정렬하여 반환
        return items
          .filter((i) => !i.correct)
          .slice()
          .sort((a, b) => a.timestamp - b.timestamp);
      },
    }),
    {
      name: "review-items-v1",
      storage: createJSONStorage(() => localStorage),
      // 필요한 데이터만 저장(메서드는 저장 안 됨)
      partialize: (s) => ({ items: s.items }),
      version: 1,
    }
  )
);

// 선택자(원하면 사용)
// export const selectIncorrect = (s: ReviewState) =>
//   s.items.filter((i) => !i.correct);
