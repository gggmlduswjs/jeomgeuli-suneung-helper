/**
 * 통일된 에러 타입 정의
 * 모든 에러를 일관된 형식으로 처리하기 위한 타입 시스템
 */

export enum ErrorCode {
  NETWORK_ERROR = 'NETWORK_ERROR',
  TIMEOUT_ERROR = 'TIMEOUT_ERROR',
  API_ERROR = 'API_ERROR',
  STT_ERROR = 'STT_ERROR',
  TTS_ERROR = 'TTS_ERROR',
  BLE_ERROR = 'BLE_ERROR',
  UNKNOWN_ERROR = 'UNKNOWN_ERROR',
}

export interface AppError {
  code: ErrorCode;
  message: string;
  userMessage: string; // 사용자에게 보여줄 메시지
  originalError?: Error | unknown;
  timestamp: number;
  status?: number; // HTTP 상태 코드 (있는 경우)
  data?: unknown; // 추가 에러 데이터
}

/**
 * 에러 생성 함수
 */
export function createError(
  code: ErrorCode,
  message: string,
  originalError?: Error | unknown,
  options?: {
    status?: number;
    data?: unknown;
  }
): AppError {
  return {
    code,
    message,
    userMessage: getUserFriendlyMessage(code, message),
    originalError,
    timestamp: Date.now(),
    status: options?.status,
    data: options?.data,
  };
}

/**
 * 사용자 친화적 메시지 생성
 */
function getUserFriendlyMessage(code: ErrorCode, message: string): string {
  switch (code) {
    case ErrorCode.NETWORK_ERROR:
      return '네트워크 연결을 확인해주세요.';
    case ErrorCode.TIMEOUT_ERROR:
      return '요청 시간이 초과되었습니다. 다시 시도해주세요.';
    case ErrorCode.API_ERROR:
      // API 에러는 원본 메시지를 사용하되, 사용자 친화적으로 변환
      if (message.includes('404')) {
        return '요청한 정보를 찾을 수 없습니다.';
      }
      if (message.includes('500')) {
        return '서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.';
      }
      if (message.includes('429')) {
        return '요청이 너무 많습니다. 잠시 후 다시 시도해주세요.';
      }
      return message || '요청 처리 중 오류가 발생했습니다.';
    case ErrorCode.STT_ERROR:
      if (message.includes('권한')) {
        return '마이크 권한이 필요합니다. 브라우저 설정에서 마이크 권한을 허용해주세요.';
      }
      if (message.includes('감지')) {
        return '음성이 감지되지 않았습니다. 다시 말씀해주세요.';
      }
      return '음성 인식에 실패했습니다. 다시 시도해주세요.';
    case ErrorCode.TTS_ERROR:
      return '음성 재생에 실패했습니다.';
    case ErrorCode.BLE_ERROR:
      return '블루투스 연결에 실패했습니다.';
    default:
      return '오류가 발생했습니다. 잠시 후 다시 시도해주세요.';
  }
}

/**
 * 에러가 AppError인지 확인
 */
export function isAppError(error: unknown): error is AppError {
  return (
    typeof error === 'object' &&
    error !== null &&
    'code' in error &&
    'message' in error &&
    'userMessage' in error &&
    'timestamp' in error
  );
}

/**
 * 알 수 없는 에러를 AppError로 변환
 */
export function toAppError(error: unknown): AppError {
  if (isAppError(error)) {
    return error;
  }

  if (error instanceof Error) {
    // 네트워크 에러인지 확인
    if (error.name === 'AbortError' || error.message.includes('timeout')) {
      return createError(ErrorCode.TIMEOUT_ERROR, error.message, error);
    }
    if (error.message.includes('network') || error.message.includes('fetch')) {
      return createError(ErrorCode.NETWORK_ERROR, error.message, error);
    }
    return createError(ErrorCode.UNKNOWN_ERROR, error.message, error);
  }

  return createError(
    ErrorCode.UNKNOWN_ERROR,
    String(error),
    error
  );
}
