/**
 * Unit Tests - 과목별 학습 전략
 */
import { describe, it, expect } from 'vitest';
import { getSubjectStrategy, extractSubjectType, SUBJECT_STRATEGIES } from '../subjectLearning';

describe('subjectLearning', () => {
  describe('extractSubjectType', () => {
    it('should extract math subject', () => {
      expect(extractSubjectType('수학')).toBe('math');
      expect(extractSubjectType('수능특강 수학')).toBe('math');
    });

    it('should extract korean subject', () => {
      expect(extractSubjectType('국어')).toBe('korean');
      expect(extractSubjectType('수능특강 국어')).toBe('korean');
    });

    it('should extract english subject', () => {
      expect(extractSubjectType('영어')).toBe('english');
      expect(extractSubjectType('수능특강 영어')).toBe('english');
    });

    it('should default to math for unknown subject', () => {
      expect(extractSubjectType('알 수 없는 과목')).toBe('math');
    });
  });

  describe('getSubjectStrategy', () => {
    it('should return math strategy for math', () => {
      const strategy = getSubjectStrategy('math');
      expect(strategy.subject).toBe('math');
      expect(strategy.readQuestion.chunkStrategy).toBe('smart');
      expect(strategy.specialHandling?.math).toBe('formula-braille');
    });

    it('should return korean strategy for korean', () => {
      const strategy = getSubjectStrategy('korean');
      expect(strategy.subject).toBe('korean');
      expect(strategy.readQuestion.chunkStrategy).toBe('sentence');
      expect(strategy.specialHandling?.korean).toBe('passage-braille');
    });

    it('should return english strategy for english', () => {
      const strategy = getSubjectStrategy('english');
      expect(strategy.subject).toBe('english');
      expect(strategy.readQuestion.chunkStrategy).toBe('word');
      expect(strategy.specialHandling?.english).toBe('audio-first');
    });

    it('should adjust strategy for 3-cell display', () => {
      // 3-cell은 audioFallback이 true여야 함
      const strategy = getSubjectStrategy('math');
      expect(strategy.readQuestion.audioFallback).toBe(true);
    });
  });

  describe('SUBJECT_STRATEGIES', () => {
    it('should have all required subjects', () => {
      expect(SUBJECT_STRATEGIES.math).toBeDefined();
      expect(SUBJECT_STRATEGIES.korean).toBeDefined();
      expect(SUBJECT_STRATEGIES.english).toBeDefined();
      expect(SUBJECT_STRATEGIES.science).toBeDefined();
      expect(SUBJECT_STRATEGIES.social).toBeDefined();
    });

    it('should have consistent structure for all strategies', () => {
      Object.values(SUBJECT_STRATEGIES).forEach(strategy => {
        expect(strategy.readQuestion).toBeDefined();
        expect(strategy.displayContent).toBeDefined();
        expect(strategy.readQuestion.primary).toMatch(/^(braille-chunk|audio|mixed)$/);
        expect(strategy.readQuestion.chunkStrategy).toMatch(/^(word|sentence|smart)$/);
      });
    });
  });
});

