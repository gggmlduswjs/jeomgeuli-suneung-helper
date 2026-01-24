/**
 * 템플릿 편집 컴포넌트
 * 패턴 추가/수정, 테스트 기능
 */
import { useState } from 'react';
import { templatesAPI, type ParsingTemplate } from '../../services/templates';
import { Save, X } from 'lucide-react';
import TemplatePatternEditor from './TemplatePatternEditor';
import TemplateAdvancedConfig from './TemplateAdvancedConfig';
import TemplateTestPanel from './TemplateTestPanel';

interface TemplateEditorProps {
  template: ParsingTemplate;
  mode?: 'edit' | 'create';
  onSave: (template: ParsingTemplate) => void;
  onCancel: () => void;
  onSpeak?: (message: string) => void;
}

export default function TemplateEditor({ template, mode = 'edit', onSave, onCancel, onSpeak }: TemplateEditorProps) {
  const [editedTemplate, setEditedTemplate] = useState<ParsingTemplate>({ ...template });

  const handleSave = async () => {
    try {
      if (mode === 'create') {
        const result = await templatesAPI.create(editedTemplate);
        onSpeak?.(result.message || '템플릿이 생성되었습니다.');
        onSave(result.template);
      } else {
        await templatesAPI.update(template.subject, template.name, editedTemplate);
        onSpeak?.('템플릿이 저장되었습니다.');
        onSave(editedTemplate);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '템플릿 저장 실패';
      onSpeak?.(message);
    }
  };

  const handlePatternsDetected = (detectedPatterns: { lecture_title_patterns: string[] }) => {
    setEditedTemplate(prev => ({
      ...prev,
      patterns: {
        ...prev.patterns,
        lecture_title_patterns: [
          ...(prev.patterns.lecture_title_patterns || []),
          ...detectedPatterns.lecture_title_patterns
        ]
      }
    }));
  };

  return (
    <div className="flex flex-col h-full overflow-y-auto">
      {/* 헤더 */}
      <div className="mb-4 sticky top-0 bg-background z-10 pb-4 border-b">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-xl font-bold">{mode === 'create' ? '템플릿 생성' : '템플릿 편집'}</h2>
          <button
            onClick={onCancel}
            className="px-3 py-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <p className="text-sm text-muted-foreground">{template.name}</p>
      </div>

      {/* 기본 정보 */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-3">기본 정보</h3>
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium mb-1">이름</label>
            <input
              type="text"
              value={editedTemplate.name}
              onChange={(e) => setEditedTemplate(prev => ({ ...prev, name: e.target.value }))}
              className="w-full px-3 py-2 border border-border rounded-lg bg-background"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">버전</label>
            <input
              type="text"
              value={editedTemplate.version}
              onChange={(e) => setEditedTemplate(prev => ({ ...prev, version: e.target.value }))}
              className="w-full px-3 py-2 border border-border rounded-lg bg-background"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">설명</label>
            <textarea
              value={editedTemplate.description}
              onChange={(e) => setEditedTemplate(prev => ({ ...prev, description: e.target.value }))}
              className="w-full px-3 py-2 border border-border rounded-lg bg-background"
              rows={2}
            />
          </div>
        </div>
      </div>

      {/* 패턴 설정 */}
      <TemplatePatternEditor
        patterns={editedTemplate.patterns}
        onUpdatePatterns={(patterns) => setEditedTemplate(prev => ({ ...prev, patterns }))}
      />

      {/* 설정 */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-3">설정</h3>
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium mb-1">목차 종료 페이지</label>
            <input
              type="number"
              value={editedTemplate.config.toc_end_page || 7}
              onChange={(e) => setEditedTemplate(prev => ({
                ...prev,
                config: {
                  ...prev.config,
                  toc_end_page: parseInt(e.target.value) || 7
                }
              }))}
              className="w-full px-3 py-2 border border-border rounded-lg bg-background"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">본문 시작 페이지</label>
            <input
              type="number"
              value={editedTemplate.config.start_content_page || 8}
              onChange={(e) => setEditedTemplate(prev => ({
                ...prev,
                config: {
                  ...prev.config,
                  start_content_page: parseInt(e.target.value) || 8
                }
              }))}
              className="w-full px-3 py-2 border border-border rounded-lg bg-background"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">문단 Y 임계값</label>
            <input
              type="number"
              value={editedTemplate.config.paragraph_y_threshold || 25}
              onChange={(e) => setEditedTemplate(prev => ({
                ...prev,
                config: {
                  ...prev.config,
                  paragraph_y_threshold: parseInt(e.target.value) || 25
                }
              }))}
              className="w-full px-3 py-2 border border-border rounded-lg bg-background"
            />
          </div>
        </div>
      </div>

      {/* 커리큘럼 구조 */}
      {(editedTemplate.config.unit_order || editedTemplate.config.is_lecture_based !== undefined) && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-3">커리큘럼 구조</h3>
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium mb-1">강의 기반 구조</label>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={editedTemplate.config.is_lecture_based !== false}
                  onChange={(e) => setEditedTemplate(prev => ({
                    ...prev,
                    config: {
                      ...prev.config,
                      is_lecture_based: e.target.checked
                    }
                  }))}
                  className="w-4 h-4"
                />
                <span className="text-sm text-muted-foreground">강의 기반 구조 사용</span>
              </div>
            </div>
            {editedTemplate.config.unit_order && (
              <div>
                <label className="block text-sm font-medium mb-1">단위 순서</label>
                <div className="text-sm text-muted-foreground">
                  {editedTemplate.config.unit_order.join(' → ')}
                </div>
              </div>
            )}
            {editedTemplate.config.lecture_units && (
              <div>
                <label className="block text-sm font-medium mb-1">강의 내 단위</label>
                <div className="text-sm text-muted-foreground">
                  {editedTemplate.config.lecture_units.join(', ')}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 목차 정보 */}
      {editedTemplate.config.toc_text && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-3">목차 텍스트</h3>
          <div className="space-y-2">
            <div className="text-xs text-muted-foreground mb-2">
              길이: {editedTemplate.config.toc_text.length}자
              {editedTemplate.config.toc_lecture_list && (
                <span className="ml-2">
                  • 강의 수: {editedTemplate.config.toc_lecture_list.length}개
                </span>
              )}
            </div>
            <textarea
              value={editedTemplate.config.toc_text}
              onChange={(e) => setEditedTemplate(prev => ({
                ...prev,
                config: {
                  ...prev.config,
                  toc_text: e.target.value
                }
              }))}
              className="w-full px-3 py-2 border border-border rounded-lg bg-background text-sm font-mono"
              rows={8}
              readOnly
            />
            <p className="text-xs text-muted-foreground">읽기 전용 (템플릿 생성 시 저장됨)</p>
          </div>
        </div>
      )}

      {/* 강의 목록 */}
      {editedTemplate.config.toc_lecture_list && editedTemplate.config.toc_lecture_list.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-3">
            강의 목록 ({editedTemplate.config.toc_lecture_list.length}개)
          </h3>
          <div className="max-h-64 overflow-y-auto border border-border rounded-lg">
            <table className="w-full text-sm">
              <thead className="bg-secondary sticky top-0">
                <tr>
                  <th className="px-3 py-2 text-left">ID</th>
                  <th className="px-3 py-2 text-left">제목</th>
                  <th className="px-3 py-2 text-left">페이지</th>
                </tr>
              </thead>
              <tbody>
                {editedTemplate.config.toc_lecture_list.slice(0, 20).map((lecture, index: number) => (
                  <tr key={index} className="border-t border-border">
                    <td className="px-3 py-2">{lecture.lecture_id}</td>
                    <td className="px-3 py-2">{lecture.title}</td>
                    <td className="px-3 py-2 text-muted-foreground">
                      {lecture.start_page ? `${lecture.start_page}${lecture.end_page ? `-${lecture.end_page}` : '+'}` : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {editedTemplate.config.toc_lecture_list.length > 20 && (
              <div className="px-3 py-2 text-xs text-muted-foreground text-center border-t border-border">
                외 {editedTemplate.config.toc_lecture_list.length - 20}개 강의...
              </div>
            )}
          </div>
        </div>
      )}

      {/* 영역 정보 */}
      {(editedTemplate.config.region_hints || editedTemplate.config.region_text_examples || editedTemplate.config.region_image_examples) && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-3">영역 정보</h3>
          <div className="space-y-3">
            {editedTemplate.config.region_hints && Object.keys(editedTemplate.config.region_hints).length > 0 && (
              <div>
                <label className="block text-sm font-medium mb-1">영역 힌트 (Y 좌표)</label>
                <div className="text-xs text-muted-foreground space-y-1">
                  {Object.entries(editedTemplate.config.region_hints).map(([label, hint]: [string, any]) => (
                    <div key={label}>
                      <strong>{label}</strong>: y_min={hint.y_min?.toFixed(3)}, y_max={hint.y_max?.toFixed(3)}
                    </div>
                  ))}
                </div>
              </div>
            )}
            {editedTemplate.config.region_text_examples && Object.keys(editedTemplate.config.region_text_examples).length > 0 && (
              <div>
                <label className="block text-sm font-medium mb-1">텍스트 예시</label>
                <div className="text-xs text-muted-foreground">
                  {Object.entries(editedTemplate.config.region_text_examples).map(([label, examples]: [string, any]) => (
                    <div key={label} className="mb-1">
                      <strong>{label}</strong>: {Array.isArray(examples) ? examples.length : 0}개 예시
                    </div>
                  ))}
                </div>
              </div>
            )}
            {editedTemplate.config.region_image_examples && Object.keys(editedTemplate.config.region_image_examples).length > 0 && (
              <div>
                <label className="block text-sm font-medium mb-1">이미지 예시</label>
                <div className="text-xs text-muted-foreground">
                  {Object.entries(editedTemplate.config.region_image_examples).map(([label, images]: [string, any]) => (
                    <div key={label} className="mb-1">
                      <strong>{label}</strong>: {Array.isArray(images) ? images.length : 0}개 이미지
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 고급 설정 */}
      <TemplateAdvancedConfig
        config={editedTemplate.config}
        onUpdateConfig={(config) => setEditedTemplate(prev => ({ ...prev, config }))}
      />

      {/* 통계 정보 */}
      {(editedTemplate as any)._summary && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-3">통계 정보</h3>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="p-3 bg-card border border-border rounded-lg">
              <div className="text-xs text-muted-foreground mb-1">총 강의 수</div>
              <div className="text-lg font-semibold">{(editedTemplate as any)._summary.total_lectures || 0}</div>
            </div>
            <div className="p-3 bg-card border border-border rounded-lg">
              <div className="text-xs text-muted-foreground mb-1">페이지 정보 있는 강의</div>
              <div className="text-lg font-semibold">{(editedTemplate as any)._summary.lectures_with_pages || 0}</div>
            </div>
            <div className="p-3 bg-card border border-border rounded-lg">
              <div className="text-xs text-muted-foreground mb-1">목차 텍스트 길이</div>
              <div className="text-lg font-semibold">{(editedTemplate as any)._summary.toc_text_length || 0}자</div>
            </div>
            <div className="p-3 bg-card border border-border rounded-lg">
              <div className="text-xs text-muted-foreground mb-1">영역 정보</div>
              <div className="text-lg font-semibold">
                {[(editedTemplate as any)._summary.has_region_hints && '힌트', 
                  (editedTemplate as any)._summary.has_region_text_examples && '텍스트',
                  (editedTemplate as any)._summary.has_region_image_examples && '이미지']
                  .filter(Boolean).join(', ') || '없음'}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 테스트 섹션 */}
      <TemplateTestPanel
        subject={template.subject}
        name={template.name}
        mode={mode}
        onSpeak={onSpeak}
        onPatternsDetected={handlePatternsDetected}
      />

      {/* 저장 버튼 */}
      <div className="sticky bottom-0 bg-background pt-4 pb-2 border-t">
        <div className="flex gap-2">
          <button
            onClick={onCancel}
            className="flex-1 px-4 py-3 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 transition-colors"
          >
            취소
          </button>
          <button
            onClick={handleSave}
            className="flex-1 px-4 py-3 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors flex items-center justify-center gap-2"
          >
            <Save className="w-4 h-4" />
            저장
          </button>
        </div>
      </div>
    </div>
  );
}
