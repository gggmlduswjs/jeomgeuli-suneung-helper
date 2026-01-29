/**
 * 수학1 교재 API
 */
import { api } from './api';

export interface Math1LectureSummary {
  lecture_id: number;
  title: string;
}

export interface Math1Lecture {
  subject: string;
  lecture_id: number;
  title: string;
  page?: number;
  sections?: unknown[];
  problems?: unknown[];
}

export const math1API = {
  async getLectures(): Promise<Math1LectureSummary[]> {
    return api.get<Math1LectureSummary[]>('/math1/lectures');
  },
  async getLecture(lectureId: number): Promise<Math1Lecture> {
    return api.get<Math1Lecture>(`/math1/lectures/${lectureId}`);
  },
};
