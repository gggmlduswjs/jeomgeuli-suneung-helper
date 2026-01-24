/**
 * AI 질문 입력 컴포넌트
 * 사용자가 질문을 입력하면 AI가 답변
 */
import { useState } from 'react';
import { useAILearningAssistant } from '../../hooks/useAILearningAssistant';
import useSTT from '../../hooks/useSTT';
import MicButton from '../input/MicButton';

interface AIQuestionInputProps {
  unitId?: string;
  lessonId?: string;
  onAnswer?: (answer: string) => void;
}

export default function AIQuestionInput({ 
  unitId, 
  lessonId,
  onAnswer 
}: AIQuestionInputProps) {
  const [question, setQuestion] = useState('');
  const { askQuestion, isAnswering } = useAILearningAssistant(unitId, lessonId);
  const { start: startSTT, stop: stopSTT, isListening, transcript } = useSTT();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || isAnswering) return;

    const answer = await askQuestion(question);
    if (answer && onAnswer) {
      onAnswer(answer);
    }
    setQuestion('');
  };

  const handleVoiceInput = () => {
    if (isListening) {
      stopSTT();
    } else {
      startSTT();
    }
  };

  // 음성 인식 결과가 있으면 질문에 자동 입력
  if (transcript && !isListening && transcript !== question) {
    setQuestion(transcript);
  }

  return (
    <div className="bg-card border border-border rounded-lg p-4">
      <h4 className="font-semibold mb-2">AI에게 질문하기</h4>
      
      <form onSubmit={handleSubmit} className="space-y-2">
        <div className="flex gap-2">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="질문을 입력하세요..."
            className="flex-1 px-3 py-2 border border-border rounded-lg"
            disabled={isAnswering}
          />
          <MicButton
            onClick={handleVoiceInput}
            isListening={isListening}
            disabled={isAnswering}
          />
        </div>
        
        <button
          type="submit"
          disabled={!question.trim() || isAnswering}
          className="btn-primary w-full"
        >
          {isAnswering ? '답변 생성 중...' : '질문하기'}
        </button>
      </form>
      
      {transcript && (
        <div className="mt-2 text-sm text-muted">
          인식된 음성: {transcript}
        </div>
      )}
    </div>
  );
}
