/**
 * Unit Tests - brailleChunk 유틸리티
 */
import { describe, it, expect } from 'vitest';
import { splitToBrailleChunks, estimateBrailleCells } from '../brailleChunk';

describe('brailleChunk', () => {
  describe('estimateBrailleCells', () => {
    it('should estimate cells correctly for Korean text', () => {
      expect(estimateBrailleCells('안녕')).toBe(4); // 한글 2자 = 4 cells
    });

    it('should estimate cells correctly for English text', () => {
      expect(estimateBrailleCells('hello')).toBe(5); // 영문 5자 = 5 cells
    });

    it('should estimate cells correctly for mixed text', () => {
      expect(estimateBrailleCells('안녕 hello')).toBe(10); // 한글 4 + 공백 1 + 영문 5 = 10 cells
    });

    it('should return 0 for empty text', () => {
      expect(estimateBrailleCells('')).toBe(0);
    });
  });

  describe('splitToBrailleChunks', () => {
    it('should split by word strategy', () => {
      const text = '안녕하세요 반갑습니다';
      const chunks = splitToBrailleChunks(text, {
        maxCells: 3,
        strategy: 'word',
      });
      
      expect(chunks.length).toBeGreaterThan(0);
      chunks.forEach(chunk => {
        expect(estimateBrailleCells(chunk)).toBeLessThanOrEqual(3);
      });
    });

    it('should split by sentence strategy', () => {
      const text = '첫 번째 문장입니다. 두 번째 문장입니다.';
      const chunks = splitToBrailleChunks(text, {
        maxCells: 3,
        strategy: 'sentence',
      });
      
      expect(chunks.length).toBeGreaterThan(0);
    });

    it('should split by smart strategy', () => {
      const text = '수식 x² + 2x + 1 = 0 입니다.';
      const chunks = splitToBrailleChunks(text, {
        maxCells: 3,
        strategy: 'smart',
      });
      
      expect(chunks.length).toBeGreaterThan(0);
    });

    it('should return empty array for empty text', () => {
      const chunks = splitToBrailleChunks('', {
        maxCells: 3,
        strategy: 'word',
      });
      
      expect(chunks).toEqual([]);
    });
  });
});

