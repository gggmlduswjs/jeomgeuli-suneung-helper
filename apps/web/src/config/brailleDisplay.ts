/**
 * 점자 디스플레이 설정 시스템
 * 확장 가능한 구조로 설계 (3-cell → 6-cell → 12-cell 등)
 */

export interface BrailleDisplayConfig {
  maxCells: number; // 3, 6, 12, 20 등 확장 가능
  scrollMode: 'auto' | 'manual'; // 자동 스크롤 vs 수동 제어
  chunkStrategy: 'word' | 'sentence' | 'smart'; // 청크 분할 전략
}

export const DEFAULT_BRAILLE_CONFIG: BrailleDisplayConfig = {
  maxCells: 3,
  scrollMode: 'manual',
  chunkStrategy: 'smart',
};

const STORAGE_KEY = 'braille_display_config';

/**
 * 설정 저장소 (localStorage)
 */
export const brailleDisplayConfig = {
  /**
   * 설정 조회
   */
  get(): BrailleDisplayConfig {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        // 기본값과 병합하여 누락된 필드 보완
        return { ...DEFAULT_BRAILLE_CONFIG, ...parsed };
      }
    } catch (error) {
      console.error('[BrailleDisplayConfig] Failed to load config:', error);
    }
    return { ...DEFAULT_BRAILLE_CONFIG };
  },

  /**
   * 설정 저장
   */
  set(config: Partial<BrailleDisplayConfig>): void {
    try {
      const current = this.get();
      const merged = { ...current, ...config };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(merged));
    } catch (error) {
      console.error('[BrailleDisplayConfig] Failed to save config:', error);
    }
  },

  /**
   * 설정 초기화
   */
  reset(): void {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (error) {
      console.error('[BrailleDisplayConfig] Failed to reset config:', error);
    }
  },
};

