/**
 * 그래프 미리보기 컴포넌트
 * 그래프 패턴 청크일 때 표시
 */
import { BarChart3 } from 'lucide-react';

interface GraphPreviewProps {
  chunk: {
    id: number;
    text: string;
    cells: number[][];
    semanticType: string;
  };
}

export default function GraphPreview({ chunk }: GraphPreviewProps) {
  // TODO: 실제 그래프 이미지 표시
  // 현재는 기본 구조만 제공

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex items-center gap-2 mb-3">
        <BarChart3 className="w-5 h-5 text-blue-600" />
        <h4 className="text-sm font-semibold text-gray-800">그래프 분석 결과</h4>
      </div>
      
      <div className="bg-gray-50 rounded p-3 text-sm text-gray-700">
        {chunk.text}
      </div>
      
      <div className="mt-3 text-xs text-gray-500">
        점자 패턴: {chunk.semanticType}
      </div>
    </div>
  );
}

