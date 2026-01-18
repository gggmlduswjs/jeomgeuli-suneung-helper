import { useEffect, useState } from "react";
import VoiceService from "../../services/VoiceService";
import { useVoiceStore } from "../../store/voice";

type Props = {
  onResult?: (text: string) => void;
  className?: string;
  label?: string; // 접근성 라벨 커스터마이즈
};

export default function MicButton({ onResult, className = "", label = "음성 입력" }: Props) {
  const isListening = useVoiceStore(state => state.isListening);
  const transcript = useVoiceStore(state => state.transcript);
  const error = useVoiceStore(state => state.sttError);
  const [localError, setLocalError] = useState<string | null>(null);

  // STT 결과 처리
  useEffect(() => {
    if (transcript && onResult) {
      onResult(transcript);
    }
  }, [transcript, onResult]);

  // 에러 처리
  useEffect(() => {
    if (error) {
      setLocalError(error);
    } else {
      setLocalError(null);
    }
  }, [error]);

  const start = async () => {
    try {
      console.log('[MicButton] 음성 인식 시작 시도...');
      await VoiceService.startSTT({
        onResult: (text) => {
          console.log(`[MicButton] 인식 결과: "${text}"`);
          onResult?.(text);
        },
        onError: (errorMsg) => {
          console.error(`[MicButton] 오류 발생: ${errorMsg}`);
          setLocalError(errorMsg);
        },
        autoStop: true,
      });
    } catch (err) {
      console.warn('[MicButton] 음성 인식 시작 실패:', err);
      setLocalError("음성 인식을 시작할 수 없습니다.");
      onResult?.("");
    }
  };

  const stop = () => {
    console.log('[MicButton] 음성 인식 중지 요청');
    VoiceService.stopSTT();
  };

  const handleClick = () => {
    if (isListening) {
      console.log('[MicButton] 마이크 버튼 클릭: 중지');
      stop();
    } else {
      console.log('[MicButton] 마이크 버튼 클릭: 시작');
      start();
    }
  };

  // 언마운트 시 정리
  useEffect(() => {
    return () => {
      VoiceService.stopSTT();
    };
  }, []);

  const displayError = localError || error;
  const disabled = !!displayError;

  return (
    <div className="inline-flex flex-col items-center">
      <button
        type="button"
        onClick={handleClick}
        disabled={disabled}
        role="switch"
        aria-checked={isListening}
        aria-label={label}
        className={`w-16 h-16 rounded-full flex items-center justify-center shadow-lg hover:shadow-xl transition-all focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2
          ${isListening ? "bg-red-500 text-white animate-pulse" : "bg-accent text-primary"}
          ${disabled ? "opacity-50 cursor-not-allowed" : ""}
          ${className}
        `}
      >
        {isListening ? (
          <div aria-hidden className="w-6 h-6 bg-white/90 rounded-full" />
        ) : (
          // 마이크 아이콘 (SVG)
          <svg aria-hidden className="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
            <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
          </svg>
        )}
      </button>

      {/* 상태 텍스트 (스크린리더용) */}
      <span className="sr-only" aria-live="polite">
        {isListening ? "음성 입력 중" : "음성 대기"}
      </span>

      {/* 오류 메시지 (필요시 UI로 노출) */}
      {displayError && (
        <span className="mt-2 text-xs text-red-600" aria-live="polite">
          {displayError.includes("권한")
            ? "마이크 권한이 거부되었습니다."
            : displayError.includes("감지")
            ? "음성이 감지되지 않았습니다."
            : displayError.includes("마이크")
            ? "마이크가 감지되지 않았습니다."
            : displayError}
        </span>
      )}

      {/* 디버그용 텍스트 (원하면 숨겨도 됨) */}
      {transcript && (
        <span className="mt-1 text-xs text-gray-500 truncate max-w-[12rem]" title={transcript}>
          {transcript}
        </span>
      )}
    </div>
  );
}
