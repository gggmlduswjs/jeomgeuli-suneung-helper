/**
 * 학습 단위 목록 사이드바 컴포넌트
 */
import { useNavigate } from 'react-router-dom';
import type { Unit } from '../../types/unit';

interface UnitListSidebarProps {
  units: Unit[];
  currentUnitId: string | null;
  lessonTitle?: string;
  onClose: () => void;
  getUnitTypeLabel: (unit: Unit) => string;
}

export default function UnitListSidebar({
  units,
  currentUnitId,
  lessonTitle,
  onClose,
  getUnitTypeLabel,
}: UnitListSidebarProps) {
  const navigate = useNavigate();

  return (
    <div className="fixed inset-0 z-50 bg-black/50" onClick={onClose}>
      <div 
        className="absolute right-0 top-0 h-full w-80 bg-background border-l border-border shadow-lg overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-4 border-b border-border">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">학습 단위 목록</h3>
            <button
              onClick={onClose}
              className="text-muted-foreground hover:text-foreground"
              aria-label="닫기"
            >
              ✕
            </button>
          </div>
          {lessonTitle && (
            <p className="text-sm text-muted-foreground mt-1">
              {lessonTitle}
            </p>
          )}
        </div>
        <div className="p-2">
          {units.map((u, index) => {
            const isActive = u.unit_id === currentUnitId;
            const unitTypeLabel = getUnitTypeLabel(u);
            return (
              <button
                key={u.unit_id}
                onClick={() => {
                  navigate(`/unit/${u.unit_id}`);
                  onClose();
                }}
                className={`w-full p-3 text-left rounded-lg mb-2 transition-colors ${
                  isActive
                    ? 'bg-primary/20 border-2 border-primary'
                    : 'bg-card border border-border hover:border-primary/50'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="font-medium text-sm">{u.title}</div>
                    <div className="text-xs text-muted-foreground mt-1">
                      {unitTypeLabel} • {index + 1} / {units.length}
                    </div>
                  </div>
                  {isActive && (
                    <span className="text-primary text-xs">현재</span>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
