/**
 * 수식 계산 도구 (한소네 대체)
 * 실제 수능 환경: 수학 영역 필수
 */
import { useState, useEffect } from 'react';
import { useTTS } from '../../hooks/useTTS';
import { useBrailleBLE } from '../../hooks/useBrailleBLE';

// 간단한 수식 계산 함수 (mathjs 대체)
function evaluateExpression(expr: string): number {
  try {
    // 안전한 계산을 위해 Function 생성자 사용 (제한적)
    // 실제 프로덕션에서는 mathjs 사용 권장
    const sanitized = expr.replace(/[^0-9+\-*/().\s]/g, '');
    // eslint-disable-next-line no-eval
    return eval(sanitized) as number;
  } catch {
    throw new Error('계산 오류');
  }
}

interface MathCalculatorProps {
  onClose?: () => void;
}

export default function MathCalculator({ onClose }: MathCalculatorProps) {
  const [expression, setExpression] = useState('');
  const [result, setResult] = useState<string | null>(null);
  const [history, setHistory] = useState<Array<{ expr: string; result: string }>>([]);
  const [error, setError] = useState<string | null>(null);
  const { speak } = useTTS();
  const { sendText } = useBrailleBLE();

  // 계산 실행
  const calculate = () => {
    if (!expression.trim()) return;

    try {
      const calculated = evaluateExpression(expression);
      const resultStr = String(calculated);
      setResult(resultStr);
      setError(null);
      setHistory(prev => [...prev, { expr: expression, result: resultStr }].slice(-10));

      // 음성으로 결과 읽기
      speak(`계산 결과는 ${resultStr}입니다.`);

      // 점자 디스플레이에 표시
      if (sendText) {
        sendText(`${expression} = ${resultStr}`);
      }
    } catch (err) {
      const errorMsg = '계산 오류가 발생했습니다.';
      setError(errorMsg);
      setResult(null);
      speak(errorMsg);
    }
  };

  // 키보드 단축키
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        calculate();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [expression]);

  // 수식 음성 설명
  const speakExpression = (expr: string) => {
    // 간단한 수식 음성 변환
    let spoken = expr
      .replace(/\^/g, '제곱')
      .replace(/\*/g, '곱하기')
      .replace(/\//g, '나누기')
      .replace(/\+/g, '더하기')
      .replace(/-/g, '빼기')
      .replace(/=/g, '는')
      .replace(/\(/g, '괄호 열기')
      .replace(/\)/g, '괄호 닫기');
    
    speak(spoken);
  };

  return (
    <div className="fixed bottom-4 right-4 z-50 bg-card border border-border rounded-lg shadow-lg p-4 min-w-[320px] max-w-[400px]">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold">수식 계산기</h3>
        {onClose && (
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground"
            aria-label="계산기 닫기"
          >
            ✕
          </button>
        )}
      </div>

      <div className="space-y-3">
        {/* 입력 */}
        <div>
          <label className="block text-sm font-medium mb-1">수식 입력</label>
          <input
            type="text"
            value={expression}
            onChange={(e) => setExpression(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                calculate();
              }
            }}
            placeholder="예: 2 + 3 * 4"
            className="w-full px-3 py-2 border border-border rounded bg-background text-foreground"
            aria-label="수식 입력"
          />
          <button
            onClick={() => speakExpression(expression)}
            className="mt-1 text-xs text-muted-foreground hover:text-foreground"
            aria-label="수식 음성 설명"
          >
            🔊 수식 읽기
          </button>
        </div>

        {/* 결과 */}
        {result !== null && (
          <div className="bg-success/10 border border-success rounded p-3">
            <div className="text-sm text-muted-foreground mb-1">결과</div>
            <div className="text-2xl font-bold">{result}</div>
          </div>
        )}

        {error && (
          <div className="bg-destructive/10 border border-destructive rounded p-3 text-destructive text-sm">
            {error}
          </div>
        )}

        {/* 계산 버튼 */}
        <button
          onClick={calculate}
          className="w-full px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90"
        >
          계산 (Ctrl+Enter)
        </button>

        {/* 히스토리 */}
        {history.length > 0 && (
          <div className="mt-4 border-t border-border pt-3">
            <div className="text-sm font-medium mb-2">계산 히스토리</div>
            <div className="space-y-1 max-h-32 overflow-y-auto">
              {history.slice().reverse().map((item, index) => (
                <div
                  key={index}
                  className="text-xs bg-muted rounded p-2 cursor-pointer hover:bg-muted/80"
                  onClick={() => {
                    setExpression(item.expr);
                    setResult(item.result);
                  }}
                >
                  <div className="font-mono">{item.expr}</div>
                  <div className="text-muted-foreground">= {item.result}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 도움말 */}
        <div className="text-xs text-muted-foreground mt-3 pt-3 border-t border-border">
          <div>• Enter: 계산 실행</div>
          <div>• Ctrl+Enter: 계산 실행</div>
          <div>• 지원 연산: +, -, *, /, ^, (), 함수</div>
        </div>
      </div>
    </div>
  );
}
