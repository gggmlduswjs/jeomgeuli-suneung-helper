/**
 * 그래프 듀얼 뷰
 * 보호자용 그래프 + 점자 패턴 미리보기
 */
import { useState } from 'react';
import { BarChart3, Braille } from 'lucide-react';
import useTTS from '../../../hooks/useTTS';

interface GraphDualViewProps {
  graphImage?: string;
  analysisResult?: {
    trend: string;
    extremum: string;
    intervals: Array<{ type: string; range: string }>;
    semanticDescription: string;
  };
  braillePatterns?: Array<{
    text: string;
    cells: number[][];
  }>;
}

export default function GraphDualView({
  graphImage,
  analysisResult,
  braillePatterns = []
}: GraphDualViewProps) {
  const { speak, stop: stopTTS } = useTTS();
  const [selectedPattern, setSelectedPattern] = useState<number | null>(null);

  const describeGraph = () => {
    if (!analysisResult) return;
    
    const description = `
      그래프 분석 결과:
      추세: ${analysisResult.trend}
      극값: ${analysisResult.extremum}
      ${analysisResult.semanticDescription}
    `;
    speak(description);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* 왼쪽: 그래프 원본 + 분석 결과 (보호자용) */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center gap-2 mb-4">
          <BarChart3 className="w-5 h-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-800">그래프 분석</h3>
        </div>

        {graphImage && (
          <div className="mb-4">
            <img
              src={graphImage}
              alt="그래프"
              className="w-full rounded-lg border border-gray-200"
            />
          </div>
        )}

        {analysisResult && (
          <div className="space-y-3">
            <div>
              <span className="text-sm font-medium text-gray-600">추세: </span>
              <span className="text-sm text-gray-800">{analysisResult.trend}</span>
            </div>
            <div>
              <span className="text-sm font-medium text-gray-600">극값: </span>
              <span className="text-sm text-gray-800">{analysisResult.extremum}</span>
            </div>
            
            {analysisResult.intervals && analysisResult.intervals.length > 0 && (
              <div>
                <span className="text-sm font-medium text-gray-600">증감 구간: </span>
                <div className="mt-2 space-y-1">
                  {analysisResult.intervals.map((interval, idx) => (
                    <div key={idx} className="text-xs text-gray-700">
                      {interval.type}: {interval.range}
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="mt-4 p-3 bg-blue-50 rounded-lg">
              <p className="text-sm text-gray-700">{analysisResult.semanticDescription}</p>
            </div>

            <button
              onClick={describeGraph}
              className="w-full mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
              aria-label="그래프 분석 결과 음성으로 듣기"
            >
              🔊 분석 결과 듣기
            </button>
          </div>
        )}
      </div>

      {/* 오른쪽: 점자 패턴 미리보기 */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center gap-2 mb-4">
          <Braille className="w-5 h-5 text-green-600" />
          <h3 className="text-lg font-semibold text-gray-800">점자 패턴</h3>
        </div>

        {braillePatterns.length > 0 ? (
          <div className="space-y-4">
            {braillePatterns.map((pattern, idx) => (
              <div
                key={idx}
                className={`p-3 rounded-lg border-2 transition-colors cursor-pointer ${
                  selectedPattern === idx
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => {
                  setSelectedPattern(idx);
                  stopTTS();
                  speak(pattern.text);
                }}
              >
                <div className="text-xs text-gray-600 mb-2">패턴 {idx + 1}</div>
                <div className="text-sm text-gray-800 mb-2">{pattern.text}</div>
                <div className="flex gap-1">
                  {pattern.cells.map((cell, cellIdx) => (
                    <div
                      key={cellIdx}
                      className="w-6 h-8 border border-gray-300 rounded bg-white grid grid-cols-2 gap-0.5 p-0.5"
                    >
                      {Array.isArray(cell) && cell.map((dot, dotIdx) => (
                        <div
                          key={dotIdx}
                          className={`w-2 h-2 rounded-full ${
                            dot ? 'bg-gray-900' : 'bg-gray-200'
                          }`}
                        />
                      ))}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-400 text-sm">
            점자 패턴이 없습니다.
          </div>
        )}
      </div>
    </div>
  );
}

