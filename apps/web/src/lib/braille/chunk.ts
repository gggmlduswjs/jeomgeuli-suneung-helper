/**
 * 텍스트 청크 분할 유틸리티
 * 3-cell 점자 디스플레이 제약을 고려한 텍스트 분할
 */

export interface ChunkOptions {
  maxCells: number;
  strategy: 'word' | 'sentence' | 'smart';
  preserveMeaning?: boolean; // 의미 단위 보존
}

/**
 * 텍스트를 점자 청크로 분할
 */
export function splitToBrailleChunks(
  text: string,
  options: ChunkOptions
): string[] {
  const { maxCells, strategy, preserveMeaning = true } = options;

  if (!text || text.trim().length === 0) {
    return [];
  }

  switch (strategy) {
    case 'word':
      return splitByWord(text, maxCells, preserveMeaning);
    
    case 'sentence':
      return splitBySentence(text, maxCells, preserveMeaning);
    
    case 'smart':
      return splitBySmart(text, maxCells, preserveMeaning);
    
    default:
      return splitByWord(text, maxCells, preserveMeaning);
  }
}

/**
 * 단어 단위 분할
 */
function splitByWord(text: string, maxCells: number, preserveMeaning: boolean): string[] {
  const words = text.split(/\s+/).filter(w => w.length > 0);
  const chunks: string[] = [];
  let currentChunk = '';

  for (const word of words) {
    const testChunk = currentChunk ? `${currentChunk} ${word}` : word;
    const estimatedCells = estimateBrailleCells(testChunk);

    if (estimatedCells <= maxCells) {
      currentChunk = testChunk;
    } else {
      if (currentChunk) {
        chunks.push(currentChunk);
      }
      // 단어가 maxCells를 초과하는 경우 강제로 분할
      if (estimateBrailleCells(word) > maxCells) {
        // 긴 단어는 문자 단위로 분할
        const wordChunks = splitLongWord(word, maxCells);
        chunks.push(...wordChunks);
        currentChunk = '';
      } else {
        currentChunk = word;
      }
    }
  }

  if (currentChunk) {
    chunks.push(currentChunk);
  }

  return chunks.length > 0 ? chunks : [text];
}

/**
 * 문장 단위 분할
 */
function splitBySentence(text: string, maxCells: number, preserveMeaning: boolean): string[] {
  // 문장 구분자: . ! ? (한글/영문 모두)
  const sentences = text.split(/([.!?]\s+)/).filter(s => s.trim().length > 0);
  const chunks: string[] = [];
  let currentChunk = '';

  for (let i = 0; i < sentences.length; i++) {
    const sentence = sentences[i];
    const testChunk = currentChunk ? `${currentChunk}${sentence}` : sentence;
    const estimatedCells = estimateBrailleCells(testChunk);

    if (estimatedCells <= maxCells) {
      currentChunk = testChunk;
    } else {
      if (currentChunk) {
        chunks.push(currentChunk.trim());
      }
      // 문장이 maxCells를 초과하는 경우 단어 단위로 재분할
      if (estimateBrailleCells(sentence) > maxCells) {
        const sentenceChunks = splitByWord(sentence, maxCells, preserveMeaning);
        chunks.push(...sentenceChunks);
        currentChunk = '';
      } else {
        currentChunk = sentence;
      }
    }
  }

  if (currentChunk) {
    chunks.push(currentChunk.trim());
  }

  return chunks.length > 0 ? chunks : [text];
}

/**
 * 스마트 분할 (의미 단위)
 */
function splitBySmart(text: string, maxCells: number, preserveMeaning: boolean): string[] {
  // 수식 패턴 감지 (예: x², ∫, ∑ 등)
  const formulaPattern = /[a-zA-Z]\s*[²³⁴⁵⁶⁷⁸⁹⁰⁺⁻⁼⁽⁾∫∑∏√∞±×÷≤≥≠≈]/g;
  
  // 구문 패턴 (예: "~이다", "~하다" 등)
  const phrasePattern = /[가-힣]+(?:이다|하다|되다|있다|없다|되다)/g;
  
  // 먼저 수식과 구문을 보존하면서 분할
  const chunks: string[] = [];
  let remaining = text;
  let lastIndex = 0;

  // 수식과 구문 위치 찾기
  const importantParts: Array<{ start: number; end: number; text: string }> = [];
  
  let match;
  while ((match = formulaPattern.exec(text)) !== null) {
    importantParts.push({
      start: match.index,
      end: match.index + match[0].length,
      text: match[0],
    });
  }
  
  while ((match = phrasePattern.exec(text)) !== null) {
    importantParts.push({
      start: match.index,
      end: match.index + match[0].length,
      text: match[0],
    });
  }

  // 중요 부분을 기준으로 분할
  if (importantParts.length > 0) {
    // 중요 부분을 기준으로 앞뒤 텍스트 분할
    for (const part of importantParts) {
      if (part.start > lastIndex) {
        const before = text.substring(lastIndex, part.start);
        if (before.trim()) {
          const beforeChunks = splitByWord(before, maxCells, preserveMeaning);
          chunks.push(...beforeChunks);
        }
      }
      
      // 중요 부분 자체가 maxCells를 초과하면 분할
      if (estimateBrailleCells(part.text) > maxCells) {
        const partChunks = splitByWord(part.text, maxCells, preserveMeaning);
        chunks.push(...partChunks);
      } else {
        chunks.push(part.text);
      }
      
      lastIndex = part.end;
    }
    
    // 남은 텍스트 처리
    if (lastIndex < text.length) {
      const after = text.substring(lastIndex);
      if (after.trim()) {
        const afterChunks = splitByWord(after, maxCells, preserveMeaning);
        chunks.push(...afterChunks);
      }
    }
  } else {
    // 중요 부분이 없으면 단어 단위로 분할
    return splitByWord(text, maxCells, preserveMeaning);
  }

  return chunks.length > 0 ? chunks : [text];
}

/**
 * 긴 단어를 문자 단위로 분할
 */
function splitLongWord(word: string, maxCells: number): string[] {
  const chunks: string[] = [];
  let currentChunk = '';

  for (const char of word) {
    const testChunk = currentChunk + char;
    const estimatedCells = estimateBrailleCells(testChunk);

    if (estimatedCells <= maxCells) {
      currentChunk = testChunk;
    } else {
      if (currentChunk) {
        chunks.push(currentChunk);
      }
      currentChunk = char;
    }
  }

  if (currentChunk) {
    chunks.push(currentChunk);
  }

  return chunks.length > 0 ? chunks : [word];
}

/**
 * 텍스트를 점자로 변환했을 때 예상 cell 수 계산
 * 간단한 추정: 한글 1자 = 2 cells, 영문/숫자 1자 = 1 cell, 공백 = 0.5 cell
 */
export function estimateBrailleCells(text: string): number {
  if (!text) return 0;

  let cells = 0;
  for (const char of text) {
    if (/[가-힣]/.test(char)) {
      // 한글: 2 cells
      cells += 2;
    } else if (/[a-zA-Z0-9]/.test(char)) {
      // 영문/숫자: 1 cell
      cells += 1;
    } else if (/\s/.test(char)) {
      // 공백: 0.5 cell (반올림)
      cells += 0.5;
    } else {
      // 기타 문자: 1 cell
      cells += 1;
    }
  }

  return Math.ceil(cells);
}

