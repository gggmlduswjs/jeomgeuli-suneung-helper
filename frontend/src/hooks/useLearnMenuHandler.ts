/**
 * 학습 메뉴 항목 선택 처리 훅
 * 음성 명령으로 자모/단어/문장/자유변환 페이지로 이동
 */
import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import useTTS from './useTTS';

export function useLearnMenuHandler(stopSTT: () => void) {
  const navigate = useNavigate();
  const { speak, stop: stopTTS } = useTTS();

  const handleLearnMenuSelection = useCallback((text: string) => {
    let normalized = text.toLowerCase().trim();

    // 오인식 패턴 보정
    const misrecognitionMap: Record<string, string> = {
      "자무": "자모", "자모.": "자모", "참호": "자모", "잠오": "자모", "사모": "자모",
      "단어.": "단어", "다워": "단어", "다오": "단어", "암호": "단어",
      "문장.": "문장",
      "학습모드": "학습", "학습모드.": "학습",
    };

    for (const [wrong, correct] of Object.entries(misrecognitionMap)) {
      if (normalized.includes(wrong)) {
        normalized = normalized.replace(wrong, correct);
      }
    }

    // 자모 학습
    if (/(자모|자음|모음|자무|참호|잠오|사모)/.test(normalized) ||
        normalized.startsWith('자') ||
        normalized.includes('자모') ||
        normalized.includes('자음') ||
        normalized.includes('모음') ||
        (normalized.length <= 3 && normalized[0] === '자')) {
      stopTTS();
      navigate('/learn/char');
      speak('자모 학습으로 이동합니다.');
      stopSTT();
      return true;
    }

    // 단어 학습
    if (/(단어|워드|다워|다오|암호|word)/.test(normalized) ||
        normalized.startsWith('단') ||
        normalized.startsWith('word') ||
        normalized.includes('단어') ||
        normalized.includes('다워') ||
        normalized.includes('암호') ||
        normalized.includes('word') ||
        (normalized.length <= 3 && normalized[0] === '단') ||
        (normalized.length <= 3 && normalized[0] === '다') ||
        normalized === 'word' || normalized === '워드') {
      stopTTS();
      navigate('/learn/word');
      speak('단어 학습으로 이동합니다.');
      stopSTT();
      return true;
    }

    // 문장 학습
    if (/(문장|센턴스)/.test(normalized) ||
        normalized.startsWith('문') ||
        normalized.includes('문장') ||
        (normalized.length <= 3 && normalized[0] === '문')) {
      stopTTS();
      navigate('/learn/sentence');
      speak('문장 학습으로 이동합니다.');
      stopSTT();
      return true;
    }

    // 자유 변환
    if (/(자유\s*변환|자유변환|변환)/.test(normalized) ||
        normalized.includes('변환') ||
        normalized.includes('자유')) {
      stopTTS();
      navigate('/learn/free');
      speak('자유 변환으로 이동합니다.');
      stopSTT();
      return true;
    }

    return false;
  }, [navigate, speak, stopTTS, stopSTT]);

  return { handleLearnMenuSelection };
}
