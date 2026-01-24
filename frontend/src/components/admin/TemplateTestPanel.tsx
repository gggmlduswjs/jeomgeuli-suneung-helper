/**
 * 템플릿 테스트 패널 컴포넌트
 * 샘플 텍스트 입력, 테스트/패턴 감지 기능
 */
import { useState } from 'react';
import { Play, Sparkles } from 'lucide-react';
import { templatesAPI } from '../../services/templates';

interface TestResult {
  confidence: number;
  matches: {
    lecture_title: unknown[];
    problem_number: unknown[];
  };
}

interface TemplateTestPanelProps {
  subject: string;
  name: string;
  mode: 'edit' | 'create';
  onSpeak?: (message: string) => void;
  onPatternsDetected?: (patterns: { lecture_title_patterns: string[] }) => void;
}

export default function TemplateTestPanel({
  subject,
  name,
  mode,
  onSpeak,
  onPatternsDetected
}: TemplateTestPanelProps) {
  const [testSampleText, setTestSampleText] = useState('');
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const [testing, setTesting] = useState(false);
  const [detecting, setDetecting] = useState(false);

  const handleTest = async () => {
    if (mode === 'create') {
      onSpeak?.('템플릿을 먼저 저장(생성)한 뒤 테스트할 수 있습니다.');
      return;
    }
    if (!testSampleText.trim()) {
      onSpeak?.('테스트할 샘플 텍스트를 입력해주세요.');
      return;
    }

    setTesting(true);
    try {
      const result = await templatesAPI.test(subject, name, testSampleText);
      setTestResult(result);
      onSpeak?.(`테스트 완료. 신뢰도 ${Math.round(result.confidence * 100)}%`);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '템플릿 테스트 실패';
      onSpeak?.(message);
    } finally {
      setTesting(false);
    }
  };

  const handleDetectPatterns = async () => {
    if (!testSampleText.trim()) {
      onSpeak?.('패턴 감지를 위한 샘플 텍스트를 입력해주세요.');
      return;
    }

    setDetecting(true);
    try {
      const result = await templatesAPI.detectPatterns(testSampleText, subject);
      if (result.detected_patterns.lecture_title_patterns.length > 0) {
        onPatternsDetected?.(result.detected_patterns);
        onSpeak?.('패턴이 감지되어 추가되었습니다.');
      } else {
        onSpeak?.('감지된 패턴이 없습니다.');
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '패턴 감지 실패';
      onSpeak?.(message);
    } finally {
      setDetecting(false);
    }
  };

  return (
    <div className="mb-6">
      <h3 className="text-lg font-semibold mb-3">테스트</h3>
      <div className="space-y-3">
        <div>
          <label className="block text-sm font-medium mb-2">샘플 텍스트</label>
          <textarea
            value={testSampleText}
            onChange={(e) => setTestSampleText(e.target.value)}
            placeholder="테스트할 샘플 텍스트를 입력하세요..."
            className="w-full px-3 py-2 border border-border rounded-lg bg-background font-mono text-sm"
            rows={6}
          />
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleTest}
            disabled={testing || !testSampleText.trim()}
            className="flex-1 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
          >
            <Play className="w-4 h-4" />
            {testing ? '테스트 중...' : '테스트'}
          </button>
          <button
            onClick={handleDetectPatterns}
            disabled={detecting || !testSampleText.trim()}
            className="px-4 py-2 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
            title="AI로 패턴 자동 감지"
          >
            <Sparkles className="w-4 h-4" />
            {detecting ? '감지 중...' : '패턴 감지'}
          </button>
        </div>
        {testResult && (
          <div className="p-3 bg-card border border-border rounded-lg">
            <div className="text-sm font-medium mb-2">
              신뢰도: {Math.round(testResult.confidence * 100)}%
            </div>
            {testResult.matches.lecture_title.length > 0 && (
              <div className="text-xs text-muted-foreground mb-1">
                강의 제목 매칭: {testResult.matches.lecture_title.length}개
              </div>
            )}
            {testResult.matches.problem_number.length > 0 && (
              <div className="text-xs text-muted-foreground mb-1">
                문제 번호 매칭: {testResult.matches.problem_number.length}개
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
