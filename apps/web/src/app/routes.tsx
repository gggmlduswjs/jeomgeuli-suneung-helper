/**
 * 라우트 정의
 * 모든 라우트를 중앙에서 관리
 */
import { lazy } from 'react';

// NEW: Single-flow accessibility-first UI (Phase 2)
const Start = lazy(() => import('../pages/Start'));
const BookSelect = lazy(() => import('../pages/BookSelect'));
const QuestionLearning = lazy(() => import('../pages/QuestionLearning'));
const QuestionList = lazy(() => import('../pages/QuestionList'));
const LearningSummary = lazy(() => import('../pages/LearningSummary'));

// Lazy load pages for code splitting
// MVP 2.0 기존 페이지 (호환성 유지)
const Main = lazy(() => import('../pages/Main'));
const Book = lazy(() => import('../pages/Book'));
const Lesson = lazy(() => import('../pages/Lesson'));
const Unit = lazy(() => import('../pages/Unit'));

// 레거시 페이지 (호환성 유지) - 존재하는 페이지만 import
const Textbook = lazy(() => import('../pages/Textbook'));
const Question = lazy(() => import('../pages/Question'));
const Curriculum = lazy(() => import('../pages/Curriculum'));
const NotFound = lazy(() => import('../pages/NotFound'));

// 삭제된 페이지들 (주석 처리)
// const Passage = lazy(() => import('../pages/Passage/Passage'));
// const GraphTable = lazy(() => import('../pages/GraphTable/GraphTable'));
// const Vocab = lazy(() => import('../pages/Vocab/Vocab'));
// const BrailleSpeed = lazy(() => import('../pages/BrailleSpeed/BrailleSpeed'));
// const ExamMode = lazy(() => import('../pages/ExamMode/ExamMode'));
// const ExamTimer = lazy(() => import('../pages/ExamTimer/ExamTimer'));
// const Explore = lazy(() => import('../pages/Explore'));
// const LearnIndex = lazy(() => import('../pages/LearnIndex'));
// const LearnStep = lazy(() => import('../pages/LearnStep'));
// const FreeConvert = lazy(() => import('../pages/FreeConvert'));
// const Quiz = lazy(() => import('../pages/Quiz'));
// const TextbookConverter = lazy(() => import('../pages/exam/TextbookConverter'));
// const TextCompress = lazy(() => import('../pages/exam/TextCompress'));
// const SentenceRepeat = lazy(() => import('../pages/exam/SentenceRepeat'));

/**
 * 메인 라우트 정의 (MVP 3.0 - Single-flow UI)
 */
export const routes = [
  // NEW: Single-flow accessibility-first UI
  { path: '/', element: Start },
  { path: '/books', element: BookSelect },
  { path: '/learn/:bookId/:lessonId/:questionId', element: QuestionLearning },
  { path: '/questions/:lessonId', element: QuestionList },
  { path: '/summary', element: LearningSummary },

  // Legacy routes (compatibility maintained during transition)
  { path: '/main', element: Main }, // Old home page
  { path: '/book', element: Book },
  { path: '/book/:bookId', element: Book },
  { path: '/lesson/:lessonId', element: Lesson },
  { path: '/unit/:unitId', element: Unit },

  // Legacy routes (compatibility maintained)
  { path: '/textbook', element: Textbook },
  { path: '/question', element: Question },
  { path: '/curriculum', element: Curriculum },
];

/**
 * 레거시 라우트 리다이렉트
 * 레거시 경로를 새 경로로 리다이렉트
 */
export const legacyRedirects = [
  { from: '/learn', to: '/textbook', element: Textbook },
  { from: '/quiz', to: '/question', element: Question },
  { from: '/review', to: '/question', element: Question },
  { from: '/free-convert', to: '/textbook', element: Textbook },
];

/**
 * 레거시 라우트 (제거 예정)
 * 호환성 유지가 필요 없는 경우 제거 가능
 * 현재는 모든 레거시 페이지가 삭제되어 빈 배열
 */
export const legacyRoutes: Array<{ path: string; element: any }> = [
  // 삭제된 레거시 페이지들
  // { path: '/explore', element: Explore },
  // { path: '/learn', element: LearnIndex },
  // { path: '/learn/char', element: LearnStep },
  // { path: '/learn/word', element: LearnStep },
  // { path: '/learn/sentence', element: LearnStep },
  // { path: '/learn/free', element: FreeConvert },
  // { path: '/quiz', element: Quiz },
  // { path: '/learn/quiz', element: Quiz },
  // { path: '/exam/textbook', element: TextbookConverter },
  // { path: '/exam/compress', element: TextCompress },
  // { path: '/exam/repeat', element: SentenceRepeat },
];

/**
 * 404 라우트
 */
export const notFoundRoute = { path: '*', element: NotFound };

