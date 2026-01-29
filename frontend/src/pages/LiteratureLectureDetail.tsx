/**
 * 문학 강의 상세 페이지 (UnitSwipe 방식)
 * 개념 → 본문 → 문제 순서로 Unit 단위로 순차 표시
 */
import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import AppShellMobile from '../components/ui/AppShellMobile';
import SpeechBar from '../components/input/SpeechBar';
import ToastA11y from '../components/system/ToastA11y';
import { usePageBase } from '../hooks/usePageBase';
import { useLiteratureUnitData } from '../hooks/useLiteratureUnitData';
import { useLiteratureProgressStore } from '../store/literatureProgressStore';
import { useLastLectureStore } from '../store/lastLectureStore';
import UnitCardSwiper from '../components/unit/UnitCardSwiper';
import UnitViewer from '../components/unit/UnitViewer';
import AnswerInput from '../components/question/AnswerInput';
import AnswerResultComponent from '../components/question/AnswerResult';
import AIExplanationCard from '../components/unit/AIExplanationCard';
import AIQuestionInput from '../components/ai/AIQuestionInput';
import UnitListSidebar from '../components/unit/UnitListSidebar';
import BrailleKeywordsPanel from '../components/braille/BrailleKeywordsPanel';
import { useKeyboardShortcuts } from '../contexts/KeyboardContext';
import { useExtractKeywords } from '../hooks/useExtractKeywords';
import { useToast } from '../hooks/useToast';
import useTTS from '../hooks/useTTS';
import useSTT from '../hooks/useSTT';
import useVoiceCommands from '../hooks/useVoiceCommands';
import useBrailleBLE from '../hooks/useBrailleBLE';
import { useUnitAI } from '../hooks/useUnitAI';
import { getUnitTypeLabel, getUnitNumber, getTotalUnits } from '../utils/unitHelpers';
import { createModuleLogger } from '../utils/logger';
import { DEFAULT_USER_ID, MAX_ANSWER_CHOICES, TOAST_DURATION } from '../constants';
import type { Unit } from '../types/unit';

const logger = createModuleLogger('LiteratureLectureDetail');

export default function LiteratureLectureDetail() {
  const { lectureId } = useParams<{ lectureId: string }>();
  const navigate = useNavigate();
  
  // 문학 Unit 데이터 로드
  const {
    unit,
    allUnits,
    lectureTitle,
    loading,
    error,
    loadLecture,
    loadUnit,
  } = useLiteratureUnitData();

  // 현재 Unit 인덱스
  const [currentUnitIndex, setCurrentUnitIndex] = useState(0);

  // TTS/STT
  const { speak, stop: stopTTS } = useTTS();
  const { stop: stopSTT, isListening, transcript } = useSTT();
  const { showToast, toastMessage, setShowToast, showToastMessage } = useToast();

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
  const [showBrailleKeywords, setShowBrailleKeywords] = useState(false);
  const [keywords, setKeywords] = useState<string[]>([]);
  const { extractKeywords, isLoading: isExtractingKeywords } = useExtractKeywords();

  // 진도 관리
  const {
    setLastLecture,
    completeLecture,
    isLectureCompleted,
    saveProblemResult,
    addStudyTime,
  } = useLiteratureProgressStore();
  const setLastLectureGlobal = useLastLectureStore((s) => s.setLastLecture);

  const [studyStartTime] = useState(Date.now());

  // AI 설명 자동 로드를 위한 ref
  const loadAIExplanationRef = useRef(loadAIExplanation);
  loadAIExplanationRef.current = loadAIExplanation;

  const {
    stopTTS: stopTTSCallback,
    stopSTT: stopSTTCallback,
  } = usePageBase({
    autoAnnounce: lectureTitle ? `${lectureTitle} 학습을 시작합니다.` : '강의를 불러오는 중입니다.',
    voiceCommands: {
      home: () => {
        stopTTS();
        navigate('/');
        showToastMessage('홈으로 이동합니다.');
        speak('홈으로 이동합니다.');
        stopSTT();
      },
      back: () => {
        stopTTS();
        navigate('/literature/lectures');
        showToastMessage('강의 목록으로 돌아갑니다.');
        speak('강의 목록으로 돌아갑니다.');
        stopSTT();
      },
    },
  });

  // 강의 로드
  useEffect(() => {
    if (lectureId) {
      const id = parseInt(lectureId);
      loadLecture(id);
      setLastLecture(id);
    }
  }, [lectureId, loadLecture, setLastLecture]);

  // 마지막 강의 저장 (홈 "진행 중인 학습"용)
  useEffect(() => {
    if (lectureId && lectureTitle && unit) {
      setLastLectureGlobal({
        subject: 'literature',
        lectureId: parseInt(lectureId),
        lectureTitle,
        unitId: unit.unit_id,
      });
    }
  }, [lectureId, lectureTitle, unit, setLastLectureGlobal]);

  // 페이지 나가기 전 학습 시간 저장
  useEffect(() => {
    return () => {
      const studyTime = Math.floor((Date.now() - studyStartTime) / 1000);
      addStudyTime(studyTime);
    };
  }, [studyStartTime, addStudyTime]);

  // 현재 Unit ID로 인덱스 계산
  useEffect(() => {
    if (unit && allUnits.length > 0) {
      const index = allUnits.findIndex(u => u.unit_id === unit.unit_id);
      if (index !== -1) {
        setCurrentUnitIndex(index);
      }
    }
  }, [unit, allUnits]);

  // 인덱스 변경 시 Unit 변경
  const handleIndexChange = useCallback((newIndex: number) => {
    if (newIndex < 0 || newIndex >= allUnits.length) return;

    const newUnit = allUnits[newIndex];
    if (newUnit && newUnit.unit_id !== unit?.unit_id) {
      loadUnit(newUnit.unit_id);
      // 답안 상태 초기화
      setUserAnswer(null);
      setAnswerResult(null);
      resetAI();
    }
  }, [allUnits, unit, loadUnit, resetAI]);

  // 답안 제출
  const handleAnswer = useCallback(async (answer: number) => {
    if (!unit || unit.type !== 'QUESTION' || !unit.question) return;

    setUserAnswer(answer);

    // 정답 확인
    const isCorrect = unit.question.answer === answer;

    // 문제 결과 저장
    if (unit.unit_id.includes('problem')) {
      const problemId = unit.unit_id.split('_').pop() || '';
      saveProblemResult(problemId, answer.toString(), isCorrect);
    }

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
  }, [unit, saveProblemResult]);

  // Unit 정보 계산
  const unitNumber = getUnitNumber(unit, allUnits);
  const totalUnits = getTotalUnits(unit, allUnits);
  const unitTypeLabel = getUnitTypeLabel(unit);

  // 다음 Unit으로 이동
  const handleNextUnit = useCallback(() => {
    if (currentUnitIndex < allUnits.length - 1) {
      handleIndexChange(currentUnitIndex + 1);
    } else {
      // 마지막 Unit이면 강의 완료 처리
      if (lectureId && !isLectureCompleted(parseInt(lectureId))) {
        completeLecture(parseInt(lectureId));
        showToastMessage('강의를 완료했습니다!');
        speak('모든 학습을 완료했습니다. 강의를 완료했습니다!');
      }
      navigate('/literature/lectures');
    }
  }, [currentUnitIndex, allUnits.length, handleIndexChange, lectureId, isLectureCompleted, completeLecture, navigate, showToastMessage, speak]);

  // 이전 Unit으로 이동
  const handlePrevUnit = useCallback(() => {
    if (currentUnitIndex > 0) {
      handleIndexChange(currentUnitIndex - 1);
    } else {
      showToastMessage('첫 번째 학습 단위입니다.');
    }
  }, [currentUnitIndex, handleIndexChange, showToastMessage]);

  // Enter 키 처리
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
      if (unit?.unit_id && loadAIExplanationRef.current) {
        loadAIExplanationRef.current(unit.unit_id);
      }
    },
    arrowleft: handlePrevUnit,
    arrowright: handleNextUnit,
    m: () => setShowUnitList(prev => !prev),
    q: () => navigate('/literature/lectures'),
    r: () => {
      if (unit?.unit_id && loadAIExplanationRef.current) {
        resetAI();
        loadAIExplanationRef.current(unit.unit_id);
      }
    },
  };

  // 답안 선택 단축키 (1-5)
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

  useKeyboardShortcuts(shortcuts, [unit, userAnswer, answerResult, allUnits, handleEnterKey, handlePrevUnit, handleNextUnit]);

  // 음성 명령어
  const { onSpeech } = useVoiceCommands({
    home: () => {
      stopTTS();
      navigate('/');
      stopSTT();
    },
    back: () => {
      navigate('/literature/lectures');
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

  if (loading) {
    return (
      <AppShellMobile title="강의 상세" className="relative h-screen flex flex-col">
        <div className="flex items-center justify-center flex-1">
          <p className="text-muted" role="status" aria-live="polite">
            강의를 불러오는 중...
          </p>
        </div>
      </AppShellMobile>
    );
  }

  if (error || !unit || allUnits.length === 0) {
    return (
      <AppShellMobile title="강의 상세" className="relative h-screen flex flex-col">
        <div className="flex items-center justify-center flex-1 px-4">
          <div className="bg-destructive/10 border border-destructive rounded-lg p-6 max-w-md">
            <h3 className="text-lg font-semibold text-destructive mb-2">오류 발생</h3>
            <p className="text-sm mb-4">{error || '강의를 찾을 수 없습니다.'}</p>
            <button
              onClick={() => navigate('/literature/lectures')}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
              aria-label="강의 목록으로 돌아가기"
            >
              강의 목록으로
            </button>
          </div>
        </div>
      </AppShellMobile>
    );
  }

  return (
    <AppShellMobile title={lectureTitle} className="relative h-screen flex flex-col bg-background">
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="px-4 pt-4 pb-2 border-b border-border bg-background">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <button
                onClick={() => navigate('/')}
                className="p-2 hover:bg-accent rounded-lg transition-colors"
                aria-label="홈으로"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                </svg>
              </button>
              <span className="text-sm text-muted-foreground">{unitNumber} / {totalUnits}</span>
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

        {/* 점자 키워드 패널 */}
        {showBrailleKeywords && (
          <BrailleKeywordsPanel
            keywords={keywords}
            unitTitle={unit?.title}
            onClose={() => setShowBrailleKeywords(false)}
          />
        )}

        {/* 학습 단위 목록 사이드바 */}
        {showUnitList && (
          <UnitListSidebar
            units={allUnits}
            currentUnitId={unit?.unit_id || null}
            lessonTitle={lectureTitle}
            onClose={() => setShowUnitList(false)}
            getUnitTypeLabel={getUnitTypeLabel}
          />
        )}

        {/* Content with Card Swiper */}
        {!loading && !error && unit && allUnits.length > 0 && (
          <UnitCardSwiper
            currentIndex={currentUnitIndex}
            totalUnits={allUnits.length}
            onIndexChange={handleIndexChange}
            className="flex-1 flex flex-col"
          >
            {/* Unit 카드 */}
            <div className="flex-1 overflow-y-auto px-4 py-3">
              <div className={`unit-card ${getUnitTypeColor(unit.type)} bg-card rounded-xl shadow-sm p-4 space-y-3`}>
                {/* Unit 타입 아이콘 및 제목 */}
                <div className="flex items-start gap-2">
                  <div className="text-3xl flex-shrink-0">
                    {getUnitIcon(unit.type)}
                  </div>
                  <div className="flex-1">
                    <div className="text-xs text-muted-foreground mb-0.5">
                      {unitTypeLabel}
                    </div>
                    <h2 className="text-xl font-bold text-fg">{unit.title}</h2>
                  </div>
                </div>

                {/* Unit 내용 */}
                <UnitViewer unit={unit} onSpeak={speak} />

                {/* AI 설명 */}
                <AIExplanationCard
                  sectionType={unit?.type === 'CONCEPT_CORE' ? 'concept' : (unit?.type === 'PASSAGE' ? 'content' : 'problem')}
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
                    if (unit.unit_id && unit) {
                      resetAI();
                      loadAIExplanation(unit.unit_id, unit);
                    }
                  }}
                />

                {/* AI 질문 입력 (개념/본문인 경우) */}
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
              onClick={async () => {
                if (unit) {
                  const extracted = await extractKeywords(unit);
                  setKeywords(extracted);
                  setShowBrailleKeywords(true);
                }
              }}
              className="p-2 hover:bg-accent rounded-lg transition-colors"
              aria-label="점자 모듈 - 핵심 키워드"
              disabled={!unit || isExtractingKeywords}
            >
              {/* 점자 아이콘 (6점 점자 패턴) */}
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-label="점자">
                {/* 점자 패턴: 2x3 그리드 */}
                <circle cx="6" cy="6" r="2" />
                <circle cx="18" cy="6" r="2" />
                <circle cx="6" cy="12" r="2" />
                <circle cx="18" cy="12" r="2" />
                <circle cx="6" cy="18" r="2" />
                <circle cx="18" cy="18" r="2" />
              </svg>
            </button>

            <button
              onClick={handleNextUnit}
              disabled={
                currentUnitIndex === allUnits.length - 1 &&
                unit?.type === 'QUESTION' &&
                !answerResult &&
                (unit?.question?.choices?.length ?? 0) > 0
              }
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
