import { describe, it, expect, beforeEach } from 'vitest';
import CommandService from '../CommandService';
import type { CommandHandlers } from '../../lib/voice/CommandRouter';

describe('CommandService', () => {
  let handlers: CommandHandlers;
  let callLog: string[];

  beforeEach(() => {
    callLog = [];
    handlers = {
      learn: () => { callLog.push('learn'); },
      home: () => { callLog.push('home'); },
      next: () => { callLog.push('next'); },
    };
    CommandService.clearCache();
  });

  describe('processCommand', () => {
    it('should process valid command', () => {
      const result = CommandService.processCommand('학습', handlers);
      expect(result).toBe(true);
      expect(callLog).toContain('learn');
    });

    it('should return false for invalid command', () => {
      const result = CommandService.processCommand('알 수 없는 명령', handlers);
      expect(result).toBe(false);
      expect(callLog.length).toBe(0);
    });

    it('should handle empty text', () => {
      const result = CommandService.processCommand('', handlers);
      expect(result).toBe(false);
    });
  });

  describe('processCommandWithAlternatives', () => {
    it('should process first matching alternative', () => {
      const alternatives = [
        { transcript: '알 수 없는 명령', confidence: 0.9 },
        { transcript: '학습', confidence: 0.8 },
        { transcript: '홈', confidence: 0.7 },
      ];

      const result = CommandService.processCommandWithAlternatives(alternatives, handlers);
      expect(result).toBe(true);
      expect(callLog).toContain('learn');
    });

    it('should return false if no alternative matches', () => {
      const alternatives = [
        { transcript: '알 수 없는 명령1', confidence: 0.9 },
        { transcript: '알 수 없는 명령2', confidence: 0.8 },
      ];

      const result = CommandService.processCommandWithAlternatives(alternatives, handlers);
      expect(result).toBe(false);
    });
  });

  describe('cache', () => {
    it('should track cache statistics', () => {
      CommandService.processCommand('학습', handlers);
      const stats = CommandService.getCacheStats();
      
      expect(stats.misses).toBeGreaterThanOrEqual(0);
      expect(stats.hits).toBeGreaterThanOrEqual(0);
      expect(stats.size).toBeGreaterThanOrEqual(0);
      expect(stats.hitRate).toBeGreaterThanOrEqual(0);
      expect(stats.hitRate).toBeLessThanOrEqual(1);
    });

    it('should clear cache', () => {
      CommandService.processCommand('학습', handlers);
      CommandService.clearCache();
      
      const stats = CommandService.getCacheStats();
      expect(stats.size).toBe(0);
      expect(stats.hits).toBe(0);
      expect(stats.misses).toBe(0);
    });
  });
});



