/**
 * API 클라이언트 기본 설정
 */
const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1초

export interface ApiError {
  detail?: string;
  message?: string;
  error?: string;
}

/**
 * 재시도 가능한 네트워크 에러인지 확인
 */
function isRetryableError(error: unknown): boolean {
  if (error instanceof TypeError) {
    // 네트워크 에러 (fetch 실패)
    return error.message.includes('fetch') || error.message.includes('network');
  }
  if (error instanceof Error) {
    // 연결 관련 에러
    return error.message.includes('ECONNRESET') || 
           error.message.includes('ECONNREFUSED') ||
           error.message.includes('Failed to fetch');
  }
  return false;
}

/**
 * 재시도 로직이 포함된 fetch 래퍼
 */
async function fetchWithRetry<T>(
  fetchFn: () => Promise<Response>,
  retries: number = MAX_RETRIES
): Promise<T> {
  try {
    const response = await fetchFn();
    if (!response.ok) {
      const error: ApiError = await response.json().catch(() => ({
        detail: `HTTP ${response.status}`,
      }));
      throw new Error(error.detail || error.message || error.error || 'API 요청 실패');
    }
    return response.json();
  } catch (error) {
    // 재시도 가능한 에러이고 재시도 횟수가 남아있으면 재시도
    if (isRetryableError(error) && retries > 0) {
      if (import.meta.env.DEV) {
        console.warn(`[API] 재시도 중... (남은 횟수: ${retries})`, error);
      }
      await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
      return fetchWithRetry(fetchFn, retries - 1);
    }
    // 재시도 불가능하거나 재시도 횟수 초과
    throw error;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error: ApiError = await response.json().catch(() => ({
      detail: `HTTP ${response.status}`,
    }));
    throw new Error(error.detail || error.message || error.error || 'API 요청 실패');
  }
  return response.json();
}

export const api = {
  get: async <T>(path: string): Promise<T> => {
    return fetchWithRetry<T>(() => fetch(`${API_BASE}${path}`));
  },

  post: async <T>(path: string, body?: any): Promise<T> => {
    return fetchWithRetry<T>(() => fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: body ? JSON.stringify(body) : undefined,
    }));
  },

  postFormData: async <T>(path: string, formData: FormData): Promise<T> => {
    return fetchWithRetry<T>(() => fetch(`${API_BASE}${path}`, {
      method: 'POST',
      body: formData,
    }));
  },
};
