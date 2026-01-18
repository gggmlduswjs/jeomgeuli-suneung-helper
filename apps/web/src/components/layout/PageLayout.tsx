/**
 * 페이지 레이아웃 컴포넌트
 * 공통 레이아웃 구조를 통합하여 제공
 */
import { ReactNode } from 'react';
import AppShellMobile from '../ui/AppShellMobile';
import SpeechBar from '../input/SpeechBar';
import ToastA11y from '../system/ToastA11y';
import { usePageBase, type UsePageBaseOptions } from '../../hooks/usePageBase';

export interface PageLayoutProps {
  /** 페이지 제목 */
  title: string;
  /** 페이지 내용 */
  children: ReactNode;
  /** 뒤로가기 버튼 표시 여부 */
  showBackButton?: boolean;
  /** 뒤로가기 핸들러 */
  onBack?: () => void;
  /** 추가 CSS 클래스 */
  className?: string;
  /** usePageBase 옵션 */
  pageBaseOptions?: UsePageBaseOptions;
}

/**
 * 페이지 레이아웃 컴포넌트
 * 공통 레이아웃 구조를 제공합니다.
 */
export function PageLayout({
  title,
  children,
  showBackButton = false,
  onBack,
  className = '',
  pageBaseOptions = {},
}: PageLayoutProps) {
  const {
    isListening,
    transcript,
    showToast,
    toastMessage,
    setShowToast,
  } = usePageBase(pageBaseOptions);
  
  return (
    <AppShellMobile 
      title={title} 
      showBackButton={showBackButton} 
      onBack={onBack}
      className={className}
    >
      {pageBaseOptions.showSpeechBar !== false && (
        <div className="mb-4">
          <SpeechBar 
            isListening={isListening} 
            transcript={transcript} 
          />
        </div>
      )}
      {children}
      <ToastA11y
        message={toastMessage}
        isVisible={showToast}
        duration={3000}
        onClose={() => setShowToast(false)}
      />
    </AppShellMobile>
  );
}

