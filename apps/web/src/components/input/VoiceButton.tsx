// import React from 'react';
import { Mic, MicOff } from 'lucide-react';

interface VoiceButtonProps {
  onStart?: () => void;
  onStop?: () => void;
  isListening?: boolean;
  disabled?: boolean;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export default function VoiceButton({
  onStart,
  onStop,
  isListening = false,
  disabled = false,
  className = '',
  size = 'md',
}: VoiceButtonProps) {
  const handleClick = () => {
    if (disabled) return;
    if (isListening) onStop?.();
    else onStart?.();
  };

  const sizeClass =
    size === 'sm' ? 'p-2' : size === 'lg' ? 'p-4' : 'p-3';
  const iconSize = size === 'sm' ? 16 : size === 'lg' ? 24 : 20;

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={disabled}
      role="switch"
      aria-checked={isListening}
      aria-label={isListening ? '음성 인식 중지' : '음성 인식 시작'}
      className={`
        ${sizeClass} rounded-full transition-colors
        focus:outline-none focus:ring-2 focus:ring-offset-2
        ${isListening
          ? 'bg-red-500 hover:bg-red-600 text-white focus:ring-red-400'
          : 'bg-blue-500 hover:bg-blue-600 text-white focus:ring-blue-400'}
        disabled:opacity-50 disabled:cursor-not-allowed
        ${className}
      `}
    >
      {isListening ? <MicOff size={iconSize} /> : <Mic size={iconSize} />}
    </button>
  );
}
