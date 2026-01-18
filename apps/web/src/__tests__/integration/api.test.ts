/**
 * Integration Tests - API
 * Frontend-Backend 통합 테스트
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { examAPI, vocabAPI } from '../../lib/api';

// Mock fetch
global.fetch = vi.fn();

describe('API Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('ExamAPI Integration', () => {
    it('should fetch textbooks and units in sequence', async () => {
      // Mock textbooks response
      const mockTextbooks = {
        textbooks: [
          { id: 1, title: '수능특강 국어', publisher: 'EBS', year: 2024 },
        ],
      };

      // Mock units response
      const mockUnits = {
        units: [
          { id: 1, title: '1단원', order: 1, content: '내용', textbook_id: 1 },
        ],
      };

      // Mock fetch responses
      vi.mocked(fetch)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockTextbooks,
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockUnits,
        } as Response);

      // 실제 API 호출 시뮬레이션
      const textbooks = await examAPI.listTextbooks();
      expect(textbooks).toHaveLength(1);

      const units = await examAPI.listUnits(1);
      expect(units).toHaveLength(1);
      expect(units[0].textbook_id).toBe(1);
    });

    it('should handle question submission flow', async () => {
      const mockQuestion = {
        question: {
          id: 1,
          question_text: '테스트 문제',
          choice1: '선택지1',
          choice2: '선택지2',
          correct_answer: 1,
        },
      };

      const mockSubmitResult = {
        result: {
          is_correct: true,
          correct_answer: 1,
          explanation: '정답입니다',
        },
      };

      vi.mocked(fetch)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockQuestion,
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockSubmitResult,
        } as Response);

      // 문제 조회 및 답안 제출 플로우
      const question = await examAPI.getQuestion(1);
      expect(question).not.toBeNull();

      if (question) {
        const result = await examAPI.submitAnswer(question.id, 1, 5.0);
        expect(result).not.toBeNull();
        expect(result?.is_correct).toBe(true);
      }
    });
  });

  describe('VocabAPI Integration', () => {
    it('should fetch vocab and mark as learned', async () => {
      const mockVocab = {
        vocab: [
          {
            id: 1,
            word: '테스트',
            meaning: '테스트 의미',
            example: '테스트 예문',
            queue_id: 1,
          },
        ],
        sisa: [],
      };

      const mockMarkLearned = {
        ok: true,
        message: '학습 완료 처리되었습니다',
      };

      vi.mocked(fetch)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockVocab,
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockMarkLearned,
        } as Response);

      // 어휘 조회 및 학습 완료 플로우
      const data = await vocabAPI.getTodayVocab();
      expect(data).not.toBeNull();
      expect(data?.vocab).toHaveLength(1);

      if (data && data.vocab.length > 0) {
        const success = await vocabAPI.markLearned(data.vocab[0].queue_id, 3);
        expect(success).toBe(true);
      }
    });
  });
});


