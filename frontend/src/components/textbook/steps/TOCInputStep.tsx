/**
 * TOC(목차) 입력 스텝
 * 목차 텍스트 입력 및 텍스트 예시 추출
 */
import { FileText } from 'lucide-react';

interface TOCInputStepProps {
  tocText: string;
  tocLectureExamples: string;
  tocNonLectureExamples: string;
  expectedLectureCount: string;
  extractedTextExamples: { [key: string]: string[] } | null;
  extractingText: boolean;
  onTocTextChange: (text: string) => void;
  onLectureExamplesChange: (text: string) => void;
  onNonLectureExamplesChange: (text: string) => void;
  onExpectedCountChange: (count: string) => void;
  onExtractTextExamples: () => void;
}

export default function TOCInputStep({
  tocText,
  tocLectureExamples,
  tocNonLectureExamples,
  expectedLectureCount,
  extractedTextExamples,
  extractingText,
  onTocTextChange,
  onLectureExamplesChange,
  onNonLectureExamplesChange,
  onExpectedCountChange,
  onExtractTextExamples
}: TOCInputStepProps) {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">5. 목차 입력</h3>
        <p className="text-sm text-muted-foreground mb-4">
          교재의 목차를 붙여넣어 주세요
        </p>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">
            목차 텍스트
            <span className="text-xs text-muted-foreground ml-2">
              (PDF에서 복사하거나 직접 입력)
            </span>
          </label>
          <textarea
            value={tocText}
            onChange={(e) => onTocTextChange(e.target.value)}
            className="w-full px-3 py-2 border border-border rounded-lg bg-background font-mono text-sm"
            rows={12}
            placeholder="1강 문학의 이해&#10;2강 현대시의 흐름&#10;3강 고전시가..."
          />
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
