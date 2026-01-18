import { useState, useEffect } from 'react';
import useSTT from '../../../hooks/useSTT';

interface AnswerInputProps {
  onAnswer: (answer: number) => void;
  onSpeak: (text: string) => void;
  maxChoice: number;
}

export default function AnswerInput({ onAnswer, onSpeak, maxChoice }: AnswerInputProps) {
  const { start: startSTT, stop: stopSTT, isListening, transcript } = useSTT();
  const [textAnswer, setTextAnswer] = useState('');

  // 음성 입력 처리
  useEffect(() => {
    if (!transcript) return;

    const normalized = transcript.toLowerCase().trim();
    
    // 숫자 추출 (1번, 2번, 첫번째, 두번째 등)
    const numberMatch = normalized.match(/(\d+)\s*(번|번째|번 선택지)/);
    if (numberMatch) {
      const num = parseInt(numberMatch[1]);
      if (num >= 1 && num <= maxChoice) {
        stopSTT();
        onAnswer(num);
        return;
      }
    }

    // 한글 숫자 처리
    const koreanNumbers: Record<string, number> = {
      '첫': 1, '첫번째': 1, '일': 1,
      '두': 2, '두번째': 2, '이': 2,
      '세': 3, '세번째': 3, '삼': 3,
      '네': 4, '네번째': 4, '사': 4,
      '다섯': 5, '다섯번째': 5, '오': 5,
    };

    for (const [key, value] of Object.entries(koreanNumbers)) {
      if (normalized.includes(key) && value <= maxChoice) {
        stopSTT();
        onAnswer(value);
        return;
      }
    }
  }, [transcript, maxChoice, onAnswer, stopSTT]);

  const handleTextSubmit = () => {
    const num = parseInt(textAnswer);
    if (num >= 1 && num <= maxChoice) {
      onAnswer(num);
      setTextAnswer('');
    } else {
      onSpeak(`1부터 ${maxChoice}까지의 숫자를 입력해주세요.`);
    }
  };

  const handleVoiceInput = () => {
    if (isListening) {
      stopSTT();
      onSpeak('음성 입력을 중지했습니다.');
    } else {
      startSTT();
      onSpeak('답안을 말씀해주세요. 예: 1번, 2번');
    }
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">답안 입력</h3>
      
      <div className="flex gap-2">
        <input
          type="number"
          min="1"
          max={maxChoice}
          value={textAnswer}
          onChange={(e) => setTextAnswer(e.target.value)}
          placeholder={`1-${maxChoice}번`}
          className="flex-1 px-4 py-2 border border-border rounded-lg"
          aria-label="답안 번호 입력"
        />
        <button
          onClick={handleTextSubmit}
          className="btn-primary px-6"
          aria-label="답안 제출"
        >
          제출
        </button>
      </div>

      <div className="flex gap-2">
        <button
          onClick={handleVoiceInput}
          className={`flex-1 ${isListening ? 'btn-error' : 'btn-accent'}`}
          aria-label={isListening ? '음성 입력 중지' : '음성 입력 시작'}
        >
          {isListening ? '음성 입력 중지' : '음성으로 답하기'}
        </button>
      </div>

      {isListening && transcript && (
        <div className="bg-accent/10 border border-accent rounded-lg p-2">
          <p className="text-sm text-muted">인식 중: {transcript}</p>
        </div>
      )}
    </div>
  );
}


