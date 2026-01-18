/**
 * Explore 페이지 뉴스 탐색 로직 훅
 */
import { useState, useCallback } from 'react';
import { chatAPI } from '../../../lib/api/chat';

export interface ExploreData {
  answer: string;
  news: any[];
  query: string;
}

export interface UseExploreNewsReturn {
  exploreData: ExploreData | null;
  isExploreLoading: boolean;
  handleExplore: (query: string) => Promise<void>;
}

export function useExploreNews(speak: (text: string) => void): UseExploreNewsReturn {
  const [exploreData, setExploreData] = useState<ExploreData | null>(null);
  const [isExploreLoading, setIsExploreLoading] = useState(false);

  // 정보탐색 처리
  const handleExplore = useCallback(async (query: string) => {
    if (!query.trim()) return;
    
    setIsExploreLoading(true);
    try {
      // fetchExplore 대신 askChat 사용 (뉴스 정보 포함)
      const result = await chatAPI.fetchExplore(query);
      
      setExploreData({
        answer: result.answer || '',
        news: result.news || [],
        query: result.query || query,
      });
      
      // TTS로 답변 읽기
      if (result.answer) {
        await speak(result.answer);
      }
    } catch (error) {
      console.error('정보탐색 오류:', error);
      const errorMessage = `정보탐색 중 오류가 발생했습니다: ${error}`;
      setExploreData({
        answer: errorMessage,
        news: [],
        query: query
      });
      
      // 오류 메시지도 TTS로 읽기
      await speak(errorMessage);
    } finally {
      setIsExploreLoading(false);
    }
  }, [speak]);

  return {
    exploreData,
    isExploreLoading,
    handleExplore,
  };
}

