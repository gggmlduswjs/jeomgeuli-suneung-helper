// src/pages/NotFound.tsx
import { useEffect, useRef } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import AppShellMobile from "../components/ui/AppShellMobile";
import { Home, ArrowLeft, Search } from "lucide-react";

export default function NotFound() {
  const h1Ref = useRef<HTMLHeadingElement>(null);
  const navigate = useNavigate();
  const { pathname } = useLocation();

  // 접근성: 진입 시 제목에 포커스
  useEffect(() => {
    h1Ref.current?.focus();
  }, []);

  return (
    <AppShellMobile title="페이지 없음" showBackButton>
      <div className="text-center space-y-6">
        <div className="text-6xl" aria-hidden>😵‍💫</div>

        <h1
          ref={h1Ref}
          tabIndex={-1}
          className="h2"
          aria-label="페이지를 찾을 수 없어요"
        >
          페이지를 찾을 수 없어요
        </h1>

        <p className="text-secondary break-all">
          요청 경로:{" "}
          <code className="px-2 py-1 bg-card rounded border border-border">
            {pathname}
          </code>
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <button
            onClick={() => navigate(-1)}
            className="btn-ghost flex items-center justify-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" aria-hidden />
            이전 페이지
          </button>

          <Link to="/" className="btn-primary flex items-center justify-center gap-2">
            <Home className="w-4 h-4" aria-hidden />
            홈으로
          </Link>

          <Link to="/explore" className="btn-accent flex items-center justify-center gap-2">
            <Search className="w-4 h-4" aria-hidden />
            정보 탐색
          </Link>
        </div>

        <div className="text-xs text-muted">
          계속 문제가 발생하면 네트워크 연결 또는 환경변수{" "}
          <code>VITE_API_BASE_URL</code> 설정을 확인하세요.
        </div>
      </div>
    </AppShellMobile>
  );
}
