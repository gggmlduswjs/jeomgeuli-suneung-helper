/**
 * Explore 페이지 키워드 관리 훅
 */
import { useState, useCallback } from 'react';
import { learningAPI } from '../../../lib/api/learning';

export interface UseExploreKeywordsReturn {
  isSaving: boolean;
  handleLearn: (keywords: string[]) => Promise<void>;
  handleBrailleOutput: (keywords: string[]) => void;
}

export function useExploreKeywords(
  braille: { enqueueKeywords: (keywords: string[]) => void },
  speak: (text: string) => void,
  showToastMessage: (message: string) => void
): UseExploreKeywordsReturn {
  const [isSaving, setIsSaving] = useState(false);

  // 점자 출력 핸들러 (점자 출력만)
  const handleBrailleOutput = useCallback((keywords: string[]) => {
    braille.enqueueKeywords(keywords);
  }, [braille]);

  // 복습하기 핸들러 (복습 목록에 저장 + 팝업 메시지)
  const handleLearn = useCallback(async (keywords: string[]) => {
    if (!keywords || keywords.length === 0) return;
    
    try {
      setIsSaving(true);
      console.log('[Explore] 복습하기 버튼 클릭, 키워드:', keywords);
      let successCount = 0;
      const savedKeywords: string[] = [];
      
      // 키워드를 복습 목록에 저장
      for (const keyword of keywords) {
        try {
          const payload = {
            type: 'word',
            content: keyword,
            text: keyword,
            word: keyword,
          };

          const result = await learningAPI.saveReview('keyword', payload);
          
          if (result) {
            console.log(`[Explore] 키워드 "${keyword}" 저장 성공:`, result);
            successCount++;
            savedKeywords.push(keyword);
          } else {
            console.error(`[Explore] 키워드 "${keyword}" 저장 실패:`, result);
          }
        } catch (error) {
          console.error(`[Explore] 키워드 "${keyword}" 저장 중 오류:`, error);
        }
      }
      
      if (successCount > 0) {
        // 성공 메시지
        const keywordText = savedKeywords.length <= 3 
          ? savedKeywords.join(', ')
          : `${savedKeywords.slice(0, 3).join(', ')} 외 ${savedKeywords.length - 3}개`;
        const successMessage = `키워드 ${successCount}개가 복습 목록에 추가되었습니다: ${keywordText}`;
        
        // 팝업 메시지 표시
        showToastMessage(successMessage);
        
        // TTS 안내
        await speak(`키워드 ${successCount}개가 복습 목록에 추가되었습니다.`);
      } else {
        // 실패 메시지
        const errorMessage = '키워드 저장에 실패했습니다. 다시 시도해주세요.';
        showToastMessage(errorMessage);
        await speak(errorMessage);
      }
      
    } catch (error) {
      console.error('[Explore] 키워드 복습 저장 실패:', error);
      const errorMessage = '키워드 저장 중 오류가 발생했습니다.';
      showToastMessage(errorMessage);
      await speak(errorMessage);
    } finally {
      setIsSaving(false);
    }
  }, [speak, showToastMessage]);

  return {
    isSaving,
    handleLearn,
    handleBrailleOutput,
  };
}

