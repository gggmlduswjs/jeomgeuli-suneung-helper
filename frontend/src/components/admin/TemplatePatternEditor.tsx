/**
 * 템플릿 패턴 편집 컴포넌트
 * 강의 제목, 목차, 문제 번호, 개념 제목, 본문 헤더, 섹션 제목 패턴 관리
 */
import { Plus, Trash2 } from 'lucide-react';

type PatternKey =
  | 'lecture_title_patterns'
  | 'toc_lecture_patterns'
  | 'concept_title_patterns'
  | 'content_header_patterns'
  | 'section_title_patterns';

interface TemplatePatterns {
  lecture_title_patterns?: string[];
  toc_lecture_patterns?: string[];
  concept_title_patterns?: string[];
  content_header_patterns?: string[];
  section_title_patterns?: string[];
  problem_number_pattern?: string;
  [key: string]: unknown;
}

interface TemplatePatternEditorProps {
  patterns: TemplatePatterns;
  onUpdatePatterns: (patterns: TemplatePatterns) => void;
}

export default function TemplatePatternEditor({
  patterns,
  onUpdatePatterns
}: TemplatePatternEditorProps) {
  const addPattern = (patternType: PatternKey) => {
    const current = (patterns[patternType] || []) as string[];
    const patternArray = Array.isArray(current) ? current : [];
    onUpdatePatterns({
      ...patterns,
      [patternType]: [...patternArray, '']
    });
  };

  const updatePattern = (patternType: PatternKey, index: number, value: string) => {
    const patternArray = [...(((patterns[patternType] || []) as string[]) || [])];
    patternArray[index] = value;
    onUpdatePatterns({
      ...patterns,
      [patternType]: patternArray
    });
  };

  const removePattern = (patternType: PatternKey, index: number) => {
    const patternArray = [...(((patterns[patternType] || []) as string[]) || [])];
    patternArray.splice(index, 1);
    onUpdatePatterns({
      ...patterns,
      [patternType]: patternArray
    });
  };

  return (
    <div className="mb-6">
      <h3 className="text-lg font-semibold mb-3">패턴 설정</h3>

      {/* 강의 제목 패턴 */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <label className="text-sm font-medium">강의 제목 패턴</label>
          <button
            onClick={() => addPattern('lecture_title_patterns')}
            className="px-2 py-1 text-xs bg-primary/10 text-primary rounded hover:bg-primary/20 transition-colors flex items-center gap-1"
          >
            <Plus className="w-3 h-3" />
            추가
          </button>
        </div>
        <div className="space-y-2">
          {(patterns.lecture_title_patterns || []).map((pattern, index) => (
            <div key={index} className="flex gap-2">
              <input
                type="text"
                value={pattern}
                onChange={(e) => updatePattern('lecture_title_patterns', index, e.target.value)}
                placeholder="예: ^\\d+강\\s+[가-힣]+"
                className="flex-1 px-3 py-2 border border-border rounded-lg bg-background text-sm font-mono"
              />
              <button
                onClick={() => removePattern('lecture_title_patterns', index)}
                className="px-3 py-2 text-danger hover:bg-danger/10 rounded-lg transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* 목차 강의 패턴 */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <label className="text-sm font-medium">목차 강의 패턴 (TOC 기반 강의목록)</label>
          <button
            onClick={() => addPattern('toc_lecture_patterns')}
            className="px-2 py-1 text-xs bg-primary/10 text-primary rounded hover:bg-primary/20 transition-colors flex items-center gap-1"
          >
            <Plus className="w-3 h-3" />
            추가
          </button>
        </div>
        <div className="space-y-2">
          {(patterns.toc_lecture_patterns || []).map((pattern, index) => (
            <div key={index} className="flex gap-2">
              <input
                type="text"
                value={pattern}
                onChange={(e) => updatePattern('toc_lecture_patterns', index, e.target.value)}
                placeholder="예: ^\\d+강\\s*\\|\\s*"
                className="flex-1 px-3 py-2 border border-border rounded-lg bg-background text-sm font-mono"
              />
              <button
                onClick={() => removePattern('toc_lecture_patterns', index)}
                className="px-3 py-2 text-danger hover:bg-danger/10 rounded-lg transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* 문제 번호 패턴 */}
      <div className="mb-4">
        <label className="block text-sm font-medium mb-2">문제 번호 패턴</label>
        <input
          type="text"
          value={patterns.problem_number_pattern || ''}
          onChange={(e) => onUpdatePatterns({
            ...patterns,
            problem_number_pattern: e.target.value
          })}
          placeholder="예: ^\\d+\\."
          className="w-full px-3 py-2 border border-border rounded-lg bg-background text-sm font-mono"
        />
      </div>

      {/* 개념 제목 패턴 */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <label className="text-sm font-medium">개념 제목 패턴</label>
          <button
            onClick={() => addPattern('concept_title_patterns')}
            className="px-2 py-1 text-xs bg-primary/10 text-primary rounded hover:bg-primary/20 transition-colors flex items-center gap-1"
          >
            <Plus className="w-3 h-3" />
            추가
          </button>
        </div>
        <div className="space-y-2">
          {(patterns.concept_title_patterns || []).map((pattern, index) => (
            <div key={index} className="flex gap-2">
              <input
                type="text"
                value={pattern}
                onChange={(e) => updatePattern('concept_title_patterns', index, e.target.value)}
                placeholder="예: ^\\(\\d+\\)\\s+[가-힣]+"
                className="flex-1 px-3 py-2 border border-border rounded-lg bg-background text-sm font-mono"
              />
              <button
                onClick={() => removePattern('concept_title_patterns', index)}
                className="px-3 py-2 text-danger hover:bg-danger/10 rounded-lg transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* 본문 헤더 패턴 */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <label className="text-sm font-medium">본문 헤더 패턴</label>
          <button
            onClick={() => addPattern('content_header_patterns')}
            className="px-2 py-1 text-xs bg-primary/10 text-primary rounded hover:bg-primary/20 transition-colors flex items-center gap-1"
          >
            <Plus className="w-3 h-3" />
            추가
          </button>
        </div>
        <div className="space-y-2">
          {(patterns.content_header_patterns || []).map((pattern, index) => (
            <div key={index} className="flex gap-2">
              <input
                type="text"
                value={pattern}
                onChange={(e) => updatePattern('content_header_patterns', index, e.target.value)}
                placeholder="예: ^작품으로 이해하기"
                className="flex-1 px-3 py-2 border border-border rounded-lg bg-background text-sm font-mono"
              />
              <button
                onClick={() => removePattern('content_header_patterns', index)}
                className="px-3 py-2 text-danger hover:bg-danger/10 rounded-lg transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* 섹션 제목 패턴 */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <label className="text-sm font-medium">섹션 제목 패턴</label>
          <button
            onClick={() => addPattern('section_title_patterns')}
            className="px-2 py-1 text-xs bg-primary/10 text-primary rounded hover:bg-primary/20 transition-colors flex items-center gap-1"
          >
            <Plus className="w-3 h-3" />
            추가
          </button>
        </div>
        <div className="space-y-2">
          {(patterns.section_title_patterns || []).map((pattern, index) => (
            <div key={index} className="flex gap-2">
              <input
                type="text"
                value={pattern}
                onChange={(e) => updatePattern('section_title_patterns', index, e.target.value)}
                placeholder="예: ^\\d+\\."
                className="flex-1 px-3 py-2 border border-border rounded-lg bg-background text-sm font-mono"
              />
              <button
                onClick={() => removePattern('section_title_patterns', index)}
                className="px-3 py-2 text-danger hover:bg-danger/10 rounded-lg transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
