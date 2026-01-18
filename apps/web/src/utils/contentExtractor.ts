/**
 * 콘텐츠 추출 유틸리티
 * 수식, 키워드, 핵심 문장 등을 추출
 */

/**
 * 수식 추출 (예: "x² + 2x + 1 = 0")
 */
export function extractFormula(text: string): string {
  if (!text) return '';

  // 수식 패턴: 변수, 지수, 연산자, 등호 등
  const formulaPattern = /[a-zA-Z]\s*[²³⁴⁵⁶⁷⁸⁹⁰⁺⁻⁼⁽⁾∫∑∏√∞±×÷≤≥≠≈]|[\+\-\*\/\=\<\>\(\)\^]|\\[a-zA-Z]+/g;
  
  const matches = text.match(formulaPattern);
  if (matches && matches.length > 0) {
    // 수식 부분만 추출
    const formulaStart = text.search(formulaPattern);
    if (formulaStart !== -1) {
      // 수식이 끝나는 지점 찾기 (공백, 문장부호 등)
      let formulaEnd = formulaStart;
      for (let i = formulaStart; i < text.length; i++) {
        const char = text[i];
        if (/[.!?]/.test(char) || (/\s/.test(char) && i > formulaStart + 10)) {
          formulaEnd = i;
          break;
        }
      }
      if (formulaEnd === formulaStart) {
        formulaEnd = Math.min(formulaStart + 50, text.length);
      }
      return text.substring(formulaStart, formulaEnd).trim();
    }
  }

  return '';
}

/**
 * 핵심 키워드 추출
 * @param text 텍스트
 * @param maxCount 최대 키워드 수
 */
export function extractKeywords(text: string, maxCount: number = 3): string[] {
  if (!text) return [];

  // 한글 키워드 패턴 (2글자 이상 명사)
  const koreanKeywordPattern = /[가-힣]{2,}/g;
  const koreanMatches = text.match(koreanKeywordPattern) || [];

  // 영어 키워드 패턴 (3글자 이상 단어)
  const englishKeywordPattern = /\b[a-zA-Z]{3,}\b/g;
  const englishMatches = text.match(englishKeywordPattern) || [];

  // 키워드 빈도 계산
  const keywordCount: Map<string, number> = new Map();
  
  [...koreanMatches, ...englishMatches].forEach(keyword => {
    const lower = keyword.toLowerCase();
    keywordCount.set(lower, (keywordCount.get(lower) || 0) + 1);
  });

  // 빈도순으로 정렬
  const sorted = Array.from(keywordCount.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, maxCount)
    .map(([keyword]) => keyword);

  return sorted;
}

/**
 * 지문 핵심 문장 추출
 */
export function extractPassageKey(passage: string): string {
  if (!passage) return '';

  // 문장 분리
  const sentences = passage.split(/[.!?]\s+/).filter(s => s.trim().length > 0);
  
  if (sentences.length === 0) return passage;

  // 첫 번째 문장과 마지막 문장이 핵심일 가능성이 높음
  // 중간 문장 중 가장 긴 문장도 고려
  const firstSentence = sentences[0];
  const lastSentence = sentences[sentences.length - 1];
  const longestSentence = sentences.reduce((longest, current) => 
    current.length > longest.length ? current : longest
  );

  // 핵심 문장 선택 (첫 문장 우선, 길이 고려)
  if (firstSentence.length >= 20) {
    return firstSentence;
  } else if (longestSentence.length >= 30) {
    return longestSentence;
  } else {
    return lastSentence;
  }
}

/**
 * 수식이 포함된 텍스트인지 확인
 */
export function containsFormula(text: string): boolean {
  if (!text) return false;
  
  const formulaPattern = /[a-zA-Z]\s*[²³⁴⁵⁶⁷⁸⁹⁰⁺⁻⁼⁽⁾∫∑∏√∞±×÷≤≥≠≈]|[\+\-\*\/\=\<\>\(\)\^]|\\[a-zA-Z]+/;
  return formulaPattern.test(text);
}

/**
 * 텍스트에서 숫자 추출
 */
export function extractNumbers(text: string): number[] {
  if (!text) return [];

  const numberPattern = /-?\d+\.?\d*/g;
  const matches = text.match(numberPattern);
  
  if (!matches) return [];

  return matches.map(m => {
    const num = parseFloat(m);
    return isNaN(num) ? 0 : num;
  }).filter(n => n !== 0);
}

