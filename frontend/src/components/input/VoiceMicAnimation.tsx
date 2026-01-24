/**
 * 마이크 애니메이션 UI 컴포넌트
 * ChatGPT 스타일의 파동 효과와 상태 표시
 */

interface VoiceMicAnimationProps {
  isListening: boolean;
  isLongPressing: boolean;
  transcript: string;
  recognizedCommand: string | null;
}

export default function VoiceMicAnimation({
  isListening,
  isLongPressing,
  transcript,
  recognizedCommand
}: VoiceMicAnimationProps) {
  return (
    <div
      className={`fixed inset-0 z-[9999] flex items-center justify-center pointer-events-none transition-opacity duration-300 ${
        isListening || isLongPressing ? 'opacity-100' : 'opacity-0'
      }`}
      style={{ touchAction: 'none', userSelect: 'none' }}
      aria-hidden="true"
    >
      {/* 배경 오버레이 */}
      <div
        className={`absolute inset-0 bg-black/20 backdrop-blur-sm transition-opacity duration-300 ${
          isListening || isLongPressing ? 'opacity-100' : 'opacity-0'
        }`}
      />

      {/* 중앙 마이크 애니메이션 */}
      <div className="relative flex flex-col items-center justify-center">
        {/* 파동 효과 (ChatGPT 스타일) */}
        <div className="absolute inset-0 flex items-center justify-center">
          {[0, 1, 2, 3].map((i) => (
            <div
              key={i}
              className={`absolute rounded-full border-2 ${
                isListening || isLongPressing
                  ? 'border-primary/40 animate-ping'
                  : 'border-primary/20'
              }`}
              style={{
                width: `${96 + i * 32}px`,
                height: `${96 + i * 32}px`,
                animationDelay: `${i * 150}ms`,
                animationDuration: '2s',
              }}
            />
          ))}
        </div>

        {/* 마이크 아이콘 */}
        <div
          className={`relative w-24 h-24 rounded-full bg-gradient-to-br from-primary via-primary/90 to-accent flex items-center justify-center shadow-2xl transition-all duration-300 ${
            isListening || isLongPressing
              ? 'scale-110 ring-4 ring-primary/30'
              : 'scale-100'
          }`}
        >
          {/* 마이크 SVG */}
          <svg
            className={`w-12 h-12 text-white transition-transform duration-300 ${
              isListening ? 'scale-110' : 'scale-100'
            }`}
            fill="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
            <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
          </svg>

          {/* 내부 펄스 효과 */}
          {isListening && (
            <>
              <div className="absolute inset-0 rounded-full bg-white/30 animate-ping" style={{ animationDuration: '1s' }} />
              <div className="absolute inset-0 rounded-full bg-white/20 animate-pulse" style={{ animationDuration: '2s' }} />
            </>
          )}
        </div>

        {/* 상태 텍스트 */}
        <div className="mt-8 text-center">
          <p className="text-white text-lg font-semibold drop-shadow-lg">
            {transcript?.trim()
              ? transcript.trim()
              : (isLongPressing || isListening)
                ? '음성 인식 준비 중...'
                : ''}
          </p>
          {/* 인식 중일 때 하단에 상태 표시 */}
          {transcript?.trim() && (
            <p className="text-white/70 text-xs mt-1 drop-shadow-md">
              음성 인식 중...
            </p>
          )}
          {/* 명령어 인식 성공 시 표시 */}
          {recognizedCommand && (
            <p className="text-green-300 text-sm mt-2 font-bold drop-shadow-md animate-pulse">
              {recognizedCommand}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
