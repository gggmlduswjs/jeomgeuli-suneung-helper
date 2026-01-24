
import { brailleAPI } from '@/lib/api/BrailleAPI';
import { useState, useEffect } from 'react';

interface BrailleCellsProps {
  data: string[];
  className?: string;
}

// 점자 셀 표시 컴포넌트
function BrailleDot({ on }: { on: boolean }) {
  return (
    <span 
      className={`inline-block w-3 h-3 rounded-full mx-0.5 my-0.5 border ${
        on 
          ? "bg-gray-800 border-gray-800 shadow-sm" 
          : "bg-gray-100 border-gray-300"
      }`} 
    />
  );
}

function BrailleCell({ cell }: { cell: number[] }) {
  if (!Array.isArray(cell) || cell.length !== 6) {
    return <div className="inline-block w-8 h-12 bg-gray-100 rounded border"></div>;
  }
  
  const [a, b, c, d, e, f] = cell;
  
  return (
    <div className="inline-flex flex-col px-2 py-1 rounded border border-gray-300 bg-white shadow-sm">
      <div className="flex">
        <BrailleDot on={!!a} />
        <BrailleDot on={!!d} />
      </div>
      <div className="flex">
        <BrailleDot on={!!b} />
        <BrailleDot on={!!e} />
      </div>
      <div className="flex">
        <BrailleDot on={!!c} />
        <BrailleDot on={!!f} />
      </div>
    </div>
  );
}

export function BrailleCells({ data, className = "" }: BrailleCellsProps) {
  const [brailleData, setBrailleData] = useState<{ [key: string]: number[][] }>({});

  useEffect(() => {
    // 키워드들을 점자로 변환
    const convertKeywords = async () => {
      const converted: { [key: string]: number[][] } = {};
      
      for (const keyword of data) {
        try {
          const result = await brailleAPI.convertBraille(keyword, 'word');
          if (result.ok && result.cells && Array.isArray(result.cells)) {
            converted[keyword] = result.cells;
          }
        } catch (error) {
          console.error(`키워드 "${keyword}" 점자 변환 실패:`, error);
        }
      }
      
      setBrailleData(converted);
    };

    if (data && data.length > 0) {
      convertKeywords();
    }
  }, [data]);

  if (!data || data.length === 0) {
    return (
      <div className={`flex items-center justify-center p-4 bg-gray-100 rounded-lg ${className}`}>
        <span className="text-gray-500 text-sm">출력할 키워드가 없습니다</span>
      </div>
    );
  }

  return (
    <div className={`space-y-3 ${className}`}>
      {data.map((keyword, index) => {
        const cells = brailleData[keyword] || [];
        
        return (
          <div key={index} className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
            {/* 키워드 텍스트 */}
            <div className="flex-shrink-0">
              <span className="text-sm font-medium text-blue-800 bg-blue-100 px-2 py-1 rounded">
                {keyword}
              </span>
            </div>
            
            {/* 점자 셀들 */}
            <div className="flex items-center gap-1">
              {cells.length > 0 ? (
                cells.map((cell, cellIndex) => (
                  <BrailleCell key={cellIndex} cell={cell} />
                ))
              ) : (
                <div className="text-xs text-gray-400 italic">
                  점자 변환 중...
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default BrailleCells;
