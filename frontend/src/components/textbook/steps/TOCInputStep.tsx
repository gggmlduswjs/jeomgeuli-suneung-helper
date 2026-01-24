/**
 * TOC(목차) 입력 스텝
 * 목차 페이지 번호 입력 → 텍스트 자동 추출 → 강의 목록 분석
 */
import { FileText, Sparkles } from 'lucide-react';

interface TOCInputStepProps {
  tocPages: string;
  tocText: string;
  tocLectureExamples: string;
  tocNonLectureExamples: string;
  expectedLectureCount: string;
  extractedTextExamples: { [key: string]: string[] } | null;
  extractingText: boolean;
  extractingTocText: boolean;
  cleaningTocText: boolean;
  onTocPagesChange: (pages: string) => void;
  onTocTextChange: (text: string) => void;
  onLectureExamplesChange: (text: string) => void;
  onNonLectureExamplesChange: (text: string) => void;
  onExpectedCountChange: (count: string) => void;
  onExtractTocText: () => void;
  onCleanTocText: () => void;
  onExtractTextExamples: () => void;
}

export default function TOCInputStep({
  tocPages,
  tocText,
  tocLectureExamples,
  tocNonLectureExamples,
  expectedLectureCount,
  extractedTextExamples,
  extractingText,
  extractingTocText,
  cleaningTocText,
  onTocPagesChange,
  onTocTextChange,
  onLectureExamplesChange,
  onNonLectureExamplesChange,
  onExpectedCountChange,
  onExtractTocText,
  onCleanTocText,
  onExtractTextExamples
}: TOCInputStepProps) {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">5. 목차 입력</h3>
        <p className="text-sm text-muted-foreground mb-4">
          목차 페이지 번호를 입력하면 자동으로 텍스트를 추출합니다
        </p>
      </div>

      <div className="space-y-4">
        {/* 목차 페이지 번호 입력 */}
        <div>
          <label className="block text-sm font-medium mb-2">
            목차 페이지 번호
            <span className="text-xs text-muted-foreground ml-2">
              (쉼표로 구분, 예: 3,4,5)
            </span>
          </label>
          <input
            type="text"
            value={tocPages}
            onChange={(e) => onTocPagesChange(e.target.value)}
            className="w-full px-3 py-2 border border-border rounded-lg bg-background text-sm"
            placeholder="3,4,5"
          />
          <p className="text-xs text-muted-foreground mt-1">
            목차가 있는 PDF 페이지 번호를 입력하세요
          </p>
        </div>

        {/* 목차 텍스트 추출 버튼 */}
        <button
          onClick={onExtractTocText}
          disabled={extractingTocText || !tocPages.trim()}
          className="w-full px-4 py-3 bg-primary/10 text-primary rounded-lg hover:bg-primary/20 transition-colors flex items-center justify-center gap-2 disabled:opacity-50 font-medium"
        >
          <Sparkles className="w-4 h-4" />
          {extractingTocText ? '추출 중...' : 'PDF에서 목차 텍스트 추출'}
        </button>

        {/* 추출된 목차 텍스트 */}
        <div>
          <label className="block text-sm font-medium mb-2">
            목차 텍스트
            <span className="text-xs text-muted-foreground ml-2">
              (검토 및 수정 가능)
            </span>
          </label>
          <textarea
            value={tocText}
            onChange={(e) => onTocTextChange(e.target.value)}
            className="w-full px-3 py-2 border border-border rounded-lg bg-background font-mono text-sm"
            rows={12}
            placeholder="위 버튼을 클릭하여 목차 텍스트를 추출하거나 직접 붙여넣으세요...&#10;&#10;1강 문학의 이해&#10;2강 현대시의 흐름&#10;3강 고전시가..."
          />
          <p className="text-xs text-muted-foreground mt-1">
            추출된 텍스트가 올바른지 확인하고 필요시 수정하세요
          </p>

          {/* AI로 목차 텍스트 정제 버튼 */}
          {tocText.trim().length > 20 && (
            <button
              onClick={onCleanTocText}
              disabled={cleaningTocText}
              className="w-full mt-2 px-4 py-2 bg-gradient-to-r from-purple-500/10 to-blue-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20 rounded-lg hover:from-purple-500/20 hover:to-blue-500/20 transition-colors flex items-center justify-center gap-2 font-medium disabled:opacity-50"
            >
              <Sparkles className="w-4 h-4" />
              {cleaningTocText ? 'AI 정제 중...' : 'AI로 목차 텍스트 정제 (OCR 오류 수정)'}
            </button>
          )}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              강의 제목 예시 (선택)
            </label>
            <textarea
              value={tocLectureExamples}
              onChange={(e) => onLectureExamplesChange(e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-lg bg-background font-mono text-xs"
              rows={4}
              placeholder="1강 문학의 이해&#10;2강 현대시의 흐름"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">
              비강의 텍스트 예시 (선택)
            </label>
            <textarea
              value={tocNonLectureExamples}
              onChange={(e) => onNonLectureExamplesChange(e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-lg bg-background font-mono text-xs"
              rows={4}
              placeholder="목차&#10;부록&#10;참고문헌"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">
            예상 강의 수 (선택)
          </label>
          <input
            type="text"
            value={expectedLectureCount}
            onChange={(e) => onExpectedCountChange(e.target.value)}
            className="w-full px-3 py-2 border border-border rounded-lg bg-background"
            placeholder="예: 20"
          />
          <p className="text-xs text-muted-foreground mt-1">
            AI가 자동으로 추측하지만, 정확한 수를 입력하면 더 정확한 결과를 얻을 수 있습니다.
          </p>
        </div>

        {/* 텍스트 예시 추출 버튼 */}
        <button
          onClick={onExtractTextExamples}
          disabled={extractingText}
          className="w-full px-4 py-3 bg-secondary hover:bg-secondary/80 rounded-lg transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
        >
          <FileText className="w-4 h-4" />
          {extractingText ? '추출 중...' : 'PDF에서 텍스트 예시 자동 추출'}
        </button>

        {/* 추출된 텍스트 예시 표시 */}
        {extractedTextExamples && Object.keys(extractedTextExamples).length > 0 && (
          <div className="p-4 bg-card border border-border rounded-lg">
            <div className="text-sm font-medium mb-3">
              추출된 텍스트 예시 (자동)
            </div>
            <div className="space-y-2 text-xs">
              {Object.entries(extractedTextExamples).map(([page, examples]) => (
                <div key={page} className="p-2 bg-background rounded">
                  <div className="font-medium text-muted-foreground mb-1">
                    페이지 {page}:
                  </div>
                  <div className="space-y-1 font-mono text-[10px]">
                    {examples.slice(0, 3).map((ex, idx) => (
                      <div key={idx} className="truncate">{ex}</div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              ℹ️ 이 예시들은 AI가 패턴을 학습하는 데 사용됩니다.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
