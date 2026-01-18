interface BottomBarProps {
  onLeft?: () => void;
  onMid?: () => void;
  onRight?: () => void;
  rightLabel?: string;
}

export default function BottomBar({
  onLeft,
  onMid,
  onRight,
  rightLabel = "다음",
}: BottomBarProps) {
  return (
    <div className="fixed left-0 right-0 bottom-0 bg-white/90 backdrop-blur border-t px-4 py-3 flex gap-3">
      <button
        type="button"
        className="flex-1 rounded-xl border py-3 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary"
        onClick={() => onLeft?.()}
      >
        이전
      </button>
      <button
        type="button"
        className="flex-1 rounded-xl border py-3 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary"
        onClick={() => onMid?.()}
      >
        반복
      </button>
      <button
        type="button"
        className="flex-1 rounded-xl bg-sky-600 text-white py-3 hover:bg-sky-700 focus:outline-none focus:ring-2 focus:ring-sky-400"
        onClick={() => onRight?.()}
      >
        {rightLabel}
      </button>
    </div>
  );
}
