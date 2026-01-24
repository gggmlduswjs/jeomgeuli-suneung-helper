import { useEffect, useState } from 'react';
import { http } from '@/lib/http';

interface HealthCheckProps {
  children: React.ReactNode;
}

interface HealthCheckResponse {
  ok?: boolean;
  status?: string;
}

export default function HealthCheck({ children }: HealthCheckProps) {
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const result = await http.get<HealthCheckResponse>('/health');
        setIsHealthy(result?.ok === true || result?.status === 'healthy');
        setError(null);
      } catch (e: unknown) {
        setIsHealthy(false);
        setError(e instanceof Error ? e.message : 'Health check failed');
        if (import.meta.env.DEV) {
          console.error('[HealthCheck] API health check failed:', e);
        }
      }
    };

    checkHealth();
  }, []);

  // Show loading state
  if (isHealthy === null) {
    return (
      <div className="min-h-screen bg-bg text-fg flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-muted">초기화 중...</p>
        </div>
      </div>
    );
  }

  // Show error state
  if (isHealthy === false) {
    return (
      <div className="min-h-screen bg-bg text-fg flex items-center justify-center">
        <div className="max-w-md mx-auto p-6 text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-2xl">⚠️</span>
          </div>
          <h1 className="text-xl font-bold text-red-600 mb-2">연결 실패</h1>
          <p className="text-muted mb-4">
            백엔드 서버에 연결할 수 없습니다.
          </p>
          <p className="text-sm text-gray-500 mb-4">
            {error}
          </p>
          <div className="text-sm text-gray-500">
            <p>개발 서버와 백엔드 API가 실행 중인지 확인하세요:</p>
            <ul className="mt-2 text-left">
              <li>• 백엔드: <code className="bg-gray-100 px-1 rounded">cd api && uvicorn app.main:app --reload</code></li>
              <li>• 프론트엔드: <code className="bg-gray-100 px-1 rounded">npm run dev</code></li>
            </ul>
          </div>
          <button 
            onClick={() => window.location.reload()} 
            className="mt-4 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
          >
            다시 시도
          </button>
        </div>
      </div>
    );
  }

  // Show app content when healthy
  return <>{children}</>;
}
