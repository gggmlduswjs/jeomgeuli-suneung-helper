import { useState, useEffect } from 'react';
import useSTT from '../../../hooks/useSTT';

interface PassageInputProps {
  onAnalyze: (passage: string) => void;
  onSpeak: (text: string) => void;
}

export default function PassageInput({ onAnalyze, onSpeak }: PassageInputProps) {
  const [text, setText] = useState('');
  const { start: startSTT, stop: stopSTT, isListening, transcript } = useSTT();

  // 음성 입력 처리
  const handleVoiceInput = () => {
    if (isListening) {
      stopSTT();
      onSpeak('음성 입력을 중지했습니다.');
    } else {
      startSTT();
      onSpeak('지문을 말씀해주세요.');
    }
  };

  // 음성 입력이 완료되면 텍스트에 추가
  const handleTranscript = () => {
    if (transcript && !isListening) {
      setText(prev => prev + (prev ? ' ' : '') + transcript);
    }
  };

  // transcript가 변경될 때마다 처리
  useEffect(() => {
    if (transcript && !isListening) {
      setText(prev => prev + (prev ? ' ' : '') + transcript);
    }
  }, [transcript, isListening]);

  const handleSubmit = () => {
    if (text.trim()) {
      onAnalyze(text.trim());
    } else {
      onSpeak('지문을 입력해주세요.');
    }
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">지문 입력</h3>
      
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="지문을 입력하거나 음성으로 말씀해주세요..."
        className="w-full min-h-[200px] px-4 py-3 border border-border rounded-lg resize-y"
        aria-label="지문 입력"
      />

      <div className="flex gap-2">
        <button
          onClick={handleVoiceInput}
          className={`flex-1 ${isListening ? 'btn-error' : 'btn-accent'}`}
          aria-label={isListening ? '음성 입력 중지' : '음성 입력 시작'}
        >
          {isListening ? '음성 입력 중지' : '음성으로 입력'}
        </button>
        <button
          onClick={handleSubmit}
          className="btn-primary px-6"
          disabled={!text.trim()}
          aria-label="분석 시작"
        >
          분석
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

