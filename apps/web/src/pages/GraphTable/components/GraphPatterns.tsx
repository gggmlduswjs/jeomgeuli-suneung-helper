import { useEffect } from 'react';
import { BraillePatternFactory } from '../../../lib/braillePattern';
import useBrailleBLE from '../../../hooks/useBrailleBLE';
import type { GraphPatterns as GraphPatternsType } from '../../../lib/api';

interface GraphPatternsProps {
  patterns: GraphPatternsType | null;
  onSpeak: (text: string) => void;
  readingMode?: 'braille-only' | 'audio-first' | 'mixed';
}

export default function GraphPatterns({ patterns, onSpeak, readingMode = 'braille-only' }: GraphPatternsProps) {
  const { isConnected, writeCells } = useBrailleBLE();

  // 패턴 음성 안내 및 점자 전송
  useEffect(() => {
    if (!patterns) return;

    // 점자 읽기 모드: 음성 최소화
    if (readingMode === 'braille-only') {
      onSpeak('그래프 패턴을 점자로 읽어보세요.');
    } else {
      const descriptions: string[] = [];

      // 추세 설명
      if (patterns.trend === 'increase') {
        descriptions.push('추세는 증가입니다.');
      } else if (patterns.trend === 'decrease') {
        descriptions.push('추세는 감소입니다.');
      } else {
        descriptions.push('추세는 유지입니다.');
      }

      // 극값 설명
      if (patterns.extremum === 'maximum') {
        descriptions.push('극대점이 있습니다.');
      } else if (patterns.extremum === 'minimum') {
        descriptions.push('극소점이 있습니다.');
      }

      // 비교 설명
      if (patterns.comparison === 'greater') {
        descriptions.push('값이 더 큽니다.');
      } else if (patterns.comparison === 'less') {
        descriptions.push('값이 더 작습니다.');
      } else {
        descriptions.push('값이 같습니다.');
      }

      // 음성 안내
      onSpeak(descriptions.join(' '));
    }

    // 점자 패턴 전송
    if (isConnected) {
      // 추세 패턴
      setTimeout(() => {
        const trendPattern = BraillePatternFactory.createTrendPattern(patterns.trend);
        writeCells([trendPattern]);
      }, 2000);

      // 극값 패턴
      if (patterns.extremum !== 'none') {
        setTimeout(() => {
          const extremumPattern = BraillePatternFactory.createExtremumPattern(patterns.extremum as 'maximum' | 'minimum');
          writeCells([extremumPattern]);
        }, 3000);
      }
    }
  }, [patterns, onSpeak, isConnected, writeCells, readingMode]);

  if (!patterns) {
    return null;
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">추출된 패턴</h3>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-card border border-border rounded-lg p-4">
          <h4 className="font-semibold mb-2">추세</h4>
          <p className="text-base">
            {patterns.trend === 'increase' && '증가 ↗'}
            {patterns.trend === 'decrease' && '감소 ↘'}
            {patterns.trend === 'stable' && '유지 →'}
          </p>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <h4 className="font-semibold mb-2">극값</h4>
          <p className="text-base">
            {patterns.extremum === 'maximum' && '극대 ⬆'}
            {patterns.extremum === 'minimum' && '극소 ⬇'}
            {patterns.extremum === 'none' && '없음'}
          </p>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <h4 className="font-semibold mb-2">비교</h4>
          <p className="text-base">
            {patterns.comparison === 'greater' && '더 큼 >'}
            {patterns.comparison === 'less' && '더 작음 <'}
            {patterns.comparison === 'equal' && '같음 ='}
          </p>
        </div>
      </div>
    </div>
  );
}


