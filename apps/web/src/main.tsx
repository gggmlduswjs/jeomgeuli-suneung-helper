import React, { Suspense } from "react";
import ReactDOM from "react-dom/client";
import App from "./app/App";
import ErrorBoundary from "./components/system/ErrorBoundary";
import "./index.css";

const containerId = "root";
let container = document.getElementById(containerId);

// 컨테이너가 없으면 생성 (안전하게)
if (!container) {
  container = document.createElement("div");
  container.id = containerId;
  // 중복 체크 후 추가
  if (!document.getElementById(containerId)) {
    document.body.appendChild(container);
  } else {
    container = document.getElementById(containerId)!;
  }
}

const Fallback = () => <div style={{ padding:16 }}>로딩 중...</div>;

// 전역 헬스 체크 초기화
(window as any).__APP_HEALTH__ = { 
  buildTime: new Date().toISOString(),
  cssLoaded: true,
  routesReady: false,
  appMounted: false
};

// 기존 root가 있으면 unmount 후 재생성 (안전하게)
let root: ReactDOM.Root;
try {
  // container가 유효한지 확인
  if (container && container.parentNode) {
    root = ReactDOM.createRoot(container);
    root.render(
      <React.StrictMode>
        <ErrorBoundary>
          <Suspense fallback={<Fallback />}>
            <App />
          </Suspense>
        </ErrorBoundary>
      </React.StrictMode>
    );
  } else {
    console.error("Container is not attached to DOM");
  }
} catch (error) {
  console.error("Failed to render app:", error);
}

// Service worker disabled for development
// if ("serviceWorker" in navigator) {
//   window.addEventListener("load", () => {
//     navigator.serviceWorker.register("/sw.js").catch(()=>{});
//   });
// }
