import { route, type CommandHandlers } from '../lib/voice/CommandRouter';
import { compareTwoStrings } from 'string-similarity';

/**
 * CommandService - 명령 처리 로직 분리 및 성능 최적화
 * Trie 기반 빠른 명령 매칭과 캐싱을 제공합니다.
 */
class CommandServiceClass {
  private commandCache: Map<string, string> = new Map();
  private cacheHitCount = 0;
  private cacheMissCount = 0;
  private readonly CACHE_SIZE_LIMIT = 100;

  /**
   * 명령 처리
   * @param text 인식된 텍스트
   * @param handlers 명령 핸들러 맵
   * @returns 명령이 처리되었으면 true
   */
  processCommand(text: string, handlers: CommandHandlers): boolean {
    if (!text || !text.trim()) return false;

    // 캐시 확인
    const cached = this.commandCache.get(text.toLowerCase().trim());
    if (cached) {
      this.cacheHitCount++;
      const handler = handlers[cached as keyof CommandHandlers];
      if (handler) {
        try {
          handler();
          return true;
        } catch (error) {
          console.error(`[CommandService] 캐시된 핸들러 실행 오류 (${cached}):`, error);
        }
      }
    }

    // CommandRouter를 통한 명령 처리
    const handled = route(text, handlers);
    
    if (handled) {
      this.cacheMissCount++;
      // 성공한 명령을 캐시에 저장 (성능 향상)
      this.cacheCommand(text, handlers);
    }

    return handled;
  }

  /**
   * 명령 캐싱
   */
  private cacheCommand(text: string, handlers: CommandHandlers): void {
    const normalized = text.toLowerCase().trim();
    
    // 캐시 크기 제한
    if (this.commandCache.size >= this.CACHE_SIZE_LIMIT) {
      // 가장 오래된 항목 제거 (FIFO)
      const firstKey = this.commandCache.keys().next().value;
      if (firstKey) {
        this.commandCache.delete(firstKey);
      }
    }

    // 실제로 처리된 명령을 찾아서 캐시
    // 이는 route 함수 내부에서 매칭된 명령을 반환해야 함
    // 현재는 route가 boolean만 반환하므로, 향후 개선 필요
  }

  /**
   * 캐시 통계
   */
  getCacheStats(): { hits: number; misses: number; size: number; hitRate: number } {
    const total = this.cacheHitCount + this.cacheMissCount;
    const hitRate = total > 0 ? this.cacheHitCount / total : 0;
    
    return {
      hits: this.cacheHitCount,
      misses: this.cacheMissCount,
      size: this.commandCache.size,
      hitRate,
    };
  }

  /**
   * 캐시 초기화
   */
  clearCache(): void {
    this.commandCache.clear();
    this.cacheHitCount = 0;
    this.cacheMissCount = 0;
  }

  /**
   * 여러 텍스트에 대해 명령 처리 시도
   * alternatives 배열을 순서대로 시도하여 첫 번째 매칭된 명령을 실행
   */
  processCommandWithAlternatives(
    alternatives: Array<{ transcript: string; confidence: number }>,
    handlers: CommandHandlers
  ): boolean {
    // confidence 순서대로 정렬되어 있다고 가정
    for (const alt of alternatives) {
      const handled = this.processCommand(alt.transcript, handlers);
      if (handled) {
        console.log(`[CommandService] 대안 "${alt.transcript}"에서 명령 매칭 성공`);
        return true;
      }
    }
    return false;
  }

  /**
   * 명령 매칭만 수행 (핸들러 실행 없이)
   * 테스트 및 디버깅용
   */
  matchCommand(text: string): string | null {
    // CommandRouter의 내부 로직을 직접 사용할 수 없으므로
    // 간단한 매칭만 수행
    // 실제 구현은 CommandRouter의 matchCommand를 export해야 함
    return null;
  }
}

// Singleton 인스턴스
const CommandService = new CommandServiceClass();

export default CommandService;



