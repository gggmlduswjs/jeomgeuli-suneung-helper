import BrailleCell from './BrailleCell';
import type { DotArray } from '@/types';

interface BraillePanelProps {
  braille: {
    status: string;
    currentWord: string;
    currentCells: DotArray[];
    demoMode: boolean;
    queue: string[];
    next: () => void;
    repeat: () => void;
    pause: () => void;
    enqueueKeywords: (keywords: string[]) => void;
  };
}

export function BraillePanel({ braille }: BraillePanelProps) {
  const {
    status,
    currentWord,
    currentCells,
    demoMode,
    queue,
    next,
    repeat,
    pause,
  } = braille;

  const isActive = status.includes('출력 중');

  return (
    <section
      className="braille-panel bg-white border border-slate-200 rounded-lg p-4 mb-4"
      role="region"
      aria-label="점자 출력 패널"
    >
      {/* 패널 헤더 */}
      <div className="panel-header flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span
            className={`px-2 py-1 rounded-full text-xs font-medium ${
              status.includes('출력 중')
                ? 'bg-green-100 text-green-700'
                : status.includes('일시 정지')
                ? 'bg-yellow-100 text-yellow-700'
                : 'bg-slate-100 text-slate-700'
            }`}
            aria-live="polite"
          >
            {status}
          </span>
          {demoMode && (
            <span className="text-xs text-slate-500 bg-slate-50 px-2 py-1 rounded">
              데모 모드
            </span>
          )}
        </div>

        <div className="controls flex gap-2">
          <button
            type="button"
            onClick={repeat}
            disabled={!queue.length}
            className="px-2 py-1 rounded bg-slate-100 text-sm hover:bg-slate-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="현재 키워드 반복"
          >
            ⟳ 반복
          </button>
          <button
            type="button"
            onClick={next}
            disabled={!queue.length}
            className="px-2 py-1 rounded bg-slate-100 text-sm hover:bg-slate-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="다음 키워드"
          >
            ▶ 다음
          </button>
          <button
            type="button"
            onClick={pause}
            disabled={!queue.length}
            className="px-2 py-1 rounded bg-slate-100 text-sm hover:bg-slate-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="점자 출력 정지"
          >
            ■ 정지
          </button>
        </div>
      </div>

      {/* 미리보기 영역 */}
      <div className="preview text-center">
        <div className="word mb-3" aria-live="polite">
          <span className="text-lg font-medium text-slate-800">
            {currentWord || '현재 출력 중인 점자'}
          </span>
        </div>

        <div
          className="cells flex justify-center gap-2 mb-3"
          role="group"
          aria-label="점자 셀 미리보기"
        >
          {currentCells?.length ? (
            currentCells.map((pattern: DotArray, i: number) => (
              <BrailleCell
                key={i}
                pattern={pattern}
                active={isActive}
                className="scale-110"
              />
            ))
          ) : (
            <BrailleCell
              pattern={[false, false, false, false, false, false] as DotArray}
              active={false}
              className="scale-110"
            />
          )}
        </div>

        {!currentCells?.length && (
          <small className="text-slate-500">대기 중</small>
        )}
      </div>

      {/* 힌트 */}
      <div className="hint text-center text-sm text-slate-600 mb-3">
        음성 명령: ‘자세히’, ‘다음’, ‘점자 출력’ — 이 키워드로 학습을 이어가 보세요.
      </div>

      {/* 개발자 테스트 버튼 - 실제 키워드가 있을 때만 표시 */}
      {/* <div className="dev text-center">
        <button
          type="button"
          onClick={() => enqueueKeywords(['경제', '기술', '스포츠'])}
          className="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg text-sm font-medium hover:bg-blue-200 transition-colors"
          title="BLE 없이도 상단 미리보기로 순환 표시"
        >
          임시 출력(경제·기술·스포츠)
        </button>
      </div> */}
    </section>
  );
}

export default BraillePanel;
