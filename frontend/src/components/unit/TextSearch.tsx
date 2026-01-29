/**
 * 텍스트 검색 컴포넌트 (Ctrl+F)
 * 실제 수능 환경: 국어/영어 영역에서 필수
 */
import { useState, useEffect, useRef } from 'react';
import { useTTS } from '../../hooks/useTTS';

interface TextSearchProps {
  content: string;
  onSearchResult?: (index: number, total: number) => void;
  onClose?: () => void;
}

// 특수문자 변형 매핑 (2026학년도 수능 이슈 대응)
const SPECIAL_CHAR_MAP: Record<string, string[]> = {
  '(가)': ['(가)', '㈎', '（가）'],
  '(나)': ['(나)', '㈏', '（나）'],
  '(다)': ['(다)', '㈐', '（다）'],
  '(라)': ['(라)', '㈑', '（라）'],
  '(마)': ['(마)', '㈒', '（마）'],
};

function normalizeSearchQuery(query: string): string {
  // 특수문자 변형 처리
  let normalized = query;
  for (const [key, variants] of Object.entries(SPECIAL_CHAR_MAP)) {
    for (const variant of variants) {
      if (normalized.includes(variant)) {
        normalized = normalized.replace(variant, key);
      }
    }
  }
  return normalized;
}

function createSearchRegex(query: string, caseSensitive: boolean = false): RegExp {
  const normalized = normalizeSearchQuery(query);
  // 특수문자 변형을 모두 포함한 정규식 생성
  let pattern = normalized;
  for (const [key, variants] of Object.entries(SPECIAL_CHAR_MAP)) {
    if (pattern.includes(key)) {
      const variantPattern = variants.map(v => v.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|');
      pattern = pattern.replace(key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), variantPattern);
    }
  }
  return new RegExp(pattern, caseSensitive ? 'g' : 'gi');
}

export default function TextSearch({ content, onSearchResult, onClose }: TextSearchProps) {
  const [query, setQuery] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);
  const [results, setResults] = useState<number[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const { speak } = useTTS();

  // Ctrl+F 단축키
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
        e.preventDefault();
        setIsOpen(true);
        setTimeout(() => inputRef.current?.focus(), 0);
      }
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
        onClose?.();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // 검색 실행
  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      setCurrentIndex(0);
      return;
    }

    try {
      const regex = createSearchRegex(query);
      const matches: number[] = [];
      let match;
      let searchIndex = 0;

      while ((match = regex.exec(content)) !== null) {
        matches.push(match.index);
        if (searchIndex++ > 1000) break; // 무한 루프 방지
      }

      setResults(matches);
      setCurrentIndex(0);
      
      if (matches.length > 0 && onSearchResult) {
        onSearchResult(0, matches.length);
        speak(`${matches.length}개의 결과를 찾았습니다. 1번째 결과입니다.`);
      } else if (matches.length === 0) {
        speak('검색 결과가 없습니다.');
      }
    } catch (error) {
      console.error('Search error:', error);
      speak('검색 중 오류가 발생했습니다.');
    }
  }, [query, content, onSearchResult, speak]);

  // 다음/이전 결과 이동
  const navigateResult = (direction: 'next' | 'prev') => {
    if (results.length === 0) return;

    let newIndex = currentIndex;
    if (direction === 'next') {
      newIndex = (currentIndex + 1) % results.length;
    } else {
      newIndex = (currentIndex - 1 + results.length) % results.length;
    }

    setCurrentIndex(newIndex);
    if (onSearchResult) {
      onSearchResult(newIndex, results.length);
    }
    speak(`${newIndex + 1}번째 결과입니다. 총 ${results.length}개 중`);
    
    // 스크롤 이동
    const position = results[newIndex];
    const element = document.querySelector('[data-search-content]');
    if (element) {
      const textNode = findTextNodeAtPosition(element, position);
      if (textNode) {
        textNode.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  };

  // 키보드 단축키
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        navigateResult('next');
      } else if (e.key === 'Enter' && e.shiftKey) {
        e.preventDefault();
        navigateResult('prev');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, currentIndex, results.length]);

  if (!isOpen) return null;

  return (
    <div className="fixed top-4 left-2 right-2 sm:left-1/2 sm:right-auto sm:transform sm:-translate-x-1/2 z-50 bg-card border border-border rounded-lg shadow-lg p-2 sm:p-4 w-auto sm:min-w-[400px]">
      <div className="flex items-center gap-2">
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="검색어 입력 (Ctrl+F)"
          className="flex-1 px-2 sm:px-3 py-1.5 sm:py-2 border border-border rounded bg-background text-foreground text-sm sm:text-base"
          aria-label="텍스트 검색"
        />
        <button
          onClick={() => {
            setIsOpen(false);
            onClose?.();
          }}
          className="px-2 sm:px-3 py-1.5 sm:py-2 text-muted-foreground hover:text-foreground flex-shrink-0"
          aria-label="검색 닫기"
        >
          ✕
        </button>
      </div>
      
      {results.length > 0 && (
        <div className="mt-2 flex items-center justify-between text-sm text-muted-foreground">
          <span>
            {currentIndex + 1} / {results.length}
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => navigateResult('prev')}
              className="px-2 py-1 hover:bg-muted rounded"
              aria-label="이전 결과"
            >
              ↑ 이전
            </button>
            <button
              onClick={() => navigateResult('next')}
              className="px-2 py-1 hover:bg-muted rounded"
              aria-label="다음 결과"
            >
              다음 ↓
            </button>
          </div>
        </div>
      )}
      
      {query && results.length === 0 && (
        <div className="mt-2 text-sm text-muted-foreground">
          검색 결과가 없습니다.
        </div>
      )}
    </div>
  );
}

// 텍스트 노드에서 특정 위치 찾기 (간단한 버전)
function findTextNodeAtPosition(element: Element, position: number): Node | null {
  const walker = document.createTreeWalker(
    element,
    NodeFilter.SHOW_TEXT,
    null
  );

  let currentPos = 0;
  let node;

  while ((node = walker.nextNode())) {
    const nodeLength = node.textContent?.length || 0;
    if (currentPos + nodeLength >= position) {
      return node;
    }
    currentPos += nodeLength;
  }

  return null;
}
