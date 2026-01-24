/**
 * Vitest 테스트 설정 파일
 * 모든 테스트 실행 전에 로드됩니다
 */

import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';

// 각 테스트 후 자동 정리
afterEach(() => {
  cleanup();
});

// 커스텀 매처 추가 (필요시)
// expect.extend({
//   toBeWithinRange(received, floor, ceiling) {
//     const pass = received >= floor && received <= ceiling;
//     return {
//       pass,
//       message: () => `expected ${received} to be within range ${floor} - ${ceiling}`,
//     };
//   },
// });
