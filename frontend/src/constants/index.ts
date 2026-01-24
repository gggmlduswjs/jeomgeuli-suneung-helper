/**
 * 애플리케이션 상수
 */

// 사용자 ID (임시 - 나중에 인증 시스템으로 대체)
export const DEFAULT_USER_ID = 'u_demo';

// Toast 기본 지속 시간 (ms)
export const TOAST_DURATION = 3000;

// AI 설명 자동 로드 딜레이 (ms)
export const AI_EXPLANATION_AUTO_LOAD_DELAY = 500;

// 키보드 단축키 관련
export const KEYBOARD_SHORTCUTS = {
  ENTER: 'enter',
  TAB: 'tab',
  ARROW_LEFT: 'arrowleft',
  ARROW_RIGHT: 'arrowright',
  M: 'm',
  Q: 'q',
  B: 'b',
  R: 'r',
} as const;

// 답안 선택 최대 개수
export const MAX_ANSWER_CHOICES = 5;

// 라우트 경로
export const ROUTES = {
  HOME: '/',
  BOOKS: '/books',
  SUMMARY: '/summary',
  ADMIN: '/admin',
  UNIT: (unitId: string) => `/unit/${unitId}`,
  LESSON: (lessonId: string) => `/lesson/${lessonId}`,
} as const;
