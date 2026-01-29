/**
 * 점자 모듈 - 핵심 키워드 표시 패널
 */
import { useEffect, useState, useMemo } from 'react';
import { localToBrailleCells } from '../../lib/braille/converter';
import { useBrailleBLE } from '../../hooks/useBrailleBLE';
import { createModuleLogger } from '../../utils/logger';
import type { DotArray } from '../../types';

const logger = createModuleLogger('BrailleKeywordsPanel');

/**
 * 단일 점자셀 컴포넌트
 * 파란색 primary 테마로 점자 패턴 표시 (빈 점은 렌더링하지 않음)
 */
function SingleBrailleCell({ pattern, active }: { pattern: DotArray; active: boolean }) {
  const normalizeTo6 = (arr: DotArray): [boolean, boolean, boolean, boolean, boolean, boolean] => {
    const out: boolean[] = Array.isArray(arr) ? arr.slice(0, 6) : [];
    while (out.length < 6) out.push(false);
    return out as [boolean, boolean, boolean, boolean, boolean, boolean];
  };

  const braillePattern = normalizeTo6(pattern);
  
  // 점의 위치를 정확하게 계산 (2열 3행 그리드, 42px x 64px)
  // 각 열: 21px, 각 행: 약 21.33px
  // 점 크기: 14px (크기 키움), 중앙 정렬
  const cellWidth = 42;
  const cellHeight = 64;
  const dotSize = 14;
  const colWidth = cellWidth / 2; // 21px
  const rowHeight = cellHeight / 3; // 약 21.33px
  
  const dotPositions: Array<{ top: number; left: number; index: number }> = [
    { top: rowHeight * 0 + (rowHeight - dotSize) / 2, left: colWidth * 0 + (colWidth - dotSize) / 2, index: 0 }, // 왼쪽 위
    { top: rowHeight * 0 + (rowHeight - dotSize) / 2, left: colWidth * 1 + (colWidth - dotSize) / 2, index: 1 }, // 오른쪽 위
    { top: rowHeight * 1 + (rowHeight - dotSize) / 2, left: colWidth * 0 + (colWidth - dotSize) / 2, index: 2 }, // 왼쪽 중간
    { top: rowHeight * 1 + (rowHeight - dotSize) / 2, left: colWidth * 1 + (colWidth - dotSize) / 2, index: 3 }, // 오른쪽 중간
    { top: rowHeight * 2 + (rowHeight - dotSize) / 2, left: colWidth * 0 + (colWidth - dotSize) / 2, index: 4 }, // 왼쪽 아래
    { top: rowHeight * 2 + (rowHeight - dotSize) / 2, left: colWidth * 1 + (colWidth - dotSize) / 2, index: 5 }, // 오른쪽 아래
  ];

  return (
    <div
      className="relative flex-shrink-0 rounded-xl overflow-hidden border border-border/50"
      style={{ 
        width: `${cellWidth}px`, 
        height: `${cellHeight}px`,
        background: 'transparent',
        boxShadow: 'none',
      }}
      role="group"
      aria-label="점자 셀"
    >
      {/* 활성화된 점만 렌더링 */}
      {dotPositions
        .filter((_, index) => braillePattern[index])
        .map(({ top, left, index }) => (
          <div
            key={index}
            className="absolute rounded-full transition-all"
            style={{
              width: `${dotSize}px`,
              height: `${dotSize}px`,
              top: `${top}px`,
              left: `${left}px`,
              background: '#0EA5E9',
              border: '2px solid #0284C7', // 테두리 (조금 더 진한 파란색)
              boxShadow: '0 2px 4px rgba(0, 0, 0, 0.2)',
            }}
            aria-hidden={true}
          />
        ))}
    </div>
  );
}

interface BrailleKeywordsPanelProps {
  keywords: string[];
  unitTitle?: string;
  onClose: () => void;
}

export default function BrailleKeywordsPanel({
  keywords,
  unitTitle,
  onClose,
}: BrailleKeywordsPanelProps) {
  const { sendText, isConnected } = useBrailleBLE();
  const [currentKeywordIndex, setCurrentKeywordIndex] = useState(0);
  const [isLoadingCells, setIsLoadingCells] = useState(true);

  // 최대 3개만 표시 (hook 호출 전에 계산)
  const displayKeywords = keywords.slice(0, 3);

  // 각 키워드의 점자셀 미리 계산 (모든 hook은 early return 전에 호출)
  const keywordCells = useMemo(() => {
    const cellsMap: Record<string, DotArray[]> = {};
    displayKeywords.forEach(keyword => {
      try {
        cellsMap[keyword] = localToBrailleCells(keyword);
      } catch {
        cellsMap[keyword] = [];
      }
    });
    return cellsMap;
  }, [displayKeywords]);

  // 점자셀 계산 완료 후 로딩 상태 해제
  useEffect(() => {
    if (Object.keys(keywordCells).length > 0) {
      // 짧은 딜레이로 로딩 상태 표시 (사용자 경험 개선)
      const timer = setTimeout(() => setIsLoadingCells(false), 150);
      return () => clearTimeout(timer);
    }
  }, [keywordCells]);

  // 점자 디스플레이에 키워드 전송
  useEffect(() => {
    if (keywords.length > 0 && isConnected) {
      const keyword = keywords[currentKeywordIndex];
      sendText(keyword);
      logger.log(`점자 전송: ${keyword}`);
    }
  }, [keywords, currentKeywordIndex, isConnected, sendText]);

  // 키워드가 없으면 안내 메시지 (모든 hook 호출 후 early return)
  if (keywords.length === 0) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
        <div className="rounded-lg p-6 max-w-md w-full mx-4" style={{ background: 'transparent' }}>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold">점자 모듈</h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-accent rounded-lg transition-colors"
              aria-label="닫기"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <p className="text-muted-foreground">핵심 키워드를 추출하는 중입니다...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
        <div className="rounded-lg p-6 max-w-md w-full mx-4" style={{ background: 'transparent' }}>
        {/* 헤더 */}
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-bold">점자 모듈</h2>
            {unitTitle && <p className="text-sm text-muted-foreground mt-1">{unitTitle}</p>}
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-accent rounded-lg transition-colors"
            aria-label="닫기"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* 점자 디스플레이 상태 */}
        <div className="mb-4 p-3 rounded-lg" style={{ background: '#3BB3AF' }}>
          {isConnected ? (
            <p className="text-sm font-medium" style={{ color: '#1a5f5c' }}>✓ 점자 디스플레이 연결됨</p>
          ) : (
            <p className="text-sm" style={{ color: '#1a5f5c' }}>점자 디스플레이를 연결해주세요</p>
          )}
        </div>

        {/* 핵심 키워드 - 현재 키워드의 점자셀만 표시 */}
        <div className="mb-4">
          <h3 className="text-sm font-semibold mb-3 text-muted-foreground">핵심 키워드</h3>
          <div className="flex gap-2 justify-center items-center min-h-[80px]">
            {isLoadingCells ? (
              <div className="flex gap-2 items-center justify-center">
                {[1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className="relative flex-shrink-0 rounded-xl overflow-hidden border border-border/50 animate-pulse"
                    style={{ 
                      width: '42px', 
                      height: '64px',
                      background: 'rgba(14, 165, 233, 0.1)',
                    }}
                    aria-label="점자셀 로딩 중"
                  />
                ))}
              </div>
            ) : (() => {
              const currentKeyword = displayKeywords[currentKeywordIndex];
              const allCells = keywordCells[currentKeyword] || [];
              
              if (allCells.length === 0) {
                return (
                  <div className="text-sm text-muted-foreground">
                    점자셀을 생성할 수 없습니다.
                  </div>
                );
              }
              
              return (
                <div className="flex gap-2 items-center justify-center flex-wrap">
                  {allCells.map((cell, cellIndex) => (
                    <SingleBrailleCell
                      key={cellIndex}
                      pattern={cell}
                      active={true}
                    />
                  ))}
                </div>
              );
            })()}
          </div>
        </div>

        {/* 현재 키워드 정보 */}
        <div className="mb-4 p-3 rounded-lg text-center" style={{ background: '#3182F6', boxShadow: '0 2px 4px rgba(0, 0, 0, 0.15)' }}>
          <p className="text-sm mb-1" style={{ color: 'rgba(255, 255, 255, 0.8)' }}>
            {currentKeywordIndex + 1} / {displayKeywords.length}
          </p>
          <p className="text-lg font-semibold" style={{ color: 'white' }}>
            {displayKeywords[currentKeywordIndex]}
          </p>
        </div>

        {/* 네비게이션 */}
        <div className="flex items-center justify-between gap-3">
          <button
            onClick={() => setCurrentKeywordIndex((prev) => Math.max(0, prev - 1))}
            disabled={currentKeywordIndex === 0}
            className="px-4 py-2 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            style={{
              background: '#3BB3AF',
              color: '#1a5f5c',
              boxShadow: '0 2px 4px rgba(0, 0, 0, 0.15)',
            }}
          >
            이전
          </button>
          <button
            onClick={() => setCurrentKeywordIndex((prev) => Math.min(displayKeywords.length - 1, prev + 1))}
            disabled={currentKeywordIndex >= displayKeywords.length - 1}
            className="px-4 py-2 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            style={{
              background: '#3182F6',
              color: 'white',
              boxShadow: '0 2px 4px rgba(0, 0, 0, 0.15)',
            }}
          >
            다음
          </button>
        </div>
      </div>
    </div>
  );
}
