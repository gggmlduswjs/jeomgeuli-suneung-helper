/**
 * Question List Screen - Navigate through all questions in a lesson
 * Shows completion status and allows quick jumps
 */
import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { lessonsAPI } from '../services/lessons';
import { unitsAPI } from '../services/units';
import { progressAPI } from '../services/progress';
import type { Unit } from '../types/unit';
import type { Lesson } from '../types/lesson';
import { useKeyboardShortcuts } from '../contexts/KeyboardContext';
import { useAutoGuidance } from '../hooks/useAutoGuidance';
import AppShellMobile from '../components/ui/AppShellMobile';
import ToastA11y from '../components/system/ToastA11y';

interface QuestionWithStatus extends Unit {
  status: 'unanswered' | 'correct' | 'incorrect';
  isCurrent: boolean;
}

export default function QuestionList() {
  const navigate = useNavigate();
  const { lessonId } = useParams<{ lessonId: string }>();

  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [questions, setQuestions] = useState<QuestionWithStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const [currentQuestionId, setCurrentQuestionId] = useState<string | null>(null);

  // Load questions
  useEffect(() => {
    if (lessonId) {
      loadQuestions(lessonId);
    }
  }, [lessonId]);

  const loadQuestions = async (id: string) => {
    setLoading(true);
    try {
      // Load lesson info
      const lessonData = await lessonsAPI.get(id);
      setLesson(lessonData);

      // Load units
      const units = await unitsAPI.list(id);
      const questionUnits = units.filter(u => u.type === 'QUESTION');

      // Get current progress
      const progress = await progressAPI.getContinue('u_demo');
      const currentUnitId = progress?.unit_id;
      setCurrentQuestionId(currentUnitId || null);

      // Find current question index
      const currentIndex = questionUnits.findIndex(q => q.unit_id === currentUnitId);
      if (currentIndex >= 0) {
        setSelectedIndex(currentIndex);
      }

      // TODO: Get answer status for each question
      // For now, just mark questions before current as answered
      const questionsWithStatus: QuestionWithStatus[] = questionUnits.map((q, index) => ({
        ...q,
        status: index < currentIndex ? 'correct' : 'unanswered',
        isCurrent: q.unit_id === currentUnitId,
      }));

      setQuestions(questionsWithStatus);
    } catch (err) {
      console.error('[QuestionList] Failed to load questions:', err);
    } finally {
      setLoading(false);
    }
  };

  // Auto-announce on load
  const autoAnnounceMessage = lesson && questions.length > 0
    ? `${lesson.title} 문제 목록. 총 ${questions.length}문제. 위아래 화살표로 이동하고 엔터키로 선택하세요.`
    : '';

  useAutoGuidance(autoAnnounceMessage, [loading, lesson]);

  // Keyboard shortcuts
  const shortcuts: Record<string, () => void> = {
    arrowup: () => handleNavigateUp(),
    arrowdown: () => handleNavigateDown(),
    enter: () => handleSelectCurrent(),
    b: () => handleBack(),
  };

  // Add number shortcuts for direct jump (1-9, then 0-9 for second digit)
  for (let i = 1; i <= 9; i++) {
    shortcuts[i.toString()] = () => handleNumberKey(i);
  }
  shortcuts['0'] = () => handleNumberKey(0);

  useKeyboardShortcuts(shortcuts, [selectedIndex, questions]);

  const [numberBuffer, setNumberBuffer] = useState<number[]>([]);
  const [numberTimer, setNumberTimer] = useState<NodeJS.Timeout | null>(null);

  const handleNumberKey = (digit: number) => {
    // Clear existing timer
    if (numberTimer) {
      clearTimeout(numberTimer);
    }

    const newBuffer = [...numberBuffer, digit];
    setNumberBuffer(newBuffer);

    // Set timer to execute jump after 500ms
    const timer = setTimeout(() => {
      const number = parseInt(newBuffer.join(''));
      if (number > 0 && number <= questions.length) {
        setSelectedIndex(number - 1);
        announceQuestion(number - 1);
      } else {
        showToastMsg('잘못된 번호입니다.');
      }
      setNumberBuffer([]);
    }, 500);

    setNumberTimer(timer);
  };

  const handleNavigateUp = () => {
    if (selectedIndex > 0) {
      const newIndex = selectedIndex - 1;
      setSelectedIndex(newIndex);
      announceQuestion(newIndex);
    }
  };

  const handleNavigateDown = () => {
    if (selectedIndex < questions.length - 1) {
      const newIndex = selectedIndex + 1;
      setSelectedIndex(newIndex);
      announceQuestion(newIndex);
    }
  };

  const announceQuestion = (index: number) => {
    const question = questions[index];
    if (question) {
      const statusText =
        question.status === 'correct'
          ? '정답'
          : question.status === 'incorrect'
          ? '오답'
          : '미학습';
      const currentText = question.isCurrent ? ', 현재 위치' : '';
      showToastMsg(`${index + 1}번: ${question.title}, ${statusText}${currentText}`);
    }
  };

  const handleSelectCurrent = () => {
    if (selectedIndex >= 0 && selectedIndex < questions.length) {
      const question = questions[selectedIndex];
      const bookId = lesson?.book_id;

      if (bookId && lessonId && question.unit_id) {
        navigate(`/learn/${bookId}/${lessonId}/${question.unit_id}`);
      }
    }
  };

  const handleBack = () => {
    // Go back to current question if there is one
    if (currentQuestionId && lesson?.book_id && lessonId) {
      navigate(`/learn/${lesson.book_id}/${lessonId}/${currentQuestionId}`);
    } else {
      navigate('/books');
    }
  };

  const showToastMsg = (message: string) => {
    setToastMessage(message);
    setShowToast(true);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'correct':
        return '✓';
      case 'incorrect':
        return '✗';
      default:
        return '○';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'correct':
        return 'text-success';
      case 'incorrect':
        return 'text-error';
      default:
        return 'text-muted-foreground';
    }
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

  const completedCount = questions.filter(q => q.status === 'correct').length;
  const progressPercentage = questions.length > 0
    ? Math.round((completedCount / questions.length) * 100)
    : 0;

  return (
    <AppShellMobile 
      className="relative h-screen flex flex-col"
      showHeader={false}
      showFooter={false}
    >
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="px-4 py-3 border-b border-border">
          <h2 className="text-lg font-semibold">{lesson?.title}</h2>
          <p className="text-sm text-muted-foreground">
            {questions.length}문제 중 {completedCount}문제 완료 ({progressPercentage}%)
          </p>
        </div>

        {/* Question list */}
        <div className="flex-1 overflow-y-auto px-4 py-4">
          {questions.length === 0 ? (
            <div className="text-center py-8 text-muted">
              <p>문제가 없습니다.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {questions.map((question, index) => {
                const isSelected = selectedIndex === index;

                return (
                  <button
                    key={question.unit_id}
                    onClick={() => {
                      setSelectedIndex(index);
                      handleSelectCurrent();
                    }}
                    onMouseEnter={() => setSelectedIndex(index)}
                    className={`w-full p-4 text-left rounded-lg transition-colors ${
                      question.isCurrent
                        ? 'bg-primary text-primary-foreground'
                        : isSelected
                        ? 'bg-secondary text-secondary-foreground'
                        : 'bg-card border border-border hover:border-primary'
                    }`}
                    aria-label={`${index + 1}번: ${question.title}`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className={`text-lg ${getStatusColor(question.status)}`}>
                          {getStatusIcon(question.status)}
                        </span>
                        <div>
                          <div className="font-semibold">
                            {index + 1}번
                            {question.isCurrent && (
                              <span className="ml-2 text-xs opacity-75">(현재)</span>
                            )}
                          </div>
                          <div className="text-sm opacity-90">{question.title}</div>
                        </div>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-3 border-t border-border bg-background">
          <div className="flex items-center justify-between">
            <button
              onClick={handleBack}
              className="px-4 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              [B] 뒤로가기
            </button>
            <div className="text-xs text-muted-foreground">
              [↑↓] 이동 | [Enter] 선택 | [1-9] 빠른 이동
            </div>
          </div>
        </div>
      </div>

      <ToastA11y
        message={toastMessage}
        isVisible={showToast}
        duration={2000}
        onClose={() => setShowToast(false)}
      />
    </AppShellMobile>
  );
}
