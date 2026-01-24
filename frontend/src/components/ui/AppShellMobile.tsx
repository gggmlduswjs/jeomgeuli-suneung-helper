import React, { useState } from 'react';
import { ArrowLeft, Volume2, VolumeX, Home, BookOpen, BookMarked, Timer } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';

interface AppShellMobileProps {
  title?: string;
  showBackButton?: boolean;
  onBack?: () => void;
  children: React.ReactNode;
  className?: string;
  showHeader?: boolean;  // 헤더 표시 여부
  showFooter?: boolean;  // 푸터 표시 여부
}

export default function AppShellMobile({
  title = '',
  showBackButton = false,
  onBack,
  children,
  className = '',
  showHeader = false,  // 기본값: 헤더 숨김
  showFooter = false,  // 기본값: 푸터 숨김
}: AppShellMobileProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const [isTTSEnabled, setIsTTSEnabled] = useState(true);

  const handleBack = () => {
    if (onBack) onBack();
    else navigate(-1);
  };

  // 사용처가 생길 수 있어 남겨두되 안전 가드 추가
  // const _speakText = (text: string) => {
  //   if (!isTTSEnabled) return;
  //   if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
  //     window.speechSynthesis.cancel();
  //     const utterance = new SpeechSynthesisUtterance(text);
  //     utterance.lang = 'ko-KR';
  //     utterance.rate = 0.9;
  //     utterance.volume = 1.0;
  //     window.speechSynthesis.speak(utterance);
  //   }
  // };

  const toggleTTS = () => {
    setIsTTSEnabled((prev) => {
      const next = !prev;
      if (!next && typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
      return next;
    });
  };

  const isActive = (path: string) => location.pathname === path;

  // 네비게이션 버튼 컴포넌트
  const NavButton = ({
    icon: Icon,
    label,
    onClick,
    isActive,
    ariaLabel,
    ariaCurrent
  }: {
    icon: React.ComponentType<{ className?: string }>;
    label: string;
    onClick: () => void;
    isActive: boolean;
    ariaLabel: string;
    ariaCurrent?: 'page' | undefined;
  }) => (
    <button
      type="button"
      onClick={onClick}
      className="relative flex flex-col items-center justify-center px-2 py-2.5 min-w-[52px] rounded-xl transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary/50 active:scale-95 group touch-manipulation"
      aria-label={ariaLabel}
      aria-current={ariaCurrent}
    >
      {/* 활성 상태 배경 */}
      {isActive && (
        <div className="absolute inset-0 rounded-xl bg-gradient-to-b from-primary/8 via-primary/5 to-transparent" />
      )}
      
      {/* 호버 배경 */}
      {!isActive && (
        <div className="absolute inset-0 rounded-xl bg-card/80 opacity-0 group-hover:opacity-100 transition-opacity duration-200" />
      )}
      
      {/* 활성 상태 상단 인디케이터 바 */}
      {isActive && (
        <div className="absolute top-0 left-1/2 transform -translate-x-1/2 w-7 h-0.5 bg-primary rounded-full" />
      )}
      
      {/* 아이콘 */}
      <div className={`relative z-10 mb-1 transition-all duration-200 ${
        isActive ? 'scale-110' : 'scale-100 group-hover:scale-105'
      }`}>
        <Icon 
          className={`w-5 h-5 transition-colors duration-200 ${
            isActive 
              ? 'text-primary drop-shadow-sm' 
              : 'text-muted/60 group-hover:text-fg/80'
          }`} 
          aria-hidden="true" 
        />
      </div>
      
      {/* 라벨 */}
      <span 
        className={`text-[10px] font-medium transition-all duration-200 relative z-10 leading-tight ${
          isActive 
            ? 'text-primary font-semibold' 
            : 'text-muted/60 group-hover:text-fg/70'
        }`}
      >
        {label}
      </span>
    </button>
  );

  return (
    <div className={`min-h-screen bg-bg text-fg flex flex-col ${className}`}>
      {/* 상단 헤더 - 선택적 표시 */}
      {showHeader && (
      <header 
        className="sticky top-0 z-50 backdrop-blur-xl border-b border-border/50 shadow-soft"
        style={{ background: 'linear-gradient(180deg, rgba(249, 250, 251, 0.8) 0%, rgba(255, 255, 255, 1) 100%)' }}
      >
        <div className="w-full md:max-w-md md:mx-auto">
          <div className="flex items-center justify-between px-4 py-2.5">
            {/* 왼쪽: 홈 버튼 + 뒤로가기 버튼 */}
            <div className="flex items-center gap-2">
              {/* 홈 버튼 - 홈 페이지가 아닐 때만 표시 */}
              {location.pathname !== '/' && (
                <button
                  type="button"
                  onClick={() => navigate('/')}
                  className="p-2.5 -ml-2 rounded-xl hover:bg-card border border-border/40 
                             focus:outline-none focus:ring-2 focus:ring-primary/50 
                             transition-all duration-300 active:scale-95 touch-manipulation
                             hover:shadow-soft hover:border-primary/30"
                  style={{ background: 'rgba(249, 250, 251, 0.8)' }}
                  aria-label="홈으로 가기"
                >
                  <Home className="w-5 h-5 text-fg" aria-hidden="true" />
                </button>
              )}
              {/* 뒤로가기 버튼 */}
              {showBackButton && (
                <button
                  type="button"
                  onClick={handleBack}
                  className="p-2.5 rounded-xl hover:bg-card border border-border/40 
                             focus:outline-none focus:ring-2 focus:ring-primary/50 
                             transition-all duration-300 active:scale-95 touch-manipulation
                             hover:shadow-soft hover:border-primary/30"
                  style={{ background: 'rgba(249, 250, 251, 0.8)' }}
                  aria-label="뒤로 가기"
                >
                  <ArrowLeft className="w-5 h-5 text-fg" aria-hidden="true" />
                </button>
              )}
            </div>

            {/* 중앙: 제목 */}
            <h1 className="text-base font-bold text-fg flex-1 text-center tracking-tight px-2">
              {title}
            </h1>

            {/* 오른쪽: 음성 안내 버튼 */}
            <div className="w-11 flex items-center justify-end">
              <button
                type="button"
                onClick={toggleTTS}
                className={`p-2.5 -mr-2 rounded-xl border-2 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all duration-200 active:scale-95 touch-manipulation ${
                  isTTSEnabled 
                    ? 'bg-primary text-white border-primary/30 hover:bg-primary/90 shadow-sm shadow-primary/20' 
                    : 'bg-white text-muted/50 border-border/40 hover:bg-card/80 hover:border-border hover:text-fg/70'
                }`}
                aria-label={isTTSEnabled ? '음성 안내 끄기' : '음성 안내 켜기'}
                aria-pressed={isTTSEnabled}
              >
                {isTTSEnabled ? (
                  <Volume2 className="w-4 h-4" aria-hidden="true" />
                ) : (
                  <VolumeX className="w-4 h-4" aria-hidden="true" />
                )}
              </button>
            </div>
          </div>
        </div>
      </header>
      )}

      {/* 메인 콘텐츠 */}
      <main className="flex-1 overflow-hidden bg-bg">
        <div className="w-full md:max-w-md md:mx-auto h-full flex flex-col">{children}</div>
      </main>

      {/* 하단 탭 네비게이션 - 선택적 표시 */}
      {showFooter && (
      <nav 
        className="sticky bottom-0 z-50 bg-white/98 backdrop-blur-xl border-t border-border/60 shadow-[0_-2px_12px_rgba(0,0,0,0.05)]" 
        role="navigation" 
        aria-label="메인 네비게이션"
      >
        <div className="w-full md:max-w-md md:mx-auto px-3 py-2">
          <div className="flex items-center justify-around gap-1">
            <NavButton
              icon={Home}
              label="홈"
              onClick={() => navigate('/')}
              isActive={isActive('/')}
              ariaLabel="홈으로 가기"
              ariaCurrent={isActive('/') ? 'page' : undefined}
            />
            <NavButton
              icon={BookOpen}
              label="교재"
              onClick={() => navigate('/books')}
              isActive={isActive('/books') || isActive('/textbook') || isActive('/passage')}
              ariaLabel="교재 학습"
              ariaCurrent={isActive('/books') || isActive('/textbook') || isActive('/passage') ? 'page' : undefined}
            />
            {/* Question 페이지는 제거됨 - Unit.tsx로 통합 */}
            <NavButton
              icon={BookMarked}
              label="어휘"
              onClick={() => navigate('/vocab')}
              isActive={isActive('/vocab')}
              ariaLabel="어휘 학습"
              ariaCurrent={isActive('/vocab') ? 'page' : undefined}
            />
            <NavButton
              icon={Timer}
              label="시험"
              onClick={() => navigate('/exam-mode')}
              isActive={isActive('/exam-mode') || isActive('/exam-timer')}
              ariaLabel="시험 모드"
              ariaCurrent={isActive('/exam-mode') || isActive('/exam-timer') ? 'page' : undefined}
            />
          </div>
        </div>
      </nav>
      )}
    </div>
  );
}
