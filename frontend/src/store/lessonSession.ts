// src/store/lessonSession.ts
import type { LessonItem } from '@/lib/normalize';

export type LessonMode = 'char'|'word'|'sentence';
export type LessonSession = {
  mode: LessonMode;
  items: LessonItem[];
  createdAt: number;
};

const KEY = 'lesson_session_v1';

export function saveLessonSession(s: LessonSession) {
  try { sessionStorage.setItem(KEY, JSON.stringify(s)); } catch {}
}
export function loadLessonSession(): LessonSession | null {
  try {
    const raw = sessionStorage.getItem(KEY);
    if (!raw) return null;
    const j = JSON.parse(raw);
    if (!Array.isArray(j?.items)) return null;
    return j as LessonSession;
  } catch { return null; }
}
export function clearLessonSession() {
  try { sessionStorage.removeItem(KEY); } catch {}
}
