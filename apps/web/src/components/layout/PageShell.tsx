/**
 * 페이지 공통 레이아웃 컴포넌트
 * AppShellMobile + SpeechBar + ToastA11y 통합
 * 
 * 사용법:
 * <PageShell title="페이지 제목" loading={loading} error={error} pageOptions={{...}}>
 *   페이지 내용
 * </PageShell>
 */
import AppShellMobile from '../ui/AppShellMobile';
import SpeechBar from '../input/SpeechBar';
import ToastA11y from '../system/ToastA11y';
import { usePageBase, type UsePageBaseOptions } from '../../hooks/usePageBase';
import { useNavigate } from 'react-router-dom';
import { useEffect, useMemo } from 'react';

interface PageShellProps {
  title: string;
  children: React.ReactNode;
  className?: string;
  showBackButton?: boolean;
  pageOptions?: Omit<UsePageBaseOptions, 'voiceCommands'> & {
    voiceCommands?: UsePageBaseOptions['voiceCommands'];
  };
  loading?: boolean;
  error?: string | null;
  onError?: (error: string) => void;
  /** 커스텀 로딩 컴포넌트 */
  loadingComponent?: React.ReactNode;
  /** 커스텀 에러 컴포넌트 */
  errorComponent?: React.ReactNode;
  /** children을 항상 렌더링 (로딩/에러 상태와 무관) */
  alwaysRenderChildren?: boolean;
}

export default function PageShell({
  title,
  children,
  className,
  showBackButton,
  pageOptions = {},
  loading,
  error,
  onError,
  loadingComponent,
  errorComponent,
  alwaysRenderChildren = false,
}: PageShellProps) {
  const navigate = useNavigate();
  
  // 음성 명령어에 기본 home 명령 추가
  const mergedVoiceCommands = useMemo(() => ({
    home: () => {
      navigate('/');
    },
    ...pageOptions.voiceCommands,
  }), [navigate, pageOptions.voiceCommands]);

  const {
    speak,
    stopTTS,
    stopSTT,
    isListening,
    transcript,
    showToast,
    toastMessage,
    setShowToast,
  } = usePageBase({
    ...pageOptions,
    voiceCommands: mergedVoiceCommands,
  });

  // 에러가 있으면 음성으로 안내
  useEffect(() => {
    if (error && onError) {
      onError(error);
    } else if (error) {
      speak(error);
    }
  }, [error, speak, onError]);

  const defaultLoadingComponent = (
    <div className="text-center py-8">
      <p className="text-muted">로딩 중...</p>
    </div>
  );

  const defaultErrorComponent = error ? (
    <div className="bg-error/10 border border-error rounded-lg p-4 mb-4">
      <p className="text-error">{error}</p>
    </div>
  ) : null;

  return (
    <AppShellMobile title={title} className={className} showBackButton={showBackButton}>
      <div className="mb-4">
        <SpeechBar isListening={isListening} transcript={transcript} />
      </div>

      <div className="p-4">
        {loading && !alwaysRenderChildren && (loadingComponent || defaultLoadingComponent)}
        {error && !alwaysRenderChildren && (errorComponent || defaultErrorComponent)}
        
        {(alwaysRenderChildren || (!loading && !error)) && (
          <>
            {error && alwaysRenderChildren && (errorComponent || defaultErrorComponent)}
            {children}
          </>
        )}
      </div>

      <ToastA11y
        message={toastMessage}
        isVisible={showToast}
        duration={3000}
        onClose={() => setShowToast(false)}
      />
    </AppShellMobile>
  );
}
