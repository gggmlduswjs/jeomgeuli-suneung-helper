import { useVoiceStore } from '../store/voice';
import VoiceEventBus, { VoiceEventType, emitTranscript } from '../lib/voice/VoiceEventBus';
import micMode from '../lib/voice/MicMode';
import GoogleStreamingProvider from '../stt/GoogleStreamingProvider';
import { TranscriptProcessor } from '../lib/voice/TranscriptProcessor';
import { CircuitBreaker } from '../lib/voice/CircuitBreaker';

/**
 * STT Provider 인터페이스
 */
export interface STTProvider {
  start(): Promise<void>;
  stop(): void;
  isListening(): boolean;
  onResult(callback: (final: boolean, alternatives: Array<{ transcript: string; confidence?: number }>) => void): void;
  onError(callback: (error: { code: string; message?: string }) => void): void;
}

/**
 * STT 시작 옵션
 */
export interface StartSTTOptions {
  onResult?: (text: string, alternatives?: Array<{ transcript: string; confidence: number }>) => void;
  onError?: (error: string) => void;
  autoStop?: boolean; // 결과 수신 후 자동 중지 여부
}

/**
 * TTS Provider 인터페이스
 */
export interface TTSProvider {
  speak(text: string | string[], options?: { rate?: number; pitch?: number; volume?: number; lang?: string }): Promise<void>;
  stop(): void;
  pause(): void;
  resume(): void;
  isSpeaking(): boolean;
}

/**
 * VoiceService - 음성 관련 비즈니스 로직 통합 서비스
 * STT/TTS 프로바이더를 관리하고 명령 처리를 오케스트레이션합니다.
 */
class VoiceServiceClass {
  private sttProvider: STTProvider | null = null;
  private ttsProvider: TTSProvider | null = null;
  private isInitialized = false;
  private transcriptProcessor: TranscriptProcessor;
  private circuitBreaker: CircuitBreaker;
  private currentAnswerList: string[] = [];

  /**
   * 서비스 초기화
   */
  init(sttProvider?: STTProvider, ttsProvider?: TTSProvider): void {
    if (this.isInitialized) {
      console.warn('[VoiceService] 이미 초기화됨');
      return;
    }

    // TranscriptProcessor 및 CircuitBreaker 초기화
    this.transcriptProcessor = new TranscriptProcessor();
    this.circuitBreaker = new CircuitBreaker(3, 5000); // 최대 3회 실패, 5초 후 재시도

    this.sttProvider = sttProvider || this.createDefaultSTTProvider();
    this.ttsProvider = ttsProvider || this.createDefaultTTSProvider();
    
    this.setupEventListeners();
    this.isInitialized = true;
  }

  /**
   * 기본 STT Provider 생성
   */
  private createDefaultSTTProvider(): STTProvider {
    // Google Streaming Provider 또는 Web Speech API 사용
    try {
      const mode = String((import.meta as any).env?.VITE_STT_PROVIDER || 'webspeech').toLowerCase();
      if (mode === 'google') {
        return new GoogleStreamingProvider() as unknown as STTProvider;
      }
    } catch (error) {
      console.warn('[VoiceService] Google provider 생성 실패, Web Speech 사용:', error);
    }

    return this.createWebSpeechSTTProvider();
  }

  /**
   * Web Speech API 기반 STT Provider 생성
   */
  private createWebSpeechSTTProvider(): STTProvider {
    const Recognition = this.getRecognitionCtor();
    if (!Recognition) {
      throw new Error('브라우저가 음성 인식을 지원하지 않습니다.');
    }

    let recognitionInstance: any = null;
    let isListening = false;
    let isIntentionallyStopped = false; // 의도적인 중단 추적
    let hasEnded = false; // onend가 호출되었는지 추적
    let resultCallback: ((final: boolean, alternatives: Array<{ transcript: string; confidence?: number }>) => void) | null = null;
    let errorCallback: ((error: { code: string; message?: string }) => void) | null = null;
    let lastAlternatives: Array<{ transcript: string; confidence?: number }> = []; // 마지막 alternatives 저장
    
    // TranscriptProcessor 인스턴스 (각 recognition 인스턴스마다 별도)
    const processor = new TranscriptProcessor();

    return {
      start: async () => {
        // Store의 상태도 확인하여 동기화
        const storeListening = useVoiceStore.getState().isListening;
        
        // recognition 인스턴스가 실제로 존재하고 활성 상태인지 확인
        if (recognitionInstance) {
          // Web Speech API의 recognition 상태 확인
          // Chrome: recognition.state ('idle' | 'listening' | 'stopped')
          // 일부 브라우저: recognition.readyState (0=idle, 1=starting, 2=listening, 3=stopped)
          const recognitionState = recognitionInstance.state || 
            (recognitionInstance.readyState === 2 ? 'listening' : 'idle');
          
          if (recognitionState === 'listening') {
            console.warn('[VoiceService] 이미 음성 인식이 진행 중입니다.');
            return;
          } else {
            // 인스턴스가 있지만 비활성 상태면 리셋
            console.log('[VoiceService] recognition 인스턴스가 비활성 상태 - 리셋');
            recognitionInstance = null;
          }
        }
        
        // 상태 불일치 감지 시 리셋
        if (isListening || storeListening) {
          console.log('[VoiceService] 상태 불일치 감지 - 리셋 후 재시작');
          isListening = false;
          useVoiceStore.getState().setListening(false);
          recognitionInstance = null;
        }

        try {
          const recognition = new Recognition();
          recognition.lang = 'ko-KR';
          recognition.continuous = true; // 계속 듣도록 설정
          recognition.interimResults = true; // 중간 결과도 받기
          recognition.maxAlternatives = 3;

          // 정답 목록을 제어어로 등록 (인식률 향상)
          const answerList = this.currentAnswerList;
          if (answerList.length > 0 && ('webkitSpeechGrammarList' in recognition || 'SpeechGrammarList' in window)) {
            try {
              const SpeechGrammarList = (window as any).SpeechGrammarList || (window as any).webkitSpeechGrammarList;
              const grammarList = new SpeechGrammarList();
              
              // JSGF 형식으로 문법 생성 (최대 100개까지, 브라우저 호환성 고려)
              const limitedAnswers = answerList.slice(0, 100);
              const grammar = `#JSGF V1.0; grammar answers; public <answer> = ${limitedAnswers.join(' | ')};`;
              grammarList.addFromString(grammar, 1.0);
              recognition.grammars = grammarList;
              console.log('[VoiceService] 정답 목록을 제어어로 등록:', limitedAnswers.length, '개');
            } catch (error) {
              console.warn('[VoiceService] SpeechGrammarList 설정 실패:', error);
            }
          }

          recognition.onstart = () => {
            isListening = true;
            isIntentionallyStopped = false; // 시작 시 플래그 리셋
            hasEnded = false; // 시작 시 리셋
            lastAlternatives = []; // 시작 시 초기화
            processor.reset(); // 시작 시 processor 리셋
            useVoiceStore.getState().setListening(true);
            useVoiceStore.getState().setSTTError(null);
          };

          recognition.onresult = (event: any) => {
            console.log('[VoiceService] onresult 호출:', {
              resultIndex: event.resultIndex,
              resultsLength: event.results.length,
            });
            
            const alternatives: Array<{ transcript: string; confidence?: number }> = [];
            let finalTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; i++) {
              const result = event.results[i];
              console.log('[VoiceService] result:', {
                isFinal: result.isFinal,
                length: result.length,
                transcript: result[0]?.transcript,
              });
              
              // interimResults가 true일 때는 모든 결과 처리
              for (let j = 0; j < result.length; j++) {
                const alt = result[j];
                const t = alt?.transcript ?? '';
                const conf = alt?.confidence ?? 0;
                if (t.trim()) {
                  alternatives.push({ transcript: t.trim(), confidence: conf });
                  // final 결과만 최종 텍스트로 사용
                  if (result.isFinal && j === 0) {
                    finalTranscript = t.trim();
                  }
                }
              }
            }

            // alternatives 저장 (onend에서 사용하기 위해)
            lastAlternatives = alternatives;
            
            // 중간 결과 찾기 (전체 results를 역순으로 확인하여 가장 최신 중간 결과 찾기)
            let interimTranscript = '';
            // 전체 results를 역순으로 확인하여 가장 최신 중간 결과 찾기
            for (let i = event.results.length - 1; i >= 0; i--) {
              const result = event.results[i];
              if (!result.isFinal && result.length > 0) {
                const t = result[0]?.transcript?.trim() ?? '';
                if (t) {
                  interimTranscript = t;
                  break; // 가장 최신 중간 결과를 찾으면 중단
                }
              }
            }
            
            // 중간 결과를 먼저 처리 (실시간 표시를 위해)
            if (interimTranscript) {
              processor.processInterim(interimTranscript, alternatives);
            }
            
            // 그 다음 최종 결과 처리
            if (finalTranscript) {
              // 최종 결과 처리
              const sortedAlts = alternatives
                .map(a => ({ transcript: a.transcript, confidence: a.confidence ?? 0 }))
                .sort((a, b) => b.confidence - a.confidence);
              
              processor.processFinal(
                finalTranscript,
                sortedAlts,
                resultCallback ? (text, alts) => {
                  resultCallback(true, alts);
                } : undefined
              );
            }
          };

          recognition.onerror = (event: any) => {
            const code = event?.error ?? 'unknown';
            
            // 'aborted'는 의도적인 중단이거나 이미 종료된 경우 에러로 처리하지 않음
            if (code === 'aborted') {
              // 이미 onend가 호출되었거나 의도적으로 중단된 경우
              if (hasEnded || isIntentionallyStopped) {
                console.log('[VoiceService] 음성 인식이 정상적으로 종료되었습니다.');
                isListening = false;
                useVoiceStore.getState().setListening(false);
                recognitionInstance = null; // 인스턴스 리셋
                return;
              }
              // 그 외의 경우는 브라우저가 자동으로 중단한 것으로 간주 (음성 미감지 등, 에러 아님)
              console.log('[VoiceService] 음성 인식이 자동으로 중단되었습니다 (음성 미감지).');
              isListening = false;
              useVoiceStore.getState().setListening(false);
              recognitionInstance = null; // 인스턴스 리셋
              // 에러 메시지 설정하지 않음
              return;
            }
            
            // CircuitBreaker에 실패 기록 (중요한 에러만)
            const criticalErrors = ['not-allowed', 'audio-capture', 'network'];
            if (criticalErrors.includes(code)) {
              try {
                this.circuitBreaker.executeSync(() => {
                  throw new Error(`STT error: ${code}`);
                });
              } catch {
                // CircuitBreaker가 실패를 기록함
              }
            }
            
            const msg = this.getErrorMessage(code);
            isListening = false;
            useVoiceStore.getState().setSTTError(msg);
            useVoiceStore.getState().setListening(false);
            recognitionInstance = null; // 인스턴스 리셋
            if (errorCallback) {
              errorCallback({ code, message: msg });
            }
          };

          recognition.onend = () => {
            hasEnded = true; // 종료 플래그 설정
            isListening = false;
            isIntentionallyStopped = false; // 종료 시 플래그 리셋
            useVoiceStore.getState().setListening(false);
            
            // 마지막 중간 결과를 최종 결과로 승격
            // Store에서 현재 transcript를 확인하고, alternatives는 마지막으로 저장된 것 사용
            const currentTranscript = useVoiceStore.getState().transcript;
            const finalAlts = lastAlternatives.length > 0 
              ? lastAlternatives.map(a => ({ transcript: a.transcript, confidence: a.confidence ?? 0.8 }))
              : (currentTranscript ? [{ transcript: currentTranscript, confidence: 0.8 }] : []);
            
            processor.promoteInterimToFinal(
              finalAlts,
              resultCallback ? (text, alts) => {
                resultCallback(true, alts);
              } : undefined
            );
            
            recognitionInstance = null;
          };

          recognitionInstance = recognition;
          
          // CircuitBreaker를 사용하여 안전하게 시작
          try {
            this.circuitBreaker.executeSync(() => {
              recognition.start();
            });
          } catch (circuitError: any) {
            console.error('[VoiceService] Circuit breaker blocked start:', circuitError);
            isListening = false;
            const msg = '음성 인식 서비스가 일시적으로 사용할 수 없습니다. 잠시 후 다시 시도해주세요.';
            useVoiceStore.getState().setSTTError(msg);
            if (errorCallback) {
              errorCallback({ code: 'circuit_open', message: msg });
            }
            return;
          }
        } catch (error: any) {
          isListening = false;
          const msg = error?.message || '음성 인식을 시작할 수 없습니다.';
          useVoiceStore.getState().setSTTError(msg);
          if (errorCallback) {
            errorCallback({ code: 'start_failed', message: msg });
          }
        }
      },

      stop: () => {
        // 의도적인 중단 플래그 설정
        isIntentionallyStopped = true;
        
        if (recognitionInstance) {
          try {
            if (typeof recognitionInstance.abort === 'function') {
              recognitionInstance.abort();
            } else {
              recognitionInstance.stop();
            }
          } catch (error) {
            console.warn('[VoiceService] STT 중지 중 오류:', error);
          }
          recognitionInstance = null;
        }
        isListening = false;
        useVoiceStore.getState().setListening(false);
      },

      isListening: () => isListening,

      onResult: (callback) => {
        resultCallback = callback;
      },

      onError: (callback) => {
        errorCallback = callback;
      },
    };
  }

  /**
   * 기본 TTS Provider 생성
   */
  private createDefaultTTSProvider(): TTSProvider {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
      throw new Error('브라우저가 음성 합성을 지원하지 않습니다.');
    }

    let currentUtterance: SpeechSynthesisUtterance | null = null;
    let utteranceQueue: string[] = [];
    let isProcessing = false;
    let isSpeaking = false;
    let isPaused = false;

    const processQueue = async (options: { rate?: number; pitch?: number; volume?: number; lang?: string } = {}) => {
      if (isProcessing || !utteranceQueue.length) return;

      isProcessing = true;
      const text = utteranceQueue.shift()!;
      const utt = new SpeechSynthesisUtterance(text);
      
      utt.rate = options.rate ?? 0.9;
      utt.pitch = options.pitch ?? 1.0;
      utt.volume = options.volume ?? 1.0;
      utt.lang = options.lang || 'ko-KR';

      utt.onstart = () => {
        currentUtterance = utt;
        isSpeaking = true;
        isPaused = false;
        useVoiceStore.getState().setSpeaking(true);
      };

      utt.onend = () => {
        currentUtterance = null;
        isSpeaking = false;
        isPaused = false;
        isProcessing = false;
        useVoiceStore.getState().setSpeaking(false);
        
        if (utteranceQueue.length) {
          setTimeout(() => processQueue(options), 60);
        }
      };

      utt.onerror = () => {
        currentUtterance = null;
        isSpeaking = false;
        isPaused = false;
        isProcessing = false;
        useVoiceStore.getState().setSpeaking(false);
        
        if (utteranceQueue.length) {
          setTimeout(() => processQueue(options), 60);
        }
      };

      try {
        window.speechSynthesis.speak(utt);
      } catch (error) {
        isProcessing = false;
        currentUtterance = null;
        if (utteranceQueue.length) {
          setTimeout(() => processQueue(options), 60);
        }
      }
    };

    return {
      speak: async (text: string | string[], options = {}) => {
        // Mic Mode 체크
        if (micMode.isActive() && !(options as any)?.allowDuringMic) {
          return;
        }

        const texts = (Array.isArray(text) ? text : [text])
          .map(t => String(t ?? '').trim())
          .filter(Boolean);

        if (!texts.length) return;

        // 기존 재생 정리
        try {
          window.speechSynthesis.cancel();
        } catch {}
        
        utteranceQueue = texts;
        useVoiceStore.getState().setTTSError(null);
        processQueue(options);
      },

      stop: () => {
        try {
          window.speechSynthesis.cancel();
        } catch {}
        utteranceQueue = [];
        currentUtterance = null;
        isProcessing = false;
        isSpeaking = false;
        isPaused = false;
        useVoiceStore.getState().setSpeaking(false);
      },

      pause: () => {
        if (!isSpeaking || isPaused) return;
        try {
          window.speechSynthesis.pause();
          isPaused = true;
          useVoiceStore.getState().setPaused(true);
        } catch {}
      },

      resume: () => {
        if (!isSpeaking || !isPaused) return;
        try {
          window.speechSynthesis.resume();
          isPaused = false;
          useVoiceStore.getState().setPaused(false);
        } catch {}
      },

      isSpeaking: () => isSpeaking,
    };
  }

  /**
   * Speech Recognition 생성자 가져오기
   */
  private getRecognitionCtor(): (new () => any) | null {
    if (typeof window === 'undefined') return null;
    const w = window as any;
    return w.SpeechRecognition || w.webkitSpeechRecognition || null;
  }

  /**
   * 에러 메시지 변환
   */
  private getErrorMessage(code: string): string {
    switch (code) {
      case 'not-allowed':
        return '마이크 권한이 거부되었습니다.';
      case 'no-speech':
        return '음성이 감지되지 않았습니다.';
      case 'audio-capture':
        return '마이크가 감지되지 않았습니다.';
      case 'network':
        return '네트워크 오류가 발생했습니다.';
      case 'aborted':
        return '음성 인식이 중단되었습니다.';
      default:
        return '음성 인식 오류가 발생했습니다.';
    }
  }

  /**
   * 이벤트 리스너 설정
   */
  private setupEventListeners(): void {
    // Mic Mode 변경 시 TTS 자동 중지
    VoiceEventBus.on(VoiceEventType.MIC_MODE, (event) => {
      const detail = event.detail as { active?: boolean };
      if (detail?.active && this.ttsProvider) {
        this.ttsProvider.stop();
      }
    });
  }

  /**
   * STT 시작
   */
  async startSTT(options?: StartSTTOptions): Promise<void> {
    // 이미 리스닝 중이면 무시 (중복 시작 방지)
    if (this.sttProvider?.isListening()) {
      console.log('[VoiceService] 이미 리스닝 중 - 무시');
      return;
    }
    
    if (!this.isInitialized) {
      this.init();
    }

    if (!this.sttProvider) {
      throw new Error('STT Provider가 초기화되지 않았습니다.');
    }

    // TTS 중지
    if (this.ttsProvider) {
      this.ttsProvider.stop();
    }

    // Mic Mode 활성화 (Store 업데이트)
    useVoiceStore.getState().setMicMode(true);
    micMode.requestStart(); // 하위 호환성을 위해 유지 (내부적으로는 Store 사용)

    // 콜백 등록
    if (options?.onResult || options?.onError) {
      if (options.onResult) {
        this.sttProvider.onResult((final, alternatives) => {
          if (final && alternatives.length > 0) {
            const text = alternatives[0].transcript;
            const alts = alternatives.map(a => ({
              transcript: a.transcript,
              confidence: a.confidence ?? 0,
            }));
            options.onResult!(text, alts);
            
            // autoStop 옵션이 있으면 자동 중지
            if (options.autoStop) {
              this.stopSTT();
            }
          }
        });
      }

      if (options.onError) {
        this.sttProvider.onError((error) => {
          options.onError!(error.message || '음성 인식 오류가 발생했습니다.');
        });
      }
    }

    await this.sttProvider.start();
  }

  /**
   * STT 중지
   */
  stopSTT(): void {
    // 이미 중지되었으면 무시 (중복 중지 방지)
    if (!this.sttProvider?.isListening()) {
      console.log('[VoiceService] 이미 중지됨 - 무시');
      return;
    }
    
    if (this.sttProvider) {
      this.sttProvider.stop();
    }
    // Store 업데이트
    useVoiceStore.getState().setMicMode(false);
    // transcript 초기화 - 페이지 이동 시 이전 transcript가 남지 않도록
    useVoiceStore.getState().resetTranscript();
    micMode.requestStop(); // 하위 호환성을 위해 유지
  }

  /**
   * TTS 재생
   */
  async speak(text: string | string[], options?: { rate?: number; pitch?: number; volume?: number; lang?: string; allowDuringMic?: boolean }): Promise<void> {
    if (!this.isInitialized) {
      this.init();
    }

    if (!this.ttsProvider) {
      throw new Error('TTS Provider가 초기화되지 않았습니다.');
    }

    await this.ttsProvider.speak(text, options);
  }

  /**
   * TTS 중지
   */
  stopTTS(): void {
    if (this.ttsProvider) {
      this.ttsProvider.stop();
    }
  }

  /**
   * TTS 일시정지
   */
  pauseTTS(): void {
    if (this.ttsProvider) {
      this.ttsProvider.pause();
    }
  }

  /**
   * TTS 재개
   */
  resumeTTS(): void {
    if (this.ttsProvider) {
      this.ttsProvider.resume();
    }
  }

  /**
   * 현재 STT 상태
   */
  isSTTListening(): boolean {
    return this.sttProvider?.isListening() ?? false;
  }

  /**
   * 현재 STT 상태 전체 조회
   */
  getSTTState(): {
    isListening: boolean;
    transcript: string;
    alternatives: Array<{ transcript: string; confidence: number }>;
    error: string | null;
  } {
    const store = useVoiceStore.getState();
    return {
      isListening: this.sttProvider?.isListening() ?? false,
      transcript: store.transcript,
      alternatives: store.alternatives,
      error: store.sttError,
    };
  }

  /**
   * 현재 TTS 상태
   */
  isTTSSpeaking(): boolean {
    return this.ttsProvider?.isSpeaking() ?? false;
  }

  /**
   * 정답 목록 설정 (제어어로 등록하여 인식률 향상)
   */
  setAnswerList(answers: string[]): void {
    this.currentAnswerList = answers;
    console.log('[VoiceService] 정답 목록 설정:', answers.length, '개');
  }
}

// Singleton 인스턴스
const VoiceService = new VoiceServiceClass();

// 자동 초기화
VoiceService.init();

export default VoiceService;

