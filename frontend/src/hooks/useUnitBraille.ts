/**
 * Unit 점자 처리 훅
 */
import { useState, useEffect } from 'react';
import { useBrailleChunkReader } from './useBrailleChunkReader';
import { BRAILLE_CHUNK_SIZE } from '../components/unit/constants';
import type { Unit } from '../types/api';
import type { SubjectStrategy } from '../strategies/subjectLearning';

interface UseUnitBrailleOptions {
  unit: Unit | null;
  strategy: SubjectStrategy;
  readingMode: 'braille-only' | 'audio-first' | 'mixed';
  isConnected: boolean;
  writeCells: (cells: number[][]) => void;
}

export function useUnitBraille({
  unit,
  strategy,
  readingMode,
  isConnected,
  writeCells,
}: UseUnitBrailleOptions) {
  const [brailleStatus, setBrailleStatus] = useState<'pending' | 'converting' | 'completed' | 'failed'>('pending');
  const [brailleCells, setBrailleCells] = useState<number[][]>([]);
  const [brailleStrategy, setBrailleStrategy] = useState<string>('korean');

  // 점자 데이터 로드 (섹션 변경 시 초기화)
  useEffect(() => {
    if (!unit) {
      // unit이 없으면 상태 초기화
      setBrailleStatus('pending');
      setBrailleCells([]);
      return;
    }

    // 섹션 변경 시 이전 데이터 초기화
    setBrailleCells([]);
    
    // 현재는 API에서 점자 상태를 조회하지 않고, 텍스트를 직접 점자로 변환
    // 점자 변환은 클라이언트 측에서 처리 (useBrailleChunkReader 사용)
    setBrailleStatus('completed');
    setBrailleStrategy('korean');
  }, [unit?.id, unit?.content]); // unit.id와 content 변경 시 재로드

  // 점자 데이터가 있으면 사용, 없으면 텍스트에서 변환
  const textToDisplay = brailleCells.length > 0 && brailleStatus === 'completed'
    ? ''
    : unit?.content || '';

  // 청크 리더 (과목별 전략 적용)
  const chunkReader = useBrailleChunkReader(textToDisplay, {
    maxCells: BRAILLE_CHUNK_SIZE,
    strategy: strategy.displayContent.extractKey ? 'smart' : strategy.readQuestion.chunkStrategy,
    autoPlay: false, // 수동 네비게이션 (다음/이전 버튼으로 제어)
    subject: unit?.textbook?.subject?.toLowerCase() as any, // 과목별 전략 적용
  });

  // 점자 읽기 모드: 점자 데이터 표시
  useEffect(() => {
    if (readingMode === 'braille-only' && brailleCells.length > 0 && brailleStatus === 'completed' && isConnected) {
      const firstChunk = brailleCells.slice(0, BRAILLE_CHUNK_SIZE);
      if (firstChunk.length > 0) {
        writeCells(firstChunk);
      }
    }
  }, [brailleCells, brailleStatus, readingMode, isConnected, writeCells]);

  // 청크 네비게이션: 점자 데이터 사용 시
  useEffect(() => {
    if (brailleCells.length > 0 && brailleStatus === 'completed' && isConnected && readingMode === 'braille-only') {
      const startIndex = chunkReader.currentIndex * BRAILLE_CHUNK_SIZE;
      const chunk = brailleCells.slice(startIndex, startIndex + BRAILLE_CHUNK_SIZE);
      if (chunk.length > 0) {
        writeCells(chunk);
      }
    }
  }, [chunkReader.currentIndex, brailleCells, brailleStatus, isConnected, writeCells, readingMode]);

  return {
    brailleStatus,
    brailleCells,
    brailleStrategy,
    chunkReader,
  };
}
