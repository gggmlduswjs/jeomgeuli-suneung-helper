/**
 * 문학 교재 API 서비스
 */
import { api } from './api';

export interface LiteratureLecture {
  subject: string;
  lecture_id: number;
  title: string;
  problems?: string[];  // 문제 ID 목록 (예: ["01", "02", "03"])
  keywords?: string[];  // 핵심 키워드 목록 (예: ["시적 표현", "형식", "형상화"])
  sections: Array<{
    title: string;
    content: string[];
    page?: number;  // 페이지 정보 (이미지 매칭용)
  }>;
}

// 강의 목록용 타입 (sections 없음)
export interface LiteratureLectureSummary {
  lecture_id: number;
  title: string;
}

export interface LiteratureProblem {
  problem_id: string;
  page: number;
  content: string[];
  choices: Record<string, string>;
  question_text: string;
  full_text: string;
  bbox?: number[];
}

export interface LiteratureContent {
  content_id: string;
  page: number;
  title: string;
  image_path: string;
  text: string[];  // 원본 텍스트 (TTS용)
  bbox: number[];
  lecture_id?: number;  // 속한 강의 ID
}

export const literatureAPI = {
  /**
   * 문학 강의 목록 조회
   */
  async getLectures(): Promise<LiteratureLectureSummary[]> {
    return api.get<LiteratureLectureSummary[]>('/literature/lectures');
  },

  /**
   * 문학 강의 상세 조회
   */
  async getLecture(lectureId: number): Promise<LiteratureLecture> {
    return api.get<LiteratureLecture>(`/literature/lectures/${lectureId}`);
  },

  /**
   * 문학 문제 목록 조회
   */
  async getProblems(): Promise<LiteratureProblem[]> {
    return api.get<LiteratureProblem[]>('/literature/problems');
  },

  /**
   * 문학 문제 상세 조회
   */
  async getProblem(problemId: string): Promise<LiteratureProblem> {
    return api.get<LiteratureProblem>(`/literature/problems/${problemId}`);
  },

  /**
   * 개념 이미지 목록
   */
  async getConceptImages(): Promise<string[]> {
    return api.get<string[]>('/literature/images/concepts');
  },

  /**
   * 본문 이미지 목록
   */
  async getContentImages(): Promise<string[]> {
    return api.get<string[]>('/literature/images/content');
  },

  /**
   * 문제 이미지 목록
   */
  async getProblemImages(): Promise<string[]> {
    return api.get<string[]>('/literature/images/problems');
  },

  /**
   * 본문 목록 조회 (이미지 + 메타데이터)
   */
  async getContentList(): Promise<LiteratureContent[]> {
    return api.get<LiteratureContent[]>('/literature/content');
  },

  /**
   * 본문 상세 조회
   */
  async getContent(contentId: string): Promise<LiteratureContent> {
    return api.get<LiteratureContent>(`/literature/content/${contentId}`);
  },

  /**
   * AI 개념 설명
   */
  async explainConcept(conceptTitle: string, conceptContent: string[], subject: string = 'literature') {
    return api.post<{
      concept_title: string;
      original_content: string[];
      ai_explanation: string;
      subject: string;
    }>('/literature/ai/explain-concept', {
      concept_title: conceptTitle,
      concept_content: conceptContent,
      subject,
    });
  },

  /**
   * AI 본문 설명
   */
  async explainContent(contentTitle: string, contentText: string[], subject: string = 'literature') {
    return api.post<{
      content_title: string;
      original_text: string[];
      ai_explanation: string;
      subject: string;
    }>('/literature/ai/explain-content', {
      content_title: contentTitle,
      content_text: contentText,
      subject,
    });
  },

  /**
   * AI 문제 설명
   */
  async explainProblem(
    problemId: string,
    questionText: string,
    choices: Record<string, string>,
    passage?: string[],
    subject: string = 'literature'
  ) {
    return api.post<{
      problem_id: string;
      question_text: string;
      choices: Record<string, string>;
      passage?: string[];
      ai_explanation: string;
      subject: string;
    }>('/literature/ai/explain-problem', {
      problem_id: problemId,
      question_text: questionText,
      choices,
      passage,
      subject,
    });
  },

  /**
   * 유사 콘텐츠 찾기 (ML 기반)
   */
  async findSimilarContent(
    queryText: string,
    candidateTexts: string[],
    topK: number = 5,
    minSimilarity: number = 0.3,
    subject: string = 'literature'
  ) {
    return api.post<{
      query_text: string;
      similar_contents: Array<{
        text: string;
        similarity: number;
        index: number;
      }>;
      top_k: number;
      min_similarity: number;
      total_candidates: number;
      found_count: number;
      subject: string;
    }>('/literature/ai/find-similar-content', {
      query_text: queryText,
      candidate_texts: candidateTexts,
      top_k: topK,
      min_similarity: minSimilarity,
      subject,
    });
  },

  /**
   * TF-IDF 기반 키워드 추출
   */
  async extractKeywordsTFIDF(
    texts: string[],
    topK: number = 10,
    subject: string = 'literature'
  ) {
    return api.post<{
      keywords: Array<{
        keyword: string;
        score: number;
      }>;
      top_k: number;
      total_texts: number;
      subject: string;
    }>('/literature/ai/extract-keywords-tfidf', {
      texts,
      top_k: topK,
      subject,
    });
  },

  /**
   * 두 텍스트 간 유사도 계산
   */
  async computeSimilarity(
    text1: string,
    text2: string,
    subject: string = 'literature'
  ) {
    return api.post<{
      text1: string;
      text2: string;
      similarity: number;
      subject: string;
    }>('/literature/ai/compute-similarity', {
      text1,
      text2,
      subject,
    });
  },
};
