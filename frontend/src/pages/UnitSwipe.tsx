/**
 * 학습 단위 페이지 (카드 스와이프 버전)
 * 좌우 스와이프로 Unit 간 이동하는 개선된 학습 화면
 */
import { useEffect, useState, useRef, useCallback } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import AppShellMobile from '../components/ui/AppShellMobile';
import SpeechBar from '../components/input/SpeechBar';
import useTTS from '../hooks/useTTS';
import useSTT from '../hooks/useSTT';
import useVoiceCommands from '../hooks/useVoiceCommands';
import { useKeyboardShortcuts } from '../contexts/KeyboardContext';
import ToastA11y from '../components/system/ToastA11y';
import UnitViewer from '../components/unit/UnitViewer';
import UnitCardSwiper from '../components/unit/UnitCardSwiper';
import AnswerInput from '../components/question/AnswerInput';
import AnswerResultComponent from '../components/question/AnswerResult';
import { answersAPI } from '../services/answers';
import AIQuestionInput from '../components/ai/AIQuestionInput';
import AIExplanationCard from '../components/unit/AIExplanationCard';
import useBrailleBLE from '../hooks/useBrailleBLE';
import { useUnitData } from '../hooks/useUnitData';
import { useUnitAI } from '../hooks/useUnitAI';
import { useToast } from '../hooks/useToast';
import UnitHeader from '../components/unit/UnitHeader';
import UnitListSidebar from '../components/unit/UnitListSidebar';
import { getUnitTypeLabel, getUnitNumber, getTotalUnits } from '../utils/unitHelpers';
import { createModuleLogger } from '../utils/logger';
import { DEFAULT_USER_ID, AI_EXPLANATION_AUTO_LOAD_DELAY, MAX_ANSWER_CHOICES, ROUTES, TOAST_DURATION } from '../constants';
import type { Unit as UnitType } from '../types/unit';

const logger = createModuleLogger('UnitSwipe');

export default function UnitSwipePage() {
  const navigate = useNavigate();
  const { unitId } = useParams<{ unitId: string }>();
  const [searchParams] = useSearchParams();
  const { speak, stop: stopTTS } = useTTS();
  const { stop: stopSTT, isListening, transcript } = useSTT();
  const { showToast, toastMessage, setShowToast, showToastMessage } = useToast();

  // 데이터 로딩
  const { unit, lesson, book, allUnits, loading, error, loadUnit } = useUnitData();

  // 현재 Unit 인덱스
  const [currentUnitIndex, setCurrentUnitIndex] = useState(0);

  // 점자
  const { sendText } = useBrailleBLE();

  // AI 설명
  const {
    aiExplanation,
    isAiLoading,
    loadAIExplanation,
    reset: resetAI
  } = useUnitAI(speak, sendText);

  // 답안 상태
  const [userAnswer, setUserAnswer] = useState<number | null>(null);
  const [answerResult, setAnswerResult] = useState<{ is_correct: boolean; correct_answer: number; explanation?: string } | null>(null);
  const [showUnitList, setShowUnitList] = useState(false);

  // AI 설명 자동 로드를 위한 ref
  const loadAIExplanationRef = useRef(loadAIExplanation);
  const explanationLoadTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // ref 업데이트
  loadAIExplanationRef.current = loadAIExplanation;

  // 현재 Unit ID로 인덱스 계산
  useEffect(() => {
    if (unit && allUnits.length > 0) {
      const index = allUnits.findIndex(u => u.unit_id === unit.unit_id);
      if (index !== -1) {
        setCurrentUnitIndex(index);
      }
    }
  }, [unit, allUnits]);

  // Unit 로드 및 AI 설명 자동 로드
  useEffect(() => {
    if (!unitId) return;

    // 답안 상태 초기화
    setUserAnswer(null);
    setAnswerResult(null);
    resetAI();

    // Unit 로드
    loadUnit(unitId).then(() => {
      // AI 설명 자동 로드 (짧은 딜레이)
      explanationLoadTimeoutRef.current = setTimeout(() => {
        if (loadAIExplanationRef.current) {
          loadAIExplanationRef.current(unitId);
        }
      }, AI_EXPLANATION_AUTO_LOAD_DELAY);
    });

    // Cleanup
    return () => {
      if (explanationLoadTimeoutRef.current) {
        clearTimeout(explanationLoadTimeoutRef.current);
        explanationLoadTimeoutRef.current = null;
      }
    };
  }, [unitId, loadUnit, resetAI]);

  // 인덱스 변경 시 Unit 변경
  const handleIndexChange = useCallback((newIndex: number) => {
    if (newIndex < 0 || newIndex >= allUnits.length) return;

    const newUnit = allUnits[newIndex];
    if (newUnit && newUnit.unit_id !== unitId) {
      navigate(ROUTES.UNIT(newUnit.unit_id), { replace: true });
    }
  }, [allUnits, unitId, navigate]);

  const handleAnswer = useCallback(async (answer: number) => {
    if (!unit || unit.type !== 'QUESTION' || !unit.question) return;

    setUserAnswer(answer);

    // 정답 확인
    const isCorrect = unit.question.answer === answer;

    // 답안 제출
    try {
      await answersAPI.submit({
        user_id: DEFAULT_USER_ID,
        unit_id: unit.unit_id,
        selected: answer,
        is_correct: isCorrect,
      });

      // 결과 표시
      setAnswerResult({
        is_correct: isCorrect,
        correct_answer: unit.question!.answer || 0,
        explanation: isCorrect ? '정답입니다!' : '오답입니다.',
      });

      // 오답 시 AI 설명 자동 로드
      if (!isCorrect && loadAIExplanationRef.current) {
        loadAIExplanationRef.current(unit.unit_id);
      }
    } catch (err) {
      logger.error('답안 제출 실패:', err);
    }
  }, [unit]);

  // Unit 정보 계산
  const unitNumber = getUnitNumber(unit, allUnits);
  const totalUnits = getTotalUnits(unit, allUnits);
  const unitTypeLabel = getUnitTypeLabel(unit);

  const handleNextUnit = useCallback(() => {
    if (currentUnitIndex < allUnits.length - 1) {
      handleIndexChange(currentUnitIndex + 1);
    } else {
      // 마지막 Unit이면 학습 요약으로
      navigate(ROUTES.SUMMARY);
    }
  }, [currentUnitIndex, allUnits.length, handleIndexChange, navigate]);

  const handlePrevUnit = useCallback(() => {
    if (currentUnitIndex > 0) {
      handleIndexChange(currentUnitIndex - 1);
    } else {
      showToastMessage('첫 번째 유닛입니다.');
    }
  }, [currentUnitIndex, handleIndexChange, showToastMessage]);

  const handleEnterKey = useCallback(() => {
    if (answerResult) {
      handleNextUnit();
    } else if (userAnswer !== null && unit?.type === 'QUESTION') {
      handleAnswer(userAnswer);
    } else {
      handleNextUnit();
    }
  }, [answerResult, userAnswer, unit, handleAnswer, handleNextUnit]);

  // Keyboard shortcuts
  const shortcuts: Record<string, () => void> = {
    enter: handleEnterKey,
    tab: () => {
      if (unitId && loadAIExplanationRef.current) {
        loadAIExplanationRef.current(unitId);
      }
    },
    arrowleft: handlePrevUnit,
    arrowright: handleNextUnit,
    m: () => setShowUnitList(prev => !prev),
    q: () => navigate(ROUTES.SUMMARY),
    b: () => {
      if (lesson?.lesson_id) {
        navigate(ROUTES.LESSON(lesson.lesson_id));
      } else {
        navigate(ROUTES.BOOKS);
      }
    },
    r: () => {
      if (unitId && loadAIExplanationRef.current) {
        resetAI();
        loadAIExplanationRef.current(unitId);
      }
    },
  };

  // Add number shortcuts for answer selection (1-5)
  if (unit?.type === 'QUESTION' && !answerResult) {
    for (let i = 1; i <= MAX_ANSWER_CHOICES; i++) {
      shortcuts[i.toString()] = () => {
        if (unit?.question?.choices && i <= unit.question.choices.length) {
          setUserAnswer(i);
          showToastMessage(`${i}번 선택`);
        }
      };
    }
  }

  useKeyboardShortcuts(shortcuts, [unit, userAnswer, answerResult, lesson, allUnits, unitId, handleEnterKey, handlePrevUnit, handleNextUnit]);

  // 음성 명령어
  const { onSpeech } = useVoiceCommands({
    home: () => {
      stopTTS();
      navigate('/');
      stopSTT();
    },
    back: () => {
      if (unit?.lesson_id) {
        navigate(`/lesson/${unit.lesson_id}`);
      } else {
        navigate('/');
      }
    },
  });

  useEffect(() => {
    if (!transcript) return;
    onSpeech(transcript);
  }, [transcript, onSpeech]);

  // Unit 타입 아이콘
  const getUnitIcon = (unitType: string) => {
    const icons: Record<string, string> = {
      'CONCEPT_CORE': '📖',
      'CONCEPT_FORM': '📖',
      'CONCEPT_CONTENT': '📖',
      'CONCEPT_SUMMARY': '📖',
      'PASSAGE': '📚',
      'QUESTION': '✏️'
    };
    return icons[unitType] || '📄';
  };

  // Unit 타입별 배경색
  const getUnitTypeColor = (unitType: string) => {
    if (unitType.includes('CONCEPT')) return 'border-l-4 border-blue-500';
    if (unitType === 'PASSAGE') return 'border-l-4 border-green-500';
    if (unitType === 'QUESTION') return 'border-l-4 border-orange-500';
    return 'border-l-4 border-gray-500';
  };

  return (
    <AppShellMobile
      title={book?.title ? `${book.title}` : (unit?.title || '학습 단위')}
      className="relative h-screen flex flex-col bg-background"
    >
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="px-4 pt-4 pb-2 border-b border-border bg-background">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              {lesson && (
                <span className="text-sm text-muted-foreground">
                  {lesson.title}
                </span>
              )}
            </div>
            <button
              onClick={() => setShowUnitList(true)}
              className="p-2 hover:bg-accent rounded-lg transition-colors"
              aria-label="Unit 목록"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>

          <SpeechBar isListening={isListening} transcript={transcript} />
        </div>

        {/* 학습 단위 목록 사이드바 */}
        {showUnitList && (
          <UnitListSidebar
            units={allUnits}
            currentUnitId={unit?.unit_id || null}
            lessonTitle={lesson?.title}
            onClose={() => setShowUnitList(false)}
            getUnitTypeLabel={getUnitTypeLabel}
          />
        )}

        {/* Content with Card Swiper */}
        {loading && (
          <div className="flex-1 flex items-center justify-center">
            <p className="text-muted">로딩 중...</p>
          </div>
        )}

        {error && (
          <div className="flex-1 flex items-center justify-center px-4">
            <div className="bg-error/10 border border-error rounded-lg p-4">
              <p className="text-error">{error}</p>
            </div>
          </div>
        )}

        {!loading && !error && unit && allUnits.length > 0 && (
          <UnitCardSwiper
            currentIndex={currentUnitIndex}
            totalUnits={allUnits.length}
            onIndexChange={handleIndexChange}
            className="flex-1 flex flex-col"
          >
            {/* Unit 카드 */}
            <div className="flex-1 overflow-y-auto px-4 py-4">
              <div className={`unit-card ${getUnitTypeColor(unit.type)} bg-card rounded-2xl shadow-soft p-6 space-y-6`}>
                {/* Unit 타입 아이콘 및 제목 */}
                <div className="flex items-start gap-3">
                  <div className="text-4xl flex-shrink-0">
                    {getUnitIcon(unit.type)}
                  </div>
                  <div className="flex-1">
                    <div className="text-xs text-muted-foreground mb-1">
                      {unitTypeLabel}
                    </div>
                    <h2 className="text-2xl font-bold text-fg">{unit.title}</h2>
                  </div>
                </div>

                {/* Unit 내용 */}
                <UnitViewer unit={unit} onSpeak={speak} />

                {/* AI 설명 */}
                <AIExplanationCard
                  sectionType={unit?.type === 'CONCEPT_CORE' ? 'concept' : 'content'}
                  aiExplanation={aiExplanation}
                  loadingAI={isAiLoading}
                  onSpeak={async (text: string) => {
                    speak(text);
                    try {
                      await sendText(text);
                    } catch (err) {
                      logger.error('점자 출력 실패:', err);
                    }
                  }}
                  onLoadExplanation={() => {
                    if (unitId) {
                      resetAI();
                      loadAIExplanation(unitId);
                    }
                  }}
                />

                {/* AI 질문 입력 (개념/작품인 경우) */}
                {unit && (unit.type === 'CONCEPT_CORE' || unit.type === 'PASSAGE') && (
                  <AIQuestionInput
                    unitId={unit.unit_id}
                    lessonId={unit.lesson_id}
                    onAnswer={(answer) => {
                      logger.log('AI 답변:', answer);
                    }}
                  />
                )}

                {/* 문제인 경우 답안 입력 */}
                {unit.type === 'QUESTION' && unit.question && !answerResult && (
                  <AnswerInput
                    maxChoice={unit.question.choices?.length || 5}
                    onAnswer={handleAnswer}
                    onSpeak={speak}
                  />
                )}

                {/* 답안 결과 */}
                {answerResult && userAnswer !== null && (
                  <AnswerResultComponent
                    result={answerResult}
                    userAnswer={userAnswer}
                    onSpeak={speak}
                  />
                )}
              </div>
            </div>
          </UnitCardSwiper>
        )}

        {/* Footer - Navigation and shortcuts */}
        <div className="px-4 py-3 border-t border-border bg-background">
          <div className="flex items-center justify-between mb-2">
            <button
              onClick={handlePrevUnit}
              disabled={currentUnitIndex === 0}
              className="flex items-center gap-2 px-4 py-2 bg-accent rounded-lg hover:bg-accent/80 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              <span className="text-sm font-medium">이전</span>
            </button>

            <button
              onClick={() => setShowUnitList(true)}
              className="p-2 hover:bg-accent rounded-lg transition-colors"
              aria-label="목록"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>

            <button
              onClick={handleNextUnit}
              disabled={currentUnitIndex === allUnits.length - 1}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <span className="text-sm font-medium">
                {answerResult ? '다음' : (unit?.type === 'QUESTION' && userAnswer ? '제출' : '다음')}
              </span>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>

          {/* Keyboard shortcuts */}
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <div className="space-x-2">
              <span>[Enter] {answerResult ? '다음' : (unit?.type === 'QUESTION' ? '제출' : '다음')}</span>
              <span>[←→] 이동</span>
            </div>
            <div className="space-x-2">
              <span>[M] 목록</span>
              <span>[Q] 종료</span>
            </div>
          </div>
        </div>
      </div>

      <ToastA11y
        message={toastMessage}
        isVisible={showToast}
        duration={TOAST_DURATION}
        onClose={() => setShowToast(false)}
      />
    </AppShellMobile>
  );
}
