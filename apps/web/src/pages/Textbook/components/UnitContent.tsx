import { useEffect, useState, useRef } from 'react';
import { useBrailleChunkReader } from '../../../hooks/useBrailleChunkReader';
import { getSubjectStrategy, extractSubjectType } from '../../../strategies/subjectLearning';
import { extractKeywords } from '../../../utils/contentExtractor';
import { examAPI } from '../../../lib/api';
import useBrailleBLE from '../../../hooks/useBrailleBLE';
import type { Unit } from '../../../lib/api';

interface UnitContentProps {
  unit: Unit | null;
  onSpeak: (text: string) => void;
  readingMode?: 'braille-only' | 'audio-first' | 'mixed';
}

export default function UnitContent({ unit, onSpeak, readingMode = 'braille-only' }: UnitContentProps) {
  const [brailleStatus, setBrailleStatus] = useState<'pending' | 'converting' | 'completed' | 'failed'>('pending');
  const [brailleCells, setBrailleCells] = useState<number[][]>([]);
  const [brailleStrategy, setBrailleStrategy] = useState<string>('korean');
  const { isConnected, writeCells } = useBrailleBLE();
  const chunkNavigationRef = useRef<{ next: () => void; prev: () => void; reset: () => void } | null>(null);

  // 과목 추출 (unit의 textbook에서 subject 가져오기)
  // TODO: Unit 타입에 textbook 정보 추가 필요
  const subject = 'math'; // 기본값, 나중에 unit.textbook?.subject로 변경
  const strategy = getSubjectStrategy(subject);

  // 점자 데이터 로드
  useEffect(() => {
    if (!unit) return;

    const loadBrailleStatus = async () => {
      try {
        const status = await examAPI.getBrailleStatus(unit.id);
        setBrailleStatus(status.status as any);
        setBrailleCells(status.cells || []);
        setBrailleStrategy(status.strategy || 'korean');
      } catch (error) {
        console.error('[UnitContent] 점자 상태 조회 실패:', error);
        setBrailleStatus('pending');
      }
    };

    loadBrailleStatus();
  }, [unit]);

  // 점자 데이터가 있으면 사용, 없으면 텍스트에서 변환
  const textToDisplay = brailleCells.length > 0 && brailleStatus === 'completed'
    ? '' // 점자 데이터 사용
    : unit?.content || '';

  // 청크 리더 (과목별 전략 적용)
  const chunkReader = useBrailleChunkReader(textToDisplay, {
    maxCells: 3,
    strategy: strategy.displayContent.extractKey ? 'smart' : strategy.readQuestion.chunkStrategy,
    autoPlay: false,
  });

  // chunkNavigationRef에 함수 등록
  useEffect(() => {
    chunkNavigationRef.current = {
      next: chunkReader.next,
      prev: chunkReader.prev,
      reset: chunkReader.reset,
    };
  }, [chunkReader.next, chunkReader.prev, chunkReader.reset]);

  // 점자 읽기 모드: 점자 데이터 표시
  useEffect(() => {
    if (readingMode === 'braille-only' && brailleCells.length > 0 && brailleStatus === 'completed' && isConnected) {
      // 첫 번째 청크를 점자로 표시 (3-cell)
      const firstChunk = brailleCells.slice(0, 3);
      if (firstChunk.length > 0) {
        // writeCells는 number[][]를 받음 (각 셀은 6개 점 배열)
        writeCells(firstChunk);
      }
      // 음성 최소화: 한 번만
      onSpeak('점자로 읽어보세요.');
    }
  }, [brailleCells, brailleStatus, readingMode, isConnected, writeCells, onSpeak]);

  // 청크 네비게이션: 점자 데이터 사용 시
  useEffect(() => {
    if (brailleCells.length > 0 && brailleStatus === 'completed' && isConnected && readingMode === 'braille-only') {
      const startIndex = chunkReader.currentIndex * 3;
      const chunk = brailleCells.slice(startIndex, startIndex + 3);
      if (chunk.length > 0) {
        writeCells(chunk);
      }
    }
  }, [chunkReader.currentIndex, brailleCells, brailleStatus, isConnected, writeCells, readingMode]);

  // 단원 내용 음성 안내 (점자 읽기 모드가 아닐 때만)
  useEffect(() => {
    if (unit && readingMode !== 'braille-only') {
      // 음성 우선: 전체 내용 읽기
      if (strategy.displayContent.useAudio) {
        const intro = `${unit.title}입니다.`;
        onSpeak(intro);
        
        // 내용이 있으면 전체 또는 요약하여 안내
        if (unit.content) {
          if (strategy.displayContent.extractKey) {
            // 핵심만 추출
            const keywords = extractKeywords(unit.content, 3);
            const keyText = keywords.length > 0 
              ? `핵심 키워드: ${keywords.join(', ')}`
              : unit.content.substring(0, 200);
            setTimeout(() => {
              onSpeak(keyText);
            }, 2000);
          } else {
            // 전체 내용
            const contentPreview = unit.content.length > 500 
              ? unit.content.substring(0, 500) + '...'
              : unit.content;
            setTimeout(() => {
              onSpeak(contentPreview);
            }, 2000);
          }
        }
      }
    } else if (unit && readingMode === 'braille-only' && brailleStatus === 'pending') {
      // 점자 변환 대기 중
      onSpeak('점자 변환 중입니다. 잠시만 기다려주세요.');
    }
  }, [unit, onSpeak, strategy, readingMode, brailleStatus]);

  if (!unit) {
    return (
      <div className="p-4 text-center text-muted">
        <p>단원을 선택해주세요.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-bold mb-2">{unit.title}</h2>
        {unit.textbook_title && (
          <p className="text-sm text-muted">교재: {unit.textbook_title}</p>
        )}
      </div>

      {/* 점자 변환 상태 표시 */}
      {readingMode === 'braille-only' && (
        <div className="bg-accent/10 border border-accent/20 rounded-lg p-3">
          {brailleStatus === 'pending' && (
            <p className="text-sm text-muted">점자 변환 대기 중...</p>
          )}
          {brailleStatus === 'converting' && (
            <p className="text-sm text-muted">점자 변환 중입니다. 잠시만 기다려주세요.</p>
          )}
          {brailleStatus === 'completed' && (
            <div className="space-y-2">
              <p className="text-sm font-medium">점자 읽기 모드</p>
              {isConnected && chunkReader.totalChunks > 1 && (
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted">
                    {chunkReader.currentIndex + 1} / {chunkReader.totalChunks}
                  </span>
                  <div className="flex gap-2">
                    <button
                      onClick={chunkReader.prev}
                      disabled={chunkReader.currentIndex === 0}
                      className="btn-ghost text-xs px-2 py-1 disabled:opacity-50"
                      aria-label="이전 청크"
                    >
                      ← 이전
                    </button>
                    <button
                      onClick={chunkReader.next}
                      disabled={chunkReader.currentIndex >= chunkReader.totalChunks - 1}
                      className="btn-ghost text-xs px-2 py-1 disabled:opacity-50"
                      aria-label="다음 청크"
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
                </div>
              )}
            </div>
          )}
          {brailleStatus === 'failed' && (
            <p className="text-sm text-error">점자 변환에 실패했습니다. 다시 시도해주세요.</p>
          )}
        </div>
      )}
      
      <div className="prose max-w-none">
        <div className="whitespace-pre-wrap text-base leading-relaxed">
          {readingMode === 'braille-only' && brailleStatus === 'completed'
            ? '점자로 읽어보세요.' // 점자 모드에서는 텍스트 숨김 (선택적)
            : unit.content || '내용이 없습니다.'}
        </div>
      </div>
    </div>
  );
}


