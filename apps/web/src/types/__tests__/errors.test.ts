import { describe, it, expect } from 'vitest';
import { createError, ErrorCode, isAppError, toAppError } from '../errors';

describe('Error Handling', () => {
  describe('createError', () => {
    it('should create AppError with correct structure', () => {
      const error = createError(ErrorCode.NETWORK_ERROR, 'Network failed');
      
      expect(error.code).toBe(ErrorCode.NETWORK_ERROR);
      expect(error.message).toBe('Network failed');
      expect(error.userMessage).toBeTruthy();
      expect(error.timestamp).toBeGreaterThan(0);
    });

    it('should generate user-friendly messages', () => {
      const networkError = createError(ErrorCode.NETWORK_ERROR, 'Network error');
      expect(networkError.userMessage).toContain('네트워크');

      const timeoutError = createError(ErrorCode.TIMEOUT_ERROR, 'Timeout');
      expect(timeoutError.userMessage).toContain('시간이 초과');

      const sttError = createError(ErrorCode.STT_ERROR, 'Permission denied');
      expect(sttError.userMessage).toContain('마이크');
    });

    it('should include optional status and data', () => {
      const error = createError(
        ErrorCode.API_ERROR,
        'API error',
        undefined,
        { status: 404, data: { detail: 'Not found' } }
      );
      
      expect(error.status).toBe(404);
      expect(error.data).toEqual({ detail: 'Not found' });
    });
  });

  describe('isAppError', () => {
    it('should identify AppError correctly', () => {
      const appError = createError(ErrorCode.NETWORK_ERROR, 'Test');
      expect(isAppError(appError)).toBe(true);
    });

    it('should reject non-AppError objects', () => {
      expect(isAppError(new Error('test'))).toBe(false);
      expect(isAppError('string')).toBe(false);
      expect(isAppError(null)).toBe(false);
      expect(isAppError(undefined)).toBe(false);
    });
  });

  describe('toAppError', () => {
    it('should convert Error to AppError', () => {
      const error = new Error('Test error');
      const appError = toAppError(error);
      
      expect(isAppError(appError)).toBe(true);
      expect(appError.message).toBe('Test error');
    });

    it('should detect timeout errors', () => {
      const abortError = new Error('Aborted');
      abortError.name = 'AbortError';
      const appError = toAppError(abortError);
      
      expect(appError.code).toBe(ErrorCode.TIMEOUT_ERROR);
    });

    it('should detect network errors', () => {
      const networkError = new Error('Failed to fetch');
      const appError = toAppError(networkError);
      
      expect(appError.code).toBe(ErrorCode.NETWORK_ERROR);
    });

    it('should handle unknown types', () => {
      const appError = toAppError('string error');
      expect(isAppError(appError)).toBe(true);
      expect(appError.code).toBe(ErrorCode.UNKNOWN_ERROR);
    });

    it('should return AppError as-is', () => {
      const original = createError(ErrorCode.API_ERROR, 'Original');
      const converted = toAppError(original);
      
      expect(converted).toBe(original);
    });
  });
});

