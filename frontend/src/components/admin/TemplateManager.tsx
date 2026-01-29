/**
 * 템플릿 관리 컴포넌트
 * 템플릿 목록, 편집, 복사, 테스트 기능
 */
import { useEffect, useState } from 'react';
import { templatesAPI, type ParsingTemplate } from '../../services/templates';
import { 
  FileText, 
  Copy, 
  Edit, 
  Trash2, 
  ChevronLeft,
  Sparkles
} from 'lucide-react';
import TemplateEditor from './TemplateEditor';

interface TemplateManagerProps {
  onBack: () => void;
  onSpeak?: (message: string) => void;
  onCreateTemplate?: () => void;
}

export default function TemplateManager({ onBack, onSpeak, onCreateTemplate }: TemplateManagerProps) {
  const [templates, setTemplates] = useState<ParsingTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSubject, setSelectedSubject] = useState<string | undefined>(undefined);
  const [editingTemplate, setEditingTemplate] = useState<ParsingTemplate | null>(null);

  useEffect(() => {
    loadTemplates();
  }, [selectedSubject]);

  const loadTemplates = async () => {
    setLoading(true);
    try {
      const data = await templatesAPI.list(selectedSubject);
      setTemplates(data);
    } catch (err) {
      console.error('[TemplateManager] Failed to load templates:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async (template: ParsingTemplate) => {
    try {
      const newName = `${template.name}_copy`;
      const newVersion = template.version ? String(parseInt(template.version) + 1) : template.version;
      await templatesAPI.copy(template.subject, template.name, newName, newVersion);
      onSpeak?.('템플릿이 복사되었습니다.');
      await loadTemplates();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '템플릿 복사 실패';
      onSpeak?.(message);
    }
  };

  const handleDelete = async (template: ParsingTemplate) => {
    if (!confirm(`정말 "${template.name}" 템플릿을 삭제하시겠습니까?`)) {
      return;
    }

    try {
      await templatesAPI.delete(template.subject, template.name);
      onSpeak?.('템플릿이 삭제되었습니다.');
      await loadTemplates();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '템플릿 삭제 실패';
      onSpeak?.(message);
    }
  };

  const subjects = ['literature', 'math1', 'english'];

  return (
    <div className="flex flex-col h-full">
      {/* 헤더 */}
      <div className="mb-4">
        <button
          onClick={onBack}
          className="mb-2 px-3 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center gap-2"
        >
          <ChevronLeft className="w-4 h-4" />
          뒤로가기
        </button>
        <h2 className="text-xl font-bold">템플릿 관리</h2>
        <p className="text-sm text-muted-foreground">파싱 패턴 템플릿 관리</p>
      </div>

      {/* 액션 버튼 */}
      {onCreateTemplate && (
        <div className="mb-4">
          <button
            onClick={onCreateTemplate}
            className="w-full px-4 py-3 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors flex items-center justify-center gap-2 font-medium"
          >
            <Sparkles className="w-5 h-5" />
            템플릿 생성
          </button>
        </div>
      )}

      {/* 과목 필터 */}
      <div className="mb-4 flex gap-2">
        <button
          onClick={() => setSelectedSubject(undefined)}
          className={`px-3 py-1 text-sm rounded-lg transition-colors ${
            !selectedSubject
              ? 'bg-primary text-white'
              : 'bg-secondary text-secondary-foreground'
          }`}
        >
          전체
        </button>
        {subjects.map(subject => (
          <button
            key={subject}
            onClick={() => setSelectedSubject(subject)}
            className={`px-3 py-1 text-sm rounded-lg transition-colors ${
              selectedSubject === subject
                ? 'bg-primary text-white'
                : 'bg-secondary text-secondary-foreground'
            }`}
          >
            {subject === 'literature' ? '문학' : subject === 'math1' ? '수학' : '영어'}
          </button>
        ))}
      </div>

      {/* 템플릿 목록 */}
      {loading ? (
        <div className="flex-1 flex items-center justify-center">
          <p className="text-muted">로딩 중...</p>
        </div>
      ) : templates.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center py-12">
          <FileText className="w-16 h-16 text-muted-foreground mb-4" />
          <p className="text-muted-foreground mb-4">템플릿이 없습니다.</p>
        </div>
      ) : editingTemplate ? (
        <div className="flex-1 overflow-hidden">
          <TemplateEditor
            template={editingTemplate}
            mode="edit"
            onSave={() => {
              setEditingTemplate(null);
              loadTemplates();
            }}
            onCancel={() => setEditingTemplate(null)}
            onSpeak={onSpeak}
          />
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto space-y-3">
          {templates.map((template) => (
            <div
              key={`${template.subject}_${template.name}`}
              className="bg-card border border-border rounded-lg p-4"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <h3 className="font-semibold text-lg mb-1">{template.name}</h3>
                  <div className="flex items-center gap-3 text-sm text-muted-foreground mb-2">
                    <span>{template.subject === 'literature' ? '문학' : template.subject === 'math1' ? '수학' : '영어'}</span>
                    {template.version && <span>• {template.version}년</span>}
                    <span>• 신뢰도: {Math.round(template.confidence * 100)}%</span>
                  </div>
                  {template.description && (
                    <p className="text-sm text-muted-foreground mb-2">{template.description}</p>
                  )}
                </div>
              </div>

              {/* 패턴 미리보기 */}
              <div className="mb-3 text-xs text-muted-foreground">
                <div>강의 패턴: {template.patterns.lecture_title_patterns?.length || 0}개</div>
                <div>문제 패턴: {template.patterns.problem_number_pattern ? '1개' : '0개'}</div>
              </div>

              {/* 액션 버튼 */}
              <div className="flex gap-2">
                <button
                  onClick={() => handleCopy(template)}
                  className="flex-1 px-3 py-2 text-sm bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 transition-colors flex items-center justify-center gap-2"
                >
                  <Copy className="w-4 h-4" />
                  복사
                </button>
                <button
                  onClick={() => setEditingTemplate(template)}
                  className="flex-1 px-3 py-2 text-sm bg-primary/10 text-primary border border-primary/30 rounded-lg hover:bg-primary/20 transition-colors flex items-center justify-center gap-2"
                >
                  <Edit className="w-4 h-4" />
                  편집
                </button>
                <button
                  onClick={() => handleDelete(template)}
                  className="px-3 py-2 text-sm bg-danger/10 text-danger border border-danger/30 rounded-lg hover:bg-danger/20 transition-colors flex items-center justify-center gap-2"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
