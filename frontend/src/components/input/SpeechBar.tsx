// import React from 'react';

interface SpeechBarProps {
  transcript: string;
  isListening: boolean;
  className?: string;
}

export default function SpeechBar({ 
  transcript, 
  isListening, 
  className = "" 
}: SpeechBarProps) {
  if (!isListening && !transcript) {
    return null;
  }

  return (
    <div
      className={`bg-white border border-gray-200 rounded-md p-2 shadow-sm ${className}`}
      aria-live="polite"
    >
      <div className="flex items-center space-x-1.5">
        <div
          className={`w-1.5 h-1.5 rounded-full ${
            isListening ? 'bg-red-500 animate-pulse' : 'bg-gray-300'
          }`}
        />
        <span className="text-xs text-gray-600">
          {isListening ? '🎤 음성 인식 중...' : '✅ 인식 완료'}
        </span>
      </div>

      {transcript && (
        <div className="mt-1.5 p-1.5 bg-gray-50 rounded text-xs text-gray-800 italic">
          {transcript}
        </div>
      )}
    </div>
  );
}
