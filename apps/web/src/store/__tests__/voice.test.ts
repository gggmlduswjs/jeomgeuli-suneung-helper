import { describe, it, expect, beforeEach } from 'vitest';
import { useVoiceStore } from '../voice';

describe('useVoiceStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    useVoiceStore.getState().resetAll();
  });

  describe('STT state', () => {
    it('should update listening state', () => {
      useVoiceStore.getState().setListening(true);
      expect(useVoiceStore.getState().isListening).toBe(true);
      
      useVoiceStore.getState().setListening(false);
      expect(useVoiceStore.getState().isListening).toBe(false);
    });

    it('should update transcript', () => {
      const transcript = '테스트 텍스트';
      const alternatives = [
        { transcript: '테스트 텍스트', confidence: 0.9 },
        { transcript: '테스트 텍스', confidence: 0.7 },
      ];
      
      useVoiceStore.getState().setTranscript(transcript, alternatives);
      
      expect(useVoiceStore.getState().transcript).toBe(transcript);
      expect(useVoiceStore.getState().alternatives).toEqual(alternatives);
    });

    it('should clear error on successful transcript', () => {
      useVoiceStore.getState().setSTTError('Previous error');
      useVoiceStore.getState().setTranscript('Success');
      
      expect(useVoiceStore.getState().sttError).toBeNull();
    });

    it('should set STT error', () => {
      const error = 'STT error occurred';
      useVoiceStore.getState().setSTTError(error);
      
      expect(useVoiceStore.getState().sttError).toBe(error);
      expect(useVoiceStore.getState().isListening).toBe(false);
    });
  });

  describe('TTS state', () => {
    it('should update speaking state', () => {
      useVoiceStore.getState().setSpeaking(true);
      expect(useVoiceStore.getState().isSpeaking).toBe(true);
      
      useVoiceStore.getState().setSpeaking(false);
      expect(useVoiceStore.getState().isSpeaking).toBe(false);
    });

    it('should reset paused when speaking starts', () => {
      useVoiceStore.getState().setPaused(true);
      useVoiceStore.getState().setSpeaking(true);
      
      expect(useVoiceStore.getState().isPaused).toBe(false);
    });

    it('should set TTS error', () => {
      const error = 'TTS error';
      useVoiceStore.getState().setTTSError(error);
      
      expect(useVoiceStore.getState().ttsError).toBe(error);
    });
  });

  describe('Mic Mode', () => {
    it('should toggle mic mode', () => {
      expect(useVoiceStore.getState().micMode).toBe(false);
      
      useVoiceStore.getState().setMicMode(true);
      expect(useVoiceStore.getState().micMode).toBe(true);
      
      useVoiceStore.getState().toggleMicMode();
      expect(useVoiceStore.getState().micMode).toBe(false);
    });
  });

  describe('reset functions', () => {
    it('should reset transcript', () => {
      useVoiceStore.getState().setTranscript('Test', []);
      useVoiceStore.getState().setSTTError('Error');
      
      useVoiceStore.getState().resetTranscript();
      
      expect(useVoiceStore.getState().transcript).toBe('');
      expect(useVoiceStore.getState().alternatives).toEqual([]);
      expect(useVoiceStore.getState().sttError).toBeNull();
    });

    it('should reset all state', () => {
      useVoiceStore.getState().setListening(true);
      useVoiceStore.getState().setSpeaking(true);
      useVoiceStore.getState().setTranscript('Test');
      useVoiceStore.getState().setMicMode(true);
      
      useVoiceStore.getState().resetAll();
      
      expect(useVoiceStore.getState().isListening).toBe(false);
      expect(useVoiceStore.getState().isSpeaking).toBe(false);
      expect(useVoiceStore.getState().transcript).toBe('');
      expect(useVoiceStore.getState().micMode).toBe(false);
    });
  });
});

