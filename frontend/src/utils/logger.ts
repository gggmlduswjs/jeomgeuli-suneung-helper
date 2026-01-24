/**
 * 로깅 유틸리티
 * 개발 환경에서만 로그를 출력하고, 프로덕션에서는 제거
 */

type LogLevel = 'log' | 'warn' | 'error' | 'info' | 'debug';

interface Logger {
  log: (...args: unknown[]) => void;
  warn: (...args: unknown[]) => void;
  error: (...args: unknown[]) => void;
  info: (...args: unknown[]) => void;
  debug: (...args: unknown[]) => void;
}

const isDevelopment = import.meta.env.DEV;

/**
 * 로거 인스턴스 생성
 * @param prefix - 로그 접두사 (예: 'VoiceService', 'API', 'Store')
 */
function createLogger(prefix: string): Logger {
  const formatMessage = (level: LogLevel, ...args: unknown[]): unknown[] => {
    return [`[${prefix}]`, `[${level.toUpperCase()}]`, ...args];
  };

  return {
    log: (...args: unknown[]) => {
      if (isDevelopment) {
        console.log(...formatMessage('log', ...args));
      }
    },
    warn: (...args: unknown[]) => {
      if (isDevelopment) {
        console.warn(...formatMessage('warn', ...args));
      }
    },
    error: (...args: unknown[]) => {
      // 에러는 프로덕션에서도 출력 (모니터링용)
      console.error(...formatMessage('error', ...args));
    },
    info: (...args: unknown[]) => {
      if (isDevelopment) {
        console.info(...formatMessage('info', ...args));
      }
    },
    debug: (...args: unknown[]) => {
      if (isDevelopment) {
        console.debug(...formatMessage('debug', ...args));
      }
    },
  };
}

/**
 * 기본 로거
 */
export const logger = createLogger('App');

/**
 * 모듈별 로거 생성 함수
 */
export function createModuleLogger(moduleName: string): Logger {
  return createLogger(moduleName);
}
