import { BrailleCells } from './BrailleCells';

interface BrailleOutputPanelProps {
  currentBraille: string[];
  className?: string;
}

export function BrailleOutputPanel({ 
  currentBraille, 
  className = "" 
}: BrailleOutputPanelProps) {
  const hasBraille = currentBraille && currentBraille.length > 0;

  return (
    <div className={`bg-white border-b border-gray-200 shadow-sm ${className}`}>
      <div className="max-w-4xl mx-auto px-4 py-3">
        {/* 헤더 */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <span className="text-lg">⠠⠃</span>
              <h3 className="text-lg font-semibold text-gray-800">
                현재 출력 중인 점자
              </h3>
            </div>
            {hasBraille && (
              <span className="text-xs bg-blue-100 text-blue-600 px-2 py-1 rounded-full font-medium">
                {currentBraille.length}개 키워드
              </span>
            )}
          </div>
          
          {/* 상태 표시 */}
          <div className="flex items-center gap-2">
            {hasBraille ? (
              <>
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-xs text-green-600 font-medium">출력 중</span>
              </>
            ) : (
              <>
                <div className="w-2 h-2 bg-gray-300 rounded-full"></div>
                <span className="text-xs text-gray-500">대기 중</span>
              </>
            )}
          </div>
        </div>

        {/* 점자 출력 영역 */}
        <div className="min-h-[60px]">
          <BrailleCells data={currentBraille} />
        </div>

        {/* 추가 정보 */}
        {hasBraille && (
          <div className="mt-2 pt-2 border-t border-gray-100">
            <p className="text-xs text-gray-500">
              💡 키워드를 점자 디스플레이로 전송하여 시각적 학습을 도와드립니다
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default BrailleOutputPanel;
