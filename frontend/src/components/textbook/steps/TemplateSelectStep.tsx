/**
 * 템플릿 선택 스텝
 * 기존 템플릿 선택 또는 새 템플릿 생성 선택
 */
import { FileText, Sparkles } from 'lucide-react';
import type { ParsingTemplate } from '../../../services/templates';

interface TemplateSelectStepProps {
  availableTemplates: ParsingTemplate[];
  selectedTemplate: ParsingTemplate | null;
  loadingTemplates: boolean;
  onTemplateSelect: (template: ParsingTemplate | null) => void;
  onCreateNew: () => void;
}

export default function TemplateSelectStep({
  availableTemplates,
  selectedTemplate,
  loadingTemplates,
  onTemplateSelect,
  onCreateNew
}: TemplateSelectStepProps) {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">2. 템플릿 선택</h3>
        <p className="text-sm text-muted-foreground mb-4">
          기존 템플릿을 선택하거나 새로운 템플릿을 생성하세요
        </p>
      </div>

      {loadingTemplates ? (
        <div className="text-center py-8 text-muted-foreground">
          템플릿 목록을 불러오는 중...
        </div>
      ) : (
        <div className="space-y-3">
          {/* 새 템플릿 생성 옵션 */}
          <button
            onClick={onCreateNew}
            className="w-full p-4 border-2 border-dashed border-primary rounded-lg hover:bg-primary/5 transition-colors text-left flex items-center gap-3"
          >
            <Sparkles className="w-5 h-5 text-primary" />
            <div>
              <div className="font-medium">새 템플릿 생성</div>
              <div className="text-xs text-muted-foreground">
                AI가 PDF를 분석하여 자동으로 템플릿을 생성합니다
              </div>
            </div>
          </button>

          {/* 기존 템플릿 목록 */}
          {availableTemplates.length > 0 && (
            <>
              <div className="text-sm font-medium mt-6 mb-2">기존 템플릿</div>
              {availableTemplates.map((template) => (
                <button
                  key={`${template.subject}-${template.name}`}
                  onClick={() => onTemplateSelect(
                    selectedTemplate?.name === template.name ? null : template
                  )}
                  className={`w-full p-4 border rounded-lg text-left transition-colors flex items-center gap-3 ${
                    selectedTemplate?.name === template.name
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-primary/50'
                  }`}
                >
                  <FileText className={`w-5 h-5 ${
                    selectedTemplate?.name === template.name
                      ? 'text-primary'
                      : 'text-muted-foreground'
                  }`} />
                  <div className="flex-1">
                    <div className="font-medium">{template.name}</div>
                    {template.description && (
                      <div className="text-xs text-muted-foreground mt-1">
                        {template.description}
                      </div>
                    )}
                    <div className="text-xs text-muted-foreground mt-1">
                      버전: {template.version}
                    </div>
                  </div>
                </button>
              ))}
            </>
          )}

          {availableTemplates.length === 0 && (
            <div className="text-center py-8 text-muted-foreground text-sm">
              사용 가능한 템플릿이 없습니다. 새 템플릿을 생성해주세요.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
