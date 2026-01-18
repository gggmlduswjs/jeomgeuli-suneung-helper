/**
 * Explore 페이지 채팅 로직 훅
 */
import { useState, useCallback, useRef, useEffect } from 'react';
import { chatAPI, type ChatResponse } from '../../../lib/api/chat';
import type { ChatMessage } from '../../../types';
import { useBraillePlayback } from '../../../hooks/useBraillePlayback';

export interface UseExploreChatReturn {
  messages: ChatMessage[];
  isLoading: boolean;
  handleSubmit: (userText: string) => Promise<void>;
  handleDetail: (topic: string) => Promise<void>;
  handleAiResponse: (res: ChatResponse) => Promise<void>;
}

export function useExploreChat(
  braille: ReturnType<typeof useBraillePlayback>,
  speak: (text: string) => void
): UseExploreChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);

  // 새 메시지 렌더 시 맨 아래로 스크롤
  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight });
  }, [messages, isLoading]);

  // AI 응답 공통 처리
  const handleAiResponse = useCallback(async (res: ChatResponse) => {
    // 키워드 3개까지만 큐 적재
    const ks = (res?.keywords ?? [])
      .filter((s: unknown): s is string => typeof s === 'string' && s.trim().length > 0)
      .slice(0, 3);

    // 점자 큐 적재 (토글 ON일 때 훅이 자동 재생)
    if (ks.length) braille.enqueueKeywords(ks);
  }, [braille]);

  // "자세히" 요청 처리
  const handleDetail = useCallback(async (topic: string) => {
    if (!topic) return;
    
    setIsLoading(true);
    const typingId = `typing_${Date.now()}`;
    
    setMessages(p => [
      ...p,
      {
        id: typingId,
        role: 'assistant',
        type: 'text',
        text: '__typing__',
        createdAt: Date.now(),
      },
    ]);

    try {
      // 기존 답변을 확장하는 프롬프트로 변경
      const expandPrompt = `위에서 "${topic}"에 대해 간단히 설명했는데, 이제 더 자세하고 구체적으로 설명해주세요. 

다음 내용을 포함해주세요:
- 기본 개념과 정의
- 주요 특징과 원리  
- 실제 활용 사례나 예시
- 관련된 중요 정보

답변 후에 핵심 키워드 3개를 추출해서 "키워드: 키워드1, 키워드2, 키워드3" 형태로 끝에 추가해주세요.`;

      const result = await chatAPI.askChatWithKeywords(expandPrompt);
      
      // typing indicator 제거
      setMessages(p => p.filter(m => m.id !== typingId));

      // Create response object for compatibility
      const response = { answer: result.answer, keywords: result.keywords, ok: true };

      // 공통 처리(키워드 큐, 불릿 추출)
      await handleAiResponse(response);

      // AI 응답을 메시지로 추가
      const cardMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        type: 'text',
        text: result.answer,
        keywords: result.keywords,
        createdAt: Date.now(),
      };
      setMessages(p => [...p, cardMsg]);

      // TTS로 자동 낭독
      await speak(result.answer);
    } catch (error) {
      console.error('자세히 요청 오류:', error);
      setMessages(p => [
        ...p.filter(m => m.id !== typingId),
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          type: 'text',
          text: '죄송합니다. 자세한 정보를 가져오는 중 오류가 발생했습니다.',
          createdAt: Date.now(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }, [handleAiResponse, speak]);

  // 메시지 전송 처리
  const handleSubmit = useCallback(async (userText: string) => {
    const trimmedText = userText?.trim();
    if (!trimmedText) {
      console.log('[Explore] handleSubmit: 빈 텍스트 - 건너뜀');
      return;
    }
    
    if (isLoading) {
      console.log('[Explore] handleSubmit: 이미 로딩 중 - 건너뜀');
      return;
    }

    console.log('[Explore] handleSubmit 실행:', trimmedText);

    // 사용자 메시지 추가
    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      type: 'text',
      text: userText,
      createdAt: Date.now(),
    };
    setMessages(p => [...p, userMsg]);

    setIsLoading(true);
    const typingId = `typing_${Date.now()}`;
    
    setMessages(p => [
      ...p,
      {
        id: typingId,
        role: 'assistant',
        type: 'text',
        text: '__typing__',
        createdAt: Date.now(),
      },
    ]);

    try {
      // AI API 호출 - 키워드와 함께
      const result = await chatAPI.askChatWithKeywords(userText);
      if (import.meta?.env?.DEV) {
        console.debug("[Explore] result=", result);
      }

      // typing indicator 제거
      setMessages(p => p.filter(m => m.id !== typingId));

      // Create response object for compatibility
      const response = { answer: result.answer, keywords: result.keywords, ok: true };

      // 공통 처리(키워드 큐, 불릿 추출)
      await handleAiResponse(response);

      // AI 응답을 메시지로 추가
      const cardMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        type: 'text',
        text: result.answer,
        keywords: result.keywords,
        createdAt: Date.now(),
      };
      setMessages(p => [...p, cardMsg]);

      // TTS로 자동 낭독
      await speak(result.answer);
    } catch (error) {
      console.error('AI 응답 오류:', error);
      setMessages(p => [
        ...p.filter(m => m.id !== typingId),
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          type: 'text',
          text: '죄송합니다. 응답을 생성하는 중 오류가 발생했습니다.',
          createdAt: Date.now(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, handleAiResponse, speak]);

  return {
    messages,
    isLoading,
    handleSubmit,
    handleDetail,
    handleAiResponse,
  };
}

