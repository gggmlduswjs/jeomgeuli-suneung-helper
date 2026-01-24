// src/store/useKeywordsStore.ts
import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

export type Keyword = string;

type KeywordsState = {
  keywords: Keyword[];
  setKeywords: (keywords: Keyword[]) => void;
  addKeyword: (keyword: Keyword) => void;
  addKeywords: (keywords: Keyword[]) => void;
  removeKeyword: (keyword: Keyword) => void;
  clearKeywords: () => void;
};

const CAP = 20; // 최대 보관 개수(원하면 조절)
const normalize = (arr: Keyword[]): Keyword[] => {
  const out: Keyword[] = [];
  const seen = new Set<string>();
  for (const raw of arr) {
    const k = (raw ?? "").trim();
    if (!k) continue;
    const key = k.toLowerCase();     // 대소문자 무시 중복 제거
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(k);                      // 원본 케이스 유지
  }
  return out.slice(0, CAP);
};

export const useKeywordsStore = create<KeywordsState>()(
  persist(
    (set, _get) => ({
      keywords: [],

      setKeywords: (keywords) => set({ keywords: normalize(keywords) }),

      addKeyword: (keyword) =>
        set((state) => ({ keywords: normalize([...state.keywords, keyword]) })),

      addKeywords: (keywords) =>
        set((state) => ({ keywords: normalize([...state.keywords, ...keywords]) })),

      removeKeyword: (keyword) =>
        set((state) => ({
          keywords: state.keywords.filter(
            (k) => k.toLowerCase() !== keyword.trim().toLowerCase()
          ),
        })),

      clearKeywords: () => set({ keywords: [] }),
    }),
    {
      name: "keywords-v1",
      storage: createJSONStorage(() => localStorage),
      partialize: (s) => ({ keywords: s.keywords }), // 필요한 것만 저장
      version: 1,
    }
  )
);

// 선택자 예시 (컴포넌트에서 불필요 리렌더 줄이고 싶을 때 사용)
// export const selectKeywords = (s: KeywordsState) => s.keywords;
