/**
 * 라우트 정의
 * 모든 라우트를 중앙에서 관리
 */
import { lazy } from 'react';

// Lazy load pages for code splitting
// MVP 2.0 새 페이지
const Main = lazy(() => import('../pages/Main'));
const Book = lazy(() => import('../pages/Book'));
const Lesson = lazy(() => import('../pages/Lesson'));
const Unit = lazy(() => import('../pages/Unit'));
// Review 페이지는 삭제됨 - Question 페이지로 리다이렉트
// const Review = lazy(() => import('../pages/Review'));

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
 * 메인 라우트 정의 (MVP 2.0)
 */
export const routes = [
  { path: '/', element: Main },
  { path: '/book', element: Book },
  { path: '/book/:bookId', element: Book },
  { path: '/lesson/:lessonId', element: Lesson },
  { path: '/unit/:unitId', element: Unit },
  // Review는 Question으로 리다이렉트
  // { path: '/review', element: Review },
  // 레거시 라우트 (호환성 유지) - 존재하는 페이지만
  { path: '/textbook', element: Textbook },
  { path: '/question', element: Question },
  { path: '/curriculum', element: Curriculum },
  // 삭제된 페이지 라우트 (주석 처리)
  // { path: '/passage', element: Passage },
  // { path: '/graph-table', element: GraphTable },
  // { path: '/vocab', element: Vocab },
  // { path: '/braille-speed', element: BrailleSpeed },
  // { path: '/exam-mode', element: ExamMode },
  // { path: '/exam-timer', element: ExamTimer },
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

