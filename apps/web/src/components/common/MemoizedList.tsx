/**
 * Performance Optimization - Memoized List Component
 * 긴 리스트를 위한 메모이제이션 컴포넌트
 */
import { memo, useMemo } from 'react';

interface MemoizedListProps<T> {
  items: T[];
  renderItem: (item: T, index: number) => React.ReactNode;
  keyExtractor: (item: T, index: number) => string | number;
  className?: string;
}

function MemoizedList<T>({ items, renderItem, keyExtractor, className }: MemoizedListProps<T>) {
  const memoizedItems = useMemo(
    () => items.map((item, index) => ({
      item,
      index,
      key: keyExtractor(item, index),
      element: renderItem(item, index),
    })),
    [items, renderItem, keyExtractor]
  );

  return (
    <div className={className} role="list">
      {memoizedItems.map(({ key, element }) => (
        <div key={key} role="listitem">
          {element}
        </div>
      ))}
    </div>
  );
}

export default memo(MemoizedList) as typeof MemoizedList;


