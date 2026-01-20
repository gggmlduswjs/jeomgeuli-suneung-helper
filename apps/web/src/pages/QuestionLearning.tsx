/**
 * Question Learning Screen - Core learning experience
 * Merged from Unit.tsx and Question.tsx with keyboard-first design
 */
import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { unitsAPI } from '../services/units';
import { answersAPI } from '../services/answers';
import { progressAPI } from '../services/progress';
import { lessonsAPI } from '../services/lessons';
import { booksAPI } from '../services/books';
import { aiAPI } from '../services/ai';
import type { Unit } from '../types/unit';
import type { Lesson } from '../types/lesson';
import type { Book } from '../types/book';
import { useKeyboardShortcuts } from '../contexts/KeyboardContext';
import { useAutoGuidance, useConditionalGuidance } from '../hooks/useAutoGuidance';
import { useAutoBraille } from '../hooks/useAutoBraille';
import { useTTS } from '../hooks/useTTS';
import AppShellMobile from '../components/ui/AppShellMobile';
import ToastA11y from '../components/system/ToastA11y';
import UnitViewer from '../components/unit/UnitViewer';
import AnswerInput from '../components/question/AnswerInput';
import AnswerResultComponent from '../components/question/AnswerResult';

interface AnswerResult {
  is_correct: boolean;
  correct_answer: number;
  explanation?: string;
}

export default function QuestionLearning() {
  const navigate = useNavigate();
  const { bookId, lessonId, questionId } = useParams<{
    bookId: string;
    lessonId: string;
    questionId: string;
  }>();

  const { speak, stop: stopTTS, pause, resume, isPaused } = useTTS();

  const [currentUnit, setCurrentUnit] = useState<Unit | null>(null);
  const [book, setBook] = useState<Book | null>(null);
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [allUnits, setAllUnits] = useState<Unit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Question state
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [answerResult, setAnswerResult] = useState<AnswerResult | null>(null);
  const [showAIExplanation, setShowAIExplanation] = useState(false);
  const [aiExplanation, setAiExplanation] = useState<string | null>(null);
  const [isAiLoading, setIsAiLoading] = useState(false);

  // UI state
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');

  // Load question data
  useEffect(() => {
    if (questionId) {
      loadQuestion(questionId);
    }
  }, [questionId]);

  const loadQuestion = async (unitId: string) => {
    setLoading(true);
    setError(null);
    setSelectedAnswer(null);
    setAnswerResult(null);
    setShowAIExplanation(false);
    setAiExplanation(null);

    try {
      // Load unit
      const unit = await unitsAPI.get(unitId);
      setCurrentUnit(unit);

      // Load lesson
      const lessonData = await lessonsAPI.get(unit.lesson_id);
      setLesson(lessonData);

      // Load book
      const bookData = await booksAPI.get(lessonData.book_id);
      setBook(bookData);

      // Load all units in lesson
      const units = await unitsAPI.list(unit.lesson_id);
      setAllUnits(units);

      // Save progress
      await progressAPI.save({
        user_id: 'u_demo',
        unit_id: unitId,
        lesson_id: unit.lesson_id,
        book_id: lessonData.book_id,
      });
    } catch (err) {
      console.error('[QuestionLearning] Failed to load question:', err);
      setError('문제를 불러오는 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  // Get unit number and total (전체 유닛 순서)
  const unitNumber = currentUnit ? currentUnit.order + 1 : 0;
  const totalUnits = allUnits.length;

  // Get unit type label
  const getUnitTypeLabel = (unit: Unit | null) => {
    if (!unit) return '유닛';
    switch (unit.type) {
      case 'CONCEPT_CORE':
      case 'CONCEPT_FORM':
      case 'CONCEPT_CONTENT':
        return '개념';
      case 'PASSAGE':
        return '본문';
      case 'QUESTION':
        return '문제';
      case 'CONCEPT_SUMMARY':
        return '요약';
      default:
        return '유닛';
    }
  };

  const unitTypeLabel = getUnitTypeLabel(currentUnit);

  // Auto-announce on load
  const autoAnnounceMessage = currentUnit && lesson
    ? `${lesson.title} ${unitTypeLabel} ${unitNumber}입니다.`
    : '';

  useAutoGuidance(autoAnnounceMessage, [currentUnit?.unit_id]);

  // Auto-announce answer result
  useConditionalGuidance(
    answerResult
      ? answerResult.is_correct
        ? '정답입니다!'
        : `오답입니다. 정답은 ${answerResult.correct_answer}번입니다.`
      : '',
    !!answerResult,
    [answerResult]
  );

  // Auto-braille output
  const brailleContent = currentUnit?.question?.stem || currentUnit?.content_text || '';
  useAutoBraille(brailleContent, {
    enabled: !loading && !!currentUnit,
    strategy: 'sentence',
    subject: 'korean',
  });

  // Keyboard shortcuts
  const shortcuts: Record<string, () => void> = {
    enter: () => handleEnterKey(),
    tab: () => handleToggleAI(),
    space: () => handlePauseTTS(),
    arrowleft: () => handlePrevQuestion(),
    arrowright: () => handleNextQuestion(),
    m: () => handleQuestionList(),
    q: () => handleSummary(),
    b: () => handleBack(),
    r: () => handleReplay(),
  };

  // Add number shortcuts for answer selection (1-5)
  if (currentUnit?.type === 'QUESTION' && !answerResult) {
    for (let i = 1; i <= 5; i++) {
      shortcuts[i.toString()] = () => handleSelectAnswer(i);
    }
  }

  useKeyboardShortcuts(shortcuts, [currentUnit, selectedAnswer, answerResult, showAIExplanation]);

  const handleSelectAnswer = (answer: number) => {
    if (!currentUnit?.question?.choices || answer > currentUnit.question.choices.length) {
      return;
    }

    setSelectedAnswer(answer);
    showToastMsg(`${answer}번 선택`);
  };

  const handleEnterKey = () => {
    if (answerResult) {
      // Already answered, go to next question
      handleNextQuestion();
    } else if (selectedAnswer !== null) {
      // Submit answer
      handleSubmitAnswer();
    } else {
      // No answer selected - skip to next (for non-question units or skipping questions)
      handleNextQuestion();
    }
  };

  const handleSubmitAnswer = async () => {
    if (!currentUnit || currentUnit.type !== 'QUESTION' || !currentUnit.question || selectedAnswer === null) {
      return;
    }

    const isCorrect = currentUnit.question.answer === selectedAnswer;

    try {
      // Submit answer
      await answersAPI.submit({
        user_id: 'u_demo',
        unit_id: currentUnit.unit_id,
        selected: selectedAnswer,
        is_correct: isCorrect,
      });

      // Set result
      setAnswerResult({
        is_correct: isCorrect,
        correct_answer: currentUnit.question.answer || 0,
        explanation: isCorrect ? '정답입니다!' : '오답입니다.',
      });

      // Auto-load AI explanation for incorrect answers
      if (!isCorrect) {
        loadAIExplanation();
      }
    } catch (err) {
      console.error('[QuestionLearning] Failed to submit answer:', err);
      showToastMsg('답안 제출 중 오류가 발생했습니다.');
    }
  };

  const handleToggleAI = () => {
    if (!currentUnit) return;

    if (showAIExplanation) {
      setShowAIExplanation(false);
      stopTTS();
    } else {
      setShowAIExplanation(true);
      if (!aiExplanation && !isAiLoading) {
        loadAIExplanation();
      } else if (aiExplanation) {
        speak(aiExplanation);
      }
    }
  };

  const loadAIExplanation = async () => {
    if (!currentUnit) return;

    setIsAiLoading(true);
    try {
      const response = await aiAPI.teachUnit(currentUnit.unit_id);
      setAiExplanation(response.explanation);

      if (response.explanation) {
        speak(response.explanation);
      }
    } catch (err) {
      console.error('[QuestionLearning] Failed to load AI explanation:', err);
      showToastMsg('AI 설명을 불러오는 중 오류가 발생했습니다.');
    } finally {
      setIsAiLoading(false);
    }
  };

  const handlePauseTTS = () => {
    if (isPaused) {
      resume();
    } else {
      pause();
    }
  };

  const handlePrevQuestion = () => {
    // 전체 유닛 순서대로 이동
    const currentIndex = allUnits.findIndex(u => u.unit_id === currentUnit?.unit_id);

    if (currentIndex > 0) {
      const prevUnit = allUnits[currentIndex - 1];
      navigate(`/learn/${bookId}/${lessonId}/${prevUnit.unit_id}`);
    } else {
      showToastMsg('첫 번째 유닛입니다.');
    }
  };

  const handleNextQuestion = () => {
    // 전체 유닛 순서대로 이동
    const currentIndex = allUnits.findIndex(u => u.unit_id === currentUnit?.unit_id);

    if (currentIndex < allUnits.length - 1) {
      const nextUnit = allUnits[currentIndex + 1];
      navigate(`/learn/${bookId}/${lessonId}/${nextUnit.unit_id}`);
    } else {
      // End of lesson, go to summary
      navigate('/summary');
    }
  };

  const handleQuestionList = () => {
    if (lessonId) {
      navigate(`/questions/${lessonId}`);
    }
  };

  const handleSummary = () => {
    navigate('/summary');
  };

  const handleBack = () => {
    navigate('/books');
  };

  const handleReplay = () => {
    if (currentUnit) {
      const message = `${lesson?.title} ${unitTypeLabel} ${unitNumber}입니다.`;
      speak(message);
    }
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

  if (error || !currentUnit) {
    return (
      <AppShellMobile 
        className="relative h-screen flex flex-col"
        showHeader={false}
        showFooter={false}
      >
        <div className="flex items-center justify-center flex-1">
          <div className="text-center">
            <p className="text-error mb-4">{error || '문제를 찾을 수 없습니다.'}</p>
            <button
              onClick={() => navigate('/books')}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg"
            >
              교재 선택으로 돌아가기
            </button>
          </div>
        </div>
      </AppShellMobile>
    );
  }

  return (
    <AppShellMobile
      title={`${book?.title || ''} [${unitNumber}/${totalUnits}]`}
      className="relative h-screen flex flex-col"
    >
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="px-4 py-3 border-b border-border">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold">{lesson?.title}</h2>
              <p className="text-sm text-muted-foreground">
                {unitTypeLabel} {unitNumber} / {totalUnits}
              </p>
            </div>
            <div className="text-sm text-muted-foreground">
              {Math.round((unitNumber / totalUnits) * 100)}%
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
          {/* Unit content */}
          {currentUnit.type !== 'QUESTION' ? (
            <UnitViewer unit={currentUnit} onSpeak={speak} />
          ) : (
            <>
              {/* Question display */}
              <div className="bg-card border border-border rounded-lg p-4">
                <h3 className="text-sm font-semibold text-muted-foreground mb-2">문제</h3>
                
                {/* 문제 이미지 표시 */}
                {currentUnit.image_path && (
                  <div className="mb-4 border border-border/50 rounded-lg overflow-hidden">
                    <img 
                      src={currentUnit.image_path} 
                      alt={currentUnit.title}
                      className="w-full h-auto"
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = 'none';
                      }}
                    />
                  </div>
                )}
                
                {/* 문제 지문 표시 (더미 데이터가 아닌 경우만) */}
                {currentUnit.question?.stem && !currentUnit.question.stem.includes('(페이지') && (
                  <p className="text-base whitespace-pre-wrap mb-4">
                    {currentUnit.question.stem}
                  </p>
                )}

                {/* Choices */}
                {currentUnit.question?.choices && currentUnit.question.choices.length > 0 && (
                  <div className="space-y-2">
                    <h4 className="text-sm font-semibold text-muted-foreground">선택지</h4>
                    {currentUnit.question.choices.map((choice, index) => {
                      const choiceNum = index + 1;
                      const isSelected = selectedAnswer === choiceNum;
                      const isCorrect = answerResult && choiceNum === answerResult.correct_answer;
                      const isWrong = answerResult && isSelected && !answerResult.is_correct;

                      return (
                        <button
                          key={index}
                          onClick={() => !answerResult && handleSelectAnswer(choiceNum)}
                          disabled={!!answerResult}
                          className={`w-full p-3 text-left rounded-lg transition-colors ${
                            isCorrect
                              ? 'bg-success/20 border-2 border-success'
                              : isWrong
                              ? 'bg-error/20 border-2 border-error'
                              : isSelected
                              ? 'bg-primary/20 border-2 border-primary'
                              : 'bg-muted border border-border hover:border-primary'
                          }`}
                          aria-label={`${choiceNum}번: ${choice}`}
                        >
                          <span className="font-semibold mr-2">{choiceNum}.</span>
                          {choice}
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Answer result */}
              {answerResult && (
                <div
                  className={`p-4 rounded-lg ${
                    answerResult.is_correct
                      ? 'bg-success/20 border border-success'
                      : 'bg-error/20 border border-error'
                  }`}
                >
                  <p className="font-semibold">
                    {answerResult.is_correct ? '✓ 정답입니다!' : '✗ 오답입니다.'}
                  </p>
                  {!answerResult.is_correct && (
                    <p className="text-sm mt-1">정답: {answerResult.correct_answer}번</p>
                  )}
                </div>
              )}
            </>
          )}

          {/* AI Explanation */}
          {showAIExplanation && (
            <div className="bg-info/10 border border-info rounded-lg p-4">
              <h3 className="text-sm font-semibold text-info mb-2">AI 설명</h3>
              {isAiLoading ? (
                <p className="text-sm text-muted-foreground">AI가 설명을 생성하고 있습니다...</p>
              ) : aiExplanation ? (
                <p className="text-sm whitespace-pre-wrap">{aiExplanation}</p>
              ) : (
                <p className="text-sm text-muted-foreground">설명을 불러올 수 없습니다.</p>
              )}
            </div>
          )}
        </div>

        {/* Footer - Keyboard shortcuts */}
        <div className="px-4 py-3 border-t border-border bg-background">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <div className="space-x-2">
              <span>[Enter] {answerResult ? '다음' : '제출'}</span>
              <span>[←→] 이동</span>
              <span>[Tab] AI설명</span>
            </div>
            <div className="space-x-2">
              <span>[M] 목록</span>
              <span>[Q] 종료</span>
              <span>[B] 뒤로</span>
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
