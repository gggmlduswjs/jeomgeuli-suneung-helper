/**
 * 영어 교재 API
 */
import { api } from './api';

export interface EnglishLectureSummary {
  lecture_id: number;
  title: string;
}

export interface EnglishLecture {
  subject: string;
  lecture_id: number;
  title: string;
  page?: number;
  sections?: Array<{
    title: string;
    type?: string;
    content?: string[];
    page?: number;
    content_id?: string;
    image_path?: string;
  }>;
  problems?: string[];
  problem_meta?: Array<{
    problem_id: string;
    source?: string;
    question: string;
    passage_summary?: string;
    choices: Record<string, string>;
    correct_answer: string;
  }>;
}

export interface EnglishProblem {
  problem_id: string;
  page: number;
  source?: string;
  question?: string;
  question_text?: string;
  choices?: Record<string, string>;
  correct_answer?: string;
  passage?: string;
}

export const englishAPI = {
  async getLectures(): Promise<EnglishLectureSummary[]> {
    return api.get<EnglishLectureSummary[]>('/english/lectures');
  },
  async getLecture(lectureId: number): Promise<EnglishLecture> {
    return api.get<EnglishLecture>(`/english/lectures/${lectureId}`);
  },
  async getProblems(): Promise<EnglishProblem[]> {
    return api.get<EnglishProblem[]>('/english/problems');
  },
  async getProblem(problemId: string): Promise<EnglishProblem> {
    return api.get<EnglishProblem>(`/english/problems/${problemId}`);
  },
  async getConceptImages(): Promise<string[]> {
    return api.get<string[]>('/english/images/concepts');
  },
  async getContentImages(): Promise<string[]> {
    return api.get<string[]>('/english/images/content');
  },
  async getProblemImages(): Promise<string[]> {
    return api.get<string[]>('/english/images/problems');
  },
  async getContentList(): Promise<unknown[]> {
    return api.get<unknown[]>('/english/content');
  },
  async getContent(contentId: string): Promise<unknown> {
    return api.get<unknown>(`/english/content/${contentId}`);
  },
};
