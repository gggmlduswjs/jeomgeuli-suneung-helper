/**
 * TOC 텍스트 자동 분석 hook
 * 목차 텍스트에서 강의 라인, 비강의 라인, 강의 개수를 자동으로 추출
 */
import { useEffect } from 'react';

interface AutoExtractResult {
  lectureLines: string[];
  nonLectureLines: string[];
  lectureCount: number;
}

/**
 * TOC 텍스트를 분석하여 강의 정보를 자동 추출
 */
export function extractTOCInfo(tocText: string): AutoExtractResult {
  const lines = tocText.split('\n').map(l => l.trim()).filter(Boolean);

  // 강의 라인 패턴 찾기 (예: "1강", "2강", "1강 |", "강 1" 등)
  const lecturePattern = /(\d+)\s*강|강\s*(\d+)/i;
  const lectureLines: string[] = [];
  const nonLectureKeywords = ['정답', '해설', '부록', '찾아보기', '목차', '차례', 'INDEX', 'Appendix'];
  const nonLectureLines: string[] = [];
  const lectureNumbers = new Set<number>();

  for (const line of lines) {
    const lectureMatch = lecturePattern.exec(line);
    if (lectureMatch) {
      const num = parseInt(lectureMatch[1] || lectureMatch[2], 10);
      if (!isNaN(num) && num > 0 && num < 200) {
        lectureNumbers.add(num);
        if (lectureLines.length < 5) {
          lectureLines.push(line);
        }
      }
    } else {
      // 비강의 라인 체크
      const isNonLecture = nonLectureKeywords.some(keyword =>
        line.includes(keyword) && line.length < 50
      );
      if (isNonLecture && nonLectureLines.length < 3) {
        nonLectureLines.push(line);
      }
    }
  }

  return {
    lectureLines,
    nonLectureLines,
    lectureCount: lectureNumbers.size
  };
}

/**
 * TOC 텍스트 자동 분석 hook
 * tocText가 변경되면 자동으로 강의 정보를 추출하고 콜백 호출
 */
export function useTOCAutoExtract(
  tocText: string,
  onExtract: (result: AutoExtractResult) => void,
  deps: React.DependencyList = []
) {
  useEffect(() => {
    // 텍스트가 충분히 길면 자동 분석
    if (tocText.trim().length > 50) {
      const result = extractTOCInfo(tocText);

      // 강의 라인이 최소 1개 이상 있으면 콜백 호출
      if (result.lectureLines.length > 0) {
        onExtract(result);
      }
    }
  }, [tocText, ...deps]);
}
