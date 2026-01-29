/**
 * 라우트 정의
 * 모든 라우트를 중앙에서 관리
 */
import { lazy } from 'react';

// NEW: Single-flow accessibility-first UI (Phase 2)
const Start = lazy(() => import('../pages/Start'));
const BookSelect = lazy(() => import('../pages/BookSelect'));
const LearningSummary = lazy(() => import('../pages/LearningSummary'));
const BookLectures = lazy(() => import('../pages/BookLectures'));

// Lazy load pages for code splitting
// MVP 2.0 기존 페이지 (호환성 유지)
const Main = lazy(() => import('../pages/Main'));
const Book = lazy(() => import('../pages/Book'));
const Lesson = lazy(() => import('../pages/Lesson'));
const Unit = lazy(() => import('../pages/Unit'));
const UnitSwipe = lazy(() => import('../pages/UnitSwipe')); // NEW: 카드 스와이프 학습 페이지
const LiteratureLectures = lazy(() => import('../pages/LiteratureLectures'));
const LiteratureLectureDetail = lazy(() => import('../pages/LiteratureLectureDetail'));
const EnglishLectures = lazy(() => import('../pages/EnglishLectures'));
const EnglishLectureDetail = lazy(() => import('../pages/EnglishLectureDetail'));
const Math1Lectures = lazy(() => import('../pages/Math1Lectures'));
const Math1LectureDetail = lazy(() => import('../pages/Math1LectureDetail'));

// 레거시 페이지 (호환성 유지) - 존재하는 페이지만 import
const Curriculum = lazy(() => import('../pages/Curriculum'));
const LearnRedirect = lazy(() => import('../components/routing/LearnRedirect'));
const NotFound = lazy(() => import('../pages/NotFound'));

// 관리자 페이지
const Admin = lazy(() => import('../pages/Admin'));

/**
 * 메인 라우트 정의 (MVP 3.0 - Single-flow UI)
 */
export const routes = [
  // NEW: Single-flow accessibility-first UI
  { path: '/', element: Start },
  { path: '/books', element: BookSelect },
  { path: '/summary', element: LearningSummary },
  { path: '/lectures/:bookId', element: BookLectures },

  // Redirect legacy /learn route to /unit
  { path: '/learn/:bookId/:lessonId/:questionId', element: LearnRedirect },

  // Legacy routes (compatibility maintained during transition)
  { path: '/main', element: Main }, // Old home page
  { path: '/book', element: Book },
  { path: '/book/:bookId', element: Book },
  { path: '/lesson/:lessonId', element: Lesson },
  { path: '/unit/:unitId', element: UnitSwipe }, // NEW: 스와이프 기반 학습 페이지

  // Literature routes
  { path: '/literature/lectures', element: LiteratureLectures },
  { path: '/literature/lectures/:lectureId', element: LiteratureLectureDetail },
  // English routes
  { path: '/english/lectures', element: EnglishLectures },
  { path: '/english/lectures/:lectureId', element: EnglishLectureDetail },
  // Math1 routes
  { path: '/math1/lectures', element: Math1Lectures },
  { path: '/math1/lectures/:lectureId', element: Math1LectureDetail },

  // Legacy routes (compatibility maintained)
  { path: '/curriculum', element: Curriculum },
  
  // Admin routes
  { path: '/admin', element: Admin },
  
  // Redirect legacy routes
  { path: '/textbook', element: BookSelect }, // Textbook -> BookSelect로 리다이렉트
  { path: '/question', element: NotFound }, // Question -> 404 (더 이상 사용 안 함)
  { path: '/literature/lecture/:lectureId', element: NotFound }, // LiteratureLecture -> 404 (Unit으로 통합)
];

/**
 * 레거시 라우트 리다이렉트
 * 레거시 경로를 새 경로로 리다이렉트
 */
export const legacyRedirects = [
  { from: '/learn', to: '/books', element: BookSelect },
  { from: '/quiz', to: '/books', element: BookSelect },
  { from: '/review', to: '/books', element: BookSelect },
  { from: '/free-convert', to: '/books', element: BookSelect },
];

/**
 * 레거시 라우트 (제거 예정)
 * 현재는 빈 배열로 유지 (호환성 유지)
 */
export const legacyRoutes: Array<{ path: string; element: React.ComponentType }> = [];

/**
 * 404 라우트
 */
export const notFoundRoute: { path: string; element: React.ComponentType } = { path: '*', element: NotFound };

