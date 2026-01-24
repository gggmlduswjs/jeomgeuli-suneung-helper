/**
 * Web Speech API 기반 STT Provider
 */
import { useVoiceStore } from '../../../store/voice';
import { TranscriptProcessor } from '../../../lib/voice/TranscriptProcessor';
import { CircuitBreaker } from '../../../lib/voice/CircuitBreaker';
import type { STTProvider } from '../types';

/**
 * Speech Recognition 생성자 가져오기
 */
function getRecognitionCtor(): (new () => any) | null {
  if (typeof window === 'undefined') return null;
  const w = window as any;
  return w.SpeechRecognition || w.webkitSpeechRecognition || null;
}

/**
 * 에러 메시지 변환
 */
function getErrorMessage(code: string): string {
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
 * Web Speech API 기반 STT Provider 생성
 */
export function createWebSpeechSTTProvider(
  currentAnswerList: string[],
  circuitBreaker: CircuitBreaker | null
): STTProvider {
  const Recognition = getRecognitionCtor();
  if (!Recognition) {
    throw new Error('브라우저가 음성 인식을 지원하지 않습니다.');
  }

  type SpeechRecognitionInstance = InstanceType<typeof Recognition>;
  let recognitionInstance: SpeechRecognitionInstance | null = null;
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
          if (import.meta.env.DEV) {
            console.warn('[VoiceService] 이미 음성 인식이 진행 중입니다.');
          }
          return;
        } else {
          // 인스턴스가 있지만 비활성 상태면 리셋
          if (import.meta.env.DEV) {
            if (import.meta.env.DEV) console.log('[VoiceService] recognition 인스턴스가 비활성 상태 - 리셋');
          }
          recognitionInstance = null;
        }
      }

      // 상태 불일치 감지 시 리셋
      if (isListening || storeListening) {
        if (import.meta.env.DEV) {
          if (import.meta.env.DEV) console.log('[VoiceService] 상태 불일치 감지 - 리셋 후 재시작');
        }
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
        const answerList = currentAnswerList;
        if (answerList.length > 0 && ('webkitSpeechGrammarList' in recognition || 'SpeechGrammarList' in window)) {
          try {
            const SpeechGrammarList = (window as any).SpeechGrammarList || (window as any).webkitSpeechGrammarList;
            const grammarList = new SpeechGrammarList();

            // JSGF 형식으로 문법 생성 (최대 100개까지, 브라우저 호환성 고려)
            const limitedAnswers = answerList.slice(0, 100);
            const grammar = `#JSGF V1.0; grammar answers; public <answer> = ${limitedAnswers.join(' | ')};`;
            grammarList.addFromString(grammar, 1.0);
            recognition.grammars = grammarList;
            if (import.meta.env.DEV) {
              if (import.meta.env.DEV) console.log('[VoiceService] 정답 목록을 제어어로 등록:', limitedAnswers.length, '개');
            }
          } catch (error) {
            if (import.meta.env.DEV) {
              console.warn('[VoiceService] SpeechGrammarList 설정 실패:', error);
            }
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
          // 개발 환경에서만 로그 출력 (디버깅용)
          if (import.meta.env.DEV) {
            if (import.meta.env.DEV) console.log('[VoiceService] onresult 호출:', {
              resultIndex: event.resultIndex,
              resultsLength: event.results.length,
            });
          }

          const alternatives: Array<{ transcript: string; confidence?: number }> = [];
          let finalTranscript = '';

          for (let i = event.resultIndex; i < event.results.length; i++) {
            const result = event.results[i];
            // 개발 환경에서만 로그 출력
            if (import.meta.env.DEV) {
              if (import.meta.env.DEV) console.log('[VoiceService] result:', {
                isFinal: result.isFinal,
                length: result.length,
                transcript: result[0]?.transcript,
              });
            }

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
              resultCallback ? (_text, alts) => {
                resultCallback?.(true, alts);
              } : undefined
            );
          }
        };

        recognition.onerror = (event: Event & { error?: string }) => {
          const code = event?.error ?? 'unknown';

          // 'aborted'는 의도적인 중단이거나 이미 종료된 경우 에러로 처리하지 않음
          if (code === 'aborted') {
            // 이미 onend가 호출되었거나 의도적으로 중단된 경우
            if (hasEnded || isIntentionallyStopped) {
              if (import.meta.env.DEV) {
                if (import.meta.env.DEV) console.log('[VoiceService] 음성 인식이 정상적으로 종료되었습니다.');
              }
              isListening = false;
              useVoiceStore.getState().setListening(false);
              recognitionInstance = null; // 인스턴스 리셋
              return;
            }
            // 그 외의 경우는 브라우저가 자동으로 중단한 것으로 간주 (음성 미감지 등, 에러 아님)
            if (import.meta.env.DEV) {
              if (import.meta.env.DEV) console.log('[VoiceService] 음성 인식이 자동으로 중단되었습니다 (음성 미감지).');
            }
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
              circuitBreaker?.executeSync(() => {
                throw new Error(`STT error: ${code}`);
              });
            } catch {
              // CircuitBreaker가 실패를 기록함
            }
          }

          const msg = getErrorMessage(code);
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
            resultCallback ? (_text, alts) => {
              resultCallback?.(true, alts);
            } : undefined
          );

          recognitionInstance = null;
        };

        recognitionInstance = recognition;

        // CircuitBreaker를 사용하여 안전하게 시작
        try {
          circuitBreaker?.executeSync(() => {
            recognition.start();
          });
        } catch (circuitError: unknown) {
          console.error('[VoiceService] Circuit breaker blocked start:', circuitError);
          isListening = false;
          const msg = '음성 인식 서비스가 일시적으로 사용할 수 없습니다. 잠시 후 다시 시도해주세요.';
          useVoiceStore.getState().setSTTError(msg);
          if (errorCallback) {
            errorCallback({ code: 'circuit_open', message: msg });
          }
          return;
        }
      } catch (error: unknown) {
        isListening = false;
        const msg = error instanceof Error ? error.message : '음성 인식을 시작할 수 없습니다.';
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
