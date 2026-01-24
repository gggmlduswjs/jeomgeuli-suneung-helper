import { useEffect, useRef, useState, useCallback } from 'react';
import useSTT from '../../hooks/useSTT';
import useVoiceCommands from '../../hooks/useVoiceCommands';
import { useNavigate, useLocation } from 'react-router-dom';
import useTTS from '../../hooks/useTTS';
import { onMicIntent } from '../../lib/voice/VoiceEventBus';
import { useVoiceStore } from '../../store/voice';
import VoiceService from '../../services/voice';
import VoiceMicAnimation from './VoiceMicAnimation';
import { useLearnMenuHandler } from '../../hooks/useLearnMenuHandler';

interface GlobalVoiceRecognitionProps {
  onTranscript?: (text: string) => void;
}

export default function GlobalVoiceRecognition({ onTranscript }: GlobalVoiceRecognitionProps) {
  const { start: startSTT, stop: stopSTT, isListening, transcript } = useSTT();
  const { speak, stop: stopTTS } = useTTS();
  const navigate = useNavigate();
  const location = useLocation();
  
  const [showAnimation, setShowAnimation] = useState(false);
  const [isLongPressing, setIsLongPressing] = useState(false);
  const [recognizedCommand, setRecognizedCommand] = useState<string | null>(null); // 인식된 명령어 표시용
  const activePointerRef = useRef<{ pointerId: number; startTime: number } | null>(null);
  const lastBroadcastRef = useRef<{ text: string; time: number }>({ text: '', time: 0 });
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
      type AudioContextConstructor = typeof AudioContext;
      const AC = ((window as any).AudioContext || (window as any).webkitAudioContext) as AudioContextConstructor | undefined;
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
      // TODO: VoiceEventBus에 emitMicMode 메서드 추가 필요
      // try { VoiceEventBus.emitMicMode(false); } catch {}
    }
  }, [stopSTT, isListening]);

  // 학습 메뉴 항목 선택 처리 (훅으로 추출)
  const { handleLearnMenuSelection } = useLearnMenuHandler(stopSTT);

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
    
    // 관리자 페이지에서는 음성 인식 처리하지 않음
    if (location.pathname.startsWith('/admin')) {
      return;
    }
    
    const handleFinalTranscript = (e: Event) => {
      const detail = (e as CustomEvent)?.detail as { text?: string };
      const finalText = detail?.text;
      if (!finalText) return;
      
      if (import.meta.env.DEV) console.log('[GlobalVoice] 최종 인식 결과 수신:', finalText);
      
      // 중복 처리 방지 (시간 단축: 500ms → 300ms)
      const now = Date.now();
      if (finalText === lastBroadcastRef.current.text && now - lastBroadcastRef.current.time < 300) {
        if (import.meta.env.DEV) console.log('[GlobalVoice] 최종 결과 중복 무시:', finalText);
        return;
      }
      
      // Store에서 최신 alternatives 가져오기
      const currentAlternatives = useVoiceStore.getState().alternatives;
      
      // 먼저 명령어 매칭 시도 (즉시 처리)

      // 여러 대안이 있으면 모두 시도 (confidence 순서대로)
      if (currentAlternatives && currentAlternatives.length > 0) {
        for (const alt of currentAlternatives) {
          const matched = onSpeech(alt.transcript);
          if (matched) {
            console.log(`[GlobalVoice] 대안 "${alt.transcript}"에서 명령 매칭 성공 - 즉시 처리`);
            lastBroadcastRef.current = { text: finalText, time: now };
            commandExecutedRef.current = now; // 명령어 실행 시간 기록
            
            // 인식된 명령어 표시
            setRecognizedCommand(`✓ 인식: ${alt.transcript}`);
            setTimeout(() => setRecognizedCommand(null), 2000); // 2초 후 사라짐
            
            // 명령 매칭 시 즉시 마이크 끄기
            if (isListening) {
              if (import.meta.env.DEV) console.log('[GlobalVoice] 명령 매칭 - 마이크 자동 종료');
              VoiceService.stopSTT();
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
        lastBroadcastRef.current = { text: finalText, time: now };
        commandExecutedRef.current = now; // 명령어 실행 시간 기록
        
        // 인식된 명령어 표시
        setRecognizedCommand(`✓ 인식: ${finalText}`);
        setTimeout(() => setRecognizedCommand(null), 2000); // 2초 후 사라짐
        
        // 명령 매칭 시 즉시 마이크 끄기
        if (isListening) {
          if (import.meta.env.DEV) console.log('[GlobalVoice] 명령 매칭 - 마이크 자동 종료');
          VoiceService.stopSTT();
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
          if (import.meta.env.DEV) console.log('[GlobalVoice] 메뉴 선택 - 마이크 자동 종료');
          VoiceService.stopSTT();
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
        if (import.meta.env.DEV) console.log('[GlobalVoice] 일반 텍스트 처리:', finalText);
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
    // 관리자 페이지에서는 마이크 기능 비활성화
    if (location.pathname.startsWith('/admin')) {
      return;
    }

    // 버튼/입력 필드/링크 필터링 (더 엄격하게)
    const target = e.target as HTMLElement;
    if (
      target.tagName === 'BUTTON' ||
      target.tagName === 'INPUT' ||
      target.tagName === 'TEXTAREA' ||
      target.tagName === 'A' ||
      target.tagName === 'SELECT' ||
      target.closest('button') ||
      target.closest('input') ||
      target.closest('textarea') ||
      target.closest('a') ||
      target.closest('[role="button"]') ||
      target.closest('[onclick]') ||
      // 스크롤 가능한 영역은 제외하지 않음 (길게 누르면 마이크 켜짐)
      target.getAttribute('data-no-long-press') === 'true' // 특정 요소는 명시적으로 제외
    ) {
      return; // 버튼/입력 필드/링크에서는 마이크 시작하지 않음
    }

    // 이미 활성 포인터가 있으면 무시
    if (activePointerRef.current) {
      return;
    }

    // 이미 마이크가 켜져 있으면 무시
    if (isListening) {
      return;
    }

    // 활성 포인터 등록 (길게 누르기 감지용)
    activePointerRef.current = {
      pointerId: e.pointerId,
      startTime: Date.now()
    };

    // 짧게 누른 경우 클릭으로 처리 (300ms 후에 마이크 시작)
    const longPressTimer = setTimeout(() => {
      // 300ms 이상 누르고 있으면 마이크 시작
      if (activePointerRef.current && activePointerRef.current.pointerId === e.pointerId) {
        // 텍스트 선택 및 시스템 제스처 차단 (길게 누르는 경우에만)
        e.preventDefault();
        
        // 마이크 시작
        setIsLongPressing(true);
        setShowAnimation(true);
        stopTTS(); // TTS 중지 (홈 화면 등에서 안내 멘트 중단)
        VoiceService.startSTT();
      }
    }, 300); // 300ms 후에 길게 누르기로 인식

      // 타이머 저장 (pointerUp에서 취소하기 위해)
    (activePointerRef.current as any).timer = longPressTimer;
  }, [isListening, stopTTS, location.pathname]);

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

    // 길게 누르기 타이머 취소 (짧게 누른 경우 클릭으로 처리)
    const timer = (activePointerRef.current as any).timer;
    if (timer) {
      clearTimeout(timer);
    }

    // 짧게 누른 경우 (300ms 미만) - 클릭으로 간주하고 마이크 시작하지 않음
    const pressDuration = Date.now() - activePointerRef.current.startTime;
    const wasShortPress = pressDuration < 300;

    // 마이크 중지 (이미 마이크가 켜져 있는 경우)
    if (isListening && !wasShortPress) {
      VoiceService.stopSTT();
    }

    // 상태 리셋
    activePointerRef.current = null;
    setIsLongPressing(false);
    
    // 짧게 누른 경우 애니메이션 즉시 숨김 (클릭 이벤트가 정상 동작하도록)
    if (wasShortPress) {
      setShowAnimation(false);
    } else {
      setTimeout(() => {
        if (!isListening) {
          setShowAnimation(false);
        }
      }, 200);
    }
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
    
    // 관리자 페이지에서는 자동 재시작 비활성화
    if (location.pathname.startsWith('/admin')) {
      return;
    }
    
    // 마우스를 누르고 있는데 음성 인식이 꺼진 경우 자동 재시작
    if (isLongPressing && !isListening && activePointerRef.current) {
      // 최근에 명령어가 실행되었는지 확인 (시간 단축: 2000ms → 1000ms)
      const timeSinceLastCommand = Date.now() - commandExecutedRef.current;
      // 명령어 실행 후 1초 이내면 재시작하지 않음 (명령어 실행 후 자동 종료된 경우)
      if (timeSinceLastCommand < 1000) {
        if (import.meta.env.DEV) console.log('[GlobalVoice] 최근 명령어 실행으로 인한 자동 종료 - 재시작하지 않음');
        return;
      }
      
      // 이미 진행 중인지 확인 (VoiceService의 내부 상태 확인 불가하므로 짧은 딜레이 후 재시작)
      const timer = setTimeout(() => {
        // 재시작 전에 다시 확인 (다른 곳에서 이미 시작했을 수 있음)
        const currentListening = useVoiceStore.getState().isListening;
        // 다시 한 번 명령어 실행 시간 확인
        const timeSinceLastCommand2 = Date.now() - commandExecutedRef.current;
        if (isLongPressing && !currentListening && activePointerRef.current && timeSinceLastCommand2 >= 1000) {
          if (import.meta.env.DEV) console.log('[GlobalVoice] 음성 인식이 자동 중단됨 - 재시작');
          VoiceService.startSTT();
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
        VoiceService.stopSTT();
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

  // 관리자 페이지에서는 마이크 UI 표시하지 않음
  if (location.pathname.startsWith('/admin')) {
    return null;
  }

  if (!showAnimation && !isListening) {
    return null;
  }

  return (
    <VoiceMicAnimation
      isListening={isListening}
      isLongPressing={isLongPressing}
      transcript={transcript || ''}
      recognizedCommand={recognizedCommand}
    />
  );
}

