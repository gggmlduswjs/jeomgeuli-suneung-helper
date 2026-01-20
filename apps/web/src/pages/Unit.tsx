/**
 * 학습 단위 페이지
 * 개념/작품/문제 통합 뷰어
 */
import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import AppShellMobile from '../components/ui/AppShellMobile';
import SpeechBar from '../components/input/SpeechBar';
import useTTS from '../hooks/useTTS';
import useSTT from '../hooks/useSTT';
import useVoiceCommands from '../hooks/useVoiceCommands';
import ToastA11y from '../components/system/ToastA11y';
import UnitViewer from '../components/unit/UnitViewer';
import AnswerInput from '../components/question/AnswerInput';
import AnswerResultComponent from '../components/question/AnswerResult';
import { unitsAPI } from '../services/units';
import { answersAPI } from '../services/answers';
import { progressAPI } from '../services/progress';
import { aiAPI } from '../services/ai';
import AIQuestionInput from '../components/ai/AIQuestionInput';
import AIExplanationCard from '../components/ai/AIExplanationCard';
import { useBrailleBLE } from '../hooks/useBrailleBLE';
import type { Unit } from '../types/unit';
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
  const [userAnswer, setUserAnswer] = useState<number | null>(null);
  const [answerResult, setAnswerResult] = useState<{ is_correct: boolean; correct_answer: number; explanation?: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aiExplanation, setAiExplanation] = useState<string | null>(null);
  const [isAiLoading, setIsAiLoading] = useState(false);
  
  const { saveProgress } = useProgressStore();
  const { sendText } = useBrailleBLE();

  useEffect(() => {
    if (unitId) {
      loadUnit(unitId);
    }
  }, [unitId]);

  const loadUnit = async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await unitsAPI.get(id);
      setUnit(data);
      
      // 진도 저장
      await progressAPI.save({
        user_id: 'u_demo',
        unit_id: id,
        lesson_id: data.lesson_id,
      });
      
      // AI 설명 요청 (강의 대본 기반)
      if (data.type !== 'QUESTION') {
        loadAIExplanation(id);
      }
      
      // 음성 안내
      if (data.type === 'QUESTION') {
        speak(`${data.title}입니다. 문제를 읽고 답하세요.`);
      } else {
        speak(`${data.title}입니다.`);
      }
    } catch (err) {
      const errorMsg = '학습 단위를 불러오는 중 오류가 발생했습니다.';
      setError(errorMsg);
      speak(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const loadAIExplanation = async (unitId: string) => {
    setIsAiLoading(true);
    try {
      const response = await aiAPI.teachUnit(unitId);
      setAiExplanation(response.explanation);
      // AI 설명을 TTS로 재생
      if (response.explanation) {
        speak(response.explanation);
        // 점자로도 출력
        try {
          await sendText(response.explanation);
        } catch (err) {
          console.error('[Unit] 점자 출력 실패:', err);
          // 점자 실패해도 계속 진행
        }
      }
    } catch (err) {
      console.error('[Unit] AI 설명 로드 실패:', err);
      // AI 실패해도 계속 진행
    } finally {
      setIsAiLoading(false);
    }
  };

  const handleQuestion = async (question: string) => {
    if (!unit) return;
    
    setIsAiLoading(true);
    try {
      const response = await aiAPI.answerQuestion(question, unit.unit_id, unit.lesson_id);
      setAiExplanation(response.answer);
      speak(response.answer);
    } catch (err) {
      console.error('[Unit] AI 질문 답변 실패:', err);
      speak('죄송합니다. 답변을 생성하는 중 오류가 발생했습니다.');
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
      
      if (isCorrect) {
        speak('정답입니다!');
      } else {
        speak(`오답입니다. 정답은 ${unit.question!.answer}번입니다.`);
      }
    } catch (err) {
      console.error('[Unit] 답안 제출 실패:', err);
    }
  };

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
    <AppShellMobile title={unit?.title || '학습 단위'} className="relative">
      <div className="mb-4">
        <SpeechBar isListening={isListening} transcript={transcript} />
      </div>

      <div className="p-4">
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
            
            {/* AI 설명 표시 */}
            {isAiLoading && (
              <div className="bg-info/10 border border-info rounded-lg p-4">
                <p className="text-info">AI가 설명을 생성하고 있습니다...</p>
              </div>
            )}
            
            {aiExplanation && !isAiLoading && (
              <AIExplanationCard
                explanation={aiExplanation}
                isLoading={false}
                onReplay={async () => {
                  speak(aiExplanation);
                  // 점자로도 출력
                  try {
                    await sendText(aiExplanation);
                  } catch (err) {
                    console.error('[Unit] 점자 출력 실패:', err);
                  }
                }}
              />
            )}
            
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

      <ToastA11y
        message={toastMessage}
        isVisible={showToast}
        duration={3000}
        onClose={() => setShowToast(false)}
      />
    </AppShellMobile>
  );
}
