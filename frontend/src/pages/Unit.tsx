/**
 * 학습 단위 페이지 - 메인 학습 화면
 * 개념/작품/문제 통합 뷰어 + 네비게이션
 */
import { useEffect, useState, useRef, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import AppShellMobile from '../components/ui/AppShellMobile';
import SpeechBar from '../components/input/SpeechBar';
import useTTS from '../hooks/useTTS';
import useSTT from '../hooks/useSTT';
import useVoiceCommands from '../hooks/useVoiceCommands';
import { useKeyboardShortcuts } from '../contexts/KeyboardContext';
import ToastA11y from '../components/system/ToastA11y';
import UnitViewer from '../components/unit/UnitViewer';
import AnswerInput from '../components/question/AnswerInput';
import AnswerResultComponent from '../components/question/AnswerResult';
import { answersAPI } from '../services/answers';
import AIQuestionInput from '../components/ai/AIQuestionInput';
import AIExplanationCard from '../components/unit/AIExplanationCard';
import useBrailleBLE from '../hooks/useBrailleBLE';
import { useUnitData } from '../hooks/useUnitData';
import { useUnitAI } from '../hooks/useUnitAI';
import { useUnitNavigation } from '../hooks/useUnitNavigation';
import { useToast } from '../hooks/useToast';
import UnitHeader from '../components/unit/UnitHeader';
import UnitListSidebar from '../components/unit/UnitListSidebar';
import { getUnitTypeLabel, getUnitNumber, getTotalUnits } from '../utils/unitHelpers';
import { createModuleLogger } from '../utils/logger';
import { DEFAULT_USER_ID, AI_EXPLANATION_AUTO_LOAD_DELAY, MAX_ANSWER_CHOICES, ROUTES, TOAST_DURATION } from '../constants';

const logger = createModuleLogger('Unit');

export default function UnitPage() {
  const navigate = useNavigate();
  const { unitId } = useParams<{ unitId: string }>();
  const { speak, stop: stopTTS } = useTTS();
  const { stop: stopSTT, isListening, transcript } = useSTT();
  const { showToast, toastMessage, setShowToast, showToastMessage } = useToast();
  
  // 데이터 로딩
  const { unit, lesson, book, allUnits, loading, error, loadUnit } = useUnitData();
  
  // 점자
  const { sendText } = useBrailleBLE();
  
  // AI 설명
  const {
    aiExplanation,
    isAiLoading,
    loadAIExplanation,
    reset: resetAI
  } = useUnitAI(speak, sendText);
  
  // 네비게이션
  const { handlePrevUnit, handleNextUnit } = useUnitNavigation();
  
  // 답안 상태
  const [userAnswer, setUserAnswer] = useState<number | null>(null);
  const [answerResult, setAnswerResult] = useState<{ is_correct: boolean; correct_answer: number; explanation?: string } | null>(null);
  const [showUnitList, setShowUnitList] = useState(false);
  
  // AI 설명 자동 로드를 위한 ref
  const loadAIExplanationRef = useRef(loadAIExplanation);
  const explanationLoadTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  // ref 업데이트
  loadAIExplanationRef.current = loadAIExplanation;

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

  const handleEnterKey = useCallback(() => {
    const navigateToSummary = () => navigate(ROUTES.SUMMARY);
    if (answerResult) {
      handleNextUnit(unit, allUnits, navigateToSummary);
    } else if (userAnswer !== null && unit?.type === 'QUESTION') {
      handleAnswer(userAnswer);
    } else {
      handleNextUnit(unit, allUnits, navigateToSummary);
    }
  }, [answerResult, userAnswer, unit, allUnits, handleAnswer, handleNextUnit, navigate]);

  const handlePrevUnitWithToast = useCallback(() => {
    const currentIndex = allUnits.findIndex(u => u.unit_id === unit?.unit_id);
    if (currentIndex === 0) {
      showToastMessage('첫 번째 유닛입니다.');
    } else {
      handlePrevUnit(unit, allUnits);
    }
  }, [unit, allUnits, handlePrevUnit, showToastMessage]);

  // Keyboard shortcuts
  const shortcuts: Record<string, () => void> = {
    enter: handleEnterKey,
    tab: () => {
      if (unitId && loadAIExplanationRef.current) {
        loadAIExplanationRef.current(unitId);
      }
    },
    arrowleft: handlePrevUnitWithToast,
    arrowright: () => handleNextUnit(unit, allUnits, () => navigate(ROUTES.SUMMARY)),
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

  useKeyboardShortcuts(shortcuts, [unit, userAnswer, answerResult, lesson, allUnits, unitId, handleEnterKey, handlePrevUnitWithToast]);

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

  return (
    <AppShellMobile 
      title={book?.title ? `${book.title} [${unitNumber}/${totalUnits}]` : (unit?.title || '학습 단위')} 
      className="relative h-screen flex flex-col"
    >
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <UnitHeader
          lesson={lesson}
          unit={unit}
          unitTypeLabel={unitTypeLabel}
          unitNumber={unitNumber}
          totalUnits={totalUnits}
          onShowUnitList={() => setShowUnitList(true)}
        />

        <div className="mb-4 px-4 pt-2">
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

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-4 py-4">
        {loading && (
          <div className="text-center py-8">
            <p className="text-muted">로딩 중...</p>
          </div>
        )}

        {error && (
          <div className="bg-error/10 border border-error rounded-lg p-4 mb-4">
            <p className="text-error">{error}</p>
          </div>
        )}

        {!loading && !error && unit && (
          <div className="space-y-4">
            <UnitViewer unit={unit} onSpeak={speak} />
            
            {/* AI 설명 표시 - 항상 표시 */}
            <AIExplanationCard
              sectionType={unit?.type === 'CONCEPT_CORE' ? 'concept' : 'content'}
              aiExplanation={aiExplanation}
              loadingAI={isAiLoading}
              onSpeak={async (text: string) => {
                speak(text);
                // 점자로도 출력
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
              hasContent={true} // 항상 표시
            />
            
            {/* AI 질문 입력 (개념/작품인 경우) */}
            {unit && (unit.type === 'CONCEPT_CORE' || unit.type === 'PASSAGE') && (
              <div className="mt-4">
                <AIQuestionInput
                  unitId={unit.unit_id}
                  lessonId={unit.lesson_id}
                  onAnswer={(answer) => {
                    logger.log('AI 답변:', answer);
                  }}
                />
              </div>
            )}
            
            {/* 문제인 경우 답안 입력 */}
            {unit.type === 'QUESTION' && unit.question && !answerResult && (
              <AnswerInput
                choices={unit.question.choices}
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
        )}
        </div>

        {/* Footer - Keyboard shortcuts */}
        <div className="px-4 py-3 border-t border-border bg-background">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <div className="space-x-2">
              <span>[Enter] {answerResult ? '다음' : (unit?.type === 'QUESTION' ? '제출' : '다음')}</span>
              <span>[←→] 이동</span>
              <span>[Tab] AI설명</span>
            </div>
            <div className="space-x-2">
              <span>[M] 목록 토글</span>
              <span>[Q] 종료</span>
              <span>[B] 뒤로</span>
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
