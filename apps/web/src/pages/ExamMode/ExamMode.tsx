import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import AppShellMobile from '../../components/ui/AppShellMobile';
import SpeechBar from '../../components/input/SpeechBar';
import useTTS from '../../hooks/useTTS';
import useSTT from '../../hooks/useSTT';
import useVoiceCommands from '../../hooks/useVoiceCommands';
import ToastA11y from '../../components/system/ToastA11y';
import { BraillePatternFactory } from '../../lib/braillePattern';
import useBrailleBLE from '../../hooks/useBrailleBLE';
import { examAPI, type Question, type AnswerResult } from '../../lib/api';
import { useExamStore } from '../../store/examStore';
import QuestionDisplay from '../Question/components/QuestionDisplay';
import AnswerInput from '../Question/components/AnswerInput';
import AnswerResultComponent from '../Question/components/AnswerResult';

type ExamStatus = 'setup' | 'running' | 'paused' | 'finished';

export default function ExamMode() {
  const navigate = useNavigate();
  const { speak, stop: stopTTS } = useTTS();
  const { start: startSTT, stop: stopSTT, isListening, transcript } = useSTT();
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  
  const [status, setStatus] = useState<ExamStatus>('setup');
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null);
  const [answerResult, setAnswerResult] = useState<AnswerResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const { isConnected, writeCells } = useBrailleBLE();
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // Store
  const {
    currentQuestionIndex,
    totalQuestions,
    answers,
    remainingTime,
    isTimerRunning,
    startExam: startExamStore,
    setAnswer,
    nextQuestion,
    prevQuestion,
    goToQuestion,
    updateTimer,
  } = useExamStore();

  // 페이지 진입 시 자동 음성 안내
  useEffect(() => {
    const welcomeMessage = '실전 모의고사 모드입니다. 12시간 수능 시험을 시뮬레이션할 수 있습니다.';
    const timer = setTimeout(() => {
      speak(welcomeMessage);
    }, 500);
    return () => clearTimeout(timer);
  }, [speak]);

  // 타이머 실행
  useEffect(() => {
    if (isTimerRunning && status === 'running') {
      intervalRef.current = setInterval(() => {
        updateTimer(Math.max(0, remainingTime - 1));
        
        if (remainingTime <= 0) {
          finishExam();
        }
      }, 1000);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isTimerRunning, status, remainingTime, updateTimer]);

  // 현재 문제 로드
  useEffect(() => {
    if (status === 'running' && questions.length > 0 && currentQuestionIndex < questions.length) {
      loadQuestion(questions[currentQuestionIndex].id);
    }
  }, [currentQuestionIndex, questions, status]);

  const loadQuestion = async (questionId: number) => {
    setLoading(true);
    setError(null);
    setAnswerResult(null);
    
    try {
      const question = await examAPI.getQuestion(questionId);
      if (question) {
        setCurrentQuestion(question);
        
        // 문제 번호 점자 패턴 전송
        if (isConnected && currentQuestionIndex < 5) {
          const pattern = BraillePatternFactory.createNumberPattern((currentQuestionIndex + 1) as 1 | 2 | 3 | 4 | 5);
          writeCells([pattern]);
        }
      }
    } catch (err) {
      const errorMsg = '문제를 불러오는 중 오류가 발생했습니다.';
      setError(errorMsg);
      speak(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleStartExam = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await examAPI.startExam();
      if (result) {
        // TODO: 문제 목록 가져오기
        // 임시로 빈 배열
        const questionList: Question[] = [];
        setQuestions(questionList);
        
        if (questionList.length > 0) {
          startExamStore(questionList.length, 12 * 60 * 60); // 12시간
          setStatus('running');
          loadQuestion(questionList[0].id);
          speak('시험이 시작되었습니다.');
        } else {
          speak('시험 문제를 불러올 수 없습니다.');
        }
      }
    } catch (err) {
      const errorMsg = '시험 시작 중 오류가 발생했습니다.';
      setError(errorMsg);
      speak(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleAnswer = async (answer: number) => {
    if (!currentQuestion) return;

    setLoading(true);
    setError(null);

    try {
      const result = await examAPI.submitAnswer(currentQuestion.id, answer);
      if (result) {
        setAnswerResult(result);
        setAnswer(currentQuestionIndex, answer.toString());
      }
    } catch (err) {
      const errorMsg = '답안 제출 중 오류가 발생했습니다.';
      setError(errorMsg);
      speak(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleNext = () => {
    if (currentQuestionIndex < totalQuestions - 1) {
      nextQuestion();
    } else {
      speak('마지막 문제입니다.');
    }
  };

  const handlePrev = () => {
    if (currentQuestionIndex > 0) {
      prevQuestion();
    } else {
      speak('첫 번째 문제입니다.');
    }
  };

  const finishExam = () => {
    setStatus('finished');
    speak('시험이 종료되었습니다.');
  };

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // 음성 명령 처리
  const { onSpeech } = useVoiceCommands({
    home: () => {
      stopTTS();
      navigate('/');
      stopSTT();
    },
    back: () => {
      if (status === 'running') {
        setStatus('paused');
        speak('시험을 일시정지했습니다.');
      } else {
        navigate('/');
      }
    },
    help: () => {
      stopTTS();
      const helpText = '실전 모의고사 모드입니다. 음성으로 "다음 문제", "이전 문제", "1번 문제" 등을 말할 수 있습니다.';
      speak(helpText);
    },
  });

  useEffect(() => {
    if (!transcript) return;
    
    const normalized = transcript.toLowerCase().trim();
    
    if (normalized.includes('다음 문제') || normalized.includes('다음문제')) {
      stopTTS();
      handleNext();
      stopSTT();
      return;
    }
    
    if (normalized.includes('이전 문제') || normalized.includes('이전문제')) {
      stopTTS();
      handlePrev();
      stopSTT();
      return;
    }
    
    // 숫자로 문제 이동
    const numberMatch = normalized.match(/(\d+)\s*(번|번째|번 문제)/);
    if (numberMatch) {
      const num = parseInt(numberMatch[1]);
      if (num > 0 && num <= totalQuestions) {
        stopTTS();
        goToQuestion(num - 1);
        speak(`${num}번 문제로 이동합니다.`);
        stopSTT();
        return;
      }
    }
    
    onSpeech(transcript);
  }, [transcript, onSpeech, totalQuestions, goToQuestion]);

  const showToastMessage = (message: string) => {
    setToastMessage(message);
    setShowToast(true);
  };

  const maxChoice = currentQuestion?.choice5 ? 5 : 4;

  return (
    <AppShellMobile title="실전 모의고사" className="relative">
      <div className="mb-4">
        <SpeechBar isListening={isListening} transcript={transcript} />
      </div>

      <div className="p-4">
        {status === 'setup' && (
          <div className="space-y-4">
            <div className="bg-card border border-border rounded-lg p-6 text-center">
              <h3 className="text-lg font-semibold mb-4">실전 모의고사</h3>
              <p className="text-base text-muted mb-6">
                12시간 수능 시험을 시뮬레이션합니다.
              </p>
              <button
                onClick={handleStartExam}
                className="btn-primary w-full"
                disabled={loading}
                aria-label="시험 시작"
              >
                {loading ? '시작 중...' : '시험 시작'}
              </button>
            </div>
          </div>
        )}

        {status === 'running' && (
          <div className="space-y-6">
            <div className="bg-card border border-border rounded-lg p-4 text-center">
              <p className="text-sm text-muted mb-1">남은 시간</p>
              <p className="text-2xl font-bold">{formatTime(remainingTime)}</p>
              <p className="text-sm text-muted mt-2">
                문제 {currentQuestionIndex + 1} / {totalQuestions}
              </p>
            </div>

            {loading && !currentQuestion && (
              <div className="text-center py-8">
                <p className="text-muted">로딩 중...</p>
              </div>
            )}

            {error && (
              <div className="bg-error/10 border border-error rounded-lg p-4">
                <p className="text-error">{error}</p>
              </div>
            )}

            {currentQuestion && (
              <>
                <div className="flex gap-2 mb-4">
                  <button
                    onClick={handlePrev}
                    className="btn-ghost"
                    disabled={currentQuestionIndex === 0}
                    aria-label="이전 문제"
                  >
                    ← 이전
                  </button>
                  <button
                    onClick={handleNext}
                    className="btn-ghost"
                    disabled={currentQuestionIndex === totalQuestions - 1}
                    aria-label="다음 문제"
                  >
                    다음 →
                  </button>
                </div>

                <QuestionDisplay
                  question={currentQuestion}
                  onSpeak={speak}
                />

                {!answerResult && (
                  <AnswerInput
                    onAnswer={handleAnswer}
                    onSpeak={speak}
                    maxChoice={maxChoice}
                  />
                )}

                {answerResult && (
                  <AnswerResultComponent
                    result={answerResult}
                    userAnswer={parseInt(answers[currentQuestionIndex] || '0')}
                    onSpeak={speak}
                  />
                )}
              </>
            )}
          </div>
        )}

        {status === 'finished' && (
          <div className="bg-card border border-border rounded-lg p-6 text-center">
            <h3 className="text-lg font-semibold mb-4">시험 종료</h3>
            <p className="text-base mb-4">
              시험이 완료되었습니다.
            </p>
            <button
              onClick={() => navigate('/')}
              className="btn-primary"
              aria-label="홈으로"
            >
              홈으로
            </button>
          </div>
        )}
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
