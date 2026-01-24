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
      className={`bg-white border border-gray-200 rounded-lg p-4 shadow-sm ${className}`}
      aria-live="polite"
    >
      <div className="flex items-center space-x-2">
        <div
          className={`w-2 h-2 rounded-full ${
            isListening ? 'bg-red-500 animate-pulse' : 'bg-gray-300'
          }`}
        />
        <span className="text-sm text-gray-600">
          {isListening ? '🎤 음성 인식 중...' : '✅ 인식 완료'}
        </span>
      </div>

      {transcript && (
        <div className="mt-2 p-2 bg-gray-50 rounded text-sm text-gray-800 italic">
          {transcript}
        </div>
      )}
    </div>
  );
}
