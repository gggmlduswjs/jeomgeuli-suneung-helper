import { useEffect } from 'react';
import { BraillePatternFactory } from '../../../lib/braillePattern';
import useBrailleBLE from '../../../hooks/useBrailleBLE';
import { useBrailleChunkReader } from '../../../hooks/useBrailleChunkReader';
import { extractKeywords } from '../../../utils/contentExtractor';
import type { PassageStructure as PassageStructureType } from '../../../lib/api';

interface PassageStructureProps {
  structure: PassageStructureType | null;
  onSpeak: (text: string) => void;
  chunkNavigationRef?: React.MutableRefObject<{ next: () => void; prev: () => void; reset: () => void } | null>;
  readingMode?: 'braille-only' | 'audio-first' | 'mixed';
}

export default function PassageStructure({ structure, onSpeak, chunkNavigationRef, readingMode = 'braille-only' }: PassageStructureProps) {
  const { isConnected, writeCells } = useBrailleBLE();
  
  // 지문 핵심 키워드를 청크로 분할하여 점자 출력
  const keywordsText = structure?.keywords?.join(' ') || '';
  const chunkReader = useBrailleChunkReader(keywordsText, {
    maxCells: 3,
    strategy: 'sentence', // 국어: 문장 단위
    autoPlay: false,
    subject: 'korean', // 과목별 전략 적용
  });

  // chunkNavigationRef에 함수 등록 (부모 컴포넌트에서 음성 명령으로 접근 가능)
  useEffect(() => {
    if (chunkNavigationRef) {
      chunkNavigationRef.current = {
        next: chunkReader.next,
        prev: chunkReader.prev,
        reset: chunkReader.reset,
      };
    }
  }, [chunkReader.next, chunkReader.prev, chunkReader.reset, chunkNavigationRef]);

  // 구조화된 결과 음성 안내
  useEffect(() => {
    if (!structure) return;

    // 점자 읽기 모드: 음성 최소화
    if (readingMode === 'braille-only') {
      onSpeak('지문을 점자로 읽어보세요.');
      return;
    }

    // 요약 읽기
    onSpeak(`요약: ${structure.summary}`);

    // 등장인물 읽기
    if (structure.characters && structure.characters.length > 0) {
      setTimeout(() => {
        onSpeak(`등장인물: ${structure.characters.join(', ')}`);
      }, 3000);
    }

    // 구조 읽기
    if (structure.structure) {
      setTimeout(() => {
        onSpeak(`구조: ${structure.structure}`);
      }, 5000);
    }

    // 키워드 점자 패턴 전송
    if (structure.keywords && structure.keywords.length > 0 && isConnected) {
      structure.keywords.slice(0, 5).forEach((_, index) => {
        if (index < 5) {
          setTimeout(() => {
            const pattern = BraillePatternFactory.createNumberPattern((index + 1) as 1 | 2 | 3 | 4 | 5);
            writeCells([pattern]);
          }, 7000 + index * 500);
        }
      });
    }
  }, [structure, onSpeak, isConnected, writeCells, readingMode]);

  if (!structure) {
    return null;
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">분석 결과</h3>

      <div className="bg-card border border-border rounded-lg p-4">
        <h4 className="font-semibold mb-2">요약</h4>
        <p className="text-base leading-relaxed whitespace-pre-wrap">
          {structure.summary}
        </p>
      </div>

      {structure.characters && structure.characters.length > 0 && (
        <div className="bg-card border border-border rounded-lg p-4">
          <h4 className="font-semibold mb-2">등장인물/개념</h4>
          <ul className="list-disc list-inside space-y-1">
            {structure.characters.map((char, index) => (
              <li key={index}>{char}</li>
            ))}
          </ul>
        </div>
      )}

      {structure.structure && (
        <div className="bg-card border border-border rounded-lg p-4">
          <h4 className="font-semibold mb-2">구조</h4>
          <p className="text-base leading-relaxed whitespace-pre-wrap">
            {structure.structure}
          </p>
        </div>
      )}

      {structure.keywords && structure.keywords.length > 0 && (
        <div className="bg-card border border-border rounded-lg p-4">
          <h4 className="font-semibold mb-2">키워드</h4>
          <div className="flex flex-wrap gap-2">
            {structure.keywords.map((keyword, index) => (
              <span
                key={index}
                className="px-3 py-1 bg-accent/10 border border-accent/20 rounded-full text-sm"
              >
                {index + 1}. {keyword}
              </span>
            ))}
          </div>
          
          {/* 청크 네비게이션 (점자 디스플레이 연결 시 표시) */}
          {isConnected && chunkReader.totalChunks > 1 && (
            <div className="mt-4 bg-accent/10 border border-accent/20 rounded-lg p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">점자 키워드 청크</span>
                <span className="text-xs text-muted">
                  {chunkReader.currentIndex + 1} / {chunkReader.totalChunks}
                </span>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={chunkReader.prev}
                  disabled={chunkReader.currentIndex === 0}
                  className="btn-ghost text-xs px-2 py-1 disabled:opacity-50"
                  aria-label="이전 키워드"
                >
                  ← 이전
                </button>
                <button
                  onClick={chunkReader.next}
                  disabled={chunkReader.currentIndex >= chunkReader.totalChunks - 1}
                  className="btn-ghost text-xs px-2 py-1 disabled:opacity-50"
                  aria-label="다음 키워드"
                >
                  다음 →
                </button>
                <button
                  onClick={chunkReader.reset}
                  className="btn-ghost text-xs px-2 py-1"
                  aria-label="처음으로"
                >
                  처음
                </button>
              </div>
              {chunkReader.currentChunk && (
                <p className="text-xs text-muted mt-2">
                  현재: {chunkReader.currentChunk}
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}


