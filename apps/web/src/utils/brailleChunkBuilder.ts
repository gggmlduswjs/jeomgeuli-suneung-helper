/**
 * Builder Pattern - 점자 청크 빌더
 * 복잡한 텍스트를 점자 청크로 구성하는 빌더
 */

export class BrailleChunkBuilder {
  private chunks: string[] = [];
  private currentChunk: string = '';
  private maxCells: number;

  constructor(maxCells: number = 3) {
    this.maxCells = maxCells;
  }

  /**
   * 일반 텍스트 추가
   */
  addText(text: string): this {
    if (!text) return this;

    const words = text.split(/\s+/).filter(w => w.length > 0);
    
    for (const word of words) {
      const testChunk = this.currentChunk 
        ? `${this.currentChunk} ${word}` 
        : word;
      
      const estimatedCells = this.estimateCells(testChunk);
      
      if (estimatedCells <= this.maxCells) {
        this.currentChunk = testChunk;
      } else {
        if (this.currentChunk) {
          this.chunks.push(this.currentChunk);
        }
        this.currentChunk = word;
      }
    }

    return this;
  }

  /**
   * 수식 추가 (의미 단위 보존)
   */
  addFormula(formula: string): this {
    if (!formula) return this;

    // 수식은 하나의 청크로 유지 (가능한 경우)
    const estimatedCells = this.estimateCells(formula);
    
    if (estimatedCells <= this.maxCells) {
      // 현재 청크에 추가 가능
      if (this.currentChunk) {
        const testChunk = `${this.currentChunk} ${formula}`;
        if (this.estimateCells(testChunk) <= this.maxCells) {
          this.currentChunk = testChunk;
        } else {
          this.chunks.push(this.currentChunk);
          this.currentChunk = formula;
        }
      } else {
        this.currentChunk = formula;
      }
    } else {
      // 수식이 너무 길면 분할
      if (this.currentChunk) {
        this.chunks.push(this.currentChunk);
        this.currentChunk = '';
      }
      // 수식을 문자 단위로 분할
      const formulaChunks = this.splitLongText(formula);
      this.chunks.push(...formulaChunks);
    }

    return this;
  }

  /**
   * 키워드 추가 (강조 표시용)
   */
  addKeyword(keyword: string): this {
    if (!keyword) return this;

    // 키워드는 별도 청크로 분리 (강조를 위해)
    if (this.currentChunk) {
      this.chunks.push(this.currentChunk);
      this.currentChunk = '';
    }

    const estimatedCells = this.estimateCells(keyword);
    if (estimatedCells <= this.maxCells) {
      this.chunks.push(keyword);
    } else {
      // 긴 키워드는 분할
      const keywordChunks = this.splitLongText(keyword);
      this.chunks.push(...keywordChunks);
    }

    return this;
  }

  /**
   * 청크 빌드 완료
   */
  build(): string[] {
    if (this.currentChunk) {
      this.chunks.push(this.currentChunk);
      this.currentChunk = '';
    }
    return this.chunks.length > 0 ? this.chunks : [];
  }

  /**
   * 청크 수 예상
   */
  private estimateCells(text: string): number {
    if (!text) return 0;

    let cells = 0;
    for (const char of text) {
      if (/[가-힣]/.test(char)) {
        cells += 2; // 한글: 2 cells
      } else if (/[a-zA-Z0-9]/.test(char)) {
        cells += 1; // 영문/숫자: 1 cell
      } else if (/\s/.test(char)) {
        cells += 0.5; // 공백: 0.5 cell
      } else {
        cells += 1; // 기타: 1 cell
      }
    }

    return Math.ceil(cells);
  }

  /**
   * 긴 텍스트 분할
   */
  private splitLongText(text: string): string[] {
    const chunks: string[] = [];
    let currentChunk = '';

    for (const char of text) {
      const testChunk = currentChunk + char;
      const estimatedCells = this.estimateCells(testChunk);

      if (estimatedCells <= this.maxCells) {
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

    return chunks.length > 0 ? chunks : [text];
  }

  /**
   * 빌더 초기화
   */
  reset(): this {
    this.chunks = [];
    this.currentChunk = '';
    return this;
  }
}

