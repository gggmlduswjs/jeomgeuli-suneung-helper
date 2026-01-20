import { useEffect, useState, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import AppShellMobile from '../components/ui/AppShellMobile';
import SpeechBar from '../components/input/SpeechBar';
import useTTS from '../hooks/useTTS';
import useSTT from '../hooks/useSTT';
import useVoiceCommands from '../hooks/useVoiceCommands';
import ToastA11y from '../components/system/ToastA11y';
import { examAPI, type Question, type AnswerResult } from '../lib/api';
import { useLearnStore } from '../store/learnStore';
import QuestionDisplay from '../components/question/QuestionDisplay';
import AnswerInput from '../components/question/AnswerInput';
import AnswerResultComponent from '../components/question/AnswerResult';
import WrongAnswerList from '../components/question/WrongAnswerList';

type ViewMode = 'question' | 'wrongAnswers';

export default function Question() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { speak, stop: stopTTS } = useTTS();
  const { start: startSTT, stop: stopSTT, isListening, transcript } = useSTT();
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  
  // State
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null);
  const [answerResult, setAnswerResult] = useState<AnswerResult | null>(null);
  const [userAnswer, setUserAnswer] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('question');
  
  // Store
  const { wrongAnswers, setQuestion, addWrongAnswer } = useLearnStore();

  // URL에서 questionId 가져오기
  const questionId = searchParams.get('id') ? parseInt(searchParams.get('id')!) : null;
  const subjectParam = searchParams.get('subject') || 'math';
  const modeParam = searchParams.get('mode');
  
  // 점자 읽기 모드 설정
  type ReadingMode = 'braille-only' | 'braille-with-audio' | 'audio-first';
  const readingMode: ReadingMode = modeParam === 'braille-read'
    ? 'braille-only'
    : modeParam === 'braille-with-audio'
    ? 'braille-with-audio'
    : 'braille-only'; // 기본값: 점자 읽기 모드

  // 페이지 진입 시 문제 로드
  useEffect(() => {
    if (questionId) {
      loadQuestion(questionId);
    } else {
      // 문제 ID가 없으면 오답 노트 보기
      setViewMode('wrongAnswers');
    }
  }, [questionId]);

  // 페이지 진입 시 자동 음성 안내
  useEffect(() => {
    const welcomeMessage = viewMode === 'wrongAnswers'
      ? '오답 노트 모드입니다. 틀린 문제를 다시 풀어볼 수 있습니다.'
      : readingMode === 'braille-only'
      ? '점자 문제 읽기 모드입니다. 점자로 문제를 읽고 답하세요.'
      : '문항 풀이 오답노트 모드입니다. 문제를 풀고 오답을 기록할 수 있습니다.';
    const timer = setTimeout(() => {
      speak(welcomeMessage);
    }, 500);
    return () => clearTimeout(timer);
  }, [speak, viewMode, readingMode]);

  const loadQuestion = async (id: number) => {
    setLoading(true);
    setError(null);
    setAnswerResult(null);
    setUserAnswer(null);
    
    try {
      const question = await examAPI.getQuestion(id);
      if (question) {
        setCurrentQuestion(question);
        setQuestion(question);
      } else {
        const errorMsg = '문제를 불러올 수 없습니다.';
        setError(errorMsg);
        speak(errorMsg);
      }
    } catch (err) {
      const errorMsg = '문제를 불러오는 중 오류가 발생했습니다.';
      setError(errorMsg);
      speak(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleAnswer = async (answer: number) => {
    if (!currentQuestion) return;

    setUserAnswer(answer);
    setLoading(true);
    setError(null);

    try {
      const result = await examAPI.submitAnswer(currentQuestion.id, answer);
      if (result) {
        setAnswerResult(result);
        
        // 오답이면 오답 노트에 추가
        if (!result.is_correct) {
          addWrongAnswer({
            question: currentQuestion,
            userAnswer: answer,
            correctAnswer: result.correct_answer,
            attemptedAt: new Date().toISOString(),
          });
        }
      } else {
        const errorMsg = '답안 제출에 실패했습니다.';
        setError(errorMsg);
        speak(errorMsg);
      }
    } catch (err) {
      const errorMsg = '답안 제출 중 오류가 발생했습니다.';
      setError(errorMsg);
      speak(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleNextQuestion = () => {
    // 다음 문제 로드 (임시로 같은 문제 다시 로드)
    if (currentQuestion) {
      loadQuestion(currentQuestion.id);
    }
  };

  const handleSelectWrongAnswer = (question: Question) => {
    navigate(`/question?id=${question.id}`);
    setViewMode('question');
    loadQuestion(question.id);
  };

  // 청크 네비게이션을 위한 ref (QuestionDisplay에서 접근)
  const chunkNavigationRef = useRef<{ next: () => void; prev: () => void; reset: () => void } | null>(null);

  // 음성 명령 처리
  const { onSpeech } = useVoiceCommands({
    home: () => {
      stopTTS();
      navigate('/');
      stopSTT();
    },
    back: () => {
      if (viewMode === 'wrongAnswers') {
        navigate('/');
      } else {
        setViewMode('wrongAnswers');
        speak('오답 노트로 돌아갑니다.');
      }
    },
    help: () => {
      stopTTS();
      const helpText = '문항 풀이 모드입니다. 문제를 풀고 정답 여부를 점자 패턴으로 확인할 수 있습니다. 음성으로 "1번", "2번" 등으로 답안을 입력할 수 있습니다. "다음", "이전", "반복" 명령으로 점자 청크를 이동할 수 있습니다.';
      speak(helpText);
    },
    // 청크 네비게이션 명령
    next: () => {
      if (chunkNavigationRef.current) {
        chunkNavigationRef.current.next();
        speak('다음 청크로 이동했습니다.');
      }
    },
    prev: () => {
      if (chunkNavigationRef.current) {
        chunkNavigationRef.current.prev();
        speak('이전 청크로 이동했습니다.');
      }
    },
    repeat: () => {
      if (chunkNavigationRef.current) {
        chunkNavigationRef.current.reset();
        speak('현재 청크를 다시 읽습니다.');
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

  const maxChoice = currentQuestion?.choice5 ? 5 : 4;

  return (
    <AppShellMobile title="문항 풀이·오답노트" className="relative">
      <div className="mb-4">
        <SpeechBar isListening={isListening} transcript={transcript} />
      </div>

      <div className="p-4">
        {viewMode === 'wrongAnswers' ? (
          <div className="space-y-4">
            <button
              onClick={() => navigate('/')}
              className="btn-ghost mb-4"
              aria-label="홈으로 돌아가기"
            >
              ← 홈
            </button>
            <WrongAnswerList
              wrongAnswers={wrongAnswers}
              onSelect={handleSelectWrongAnswer}
              onSpeak={speak}
            />
          </div>
        ) : (
          <>
            {loading && !currentQuestion && (
              <div className="text-center py-8">
                <p className="text-muted">로딩 중...</p>
              </div>
            )}

            {error && (
              <div className="bg-error/10 border border-error rounded-lg p-4 mb-4">
                <p className="text-error">{error}</p>
              </div>
            )}

            {currentQuestion && (
              <div className="space-y-6">
                <div className="flex gap-2 mb-4">
                  <button
                    onClick={() => setViewMode('wrongAnswers')}
                    className="btn-ghost"
                    aria-label="오답 노트 보기"
                  >
                    오답 노트
                  </button>
                  <button
                    onClick={handleNextQuestion}
                    className="btn-ghost"
                    aria-label="다음 문제"
                  >
                    다음 문제 →
                  </button>
                </div>

                <QuestionDisplay
                  question={currentQuestion}
                  onSpeak={speak}
                  chunkNavigationRef={chunkNavigationRef}
                  readingMode={readingMode}
                  subject={subjectParam as 'math' | 'korean' | 'english' | 'science' | 'social'}
                />

                {!answerResult && (
                  <AnswerInput
                    onAnswer={handleAnswer}
                    onSpeak={speak}
                    maxChoice={maxChoice}
                  />
                )}

                {answerResult && userAnswer !== null && (
                  <div className="space-y-4">
                    <AnswerResultComponent
                      result={answerResult}
                      userAnswer={userAnswer}
                      onSpeak={speak}
                    />
                    <button
                      onClick={handleNextQuestion}
                      className="btn-primary w-full"
                      aria-label="다음 문제"
                    >
                      다음 문제
                    </button>
                  </div>
                )}
              </div>
            )}
          </>
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

