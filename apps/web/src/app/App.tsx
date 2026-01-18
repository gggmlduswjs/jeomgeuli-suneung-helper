import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Suspense, useEffect, useRef } from "react";
import ErrorBoundary from "../components/system/ErrorBoundary";
import GlobalVoiceRecognition from "../components/input/GlobalVoiceRecognition";
import PerformanceMonitor from "../components/system/PerformanceMonitor";
import DevHealth from "../components/system/DevHealth";
import HealthCheck from "../components/system/HealthCheck";
import VoiceRecognitionDebug from "../components/debug/VoiceRecognitionDebug";
import { routes, legacyRedirects, legacyRoutes, notFoundRoute } from "./routes";

// Loading component
const PageLoader = () => (
  <div className="flex items-center justify-center min-h-screen" role="status" aria-label="페이지 로딩 중">
    <div className="text-lg">로딩 중...</div>
  </div>
);

export default function App(){
  // 개발 헬스 기록
  (window as any).__APP_HEALTH__ = { ...(window as any).__APP_HEALTH__, appMounted: true };
  console.log("[APP] mounted", (window as any).__APP_HEALTH__);

  // 전역 마이크 모드 시 모든 미디어 볼륨/재생 제어 (추가 음소거)
  const pausedMediaRef = useRef<HTMLMediaElement[]>([]);
  const volumeMapRef = useRef<Map<HTMLMediaElement, number>>(new Map());
  useEffect(() => {
    const onMicMode = (e: Event) => {
      const active = !!(e as CustomEvent)?.detail?.active;
      try {
        const media = Array.from(document.querySelectorAll('audio,video')) as HTMLMediaElement[];
        if (active) {
          pausedMediaRef.current = [];
          volumeMapRef.current.clear();
          media.forEach(m => {
            // 저장 후 즉시 음소거 및 일시정지
            if (!volumeMapRef.current.has(m)) volumeMapRef.current.set(m, m.volume);
            m.volume = 0;
            if (!m.paused && !m.ended) {
              try { m.pause(); pausedMediaRef.current.push(m); } catch {}
            }
          });
        } else {
          // 복귀: 볼륨 복원(일단 0→원래값), 필요 시 재생 복귀는 스킵
          media.forEach(m => {
            const prev = volumeMapRef.current.get(m);
            if (typeof prev === 'number') {
              m.volume = prev;
            }
          });
          volumeMapRef.current.clear();
          pausedMediaRef.current = [];
        }
      } catch {}
    };
    window.addEventListener('voice:mic-mode', onMicMode as EventListener);
    return () => window.removeEventListener('voice:mic-mode', onMicMode as EventListener);
  }, []);

  return (
    <ErrorBoundary>
      <HealthCheck>
        <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
          {import.meta.env.DEV && <DevHealth />}
          {import.meta.env.DEV && <PerformanceMonitor />}
          {import.meta.env.DEV && <VoiceRecognitionDebug />}
          {/* 전역 음성 인식: 모든 페이지에서 화면을 길게 누르면 음성 인식 시작 */}
          <GlobalVoiceRecognition />
          <Suspense fallback={<PageLoader />}>
            <Routes>
              {/* 메인 라우트 */}
              {routes.map((route) => (
                <Route key={route.path} path={route.path} element={<route.element />} />
              ))}
              
              {/* 레거시 라우트 리다이렉트 */}
              {legacyRedirects.map((redirect) => (
                <Route 
                  key={redirect.from} 
                  path={redirect.from} 
                  element={<Navigate to={redirect.to} replace />} 
                />
              ))}

              {/* 레거시 라우트 (제거 예정) */}
              {legacyRoutes.map((route) => (
                <Route key={route.path} path={route.path} element={<route.element />} />
              ))}

              {/* 404 라우트 */}
              <Route path={notFoundRoute.path} element={<notFoundRoute.element />} />
            </Routes>
          </Suspense>
        </BrowserRouter>
      </HealthCheck>
    </ErrorBoundary>
  );
}