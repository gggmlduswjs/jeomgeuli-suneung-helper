import { useState, useRef, useEffect, useMemo, useCallback } from "react";
import { Send, Mic, MicOff, Volume2, VolumeX } from "lucide-react";
import { useTTS } from "@/hooks/useTTS";
import useVoiceCommands from "@/hooks/useVoiceCommands";

interface ChatLikeInputProps {
  onSubmit: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
  autoSubmitOnVoiceCommand?: boolean; // 음성 명령으로 자동 전송 여부
  autoSubmitOnTranscriptDelay?: number; // 전역 transcript 누적 후 자동 전송 지연(ms), 미설정 시 비활성
}

export default function ChatLikeInput({
  onSubmit,
  disabled = false,
  placeholder = "메시지를 입력하거나 음성으로 말하세요...",
  className = "",
  autoSubmitOnVoiceCommand = true, // 기본값: true
  autoSubmitOnTranscriptDelay,
}: ChatLikeInputProps) {
  const [inputText, setInputText] = useState("");
  const [isComposing, setIsComposing] = useState(false); // IME(한글) 조합 여부
  const inputRef = useRef<HTMLInputElement>(null);
  const lastTranscriptRef = useRef(""); // 중복 처리 방지
  const lastGlobalTextRef = useRef("");
  const lastGlobalTimeRef = useRef(0);
  const autoSendTimerRef = useRef<number | undefined>(undefined);

  const { speak: _speak, stop, isSpeaking } = useTTS();
  const isListening = false; // 전역 STT만 사용
  const transcript = "";     // 전역 voice:transcript만 사용

  const handleSubmit = useCallback((e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const text = inputText.trim();
    if (!text || disabled || isListening || isComposing) return;
    onSubmit(text);
    setInputText("");
    inputRef.current?.focus();
  }, [inputText, disabled, isListening, isComposing, onSubmit]);

  // 음성 명령 처리
  const { onSpeech } = useVoiceCommands({
    submit: () => {
      if (inputText.trim() && !disabled && !isListening) {
        handleSubmit();
      }
    },
    clear: () => {
      setInputText("");
      inputRef.current?.focus();
    },
    stop: () => {
      if (isListening) stopSTT();
      if (isSpeaking) stop();
    },
  });

  // 로컬 STT 미사용: 전역 voice:transcript로만 입력 누적

  // 전역 Global STT에서 오는 문장을 입력란에 누적 (탐색/자유변환 등 공통)
  useEffect(() => {
    const onVoiceTranscript = (e: Event) => {
      const detail = (e as CustomEvent)?.detail as { text?: string } | undefined;
      const text = detail?.text;
      if (!text || !text.trim()) return;
      const trimmed = text.trim();
      const now = Date.now();
      // 1.5초 내 동일 문장 재유입 차단
      if (trimmed === lastGlobalTextRef.current && now - lastGlobalTimeRef.current < 1500) {
        return;
      }
      lastGlobalTextRef.current = trimmed;
      lastGlobalTimeRef.current = now;
      setInputText(prev => (prev && prev.trim() ? prev + " " + trimmed : trimmed));
    };
    window.addEventListener('voice:transcript', onVoiceTranscript as EventListener);
    return () => window.removeEventListener('voice:transcript', onVoiceTranscript as EventListener);
  }, []);

  // 전역 transcript 누적 후 자동 전송 (옵션)
  useEffect(() => {
    if (!autoSubmitOnTranscriptDelay) return;
    if (!inputText || !inputText.trim()) return;
    if (isListening) return;
    window.clearTimeout(autoSendTimerRef.current);
    autoSendTimerRef.current = window.setTimeout(() => {
      // 입력이 남아 있고 청취 중이 아니면 자동 전송
      if (inputText.trim() && !isListening && !disabled && !isComposing) {
        handleSubmit();
      }
    }, autoSubmitOnTranscriptDelay) as unknown as number;
    return () => window.clearTimeout(autoSendTimerRef.current);
  }, [inputText, isListening, disabled, isComposing, autoSubmitOnTranscriptDelay, handleSubmit]);

  // 로컬 transcript 기반 처리 제거 (전역 브로드캐스트에서만 처리)

  // 언마운트 시 TTS/STT 정리
  useEffect(() => {
    return () => {
      try {
        if (isSpeaking) stop();
        if (isListening) stopSTT();
      } catch {}
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const canSubmit = useMemo(
    () => !disabled && !isListening && inputText.trim().length > 0 && !isComposing,
    [disabled, isListening, inputText, isComposing]
  );

  const micDisabled = useMemo(() => disabled || isSpeaking, [disabled, isSpeaking]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    // 한글 조합 중에는 Enter 방지
    if (isComposing) return;
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    } else if (e.key === "Escape") {
      if (isListening) stopSTT();
      if (isSpeaking) stop();
    }
  };

  const handleMicClick = () => {};

  const handleStopClick = () => {
    if (isSpeaking) stop();
    if (isListening) stopSTT();
  };

  return (
    <div
      className={`
        fixed bottom-0 left-0 right-0 bg-white border-t border-border
        p-4 shadow-toss-lg ${className}
      `}
      aria-label="메시지 입력 영역"
    >
      <form onSubmit={handleSubmit} className="flex gap-3 items-end">
        {/* 입력창 */}
        <div className="flex-1">
          <input
            ref={inputRef}
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            onCompositionStart={() => setIsComposing(true)}
            onCompositionEnd={() => setIsComposing(false)}
            placeholder={placeholder}
            disabled={disabled}
            autoComplete="off"
            inputMode="text"
            enterKeyHint="send"
            className="
              w-full px-4 py-2.5 rounded-2xl border border-border
              bg-bg text-fg placeholder:text-muted
              focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent
              disabled:opacity-50 disabled:cursor-not-allowed
              text-base
            "
            aria-label="메시지 입력"
            aria-describedby="input-help"
          />
          <div id="input-help" className="sr-only">
            Enter로 전송, Esc로 음성 중지
          </div>
        </div>

        {/* 음성 버튼 */}
        <button
          type="button"
          onClick={handleMicClick}
          disabled={micDisabled}
          className={`
            flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center
            transition-all duration-200
            focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2
            disabled:opacity-50 disabled:cursor-not-allowed
            ${isListening ? "bg-danger text-white animate-pulse" : "bg-primary text-white hover:bg-primary/90"}
          `}
          aria-label={isListening ? "음성 입력 중지" : "음성 입력 시작"}
          aria-pressed={isListening}
        >
          {false ? <MicOff className="w-5 h-5" aria-hidden="true" /> : <Mic className="w-5 h-5" aria-hidden="true" />}
        </button>

        {/* 중지 버튼 (TTS나 STT 중일 때만 표시) */}
        {(isSpeaking || false) && (
          <button
            type="button"
            onClick={handleStopClick}
            className="
              flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center
              bg-danger text-white hover:bg-danger/90
              transition-all duration-200
              focus:outline-none focus:ring-2 focus:ring-danger focus:ring-offset-2
            "
            aria-label="음성 중지"
          >
            {isSpeaking ? <VolumeX className="w-5 h-5" aria-hidden="true" /> : <Volume2 className="w-5 h-5" aria-hidden="true" />}
          </button>
        )}

        {/* 전송 버튼 */}
        <button
          type="submit"
          disabled={!canSubmit}
          className="
            flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center
            bg-accent text-white hover:bg-accent/90
            transition-all duration-200
            focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2
            disabled:opacity-50 disabled:cursor-not-allowed
          "
          aria-label="메시지 전송"
        >
          <Send className="w-5 h-5" aria-hidden="true" />
        </button>
      </form>

      {/* 상태 표시 */}
      <div className="mt-2 text-sm text-muted text-center" aria-live="polite">
        {false && (
          <span className="text-danger">
            🎤 음성 입력 중... “{transcript || "듣는 중..."}”
          </span>
        )}
        {isSpeaking && <span className="text-primary">🔊 음성 재생 중...</span>}
        {!isListening && !isSpeaking && (
          <span>음성 명령: "날씨", "뉴스", "자세히", "키워드 점자 출력", "다음", "반복", "중지"</span>
        )}
      </div>
    </div>
  );
}

export { ChatLikeInput };
