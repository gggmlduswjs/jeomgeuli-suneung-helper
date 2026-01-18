import { useState, useEffect, useRef } from 'react';

interface AudioSyncOptions {
  lessonId: string;
  textSections: Array<{
    id: string;
    content: string;
    timestamp?: number;
  }>;
  audioElement?: HTMLAudioElement | null;
}

interface UseAudioSyncReturn {
  currentSection: number;
  isSyncing: boolean;
  syncError: string | null;
}

/**
 * 강의 음성-텍스트 자동 동기화 훅
 */
export function useAudioSync({
  lessonId,
  textSections,
  audioElement
}: AudioSyncOptions): UseAudioSyncReturn {
  const [currentSection, setCurrentSection] = useState(0);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncError, setSyncError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!audioElement || textSections.length === 0) {
      return;
    }

    // 재생 시간에 따라 해당 텍스트 섹션으로 자동 스크롤
    const handleTimeUpdate = () => {
      const currentTime = audioElement.currentTime;

      // 타임스탬프가 있는 섹션 찾기
      const sectionIndex = textSections.findIndex((section, index) => {
        const nextSection = textSections[index + 1];
        const sectionStart = section.timestamp || 0;
        const sectionEnd = nextSection?.timestamp || Infinity;

        return currentTime >= sectionStart && currentTime < sectionEnd;
      });

      if (sectionIndex !== -1 && sectionIndex !== currentSection) {
        setCurrentSection(sectionIndex);
        
        // 해당 섹션으로 스크롤
        const sectionElement = document.getElementById(`section-${textSections[sectionIndex].id}`);
        if (sectionElement) {
          sectionElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }
    };

    audioElement.addEventListener('timeupdate', handleTimeUpdate);

    return () => {
      audioElement.removeEventListener('timeupdate', handleTimeUpdate);
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [audioElement, textSections, currentSection]);

  return {
    currentSection,
    isSyncing,
    syncError
  };
}
