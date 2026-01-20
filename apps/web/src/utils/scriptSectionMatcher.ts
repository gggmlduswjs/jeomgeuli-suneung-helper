/**
 * 강의 대본 섹션과 블록 매칭 유틸리티
 * 블록과 강의 대본 JSON의 섹션을 키워드/제목으로 매칭
 */

export interface ScriptSection {
  section_id: string;
  title: string;
  keywords: string[];
  content: string;
}

export interface BlockInfo {
  block_id: string;
  title: string;
  block_type: string;
  keywords?: string[];
  content?: string;
}

/**
 * 텍스트 유형 추론
 * 강의 대본 내용을 분석하여 해설/필기/지시 구분
 */
export function inferTextType(section: ScriptSection): 'explanation' | 'note' | 'instruction' {
  const content = section.content.toLowerCase();
  const title = section.title.toLowerCase();
  
  // 지시 패턴 (문제 풀이, 명령형 표현)
  const instructionPatterns = [
    '문제', '풀어', '해결', '선택', '답', '보기', '보도록', '보겠습니다',
    '다음', '이제', '자', '봐', '보세요', '하세요', '보자', '가 볼게요',
    '읽어', '쓰', '적어', '표시', '체크', '확인', '보고', '옵시다',
    '넘어가', '갑니다', '해결하러', '한번', '같이', '보도록'
  ];
  
  // 필기 패턴 (중요 내용, 암기, 별표)
  const notePatterns = [
    '필기', '적어', '쓰', '기억', '암기', '정리', '챙겨',
    '표', '표시', '체크', '별표', '중요', '붙일게요', '써두세요',
    '챙겨가', '알아두세요', '기억해', '필수', '반드시', '꼭',
    '옆에다', '여기 쓸게요', '써 드릴게요', '이것까지'
  ];
  
  // 해설 패턴 (설명, 개념, 분석)
  const explanationPatterns = [
    '설명', '이해', '의미', '개념', '정의', '이유',
    '왜', '어떻게', '분석', '해석', '작품', '시',
    '이야기', '얘기', '말이야', '거야', '거죠', '거든요'
  ];
  
  // 제목 기반 우선 판단
  if (title.includes('문제')) {
    return 'instruction';
  }
  if (title.includes('정리') || title.includes('복습') || title.includes('담판')) {
    return 'note';
  }
  
  // 지시 우선 확인 (문제 풀이 관련)
  let instructionScore = 0;
  for (const pattern of instructionPatterns) {
    if (content.includes(pattern) || title.includes(pattern)) {
      instructionScore += title.includes(pattern) ? 3 : 1;
    }
  }
  
  // 필기 확인 (중요 내용 강조)
  let noteScore = 0;
  for (const pattern of notePatterns) {
    if (content.includes(pattern) || title.includes(pattern)) {
      noteScore += title.includes(pattern) ? 3 : 1;
    }
  }
  
  // 점수 기반 판단
  if (instructionScore >= 2) {
    return 'instruction';
  }
  if (noteScore >= 2) {
    return 'note';
  }
  
  // 기본값은 해설
  return 'explanation';
}

/**
 * 제목 정규화 (특수문자, 공백, 대소문자 제거)
 */
function normalizeTitle(title: string): string {
  return title
    .toLowerCase()
    .replace(/[–—\-]/g, '-')  // 다양한 대시 통일
    .replace(/[①-⑳]/g, '')  // 원문자 제거
    .replace(/[<>]/g, '')  // 괄호 제거
    .replace(/\s+/g, ' ')  // 여러 공백을 하나로
    .trim();
}

/**
 * 제목 핵심 단어 추출 (불필요한 단어 제거)
 */
function extractCoreWords(title: string): string[] {
  const normalized = normalizeTitle(title);
  const stopWords = ['의', '와', '과', '을', '를', '이', '가', '은', '는', '에서', '로', '으로', '에', '에게'];
  return normalized
    .split(/\s+/)
    .filter(word => word.length > 1 && !stopWords.includes(word))
    .filter(word => !/^[0-9]+$/.test(word)); // 숫자만 있는 단어 제거
}

/**
 * 블록과 강의 대본 섹션 매칭
 * 키워드와 제목을 기반으로 매칭 (개선된 버전)
 */
export function matchBlockToSection(
  block: BlockInfo,
  sections: ScriptSection[]
): ScriptSection | null {
  if (!sections || sections.length === 0) {
    return null;
  }
  
  const blockTitle = block.title || '';
  const blockTitleNormalized = normalizeTitle(blockTitle);
  const blockCoreWords = extractCoreWords(blockTitle);
  const blockKeywords = block.keywords || [];
  
  let bestMatch: ScriptSection | null = null;
  let bestScore = 0;
  
  for (const section of sections) {
    let score = 0;
    const sectionTitle = section.title || '';
    const sectionTitleNormalized = normalizeTitle(sectionTitle);
    const sectionCoreWords = extractCoreWords(sectionTitle);
    
    // 1. 제목 정확히 일치 (높은 점수)
    if (blockTitleNormalized === sectionTitleNormalized) {
      score += 100;
    }
    // 2. 제목 포함 관계 (높은 점수)
    else if (blockTitleNormalized.includes(sectionTitleNormalized) || 
             sectionTitleNormalized.includes(blockTitleNormalized)) {
      score += 50;
    }
    // 3. 핵심 단어 매칭 (중간 점수)
    else {
      const commonWords = blockCoreWords.filter(word => 
        sectionCoreWords.some(sw => sw.includes(word) || word.includes(sw))
      );
      score += commonWords.length * 10;
      
      // 핵심 단어가 모두 일치하면 높은 점수
      if (commonWords.length > 0 && 
          commonWords.length === Math.min(blockCoreWords.length, sectionCoreWords.length)) {
        score += 20;
      }
    }
    
    // 4. 키워드 매칭
    for (const sectionKeyword of section.keywords) {
      const sectionKwLower = sectionKeyword.toLowerCase();
      
      // 블록 키워드와 매칭
      for (const blockKeyword of blockKeywords) {
        const blockKwLower = blockKeyword.toLowerCase();
        if (blockKwLower === sectionKwLower) {
          score += 5;
        } else if (blockKwLower.includes(sectionKwLower) || sectionKwLower.includes(blockKwLower)) {
          score += 3;
        }
      }
      
      // 블록 제목과 키워드 매칭
      if (blockTitleNormalized.includes(sectionKwLower) || sectionKwLower.includes(blockTitleNormalized)) {
        score += 3;
      }
    }
    
    // 5. 특수 케이스 매칭
    // "강의 소개" <-> "강의 오리엔테이션"
    if ((blockTitle.includes('강의 소개') || blockTitle.includes('오리엔테이션')) &&
        (sectionTitle.includes('강의 소개') || sectionTitle.includes('오리엔테이션'))) {
      score += 30;
    }
    
    // "시적 화자의 정서" <-> "시의 내용 – 화자와 정서"
    if ((blockTitle.includes('화자') && blockTitle.includes('정서')) &&
        (sectionTitle.includes('화자') && sectionTitle.includes('정서'))) {
      score += 30;
    }
    
    // "박두진의 해" <-> "작품 ① 박두진 <해>"
    if (blockTitle.includes('박두진') && blockTitle.includes('해') &&
        sectionTitle.includes('박두진') && sectionTitle.includes('해')) {
      score += 30;
    }
    
    // "문제 1번" <-> "문제 1번 – 표현"
    if (blockTitle.includes('문제') && sectionTitle.includes('문제')) {
      const blockNum = blockTitle.match(/문제\s*(\d+)/)?.[1];
      const sectionNum = sectionTitle.match(/문제\s*(\d+)/)?.[1];
      if (blockNum && sectionNum && blockNum === sectionNum) {
        score += 30;
      }
    }
    
    if (score > bestScore) {
      bestScore = score;
      bestMatch = section;
    }
  }
  
  // 점수가 10 이상이면 매칭된 것으로 간주 (기존 2에서 상향)
  return bestScore >= 10 ? bestMatch : null;
}

/**
 * 블록 JSON 파일 로드
 */
export interface BlockData {
  block_id: string;
  block_type: string;
  order: number;
  title: string;
  keywords: string[];
  tts?: {
    mode: string;
    script: string;
  };
  pdf_ref?: {
    page: number;
    position: string;
  };
  [key: string]: any;
}

export interface BlocksJsonData {
  lesson_id: string;
  subject: string;
  lesson_number: number;
  lesson_title: string;
  blocks: BlockData[];
}

export async function loadBlocksJson(
  subject: string,
  lessonNumber: number
): Promise<BlocksJsonData | null> {
  try {
    const possiblePaths = [
      `/api/data/${subject}_${lessonNumber}_blocks.json`,
      `/api/data/${subject}_${String(lessonNumber).padStart(2, '0')}_blocks.json`,
      `/api/data/${subject}_1_blocks.json`, // 기본값
    ];
    
    for (const blocksPath of possiblePaths) {
      try {
        const cacheBuster = `?t=${Date.now()}`;
        const response = await fetch(blocksPath + cacheBuster, {
          cache: 'no-cache',
          headers: {
            'Cache-Control': 'no-cache',
          },
        });
        if (response.ok) {
          const data = await response.json();
          if (data.blocks && Array.isArray(data.blocks)) {
            console.log(`[ScriptMatcher] 블록 JSON 로드 성공: ${blocksPath} (${data.blocks.length}개 블록)`);
            return data as BlocksJsonData;
          }
        }
      } catch (e) {
        continue;
      }
    }
    
    console.warn(`[ScriptMatcher] 블록 JSON을 찾을 수 없습니다. 시도한 경로: ${possiblePaths.join(', ')}`);
    return null;
  } catch (error) {
    console.error('[ScriptMatcher] 블록 JSON 로드 실패:', error);
    return null;
  }
}

/**
 * 강의 대본 JSON 로드 및 매칭
 */
export async function loadAndMatchScriptSections(
  lessonId: string,
  subject: string,
  lessonNumber: number
): Promise<ScriptSection[]> {
  try {
    // 강의 대본 JSON 파일 경로
    // 여러 가능한 경로 시도 (실제 파일 위치에 맞게)
    const possiblePaths = [
      `/api/data/${subject}_${lessonNumber}_script.json`,  // api/data/korean_1_script.json
      `/api/data/${subject}_${String(lessonNumber).padStart(2, '0')}_script.json`,
      `/api/data/${subject}_1_script.json`, // 기본값
      `/api/data/lecture_scripts_json/${subject}_${lessonNumber}_script.json`, // 이전 경로 (호환성)
    ];
    
    for (const scriptPath of possiblePaths) {
      try {
        // 캐시 무시: 최신 데이터를 가져오기 위해 timestamp 추가
        const cacheBuster = `?t=${Date.now()}`;
        const response = await fetch(scriptPath + cacheBuster, {
          cache: 'no-cache',
          headers: {
            'Cache-Control': 'no-cache',
          },
        });
        if (response.ok) {
          const data = await response.json();
          const sections = data.script_sections || [];
          if (sections.length > 0) {
            console.log(`[ScriptMatcher] 강의 대본 JSON 로드 성공: ${scriptPath} (${sections.length}개 섹션)`);
            return sections;
          }
        }
      } catch (e) {
        // 다음 경로 시도
        continue;
      }
    }
    
    console.warn(`[ScriptMatcher] 강의 대본 JSON을 찾을 수 없습니다. 시도한 경로: ${possiblePaths.join(', ')}`);
    return [];
  } catch (error) {
    console.error('[ScriptMatcher] 강의 대본 JSON 로드 실패:', error);
    return [];
  }
}

/**
 * 블록별로 매칭된 섹션 정보 저장
 */
export interface BlockSectionMatch {
  block_id: string;
  section: ScriptSection;
  text_type: 'explanation' | 'note' | 'instruction';
  match_score: number;
}

export class BlockSectionMatcher {
  private matches: Map<string, BlockSectionMatch> = new Map();
  private sections: ScriptSection[] = [];
  private blocksData: BlocksJsonData | null = null;
  private blockMap: Map<string, BlockData> = new Map(); // block_id -> BlockData
  private orderMap: Map<number, BlockData> = new Map(); // order -> BlockData
  
  /**
   * 강의 대본 섹션 및 블록 JSON 로드
   */
  async loadSections(lessonId: string, subject: string, lessonNumber: number): Promise<void> {
    // script.json 로드
    this.sections = await loadAndMatchScriptSections(lessonId, subject, lessonNumber);
    
    // blocks.json 로드
    this.blocksData = await loadBlocksJson(subject, lessonNumber);
    
    if (this.blocksData && this.blocksData.blocks) {
      // 블록 맵 생성 (block_id와 order 기반)
      this.blocksData.blocks.forEach(block => {
        this.blockMap.set(block.block_id, block);
        this.orderMap.set(block.order, block);
      });
      console.log(`[BlockSectionMatcher] 블록 데이터 로드 완료: ${this.blocksData.blocks.length}개 블록`);
    }
  }
  
  /**
   * block_id로 블록 데이터 조회
   */
  getBlockByBlockId(blockId: string): BlockData | undefined {
    return this.blockMap.get(blockId);
  }
  
  /**
   * order로 블록 데이터 조회
   */
  getBlockByOrder(order: number): BlockData | undefined {
    return this.orderMap.get(order);
  }
  
  /**
   * unit_index로 블록 데이터 조회 (unit_index는 0-based, order는 0-based)
   */
  getBlockByUnitIndex(unitIndex: number): BlockData | undefined {
    return this.orderMap.get(unitIndex);
  }
  
  /**
   * 블록과 섹션 매칭 (개선된 버전: blocks.json 우선 사용)
   */
  matchBlock(block: BlockInfo): BlockSectionMatch | null {
    // 1. blocks.json에서 직접 블록 찾기 (block_id 기반)
    let blockData: BlockData | undefined;
    if (block.block_id) {
      blockData = this.getBlockByBlockId(block.block_id);
    }
    
    // 2. blocks.json의 tts.script가 있으면 우선 사용
    if (blockData && blockData.tts && blockData.tts.script) {
      // script.json에서 매칭된 섹션 찾기 (참고용)
      const matchedSection = matchBlockToSection(block, this.sections);
      
      const textType = matchedSection ? inferTextType(matchedSection) : 'explanation';
      const match: BlockSectionMatch = {
        block_id: block.block_id,
        section: matchedSection || {
          section_id: blockData.block_id,
          title: blockData.title,
          keywords: blockData.keywords || [],
          content: blockData.tts.script
        },
        text_type: textType,
        match_score: matchedSection ? 100 : 50 // blocks.json 직접 매칭은 높은 점수
      };
      
      this.matches.set(block.block_id, match);
      return match;
    }
    
    // 3. blocks.json에 없으면 script.json에서 매칭 시도
    const matchedSection = matchBlockToSection(block, this.sections);
    
    if (!matchedSection) {
      return null;
    }
    
    const textType = inferTextType(matchedSection);
    const match: BlockSectionMatch = {
      block_id: block.block_id,
      section: matchedSection,
      text_type: textType,
      match_score: 1
    };
    
    this.matches.set(block.block_id, match);
    return match;
  }
  
  /**
   * 블록 ID로 매칭된 섹션 조회
   */
  getMatch(blockId: string): BlockSectionMatch | undefined {
    return this.matches.get(blockId);
  }
  
  /**
   * 모든 매칭 조회
   */
  getAllMatches(): BlockSectionMatch[] {
    return Array.from(this.matches.values());
  }
  
  /**
   * 섹션 ID로 섹션 조회
   */
  getSection(sectionId: string): ScriptSection | undefined {
    return this.sections.find(s => s.section_id === sectionId);
  }
  
  /**
   * blocks.json의 블록 데이터 조회
   */
  getBlocksData(): BlocksJsonData | null {
    return this.blocksData;
  }
}
