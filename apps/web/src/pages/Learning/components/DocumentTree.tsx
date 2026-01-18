/**
 * 지문/문항 구조 트리 (보호자용)
 * 왼쪽 패널에 표시되는 문서 구조
 */
import { useState, useEffect } from 'react';
import { ChevronRight, ChevronDown, FileText, HelpCircle } from 'lucide-react';

interface DocumentTreeProps {
  unitId?: number;
  passageId?: number;
  questionId?: number;
  currentChunkIndex: number;
  onChunkSelect: (index: number) => void;
}

interface TreeNode {
  id: number;
  type: 'passage' | 'question' | 'choice';
  title: string;
  chunks: Array<{ index: number; text: string }>;
  expanded?: boolean;
  children?: TreeNode[];
}

export default function DocumentTree({
  unitId,
  passageId,
  questionId,
  currentChunkIndex,
  onChunkSelect
}: DocumentTreeProps) {
  const [tree, setTree] = useState<TreeNode[]>([]);
  const [expandedNodes, setExpandedNodes] = useState<Set<number>>(new Set());

  // TODO: API에서 문서 구조 가져오기
  useEffect(() => {
    // 예시 데이터
    const mockTree: TreeNode[] = [
      {
        id: 1,
        type: 'passage',
        title: '지문 1',
        chunks: [
          { index: 0, text: '첫 번째 문장...' },
          { index: 1, text: '두 번째 문장...' }
        ]
      },
      {
        id: 2,
        type: 'question',
        title: '문항 1',
        chunks: [
          { index: 2, text: '문제 내용...' }
        ],
        children: [
          {
            id: 3,
            type: 'choice',
            title: '① 선택지 1',
            chunks: [{ index: 3, text: '선택지 내용...' }]
          }
        ]
      }
    ];
    setTree(mockTree);
  }, [unitId, passageId, questionId]);

  const toggleNode = (nodeId: number) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(nodeId)) {
      newExpanded.delete(nodeId);
    } else {
      newExpanded.add(nodeId);
    }
    setExpandedNodes(newExpanded);
  };

  const renderNode = (node: TreeNode, level: number = 0) => {
    const isExpanded = expandedNodes.has(node.id);
    const hasChildren = node.children && node.children.length > 0;
    const isCurrent = node.chunks.some(chunk => chunk.index === currentChunkIndex);

    return (
      <div key={node.id} className="select-none">
        <div
          className={`flex items-center gap-2 px-3 py-2 cursor-pointer hover:bg-gray-100 transition-colors ${
            isCurrent ? 'bg-blue-50 border-l-2 border-blue-500' : ''
          }`}
          style={{ paddingLeft: `${12 + level * 16}px` }}
          onClick={() => {
            if (hasChildren) {
              toggleNode(node.id);
            } else if (node.chunks.length > 0) {
              onChunkSelect(node.chunks[0].index);
            }
          }}
        >
          {hasChildren ? (
            isExpanded ? (
              <ChevronDown className="w-4 h-4 text-gray-500" />
            ) : (
              <ChevronRight className="w-4 h-4 text-gray-500" />
            )
          ) : (
            <div className="w-4" />
          )}
          
          {node.type === 'passage' ? (
            <FileText className="w-4 h-4 text-blue-600" />
          ) : node.type === 'question' ? (
            <HelpCircle className="w-4 h-4 text-green-600" />
          ) : (
            <div className="w-4 h-4 rounded-full bg-gray-300" />
          )}
          
          <span className="text-sm font-medium text-gray-800 flex-1">
            {node.title}
          </span>
          
          {node.chunks.length > 0 && (
            <span className="text-xs text-gray-500">
              {node.chunks.length}개
            </span>
          )}
        </div>
        
        {hasChildren && isExpanded && (
          <div>
            {node.children!.map(child => renderNode(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-gray-200 bg-gray-50">
        <h3 className="text-sm font-semibold text-gray-700">문서 구조</h3>
      </div>
      
      <div className="flex-1 overflow-y-auto">
        {tree.map(node => renderNode(node))}
      </div>
    </div>
  );
}

