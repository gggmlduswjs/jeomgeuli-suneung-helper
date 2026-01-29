/**
 * 영어 강의 상세 페이지 (UnitSwipe 방식)
 * 개념 → 본문 → 문제 순서로 Unit 단위 표시
 */
import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import AppShellMobile from '../components/ui/AppShellMobile';
import SpeechBar from '../components/input/SpeechBar';
import ToastA11y from '../components/system/ToastA11y';
import { usePageBase } from '../hooks/usePageBase';
import { useEnglishUnitData } from '../hooks/useEnglishUnitData';
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
import { MAX_ANSWER_CHOICES, TOAST_DURATION } from '../constants';
import { useLastLectureStore } from '../store/lastLectureStore';

const logger = createModuleLogger('EnglishLectureDetail');
const LIST_PATH = '/english/lectures';

export default function EnglishLectureDetail() {
  const { lectureId } = useParams<{ lectureId: string }>();
  const navigate = useNavigate();
  const { unit, allUnits, lectureTitle, loading, error, loadLecture, loadUnit } = useEnglishUnitData();
  const [currentUnitIndex, setCurrentUnitIndex] = useState(0);
  const { speak, stop: stopTTS } = useTTS();
  const { stop: stopSTT, isListening, transcript } = useSTT();
  const { showToast, toastMessage, setShowToast, showToastMessage } = useToast();
  const { sendText } = useBrailleBLE();
  const { aiExplanation, isAiLoading, loadAIExplanation, reset: resetAI } = useUnitAI(speak, sendText);
  const [userAnswer, setUserAnswer] = useState<number | null>(null);
  const [answerResult, setAnswerResult] = useState<{ is_correct: boolean; correct_answer: number; explanation?: string } | null>(null);
  const [showUnitList, setShowUnitList] = useState(false);
  const [showBrailleKeywords, setShowBrailleKeywords] = useState(false);
  const [keywords, setKeywords] = useState<string[]>([]);
  const { extractKeywords, isLoading: isExtractingKeywords } = useExtractKeywords();
  const loadAIExplanationRef = useRef(loadAIExplanation);
  loadAIExplanationRef.current = loadAIExplanation;
  const setLastLectureGlobal = useLastLectureStore((s) => s.setLastLecture);

  const { stopTTS: stopTTSCallback, stopSTT: stopSTTCallback } = usePageBase({
    autoAnnounce: lectureTitle ? `${lectureTitle} 학습을 시작합니다.` : '강의를 불러오는 중입니다.',
    voiceCommands: {
      home: () => { stopTTS(); navigate('/'); showToastMessage('홈으로 이동합니다.'); speak('홈으로 이동합니다.'); stopSTT(); },
      back: () => { stopTTS(); navigate(LIST_PATH); showToastMessage('강의 목록으로 돌아갑니다.'); speak('강의 목록으로 돌아갑니다.'); stopSTT(); },
    },
  });

  useEffect(() => {
    if (lectureId) loadLecture(parseInt(lectureId));
  }, [lectureId, loadLecture]);

  useEffect(() => {
    if (lectureId && lectureTitle && unit) {
      setLastLectureGlobal({
        subject: 'english',
        lectureId: parseInt(lectureId),
        lectureTitle,
        unitId: unit.unit_id,
      });
    }
  }, [lectureId, lectureTitle, unit, setLastLectureGlobal]);

  useEffect(() => {
    if (unit && allUnits.length > 0) {
      const idx = allUnits.findIndex((u) => u.unit_id === unit.unit_id);
      if (idx !== -1) setCurrentUnitIndex(idx);
    }
  }, [unit, allUnits]);

  const handleIndexChange = useCallback((newIndex: number) => {
    if (newIndex < 0 || newIndex >= allUnits.length) return;
    const u = allUnits[newIndex];
    if (u && u.unit_id !== unit?.unit_id) {
      loadUnit(u.unit_id);
      setUserAnswer(null);
      setAnswerResult(null);
      resetAI();
    }
  }, [allUnits, unit, loadUnit, resetAI]);

  const handleAnswer = useCallback((answer: number) => {
    if (!unit || unit.type !== 'QUESTION' || !unit.question) return;
    setUserAnswer(answer);
    const isCorrect = unit.question.answer === answer;
    setAnswerResult({ is_correct: isCorrect, correct_answer: unit.question.answer ?? 0, explanation: isCorrect ? '정답입니다!' : '오답입니다.' });
    if (!isCorrect && loadAIExplanationRef.current) loadAIExplanationRef.current(unit.unit_id, unit);
  }, [unit]);

  const unitNumber = getUnitNumber(unit, allUnits);
  const totalUnits = getTotalUnits(unit, allUnits);
  const unitTypeLabel = getUnitTypeLabel(unit);

  const handleNextUnit = useCallback(() => {
    if (currentUnitIndex < allUnits.length - 1) {
      handleIndexChange(currentUnitIndex + 1);
    } else {
      showToastMessage('강의를 완료했습니다!');
      speak('모든 학습을 완료했습니다. 강의를 완료했습니다!');
      navigate(LIST_PATH);
    }
  }, [currentUnitIndex, allUnits.length, handleIndexChange, navigate, showToastMessage, speak]);

  const handlePrevUnit = useCallback(() => {
    if (currentUnitIndex > 0) handleIndexChange(currentUnitIndex - 1);
    else showToastMessage('첫 번째 학습 단위입니다.');
  }, [currentUnitIndex, handleIndexChange, showToastMessage]);

  const handleEnterKey = useCallback(() => {
    if (answerResult) handleNextUnit();
    else if (userAnswer !== null && unit?.type === 'QUESTION') handleAnswer(userAnswer);
    else handleNextUnit();
  }, [answerResult, userAnswer, unit, handleAnswer, handleNextUnit]);

  const shortcuts: Record<string, () => void> = {
    enter: handleEnterKey,
    tab: () => { if (unit?.unit_id && loadAIExplanationRef.current) loadAIExplanationRef.current(unit.unit_id, unit); },
    arrowleft: handlePrevUnit,
    arrowright: handleNextUnit,
    m: () => setShowUnitList((p) => !p),
    q: () => navigate(LIST_PATH),
    r: () => { if (unit?.unit_id && loadAIExplanationRef.current) { resetAI(); loadAIExplanationRef.current(unit.unit_id, unit); } },
  };
  if (unit?.type === 'QUESTION' && !answerResult) {
    for (let i = 1; i <= MAX_ANSWER_CHOICES; i++) {
      shortcuts[i.toString()] = () => {
        if (unit?.question?.choices && i <= unit.question.choices.length) { setUserAnswer(i); showToastMessage(`${i}번 선택`); }
      };
    }
  }
  useKeyboardShortcuts(shortcuts, [unit, userAnswer, answerResult, allUnits, handleEnterKey, handlePrevUnit, handleNextUnit]);

  const { onSpeech } = useVoiceCommands({ home: () => { stopTTS(); navigate('/'); stopSTT(); }, back: () => navigate(LIST_PATH) });
  useEffect(() => { if (transcript) onSpeech(transcript); }, [transcript, onSpeech]);

  const getUnitIcon = (t: string) => ({ CONCEPT_CORE: '📖', CONCEPT_FORM: '📖', CONCEPT_CONTENT: '📖', CONCEPT_SUMMARY: '📖', PASSAGE: '📚', QUESTION: '✏️' }[t] ?? '📄');
  const getUnitTypeColor = (t: string) => (t.includes('CONCEPT') ? 'border-l-4 border-blue-500' : t === 'PASSAGE' ? 'border-l-4 border-green-500' : t === 'QUESTION' ? 'border-l-4 border-orange-500' : 'border-l-4 border-gray-500');

  if (loading) {
    return (
      <AppShellMobile title="강의 상세" className="relative h-screen flex flex-col">
        <div className="flex items-center justify-center flex-1"><p className="text-muted" role="status" aria-live="polite">강의를 불러오는 중...</p></div>
      </AppShellMobile>
    );
  }
  if (error || !unit || allUnits.length === 0) {
    return (
      <AppShellMobile title="강의 상세" className="relative h-screen flex flex-col">
        <div className="flex items-center justify-center flex-1 px-4">
          <div className="bg-destructive/10 border border-destructive rounded-lg p-6 max-w-md">
            <h3 className="text-lg font-semibold text-destructive mb-2">오류 발생</h3>
            <p className="text-sm mb-4">{error ?? '강의를 찾을 수 없습니다.'}</p>
            <button onClick={() => navigate(LIST_PATH)} className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90" aria-label="강의 목록으로">강의 목록으로</button>
          </div>
        </div>
      </AppShellMobile>
    );
  }

  return (
    <AppShellMobile title={lectureTitle} className="relative h-screen flex flex-col bg-background">
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="px-4 pt-4 pb-2 border-b border-border bg-background">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <button onClick={() => navigate('/')} className="p-2 hover:bg-accent rounded-lg" aria-label="홈으로">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                </svg>
              </button>
              <span className="text-sm text-muted-foreground">{unitNumber} / {totalUnits}</span>
            </div>
            <button onClick={() => setShowUnitList(true)} className="p-2 hover:bg-accent rounded-lg" aria-label="Unit 목록">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" /></svg>
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

        {showUnitList && (
          <UnitListSidebar units={allUnits} currentUnitId={unit?.unit_id ?? null} lessonTitle={lectureTitle} onClose={() => setShowUnitList(false)} getUnitTypeLabel={getUnitTypeLabel} />
        )}

        {!loading && !error && unit && allUnits.length > 0 && (
          <UnitCardSwiper currentIndex={currentUnitIndex} totalUnits={allUnits.length} onIndexChange={handleIndexChange} className="flex-1 flex flex-col">
            <div className="flex-1 overflow-y-auto px-4 py-3">
              <div className={`unit-card ${getUnitTypeColor(unit.type)} bg-card rounded-xl shadow-sm p-4 space-y-3`}>
                <div className="flex items-start gap-2">
                  <div className="text-3xl flex-shrink-0">{getUnitIcon(unit.type)}</div>
                  <div className="flex-1">
                    <div className="text-xs text-muted-foreground mb-0.5">{unitTypeLabel}</div>
                    <h2 className="text-xl font-bold text-fg">{unit.title}</h2>
                  </div>
                </div>
                <UnitViewer unit={unit} onSpeak={speak} />
                <AIExplanationCard
                  sectionType={unit?.type === 'CONCEPT_CORE' ? 'concept' : unit?.type === 'PASSAGE' ? 'content' : 'problem'}
                  aiExplanation={aiExplanation}
                  loadingAI={isAiLoading}
                  onSpeak={async (text) => { speak(text); try { await sendText(text); } catch (e) { logger.error('점자 출력 실패:', e); } }}
                  onLoadExplanation={() => { if (unit.unit_id && unit) { resetAI(); loadAIExplanation(unit.unit_id, unit); } }}
                />
                {unit && (unit.type === 'CONCEPT_CORE' || unit.type === 'PASSAGE') && (
                  <AIQuestionInput unitId={unit.unit_id} lessonId={unit.lesson_id} onAnswer={(a) => logger.log('AI 답변:', a)} />
                )}
                {unit.type === 'QUESTION' && unit.question && !answerResult && (
                  <AnswerInput maxChoice={unit.question.choices?.length ?? 5} onAnswer={handleAnswer} onSpeak={speak} />
                )}
                {answerResult && userAnswer !== null && <AnswerResultComponent result={answerResult} userAnswer={userAnswer} onSpeak={speak} />}
              </div>
            </div>
          </UnitCardSwiper>
        )}

        <div className="px-4 py-3 border-t border-border bg-background">
          <div className="flex items-center justify-between mb-2">
            <button onClick={handlePrevUnit} disabled={currentUnitIndex === 0} className="flex items-center gap-2 px-4 py-2 bg-accent rounded-lg hover:bg-accent/80 disabled:opacity-50 disabled:cursor-not-allowed">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
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
                <circle cx="6" cy="6" r="2" />
                <circle cx="18" cy="6" r="2" />
                <circle cx="6" cy="12" r="2" />
                <circle cx="18" cy="12" r="2" />
                <circle cx="6" cy="18" r="2" />
                <circle cx="18" cy="18" r="2" />
              </svg>
            </button>
            <button onClick={handleNextUnit} disabled={currentUnitIndex === allUnits.length - 1 && unit?.type === 'QUESTION' && !answerResult} className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed">
              <span className="text-sm font-medium">{answerResult ? '다음' : (unit?.type === 'QUESTION' && userAnswer ? '제출' : '다음')}</span>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
            </button>
          </div>
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>[Enter] {answerResult ? '다음' : (unit?.type === 'QUESTION' ? '제출' : '다음')}</span>
            <span>[←→] 이동 [M] 목록 [Q] 종료</span>
          </div>
        </div>
      </div>
      <ToastA11y message={toastMessage} isVisible={showToast} duration={TOAST_DURATION} onClose={() => setShowToast(false)} />
    </AppShellMobile>
  );
}
