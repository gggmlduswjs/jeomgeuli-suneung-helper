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
import { unitsAPI, lessonsAPI, booksAPI } from '../services/api/client';
import { answersAPI } from '../services/answers';
import { progressAPI } from '../services/progress';
import { aiAPI } from '../services/ai';
import AIQuestionInput from '../components/ai/AIQuestionInput';
import AIExplanationCard from '../components/unit/AIExplanationCard';
import { useBrailleBLE } from '../hooks/useBrailleBLE';
import type { Unit } from '../types/unit';
import type { Lesson } from '../types/lesson';
import type { Book } from '../types/book';
import type { AnswerCreate } from '../types/answer';
import { useProgressStore } from '../store/progressStore';

export default function UnitPage() {
  const navigate = useNavigate();
  const { unitId } = useParams<{ unitId: string }>();
  const { speak, stop: stopTTS } = useTTS();
  const { start: startSTT, stop: stopSTT, isListening, transcript } = useSTT();
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  
  const [unit, setUnit] = useState<Unit | null>(null);
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [book, setBook] = useState<Book | null>(null);
  const [allUnits, setAllUnits] = useState<Unit[]>([]);
  const [userAnswer, setUserAnswer] = useState<number | null>(null);
  const [answerResult, setAnswerResult] = useState<{ is_correct: boolean; correct_answer: number; explanation?: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aiExplanation, setAiExplanation] = useState<string | null>(null);
  const [isAiLoading, setIsAiLoading] = useState(false);
  const [showUnitList, setShowUnitList] = useState(false); // 학습 단위 목록 토글
  
  const { saveProgress } = useProgressStore();
  const { sendText } = useBrailleBLE();
  
  // 중복 호출 방지
  const isLoadingRef = useRef(false);
  const loadedUnitIdRef = useRef<string | null>(null);
  const hasSpokenTitleRef = useRef<string | null>(null);
  const hasSpokenExplanationRef = useRef<string | null>(null);
  const explanationLoadTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (unitId && unitId !== loadedUnitIdRef.current && !isLoadingRef.current) {
      isLoadingRef.current = true;
      loadedUnitIdRef.current = unitId;
      hasSpokenTitleRef.current = null; // 새 unit 로드 시 초기화
      hasSpokenExplanationRef.current = null; // 새 unit 로드 시 설명도 초기화
      // 기존 timeout 정리
      if (explanationLoadTimeoutRef.current) {
        clearTimeout(explanationLoadTimeoutRef.current);
        explanationLoadTimeoutRef.current = null;
      }
      loadUnit(unitId).finally(() => {
        isLoadingRef.current = false;
      });
    }
    
    // cleanup: unitId가 변경되면 이전 ID 초기화
    return () => {
      // timeout 정리
      if (explanationLoadTimeoutRef.current) {
        clearTimeout(explanationLoadTimeoutRef.current);
        explanationLoadTimeoutRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [unitId]); // unitId만 의존성으로 유지 (loadUnit은 ref를 통해 안전하게 호출)

  const loadUnit = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);
    setUserAnswer(null);
    setAnswerResult(null);
    setAiExplanation(null);
    
    try {
      // Load unit
      const data = await unitsAPI.get(id);
      
      // Load lesson (unit의 lesson_id 검증)
      let lessonData;
      try {
        lessonData = await lessonsAPI.get(data.lesson_id);
      } catch (err: any) {
        console.error('[Unit] Lesson 로드 실패:', err);
        const errorMsg = `학습 단위의 강(레슨)을 찾을 수 없습니다. (lesson_id: ${data.lesson_id})`;
        setError(errorMsg);
        speak(errorMsg);
        setLoading(false);
        return;
      }
      
      // Load book (lesson의 book_id 검증)
      let bookData;
      try {
        bookData = await booksAPI.get(lessonData.book_id);
      } catch (err: any) {
        console.error('[Unit] Book 로드 실패:', err);
        const errorMsg = `강의 교재를 찾을 수 없습니다. (book_id: ${lessonData.book_id})`;
        setError(errorMsg);
        speak(errorMsg);
        setLoading(false);
        return;
      }
      
      // 데이터 일관성 검증: unit이 올바른 lesson에 속하는지 확인
      if (data.lesson_id !== lessonData.lesson_id) {
        console.warn('[Unit] 데이터 불일치:', {
          unit_lesson_id: data.lesson_id,
          lesson_lesson_id: lessonData.lesson_id
        });
        const errorMsg = '학습 단위 데이터가 올바르지 않습니다. 데이터를 다시 동기화해주세요.';
        setError(errorMsg);
        speak(errorMsg);
        setLoading(false);
        return;
      }
      
      setUnit(data);
      setLesson(lessonData);
      setBook(bookData);
      
      // Load all units in lesson (for navigation)
      const units = await unitsAPI.listByLesson(data.lesson_id);
      setAllUnits(units);
      
      // 진도 저장
      await progressAPI.save({
        user_id: 'u_demo',
        unit_id: id,
        lesson_id: data.lesson_id,
        book_id: lessonData.book_id,
      });
      
      // AI 설명만 자동 재생 (제목 TTS 제거)
      const titleKey = `${id}_${data.title}`;
      if (hasSpokenTitleRef.current !== titleKey) {
        hasSpokenTitleRef.current = titleKey;
        // AI 설명 요청 (강의 대본 기반) - 제목 TTS 없이 바로 시작
        explanationLoadTimeoutRef.current = setTimeout(() => {
          // ref를 통해 최신 loadAIExplanation 호출
          if (loadAIExplanationRef.current) {
            loadAIExplanationRef.current(id);
          }
        }, 500); // 짧은 딜레이로 바로 AI 설명 시작
      }
    } catch (err) {
      const errorMsg = '학습 단위를 불러오는 중 오류가 발생했습니다.';
      setError(errorMsg);
      // 에러 메시지 TTS 제거 (AI 설명만 재생)
    } finally {
      setLoading(false);
    }
  }, [speak, sendText]); // loadAIExplanation는 ref를 통해 호출하므로 의존성에서 제외

  const isLoadingExplanationRef = useRef(false);
  
  // loadAIExplanation를 ref로 저장하여 의존성 문제 방지
  const loadAIExplanationRef = useRef<((unitId: string) => Promise<void>) | null>(null);
  
  const loadAIExplanation = useCallback(async (unitId: string) => {
    // 중복 호출 방지
    if (isLoadingExplanationRef.current) {
      console.log('[Unit] AI 설명 로드 중 - 중복 호출 방지');
      return;
    }
    
    // 이미 이 unitId에 대해 설명을 말했는지 확인
    if (hasSpokenExplanationRef.current === unitId) {
      console.log('[Unit] AI 설명 이미 재생됨 - 중복 방지');
      return;
    }
    
    // 기존 timeout 정리
    if (explanationLoadTimeoutRef.current) {
      clearTimeout(explanationLoadTimeoutRef.current);
      explanationLoadTimeoutRef.current = null;
    }
    
    setIsAiLoading(true);
    isLoadingExplanationRef.current = true;
    
    try {
      const response = await aiAPI.teachUnit(unitId);
      const explanation = response.explanation;
      
      // 설명이 있으면 상태 업데이트
      if (explanation) {
        setAiExplanation(explanation);
        // TTS 재생은 한 번만 (hasSpokenExplanationRef로 보장)
        if (hasSpokenExplanationRef.current !== unitId) {
          hasSpokenExplanationRef.current = unitId;
          speak(explanation);
          // 점자로도 출력 (에러가 나도 계속 진행)
          try {
            await sendText(explanation);
          } catch (err) {
            console.error('[Unit] 점자 출력 실패:', err);
            // 점자 실패해도 계속 진행
          }
        }
      } else {
        // AI 설명이 없을 때는 TTS 재생하지 않음 (사용자가 버튼으로 들을 수 있음)
        setAiExplanation(null);
      }
    } catch (err) {
      console.error('[Unit] AI 설명 로드 실패:', err);
      setAiExplanation(null);
      // AI 실패 시에도 TTS 재생하지 않음
    } finally {
      setIsAiLoading(false);
      isLoadingExplanationRef.current = false;
    }
  }, [speak, sendText]);
  
  // loadAIExplanation를 ref에 저장
  loadAIExplanationRef.current = loadAIExplanation;

  const handleQuestion = async (question: string) => {
    if (!unit) return;
    
    setIsAiLoading(true);
    try {
      const response = await aiAPI.answerQuestion(question, unit.unit_id, unit.lesson_id);
      setAiExplanation(response.answer);
      // AI 질문 답변 TTS 제거 (AI 설명만 재생)
    } catch (err) {
      console.error('[Unit] AI 질문 답변 실패:', err);
      // 에러 메시지 TTS 제거
    } finally {
      setIsAiLoading(false);
    }
  };

  const handleAnswer = async (answer: number) => {
    if (!unit || unit.type !== 'QUESTION' || !unit.question) return;

    setUserAnswer(answer);
    
    // 정답 확인
    const isCorrect = unit.question.answer === answer;
    
    // 답안 제출
    try {
      await answersAPI.submit({
        user_id: 'u_demo',
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
      
      // 정답/오답 TTS 제거 (AI 설명만 재생)
      if (!isCorrect) {
        // 오답 시 AI 설명 자동 로드
        if (loadAIExplanationRef.current) {
          loadAIExplanationRef.current(unit.unit_id);
        }
      }
    } catch (err) {
      console.error('[Unit] 답안 제출 실패:', err);
    }
  };

  // Get unit number and total
  const questions = allUnits.filter(u => u.type === 'QUESTION');
  const unitNumber = unit 
    ? (unit.type === 'QUESTION'
      ? questions.findIndex(q => q.unit_id === unit.unit_id) + 1
      : allUnits.findIndex(u => u.unit_id === unit.unit_id) + 1)
    : 0;
  const totalUnits = unit?.type === 'QUESTION' ? questions.length : allUnits.length;

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

  const unitTypeLabel = getUnitTypeLabel(unit);

  // Navigation handlers
  const handlePrevUnit = () => {
    const currentIndex = allUnits.findIndex(u => u.unit_id === unit?.unit_id);
    if (currentIndex > 0) {
      const prevUnit = allUnits[currentIndex - 1];
      navigate(`/unit/${prevUnit.unit_id}`);
    } else {
      showToastMessage('첫 번째 유닛입니다.');
    }
  };

  const handleNextUnit = () => {
    const currentIndex = allUnits.findIndex(u => u.unit_id === unit?.unit_id);
    if (currentIndex < allUnits.length - 1) {
      const nextUnit = allUnits[currentIndex + 1];
      navigate(`/unit/${nextUnit.unit_id}`);
    } else {
      // 마지막 유닛이면 요약 페이지로
      navigate('/summary');
    }
  };

  const handleEnterKey = () => {
    if (answerResult) {
      // 이미 답변했으면 다음 유닛으로
      handleNextUnit();
    } else if (userAnswer !== null && unit?.type === 'QUESTION') {
      // 답안 제출
      handleAnswer(userAnswer);
    } else {
      // 답안이 없으면 다음 유닛으로
      handleNextUnit();
    }
  };

  // Keyboard shortcuts
  const shortcuts: Record<string, () => void> = {
    enter: () => handleEnterKey(),
    tab: () => {
      if (unitId && loadAIExplanationRef.current) {
        loadAIExplanationRef.current(unitId);
      }
    },
    arrowleft: () => handlePrevUnit(),
    arrowright: () => handleNextUnit(),
    m: () => {
      // 학습 단위 목록 토글
      setShowUnitList(prev => !prev);
    },
    q: () => navigate('/summary'),
    b: () => {
      if (lesson?.lesson_id) {
        navigate(`/lesson/${lesson.lesson_id}`);
      } else {
        navigate('/books');
      }
    },
    r: () => {
      // 현재 위치 안내 TTS 제거 (AI 설명만 재생)
      // 필요시 AI 설명을 다시 재생할 수 있도록
      if (unitId && loadAIExplanationRef.current) {
        hasSpokenExplanationRef.current = null; // 재생 가능하도록 초기화
        loadAIExplanationRef.current(unitId);
      }
    },
  };

  // Add number shortcuts for answer selection (1-5)
  if (unit?.type === 'QUESTION' && !answerResult) {
    for (let i = 1; i <= 5; i++) {
      shortcuts[i.toString()] = () => {
        if (unit?.question?.choices && i <= unit.question.choices.length) {
          setUserAnswer(i);
          showToastMessage(`${i}번 선택`);
        }
      };
    }
  }

  useKeyboardShortcuts(shortcuts, [unit, userAnswer, answerResult, lesson, allUnits]);

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

  const showToastMessage = (message: string) => {
    setToastMessage(message);
    setShowToast(true);
  };

  return (
    <AppShellMobile 
      title={book?.title ? `${book.title} [${unitNumber}/${totalUnits}]` : (unit?.title || '학습 단위')} 
      className="relative h-screen flex flex-col"
    >
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="px-4 py-3 border-b border-border">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <h2 className="text-lg font-semibold">{lesson?.title || unit?.title}</h2>
              <p className="text-sm text-muted-foreground">
                {unitTypeLabel} {unitNumber} / {totalUnits}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowUnitList(true)}
                className="px-3 py-1.5 text-sm bg-primary/10 text-primary border border-primary/30 rounded-lg hover:bg-primary/20 transition-colors"
                aria-label="학습 단위 목록"
              >
                목록
              </button>
              <div className="text-sm text-muted-foreground">
                {totalUnits > 0 ? Math.round((unitNumber / totalUnits) * 100) : 0}%
              </div>
            </div>
          </div>
        </div>

        <div className="mb-4 px-4 pt-2">
          <SpeechBar isListening={isListening} transcript={transcript} />
        </div>

        {/* 학습 단위 목록 사이드바 (토글) */}
        {showUnitList && (
          <div className="fixed inset-0 z-50 bg-black/50" onClick={() => setShowUnitList(false)}>
            <div 
              className="absolute right-0 top-0 h-full w-80 bg-background border-l border-border shadow-lg overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-4 border-b border-border">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">학습 단위 목록</h3>
                  <button
                    onClick={() => setShowUnitList(false)}
                    className="text-muted-foreground hover:text-foreground"
                    aria-label="닫기"
                  >
                    ✕
                  </button>
                </div>
                <p className="text-sm text-muted-foreground mt-1">
                  {lesson?.title || '강의'}
                </p>
              </div>
              <div className="p-2">
                {allUnits.map((u, index) => {
                  const isActive = u.unit_id === unit?.unit_id;
                  const unitTypeLabel = getUnitTypeLabel(u);
                  return (
                    <button
                      key={u.unit_id}
                      onClick={() => {
                        navigate(`/unit/${u.unit_id}`);
                        setShowUnitList(false);
                      }}
                      className={`w-full p-3 text-left rounded-lg mb-2 transition-colors ${
                        isActive
                          ? 'bg-primary/20 border-2 border-primary'
                          : 'bg-card border border-border hover:border-primary/50'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="font-medium text-sm">{u.title}</div>
                          <div className="text-xs text-muted-foreground mt-1">
                            {unitTypeLabel} • {index + 1} / {allUnits.length}
                          </div>
                        </div>
                        {isActive && (
                          <span className="text-primary text-xs">현재</span>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
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
                  console.error('[Unit] 점자 출력 실패:', err);
                }
              }}
              onLoadExplanation={() => {
                if (unitId) {
                  // 다시 생성 시 ref 초기화하여 새로 생성 가능하도록
                  hasSpokenExplanationRef.current = null;
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
                    // 답변은 이미 TTS로 재생됨
                    console.log('AI 답변:', answer);
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
            {answerResult && (
              <AnswerResultComponent
                result={answerResult}
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
        duration={3000}
        onClose={() => setShowToast(false)}
      />
    </AppShellMobile>
  );
}
