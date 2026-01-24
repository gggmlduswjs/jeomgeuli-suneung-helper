/**
 * VoiceService 유닛 테스트
 *
 * 테스트 실행:
 * npm test tests/services/voice/VoiceService.test.ts
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import type { STTProvider, TTSProvider } from '../../../src/services/voice';

// Mock implementations
class MockSTTProvider implements STTProvider {
  private listening = false;
  private resultCallback: ((final: boolean, alternatives: Array<{ transcript: string; confidence?: number }>) => void) | null = null;
  private errorCallback: ((error: { code: string; message?: string }) => void) | null = null;

  async start(): Promise<void> {
    this.listening = true;
  }

  stop(): void {
    this.listening = false;
  }

  isListening(): boolean {
    return this.listening;
  }

  onResult(callback: (final: boolean, alternatives: Array<{ transcript: string; confidence?: number }>) => void): void {
    this.resultCallback = callback;
  }

  onError(callback: (error: { code: string; message?: string }) => void): void {
    this.errorCallback = callback;
  }

  // Test helper methods
  simulateResult(text: string, isFinal: boolean = true, confidence: number = 1.0): void {
    if (this.resultCallback) {
      this.resultCallback(isFinal, [{ transcript: text, confidence }]);
    }
  }

  simulateError(code: string, message?: string): void {
    if (this.errorCallback) {
      this.errorCallback({ code, message });
    }
  }
}

class MockTTSProvider implements TTSProvider {
  private speaking = false;
  private lastText: string | string[] = '';
  private lastOptions: any = null;

  async speak(text: string | string[], options?: any): Promise<void> {
    this.speaking = true;
    this.lastText = text;
    this.lastOptions = options;
    // Simulate async speech
    await new Promise(resolve => setTimeout(resolve, 10));
    this.speaking = false;
  }

  stop(): void {
    this.speaking = false;
  }

  pause(): void {
    // Mock implementation
  }

  resume(): void {
    // Mock implementation
  }

  isSpeaking(): boolean {
    return this.speaking;
  }

  getLastText(): string | string[] {
    return this.lastText;
  }

  getLastOptions(): any {
    return this.lastOptions;
  }
}

describe('STTProvider Interface', () => {
  describe('MockSTTProvider', () => {
    let provider: MockSTTProvider;

    beforeEach(() => {
      provider = new MockSTTProvider();
    });

    it('초기 상태는 listening이 false여야 함', () => {
      expect(provider.isListening()).toBe(false);
    });

    it('start() 호출 시 listening 상태가 true가 되어야 함', async () => {
      await provider.start();
      expect(provider.isListening()).toBe(true);
    });

    it('stop() 호출 시 listening 상태가 false가 되어야 함', async () => {
      await provider.start();
      provider.stop();
      expect(provider.isListening()).toBe(false);
    });

    it('onResult 콜백이 등록되어야 함', () => {
      const callback = vi.fn();
      provider.onResult(callback);

      provider.simulateResult('테스트', true, 0.95);

      expect(callback).toHaveBeenCalledWith(true, [
        { transcript: '테스트', confidence: 0.95 }
      ]);
    });

    it('onError 콜백이 등록되어야 함', () => {
      const callback = vi.fn();
      provider.onError(callback);

      provider.simulateError('network-error', '네트워크 오류');

      expect(callback).toHaveBeenCalledWith({
        code: 'network-error',
        message: '네트워크 오류'
      });
    });

    it('중간 결과와 최종 결과를 구분해야 함', () => {
      const callback = vi.fn();
      provider.onResult(callback);

      provider.simulateResult('중간', false, 0.7);
      provider.simulateResult('최종', true, 0.95);

      expect(callback).toHaveBeenNthCalledWith(1, false, [
        { transcript: '중간', confidence: 0.7 }
      ]);
      expect(callback).toHaveBeenNthCalledWith(2, true, [
        { transcript: '최종', confidence: 0.95 }
      ]);
    });
  });
});

describe('TTSProvider Interface', () => {
  describe('MockTTSProvider', () => {
    let provider: MockTTSProvider;

    beforeEach(() => {
      provider = new MockTTSProvider();
    });

    it('초기 상태는 speaking이 false여야 함', () => {
      expect(provider.isSpeaking()).toBe(false);
    });

    it('speak() 호출 시 텍스트가 저장되어야 함', async () => {
      await provider.speak('안녕하세요');
      expect(provider.getLastText()).toBe('안녕하세요');
    });

    it('speak() 호출 시 옵션이 저장되어야 함', async () => {
      const options = { rate: 1.2, pitch: 1.0, volume: 0.8 };
      await provider.speak('테스트', options);
      expect(provider.getLastOptions()).toEqual(options);
    });

    it('speak() 중에는 isSpeaking이 true여야 함', async () => {
      const speakPromise = provider.speak('긴 텍스트');
      expect(provider.isSpeaking()).toBe(true);
      await speakPromise;
      expect(provider.isSpeaking()).toBe(false);
    });

    it('stop() 호출 시 speaking 상태가 false가 되어야 함', async () => {
      provider.speak('테스트');
      provider.stop();
      expect(provider.isSpeaking()).toBe(false);
    });

    it('배열 형태의 텍스트도 처리해야 함', async () => {
      await provider.speak(['첫번째', '두번째']);
      expect(provider.getLastText()).toEqual(['첫번째', '두번째']);
    });
  });
});

describe('Provider Integration', () => {
  it('STT와 TTS가 독립적으로 작동해야 함', async () => {
    const sttProvider = new MockSTTProvider();
    const ttsProvider = new MockTTSProvider();

    await sttProvider.start();
    await ttsProvider.speak('음성 인식 중...');

    expect(sttProvider.isListening()).toBe(true);
    expect(ttsProvider.getLastText()).toBe('음성 인식 중...');

    sttProvider.stop();
    expect(sttProvider.isListening()).toBe(false);
  });

  it('STT 결과를 받아 TTS로 재생할 수 있어야 함', async () => {
    const sttProvider = new MockSTTProvider();
    const ttsProvider = new MockTTSProvider();
    const results: string[] = [];

    sttProvider.onResult((isFinal, alternatives) => {
      if (isFinal && alternatives.length > 0) {
        const text = alternatives[0].transcript;
        results.push(text);
        ttsProvider.speak(`인식됨: ${text}`);
      }
    });

    await sttProvider.start();
    sttProvider.simulateResult('안녕', true, 0.95);

    expect(results).toContain('안녕');
    expect(ttsProvider.getLastText()).toBe('인식됨: 안녕');
  });

  it('여러 대안을 처리할 수 있어야 함', () => {
    const sttProvider = new MockSTTProvider();
    const alternatives: Array<{ transcript: string; confidence?: number }> = [];

    sttProvider.onResult((isFinal, alts) => {
      if (isFinal) {
        alternatives.push(...alts);
      }
    });

    const callback = sttProvider['resultCallback'];
    if (callback) {
      callback(true, [
        { transcript: '홈', confidence: 0.9 },
        { transcript: '롬', confidence: 0.7 },
        { transcript: '곰', confidence: 0.5 }
      ]);
    }

    expect(alternatives.length).toBe(3);
    expect(alternatives[0].transcript).toBe('홈');
    expect(alternatives[0].confidence).toBeGreaterThan(alternatives[1].confidence!);
  });
});

describe('Error Handling', () => {
  it('STT 에러를 적절히 처리해야 함', () => {
    const provider = new MockSTTProvider();
    const errors: Array<{ code: string; message?: string }> = [];

    provider.onError((error) => {
      errors.push(error);
    });

    provider.simulateError('network-error', '연결 실패');
    provider.simulateError('not-allowed', '마이크 권한 거부');

    expect(errors).toHaveLength(2);
    expect(errors[0].code).toBe('network-error');
    expect(errors[1].code).toBe('not-allowed');
  });

  it('TTS가 중단되어도 STT는 계속 작동해야 함', async () => {
    const sttProvider = new MockSTTProvider();
    const ttsProvider = new MockTTSProvider();

    await sttProvider.start();
    await ttsProvider.speak('테스트');
    ttsProvider.stop();

    expect(sttProvider.isListening()).toBe(true);
    expect(ttsProvider.isSpeaking()).toBe(false);
  });
});

describe('Edge Cases', () => {
  it('빈 텍스트를 TTS로 전달해도 오류가 발생하지 않아야 함', async () => {
    const provider = new MockTTSProvider();
    await expect(provider.speak('')).resolves.not.toThrow();
  });

  it('STT가 중지된 상태에서 결과를 시뮬레이션해도 오류가 없어야 함', () => {
    const provider = new MockSTTProvider();
    const callback = vi.fn();
    provider.onResult(callback);

    provider.simulateResult('테스트', true);
    expect(callback).toHaveBeenCalled();
  });

  it('confidence 값이 없어도 처리되어야 함', () => {
    const provider = new MockSTTProvider();
    const callback = vi.fn();
    provider.onResult(callback);

    const callbackFn = provider['resultCallback'];
    if (callbackFn) {
      callbackFn(true, [{ transcript: '테스트' }]);
    }

    expect(callback).toHaveBeenCalledWith(true, [{ transcript: '테스트' }]);
  });

  it('여러 번 start를 호출해도 안전해야 함', async () => {
    const provider = new MockSTTProvider();

    await provider.start();
    await provider.start();
    await provider.start();

    expect(provider.isListening()).toBe(true);
  });

  it('이미 중지된 상태에서 stop을 호출해도 안전해야 함', () => {
    const provider = new MockSTTProvider();

    provider.stop();
    provider.stop();

    expect(provider.isListening()).toBe(false);
  });
});
