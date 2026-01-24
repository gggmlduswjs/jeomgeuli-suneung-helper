/**
 * Unit 카드 스와이프 컴포넌트
 * 좌우 스와이프로 Unit 간 이동
 */
import { useState, useEffect, useRef, TouchEvent, ReactNode } from 'react';

interface UnitCardSwiperProps {
  children: ReactNode;
  currentIndex: number;
  totalUnits: number;
  onIndexChange: (newIndex: number) => void;
  className?: string;
}

export default function UnitCardSwiper({
  children,
  currentIndex,
  totalUnits,
  onIndexChange,
  className = ''
}: UnitCardSwiperProps) {
  const [touchStart, setTouchStart] = useState<number | null>(null);
  const [touchEnd, setTouchEnd] = useState<number | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  // 스와이프 감지를 위한 최소 거리 (픽셀)
  const minSwipeDistance = 50;

  const handleTouchStart = (e: TouchEvent) => {
    setTouchEnd(null);
    setTouchStart(e.targetTouches[0].clientX);
    setIsDragging(true);
  };

  const handleTouchMove = (e: TouchEvent) => {
    if (!touchStart) return;

    const currentTouch = e.targetTouches[0].clientX;
    const diff = currentTouch - touchStart;

    // 드래그 범위 제한 (양쪽 끝에서 저항)
    let limitedDiff = diff;
    if (currentIndex === 0 && diff > 0) {
      limitedDiff = diff * 0.3; // 첫 페이지에서 오른쪽 드래그 시 저항
    } else if (currentIndex === totalUnits - 1 && diff < 0) {
      limitedDiff = diff * 0.3; // 마지막 페이지에서 왼쪽 드래그 시 저항
    }

    setDragOffset(limitedDiff);
    setTouchEnd(currentTouch);
  };

  const handleTouchEnd = () => {
    if (!touchStart || !touchEnd) {
      setIsDragging(false);
      setDragOffset(0);
      return;
    }

    const distance = touchStart - touchEnd;
    const isLeftSwipe = distance > minSwipeDistance;
    const isRightSwipe = distance < -minSwipeDistance;

    if (isLeftSwipe && currentIndex < totalUnits - 1) {
      // 왼쪽 스와이프 -> 다음 Unit
      onIndexChange(currentIndex + 1);
    } else if (isRightSwipe && currentIndex > 0) {
      // 오른쪽 스와이프 -> 이전 Unit
      onIndexChange(currentIndex - 1);
    }

    // 상태 초기화
    setIsDragging(false);
    setDragOffset(0);
    setTouchStart(null);
    setTouchEnd(null);
  };

  // 키보드 네비게이션
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowLeft' && currentIndex > 0) {
        onIndexChange(currentIndex - 1);
      } else if (e.key === 'ArrowRight' && currentIndex < totalUnits - 1) {
        onIndexChange(currentIndex + 1);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentIndex, totalUnits, onIndexChange]);

  return (
    <div className={`unit-card-swiper ${className}`} ref={containerRef}>
      {/* 진행도 표시 */}
      <div className="progress-indicator px-4 py-2 bg-background">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-muted-foreground">
            {currentIndex + 1} / {totalUnits}
          </span>
          <div className="flex gap-1">
            {Array.from({ length: Math.min(totalUnits, 10) }).map((_, i) => (
              <div
                key={i}
                className={`h-1.5 rounded-full transition-all ${
                  i === currentIndex
                    ? 'w-6 bg-primary'
                    : i < currentIndex
                    ? 'w-1.5 bg-primary/50'
                    : 'w-1.5 bg-border'
                }`}
              />
            ))}
          </div>
        </div>

        {/* 프로그레스 바 */}
        <div className="w-full h-1 bg-border rounded-full overflow-hidden">
          <div
            className="h-full bg-primary transition-all duration-300"
            style={{ width: `${((currentIndex + 1) / totalUnits) * 100}%` }}
          />
        </div>
      </div>

      {/* 카드 컨테이너 */}
      <div
        className="card-container relative overflow-hidden"
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
        style={{ touchAction: 'pan-y pinch-zoom' }}
      >
        <div
          className={`card-wrapper transition-transform ${
            isDragging ? 'duration-0' : 'duration-300'
          } ease-out`}
          style={{
            transform: `translateX(${dragOffset}px)`
          }}
        >
          {children}
        </div>
      </div>

      {/* 네비게이션 버튼 (데스크톱용) */}
      <div className="navigation-buttons hidden md:flex absolute top-1/2 left-0 right-0 -translate-y-1/2 pointer-events-none px-4">
        <button
          onClick={() => currentIndex > 0 && onIndexChange(currentIndex - 1)}
          disabled={currentIndex === 0}
          className="pointer-events-auto w-12 h-12 rounded-full bg-background border border-border shadow-lg flex items-center justify-center hover:bg-accent disabled:opacity-30 disabled:cursor-not-allowed transition-all"
          aria-label="이전 Unit"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        <div className="flex-1" />

        <button
          onClick={() => currentIndex < totalUnits - 1 && onIndexChange(currentIndex + 1)}
          disabled={currentIndex === totalUnits - 1}
          className="pointer-events-auto w-12 h-12 rounded-full bg-background border border-border shadow-lg flex items-center justify-center hover:bg-accent disabled:opacity-30 disabled:cursor-not-allowed transition-all"
          aria-label="다음 Unit"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>

      {/* 스와이프 힌트 (첫 방문 시) */}
      {currentIndex === 0 && (
        <div className="swipe-hint absolute bottom-20 left-0 right-0 flex justify-center pointer-events-none">
          <div className="bg-background/90 border border-border rounded-full px-4 py-2 shadow-lg flex items-center gap-2 animate-pulse">
            <svg className="w-5 h-5 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16l-4-4m0 0l4-4m-4 4h18" />
            </svg>
            <span className="text-sm text-muted-foreground">좌우로 스와이프하세요</span>
            <svg className="w-5 h-5 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
            </svg>
          </div>
        </div>
      )}
    </div>
  );
}
