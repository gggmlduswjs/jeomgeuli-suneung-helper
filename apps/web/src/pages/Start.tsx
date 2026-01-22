/**
 * Start Screen - Single-flow entry point
 * Two main options: Resume / New Start
 */
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { progressAPI } from '../services/progress';
import { unitsAPI, booksAPI, lessonsAPI } from '../services/api/client';
import type { Progress } from '../types/progress';
import type { Unit } from '../types/unit';
import type { Book } from '../types/book';
import type { Lesson } from '../types/lesson';
import { useKeyboardShortcuts } from '../contexts/KeyboardContext';
import { useAutoGuidance } from '../hooks/useAutoGuidance';
import AppShellMobile from '../components/ui/AppShellMobile';
import ToastA11y from '../components/system/ToastA11y';

interface ResumeInfo {
  book: Book;
  lesson: Lesson;
  unit: Unit;
  questionNumber: number;
  totalQuestions: number;
  progressPercentage: number;
}

export default function Start() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [resumeInfo, setResumeInfo] = useState<ResumeInfo | null>(null);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');

  // Load resume information
  useEffect(() => {
    loadResumeInfo();
  }, []);

  const loadResumeInfo = async () => {
    setLoading(true);
    try {
      // Get current progress
      const progress = await progressAPI.getContinue('u_demo');

      if (!progress?.unit_id) {
        console.log('[Start] No progress found');
        setLoading(false);
        return;
      }

      let unit: Unit;
      try {
        // Get unit details
        unit = await unitsAPI.get(progress.unit_id);
      } catch (err: any) {
        // Unit이 없으면 (404) lesson_id로 첫 번째 유효한 unit 찾기
        console.warn(`[Start] Unit ${progress.unit_id} not found, trying to find valid unit from lesson`);

        if (!progress.lesson_id) {
          console.log('[Start] No lesson_id in progress, cannot recover');
          // Progress 완전 초기화
          await progressAPI.save({
            user_id: 'u_demo',
            book_id: null,
            lesson_id: null,
            unit_id: null,
            syncpoint_id: null,
          });
          setLoading(false);
          return;
        }

        try {
          // lesson_id로 첫 번째 유효한 unit 찾기
          const allUnits = await unitsAPI.listByLesson(progress.lesson_id);
          const questions = allUnits.filter(u => u.type === 'QUESTION');

          if (questions.length === 0) {
            console.log('[Start] No questions found in lesson');
            // Progress 완전 초기화
            await progressAPI.save({
              user_id: 'u_demo',
              book_id: null,
              lesson_id: null,
              unit_id: null,
              syncpoint_id: null,
            });
            setLoading(false);
            return;
          }

          // 첫 번째 문제로 설정
          unit = questions[0];

          // Progress 업데이트
          await progressAPI.save({
            user_id: 'u_demo',
            book_id: progress.book_id || null,
            lesson_id: progress.lesson_id || null,
            unit_id: unit.unit_id,
            syncpoint_id: progress.syncpoint_id || null,
          });

          console.log(`[Start] Recovered: using first question ${unit.unit_id} from lesson`);
        } catch (lessonErr: any) {
          // Lesson도 없으면 progress 완전 초기화
          console.warn(`[Start] Lesson ${progress.lesson_id} not found, clearing progress`);
          await progressAPI.save({
            user_id: 'u_demo',
            book_id: null,
            lesson_id: null,
            unit_id: null,
            syncpoint_id: null,
          });
          setLoading(false);
          return;
        }
      }

      // Get lesson details
      const lesson = await lessonsAPI.get(unit.lesson_id);

      // Get book details
      const book = await booksAPI.get(lesson.book_id);

      // Get all units in lesson to calculate question number
      const allUnits = await unitsAPI.listByLesson(unit.lesson_id);
      const questions = allUnits.filter(u => u.type === 'QUESTION');
      const currentQuestionIndex = questions.findIndex(q => q.unit_id === unit.unit_id);
      const questionNumber = currentQuestionIndex >= 0 ? currentQuestionIndex + 1 : 1;

      // Calculate progress percentage
      const totalQuestions = questions.length;
      const answeredQuestions = currentQuestionIndex >= 0 ? currentQuestionIndex : 0;
      const progressPercentage = totalQuestions > 0
        ? Math.round((answeredQuestions / totalQuestions) * 100)
        : 0;

      setResumeInfo({
        book,
        lesson,
        unit,
        questionNumber,
        totalQuestions: questions.length,
        progressPercentage,
      });
    } catch (err) {
      console.error('[Start] Failed to load resume info:', err);
      // 에러 발생 시 resume 정보 없이 계속 진행 (새로 시작만 가능)
    } finally {
      setLoading(false);
    }
  };

  // Auto-announce on load
  const autoAnnounceMessage = resumeInfo
    ? `점글이 수능 학습 도우미입니다. 마지막으로 ${resumeInfo.book.title} ${resumeInfo.lesson.title} ${resumeInfo.questionNumber}번 문제에서 멈췄습니다. 1번을 눌러 이어하기, 2번을 눌러 새로 시작하세요.`
    : '점글이 수능 학습 도우미입니다. 2번을 눌러 교재를 선택하세요.';

  useAutoGuidance(autoAnnounceMessage, [loading, resumeInfo]);

  // Keyboard shortcuts
  useKeyboardShortcuts(
    {
      '1': () => handleResume(),
      '2': () => handleNewStart(),
      'h': () => handleHelp(),
      'q': () => handleQuit(),
    },
    [resumeInfo]
  );

  const handleResume = () => {
    if (!resumeInfo) {
      showToastMsg('진행 중인 학습이 없습니다. 새로 시작하세요.');
      return;
    }

    // Navigate to the current unit
    navigate(`/unit/${resumeInfo.unit.unit_id}`);
  };

  const handleNewStart = () => {
    navigate('/books');
  };

  const handleHelp = () => {
    const helpMessage = '1번: 학습 재개. 2번: 새로 시작. H키: 도움말. Q키: 종료.';
    showToastMsg(helpMessage);
  };

  const handleQuit = () => {
    showToastMsg('앱을 종료하려면 브라우저를 닫으세요.');
  };

  const showToastMsg = (message: string) => {
    setToastMessage(message);
    setShowToast(true);
  };

  if (loading) {
    return (
      <AppShellMobile title="점글이" className="relative h-screen flex flex-col">
        <div className="flex items-center justify-center flex-1">
          <p className="text-muted">로딩 중...</p>
        </div>
      </AppShellMobile>
    );
  }

  return (
    <AppShellMobile 
      className="relative h-screen flex flex-col"
      showHeader={false}
      showFooter={false}
    >
      <div className="flex-1 flex flex-col items-center justify-center px-6 py-8">
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-extrabold mb-2 gradient-text">
            점글이 수능 학습
          </h1>
          <p className="text-sm text-muted">접근성을 위한 학습 도우미</p>
        </div>

        <div className="w-full max-w-md space-y-4">
          {/* Resume Option */}
          {resumeInfo ? (
            <button
              onClick={handleResume}
              className="w-full p-6 text-white rounded-2xl 
                         shadow-lg hover:shadow-glow transition-all duration-300 
                         hover:scale-[1.02] active:scale-[0.98] text-left
                         border border-primary-light/20"
              style={{ background: 'linear-gradient(135deg, rgb(49, 130, 246) 0%, rgb(96, 165, 250) 100%)' }}
              aria-label={`1번: 학습 재개 - ${resumeInfo.book.title} ${resumeInfo.lesson.title} ${resumeInfo.questionNumber}번 문제`}
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-lg font-bold">[1] 학습 재개</span>
                <span className="text-sm bg-white/20 px-3 py-1 rounded-full font-semibold">
                  {resumeInfo.progressPercentage}%
                </span>
              </div>
              <div className="text-sm space-y-1.5 opacity-95">
                <p className="font-medium">{resumeInfo.book.title}</p>
                <p>{resumeInfo.lesson.title}</p>
                <p className="font-semibold mt-2">
                  {resumeInfo.questionNumber}번 문제 / 총 {resumeInfo.totalQuestions}문제
                </p>
              </div>
            </button>
          ) : (
            <div 
              className="w-full p-6 border border-border/50 rounded-2xl text-center shadow-soft"
              style={{ background: 'linear-gradient(135deg, rgb(249, 250, 251) 0%, rgb(255, 255, 255) 100%)' }}
            >
              <p className="text-sm text-muted">진행 중인 학습이 없습니다</p>
            </div>
          )}

          {/* New Start Option */}
          <button
            onClick={handleNewStart}
            className="w-full p-6 border border-border/50 rounded-2xl 
                       shadow-soft hover:shadow-soft-lg hover:border-primary/30
                       transition-all duration-300 hover:scale-[1.01] active:scale-[0.99] text-left
                       hover:bg-card-hover"
              style={{ background: 'linear-gradient(135deg, rgb(249, 250, 251) 0%, rgb(255, 255, 255) 100%)' }}
            aria-label="2번: 새로 시작 - 교재 선택으로 이동"
          >
            <div className="text-lg font-bold mb-2 text-fg">[2] 새로 시작</div>
            <p className="text-sm text-muted">교재 선택으로 이동</p>
          </button>

          {/* Help */}
          <div className="flex justify-center gap-3 pt-6">
            <button
              onClick={handleHelp}
              className="px-4 py-2.5 text-sm text-muted hover:text-primary 
                         hover:bg-primary/5 rounded-xl transition-all duration-300
                         border border-transparent hover:border-primary/20"
              aria-label="H키: 도움말"
            >
              [H] 도움말
            </button>
            <button
              onClick={handleQuit}
              className="px-4 py-2.5 text-sm text-muted hover:text-primary 
                         hover:bg-primary/5 rounded-xl transition-all duration-300
                         border border-transparent hover:border-primary/20"
              aria-label="Q키: 종료"
            >
              [Q] 종료
            </button>
          </div>
        </div>

        {/* Keyboard hints */}
        <div className="mt-8 text-xs text-muted text-center">
          <p 
            className="px-4 py-2 rounded-xl border border-border/30 inline-block"
            style={{ background: 'rgba(249, 250, 251, 0.5)' }}
          >
            키보드로 조작: 1 (재개), 2 (새로시작), H (도움말), Q (종료)
          </p>
        </div>
      </div>

      <ToastA11y
        message={toastMessage}
        isVisible={showToast}
        duration={3000}
        onClose={() => setShowToast(false)}
      />
    </AppShellMobile>
  );
}
