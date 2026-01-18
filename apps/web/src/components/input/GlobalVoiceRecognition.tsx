import { useEffect, useRef, useState, useCallback } from 'react';
import useSTT from '../../hooks/useSTT';
import useVoiceCommands from '../../hooks/useVoiceCommands';
import { useNavigate, useLocation } from 'react-router-dom';
import useTTS from '../../hooks/useTTS';
import VoiceEventBus, { onMicIntent } from '../../lib/voice/VoiceEventBus';
import micMode from '../../lib/voice/MicMode';
import { useVoiceStore } from '../../store/voice';

interface GlobalVoiceRecognitionProps {
  onTranscript?: (text: string) => void;
}

export default function GlobalVoiceRecognition({ onTranscript }: GlobalVoiceRecognitionProps) {
  const { start: startSTT, stop: stopSTT, isListening, transcript, alternatives } = useSTT();
  const { speak, stop: stopTTS } = useTTS();
  const navigate = useNavigate();
  const location = useLocation();
  
  const [showAnimation, setShowAnimation] = useState(false);
  const [isLongPressing, setIsLongPressing] = useState(false);
  const [recognizedCommand, setRecognizedCommand] = useState<string | null>(null); // 인식된 명령어 표시용
  const activePointerRef = useRef<{ pointerId: number; startTime: number } | null>(null);
  const lastTranscriptRef = useRef<string>('');
  const lastBroadcastRef = useRef<{ text: string; time: number }>({ text: '', time: 0 });
  const transcriptProcessedRef = useRef(false);
  const pausedMediaRef = useRef<HTMLMediaElement[]>([]);
  const sttLockRef = useRef<boolean>(false);
  const coolUntilRef = useRef<number>(0);
  const transcriptDebounceTimerRef = useRef<NodeJS.Timeout | null>(null); // 2초 debounce 타이머
  const commandExecutedRef = useRef<number>(0); // 명령어 실행 시간 추적

  // 모든 오디오/비디오 일시정지(겹침 방지)
  const stopAllMedia = useCallback(() => {
    pausedMediaRef.current = [];
    try {
      const media = Array.from(document.querySelectorAll('audio,video')) as HTMLMediaElement[];
      media.forEach(m => {
        if (!m.paused && !m.ended) {
          try { m.pause(); } catch {}
          pausedMediaRef.current.push(m);
        }
      });
    } catch {}
  }, []);

  // 짧은 비프음 재생
  const playBeep = useCallback(() => {
    try {
      const AC: any = (window as any).AudioContext || (window as any).webkitAudioContext;
      if (!AC) return;
      const ctx = new AC();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.value = 880;
      gain.gain.value = 0.2;
      osc.connect(gain).connect(ctx.destination);
      osc.start();
      setTimeout(() => {
        try { osc.stop(); ctx.close(); } catch {}
      }, 100);
    } catch {}
  }, []);


  // STT 안전 시작/중지 (MicMode intents에 맞춰 수행)
  const safeStart = useCallback(() => {
    // 이미 리스닝 중이면 무시
    if (isListening) {
      return;
    }
    
    if (sttLockRef.current) return;
    const now = Date.now();
    if (now < coolUntilRef.current) return;
    sttLockRef.current = true;
    try {
      stopTTS();
      stopAllMedia();
      playBeep();
      
      // 마이크 시작 시 이전 transcript 초기화 (이전 데이터가 보이지 않도록)
      useVoiceStore.getState().resetTranscript();
      
      try { window.dispatchEvent(new CustomEvent('voice:mic-mode', { detail: { active: true } })); } catch {}
      startSTT();
    } finally {
      // 락을 즉시 해제하지 않고 짧은 딜레이 후 해제 (중복 호출 방지)
      setTimeout(() => {
        sttLockRef.current = false;
      }, 50);
    }
  }, [startSTT, stopTTS, stopAllMedia, playBeep, isListening]);

  const safeStop = useCallback(() => {
    // 이미 중지되었으면 무시
    if (!isListening) {
      return;
    }
    
    if (sttLockRef.current) return;
    sttLockRef.current = true;
    try {
      stopSTT();
    } finally {
      sttLockRef.current = false;
      coolUntilRef.current = Date.now() + 300; // 600ms → 300ms로 단축
      try { VoiceEventBus.emitMicMode(false); } catch {}
    }
  }, [stopSTT, isListening]);

  // 학습 메뉴 항목 선택 처리 함수 (재사용)
  const handleLearnMenuSelection = useCallback((text: string) => {
    let normalized = text.toLowerCase().trim();
    
    // 오인식 패턴 보정
    const misrecognitionMap: Record<string, string> = {
      "자무": "자모", "자모.": "자모", "참호": "자모", "잠오": "자모", "사모": "자모",
      "단어.": "단어", "다워": "단어", "다오": "단어", "암호": "단어",
      "문장.": "문장",
      "학습모드": "학습", "학습모드.": "학습",
    };
    
    for (const [wrong, correct] of Object.entries(misrecognitionMap)) {
      if (normalized.includes(wrong)) {
        normalized = normalized.replace(wrong, correct);
      }
    }
    
    // 학습 메뉴 항목 선택 처리 (어디서든 작동)
    if (/(자모|자음|모음|자무|참호|잠오|사모)/.test(normalized) || 
        normalized.startsWith('자') || 
        normalized.includes('자모') || 
        normalized.includes('자음') || 
        normalized.includes('모음') ||
        (normalized.length <= 3 && normalized[0] === '자')) {
      stopTTS();
      navigate('/learn/char');
      speak('자모 학습으로 이동합니다.');
      stopSTT();
      return true;
    }
    if (/(단어|워드|다워|다오|암호|word)/.test(normalized) || 
        normalized.startsWith('단') || 
        normalized.startsWith('word') ||
        normalized.includes('단어') ||
        normalized.includes('다워') ||
        normalized.includes('암호') ||
        normalized.includes('word') ||
        (normalized.length <= 3 && normalized[0] === '단') ||
        (normalized.length <= 3 && normalized[0] === '다') ||
        normalized === 'word' || normalized === '워드') {
      stopTTS();
      navigate('/learn/word');
      speak('단어 학습으로 이동합니다.');
      stopSTT();
      return true;
    }
    if (/(문장|센턴스)/.test(normalized) || 
        normalized.startsWith('문') || 
        normalized.includes('문장') ||
        (normalized.length <= 3 && normalized[0] === '문')) {
      stopTTS();
      navigate('/learn/sentence');
      speak('문장 학습으로 이동합니다.');
      stopSTT();
      return true;
    }
    if (/(자유\s*변환|자유변환|변환)/.test(normalized) || 
        normalized.includes('변환') || 
        normalized.includes('자유')) {
      stopTTS();
      navigate('/learn/free');
      speak('자유 변환으로 이동합니다.');
      stopSTT();
      return true;
    }
    
    return false;
  }, [navigate, speak, stopTTS, stopSTT]);

  // 음성 명령 처리
  const { onSpeech } = useVoiceCommands({
    home: () => {
      if (location.pathname !== '/') {
        stopSTT();
        navigate('/');
        speak('홈으로 이동합니다.');
      }
    },
    back: () => {
      stopSTT();
      navigate(-1);
      speak('뒤로 갑니다.');
    },
    learn: () => {
      stopSTT();
      navigate('/learn');
      speak('점자 학습 모드로 이동합니다.');
    },
    explore: () => {
      navigate('/explore');
      speak('정보 탐색 모드로 이동합니다.');
      stopSTT();
    },
    review: () => {
      navigate('/review');
      speak('복습 모드로 이동합니다.');
      stopSTT();
    },
    // 전역 재생 제어 명령은 이벤트로 브로드캐스트하여 화면 단에서 처리
    // 학습 모드(/learn/char, /learn/word, /learn/sentence)에서는 이벤트를 보내되
    // LearnStep의 onSpeech에도 도달하도록 false를 반환하지 않음 (이벤트만으로 처리)
    next: () => {
      window.dispatchEvent(new CustomEvent('voice:command', { detail: { type: 'next' } }));
      // 학습 모드에서는 이벤트만으로 처리되므로 true 반환 (LearnStep의 이벤트 리스너가 처리)
      // 다른 페이지에서는 false를 반환하여 페이지별 onSpeech에도 도달하도록 할 수 있지만,
      // 현재는 이벤트만으로 처리하는 것이 더 안정적
    },
    prev: () => {
      window.dispatchEvent(new CustomEvent('voice:command', { detail: { type: 'prev' } }));
    },
    repeat: () => {
      window.dispatchEvent(new CustomEvent('voice:command', { detail: { type: 'repeat' } }));
    },
    freeConvert: () => {
      navigate('/free-convert');
      speak('자유 변환 모드로 이동합니다.');
      stopSTT();
    },
    quiz: () => {
      navigate('/quiz');
      speak('퀴즈 모드로 이동합니다.');
      stopSTT();
    },
    help: () => {
      const helpText = '화면을 길게 눌러 음성 명령을 사용할 수 있습니다. 학습, 탐색, 복습, 변환, 퀴즈 등의 명령을 말하세요.';
      speak(helpText);
    },
    mute: () => {
      stopTTS();
    },
    unmute: () => {
      speak('음성이 활성화되었습니다.');
    },
    stop: () => {
      stopSTT();
      speak('음성 인식을 중지합니다.');
    },
    pause: () => {
      stopSTT();
    },
    // 학습 메뉴 내 항목 선택 (speak 핸들러에서 처리) + 경로 기반 바이어스
    speak: (text: string) => {
      // 학습 메뉴 항목 선택 시도 (현재 경로 바이어스)
      if (location.pathname === '/learn') {
        if (handleLearnMenuSelection(text)) return;
      }
      
      // 기본 TTS 처리
      stopTTS();
      speak(text);
    },
  });

  // 최종 인식 결과만 처리 (TRANSCRIPT 이벤트를 통해)
  useEffect(() => {
    // 퀴즈 모드에서는 GlobalVoiceRecognition이 transcript를 처리하지 않음 (퀴즈 모드가 자체적으로 처리)
    if (location.pathname.startsWith('/quiz')) {
      return;
    }
    
    const handleFinalTranscript = (e: Event) => {
      const detail = (e as CustomEvent)?.detail as { text?: string };
      const finalText = detail?.text;
      if (!finalText) return;
      
      console.log('[GlobalVoice] 최종 인식 결과 수신:', finalText);
      
      // 중복 처리 방지 (시간 단축: 500ms → 300ms)
      const now = Date.now();
      if (finalText === lastBroadcastRef.current.text && now - lastBroadcastRef.current.time < 300) {
        console.log('[GlobalVoice] 최종 결과 중복 무시:', finalText);
        return;
      }
      
      // Store에서 최신 alternatives 가져오기
      const currentAlternatives = useVoiceStore.getState().alternatives;
      
      // 먼저 명령어 매칭 시도 (즉시 처리)
      let commandMatched = false;
      
      // 여러 대안이 있으면 모두 시도 (confidence 순서대로)
      if (currentAlternatives && currentAlternatives.length > 0) {
        for (const alt of currentAlternatives) {
          const matched = onSpeech(alt.transcript);
          if (matched) {
            console.log(`[GlobalVoice] 대안 "${alt.transcript}"에서 명령 매칭 성공 - 즉시 처리`);
            commandMatched = true;
            lastBroadcastRef.current = { text: finalText, time: now };
            commandExecutedRef.current = now; // 명령어 실행 시간 기록
            
            // 인식된 명령어 표시
            setRecognizedCommand(`✓ 인식: ${alt.transcript}`);
            setTimeout(() => setRecognizedCommand(null), 2000); // 2초 후 사라짐
            
            // 명령 매칭 시 즉시 마이크 끄기
            if (isListening) {
              console.log('[GlobalVoice] 명령 매칭 - 마이크 자동 종료');
              micMode.requestStop();
            }
            // 포인터 상태 리셋
            activePointerRef.current = null;
            setIsLongPressing(false);
            // 기존 타이머 취소 (명령어는 즉시 처리)
            if (transcriptDebounceTimerRef.current) {
              clearTimeout(transcriptDebounceTimerRef.current);
              transcriptDebounceTimerRef.current = null;
            }
            return; // 명령어는 즉시 처리하고 종료
          }
        }
      }
      
      // 기본 텍스트로도 명령어 시도
      const matched = onSpeech(finalText);
      if (matched) {
        console.log(`[GlobalVoice] "${finalText}"에서 명령 매칭 성공 - 즉시 처리`);
        commandMatched = true;
        lastBroadcastRef.current = { text: finalText, time: now };
        commandExecutedRef.current = now; // 명령어 실행 시간 기록
        
        // 인식된 명령어 표시
        setRecognizedCommand(`✓ 인식: ${finalText}`);
        setTimeout(() => setRecognizedCommand(null), 2000); // 2초 후 사라짐
        
        // 명령 매칭 시 즉시 마이크 끄기
        if (isListening) {
          console.log('[GlobalVoice] 명령 매칭 - 마이크 자동 종료');
          micMode.requestStop();
        }
        // 포인터 상태 리셋
        activePointerRef.current = null;
        setIsLongPressing(false);
        // 기존 타이머 취소
        if (transcriptDebounceTimerRef.current) {
          clearTimeout(transcriptDebounceTimerRef.current);
          transcriptDebounceTimerRef.current = null;
        }
        return; // 명령어는 즉시 처리하고 종료
      }
      
      // 학습 메뉴 항목 선택 처리 시도
      if (handleLearnMenuSelection(finalText)) {
        console.log(`[GlobalVoice] "${finalText}"에서 메뉴 선택 성공 - 즉시 처리`);
        lastBroadcastRef.current = { text: finalText, time: now };
        commandExecutedRef.current = now; // 명령어 실행 시간 기록
        
        // 인식된 명령어 표시
        setRecognizedCommand(`✓ 인식: ${finalText}`);
        setTimeout(() => setRecognizedCommand(null), 2000); // 2초 후 사라짐
        
        // 메뉴 선택 시 즉시 마이크 끄기
        if (isListening) {
          console.log('[GlobalVoice] 메뉴 선택 - 마이크 자동 종료');
          micMode.requestStop();
        }
        // 포인터 상태 리셋
        activePointerRef.current = null;
        setIsLongPressing(false);
        // 기존 타이머 취소
        if (transcriptDebounceTimerRef.current) {
          clearTimeout(transcriptDebounceTimerRef.current);
          transcriptDebounceTimerRef.current = null;
        }
        return; // 메뉴 선택도 즉시 처리
      }
      
      // 명령어가 아닌 경우에만 debounce 적용 (시간 단축: 500ms → 300ms)
      // 기존 타이머 취소
      if (transcriptDebounceTimerRef.current) {
        clearTimeout(transcriptDebounceTimerRef.current);
        transcriptDebounceTimerRef.current = null;
      }
      
      // 0.3초 후 처리 (일반 텍스트는 짧은 debounce)
      transcriptDebounceTimerRef.current = setTimeout(() => {
        console.log('[GlobalVoice] 일반 텍스트 처리:', finalText);
        lastBroadcastRef.current = { text: finalText, time: Date.now() };
        
        // 기본 TTS 처리
        stopTTS();
        speak(finalText);
        onTranscript?.(finalText);
        
        transcriptDebounceTimerRef.current = null;
      }, 300); // 일반 텍스트는 0.3초 debounce
    };
    
    // TRANSCRIPT 이벤트는 최종 결과에만 발생 (emitTranscript 호출 시)
    window.addEventListener('voice:transcript', handleFinalTranscript as EventListener);
    return () => {
      window.removeEventListener('voice:transcript', handleFinalTranscript as EventListener);
      // cleanup: 타이머 정리
      if (transcriptDebounceTimerRef.current) {
        clearTimeout(transcriptDebounceTimerRef.current);
        transcriptDebounceTimerRef.current = null;
      }
    };
  }, [onSpeech, onTranscript, handleLearnMenuSelection, stopTTS, speak, isListening, location.pathname]);

  // 포인터 시작 - 화면을 누르고 있는 동안 마이크 켜기
  const handlePointerDown = useCallback((e: PointerEvent) => {
    // 버튼/입력 필드 필터링
    const target = e.target as HTMLElement;
    if (
      target.tagName === 'BUTTON' ||
      target.tagName === 'INPUT' ||
      target.tagName === 'TEXTAREA' ||
      target.closest('button') ||
      target.closest('input') ||
      target.closest('textarea') ||
      target.closest('a')
    ) {
      return;
    }

    // 이미 활성 포인터가 있으면 무시
    if (activePointerRef.current) {
      return;
    }

    // 이미 마이크가 켜져 있으면 무시
    if (isListening) {
      return;
    }

    // 텍스트 선택 및 시스템 제스처 차단 (크롬 검색 등)
    e.preventDefault();
    e.stopPropagation();
    e.stopImmediatePropagation();

    // 활성 포인터 등록
    activePointerRef.current = {
      pointerId: e.pointerId,
      startTime: Date.now()
    };

    // 마이크 시작
    setIsLongPressing(true);
    setShowAnimation(true);
    stopTTS(); // TTS 중지 (홈 화면 등에서 안내 멘트 중단)
    micMode.requestStart();
  }, [isListening, stopTTS]);

  // 포인터 종료 - 손을 떼면 마이크 끄기
  const handlePointerUp = useCallback((e: PointerEvent) => {
    // 활성 포인터가 없으면 무시
    if (!activePointerRef.current) {
      return;
    }

    // 같은 포인터의 이벤트만 처리
    if (activePointerRef.current.pointerId !== e.pointerId) {
      return;
    }

    // 마이크 중지
    if (isListening) {
      micMode.requestStop();
    }

    // 상태 리셋
    activePointerRef.current = null;
    setIsLongPressing(false);
    setTimeout(() => {
      if (!isListening) {
        setShowAnimation(false);
      }
    }, 200);
  }, [isListening]);

  // MicMode intents → 실제 STT start/stop 수행
  useEffect(() => {
    const unSubStart = onMicIntent((e) => {
      if (e?.action === 'start') safeStart();
      if (e?.action === 'stop') safeStop();
    });
    return () => {
      unSubStart();
    };
  }, [safeStart, safeStop]);

  // 마우스를 누르고 있는 동안 음성 인식이 자동 중단되면 재시작
  useEffect(() => {
    // 퀴즈 모드에서는 자동 재시작 비활성화 (퀴즈 모드는 자체적으로 STT 관리)
    if (location.pathname.startsWith('/quiz')) {
      return;
    }
    
    // 마우스를 누르고 있는데 음성 인식이 꺼진 경우 자동 재시작
    if (isLongPressing && !isListening && activePointerRef.current) {
      // 최근에 명령어가 실행되었는지 확인 (시간 단축: 2000ms → 1000ms)
      const timeSinceLastCommand = Date.now() - commandExecutedRef.current;
      // 명령어 실행 후 1초 이내면 재시작하지 않음 (명령어 실행 후 자동 종료된 경우)
      if (timeSinceLastCommand < 1000) {
        console.log('[GlobalVoice] 최근 명령어 실행으로 인한 자동 종료 - 재시작하지 않음');
        return;
      }
      
      // 이미 진행 중인지 확인 (VoiceService의 내부 상태 확인 불가하므로 짧은 딜레이 후 재시작)
      const timer = setTimeout(() => {
        // 재시작 전에 다시 확인 (다른 곳에서 이미 시작했을 수 있음)
        const currentListening = useVoiceStore.getState().isListening;
        // 다시 한 번 명령어 실행 시간 확인
        const timeSinceLastCommand2 = Date.now() - commandExecutedRef.current;
        if (isLongPressing && !currentListening && activePointerRef.current && timeSinceLastCommand2 >= 1000) {
          console.log('[GlobalVoice] 음성 인식이 자동 중단됨 - 재시작');
          micMode.requestStart();
        }
      }, 400); // 딜레이 단축: 800ms → 400ms
      return () => clearTimeout(timer);
    }
  }, [isListening, isLongPressing, location.pathname]);

  // 포인터 이동 - 아무것도 하지 않음
  const handlePointerMove = useCallback(() => {
    // 마이크는 유지, 아무것도 하지 않음
  }, []);

  // 포인터 취소 - 활성 포인터가 있으면 리셋
  const handlePointerCancel = useCallback((e: PointerEvent) => {
    if (activePointerRef.current && activePointerRef.current.pointerId === e.pointerId) {
      if (isListening) {
        micMode.requestStop();
      }
      activePointerRef.current = null;
      setIsLongPressing(false);
      setShowAnimation(false);
    }
  }, [isListening]);

  // 전역 이벤트 리스너 등록 - capture 단계에서 먼저 처리
  useEffect(() => {
    window.addEventListener('pointerdown', handlePointerDown, { capture: true, passive: false });
    window.addEventListener('pointerup', handlePointerUp, { capture: true, passive: false });
    window.addEventListener('pointermove', handlePointerMove, { capture: true, passive: false });
    window.addEventListener('pointercancel', handlePointerCancel, { capture: true, passive: false });

    // 텍스트 선택 방지를 위한 추가 이벤트
    const handleSelectStart = (e: Event) => {
      const target = e.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.closest('input') ||
        target.closest('textarea')
      ) {
        return; // 입력 필드는 허용
      }
      e.preventDefault();
    };

    const handleContextMenu = (e: Event) => {
      const target = e.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.closest('input') ||
        target.closest('textarea')
      ) {
        return; // 입력 필드는 허용
      }
      e.preventDefault();
    };

    document.addEventListener('selectstart', handleSelectStart);
    document.addEventListener('contextmenu', handleContextMenu);

    return () => {
      window.removeEventListener('pointerdown', handlePointerDown, { capture: true } as any);
      window.removeEventListener('pointerup', handlePointerUp, { capture: true } as any);
      window.removeEventListener('pointermove', handlePointerMove, { capture: true } as any);
      window.removeEventListener('pointercancel', handlePointerCancel, { capture: true } as any);
      document.removeEventListener('selectstart', handleSelectStart);
      document.removeEventListener('contextmenu', handleContextMenu);
    };
  }, [handlePointerDown, handlePointerUp, handlePointerMove, handlePointerCancel]);

  // 음성 인식 종료 시 애니메이션 숨기기
  useEffect(() => {
    // 화면을 누르고 있는 동안(isLongPressing)에는 UI를 숨기지 않음
    if (!isListening && showAnimation && !isLongPressing) {
      const timer = setTimeout(() => {
        // 다시 확인 (상태가 변경되었을 수 있음)
        if (!isListening && !isLongPressing) {
          setShowAnimation(false);
        }
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [isListening, showAnimation, isLongPressing]);

  if (!showAnimation && !isListening) {
    return null;
  }

  return (
    <div
      className={`fixed inset-0 z-[9999] flex items-center justify-center pointer-events-none transition-opacity duration-300 ${
        showAnimation || isListening ? 'opacity-100' : 'opacity-0'
      }`}
      style={{ touchAction: 'none', userSelect: 'none' }}
      aria-hidden="true"
    >
      {/* 배경 오버레이 */}
      <div
        className={`absolute inset-0 bg-black/20 backdrop-blur-sm transition-opacity duration-300 ${
          showAnimation || isListening ? 'opacity-100' : 'opacity-0'
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

