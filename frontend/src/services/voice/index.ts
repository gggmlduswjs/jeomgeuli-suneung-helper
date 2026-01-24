import { useVoiceStore } from '../../store/voice';
import VoiceEventBus, { VoiceEventType } from '../../lib/voice/VoiceEventBus';
import micMode from '../../lib/voice/MicMode';
import GoogleStreamingProvider from '../../stt/GoogleStreamingProvider';
import { CircuitBreaker } from '../../lib/voice/CircuitBreaker';
import { TranscriptProcessor } from '../../lib/voice/TranscriptProcessor';
import { createWebSpeechSTTProvider } from './providers/WebSpeechSTTProvider';
import { createWebSpeechTTSProvider } from './providers/WebSpeechTTSProvider';
import type { STTProvider, TTSProvider, StartSTTOptions } from './types';

// Re-export types
export type { STTProvider, TTSProvider, StartSTTOptions } from './types';

/**
 * VoiceService - 음성 관련 비즈니스 로직 통합 서비스
 * STT/TTS 프로바이더를 관리하고 명령 처리를 오케스트레이션합니다.
 */
class VoiceServiceClass {
  private sttProvider: STTProvider | null = null;
  private ttsProvider: TTSProvider | null = null;
  private isInitialized = false;
  private _transcriptProcessor: TranscriptProcessor | null = null;
  private circuitBreaker: CircuitBreaker | null = null;
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
    this._transcriptProcessor = new TranscriptProcessor();
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
    return createWebSpeechSTTProvider(this.currentAnswerList, this.circuitBreaker);
  }

  /**
   * 기본 TTS Provider 생성
   */
  private createDefaultTTSProvider(): TTSProvider {
    return createWebSpeechTTSProvider();
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
      // 개발 환경에서만 로그 출력
      if (import.meta.env.DEV) {
        if (import.meta.env.DEV) console.log('[VoiceService] 이미 리스닝 중 - 무시');
      }
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
      // 개발 환경에서만 로그 출력
      if (import.meta.env.DEV) {
        if (import.meta.env.DEV) console.log('[VoiceService] 이미 중지됨 - 무시');
      }
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
    // 개발 환경에서만 로그 출력
    if (import.meta.env.DEV) {
      if (import.meta.env.DEV) console.log('[VoiceService] 정답 목록 설정:', answers.length, '개');
    }
  }
}

// Singleton 인스턴스
const VoiceService = new VoiceServiceClass();

// 자동 초기화
VoiceService.init();

export default VoiceService;

