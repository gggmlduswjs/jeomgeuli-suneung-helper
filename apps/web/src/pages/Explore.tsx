import { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Home, BookOpen, Search, RefreshCw, Type, ArrowLeft, Volume2, VolumeX } from 'lucide-react';
import { ChatLikeInput } from '../components/input/ChatLikeInput';
import { AnswerCard } from '../components/ui/AnswerCard';
import { BrailleOutputPanel } from '../components/braille/BrailleOutputPanel';
import ToastA11y from '../components/system/ToastA11y';
import { useTTS } from '../hooks/useTTS';
import useSTT from '../hooks/useSTT';
import useBrailleBLE from '../hooks/useBrailleBLE';
import { useBraillePlayback } from '../hooks/useBraillePlayback';
import useVoiceCommands from '../hooks/useVoiceCommands';
import { chatAPI, type ChatResponse } from '../lib/api/ChatAPI';
import { learningAPI } from '../lib/api/LearningAPI';
import type { ChatMessage } from '../types';
import { useVoiceStore } from '../store/voice';
import VoiceEventBus, { VoiceEventType } from '../lib/voice/VoiceEventBus';

// function extractBulletsFromMarkdown(md?: string): string[] {
//   if (!md) return [];
//   const lines = md.split(/\r?\n/).map((l: string) => l.trim());
//   const bulletRegex = /^(?:•|-|\*|\d+[.)])\s+(.*)$/;
//   return lines.filter((line) => bulletRegex.test(line)).map((line) => {
//     const match = line.match(bulletRegex);
//     return match ? match[1] : line;
//   });
// }

// function getSimpleTTS(res?: ChatResponse | null): string | undefined {
//   if (!res) return;
//   return (res.actions as any)?.simple_tts || (res as any).simple_tts;
// }

export default function Explore() {
  const navigate = useNavigate();
  const location = useLocation();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentBraille, setCurrentBraille] = useState<string[]>([]); // 현재 출력 중인 점자
  const listRef = useRef<HTMLDivElement>(null);
  
  // 정보탐색 모드 상태
  const [exploreData, setExploreData] = useState<{
    answer: string;
    news: any[];
    query: string;
  } | null>(null);
  const [isExploreLoading, setIsExploreLoading] = useState(false);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  const { speak } = useTTS();
  const { stop: stopSTT } = useSTT();
  const { isConnected, connect, disconnect } = useBrailleBLE();
  const [isTTSEnabled, setIsTTSEnabled] = useState(true);
  const braille = useBraillePlayback({
    ble: {
      serviceUUID: "0000180a-0000-1000-8000-00805f9b34fb",
      characteristicUUID: "00002a00-0000-1000-8000-00805f9b34fb",
    },
  });

  // 페이지 진입 시 이전 데이터 초기화
  useEffect(() => {
    console.log('[Explore] 페이지 진입 - 이전 데이터 초기화');
    setMessages([]);
    setExploreData(null);
    setCurrentBraille([]);
    useVoiceStore.getState().resetTranscript();
  }, [location.pathname]); // 경로가 변경될 때마다 초기화

  // 페이지 진입 시 자동 음성 안내
  useEffect(() => {
    const welcomeMessage = '정보 탐색 모드입니다. 궁금한 것을 물어보세요. 뉴스나 날씨 정보도 확인할 수 있습니다.';
    
    const timer = setTimeout(() => {
      if (isTTSEnabled) {
        speak(welcomeMessage);
      }
    }, 500);

    return () => {
      clearTimeout(timer);
    };
  }, [speak, isTTSEnabled]);

  // 뒤로가기 버튼 클릭 시 홈으로 이동
  const handleBack = () => {
    navigate('/');
  };

  // TTS 토글
  const toggleTTS = () => {
    setIsTTSEnabled((prev) => {
      const next = !prev;
      if (!next && typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
      return next;
    });
  };

  // 네비게이션 활성 상태 확인
  const isActive = (path: string) => location.pathname === path;

  // 네비게이션 버튼 컴포넌트
  const NavButton = ({
    icon: Icon,
    label,
    onClick,
    isActive,
    ariaLabel,
    ariaCurrent
  }: {
    icon: React.ComponentType<{ className?: string }>;
    label: string;
    onClick: () => void;
    isActive: boolean;
    ariaLabel: string;
    ariaCurrent?: 'page' | undefined;
  }) => (
    <button
      type="button"
      onClick={onClick}
      className="relative flex flex-col items-center justify-center px-2.5 py-2.5 min-w-[52px] rounded-xl transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary/50 active:scale-95 group touch-manipulation"
      aria-label={ariaLabel}
      aria-current={ariaCurrent}
    >
      {/* 활성 상태 배경 */}
      {isActive && (
        <div className="absolute inset-0 rounded-xl bg-gradient-to-b from-primary/8 via-primary/5 to-transparent" />
      )}
      
      {/* 호버 배경 */}
      {!isActive && (
        <div className="absolute inset-0 rounded-xl bg-card/80 opacity-0 group-hover:opacity-100 transition-opacity duration-200" />
      )}
      
      {/* 활성 상태 상단 인디케이터 바 */}
      {isActive && (
        <div className="absolute top-0 left-1/2 transform -translate-x-1/2 w-7 h-0.5 bg-primary rounded-full" />
      )}
      
      {/* 아이콘 */}
      <div className={`relative z-10 mb-1 transition-all duration-200 ${
        isActive ? 'scale-110' : 'scale-100 group-hover:scale-105'
      }`}>
        <Icon 
          className={`w-5 h-5 transition-colors duration-200 ${
            isActive 
              ? 'text-primary drop-shadow-sm' 
              : 'text-muted/60 group-hover:text-fg/80'
          }`} 
          aria-hidden="true" 
        />
      </div>
      
      {/* 라벨 */}
      <span 
        className={`text-[10px] font-medium transition-all duration-200 relative z-10 leading-tight ${
          isActive 
            ? 'text-primary font-semibold' 
            : 'text-muted/60 group-hover:text-fg/70'
        }`}
      >
        {label}
      </span>
    </button>
  );

  // 새 메시지 렌더 시 맨 아래로 스크롤
  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight });
  }, [messages, isLoading]);

  // 점자 출력 핸들러 (점자 출력만)
  const handleBrailleOutput = useCallback((keywords: string[]) => {
    setCurrentBraille(keywords);
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
        setToastMessage(successMessage);
        setShowToast(true);
        
        // TTS 안내
        await speak(`키워드 ${successCount}개가 복습 목록에 추가되었습니다.`);
      } else {
        // 실패 메시지
        const errorMessage = '키워드 저장에 실패했습니다. 다시 시도해주세요.';
        setToastMessage(errorMessage);
        setShowToast(true);
        await speak(errorMessage);
      }
      
    } catch (error) {
      console.error('[Explore] 키워드 복습 저장 실패:', error);
      const errorMessage = '키워드 저장 중 오류가 발생했습니다.';
      setToastMessage(errorMessage);
      setShowToast(true);
      await speak(errorMessage);
    } finally {
      setIsSaving(false);
    }
  }, [speak]);

  // AI 응답 공통 처리
  const handleAiResponse = useCallback(async (res: ChatResponse) => {
    // 키워드 3개까지만 큐 적재
    const ks = (res?.keywords ?? [])
      .filter((s: unknown): s is string => typeof s === 'string' && s.trim().length > 0)
      .slice(0, 3);

    // 응답에서 불릿 추출
    // const answerText = normalizeAnswer(res);
    // const bullets = extractBulletsFromMarkdown(answerText);

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
          text: `죄송합니다. "${topic}"에 대한 자세한 설명을 가져오는 중 오류가 발생했습니다.`,
          createdAt: Date.now(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }, [handleAiResponse, speak]);

  // 정보탐색 모드 처리
  const handleExplore = useCallback(async (query: string) => {
    setIsExploreLoading(true);
    try {
      const data = await chatAPI.fetchExplore(query);
      setExploreData({
        answer: data.answer ?? "",
        news: data.news ?? [],
        query: data.query ?? ""
      });
      
      // TTS로 자동 낭독
      if (data.answer) {
        await speak(data.answer);
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

  // 음성 명령 처리
  const { onSpeech } = useVoiceCommands({
    // 네비게이션
    home: () => {
      stopSTT();
      window.location.href = '/';
    },
    back: () => {
      stopSTT();
      window.history.back();
    },
    
    // 복습하기
    review: () => {
      stopSTT();
      navigate('/review');
    },
    
    // 점자 제어
    brailleOn: () => braille.setEnabled(true),
    brailleOff: () => braille.setEnabled(false),
    brailleConnect: () => connect(),
    brailleDisconnect: () => disconnect(),
    
    // 재생 제어
    next: () => braille.next(),
    repeat: () => braille.repeat(),
    start: () => braille.start(),
    stop: () => braille.pause(),
    
    // 상세 정보
    detail: () => {
      // 마지막 assistant 메시지의 첫 번째 키워드로 자세히 요청
      const lastAssistantMsg = messages
        .filter(m => m.role === 'assistant' && m.keywords && m.keywords.length > 0)
        .pop();
      if (lastAssistantMsg?.keywords?.[0]) {
        handleDetail(lastAssistantMsg.keywords[0]);
      }
    },
    
    // 정보탐색
    news: () => handleExplore("오늘 뉴스"),
    weather: () => handleExplore("오늘 날씨"),
    
    // 도움말
    help: () => {
      const helpText = '사용 가능한 음성 명령어: 홈, 뒤로, 점자켜, 점자꺼, 점자연결, 점자해제, 다음, 반복, 시작, 정지, 자세히, 뉴스, 날씨, 도움말, 점자출력, 복습하기';
      speak(helpText);
    },
    
    // TTS 제어
    speak: (text: string) => speak(text),
    mute: () => {
      // TTS 중지 로직 추가 가능
    },
    unmute: () => {
      speak('음성이 활성화되었습니다.');
    },
    
    // 입력 제어
    submit: () => {
      // ChatLikeInput에서 처리되므로 여기서는 빈 핸들러
      // 필요시 추가 로직 구현 가능
    },
    clear: () => {
      // ChatLikeInput에서 처리
    },
  });

  // 마이크 시작 시 transcript 초기화
  useEffect(() => {
    const unsubscribe = VoiceEventBus.onMicIntent((event) => {
      if (event.action === 'start') {
        console.log('[Explore] 마이크 시작 - transcript 초기화');
        useVoiceStore.getState().resetTranscript();
        // ChatLikeInput의 입력란도 초기화하려면 필요시 추가
      }
    });
    return unsubscribe;
  }, []);

  // 음성 인식 결과를 자동으로 검색 처리
  const lastProcessedTextRef = useRef<string>('');
  const lastProcessedTimeRef = useRef<number>(0);
  const autoSearchTimerRef = useRef<number | undefined>(undefined);
  const pendingSearchTextRef = useRef<string | null>(null); // 타이머에서 사용할 텍스트 저장

  useEffect(() => {
    const onVoiceTranscript = (e: Event) => {
      const detail = (e as CustomEvent)?.detail as { text?: string } | undefined;
      const text = detail?.text?.trim();
      if (!text) return;

      const now = Date.now();
      // 중복 처리 방지: 1.5초 내 동일 텍스트 무시
      if (text === lastProcessedTextRef.current && now - lastProcessedTimeRef.current < 1500) {
        return;
      }

      // 짧은 텍스트(1-2글자)는 검색하지 않음 (중간 결과로 인한 오검색 방지)
      // 단, 명령어 패턴이 포함된 경우는 예외
      const trimmedText = text.trim();
      const normalizedForCheck = trimmedText.toLowerCase().replace(/[.,!?]/g, '');
      const isCommandPattern = normalizedForCheck.includes('점자') || 
                                normalizedForCheck.includes('복습') ||
                                normalizedForCheck.includes('탐색');
      
      if (trimmedText.length <= 2 && !isCommandPattern) {
        console.log('[Explore] 짧은 텍스트 무시 (중간 결과 가능성):', trimmedText);
        return;
      }

      // "점자 출력" 명령어 처리 (명령어 라우터보다 먼저 체크)
      // 부분 일치도 허용하여 "점자", "점자출력", "점자 출력" 모두 인식
      const normalizedText = text.toLowerCase().replace(/\s+/g, '');
      if (normalizedText.includes('점자출력') || 
          (normalizedText.includes('점자') && normalizedText.length >= 2)) {
        const lastAssistantMsg = messages
          .filter(m => m.role === 'assistant' && m.keywords && m.keywords.length > 0)
          .pop();
        if (lastAssistantMsg?.keywords && lastAssistantMsg.keywords.length > 0) {
          console.log('[Explore] 점자 출력 명령어 처리:', lastAssistantMsg.keywords);
          handleBrailleOutput(lastAssistantMsg.keywords);
          lastProcessedTextRef.current = text;
          lastProcessedTimeRef.current = now;
          return;
        } else {
          console.warn('[Explore] 점자 출력: 출력할 키워드가 없습니다.');
          speak('출력할 키워드가 없습니다. 먼저 검색을 해주세요.');
          return;
        }
      }

      // "복습하기" 명령어 처리 (명령어 라우터보다 먼저 체크)
      const normalizedForReview = text.toLowerCase().replace(/[.,!?]/g, '').trim();
      if (normalizedForReview === '복습하기' || normalizedForReview === '복습' || 
          normalizedForReview === '복습하기로' || normalizedForReview === '복습으로' ||
          (normalizedForReview.includes('복습') && normalizedForReview.length >= 2)) {
        const lastAssistantMsg = messages
          .filter(m => m.role === 'assistant' && m.keywords && m.keywords.length > 0)
          .pop();
        if (lastAssistantMsg?.keywords && lastAssistantMsg.keywords.length > 0) {
          console.log('[Explore] 복습하기 명령어 처리:', lastAssistantMsg.keywords);
          // 키워드를 복습 목록에 저장한 후 페이지 이동
          handleLearn(lastAssistantMsg.keywords).then(() => {
            // 저장 완료 후 복습 페이지로 이동
            stopSTT();
            navigate('/review');
          }).catch((error) => {
            console.error('[Explore] 복습하기 처리 중 오류:', error);
            speak('복습 목록 저장 중 오류가 발생했습니다.');
          });
          lastProcessedTextRef.current = text;
          lastProcessedTimeRef.current = now;
          return;
        } else {
          console.warn('[Explore] 복습하기: 저장할 키워드가 없습니다.');
          speak('저장할 키워드가 없습니다. 먼저 검색을 해주세요.');
          return;
        }
      }

      // 명령어 체크 (Explore 페이지에서는 "탐색" 명령어를 검색으로 처리)
      const handled = onSpeech(text);
      if (handled) {
        // "탐색" 관련 명령어는 Explore 페이지에서 검색으로 처리
        const normalized = text.toLowerCase().replace(/[.,!?]/g, '').trim();
        if (normalized === '탐색' || normalized === '정보탐색' || normalized === '정보 탐색' || normalized === '검색') {
          console.log('[Explore] "탐색" 명령어를 검색으로 처리:', text);
          // 검색으로 처리하도록 계속 진행 (return하지 않음)
        } else {
          console.log('[Explore] 명령어 처리됨 - 검색 건너뜀:', text);
          lastProcessedTextRef.current = text;
          lastProcessedTimeRef.current = now;
          return;
        }
      }

      // 명령어가 아닌 경우 또는 "탐색" 명령어인 경우 즉시 자동 검색
      console.log('[Explore] 음성 인식 자동 검색 예약:', text);
      lastProcessedTextRef.current = text;
      lastProcessedTimeRef.current = now;
      pendingSearchTextRef.current = text; // ref에 저장하여 타이머에서 사용

      // 기존 타이머 취소하고 즉시 실행 (각 transcript마다 개별 검색)
      if (autoSearchTimerRef.current) {
        clearTimeout(autoSearchTimerRef.current);
        autoSearchTimerRef.current = undefined;
      }

      // 즉시 검색 실행 (각 음성 인식 결과마다 개별 검색)
      // trimmedText는 이미 위에서 선언되었으므로 재사용
      const currentIsLoading = isLoading;
      const currentIsExploreLoading = isExploreLoading;
      
      if (!currentIsLoading && !currentIsExploreLoading && trimmedText) {
        console.log('[Explore] 음성 인식 자동 검색 즉시 실행:', trimmedText);
        handleSubmit(trimmedText);
        pendingSearchTextRef.current = null;
      } else {
        // 조건이 맞지 않으면 짧은 지연 후 재시도
        autoSearchTimerRef.current = window.setTimeout(() => {
          const retryText = pendingSearchTextRef.current || trimmedText;
          const retryIsLoading = isLoading;
          const retryIsExploreLoading = isExploreLoading;
          
          console.log('[Explore] 자동 검색 재시도 체크:', {
            text: retryText.trim(),
            isLoading: retryIsLoading,
            isExploreLoading: retryIsExploreLoading,
            canExecute: !retryIsLoading && !retryIsExploreLoading && retryText.trim()
          });
          
          if (!retryIsLoading && !retryIsExploreLoading && retryText.trim()) {
            console.log('[Explore] 음성 인식 자동 검색 재시도 실행:', retryText.trim());
            handleSubmit(retryText.trim());
          } else {
            console.warn('[Explore] 자동 검색 재시도 건너뜀 - 조건 불만족:', {
              isLoading: retryIsLoading,
              isExploreLoading: retryIsExploreLoading,
              hasText: !!retryText.trim()
            });
          }
          pendingSearchTextRef.current = null;
          autoSearchTimerRef.current = undefined;
        }, 100);
      }
    };

    window.addEventListener('voice:transcript', onVoiceTranscript as EventListener);
    return () => {
      window.removeEventListener('voice:transcript', onVoiceTranscript as EventListener);
      if (autoSearchTimerRef.current) {
        clearTimeout(autoSearchTimerRef.current);
        autoSearchTimerRef.current = undefined;
      }
      pendingSearchTextRef.current = null;
    };
  }, [onSpeech, handleSubmit, isLoading, isExploreLoading, messages, handleBrailleOutput, handleLearn, navigate, stopSTT, speak]);

  return (
    <div className="flex flex-col min-h-screen bg-bg text-fg">
      {/* 헤더는 AppShellMobile 없이 직접 구현 */}
      <div className="sticky top-0 z-50 bg-white/98 backdrop-blur-xl border-b border-border/50 shadow-[0_2px_8px_rgba(0,0,0,0.04)]">
        <div className="w-full md:max-w-md md:mx-auto">
          <div className="flex items-center justify-between px-4 py-2.5">
            <div className="w-11 flex items-center">
              <button
                type="button"
                onClick={handleBack}
                className="p-2.5 -ml-2 rounded-xl bg-card/60 hover:bg-card border border-border/40 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all duration-200 active:scale-95 touch-manipulation"
                aria-label="뒤로 가기"
              >
                <ArrowLeft className="w-5 h-5 text-fg" aria-hidden="true" />
              </button>
            </div>
            <h1 className="text-base font-bold text-fg flex-1 text-center tracking-tight px-2">
              정보 탐색
            </h1>
            <div className="w-11 flex items-center justify-end">
              <button
                type="button"
                onClick={toggleTTS}
                className={`p-2.5 -mr-2 rounded-xl border focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all duration-200 active:scale-95 ${
                  isTTSEnabled 
                    ? 'bg-primary text-white border-primary/20 hover:bg-primary/90 shadow-sm' 
                    : 'bg-card/50 text-muted/60 border-border/50 hover:bg-card hover:border-border'
                }`}
                aria-label={isTTSEnabled ? '음성 안내 끄기' : '음성 안내 켜기'}
                aria-pressed={isTTSEnabled}
              >
                {isTTSEnabled ? (
                  <Volume2 className="w-4 h-4" aria-hidden="true" />
                ) : (
                  <VolumeX className="w-4 h-4" aria-hidden="true" />
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 상단 점자 출력 패널 - Sticky */}
      <BrailleOutputPanel 
        currentBraille={currentBraille}
        className="sticky top-[60px] z-20"
      />

      {/* 상단 컨트롤 바 */}
      <div className="bg-white border-b border-border px-4 py-2">
        <div className="w-full md:max-w-md md:mx-auto flex flex-wrap items-center gap-2">
          {/* BLE 연결 상태 */}
          <button
            onClick={async () => {
              try {
                if (isConnected) {
                  disconnect();
                } else {
                  await connect();
                }
              } catch (error) {
                console.log("BLE 연결 처리:", error);
              }
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 active:scale-95 ${
              isConnected
                ? 'bg-success text-white hover:bg-success/90 shadow-sm'
                : 'bg-card text-fg hover:bg-border border border-border'
            }`}
            aria-pressed={isConnected}
          >
            {isConnected ? '🔗 연결됨' : '🔌 연결'}
          </button>

          {/* 점자 출력 토글 */}
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={braille.enabled}
              onChange={(e) => braille.setEnabled(e.target.checked)}
              className="w-4 h-4 text-primary rounded focus:ring-primary"
              aria-label="점자 출력 토글"
            />
            <span className="text-xs font-medium text-fg">점자 출력</span>
          </label>

          {/* 빠른 액션 버튼들 */}
          <div className="ml-auto flex gap-1.5">
            <button
              onClick={() => handleExplore("오늘 뉴스")}
              disabled={isExploreLoading}
              className="px-2.5 py-1.5 rounded-lg bg-primary text-white text-xs font-medium hover:bg-primary/90 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm active:scale-95"
            >
              📰 뉴스
            </button>
            
            {/* 점자 제어 버튼들 */}
            <button
              onClick={() => braille.next()}
              disabled={!braille.queue.length}
              className="px-2 py-1.5 rounded-lg bg-success/10 text-success text-xs font-medium hover:bg-success/20 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed active:scale-95"
              title="다음"
            >
              ▶
            </button>
            <button
              onClick={() => braille.repeat()}
              disabled={!braille.queue.length}
              className="px-2 py-1.5 rounded-lg bg-accent/10 text-accent text-xs font-medium hover:bg-accent/20 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed active:scale-95"
              title="반복"
            >
              ⟳
            </button>
            <button
              onClick={() => braille.pause()}
              disabled={!braille.isPlaying}
              className="px-2 py-1.5 rounded-lg bg-danger/10 text-danger text-xs font-medium hover:bg-danger/20 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed active:scale-95"
              title="정지"
            >
              ⏸
            </button>
          </div>
        </div>
      </div>

      {/* 메인 콘텐츠 영역 */}
      <div className="flex-1 overflow-hidden pb-24">
        <div 
          ref={listRef}
          className="h-full overflow-y-auto px-4 py-4"
        >
          <div className="w-full md:max-w-md md:mx-auto space-y-6">
            {/* 정보탐색 결과 */}
            {exploreData && (
              <div className="bg-white rounded-xl shadow-md border border-gray-200 p-6">
                <div className="flex items-center gap-2 mb-4">
                  <span className="text-lg">🔍</span>
                  <h3 className="text-lg font-semibold text-gray-800">
                    정보탐색: {exploreData.query}
                  </h3>
                </div>
                
                <div className="mb-4">
                  <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                    {exploreData.answer}
                  </p>
                </div>

                {exploreData.news.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-600 mb-3">관련 뉴스</h4>
                    <div className="space-y-3">
                      {exploreData.news.slice(0, 3).map((news, index) => (
                        <div key={index} className="p-3 bg-gray-50 rounded-lg">
                          <a 
                            href={news.link} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="block group"
                          >
                            <h5 className="font-medium text-gray-800 group-hover:text-blue-600 transition-colors line-clamp-2">
                              {news.title?.replace(/<[^>]*>/g, '') || '제목 없음'}
                            </h5>
                            <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                              {news.description?.replace(/<[^>]*>/g, '') || '설명 없음'}
                            </p>
                            <div className="flex items-center justify-between mt-2">
                              <span className="text-xs text-gray-500">
                                {news.pubDate ? new Date(news.pubDate).toLocaleDateString('ko-KR') : '날짜 없음'}
                              </span>
                              <span className="text-xs text-blue-600 group-hover:text-blue-800">
                                원문 보기 →
                              </span>
                            </div>
                          </a>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* 채팅 메시지들 */}
            {messages.map((m) => {
              // 타이핑 인디케이터
              if (m.text === '__typing__') {
                return (
                  <div key={m.id} className="bg-white rounded-xl shadow-md border border-gray-200 p-6">
                    <div className="flex items-center gap-2" aria-label="답변 생성 중">
                      <span className="w-2 h-2 rounded-full bg-blue-400 animate-bounce [animation-delay:0ms]" />
                      <span className="w-2 h-2 rounded-full bg-blue-400 animate-bounce [animation-delay:120ms]" />
                      <span className="w-2 h-2 rounded-full bg-blue-400 animate-bounce [animation-delay:240ms]" />
                      <span className="text-sm text-gray-500 ml-2">답변을 생성하고 있습니다...</span>
                    </div>
                  </div>
                );
              }

              // 사용자 메시지
              if (m.role === 'user') {
                return (
                  <div key={m.id} className="flex justify-end">
                    <div className="bg-blue-600 text-white rounded-xl px-4 py-2 max-w-[80%] shadow-md">
                      <p className="text-sm leading-relaxed">{m.text}</p>
                    </div>
                  </div>
                );
              }

              // AI 답변 카드
              return (
                <AnswerCard
                  key={m.id}
                  text={m.text || ''}
                  keywords={m.keywords || []}
                  onBrailleOutput={handleBrailleOutput}
                  onLearn={handleLearn}
                />
              );
            })}

            {/* 로딩 상태는 __typing__ 메시지로 처리되므로 여기서는 제거 */}
          </div>
        </div>
      </div>

      {/* 하단 입력 영역 (고정 위치, 네비게이션 바 위) */}
      <div className="fixed bottom-24 left-0 right-0 z-40 bg-white/98 backdrop-blur-xl border-t border-border/60 shadow-lg">
        <div className="w-full md:max-w-md md:mx-auto px-4 py-2">
          <ChatLikeInput
            onSubmit={handleSubmit}
            disabled={isLoading}
            placeholder="궁금한 것을 물어보세요..."
          />
        </div>
      </div>

      {/* 하단 네비게이션 바 */}
      <nav 
        className="sticky bottom-0 z-50 bg-white/98 backdrop-blur-xl border-t border-border/60 shadow-[0_-2px_12px_rgba(0,0,0,0.05)]" 
        role="navigation" 
        aria-label="메인 네비게이션"
      >
        <div className="w-full md:max-w-md md:mx-auto px-3 py-2">
          <div className="flex items-center justify-around gap-1">
            <NavButton
              icon={Home}
              label="홈"
              onClick={() => navigate('/')}
              isActive={isActive('/')}
              ariaLabel="홈으로 가기"
              ariaCurrent={isActive('/') ? 'page' : undefined}
            />
            <NavButton
              icon={BookOpen}
              label="학습"
              onClick={() => navigate('/learn')}
              isActive={isActive('/learn')}
              ariaLabel="점자 학습"
              ariaCurrent={isActive('/learn') ? 'page' : undefined}
            />
            <NavButton
              icon={Search}
              label="탐색"
              onClick={() => navigate('/explore')}
              isActive={isActive('/explore')}
              ariaLabel="정보 탐색"
              ariaCurrent={isActive('/explore') ? 'page' : undefined}
            />
            <NavButton
              icon={RefreshCw}
              label="복습"
              onClick={() => navigate('/review')}
              isActive={isActive('/review')}
              ariaLabel="복습하기"
              ariaCurrent={isActive('/review') ? 'page' : undefined}
            />
            <NavButton
              icon={Type}
              label="자유"
              onClick={() => navigate('/free-convert')}
              isActive={isActive('/free-convert') || isActive('/learn/free')}
              ariaLabel="자유 변환"
              ariaCurrent={(isActive('/free-convert') || isActive('/learn/free')) ? 'page' : undefined}
            />
          </div>
        </div>
      </nav>

      {/* 토스트 알림 */}
      <ToastA11y
        message={toastMessage}
        isVisible={showToast}
        duration={3000}
        onClose={() => setShowToast(false)}
        position="top"
      />
    </div>
  );
}