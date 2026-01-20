import { useCallback, useEffect, useRef, useState } from "react";
import type { TTSOptions, TTSHookReturn } from "@/types";

function clamp(v: number, min: number, max: number) {
  return Math.max(min, Math.min(max, v));
}

/**
 * TTS 읽기 전에 특수문자 제거
 * 마크다운, HTML 태그, 기타 특수문자 제거
 */
function cleanTextForTTS(text: string): string {
  if (!text) return '';
  
  let cleaned = text;
  
  // 마크다운 볼드/이탤릭 제거 (**text**, *text*, __text__, _text_)
  cleaned = cleaned.replace(/\*\*([^*]+)\*\*/g, '$1'); // **text** -> text
  cleaned = cleaned.replace(/\*([^*]+)\*/g, '$1'); // *text* -> text
  cleaned = cleaned.replace(/__([^_]+)__/g, '$1'); // __text__ -> text
  cleaned = cleaned.replace(/_([^_]+)_/g, '$1'); // _text_ -> text
  
  // 남은 마크다운 특수문자 제거
  cleaned = cleaned.replace(/\*\*/g, ''); // 남은 **
  cleaned = cleaned.replace(/\*/g, ''); // 남은 *
  cleaned = cleaned.replace(/__/g, ''); // 남은 __
  cleaned = cleaned.replace(/_/g, ''); // 남은 _
  
  // HTML 태그 제거
  cleaned = cleaned.replace(/<[^>]+>/g, '');
  
  // 마크다운 링크 제거 [text](url) -> text
  cleaned = cleaned.replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1');
  
  // 마크다운 이미지 제거 ![alt](url) -> alt
  cleaned = cleaned.replace(/!\[([^\]]*)\]\([^\)]+\)/g, '$1');
  
  // 기타 마크다운 특수문자
  cleaned = cleaned.replace(/~~([^~]+)~~/g, '$1'); // ~~text~~ -> text
  cleaned = cleaned.replace(/`([^`]+)`/g, '$1'); // `code` -> code
  cleaned = cleaned.replace(/```[\s\S]*?```/g, ''); // 코드 블록 제거
  
  // 연속된 공백 정리
  cleaned = cleaned.replace(/\s+/g, ' ');
  
  return cleaned.trim();
}

// ko-KR 보이스를 우선 선택하는 헬퍼 (더 자연스러운 보이스 우선)
function pickVoice(voices: SpeechSynthesisVoice[], opts: TTSOptions): SpeechSynthesisVoice | null {
  const { lang = "ko-KR", voiceName } = opts;
  if (!voices?.length) return null;

  // voiceName이 명시되면 우선
  if (voiceName) {
    const named = voices.find(v => v.name === voiceName);
    if (named) return named;
  }

  // 한국어 보이스 필터링
  const koreanVoices = voices.filter(v => 
    v.lang === lang || 
    v.lang?.toLowerCase().startsWith('ko')
  );

  if (!koreanVoices.length) {
    // 한국어 보이스가 없으면 전체에서 첫 번째
    return voices[0] ?? null;
  }

  // Neural TTS 보이스 우선 선택 (더 자연스러운 음성)
  const neuralVoices = koreanVoices.filter(v => 
    v.name.toLowerCase().includes('neural') ||
    v.name.toLowerCase().includes('google') ||
    v.name.toLowerCase().includes('heami') ||
    v.name.toLowerCase().includes('sunhi')
  );

  if (neuralVoices.length > 0) {
    // Neural 보이스 중에서도 우선순위
    // 1. Microsoft Heami (Windows Neural TTS)
    const heami = neuralVoices.find(v => v.name.toLowerCase().includes('heami'));
    if (heami) return heami;
    
    // 2. Microsoft Sunhi (Windows Neural TTS)
    const sunhi = neuralVoices.find(v => v.name.toLowerCase().includes('sunhi'));
    if (sunhi) return sunhi;
    
    // 3. Google 한국어
    const google = neuralVoices.find(v => v.name.toLowerCase().includes('google'));
    if (google) return google;
    
    // 4. 첫 번째 Neural 보이스
    return neuralVoices[0];
  }

  // Neural이 없으면 일반 보이스 중에서
  // lang 정확히 일치
  const byLangExact = koreanVoices.find(v => v.lang === lang);
  if (byLangExact) return byLangExact;

  // 첫 번째 한국어 보이스
  return koreanVoices[0];
}

function useTTS(): TTSHookReturn {
  const isSupported = typeof window !== "undefined" && "speechSynthesis" in window;

  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const currentUtterance = useRef<SpeechSynthesisUtterance | null>(null);
  const utteranceQueue = useRef<string[]>([]);
  const isProcessing = useRef(false);
  const unmountedRef = useRef(false);
  const micModeRef = useRef<boolean>(false);

  // 최신 보이스 목록 캐시
  const voicesRef = useRef<SpeechSynthesisVoice[] | null>(null);

  // 보이스 로드(브라우저마다 getVoices 타이밍 이슈 대응)
  const refreshVoices = useCallback(() => {
    try {
      const list = window.speechSynthesis.getVoices();
      if (list && list.length) {
        voicesRef.current = list;
      }
    } catch {/* noop */}
  }, []);

  useEffect(() => {
    if (!isSupported) return;
    refreshVoices();
    // 일부 브라우저는 이 이벤트 이후에 보이스가 로드됨
    const handler = () => refreshVoices();
    window.speechSynthesis.addEventListener?.("voiceschanged", handler);
    // iOS/Safari 억지 트리거
    if (!voicesRef.current || voicesRef.current.length === 0) {
      setTimeout(refreshVoices, 150);
      setTimeout(refreshVoices, 500);
    }
    return () => {
      window.speechSynthesis.removeEventListener?.("voiceschanged", handler);
    };
  }, [isSupported, refreshVoices]);

  // 공용 정리
  const hardReset = useCallback(() => {
    try { window.speechSynthesis.cancel(); } catch {}
    utteranceQueue.current = [];
    currentUtterance.current = null;
    isProcessing.current = false;
    setIsSpeaking(false);
    setIsPaused(false);
  }, []);

  // Mic Mode 수신: 활성화 시 즉시 모든 음성 중지, 비활성화 시만 TTS 허용
  useEffect(() => {
    const onMicMode = (e: Event) => {
      const detail = (e as CustomEvent)?.detail as { active?: boolean } | undefined;
      const active = !!detail?.active;
      micModeRef.current = active;
      if (active) {
        hardReset();
      }
    };
    window.addEventListener('voice:mic-mode', onMicMode as EventListener);
    return () => window.removeEventListener('voice:mic-mode', onMicMode as EventListener);
  }, [hardReset]);

  const processQueue = useCallback((opts: TTSOptions) => {
    if (!isSupported || unmountedRef.current) return;
    if (isProcessing.current) return;
    if (!utteranceQueue.current.length) return;

    isProcessing.current = true;

    const nextText = utteranceQueue.current.shift()!;
    const utt = new SpeechSynthesisUtterance(nextText);

    // 옵션 적용(클램프) - 더 빠른 기본값
    const rate = clamp(opts.rate ?? 1.2, 0.1, 10);  // 기본값 1.2 (더 빠르게)
    const pitch = clamp(opts.pitch ?? 1.0, 0, 2);
    const volume = clamp(opts.volume ?? 1.0, 0, 1);
    utt.rate = rate;
    utt.pitch = pitch;
    utt.volume = volume;
    utt.lang = opts.lang || "ko-KR";

    // 보이스 선택
    const voices = voicesRef.current || window.speechSynthesis.getVoices();
    const voice = pickVoice(voices, opts);
    if (voice) utt.voice = voice;

    // 이벤트
    utt.onstart = () => {
      if (unmountedRef.current) return;
      currentUtterance.current = utt;
      setIsSpeaking(true);
      setIsPaused(false);
    };
    utt.onend = () => {
      if (unmountedRef.current) return;
      currentUtterance.current = null;
      setIsSpeaking(false);
      setIsPaused(false);
      isProcessing.current = false;
      
      // 다음 항목 처리
      if (utteranceQueue.current.length) {
        // 매우 짧은 텀을 두면 브라우저별 안정성이 올라감
        setTimeout(() => processQueue(opts), 60);
      } else {
        // 큐가 비었으면 완료 콜백 호출
        if (opts.onEnd) {
          setTimeout(() => opts.onEnd!(), 100); // 약간의 딜레이로 상태 업데이트 대기
        }
      }
    };
    utt.onerror = () => {
      if (unmountedRef.current) return;
      currentUtterance.current = null;
      setIsSpeaking(false);
      setIsPaused(false);
      isProcessing.current = false;
      // 오류가 나도 다음 큐는 시도
      if (utteranceQueue.current.length) {
        setTimeout(() => processQueue(opts), 60);
      }
    };
    utt.onpause = () => {
      if (unmountedRef.current) return;
      setIsPaused(true);
    };
    utt.onresume = () => {
      if (unmountedRef.current) return;
      setIsPaused(false);
    };

    try {
      window.speechSynthesis.speak(utt);
    } catch {
      // speak 호출 자체가 실패하면 다음 큐로 넘어감
      isProcessing.current = false;
      currentUtterance.current = null;
      if (utteranceQueue.current.length) {
        setTimeout(() => processQueue(opts), 60);
      }
    }
  }, [isSupported]);

  const speak = useCallback(async (text: string | string[], options: TTSOptions = {}) => {
    if (!isSupported) {
      console.warn("Speech synthesis is not supported in this browser");
      setError("Speech synthesis is not supported");
      return;
    }
    // Mic Mode에서는 기본적으로 안내 음성 차단 (옵션으로만 허용)
    const allowDuringMic = 'allowDuringMic' in options && options.allowDuringMic === true;
    if (micModeRef.current && !allowDuringMic) {
      console.log('[TTS] Mic Mode 활성화로 인해 TTS 차단');
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      const texts = (Array.isArray(text) ? text : [text])
        .map(t => cleanTextForTTS(String(t ?? "")))
        .filter(Boolean);
      if (!texts.length) {
        console.warn('[TTS] 빈 텍스트로 인해 재생 건너뜀');
        setIsLoading(false);
        return;
      }

      console.log('[TTS] speak 호출:', { 
        textLength: texts.join(' ').length, 
        textPreview: texts[0]?.substring(0, 50) + '...',
        queueLength: utteranceQueue.current.length 
      });

      // 새 요청이 들어오면 기존 재생은 정리 후 새 큐로 교체
      hardReset();
      utteranceQueue.current = texts;

      // 보이스 미로드일 수 있어 한 번 더 시도
      if (!voicesRef.current || voicesRef.current.length === 0) {
        try { voicesRef.current = window.speechSynthesis.getVoices(); } catch {}
      }

      processQueue(options);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
      // 오류 발생 시에도 사용자에게 피드백 제공
      console.error("TTS Error:", err);
    } finally {
      setIsLoading(false);
    }
  }, [isSupported, processQueue, hardReset]);

  const stop = useCallback(() => {
    if (!isSupported) return;
    hardReset();
  }, [isSupported, hardReset]);

  const pause = useCallback(() => {
    if (!isSupported) return;
    if (!isSpeaking || isPaused) return;
    try {
      window.speechSynthesis.pause();
      setIsPaused(true);
    } catch {/* noop */}
  }, [isSupported, isSpeaking, isPaused]);

  const resume = useCallback(() => {
    if (!isSupported) return;
    if (!isSpeaking || !isPaused) return;
    try {
      window.speechSynthesis.resume();
      setIsPaused(false);
    } catch {/* noop */}
  }, [isSupported, isSpeaking, isPaused]);

  // 페이지 전환 감지 및 음성 중지
  useEffect(() => {
    const handleBeforeUnload = () => {
      hardReset();
    };

    const handleVisibilityChange = () => {
      if (document.hidden) {
        hardReset();
      }
    };

    // 페이지 전환 시 음성 중지
    window.addEventListener('beforeunload', handleBeforeUnload);
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [hardReset]);

  // 언마운트 시 정리
  useEffect(() => {
    unmountedRef.current = false;
    return () => {
      unmountedRef.current = true;
      try { window.speechSynthesis.cancel(); } catch {}
      currentUtterance.current = null;
      utteranceQueue.current = [];
      isProcessing.current = false;
    };
  }, []);

  return {
    speak,
    stop,
    pause,
    resume,
    isSpeaking,
    isPaused,
    isSupported,
    isLoading,
    error,
  };
}

// named export와 default export 모두 제공
export { useTTS };
export default useTTS;
