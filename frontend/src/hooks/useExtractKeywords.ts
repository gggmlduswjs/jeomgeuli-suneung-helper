/**
 * 핵심 키워드 추출 훅
 */
import { useState, useCallback } from 'react';
import { literatureAPI } from '../services/literature';
import { createModuleLogger } from '../utils/logger';

const logger = createModuleLogger('ExtractKeywords');

export function useExtractKeywords() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const extractKeywords = useCallback(async (
    unit: { type: string; title: string; content_text?: string; question?: { stem?: string } } | null
  ): Promise<string[]> => {
    if (!unit) {
      return [];
    }

    setIsLoading(true);
    setError(null);

    try {
      // Unit의 텍스트 내용 추출
      let text = '';
      
      if (unit.type === 'QUESTION' && unit.question?.stem) {
        text = unit.question.stem;
      } else if (unit.content_text) {
        text = unit.content_text;
      } else {
        text = unit.title;
      }

      // 간단한 키워드 추출 (AI API 사용 또는 로컬 분석)
      // 우선 간단한 로직으로 구현
      const keywords = extractKeywordsFromText(text, unit.title);
      
      logger.log(`키워드 추출 완료: ${keywords.join(', ')}`);
      return keywords;
    } catch (err) {
      logger.error('키워드 추출 실패:', err);
      setError(err instanceof Error ? err.message : '키워드 추출 실패');
      // 실패 시 기본 키워드 반환
      return [unit.title];
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { extractKeywords, isLoading, error };
}

/**
 * 텍스트에서 핵심 키워드 추출 (간단한 버전)
 */
function extractKeywordsFromText(text: string, title: string): string[] {
  // 제목에서 키워드 추출 (숫자/특수문자 제거)
  const titleKeywords = title
    .replace(/^\d+\.\s*/, '') // 앞의 "1. " 같은 패턴 제거
    .split(/[·\s,，]/)
    .filter(w => {
      // 한글 또는 영문이 포함된 단어만
      const hasKorean = /[가-힣]/.test(w);
      const hasEnglish = /[a-zA-Z]/.test(w);
      return w.length > 1 && (hasKorean || hasEnglish) && !/^\d+$/.test(w);
    });
  
  // 텍스트에서 중요한 단어 추출
  const words = text
    .replace(/[^\w\s가-힣]/g, ' ')
    .split(/\s+/)
    .filter(w => {
      // 길이 체크
      if (w.length < 2 || w.length > 10) return false;
      // 숫자만 있는 단어 제외
      if (/^\d+$/.test(w)) return false;
      // 한글 또는 영문이 포함되어야 함
      const hasKorean = /[가-힣]/.test(w);
      const hasEnglish = /[a-zA-Z]/.test(w);
      if (!hasKorean && !hasEnglish) return false;
      // 불용어 제외
      return !isStopWord(w);
    });

  // 빈도수 계산
  const wordCount: Record<string, number> = {};
  words.forEach(word => {
    wordCount[word] = (wordCount[word] || 0) + 1;
  });

  // 빈도수 높은 순으로 정렬
  const sortedWords = Object.entries(wordCount)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([word]) => word);

  // 제목 키워드와 텍스트 키워드 결합 (중복 제거)
  const allKeywords = [...new Set([...titleKeywords, ...sortedWords])];
  
  // 최대 3개 반환
  return allKeywords.slice(0, 3);
}

/**
 * 불용어 필터링
 */
function isStopWord(word: string): boolean {
  const stopWords = [
    '그리고', '그러나', '또한', '또는', '그래서', '따라서',
    '이것', '그것', '저것', '이런', '그런', '저런',
    '있다', '없다', '되다', '하다', '이다', '아니다',
    '의', '을', '를', '이', '가', '에', '에서', '로', '으로',
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
  ];
  return stopWords.includes(word.toLowerCase());
}
