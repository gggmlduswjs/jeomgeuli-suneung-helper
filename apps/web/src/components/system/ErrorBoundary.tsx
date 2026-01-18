import React, { Component, ReactNode } from "react";

type Props = {
  children: ReactNode;
  /** 커스텀 폴백 UI를 주고 싶을 때 사용 */
  fallback?: ReactNode;
  /** 복구 시도(리셋) 시 호출되는 콜백 */
  onReset?: () => void;
};

type State = { hasError: boolean; error: Error | null };

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(err: unknown): Partial<State> {
    // any -> unknown, Error 인스턴스로 정규화
    const error = err instanceof Error ? err : new Error(String(err));
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    // 진단 로그
    console.error("[ErrorBoundary] Caught:", error, info);

    // SSR/테스트 환경 가드
    if (typeof window !== "undefined") {
      (window as any).__APP_HEALTH__ = {
        ...(window as any).__APP_HEALTH__,
        lastError: String(error?.message ?? error),
        lastErrorInfo: info?.componentStack,
      };
    }
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
    try {
      this.props.onReset?.();
    } catch {
      /* no-op */
    }
  };

  render() {
    if (this.state.hasError) {
      // 커스텀 폴백 제공 시 그대로 노출
      if (this.props.fallback) return <>{this.props.fallback}</>;

      const isDev = Boolean((import.meta as any)?.env?.DEV);

      return (
        <div
          style={{ padding: 16 }}
          role="alert"
          aria-live="assertive"
          aria-atomic="true"
        >
          <h1 style={{ fontSize: 20, marginBottom: 8 }}>
            앱에서 오류가 발생했어요.
          </h1>
          <p style={{ marginBottom: 12 }}>
            콘솔(F12)을 열어 상세 오류를 확인해 주세요.
          </p>

          {/* 개발 모드에서 에러 메시지/스택 힌트 제공 */}
          {isDev && this.state.error && (
            <details
              style={{
                marginBottom: 12,
                background: "#f8fafc",
                border: "1px solid #e2e8f0",
                borderRadius: 8,
                padding: 12,
                whiteSpace: "pre-wrap",
                fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
                fontSize: 12,
                color: "#334155",
              }}
            >
              <summary>오류 상세</summary>
              {this.state.error.stack ?? String(this.state.error)}
            </details>
          )}

          <div style={{ display: "flex", gap: 8 }}>
            <button
              type="button"
              onClick={this.handleReset}
              style={{
                padding: "8px 12px",
                borderRadius: 8,
                border: "1px solid #cbd5e1",
                background: "#ffffff",
                cursor: "pointer",
              }}
            >
              복구 시도
            </button>

            <button
              type="button"
              onClick={() => {
                if (typeof window !== "undefined") {
                  window.location.reload();
                }
              }}
              style={{
                padding: "8px 12px",
                borderRadius: 8,
                border: "1px solid #0284c7",
                background: "#0ea5e9",
                color: "#fff",
                cursor: "pointer",
              }}
            >
              새로고침
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
