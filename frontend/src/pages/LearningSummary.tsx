/**
 * Learning Summary Screen - Session completion and stats
 * Shows progress and next steps
 */
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { progressAPI } from '../services/progress';
import { unitsAPI, lessonsAPI, booksAPI } from '../services/api/client';
import type { Progress } from '../types/progress';
import type { Book } from '../types/book';
import type { Lesson } from '../types/lesson';
import { useKeyboardShortcuts } from '../contexts/KeyboardContext';
import { useAutoGuidance } from '../hooks/useAutoGuidance';
import AppShellMobile from '../components/ui/AppShellMobile';
import ToastA11y from '../components/system/ToastA11y';

interface SessionStats {
  questionsCompleted: number;
  correctAnswers: number;
  accuracy: number;
  timeSpent: string;
}

export default function LearningSummary() {
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [currentProgress, setCurrentProgress] = useState<Progress | null>(null);
  const [book, setBook] = useState<Book | null>(null);
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [sessionStats, setSessionStats] = useState<SessionStats>({
    questionsCompleted: 0,
    correctAnswers: 0,
    accuracy: 0,
    timeSpent: '0분',
  });
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const [totalQuestions, setTotalQuestions] = useState(0);

  // Load summary data
  useEffect(() => {
    loadSummary();
  }, []);

  const loadSummary = async () => {
    setLoading(true);
    try {
      // Get current progress
      const progress = await progressAPI.getContinue('u_demo');
      setCurrentProgress(progress);

      if (progress?.unit_id) {
        // Load unit to get lesson and book info
        const unit = await unitsAPI.get(progress.unit_id);
        const lessonData = await lessonsAPI.get(unit.lesson_id);
        const bookData = await booksAPI.get(lessonData.book_id);

        setLesson(lessonData);
        setBook(bookData);
      }

      // FIXME: 실제 세션 통계 계산 필요
      // 요구사항:
      // 1. 세션 시작/종료 시간 추적용 sessionStore 생성
      // 2. 답변 제출 시 정답/오답 누적 저장
      // 3. answersAPI에서 세션 통계 조회 API 추가
      // 현재는 플레이스홀더 값 사용
      setSessionStats({
        questionsCompleted: 0, // TODO: 실제 완료한 문제 수 조회 필요
        correctAnswers: 0, // answersAPI에서 조회 필요
        accuracy: 0, // 계산 필요
        timeSpent: '0분', // sessionStore에서 조회 필요
      });
    } catch (err) {
      console.error('[LearningSummary] Failed to load summary:', err);
    } finally {
      setLoading(false);
    }
  };

  // Auto-announce on load
  const autoAnnounceMessage = sessionStats.questionsCompleted > 0
    ? `학습 종료. 오늘 ${sessionStats.questionsCompleted}문제를 학습했습니다. 정답률은 ${sessionStats.accuracy}퍼센트입니다. 1번을 눌러 다음 강의로, 2번을 눌러 처음으로 이동하세요.`
    : '학습 종료. 1번을 눌러 처음으로 이동하세요.';

  useAutoGuidance(autoAnnounceMessage, [loading, sessionStats]);

  // Load total questions count
  useEffect(() => {
    const loadTotalQuestions = async () => {
      if (lesson?.lesson_id) {
        try {
          const units = await unitsAPI.listByLesson(lesson.lesson_id);
          const questionCount = units.filter(u => u.type === 'QUESTION').length;
          setTotalQuestions(questionCount);
        } catch (err) {
          console.error('[LearningSummary] Failed to load units:', err);
          // Fallback to lesson.question_count if available
          setTotalQuestions(lesson.question_count || 0);
        }
      } else {
        setTotalQuestions(lesson?.question_count || 0);
      }
    };
    
    loadTotalQuestions();
  }, [lesson]);

  // Keyboard shortcuts
  useKeyboardShortcuts(
    {
      '1': () => handleContinue(),
      '2': () => handleGoHome(),
    },
    [currentProgress]
  );

  const handleContinue = async () => {
    if (!lesson?.book_id || !lesson?.lesson_id) {
      showToastMsg('이어할 학습이 없습니다.');
      return;
    }

    try {
      // Get all lessons for this book
      const allLessons = await lessonsAPI.listByBook(lesson.book_id);
      
      // Find current lesson index
      const currentLessonIndex = allLessons.findIndex(
        l => l.lesson_id === lesson.lesson_id
      );
      
      // Find next lesson
      const nextLessonIndex = currentLessonIndex + 1;
      
      if (nextLessonIndex < allLessons.length) {
        // Go to next lesson
        const nextLesson = allLessons[nextLessonIndex];
        
        // Get first unit (preferably QUESTION) from next lesson
        const units = await unitsAPI.listByLesson(nextLesson.lesson_id);
        
        if (units.length === 0) {
          showToastMsg('다음 강의에 학습 단위가 없습니다.');
          return;
        }
        
        // Find first question or first unit
        const firstQuestion = units.find(u => u.type === 'QUESTION');
        const firstUnit = firstQuestion || units[0];
        
        // Navigate to next lesson - use first available unit
        const targetUnit = firstQuestion || firstUnit;
        navigate(`/unit/${targetUnit.unit_id}`);
        
        showToastMsg(`${nextLesson.title}로 이동합니다.`);
      } else {
        // No next lesson, go to first lesson or home
        if (allLessons.length > 0) {
          const firstLesson = allLessons[0];
          const units = await unitsAPI.listByLesson(firstLesson.lesson_id);
          
            if (units.length > 0) {
              const firstQuestion = units.find(u => u.type === 'QUESTION');
              const firstUnit = firstQuestion || units[0];
              const targetUnit = firstQuestion || firstUnit;
              navigate(`/unit/${targetUnit.unit_id}`);
            
            showToastMsg('모든 강의를 완료했습니다. 첫 번째 강의로 이동합니다.');
          } else {
            navigate('/');
            showToastMsg('모든 강의를 완료했습니다.');
          }
        } else {
          navigate('/');
          showToastMsg('강의가 없습니다.');
        }
      }
    } catch (err) {
      console.error('[LearningSummary] Failed to continue:', err);
      showToastMsg('다음 강의로 이동하는 중 오류가 발생했습니다.');
    }
  };

  const handleGoHome = () => {
    navigate('/');
  };

  const showToastMsg = (message: string) => {
    setToastMessage(message);
    setShowToast(true);
  };

  if (loading) {
    return (
      <AppShellMobile 
        className="relative h-screen flex flex-col"
        showHeader={false}
        showFooter={false}
      >
        <div className="flex items-center justify-center flex-1">
          <p className="text-muted">로딩 중...</p>
        </div>
      </AppShellMobile>
    );
  }

  const progressPercentage = totalQuestions > 0
    ? Math.min(100, Math.round((sessionStats.questionsCompleted / totalQuestions) * 100))
    : 0;

  return (
    <AppShellMobile 
      className="relative h-screen flex flex-col"
      showHeader={false}
      showFooter={false}
    >
      <div className="flex-1 flex flex-col items-center justify-center px-6 py-8">
        <h1 className="text-3xl font-bold mb-8">학습 종료</h1>

        {/* Session stats */}
        <div className="w-full max-w-md space-y-6">
          <div className="bg-card border border-border rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">오늘의 학습</h2>

            <div className="space-y-3 text-sm">
              <div className="flex items-center justify-between py-2 border-b border-border">
                <span className="text-muted-foreground">학습 문제</span>
                <span className="font-semibold">{sessionStats.questionsCompleted}개</span>
              </div>

              <div className="flex items-center justify-between py-2 border-b border-border">
                <span className="text-muted-foreground">정답률</span>
                <span className="font-semibold text-success">
                  {sessionStats.accuracy}% ({sessionStats.correctAnswers}/{sessionStats.questionsCompleted})
                </span>
              </div>

              <div className="flex items-center justify-between py-2">
                <span className="text-muted-foreground">학습 시간</span>
                <span className="font-semibold">{sessionStats.timeSpent}</span>
              </div>
            </div>
          </div>

          {/* Overall progress */}
          {book && lesson && (
            <div className="bg-card border border-border rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">전체 진행률</h2>

              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-muted-foreground">{book.title}</span>
                    <span className="font-semibold">{progressPercentage}%</span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-3">
                    <div
                      className="bg-primary h-3 rounded-full transition-all"
                      style={{ width: `${progressPercentage}%` }}
                    />
                  </div>
                </div>

                <p className="text-sm text-muted-foreground">
                  {lesson.title}: {totalQuestions}문제 중 {sessionStats.questionsCompleted}문제 완료
                </p>
              </div>
            </div>
          )}

          {/* Action buttons */}
          <div className="space-y-3">
            <button
              onClick={handleContinue}
              className="w-full p-4 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors text-left"
              aria-label="1번: 다음 강의로"
            >
              <div className="text-lg font-semibold">[1] 다음 강의로</div>
              <p className="text-sm opacity-90 mt-1">학습 계속하기</p>
            </button>

            <button
              onClick={handleGoHome}
              className="w-full p-4 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/90 transition-colors text-left"
              aria-label="2번: 처음으로"
            >
              <div className="text-lg font-semibold">[2] 처음으로</div>
              <p className="text-sm opacity-90 mt-1">시작 화면으로 이동</p>
            </button>
          </div>
        </div>

        {/* Keyboard hints */}
        <div className="mt-8 text-xs text-muted-foreground text-center">
          <p>키보드로 조작: 1 (계속), 2 (처음으로)</p>
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
