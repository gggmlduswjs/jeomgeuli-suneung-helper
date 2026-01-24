/**
 * 템플릿 고급 설정 컴포넌트
 * 폰트 정보, 레이아웃 정보, 문제 패턴, 섹션 간격 설정
 */

interface FontInfo {
  size?: number;
  weight?: string;
  family?: string;
}

interface LayoutInfo {
  header_height?: number;
  footer_height?: number;
  content_area?: {
    x_min?: number;
    y_min?: number;
    x_max?: number;
    y_max?: number;
  };
}

interface ProblemPatterns {
  number_format?: string;
  number_position?: string;
  example_numbers?: string[];
}

interface SectionSpacing {
  concept_to_passage?: number;
  passage_to_problem?: number;
  problem_to_problem?: number;
  min_section_height?: number;
  max_section_height?: number;
}

interface TemplateConfig {
  font_info?: Record<string, FontInfo>;
  layout_info?: LayoutInfo;
  problem_patterns?: ProblemPatterns;
  section_spacing?: SectionSpacing;
  [key: string]: unknown;
}

interface TemplateAdvancedConfigProps {
  config: TemplateConfig;
  onUpdateConfig: (config: TemplateConfig) => void;
}

export default function TemplateAdvancedConfig({
  config,
  onUpdateConfig
}: TemplateAdvancedConfigProps) {
  return (
    <div className="mb-6">
      <h3 className="text-lg font-semibold mb-3">고급 설정 (Priority 1)</h3>

      {/* 폰트 정보 */}
      <div className="mb-4 p-4 border border-border rounded-lg">
        <h4 className="text-sm font-medium mb-3">폰트 정보</h4>
        <div className="space-y-3">
          {['concept_title', 'passage_title', 'problem_number', 'body_text'].map((fontType) => {
            const fontInfo = config.font_info || {};
            const font = fontInfo[fontType] || { size: 0, weight: 'normal', family: '' };

            return (
              <div key={fontType} className="p-3 bg-card rounded border border-border">
                <label className="block text-xs font-medium mb-2 capitalize">{fontType.replace('_', ' ')}</label>
                <div className="grid grid-cols-3 gap-2">
                  <div>
                    <label className="block text-xs text-muted-foreground mb-1">크기</label>
                    <input
                      type="number"
                      step="0.1"
                      value={font.size || ''}
                      onChange={(e) => {
                        const value = parseFloat(e.target.value) || 0;
                        onUpdateConfig({
                          ...config,
                          font_info: {
                            ...(config.font_info || {}),
                            [fontType]: {
                              ...font,
                              size: value
                            }
                          }
                        });
                      }}
                      className="w-full px-2 py-1 text-xs border border-border rounded bg-background"
                      placeholder="14.0"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-muted-foreground mb-1">Weight</label>
                    <select
                      value={font.weight || 'normal'}
                      onChange={(e) => {
                        onUpdateConfig({
                          ...config,
                          font_info: {
                            ...(config.font_info || {}),
                            [fontType]: {
                              ...font,
                              weight: e.target.value
                            }
                          }
                        });
                      }}
                      className="w-full px-2 py-1 text-xs border border-border rounded bg-background"
                    >
                      <option value="normal">normal</option>
                      <option value="bold">bold</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs text-muted-foreground mb-1">Family</label>
                    <input
                      type="text"
                      value={font.family || ''}
                      onChange={(e) => {
                        onUpdateConfig({
                          ...config,
                          font_info: {
                            ...(config.font_info || {}),
                            [fontType]: {
                              ...font,
                              family: e.target.value
                            }
                          }
                        });
                      }}
                      className="w-full px-2 py-1 text-xs border border-border rounded bg-background"
                      placeholder="NanumGothic"
                    />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 레이아웃 정보 */}
      <div className="mb-4 p-4 border border-border rounded-lg">
        <h4 className="text-sm font-medium mb-3">레이아웃 정보</h4>
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium mb-1">헤더 높이 (px)</label>
              <input
                type="number"
                value={config.layout_info?.header_height || ''}
                onChange={(e) => {
                  const value = parseInt(e.target.value) || 0;
                  onUpdateConfig({
                    ...config,
                    layout_info: {
                      ...(config.layout_info || {}),
                      header_height: value
                    }
                  });
                }}
                className="w-full px-2 py-1 text-xs border border-border rounded bg-background"
              />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">푸터 높이 (px)</label>
              <input
                type="number"
                value={config.layout_info?.footer_height || ''}
                onChange={(e) => {
                  const value = parseInt(e.target.value) || 0;
                  onUpdateConfig({
                    ...config,
                    layout_info: {
                      ...(config.layout_info || {}),
                      footer_height: value
                    }
                  });
                }}
                className="w-full px-2 py-1 text-xs border border-border rounded bg-background"
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium mb-2">콘텐츠 영역 (픽셀)</label>
            <div className="grid grid-cols-4 gap-2">
              {(['x_min', 'y_min', 'x_max', 'y_max'] as const).map((coord) => (
                <div key={coord}>
                  <label className="block text-xs text-muted-foreground mb-1">{coord}</label>
                  <input
                    type="number"
                    value={config.layout_info?.content_area?.[coord] || ''}
                    onChange={(e) => {
                      const value = parseInt(e.target.value) || 0;
                      onUpdateConfig({
                        ...config,
                        layout_info: {
                          ...(config.layout_info || {}),
                          content_area: {
                            ...(config.layout_info?.content_area || {}),
                            [coord]: value
                          }
                        }
                      });
                    }}
                    className="w-full px-2 py-1 text-xs border border-border rounded bg-background"
                  />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 문제 패턴 */}
      <div className="mb-4 p-4 border border-border rounded-lg">
        <h4 className="text-sm font-medium mb-3">문제 번호 패턴 상세</h4>
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium mb-1">번호 형식</label>
            <input
              type="text"
              value={config.problem_patterns?.number_format || ''}
              onChange={(e) => {
                onUpdateConfig({
                  ...config,
                  problem_patterns: {
                    ...(config.problem_patterns || {}),
                    number_format: e.target.value
                  }
                });
              }}
              placeholder="1."
              className="w-full px-2 py-1 text-xs border border-border rounded bg-background font-mono"
            />
          </div>
          <div>
            <label className="block text-xs font-medium mb-1">번호 위치</label>
            <select
              value={config.problem_patterns?.number_position || 'start_of_line'}
              onChange={(e) => {
                onUpdateConfig({
                  ...config,
                  problem_patterns: {
                    ...(config.problem_patterns || {}),
                    number_position: e.target.value
                  }
                });
              }}
              className="w-full px-2 py-1 text-xs border border-border rounded bg-background"
            >
              <option value="start_of_line">줄 시작</option>
              <option value="inline">인라인</option>
              <option value="margin">여백</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium mb-1">예시 번호 (쉼표로 구분)</label>
            <input
              type="text"
              value={Array.isArray(config.problem_patterns?.example_numbers)
                ? config.problem_patterns.example_numbers.join(', ')
                : ''}
              onChange={(e) => {
                const examples = e.target.value.split(',').map(s => s.trim()).filter(Boolean);
                onUpdateConfig({
                  ...config,
                  problem_patterns: {
                    ...(config.problem_patterns || {}),
                    example_numbers: examples
                  }
                });
              }}
              placeholder="1., 2., 3., 4., 5."
              className="w-full px-2 py-1 text-xs border border-border rounded bg-background"
            />
          </div>
        </div>
      </div>

      {/* 섹션 간격 */}
      <div className="mb-4 p-4 border border-border rounded-lg">
        <h4 className="text-sm font-medium mb-3">섹션 간 간격 (픽셀)</h4>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium mb-1">Concept → Passage</label>
            <input
              type="number"
              value={config.section_spacing?.concept_to_passage || ''}
              onChange={(e) => {
                const value = parseInt(e.target.value) || 0;
                onUpdateConfig({
                  ...config,
                  section_spacing: {
                    ...(config.section_spacing || {}),
                    concept_to_passage: value
                  }
                });
              }}
              className="w-full px-2 py-1 text-xs border border-border rounded bg-background"
            />
          </div>
          <div>
            <label className="block text-xs font-medium mb-1">Passage → Problem</label>
            <input
              type="number"
              value={config.section_spacing?.passage_to_problem || ''}
              onChange={(e) => {
                const value = parseInt(e.target.value) || 0;
                onUpdateConfig({
                  ...config,
                  section_spacing: {
                    ...(config.section_spacing || {}),
                    passage_to_problem: value
                  }
                });
              }}
              className="w-full px-2 py-1 text-xs border border-border rounded bg-background"
            />
          </div>
          <div>
            <label className="block text-xs font-medium mb-1">Problem → Problem</label>
            <input
              type="number"
              value={config.section_spacing?.problem_to_problem || ''}
              onChange={(e) => {
                const value = parseInt(e.target.value) || 0;
                onUpdateConfig({
                  ...config,
                  section_spacing: {
                    ...(config.section_spacing || {}),
                    problem_to_problem: value
                  }
                });
              }}
              className="w-full px-2 py-1 text-xs border border-border rounded bg-background"
            />
          </div>
          <div>
            <label className="block text-xs font-medium mb-1">최소 섹션 높이</label>
            <input
              type="number"
              value={config.section_spacing?.min_section_height || ''}
              onChange={(e) => {
                const value = parseInt(e.target.value) || 0;
                onUpdateConfig({
                  ...config,
                  section_spacing: {
                    ...(config.section_spacing || {}),
                    min_section_height: value
                  }
                });
              }}
              className="w-full px-2 py-1 text-xs border border-border rounded bg-background"
            />
          </div>
          <div>
            <label className="block text-xs font-medium mb-1">최대 섹션 높이</label>
            <input
              type="number"
              value={config.section_spacing?.max_section_height || ''}
              onChange={(e) => {
                const value = parseInt(e.target.value) || 0;
                onUpdateConfig({
                  ...config,
                  section_spacing: {
                    ...(config.section_spacing || {}),
                    max_section_height: value
                  }
                });
              }}
              className="w-full px-2 py-1 text-xs border border-border rounded bg-background"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
